# OpenCode — Code Structure

## Repository Root Layout

```
opencode/
├── packages/              # All workspace packages (monorepo)
│   ├── opencode/          # Core CLI + server package (main)
│   ├── app/               # Web UI (SolidJS SPA, embedded in binary)
│   ├── console/           # Web management console
│   │   └── app/           # Console SolidJS frontend
│   ├── desktop/           # Tauri-based desktop app (Rust + web)
│   ├── desktop-electron/  # Electron-based desktop app
│   ├── sdk/               # Generated TypeScript SDK
│   │   └── js/            # JS/TS client
│   ├── plugin/            # Plugin API package (@opencode-ai/plugin)
│   ├── script/            # Shared build scripting utilities
│   ├── util/              # Shared TypeScript utilities
│   ├── ui/                # Shared UI component library
│   ├── extensions/        # Browser/editor extensions
│   ├── enterprise/        # Enterprise backend (SST/Cloudflare)
│   ├── function/          # Cloudflare Worker functions
│   ├── identity/          # Identity/auth service
│   ├── slack/             # Slack bot integration
│   ├── storybook/         # Component storybook
│   ├── containers/        # Docker container definitions
│   └── web/               # Marketing website
├── infra/                 # SST cloud infrastructure definitions
├── sdks/                  # SDK source templates
├── specs/                 # Specification documents
├── script/                # Root-level utility scripts
├── nix/                   # Nix flake configurations
├── patches/               # Package patches (solid-js, standard-openapi)
├── sst.config.ts          # SST cloud deployment config
├── turbo.json             # Turborepo build pipeline config
├── package.json           # Root workspace package.json (Bun)
├── bunfig.toml            # Bun configuration
├── tsconfig.json          # Root TypeScript config
└── flake.nix              # Nix development environment
```

## Core Package: `packages/opencode`

This is the primary package — the `opencode` CLI binary and HTTP server.

