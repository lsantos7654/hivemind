# OpenCode — Code Structure

## Complete Annotated Directory Tree

```
repo/                                   Root monorepo
├── package.json                        Root Bun workspace config; defines catalog versions
├── turbo.json                          Turborepo pipeline (typecheck, build, test)
├── bunfig.toml                         Bun configuration
├── tsconfig.json                       Root TypeScript config (extends per-package)
├── sst.config.ts                       SST infra config (cloud/infra resources)
├── flake.nix / flake.lock              Nix dev environment
├── CONTRIBUTING.md                     Contribution guide with dev setup
├── .opencode/                          OpenCode's own self-configuration
│   ├── command/                        Built-in slash commands for development use
│   │   ├── commit.md                   AI-assisted git commit
│   │   ├── rmslop.md                   Remove unwanted AI slop
│   │   ├── spellcheck.md              Spell-check docs
│   │   └── ...
│   └── glossary/                       Translation glossaries for localization
│
├── packages/                           All packages in the monorepo
│   ├── opencode/                       *** CORE PACKAGE *** — server, CLI, TUI
│   ├── app/                            Shared web UI (SolidJS, used by web + desktop)
│   ├── console/                        Internal admin console (SolidJS + SolidStart)
│   ├── desktop/                        Desktop app (Tauri wrapping packages/app)
│   ├── desktop-electron/               Electron desktop variant
│   ├── ui/                             Shared UI component library
│   ├── sdk/                            TypeScript SDK (@opencode-ai/sdk)
│   │   ├── js/src/                     SDK source
│   │   │   ├── client.ts               v1 client
│   │   │   ├── server.ts               Embedded server helper
│   │   │   ├── v2/                     v2 client (generated from OpenAPI)
│   │   │   │   ├── client.ts           v2 createOpencodeClient()
│   │   │   │   ├── server.ts           v2 createOpencodeServer()
│   │   │   │   └── gen/                Auto-generated hey-api client
│   │   └── openapi.json                OpenAPI 3.1 specification (generated)
│   ├── plugin/                         Plugin SDK (@opencode-ai/plugin)
│   │   └── src/
│   │       ├── index.ts                Plugin, Hooks, AuthHook, ToolHook types
│   │       └── tool.ts                 ToolDefinition interface for plugins
│   ├── script/                         Internal build/deploy scripts
│   ├── util/                           Shared utilities (@opencode-ai/util)
│   ├── extensions/                     Editor extensions
│   ├── docs/                           Documentation site (Astro)
│   ├── function/                       Serverless functions (SST)
│   ├── enterprise/                     Enterprise-specific code
│   ├── slack/                          Slack integration
│   └── storybook/                      Component storybook
│
├── github/                             GitHub Actions integration
│   ├── action.yml                      Action definition
│   └── index.ts                        Action entry point
│
├── sdks/vscode/                        VS Code extension
└── infra/                              SST/CDK infrastructure definitions
```

## Core Package: `packages/opencode/src/`

This is the heart of the project. All business logic, the HTTP server, CLI, and TUI live here.

