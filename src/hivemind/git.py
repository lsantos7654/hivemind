"""Git subprocess operations for hivemind."""

from __future__ import annotations

import asyncio
import contextlib
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from hivemind.config import (
    GIT_CLONE_TIMEOUT,
    GIT_LOCAL_TIMEOUT,
    REPOS_DIR,
    ensure_repos_link,
    save_private_repos,
    save_repos,
)
from hivemind.models import StagingResult

if TYPE_CHECKING:
    from hivemind.models import RepoEntry

__all__ = [
    "cleanup_log_files",
    "clone_repo",
    "commit_analysis_results",
    "read_analysis_error",
    "resolve_latest_commit",
    "revert_checkout",
    "save_commit_to_repos",
    "stage_for_analysis",
]


async def clone_repo(name: str, repos: dict[str, RepoEntry], *, silent: bool = False) -> bool:
    """Clone a repo to cache repos dir if not already present.

    Args:
        name: Expert name
        repos: repos data
        silent: If True, suppress output (for TUI usage)

    Returns:
        True if repo is available (already cloned or newly cloned)
    """
    if name not in repos:
        return False

    ensure_repos_link()

    repo_dir = REPOS_DIR / name
    if repo_dir.is_dir():
        return True  # Already cloned

    repo = repos[name]
    remote = repo.remote
    commit = repo.commit
    ref_name = repo.ref_name

    stdout = asyncio.subprocess.DEVNULL if silent else None
    stderr = asyncio.subprocess.DEVNULL if silent else None

    # Determine clone command
    if commit:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--quiet" if silent else "--progress",
            remote,
            str(repo_dir),
            stdout=stdout,
            stderr=stderr,
        )
        await asyncio.wait_for(proc.wait(), timeout=GIT_CLONE_TIMEOUT)
        if proc.returncode != 0:
            return False

        proc = await asyncio.create_subprocess_exec(
            "git",
            "checkout",
            "--quiet",
            commit,
            cwd=str(repo_dir),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await asyncio.wait_for(proc.wait(), timeout=GIT_LOCAL_TIMEOUT)
        if proc.returncode != 0:
            return False
    elif ref_name:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--quiet" if silent else "--progress",
            "--branch",
            ref_name,
            remote,
            str(repo_dir),
            stdout=stdout,
            stderr=stderr,
        )
        await asyncio.wait_for(proc.wait(), timeout=GIT_CLONE_TIMEOUT)
        if proc.returncode != 0:
            return False
    else:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--quiet" if silent else "--progress",
            remote,
            str(repo_dir),
            stdout=stdout,
            stderr=stderr,
        )
        await asyncio.wait_for(proc.wait(), timeout=GIT_CLONE_TIMEOUT)
        if proc.returncode != 0:
            return False

    return True


async def resolve_latest_commit(repo_dir: Path) -> str | None:
    """Resolve the latest commit from origin/HEAD, origin/main, or origin/master."""
    for ref in ["origin/HEAD", "origin/main", "origin/master"]:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "rev-parse",
            ref,
            cwd=str(repo_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0:
            return stdout.decode().strip()
    return None


async def stage_for_analysis(
    name: str,
    new_commit: str,
    expert_dir: Path,
    old_commit: str | None,
    repo_dir: Path,
    prefix: str = "hivemind-update",
) -> StagingResult:
    """Create temp directory, copy baseline files, and checkout new commit.

    Returns (tmpdir, staged_path, tmp_commit_dir).
    """
    tmpdir = tempfile.mkdtemp(prefix=f"{prefix}-{name}-")
    staged_path = Path(tmpdir) / "expert"
    staged_path.mkdir()
    tmp_commit_dir = staged_path / new_commit
    tmp_commit_dir.mkdir()

    # Copy baseline files from previous version
    if old_commit:
        old_dir = expert_dir / old_commit
        if old_dir.is_dir():
            for f in old_dir.iterdir():
                if f.is_file():
                    shutil.copy2(f, tmp_commit_dir / f.name)

    # Checkout the target commit
    proc = await asyncio.create_subprocess_exec(
        "git",
        "checkout",
        "--quiet",
        new_commit,
        cwd=str(repo_dir),
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
    )
    await asyncio.wait_for(proc.wait(), timeout=GIT_LOCAL_TIMEOUT)
    if proc.returncode != 0:
        msg = f"Failed to checkout {new_commit}"
        raise RuntimeError(msg)

    return StagingResult(tmpdir=tmpdir, staged_path=staged_path, commit_dir=tmp_commit_dir)


def read_analysis_error(
    returncode: int,
    stderr_path: Path,
    stdout_path: Path,
) -> str:
    """Read error details from analysis subprocess output files."""
    error_msg = f"AI analysis failed (exit code {returncode})"
    try:
        stderr_content = stderr_path.read_text(encoding="utf-8")
        stdout_content = stdout_path.read_text(encoding="utf-8")

        if stderr_content.strip():
            error_msg += f"\nStderr: {stderr_content[-500:]}"
        if stdout_content.strip():
            error_msg += f"\nStdout: {stdout_content[-500:]}"

        if not stderr_content.strip() and not stdout_content.strip():
            error_msg += "\nNo output captured."
    except Exception as e:
        error_msg += f"\nCould not read output: {e}"
    return error_msg


def cleanup_log_files(*paths: Path) -> None:
    """Remove temporary log files, ignoring errors."""
    for p in paths:
        with contextlib.suppress(Exception):
            if p.exists():
                p.unlink()


def commit_analysis_results(
    tmp_commit_dir: Path,
    expert_dir: Path,
    commit: str,
) -> None:
    """Move staged analysis files to final location and update HEAD symlink."""
    final_commit_dir = expert_dir / commit
    final_commit_dir.mkdir(parents=True, exist_ok=True)

    for f in tmp_commit_dir.iterdir():
        if f.is_file():
            shutil.move(str(f), str(final_commit_dir / f.name))

    # Update HEAD symlink
    head_link = expert_dir / "HEAD"
    if head_link.is_symlink():
        head_link.unlink()
    head_link.symlink_to(commit)


def save_commit_to_repos(
    name: str,
    commit: str,
    repos: dict[str, RepoEntry],
    is_private: bool,
) -> None:
    """Update the commit hash in repos config."""
    repos[name].commit = commit
    if is_private:
        save_private_repos(repos)
    else:
        save_repos(repos)


async def revert_checkout(repo_dir: Path, old_commit: str | None) -> None:
    """Revert git checkout to old commit on failure."""
    if old_commit:
        with contextlib.suppress(Exception):
            proc = await asyncio.create_subprocess_exec(
                "git",
                "checkout",
                "--quiet",
                old_commit,
                cwd=str(repo_dir),
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await asyncio.wait_for(proc.wait(), timeout=GIT_LOCAL_TIMEOUT)
