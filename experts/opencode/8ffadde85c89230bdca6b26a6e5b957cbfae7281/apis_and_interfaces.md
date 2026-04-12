# OpenCode — APIs and Interfaces

## HTTP REST API

The OpenCode server (`opencode serve`) exposes a Hono-based HTTP API. The full OpenAPI 3.1 spec is generated via:

```bash
opencode generate
```

The API is organized into two groups:

### Control Plane Routes (global, not directory-scoped)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/global/...` | Global state (themes, etc.) |
| GET/POST | `/workspace/...` | Enterprise workspace management |

### Instance Routes (scoped to a project directory via `x-opencode-directory` header or `directory` query param)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/session` | List sessions |
| POST | `/session` | Create session |
| GET | `/session/:id` | Get session |
| DELETE | `/session/:id` | Delete session |
| GET | `/session/status` | Session run status |
| POST | `/session/:id/abort` | Abort running session |
| POST | `/session/:id/chat` | Send message to session |
| GET | `/session/:id/message` | List messages in session |
| POST | `/session/:id/compact` | Compact session context |
| POST | `/session/:id/share` | Share session |
| POST | `/session/:id/unshare` | Unshare session |
| POST | `/session/:id/revert` | Revert to snapshot |
| GET | `/session/:id/todo` | Get session todos |
| GET | `/provider` | List available providers |
| GET | `/provider/:id/model` | List models for a provider |
| GET | `/config` | Get current config |
| POST | `/config` | Update config |
| GET | `/config/path` | Get config file paths |
| GET | `/permission` | Get permission ruleset |
| POST | `/permission` | Update permission |
| GET | `/mcp` | List MCP servers |
| POST | `/mcp/:name/enable` | Enable MCP server |
| POST | `/mcp/:name/disable` | Disable MCP server |
| GET | `/file` | Read file content |
| GET | `/path` | Get current paths |
| GET | `/agent` | List agents |
| GET | `/command` | List commands |
| GET | `/skill` | List skills |
| POST | `/instance/dispose` | Dispose instance |
| WS | `/pty` | PTY WebSocket terminal |
| WS | `/event` | Server-Sent Events stream |
| GET | `/tui/...` | TUI-specific endpoints |
| GET | `/question` | Pending questions |
| POST | `/question/:id` | Answer question |
| GET | `/experimental/...` | Experimental/beta endpoints |

### Server-Sent Events (SSE) Stream

The `/event` endpoint streams all internal bus events in real time. Clients connect and receive a stream of newline-delimited JSON events. Event types include session updates, message parts, tool calls, permission requests, errors, etc.

## TypeScript SDK (`@opencode-ai/sdk`)

The SDK is auto-generated from the OpenAPI spec. Install it:

```bash
npm install @opencode-ai/sdk
```

### Client Creation

```typescript
import { createOpencodeClient } from "@opencode-ai/sdk"

const client = createOpencodeClient({
  baseUrl: "http://localhost:3000",  // URL of running opencode server
  directory: "/path/to/project",    // Project directory (sets x-opencode-directory header)
})
```

`createOpencodeClient` wraps a generated `OpencodeClient` with:
- Automatic `x-opencode-directory` header injection
- GET request query param rewriting for directory routing
- Timeout disabled for long-running requests

### Key Client Methods (v2 API)

```typescript
import { createOpencodeClient } from "@opencode-ai/sdk/v2"

const client = createOpencodeClient({ baseUrl: "...", directory: "..." })

// Sessions
const sessions = await client.sessionList({ query: { roots: true } })
const session = await client.sessionCreate({ body: { ... } })
const messages = await client.sessionMessageList({ path: { id: sessionId } })

// Sending messages (streaming response)
const stream = client.sessionChat({ path: { id }, body: { text: "..." } })
for await (const event of stream) { ... }

// Providers and models
const providers = await client.providerList()
const models = await client.providerModelList({ path: { id: "anthropic" } })

// Config
const config = await client.configGet()
await client.configSet({ body: { model: "anthropic/claude-opus-4-5" } })
```

