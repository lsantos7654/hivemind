"""Configuration paths + JSON I/O primitives.

Hivemind splits state across two JSON files:

- ``hivemind.json`` — committed to git; holds the shared agent catalog
  (the set of experts + teams the project defines) plus engine / server
  configuration.
- ``config.json`` — per-machine, not committed; holds the local overlay
  (which agents are currently enabled or disabled on this machine).

``private`` state is gone: all experts live in one ``experts/`` directory
and the single repo cache under ``~/.cache/hivemind/repos/``.
"""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from hivemind.constants import (
    CACHE_DIR,
    OPENCODE_CONFIG_DIR,
    OPENCODE_DIR,
)
from hivemind.models import (
    AppConfig,
    HivemindConfig,
    ProgressCallback,
    ProgressInfo,
    UpdatePhase,
)

if TYPE_CHECKING:
    from collections.abc import Callable

__all__ = [
    "AGENTS_DIR",
    "CACHE_DIR",
    "COMMANDS_DIR",
    "CONFIG_JSON",
    "EXPERTS_DIR",
    "EXTERNAL_DOCS_DIR",
    "EXTERNAL_DOCS_LINK",
    "GIT_CLONE_TIMEOUT",
    "GIT_FETCH_TIMEOUT",
    "GIT_LOCAL_TIMEOUT",
    "HIVEMIND_JSON",
    "HIVEMIND_MD",
    "HIVEMIND_ROOT",
    "OPENCODE_CONFIG_DIR",
    "OPENCODE_DIR",
    "REPOS_DIR",
    "REPOS_LINK",
    "STAGING_DIR",
    "TEAMS_DIR",
    "count_versions",
    "ensure_external_docs_link",
    "ensure_repos_link",
    "expert_names",
    "get_expert_dir",
    "get_head_commit",
    "load_config",
    "load_hivemind",
    "load_json",
    "make_emit",
    "save_config",
    "save_hivemind",
    "save_json",
]

# --- Paths ---

HIVEMIND_ROOT = Path(__file__).resolve().parent.parent.parent
REPOS_DIR = CACHE_DIR / "repos"
STAGING_DIR = CACHE_DIR / "staging"
REPOS_LINK = HIVEMIND_ROOT / "repos"
EXTERNAL_DOCS_DIR = CACHE_DIR / "external_docs"
EXTERNAL_DOCS_LINK = HIVEMIND_ROOT / "external_docs"
HIVEMIND_JSON = HIVEMIND_ROOT / "hivemind.json"
CONFIG_JSON = HIVEMIND_ROOT / "config.json"
AGENTS_DIR = HIVEMIND_ROOT / "agents"
EXPERTS_DIR = HIVEMIND_ROOT / "experts"
TEAMS_DIR = HIVEMIND_ROOT / "teams"
HIVEMIND_MD = HIVEMIND_ROOT / "HIVEMIND.md"
COMMANDS_DIR = OPENCODE_DIR / "commands"

# --- Subprocess timeouts (seconds) ---

GIT_CLONE_TIMEOUT = 300
GIT_FETCH_TIMEOUT = 60
GIT_LOCAL_TIMEOUT = 15


# --- Progress helper ---


def make_emit(name: str, on_progress: ProgressCallback | None) -> Callable[..., None]:
    """Create a progress-emission closure."""

    def _emit(
        phase: UpdatePhase,
        message: str,
        *,
        progress_percent: int | None = None,
        new_commit: str | None = None,
        old_commit: str | None = None,
        error: str | None = None,
        files_found: list[str] | None = None,
    ) -> None:
        if on_progress:
            on_progress(
                ProgressInfo(
                    expert_name=name,
                    phase=phase,
                    message=message,
                    progress_percent=progress_percent,
                    new_commit=new_commit,
                    old_commit=old_commit,
                    error=error,
                    files_found=files_found,
                )
            )

    return _emit