```
packages/opencode/
├── src/
│   ├── index.ts           # CLI entrypoint (yargs setup, command registration)
│   ├── node.ts            # Node.js-specific entrypoint adapter
│   ├── account/           # Account and subscription management
│   ├── acp/               # Agent Client Protocol (JSON-RPC over stdio, Zed integration)
│   │   ├── agent.ts       # ACP Agent interface implementation
│   │   ├── session.ts     # ACP session state management
│   │   └── types.ts       # ACP type definitions
│   ├── agent/             # Agent definitions and orchestration
│   │   ├── agent.ts       # Agent.Service, Agent.Info schema, per-agent config loading
│   │   └── prompt/        # System prompt templates (compaction, explore, summary, title)
│   ├── auth/              # Authentication tokens and credential storage
│   ├── bus/               # Internal event bus (pub/sub within process)
│   ├── cli/               # CLI layer
│   │   ├── index.ts       # (see src/index.ts)
│   │   ├── bootstrap.ts   # Server startup and client bootstrap for TUI/run commands
│   │   ├── ui.ts          # Terminal output helpers (UI namespace)
│   │   ├── error.ts       # CLI error formatting
│   │   ├── logo.ts        # ASCII logo renderer
│   │   ├── network.ts     # Network utilities for CLI
│   │   ├── upgrade.ts     # Auto-upgrade logic
│   │   ├── heap.ts        # Heap snapshot utilities
│   │   ├── effect/        # Effect runtime for CLI context
│   │   └── cmd/           # Yargs command implementations
│   │       ├── run.ts     # `opencode run` — non-interactive agent runner
│   │       ├── serve.ts   # `opencode serve` — start HTTP server
│   │       ├── web.ts     # `opencode web` — open web UI
│   │       ├── agent.ts   # `opencode agent` — agent management
│   │       ├── models.ts  # `opencode models` — model listing
│   │       ├── providers.ts # `opencode providers` — provider management
│   │       ├── session.ts # `opencode session` — session management
│   │       ├── mcp.ts     # `opencode mcp` — MCP server management
│   │       ├── acp.ts     # `opencode acp` — start ACP stdio server
│   │       ├── generate.ts # `opencode generate` — generate OpenAPI spec
│   │       ├── pr.ts      # `opencode pr` — AI-assisted PR creation
│   │       ├── github.ts  # `opencode github` — GitHub integration
│   │       ├── export.ts  # `opencode export` — session export
│   │       ├── import.ts  # `opencode import` — session import
│   │       ├── plug.ts    # `opencode plugin` — plugin management
│   │       ├── stats.ts   # `opencode stats` — usage statistics
│   │       ├── debug/     # `opencode debug` subcommands
│   │       ├── account.ts # `opencode console` — web console
│   │       ├── db.ts      # `opencode db` — database utilities
│   │       ├── upgrade.ts # `opencode upgrade` — self-upgrade
│   │       ├── uninstall.ts # `opencode uninstall`
│   │       └── tui/       # TUI-specific commands (attach, thread)
│   ├── command/           # Slash command registry and execution
│   ├── config/            # Configuration loading and schema
│   │   ├── config.ts      # Config.Info schema (main config shape), config loading priority chain
│   │   ├── paths.ts       # Config file path resolution
│   │   ├── markdown.ts    # YAML frontmatter parser for agent/command .md files
│   │   └── console-state.ts # Console UI state persistence
│   ├── control-plane/     # Enterprise workspace/control plane
│   ├── effect/            # Effect framework integration
│   │   ├── run-service.ts # makeRuntime — shared Effect runtime factory
│   │   ├── instance-state.ts # InstanceState — per-project scoped service state
│   │   ├── instance-ref.ts   # InstanceRef — async local storage for instance context
│   │   ├── app-runtime.ts    # AppRuntime — top-level runtime
│   │   └── logger.ts      # Effect logger adapter
│   ├── env/               # Environment variable access
│   ├── file/              # File reading with MIME detection and attachment support
│   ├── filesystem/        # App filesystem (embedded web UI access)
│   ├── flag/              # Feature flags
│   ├── format/            # Code formatter integration (prettier, language-specific)
│   ├── git/               # Git utilities
│   ├── global/            # Global paths (data, config, cache dirs, XDG)
│   ├── id/                # ULID-based ID generation
│   ├── ide/               # IDE integration helpers
│   ├── installation/      # Version detection, local dev mode detection
│   ├── lsp/               # Language Server Protocol client
│   │   ├── client.ts      # LSP client (JSON-RPC over stdio)
│   │   ├── server.ts      # Built-in LSP server registry (TypeScript, Python, etc.)
│   │   ├── language.ts    # Language-to-extension mapping
│   │   └── launch.ts      # LSP server process launcher
│   ├── mcp/               # Model Context Protocol client
│   │   ├── index.ts       # MCP client management, tool discovery
│   │   ├── auth.ts        # MCP authentication
│   │   ├── oauth-callback.ts # OAuth callback server for MCP auth
│   │   └── oauth-provider.ts # OAuth provider for MCP
│   ├── npm/               # npm/bun package install utilities
│   ├── patch/             # Apply-patch utilities
│   ├── permission/        # Permission system (allow/ask/deny ruleset)
│   ├── plugin/            # Plugin loader and runtime
│   │   ├── index.ts       # Plugin.Service — loads and manages plugins
│   │   ├── loader.ts      # Dynamic plugin module loading
│   │   ├── install.ts     # Plugin installation from npm/path
│   │   ├── meta.ts        # Plugin metadata
│   │   ├── shared.ts      # Shared plugin utilities
│   │   ├── github-copilot/ # GitHub Copilot plugin
│   │   ├── codex.ts       # OpenAI Codex plugin
│   │   └── cloudflare.ts  # Cloudflare AI plugin
│   ├── project/           # Project and instance management
│   │   ├── instance.ts    # Instance — per-directory context (ALS), lifecycle
│   │   ├── project.ts     # Project.Service — project CRUD
│   │   ├── project.sql.ts # Drizzle schema for project table
│   │   ├── schema.ts      # Project ID types
│   │   ├── state.ts       # Project state
│   │   ├── vcs.ts         # VCS integration (git branch, dirty state)
│   │   └── bootstrap.ts   # Project bootstrapping
│   ├── provider/          # AI provider management
│   │   ├── provider.ts    # Provider.Service — model registry, provider factory
│   │   ├── models.ts      # ModelsDev integration (models.dev catalog)
│   │   ├── schema.ts      # ProviderID, ModelID branded types
│   │   ├── auth.ts        # Provider auth helpers
│   │   ├── error.ts       # Provider error types
│   │   ├── transform.ts   # Provider response transforms (streaming, timeout)
│   │   └── sdk/           # Custom provider SDK wrappers (e.g., GitHub Copilot)
│   ├── pty/               # Pseudo-terminal (PTY) management
│   │   ├── pty.bun.ts     # Bun native PTY implementation
│   │   └── pty.node.ts    # Node.js PTY fallback
│   ├── question/          # Interactive question/prompt system
│   ├── server/            # HTTP server
│   │   ├── server.ts      # Server namespace — Hono app factory, listen, OpenAPI spec
│   │   ├── adapter.bun.ts # Bun HTTP adapter
│   │   ├── adapter.node.ts # Node HTTP adapter
│   │   ├── middleware.ts  # Auth, CORS, compression, error, logging middleware
│   │   ├── event.ts       # SSE event streaming endpoint
│   │   ├── mdns.ts        # mDNS service discovery publishing
│   │   ├── projectors.ts  # Event projectors (DB → event bus)
│   │   ├── proxy.ts       # Proxy utilities
│   │   ├── control/       # Control plane routes (global, workspace)
│   │   ├── instance/      # Per-instance API routes
│   │   │   ├── index.ts   # InstanceRoutes — route aggregator
│   │   │   ├── session.ts # Session CRUD, messaging, compaction, share
│   │   │   ├── provider.ts # Provider/model listing
│   │   │   ├── config.ts  # Config read/write API
│   │   │   ├── permission.ts # Permission management
│   │   │   ├── mcp.ts     # MCP server management API
│   │   │   ├── lsp.ts     # LSP API
│   │   │   ├── pty.ts     # PTY (terminal) API with WebSocket
│   │   │   ├── file.ts    # File read API
│   │   │   ├── project.ts # Project API
│   │   │   ├── question.ts # Question/prompt API
│   │   │   ├── event.ts   # SSE event streaming
│   │   │   ├── experimental.ts # Experimental/beta routes
│   │   │   ├── global.ts  # Global instance info
│   │   │   ├── tui.ts     # TUI WebSocket bridge
│   │   │   ├── workspace.ts # Workspace routes
│   │   │   └── middleware.ts # Instance-scoped middleware
│   │   └── ui/            # Embedded web UI serving routes
│   ├── session/           # Session and message management
│   │   ├── index.ts       # Session.Service — CRUD, listing, messaging
│   │   ├── session.sql.ts # Drizzle schema (session, message, part, todo, permission tables)
│   │   ├── schema.ts      # SessionID, MessageID, PartID types
│   │   ├── message.ts     # Message types (v1)
│   │   ├── message-v2.ts  # Message types (v2, current)
│   │   ├── llm.ts         # LLM invocation and streaming
│   │   ├── prompt.ts      # SessionPrompt — message dispatch to agent
│   │   ├── processor.ts   # Message event processor
│   │   ├── compaction.ts  # Context compaction (summarizing old messages)
│   │   ├── revert.ts      # Undo/redo via snapshots
│   │   ├── run-state.ts   # Session run state (running/idle)
│   │   ├── status.ts      # Session status computation
│   │   ├── summary.ts     # Session summary generation
│   │   ├── system.ts      # System prompt assembly
│   │   ├── todo.ts        # In-session todo list management
│   │   ├── overflow.ts    # Token overflow / truncation handling
│   │   ├── retry.ts       # LLM retry logic
│   │   ├── instruction.ts # Instruction file loading (AGENTS.md, CLAUDE.md, etc.)
│   │   └── prompt/        # Prompt-related templates
│   ├── share/             # Session sharing (public URL)
│   ├── shell/             # Shell execution helpers
│   ├── skill/             # Skill discovery and loading
│   │   ├── index.ts       # Skill.Service — list/load skills
│   │   └── discovery.ts   # Skill file discovery
│   ├── snapshot/          # Filesystem snapshot capture and restore
│   ├── storage/           # SQLite persistence layer
│   │   ├── db.bun.ts      # Bun SQLite driver
│   │   ├── db.node.ts     # Node better-sqlite3 driver
│   │   ├── db.ts          # Database.Client singleton
│   │   ├── json-migration.ts # One-time JSON→SQLite migration
│   │   └── schema.sql.ts  # Shared Drizzle schema fragments (Timestamps)
│   ├── sync/              # Cloud sync
│   ├── tool/              # Tool implementations
│   │   ├── tool.ts        # Tool.Definition type, base tool utilities
│   │   ├── registry.ts    # Tool registry (name → definition)
│   │   ├── bash.ts        # Bash execution tool
│   │   ├── read.ts        # File read tool
│   │   ├── edit.ts        # File edit tool (string replace)
│   │   ├── write.ts       # File write tool
│   │   ├── multiedit.ts   # Multi-file edit tool
│   │   ├── apply_patch.ts # Apply unified diff patch tool
│   │   ├── glob.ts        # File pattern matching tool
│   │   ├── grep.ts        # Content search tool
│   │   ├── ls.ts          # Directory listing tool
│   │   ├── lsp.ts         # LSP-powered code search tool
│   │   ├── webfetch.ts    # URL fetch tool
│   │   ├── websearch.ts   # Web search tool
│   │   ├── codesearch.ts  # Semantic code search tool
│   │   ├── task.ts        # Subagent spawning tool
│   │   ├── todo.ts        # TodoWrite tool
│   │   ├── plan.ts        # Plan tool (plan mode)
│   │   ├── question.ts    # Interactive question tool
│   │   ├── skill.ts       # Skill injection tool
│   │   ├── schema.ts      # Tool schema utilities
│   │   ├── truncate.ts    # Output truncation
│   │   ├── truncation-dir.ts # Truncation directory management
│   │   ├── mcp-exa.ts     # Exa MCP tool wrapper
│   │   ├── external-directory.ts # External directory permission guard
│   │   └── invalid.ts     # Invalid tool placeholder
│   ├── util/              # General utilities
│   │   ├── log.ts         # Structured logger
│   │   ├── filesystem.ts  # File system helpers
│   │   ├── error.ts       # Error utilities
│   │   ├── hash.ts        # Hashing utilities
│   │   ├── lazy.ts        # Lazy initialization
│   │   ├── flock.ts       # File locking
│   │   ├── locale.ts      # Locale detection
│   │   ├── process.ts     # Process spawning utilities
│   │   ├── glob.ts        # Glob scanning utilities
│   │   ├── record.ts      # Record type guards
│   │   └── iife.ts        # IIFE helper
│   ├── v2/                # V2 API layer (experimental)
│   └── worktree/          # Git worktree management
├── bin/opencode           # Shell shim binary entry point
├── migration/             # Drizzle SQL migration files (timestamped directories)
├── test/                  # Integration and unit tests
├── script/                # Build scripts
│   ├── build.ts           # Main build script (Bun compile, multi-platform)
│   └── generate.ts        # Code generation (OpenAPI, SDK types)
├── drizzle.config.ts      # Drizzle Kit configuration
├── parsers-config.ts      # Tree-sitter parser configuration
└── tsconfig.json          # TypeScript configuration
```