## Plugin API (`@opencode-ai/plugin`)

Plugins extend OpenCode with custom tools, auth methods, provider hooks, and lifecycle hooks.

### Plugin Module Shape

```typescript
// my-plugin/index.ts
import type { PluginModule } from "@opencode-ai/plugin"

const plugin: PluginModule = {
  id: "my-plugin",
  async server(input, options) {
    return {
      // Hook into tool execution
      async "tool.execute.before"(inp, out) {
        console.log("Tool called:", inp.tool)
      },

      // Register custom tools
      tool: {
        my_tool: {
          description: "Does something",
          parameters: z.object({ path: z.string() }),
          async execute({ path }) {
            return { output: "result" }
          },
        },
      },

      // Hook into chat message lifecycle
      async "chat.message"(input, output) {
        // Called when user sends a message
      },

      // Modify LLM parameters per request
      async "chat.params"(input, output) {
        output.temperature = 0.5
      },

      // Intercept permission requests
      async "permission.ask"(input, output) {
        if (input.id === "bash") output.status = "allow"
      },

      // Listen to all events from the bus
      async event({ event }) { ... },

      // Modify config on startup
      async config(cfg) {
        cfg.model = "anthropic/claude-opus-4-5"
      },
    }
  },
}

export default plugin
```

### `PluginInput` Object

The `input` argument to `server()` provides:

```typescript
type PluginInput = {
  client: OpencodeClient      // SDK client for the running server
  project: Project            // Current project info
  directory: string           // Project root directory
  worktree: string            // Git worktree path
  serverUrl: URL              // Base URL of the running server
  $: BunShell                 // Bun shell for running commands
}
```

### Plugin Hooks Reference

| Hook | Called When |
|------|-------------|
| `event` | Any internal bus event fires |
| `config` | Config is loaded/refreshed |
| `tool` | Register additional tools |
| `auth` | Register custom provider auth methods |
| `provider` | Register custom provider model lists |
| `chat.message` | User sends a message |
| `chat.params` | LLM parameters are being prepared |
| `chat.headers` | HTTP headers for LLM request being prepared |
| `permission.ask` | Permission prompt is about to be shown |
| `command.execute.before` | Slash command is about to execute |
| `tool.execute.before` | Tool is about to be called |
| `tool.execute.after` | Tool has finished executing |
| `tool.definition` | Tool description/params sent to LLM |
| `shell.env` | Shell environment is being prepared |
| `experimental.chat.messages.transform` | Transforms message history before LLM |
| `experimental.chat.system.transform` | Transforms system prompt before LLM |
| `experimental.session.compacting` | Session compaction is starting |
| `experimental.text.complete` | Text completion part is finalized |

### Custom Tool Definition

```typescript
import type { ToolDefinition } from "@opencode-ai/plugin"
import z from "zod"

const myTool: ToolDefinition = {
  description: "Searches the issue tracker",
  parameters: z.object({
    query: z.string().describe("Search query"),
    limit: z.number().optional().default(10),
  }),
  async execute({ query, limit }, ctx) {
    // ctx.sessionID, ctx.callID available
    const results = await fetchIssues(query, limit)
    return {
      output: JSON.stringify(results),
      title: `Found ${results.length} issues`,
      metadata: { count: results.length },
    }
  },
}
```

### Auth Hook

```typescript
const authHook: AuthHook = {
  provider: "my-provider",
  methods: [
    {
      type: "oauth",
      label: "Authorize with OAuth",
      async authorize(inputs) {
        return {
          url: "https://provider.example.com/oauth/authorize?...",
          instructions: "Open the URL to authorize",
          method: "auto",
          async callback() {
            // Poll for token
            return { type: "success", refresh: "...", access: "...", expires: Date.now() + 3600000 }
          },
        }
      },
    },
    {
      type: "api",
      label: "Enter API Key",
      prompts: [{ type: "text", key: "apiKey", message: "Paste your API key:" }],
      async authorize(inputs) {
        return { type: "success", key: inputs!.apiKey }
      },
    },
  ],
}
```

