OpenCode exposes several distinct but interrelated interfaces: a terminal CLI, a typed in-process service layer, a built-in tool surface for agents, a typed HTTP API, generated SDKs, plugin hooks, and cloud/GitHub integrations. The codebase is highly schema-driven, so many of the most important APIs are expressed as `Schema.Struct(...)`, `Schema.Class(...)`, or `Context.Service<...>()` declarations rather than as traditional OO classes.

## CLI entrypoints

The primary executable entrypoint is `packages/opencode/src/index.ts`. It initializes logging, sets up process metadata, runs one-time database migration when needed, then registers a large yargs command tree. Notable exported command objects include:

- `RunCommand` for the main interactive agent flow.
- `ServeCommand` to start the HTTP server.
- `McpCommand` to manage MCP servers.
- `ProvidersCommand` and `ModelsCommand` for provider/model inspection and auth.
- `AgentCommand` to create/list agents.
- `GithubCommand` for GitHub integration setup and execution.
- `SessionCommand`, `DbCommand`, `StatsCommand`, `PrCommand`, `WebCommand`, `ExportCommand`, and `ImportCommand` for operational workflows.
- `AttachCommand` and `TuiThreadCommand` for terminal UI/session attachment flows.

From a user perspective, these commands are the canonical interface. The root README advertises installation methods and highlights the built-in `build`, `plan`, and `general` agent experience, while the GitHub Action README adds a comment-driven invocation style via `/opencode` or `/oc` in GitHub discussions.

## Agent model and built-in agents

`packages/opencode/src/agent/agent.ts` defines the core `Agent.Info` schema. Key fields include `name`, `description`, `mode` (`subagent`, `primary`, or `all`), `permission`, optional `model`, optional `variant`, optional `prompt`, and optional generation settings such as `temperature` or `topP`. The `Agent.Service` interface provides:

- `get(agent: string)`
- `list()`
- `defaultInfo()`
- `defaultAgent()`
- `generate({ description, model? })`

The same file constructs built-in agents such as:

- `build`: default full-access primary agent
- `plan`: read-only or edit-restricted planning mode
- `general`: general-purpose subagent for multi-step tasks
- `explore`: search-heavy codebase exploration subagent
- `scout`: optional docs/dependency-source specialist when experimental flags are enabled
- hidden support agents such as `compaction`, `title`, and `summary`

This is the authoritative place to understand permissions, default prompts, and agent availability.

## Session and message interfaces

The session subsystem is one of the most important internal APIs. `packages/opencode/src/session/session.ts` defines schemas like `Session.Info`, `ProjectInfo`, `GlobalInfo`, `CreateInput`, and `ForkInput`. `Session.Info` captures identifiers, directory/workspace metadata, parent/child relationships, token accounting, share URLs, titles, selected agent/model, permissions, summaries, revert metadata, and timestamps.

Related modules define adjacent types:

- `session/message.ts` and `session/message-v2.ts` describe message parts such as text, reasoning, tool invocation, files, snapshots, patches, agent parts, and subtask parts.
- `session/prompt.ts` exports `PromptInput`, `LoopInput`, `ShellInput`, and `CommandInput` for driving the prompt loop.
- `session/todo.ts`, `session/summary.ts`, `session/status.ts`, and `session/revert.ts` encapsulate todos, diffs, runtime state, and revert operations.

The `PromptInput` schema is especially useful when integrating programmatically. It allows callers to specify `sessionID`, optional `messageID`, optional `model`, optional `agent`, optional response `format`, optional system override, and an array of prompt `parts` composed from typed message-part schemas.

## Tool APIs

OpenCode’s agents operate through a first-class tool system. `packages/opencode/src/tool/registry.ts` is the composition root. It initializes built-in tools, merges plugin-defined tools, and exposes a `ToolRegistry.Service` with methods `ids()`, `all()`, `named()`, and `tools(...)`.

The built-in registry currently includes implementations for:

- file and search tools: `read`, `glob`, `grep`, `edit`, `write`, `apply_patch`
- execution and browsing tools: `shell`, `webfetch`, `websearch`
- orchestration tools: `task`, `task_status`, `todo`, `skill`, `question`, `plan`
- repository helpers: `repo_clone`, `repo_overview`
- optional `lsp`

Each tool has its own schema file, usually exporting a `Parameters` schema. For example, `tool/task.ts` defines `Parameters` with `description`, `prompt`, `subagent_type`, optional `task_id`, optional `command`, and optional `background`. The task tool is noteworthy because it can either spawn a new subagent session or resume a prior one, and it can run in foreground or background mode.

### Example: task tool payload

```ts
{
  description: "inspect provider bug",
  prompt: "Trace how ProviderV2.Info is resolved and summarize failure points",
  subagent_type: "explore",
  background: false,
}
```

This routes work to another agent session while preserving typed metadata about the child task.

## HTTP API and OpenAPI surface

The main server composition happens in `packages/opencode/src/server/routes/instance/httpapi/api.ts`. It builds three nested APIs:

- `RootHttpApi` for global and control routes
- `InstanceHttpApi` for project/session-scoped routes
- `OpenCodeHttpApi` combining root, event, instance, and PTY-connect APIs

`InstanceHttpApi` adds route groups for `config`, `experimental`, `file`, `instance`, `mcp`, `project`, `pty`, `question`, `permission`, `provider`, `session`, `sync`, `v2`, `tui`, and `workspace`. Route definitions are declared in group files under `server/routes/instance/httpapi/groups/` and implemented by handler files under `handlers/`.

