"""Core operations for hivemind - shared between CLI and TUI."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from hivemind_cli.providers import (
    Provider,
    get_provider,
    extract_description,
    strip_frontmatter,
)
from hivemind_cli.templates import update_expert_prompt


# --- Progress Callback Types ---


class UpdatePhase(str, Enum):
    """Phases of the update process."""

    CLONING = "cloning"
    FETCHING = "fetching"
    CHECKING = "checking"
    STAGING = "staging"
    ANALYZING = "analyzing"
    COMMITTING = "committing"
    UPDATING_HEAD = "updating_head"
    UPDATING_LIBRARIAN = "updating_librarian"


@dataclass
class ProgressInfo:
    """Progress information for callbacks."""

    expert_name: str
    phase: UpdatePhase
    message: str
    progress_percent: int | None = None  # 0-100 for analysis phase
    new_commit: str | None = None
    old_commit: str | None = None
    error: str | None = None


ProgressCallback = Callable[[ProgressInfo], None]


# --- Paths (shared configuration) ---

# Allow override for testing, otherwise use the same paths as cli.py
HIVEMIND_ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = Path.home() / ".cache" / "hivemind"
REPOS_DIR = CACHE_DIR / "repos"
REPOS_LINK = HIVEMIND_ROOT / "repos"
EXTERNAL_DOCS_DIR = CACHE_DIR / "external_docs"
EXTERNAL_DOCS_LINK = HIVEMIND_ROOT / "external_docs"
HIVEMIND_JSON = HIVEMIND_ROOT / "hivemind.json"
CONFIG_JSON = HIVEMIND_ROOT / "config.json"
PRIVATE_REPOS_JSON = HIVEMIND_ROOT / "private-repos.json"
AGENTS_DIR = HIVEMIND_ROOT / "agents"
EXPERTS_DIR = HIVEMIND_ROOT / "experts"
COMMANDS_DIR = HIVEMIND_ROOT / "commands"
PRIVATE_EXPERTS_DIR = HIVEMIND_ROOT / "private-experts"
TEAMS_DIR = HIVEMIND_ROOT / "teams"
PROJECTS_DIR = HIVEMIND_ROOT / "projects"
HIVEMIND_MD = HIVEMIND_ROOT / "HIVEMIND.md"


# --- Helper Functions ---


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def _load_config() -> dict:
    """Load config.json (local user state: enabled/disabled, active_provider)."""
    default = {"enabled": [], "disabled": []}
    if not CONFIG_JSON.exists():
        return default
    data = _load_json(CONFIG_JSON)
    data.setdefault("enabled", [])
    data.setdefault("disabled", [])
    return data


def _save_config(config: dict) -> None:
    _save_json(CONFIG_JSON, config)


def _load_hivemind() -> dict:
    """Load hivemind.json (shared project config: providers, repos)."""
    data = _load_json(HIVEMIND_JSON)
    data.setdefault("providers", {})
    data.setdefault("repos", {})
    return data


def _save_hivemind(data: dict) -> None:
    _save_json(HIVEMIND_JSON, data)


def _load_teams() -> dict:
    """Load teams from config.json."""
    return _load_config().get("teams", {})


def _save_teams(teams: dict) -> None:
    """Save teams to config.json."""
    config = _load_config()
    config["teams"] = teams
    _save_config(config)


def _load_projects() -> dict:
    """Load projects from config.json."""
    return _load_config().get("projects", {})


def _save_projects(projects: dict) -> None:
    """Save projects to config.json."""
    config = _load_config()
    config["projects"] = projects
    _save_config(config)


def _get_provider() -> Provider:
    """Get the active provider instance from config."""
    config = _load_config()
    active = config.get("active_provider")
    if not active:
        raise RuntimeError(
            "No active_provider set in config.json. Run 'hivemind init' first."
        )
    hivemind = _load_hivemind()
    provider_config = hivemind.get("providers", {}).get(active, {})
    return get_provider(active, provider_config)


def _load_repos() -> dict:
    return _load_hivemind().get("repos", {})


def _save_repos(repos: dict) -> None:
    hm = _load_hivemind()
    hm["repos"] = repos
    _save_hivemind(hm)


def _load_private_repos() -> dict:
    """Load private-repos.json (gitignored, never committed)."""
    if not PRIVATE_REPOS_JSON.exists():
        return {}
    try:
        return json.loads(PRIVATE_REPOS_JSON.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _save_private_repos(repos: dict) -> None:
    """Save private-repos.json."""
    PRIVATE_REPOS_JSON.write_text(json.dumps(repos, indent=2) + "\n")


def _is_private_expert(name: str) -> bool:
    """Check if expert is private based on config."""
    config = _load_config()
    return name in config.get("private", [])


def _get_expert_dir(name: str) -> Path:
    """Get expert directory (public or private)."""
    if _is_private_expert(name):
        return PRIVATE_EXPERTS_DIR / name
    return EXPERTS_DIR / name


def _get_repos_for_expert(name: str) -> tuple[dict, bool]:
    """Get (repos_dict, is_private) for expert."""
    if _is_private_expert(name):
        return _load_private_repos(), True
    return _load_repos(), False


def _expert_names() -> list[str]:
    """List all expert names from experts/ and private-experts/ directories."""
    experts = []
    if EXPERTS_DIR.exists():
        experts.extend(d.name for d in EXPERTS_DIR.iterdir() if d.is_dir())
    if PRIVATE_EXPERTS_DIR.exists():
        experts.extend(d.name for d in PRIVATE_EXPERTS_DIR.iterdir() if d.is_dir())
    return sorted(experts)


def _get_head_commit(expert_dir: Path) -> str | None:
    """Read the HEAD symlink to get the current commit hash."""
    head = expert_dir / "HEAD"
    if not head.is_symlink():
        return None
    return os.readlink(head)


def _count_versions(expert_dir: Path) -> int:
    """Count commit directories (excludes HEAD symlink)."""
    if not expert_dir.exists():
        return 0
    return sum(
        1
        for d in expert_dir.iterdir()
        if d.is_dir() and not d.is_symlink() and d.name != "__pycache__"
    )


def _ensure_repos_link() -> None:
    """Ensure HIVEMIND_ROOT/repos symlink points to the cache repos dir."""
    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    if REPOS_LINK.is_symlink():
        if REPOS_LINK.resolve() == REPOS_DIR.resolve():
            return
        REPOS_LINK.unlink()
    elif REPOS_LINK.is_dir():
        # Move existing real directory contents to cache
        for item in REPOS_LINK.iterdir():
            dest = REPOS_DIR / item.name
            if not dest.exists():
                item.rename(dest)
        REPOS_LINK.rmdir()
    elif REPOS_LINK.exists():
        REPOS_LINK.unlink()
    REPOS_LINK.symlink_to(REPOS_DIR)


def _ensure_external_docs_link() -> None:
    """Ensure HIVEMIND_ROOT/external_docs symlink points to the cache external_docs dir."""
    EXTERNAL_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    if EXTERNAL_DOCS_LINK.is_symlink():
        if EXTERNAL_DOCS_LINK.resolve() == EXTERNAL_DOCS_DIR.resolve():
            return
        EXTERNAL_DOCS_LINK.unlink()
    elif EXTERNAL_DOCS_LINK.is_dir():
        # Move existing real directory contents to cache
        for item in EXTERNAL_DOCS_LINK.iterdir():
            dest = EXTERNAL_DOCS_DIR / item.name
            if not dest.exists():
                item.rename(dest)
        EXTERNAL_DOCS_LINK.rmdir()
    elif EXTERNAL_DOCS_LINK.exists():
        EXTERNAL_DOCS_LINK.unlink()
    EXTERNAL_DOCS_LINK.symlink_to(EXTERNAL_DOCS_DIR)


def _deploy_agent(name: str) -> bool:
    """Generate and deploy agent file with provider-specific frontmatter.

    Reads the canonical body from experts/{name}/HEAD/agent.md, strips any
    existing frontmatter, extracts the description, and generates a new file
    with the active provider's frontmatter and path transformations.

    Returns False if HEAD/agent.md doesn't exist.
    """
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    expert_dir = _get_expert_dir(name)
    head_agent = expert_dir / "HEAD" / "agent.md"

    if not head_agent.exists():
        return False

    provider = _get_provider()

    # Read canonical body and strip any frontmatter
    raw_content = head_agent.read_text()
    body = strip_frontmatter(raw_content)
    description = extract_description(body)

    # Generate provider-specific content
    content = provider.format_agent_md(name, description, body)

    # Deploy to agents/ directory
    provider.deploy_agent(name, content, agents_dir=AGENTS_DIR)
    return True


def _undeploy_agent(name: str) -> None:
    """Remove agents/expert-<name>.md if it exists."""
    provider = _get_provider()
    provider.undeploy_agent(name, agents_dir=AGENTS_DIR)


def _deploy_expert(name: str) -> bool:
    """Deploy expert directory to active provider's expert location.

    Returns True if deployed, False if expert doesn't exist.
    """
    source_dir = _get_expert_dir(name)
    if not source_dir.exists():
        return False

    provider = _get_provider()
    provider.deploy_expert(name, source_dir)
    return True


def _undeploy_expert(name: str) -> None:
    """Remove expert from active provider's expert location."""
    provider = _get_provider()
    provider.undeploy_expert(name)


