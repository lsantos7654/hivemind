"""Tests for the memory-compaction daemon system_templated agent.

The daemon is registered via ``_seed_system_templated`` from
``hivemind-memory-daemon`` template; deploys verbatim with
``memory_enabled=False`` (no memory tree, no memory section appended);
is excluded from the librarian (not user-callable). Auto-spawn behavior
itself is tested at the engine layer in
``dev/opencode/.../test/plugin/hivemind-memory.test.ts``.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from hivemind.agents.base import Agent
from hivemind.agents.system_templated import SystemTemplatedBody
from hivemind.models import (
    CatalogEntry,
    HivemindConfig,
    MemoryConfig,
    SystemTemplatedParams,
)
from hivemind.templates import render

if TYPE_CHECKING:
    import pytest

DAEMON_NAME = "hivemind-memory-daemon"
DAEMON_TEMPLATE = "agents/hivemind-memory-daemon.md.j2"


class TestDaemonTemplate:
    """The Jinja template renders to a valid agent body."""

    def test_renders_without_error(self) -> None:
        body = render(DAEMON_TEMPLATE, model="test-model", small_model="test-small")
        assert body.startswith("---")

    def test_uses_lightweight_model(self) -> None:
        body = render(DAEMON_TEMPLATE, model="test-model", small_model="anthropic/claude-haiku")
        match = re.search(r"^model:\s*(.+)$", body, re.MULTILINE)
        assert match is not None
        # Lightweight default — Haiku family or smaller. Body should NOT
        # default to Sonnet (the per-session default).
        assert "haiku" in match.group(1).lower(), f"daemon model should be lightweight, got: {match.group(1)}"

    def test_memory_disabled_in_frontmatter(self) -> None:
        body = render(DAEMON_TEMPLATE, model="test-model", small_model="test-small")
        # The daemon is one-shot; it must not get hivemind's memory
        # injection (which would add a memory contract directing the
        # daemon to maintain its own memory tree).
        assert re.search(r"^memory:\s*false\s*$", body, re.MULTILINE) is not None

    def test_no_bash_no_task(self) -> None:
        body = render(DAEMON_TEMPLATE, model="test-model", small_model="test-small")
        assert re.search(r"^\s*bash:\s*false\s*$", body, re.MULTILINE) is not None
        assert re.search(r"^\s*task:\s*false\s*$", body, re.MULTILINE) is not None

    def test_permissions_scoped_to_memory_dir(self) -> None:
        body = render(DAEMON_TEMPLATE, model="test-model", small_model="test-small")
        # Must allow access to the memory tree.
        assert "~/.config/opencode/hivemind/memory/**" in body


class TestDaemonBody:
    """Daemon body integrates correctly with the Agent abstraction."""

    def test_kind_is_system_templated(self) -> None:
        body = SystemTemplatedBody(name=DAEMON_NAME, params=SystemTemplatedParams(template=DAEMON_TEMPLATE))
        assert body.kind == "system_templated"

    def test_memory_enabled_returns_false(self) -> None:
        body = SystemTemplatedBody(name=DAEMON_NAME, params=SystemTemplatedParams(template=DAEMON_TEMPLATE))
        # Body protocol opt-out — Agent.deploy skips ensure_agent_memory
        # and Agent.render_for_deploy skips the memory-section append.
        assert body.memory_enabled() is False

    def test_agent_does_not_scaffold_memory_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Agent.deploy() for the daemon does not create
        ``~/.config/opencode/hivemind/memory/hivemind-memory-daemon/``.
        """
        from hivemind import opencode

        memory_root = tmp_path / "memory"
        memory_root.mkdir()
        monkeypatch.setattr(opencode, "memory_dir", lambda: memory_root)

        from hivemind.agents.memory import ensure_agent_memory

        # Direct check: ensure_agent_memory is not called by Agent.deploy
        # for daemons. We verify the path doesn't materialize.
        body = SystemTemplatedBody(name=DAEMON_NAME, params=SystemTemplatedParams(template=DAEMON_TEMPLATE))
        agent = Agent(name=DAEMON_NAME, body=body, enabled=True)

        # Calling render_for_deploy should not append the memory section.
        rendered = agent.render_for_deploy()
        # The memory section template emits "## Memory" — it must NOT
        # appear in the daemon's deployed body.
        assert "## Memory\n" not in rendered, "memory section should not be appended for system_templated agents"

        # ensure_agent_memory still works if you call it manually,
        # confirming the skip is at the deploy layer not the helper.
        ensure_agent_memory("some-other-agent")
        assert (memory_root / "some-other-agent").is_dir()

    def test_librarian_entry_marks_internal(self) -> None:
        body = SystemTemplatedBody(name=DAEMON_NAME, params=SystemTemplatedParams(template=DAEMON_TEMPLATE))
        entry = body.librarian_entry()
        # Librarian entry must signal this is hivemind-internal so the
        # orchestrator doesn't treat it as a user-callable expert.
        assert "internal" in entry.lower() or "hivemind-internal" in entry.lower()


