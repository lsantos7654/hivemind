"""MCP tool definitions and handlers for hivemind.

Each tool wraps existing core module functions with structured arguments
and returns text content suitable for LLM consumption.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

from mcp.types import TextContent, Tool

if TYPE_CHECKING:
    from mcp.server import Server

log = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task[None]] = set()


def _text(msg: str) -> list[TextContent]:
    """Wrap a string in the MCP text content response format."""
    return [TextContent(type="text", text=msg)]


def _json_text(data: Any) -> list[TextContent]:
    """Serialize data as indented JSON wrapped in MCP text content."""
    return _text(json.dumps(data, indent=2, default=str))


# --- Tool definitions ---

TOOLS: list[Tool] = [
    # Expert management
    Tool(
        name="list_experts",
        description="List all experts with their status, HEAD commit, version count, and team memberships.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="show_expert",
        description=(
            "Show detailed information about a specific expert including status, "
            "versions, remote URL, teams, and agent deployment status."
        ),
        inputSchema={
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Expert name"}},
            "required": ["name"],
        },
    ),
    Tool(
        name="enable_expert",
        description="Enable a disabled expert. Deploys its agent and makes it available as a subagent.",
        inputSchema={
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Expert name to enable"}},
            "required": ["name"],
        },
    ),
    Tool(
        name="disable_expert",
        description="Disable an enabled expert. Removes its agent file.",
        inputSchema={
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Expert name to disable"}},
            "required": ["name"],
        },
    ),
    Tool(
        name="add_expert",
        description=(
            "Register a new expert from a git repository URL. Clones the repo, runs AI analysis, "
            "generates knowledge docs, and deploys the agent. This is a long-running operation."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Git remote URL"},
                "ref": {"type": "string", "description": "Tag, branch, or commit (optional)"},
                "private": {"type": "boolean", "description": "Mark as private (won't be committed to git)"},
            },
            "required": ["url"],
        },
    ),
    Tool(
        name="delete_expert",
        description="Delete an expert entirely — removes all local data, agent files, and cached repos.",
        inputSchema={
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Expert name to delete"}},
            "required": ["name"],
        },
    ),
    Tool(
        name="update_expert",
        description="Fetch latest commits for an expert and re-analyze with AI.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Expert name to update"},
                "skip_analysis": {
                    "type": "boolean",
                    "description": "Pull latest repo changes without re-running AI analysis",
                },
            },
            "required": ["name"],
        },
    ),
    # Knowledge access
    Tool(
        name="get_knowledge",
        description=(
            "Read an expert's knowledge document content. Available docs: "
            "summary, code_structure, build_system, apis_and_interfaces, agent."
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
    # Team management
    Tool(
        name="list_teams",
        description="List all teams with their descriptions and expert rosters.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="show_team",
        description="Show detailed information about a team including roster, description, and file status.",
        inputSchema={
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Team name"}},
            "required": ["name"],
        },
    ),
    Tool(
        name="create_team",
        description="Create a new team with an AI-generated lead agent.",
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
    Tool(
        name="delete_team",
        description="Delete a team and its deployed agents.",
        inputSchema={
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Team name to delete"}},
            "required": ["name"],
        },
    ),
    Tool(
        name="add_expert_to_team",
        description="Add an expert to a team's roster.",
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
        description="Remove an expert from a team's roster.",
        inputSchema={
            "type": "object",
            "properties": {
                "team": {"type": "string", "description": "Team name"},
                "expert": {"type": "string", "description": "Expert name to remove"},
            },
            "required": ["team", "expert"],
        },
    ),
    # System
    Tool(
        name="status",
        description="Show hivemind dashboard: provider info, enabled/disabled experts, teams, and server status.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
    Tool(
        name="redeploy",
        description="Regenerate all agent files for the active provider.",
        inputSchema={"type": "object", "properties": {}, "required": []},
    ),
]


# --- Tool handlers ---


async def _handle_list_experts() -> list[TextContent]:
    from hivemind.config import (
        expert_names,
        get_expert_dir,
        get_head_commit,
        is_private_expert,
        load_config,
        load_repos,
        load_teams,
    )

    config = load_config()
    repos = load_repos()
    teams = load_teams()
    experts = expert_names()

    if not experts:
        return _text("No experts found. Use the add_expert tool to add one.")

    results = []
    for name in experts:
        expert_dir = get_expert_dir(name)
        head_commit = get_head_commit(expert_dir)

        if name in config.enabled:
            status = "enabled"
        elif name in config.disabled:
            status = "disabled"
        else:
            status = "unlisted"

        expert_teams = [t for t, td in teams.items() if name in td.experts]
        remote = repos.get(name, None)

        results.append(
            {
                "name": name,
                "status": status,
                "head": head_commit[:12] if head_commit else None,
                "private": is_private_expert(name),
                "teams": expert_teams,
                "remote": remote.remote if remote else None,
            }
        )

    return _json_text(results)


async def _handle_show_expert(name: str) -> list[TextContent]:
    from hivemind.config import (
        AGENTS_DIR,
        count_versions,
        expert_names,
        get_expert_dir,
        get_head_commit,
        is_private_expert,
        load_config,
        load_private_repos,
        load_repos,
        load_teams,
    )

    if name not in expert_names():
        return _text(f"Error: expert '{name}' not found")

    config = load_config()
    repos = load_repos()
    private_repos = load_private_repos()
    teams = load_teams()
    is_private = is_private_expert(name)

    expert_dir = get_expert_dir(name)
    head_commit = get_head_commit(expert_dir)
    version_count = count_versions(expert_dir)

    repos_dict = private_repos if is_private else repos
    remote = repos_dict.get(name)

    if name in config.enabled:
        status = "enabled"
    elif name in config.disabled:
        status = "disabled"
    else:
        status = "unlisted"

    expert_teams = [t for t, td in teams.items() if name in td.experts]
    agent_file = AGENTS_DIR / f"expert-{name}.md"

    result = {
        "name": name,
        "status": status,
        "private": is_private,
        "head": head_commit or None,
        "versions": version_count,
        "remote": remote.remote if remote else None,
        "ref": remote.ref_name if remote and remote.ref_name else None,
        "teams": expert_teams,
        "agent_deployed": agent_file.exists(),
    }

    return _json_text(result)


async def _handle_enable_expert(name: str) -> list[TextContent]:
    from hivemind.config import load_config
    from hivemind.experts import enable_expert

    config = load_config()
    result = await enable_expert(name, config=config)

    if not result.success:
        return _text(f"Error: {result.error}")

    msg = f"Expert '{name}' enabled and deployed."
    if result.already_enabled:
        msg = f"Expert '{name}' was already enabled. Ensured repo and agent link."
    return _text(msg)


async def _handle_disable_expert(name: str) -> list[TextContent]:
    from hivemind.config import load_config
    from hivemind.experts import disable_expert

    config = load_config()
    result = disable_expert(name, config=config)

    if not result.success:
        return _text(f"Error: {result.error}")

    msg = f"Expert '{name}' disabled."
    if result.already_disabled:
        msg = f"Expert '{name}' was already disabled."
    return _text(msg)


async def _handle_add_expert(url: str, ref: str, private: bool) -> list[TextContent]:
    from hivemind.experts import add_expert

    name = url.rstrip("/").split("/")[-1].removesuffix(".git")

    result = await add_expert(
        name,
        url,
        ref_name=ref,
        is_private=private,
    )

    if not result.success:
        return _text(f"Error: {result.error}")

    return _text(f"Expert '{name}' added and deployed successfully.")


async def _handle_delete_expert(name: str) -> list[TextContent]:
    from hivemind.config import load_config
    from hivemind.experts import delete_expert

    config = load_config()
    result = delete_expert(name, config=config)

    if not result.success:
        return _text(f"Error: {result.error}")

    return _text(f"Expert '{name}' deleted.")


async def _handle_update_expert(name: str, skip_analysis: bool) -> list[TextContent]:
    from hivemind.experts import update_expert

    result = await update_expert(name, skip_analysis=skip_analysis)

    if not result.success:
        return _text(f"Error: {result.error}")

    if result.already_up_to_date:
        return _text(f"Expert '{name}' is already up to date ({result.new_commit[:12]}).")

    old_display = result.old_commit[:12] if result.old_commit else "none"
    return _text(f"Expert '{name}' updated from {old_display} to {result.new_commit[:12]}.")


async def _handle_get_knowledge(expert: str, doc: str) -> list[TextContent]:
    from hivemind.config import expert_names, get_expert_dir

    if expert not in expert_names():
        return _text(f"Error: expert '{expert}' not found")

    expert_dir = get_expert_dir(expert)
    doc_path = expert_dir / "HEAD" / f"{doc}.md"

    if not doc_path.exists():
        available = [f.stem for f in (expert_dir / "HEAD").glob("*.md") if f.exists()]
        return _text(f"Error: document '{doc}' not found for expert '{expert}'. Available: {', '.join(available)}")

    content = doc_path.read_text(encoding="utf-8")
    return _text(content)


async def _handle_search_knowledge(query: str) -> list[TextContent]:
    from hivemind.config import expert_names, get_expert_dir, load_config

    config = load_config()
    query_lower = query.lower()
    results: list[dict[str, str | int]] = []

    for name in expert_names():
        if name not in config.enabled:
            continue

        expert_dir = get_expert_dir(name)
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
                            "expert": name,
                            "file": md_file.name,
                            "line": i,
                            "text": line.strip()[:200],
                        }
                    )

    if not results:
        return _text(f"No matches found for '{query}' across enabled expert knowledge docs.")

    return _json_text(results[:50])  # Cap at 50 results


async def _handle_list_teams() -> list[TextContent]:
    from hivemind.config import load_teams

    teams = load_teams()

    if not teams:
        return _text("No teams configured. Use the create_team tool to create one.")

    results = []
    for name, data in sorted(teams.items()):
        results.append(
            {
                "name": name,
                "description": data.description,
                "experts": data.experts,
                "size": len(data.experts),
            }
        )

    return _json_text(results)


async def _handle_show_team(name: str) -> list[TextContent]:
    from hivemind.config import TEAMS_DIR, load_teams

    teams = load_teams()
    if name not in teams:
        return _text(f"Error: team '{name}' not found")

    team = teams[name]
    team_dir = TEAMS_DIR / name

    expert_notes = {}
    for expert in team.experts:
        notes_path = team_dir / f"expert-{expert}" / "notes.md"
        expert_notes[expert] = notes_path.exists()

    result = {
        "name": name,
        "description": team.description,
        "experts": team.experts,
        "lead_exists": (team_dir / "lead.md").exists(),
        "expert_notes": expert_notes,
    }

    return _json_text(result)


async def _handle_create_team(name: str, description: str, experts: list[str]) -> list[TextContent]:
    from hivemind.config import load_config
    from hivemind.teams import create_team

    config = load_config()
    result = await create_team(name, description, experts, config=config)

    if not result.success:
        return _text(f"Error: {result.error}")

    return _text(f"Team '{name}' created with experts: {', '.join(experts)}.")


async def _handle_delete_team(name: str) -> list[TextContent]:
    from hivemind.config import load_config
    from hivemind.teams import delete_team

    config = load_config()
    result = delete_team(name, config=config)

    if not result.success:
        return _text(f"Error: {result.error}")

    return _text(f"Team '{name}' deleted.")


async def _handle_add_expert_to_team(team: str, expert: str) -> list[TextContent]:
    from hivemind.config import load_config
    from hivemind.teams import add_expert_to_team

    config = load_config()
    result = await add_expert_to_team(team, expert, config=config)

    if not result.success:
        return _text(f"Error: {result.error}")

    return _text(f"Added '{expert}' to team '{team}'.")


async def _handle_remove_expert_from_team(team: str, expert: str) -> list[TextContent]:
    from hivemind.config import load_config
    from hivemind.teams import remove_expert_from_team

    config = load_config()
    result = remove_expert_from_team(team, expert, config=config)

    if not result.success:
        return _text(f"Error: {result.error}")

    return _text(f"Removed '{expert}' from team '{team}'.")


async def _handle_status() -> list[TextContent]:
    from hivemind.config import get_active_provider, load_config, load_teams
    from hivemind.server import is_server_running, load_server_state

    provider = get_active_provider()
    config = load_config()
    teams = load_teams()

    server_info = None
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

    result = {
        "engine": provider.engine,
        "model": provider.model,
        "server": server_info or {"running": False},
        "experts": {
            "enabled": len(config.enabled),
            "disabled": len(config.disabled),
            "enabled_names": config.enabled,
            "disabled_names": config.disabled,
        },
        "teams": {name: {"description": td.description, "experts": td.experts} for name, td in teams.items()},
    }

    return _json_text(result)


async def _handle_redeploy() -> list[TextContent]:
    from hivemind.config import load_config
    from hivemind.redeploy import redeploy_all_agents

    config = load_config()
    result = redeploy_all_agents(config=config)

    if not result.success:
        return _text(f"Error: {result.error}")

    deployed_count = len(config.enabled) - len(result.failed)
    teams_count = len(result.teams_deployed)
    msg = f"Redeployed {deployed_count} expert(s) and {teams_count} team(s)."
    if result.failed:
        msg += f" Failed: {', '.join(result.failed)}."
    return _text(msg)


# --- Mutation tools that trigger hot-reload ---

_MUTATION_TOOLS = {
    "enable_expert",
    "disable_expert",
    "add_expert",
    "delete_expert",
    "update_expert",
    "create_team",
    "delete_team",
    "add_expert_to_team",
    "remove_expert_from_team",
    "redeploy",
}


# --- Dispatcher ---

TOOL_HANDLERS: dict[str, Any] = {
    "list_experts": _handle_list_experts,
    "show_expert": _handle_show_expert,
    "enable_expert": _handle_enable_expert,
    "disable_expert": _handle_disable_expert,
    "add_expert": _handle_add_expert,
    "delete_expert": _handle_delete_expert,
    "update_expert": _handle_update_expert,
    "get_knowledge": _handle_get_knowledge,
    "search_knowledge": _handle_search_knowledge,
    "list_teams": _handle_list_teams,
    "show_team": _handle_show_team,
    "create_team": _handle_create_team,
    "delete_team": _handle_delete_team,
    "add_expert_to_team": _handle_add_expert_to_team,
    "remove_expert_from_team": _handle_remove_expert_from_team,
    "status": _handle_status,
    "redeploy": _handle_redeploy,
}


def _extract_args(name: str, args: dict[str, Any]) -> tuple[Any, ...]:
    """Extract positional arguments for a tool handler from the raw args dict."""
    if name in ("list_experts", "list_teams", "status", "redeploy"):
        return ()
    if name in ("show_expert", "enable_expert", "disable_expert", "delete_expert", "show_team", "delete_team"):
        return (args["name"],)
    if name == "add_expert":
        return (args["url"], args.get("ref", ""), args.get("private", False))
    if name == "update_expert":
        return (args["name"], args.get("skip_analysis", False))
    if name == "get_knowledge":
        return (args["expert"], args.get("doc", "summary"))
    if name == "search_knowledge":
        return (args["query"],)
    if name == "create_team":
        return (args["name"], args["description"], args["experts"])
    if name in ("add_expert_to_team", "remove_expert_from_team"):
        return (args["team"], args["expert"])
    return ()


def register_tools(server: Server) -> None:
    """Register all hivemind tools on the MCP server."""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
        handler = TOOL_HANDLERS.get(name)
        if handler is None:
            return _text(f"Error: unknown tool '{name}'")

        args = arguments or {}

        result: list[TextContent]
        try:
            extracted = _extract_args(name, args)
            result = await handler(*extracted)
        except Exception as e:
            log.exception("Tool '%s' failed", name)
            result = _text(f"Error executing {name}: {e}")

        # Trigger hot-reload after mutation tools
        if name in _MUTATION_TOOLS:
            await _post_mutation_reload(server)

        return result


async def _post_mutation_reload(server: Server) -> None:
    """Send ToolListChangedNotification and trigger instance reload after mutations."""
    from hivemind.config import get_active_provider
    from hivemind.mcp.notify import notify_tools_changed

    await notify_tools_changed(server)

    # Fire the opencode dispose asynchronously. /global/dispose invalidates every
    # cached InstanceState including the one the TUI's current MCP tool call is
    # running in; running it synchronously here cancels the in-flight tool before
    # the result reaches opencode. Deferring lets the tool_result propagate first.
    provider = get_active_provider()
    task = asyncio.create_task(_deferred_reload(provider))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def _deferred_reload(provider: Any) -> None:
    from hivemind.mcp.notify import notify_instance_reload

    try:
        await asyncio.sleep(0.5)
        await asyncio.to_thread(notify_instance_reload, provider)
    except Exception:
        log.exception("deferred opencode reload failed")