def _clone_repo(name: str, repos: dict, *, silent: bool = False) -> bool:
    """Clone a repo to cache repos dir if not already present.

    Args:
        name: Expert name
        repos: repos.json data
        silent: If True, suppress output (for TUI usage)

    Returns:
        True if repo is available (already cloned or newly cloned)
    """
    if name not in repos:
        return False

    _ensure_repos_link()

    repo_dir = REPOS_DIR / name
    if repo_dir.is_dir():
        return True  # Already cloned

    repo = repos[name]
    remote = repo["remote"]
    commit = repo.get("commit", "")
    ref_name = repo.get("ref_name", "")

    # Determine clone command
    if commit:
        subprocess.run(
            [
                "git",
                "clone",
                "--progress" if not silent else "--quiet",
                remote,
                str(repo_dir),
            ],
            check=True,
            stdout=subprocess.DEVNULL if silent else None,
            stderr=subprocess.DEVNULL if silent else None,
        )
        subprocess.run(
            ["git", "checkout", "--quiet", commit],
            cwd=str(repo_dir),
            check=True,
        )
    elif ref_name:
        subprocess.run(
            [
                "git",
                "clone",
                "--progress" if not silent else "--quiet",
                "--branch",
                ref_name,
                remote,
                str(repo_dir),
            ],
            check=True,
            stdout=subprocess.DEVNULL if silent else None,
            stderr=subprocess.DEVNULL if silent else None,
        )
    else:
        subprocess.run(
            [
                "git",
                "clone",
                "--progress" if not silent else "--quiet",
                remote,
                str(repo_dir),
            ],
            check=True,
            stdout=subprocess.DEVNULL if silent else None,
            stderr=subprocess.DEVNULL if silent else None,
        )

    return True


def _analyze_repo(
    name: str,
    commit: str,
    repo_dir: Path,
    expert_dir: Path,
    *,
    is_update: bool = False,
    background: bool = False,
) -> subprocess.Popen | tuple[subprocess.Popen, Path, Path, object, object] | bool:
    """Run AI analysis on a repo via the active provider's engine.

    For create (is_update=False): generates 5 files (4 knowledge + agent.md).
    For update (is_update=True): regenerates 4 knowledge files, preserves agent.md.

    If background=True, returns (proc, stderr_path, stdout_path, stderr_file, stdout_file) tuple.
    Otherwise, waits for completion and returns True on success.
    """
    commit_dir = expert_dir / commit

    # Use centralized templates from templates.py
    if is_update:
        prompt = update_expert_prompt(name, commit, repo_dir, commit_dir)
    else:
        from hivemind_cli.templates import create_expert_prompt

        prompt = create_expert_prompt(name, commit, repo_dir, commit_dir)

    provider = _get_provider()
    cmd = provider.build_analysis_command(
        extra_dirs=[repo_dir, expert_dir],
    )

    # Run from common parent so the engine has filesystem access to both
    # the repo and expert directories (matches async callers which already
    # set cwd=staged_path)
    cwd = Path(os.path.commonpath([repo_dir.resolve(), expert_dir.resolve()]))

    if background:
        # Create temp files for stderr and stdout - use NamedTemporaryFile
        stderr_file = tempfile.NamedTemporaryFile(
            mode="w",
            prefix=f"hivemind-{name}-stderr-",
            suffix=".log",
            delete=False,  # Don't auto-delete, we'll read it later
        )
        stdout_file = tempfile.NamedTemporaryFile(
            mode="w",
            prefix=f"hivemind-{name}-stdout-",
            suffix=".log",
            delete=False,  # Don't auto-delete, we'll read it later
        )
        stderr_path = Path(stderr_file.name)
        stdout_path = Path(stdout_file.name)

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=stdout_file,
            stderr=stderr_file,
            cwd=str(cwd),
        )
        proc.stdin.write(prompt.encode())
        proc.stdin.close()
        # Don't close files yet - process needs them
        return proc, stderr_path, stdout_path, stderr_file, stdout_file
    else:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd),
        )
        stdout, stderr = proc.communicate(input=prompt.encode())
        if proc.returncode != 0:
            err_output = (stderr or stdout or b"").decode().strip()
            if err_output:
                print(f"Analysis error: {err_output}", file=sys.stderr)
            else:
                print(
                    f"Analysis failed with exit code {proc.returncode}",
                    file=sys.stderr,
                )
            return False

        # Validate expected output files exist (engine may exit 0 despite
        # failing to write, e.g. OpenCode rejecting external directory access)
        expected = [
            "summary.md",
            "code_structure.md",
            "build_system.md",
            "apis_and_interfaces.md",
        ]
        if not is_update:
            expected.append("agent.md")
        missing = [f for f in expected if not (commit_dir / f).exists()]
        if missing:
            print(
                f"Analysis produced no output — missing: {', '.join(missing)}",
                file=sys.stderr,
            )
            return False

        return True


def _update_librarian() -> None:
    """Regenerate agents/librarian.md from enabled experts with valid HEAD/agent.md."""
    # Load config to get enabled experts
    config = _load_config()
    enabled_experts = set(config.get("enabled", []))

    entries: list[str] = []

    # Scan both public and private experts
    for expert_base_dir in [EXPERTS_DIR, PRIVATE_EXPERTS_DIR]:
        if not expert_base_dir.exists():
            continue
        for expert_dir in sorted(expert_base_dir.iterdir()):
            if not expert_dir.is_dir():
                continue
            name = expert_dir.name

            # Skip if not enabled
            if name not in enabled_experts:
                continue

            agent_md = expert_dir / "HEAD" / "agent.md"
            if not agent_md.exists():
                continue

            # Extract description from body (not frontmatter)
            description = ""
            try:
                text = agent_md.read_text()
                body = strip_frontmatter(text)
                description = extract_description(body)
            except OSError:
                pass

            # Read first ~5 lines of summary.md
            summary_lines = ""
            summary_md = expert_dir / "HEAD" / "summary.md"
            try:
                lines = summary_md.read_text().splitlines()
                summary_lines = "\n".join(lines[:5])
            except OSError:
                pass

            entry = f"### expert-{name}\n{description}\n\n{summary_lines}"
            entries.append(entry)

    # Generate catalog even if empty, so librarian reflects current state
    catalog = (
        "\n\n---\n\n".join(entries) if entries else "No experts are currently enabled."
    )

    # Build team catalog
    teams = _load_teams()
    team_entries: list[str] = []
    for team_name, team_data in sorted(teams.items()):
        desc = team_data.get("description", "")
        roster = ", ".join(team_data.get("experts", []))
        team_entries.append(
            f"### team-lead-{team_name}\n"
            f"Team lead for {desc}. Roster: {roster}."
        )
    team_catalog = (
        "\n\n---\n\n".join(team_entries) if team_entries else "No teams configured."
    )

    # Build project catalog
    projects = _load_projects()
    project_entries: list[str] = []
    for proj_name, proj_data in sorted(projects.items()):
        desc = proj_data.get("description", "")
        proj_teams = ", ".join(proj_data.get("teams", []))
        project_entries.append(
            f"### project-lead-{proj_name}\n"
            f"Project lead for {desc}. Teams: {proj_teams}."
        )
    project_catalog = (
        "\n\n---\n\n".join(project_entries)
        if project_entries
        else "No projects configured."
    )

    # Build librarian body
    librarian_body = (
        "# Hivemind Librarian\n\n"
        "You are the hivemind librarian. You know every registered expert, team, and "
        "project and what they specialize in. When asked a question, identify which "
        "expert(s), team lead(s), or project lead(s) are best suited and recommend "
        "them by name.\n\n"
        "## Expert Catalog\n\n"
        f"{catalog}\n\n"
        "## Team Catalog\n\n"
        f"{team_catalog}\n\n"
        "## Project Catalog\n\n"
        f"{project_catalog}\n\n"
        "## Instructions\n\n"
        "1. For project-scoped questions, recommend the project lead\n"
        "2. For cross-expert coordination, recommend the team lead\n"
        "3. For domain-specific questions, recommend the expert directly\n"
        "4. Respond with agent name(s) and why they're the right fit\n"
        "5. If multiple agents are relevant, rank by relevance\n"
        "6. If no match, say so clearly\n"
    )

    # Format with provider-specific frontmatter
    provider = _get_provider()
    content = provider.format_librarian_md(librarian_body)

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    (AGENTS_DIR / "librarian.md").write_text(content)


