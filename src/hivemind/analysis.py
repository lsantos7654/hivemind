"""AI analysis orchestration for hivemind."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import IO, TYPE_CHECKING

from hivemind.config import get_active_provider
from hivemind.git import cleanup_log_files, read_analysis_error, revert_checkout
from hivemind.models import (
    AnalysisResult,
    CancellationToken,
    UpdatePhase,
    UpdateResult,
)
from hivemind.templates import update_expert_prompt

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

__all__ = [
    "AnalysisHandle",
    "analyze_repo",
    "expected_analysis_files",
    "finish_analysis",
    "handle_async_cancellation",
    "make_cancellation_checker",
    "run_async_analysis",
    "start_analysis",
]


@dataclass
class AnalysisHandle:
    """Handle for a running analysis subprocess, allowing progress monitoring."""

    proc: subprocess.Popen[bytes]
    commit_dir: Path
    expected_files: list[str]
    stderr_path: Path
    stdout_path: Path
    _stderr_file: IO[str] | None = None  # kept open until finish
    _stdout_file: IO[str] | None = None


def analyze_repo(
    name: str,
    commit: str,
    repo_dir: Path,
    expert_dir: Path,
    *,
    is_update: bool = False,
) -> AnalysisHandle:
    """Run AI analysis on a repo via the active provider's engine.

    Starts a background subprocess and returns an AnalysisHandle for monitoring.
    Use finish_analysis() to wait for completion and validate results.

    For create (is_update=False): generates 5 files (4 knowledge + agent.md).
    For update (is_update=True): regenerates 4 knowledge files, preserves agent.md.
    """
    commit_dir = expert_dir / commit

    if is_update:
        prompt = update_expert_prompt(name, commit, repo_dir, commit_dir)
    else:
        from hivemind.templates import create_expert_prompt

        prompt = create_expert_prompt(name, commit, repo_dir, commit_dir)

    provider = get_active_provider()
    cmd = provider.build_analysis_command(
        extra_dirs=[repo_dir, expert_dir],
        write=True,
    )

    cwd = Path(os.path.commonpath([repo_dir.resolve(), expert_dir.resolve()]))

    stderr_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
        mode="w",
        encoding="utf-8",
        prefix=f"hivemind-{name}-stderr-",
        suffix=".log",
        delete=False,
    )
    stdout_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
        mode="w",
        encoding="utf-8",
        prefix=f"hivemind-{name}-stdout-",
        suffix=".log",
        delete=False,
    )
    stderr_path = Path(stderr_file.name)
    stdout_path = Path(stdout_file.name)

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=stdout_file,
            stderr=stderr_file,
            cwd=str(cwd),
        )
        assert proc.stdin is not None
        proc.stdin.write(prompt.encode())
        proc.stdin.close()
    except BaseException:
        stderr_file.close()
        stdout_file.close()
        stderr_path.unlink(missing_ok=True)
        stdout_path.unlink(missing_ok=True)
        raise

    return AnalysisHandle(
        proc=proc,
        commit_dir=commit_dir,
        expected_files=expected_analysis_files(is_update=is_update),
        stderr_path=stderr_path,
        stdout_path=stdout_path,
        _stderr_file=stderr_file,
        _stdout_file=stdout_file,
    )


def expected_analysis_files(*, is_update: bool = False) -> list[str]:
    """Return the list of files an analysis run is expected to produce."""
    files = [
        "summary.md",
        "code_structure.md",
        "build_system.md",
        "apis_and_interfaces.md",
    ]
    if not is_update:
        files.append("agent.md")
    return files


def start_analysis(
    name: str,
    commit: str,
    repo_dir: Path,
    expert_dir: Path,
    *,
    is_update: bool = False,
) -> AnalysisHandle:
    """Start an AI analysis subprocess and return a handle for monitoring.

    The caller should poll handle.proc and check handle.commit_dir for files,
    then call finish_analysis() when the process exits.
    """
    commit_dir = expert_dir / commit

    if is_update:
        prompt = update_expert_prompt(name, commit, repo_dir, commit_dir)
    else:
        from hivemind.templates import create_expert_prompt

        prompt = create_expert_prompt(name, commit, repo_dir, commit_dir)

    provider = get_active_provider()
    cmd = provider.build_analysis_command(
        extra_dirs=[repo_dir, expert_dir],
        write=True,
    )

    cwd = Path(os.path.commonpath([repo_dir.resolve(), expert_dir.resolve()]))

    stderr_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
        mode="w",
        encoding="utf-8",
        prefix=f"hivemind-{name}-stderr-",
        suffix=".log",
        delete=False,
    )
    stdout_file = tempfile.NamedTemporaryFile(  # noqa: SIM115
        mode="w",
        encoding="utf-8",
        prefix=f"hivemind-{name}-stdout-",
        suffix=".log",
        delete=False,
    )

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=stdout_file,
            stderr=stderr_file,
            cwd=str(cwd),
        )
        assert proc.stdin is not None
        proc.stdin.write(prompt.encode())
        proc.stdin.close()
    except BaseException:
        stderr_file.close()
        stdout_file.close()
        Path(stderr_file.name).unlink(missing_ok=True)
        Path(stdout_file.name).unlink(missing_ok=True)
        raise

    return AnalysisHandle(
        proc=proc,
        commit_dir=commit_dir,
        expected_files=expected_analysis_files(is_update=is_update),
        stderr_path=Path(stderr_file.name),
        stdout_path=Path(stdout_file.name),
        _stderr_file=stderr_file,
        _stdout_file=stdout_file,
    )


def finish_analysis(handle: AnalysisHandle) -> bool:
    """Wait for analysis to complete (if not already) and validate results.

    Returns True on success, False on failure. Cleans up temp files.
    """
    handle.proc.wait()

    # Close temp file handles
    if handle._stderr_file is not None:
        with contextlib.suppress(Exception):
            handle._stderr_file.close()
    if handle._stdout_file is not None:
        with contextlib.suppress(Exception):
            handle._stdout_file.close()

    if handle.proc.returncode != 0:
        err_output = ""
        try:
            err_output = handle.stderr_path.read_text(encoding="utf-8").strip()
            if not err_output:
                err_output = handle.stdout_path.read_text(encoding="utf-8").strip()
        except Exception:
            pass
        if err_output:
            logger.error("Analysis error: %s", err_output)
        else:
            logger.error("Analysis failed with exit code %d", handle.proc.returncode)
        return False

    missing = [f for f in handle.expected_files if not (handle.commit_dir / f).exists()]
    if missing:
        logger.error("Analysis produced no output — missing: %s", ", ".join(missing))
        return False

    return True


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

    # Poll with cancellation checks
    while proc.returncode is None:
        await asyncio.sleep(1)

        if cancellation_token and cancellation_token.is_cancelled():
            try:
                proc.terminate()
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
            cleanup_log_files(stderr_path, stdout_path)
            msg = "Cancelled by user"
            raise asyncio.CancelledError(msg)

        emit(UpdatePhase.ANALYZING, f"Analyzing {commit[:12]}...", new_commit=commit, old_commit=old_commit)

    if proc.returncode != 0:
        error_msg = read_analysis_error(proc.returncode, stderr_path, stdout_path)
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


def handle_async_cancellation(
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
    revert_checkout(repo_dir, old_commit)
    return UpdateResult(success=False, error=cancel_msg, cancelled=True)
