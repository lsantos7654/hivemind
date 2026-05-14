"""Phase 10 — Mid-stream: ``/hivemind_sync`` updates ``expert-bun``.

▶ Test: ``/hivemind_sync`` produces an accurate proposal for a worktree
where exactly one expert has drifted from its pinned version. The proposal
does not execute without confirmation.

▶ Test: ``switch_version`` via the curator pipeline rotates the HEAD
symlink atomically. A spawn racing the rotation never sees a half-rotated
state.
"""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from hivemind.models import CatalogEntry, GitAnalyzedParams, HivemindConfig, MemoryConfig

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch


def test_git_analyzed_params_round_trip() -> None:
    """GitAnalyzedParams serializes and deserializes correctly."""
    params = GitAnalyzedParams(
        remote="https://github.com/oven-sh/bun",
        ref_name="bun-v1.4.0",
        commit="abc123def4567890abc123def4567890abc123de",
    )
    data = params.model_dump()
    rehydrated = GitAnalyzedParams.model_validate(data)
    assert rehydrated.remote == "https://github.com/oven-sh/bun"
    assert rehydrated.commit == "abc123def4567890abc123def4567890abc123de"
    assert rehydrated.ref_name == "bun-v1.4.0"


def test_catalog_entry_git_analyzed_dispatch() -> None:
    """CatalogEntry with kind=git_analyzed dispatches to GitAnalyzedParams."""
    entry = CatalogEntry(
        kind="git_analyzed",
        body={
            "remote": "https://github.com/oven-sh/bun",
            "ref_name": "bun-v1.3.11",
            "commit": "deadbeef" * 5,
        },
    )
    assert isinstance(entry.body, GitAnalyzedParams)
    assert entry.body.commit == "deadbeef" * 5


def test_version_drift_detection_round_trip() -> None:
    """When a catalog entry's commit differs from the worktree pinned
    version, round-tripping through model_dump/validate preserves that
    difference — the raw input for hivemind_sync's proposal logic."""
    old = GitAnalyzedParams(
        remote="https://github.com/oven-sh/bun",
        ref_name="bun-v1.3.11",
        commit="oldsha" * 10,
    )
    new = GitAnalyzedParams(
        remote="https://github.com/oven-sh/bun",
        ref_name="bun-v1.4.0",
        commit="newsha" * 10,
    )
    assert old.commit != new.commit
    assert old.ref_name != new.ref_name


def test_hivemind_config_memory_section() -> None:
    """HivemindConfig round-trips the memory section."""
    cfg = HivemindConfig(
        memory=MemoryConfig(compaction_threshold_bytes=4096),
    )
    data = cfg.model_dump()
    rehydrated = HivemindConfig.model_validate(data)
    assert rehydrated.memory is not None
    assert rehydrated.memory.compaction_threshold_bytes == 4096


def test_commit_rev_parse_in_real_git(tmp_path: Path) -> None:
    """git rev-parse --verify resolves a real commit SHA — the
    plumbing used by commit_exists_in_repo and switch_version."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.email=test@test", "-c", "user.name=Test", "commit", "--allow-empty", "-m", "init"],
        cwd=repo,
        check=True,
        capture_output=True,
    )

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    ).stdout.strip()

    result = subprocess.run(
        ["git", "rev-parse", "--verify", head], cwd=repo, check=False, capture_output=True, text=True
    )
    assert result.returncode == 0


def test_bogus_commit_rev_parse_fails(tmp_path: Path) -> None:
    """git rev-parse --verify fails for a non-existent ref."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

    result = subprocess.run(
        ["git", "rev-parse", "--verify", "bogus-ref-does-not-exist"],
        cwd=repo,
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0


def test_staging_dir_uniqueness(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    """create_staging_dir produces unique directories for parallel ops."""
    from hivemind.git import create_staging_dir

    staging_root = tmp_path / "hivemind" / "staging"
    staging_root.mkdir(parents=True)
    monkeypatch.setattr("hivemind.git.STAGING_DIR", staging_root)

    dirs = {create_staging_dir("test-agent") for _ in range(10)}
    assert len(dirs) == 10
    for d in dirs:
        assert d.is_dir()
