"""MCP tool definitions and handlers for hivemind.

The MCP surface is intentionally minimal. Knowledge access is *not*
exposed because experts can read or grep their own knowledge tree
directly via the standard file tools (``~/.config/opencode/experts/<name>/HEAD/*.md``
and ``~/.cache/hivemind/repos/<name>/`` are both
``external_directory: allow``).

Tools that remain:

* **Read/query** — ``list_agents``, ``show_agent``, ``status``.
* **Lifecycle mutations** — ``enable_agent``, ``disable_agent``,
  ``delete_agent``, ``update_agent``, ``redeploy``.
* **Kind-specific creators** —
  ``prep_create_expert`` + ``finalize_create_expert`` (the create
  pipeline split into stage 1 and stage 3 so the analysis stage is
  pluggable; the orchestrator typically spawns the
  ``hivemind-expert-curator`` subagent which performs all three stages
  in-session via Bash + Read/Grep/Write — no MCP timeout), ``create_team``.
* **Roster mutations** — ``add_expert_to_team``, ``remove_expert_from_team``.
* **Cross-session** — ``list_sessions``, ``send_message``.

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
    Tool(
        name="update_agent",
        description=(
            "Update an agent's body. For git_analyzed agents this fetches latest commits "
            "and re-runs AI analysis. Other kinds may not support update."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Agent name to update"},
                "skip_analysis": {
                    "type": "boolean",
                    "description": "For git_analyzed: pull latest commits without re-running AI analysis.",
                },
            },
            "required": ["name"],
        },
    ),
    Tool(
        name="switch_version",
        description=(
            "Switch a git_analyzed agent to a specific commit, tag, or branch. Refs "
            "(e.g. '8.5.1', 'main', 'origin/feat/x') are resolved against the cloned "
            "repo — tags are fetched first so freshly-pushed releases work. Re-uses "
            "cached analysis (description.md / expertise.md / agent.md) under the "
            "resolved commit if present; otherwise checks out the commit, runs AI "
            "analysis, and stores the result. Updates the HEAD symlink so the deployed "
            "agent body comes from this commit. Use show_agent first to see which "
            "commits are already analysed locally."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Git-analyzed agent name"},
                "commit": {
                    "type": "string",
                    "description": (
                        "Target commit SHA (full or short), tag name, or branch name. "
                        "If not a valid SHA in the local clone, resolved as a git ref "
                        "(tags fetched first)."
                    ),
                },
            },
            "required": ["name", "commit"],
        },
    ),
    # --- Kind-specific creators ---
    Tool(
        name="prep_create_expert",
        description=(
            "Stage 1 of the git_analyzed create pipeline. Clones the repo, "
            "resolves the commit, builds a staging directory, and returns "
            "the analysis prompt the analyzer (subagent or human) should "
            "follow to write the 6 expected files into commit_dir. Fast — "
            "no AI invoked here. Pair with finalize_create_expert (stage 3) "
            "to land the catalog entry. Prefer spawning the "
            "`hivemind-expert-curator` subagent (background=true) which "
            "performs all three stages in-session — no MCP timeout risk."
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
        name="create_team",
        description=(
            "Create a new team-lead agent with AI-generated per-expert sections. "
            "Added to the catalog in the *unlisted* state."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Team name"},
                "description": {"type": "string", "description": "Team description"},
                "experts": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of expert names to include",
                },
            },
            "required": ["name", "description", "experts"],
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
            "Append a message to another session's inbox. Delivered immediately if that "
            "session is idle, queued and delivered on next idle if it's busy. Never throws "
            "BusyError — safe to ping a session that's mid-turn. Use list_sessions first "
            "to find the target session ID."
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


async def _handle_update_agent(name: str, skip_analysis: bool) -> list[TextContent]:
    from hivemind.agents import registry
    from hivemind.agents.git_analyzed import update_git_expert
    from hivemind.config import AGENTS_DIR
    from hivemind.deployment import regenerate_librarian

    agent = registry.get(name)
    if agent is None:
        return _text(f"Error: agent '{name}' not found")

    if agent.kind == "git_analyzed":
        result = await update_git_expert(name, skip_analysis=skip_analysis)
        if not result.success:
            return _text(f"Error: {result.error}")
        if result.already_up_to_date:
            return _text(f"Agent '{name}' is already up to date ({result.new_commit[:12]}).")
        if agent.enabled:
            agent.deploy(agents_dir=AGENTS_DIR)
            regenerate_librarian()
        old_display = result.old_commit[:12] if result.old_commit else "none"
        return _text(f"Agent '{name}' updated from {old_display} to {result.new_commit[:12]}.")

    return _text(f"Error: update not supported for agent kind '{agent.kind}'")


async def _handle_switch_version(name: str, commit: str) -> list[TextContent]:
    from hivemind.agents import registry
    from hivemind.agents.git_analyzed import switch_version
    from hivemind.config import AGENTS_DIR
    from hivemind.deployment import regenerate_librarian

    agent = registry.get(name)
    if agent is None:
        return _text(f"Error: agent '{name}' not found")
    if agent.kind != "git_analyzed":
        return _text(f"Error: switch_version is only supported for git_analyzed agents (got '{agent.kind}')")

    result = await switch_version(name=name, target_commit=commit)
    if not result.success:
        return _text(f"Error: {result.error}")
    if result.already_up_to_date:
        return _text(f"Agent '{name}' is already at {result.new_commit[:12]}.")
    if agent.enabled:
        agent.deploy(agents_dir=AGENTS_DIR)
        regenerate_librarian()
    old_display = result.old_commit[:12] if result.old_commit else "none"
    return _text(f"Agent '{name}' switched from {old_display} to {result.new_commit[:12]}.")


# ---------------------------------------------------------------------------
# Handlers — kind-specific creators
# ---------------------------------------------------------------------------


async def _handle_prep_create_expert(url: str, ref: str, name: str) -> list[TextContent]:
    from hivemind.agents.git_analyzed import prep_create_expert

    if not name:
        name = url.rstrip("/").split("/")[-1].removesuffix(".git")

    result = await prep_create_expert(name, url, ref_name=ref)
    if not result.success:
        return _text(f"Error: {result.error}")

    return _json_text(
        {
            "name": result.name,
            "url": result.url,
            "ref_name": result.ref_name,
            "commit": result.commit,
            "repo_dir": str(result.repo_dir),
            "commit_dir": str(result.commit_dir),
            "staging_root": str(result.staging_root),
            "analysis_prompt": result.analysis_prompt,
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


async def _handle_create_team(name: str, description: str, experts: list[str]) -> list[TextContent]:
    from hivemind.agents.roster_templated import create_team

    result = await create_team(name, description, experts)
    if not result.success:
        return _text(f"Error: {result.error}")
    return _text(f"Team '{name}' added to catalog with experts: {', '.join(experts)}. Call enable_agent to deploy it.")


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
    return {
        "id": session.get("id"),
        "parentID": session.get("parentID"),
        "title": session.get("title"),
        "updated": session.get("time", {}).get("updated"),
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
        sessions = opencode.session_list(roots=roots if roots else None, limit=limit)
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
    "update_agent": _handle_update_agent,
    "switch_version": _handle_switch_version,
    "prep_create_expert": _handle_prep_create_expert,
    "finalize_create_expert": _handle_finalize_create_expert,
    "create_team": _handle_create_team,
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
    "update_agent": lambda a: (a["name"], bool(a.get("skip_analysis", False))),
    "switch_version": lambda a: (a["name"], a["commit"]),
    "prep_create_expert": lambda a: (a["url"], str(a.get("ref", "")), str(a.get("name", ""))),
    "finalize_create_expert": lambda a: (a["name"],),
    "create_team": lambda a: (a["name"], a["description"], a["experts"]),
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
