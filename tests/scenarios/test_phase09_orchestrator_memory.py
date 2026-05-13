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

import pytest


@pytest.mark.skip(reason="TODO: Stage 11 — implement scenario tests")
def test_short_memory_grows_with_dated_entries() -> None:
    """Orchestrator appends to short_memory.md with date, source
    session, and rationale."""


@pytest.mark.skip(reason="TODO: Stage 11 — implement scenario tests")
def test_orchestrator_memory_injected_into_subagent_spawns() -> None:
    """When a subagent spawns under the orchestrator, the orchestrator's
    long_memory.md and topic files appear in the subagent's system
    prompt / memory section."""