# --- Core Operations ---


def update_expert(
    name: str,
    on_progress: ProgressCallback | None = None,
    *,
    skip_analysis: bool = False,
) -> dict:
    """Update a single expert with progress reporting.

    Returns:
        dict with keys: success (bool), new_commit (str), old_commit (str), error (str | None)
    """
    repos, is_private = _get_repos_for_expert(name)

    if name not in repos:
        return {"success": False, "error": f"{name} not in repos"}

    # Phase 1: Clone/fetch
    if on_progress:
        on_progress(ProgressInfo(name, UpdatePhase.CLONING, "Cloning repository..."))

    if not _clone_repo(name, repos, silent=True):
        return {"success": False, "error": "Failed to clone repository"}

    repo_dir = REPOS_DIR / name

    if on_progress:
        on_progress(
            ProgressInfo(name, UpdatePhase.FETCHING, "Fetching latest commits...")
        )

    try:
        subprocess.run(
            ["git", "fetch", "origin"],
            cwd=str(repo_dir),
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": f"Failed to fetch: {e.stderr.decode()}"}

    # Get latest commit
    if on_progress:
        on_progress(ProgressInfo(name, UpdatePhase.CHECKING, "Checking for updates..."))

    new_commit = None
    for ref in ["origin/HEAD", "origin/main", "origin/master"]:
        result = subprocess.run(
            ["git", "rev-parse", ref],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            new_commit = result.stdout.strip()
            break

    if not new_commit:
        return {"success": False, "error": "Could not resolve latest commit"}

    expert_dir = _get_expert_dir(name)
    old_commit = _get_head_commit(expert_dir)

    if old_commit == new_commit:
        return {
            "success": True,
            "already_up_to_date": True,
            "new_commit": new_commit,
            "old_commit": old_commit,
        }

    # Phase 2: Stage for analysis
    if on_progress:
        on_progress(
            ProgressInfo(
                name,
                UpdatePhase.STAGING,
                f"Staging update from {old_commit[:12] if old_commit else 'none'} to {new_commit[:12]}...",
                new_commit=new_commit,
                old_commit=old_commit,
            )
        )

    tmpdir = tempfile.mkdtemp(prefix=f"hivemind-update-{name}-")
    tmp_expert = Path(tmpdir) / "expert"
    tmp_expert.mkdir()
    tmp_commit_dir = tmp_expert / new_commit
    tmp_commit_dir.mkdir()

    try:
        # Copy baseline files
        if old_commit:
            old_dir = expert_dir / old_commit
            if old_dir.is_dir():
                for f in old_dir.iterdir():
                    if f.is_file():
                        shutil.copy2(f, tmp_commit_dir / f.name)

        # Checkout new commit
        subprocess.run(
            ["git", "checkout", "--quiet", new_commit],
            cwd=str(repo_dir),
            check=True,
        )

        # Phase 3: AI Analysis (skip if requested)
        if not skip_analysis:
            if on_progress:
                on_progress(
                    ProgressInfo(
                        name,
                        UpdatePhase.ANALYZING,
                        f"Analyzing {new_commit[:12]} (this may take 2-5 minutes)...",
                        progress_percent=0,
                        new_commit=new_commit,
                        old_commit=old_commit,
                    )
                )

            # Start analysis process
            proc, stderr_path, stdout_path, stderr_file, stdout_file = _analyze_repo(
                name, new_commit, repo_dir, tmp_expert, is_update=True, background=True
            )

            # Poll until complete (for progress updates)
            while proc.poll() is None:
                time.sleep(1)  # Check every second
                if on_progress:
                    # Continue showing analyzing message
                    on_progress(
                        ProgressInfo(
                            name,
                            UpdatePhase.ANALYZING,
                            f"Analyzing {new_commit[:12]}...",
                            new_commit=new_commit,
                            old_commit=old_commit,
                        )
                    )

            # Close files now that process is done
            stderr_file.close()
            stdout_file.close()

            if proc.returncode != 0:
                # Analysis failed - read error from stderr and stdout files
                error_msg = f"AI analysis failed (exit code {proc.returncode})"
                try:
                    stderr_content = stderr_path.read_text()
                    stdout_content = stdout_path.read_text()

                    if stderr_content.strip():
                        # Include last 500 chars of stderr
                        error_msg += f"\nStderr: {stderr_content[-500:]}"
                    if stdout_content.strip():
                        # Include last 500 chars of stdout
                        error_msg += f"\nStdout: {stdout_content[-500:]}"

                    if not stderr_content.strip() and not stdout_content.strip():
                        error_msg += f"\nNo output captured."
                except Exception as e:
                    error_msg += f"\nCould not read output: {e}"
                finally:
                    # Clean up log files
                    try:
                        stderr_path.unlink()
                        stdout_path.unlink()
                    except Exception:
                        pass

                # Revert checkout
                if old_commit:
                    subprocess.run(
                        ["git", "checkout", "--quiet", old_commit],
                        cwd=str(repo_dir),
                        capture_output=True,
                    )
                return {
                    "success": False,
                    "error": error_msg,
                    "new_commit": new_commit,
                    "old_commit": old_commit,
                }

            # Clean up log files on success
            try:
                stderr_path.unlink()
                stdout_path.unlink()
            except Exception:
                pass
        else:
            if on_progress:
                on_progress(
                    ProgressInfo(
                        name,
                        UpdatePhase.ANALYZING,
                        "Skipping analysis (reusing existing docs)...",
                        new_commit=new_commit,
                        old_commit=old_commit,
                    )
                )

        # Phase 4: Commit results
        if on_progress:
            on_progress(
                ProgressInfo(name, UpdatePhase.COMMITTING, "Committing changes...")
            )

        # Move staged files to final location
        final_commit_dir = expert_dir / new_commit
        final_commit_dir.mkdir(parents=True, exist_ok=True)

        for f in tmp_commit_dir.iterdir():
            if f.is_file():
                shutil.move(str(f), str(final_commit_dir / f.name))

        # Update HEAD symlink
        if on_progress:
            on_progress(
                ProgressInfo(
                    name, UpdatePhase.UPDATING_HEAD, "Updating HEAD symlink..."
                )
            )

        head_link = expert_dir / "HEAD"
        if head_link.is_symlink():
            head_link.unlink()
        head_link.symlink_to(new_commit)

        # Update repos.json or private-repos.json
        repos[name]["commit"] = new_commit
        if is_private:
            _save_private_repos(repos)
        else:
            _save_repos(repos)

        return {
            "success": True,
            "new_commit": new_commit,
            "old_commit": old_commit,
        }

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


async def update_expert_async_internal(
    name: str,
    on_progress: ProgressCallback | None = None,
    on_subprocess_start: Callable[[int], None] | None = None,
    cancellation_token: "CancellationToken | None" = None,
) -> dict:
    """Async version of update_expert with cancellation support.

    Args:
        name: Expert name to update
        on_progress: Progress callback function
        on_subprocess_start: Called with subprocess PID when analysis starts
        cancellation_token: Token to check for cancellation requests

    Returns:
        dict with keys: success (bool), new_commit (str), old_commit (str),
                        error (str | None), cancelled (bool | None)
    """
    from hivemind_cli.tui.operations import CancellationToken

    def _check_cancellation(phase: str):
        """Check if operation was cancelled (except during risky phases)."""
        if not cancellation_token or not cancellation_token.is_cancelled():
            return

        # Allow risky phases to complete
        risky_phases = {UpdatePhase.COMMITTING, UpdatePhase.UPDATING_HEAD}
        if phase not in risky_phases:
            raise asyncio.CancelledError(f"Cancelled before {phase}")

    repos, is_private = _get_repos_for_expert(name)

    if name not in repos:
        return {"success": False, "error": f"{name} not in repos"}

    tmpdir = None
    staged_path = None
    stderr_path = None
    stdout_path = None
    stderr_file = None
    stdout_file = None

    try:
        # Phase 1: Clone/fetch
        _check_cancellation(UpdatePhase.CLONING)
        if on_progress:
            on_progress(
                ProgressInfo(name, UpdatePhase.CLONING, "Cloning repository...")
            )

        if not _clone_repo(name, repos, silent=True):
            return {"success": False, "error": "Failed to clone repository"}

        repo_dir = REPOS_DIR / name

        _check_cancellation(UpdatePhase.FETCHING)
        if on_progress:
            on_progress(
                ProgressInfo(name, UpdatePhase.FETCHING, "Fetching latest commits...")
            )

        try:
            subprocess.run(
                ["git", "fetch", "origin"],
                cwd=str(repo_dir),
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            return {"success": False, "error": f"Failed to fetch: {e.stderr.decode()}"}

        # Get latest commit
        _check_cancellation(UpdatePhase.CHECKING)
        if on_progress:
            on_progress(
                ProgressInfo(name, UpdatePhase.CHECKING, "Checking for updates...")
            )

        new_commit = None
        for ref in ["origin/HEAD", "origin/main", "origin/master"]:
            result = subprocess.run(
                ["git", "rev-parse", ref],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                new_commit = result.stdout.strip()
                break

        if not new_commit:
            return {"success": False, "error": "Could not resolve latest commit"}

        expert_dir = _get_expert_dir(name)
        old_commit = _get_head_commit(expert_dir)

        if old_commit == new_commit:
            return {
                "success": True,
                "already_up_to_date": True,
                "new_commit": new_commit,
                "old_commit": old_commit,
            }

        # Phase 2: Stage for analysis
        _check_cancellation(UpdatePhase.STAGING)
        if on_progress:
            on_progress(
                ProgressInfo(
                    name,
                    UpdatePhase.STAGING,
                    f"Staging update from {old_commit[:12] if old_commit else 'none'} to {new_commit[:12]}...",
                    new_commit=new_commit,
                    old_commit=old_commit,
                )
            )

        tmpdir = tempfile.mkdtemp(prefix=f"hivemind-update-{name}-")
        staged_path = Path(tmpdir) / "expert"
        staged_path.mkdir()
        tmp_commit_dir = staged_path / new_commit
        tmp_commit_dir.mkdir()

        # Copy baseline files
        if old_commit:
            old_dir = expert_dir / old_commit
            if old_dir.is_dir():
                for f in old_dir.iterdir():
                    if f.is_file():
                        shutil.copy2(f, tmp_commit_dir / f.name)

        # Checkout new commit
        subprocess.run(
            ["git", "checkout", "--quiet", new_commit],
            cwd=str(repo_dir),
            check=True,
        )

        # Phase 3: AI Analysis (async subprocess)
        _check_cancellation(UpdatePhase.ANALYZING)
        if on_progress:
            on_progress(
                ProgressInfo(
                    name,
                    UpdatePhase.ANALYZING,
                    f"Analyzing {new_commit[:12]} (this may take 2-5 minutes)...",
                    progress_percent=0,
                    new_commit=new_commit,
                    old_commit=old_commit,
                )
            )

        # Prepare prompt and command
        prompt = update_expert_prompt(name, new_commit, repo_dir, tmp_commit_dir)

        # Create temp files for stderr and stdout (binary mode for subprocess)
        stderr_file = tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f"hivemind-{name}-stderr-",
            suffix=".log",
            delete=False,
        )
        stdout_file = tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f"hivemind-{name}-stdout-",
            suffix=".log",
            delete=False,
        )
        stderr_path = Path(stderr_file.name)
        stdout_path = Path(stdout_file.name)

        provider = _get_provider()
        cmd = provider.build_analysis_command(
            extra_dirs=[repo_dir, staged_path],
        )

        # Start async subprocess
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=stderr_file.fileno(),
            stderr=stdout_file.fileno(),
            cwd=str(staged_path),
        )

        # Send prompt to stdin
        if proc.stdin:
            proc.stdin.write(prompt.encode())
            await proc.stdin.drain()
            proc.stdin.close()
            await proc.stdin.wait_closed()

        # Close file handles now that subprocess has them
        stderr_file.close()
        stdout_file.close()

        # Notify TUI of subprocess PID
        if on_subprocess_start:
            on_subprocess_start(proc.pid)

        # Poll until complete with cancellation checks
        while proc.returncode is None:
            await asyncio.sleep(1)  # Non-blocking

            # Check for cancellation
            if cancellation_token and cancellation_token.is_cancelled():
                # Terminate subprocess gracefully
                try:
                    proc.terminate()  # Send SIGTERM
                    await asyncio.wait_for(proc.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    proc.kill()  # Force kill if didn't terminate
                    await proc.wait()
                raise asyncio.CancelledError("Update cancelled by user")

            # Update progress
            if on_progress:
                on_progress(
                    ProgressInfo(
                        name,
                        UpdatePhase.ANALYZING,
                        f"Analyzing {new_commit[:12]}...",
                        new_commit=new_commit,
                        old_commit=old_commit,
                    )
                )

        # Check exit code
        if proc.returncode != 0:
            # Analysis failed - read error from stderr and stdout files
            error_msg = f"AI analysis failed (exit code {proc.returncode})"
            try:
                stderr_content = stderr_path.read_text()
                stdout_content = stdout_path.read_text()

                if stderr_content.strip():
                    error_msg += f"\nStderr: {stderr_content[-500:]}"
                if stdout_content.strip():
                    error_msg += f"\nStdout: {stdout_content[-500:]}"

                if not stderr_content.strip() and not stdout_content.strip():
                    error_msg += f"\nNo output captured."

            except Exception as e:
                error_msg += f"\nCould not read output: {e}"
            finally:
                # Clean up log files
                try:
                    stderr_path.unlink()
                    stdout_path.unlink()
                except Exception:
                    pass

            # Revert checkout
            if old_commit:
                subprocess.run(
                    ["git", "checkout", "--quiet", old_commit],
                    cwd=str(repo_dir),
                    capture_output=True,
                )
            return {
                "success": False,
                "error": error_msg,
                "new_commit": new_commit,
                "old_commit": old_commit,
            }

        # Clean up log files on success
        try:
            stderr_path.unlink()
            stdout_path.unlink()
        except Exception:
            pass

        # Phase 4: Commit results (risky - let it complete)
        if on_progress:
            on_progress(
                ProgressInfo(name, UpdatePhase.COMMITTING, "Committing changes...")
            )

        # Move staged files to final location
        final_commit_dir = expert_dir / new_commit
        final_commit_dir.mkdir(parents=True, exist_ok=True)

        for f in tmp_commit_dir.iterdir():
            if f.is_file():
                shutil.move(str(f), str(final_commit_dir / f.name))

        # Update HEAD symlink (risky - let it complete)
        if on_progress:
            on_progress(
                ProgressInfo(
                    name, UpdatePhase.UPDATING_HEAD, "Updating HEAD symlink..."
                )
            )

        head_link = expert_dir / "HEAD"
        if head_link.is_symlink():
            head_link.unlink()
        head_link.symlink_to(new_commit)

        # Update repos.json
        repos[name]["commit"] = new_commit
        _save_repos(repos)

        return {
            "success": True,
            "new_commit": new_commit,
            "old_commit": old_commit,
        }

    except asyncio.CancelledError:
        # Clean up temp directory
        if staged_path and staged_path.exists():
            shutil.rmtree(staged_path, ignore_errors=True)

        # Clean up log files
        if stderr_path and stderr_path.exists():
            try:
                stderr_path.unlink()
            except Exception:
                pass
        if stdout_path and stdout_path.exists():
            try:
                stdout_path.unlink()
            except Exception:
                pass

        # Revert git checkout if needed
        if old_commit:
            try:
                repo_dir = REPOS_DIR / name
                subprocess.run(
                    ["git", "checkout", "--quiet", old_commit],
                    cwd=str(repo_dir),
                    capture_output=True,
                )
            except Exception:
                pass

        # Return cancelled result
        return {
            "success": False,
            "error": "Update cancelled by user",
            "cancelled": True,
        }

    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


def get_git_versions(name: str, expert_dir: Path) -> list:
    """Retrieve all available versions from git repo (tags + recent commits).

    Args:
        name: Expert name
        expert_dir: Path to expert directory (~/.claude/experts/<name>)

    Returns:
        List of VersionInfo objects sorted by: active first → tags → commits (by date)
    """
    from hivemind_cli.tui.models import VersionInfo

    repo_dir = REPOS_DIR / name
    if not repo_dir.exists():
        return []

    try:
        # Check if repo is shallow and unshallow it to get full history
        shallow_file = repo_dir / ".git" / "shallow"
        if shallow_file.exists():
            # Repo is shallow - fetch full history
            subprocess.run(
                ["git", "fetch", "--unshallow"],
                cwd=str(repo_dir),
                capture_output=True,
                text=True,
            )

        # Get current HEAD commit
        current_head = _get_head_commit(expert_dir)

        # Get analyzed commits from expert_dir subdirectories
        analyzed_commits = set()
        if expert_dir.exists():
            for d in expert_dir.iterdir():
                if d.is_dir() and not d.is_symlink() and d.name != "__pycache__":
                    analyzed_commits.add(d.name)

        versions = []
        commit_to_info = {}  # Track commits to avoid duplicates

        # Query git tags
        result = subprocess.run(
            [
                "git",
                "tag",
                "-l",
                "--format=%(refname:short)|%(creatordate:short)|%(objectname)",
            ],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
        )

        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|")
                if len(parts) >= 3:
                    tag_name, date, tag_commit = parts[0], parts[1], parts[2]

                    # Resolve tag to commit hash
                    resolve_result = subprocess.run(
                        ["git", "rev-parse", tag_name],
                        cwd=str(repo_dir),
                        capture_output=True,
                        text=True,
                    )
                    if resolve_result.returncode == 0:
                        commit = resolve_result.stdout.strip()

                        version_info = VersionInfo(
                            commit=commit,
                            type="tag",
                            name=tag_name,
                            date=date,
                            analyzed=commit in analyzed_commits,
                            is_active=(commit == current_head),
                        )
                        versions.append(version_info)
                        commit_to_info[commit] = version_info

        # Query recent commits (exclude ones already added as tags)
        result = subprocess.run(
            ["git", "log", "--all", "--format=%H|%cs|%s", "-n", "50"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
        )

        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue
                parts = line.split("|", 2)
                if len(parts) >= 3:
                    commit, date, message = parts[0], parts[1], parts[2]

                    # Skip if already added as a tag
                    if commit not in commit_to_info:
                        version_info = VersionInfo(
                            commit=commit,
                            type="commit",
                            name=message[:80],  # Truncate long messages
                            date=date,
                            analyzed=commit in analyzed_commits,
                            is_active=(commit == current_head),
                        )
                        versions.append(version_info)
                        commit_to_info[commit] = version_info

        # Sort: active first → analyzed → available (by date descending)
        def sort_key(v):
            if v.is_active:
                return (2, v.date)  # Highest priority with reverse=True
            elif v.analyzed:
                return (1, v.date)
            else:
                return (0, v.date)  # Lowest priority with reverse=True

        versions.sort(key=sort_key, reverse=True)
        return versions

    except Exception as e:
        print(f"Error getting git versions: {e}")
        return []


def commit_exists_in_repo(name: str, commit: str) -> bool:
    """Validate that a commit hash exists in the git repo.

    Args:
        name: Expert name
        commit: Commit hash to validate

    Returns:
        True if commit exists, False otherwise
    """
    repo_dir = REPOS_DIR / name
    if not repo_dir.exists():
        return False

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", commit],
            cwd=str(repo_dir),
            capture_output=True,
        )
        return result.returncode == 0
    except Exception:
        return False


async def switch_version_async(
    name: str,
    target_commit: str,
    on_progress: ProgressCallback | None = None,
    on_subprocess_start: Callable[[int], None] | None = None,
    cancellation_token: "CancellationToken | None" = None,
) -> dict:
    """Switch expert to a different version (async with cancellation support).

    Args:
        name: Expert name
        target_commit: Target commit hash to switch to
        on_progress: Progress callback function
        on_subprocess_start: Called with subprocess PID when analysis starts
        cancellation_token: Token to check for cancellation requests

    Returns:
        dict with keys: success (bool), old_commit (str), new_commit (str),
                        error (str | None), cancelled (bool | None)
    """
    from hivemind_cli.tui.operations import CancellationToken

    def _check_cancellation(phase: str):
        """Check if operation was cancelled (except during risky phases)."""
        if not cancellation_token or not cancellation_token.is_cancelled():
            return

        # Allow risky phases to complete
        risky_phases = {UpdatePhase.COMMITTING, UpdatePhase.UPDATING_HEAD}
        if phase not in risky_phases:
            raise asyncio.CancelledError(f"Cancelled before {phase}")

    repos, is_private = _get_repos_for_expert(name)

    if name not in repos:
        return {"success": False, "error": f"{name} not in repos"}

    expert_dir = _get_expert_dir(name)
    repo_dir = REPOS_DIR / name

    if not repo_dir.exists():
        return {"success": False, "error": "Repository not cloned"}

    tmpdir = None
    staged_path = None
    stderr_path = None
    stdout_path = None
    stderr_file = None
    stdout_file = None
    old_commit = None

    try:
        # Get current HEAD
        old_commit = _get_head_commit(expert_dir)

        # Check if already active
        if old_commit == target_commit:
            return {
                "success": True,
                "already_active": True,
                "old_commit": old_commit,
                "new_commit": target_commit,
            }

        # Check if target commit exists
        if not commit_exists_in_repo(name, target_commit):
            return {
                "success": False,
                "error": f"Commit {target_commit[:12]} not found in repository",
            }

        target_dir = expert_dir / target_commit

        # If NOT analyzed, need to checkout and analyze
        if not target_dir.exists() or not (target_dir / "agent.md").exists():
            _check_cancellation(UpdatePhase.CHECKING)
            if on_progress:
                on_progress(
                    ProgressInfo(
                        name,
                        UpdatePhase.CHECKING,
                        f"Checking out {target_commit[:12]}...",
                        old_commit=old_commit,
                        new_commit=target_commit,
                    )
                )

            # Checkout target commit
            try:
                subprocess.run(
                    ["git", "checkout", "--quiet", target_commit],
                    cwd=str(repo_dir),
                    check=True,
                )
            except subprocess.CalledProcessError as e:
                return {"success": False, "error": f"Failed to checkout commit: {e}"}

            # Create temp directory for analysis
            _check_cancellation(UpdatePhase.STAGING)
            if on_progress:
                on_progress(
                    ProgressInfo(
                        name,
                        UpdatePhase.STAGING,
                        f"Staging analysis for {target_commit[:12]}...",
                        old_commit=old_commit,
                        new_commit=target_commit,
                    )
                )

            tmpdir = tempfile.mkdtemp(prefix=f"hivemind-version-{name}-")
            staged_path = Path(tmpdir) / "expert"
            staged_path.mkdir()
            tmp_commit_dir = staged_path / target_commit
            tmp_commit_dir.mkdir()

            # Run analysis subprocess (similar to update_expert_async_internal)
            _check_cancellation(UpdatePhase.ANALYZING)
            if on_progress:
                on_progress(
                    ProgressInfo(
                        name,
                        UpdatePhase.ANALYZING,
                        f"Analyzing {target_commit[:12]} (this may take 2-5 minutes)...",
                        progress_percent=0,
                        old_commit=old_commit,
                        new_commit=target_commit,
                    )
                )

            # Prepare prompt for create (not update)
            from hivemind_cli.templates import create_expert_prompt

            prompt = create_expert_prompt(name, target_commit, repo_dir, tmp_commit_dir)

            # Create temp files for stderr and stdout (binary mode for subprocess)
            stderr_file = tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=f"hivemind-{name}-stderr-",
                suffix=".log",
                delete=False,
            )
            stdout_file = tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=f"hivemind-{name}-stdout-",
                suffix=".log",
                delete=False,
            )
            stderr_path = Path(stderr_file.name)
            stdout_path = Path(stdout_file.name)

            provider = _get_provider()
            cmd = provider.build_analysis_command(
                extra_dirs=[repo_dir, staged_path],
            )

            # Start async subprocess
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=stderr_file.fileno(),
                stderr=stdout_file.fileno(),
                cwd=str(staged_path),
            )

            # Send prompt to stdin
            if proc.stdin:
                proc.stdin.write(prompt.encode())
                await proc.stdin.drain()
                proc.stdin.close()
                await proc.stdin.wait_closed()

            # Close file handles now that subprocess has them
            stderr_file.close()
            stdout_file.close()

            # Notify TUI of subprocess PID
            if on_subprocess_start:
                on_subprocess_start(proc.pid)

            # Poll until complete with cancellation checks
            while proc.returncode is None:
                await asyncio.sleep(1)  # Non-blocking

                # Check for cancellation
                if cancellation_token and cancellation_token.is_cancelled():
                    # Terminate subprocess gracefully
                    try:
                        proc.terminate()  # Send SIGTERM
                        await asyncio.wait_for(proc.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        proc.kill()  # Force kill if didn't terminate
                        await proc.wait()
                    raise asyncio.CancelledError("Version switch cancelled by user")

                # Update progress
                if on_progress:
                    on_progress(
                        ProgressInfo(
                            name,
                            UpdatePhase.ANALYZING,
                            f"Analyzing {target_commit[:12]}...",
                            old_commit=old_commit,
                            new_commit=target_commit,
                        )
                    )

            # Check exit code
            if proc.returncode != 0:
                # Analysis failed - read error from stderr and stdout files
                error_msg = f"AI analysis failed (exit code {proc.returncode})"
                try:
                    stderr_content = stderr_path.read_text()
                    stdout_content = stdout_path.read_text()

                    if stderr_content.strip():
                        error_msg += f"\nStderr: {stderr_content[-500:]}"
                    if stdout_content.strip():
                        error_msg += f"\nStdout: {stdout_content[-500:]}"

                    if not stderr_content.strip() and not stdout_content.strip():
                        error_msg += f"\nNo output captured."

                except Exception as e:
                    error_msg += f"\nCould not read output: {e}"
                finally:
                    # Clean up log files
                    try:
                        stderr_path.unlink()
                        stdout_path.unlink()
                    except Exception:
                        pass

                # Revert checkout
                if old_commit:
                    subprocess.run(
                        ["git", "checkout", "--quiet", old_commit],
                        cwd=str(repo_dir),
                        capture_output=True,
                    )
                return {
                    "success": False,
                    "error": error_msg,
                    "old_commit": old_commit,
                    "new_commit": target_commit,
                }

            # Clean up log files on success
            try:
                stderr_path.unlink()
                stdout_path.unlink()
            except Exception:
                pass

            # Move staged files to final location
            if on_progress:
                on_progress(
                    ProgressInfo(
                        name,
                        UpdatePhase.COMMITTING,
                        "Committing changes...",
                        old_commit=old_commit,
                        new_commit=target_commit,
                    )
                )

            final_commit_dir = expert_dir / target_commit
            final_commit_dir.mkdir(parents=True, exist_ok=True)

            for f in tmp_commit_dir.iterdir():
                if f.is_file():
                    shutil.move(str(f), str(final_commit_dir / f.name))

        # Checkout target commit in repo to keep repo and symlink in sync
        try:
            subprocess.run(
                ["git", "checkout", "--quiet", target_commit],
                cwd=str(repo_dir),
                check=True,
            )
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to checkout commit in repo: {e}",
            }

        # Update HEAD symlink (risky - let it complete)
        if on_progress:
            on_progress(
                ProgressInfo(
                    name,
                    UpdatePhase.UPDATING_HEAD,
                    "Updating HEAD symlink...",
                    old_commit=old_commit,
                    new_commit=target_commit,
                )
            )

        head_link = expert_dir / "HEAD"
        if head_link.is_symlink():
            head_link.unlink()
        head_link.symlink_to(target_commit)

        # Redeploy agent file with updated content
        _deploy_agent(name)

        # Update repos.json or private-repos.json
        repos[name]["commit"] = target_commit
        if is_private:
            _save_private_repos(repos)
        else:
            _save_repos(repos)

        return {
            "success": True,
            "old_commit": old_commit,
            "new_commit": target_commit,
        }

    except asyncio.CancelledError:
        # Clean up temp directory
        if staged_path and staged_path.exists():
            shutil.rmtree(staged_path, ignore_errors=True)

        # Clean up log files
        if stderr_path and stderr_path.exists():
            try:
                stderr_path.unlink()
            except Exception:
                pass
        if stdout_path and stdout_path.exists():
            try:
                stdout_path.unlink()
            except Exception:
                pass

        # Revert git checkout if needed
        if old_commit:
            try:
                subprocess.run(
                    ["git", "checkout", "--quiet", old_commit],
                    cwd=str(repo_dir),
                    capture_output=True,
                )
            except Exception:
                pass

        # Return cancelled result
        return {
            "success": False,
            "error": "Version switch cancelled by user",
            "cancelled": True,
        }

    finally:
        if tmpdir:
            shutil.rmtree(tmpdir, ignore_errors=True)


