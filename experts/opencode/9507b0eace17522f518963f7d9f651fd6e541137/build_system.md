# OpenCode — Build System

## Build System Type

OpenCode is a **Bun monorepo** using:

- **Bun** (1.3+) as the primary runtime, test runner, and bundler.
- **Turborepo** (`turbo.json`) for task orchestration across packages.
- **TypeScript** 5.8 + `@typescript/native-preview` (tsgo) for type checking.
- **Drizzle Kit** for database migration generation.
- **Tauri** (Rust + Vite) for the desktop application.
- **SST** for cloud infrastructure (functions, storage, etc.).

## Configuration Files

| File | Purpose |
|---|---|
| `package.json` (root) | Workspace definition, catalog versions, root scripts |
| `bunfig.toml` | Bun runtime configuration |
| `turbo.json` | Turborepo task graph |
| `tsconfig.json` (root) | Base TypeScript config |
| `packages/opencode/package.json` | Core package deps, bin entry point |
| `packages/opencode/tsconfig.json` | opencode TS config (paths, etc.) |
| `packages/opencode/drizzle.config.ts` | Drizzle Kit config (schema glob, output dir) |
| `packages/opencode/script/build.ts` | Production build script |
| `packages/opencode/bin/opencode` | Shell shim that invokes `src/index.ts` |

## External Dependencies and Management

Dependencies are managed with `bun install`. The root `package.json` uses a **catalog** for shared version pinning across packages:

```json
"workspaces": {
  "packages": ["packages/*", "packages/console/*", "packages/sdk/js", "packages/slack"],
  "catalog": {
    "ai": "5.0.124",
    "zod": "4.1.8",
    "solid-js": "1.9.10",
    "hono": "4.10.7",
    ...
  }
}
```

Key dependency groups:
- **AI SDK**: `ai` (Vercel AI SDK core) + `@ai-sdk/*` provider adapters + `@openrouter/ai-sdk-provider`, `@gitlab/gitlab-ai-provider`.
- **Server**: `hono` + `hono-openapi` for HTTP + OpenAPI spec generation; `@hono/zod-validator`.
- **Database**: `drizzle-orm` (beta `1.0.0-beta.12`) + `bun:sqlite`.
- **TUI**: `@opentui/core`, `@opentui/solid`, `solid-js`, `@parcel/watcher` (file watching).
- **Protocols**: `@modelcontextprotocol/sdk` (MCP), `@agentclientprotocol/sdk` (ACP).
- **Parsing**: `web-tree-sitter` + `tree-sitter-bash` (bash command analysis), `jsonc-parser`.
- **Utilities**: `zod`, `remeda` (functional utils), `ulid` (IDs), `fuzzysort`, `xdg-basedir`, `yargs`.

Two packages are patched locally:
- `patches/@standard-community%2Fstandard-openapi@0.2.9.patch`
- `patches/@openrouter%2Fai-sdk-provider@1.5.4.patch`

## Build Targets and Commands

### Development

```bash
# Install all dependencies (from repo root)
bun install

# Start the TUI in the opencode directory
bun dev

# Start TUI against a specific directory
bun dev <path>

# Start the web interface
bun dev:web

# Start the desktop app
bun dev:desktop

# Start Storybook
bun dev:storybook
```

`bun dev` runs `packages/opencode/src/index.ts` directly using Bun (no compilation step). The `--conditions=browser` flag is passed to select the correct export conditions for TUI rendering.

### Type Checking

```bash
# Type-check all packages
bun turbo typecheck

# Type-check a single package (from package directory)
bun run typecheck   # uses tsgo --noEmit
```

### Testing

Tests use Bun's built-in test runner. Tests **cannot** be run from the repo root (a guard enforces this). Run from the package directory:

```bash
cd packages/opencode
bun test --timeout 30000

# Run a specific test file
bun test test/session/session.test.ts

# Run with coverage
bun test --coverage
```

### Database Migrations

```bash
cd packages/opencode
bun run db generate --name <slug>
# Output: migration/<timestamp>_<slug>/migration.sql + snapshot.json
```

The `drizzle.config.ts` scans `./src/**/*.sql.ts` for schema definitions and outputs to `./migration/`.

### Production Build

The production build produces self-contained executables via Bun's bundler:

