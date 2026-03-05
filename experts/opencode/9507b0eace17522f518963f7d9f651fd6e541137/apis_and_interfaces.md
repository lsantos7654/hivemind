# APIs and Interfaces — OpenCode

## Overview

OpenCode exposes its functionality through three primary integration surfaces:

1. **HTTP REST API** — A Hono-based server (default port 4096) with a full OpenAPI 3.1 spec.
2. **JavaScript/TypeScript SDK** — `@opencode-ai/sdk` wraps the HTTP API with typed client functions.
3. **Plugin System** — npm packages conforming to the `@opencode-ai/plugin` interface that can hook into the AI pipeline.

The internal TypeScript modules use a **namespace pattern** rather than classes. Each subsystem exposes a namespace (e.g., `Session`, `Tool`, `Bus`, `Provider`) that bundles related types, schemas (Zod), and pure functions.

---

## 1. HTTP REST API

### Base URL and Auth

```
http://localhost:4096
```

Optional HTTP Basic Auth is enabled by setting `OPENCODE_SERVER_PASSWORD` (and optionally `OPENCODE_SERVER_USERNAME`, default `opencode`).

Directory context is passed per-request via query param or header:
- Query: `?directory=/path/to/project`
- Header: `x-opencode-directory: /path/to/project`

### OpenAPI Spec

The full OpenAPI 3.1 spec is available at:
```
GET /openapi
```
or pre-generated at `packages/sdk/openapi.json`.

### Session Routes (`/session`)

All session interactions are under the `/session` prefix.

| Method | Path | operationId | Description |
|--------|------|-------------|-------------|
| GET | `/session` | `session.list` | List sessions (filterable by `directory`, `roots`, `start`, `search`, `limit`) |
| POST | `/session` | `session.create` | Create a new session |
| GET | `/session/status` | `session.status` | Get status of all active sessions |
| GET | `/session/:id` | `session.get` | Get session by ID |
| PATCH | `/session/:id` | `session.update` | Update title or archived timestamp |
| DELETE | `/session/:id` | `session.delete` | Delete session and all data |
| GET | `/session/:id/children` | `session.children` | List child (forked) sessions |
| POST | `/session/:id/fork` | `session.fork` | Fork session at a message point |
| POST | `/session/:id/abort` | `session.abort` | Cancel ongoing AI processing |
| POST | `/session/:id/init` | `session.init` | Generate AGENTS.md for the project |
| GET | `/session/:id/message` | `session.messages` | List all messages |
| POST | `/session/:id/message` | `session.prompt` | Send a prompt (streams response) |
| POST | `/session/:id/prompt_async` | `session.prompt_async` | Send prompt, return immediately (204) |
| POST | `/session/:id/command` | `session.command` | Execute a slash command |
| POST | `/session/:id/shell` | `session.shell` | Run a shell command via AI |
| GET | `/session/:id/message/:msgID` | `session.message` | Get a specific message |
| DELETE | `/session/:id/message/:msgID` | `session.deleteMessage` | Delete a message |
| DELETE | `/session/:id/message/:msgID/part/:partID` | `part.delete` | Delete a message part |
| PATCH | `/session/:id/message/:msgID/part/:partID` | `part.update` | Update a message part |
| POST | `/session/:id/revert` | `session.revert` | Revert a message (undo file changes) |
| POST | `/session/:id/unrevert` | `session.unrevert` | Restore reverted messages |
| GET | `/session/:id/diff` | `session.diff` | Get file diffs for a message |
| GET | `/session/:id/todo` | `session.todo` | Get todo list for a session |
| POST | `/session/:id/summarize` | `session.summarize` | Compact session with AI summary |
| POST | `/session/:id/share` | `session.share` | Create shareable link |
| DELETE | `/session/:id/share` | `session.unshare` | Remove shareable link |
| POST | `/session/:id/permissions/:permID` | `permission.respond` | Approve/deny a permission request |

### Provider Routes (`/provider`)

| Method | Path | operationId | Description |
|--------|------|-------------|-------------|
| GET | `/provider` | `provider.list` | List all providers with connection status |
| GET | `/provider/auth` | `provider.auth` | Get auth methods per provider |
| POST | `/provider/:id/oauth/authorize` | `provider.oauth.authorize` | Start OAuth flow |
| POST | `/provider/:id/oauth/callback` | `provider.oauth.callback` | Handle OAuth callback |

### Auth Routes

| Method | Path | operationId | Description |
|--------|------|-------------|-------------|
| PUT | `/auth/:providerID` | `auth.set` | Set credentials for a provider |
| DELETE | `/auth/:providerID` | `auth.remove` | Remove credentials |

### SSE Event Stream

