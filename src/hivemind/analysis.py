"""AI analysis orchestration for hivemind."""

from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from hivemind.config import get_active_provider
from hivemind.constants import AGENT_FILENAME, ANALYSIS_DOCS, PROCESS_TERMINATE_TIMEOUT
from hivemind.git import cleanup_log_files, read_analysis_error, revert_checkout
from hivemind.models import (
    AnalysisResult,
    CancellationToken,
    UpdatePhase,
    UpdateResult,
)

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

__all__ = [
    "expected_analysis_files",
    "handle_async_cancellation",
    "make_cancellation_checker",
    "run_async_analysis",
]


def expected_analysis_files(*, is_update: bool = False) -> list[str]:
    """Return the list of files an analysis run is expected to produce."""
    files = list(ANALYSIS_DOCS)
    if not is_update:
        files.append(AGENT_FILENAME)
    return files


async def run_async_analysis(
    name: str,
    commit: str,
    prompt: str,
    staged_path: Path,
    repo_dir: Path,
    emit: Callable[..., None],
    old_commit: str | None = None,
    cancellation_token: CancellationToken | None = None,
    on_subprocess_start: Callable[[int], None] | None = None,
    *,
    commit_dir: Path | None = None,
    is_update: bool = False,
) -> AnalysisResult:
    """Run AI analysis as an async subprocess with cancellation support.

    Returns (success, error_msg, stderr_path, stdout_path).
    """
    stderr_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
        mode="wb",
        prefix=f"hivemind-{name}-stderr-",
        suffix=".log",
        delete=False,
    )
    stdout_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
        mode="wb",
        prefix=f"hivemind-{name}-stdout-",
        suffix=".log",
        delete=False,
    )
    stderr_path = Path(stderr_file.name)
    stdout_path = Path(stdout_file.name)

    provider = get_active_provider()
    cmd = provider.build_analysis_command(
        extra_dirs=[repo_dir, staged_path],
        write=True,
    )

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdin=asyncio.subprocess.PIPE,
        stdout=stdout_file.fileno(),
        stderr=stderr_file.fileno(),
        cwd=str(staged_path),
    )

    if proc.stdin:
        proc.stdin.write(prompt.encode())
        await proc.stdin.drain()
        proc.stdin.close()
        await proc.stdin.wait_closed()

    stderr_file.close()
    stdout_file.close()

    if on_subprocess_start:
        on_subprocess_start(proc.pid)

    # Poll with cancellation checks and file progress tracking
    expected = expected_analysis_files(is_update=is_update)
    found: set[str] = set()

    while proc.returncode is None:
        await asyncio.sleep(1)

        if cancellation_token and cancellation_token.is_cancelled():
            try:
                proc.terminate()
                await asyncio.wait_for(proc.wait(), timeout=PROCESS_TERMINATE_TIMEOUT)
            except TimeoutError:
                proc.kill()
                await proc.wait()
            cleanup_log_files(stderr_path, stdout_path)
            msg = "Cancelled by user"
            raise asyncio.CancelledError(msg)

        # Track file creation progress
        if commit_dir:
            for f in expected:
                if f not in found and (commit_dir / f).exists():
                    found.add(f)

        progress_pct = int(len(found) / len(expected) * 100) if expected else 0
        emit(
            UpdatePhase.ANALYZING,
            f"Analyzing {commit[:12]}... ({len(found)}/{len(expected)} files)",
            progress_percent=progress_pct,
            new_commit=commit,
            old_commit=old_commit,
            files_found=sorted(found),
        )

    if proc.returncode != 0:
        error_msg = read_analysis_error(proc.returncode, stderr_path, stdout_path)
        cleanup_log_files(stderr_path, stdout_path)
        return AnalysisResult(success=False, error=error_msg, stderr_path=stderr_path, stdout_path=stdout_path)

    # Validate expected files were created
    if commit_dir:
        missing = [f for f in expected if not (commit_dir / f).exists()]
        if missing:
            error_msg = f"Analysis incomplete — missing: {', '.join(missing)}"
            cleanup_log_files(stderr_path, stdout_path)
            return AnalysisResult(success=False, error=error_msg, stderr_path=stderr_path, stdout_path=stdout_path)

    cleanup_log_files(stderr_path, stdout_path)
    return AnalysisResult(success=True, stderr_path=stderr_path, stdout_path=stdout_path)


def make_cancellation_checker(cancellation_token: CancellationToken | None) -> Callable[[str], None]:
    """Create a cancellation checker that respects risky phases."""

    def _check_cancellation(phase: str) -> None:
        if not cancellation_token or not cancellation_token.is_cancelled():
            return
        risky_phases = {UpdatePhase.COMMITTING, UpdatePhase.UPDATING_HEAD}
        if phase not in risky_phases:
            msg = f"Cancelled before {phase}"
            raise asyncio.CancelledError(msg)

    return _check_cancellation


async def handle_async_cancellation(
    staged_path: Path | None,
    stderr_path: Path | None,
    stdout_path: Path | None,
    repo_dir: Path,
    old_commit: str | None,
    cancel_msg: str = "Cancelled by user",
) -> UpdateResult:
    """Clean up and return cancelled result for async operations."""
    if staged_path and staged_path.exists():
        shutil.rmtree(staged_path, ignore_errors=True)
    if stderr_path:
        cleanup_log_files(stderr_path)
    if stdout_path:
        cleanup_log_files(stdout_path)
    await revert_checkout(repo_dir, old_commit)
    return UpdateResult(success=False, error=cancel_msg, cancelled=True)
