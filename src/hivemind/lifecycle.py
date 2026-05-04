"""Kind-agnostic lifecycle verbs for hivemind agents.

These sit on top of :mod:`hivemind.agents.registry` and
:mod:`hivemind.opencode` and provide the uniform enable / disable / delete /
update / bootstrap surface that CLI, TUI, and MCP call into. Each mutation
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
    ensure_orchestrator_memory,
    remove_agent_memory,
)
from hivemind.config import (
    AGENTS_DIR,
    COMMANDS_DIR,
    HIVEMIND_ROOT,
    SKILLS_DIR,
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
    "update_agent",
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
    agent = registry.get(name)
    if agent is None:
        return OperationResult(success=False, error=f"Agent '{name}' not found")

    already_enabled = agent.enabled
    if not already_enabled:
        registry.set_enabled(name, enabled=True)

    # ``Agent.deploy`` scaffolds memory itself (gated on memory_enabled).
    agent.deploy(agents_dir=AGENTS_DIR)
    regenerate_librarian()
    fire_post_mutation()

    return OperationResult(success=True)


def disable_agent(name: str) -> OperationResult:
    """Flip the agent to disabled, remove its deployed file, regenerate librarian."""
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
# update (dispatches to body-specific update functions)
# ---------------------------------------------------------------------------


async def update_agent(
    name: str,
    *,
    on_progress: ProgressCallback | None = None,
) -> OperationResult:
    """Update the agent's body (clone+analyze for git; no-op for others)."""
    agent = registry.get(name)
    if agent is None:
        return OperationResult(success=False, error=f"Agent '{name}' not found")

    if agent.kind == "git_analyzed":
        from hivemind.agents.git_analyzed import update_git_expert

        result = await update_git_expert(name, on_progress=on_progress)
        if not result.success:
            return OperationResult(success=False, error=result.error or "update failed")
        # Redeploy if enabled so the new body is picked up
        if agent.enabled:
            agent.deploy(agents_dir=AGENTS_DIR)
            regenerate_librarian()
        return OperationResult(success=True)

    # roster_templated and future kinds don't have an update operation yet.
    return OperationResult(
        success=False,
        error=f"update is not supported for agent kind '{agent.kind}'",
    )


# ---------------------------------------------------------------------------
# redeploy (rewrite every agent file from its current catalog state)
# ---------------------------------------------------------------------------


def redeploy_all_agents() -> RedeployResult:
    """Redeploy every enabled agent from its current catalog state.

    Also re-runs ``opencode.init_dirs`` so the user-supplied
    ``opencode/commands/`` and ``opencode/skills/`` directories are
    re-symlinked into the opencode home on every redeploy. ``init_dirs``
    is idempotent — adding/removing files in those directories then
    running ``hivemind redeploy`` is enough to make them live without a
    separate ``hivemind init`` step.

    Also syncs ``opencode/agents/<name>.md`` files into the catalog as
    ``user_supplied`` entries. Drop a markdown file in that directory
    and it lands as an unlisted agent the user can ``enable_agent`` to
    deploy.
    """
    from hivemind.agents.user_supplied import sync_user_supplied_agents

    opencode.init_dirs(
        agents_dir=AGENTS_DIR,
        commands_dir=COMMANDS_DIR,
        skills_dir=SKILLS_DIR,
        rules_source=HIVEMIND_ROOT / "HIVEMIND.md",
        teams_dir=TEAMS_DIR,
    )
    sync_user_supplied_agents()

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
        skills_dir=SKILLS_DIR,
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

    # Reconcile user-supplied agents in opencode/agents/ before deploying.
    # Newly-discovered files land in the catalog as unlisted; removed
    # files drop their catalog entry. Existing user_supplied entries are
    # preserved (so a previously-enabled agent stays enabled across
    # bootstraps).
    from hivemind.agents.user_supplied import sync_user_supplied_agents

    sync_user_supplied_agents()
    emit("opencode/agents/", "synced")

    # Auto-enable the curator subagent so the chat-TUI orchestrator can
    # always Task() it without an extra manual `enable_agent` step. The
    # curator is a user_supplied agent shipped under opencode/agents/;
    # it lands in the catalog via sync_user_supplied_agents() above and
    # we flip it to enabled here. Idempotent — set_enabled is a no-op
    # when already enabled.
    _curator_name = "hivemind-expert-curator"
    _curator = registry.get(_curator_name)
    if _curator is not None and not _curator.enabled:
        try:
            registry.set_enabled(_curator_name, True)
            emit(_curator_name, "auto-enabled")
        except Exception as exc:
            log.exception("failed to auto-enable %s", _curator_name)
            emit(_curator_name, f"auto-enable failed: {exc}")

    # Deploy every enabled agent. ``Agent.deploy`` handles memory tree
    # scaffolding internally per the agent's ``memory_enabled`` flag —
    # no explicit ``ensure_agent_memory`` call needed here.
    for agent in registry.enabled():
        try:
            agent.deploy(agents_dir=AGENTS_DIR)
            emit(agent.name, "deployed")
        except Exception as exc:
            log.exception("failed to deploy %s", agent.name)
            emit(agent.name, f"failed: {exc}")

    # Sweep stale agent files from the agents/ dir
    if AGENTS_DIR.exists():
        enabled_names = {a.name for a in registry.enabled()}
        user_supplied_enabled = {a.name for a in registry.enabled() if a.kind == "user_supplied"}
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
        # User-supplied agents land as ``<name>.md`` (no prefix). Sweep
        # any unprefixed *.md that's not in the enabled-user_supplied set
        # and not the librarian.
        for f in AGENTS_DIR.glob("*.md"):
            if f.name.startswith(("expert-", "team-lead-")) or f.name == "librarian.md":
                continue
            stem = f.stem
            if stem not in user_supplied_enabled:
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
