# Prompt: Add `list_agents`, `show_agent`, and `status` read-only MCP tools to hivemind

## Goal

Add three read-only MCP tools to `src/hivemind/mcp/tools.py` so the orchestrator can query the catalog without hand-parsing JSON files. These tools are **not** mutations -- they do not fire post-mutation hooks or trigger reloads.

## Context

The file currently has a docstring (lines 1-29) explaining that read/query tools were intentionally dropped. That rationale no longer holds -- the orchestrator (main session) doesn't have native visibility into the catalog's three-way state (enabled / disabled / unlisted) and has been forced to read raw `hivemind.json` + `config.json` and replicate the join logic. The `search_knowledge` and `get_knowledge` tools should **not** be reintroduced -- bash access to expert directories is strictly better.

## Architecture

The file uses three parallel data structures -- all three must be extended consistently:

1. **`TOOLS`** (line 64): `list[Tool]` -- MCP `Tool` objects with `name`, `description`, `inputSchema` (JSON Schema dict).
2. **`TOOL_HANDLERS`** (line 516): `dict[str, ToolHandler]` -- maps tool name to `async` handler function.
3. **`_ARG_EXTRACTORS`** (line 532): `dict[str, Callable[[dict[str, Any]], tuple[Any, ...]]]` -- extracts positional args from the raw arguments dict.

Registration happens in `register_tools()` (line 558) which wires `@server.list_tools()` and `@server.call_tool()` -- no changes needed there since it iterates `TOOLS` and dispatches via `TOOL_HANDLERS`/`_ARG_EXTRACTORS`.

Return values use two helpers:
- `_text(msg)` -- human-readable string, used by mutation handlers
- `_json_text(data)` -- `json.dumps(data, indent=2, default=str)`, used by `list_sessions`

The read-only tools should use `_json_text()` for structured output.

## State model

An agent's state comes from the **join** of two files:
- `hivemind.json` has the catalog (`agents: dict[str, CatalogEntry]`): if a name is here, the agent exists.
- `config.json` has `enabled: list[str]` and `disabled: list[str]` (per-machine overlay).

Three states:
- **enabled**: name is in `config.json:enabled`
- **disabled**: name is in `config.json:disabled`
- **unlisted**: name is in `hivemind.json` but in neither `config.json` list

The `Agent` dataclass (`src/hivemind/agents/base.py`) only has a boolean `enabled` field, so disabled and unlisted both appear as `enabled=False`. To distinguish them, the handler must read `AppConfig` directly from `src/hivemind/config.py:load_config()`.

The registry module (`src/hivemind/agents/registry.py`) provides:
- `registry.all_agents() -> list[Agent]`
- `registry.get(name) -> Agent | None`
- `registry.enabled() -> list[Agent]`

Each `Agent` has: `name: str`, `body: AgentBody`, `enabled: bool`, `kind: str` (property from body), `description: str` (property from body).

Body kinds and their params:
- `git_analyzed`: `GitAnalyzedParams(remote: str, commit: str, ref_name: str)`
- `roster_templated`: `RosterTemplatedParams(description: str, experts: list[str])`
- `user_supplied`: `UserSuppliedParams(filename: str)`

Access params via `agent.body.params` (typed -- `GitAnalyzedParams | RosterTemplatedParams | UserSuppliedParams`).

## Tools to implement

### 1. `list_agents`

Lists all agents in the catalog with their state.

Input schema:
```json
{
  "type": "object",
  "properties": {
    "state": {
      "type": "string",
      "enum": ["enabled", "disabled", "unlisted", "all"],
      "description": "Filter by state (default: all)"
    },
    "kind": {
      "type": "string",
      "enum": ["git_analyzed", "roster_templated", "user_supplied"],
      "description": "Filter by agent kind"
    }
  },
  "required": []
}
```

Output: JSON array of objects, each with `name`, `kind`, `state` (one of `"enabled"`, `"disabled"`, `"unlisted"`). Sorted by name.

Handler: use `registry.all_agents()` for the agent list, `config.load_config()` for the `AppConfig` to compute state. Filter by `state` and `kind` if provided.

### 2. `show_agent`

Show detail for a single agent.

Input schema:
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Agent name"
    }
  },
  "required": ["name"]
}
```

Output: JSON object with `name`, `kind`, `state`, and kind-specific fields:
- `git_analyzed`: include `remote`, `commit`, `ref_name` (if non-empty)
- `roster_templated`: include `description`, `experts`
- `user_supplied`: include `filename`

Handler: use `registry.get(name)`, return error if not found. Compute state from `config.load_config()`. Access body params via `agent.body.params`.

### 3. `status`

Catalog summary.

Input schema:
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

Output: JSON object with:
- `total`: total agents in catalog
- `enabled`: count of enabled
- `disabled`: count of disabled
- `unlisted`: count of unlisted
- `by_kind`: `dict[str, int]` counting agents per kind

Handler: same data sources as `list_agents`, just aggregated.

## Implementation checklist

1. Update the module docstring (lines 1-29) to reflect that read/query tools have been restored. Remove the sentence about listing/inspecting/status tools being dropped. Add `list_agents`, `show_agent`, `status` to the "Tools that remain" list under a new bullet: `* **Read/query** -- list_agents, show_agent, status.`
2. Add three `Tool()` entries to the `TOOLS` list. Place them at the **top** of the list (before lifecycle mutations) under a `# --- Read/query ---` comment.
3. Implement a helper `_agent_state(name: str, app_cfg: AppConfig) -> str` near the top with the other helpers (`_text`, `_json_text`). It returns `"enabled"`, `"disabled"`, or `"unlisted"`. Import `AppConfig` under `if TYPE_CHECKING`.
4. Add three `async def _handle_*` functions. Group them under a `# Handlers -- read/query` section comment, placed **before** the existing `# Handlers -- lifecycle mutations` section. Each handler defers its domain imports inside the function body (matching the existing pattern).
5. Add entries to `TOOL_HANDLERS` and `_ARG_EXTRACTORS` dicts.

## Conventions

- `from __future__ import annotations` is already at the top.
- Imports used only for typing go under `if TYPE_CHECKING:`.
- Domain imports (`from hivemind.agents import registry`, `from hivemind.config import load_config`) are deferred inside handler bodies -- see every existing handler for the pattern.
- No `search_knowledge` or `get_knowledge` -- bash is better.
- These tools are read-only: no `fire_post_mutation()`, no reload, no `notify_tools_changed`.

## Verification

After implementing, run:
```bash
bazelisk test //...
```

All existing tests must pass. The new tools don't need new test files -- they're thin wrappers over `registry` + `config` which are already tested. Also restart opencode after the edit so the MCP subprocess picks up the new code, then verify the tools appear in the tool inventory.