def enable_expert(name: str) -> dict:
    """Enable an expert (clone repo + create agent symlink).

    Returns:
        dict with keys: success (bool), already_enabled (bool), error (str | None)
    """
    expert_dir = _get_expert_dir(name)
    if not expert_dir.is_dir():
        return {"success": False, "error": f"Expert '{name}' not found"}

    config = _load_config()
    already_enabled = name in config["enabled"]

    if not already_enabled:
        config["enabled"].append(name)
        if name in config["disabled"]:
            config["disabled"].remove(name)
        _save_config(config)

    repos, is_private = _get_repos_for_expert(name)
    if not _clone_repo(name, repos, silent=True):
        return {"success": False, "error": "Failed to clone repository"}

    _deploy_agent(name)
    _deploy_expert(name)

    # Update librarian to reflect enabled experts
    _update_librarian()

    return {"success": True, "already_enabled": already_enabled}


def disable_expert(name: str) -> dict:
    """Disable an expert (remove agent symlink).

    Returns:
        dict with keys: success (bool), already_disabled (bool), error (str | None)
    """
    expert_dir = _get_expert_dir(name)
    if not expert_dir.is_dir():
        return {"success": False, "error": f"Expert '{name}' not found"}

    config = _load_config()
    already_disabled = name not in config["enabled"] and name in config["disabled"]

    if not already_disabled:
        if name in config["enabled"]:
            config["enabled"].remove(name)
        if name not in config["disabled"]:
            config["disabled"].append(name)
        _save_config(config)

    _undeploy_agent(name)
    _undeploy_expert(name)

    # Update librarian to reflect enabled experts
    _update_librarian()

    return {"success": True, "already_disabled": already_disabled}