```
GET /event
```

Streams all Bus events as Server-Sent Events. Clients subscribe to real-time updates for sessions, messages, tool calls, and permission requests.

---

## 2. JavaScript/TypeScript SDK

Package: `@opencode-ai/sdk`

### Installation

```bash
npm install @opencode-ai/sdk
```

### Creating a Client

```typescript
import { createOpencodeClient } from "@opencode-ai/sdk"

const client = createOpencodeClient({
  baseUrl: "http://localhost:4096",
  directory: "/path/to/project",  // optional, sets x-opencode-directory header
})
```

### Embedded Server + Client (SDK v2)

The SDK v2 can spin up the OpenCode server in-process:

```typescript
import { createOpencode } from "@opencode-ai/sdk/v2"

const { client, server } = await createOpencode({
  // optional ServerOptions
})

// client is pre-configured against the embedded server
const session = await client.session.create()
```

### Typed Client Methods

All HTTP routes have typed equivalents. Example workflow:

```typescript
// Create a session
const session = await client.session.create({})

// Send a prompt and wait for response
const msg = await client.session.prompt(session.id, {
  providerID: "anthropic",
  modelID: "claude-opus-4-5",
  parts: [{ type: "text", text: "Refactor the login function" }],
})

// List messages
const messages = await client.session.messages(session.id)
```

---

## 3. Internal Module APIs

### `Session` Namespace

Located at `packages/opencode/src/session/index.ts`.

Key functions:

```typescript
Session.create(opts?)              // Create a new session → Session.Info
Session.get(sessionID)             // Fetch session → Session.Info
Session.list(filters)              // Async generator of Session.Info
Session.messages({ sessionID })    // Fetch all messages
Session.remove(sessionID)          // Delete session
Session.fork({ sessionID, messageID }) // Fork at message → Session.Info
Session.setTitle({ sessionID, title }) // Update title
Session.share(sessionID)           // Generate share URL
Session.unshare(sessionID)         // Remove share URL
Session.removeMessage(...)         // Delete a message and its parts
Session.updatePart(part)           // Update a message part
```

`Session.Info` schema (Zod):

```typescript
{
  id: string,
  slug: string,
  projectID: string,
  directory: string,
  parentID?: string,
  title: string,
  version: number,
  time: { created, updated, compacting?, archived? },
  share?: { url: string },
  revert?: any,
  summary?: { additions, deletions, files, diffs? },
  permission?: PermissionNext.Ruleset,
}
```

### `Tool` Namespace

Located at `packages/opencode/src/tool/tool.ts`.

Defines the `Tool.define()` factory for creating tools:

```typescript
import { Tool } from "../tool/tool"
import z from "zod"

const MyTool = Tool.define("my_tool", {
  description: "Does something useful",
  parameters: z.object({
    path: z.string().describe("File path"),
  }),
  async execute(args, ctx) {
    // ctx provides: sessionID, messageID, abort signal, metadata(), ask()
    await ctx.ask({ permission: "read", patterns: [args.path], metadata: {}, always: [] })
    return {
      title: "Read file",
      metadata: {},
      output: "file contents...",
    }
  },
})
```

`Tool.Context` provides:
- `sessionID` / `messageID` — current conversation context
- `abort: AbortSignal` — cancellation token
- `metadata(...)` — update tool call display title/metadata
- `ask(...)` — request user permission before proceeding
- `messages` — full conversation history

### `Bus` Namespace

Located at `packages/opencode/src/bus/index.ts`.

Typed pub/sub system scoped per project directory:

```typescript
import { Bus } from "../bus"
import { BusEvent } from "../bus/bus-event"

// Define an event type
const MyEvent = BusEvent.define("my.event", z.object({ value: z.string() }))

// Publish
await Bus.publish(MyEvent, { value: "hello" })

// Subscribe
const unsub = Bus.subscribe(MyEvent, (event) => {
  console.log(event.properties.value)
})

// Subscribe to all events (wildcard)
Bus.subscribeAll((event) => { /* event.type, event.properties */ })

// One-shot subscription
Bus.once(MyEvent, (event) => {
  if (someCondition) return "done"  // return "done" to auto-unsubscribe
})

// Cleanup
unsub()
```

Events emitted by the core system are forwarded to connected SSE clients via `GlobalBus`.

### `Config` Namespace

Located at `packages/opencode/src/config/config.ts`.

Six-layer precedence (low → high):
1. Remote `.well-known/opencode` (org-level defaults)
2. Global user config (`~/.config/opencode/opencode.json`)
3. Custom config (`OPENCODE_CONFIG` env var path)
4. Project config (`opencode.json` or `opencode.jsonc` at project root)
5. `.opencode/` directory files
6. Inline config (`OPENCODE_CONFIG_CONTENT` env var JSON)

