"""Shared constants for hivemind -- path defaults, analysis contracts, and configuration.

This module exists to centralize cross-module contracts and break circular
imports between config.py and providers/.
"""

from __future__ import annotations

from pathlib import Path

# --- Path defaults ---

CACHE_DIR: Path = Path.home() / ".cache" / "hivemind"

# Repository root (constants.py → hivemind/ → src/ → repo root)
_REPO_ROOT: Path = Path(__file__).resolve().parents[2]

# OpenCode add-ons bundled with this repo (commands, config defaults).
# Decoupled from hivemind core so they can be inspected/tested as plain OpenCode
# artifacts without going through hivemind. TUI plugins are no longer used —
# branding and connection-indicator behavior is patched directly into the
# bundled bun-compiled engine; see //third_party/patches/.
OPENCODE_DIR: Path = _REPO_ROOT / "opencode"
OPENCODE_CONFIG_DIR: Path = OPENCODE_DIR / "config"

# --- Provider defaults ---

DEFAULT_TEMPERATURE: float = 0.1

# --- Analysis file contracts ---

DESCRIPTION_FILENAME: str = "description.md"
EXPERTISE_FILENAME: str = "expertise.md"
ANALYSIS_DOCS: list[str] = [
    "summary.md",
    "code_structure.md",
    "build_system.md",
    "apis_and_interfaces.md",
]

# --- Template placeholders (resolved by provider _transform_body) ---

EXPERTS_DIR_PLACEHOLDER: str = "{EXPERTS_DIR}"
TEAMS_DIR_PLACEHOLDER: str = "{TEAMS_DIR}"
CACHE_DIR_PLACEHOLDER: str = "{CACHE_DIR}"

# --- Subprocess timeouts (seconds) ---

ENGINE_VALIDATION_TIMEOUT: int = 15
PROCESS_TERMINATE_TIMEOUT: float = 5.0
