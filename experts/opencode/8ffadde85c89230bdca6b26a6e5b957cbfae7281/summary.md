# OpenCode — Summary

## Repository Purpose and Goals

OpenCode is a 100% open-source, AI-powered coding agent designed for the terminal, desktop, and web. Its stated goals are:

- **Provider agnosticism**: Unlike competitors tied to a single provider, OpenCode works with Anthropic Claude, OpenAI, Google, xAI, Mistral, Groq, GitHub Copilot, Amazon Bedrock, Google Vertex, GitLab, OpenRouter, and many more, including local models via OpenAI-compatible endpoints.
- **Open source**: MIT licensed; the full implementation is publicly available and community-driven.
- **TUI-first**: Built by Neovim users and the creators of terminal.shop; the terminal interface pushes the limits of what is achievable in a terminal environment using the `@opentui/core` framework.
- **Client/server architecture**: The core agent runs as a local HTTP server (`opencode serve`), and the TUI/desktop/web are all clients that connect to it. This design allows, for example, running the agent on a remote machine and controlling it from a mobile app.
- **LSP integration**: Out-of-the-box Language Server Protocol support for semantic code awareness.
- **Extensibility**: A plugin system, custom agents, custom commands, MCP (Model Context Protocol) support, and a JavaScript/TypeScript SDK for programmatic access.

## Key Features and Capabilities

- **Multiple built-in agents**: `build` (default, full access), `plan` (read-only exploration), `general` (subagent for complex searches), plus support for user-defined custom agents.
- **Tool ecosystem**: File read/write/edit, bash execution, glob/grep/list, LSP-powered code search, web fetch and search, task spawning, todo management, apply-patch, and multi-edit tools.
- **Session management**: Persistent SQLite-backed sessions with compaction, sharing, undo/redo (via filesystem snapshots), forking, and import/export.
- **MCP support**: Configure local subprocess MCP servers or remote HTTP MCP servers with OAuth support; discover tools from them automatically.
- **Plugin system**: Extend OpenCode via `@opencode-ai/plugin`-based plugins that can register custom tools, auth methods, provider hooks, and hook into the lifecycle (tool execution, chat messages, permission requests, etc.).
- **Custom commands and agents**: Define slash commands (`.opencode/commands/`) and custom agents (`.opencode/agents/`) as Markdown files with YAML frontmatter.
- **Skills**: Named context bundles (Markdown files) that can be injected into prompts using the `skill` tool.
- **ACP (Agent Client Protocol)**: JSON-RPC over stdio interface for integration with editors like Zed.
- **Desktop app**: Cross-platform Electron-based desktop app (BETA).
- **Web UI**: SolidJS-based single-page app bundled into the CLI binary and also served as a standalone web console.
- **Enterprise features**: MDM/managed preferences support on macOS, enterprise URL configuration, Stripe-integrated subscription billing, workspace management.
- **Snapshot and revert**: Filesystem snapshots before each tool invocation allow undoing changes at the message level.
- **Share**: Sessions can be shared to a public URL.
- **GitHub Actions integration**: `@actions/core` and `@actions/github` are included for CI usage.
- **PR workflow**: A `pr` command for AI-assisted pull request creation.

## Primary Use Cases and Target Audience

- **Software engineers** who want an AI pair-programmer in the terminal that is not locked to a single AI provider.
- **Neovim / terminal power users** who want a TUI-native experience.
- **Teams and enterprises** seeking a self-hostable or enterprise-managed AI coding assistant.
- **Developers building on OpenCode** who need a programmable coding agent via the REST API or TypeScript SDK.
- **CI/CD pipelines** running automated AI-assisted coding tasks in GitHub Actions.

## High-Level Architecture Overview

```
┌─────────────────────────────────┐
│           Clients               │
│  TUI  │  Desktop  │  Web  │ SDK │
└────────────┬────────────────────┘
             │ HTTP / WebSocket
┌────────────▼────────────────────┐
│       opencode server           │
│   (Hono HTTP + WS, SQLite DB)   │
│                                 │
│  ┌──────────┐  ┌─────────────┐  │
│  │ Sessions │  │   Agents    │  │
│  │ Messages │  │   Tools     │  │
│  │ Projects │  │   MCP       │  │
│  └──────────┘  │   LSP       │  │
│                └─────────────┘  │
└─────────────────────────────────┘
             │
┌────────────▼────────────────────┐
│      AI Providers (via          │
│      Vercel AI SDK)             │
│  Anthropic │ OpenAI │ Google... │
└─────────────────────────────────┘
```

The **core** package (`packages/opencode`) is a Bun-based TypeScript application. It exposes a Hono HTTP server and uses SQLite (via Drizzle ORM) for local persistence. Sessions, messages, and tool call state are stored in `~/.local/share/opencode/opencode.db` (XDG-compliant).

The **Effect** functional programming library underpins the service layer; services are defined as Effect layers and run through a shared `makeRuntime`. Per-directory state is managed with `InstanceState` (a `ScopedCache` keyed by project directory).

The **AI SDK** (Vercel AI SDK `ai` package) drives LLM interaction with streaming support and a provider-agnostic interface. The provider layer translates OpenCode's provider configuration into AI SDK provider instances.

## Related Projects and Dependencies

- [`@opentui/core`](https://github.com/anomalyco/opentui) — Custom terminal UI framework powering the TUI renderer.
- [Vercel AI SDK (`ai`)](https://sdk.vercel.ai) — Provider-agnostic LLM interface.
- [Effect](https://effect.website) — Functional effect system for TypeScript (services, layers, error handling).
- [Drizzle ORM](https://orm.drizzle.team) — SQLite schema and query builder.
- [Hono](https://hono.dev) — Lightweight web framework for the HTTP server.
- [SST](https://sst.dev) — Infrastructure-as-code for cloud backend deployment (Cloudflare Workers, PlanetScale).
- [Turbo](https://turbo.build) — Monorepo build orchestrator.
- [Bun](https://bun.sh) — JavaScript runtime, package manager, bundler, and test runner.
- [SolidJS](https://www.solidjs.com) — Reactive UI framework for the web/desktop frontends.
