"""Kind-agnostic lifecycle verbs for hivemind agents.

These sit on top of :mod:`hivemind.agents.registry` and
:mod:`hivemind.opencode` and provide the uniform enable / disable / delete /
refresh / bootstrap surface that CLI, TUI, and MCP call into. Each mutation
tail is:

1. Mutate the registry (flip enabled state, or remove)
2. Deploy or undeploy the agent via ``Agent.deploy`` / ``Agent.undeploy``
3. Regenerate the librarian catalog
4. Fire the post-mutation hook so listeners (CLI/TUI/MCP) can notify opencode

Body-specific mutations (create a new expert, modify a team's roster, switch
expert version) live in the per-body modules under ``hivemind.agents.*``.
They also fire the post-mutation hook at their tail.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from hivemind import opencode

if TYPE_CHECKING:
    from collections.abc import Callable
from hivemind.agents import registry
from hivemind.agents.memory import (
    ensure_agent_memory,
    ensure_orchestrator_memory,
    remove_agent_memory,
)
from hivemind.config import (
    AGENTS_DIR,
    COMMANDS_DIR,
    HIVEMIND_ROOT,
    TEAMS_DIR,
    ensure_external_docs_link,
    ensure_repos_link,
)
from hivemind.deployment import regenerate_hivemind_md, regenerate_librarian
from hivemind.hooks import fire_post_mutation
from hivemind.models import (
    InitResult,
    OperationResult,
    ProgressCallback,
    RedeployResult,
)

log = logging.getLogger(__name__)


__all__ = [
    "bootstrap_workspace",
    "delete_agent",
    "disable_agent",
    "enable_agent",
    "redeploy_all_agents",
    "refresh_agent",
]


# ---------------------------------------------------------------------------
# enable / disable / delete
# ---------------------------------------------------------------------------


def enable_agent(name: str) -> OperationResult:
    """Flip the agent to enabled, deploy its files, regenerate librarian.

    Note: does not validate the opencode engine — ``enable`` writes an
    agent file and (for git-analyzed agents) symlinks the cached repo. It
    never invokes opencode's model. The creators that *do* spawn opencode
    (``create_git_expert``, ``update_git_expert``) validate for themselves.
    Skipping validation here keeps the MCP handler fast (~5 ms vs
    ~900 ms) so the tool response returns well before the post-mutation
    ``/global/dispose`` POST lands.
    """
    registry.load(refresh=True)
    agent = registry.get(name)
    if agent is None:
        return OperationResult(success=False, error=f"Agent '{name}' not found")

    already_enabled = agent.enabled
    if not already_enabled:
        registry.set_enabled(name, enabled=True)

    ensure_agent_memory(name)
    agent.deploy(agents_dir=AGENTS_DIR)
    regenerate_librarian()
    fire_post_mutation()

    return OperationResult(success=True)


def disable_agent(name: str) -> OperationResult:
    """Flip the agent to disabled, remove its deployed file, regenerate librarian."""
    registry.load(refresh=True)
    agent = registry.get(name)
    if agent is None:
        return OperationResult(success=False, error=f"Agent '{name}' not found")

    if agent.enabled:
        registry.set_enabled(name, enabled=False)

    agent.undeploy(agents_dir=AGENTS_DIR)
    regenerate_librarian()
    fire_post_mutation()

    return OperationResult(success=True)


def delete_agent(name: str, *, purge_memory: bool = False) -> OperationResult:
    """Remove the agent entirely from catalog + backing files.

    Memory files under the opencode memory tree are preserved by default;
    pass ``purge_memory=True`` to remove them as well.
    """
    registry.load(refresh=True)
    agent = registry.get(name)
    if agent is None:
        return OperationResult(success=False, error=f"Agent '{name}' not found")

    agent.undeploy(agents_dir=AGENTS_DIR)
    agent.body.on_delete()
    registry.remove(name)

    if purge_memory:
        remove_agent_memory(name)

    regenerate_librarian()
    fire_post_mutation()
    return OperationResult(success=True)


# ---------------------------------------------------------------------------
# refresh (dispatches to body-specific refresh functions)
# ---------------------------------------------------------------------------


async def refresh_agent(
    name: str,
    *,
    on_progress: ProgressCallback | None = None,
) -> OperationResult:
    """Refresh the agent's body (clone+analyze for git; no-op for others)."""
    registry.load(refresh=True)
    agent = registry.get(name)
    if agent is None:
        return OperationResult(success=False, error=f"Agent '{name}' not found")

    if agent.kind == "git_analyzed":
        from hivemind.agents.git_analyzed import update_git_expert

        result = await update_git_expert(name, on_progress=on_progress)
        if not result.success:
            return OperationResult(success=False, error=result.error or "refresh failed")
        # Redeploy if enabled so the new body is picked up
        if agent.enabled:
            agent.deploy(agents_dir=AGENTS_DIR)
            regenerate_librarian()
        return OperationResult(success=True)

    # roster_templated and future kinds don't have a refresh operation yet.
    return OperationResult(
        success=False,
        error=f"refresh is not supported for agent kind '{agent.kind}'",
    )