def redeploy_all_agents() -> dict:
    """Regenerate all enabled agent files with current provider settings.

    Used after changing provider config (tools, model, etc.) to apply changes
    to all deployed agent files without re-running AI analysis.

    Returns:
        dict with keys: success (bool), deployed (list[str]), failed (list[str]),
        teams_deployed (list[str]), projects_deployed (list[str])
    """
    config = _load_config()
    enabled = config.get("enabled", [])

    deployed: list[str] = []
    failed: list[str] = []

    for name in enabled:
        if _deploy_agent(name):
            deployed.append(name)
        else:
            failed.append(name)

    # Redeploy team leads and team-scoped experts
    teams_deployed: list[str] = []
    teams = _load_teams()
    for team_name in teams:
        if _deploy_team_lead(team_name):
            teams_deployed.append(f"team-lead-{team_name}")
        _deploy_team_experts(team_name)

    # Redeploy project leads
    projects_deployed: list[str] = []
    projects = _load_projects()
    for project_name in projects:
        if _deploy_project_lead(project_name):
            projects_deployed.append(f"project-lead-{project_name}")

    # Regenerate librarian and HIVEMIND.md
    _update_librarian()
    _regenerate_hivemind_md()

    return {
        "success": True,
        "deployed": deployed,
        "failed": failed,
        "teams_deployed": teams_deployed,
        "projects_deployed": projects_deployed,
    }


