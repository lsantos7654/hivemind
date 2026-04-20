"""Per-agent memory scaffolding.

Each agent has a durable memory directory under
``~/.config/opencode/hivemind/memory/<agent-name>/`` containing:

- ``MEMORY.md`` — index of pinned topic files (one line per entry)
- ``short_memory.md`` — working context (bounded; ~400 lines)
- ``long_memory.md`` — consolidated durable knowledge
- ``<topic>.md`` — individual memory docs (referenced in MEMORY.md)

The orchestrator (opencode's user-facing session) has a parallel
``_orchestrator/`` directory with the same layout.

Hivemind provides the directory structure and the agent.md memory section;
the subagent decides when to consolidate short → long per its prompt.
"""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from hivemind import opencode
from hivemind.templates import render

if TYPE_CHECKING:
    from pathlib import Path

SHORT_MEMORY_STUB = "# Short-term memory\n\nWorking context for the current session(s). Keep this file concise.\n"

LONG_MEMORY_STUB = (
    "# Long-term memory\n\n"
    "Consolidated durable knowledge. Consolidated here from short_memory.md\n"
    "when that file exceeds ~400 lines.\n"
)

MEMORY_INDEX_STUB = "# Memory index\n\n"


__all__ = [
    "agent_memory_dir",
    "ensure_agent_memory",
    "ensure_orchestrator_memory",
    "orchestrator_memory_dir",
    "remove_agent_memory",
    "render_memory_section",
]


def agent_memory_dir(name: str) -> Path:
    """Return ``~/.config/opencode/hivemind/memory/<name>/``."""
    return opencode.memory_dir() / name


def orchestrator_memory_dir() -> Path:
    """Return the orchestrator's memory directory."""
    return opencode.orchestrator_memory_dir()


def ensure_agent_memory(name: str) -> Path:
    """Create memory dir + stubs for ``name`` if not present. Returns the dir."""
    path = agent_memory_dir(name)
    _ensure_dir_with_stubs(path)
    return path


def ensure_orchestrator_memory() -> Path:
    """Create orchestrator memory dir + stubs if not present."""
    path = orchestrator_memory_dir()
    _ensure_dir_with_stubs(path)
    return path


def remove_agent_memory(name: str) -> None:
    """Delete the agent's memory directory if it exists (opt-in on delete)."""
    path = agent_memory_dir(name)
    if path.exists():
        shutil.rmtree(path)


def render_memory_section(name: str, kind: str) -> str:
    """Render the ``## Memory`` section to append to a deployed agent.md body."""
    return render(
        "memory_section.md.j2",
        memory_path=str(agent_memory_dir(name)),
        kind=kind,
    )


# ---------------------------------------------------------------------------


def _ensure_dir_with_stubs(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)

    memory_index = path / "MEMORY.md"
    if not memory_index.exists():
        memory_index.write_text(MEMORY_INDEX_STUB, encoding="utf-8")

    short = path / "short_memory.md"
    if not short.exists():
        short.write_text(SHORT_MEMORY_STUB, encoding="utf-8")

    long = path / "long_memory.md"
    if not long.exists():
        long.write_text(LONG_MEMORY_STUB, encoding="utf-8")