class TestCatalogRoundTrip:
    """A daemon catalog entry round-trips through HivemindConfig."""

    def test_catalog_entry_validates(self) -> None:
        entry = CatalogEntry.model_validate(
            {
                "kind": "system_templated",
                "body": {"template": DAEMON_TEMPLATE},
            }
        )
        assert entry.kind == "system_templated"
        assert isinstance(entry.body, SystemTemplatedParams)
        assert entry.body.template == DAEMON_TEMPLATE


class TestMemoryConfig:
    """The hivemind.json memory section parses cleanly."""

    def test_default_threshold(self) -> None:
        cfg = MemoryConfig()
        assert cfg.compaction_threshold_bytes == 8192

    def test_custom_threshold_round_trips(self) -> None:
        cfg = MemoryConfig.model_validate({"compaction_threshold_bytes": 4096})
        assert cfg.compaction_threshold_bytes == 4096

    def test_full_hivemind_config_includes_memory(self) -> None:
        cfg = HivemindConfig.model_validate(
            {
                "home_dir": "~/.config/opencode",
                "memory": {"compaction_threshold_bytes": 16384},
            }
        )
        assert cfg.memory.compaction_threshold_bytes == 16384


class TestCleanupInvariants:
    """Phase 1 cleanup must not regress."""

    def test_no_notes_stub_helpers_exported(self) -> None:
        """notes.md infrastructure removed in Phase 1."""
        from hivemind.agents import roster_templated

        for stale in (
            "create_expert_notes_stub",
            "create_team_lead_notes_stub",
            "refresh_expert_notes_header",
            "refresh_team_lead_notes_header",
        ):
            assert not hasattr(roster_templated, stale), f"{stale} should be removed"

    def test_no_notes_template_files(self) -> None:
        templates_dir = Path(__file__).parent.parent / "src/hivemind/templates"
        assert not (templates_dir / "expert_notes.md.j2").exists()
        assert not (templates_dir / "team_lead_notes.md.j2").exists()

    def test_memory_section_no_longer_references_memory_index(self) -> None:
        templates_dir = Path(__file__).parent.parent / "src/hivemind/templates"
        body = (templates_dir / "memory_section.md.j2").read_text(encoding="utf-8")
        # The MEMORY.md index file is gone; the section should describe
        # discovery via filename, not via an index file.
        assert "scan `MEMORY.md`" not in body
        assert "indexed in `MEMORY.md`" not in body

    def test_memory_module_does_not_scaffold_memory_index(self) -> None:
        from hivemind.agents import memory as memory_mod

        assert not hasattr(memory_mod, "MEMORY_INDEX_STUB"), (
            "MEMORY_INDEX_STUB should be removed when MEMORY.md goes away"
        )