# --- HIVEMIND.md Generation ---


def _regenerate_hivemind_md() -> None:
    """Regenerate HIVEMIND.md from base template + active project appendix."""
    from hivemind_cli.templates import hivemind_md_base

    content = hivemind_md_base()

    # Check for active project
    config = _load_config()
    active_project = config.get("active_project")

    if active_project:
        projects = _load_projects()
        if active_project in projects:
            project_md_path = PROJECTS_DIR / active_project / "project.md"
            if project_md_path.exists():
                project_content = project_md_path.read_text().strip()
                if project_content:
                    content += "\n" + project_content + "\n"

    HIVEMIND_MD.write_text(content)


# --- Team Operations ---


def _deploy_team_lead(team_name: str) -> bool:
    """Deploy team lead agent file with provider-specific frontmatter.

    Reads teams/{team_name}/lead.md, applies frontmatter, writes to
    agents/team-lead-{team_name}.md.

    Returns False if lead.md doesn't exist.
    """
    lead_md = TEAMS_DIR / team_name / "lead.md"
    if not lead_md.exists():
        return False

    provider = _get_provider()
    body = strip_frontmatter(lead_md.read_text())
    description = extract_description(body)

    content = provider.format_lead_md(f"team-lead-{team_name}", description, body)

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    agent_file = AGENTS_DIR / f"team-lead-{team_name}.md"
    if agent_file.is_symlink():
        agent_file.unlink()
    agent_file.write_text(content)
    return True


def _undeploy_team_lead(team_name: str) -> None:
    """Remove agents/team-lead-{team_name}.md if it exists."""
    agent_file = AGENTS_DIR / f"team-lead-{team_name}.md"
    if agent_file.is_symlink() or agent_file.exists():
        agent_file.unlink()


