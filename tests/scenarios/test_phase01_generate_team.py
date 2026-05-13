"""Phase 1 — Day 1: scope, set up, generate the team.

▶ Test: ``/hivemind_generate_team`` end-to-end against a tmpdir worktree
containing ``package.json`` + ``Cargo.toml`` + ``MODULE.bazel``. Assert:
missing experts created, existing experts left untouched, team-lead
deployed and enabled, every curator session auto-deleted (subagent tree
returns to baseline).

▶ Test: Curator session has ``ephemeral === true`` on its session row.
Two parallel curators do not race the catalog (no overlapping
``hivemind.json`` writes).

▶ Test: ``/global/reload-agents`` is non-destructive. The orchestrator's
MCP subprocess survives the team's enablement (no SIGTERM, no
``Tool execution aborted``).
"""

from __future__ import annotations

import pytest


@pytest.mark.skip(reason="TODO: Stage 11 — implement scenario tests")
def test_generate_team_against_tmpdir_worktree() -> None:
    """End-to-end: /hivemind_generate_team creates missing experts,
    deploys the team-lead, and curator sessions auto-delete."""


@pytest.mark.skip(reason="TODO: Stage 11 — implement scenario tests")
def test_curator_session_is_ephemeral() -> None:
    """Curator session row has ephemeral === true; parallel curators
    do not race on hivemind.json writes."""


@pytest.mark.skip(reason="TODO: Stage 11 — implement scenario tests")
def test_global_reload_agents_is_nondestructive() -> None:
    """POST /global/reload-agents does not terminate in-flight MCP
    subprocess; no SIGTERM, no Tool execution aborted."""
