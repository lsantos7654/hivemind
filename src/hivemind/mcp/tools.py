"""MCP tool definitions and handlers for hivemind.

The MCP surface is intentionally **mutation + research only**. Listing,
inspecting, and status-dashboard tools were dropped because opencode
already discovers agents natively from ``agents/*.md`` and surfaces them
in its UI; duplicating that surface required a process-local catalog
cache that grew stale whenever another process (CLI, TUI, a different
opencode session) wrote to ``hivemind.json`` / ``config.json``. With
read-only catalog tools removed, callers either use opencode's native
discovery or read the JSON files directly.

Tools that remain:

* **Lifecycle mutations** — ``enable_agent``, ``disable_agent``,
  ``delete_agent``, ``refresh_agent``, ``redeploy``.
* **Kind-specific creators** — ``create_git_expert``, ``create_team``.
* **Roster mutations** — ``add_expert_to_team``, ``remove_expert_from_team``.
* **Knowledge research** — ``get_knowledge``, ``search_knowledge``
  (independent of opencode's agent surface; reads ``experts/<name>/HEAD/``
  knowledge docs).

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
        name="refresh_agent",
        description=(
            "Refresh an agent's body. For git_analyzed agents this fetches + re-analyzes; "
            "other kinds may not support refresh."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Agent name to refresh"},
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
    # --- Knowledge access ---
    Tool(
        name="get_knowledge",
        description=(
            "Read an expert's knowledge document content. "
            "Available docs: summary, code_structure, build_system, apis_and_interfaces, agent."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "expert": {"type": "string", "description": "Expert name"},
                "doc": {
                    "type": "string",
                    "description": "Document name (default: summary)",
                    "enum": ["summary", "code_structure", "build_system", "apis_and_interfaces", "agent"],
                },
            },
            "required": ["expert"],
        },
    ),
    Tool(
        name="search_knowledge",
        description="Search across all enabled experts' knowledge documents for a query string.",
        inputSchema={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        },
    ),
    # --- Cross-session messaging ---
    Tool(
        name="list_sessions",
        description=(
            "List opencode sessions in the running engine. Returns id, parentID, title, "
            "and updated timestamp for each. Useful before send_to_session / fork_session."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "roots": {
                    "type": "boolean",
                    "description": "Only return root sessions (no parentID). Default: false.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of sessions to return. Default: 20.",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="send_to_session",
        description=(
            "Append a message to another session's inbox. Delivered immediately if that "
            "session is idle, queued and delivered on next idle if it's busy. Never throws "
            "BusyError — useful for pinging a session that's mid-turn."
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
        name="send_to_main",
        description=(
            "Append a message to the user-facing root session (the most recently updated "
            "session with no parent). Use from inside a subagent to surface a finding to "
            "the user without waiting for the Task call to finish."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Message text to append"},
            },
            "required": ["message"],
        },
    ),
    Tool(
        name="fork_session",
        description=(
            "Fork an existing session (deep-copies its message history) and immediately "
            "send a follow-up prompt to the fork. Returns the new session's ID. "
            "Pass parent_id to make the fork a subagent of a chosen session (default: "
            "upstream sibling — parent_id=null)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Source session to fork"},
                "prompt": {"type": "string", "description": "Initial prompt for the fork"},
                "parent_id": {
                    "type": "string",
                    "description": "Attach the fork as a subagent of this session (optional).",
                },
                "message_id": {
                    "type": "string",
                    "description": "Truncate the fork's history at this message ID (optional).",
                },
            },
            "required": ["session_id", "prompt"],
        },
    ),
    Tool(
        name="continue_expert",
        description=(
            "Resume a conversation with an existing expert subagent by name. Looks up the "
            "most recently updated session whose title matches '@<name> subagent' and "
            "delivers the message via that session's inbox. Returns an error if no "
            "matching session exists — call Task(<name>, ...) first to spawn one."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Expert agent name (e.g. expert-opencode)"},
                "message": {"type": "string", "description": "Follow-up message"},
            },
            "required": ["name", "message"],
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


async def _handle_refresh_agent(name: str, skip_analysis: bool) -> list[TextContent]:
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

    return _text(f"Error: refresh not supported for agent kind '{agent.kind}'")


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
# Handlers — knowledge
# ---------------------------------------------------------------------------


async def _handle_get_knowledge(expert: str, doc: str) -> list[TextContent]:
    from hivemind.config import get_expert_dir

    expert_dir = get_expert_dir(expert)
    if not expert_dir.exists():
        return _text(f"Error: expert '{expert}' not found")

    doc_path = expert_dir / "HEAD" / f"{doc}.md"
    if not doc_path.exists():
        available = [f.stem for f in (expert_dir / "HEAD").glob("*.md") if f.exists()]
        return _text(f"Error: document '{doc}' not found for expert '{expert}'. Available: {', '.join(available)}")

    return _text(doc_path.read_text(encoding="utf-8"))


async def _handle_search_knowledge(query: str) -> list[TextContent]:
    from hivemind.agents import registry
    from hivemind.config import get_expert_dir

    query_lower = query.lower()
    results: list[dict[str, str | int]] = []

    for agent in registry.enabled():
        if agent.kind != "git_analyzed":
            continue
        expert_dir = get_expert_dir(agent.name)
        head_dir = expert_dir / "HEAD"
        if not head_dir.exists():
            continue

        for md_file in head_dir.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except OSError:
                continue

            for i, line in enumerate(content.splitlines(), 1):
                if query_lower in line.lower():
                    results.append(
                        {
                            "expert": agent.name,
                            "file": md_file.name,
                            "line": i,
                            "text": line.strip()[:200],
                        }
                    )

    if not results:
        return _text(f"No matches found for '{query}' across enabled expert knowledge docs.")
    return _json_text(results[:50])


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


async def _handle_list_sessions(roots: bool, limit: int) -> list[TextContent]:
    from hivemind import opencode

    try:
        sessions = opencode.session_list(roots=roots if roots else None, limit=limit)
    except RuntimeError as exc:
        return _text(f"Error: {exc}")
    return _json_text([_slim_session(s) for s in sessions])


async def _handle_send_to_session(session_id: str, message: str) -> list[TextContent]:
    from hivemind import opencode

    try:
        result = opencode.session_inbox(session_id, message)
    except RuntimeError as exc:
        return _text(f"Error: {exc}")
    state = "queued" if result.get("queued") else "delivered"
    return _text(f"Message {state} to {session_id} (queue depth: {result.get('depth', 0)}).")


async def _handle_send_to_main(message: str) -> list[TextContent]:
    from hivemind import opencode

    try:
        roots = opencode.session_list(roots=True, limit=1)
    except RuntimeError as exc:
        return _text(f"Error: {exc}")
    if not roots:
        return _text("Error: no root session is currently active in this engine.")
    target = roots[0]["id"]
    result = opencode.session_inbox(target, message)
    state = "queued" if result.get("queued") else "delivered"
    return _text(f"Message {state} to main session {target} (queue depth: {result.get('depth', 0)}).")


async def _handle_fork_session(
    session_id: str,
    prompt: str,
    parent_id: str,
    message_id: str,
) -> list[TextContent]:
    from hivemind import opencode

    try:
        forked = opencode.session_fork(
            session_id,
            message_id=message_id or None,
            parent_id=parent_id or None,
        )
    except RuntimeError as exc:
        return _text(f"Error: {exc}")
    new_id = forked["id"]
    opencode.session_inbox(new_id, prompt)
    return _json_text(
        {
            "forked_from": session_id,
            "new_session_id": new_id,
            "parent_id": forked.get("parentID"),
            "title": forked.get("title"),
            "prompt_delivered": True,
        }
    )


async def _handle_continue_expert(name: str, message: str) -> list[TextContent]:
    from hivemind import opencode

    try:
        sessions = opencode.session_list(limit=50)
    except RuntimeError as exc:
        return _text(f"Error: {exc}")
    needle = f"@{name} subagent"
    matching = [s for s in sessions if needle in (s.get("title") or "")]
    if not matching:
        return _text(
            f"Error: no live session for expert '{name}'. Use Task(subagent_type='{name}', ...) to spawn one first."
        )
    # session_list already returns most-recently-updated first.
    target = matching[0]
    result = opencode.session_inbox(target["id"], message)
    state = "queued" if result.get("queued") else "delivered"
    return _text(f"Message {state} to {name} session {target['id']} (queue depth: {result.get('depth', 0)}).")


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
    "refresh_agent": _handle_refresh_agent,
    "create_git_expert": _handle_create_git_expert,
    "create_team": _handle_create_team,
    "add_expert_to_team": _handle_add_expert_to_team,
    "remove_expert_from_team": _handle_remove_expert_from_team,
    "get_knowledge": _handle_get_knowledge,
    "search_knowledge": _handle_search_knowledge,
    "list_sessions": _handle_list_sessions,
    "send_to_session": _handle_send_to_session,
    "send_to_main": _handle_send_to_main,
    "fork_session": _handle_fork_session,
    "continue_expert": _handle_continue_expert,
    "redeploy": _handle_redeploy,
}


def _extract_args(name: str, args: dict[str, Any]) -> tuple[Any, ...]:
    if name == "redeploy":
        return ()
    if name in ("enable_agent", "disable_agent"):
        return (args["name"],)
    if name == "delete_agent":
        return (args["name"], bool(args.get("purge_memory", False)))
    if name == "refresh_agent":
        return (args["name"], bool(args.get("skip_analysis", False)))
    if name == "create_git_expert":
        return (args["url"], args.get("ref", ""))
    if name == "create_team":
        return (args["name"], args["description"], args["experts"])
    if name in ("add_expert_to_team", "remove_expert_from_team"):
        return (args["team"], args["expert"])
    if name == "get_knowledge":
        return (args["expert"], args.get("doc", "summary"))
    if name == "search_knowledge":
        return (args["query"],)
    if name == "list_sessions":
        return (bool(args.get("roots", False)), int(args.get("limit", 20)))
    if name == "send_to_session":
        return (args["session_id"], args["message"])
    if name == "send_to_main":
        return (args["message"],)
    if name == "fork_session":
        return (
            args["session_id"],
            args["prompt"],
            args.get("parent_id", ""),
            args.get("message_id", ""),
        )
    if name == "continue_expert":
        return (args["name"], args["message"])
    return ()


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
