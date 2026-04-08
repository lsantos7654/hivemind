"""Configuration, path constants, and filesystem helpers for hivemind."""

from __future__ import annotations

import contextlib
import json
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from hivemind.models import (
    AppConfig,
    HivemindConfig,
    ProgressCallback,
    ProgressInfo,
    ProviderConfig,
    RepoEntry,
    RepoLookup,
    TeamData,
    UpdatePhase,
)
from hivemind.providers import (
    Provider,
    get_provider,
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
    # Timeout constants
    "GIT_CLONE_TIMEOUT",
    "GIT_FETCH_TIMEOUT",
    "GIT_LOCAL_TIMEOUT",
    "HIVEMIND_JSON",
    "HIVEMIND_MD",
    # Path constants
    "HIVEMIND_ROOT",
    "PRIVATE_EXPERTS_DIR",
    "PRIVATE_REPOS_JSON",
    "PROVIDERS_DIR",
    "REPOS_DIR",
    "REPOS_LINK",
    "TEAMS_DIR",
    "_provider_cache",
    "count_versions",
    "ensure_external_docs_link",
    "ensure_repos_link",
    "expert_names",
    "get_active_provider",
    "get_expert_dir",
    "get_head_commit",
    "get_repos_for_expert",
    "invalidate_provider_cache",
    "is_private_expert",
    "load_config",
    "load_hivemind",
    "load_json",
    "load_private_repos",
    "load_repos",
    "load_teams",
    # Functions
    "make_emit",
    "save_config",
    "save_hivemind",
    "save_json",
    "save_private_repos",
    "save_repos",
    "save_teams",
]

# --- Paths (shared configuration) ---

# Allow override for testing, otherwise use the same paths as cli.py
HIVEMIND_ROOT = Path(__file__).resolve().parent.parent.parent
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
PROVIDERS_DIR = HIVEMIND_ROOT / "providers"
HIVEMIND_MD = HIVEMIND_ROOT / "HIVEMIND.md"

# --- Subprocess Timeout Constants (seconds) ---
GIT_CLONE_TIMEOUT = 300
GIT_FETCH_TIMEOUT = 60
GIT_LOCAL_TIMEOUT = 15


# --- Config I/O (future: adapters/json_config.py) ---


def make_emit(name: str, on_progress: ProgressCallback | None) -> Callable[..., None]:
    """Create a progress emission closure, collapsing the repeated guard pattern."""

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
    """Load config.json (local user state: enabled/disabled, active_provider)."""
    if not CONFIG_JSON.exists():
        return AppConfig()
    return AppConfig.model_validate(load_json(CONFIG_JSON))


def save_config(config: AppConfig) -> None:
    save_json(CONFIG_JSON, config.model_dump(exclude_defaults=True))


def load_hivemind() -> HivemindConfig:
    """Load hivemind.json (shared project config: providers, repos)."""
    return HivemindConfig.model_validate(load_json(HIVEMIND_JSON))


def save_hivemind(data: HivemindConfig) -> None:
    save_json(HIVEMIND_JSON, data.model_dump(exclude_defaults=True))


def load_teams() -> dict[str, TeamData]:
    """Load teams from config.json."""
    return load_config().teams


def save_teams(teams: dict[str, TeamData], config: AppConfig) -> None:
    """Save teams to config.json."""
    config.teams = teams
    save_config(config)


_provider_cache: Provider | None = None


def get_active_provider() -> Provider:
    """Get the active provider instance, cached for the session."""
    global _provider_cache
    if _provider_cache is not None:
        return _provider_cache
    config = load_config()
    active = config.active_provider
    if not active:
        msg = "No active_provider set in config.json. Run 'hivemind init' first."
        raise RuntimeError(msg)
    hivemind = load_hivemind()
    prov = hivemind.providers.get(active, ProviderConfig())
    _provider_cache = get_provider(active, prov, providers_dir=PROVIDERS_DIR)
    return _provider_cache


def invalidate_provider_cache() -> None:
    """Reset provider cache (call after switching providers)."""
    global _provider_cache
    _provider_cache = None


def load_repos() -> dict[str, RepoEntry]:
    return load_hivemind().repos


def save_repos(repos: dict[str, RepoEntry]) -> None:
    hm = load_hivemind()
    hm.repos = repos
    save_hivemind(hm)


def load_private_repos() -> dict[str, RepoEntry]:
    """Load private-repos.json (gitignored, never committed)."""
    if not PRIVATE_REPOS_JSON.exists():
        return {}
    try:
        data = json.loads(PRIVATE_REPOS_JSON.read_text(encoding="utf-8"))
        return {k: RepoEntry.model_validate(v) for k, v in data.items()}
    except (OSError, json.JSONDecodeError):
        return {}


def save_private_repos(repos: dict[str, RepoEntry]) -> None:
    """Save private-repos.json."""
    data = {k: v.model_dump(exclude_defaults=True) for k, v in repos.items()}
    PRIVATE_REPOS_JSON.write_text(json.dumps(data, indent=2) + "\n")


# --- Expert File Store (future: adapters/filesystem_store.py) ---


def is_private_expert(name: str) -> bool:
    """Check if expert is private (lives in private-experts/)."""
    return (PRIVATE_EXPERTS_DIR / name).is_dir()


def get_expert_dir(name: str) -> Path:
    """Get expert directory (public or private)."""
    if is_private_expert(name):
        return PRIVATE_EXPERTS_DIR / name
    return EXPERTS_DIR / name


def get_repos_for_expert(name: str) -> RepoLookup:
    """Get (repos_dict, is_private) for expert."""
    if is_private_expert(name):
        return RepoLookup(repos=load_private_repos(), is_private=True)
    return RepoLookup(repos=load_repos(), is_private=False)


def expert_names() -> list[str]:
    """List all expert names from experts/ and private-experts/ directories."""
    experts: list[str] = []
    if EXPERTS_DIR.exists():
        experts.extend(d.name for d in EXPERTS_DIR.iterdir() if d.is_dir())
    if PRIVATE_EXPERTS_DIR.exists():
        experts.extend(d.name for d in PRIVATE_EXPERTS_DIR.iterdir() if d.is_dir())
    return sorted(experts)


def get_head_commit(expert_dir: Path) -> str | None:
    """Read the HEAD symlink to get the current commit hash."""
    head = expert_dir / "HEAD"
    if not head.is_symlink():
        return None
    return str(head.readlink())


def count_versions(expert_dir: Path) -> int:
    """Count commit directories (excludes HEAD symlink)."""
    if not expert_dir.exists():
        return 0
    return sum(1 for d in expert_dir.iterdir() if d.is_dir() and not d.is_symlink() and d.name != "__pycache__")


def ensure_repos_link() -> None:
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


def ensure_external_docs_link() -> None:
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
