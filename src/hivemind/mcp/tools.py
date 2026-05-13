"""MCP tool definitions and handlers for hivemind.

The MCP surface is intentionally minimal. Knowledge access is *not*
exposed because experts can read or grep their own knowledge tree
directly via the standard file tools (``~/.config/opencode/experts/<name>/HEAD/*.md``
and ``~/.cache/hivemind/repos/<name>/`` are both
``external_directory: allow``).

Tools that remain:

* **Read/query** — ``list_agents``, ``show_agent``, ``status``.
* **Lifecycle mutations (fast, no AI)** — ``enable_agent``,
  ``disable_agent``, ``delete_agent``, ``redeploy``.
* **Curator-scoped pipeline** — four prep/finalize pairs that the
  ``hivemind-expert-curator`` subagent uses to run the slow operations
  in-session (no MCP timeout):
  ``prep_create_expert`` + ``finalize_create_expert``,
  ``prep_update_agent`` + ``finalize_update_agent``,
  ``prep_switch_version`` + ``finalize_switch_version``,
  ``prep_create_team`` + ``finalize_create_team``.
  The curator's permission allowlist names exactly these eight tools.
  The previous blocking ``update_agent`` / ``switch_version`` /
  ``create_team`` MCP tools have been removed — they were the leaky
  surface that forced orchestrator docs to mention CLI fallbacks.
* **Team roster mutations** (fast, no AI) — ``add_expert_to_team``,
  ``remove_expert_from_team``.
* **Cross-session** — ``list_sessions``, ``send_message``,
  ``delete_session``.

Cross-session forking-with-context goes through opencode's native
``Task(source_session_id=..., subagent_type=..., description=..., prompt=...)``
primitive (patches 0015/0016), not an MCP tool — that way the
orchestrator gets the standard ctrl-x-down drill-down. ``Task(task_id=...)``
resumes a prior subagent. The two are mutually exclusive.

Domain mutations fire the shared :mod:`hivemind.hooks` event themselves;
this module just registers two MCP-specific listeners at server startup
— one for the ``/global/reload-agents`` POST and one for
``ToolListChangedNotification``.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

from mcp.types import TextContent, Tool

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from mcp.server import Server

    from hivemind.models import AppConfig

    ToolHandler = Callable[..., Awaitable[list[TextContent]]]

log = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task[None]] = set()


def _text(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=msg)]


def _json_text(data: Any) -> list[TextContent]:
    return _text(json.dumps(data, indent=2, default=str))


def _agent_state(name: str, app_cfg: AppConfig) -> str:
    """Resolve enabled / disabled / unlisted from the local overlay."""
    if name in app_cfg.enabled:
        return "enabled"
    if name in app_cfg.disabled:
        return "disabled"
    return "unlisted"


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS: list[Tool] = [
    # --- Read/query ---
    Tool(
        name="list_agents",
        description="List agents in the catalog with their state (enabled / disabled / unlisted).",
        inputSchema={
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["enabled", "disabled", "unlisted", "all"],
                    "description": "Filter by state (default: all)",
                },
                "kind": {
                    "type": "string",
                    "enum": ["git_analyzed", "roster_templated", "user_supplied"],
                    "description": "Filter by agent kind",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="show_agent",
        description="Show detail for a single agent (kind, state, kind-specific body params).",
        inputSchema={
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Agent name"}},
            "required": ["name"],
        },
    ),
    Tool(
        name="status",
        description="Catalog summary: total / enabled / disabled / unlisted counts plus per-kind breakdown.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    # --- Lifecycle mutations (kind-agnostic) ---
    Tool(
        name="enable_agent",
        description="Enable an agent. Deploys its files (and for git_analyzed, ensures the repo is cloned).",
        inputSchema={
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Agent name to enable"}},
            "required": ["name"],
        },
    ),
    Tool(
        name="disable_agent",
        description="Disable an agent. Removes the deployed agent file while preserving backing data.",
        inputSchema={
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Agent name to disable"}},
            "required": ["name"],
        },
    ),
    Tool(
        name="delete_agent",
        description=(
            "Remove an agent entirely — deletes backing files and catalog entry. Memory is preserved by default."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Agent name to delete"},
                "purge_memory": {
                    "type": "boolean",
                    "description": "Also delete the agent's memory directory (default: false).",
                },
            },
            "required": ["name"],
        },
    ),
    # --- Curator-scoped pipeline (prep + finalize) ---
    # These primitives exist for the ``hivemind-expert-curator`` subagent
    # to run the slow operations (create expert, update expert,
    # switch_version, create team) in-session — its permission allowlist
    # names exactly these four pairs. Direct orchestrator calls work but
    # are unusual; the canonical path is
    # ``Task(subagent_type="hivemind-expert-curator", background=true,
    # prompt="...")`` which routes to the right pair internally.
    Tool(
        name="prep_create_expert",
        description=(
            "Stage 1 of the git_analyzed create pipeline. Clones the repo, "
            "resolves the commit, builds a staging directory, and returns "
            "the staging metadata (name, url, ref_name, commit, repo_dir, "
            "commit_dir, staging_root). Fast — no AI invoked here. Intended "
            "for use by the `hivemind-expert-curator` subagent (which has "
            "the analysis instructions baked into its own prompt and writes "
            "the 6 expected files into commit_dir). Pair with "
            "finalize_create_expert (stage 3) to land the catalog entry."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Git remote URL"},
                "ref": {"type": "string", "description": "Tag, branch, or commit (optional)"},
                "name": {
                    "type": "string",
                    "description": "Expert name (defaults to repo basename)",
                },
            },
            "required": ["url"],
        },
    ),
    Tool(
        name="finalize_create_expert",
        description=(
            "Stage 3 of the git_analyzed create pipeline. Locates the "
            "staging dir for `name` (created by prep_create_expert), "
            "validates that all 6 expected analysis files exist in it, "
            "moves the cloned repo + expert dir to their final cache "
            "locations, and registers the catalog entry as *unlisted*. "
            "Fast — no AI invoked. Call enable_agent afterwards to deploy."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Expert name (must match a staging dir from prep_create_expert)",
                },
            },
            "required": ["name"],
        },
    ),
    Tool(
        name="prep_update_agent",
        description=(
            "Stage 1 of the git_analyzed update pipeline. Fetches origin, "
            "resolves the latest commit, and stages the analysis input "
            "(preserves description.md + expertise.md from the prior "
            "commit). Returns staging metadata + analysis_prompt. Fast — "
            "no AI invoked here. If the agent is already at the latest "
            "commit, returns success with already_up_to_date=True and "
            "the staging fields unset. Pair with finalize_update_agent "
            "(stage 3) — the curator subagent writes the 4 fresh "
            "knowledge docs into commit_dir between prep and finalize."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Agent name to update"},
            },
            "required": ["name"],
        },
    ),
    Tool(
        name="finalize_update_agent",
        description=(
            "Stage 3 of the git_analyzed update pipeline. Locates the "
            "update-intent staging dir for `name`, validates the 4 "
            "expected fresh analysis docs (description.md + expertise.md "
            "are preserved from the prior commit by prep), moves the "
            "staged commit dir into the agent's expert dir, repoints "
            "HEAD, updates the catalog body's commit, fires the "
            "post-mutation hook. Fast — no AI invoked."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Agent name (must match a staging dir from prep_update_agent)",
                },
            },
            "required": ["name"],
        },
    ),
    Tool(
        name="prep_switch_version",
        description=(
            "Stage 1 of the git_analyzed switch_version pipeline. "
            "Resolves the ref (tag, branch, full or short SHA — tags "
            "fetched first) to a full commit SHA, then determines the "
            "finalize path. Returns `cached: true` (target commit's "
            "analysis docs already on disk — finalize is sub-second), "
            "`already_up_to_date: true` (HEAD already at the resolved "
            "commit), or staging metadata + analysis_prompt for the "
            "fresh path. Fast — no AI invoked here. Pair with "
            "finalize_switch_version (stage 3); the curator writes the "
            "6 expected files into commit_dir between prep and finalize "
            "only when cached=false."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Git-analyzed agent name"},
                "ref": {
                    "type": "string",
                    "description": (
                        "Target commit SHA (full or short), tag name, or branch name. "
                        "Resolved against the local clone (tags fetched first)."
                    ),
                },
            },
            "required": ["name", "ref"],
        },
    ),
    Tool(
        name="finalize_switch_version",
        description=(
            "Stage 3 of the git_analyzed switch_version pipeline. Two "
            "paths: cached (just repoint HEAD + checkout + post-mutation, "
            "sub-second) or fresh (validate the 6 expected files in the "
            "switch-intent staging dir, move into experts/<name>/<commit>/, "
            "then the cached-path tail). The cached vs fresh decision was "
            "made by prep_switch_version — finalize just executes the "
            "right tail. Fast — no AI invoked."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": (
                        "Git-analyzed agent name. Reads the prior prep_switch_version "
                        "result from the staging dir to know cached vs fresh."
                    ),
                },
            },
            "required": ["name"],
        },
    ),
    Tool(
        name="prep_create_team",
        description=(
            "Stage 1 of the roster_templated team-creation pipeline. "
            "Validates the team name is free, validates each expert "
            "exists, and sets up a staging directory with one section "
            "file slot per expert. Returns the staging metadata + "
            "per-expert input/output paths the curator subagent reads "
            "and writes. Fast — no AI invoked here. Pair with "
            "finalize_create_team (stage 3) to register the catalog "
            "entry as *unlisted*."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Team name"},
                "description": {"type": "string", "description": "Team description"},
                "experts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of expert names to include in the team's roster",
                },
            },
            "required": ["name", "description", "experts"],
        },
    ),
    Tool(
        name="finalize_create_team",
        description=(
            "Stage 3 of the roster_templated team-creation pipeline. "
            "Locates the create_team-intent staging dir for `name`, "
            "validates that every expected ``expert-<member>.md`` "
            "section file exists in it, moves them into "
            "``TEAMS_DIR/<name>/``, writes the team description and "
            "per-expert + team-lead notes stubs, and registers the "
            "catalog entry as *unlisted*. Fast — no AI invoked. Call "
            "enable_agent afterwards to deploy the team-lead agent."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Team name (must match a staging dir from prep_create_team)",
                },
            },
            "required": ["name"],
        },
    ),
    # --- Team roster management ---
    Tool(
        name="add_expert_to_team",
        description="Add an expert to a team's roster (team must be enabled).",
        inputSchema={
            "type": "object",
            "properties": {
                "team": {"type": "string", "description": "Team name"},
                "expert": {"type": "string", "description": "Expert name to add"},
            },
            "required": ["team", "expert"],
        },
    ),
    Tool(
        name="remove_expert_from_team",
        description="Remove an expert from a team's roster (team must be enabled).",
        inputSchema={
            "type": "object",
            "properties": {
                "team": {"type": "string", "description": "Team name"},
                "expert": {"type": "string", "description": "Expert name to remove"},
            },
            "required": ["team", "expert"],
        },
    ),
    # --- Cross-session messaging ---
    Tool(
        name="list_sessions",
        description=(
            "List opencode sessions someone is currently attached to via a TUI. By default "
            "returns only 'live' sessions — those with at least one open SSE subscription "
            "from a TUI. Returns id, parentID, title, updated timestamp, and (in tree mode) "
            "nested children. Pass live_only=False to see every session in the engine's DB."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "live_only": {
                    "type": "boolean",
                    "description": (
                        "Filter to sessions a TUI is currently attached to (default: true). "
                        "Subagents of a live root are included even though they don't have "
                        "their own SSE attachment."
                    ),
                },
                "tree": {
                    "type": "boolean",
                    "description": (
                        "Return a nested tree (each node has a 'children' array) instead of "
                        "a flat list. Sessions with parentID outside the result set become "
                        "roots in the returned tree. Default: false."
                    ),
                },
                "roots": {
                    "type": "boolean",
                    "description": "Only return root sessions (no parentID). Default: false.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of sessions to return. Default: 50.",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="send_message",
        description=(
            "Append a message to another session's inbox. For cross-session TUI messaging "
            "only — not for continuing expert conversations (use Task(task_id=...) to resume "
            "a subagent). Delivered immediately if that session is idle, queued and delivered "
            "on next idle if it's busy. Never throws BusyError — safe to ping a session "
            "that's mid-turn. Use list_sessions first to find the target session ID."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Target session ID (ses_...)"},
                "message": {"type": "string", "description": "Message text to append"},
            },
            "required": ["session_id", "message"],
        },
    ),
    Tool(
        name="delete_session",
        description=(
            "Hard-delete a session — typically a subagent that's no longer needed. "
            "Recursively deletes any descendant sessions. Aborts an in-flight prompt "
            "first so it stops cleanly. Updates the parent's footer subagent pill and "
            "drops the session from `list_sessions` automatically (fires `session.deleted` "
            "on the engine bus). Not recoverable. Idempotent — safe to re-issue. "
            "Intended for cleaning up stale/done subagents; deleting your own session "
            "mid-turn will orphan the conversation."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID to delete (ses_...)",
                },
            },
            "required": ["session_id"],
        },
    ),
    # --- System ---
    Tool(
        name="redeploy",
        description="Regenerate all agent files for every enabled agent from the current catalog.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]


# ---------------------------------------------------------------------------
# Handlers — read/query
# ---------------------------------------------------------------------------


async def _handle_list_agents(state: str, kind: str) -> list[TextContent]:
    from hivemind.agents import registry
    from hivemind.config import load_config

    app_cfg = load_config()
    rows: list[dict[str, str]] = []
    for agent in registry.all_agents():
        agent_state = _agent_state(agent.name, app_cfg)
        if state != "all" and agent_state != state:
            continue
        if kind and agent.kind != kind:
            continue
        rows.append({"name": agent.name, "kind": agent.kind, "state": agent_state})
    rows.sort(key=lambda r: r["name"])
    return _json_text(rows)


async def _handle_show_agent(name: str) -> list[TextContent]:
    from hivemind.agents import registry
    from hivemind.agents.git_analyzed import GitAnalyzedBody
    from hivemind.agents.roster_templated import RosterTemplatedBody
    from hivemind.agents.user_supplied import UserSuppliedBody
    from hivemind.config import load_config

    agent = registry.get(name)
    if agent is None:
        return _text(f"Error: agent '{name}' not found")

    app_cfg = load_config()
    detail: dict[str, Any] = {
        "name": agent.name,
        "kind": agent.kind,
        "state": _agent_state(agent.name, app_cfg),
    }
    body = agent.body
    if isinstance(body, GitAnalyzedBody):
        detail["remote"] = body.params.remote
        if body.params.commit:
            detail["commit"] = body.params.commit
        if body.params.ref_name:
            detail["ref_name"] = body.params.ref_name
    elif isinstance(body, RosterTemplatedBody):
        detail["description"] = body.params.description
        detail["experts"] = list(body.params.experts)
    elif isinstance(body, UserSuppliedBody):
        detail["filename"] = body.params.filename
    return _json_text(detail)


async def _handle_status() -> list[TextContent]:
    from hivemind.agents import registry
    from hivemind.config import load_config

    app_cfg = load_config()
    agents = registry.all_agents()
    counts = {"enabled": 0, "disabled": 0, "unlisted": 0}
    by_kind: dict[str, int] = {}
    for agent in agents:
        counts[_agent_state(agent.name, app_cfg)] += 1
        by_kind[agent.kind] = by_kind.get(agent.kind, 0) + 1
    return _json_text(
        {
            "total": len(agents),
            "enabled": counts["enabled"],
            "disabled": counts["disabled"],
            "unlisted": counts["unlisted"],
            "by_kind": by_kind,
        }
    )


# ---------------------------------------------------------------------------
# Handlers — lifecycle mutations
# ---------------------------------------------------------------------------


async def _handle_enable_agent(name: str) -> list[TextContent]:
    from hivemind.lifecycle import enable_agent

    result = enable_agent(name)
    if not result.success:
        return _text(f"Error: {result.error}")
    return _text(f"Agent '{name}' enabled and deployed.")


async def _handle_disable_agent(name: str) -> list[TextContent]:
    from hivemind.lifecycle import disable_agent

    result = disable_agent(name)
    if not result.success:
        return _text(f"Error: {result.error}")
    return _text(f"Agent '{name}' disabled.")


async def _handle_delete_agent(name: str, purge_memory: bool) -> list[TextContent]:
    from hivemind.lifecycle import delete_agent

    result = delete_agent(name, purge_memory=purge_memory)
    if not result.success:
        return _text(f"Error: {result.error}")
    suffix = " (memory purged)" if purge_memory else ""
    return _text(f"Agent '{name}' deleted{suffix}.")


# ---------------------------------------------------------------------------
# Handlers — curator-scoped expert pipeline (prep + finalize)
# ---------------------------------------------------------------------------


async def _handle_prep_create_expert(url: str, ref: str, name: str) -> list[TextContent]:
    from hivemind.agents.git_analyzed import prep_create_expert

    if not name:
        name = url.rstrip("/").split("/")[-1].removesuffix(".git")

    result = await prep_create_expert(name, url, ref_name=ref)
    if not result.success:
        return _text(f"Error: {result.error}")

    # ``analysis_prompt`` deliberately omitted: the curator subagent
    # has the analysis instructions baked into its own deployed body
    # (via the system_templated template's `{% include %}` of
    # prompts/create_expert.md.j2). Shipping the prompt back here would
    # be redundant — the curator just needs the path metadata.
    return _json_text(
        {
            "name": result.name,
            "url": result.url,
            "ref_name": result.ref_name,
            "commit": result.commit,
            "repo_dir": str(result.repo_dir),
            "commit_dir": str(result.commit_dir),
            "staging_root": str(result.staging_root),
        }
    )


async def _handle_finalize_create_expert(name: str) -> list[TextContent]:
    from hivemind.agents.git_analyzed import (
        finalize_create_expert,
        find_staged_prep,
        load_prep_result,
    )

    try:
        staging_root = find_staged_prep(name)
    except ValueError as exc:
        return _text(f"Error: {exc}")

    if staging_root is None:
        return _text(f"Error: no staging dir for '{name}' — call prep_create_expert first.")

    prep = load_prep_result(staging_root)
    if not prep.success:
        return _text(f"Error: {prep.error}")

    result = await finalize_create_expert(prep)
    if not result.success:
        return _text(f"Error: {result.error}")

    return _text(f"Expert '{name}' registered at {prep.commit[:12]}. Run enable_agent to deploy.")


async def _handle_prep_update_agent(name: str) -> list[TextContent]:
    from hivemind.agents.git_analyzed import prep_update_agent

    result = await prep_update_agent(name)
    if not result.success:
        return _text(f"Error: {result.error}")

    if result.already_up_to_date:
        return _json_text(
            {
                "name": result.name,
                "new_commit": result.new_commit,
                "old_commit": result.old_commit,
                "already_up_to_date": True,
            }
        )

    # ``analysis_prompt`` deliberately omitted — the curator subagent
    # has the update prompt baked into its own deployed body.
    return _json_text(
        {
            "name": result.name,
            "new_commit": result.new_commit,
            "old_commit": result.old_commit,
            "already_up_to_date": False,
            "repo_dir": str(result.repo_dir),
            "commit_dir": str(result.commit_dir),
            "staging_root": str(result.staging_root),
        }
    )


async def _handle_finalize_update_agent(name: str) -> list[TextContent]:
    from hivemind.agents import registry
    from hivemind.agents.git_analyzed import (
        finalize_update_agent,
        find_staged_update_prep,
        load_update_prep_result,
    )
    from hivemind.config import AGENTS_DIR
    from hivemind.deployment import regenerate_librarian

    try:
        staging_root = find_staged_update_prep(name)
    except ValueError as exc:
        return _text(f"Error: {exc}")

    if staging_root is None:
        return _text(f"Error: no update staging dir for '{name}' — call prep_update_agent first.")

    prep = load_update_prep_result(staging_root)
    if not prep.success:
        return _text(f"Error: {prep.error}")

    result = await finalize_update_agent(prep)
    if not result.success:
        return _text(f"Error: {result.error}")

    # Redeploy if the agent is currently enabled, so the new body lands
    # in opencode's agents/ dir without a separate enable_agent call.
    agent = registry.get(name)
    if agent is not None and agent.enabled:
        agent.deploy(agents_dir=AGENTS_DIR)
        regenerate_librarian()

    old_display = result.old_commit[:12] if result.old_commit else "none"
    return _text(f"Agent '{name}' updated from {old_display} to {result.new_commit[:12]}.")


async def _handle_prep_switch_version(name: str, ref: str) -> list[TextContent]:
    from hivemind.agents.git_analyzed import prep_switch_version

    result = await prep_switch_version(name, ref)
    if not result.success:
        return _text(f"Error: {result.error}")

    if result.already_up_to_date:
        return _json_text(
            {
                "name": result.name,
                "target_commit": result.target_commit,
                "old_commit": result.old_commit,
                "cached": True,
                "already_up_to_date": True,
            }
        )

    if result.cached:
        return _json_text(
            {
                "name": result.name,
                "target_commit": result.target_commit,
                "old_commit": result.old_commit,
                "cached": True,
                "already_up_to_date": False,
            }
        )

    # Fresh path — analyzer needs to write 6 files into commit_dir.
    return _json_text(
        {
            "name": result.name,
            "target_commit": result.target_commit,
            "old_commit": result.old_commit,
            "cached": False,
            "already_up_to_date": False,
            "repo_dir": str(result.repo_dir),
            "commit_dir": str(result.commit_dir),
            "staging_root": str(result.staging_root),
        }
    )


async def _handle_finalize_switch_version(name: str) -> list[TextContent]:
    from hivemind.agents import registry
    from hivemind.agents.git_analyzed import (
        finalize_switch_version,
        find_staged_switch_prep,
        load_switch_prep_result,
    )
    from hivemind.config import AGENTS_DIR
    from hivemind.deployment import regenerate_librarian

    try:
        staging_root = find_staged_switch_prep(name)
    except ValueError as exc:
        return _text(f"Error: {exc}")

    if staging_root is None:
        return _text(f"Error: no switch staging dir for '{name}' — call prep_switch_version first.")

    prep = load_switch_prep_result(staging_root)
    if not prep.success:
        return _text(f"Error: {prep.error}")

    result = await finalize_switch_version(prep)
    if not result.success:
        return _text(f"Error: {result.error}")

    # Redeploy if currently enabled.
    agent = registry.get(name)
    if agent is not None and agent.enabled:
        agent.deploy(agents_dir=AGENTS_DIR)
        regenerate_librarian()

    old_display = result.old_commit[:12] if result.old_commit else "none"
    return _text(f"Agent '{name}' switched from {old_display} to {result.new_commit[:12]}.")


async def _handle_prep_create_team(name: str, description: str, experts: list[str]) -> list[TextContent]:
    from hivemind.agents.roster_templated import prep_create_team

    result = await prep_create_team(name, description, experts)
    if not result.success:
        return _text(f"Error: {result.error}")

    return _json_text(
        {
            "name": result.name,
            "description": result.description,
            "experts": result.experts,
            "expert_paths": result.expert_paths,
            "staging_root": str(result.staging_root),
        }
    )


async def _handle_finalize_create_team(name: str) -> list[TextContent]:
    from hivemind.agents import registry
    from hivemind.agents.roster_templated import (
        finalize_create_team,
        find_staged_create_team_prep,
        load_create_team_prep_result,
    )
    from hivemind.config import AGENTS_DIR
    from hivemind.deployment import regenerate_librarian

    try:
        staging_root = find_staged_create_team_prep(name)
    except ValueError as exc:
        return _text(f"Error: {exc}")

    if staging_root is None:
        return _text(f"Error: no create_team staging dir for '{name}' — call prep_create_team first.")

    prep = load_create_team_prep_result(staging_root)
    if not prep.success:
        return _text(f"Error: {prep.error}")

    result = await finalize_create_team(prep)
    if not result.success:
        return _text(f"Error: {result.error}")

    # Redeploy if currently enabled (rare on first creation but harmless).
    agent = registry.get(name)
    if agent is not None and agent.enabled:
        agent.deploy(agents_dir=AGENTS_DIR)
        regenerate_librarian()

    experts_summary = ", ".join(prep.experts)
    return _text(f"Team '{name}' added to catalog with experts: {experts_summary}. Call enable_agent to deploy it.")


async def _handle_add_expert_to_team(team: str, expert: str) -> list[TextContent]:
    from hivemind.agents.roster_templated import add_expert_to_team

    result = await add_expert_to_team(team, expert)
    if not result.success:
        return _text(f"Error: {result.error}")
    return _text(f"Added '{expert}' to team '{team}'.")


async def _handle_remove_expert_from_team(team: str, expert: str) -> list[TextContent]:
    from hivemind.agents.roster_templated import remove_expert_from_team

    result = remove_expert_from_team(team, expert)
    if not result.success:
        return _text(f"Error: {result.error}")
    return _text(f"Removed '{expert}' from team '{team}'.")


# ---------------------------------------------------------------------------
# Handlers — cross-session messaging
# ---------------------------------------------------------------------------


def _slim_session(session: dict[str, Any]) -> dict[str, Any]:
    project = session.get("project") or {}
    meta = session.get("metadata") or {}
    return {
        "id": session.get("id"),
        "parentID": session.get("parentID"),
        "title": session.get("title"),
        "slug": session.get("slug"),
        "directory": session.get("directory"),
        "project": project.get("name") or project.get("worktree"),
        "branch": meta.get("git_branch"),
        "remote": meta.get("git_remote_url"),
        "updated": session.get("time", {}).get("updated"),
        "ephemeral": session.get("ephemeral"),
    }


def _build_session_tree(slim: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Nest sessions under their parents.

    Each input dict has at least ``id`` and ``parentID``. The output is
    a forest: any session whose ``parentID`` is missing from the input
    set becomes a root. Children are placed under their parent's
    ``children`` array, recursively.
    """
    by_id: dict[str, dict[str, Any]] = {}
    for s in slim:
        if s.get("id"):
            entry = dict(s)
            entry["children"] = []
            by_id[entry["id"]] = entry
    roots: list[dict[str, Any]] = []
    for entry in by_id.values():
        parent_id = entry.get("parentID")
        if parent_id and parent_id in by_id:
            by_id[parent_id]["children"].append(entry)
        else:
            roots.append(entry)
    return roots


