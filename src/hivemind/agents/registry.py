"""Single source of truth for agent CRUD.

The registry loads ``hivemind.json`` (catalog, committed) and ``config.json``
(enabled/disabled overlay, local), materialises concrete ``Agent`` objects,
and persists mutations back to the right file. CLI, TUI, and MCP all go
through this module; none of them poke the JSON files directly.

``roster_templated`` (team) entries live in ``config.json.teams``, not in
``hivemind.json.agents``, because ``teams/`` is gitignored and teams are
per-machine artifacts. All other agent kinds (``git_analyzed``,
``user_supplied``, ``system_templated``) live in the committed
``hivemind.json.agents`` catalog.

There is no cache. Every call re-reads both files. The previous
process-local cache caused stale reads in long-lived processes (notably
the MCP subprocess opencode spawns) when another process mutated the
JSON files. JSON parse on a ~50 KB catalog is sub-millisecond and these
helpers are not on a hot path.
"""

from __future__ import annotations

from typing import assert_never

from hivemind.agents.base import Agent, AgentBody
from hivemind.config import load_config, load_hivemind, save_config, save_hivemind
from hivemind.models import (
    CatalogEntry,
    GitAnalyzedParams,
    RosterTemplatedParams,
    SystemTemplatedParams,
    UserSuppliedParams,
)

__all__ = [
    "add",
    "all_agents",
    "all_names",
    "by_kind",
    "enabled",
    "get",
    "get_or_raise",
    "is_enabled",
    "load",
    "remove",
    "save_body",
    "set_enabled",
]


def _body_from_catalog(name: str, entry: CatalogEntry) -> AgentBody:
    """Materialise a concrete body from a typed catalog entry."""
    if isinstance(entry.body, GitAnalyzedParams):
        from hivemind.agents.git_analyzed import GitAnalyzedBody

        return GitAnalyzedBody(name=name, params=entry.body)
    if isinstance(entry.body, RosterTemplatedParams):
        from hivemind.agents.roster_templated import RosterTemplatedBody

        return RosterTemplatedBody(name=name, params=entry.body)
    if isinstance(entry.body, UserSuppliedParams):
        from hivemind.agents.user_supplied import UserSuppliedBody

        return UserSuppliedBody(name=name, params=entry.body)
    if isinstance(entry.body, SystemTemplatedParams):
        from hivemind.agents.system_templated import SystemTemplatedBody

        return SystemTemplatedBody(name=name, params=entry.body)
    assert_never(entry.body)


# ---------------------------------------------------------------------------
# Read API
# ---------------------------------------------------------------------------


def load() -> dict[str, Agent]:
    """Return ``{name: Agent}`` for every catalog entry, joined with the overlay.

    ``roster_templated`` entries are sourced from ``config.json.teams``
    (per-machine, gitignored). All other kinds come from
    ``hivemind.json.agents`` (committed). On first encounter after an
    upgrade, any stale ``roster_templated`` entries in ``hivemind.json``
    are auto-migrated into ``config.json`` and removed from the committed
    catalog.
    """
    hivemind_cfg = load_hivemind()
    app_cfg = load_config()
    enabled_set = set(app_cfg.enabled)

    # Detect and auto-migrate stale roster_templated entries from
    # hivemind.json (committed) into config.json (per-machine).
    stale_roster: list[str] = []
    for name, entry in list(hivemind_cfg.agents.items()):
        if entry.kind == "roster_templated":
            stale_roster.append(name)
    if stale_roster:
        for name in stale_roster:
            entry = hivemind_cfg.agents.pop(name)
            if isinstance(entry.body, RosterTemplatedParams) and name not in app_cfg.teams:
                # Clone the params so we don't share a mutable ref.
                app_cfg.teams[name] = RosterTemplatedParams(
                    description=entry.body.description,
                    experts=list(entry.body.experts),
                )
        save_hivemind(hivemind_cfg)
        save_config(app_cfg)

    agents: dict[str, Agent] = {}
    # Materialise from hivemind.json (committed catalog — all non-roster kinds).
    for name, entry in hivemind_cfg.agents.items():
        try:
            body = _body_from_catalog(name, entry)
        except Exception:
            import logging

            logging.getLogger(__name__).exception("failed to materialise agent %r", name)
            continue
        agents[name] = Agent(name=name, body=body, enabled=name in enabled_set)

    # Materialise teams from config.json.teams (per-machine).
    for name, params in app_cfg.teams.items():
        try:
            from hivemind.agents.roster_templated import RosterTemplatedBody

            body = RosterTemplatedBody(name=name, params=params)
            agents[name] = Agent(name=name, body=body, enabled=name in enabled_set)
        except Exception:
            import logging

            logging.getLogger(__name__).exception("failed to materialise team %r", name)
            continue

    return agents


