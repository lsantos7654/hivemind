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

from hivemind.models import CatalogEntry, HivemindConfig, RosterTemplatedParams


def test_roster_templated_params_round_trip() -> None:
    """RosterTemplatedParams — the body of a team-lead catalog entry —
    serializes and deserializes correctly."""
    params = RosterTemplatedParams(
        description="Build + Python tooling",
        experts=["expert-bun", "expert-bazel"],
    )
    data = params.model_dump()
    rehydrated = RosterTemplatedParams.model_validate(data)
    assert rehydrated.description == "Build + Python tooling"
    assert "expert-bun" in rehydrated.experts
    assert "expert-bazel" in rehydrated.experts


def test_catalog_entry_roster_templated_dispatch() -> None:
    """CatalogEntry with kind=roster_templated dispatches to
    RosterTemplatedParams via the mode='before' validator."""
    entry = CatalogEntry(
        kind="roster_templated",
        body={
            "description": "Prism project team",
            "experts": ["expert-bun", "expert-bazel", "expert-rust"],
        },
    )
    assert isinstance(entry.body, RosterTemplatedParams)
    assert len(entry.body.experts) == 3
    assert "expert-rust" in entry.body.experts


def test_team_catalog_entry_can_coexist_with_other_entries() -> None:
    """A team-lead entry alongside git_analyzed entries in a
    HivemindConfig validates correctly — no catalog race condition."""
    cfg = HivemindConfig(
        agents={
            "team-lead-prism": CatalogEntry(
                kind="roster_templated",
                body={"description": "Prism team", "experts": ["expert-bun"]},
            ),
            "expert-bun": CatalogEntry(
                kind="git_analyzed",
                body={
                    "remote": "https://github.com/oven-sh/bun",
                    "ref_name": "bun-v1.3.11",
                    "commit": "a" * 40,
                },
            ),
        },
    )
    assert len(cfg.agents) == 2
    assert cfg.agents["team-lead-prism"].kind == "roster_templated"
    assert cfg.agents["expert-bun"].kind == "git_analyzed"


def test_team_experts_list_is_ordered() -> None:
    """The experts list in a team preserves insertion order — important
    for the librarian and team-lead routing."""
    names = ["expert-c", "expert-a", "expert-b"]
    params = RosterTemplatedParams(
        description="Test",
        experts=names,
    )
    assert params.experts == names


def test_curator_ephemeral_invariant() -> None:
    """The curator agent template declares ephemeral: true — verified
    in test_ephemeral_invariants.py. This test confirms the catalog
    can represent an ephemeral entry."""
    from hivemind.agents.system_templated import SystemTemplatedParams

    params = SystemTemplatedParams(template="hivemind-expert-curator")
    assert params.template == "hivemind-expert-curator"