async def _handle_list_sessions(
    live_only: bool,
    tree: bool,
    roots: bool,
    limit: int,
) -> list[TextContent]:
    from hivemind import opencode

    try:
        sessions = opencode.session_list(roots=roots or None, limit=limit)
    except RuntimeError as exc:
        return _text(f"Error: {exc}")

    if live_only:
        try:
            live = opencode.live_session_ids()
        except RuntimeError as exc:
            return _text(f"Error: {exc}")
        # Live filter applies to roots only — subagents render under their
        # live parent without needing their own SSE attachment.
        kept_ids: set[str] = set()
        for s in sessions:
            sid = s.get("id")
            parent_id = s.get("parentID")
            if not sid:
                continue
            if sid in live or (parent_id and parent_id in live):
                kept_ids.add(sid)
        # Second pass: include any session whose ancestor chain reaches a
        # live root (covers grandchildren of subagents, etc.).
        by_id = {s["id"]: s for s in sessions if s.get("id")}
        changed = True
        while changed:
            changed = False
            for s in sessions:
                sid = s.get("id")
                parent_id = s.get("parentID")
                if sid and sid not in kept_ids and parent_id in kept_ids and parent_id in by_id:
                    kept_ids.add(sid)
                    changed = True
        sessions = [s for s in sessions if s.get("id") in kept_ids]

    slim = [_slim_session(s) for s in sessions]
    for i, s in enumerate(slim):
        s["index"] = i + 1
    if tree:
        return _json_text(_build_session_tree(slim))
    return _json_text(slim)