Enterprise managed config (`/etc/opencode` on Linux) always overrides all layers.

```typescript
const config = await Config.get()
// config.model, config.provider, config.permission, config.plugin, ...
```

### `Provider` Namespace

Located at `packages/opencode/src/provider/provider.ts`.

Wraps Vercel AI SDK providers:

```typescript
Provider.list()                     // Connected providers (have valid auth)
Provider.fromModelsDevProvider(p)   // Convert models.dev schema → Provider.Info
Provider.sort(models)               // Sort models by preference
```

Provider catalog sourced from `https://models.dev`. Supports 40+ providers including Anthropic, OpenAI, Google, Azure, Bedrock, Mistral, Groq, and more.

### `PermissionNext` Namespace

Located at `packages/opencode/src/permission/next.ts`.

Permission actions: `"allow"` | `"deny"` | `"ask"`

```typescript
// Build a ruleset from config format
const ruleset = PermissionNext.fromConfig({
  "*": "allow",
  "read": { "*.env": "ask", "*": "allow" },
  "bash": "ask",
})

// Merge rulesets (later entries take precedence for conflicting patterns)
const merged = PermissionNext.merge(defaultRuleset, userRuleset)

// Reply to a pending permission request
PermissionNext.reply({ requestID: "perm_xxx", reply: "allow" })
```

---

## 4. Plugin Interface

Package: `@opencode-ai/plugin`

A plugin is an npm package that exports a `Plugin` function:

```typescript
import type { Plugin } from "@opencode-ai/plugin"

const MyPlugin: Plugin = async (input) => {
  // input: { client, project, directory, worktree, serverUrl, $ }
  return {
    // All hooks are optional
    async "chat.message"(input, output) {
      // Modify output.parts before sending to LLM
    },
    async "chat.params"(input, output) {
      // Adjust temperature, topP, topK, options
      output.temperature = 0.5
    },
    async "chat.headers"(input, output) {
      // Add custom HTTP headers for the LLM request
      output.headers["X-Custom"] = "value"
    },
    async "permission.ask"(input, output) {
      // Auto-allow/deny certain permissions
      output.status = "allow"
    },
    async "tool.execute.before"(input, output) {
      // Modify args before tool execution
    },
    async "tool.execute.after"(input, output) {
      // Post-process tool results
    },
    async "shell.env"(input, output) {
      // Inject environment variables into shell executions
      output.env["MY_VAR"] = "value"
    },
    tool: {
      my_custom_tool: { /* ToolDefinition */ },
    },
    auth: {
      provider: "my-provider",
      methods: [{ type: "api", label: "API Key", prompts: [...] }],
    },
    // Experimental hooks
    async "experimental.chat.system.transform"(input, output) {
      output.system.push("Additional system instructions")
    },
    async "experimental.session.compacting"(input, output) {
      output.context.push("Preserve these important facts")
    },
  }
}

export default MyPlugin
```

Register plugins in `opencode.json`:
```json
{
  "plugin": ["my-plugin@1.0.0", "file:///local/path/plugin"]
}
```

---

## 5. Agent Configuration

Agents are defined in `opencode.json` under `agent.<name>`:

```json
{
  "agent": {
    "my_agent": {
      "description": "Specialized agent for frontend tasks",
      "model": { "providerID": "anthropic", "modelID": "claude-opus-4-5" },
      "prompt": "You are a frontend specialist...",
      "temperature": 0.3,
      "mode": "subagent",
      "permission": {
        "bash": "deny",
        "read": "allow",
        "write": { "src/**": "allow", "*": "ask" }
      }
    }
  }
}
```

Built-in agents: `build` (default), `plan` (read-only), `code_review` (analysis).

---

## 6. MCP (Model Context Protocol) Integration

MCP servers are configured in `opencode.json`:

```json
{
  "mcp": {
    "my_server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@my-org/mcp-server"]
    }
  }
}
```

MCP tools appear as regular tools in the AI's tool registry. Routes at `/mcp` expose MCP server management endpoints.

---

## 7. Skill System

Skills are markdown files that inject additional context into the system prompt. Place files in `.opencode/skills/` or configure globally:

```
.opencode/skills/my-skill.md
```

The `Skill.dirs()` function returns all skill directories; the system prompt loader reads and concatenates them automatically.

---

## Error Format

All API errors follow a consistent `NamedError` JSON envelope:

```json
{
  "name": "NotFoundError",
  "message": "Session not found",
  "data": { }
}
```

HTTP status codes: `400` (bad request / model not found), `404` (not found), `500` (server error).
