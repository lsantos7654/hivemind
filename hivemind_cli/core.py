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
CLAUDE_DIR = Path.home() / ".claude"
CACHE_DIR = Path.home() / ".cache" / "hivemind"
REPOS_DIR = CACHE_DIR / "repos"
REPOS_LINK = HIVEMIND_ROOT / "repos"
REPOS_JSON = HIVEMIND_ROOT / "repos.json"
CONFIG_JSON = HIVEMIND_ROOT / "config.json"
AGENTS_DIR = HIVEMIND_ROOT / "agents"
EXPERTS_DIR = HIVEMIND_ROOT / "experts"
COMMANDS_DIR = HIVEMIND_ROOT / "commands"
CLAUDE_MD = HIVEMIND_ROOT / "CLAUDE.md"
PRIVATE_EXPERTS_DIR = HIVEMIND_ROOT / "private-experts"
PRIVATE_REPOS_JSON = HIVEMIND_ROOT / "private-repos.json"


# --- Helper Functions ---


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def _save_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2) + "\n")


def _load_config() -> dict:
    default = {"enabled": [], "disabled": []}
    if not CONFIG_JSON.exists():
        return default
    data = _load_json(CONFIG_JSON)
    data.setdefault("enabled", [])
    data.setdefault("disabled", [])
    return data


def _save_config(config: dict) -> None:
    _save_json(CONFIG_JSON, config)


def _load_repos() -> dict:
    return _load_json(REPOS_JSON)


def _save_repos(repos: dict) -> None:
    _save_json(REPOS_JSON, repos)


def _load_private_repos() -> dict:
    """Load private-repos.json."""
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


def _link_agent(name: str) -> bool:
    """Create agents/expert-<name>.md → ../experts/<name>/HEAD/agent.md.

    Returns False if HEAD/agent.md doesn't exist.
    """
    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    expert_dir = _get_expert_dir(name)
    head_agent = expert_dir / "HEAD" / "agent.md"

    if not head_agent.exists():
        return False

    agent_link = AGENTS_DIR / f"expert-{name}.md"
    # Determine correct link target based on private/public
    if _is_private_expert(name):
        link_target = Path("..") / "private-experts" / name / "HEAD" / "agent.md"
    else:
        link_target = Path("..") / "experts" / name / "HEAD" / "agent.md"

    if agent_link.is_symlink():
        if os.readlink(agent_link) == str(link_target):
            return True  # Already correct
        agent_link.unlink()
    elif agent_link.exists():
        agent_link.unlink()

    agent_link.symlink_to(link_target)
    return True


def _unlink_agent(name: str) -> None:
    """Remove agents/expert-<name>.md if it exists."""
    agent_link = AGENTS_DIR / f"expert-{name}.md"
    if agent_link.is_symlink() or agent_link.exists():
        agent_link.unlink()


def _link_expert(name: str) -> bool:
    """Create ~/.claude/experts/<name> → {experts,private-experts}/<name>/.

    Returns True if symlink was created/updated, False if expert doesn't exist.
    """
    CLAUDE_EXPERTS_DIR = CLAUDE_DIR / "experts"
    CLAUDE_EXPERTS_DIR.mkdir(parents=True, exist_ok=True)

    source_dir = _get_expert_dir(name)
    if not source_dir.exists():
        return False

    expert_link = CLAUDE_EXPERTS_DIR / name

    # Check if already correct
    if expert_link.is_symlink():
        if expert_link.resolve() == source_dir.resolve():
            return True  # Already correct
        expert_link.unlink()
    elif expert_link.exists():
        # Remove non-symlink file/directory
        if expert_link.is_dir():
            shutil.rmtree(expert_link)
        else:
            expert_link.unlink()

    expert_link.symlink_to(source_dir)
    return True


