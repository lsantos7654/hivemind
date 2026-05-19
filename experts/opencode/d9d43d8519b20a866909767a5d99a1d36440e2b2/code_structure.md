The OpenCode repository is a large Bun-based monorepo. At the root are the product README files, workspace configuration (`package.json`, `turbo.json`, `tsconfig.json`, `bun.lock`), infrastructure definitions (`sst.config.ts`, `infra/`), a shell installer (`install`), and many product packages under `packages/`. The top-level layout reads roughly as follows:

```text
.
├── package.json                 # Workspace root; Bun version, scripts, dependency catalog
├── turbo.json                   # Turborepo task graph for build/typecheck/test
├── tsconfig.json                # Root TS config extending @tsconfig/bun
├── bun.lock / bunfig.toml       # Bun lockfile and runtime config
├── sst.config.ts                # SST app entrypoint for Cloudflare-hosted infrastructure
├── infra/                       # SST/Cloudflare resources for API, docs, console, enterprise
├── install                      # Standalone shell installer for released binaries
├── github/                      # GitHub Action implementation for comment-driven automation
├── packages/                    # Main monorepo workspace collection
├── script/                      # Root-level helper scripts
├── sdks/                        # Additional SDK distributions (for example VS Code)
├── specs/                       # Specifications and design artifacts
├── patches/                     # Patched dependency sources
├── perf/                        # Performance and benchmarking notes
└── README*.md                   # Multilingual documentation
```

The root `package.json` shows the repo’s organizational intent. It defines workspaces for `packages/*`, `packages/console/*`, `packages/sdk/js`, and `packages/slack`, and centralizes a large version catalog for Effect, AI SDK provider packages, Solid, Vite, Drizzle, Hono, OpenTUI, Playwright, and TypeScript. Root scripts are intentionally lightweight: `dev` runs the main `packages/opencode` entrypoint, while `dev:web`, `dev:desktop`, `dev:console`, `typecheck`, and `lint` dispatch into package-local tooling.

## Core runtime package: `packages/opencode`

`packages/opencode` is the executable application and the most important directory in the repository. Its own `package.json` declares the `opencode` binary, exports `./src/*.ts`, provides Bun scripts for `dev`, `build`, `test`, `test:httpapi`, `bench:test`, `profile:test`, and `db`, and depends on the broadest set of runtime libraries.

Its `src/` tree is extensive:

```text
packages/opencode/src/
├── index.ts                     # CLI bootstrap, logging, DB migration, command registration
├── account/                     # Account and auth-related workflows
├── acp/                         # ACP support
├── agent/                       # Agent schema, built-in agents, generation prompts
├── auth/                        # Authentication helpers
├── background/                  # Background job execution
├── bus/                         # Event bus and event definitions
├── cli/                         # CLI command implementations and terminal UI support
├── command/                     # Command parsing/execution helpers
├── config/                      # Config schemas and loaders
├── control-plane/               # Workspace/control-plane constructs
├── effect/                      # Effect runtime helpers and state
├── file/                        # File search and read helpers
├── format/                      # Output formatting utilities
├── git/                         # Git integration
├── ide/ / lsp/                  # IDE/LSP integration layers
├── mcp/                         # Model Context Protocol support
├── permission/                  # Permission model and schema
├── project/                     # Project discovery and instance context
├── provider/                    # Model/provider runtime selection
├── pty/                         # PTY backends and terminal plumbing
├── reference/                   # Reference/repository cache helpers
├── server/                      # HTTP API, SSE, routing, server startup
├── session/                     # Session state, prompts, messages, summaries, retries
├── share/                       # Sharing/export flows
├── shell/                       # Shell command support
├── skill/                       # Skill discovery and loading
├── snapshot/                    # Diffs and file snapshots
├── storage/                     # DB and storage adapters
├── sync/                        # Sync events and shared-session syncing
├── tool/                        # Built-in tools exposed to agents
├── v2/                          # Newer versioned schemas/services
└── worktree/                    # Managed worktree support
```

Several subtrees are especially central. `cli/` contains command modules such as `run`, `serve`, `mcp`, `providers`, `agent`, `github`, `web`, `session`, `stats`, `db`, and TUI-specific commands under `cli/cmd/tui/`. `server/` hosts the typed HTTP API; its `routes/instance/httpapi/` subtree contains the composed API spec, middleware, route groups, handlers, and public OpenAPI shaping logic. `session/` is effectively the product’s conversational state engine, holding schemas for session/message objects plus services for prompt loops, retries, compaction, summaries, todos, status, and revert. `tool/` mirrors the tool vocabulary seen by agents, with one file per tool and a `registry.ts` that assembles the active tool list.

