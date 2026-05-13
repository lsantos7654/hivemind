"""Tests for registry cross-kind naming-collision enforcement."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from hivemind.agents.base import Agent
from hivemind.agents.git_analyzed import GitAnalyzedBody
from hivemind.agents.registry import add, load, save_body
from hivemind.agents.roster_templated import RosterTemplatedBody
from hivemind.models import AppConfig, CatalogEntry, GitAnalyzedParams, HivemindConfig, RosterTemplatedParams

if TYPE_CHECKING:
    from collections.abc import Iterator


class TestAddCrossKindCollision:
    """``registry.add()`` must reject cross-kind name collisions."""

    def _make_expert_agent(self) -> Agent:
        body = GitAnalyzedBody(
            name="bazel",
            params=GitAnalyzedParams(remote="https://github.com/bazelbuild/bazel.git", commit="abc123"),
        )
        return Agent(name="bazel", body=body)

    def _make_team_agent(self) -> Agent:
        body = RosterTemplatedBody(
            name="bazel-tooling",
            params=RosterTemplatedParams(description="Build tooling team", experts=["expert-bazel"]),
        )
        return Agent(name="bazel-tooling", body=body)

    @pytest.fixture(autouse=True)
    def _mock_saves(self) -> Iterator[None]:
        with patch("hivemind.agents.registry.save_config"), patch("hivemind.agents.registry.save_hivemind"):
            yield

    def test_rejects_team_when_expert_exists(self) -> None:
        """Adding a roster_templated agent must fail when the name is already an expert."""
        team_agent = self._make_team_agent()
        team_agent.name = "bazel"  # collide with expert

        hivemind_cfg = HivemindConfig(
            agents={
                "bazel": CatalogEntry(
                    kind="git_analyzed", body=GitAnalyzedParams(remote="https://example.com", commit="def456")
                )
            }
        )
        app_cfg = AppConfig()

        with (
            patch("hivemind.agents.registry.load_hivemind", return_value=hivemind_cfg),
            patch("hivemind.agents.registry.load_config", return_value=app_cfg),
        ):
            with pytest.raises(ValueError, match=r"agent .* already exists as git_analyzed"):
                add(team_agent)

    def test_rejects_expert_when_team_exists(self) -> None:
        """Adding a git_analyzed agent must fail when the name is already a team."""
        expert_agent = self._make_expert_agent()
        expert_agent.name = "my-team"  # collide with team

        hivemind_cfg = HivemindConfig(agents={})
        app_cfg = AppConfig(teams={"my-team": RosterTemplatedParams(description="Existing team")})

        with (
            patch("hivemind.agents.registry.load_hivemind", return_value=hivemind_cfg),
            patch("hivemind.agents.registry.load_config", return_value=app_cfg),
        ):
            with pytest.raises(ValueError, match=r"team .* already exists with that name"):
                add(expert_agent)

    def test_add_allows_unique_names(self) -> None:
        """Non-colliding additions across kinds must succeed."""
        expert = self._make_expert_agent()
        team = self._make_team_agent()

        hivemind_cfg = HivemindConfig(agents={})
        app_cfg = AppConfig(teams={})

        with (
            patch("hivemind.agents.registry.load_hivemind", return_value=hivemind_cfg),
            patch("hivemind.agents.registry.load_config", return_value=app_cfg),
        ):
            add(expert)  # must not raise
            add(team)  # must not raise


class TestLoadCrossKindCollision:
    """``registry.load()`` must skip teams that collide with an existing expert."""

    def test_skips_team_on_name_collision(self, caplog: pytest.LogCaptureFixture) -> None:
        hivemind_cfg = HivemindConfig(
            agents={
                "bazel": CatalogEntry(
                    kind="git_analyzed", body=GitAnalyzedParams(remote="https://example.com", commit="abc123")
                )
            }
        )
        app_cfg = AppConfig(teams={"bazel": RosterTemplatedParams(description="Colliding team")})

        with (
            patch("hivemind.agents.registry.load_hivemind", return_value=hivemind_cfg),
            patch("hivemind.agents.registry.load_config", return_value=app_cfg),
        ):
            with caplog.at_level(logging.ERROR):
                result = load()

        # The expert (from hivemind.json) must be present.
        assert "bazel" in result
        assert result["bazel"].kind == "git_analyzed"

        # The team must NOT overwrite the expert — only the git_analyzed entry exists.
        assert len(result) == 1

        # An error must be logged about the collision.
        collision_errors = [r for r in caplog.records if r.levelno == logging.ERROR and "name collision" in r.message]
        assert len(collision_errors) >= 1

    def test_no_collision_when_names_differ(self) -> None:
        """Teams whose names don't collide are loaded normally."""
        hivemind_cfg = HivemindConfig(
            agents={
                "expert-foo": CatalogEntry(
                    kind="git_analyzed", body=GitAnalyzedParams(remote="https://example.com", commit="abc123")
                )
            }
        )
        app_cfg = AppConfig(teams={"team-bar": RosterTemplatedParams(description="No collision")})

        with (
            patch("hivemind.agents.registry.load_hivemind", return_value=hivemind_cfg),
            patch("hivemind.agents.registry.load_config", return_value=app_cfg),
        ):
            result = load()

        assert "expert-foo" in result
        assert "team-bar" in result
        assert result["expert-foo"].kind == "git_analyzed"
        assert result["team-bar"].kind == "roster_templated"


class TestSaveBodyCrossKindCollision:
    """``registry.save_body()`` must reject cross-kind name collisions."""

    def _make_team_agent(self) -> Agent:
        body = RosterTemplatedBody(
            name="bazel-tooling",
            params=RosterTemplatedParams(description="Build tooling team"),
        )
        return Agent(name="bazel-tooling", body=body)

    def _make_expert_agent(self) -> Agent:
        body = GitAnalyzedBody(
            name="bazel",
            params=GitAnalyzedParams(remote="https://github.com/bazelbuild/bazel.git", commit="abc123"),
        )
        return Agent(name="bazel", body=body)

    @pytest.fixture(autouse=True)
    def _mock_saves(self) -> Iterator[None]:
        with patch("hivemind.agents.registry.save_config"), patch("hivemind.agents.registry.save_hivemind"):
            yield

    def test_save_body_rejects_team_when_expert_exists(self) -> None:
        """Saving a roster body must fail when the name is already an expert."""
        team = self._make_team_agent()
        team.name = "bazel"

        hivemind_cfg = HivemindConfig(
            agents={
                "bazel": CatalogEntry(
                    kind="git_analyzed", body=GitAnalyzedParams(remote="https://example.com", commit="def456")
                )
            }
        )
        app_cfg = AppConfig(teams={"bazel": RosterTemplatedParams(description="Existing team")})

        with (
            patch("hivemind.agents.registry.load_hivemind", return_value=hivemind_cfg),
            patch("hivemind.agents.registry.load_config", return_value=app_cfg),
        ):
            with pytest.raises(ValueError, match=r"agent .* already exists as git_analyzed"):
                save_body(team)
