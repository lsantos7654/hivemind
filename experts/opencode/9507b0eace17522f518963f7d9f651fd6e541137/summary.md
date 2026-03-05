# OpenCode — Summary

## Repository Purpose and Goals

OpenCode is a 100% open-source, AI-powered coding agent designed to run in the terminal (and as a desktop application). It provides a conversational interface where developers can ask an AI assistant to read, write, edit, and run code using a rich set of built-in tools. The core goal is to be a provider-agnostic alternative to proprietary tools such as Claude Code, supporting dozens of AI model providers out of the box while exposing a clean client/server architecture that allows multiple front-ends (TUI, web, desktop, mobile) to connect to the same backend agent process.

The project is maintained by the team behind [terminal.shop](https://terminal.shop) and SST, and reflects a deliberate focus on terminal-first UX, deep LSP integration, and extensibility through plugins and custom agents.

## Key Features and Capabilities

- **Multi-provider AI support** — Anthropic, OpenAI, Google Gemini, Vertex AI, AWS Bedrock, Azure, Mistral, Groq, Cohere, DeepInfra, Cerebras, Together AI, Perplexity, Vercel, xAI, OpenRouter, GitLab, GitHub Copilot, and any OpenAI-compatible endpoint. Models sourced from `models.dev`.
- **Rich TUI** — A full terminal user interface built with SolidJS and the `opentui` library, supporting keyboard navigation, dialogs, session management, theming, command palette, and real-time streaming output.
- **Desktop application (beta)** — Cross-platform (macOS, Windows, Linux) Tauri-based desktop app wrapping the same web UI.
- **Client/server architecture** — The `opencode serve` command starts a headless HTTP+SSE server; all clients (TUI, web, desktop, third-party tools) communicate via a documented OpenAPI 3.1 REST API.
- **Built-in agents** — `build` (full-access default), `plan` (read-only analysis), `general` (multi-step subagent), `explore` (fast codebase exploration). Additional custom agents can be defined in config.
- **Task/subagent system** — Primary agents can delegate work to specialized subagents using the `task` tool.
- **LSP integration** — Automatic Language Server Protocol diagnostics fed back to the model after edits, for TypeScript, Python, Go, Rust, C/C++, Lua, Ruby, Swift, and more.
- **MCP (Model Context Protocol)** — Connect to external tool servers via stdio, SSE, or Streamable HTTP transports, including OAuth-authenticated MCP servers.
- **Plugin system** — Extend OpenCode with npm packages via `@opencode-ai/plugin`. Plugins can add auth providers, tool definitions, and lifecycle hooks.
- **Slash commands** — Markdown-template-based commands that can be defined in `.opencode/command/` directories (project or global scope). Built-in `init` and `review` commands.
- **Skills** — Reusable markdown instruction files discoverable from `.opencode/skills/`, `skills/`, `.claude/skills/`, and `.agents/skills/` (SKILL.md convention).
- **Session management** — Persistent sessions with SQLite storage, forking, revert/unrevert (git-snapshot-based), sharing, title generation, and compaction.
- **Permission system** — Fine-grained allow/deny/ask rules per tool and file pattern, configurable globally, per-project, and per-session.
- **Context compaction** — Automatic summarization and pruning of long conversations when the context window is near full.
- **Git snapshots** — Automatic tracking of file changes during a session using a hidden git repo, enabling diff views and revert.
- **Worktrees** — Isolated git worktrees per session/workspace to allow parallel independent work.
- **Workspace/cloud support** — Control plane layer for multi-workspace (e.g., GitHub Codespaces, Daytona) remote sessions.
- **ACP (Agent Client Protocol)** — Support for the `@agentclientprotocol/sdk` standard for IDE integration.
- **Web interface** — `opencode web` starts a browser-based UI on top of the same server.
- **Session sharing** — Share sessions via a public URL for collaboration or review.
- **Auto-update** — Built-in upgrade mechanism.
- **Formatters** — Automatic post-edit formatting (Prettier, Black, gofmt, rustfmt, etc.).
- **PTY support** — Persistent pseudo-terminal sessions accessible via the API.

## Primary Use Cases and Target Audience

- **Individual developers** wanting an open-source, terminal-friendly AI coding assistant not locked into Anthropic/OpenAI.
- **Teams** using enterprise providers (Vertex, Bedrock, Azure, GitLab) or self-hosted models, needing a provider-agnostic tool.
- **IDE/editor integrators** building extensions (VS Code, JetBrains, Zed) that connect to the headless server via the REST API or ACP protocol.
- **Automation/CI** scenarios where `opencode run` or the `github` action executes AI-assisted code changes non-interactively.
- **Plugin and tool developers** extending OpenCode's capabilities via the `@opencode-ai/plugin` package.

## High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        opencode process                          │
│                                                                  │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────────┐ │
│  │  CLI (yargs) │   │  TUI (Solid) │   │  Server (Hono/HTTP)  │ │
│  └──────┬───────┘   └──────┬───────┘   └──────────┬───────────┘ │
│         │                  │  (Worker thread RPC)  │ SSE / REST  │
│         └──────────────────┴──────────────────────┘             │
│                            │                                     │
│                 ┌──────────▼──────────┐                          │
│                 │   Session/Processor  │                          │
│                 │  (LLM streaming,    │                          │
│                 │   tool dispatch)    │                          │
│                 └──────────┬──────────┘                          │
│          ┌─────────────────┼──────────────────┐                  │
│          │                 │                  │                  │
│  ┌───────▼──────┐  ┌───────▼──────┐  ┌───────▼──────┐          │
│  │  Tool Registry│  │  Provider    │  │  MCP / LSP   │          │
│  │  (bash, edit,│  │  (ai-sdk,    │  │  Clients     │          │
│  │  read, glob,…│  │  40+ models) │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                            │                                     │
│                 ┌──────────▼──────────┐                          │
│                 │  SQLite (Drizzle)    │                          │
│                 │  + XDG data paths   │                          │
│                 └─────────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

The server process bootstraps a per-directory `Instance` context holding project info, config, and all per-instance singletons (session state, LSP clients, MCP connections). Events flow through an in-process `Bus` (pub/sub) and are forwarded to connected clients via SSE. The TUI runs the server logic inside a dedicated worker thread and communicates via a simple JSON-RPC bridge.

## Related Projects and Dependencies

| Dependency | Role |
|---|---|
| `ai` (Vercel AI SDK) | Core LLM streaming abstraction |
| `@ai-sdk/*` | Provider adapters (Anthropic, OpenAI, Google, etc.) |
| `hono` + `hono-openapi` | HTTP server and OpenAPI spec generation |
| `drizzle-orm` + `bun:sqlite` | ORM and database |
| `@opentui/solid` | Terminal UI rendering |
| `solid-js` | Reactive UI framework (TUI + web) |
| `@modelcontextprotocol/sdk` | MCP client |
| `@agentclientprotocol/sdk` | ACP agent/IDE protocol |
| `web-tree-sitter` / `tree-sitter-bash` | Bash AST parsing for permission analysis |
| `@parcel/watcher` | File system watching |
| `bun-pty` | PTY session support |
| `zod` | Schema validation throughout |
| `yargs` | CLI argument parsing |
| `models.dev` | Model catalog and capability database |
| `Tauri` | Desktop app shell |
