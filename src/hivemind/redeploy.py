"""Redeploy orchestration for hivemind — sits above deployment and teams."""

from __future__ import annotations

from hivemind.config import get_active_provider, load_teams
from hivemind.deployment import (
    deploy_agent,
    deploy_expert,
    deploy_team_lead,
    flush_librarian,
    mark_librarian_dirty,
    regenerate_hivemind_md,
)
from hivemind.models import AppConfig, RedeployResult
from hivemind.teams import (
    refresh_expert_notes_header,
    refresh_team_lead_body,
    refresh_team_lead_notes_header,
)

__all__ = ["redeploy_all_agents"]


def redeploy_all_agents(config: AppConfig) -> RedeployResult:
    """Regenerate all enabled agent files with current provider settings."""
    # Validate engine/model before deploying any agents — deployed agents
    # reference the configured model, so if it's invalid they'll all fail at runtime.
    provider = get_active_provider()
    validation = provider.validate_engine()
    if not validation.success:
        return RedeployResult(
            success=False,
            error=f"Cannot redeploy: {validation.error}",
        )

    enabled = config.enabled

    deployed: list[str] = []
    failed: list[str] = []

    for name in enabled:
        if deploy_agent(name):
            deployed.append(name)
        else:
            failed.append(name)

    # Deploy expert directories to provider's experts/ location
    experts_deployed = [name for name in enabled if deploy_expert(name)]

    # Refresh team templates and redeploy team leads
    teams_deployed: list[str] = []
    teams_failed: list[str] = []
    teams = load_teams()
    for team_name, team_data in teams.items():
        refresh_team_lead_body(team_name)
        refresh_team_lead_notes_header(team_name)
        if deploy_team_lead(team_name):
            teams_deployed.append(f"team-lead-{team_name}")
        else:
            teams_failed.append(team_name)
        for expert_name in team_data.experts:
            refresh_expert_notes_header(team_name, expert_name)

    # Regenerate librarian and HIVEMIND.md
    mark_librarian_dirty()
    flush_librarian(config=config)
    regenerate_hivemind_md(config=config)

    return RedeployResult(
        failed=failed,
        teams_failed=teams_failed,
        experts_deployed=experts_deployed,
        teams_deployed=teams_deployed,
    )