async def _handle_send_message(session_id: str, message: str) -> list[TextContent]:
    from hivemind import opencode

    try:
        result = opencode.session_inbox(session_id, message)
    except RuntimeError as exc:
        return _text(f"Error: {exc}")
    state = "queued" if result.get("queued") else "delivered"
    return _text(f"Message {state} to {session_id} (queue depth: {result.get('depth', 0)}).")


async def _handle_delete_session(session_id: str) -> list[TextContent]:
    import httpx

    from hivemind import opencode

    try:
        opencode.session_delete(session_id)
    except RuntimeError as exc:
        return _text(f"Error: {exc}")
    except httpx.HTTPStatusError as exc:
        return _text(f"Error: {exc}")
    return _text(f"Deleted session {session_id}.")


# ---------------------------------------------------------------------------
# Handlers — system
# ---------------------------------------------------------------------------


async def _handle_redeploy() -> list[TextContent]:
    from hivemind.lifecycle import redeploy_all_agents

    result = redeploy_all_agents()
    if not result.success:
        return _text(f"Error: {result.error}")
    msg = f"Redeployed {len(result.experts_deployed)} expert(s) and {len(result.teams_deployed)} team(s)."
    if result.failed or result.teams_failed:
        parts = []
        if result.failed:
            parts.append(f"experts: {', '.join(result.failed)}")
        if result.teams_failed:
            parts.append(f"teams: {', '.join(result.teams_failed)}")
        msg += f" Failed — {'; '.join(parts)}."
    return _text(msg)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


