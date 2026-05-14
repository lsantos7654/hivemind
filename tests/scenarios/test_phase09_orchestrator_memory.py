"""Phase 9 — Orchestrator pins a project convention.

▶ Test: The orchestrator's ``short_memory.md`` grows with appended entries
on cue. Entries include date, source PR / source session, and the rationale.

▶ Test: Orchestrator memory is read by every spawn — when any subagent
(expert or otherwise) starts under the orchestrator, the orchestrator's
``_orchestrator/long_memory.md`` and topic files are part of the
orchestrator's system context. (This propagates project conventions
implicitly.)
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import pytest

from hivemind import opencode as _opencode
from hivemind.agents.memory import (
    LONG_MEMORY_STUB,
    SHORT_MEMORY_STUB,
    agent_memory_dir,
    ensure_agent_memory,
    remove_agent_memory,
    render_memory_section,
)

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture
def memory_tmpdir(tmp_path: Path, monkeypatch: MonkeyPatch) -> Path:
    """Redirect memory dir to tmp_path so tests never touch real files."""
    mem = tmp_path / "memory"
    mem.mkdir()
    monkeypatch.setattr(_opencode, "memory_dir", lambda: mem)
    return mem


def test_ensure_agent_memory_creates_stubs(memory_tmpdir: Path) -> None:
    """ensure_agent_memory creates the memory directory with
    short_memory.md and long_memory.md stubs."""
    result = ensure_agent_memory("test-agent")

    assert result.is_dir()
    assert result == memory_tmpdir / "test-agent"

    short = result / "short_memory.md"
    long = result / "long_memory.md"
    assert short.exists()
    assert long.exists()
    assert short.read_text(encoding="utf-8").startswith("# Short-term memory")
    assert long.read_text(encoding="utf-8").startswith("# Long-term memory")


def test_short_memory_grows_with_appended_entries(memory_tmpdir: Path) -> None:
    """Orchestrator appends dated entries to short_memory.md.
    Entries include date, source session, and rationale."""
    ensure_agent_memory("_orchestrator")
    short_path = memory_tmpdir / "_orchestrator" / "short_memory.md"

    today = datetime.date.today().isoformat()
    entry = (
        f"\n## prism — schema convention ({today})\n\n"
        "Column names in prism migrations are fully-qualified.\n"
        "triggered_by: PR1↔PR3 column-name confirmation\n"
    )
    with short_path.open("a", encoding="utf-8") as fh:
        fh.write(entry)

    content = short_path.read_text(encoding="utf-8")
    assert today in content
    assert "fully-qualified" in content
    assert "triggered_by" in content
    assert content.startswith("# Short-term memory")


def test_short_memory_is_idempotent_on_second_ensure(memory_tmpdir: Path) -> None:
    """Calling ensure_agent_memory twice does not overwrite existing content."""
    ensure_agent_memory("persistent")
    short_path = memory_tmpdir / "persistent" / "short_memory.md"
    short_path.write_text("custom notes\n", encoding="utf-8")

    ensure_agent_memory("persistent")
    assert short_path.read_text(encoding="utf-8") == "custom notes\n"


def test_render_memory_section_includes_correct_paths(memory_tmpdir: Path) -> None:
    """render_memory_section references the agent's memory directory."""
    ensure_agent_memory("expert-rust")
    section = render_memory_section("expert-rust", "git_analyzed")

    assert "## Memory" in section
    assert "expert-rust" in section
    assert len(section.strip().splitlines()) > 2


def test_short_memory_stub_is_well_formed() -> None:
    """SHORT_MEMORY_STUB is non-empty with a markdown heading."""
    assert len(SHORT_MEMORY_STUB) > 0
    assert SHORT_MEMORY_STUB.startswith("#")


def test_long_memory_stub_is_well_formed() -> None:
    """LONG_MEMORY_STUB is non-empty with a markdown heading."""
    assert len(LONG_MEMORY_STUB) > 0
    assert LONG_MEMORY_STUB.startswith("#")


def test_remove_agent_memory_deletes_directory(memory_tmpdir: Path) -> None:
    """remove_agent_memory deletes the entire memory directory."""
    ensure_agent_memory("to-remove")
    mem_dir = memory_tmpdir / "to-remove"
    assert mem_dir.is_dir()

    remove_agent_memory("to-remove")
    assert not mem_dir.exists()


def test_agent_memory_dir_returns_correct_path(memory_tmpdir: Path) -> None:
    """agent_memory_dir returns the expected subdirectory."""
    result = agent_memory_dir("my-agent")
    assert result == memory_tmpdir / "my-agent"