def _deploy_team_expert(team_name: str, expert_name: str) -> bool:
    """Deploy a team-scoped expert copy.

    Reads original expert body, appends team general.md + per-expert context,
    writes to agents/expert-{expert_name}_{team_name}.md.

    Returns False if original expert agent.md doesn't exist.
    """
    expert_dir = _get_expert_dir(expert_name)
    head_agent = expert_dir / "HEAD" / "agent.md"

    if not head_agent.exists():
        return False

    provider = _get_provider()
    body = strip_frontmatter(head_agent.read_text())

    # Append team context
    team_context_parts: list[str] = []

    # General team context (shared across all experts on the team)
    general_md = TEAMS_DIR / team_name / "general.md"
    if general_md.exists():
        general_content = general_md.read_text().strip()
        if general_content:
            team_context_parts.append(general_content)

    # Per-expert team context
    expert_override = TEAMS_DIR / team_name / "experts" / f"{expert_name}.md"
    if expert_override.exists():
        override_content = expert_override.read_text().strip()
        if override_content:
            team_context_parts.append(override_content)

    if team_context_parts:
        body += f"\n\n## Team Context: {team_name}\n\n"
        body += "\n\n".join(team_context_parts)
        body += "\n"

    description = extract_description(body)
    agent_name = f"{expert_name}_{team_name}"
    content = provider.format_agent_md(agent_name, description, body)

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    agent_file = AGENTS_DIR / f"expert-{agent_name}.md"
    if agent_file.is_symlink():
        agent_file.unlink()
    agent_file.write_text(content)
    return True


def _undeploy_team_expert(team_name: str, expert_name: str) -> None:
    """Remove agents/expert-{expert_name}_{team_name}.md if it exists."""
    agent_file = AGENTS_DIR / f"expert-{expert_name}_{team_name}.md"
    if agent_file.is_symlink() or agent_file.exists():
        agent_file.unlink()


def _deploy_team_experts(team_name: str) -> list[str]:
    """Deploy all team-scoped expert copies for a team.

    Returns list of successfully deployed expert names.
    """
    teams = _load_teams()
    if team_name not in teams:
        return []

    deployed = []
    for expert_name in teams[team_name].get("experts", []):
        if _deploy_team_expert(team_name, expert_name):
            deployed.append(expert_name)
    return deployed


def _undeploy_team_experts(team_name: str) -> None:
    """Remove all team-scoped expert copies for a team."""
    teams = _load_teams()
    if team_name not in teams:
        return
    for expert_name in teams[team_name].get("experts", []):
        _undeploy_team_expert(team_name, expert_name)


def _generate_team_lead(
    team_name: str,
    description: str,
    roster: list[dict[str, str]],
) -> bool:
    """AI-generate a team lead agent definition.

    Runs the provider's analysis engine to create teams/{team_name}/lead.md.

    Returns True on success.
    """
    from hivemind_cli.templates import team_lead_prompt

    team_dir = TEAMS_DIR / team_name
    prompt = team_lead_prompt(team_name, description, roster, team_dir)

    provider = _get_provider()
    cmd = provider.build_analysis_command(extra_dirs=[team_dir])

    proc = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        capture_output=True,
    )

    lead_path = team_dir / "lead.md"
    return lead_path.exists() and lead_path.stat().st_size > 0


def create_team(
    name: str,
    description: str,
    experts: list[str],
    max_roster: int | None = None,
    skip_analysis: bool = False,
) -> dict:
    """Create a new team.

    Args:
        name: Team name
        description: Team description
        experts: List of expert names for the roster
        max_roster: Optional roster size limit
        skip_analysis: Skip AI generation of team lead (use template directly)

    Returns:
        dict with keys: success (bool), error (str | None)
    """
    teams = _load_teams()
    if name in teams:
        return {"success": False, "error": f"Team '{name}' already exists"}

    # Validate experts exist
    config = _load_config()
    enabled = set(config.get("enabled", []))
    all_experts = set(_expert_names())
    for expert in experts:
        if expert not in all_experts:
            return {"success": False, "error": f"Expert '{expert}' does not exist"}

    # Check roster limit
    defaults = config.get("defaults", {})
    limit = max_roster or defaults.get("team_max_roster", 8)
    if len(experts) > limit:
        return {
            "success": False,
            "error": f"Roster size {len(experts)} exceeds limit {limit}",
        }

    # Create team directory
    team_dir = TEAMS_DIR / name
    team_dir.mkdir(parents=True, exist_ok=True)
    (team_dir / "experts").mkdir(exist_ok=True)

    # Pre-populate context files
    expert_list = "\n".join(f"- **{e}**" for e in experts)
    (team_dir / "general.md").write_text(
        f"# {name}\n\n{description}\n\n## Experts\n\n{expert_list}\n"
    )
    (team_dir / "private.md").write_text(
        f"# {name} — Private Notes\n\nTeam lead's private notes. Not shared with experts.\n"
    )

    # Build roster info
    roster = []
    for expert_name in experts:
        expert_dir = _get_expert_dir(expert_name)
        head_agent = expert_dir / "HEAD" / "agent.md"
        desc = ""
        if head_agent.exists():
            desc = extract_description(strip_frontmatter(head_agent.read_text()))
        roster.append({"name": expert_name, "description": desc})

    # Generate or template the lead
    if skip_analysis:
        from hivemind_cli.templates import team_lead_template

        lead_body = team_lead_template(name, description, roster)
        (team_dir / "lead.md").write_text(lead_body)
    else:
        _generate_team_lead(name, description, roster)

    # Fallback: if AI generation didn't produce lead.md, use template
    if not (team_dir / "lead.md").exists():
        from hivemind_cli.templates import team_lead_template

        lead_body = team_lead_template(name, description, roster)
        (team_dir / "lead.md").write_text(lead_body)

    # Save to hivemind.json
    team_data: dict = {
        "description": description,
        "experts": experts,
        "max_roster": limit,
    }
    teams[name] = team_data
    _save_teams(teams)

    # Deploy
    _deploy_team_lead(name)
    _deploy_team_experts(name)
    _update_librarian()

    return {"success": True}


def delete_team(name: str) -> dict:
    """Delete a team and all its deployed agents.

    Returns:
        dict with keys: success (bool), error (str | None)
    """
    teams = _load_teams()
    if name not in teams:
        return {"success": False, "error": f"Team '{name}' does not exist"}

    # Undeploy
    _undeploy_team_lead(name)
    _undeploy_team_experts(name)

    # Remove from projects that reference this team
    projects = _load_projects()
    for proj_name, proj in projects.items():
        if name in proj.get("teams", []):
            proj["teams"].remove(name)
    _save_projects(projects)

    # Remove team directory
    team_dir = TEAMS_DIR / name
    if team_dir.exists():
        import shutil

        shutil.rmtree(team_dir)

    # Remove from hivemind.json
    del teams[name]
    _save_teams(teams)

    _update_librarian()
    return {"success": True}


def add_expert_to_team(team_name: str, expert_name: str) -> dict:
    """Add an expert to a team's roster.

    Returns:
        dict with keys: success (bool), error (str | None)
    """
    teams = _load_teams()
    if team_name not in teams:
        return {"success": False, "error": f"Team '{team_name}' does not exist"}

    team = teams[team_name]
    experts = team.get("experts", [])

    if expert_name in experts:
        return {"success": False, "error": f"Expert '{expert_name}' already on team"}

    # Validate expert exists
    all_experts = set(_expert_names())
    if expert_name not in all_experts:
        return {"success": False, "error": f"Expert '{expert_name}' does not exist"}

    # Check roster limit
    limit = team.get("max_roster", 8)
    if len(experts) >= limit:
        return {
            "success": False,
            "error": f"Roster full ({len(experts)}/{limit})",
        }

    experts.append(expert_name)
    team["experts"] = experts
    _save_teams(teams)

    # Deploy team-scoped copy
    _deploy_team_expert(team_name, expert_name)
    _update_librarian()

    return {"success": True}


def remove_expert_from_team(team_name: str, expert_name: str) -> dict:
    """Remove an expert from a team's roster.

    Returns:
        dict with keys: success (bool), error (str | None)
    """
    teams = _load_teams()
    if team_name not in teams:
        return {"success": False, "error": f"Team '{team_name}' does not exist"}

    team = teams[team_name]
    experts = team.get("experts", [])

    if expert_name not in experts:
        return {"success": False, "error": f"Expert '{expert_name}' not on team"}

    experts.remove(expert_name)
    team["experts"] = experts
    _save_teams(teams)

    # Undeploy team-scoped copy
    _undeploy_team_expert(team_name, expert_name)

    # Remove per-expert context file if it exists
    expert_override = TEAMS_DIR / team_name / "experts" / f"{expert_name}.md"
    if expert_override.exists():
        expert_override.unlink()

    _update_librarian()
    return {"success": True}