```bash
# Build for all platforms
./packages/opencode/script/build.ts

# Build single executable for current platform only
./packages/opencode/script/build.ts --single

# Build baseline (no AVX2)
./packages/opencode/script/build.ts --baseline
```

The build script (`script/build.ts`):
1. Fetches the `models.dev` API snapshot and writes it as `src/provider/models-snapshot.ts`.
2. Reads all migration SQL files and embeds them as a constant (`OPENCODE_MIGRATIONS`).
3. Builds the TUI worker (`tui/worker.ts`) as a separate bundle with SolidJS JSX transform.
4. Bundles the main entry point (`src/index.ts`) using `Bun.build()` with targets for:
   - `linux-arm64`, `linux-x64` (glibc + musl), `linux-x64` (no AVX2)
   - `darwin-arm64`, `darwin-x64`
   - `windows-x64`
5. Optionally bundles the GitHub Action entry point.

Output goes to `dist/opencode-<os>-<arch>/bin/opencode`.

### SDK Build

```bash
cd packages/sdk/js
bun ./script/build.ts
# Generates dist/ with CJS/ESM builds and type declarations
# Also regenerates the hey-api client from openapi.json
```

To regenerate the OpenAPI spec and SDK client:
```bash
# From repo root
./packages/sdk/js/script/build.ts
```

### Plugin Build

```bash
cd packages/plugin
bun run build   # tsc → dist/
```

### Desktop Build

```bash
bun dev:desktop   # Tauri dev mode (requires Rust toolchain)
```

### GitHub Action

```bash
cd github
bun run script/build  # esbuild bundle → dist/
```

## How to Deploy

### Publishing to npm

GitHub Actions workflows handle publishing:

- `.github/workflows/publish.yml` — publishes `opencode-ai` to npm on version tags.
- `.github/workflows/beta.yml` — publishes beta versions.
- `.github/workflows/publish-vscode.yml` — publishes the VS Code extension.
- `.github/workflows/publish-python-sdk.yml` — publishes the Python SDK.

### Container Build

- `.github/workflows/containers.yml` — builds and pushes Docker images.
- `packages/opencode/Dockerfile` — production container definition.

### Nix

- `flake.nix` provides a Nix development shell and derivation.
- `.github/workflows/nix-hashes.yml` / `nix-eval.yml` — keep the Nix flake up to date.

## Key Environment Variables

| Variable | Purpose |
|---|---|
| `OPENCODE_CONFIG` | Path to a custom config file |
| `OPENCODE_CONFIG_CONTENT` | Inline JSON config (overrides file config) |
| `OPENCODE_CONFIG_DIR` | Custom `.opencode` directory path |
| `OPENCODE_DISABLE_PROJECT_CONFIG` | Disable project-level config loading |
| `OPENCODE_SERVER_PASSWORD` | HTTP basic auth password for `opencode serve` |
| `OPENCODE_SERVER_USERNAME` | HTTP basic auth username |
| `OPENCODE_INSTALL_DIR` | Override binary installation directory |
| `OPENCODE_DISABLE_AUTOUPDATE` | Disable automatic updates |
| `OPENCODE_DISABLE_LSP_DOWNLOAD` | Skip LSP binary download |
| `OPENCODE_ENABLE_EXPERIMENTAL_MODELS` | Show experimental models |
| `OPENCODE_EXPERIMENTAL` | Enable all experimental features |
| `OPENCODE_MODELS_URL` | Override models.dev endpoint |
| `OPENCODE_TEST_HOME` | Override home dir in tests |
| `OPENCODE_TEST_MANAGED_CONFIG_DIR` | Override managed config dir in tests |
| `OPENCODE_GIT_BASH_PATH` | Custom git-bash path on Windows |

## CI/CD Workflows

Key GitHub Actions workflows in `.github/workflows/`:

| Workflow | Trigger | Purpose |
|---|---|---|
| `test.yml` | PR / push | Run `bun test` across packages |
| `typecheck.yml` | PR / push | `bun turbo typecheck` |
| `publish.yml` | Version tag | Publish npm package |
| `beta.yml` | Manual/schedule | Publish beta |
| `deploy.yml` | Push to dev | Deploy web/docs |
| `generate.yml` | Code change | Regenerate OpenAPI/SDK |
| `opencode.yml` | PRs | Run OpenCode itself on PRs |
| `containers.yml` | Push | Build Docker images |