def all_agents() -> list[Agent]:
    """Every agent in the catalog (enabled, disabled, unlisted)."""
    return list(load().values())


def all_names() -> list[str]:
    return sorted(load().keys())


def get(name: str) -> Agent | None:
    return load().get(name)


def get_or_raise(name: str) -> Agent:
    agent = load().get(name)
    if agent is None:
        msg = f"agent {name!r} not in catalog"
        raise KeyError(msg)
    return agent


def by_kind(kind: str) -> list[Agent]:
    return [a for a in load().values() if a.kind == kind]


def enabled() -> list[Agent]:
    return [a for a in load().values() if a.enabled]


def is_enabled(name: str) -> bool:
    agent = get(name)
    return bool(agent and agent.enabled)


# ---------------------------------------------------------------------------
# Mutation API
# ---------------------------------------------------------------------------


def add(agent: Agent) -> None:
    """Add a new agent to the catalog in the *unlisted* state.

    Writes the catalog entry to the appropriate file:
    ``hivemind.json`` for most kinds, ``config.json.teams`` for
    ``roster_templated``. Does NOT flip enabled state — callers that
    want the agent live must also call ``set_enabled(name, True)``
    (and deploy it).
    """
    if agent.kind == "roster_templated":
        from hivemind.agents.roster_templated import RosterTemplatedBody

        app_cfg = load_config()
        if agent.name in app_cfg.teams:
            msg = f"team {agent.name!r} already in catalog"
            raise ValueError(msg)
        assert isinstance(agent.body, RosterTemplatedBody)
        app_cfg.teams[agent.name] = agent.body.params
        save_config(app_cfg)
    else:
        hivemind_cfg = load_hivemind()
        if agent.name in hivemind_cfg.agents:
            msg = f"agent {agent.name!r} already in catalog"
            raise ValueError(msg)
        hivemind_cfg.agents[agent.name] = _serialize_entry(agent.body)
        save_hivemind(hivemind_cfg)


def _serialize_entry(body: AgentBody) -> CatalogEntry:
    """Build a validated :class:`CatalogEntry` from a live body."""
    return CatalogEntry.model_validate({"kind": body.kind, "body": body.to_catalog()})


def save_body(agent: Agent) -> None:
    """Persist the agent's current body params back to its catalog file.

    Call this after a body-level mutation (commit bump, roster change, …).
    """
    if agent.kind == "roster_templated":
        from hivemind.agents.roster_templated import RosterTemplatedBody

        app_cfg = load_config()
        if agent.name not in app_cfg.teams:
            msg = f"team {agent.name!r} not in catalog"
            raise KeyError(msg)
        assert isinstance(agent.body, RosterTemplatedBody)
        app_cfg.teams[agent.name] = agent.body.params
        save_config(app_cfg)
    else:
        hivemind_cfg = load_hivemind()
        if agent.name not in hivemind_cfg.agents:
            msg = f"agent {agent.name!r} not in catalog"
            raise KeyError(msg)
        hivemind_cfg.agents[agent.name] = _serialize_entry(agent.body)
        save_hivemind(hivemind_cfg)


def set_enabled(name: str, enabled: bool) -> None:
    """Flip enable/disable state for ``name`` in ``config.json``."""
    # Validate the agent exists in the catalog before mutating the overlay.
    get_or_raise(name)

    app_cfg = load_config()
    dirty = False
    if enabled:
        if name not in app_cfg.enabled:
            app_cfg.enabled.append(name)
            dirty = True
        if name in app_cfg.disabled:
            app_cfg.disabled.remove(name)
            dirty = True
    else:
        if name in app_cfg.enabled:
            app_cfg.enabled.remove(name)
            dirty = True
        if name not in app_cfg.disabled:
            app_cfg.disabled.append(name)
            dirty = True
    if dirty:
        save_config(app_cfg)


def remove(name: str) -> None:
    """Remove an agent from the catalog and from any local overlay lists."""
    # Determine where the agent lives — roster_templated entries are in
    # config.json.teams; everything else is in hivemind.json.agents.
    hivemind_cfg = load_hivemind()
    if name in hivemind_cfg.agents:
        del hivemind_cfg.agents[name]
        save_hivemind(hivemind_cfg)
    else:
        # Fall back to config.json.teams (roster_templated or stale entry).
        app_cfg = load_config()
        if name in app_cfg.teams:
            del app_cfg.teams[name]
            save_config(app_cfg)

    app_cfg = load_config()
    dirty = False
    if name in app_cfg.enabled:
        app_cfg.enabled.remove(name)
        dirty = True
    if name in app_cfg.disabled:
        app_cfg.disabled.remove(name)
        dirty = True
    if dirty:
        save_config(app_cfg)
