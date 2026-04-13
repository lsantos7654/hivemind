"""Provider backend server lifecycle management.

Handles starting, stopping, and monitoring the provider's backend server
(e.g. ``opencode serve``).  State is persisted to ``~/.cache/hivemind/server.json``
so that subsequent ``hivemind`` invocations can detect a running server and
connect to it.
"""

from __future__ import annotations

import contextlib
import json
import os
import signal
import subprocess
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import httpx

from hivemind.constants import CACHE_DIR, PROCESS_TERMINATE_TIMEOUT
from hivemind.models import ServerState

if TYPE_CHECKING:
    from hivemind.providers.base import Provider

__all__ = [
    "clear_server_state",
    "get_server_url",
    "is_server_running",
    "load_server_state",
    "save_server_state",
    "start_server",
    "stop_server",
]

SERVER_STATE_FILE = CACHE_DIR / "server.json"
SERVER_LOG_FILE = CACHE_DIR / "server.log"

# --- State file I/O ---


def load_server_state() -> ServerState | None:
    """Load server state from disk, returning None if missing or corrupt."""
    if not SERVER_STATE_FILE.exists():
        return None
    try:
        data = json.loads(SERVER_STATE_FILE.read_text(encoding="utf-8"))
        return ServerState(**data)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None


def save_server_state(state: ServerState) -> None:
    """Persist server state to disk."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    SERVER_STATE_FILE.write_text(
        json.dumps(state.model_dump(mode="json"), indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def clear_server_state() -> None:
    """Remove the server state file."""
    if SERVER_STATE_FILE.exists():
        SERVER_STATE_FILE.unlink()


# --- Process helpers ---


def _pid_alive(pid: int) -> bool:
    """Check if a process is still running."""
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # process exists but we can't signal it
    return True


def is_server_running() -> bool:
    """Check if a managed server is currently running.

    Cleans up stale state files if the process is dead.
    """
    state = load_server_state()
    if state is None:
        return False
    if not _pid_alive(state.pid):
        clear_server_state()
        return False
    return True


def get_server_url() -> str | None:
    """Return the HTTP URL of the running server, or None."""
    state = load_server_state()
    if state is None:
        return None
    if not _pid_alive(state.pid):
        clear_server_state()
        return None
    return f"http://{state.hostname}:{state.port}"


# --- Lifecycle ---


def start_server(
    provider: Provider,
    *,
    port: int | None = None,
    hostname: str | None = None,
    timeout: float = 30.0,
) -> ServerState:
    """Start the provider's backend server as a background process.

    Args:
        provider: Active provider instance
        port: Override port (defaults to provider config)
        hostname: Override hostname (defaults to provider config)
        timeout: Seconds to wait for the health endpoint

    Returns:
        ServerState with process details

    Raises:
        RuntimeError: If the provider doesn't support servers, a server is
            already running, or the health check times out.
    """
    if not provider.supports_server:
        msg = f"Provider '{provider.name}' does not support a backend server."
        raise RuntimeError(msg)

    if is_server_running():
        state = load_server_state()
        assert state is not None
        msg = f"Server already running on {state.hostname}:{state.port} (PID {state.pid})"
        raise RuntimeError(msg)

    server_cfg = provider.server_config
    effective_port = port or server_cfg.port
    effective_hostname = hostname or server_cfg.hostname

    cmd = provider.start_server_command(effective_port, effective_hostname)
    log_file = SERVER_LOG_FILE

    # Ensure cache dir exists for log file
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Start as detached background process
    with log_file.open("a", encoding="utf-8") as log_fh:
        log_fh.write(f"\n--- Server start: {datetime.now(UTC).isoformat()} ---\n")
        log_fh.write(f"Command: {' '.join(cmd)}\n")
        log_fh.flush()

        proc = subprocess.Popen(
            cmd,
            stdout=log_fh,
            stderr=log_fh,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

    state = ServerState(
        pid=proc.pid,
        port=effective_port,
        hostname=effective_hostname,
        provider=provider.name,
        started_at=datetime.now(UTC),
        log_file=str(log_file),
    )
    save_server_state(state)

    # Poll health endpoint until ready
    health_url = provider.health_check_url(effective_port, effective_hostname)
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        # Check if process died
        if proc.poll() is not None:
            clear_server_state()
            msg = f"Server process exited with code {proc.returncode}. Check {log_file}"
            raise RuntimeError(msg)

        try:
            resp = httpx.get(health_url, timeout=2.0)
            if resp.status_code == 200:
                return state
        except httpx.ConnectError:
            pass
        except httpx.TimeoutException:
            pass

        time.sleep(0.5)

    # Timed out — kill the process
    proc.terminate()
    clear_server_state()
    msg = f"Server did not become healthy within {timeout}s. Check {log_file}"
    raise RuntimeError(msg)


def stop_server() -> bool:
    """Stop the managed server process.

    Returns:
        True if a server was stopped, False if none was running.
    """
    state = load_server_state()
    if state is None:
        return False

    pid = state.pid
    if not _pid_alive(pid):
        clear_server_state()
        return False

    # Send SIGTERM for clean shutdown
    os.kill(pid, signal.SIGTERM)

    # Wait for process to exit
    deadline = time.monotonic() + PROCESS_TERMINATE_TIMEOUT
    while time.monotonic() < deadline:
        if not _pid_alive(pid):
            clear_server_state()
            return True
        time.sleep(0.2)

    # Force kill if still alive
    with contextlib.suppress(ProcessLookupError):
        os.kill(pid, signal.SIGKILL)

    clear_server_state()
    return True
