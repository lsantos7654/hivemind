"""Git subprocess operations for hivemind."""

from __future__ import annotations

import asyncio
import contextlib
import shutil
import time
from pathlib import Path
from uuid import uuid4

from hivemind.config import (
    GIT_CLONE_TIMEOUT,
    GIT_FETCH_TIMEOUT,
    GIT_LOCAL_TIMEOUT,
    REPOS_DIR,
    STAGING_DIR,
    ensure_repos_link,
)
from hivemind.constants import DESCRIPTION_FILENAME, EXPERTISE_FILENAME
from hivemind.models import StagingResult

__all__ = [
    "cleanup_log_files",
    "clone_from_remote",
    "commit_analysis_results",
    "create_staging_dir",
    "read_analysis_error",
    "resolve_commit_provenance",
    "resolve_default_branch",
    "resolve_latest_commit",
    "resolve_ref",
    "revert_checkout",
    "stage_for_analysis",
]


async def clone_from_remote(
    name: str,
    remote: str,
    *,
    commit: str = "",
    ref_name: str = "",
    silent: bool = False,
) -> bool:
    """Clone ``remote`` into ``REPOS_DIR/<name>`` if not already present.

    Returns True when the repo is available on disk afterwards.
    """
    ensure_repos_link()

    repo_dir = REPOS_DIR / name
    if repo_dir.is_dir():
        return True  # already cloned

    stdout = asyncio.subprocess.DEVNULL if silent else None
    stderr = asyncio.subprocess.DEVNULL if silent else None

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


async def resolve_commit_provenance(repo_dir: Path, commit: str) -> str | None:
    """Resolve a commit's most-meaningful ref name.

    Tries ``git describe --tags --exact-match <commit>`` first — when
    the commit IS at a tagged release, that tag is the most useful
    catalog identifier (lets ``/hivemind_sync`` compare against project
    pins like ``8.5.1`` cleanly). Falls back to
    :func:`resolve_default_branch` when the commit isn't at a tag (the
    common case when an expert was added at default-branch HEAD without
    ``--ref``). Returns ``None`` if neither resolution succeeds.
    """
    proc = await asyncio.create_subprocess_exec(
        "git",
        "describe",
        "--tags",
        "--exact-match",
        commit,
        cwd=str(repo_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=GIT_LOCAL_TIMEOUT)
    except (TimeoutError, OSError):
        stdout = b""
    if proc.returncode == 0:
        tag = stdout.decode().strip()
        if tag:
            return tag
    return await resolve_default_branch(repo_dir)


async def resolve_default_branch(repo_dir: Path) -> str | None:
    """Resolve the upstream default branch name (e.g. ``main``, ``master``).

    Reads ``refs/remotes/origin/HEAD`` (a symbolic ref set by
    ``git clone`` when origin reports its default branch) and strips the
    ``origin/`` prefix. Returns ``None`` if the symbolic ref isn't set
    (offline clone, shallow clone without fetch, or detached-head
    weirdness).

    Used by ``prep_create_expert`` to populate ``ref_name`` for adds that
    didn't pass an explicit ``--ref`` — ensures the catalog always
    records provenance ("we cloned default-branch HEAD") rather than
    leaving ``ref_name=""`` and forcing later consumers to improvise via
    ``git describe``.
    """
    proc = await asyncio.create_subprocess_exec(
        "git",
        "symbolic-ref",
        "--short",
        "refs/remotes/origin/HEAD",
        cwd=str(repo_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=GIT_LOCAL_TIMEOUT)
    except (TimeoutError, OSError):
        return None
    if proc.returncode != 0:
        return None
    output = stdout.decode().strip()
    output = output.removeprefix("origin/")
    return output or None


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


async def resolve_ref(repo_dir: Path, ref: str, *, fetch: bool = True) -> str | None:
    """Resolve a ref (tag, branch, full or short SHA) to a full commit SHA.

    When ``fetch`` is True, fetches tags first so freshly-pushed tags resolve
    even if the local clone is stale. Network failures during fetch are
    swallowed — local refs may still resolve. The ``^{commit}`` suffix
    dereferences annotated tags to their underlying commit object. Returns
    the full SHA on success, ``None`` on failure.
    """
    if fetch:
        proc = await asyncio.create_subprocess_exec(
            "git",
            "fetch",
            "--tags",
            "--quiet",
            cwd=str(repo_dir),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        with contextlib.suppress(TimeoutError, OSError):
            await asyncio.wait_for(proc.wait(), timeout=GIT_FETCH_TIMEOUT)

    proc = await asyncio.create_subprocess_exec(
        "git",
        "rev-parse",
        "--verify",
        f"{ref}^{{commit}}",
        cwd=str(repo_dir),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=GIT_LOCAL_TIMEOUT)
    except (TimeoutError, OSError):
        return None
    if proc.returncode != 0:
        return None
    sha = stdout.decode().strip()
    return sha or None


_STALE_STAGING_HOURS = 6


def _cleanup_stale_staging() -> None:
    """Remove staging subdirectories older than _STALE_STAGING_HOURS."""
    if not STAGING_DIR.is_dir():
        return
    cutoff = time.time() - _STALE_STAGING_HOURS * 3600
    for child in STAGING_DIR.iterdir():
        if child.is_dir():
            try:
                if child.stat().st_mtime < cutoff:
                    shutil.rmtree(child)
            except OSError:
                pass


def create_staging_dir(name: str) -> Path:
    """Create a unique subdirectory under STAGING_DIR for an operation."""
    _cleanup_stale_staging()
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    staging = STAGING_DIR / f"{name}-{uuid4().hex[:12]}"
    staging.mkdir()
    return staging


async def stage_for_analysis(
    name: str,
    new_commit: str,
    expert_dir: Path,
    old_commit: str | None,
    repo_dir: Path,
) -> StagingResult:
    """Create staging directory, preserve description.md + expertise.md, and checkout new commit."""
    tmpdir = str(create_staging_dir(name))
    staged_path = Path(tmpdir) / "expert"
    staged_path.mkdir()
    tmp_commit_dir = staged_path / new_commit
    tmp_commit_dir.mkdir()

    if old_commit:
        for fname in (DESCRIPTION_FILENAME, EXPERTISE_FILENAME):
            old_file = expert_dir / old_commit / fname
            if old_file.is_file():
                shutil.copy2(old_file, tmp_commit_dir / fname)

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


def read_analysis_error(returncode: int, stderr_path: Path, stdout_path: Path) -> str:
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


def commit_analysis_results(tmp_commit_dir: Path, expert_dir: Path, commit: str) -> None:
    """Move staged analysis files to final location and update HEAD symlink."""
    final_commit_dir = expert_dir / commit
    final_commit_dir.mkdir(parents=True, exist_ok=True)

    for f in tmp_commit_dir.iterdir():
        if f.is_file():
            shutil.move(str(f), str(final_commit_dir / f.name))

    head_link = expert_dir / "HEAD"
    if head_link.is_symlink():
        head_link.unlink()
    head_link.symlink_to(commit)


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