## Configuration API (`config.ts`)

The `Config.Info` Zod schema defines all supported configuration options. Config is loaded in priority order (highest first):

1. Enterprise managed config (macOS MDM plist, or files in system managed config dir)
2. Global config (`~/.config/opencode/config.json`)
3. Local project config (`.opencode/config.json` in project root)
4. Environment variables

### Key Config Fields

```typescript
// opencode.config.json (or .opencode/config.json)
{
  "$schema": "https://opencode.ai/config.schema.json",
  "model": "anthropic/claude-opus-4-5",        // Default model
  "small_model": "anthropic/claude-haiku-4-5", // Fast model for background tasks
  "default_agent": "build",                    // Default primary agent

  // Provider configuration and overrides
  "provider": {
    "anthropic": {
      "options": { "apiKey": "sk-ant-..." }
    },
    "openai": {
      "options": { "baseURL": "https://custom.endpoint.com/v1" }
    }
  },

  // MCP server configuration
  "mcp": {
    "filesystem": {
      "type": "local",
      "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/"],
      "enabled": true
    },
    "remote-mcp": {
      "type": "remote",
      "url": "https://mcp.example.com/sse",
      "oauth": { "clientId": "...", "scope": "read write" }
    }
  },

  // Agent customization
  "agent": {
    "build": {
      "model": "anthropic/claude-opus-4-5",
      "temperature": 0.7,
      "steps": 50,
      "permission": { "bash": "allow", "edit": "ask" }
    },
    "my-custom-agent": {
      "mode": "primary",
      "prompt": "You are a security expert...",
      "description": "Security-focused code review agent"
    }
  },

  // Slash commands
  "command": {
    "test": {
      "template": "Run all tests in {{path}} and fix any failures",
      "description": "Run and fix tests"
    }
  },

  // LSP server configuration
  "lsp": {
    "typescript": { "disabled": false },
    "custom-lsp": {
      "command": ["my-lsp-server", "--stdio"],
      "extensions": [".myext"]
    }
  },

  // Additional instruction files
  "instructions": ["AGENTS.md", ".cursor/rules/*.md"],

  // Permission defaults
  "permission": {
    "bash": "ask",
    "edit": "allow",
    "read": "allow"
  },

  // Server options (for `opencode serve`)
  "server": {
    "port": 3000,
    "hostname": "0.0.0.0",
    "mdns": true,
    "cors": ["https://my-app.example.com"]
  },

  // Plugin list
  "plugin": ["my-npm-plugin", ["./local-plugin.ts", { "option": "value" }]],

  // Share behavior
  "share": "manual",    // "manual" | "auto" | "disabled"
  "autoupdate": true,   // true | false | "notify"

  // Skill sources
  "skills": {
    "paths": ["./.opencode/skills"],
    "urls": ["https://example.com/.well-known/skills/"]
  }
}
```

## Agent Definition (Markdown + YAML Frontmatter)

Custom agents are defined as `.md` files in `.opencode/agents/` or `agents/`:

```markdown
---
description: Security-focused code review
model: anthropic/claude-opus-4-5
mode: primary          # "primary" | "subagent" | "all"
temperature: 0.3
steps: 30
permission:
  bash: deny
  edit: ask
  read: allow
color: "#FF5733"
---

You are a security expert specializing in identifying vulnerabilities.
Focus on OWASP Top 10 issues and secure coding patterns.
Always explain the risk before suggesting a fix.
```

## Custom Commands (Markdown + YAML Frontmatter)

Slash commands are defined as `.md` files in `.opencode/commands/` or `commands/`:

```markdown
---
description: Run tests and fix failures
agent: build
model: anthropic/claude-haiku-4-5
---

Run all tests in the current project with `bun test` (or the appropriate test runner).
Analyze any failures and fix them. Re-run tests to confirm all pass.
```

Invoke with `ctrl+p` in the TUI or prefix with `/` in the input:

```
/my-command
```