TOOL_HANDLERS: dict[str, ToolHandler] = {
    "list_agents": _handle_list_agents,
    "show_agent": _handle_show_agent,
    "status": _handle_status,
    "enable_agent": _handle_enable_agent,
    "disable_agent": _handle_disable_agent,
    "delete_agent": _handle_delete_agent,
    "prep_create_expert": _handle_prep_create_expert,
    "finalize_create_expert": _handle_finalize_create_expert,
    "prep_update_agent": _handle_prep_update_agent,
    "finalize_update_agent": _handle_finalize_update_agent,
    "prep_switch_version": _handle_prep_switch_version,
    "finalize_switch_version": _handle_finalize_switch_version,
    "prep_create_team": _handle_prep_create_team,
    "finalize_create_team": _handle_finalize_create_team,
    "add_expert_to_team": _handle_add_expert_to_team,
    "remove_expert_from_team": _handle_remove_expert_from_team,
    "list_sessions": _handle_list_sessions,
    "send_message": _handle_send_message,
    "delete_session": _handle_delete_session,
    "redeploy": _handle_redeploy,
}


_ARG_EXTRACTORS: dict[str, Callable[[dict[str, Any]], tuple[Any, ...]]] = {
    "list_agents": lambda a: (str(a.get("state", "all")), str(a.get("kind", ""))),
    "show_agent": lambda a: (a["name"],),
    "status": lambda a: (),
    "redeploy": lambda a: (),
    "enable_agent": lambda a: (a["name"],),
    "disable_agent": lambda a: (a["name"],),
    "delete_agent": lambda a: (a["name"], bool(a.get("purge_memory", False))),
    "prep_create_expert": lambda a: (a["url"], str(a.get("ref", "")), str(a.get("name", ""))),
    "finalize_create_expert": lambda a: (a["name"],),
    "prep_update_agent": lambda a: (a["name"],),
    "finalize_update_agent": lambda a: (a["name"],),
    "prep_switch_version": lambda a: (a["name"], a["ref"]),
    "finalize_switch_version": lambda a: (a["name"],),
    "prep_create_team": lambda a: (a["name"], a["description"], a["experts"]),
    "finalize_create_team": lambda a: (a["name"],),
    "add_expert_to_team": lambda a: (a["team"], a["expert"]),
    "remove_expert_from_team": lambda a: (a["team"], a["expert"]),
    "list_sessions": lambda a: (
        bool(a.get("live_only", True)),
        bool(a.get("tree", False)),
        bool(a.get("roots", False)),
        int(a.get("limit", 50)),
    ),
    "send_message": lambda a: (a["session_id"], a["message"]),
    "delete_session": lambda a: (a["session_id"],),
}


