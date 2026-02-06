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


def _expert_names() -> list[str]:
    """List all expert names from experts/ directory."""
    if not EXPERTS_DIR.exists():
        return []
    return sorted(d.name for d in EXPERTS_DIR.iterdir() if d.is_dir())


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
    expert_dir = EXPERTS_DIR / name
    head_agent = expert_dir / "HEAD" / "agent.md"

    if not head_agent.exists():
        return False

    agent_link = AGENTS_DIR / f"expert-{name}.md"
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
                "--depth",
                "1",
                remote,
                str(repo_dir),
            ],
            check=True,
            stdout=subprocess.DEVNULL if silent else None,
            stderr=subprocess.DEVNULL if silent else None,
        )
    else:
        subprocess.run(
            ["git", "clone", "--progress" if not silent else "--quiet", "--depth", "1", remote, str(repo_dir)],
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
    """Regenerate agents/librarian.md from all experts with valid HEAD/agent.md."""
    from hivemind_cli.templates import librarian_template

    entries: list[str] = []

    for expert_dir in sorted(EXPERTS_DIR.iterdir()):
        if not expert_dir.is_dir():
            continue
        name = expert_dir.name
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

    if not entries:
        return

    catalog = "\n\n---\n\n".join(entries)

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
    repos = _load_repos()

    if name not in repos:
        return {"success": False, "error": f"{name} not in repos.json"}

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

    expert_dir = EXPERTS_DIR / name
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

        # Update repos.json
        repos[name]["commit"] = new_commit
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

    repos = _load_repos()

    if name not in repos:
        return {"success": False, "error": f"{name} not in repos.json"}

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

        expert_dir = EXPERTS_DIR / name
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


def enable_expert(name: str) -> dict:
    """Enable an expert (clone repo + create agent symlink).

    Returns:
        dict with keys: success (bool), already_enabled (bool), error (str | None)
    """
    if not (EXPERTS_DIR / name).is_dir():
        return {"success": False, "error": f"Expert '{name}' not found in experts/"}

    config = _load_config()
    already_enabled = name in config["enabled"]

    if not already_enabled:
        config["enabled"].append(name)
        if name in config["disabled"]:
            config["disabled"].remove(name)
        _save_config(config)

    repos = _load_repos()
    if not _clone_repo(name, repos, silent=True):
        return {"success": False, "error": "Failed to clone repository"}

    _link_agent(name)

    return {"success": True, "already_enabled": already_enabled}


def disable_expert(name: str) -> dict:
    """Disable an expert (remove agent symlink).

    Returns:
        dict with keys: success (bool), already_disabled (bool), error (str | None)
    """
    if not (EXPERTS_DIR / name).is_dir():
        return {"success": False, "error": f"Expert '{name}' not found in experts/"}

    config = _load_config()
    already_disabled = name not in config["enabled"] and name in config["disabled"]

    if not already_disabled:
        if name in config["enabled"]:
            config["enabled"].remove(name)
        if name not in config["disabled"]:
            config["disabled"].append(name)
        _save_config(config)

    _unlink_agent(name)

    return {"success": True, "already_disabled": already_disabled}
