"""Unified agent abstraction.

Agents are the uniform deployable unit — experts, team leads, and future
kinds — composed of identity + an ``AgentBody`` body strategy. CRUD is
owned by :mod:`hivemind.agents.registry`; kind-specific creation lives in
the per-kind modules (:mod:`hivemind.agents.git_analyzed`,
:mod:`hivemind.agents.roster_templated`).
"""

from hivemind.agents.base import Agent, AgentBody

__all__ = ["Agent", "AgentBody"]