def _unlink_expert(name: str) -> None:
    """Remove ~/.claude/experts/<name> if it exists."""
    expert_link = CLAUDE_DIR / "experts" / name
    if expert_link.is_symlink() or expert_link.exists():
        if expert_link.is_dir() and not expert_link.is_symlink():
            shutil.rmtree(expert_link)
        else:
            expert_link.unlink()


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
            ["git", "clone", "--progress" if not silent else "--quiet", remote, str(repo_dir)],
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
            ["git", "clone", "--progress" if not silent else "--quiet", remote, str(repo_dir)],
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
    """Run AI analysis on a repo via `claude -p`.

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

    cmd = [
        "claude",
        "-p",
        "--verbose",
        "--allowedTools",
        "Read,Grep,Glob,Bash,Write",
        "--model",
        "sonnet",
        "--add-dir",
        str(repo_dir),
        "--add-dir",
        str(expert_dir),
        "--dangerously-skip-permissions",
    ]

    if background:
        # Create temp files for stderr and stdout - use NamedTemporaryFile
        stderr_file = tempfile.NamedTemporaryFile(
            mode='w',
            prefix=f"hivemind-{name}-stderr-",
            suffix=".log",
            delete=False  # Don't auto-delete, we'll read it later
        )
        stdout_file = tempfile.NamedTemporaryFile(
            mode='w',
            prefix=f"hivemind-{name}-stdout-",
            suffix=".log",
            delete=False  # Don't auto-delete, we'll read it later
        )
        stderr_path = Path(stderr_file.name)
        stdout_path = Path(stdout_file.name)

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=stdout_file,
            stderr=stderr_file,
        )
        proc.stdin.write(prompt.encode())
        proc.stdin.close()
        # Don't close files yet - process needs them
        return proc, stderr_path, stdout_path, stderr_file, stdout_file
    else:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        _, stderr = proc.communicate(input=prompt.encode())
        if proc.returncode != 0 and stderr:
            # Print stderr for debugging
            print(f"Claude analysis error: {stderr.decode()}", file=sys.stderr)
        return proc.returncode == 0


def _update_librarian() -> None:
    """Regenerate agents/librarian.md from enabled experts with valid HEAD/agent.md."""
    from hivemind_cli.templates import librarian_template

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

            # Parse description from frontmatter
            description = ""
            try:
                text = agent_md.read_text()
                parts = text.split("---", 2)
                if len(parts) >= 3:
                    for line in parts[1].splitlines():
                        if line.startswith("description:"):
                            description = line[len("description:") :].strip()
                            break
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
    catalog = "\n\n---\n\n".join(entries) if entries else "No experts are currently enabled."

    # Use centralized librarian template
    content = librarian_template(catalog)

    AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    (AGENTS_DIR / "librarian.md").write_text(content)


# --- Core Operations ---


def update_expert(
    name: str,
    on_progress: ProgressCallback | None = None,
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
        on_progress(ProgressInfo(name, UpdatePhase.FETCHING, "Fetching latest commits..."))

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

        # Phase 3: AI Analysis (long-running, need to poll)
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
        proc, stderr_path, stdout_path, stderr_file, stdout_file = _analyze_repo(name, new_commit, repo_dir, tmp_expert, is_update=True, background=True)

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

        # Phase 4: Commit results
        if on_progress:
            on_progress(ProgressInfo(name, UpdatePhase.COMMITTING, "Committing changes..."))

        # Move staged files to final location
        final_commit_dir = expert_dir / new_commit
        final_commit_dir.mkdir(parents=True, exist_ok=True)

        for f in tmp_commit_dir.iterdir():
            if f.is_file():
                shutil.move(str(f), str(final_commit_dir / f.name))

        # Update HEAD symlink
        if on_progress:
            on_progress(ProgressInfo(name, UpdatePhase.UPDATING_HEAD, "Updating HEAD symlink..."))

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
            on_progress(ProgressInfo(name, UpdatePhase.CLONING, "Cloning repository..."))

        if not _clone_repo(name, repos, silent=True):
            return {"success": False, "error": "Failed to clone repository"}

        repo_dir = REPOS_DIR / name

        _check_cancellation(UpdatePhase.FETCHING)
        if on_progress:
            on_progress(ProgressInfo(name, UpdatePhase.FETCHING, "Fetching latest commits..."))

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
            mode='wb',
            prefix=f"hivemind-{name}-stderr-",
            suffix=".log",
            delete=False,
        )
        stdout_file = tempfile.NamedTemporaryFile(
            mode='wb',
            prefix=f"hivemind-{name}-stdout-",
            suffix=".log",
            delete=False,
        )
        stderr_path = Path(stderr_file.name)
        stdout_path = Path(stdout_file.name)

        cmd = [
            "claude",
            "-p",
            "--verbose",
            "--allowedTools",
            "Read,Grep,Glob,Bash,Write",
            "--model",
            "sonnet",
            "--add-dir",
            str(repo_dir),
            "--add-dir",
            str(staged_path),
            "--dangerously-skip-permissions",
        ]

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
            on_progress(ProgressInfo(name, UpdatePhase.COMMITTING, "Committing changes..."))

        # Move staged files to final location
        final_commit_dir = expert_dir / new_commit
        final_commit_dir.mkdir(parents=True, exist_ok=True)

        for f in tmp_commit_dir.iterdir():
            if f.is_file():
                shutil.move(str(f), str(final_commit_dir / f.name))

        # Update HEAD symlink (risky - let it complete)
        if on_progress:
            on_progress(ProgressInfo(name, UpdatePhase.UPDATING_HEAD, "Updating HEAD symlink..."))

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
            ["git", "tag", "-l", "--format=%(refname:short)|%(creatordate:short)|%(objectname)"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
        )

        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|')
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
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                parts = line.split('|', 2)
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
            return {"success": False, "error": f"Commit {target_commit[:12]} not found in repository"}

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
                mode='wb',
                prefix=f"hivemind-{name}-stderr-",
                suffix=".log",
                delete=False,
            )
            stdout_file = tempfile.NamedTemporaryFile(
                mode='wb',
                prefix=f"hivemind-{name}-stdout-",
                suffix=".log",
                delete=False,
            )
            stderr_path = Path(stderr_file.name)
            stdout_path = Path(stdout_file.name)

            cmd = [
                "claude",
                "-p",
                "--verbose",
                "--allowedTools",
                "Read,Grep,Glob,Bash,Write",
                "--model",
                "sonnet",
                "--add-dir",
                str(repo_dir),
                "--add-dir",
                str(staged_path),
                "--dangerously-skip-permissions",
            ]

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
            return {"success": False, "error": f"Failed to checkout commit in repo: {e}"}

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

        # Update agent symlink
        _link_agent(name)

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

    _link_agent(name)
    _link_expert(name)

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

    _unlink_agent(name)
    _unlink_expert(name)

    # Update librarian to reflect enabled experts
    _update_librarian()

    return {"success": True, "already_disabled": already_disabled}
