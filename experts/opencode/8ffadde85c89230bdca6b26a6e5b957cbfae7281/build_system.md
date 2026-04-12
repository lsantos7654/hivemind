# OpenCode — Build System

## Build System Type

OpenCode uses a **Bun-first monorepo** with:

- **Bun** (`1.3.11`) — runtime, package manager, test runner, and bundler/compiler
- **Turborepo** (`turbo@2.8.13`) — task orchestration and caching across packages
- **SST v3** — cloud infrastructure as code for backend deployment (Cloudflare Workers, PlanetScale)
- **Drizzle Kit** — database schema management and migration generation
- **TypeScript** (`5.8.2`) with `tsgo` (TypeScript native preview) for type checking

## Configuration Files

| File | Purpose |
|------|---------|
| `package.json` (root) | Bun workspace definition, catalog (shared dep versions), root scripts |
| `bunfig.toml` | Bun runtime configuration |
| `turbo.json` | Turborepo task pipeline (typecheck, build, test) |
| `sst.config.ts` | Cloud infra deployment (Cloudflare home, Stripe, PlanetScale) |
| `packages/opencode/package.json` | Core package scripts and dependencies |
| `packages/opencode/tsconfig.json` | TypeScript config for core package |
| `packages/opencode/drizzle.config.ts` | Drizzle ORM schema and migration config |
| `packages/opencode/script/build.ts` | Multi-platform binary compilation script |
| `packages/opencode/script/generate.ts` | OpenAPI spec and SDK type generation |
| `packages/sdk/js/script/build.ts` | JavaScript SDK build script |
| `flake.nix` / `nix/` | Nix flake for reproducible development environments |

## Workspace Structure

The root `package.json` defines Bun workspaces:

```json
{
  "workspaces": {
    "packages": [
      "packages/*",
      "packages/console/*",
      "packages/sdk/js",
      "packages/slack"
    ],
    "catalog": { ... }  // Pinned shared dependency versions
  }
}
```

The `catalog` section pins versions for shared dependencies (e.g., `effect`, `zod`, `drizzle-orm`, `solid-js`, `typescript`) so all packages use the same version without repeating version strings.

## External Dependencies and Management

All dependencies are managed by Bun. Key dependency groups:

### AI Provider SDKs (in `packages/opencode`)
- `@ai-sdk/*` — Vercel AI SDK provider adapters (Anthropic, OpenAI, Google, Azure, Bedrock, Mistral, Groq, Cerebras, Cohere, DeepInfra, Perplexity, TogetherAI, Vercel, xAI, OpenAI-compatible, gateway)
- `@openrouter/ai-sdk-provider`, `venice-ai-sdk-provider`, `gitlab-ai-provider` — third-party AI SDK providers
- `ai@6.x` — Vercel AI SDK core

### Effect Ecosystem
- `effect@4.x` — core Effect library
- `@effect/platform-node` — Effect platform bindings for Node.js

### HTTP Server
- `hono@4.x` — web framework
- `hono-openapi` — OpenAPI spec generation for Hono routes
- `@hono/node-server`, `@hono/node-ws` — Node.js adapter for Hono

### UI Framework (for embedded TUI)
- `@opentui/core`, `@opentui/solid` — custom terminal UI framework
- `solid-js`, `@solidjs/router`, `@solidjs/start` — SolidJS for web/TUI frontends

### Database
- `drizzle-orm` (catalog pinned) — ORM and query builder
- `drizzle-kit` — schema management / migration generation
- SQLite accessed via `Bun.sqlite` or `better-sqlite3` (Node.js fallback)

### PTY / Terminal
- `@lydell/node-pty`, `bun-pty` — pseudo-terminal bindings (platform-conditional via import maps)

### Protocol
- `@modelcontextprotocol/sdk` — MCP client
- `@agentclientprotocol/sdk` — ACP (JSON-RPC over stdio)
- `vscode-jsonrpc` — JSON-RPC implementation for LSP

### Build-time / Dev
- `husky` — git hooks
- `prettier` — code formatting
- `turbo` — monorepo task runner
- `tree-sitter-bash`, `tree-sitter-powershell`, `web-tree-sitter` — parser workers (embedded in binary)

## Build Targets and Commands

### Root-level Scripts

```bash
# Run dev server (TUI) locally without building
bun run dev

# Run desktop app in dev mode
bun run dev:desktop

# Run web UI dev server
bun run dev:web

# Run web console dev server
bun run dev:console

# Run Storybook for UI components
bun run dev:storybook

# Type-check all packages (via Turborepo)
bun run typecheck
```

### Core Package (`packages/opencode`)