## ACP (Agent Client Protocol)

Start an ACP server (JSON-RPC over stdio) for Zed and other ACP-compatible editor integrations:

```bash
opencode acp [--cwd /path/to/project]
```

The ACP server implements:
- `initialize` — capability negotiation
- `session/new` — create a new conversation
- `session/load` — resume an existing session
- `session/prompt` — send a message and receive a response

Zed configuration (`~/.config/zed/settings.json`):

```json
{
  "agent_servers": {
    "OpenCode": {
      "command": "opencode",
      "args": ["acp"]
    }
  }
}
```

## CLI Entry Points

```bash
opencode                          # Start interactive TUI (default)
opencode run "fix the tests"      # Non-interactive: run a single agent task
opencode serve [--port 3000]      # Start HTTP server only (no TUI)
opencode web                      # Open web UI in browser
opencode acp                      # Start ACP stdio server
opencode session list             # List sessions
opencode session import <file>    # Import session from JSON
opencode session export <id>      # Export session to JSON
opencode models                   # List available models
opencode providers                # List configured providers
opencode agent list               # List available agents
opencode mcp list                 # List MCP servers
opencode mcp enable <name>        # Enable an MCP server
opencode mcp disable <name>       # Disable an MCP server
opencode plugin list              # List installed plugins
opencode plugin install <spec>    # Install a plugin
opencode stats                    # Show usage statistics
opencode pr                       # AI-assisted PR creation
opencode github <subcommand>      # GitHub integration
opencode upgrade                  # Upgrade to latest version
opencode generate                 # Generate OpenAPI spec to stdout
opencode completion               # Generate shell completion script
```

## Effect Service Layer

Internal services follow the Effect service pattern. To consume a service in a new Effect:

```typescript
import { Effect, Layer, Context } from "effect"
import { Provider } from "./provider/provider"
import { Config } from "./config/config"
import { makeRuntime } from "./effect/run-service"

// Define a service
class MyService extends Context.Service<MyService, {
  doSomething: () => Effect.Effect<string>
}>()("@opencode/MyService") {}

// Implement it as a layer
const MyServiceLayer = Layer.effect(
  MyService,
  Effect.gen(function* () {
    const config = yield* Config.Service
    const provider = yield* Provider.Service
    return {
      doSomething: Effect.fn("MyService.doSomething")(function* () {
        const cfg = yield* config.get()
        return cfg.model ?? "default"
      }),
    }
  })
)

// Run it
const { runPromise } = makeRuntime(MyServiceLayer.pipe(
  Layer.provide(Config.layer),
  Layer.provide(Provider.layer),
))
const result = await runPromise(
  Effect.gen(function* () {
    const svc = yield* MyService
    return yield* svc.doSomething()
  })
)
```

## Integration Patterns

### Running OpenCode Programmatically

```typescript
import { createOpencodeClient } from "@opencode-ai/sdk"
import { spawn } from "child_process"

// Start the server
const proc = spawn("opencode", ["serve", "--port", "3001"])

// Wait for it to be ready (check /health)
await fetch("http://localhost:3001/health").catch(() => retry())

// Create client
const client = createOpencodeClient({
  baseUrl: "http://localhost:3001",
  directory: process.cwd(),
})

// Create and run a session
const session = await client.sessionCreate({ body: {} })
const result = await client.sessionChat({
  path: { id: session.data.id },
  body: { text: "Refactor the utils directory to use ES modules" },
})
```

### Listening to Real-Time Events

```typescript
const eventsUrl = new URL("/event", "http://localhost:3001")
eventsUrl.searchParams.set("directory", encodeURIComponent(process.cwd()))

const response = await fetch(eventsUrl.toString())
const reader = response.body!.getReader()
const decoder = new TextDecoder()

while (true) {
  const { done, value } = await reader.read()
  if (done) break
  const text = decoder.decode(value)
  for (const line of text.split("\n")) {
    if (line.startsWith("data:")) {
      const event = JSON.parse(line.slice(5))
      console.log(event)
    }
  }
}
```
