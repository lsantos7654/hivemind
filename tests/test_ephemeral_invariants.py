"""Hivemind ephemeral-spawn invariants.

These tests pin down the parts of the ephemeral feature that live
outside the engine — the daemon and curator agent templates declare
``ephemeral: true`` in frontmatter, the HIVEMIND.md template documents
the feature, and the relevant skills mention it. The engine-side
behavior (terminal-state cleanup, per-spawn override, frontmatter
default resolution) is covered in
``dev/opencode/.../test/session/ephemeral.test.ts`` and
``dev/opencode/.../test/tool/task-ephemeral.test.ts``.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from hivemind.templates import hivemind_md_base, render


def _find_repo_root() -> Path | None:
    """Locate the workspace root.

    Under bazel test the file lives in a runfiles tree without the rest
    of the repo; under direct pytest it lives in the source checkout.
    Fall back to BUILD_WORKSPACE_DIRECTORY (set by `bazel run`) when the
    parent walk can't find HIVEMIND.md.
    """
    candidates: list[Path] = []
    candidates.extend(p for p in Path(__file__).resolve().parents if (p / "HIVEMIND.md").exists())
    bwd = os.environ.get("BUILD_WORKSPACE_DIRECTORY")
    if bwd:
        candidates.append(Path(bwd))
    return next((p for p in candidates if (p / "HIVEMIND.md").exists()), None)


REPO_ROOT = _find_repo_root()
SKILL_DIR = REPO_ROOT / "opencode" / "skills" if REPO_ROOT else None


def test_memory_daemon_template_declares_ephemeral() -> None:
    """The auto-spawned memory daemon should always vanish on terminal state."""
    body = render("agents/hivemind-memory-daemon.md.j2", model="test-model", small_model="test-small")
    assert "ephemeral: true" in body, (
        "hivemind-memory-daemon must declare ephemeral: true in frontmatter — "
        "otherwise every short_memory.md write that crosses the threshold "
        "leaves a `compact memory: <agent>` corpse in the subagent tree."
    )


def test_expert_curator_template_declares_ephemeral() -> None:
    """Curator runs are one-off — every catalog mutation spins up a fresh session."""
    body = render("agents/hivemind-expert-curator.md.j2", model="test-model", small_model="test-small")
    assert "ephemeral: true" in body, (
        "hivemind-expert-curator must declare ephemeral: true in frontmatter "
        "so add/update/switch_version/create_team spawns clean themselves up."
    )


def test_hivemind_md_template_documents_ephemeral_spawns() -> None:
    """The HIVEMIND.md template must explain the ephemeral=true Task option."""
    body = hivemind_md_base(teams_path="/tmp/teams-fixture")
    assert "Ephemeral spawns" in body, "HIVEMIND.md needs an Ephemeral spawns section"
    assert "ephemeral=true" in body, "HIVEMIND.md must show the Task(ephemeral=true) form"
    # Cross-reference the always-ephemeral agents so the model knows when
    # passing the flag is redundant.
    assert "hivemind-memory-daemon" in body
    assert "hivemind-expert-curator" in body


@pytest.mark.skipif(SKILL_DIR is None, reason="skill files not in runfiles tree")
def test_cross_session_skill_mentions_ephemeral_forks() -> None:
    """The cross-session skill should call out ephemeral=true for one-off forks."""
    assert SKILL_DIR is not None
    skill = (SKILL_DIR / "hivemind-cross-session/SKILL.md").read_text()
    assert "ephemeral=true" in skill, (
        "hivemind-cross-session skill should document ephemeral forks — "
        "Task(source_session_id=..., ephemeral=true) is the natural way to "
        "probe another session without polluting the subagent tree."
    )


@pytest.mark.skipif(SKILL_DIR is None, reason="skill files not in runfiles tree")
def test_expert_management_skill_mentions_curator_is_ephemeral() -> None:
    """Expert-management skill should note the curator is always ephemeral."""
    assert SKILL_DIR is not None
    skill = (SKILL_DIR / "hivemind-expert-management/SKILL.md").read_text()
    assert "ephemeral" in skill, (
        "hivemind-expert-management skill should explain that curator spawns "
        "are always ephemeral so the user doesn't pass ephemeral=true manually."
    )
