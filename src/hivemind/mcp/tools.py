"""MCP tool definitions and handlers for hivemind.

The MCP surface is split into **kind-agnostic lifecycle tools** (list, show,
enable, disable, delete, refresh) and **kind-specific creators** (for
``create_git_expert`` and ``create_team``). Adding a new agent kind only
requires adding one new creator tool; the lifecycle tools automatically
cover it.

The post-mutation hot-reload used to be triggered from a dispatcher-level
``_MUTATION_TOOLS`` list here. That is gone: domain mutations fire the
shared :mod:`hivemind.hooks` event themselves, and this module just
registers two MCP-specific listeners at server startup — one for the
deferred ``/global/dispose`` POST (500 ms delayed to avoid cancelling the
in-flight tool) and one for ``ToolListChangedNotification``.
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
    # --- Lifecycle (kind-agnostic) ---
    Tool(
        name="list_agents",
        description="List every agent in the catalog, with kind, enabled state, and summary metadata.",
        inputSchema={
            "type": "object",
            "properties": {
                "kind": {
                    "type": "string",
                    "description": (
                        "Optional filter: only return agents of this kind (e.g. 'git_analyzed', 'roster_templated')."
                    ),
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="show_agent",
        description="Show detailed information about a specific agent, including body-specific metadata.",
        inputSchema={
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Agent name"}},
            "required": ["name"],
        },
    ),
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
            "Create a new team-lead agent with an AI-generated lead.md. Added to the catalog in the *unlisted* state."
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
    # --- System ---
    Tool(
        name="status",
        description="Show hivemind dashboard: engine info, enabled/disabled counts, teams, and server status.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="redeploy",
        description="Regenerate all agent files for every enabled agent from the current catalog.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]


# ---------------------------------------------------------------------------
# Handlers — lifecycle
# ---------------------------------------------------------------------------


async def _handle_list_agents(kind: str | None) -> list[TextContent]:
    from hivemind.agents import registry

    registry.load(refresh=True)
    agents = registry.by_kind(kind) if kind else registry.all_agents()
    if not agents:
        return _text("No agents found." + (f" (kind={kind})" if kind else ""))

    results: list[dict[str, Any]] = [
        {
            "name": agent.name,
            "kind": agent.kind,
            "enabled": agent.enabled,
            "description": agent.description,
        }
        for agent in sorted(agents, key=lambda a: a.name)
    ]
    return _json_text(results)


async def _handle_show_agent(name: str) -> list[TextContent]:
    from hivemind.agents import registry
    from hivemind.config import AGENTS_DIR, count_versions, get_expert_dir, get_head_commit
    from hivemind.opencode import agent_filename

    registry.load(refresh=True)
    agent = registry.get(name)
    if agent is None:
        return _text(f"Error: agent '{name}' not found")

    status = "enabled" if agent.enabled else "disabled"
    catalog_body = agent.body.to_catalog()

    extra: dict[str, Any] = {}
    if agent.kind == "git_analyzed":
        expert_dir = get_expert_dir(name)
        head_commit = get_head_commit(expert_dir)
        extra = {
            "head": head_commit,
            "versions": count_versions(expert_dir),
        }

    deployed_file = AGENTS_DIR / agent_filename(agent.kind, name)  # type: ignore[arg-type]
    return _json_text(
        {
            "name": name,
            "kind": agent.kind,
            "status": status,
            "description": agent.description,
            "body": catalog_body,
            "agent_deployed": deployed_file.exists(),
            **extra,
        }
    )


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

    registry.load(refresh=True)
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

    registry.load(refresh=True)
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
# Handlers — system
# ---------------------------------------------------------------------------


async def _handle_status() -> list[TextContent]:
    from hivemind import opencode
    from hivemind.agents import registry
    from hivemind.server import is_server_running, load_server_state

    registry.load(refresh=True)

    server_info: dict[str, Any] = {"running": False}
    if is_server_running():
        state = load_server_state()
        if state:
            server_info = {
                "running": True,
                "port": state.port,
                "hostname": state.hostname,
                "pid": state.pid,
                "started_at": state.started_at.isoformat(),
            }

    experts = list(registry.by_kind("git_analyzed"))
    teams = list(registry.by_kind("roster_templated"))

    cfg = opencode._cfg()
    try:
        engine_path = opencode._engine_path()
    except RuntimeError as e:
        engine_path = f"<unavailable: {e}>"
    return _json_text(
        {
            "engine": engine_path,
            "model": cfg.model,
            "server": server_info,
            "experts": {
                "enabled": sum(1 for a in experts if a.enabled),
                "disabled": sum(1 for a in experts if not a.enabled),
                "names": sorted(a.name for a in experts),
            },
            "teams": {
                a.name: {
                    "enabled": a.enabled,
                    "description": a.body.to_catalog().get("description", ""),
                    "experts": a.body.to_catalog().get("experts", []),
                }
                for a in teams
            },
        }
    )


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
    "status": _handle_status,
    "redeploy": _handle_redeploy,
}


def _extract_args(name: str, args: dict[str, Any]) -> tuple[Any, ...]:
    if name in ("status", "redeploy"):
        return ()
    if name == "list_agents":
        return (args.get("kind"),)
    if name in ("show_agent", "enable_agent", "disable_agent"):
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