The session group (`groups/session.ts`) is a good representative API. It declares route constants such as:

- `GET /session`
- `GET /session/status`
- `GET /session/:sessionID`
- `GET /session/:sessionID/children`
- `GET /session/:sessionID/todo`
- `GET /session/:sessionID/diff`
- `GET /session/:sessionID/message`
- `POST /session`
- `DELETE /session/:sessionID`
- `PATCH /session/:sessionID`
- `POST /session/:sessionID/fork`
- `POST /session/:sessionID/message`
- `POST /session/:sessionID/command`
- `POST /session/:sessionID/shell`
- `POST /session/:sessionID/revert`

These endpoints consume typed payloads derived from session schemas such as `Session.CreateInput`, `SessionPrompt.PromptInput`, `SessionPrompt.CommandInput`, `SessionPrompt.ShellInput`, and `SessionRevert.RevertInput`.

The root/global API (`groups/global.ts`) adds `GET /global/health`, `GET/PATCH /global/config`, `GET /global/event`, `POST /global/dispose`, and `POST /global/upgrade`. The MCP API (`groups/mcp.ts`) adds routes for status, dynamic server addition, OAuth auth start/callback/authenticate/remove, and connect/disconnect operations. The `v2` API (`groups/v2.ts`) groups experimental `session`, `message`, `model`, and `provider` surfaces under a versioned namespace.

### Example: server access

```ts
import { openapi, listen } from "@/server/server"

const spec = await openapi()
const listener = await listen({ hostname: "127.0.0.1", port: 4096 })
console.log(listener.url.toString())
```

`packages/opencode/src/server/server.ts` exposes `openapi()` and `listen(...)`, making it the main programmatic entrypoint for embedding or launching the server.

## SDK interfaces

`packages/sdk/js/package.json` exports several stable entrypoints:

- `@opencode-ai/sdk`
- `@opencode-ai/sdk/client`
- `@opencode-ai/sdk/server`
- `@opencode-ai/sdk/v2`
- `@opencode-ai/sdk/v2/client`
- `@opencode-ai/sdk/v2/gen/client`
- `@opencode-ai/sdk/v2/server`

The SDK build script generates `src/v2/gen` directly from the OpenAPI document produced by the live server, so the SDK is effectively a typed façade over the server routes. For external consumers, these SDK exports are the most convenient way to integrate without hand-authoring HTTP requests.

## Core/provider/LLM interfaces

`packages/core/src/provider.ts` defines the canonical provider schema. `ProviderV2.ID` includes well-known providers such as `opencode`, `anthropic`, `openai`, `google`, `google-vertex`, `github-copilot`, `amazon-bedrock`, `azure`, `openrouter`, `mistral`, and `gitlab`. `ProviderV2.Info` records provider identity, enablement state, environment variables, endpoint type, and request options. `Endpoint` is a tagged union that currently supports `openai/responses`, `openai/completions`, `anthropic/messages`, `aisdk`, and `unknown` endpoint forms.

`packages/core/src/catalog.ts` builds on this with a `CatalogV2.Service` that manages provider/model lookup, updates, default model selection, and “small model” heuristics. Methods include `provider.get`, `provider.update`, `provider.all`, `model.get`, `model.update`, `model.all`, `model.available`, `model.default`, and `model.setDefault`.

Separately, `packages/llm` offers a provider-neutral LLM interface. The README demonstrates the canonical pattern:

```ts
import { Effect } from "effect"
import { LLM, LLMClient } from "@opencode-ai/llm"
import { OpenAI } from "@opencode-ai/llm/providers"

const model = OpenAI.model("gpt-4o-mini", { apiKey: process.env.OPENAI_API_KEY })
const request = LLM.request({ model, system: "You are concise.", prompt: "Say hello." })
```

The LLM package exports provider-specific helpers plus protocol-neutral generation and streaming methods, which is how the higher-level app avoids scattering provider quirks throughout the runtime.

## Skills, plugins, and external extension points

`packages/opencode/src/skill/index.ts` defines the skill discovery/loading interface. It scans built-in config directories, project `.agents` / `.claude` skill folders, explicit config paths, and pulled URL-backed skill directories. The service exposes `get(name)`, `all()`, `dirs()`, and `available(agent?)`. The built-in `customize-opencode` skill is registered in code before disk discovery so that user-defined skill files can override it.

Plugins extend tools and TUI behavior through `packages/plugin`, whose exports (`index.ts`, `tool.ts`, `tui.ts`) define the plugin authoring surface. `tool/registry.ts` shows how plugin modules are loaded dynamically from workspace tool directories and from installed plugin descriptors, then bridged into OpenCode’s internal tool definition format.

## Cloud and GitHub integration interfaces

`packages/function/src/api.ts` is the serverless API entrypoint for the Cloudflare Worker surface. It exports a `SyncServer` durable object with methods such as `fetch`, `publish`, `share`, `getData`, `assertSecret`, and `clear`, and it wires HTTP routes like `/share_create`, `/share_delete`, `/share_sync`, `/share_poll`, and `/share_data`. This is the API behind session-sharing and synchronization features on hosted surfaces.

The `github/` package implements the GitHub Action. The README documents the external interface: install with `opencode github install`, then invoke the action in GitHub comments using `/opencode` or `/oc`. This interface is important because it exposes OpenCode beyond the local CLI into CI-triggered issue and PR workflows.

Taken together, these APIs make OpenCode much more than a chat CLI: it is a layered platform with typed local runtime services, agent tools, extensible plugin points, HTTP/SDK integration surfaces, and hosted automation entrypoints.