The `test/` directory under `packages/opencode` mirrors much of the source tree. It includes test suites for `account`, `agent`, `background`, `cli`, `config`, `file`, `git`, `lsp`, `mcp`, `permission`, `provider`, `server`, `session`, `skill`, `snapshot`, `storage`, `sync`, `tool`, and `v2`. That mirrored structure is a useful map when tracing behavior or looking for usage examples. The sibling `script/` directory contains operational scripts such as `build.ts`, `generate.ts`, `httpapi-exercise.ts`, `fix-node-pty.ts`, and profiling or publication helpers.

## Shared libraries and platform packages

`packages/core` is the main shared library. Its `src/` directory contains provider and model schema definitions, the `CatalogV2` service, filesystem helpers, plugin abstractions, session prompt/message schema helpers, and utility modules. If `packages/opencode` is the runnable product, `packages/core` is the shared typed substrate.

`packages/llm` is a dedicated LLM abstraction library. It exports provider-neutral request/response/event/tool constructs plus concrete provider modules for Anthropic, OpenAI, Google, Bedrock, Azure, Cloudflare, GitHub Copilot, OpenRouter, xAI, and generic OpenAI-compatible backends. This package is intentionally decoupled so that provider protocol churn does not leak across the rest of the app.

`packages/sdk/js` is the generated SDK package. Its exports include root client/server entrypoints plus a `v2` namespace and generated OpenAPI client code under `src/v2/gen`. This is the package to inspect when integrating OpenCode programmatically from another TypeScript project.

`packages/plugin` defines the plugin authoring surface, exporting `index.ts`, `tool.ts`, and `tui.ts`. It is designed for external extensions that want to contribute tools or TUI integrations while depending only on the stable SDK/plugin contracts.

## User interfaces and hosted surfaces

`packages/app` is the browser web application built with Solid and Vite. Its `src/` tree contains `components/`, `pages/`, `context/`, `hooks/`, `i18n/`, `addons/`, `constants/`, and `utils/`. The package also carries Playwright-based `e2e/` smoke tests.

`packages/desktop` is the Electron desktop app. Its source is cleanly separated into `src/main/` (Electron main process, native integration, updater, IPC, sidecar/server handling), `src/preload/` (bridging APIs into renderer), and `src/renderer/` (Solid UI, i18n bundles, HTML entrypoints, CSS, updater UI).

`packages/web` is the documentation/marketing site built with Astro and Starlight. `packages/console/*` hosts the SaaS/console stack: `console/app` for the frontend, `console/core` for backend and data logic, `console/resource` and `console/function` for supporting services, and `console/mail` for email-related code. `packages/enterprise` is a separate Solid/Vite application targeting enterprise deployment scenarios.

## Peripheral and integration packages

Other notable packages include `packages/function` for Cloudflare Worker APIs and the `SyncServer` durable object, `packages/http-recorder` for test-time HTTP capture/replay, `packages/ui` for shared UI components, `packages/slack` for Slack integration, `packages/script` for reusable build/publish utilities, `packages/storybook` for component development, `packages/containers` for container-related assets, and `packages/docs` / `packages/extensions` / `packages/identity` for ancillary product surfaces.

## Architectural patterns

A few structural patterns recur throughout the codebase. First, the repository prefers schema-driven domain models using Effect `Schema` and `Context.Service`, producing typed services like `Agent.Service`, `Session.Service`, `Skill.Service`, `Catalog.Service`, `ToolRegistry.Service`, and `WebSocketTracker.Service`. Second, HTTP routes are grouped declaratively under `server/routes/instance/httpapi/groups/*`, then wired to handlers and middleware, keeping route definitions and implementation close but separate. Third, tool behavior is file-per-tool, making it easy to map prompt-visible tool names to implementation files. Fourth, source and tests track one another closely, so the tree itself acts as documentation for supported subsystems.

For maintainers, the code organization is pragmatic: if you are changing end-user CLI behavior, start in `packages/opencode/src/cli/`; if you are changing conversational semantics, inspect `session/` and `agent/`; if you are working on server APIs, use `server/routes/instance/httpapi/`; if you are touching provider/model normalization, begin in `packages/core` and `packages/llm`; and if you are working on product surfaces outside the terminal, move into `packages/app`, `packages/desktop`, `packages/web`, or `packages/console`.