```
src/
├── index.ts                    CLI entry point (yargs setup, all commands registered)
│
├── agent/
│   └── agent.ts                Agent.Info schema; built-in agents (build, plan, general, explore);
│                               per-instance agent registry; agent config merging
│
├── session/
│   ├── index.ts                Session CRUD, list, fork, share, revert, message management
│   ├── processor.ts            SessionProcessor: drives the LLM loop (stream → tool dispatch)
│   ├── llm.ts                  LLM.stream(): wraps Vercel AI SDK streamText with per-model options
│   ├── prompt.ts               SessionPrompt.run(): top-level prompt handler, compaction, tool setup
│   ├── system.ts               SystemPrompt: model-specific base system prompt selection
│   ├── instruction.ts          InstructionPrompt: loads instruction files from config
│   ├── compaction.ts           SessionCompaction: overflow detection, context pruning, summarization
│   ├── message-v2.ts           MessageV2 schemas (User, Assistant, TextPart, ToolPart, etc.)
│   ├── session.sql.ts          Drizzle schema: sessions, messages, parts, permissions, todos
│   ├── todo.ts                 Todo list CRUD (per-session)
│   ├── status.ts               SessionStatus: live busy/idle/error state
│   ├── summary.ts              SessionSummary: diff-based session change summary
│   ├── revert.ts               SessionRevert: git-snapshot-based revert/unrevert
│   ├── retry.ts                Retry logic for LLM errors
│   └── prompt/                 System prompt text files (anthropic.txt, gemini.txt, codex_header.txt, …)
│
├── server/
│   ├── server.ts               Hono app factory, listen(), CORS, auth middleware, route mounting
│   ├── event.ts                SSE event types
│   ├── mdns.ts                 mDNS/Bonjour service advertisement
│   └── routes/
│       ├── session.ts          /session/* endpoints (CRUD, prompt, fork, share, revert, …)
│       ├── provider.ts         /provider/* endpoints (list, auth, OAuth)
│       ├── config.ts           /config/* endpoints (get, update, providers)
│       ├── global.ts           /global/* endpoints (health, event stream, config)
│       ├── file.ts             /file/* endpoints (list, read, status)
│       ├── mcp.ts              /mcp/* endpoints (connect, status, auth)
│       ├── project.ts          /project/* endpoints (list, current, update)
│       ├── pty.ts              /pty/* endpoints (create, connect, list)
│       ├── permission.ts       /permission/* endpoints (list, reply, respond)
│       ├── question.ts         /question/* endpoints (list, reply, reject)
│       ├── tui.ts              /tui/* endpoints (TUI control from web clients)
│       ├── workspace.ts        /workspace/* (experimental workspaces)
│       └── experimental.ts     Experimental endpoints
│
├── tool/
│   ├── tool.ts                 Tool.define() factory; Tool.Info interface; validation wrapper
│   ├── registry.ts             ToolRegistry: loads built-ins + plugin tools + custom tool files
│   ├── bash.ts                 bash: shell command execution with tree-sitter analysis
│   ├── edit.ts                 edit: file modification with diff-based strategies
│   ├── write.ts                write: create/overwrite files
│   ├── read.ts                 read: file content with line offset/limit
│   ├── glob.ts                 glob: file pattern matching
│   ├── grep.ts                 grep: content search with regex
│   ├── ls.ts                   ls: directory listing
│   ├── webfetch.ts             webfetch: HTTP fetch + HTML→Markdown conversion
│   ├── websearch.ts            websearch: web search (Exa, etc.)
│   ├── codesearch.ts           codesearch: ripgrep-based code search
│   ├── task.ts                 task: spawn subagent sessions
│   ├── todo.ts                 todo: TodoWrite/TodoRead session task list
│   ├── skill.ts                skill: load and present skill documentation
│   ├── question.ts             question: ask user a clarifying question
│   ├── plan.ts                 plan-enter/plan-exit: mode switching
│   ├── apply_patch.ts          apply_patch: unified diff application
│   ├── multiedit.ts            multiedit: batch file edit tool
│   ├── lsp.ts                  lsp: LSP diagnostics/hover tool
│   ├── batch.ts                batch: batch multiple tool calls (experimental)
│   ├── invalid.ts              invalid: sends a corrective error to the model
│   └── truncation.ts           Truncate: output size limiting with file spill
│
├── provider/
│   ├── provider.ts             Provider registry, model lookup, API key loading,
│   │                           40+ bundled provider factories
│   ├── models.ts               ModelsDev: model catalog fetch/cache from models.dev
│   ├── transform.ts            ProviderTransform: per-provider option normalization
│   ├── auth.ts                 ProviderAuth: available auth methods per provider
│   └── sdk/                    Custom provider SDK overrides (copilot, etc.)
│
├── config/
│   ├── config.ts               Config.Info schema; layered config loading (remote → global →
│   │                           custom → project → .opencode dir → inline); enterprise managed dir
│   ├── paths.ts                ConfigPaths: project/global config file discovery
│   ├── markdown.ts             ConfigMarkdown: frontmatter YAML parsing for commands/skills
│   ├── tui.ts                  TuiConfig: TUI-specific configuration (themes, keybinds, etc.)
│   └── tui-schema.ts           Zod schemas for TUI configuration
│
├── cli/
│   ├── bootstrap.ts            bootstrap(): wrap a callback in an Instance context
│   ├── ui.ts                   UI: colored terminal output helpers, logo
│   ├── network.ts              Network option parsing (host/port)
│   ├── upgrade.ts              Auto-upgrade logic
│   └── cmd/
│       ├── run.ts              `opencode run` — non-interactive CLI mode
│       ├── serve.ts            `opencode serve` — headless server
│       ├── web.ts              `opencode web` — server + browser UI
│       ├── auth.ts             `opencode auth` — API key management
│       ├── models.ts           `opencode models` — list available models
│       ├── mcp.ts              `opencode mcp` — MCP server management
│       ├── agent.ts            `opencode agent` — list/inspect agents
│       ├── session.ts          `opencode session` — session management
│       ├── acp.ts              `opencode acp` — ACP server
│       ├── github.ts           `opencode github` — GitHub PR integration
│       ├── upgrade.ts          `opencode upgrade`
│       └── tui/                TUI sub-commands
│           ├── thread.ts       `opencode [project]` — default TUI launcher
│           ├── attach.ts       `opencode attach` — attach to running session
│           ├── app.tsx         TUI SolidJS root component
│           ├── worker.ts       TUI worker thread (runs the server)
│           ├── event.ts        TUI-specific event types
│           ├── component/      TUI UI components (dialogs, prompt, etc.)
│           ├── routes/         TUI page routes (home, session)
│           ├── context/        SolidJS context providers (SDK, sync, theme, etc.)
│           └── ui/             Lower-level TUI UI primitives
│
├── lsp/
│   ├── index.ts                LSP namespace entry; coordinate LSP clients per file
│   ├── server.ts               LSPServer: spawn definitions for 10+ language servers
│   ├── client.ts               LSPClient: JSON-RPC over stdio
│   └── language.ts             Language→extensions mapping
│
├── mcp/
│   ├── index.ts                MCP namespace; client management, tool conversion
│   ├── auth.ts                 MCP auth storage
│   ├── oauth-provider.ts       MCP OAuth 2.0 provider
│   └── oauth-callback.ts       OAuth callback handler
│
├── permission/
│   └── next.ts                 PermissionNext: ruleset evaluation, allow/deny/ask per tool+pattern
│
├── auth/
│   └── index.ts                Auth: API key and OAuth token storage (~/.local/share/opencode/auth.json)
│
├── storage/
│   ├── db.ts                   Database: Bun SQLite + Drizzle client, migration runner
│   ├── schema.ts               Aggregated schema exports
│   ├── schema.sql.ts           Top-level SQL schema
│   └── json-migration.ts       Migration from legacy JSON storage to SQLite
│
├── project/
│   ├── instance.ts             Instance: per-directory context provider, state factory
│   ├── bootstrap.ts            InstanceBootstrap: init hook (LSP, MCP, plugins, watchers)
│   ├── project.ts              Project: detect VCS, project metadata
│   ├── project.sql.ts          Drizzle schema for projects
│   ├── state.ts                State: per-instance state factory with lifecycle management
│   └── vcs.ts                  VCS: git detection and operations
│
├── acp/
│   ├── agent.ts                ACP.Agent: implements @agentclientprotocol/sdk AgentSide
│   ├── session.ts              ACPSessionManager: maps ACP sessions to opencode sessions
│   └── types.ts                ACP config types
│
├── plugin/
│   └── index.ts                Plugin: loads built-in and npm plugins; fires lifecycle hooks
│
├── bus/
│   ├── index.ts                Bus: in-process pub/sub per Instance
│   ├── bus-event.ts            BusEvent.define() — typed event definitions
│   └── global.ts               GlobalBus: cross-instance event emitter (Node EventEmitter)
│
├── snapshot/
│   └── index.ts                Snapshot: hidden git repo for file change tracking
│
├── worktree/
│   └── index.ts                Worktree: git worktree creation/removal for isolated sessions
│
├── control-plane/
│   ├── workspace.ts            Workspace: cloud/remote workspace management
│   ├── workspace-context.ts    WorkspaceContext: current workspace resolution
│   ├── workspace-router-middleware.ts  Route-level workspace injection
│   └── adaptors/               Workspace adaptor implementations (Codespace, Daytona, etc.)
│
├── command/
│   └── index.ts                Command: slash command discovery, template rendering, MCP commands
│
├── skill/
│   └── skill.ts                Skill: SKILL.md file discovery and registry
│
├── format/
│   └── index.ts                Format: post-edit formatter dispatch
│
├── file/
│   ├── index.ts                File: file read/write with event publication
│   ├── ripgrep.ts              Ripgrep: directory tree/search utilities
│   ├── time.ts                 FileTime: modification-time locking
│   └── watcher.ts              FileWatcher: parcel-watcher-based change detection
│
├── global/
│   └── index.ts                Global.Path: XDG-based data/cache/config/state directories
│
├── flag/
│   └── flag.ts                 Flag: all OPENCODE_* environment variable flags
│
├── installation/
│   └── index.ts                Installation: version, local dev detection, binary path
│
├── scheduler/
│   └── index.ts                Scheduler: interval task runner (snapshot cleanup, etc.)
│
└── util/                       Shared low-level utilities
    ├── log.ts                  Log: structured logger with tagging
    ├── context.ts              Context: async-context-variable abstraction
    ├── lazy.ts                 lazy(): memoized async initializer
    ├── fn.ts                   fn(): Zod-validated function wrapper
    ├── rpc.ts                  Rpc: Worker thread JSON-RPC bridge
    ├── filesystem.ts           Filesystem: async file helpers
    ├── abort.ts                Abort signal utilities
    ├── glob.ts                 Glob: bun Glob wrapper
    ├── token.ts                Token: rough token estimator
    └── ...
```

## Code Organization Patterns

- **Namespace modules** — Nearly every module exports a single TypeScript `namespace` (e.g., `Session`, `Provider`, `Agent`) that groups related types, constants, and functions. This avoids class-based OOP in favor of plain functions.
- **Zod-first schemas** — All data shapes are defined as `z.object(…)` with `.meta({ ref: "…" })` for OpenAPI schema generation. Types are inferred via `z.infer<typeof Foo>`.
- **`Instance.state()`** — Per-directory singleton state, automatically scoped and disposed with the Instance lifecycle.
- **`Tool.define()`** — Tool registration always goes through this factory, which handles input validation and output truncation.
- **`BusEvent.define()` + `Bus.publish()`** — Typed pub/sub for decoupled event propagation across modules.
- **SQL schemas in `.sql.ts` files** — Drizzle table definitions co-located with their domain modules.
- **Text prompt files as `.txt` imports** — System prompts and tool descriptions are stored as plain text files imported via Bun's native text import.
- **`lazy()`** — Memoized per-instance async initializers used for expensive one-time setup (LSP, MCP, tool registry).
