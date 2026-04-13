"""Firecrawl Docker service lifecycle management.

Manages the self-hosted Firecrawl instance via docker compose.
The compose file is bundled in this package under compose/.
On first start, it's copied to a runtime directory at ~/.cache/hivemind/firecrawl/.
"""

import shutil
import subprocess
import time
from pathlib import Path

import httpx

FIRECRAWL_URL = "http://localhost:3002"
FIRECRAWL_HEALTH_ENDPOINT = f"{FIRECRAWL_URL}/v0/health/liveness"

# Runtime directory where docker compose runs from
RUNTIME_DIR = Path.home() / ".cache" / "hivemind" / "firecrawl"

# Bundled compose files shipped with the package
_COMPOSE_SRC = Path(__file__).parent / "compose"

_HEALTH_TIMEOUT = 120  # seconds to wait for service to become healthy
_HEALTH_POLL_INTERVAL = 2  # seconds between health checks


class FirecrawlNotRunningError(Exception):
    """Raised when the Firecrawl service is not reachable."""


def is_firecrawl_running() -> bool:
    """Check if the Firecrawl service is reachable."""
    try:
        response = httpx.get(FIRECRAWL_HEALTH_ENDPOINT, timeout=5)
    except httpx.HTTPError:
        return False
    else:
        return response.status_code == 200


def ensure_firecrawl_running() -> None:
    """Check that Firecrawl is running. Raise if not."""
    if not is_firecrawl_running():
        msg = (
            f"Firecrawl service is not running at {FIRECRAWL_URL}.\n"
            "Start it with: hivemind crawl start\n"
            "Then retry this command."
        )
        raise FirecrawlNotRunningError(msg)


def _ensure_runtime_dir() -> Path:
    """Copy bundled compose files to the runtime directory if needed.

    Copies the full compose/ tree (including init-db/ for building
    the nuq-postgres image locally on arm64).

    Returns the runtime directory path.
    """
    compose_file = RUNTIME_DIR / "docker-compose.yaml"
    if compose_file.exists():
        return RUNTIME_DIR

    # copytree handles the full directory tree including init-db/
    shutil.copytree(_COMPOSE_SRC, RUNTIME_DIR, dirs_exist_ok=True)

    return RUNTIME_DIR


def _docker_available() -> bool:
    """Check if Docker is available."""
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
    else:
        return True


def _wait_for_healthy(timeout: int = _HEALTH_TIMEOUT) -> bool:
    """Poll the health endpoint until it responds or timeout is reached."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if is_firecrawl_running():
            return True
        time.sleep(_HEALTH_POLL_INTERVAL)
    return False


def start_firecrawl() -> None:
    """Start the Firecrawl Docker service.

    Copies the bundled compose file to the runtime directory on first run,
    then starts all containers. Waits for the health check to pass.

    Raises:
        RuntimeError: If Docker is not available or the service fails to start.
    """
    if is_firecrawl_running():
        return

    if not _docker_available():
        msg = "Docker is not available. Install Docker and ensure it is running."
        raise RuntimeError(msg)

    runtime_dir = _ensure_runtime_dir()

    subprocess.run(
        ["docker", "compose", "up", "-d", "--build"],
        cwd=str(runtime_dir),
        check=True,
    )

    if not _wait_for_healthy():
        msg = (
            f"Firecrawl service did not become healthy within {_HEALTH_TIMEOUT}s.\n"
            f"Check logs with: docker compose -f {runtime_dir}/docker-compose.yaml logs"
        )
        raise RuntimeError(msg)


def stop_firecrawl() -> None:
    """Stop the Firecrawl Docker service."""
    compose_file = RUNTIME_DIR / "docker-compose.yaml"
    if not compose_file.exists():
        return

    subprocess.run(
        ["docker", "compose", "down"],
        cwd=str(RUNTIME_DIR),
        check=True,
    )
