"""Shared test fixtures for hivemind tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def core_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Redirect all module-level path constants in core.py to tmp_path.

    Tests using this fixture never touch real project files.
    """
    import hivemind_cli.core as core

    hivemind_root = tmp_path / "hivemind"
    hivemind_root.mkdir()

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    repos_dir = cache_dir / "repos"
    repos_dir.mkdir()

    experts_dir = hivemind_root / "experts"
    experts_dir.mkdir()
    agents_dir = hivemind_root / "agents"
    agents_dir.mkdir()
    teams_dir = hivemind_root / "teams"
    teams_dir.mkdir()

    config_json = hivemind_root / "config.json"
    hivemind_json = hivemind_root / "hivemind.json"

    monkeypatch.setattr(core, "HIVEMIND_ROOT", hivemind_root)
    monkeypatch.setattr(core, "CACHE_DIR", cache_dir)
    monkeypatch.setattr(core, "REPOS_DIR", repos_dir)
    monkeypatch.setattr(core, "EXPERTS_DIR", experts_dir)
    monkeypatch.setattr(core, "AGENTS_DIR", agents_dir)
    monkeypatch.setattr(core, "TEAMS_DIR", teams_dir)
    monkeypatch.setattr(core, "CONFIG_JSON", config_json)
    monkeypatch.setattr(core, "HIVEMIND_JSON", hivemind_json)

    return {
        "root": hivemind_root,
        "cache": cache_dir,
        "repos": repos_dir,
        "experts": experts_dir,
        "agents": agents_dir,
        "teams": teams_dir,
        "config_json": config_json,
        "hivemind_json": hivemind_json,
    }