# ---------------------------------------------------------------------------
# redeploy (rewrite every agent file from its current catalog state)
# ---------------------------------------------------------------------------


def redeploy_all_agents() -> RedeployResult:
    """Redeploy every enabled agent from its current catalog state."""
    registry.load(refresh=True)

    failed: list[str] = []
    teams_failed: list[str] = []
    experts_deployed: list[str] = []
    teams_deployed: list[str] = []

    for agent in registry.enabled():
        try:
            agent.deploy(agents_dir=AGENTS_DIR)
        except Exception:
            log.exception("failed to redeploy %s", agent.name)
            if agent.kind == "roster_templated":
                teams_failed.append(agent.name)
            else:
                failed.append(agent.name)
            continue
        if agent.kind == "roster_templated":
            teams_deployed.append(agent.name)
        else:
            experts_deployed.append(agent.name)

    regenerate_librarian()
    fire_post_mutation()

    return RedeployResult(
        failed=failed,
        teams_failed=teams_failed,
        experts_deployed=experts_deployed,
        teams_deployed=teams_deployed,
    )


# ---------------------------------------------------------------------------
# bootstrap (opencode symlinks + all enabled agents + librarian + stale sweep)
# ---------------------------------------------------------------------------


def bootstrap_workspace(  # noqa: C901 — orchestrates distinct init phases; splitting hurts readability
    *,
    on_event: Callable[[str, str], None] | None = None,
) -> list[InitResult]:
    """Initialise the opencode workspace and deploy every enabled agent.

    Emits events via ``on_event(label, status)`` for UI rendering. Returns
    the list of :class:`InitResult` events also emitted to the callback, in
    order, for callers that prefer a final summary over streaming.
    """
    events: list[InitResult] = []

    def emit(label: str, status: str) -> None:
        events.append(InitResult(label=label, status=status))
        if on_event:
            on_event(label, status)

    # HIVEMIND.md is the target of one of the symlinks opencode creates
    regenerate_hivemind_md()
    emit("HIVEMIND.md", "generated")

    init_events = opencode.init_dirs(
        agents_dir=AGENTS_DIR,
        commands_dir=COMMANDS_DIR,
        rules_source=HIVEMIND_ROOT / "HIVEMIND.md",
        teams_dir=TEAMS_DIR,
    )
    for ev in init_events:
        events.append(ev)
        if on_event:
            on_event(ev.label, ev.status)

    ensure_repos_link()
    emit("repos/", "ready")
    ensure_external_docs_link()
    emit("external_docs/", "ready")

    # Orchestrator memory
    ensure_orchestrator_memory()
    emit("orchestrator memory", "ready")

    # Deploy every enabled agent
    registry.load(refresh=True)
    for agent in registry.enabled():
        try:
            ensure_agent_memory(agent.name)
            agent.deploy(agents_dir=AGENTS_DIR)
            emit(agent.name, "deployed")
        except Exception as exc:
            log.exception("failed to deploy %s", agent.name)
            emit(agent.name, f"failed: {exc}")

    # Sweep stale agent files from the agents/ dir
    if AGENTS_DIR.exists():
        enabled_names = {a.name for a in registry.enabled()}
        for f in AGENTS_DIR.glob("expert-*.md"):
            agent_name = f.name.removeprefix("expert-").removesuffix(".md")
            if agent_name not in enabled_names:
                f.unlink()
                emit(f.name, "removed (stale)")
        for f in AGENTS_DIR.glob("team-lead-*.md"):
            team_name = f.name.removeprefix("team-lead-").removesuffix(".md")
            if team_name not in enabled_names:
                f.unlink()
                emit(f.name, "removed (stale)")

    # Sweep stale expert symlinks in opencode experts dir
    provider_experts = opencode.home_dir() / "experts"
    if provider_experts.is_dir():
        enabled_names = {a.name for a in registry.enabled()}
        for link in provider_experts.iterdir():
            if link.name not in enabled_names:
                if link.is_symlink():
                    link.unlink()
                elif link.is_dir():
                    import shutil

                    shutil.rmtree(link)
                emit(link.name, "expert link removed (stale)")

    regenerate_librarian()
    emit("librarian", "regenerated")

    fire_post_mutation()
    return events


# ---------------------------------------------------------------------------
# Misc helpers exported for ingress use
# ---------------------------------------------------------------------------


# Re-export for convenience so ingress modules can do
# ``from hivemind import lifecycle`` and access everything.
# (Keeps imports tidy in cli.py / tui / mcp.)