def _extract_args(name: str, args: dict[str, Any]) -> tuple[Any, ...]:
    extractor = _ARG_EXTRACTORS.get(name)
    return extractor(args) if extractor else ()


def register_tools(server: Server) -> None:
    """Register tool endpoints and wire up post-mutation listeners."""
    from hivemind.hooks import register_post_mutation

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            return _text(f"Error: unknown tool '{name}'")
        args = arguments or {}
        try:
            extracted = _extract_args(name, args)
            return await handler(*extracted)
        except Exception as e:
            log.exception("Tool '%s' failed", name)
            return _text(f"Error executing {name}: {e}")

    # Post-mutation listeners — deferred reload (detached) + tools-changed (in-proc)
    register_post_mutation(_schedule_deferred_reload)

    def _schedule_tools_changed() -> None:
        task = asyncio.create_task(_safe_notify_tools_changed(server))
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

    register_post_mutation(_schedule_tools_changed)


def _schedule_deferred_reload() -> None:
    """POST ``/global/dispose`` synchronously.

    This almost always aborts the in-flight MCP tool call. Opencode's
    dispose finalizer (``mcp/index.ts:527-548``) SIGTERMs the hivemind
    MCP subprocess and closes its stdio as part of invalidating every
    cached ``InstanceState``. There is no finer-grained invalidation
    primitive — that's the only way to get opencode to re-scan
    ``agents/*.md``.

    The mutation has already landed on disk by the time this runs, so
    after the user resumes with ``continue`` the new state is visible.
    ``HIVEMIND.md`` documents the expected behaviour so main warns the
    user in advance and verifies with a read-only call after resumption.
    """
    from hivemind import opencode

    opencode.notify_instance_reload()


async def _safe_notify_tools_changed(server: Server) -> None:
    from hivemind.mcp.notify import notify_tools_changed

    try:
        await notify_tools_changed(server)
    except Exception:
        log.exception("notify_tools_changed failed")
