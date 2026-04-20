"""Single source of truth for agent CRUD.

The registry loads ``hivemind.json`` (catalog, committed) and ``config.json``
(enabled/disabled overlay, local), materialises concrete ``Agent`` objects,
and persists mutations back to the right file. CLI, TUI, and MCP all go
through this module; none of them poke the JSON files directly.
"""

from __future__ import annotations

from typing import assert_never

from hivemind.agents.base import Agent, AgentBody
from hivemind.config import load_config, load_hivemind, save_config, save_hivemind
from hivemind.models import (
    AppConfig,
    CatalogEntry,
    GitAnalyzedParams,
    HivemindConfig,
    RosterTemplatedParams,
)

__all__ = [
    "add",
    "all_agents",
    "all_names",
    "by_kind",
    "clear_cache",
    "enabled",
    "get",
    "get_or_raise",
    "is_enabled",
    "load",
    "remove",
    "set_enabled",
]


# ---------------------------------------------------------------------------
# Kind dispatch (typed via the discriminated-union CatalogEntry.body)
# ---------------------------------------------------------------------------


def _body_from_catalog(name: str, entry: CatalogEntry) -> AgentBody:
    """Materialise a concrete body from a typed catalog entry.

    ``entry.body`` is already a validated Pydantic params model (via the
    discriminated union on :class:`CatalogEntry`); we only need to pair it
    with a body class by ``isinstance``.
    """
    if isinstance(entry.body, GitAnalyzedParams):
        from hivemind.agents.git_analyzed import GitAnalyzedBody

        return GitAnalyzedBody(name=name, params=entry.body)
    if isinstance(entry.body, RosterTemplatedParams):
        from hivemind.agents.roster_templated import RosterTemplatedBody

        return RosterTemplatedBody(name=name, params=entry.body)
    assert_never(entry.body)


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------


_cache: dict[str, Agent] | None = None
_hivemind_cfg: HivemindConfig | None = None
_app_cfg: AppConfig | None = None


def load(*, refresh: bool = False) -> dict[str, Agent]:
    """Return ``{name: Agent}`` for every catalog entry, joined with the overlay."""
    global _cache, _hivemind_cfg, _app_cfg
    if _cache is not None and not refresh:
        return _cache

    _hivemind_cfg = load_hivemind()
    _app_cfg = load_config()

    enabled_set = set(_app_cfg.enabled)

    agents: dict[str, Agent] = {}
    for name, entry in _hivemind_cfg.agents.items():
        try:
            body = _body_from_catalog(name, entry)
        except Exception:
            # A broken entry shouldn't kill the whole load; skip it.
            import logging

            logging.getLogger(__name__).exception("failed to materialise agent %r", name)
            continue
        agents[name] = Agent(name=name, body=body, enabled=name in enabled_set)

    _cache = agents
    return _cache


def clear_cache() -> None:
    """Drop the in-memory cache (call after external config changes / tests)."""
    global _cache, _hivemind_cfg, _app_cfg
    _cache = None
    _hivemind_cfg = None
    _app_cfg = None


# ---------------------------------------------------------------------------
# Read API
# ---------------------------------------------------------------------------


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

    Writes the catalog entry to ``hivemind.json``. Does NOT flip enabled
    state — callers that want the agent live must also call
    ``set_enabled(name, True)`` (and deploy it).
    """
    agents = load()
    if agent.name in agents:
        msg = f"agent {agent.name!r} already in catalog"
        raise ValueError(msg)

    assert _hivemind_cfg is not None
    _hivemind_cfg.agents[agent.name] = _serialize_entry(agent.body)
    save_hivemind(_hivemind_cfg)

    agent.enabled = False
    agents[agent.name] = agent


def remove(name: str) -> None:
    """Remove an agent from the catalog and from any local overlay lists."""
    agents = load()
    agents.pop(name, None)

    assert _hivemind_cfg is not None
    assert _app_cfg is not None

    if name in _hivemind_cfg.agents:
        del _hivemind_cfg.agents[name]
        save_hivemind(_hivemind_cfg)

    dirty = False
    if name in _app_cfg.enabled:
        _app_cfg.enabled.remove(name)
        dirty = True
    if name in _app_cfg.disabled:
        _app_cfg.disabled.remove(name)
        dirty = True
    if dirty:
        save_config(_app_cfg)


def set_enabled(name: str, enabled: bool) -> None:
    """Flip enable/disable state for ``name`` in ``config.json``."""
    agent = get_or_raise(name)

    assert _app_cfg is not None
    dirty = False
    if enabled:
        if name not in _app_cfg.enabled:
            _app_cfg.enabled.append(name)
            dirty = True
        if name in _app_cfg.disabled:
            _app_cfg.disabled.remove(name)
            dirty = True
    else:
        if name in _app_cfg.enabled:
            _app_cfg.enabled.remove(name)
            dirty = True
        if name not in _app_cfg.disabled:
            _app_cfg.disabled.append(name)
            dirty = True

    if dirty:
        save_config(_app_cfg)

    agent.enabled = enabled


def save_body(agent: Agent) -> None:
    """Persist the agent's current body params back to ``hivemind.json``.

    Call this after a body-level mutation (commit bump, roster change, …).
    """
    assert _hivemind_cfg is not None
    if agent.name not in _hivemind_cfg.agents:
        msg = f"agent {agent.name!r} not in catalog"
        raise KeyError(msg)
    _hivemind_cfg.agents[agent.name] = _serialize_entry(agent.body)
    save_hivemind(_hivemind_cfg)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _serialize_entry(body: AgentBody) -> CatalogEntry:
    """Build a validated :class:`CatalogEntry` from a live body."""
    return CatalogEntry.model_validate({"kind": body.kind, "body": body.to_catalog()})
