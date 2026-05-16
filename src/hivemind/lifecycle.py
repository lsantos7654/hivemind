"""Kind-agnostic lifecycle verbs for hivemind agents.

These sit on top of :mod:`hivemind.agents.registry` and
:mod:`hivemind.opencode` and provide the uniform enable / disable / delete /
update / sync surface that CLI, TUI, and MCP call into. Each mutation
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
    load_config,
)
from hivemind.deployment import regenerate_hivemind_md, regenerate_librarian
from hivemind.hooks import fire_post_mutation
from hivemind.models import (
    OperationResult,
    ProgressCallback,
    RedeployResult,
)

log = logging.getLogger(__name__)


__all__ = [
    "delete_agent",
    "disable_agent",
    "enable_agent",
    "sync_workspace",
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
            return OperationResult(success=False, error=result.error)
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
# sync (full workspace refresh: symlinks + deploy + stale sweep + librarian)
# ---------------------------------------------------------------------------


def sync_workspace(  # noqa: C901 — orchestrates distinct sync phases; splitting hurts readability
    *,
    on_event: Callable[[str, str], None] | None = None,
) -> RedeployResult:
    """Sync the opencode workspace: symlinks, runtime config, agents, sweep.

    The superset of what ``init`` and ``redeploy`` used to do separately.
    Every call is idempotent — stale files are swept, new user_supplied and
    system_templated agents are discovered, all enabled agents are deployed,
    and the librarian is regenerated.  Adding/removing files in
    ``opencode/{commands,skills,agents}/`` and running ``hivemind sync`` is
    all that's needed to make them live.

    Emits per-phase progress via ``on_event(label, status)`` for CLI/TUI
    rendering. Returns a :class:`RedeployResult` for programmatic callers
    (MCP, etc.).
    """

    def emit(label: str, status: str) -> None:
        if on_event:
            on_event(label, status)

    from hivemind.agents.user_supplied import sync_user_supplied_agents

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
        emit(ev.label, ev.status)

    ensure_repos_link()
    emit("repos/", "ready")
    ensure_external_docs_link()
    emit("external_docs/", "ready")

    ensure_orchestrator_memory()
    emit("orchestrator memory", "ready")

    sync_user_supplied_agents()
    emit("opencode/agents/", "synced")

    _seed_all_system_templated(emit)

    failed: list[str] = []
    teams_failed: list[str] = []
    experts_deployed: list[str] = []
    teams_deployed: list[str] = []

    for agent in registry.enabled():
        try:
            agent.deploy(agents_dir=AGENTS_DIR)
        except Exception:
            log.exception("failed to deploy %s", agent.name)
            if agent.kind == "roster_templated":
                teams_failed.append(agent.name)
            else:
                failed.append(agent.name)
            emit(agent.name, "failed: see log")
            continue
        if agent.kind == "roster_templated":
            teams_deployed.append(agent.name)
        else:
            experts_deployed.append(agent.name)
        emit(agent.name, "deployed")

    # Sweep stale agent files from the agents/ dir
    if AGENTS_DIR.exists():
        enabled_names = {a.name for a in registry.enabled()}
        unprefixed_enabled = {a.name for a in registry.enabled() if a.kind in ("user_supplied", "system_templated")}
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
        for f in AGENTS_DIR.glob("*.md"):
            if f.name.startswith(("expert-", "team-lead-")) or f.name == "librarian.md":
                continue
            stem = f.stem
            if stem not in unprefixed_enabled:
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

    return RedeployResult(
        failed=failed,
        teams_failed=teams_failed,
        experts_deployed=experts_deployed,
        teams_deployed=teams_deployed,
    )


def _seed_system_templated(
    emit: Callable[[str, str], None],
    name: str,
    template: str,
) -> None:
    """Idempotently seed a hivemind-managed ``system_templated`` agent.

    - Not in catalog: seed + auto-enable.
    - Already in catalog as ``system_templated`` and enabled: no-op.
    - Already in catalog but not enabled: auto-enable unless the user
      has explicitly disabled it (i.e. the name appears in
      ``config.json.disabled``).
    """
    existing = registry.get(name)
    if existing is not None:
        if existing.enabled:
            return
        # Agent exists but isn't enabled. Check whether the user
        # explicitly disabled it — if not (e.g. the entry landed in
        # hivemind.json via a teammate's push and this machine has
        # never seen it), auto-enable now.
        app_cfg = load_config()
        if name in app_cfg.disabled:
            return  # user explicitly disabled — respect their choice
        # Not explicitly disabled — treat as unlisted and auto-enable.
        registry.set_enabled(name, enabled=True)
        emit(name, "auto-enabled (was unlisted)")
        return
    try:
        from hivemind.agents.base import Agent
        from hivemind.agents.system_templated import SystemTemplatedBody
        from hivemind.models import SystemTemplatedParams

        body = SystemTemplatedBody(
            name=name,
            params=SystemTemplatedParams(template=template),
        )
        registry.add(Agent(name=name, body=body))
        registry.set_enabled(name, enabled=True)
        emit(name, "seeded + auto-enabled")
    except Exception as exc:
        log.exception("failed to seed %s", name)
        emit(name, f"seed failed: {exc}")


def _seed_all_system_templated(emit: Callable[[str, str], None]) -> None:
    """Auto-discover and seed every ``templates/agents/*.md.j2`` template.

    The name is derived from the filename: ``hivemind-crawler.md.j2`` →
    ``hivemind-crawler``. Drop a new ``.md.j2`` file in the directory and
    the next ``hivemind sync`` auto-registers it — no source-code edits
    needed.
    """
    from hivemind.templates import list_templates

    for path in list_templates():
        if not path.startswith("agents/") or not path.endswith(".md.j2"):
            continue
        filename = path.removeprefix("agents/")
        name = filename.removesuffix(".md.j2")
        _seed_system_templated(emit, name, path)


# ---------------------------------------------------------------------------
# Misc helpers exported for ingress use
# ---------------------------------------------------------------------------


# Re-export for convenience so ingress modules can do
# ``from hivemind import lifecycle`` and access everything.
# (Keeps imports tidy in cli.py / tui / mcp.)