```bash
# Run directly without building (development)
bun run dev

# Build self-contained binaries for all platforms
bun run build

# Build only for current platform
bun run build -- --single

# Build only for current platform + baseline (no AVX2)
bun run build -- --single --baseline

# Type-check (using tsgo, TypeScript native preview)
bun run typecheck

# Run tests (30 second timeout)
bun run test

# Run tests with JUnit output (CI)
bun run test:ci

# Generate Drizzle migration
bun run db generate --name <slug>

# Fix node-pty after install
bun run fix-node-pty

# Upgrade @opentui dependency
bun run upgrade-opentui
```

### Build Process Detail (`packages/opencode/script/build.ts`)

The build script:

1. Runs `script/generate.ts` to regenerate the OpenAPI spec and SDK types.
2. Builds the web UI (`packages/app`) and embeds it as a virtual file map in the binary.
3. Loads all SQL migration files from `migration/` directories into a JSON constant (`OPENCODE_MIGRATIONS`).
4. Compiles a self-contained binary for each target platform using `Bun.build` with `compile: true`:
   - Entrypoints: `src/index.ts`, `parser.worker.js` (from `@opentui/core`), TUI worker
   - All bundled into a single native executable (no Node.js/Bun runtime required at runtime)
   - Defines: `OPENCODE_VERSION`, `OPENCODE_MIGRATIONS`, `OPENCODE_CHANNEL`, `OPENCODE_LIBC`
5. Runs a smoke test (`opencode --version`) for binaries matching the current host platform.
6. On release (`Script.release`): creates `.zip`/`.tar.gz` archives and uploads to GitHub Releases.

**Supported targets:**

| OS | Arch | Variant |
|----|------|---------|
| Linux | arm64 | glibc |
| Linux | x64 | glibc |
| Linux | x64 | glibc baseline (no AVX2) |
| Linux | arm64 | musl |
| Linux | x64 | musl |
| Linux | x64 | musl baseline |
| macOS | arm64 | — |
| macOS | x64 | — |
| macOS | x64 | baseline |
| Windows | arm64 | — |
| Windows | x64 | — |
| Windows | x64 | baseline |

### SDK Build (`packages/sdk/js/script/build.ts`)

The JS SDK is generated from `packages/sdk/openapi.json` and rebuilt with:

```bash
./packages/sdk/js/script/build.ts
```

### Turborepo Pipeline (`turbo.json`)

```json
{
  "tasks": {
    "typecheck": {},              // No dependencies; run per-package
    "build": { "outputs": ["dist/**"] },
    "opencode#test": { "dependsOn": ["^build"] },    // Tests need deps built
    "opencode#test:ci": { "dependsOn": ["^build"] }
  }
}
```

## How to Build, Test, and Deploy

### Development (no build needed)

```bash
# Install dependencies
bun install

# Start the opencode TUI against a project directory
bun run dev -- /path/to/project
```

### Type Checking

```bash
# Check all packages
bun run typecheck

# Check only the core package
cd packages/opencode && bun run typecheck
```

### Testing

```bash
# Run tests in the core package (cannot run from root)
cd packages/opencode
bun test

# Run specific test file
bun test test/session.test.ts

# CI mode with JUnit report
bun run test:ci
```

### Building the CLI Binary

```bash
# Build for all platforms (produces dist/<platform>/bin/opencode)
cd packages/opencode
bun run build

# Build for current platform only (faster)
bun run build -- --single

# Skip web UI embedding (faster, no web UI)
bun run build -- --single --skip-embed-web-ui
```

### Database Migrations

```bash
cd packages/opencode

# Generate a new migration (after editing src/**/*.sql.ts schema files)
bun run db generate --name my-change

# Output: migration/<timestamp>_my-change/migration.sql + snapshot.json
```

### Cloud Deployment (Backend/Enterprise)

The cloud backend (identity, console, enterprise APIs) is deployed with SST v3:

```bash
# Deploy to a stage
sst deploy --stage production

# Infrastructure is defined in:
# infra/app.js
# infra/console.js
# infra/enterprise.js
```

The SST config targets Cloudflare Workers as the `home` provider and uses PlanetScale for managed MySQL and Stripe for billing.

## Installation

End users install the pre-compiled binary via:

```bash
# One-liner installer
curl -fsSL https://opencode.ai/install | bash

# npm / bun / pnpm / yarn
npm i -g opencode-ai@latest

# Homebrew
brew install anomalyco/tap/opencode
```

The install script respects `$OPENCODE_INSTALL_DIR`, `$XDG_BIN_DIR`, and `$HOME/bin` for the installation path.