# --- Project Operations ---


def _deploy_project_lead(project_name: str) -> bool:
    """Deploy project lead agent file with provider-specific frontmatter.

    Reads projects/{project_name}/lead.md, applies frontmatter, writes to
    agents/project-lead-{project_name}.md.

    Returns False if lead.md doesn't exist.
    """
    lead_md = PROJECTS_DIR / project_name / "lead.md"
    if not lead_md.exists():
        return False

    provider = _get_provider()
    body = strip_frontmatter(lead_md.read_text())
    description = extract_description(body)

    content = provider.format_lead_md(
        f"project-lead-{project_name}", description, body
    )

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    agent_file = AGENTS_DIR / f"project-lead-{project_name}.md"
    if agent_file.is_symlink():
        agent_file.unlink()
    agent_file.write_text(content)
    return True


def _undeploy_project_lead(project_name: str) -> None:
    """Remove agents/project-lead-{project_name}.md if it exists."""
    agent_file = AGENTS_DIR / f"project-lead-{project_name}.md"
    if agent_file.is_symlink() or agent_file.exists():
        agent_file.unlink()


def _generate_project_lead(
    project_name: str,
    description: str,
    teams: list[dict[str, str]],
    repos: list[str],
    objectives: list[str],
) -> bool:
    """AI-generate a project lead agent definition.

    Returns True on success.
    """
    from hivemind_cli.templates import project_lead_prompt

    project_dir = PROJECTS_DIR / project_name
    prompt = project_lead_prompt(
        project_name, description, teams, repos, objectives, project_dir
    )

    provider = _get_provider()
    cmd = provider.build_analysis_command(extra_dirs=[project_dir])

    proc = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        capture_output=True,
    )

    lead_path = project_dir / "lead.md"
    return lead_path.exists() and lead_path.stat().st_size > 0


def create_project(
    name: str,
    description: str,
    teams_list: list[str],
    repos: list[str],
    objectives: list[str],
    skip_analysis: bool = False,
) -> dict:
    """Create a new project.

    Returns:
        dict with keys: success (bool), error (str | None)
    """
    projects = _load_projects()
    if name in projects:
        return {"success": False, "error": f"Project '{name}' already exists"}

    # Validate teams exist
    all_teams = _load_teams()
    for team_name in teams_list:
        if team_name not in all_teams:
            return {"success": False, "error": f"Team '{team_name}' does not exist"}

    # Create project directory
    project_dir = PROJECTS_DIR / name
    project_dir.mkdir(parents=True, exist_ok=True)

    # Pre-populate context files
    teams_str = "\n".join(f"- **{t}**" for t in teams_list) if teams_list else "- (none)"
    repos_str = "\n".join(f"- {r}" for r in repos) if repos else "- (none)"
    obj_str = "\n".join(f"- {o}" for o in objectives) if objectives else "- (none)"

    (project_dir / "overview.md").write_text(
        f"# {name}\n\n{description}\n\n"
        f"## Teams\n\n{teams_str}\n\n"
        f"## Repos\n\n{repos_str}\n\n"
        f"## Objectives\n\n{obj_str}\n"
    )
    (project_dir / "context.md").write_text(
        f"# {name} — Context\n\nProject decisions, progress notes, and todos.\n"
    )
    (project_dir / "project.md").write_text(
        f"## Active Project: {name}\n\nProject lead: `project-lead-{name}`\n"
    )

    # Build teams info
    teams_info = []
    for team_name in teams_list:
        team_desc = all_teams[team_name].get("description", "")
        teams_info.append({"name": team_name, "description": team_desc})

    # Generate or template the lead
    if skip_analysis:
        from hivemind_cli.templates import project_lead_template

        lead_body = project_lead_template(
            name, description, teams_info, repos, objectives
        )
        (project_dir / "lead.md").write_text(lead_body)
    else:
        _generate_project_lead(name, description, teams_info, repos, objectives)

    # Fallback
    if not (project_dir / "lead.md").exists():
        from hivemind_cli.templates import project_lead_template

        lead_body = project_lead_template(
            name, description, teams_info, repos, objectives
        )
        (project_dir / "lead.md").write_text(lead_body)

    # Save to hivemind.json
    project_data: dict = {
        "description": description,
        "teams": teams_list,
        "repos": repos,
        "objectives": objectives,
    }
    projects[name] = project_data
    _save_projects(projects)

    # Deploy
    _deploy_project_lead(name)
    _update_librarian()

    return {"success": True}


def delete_project(name: str) -> dict:
    """Delete a project.

    Returns:
        dict with keys: success (bool), error (str | None)
    """
    projects = _load_projects()
    if name not in projects:
        return {"success": False, "error": f"Project '{name}' does not exist"}

    # Clear active project if this is it
    config = _load_config()
    if config.get("active_project") == name:
        config["active_project"] = None
        _save_config(config)

    _undeploy_project_lead(name)

    # Remove project directory
    project_dir = PROJECTS_DIR / name
    if project_dir.exists():
        import shutil

        shutil.rmtree(project_dir)

    del projects[name]
    _save_projects(projects)

    _update_librarian()
    _regenerate_hivemind_md()
    return {"success": True}


def add_team_to_project(project_name: str, team_name: str) -> dict:
    """Add a team to a project.

    Returns:
        dict with keys: success (bool), error (str | None)
    """
    projects = _load_projects()
    if project_name not in projects:
        return {"success": False, "error": f"Project '{project_name}' does not exist"}

    teams = _load_teams()
    if team_name not in teams:
        return {"success": False, "error": f"Team '{team_name}' does not exist"}

    project = projects[project_name]
    project_teams = project.get("teams", [])
    if team_name in project_teams:
        return {"success": False, "error": f"Team '{team_name}' already on project"}

    project_teams.append(team_name)
    project["teams"] = project_teams
    _save_projects(projects)

    _update_librarian()
    return {"success": True}


def remove_team_from_project(project_name: str, team_name: str) -> dict:
    """Remove a team from a project.

    Returns:
        dict with keys: success (bool), error (str | None)
    """
    projects = _load_projects()
    if project_name not in projects:
        return {"success": False, "error": f"Project '{project_name}' does not exist"}

    project = projects[project_name]
    project_teams = project.get("teams", [])
    if team_name not in project_teams:
        return {"success": False, "error": f"Team '{team_name}' not on project"}

    project_teams.remove(team_name)
    project["teams"] = project_teams
    _save_projects(projects)

    _update_librarian()
    return {"success": True}


def add_repo_to_project(project_name: str, repo_name: str) -> dict:
    """Add a repo to a project.

    Returns:
        dict with keys: success (bool), error (str | None)
    """
    projects = _load_projects()
    if project_name not in projects:
        return {"success": False, "error": f"Project '{project_name}' does not exist"}

    project = projects[project_name]
    project_repos = project.get("repos", [])
    if repo_name in project_repos:
        return {"success": False, "error": f"Repo '{repo_name}' already on project"}

    project_repos.append(repo_name)
    project["repos"] = project_repos
    _save_projects(projects)

    return {"success": True}


def set_active_project(name: str) -> dict:
    """Set the active project and regenerate HIVEMIND.md.

    Returns:
        dict with keys: success (bool), error (str | None)
    """
    projects = _load_projects()
    if name not in projects:
        return {"success": False, "error": f"Project '{name}' does not exist"}

    config = _load_config()
    config["active_project"] = name
    _save_config(config)

    _regenerate_hivemind_md()
    return {"success": True}


def clear_active_project() -> dict:
    """Clear the active project and regenerate HIVEMIND.md.

    Returns:
        dict with keys: success (bool)
    """
    config = _load_config()
    config["active_project"] = None
    _save_config(config)

    _regenerate_hivemind_md()
    return {"success": True}


def switch_provider(provider_name: str) -> dict:
    """Switch active provider.

    Args:
        provider_name: Name of provider to switch to (e.g. "claude", "opencode")

    Returns:
        dict with keys: success (bool), error (str | None), old_provider (str), new_provider (str)
    """
    from hivemind_cli.providers import PROVIDER_CLASSES

    if provider_name not in PROVIDER_CLASSES:
        available = ", ".join(PROVIDER_CLASSES)
        return {
            "success": False,
            "error": f"Unknown provider '{provider_name}'. Available: {available}",
        }

    config = _load_config()
    old_provider = config.get("active_provider", "")

    if old_provider == provider_name:
        return {
            "success": True,
            "old_provider": old_provider,
            "new_provider": provider_name,
            "already_active": True,
        }

    config["active_provider"] = provider_name
    _save_config(config)

    return {
        "success": True,
        "old_provider": old_provider,
        "new_provider": provider_name,
    }
