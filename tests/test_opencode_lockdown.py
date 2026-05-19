"""Lockdown-specific tests for hivemind's opencode integration."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from hivemind.config import load_config, save_config
from hivemind.models import AppConfig
from hivemind.opencode import _post_init_dirs, invalidate_config_cache, validate_model_config

if TYPE_CHECKING:
    from pathlib import Path


def test_validate_model_config_requires_both_models(monkeypatch: pytest.MonkeyPatch) -> None:
    import hivemind.opencode as opencode

    monkeypatch.setattr(opencode, "_app_config_cache", AppConfig())

    result = validate_model_config(require_configured=True)

    assert result.success is False
    assert result.error == "No models configured. Run 'hivemind -- auth login' and then 'hivemind sync'."


def test_validate_model_config_clears_stale_models(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import hivemind.config as config

    config_json = tmp_path / "config.json"
    monkeypatch.setattr(config, "CONFIG_JSON", config_json)
    invalidate_config_cache()
    save_config(
        AppConfig(
            model="anthropic/claude-sonnet-4-20250514",
            small_model="anthropic/claude-haiku-4-5",
        )
    )
    monkeypatch.setattr(
        "hivemind.opencode.list_engine_models",
        lambda: ["openai/gpt-5", "openai/gpt-5-mini"],
    )

    result = validate_model_config(require_configured=True)

    assert result.success is False
    assert "Configured models no longer available" in (result.error or "")
    assert load_config().model == ""
    assert load_config().small_model == ""


def test_post_init_dirs_syncs_model_choices(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import hivemind.opencode as opencode

    home = tmp_path / "opencode-home"
    home.mkdir()
    monkeypatch.setattr(opencode, "home_dir", lambda: home)
    monkeypatch.setattr(
        opencode,
        "_app_config_cache",
        AppConfig(
            model="openai/gpt-5",
            small_model="openai/gpt-5-mini",
        ),
    )

    _post_init_dirs()

    data = json.loads((home / "opencode.json").read_text(encoding="utf-8"))
    assert data["model"] == "openai/gpt-5"
    assert data["small_model"] == "openai/gpt-5-mini"


def test_launch_opencode_fails_before_exec_on_invalid_models(monkeypatch: pytest.MonkeyPatch) -> None:
    from click.exceptions import Exit

    import hivemind.cli as cli
    import hivemind.opencode as opencode
    import hivemind.server as server
    from hivemind.models import OperationResult

    monkeypatch.setattr(
        opencode,
        "validate_model_config",
        lambda require_configured: OperationResult(success=False, error="bad"),
    )
    monkeypatch.setattr(opencode, "sync_runtime_config", lambda: pytest.fail("should not sync on invalid config"))
    monkeypatch.setattr(server, "is_server_running", lambda: pytest.fail("should exit before server check"))

    with pytest.raises(Exit):
        cli._launch_opencode([])


def test_launch_opencode_syncs_runtime_config_before_exec(monkeypatch: pytest.MonkeyPatch) -> None:
    import hivemind.cli as cli
    import hivemind.opencode as opencode
    import hivemind.server as server
    from hivemind.models import OperationResult

    calls: list[str] = []

    monkeypatch.setattr(opencode, "validate_model_config", lambda require_configured: OperationResult(success=True))
    monkeypatch.setattr(opencode, "sync_runtime_config", lambda: calls.append("sync") or [])
    monkeypatch.setattr(server, "is_server_running", lambda: False)
    monkeypatch.setattr(opencode, "launch_command", lambda extra_args=None: ["engine", *(extra_args or [])])
    monkeypatch.setattr(cli.os, "execvp", lambda file, args: calls.extend(["exec", file, *args]))

    cli._launch_opencode(["--models"])

    assert calls == ["sync", "exec", "engine", "engine", "--models"]