# --- JSON I/O ---


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    result: dict[str, object] = json.loads(text)
    return result


def save_json(path: Path, data: dict[str, object]) -> None:
    content = json.dumps(data, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    tmp_path = Path(tmp)
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        tmp_path.replace(path)
    except BaseException:
        with contextlib.suppress(OSError):
            os.close(fd)
        with contextlib.suppress(OSError):
            tmp_path.unlink()
        raise


def load_config() -> AppConfig:
    """Load config.json (local overlay: enabled / disabled agent names)."""
    if not CONFIG_JSON.exists():
        return AppConfig()
    return AppConfig.model_validate(load_json(CONFIG_JSON))


def save_config(config: AppConfig) -> None:
    save_json(CONFIG_JSON, config.model_dump(exclude_defaults=True))


def load_hivemind() -> HivemindConfig:
    """Load hivemind.json (shared catalog + engine/server settings)."""
    return HivemindConfig.model_validate(load_json(HIVEMIND_JSON))


def save_hivemind(data: HivemindConfig) -> None:
    save_json(HIVEMIND_JSON, data.model_dump(exclude_defaults=True))
    from hivemind.opencode import invalidate_config_cache

    invalidate_config_cache()


# --- Expert filesystem helpers ---


def get_expert_dir(name: str) -> Path:
    """Return ``experts/<name>``. All experts live in one directory now."""
    return EXPERTS_DIR / name


def expert_names() -> list[str]:
    """List expert names present in ``experts/``."""
    if not EXPERTS_DIR.exists():
        return []
    return sorted(d.name for d in EXPERTS_DIR.iterdir() if d.is_dir())


def get_head_commit(expert_dir: Path) -> str | None:
    """Read the HEAD symlink to get the current commit hash."""
    head = expert_dir / "HEAD"
    if not head.is_symlink():
        return None
    return str(head.readlink())


def count_versions(expert_dir: Path) -> int:
    """Count commit directories under an expert dir (excludes HEAD)."""
    if not expert_dir.exists():
        return 0
    return sum(1 for d in expert_dir.iterdir() if d.is_dir() and not d.is_symlink() and d.name != "__pycache__")


def ensure_repos_link() -> None:
    """Ensure ``HIVEMIND_ROOT/repos`` symlinks to the cache repos dir."""
    REPOS_DIR.mkdir(parents=True, exist_ok=True)
    if REPOS_LINK.is_symlink():
        if REPOS_LINK.resolve() == REPOS_DIR.resolve():
            return
        REPOS_LINK.unlink()
    elif REPOS_LINK.is_dir():
        for item in REPOS_LINK.iterdir():
            dest = REPOS_DIR / item.name
            if not dest.exists():
                item.rename(dest)
        REPOS_LINK.rmdir()
    elif REPOS_LINK.exists():
        REPOS_LINK.unlink()
    REPOS_LINK.symlink_to(REPOS_DIR)


def ensure_external_docs_link() -> None:
    """Ensure ``HIVEMIND_ROOT/external_docs`` symlinks to the cache external_docs dir."""
    EXTERNAL_DOCS_DIR.mkdir(parents=True, exist_ok=True)
    if EXTERNAL_DOCS_LINK.is_symlink():
        if EXTERNAL_DOCS_LINK.resolve() == EXTERNAL_DOCS_DIR.resolve():
            return
        EXTERNAL_DOCS_LINK.unlink()
    elif EXTERNAL_DOCS_LINK.is_dir():
        for item in EXTERNAL_DOCS_LINK.iterdir():
            dest = EXTERNAL_DOCS_DIR / item.name
            if not dest.exists():
                item.rename(dest)
        EXTERNAL_DOCS_LINK.rmdir()
    elif EXTERNAL_DOCS_LINK.exists():
        EXTERNAL_DOCS_LINK.unlink()
    EXTERNAL_DOCS_LINK.symlink_to(EXTERNAL_DOCS_DIR)