## Supporting Packages

### `packages/app` — Web UI (SolidJS)
Embedded web UI SPA; built with SolidJS + Vite + TailwindCSS. Built during `opencode build` and embedded as a virtual file system in the binary. Also served standalone for the web console. Source in `src/` with pages, components, hooks, context providers, and i18n.

### `packages/sdk/js` — TypeScript SDK
Auto-generated from `packages/sdk/openapi.json` via `openapi-typescript` / `hey-api`. Exports `createOpencodeClient()`, typed request/response types, and a typed `OpencodeClient` class. Consumers use this to drive OpenCode programmatically.

### `packages/plugin` — Plugin API
Exports the `Plugin`, `Hooks`, `AuthHook`, `ProviderHook`, `ToolDefinition`, and related types that plugin authors use to extend OpenCode. This is the public extension API.

### `packages/util` — Shared Utilities
Exports `NamedError` and other shared TypeScript utilities used across the monorepo.

### `packages/script` — Build Utilities
Exports `Script.version`, `Script.channel`, `Script.release` used in build scripts.

### `packages/desktop-electron` — Electron Desktop App
Cross-platform desktop app packaging the web UI. Published separately as `opencode-desktop`.

## Code Organization Patterns

1. **Namespace modules**: Most source files export a top-level namespace (e.g., `export namespace Agent { ... }`) containing types, services, and related functions. This avoids namespace pollution and groups related items.

2. **Effect service pattern**: Services are defined as `Context.Service` classes with a `layer` export (an Effect `Layer`) and a `Service` tag. Consumers yield the service tag in `Effect.gen` to access the implementation.

3. **Drizzle schema colocation**: Database table schemas (`*.sql.ts`) live next to the domain module they belong to (e.g., `session/session.sql.ts`, `project/project.sql.ts`).

4. **Platform conditionals via import maps**: The `package.json` `imports` field maps `#db`, `#pty`, and `#hono` to Bun-native or Node.js fallback implementations, selected at bundle time via build conditions.

5. **Zod schema-first**: All configuration, API request/response, and data shapes are defined as Zod schemas, which also generate TypeScript types and OpenAPI documentation via `hono-openapi`.

6. **File-per-route**: Server routes are split into one file per resource group under `src/server/instance/`, each returning a `Hono` sub-application composed in `src/server/instance/index.ts`.
