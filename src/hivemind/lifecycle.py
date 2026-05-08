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

    # Idempotent — seed the hivemind-managed system_templated agents
    # (curator + crawler) and backfill ref_name on git_analyzed entries
    # that lack it. Running here too (in addition to
    # ``bootstrap_workspace``) means ``hivemind redeploy`` is sufficient
    # to bring up new system agents and to migrate existing catalogs.
    def _noop_emit(label: str, status: str) -> None:
        pass

    _seed_system_templated(_noop_emit, "hivemind-expert-curator", "agents/hivemind-expert-curator.md.j2")
    _seed_system_templated(_noop_emit, "hivemind-crawler", "agents/hivemind-crawler.md.j2")
    _seed_system_templated(_noop_emit, "hivemind-memory-daemon", "agents/hivemind-memory-daemon.md.j2")
    _backfill_ref_names_for_git_agents(_noop_emit)

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

    # Seed hivemind-managed system_templated agents (the curator + the
    # crawler). They're rendered from
    # ``src/hivemind/templates/agents/<name>.md.j2`` rather than dropped
    # into ``opencode/agents/`` by the user. Auto-enabled on first seed;
    # subsequent bootstraps respect any explicit disable.
    #
    # Migration: earlier revisions shipped the curator as a user_supplied
    # agent under ``opencode/agents/``. If a stale catalog entry of that
    # kind exists, ``_seed_system_templated`` drops it before re-seeding.
    _seed_system_templated(emit, "hivemind-expert-curator", "agents/hivemind-expert-curator.md.j2")
    _seed_system_templated(emit, "hivemind-crawler", "agents/hivemind-crawler.md.j2")
    _seed_system_templated(emit, "hivemind-memory-daemon", "agents/hivemind-memory-daemon.md.j2")

    # One-shot migration: backfill ``ref_name`` on git_analyzed entries
    # that were added without ``--ref`` (so the catalog stored
    # ``ref_name=""``). Without this, ``show_agent`` returns a bare
    # commit SHA with no provenance and downstream consumers
    # (e.g. ``/hivemind_sync``) have to improvise via ``git describe``.
    # We resolve ``origin/HEAD`` for each repo and store the default
    # branch name (e.g. ``"main"``). Skip silently if the repo isn't
    # cloned locally — it'll get backfilled on the next add of that
    # expert via the forward fix in ``prep_create_expert``.
    _backfill_ref_names_for_git_agents(emit)

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
        # Both user_supplied and system_templated agents deploy as
        # ``<name>.md`` (no prefix), so the unprefixed-sweep needs to
        # know both kinds' enabled names to avoid deleting them.
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
        # Unprefixed agents (user_supplied + system_templated) land as
        # ``<name>.md``. Sweep any not in ``unprefixed_enabled`` (and not
        # the librarian).
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
    return events


def _seed_system_templated(
    emit: Callable[[str, str], None],
    name: str,
    template: str,
) -> None:
    """Idempotently seed a hivemind-managed ``system_templated`` agent.

    Three behaviors:

    - Stale entry of a different kind (e.g. legacy ``user_supplied``
      from an earlier shipping shape): drop it, then seed fresh.
    - Not in catalog: seed + auto-enable.
    - Already in catalog as ``system_templated``: no-op (respect the
      user's enable/disable state from prior bootstraps).
    """
    existing = registry.get(name)
    if existing is not None and existing.kind != "system_templated":
        try:
            registry.remove(name)
            emit(name, "migrated (dropped stale entry)")
            existing = None
        except Exception as exc:
            log.exception("failed to drop stale %s entry", name)
            emit(name, f"migration failed: {exc}")
            return
    if existing is not None:
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


def _backfill_ref_names_for_git_agents(emit: Callable[[str, str], None]) -> None:
    """One-shot: populate / repair ``ref_name`` for git_analyzed entries.

    Three cases:

    - ``ref_name == ""`` (initial backfill): resolve via
      :func:`resolve_commit_provenance` (tag-exact-match preferred,
      default branch fallback) and store the result.
    - ``ref_name`` matches the upstream default branch (auto-backfilled
      by an earlier run that didn't check tags): re-resolve and
      overwrite if the new value differs (catches the prior backfill's
      ``"master"``/``"main"`` answers when the commit IS at a tag).
    - ``ref_name`` is anything else (user-set tag, custom branch, etc.):
      leave alone.

    Idempotent — once each entry's ``ref_name`` is the right tag or
    a non-default-branch value, subsequent runs are no-ops. Skips
    silently when the cached repo isn't on disk (offline / never
    cloned) or when no ref resolves.
    """
    from hivemind.agents.base import run_coro_sync
    from hivemind.agents.git_analyzed import GitAnalyzedBody
    from hivemind.config import REPOS_DIR
    from hivemind.git import resolve_commit_provenance, resolve_default_branch

    for agent in registry.all_agents():
        if not isinstance(agent.body, GitAnalyzedBody):
            continue
        repo_dir = REPOS_DIR / agent.name
        if not repo_dir.is_dir():
            continue
        commit = agent.body.params.commit
        if not commit:
            continue
        current_ref = agent.body.params.ref_name

        # Decide whether this entry is eligible for re-resolution.
        if current_ref:
            try:
                default_branch = run_coro_sync(resolve_default_branch(repo_dir))
            except Exception:
                log.exception("failed to resolve origin/HEAD for %s", agent.name)
                continue
            if not default_branch or current_ref != default_branch:
                # User-set tag or custom branch — leave alone.
                continue
            # ``current_ref == default_branch`` → previously
            # auto-backfilled, safe to overwrite if there's a tag now.

        try:
            new_ref = run_coro_sync(resolve_commit_provenance(repo_dir, commit))
        except Exception:
            log.exception("failed to resolve commit provenance for %s", agent.name)
            continue
        if not new_ref or new_ref == current_ref:
            continue

        agent.body.params.ref_name = new_ref
        try:
            registry.save_body(agent)
            emit(agent.name, f"ref_name resolved to {new_ref}")
        except Exception as exc:
            log.exception("failed to save body after ref_name resolution for %s", agent.name)
            emit(agent.name, f"ref_name resolution failed: {exc}")


# ---------------------------------------------------------------------------
# Misc helpers exported for ingress use
# ---------------------------------------------------------------------------


# Re-export for convenience so ingress modules can do
# ``from hivemind import lifecycle`` and access everything.
# (Keeps imports tidy in cli.py / tui / mcp.)
