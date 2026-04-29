"""MCP tool definitions and handlers for hivemind.

The MCP surface is intentionally minimal. Listing/inspecting/status
tools were dropped because opencode discovers agents natively from
``agents/*.md`` and surfaces them in its UI; knowledge access was
dropped because experts can read or grep their own knowledge tree
directly via the standard file tools (``~/.config/opencode/experts/<name>/HEAD/*.md``
and ``~/.cache/hivemind/repos/<name>/`` are both
``external_directory: allow``).

Tools that remain:

* **Lifecycle mutations** — ``enable_agent``, ``disable_agent``,
  ``delete_agent``, ``update_agent``, ``redeploy``.
* **Kind-specific creators** — ``create_git_expert``, ``create_team``.
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

    ToolHandler = Callable[..., Awaitable[list[TextContent]]]

log = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task[None]] = set()


def _text(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=msg)]


def _json_text(data: Any) -> list[TextContent]:
    return _text(json.dumps(data, indent=2, default=str))


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS: list[Tool] = [
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
    # --- Kind-specific creators ---
    Tool(
        name="create_git_expert",
        description=(
            "Register a new git-analyzed expert from a remote URL. Clones the repo, runs "
            "AI analysis, and adds the agent to the catalog in the *unlisted* state. "
            "Call `enable_agent` afterwards to deploy it."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Git remote URL"},
                "ref": {"type": "string", "description": "Tag, branch, or commit (optional)"},
            },
            "required": ["url"],
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
    # --- System ---
    Tool(
        name="redeploy",
        description="Regenerate all agent files for every enabled agent from the current catalog.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]


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


# ---------------------------------------------------------------------------
# Handlers — kind-specific creators
# ---------------------------------------------------------------------------


async def _handle_create_git_expert(url: str, ref: str) -> list[TextContent]:
    from hivemind.agents.git_analyzed import create_git_expert

    name = url.rstrip("/").split("/")[-1].removesuffix(".git")
    result = await create_git_expert(name, url, ref_name=ref)
    if not result.success:
        return _text(f"Error: {result.error}")
    return _text(f"Agent '{name}' added to catalog (unlisted). Call enable_agent to deploy it.")


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
    "enable_agent": _handle_enable_agent,
    "disable_agent": _handle_disable_agent,
    "delete_agent": _handle_delete_agent,
    "update_agent": _handle_update_agent,
    "create_git_expert": _handle_create_git_expert,
    "create_team": _handle_create_team,
    "add_expert_to_team": _handle_add_expert_to_team,
    "remove_expert_from_team": _handle_remove_expert_from_team,
    "list_sessions": _handle_list_sessions,
    "send_message": _handle_send_message,
    "redeploy": _handle_redeploy,
}


_ARG_EXTRACTORS: dict[str, Callable[[dict[str, Any]], tuple[Any, ...]]] = {
    "redeploy": lambda a: (),
    "enable_agent": lambda a: (a["name"],),
    "disable_agent": lambda a: (a["name"],),
    "delete_agent": lambda a: (a["name"], bool(a.get("purge_memory", False))),
    "update_agent": lambda a: (a["name"], bool(a.get("skip_analysis", False))),
    "create_git_expert": lambda a: (a["url"], a.get("ref", "")),
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
