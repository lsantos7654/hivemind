OpenCode uses Bun as its package manager, runtime, test runner, and compiler target, with Turborepo coordinating monorepo tasks and SST handling cloud deployment. The root `package.json` sets `packageManager` to `bun@1.3.14`, and nearly every package-local script assumes a Bun-centric workflow such as `bun test`, `bun run`, `bun dev`, or `bun install`. The root `turbo.json` provides the workspace task graph for `typecheck`, `build`, `test`, and CI-flavored test targets, while package-level `package.json` files define the actual commands that Turborepo orchestrates.

## Workspace and dependency management

Dependency management is centralized in the root workspace. The root `package.json` declares workspace globs for `packages/*`, `packages/console/*`, `packages/sdk/js`, and `packages/slack`, then uses the Bun workspace catalog to pin shared versions for major dependencies such as `effect`, `ai`, `hono`, `drizzle-orm`, `vite`, `solid-js`, `@playwright/test`, and multiple AI provider SDKs. The lockfile is `bun.lock`, and there is also a `bunfig.toml` at the root.

This setup means there are two levels of dependencies to keep in mind:

- root-catalog dependencies shared across many packages;
- package-local dependencies and scripts in each subproject.

Formatting and linting are intentionally simple at the root: `lint` runs `oxlint`, and formatting preferences live under the root `prettier` key (`semi: false`, `printWidth: 120`). Type checking is generally package-local via `tsgo --noEmit` or `tsgo -b`, but is typically orchestrated from the root with `bun turbo typecheck`.

## Main development commands

The root scripts are the starting point for most work:

- `bun run dev` launches the main `packages/opencode` runtime with browser conditions enabled.
- `bun run dev:web` starts the browser app in `packages/app`.
- `bun run dev:desktop` starts the Electron desktop package.
- `bun run dev:console` starts the console app, with a high file-descriptor limit when available.
- `bun run dev:storybook` starts Storybook.
- `bun run lint` runs Oxlint.
- `bun run typecheck` delegates to Turborepo.

The root `test` script deliberately fails with “do not run tests from root”, which is a strong convention signal: tests should be run at the package level or through targeted Turbo/Bun commands, not through a blanket workspace command with ambiguous scope.

## Building the CLI runtime

The heaviest build path lives in `packages/opencode`. Its `scripts` include:

- `build`: `bun run script/build.ts`
- `dev`: `bun run --conditions=browser ./src/index.ts`
- `test`: `bun test --timeout 30000`
- `test:httpapi`: exercise the HTTP API in multiple modes
- `db`: `bun drizzle-kit`

`packages/opencode/script/build.ts` is the key build script. It does more than bundle TypeScript: it loads SQL migrations from timestamped directories, optionally builds the web UI from `packages/app` so it can be embedded into the binary, assembles a target matrix for Linux/macOS/Windows and multiple CPU variants, invokes `Bun.build()` with `compile` enabled to produce self-contained executables, sets compile-time constants such as `OPENCODE_VERSION`, `OPENCODE_MIGRATIONS`, and worker paths, and then runs a smoke test (`opencode --version`) for the native platform build. This makes the CLI build closer to a release pipeline than a simple transpilation step.

The same package also carries `script/fix-node-pty.ts`, invoked from the root `postinstall`, which indicates that native PTY dependencies require post-install adjustment. Other support scripts include `generate.ts`, `publish.ts`, `check-migrations.ts`, `profile-test-files.ts`, and `httpapi-exercise.ts`.

## Package-specific build/test patterns

Several subpackages follow repeatable conventions:

- `packages/core`, `packages/llm`, `packages/http-recorder`, `packages/plugin`, and `packages/sdk/js` mostly use `tsgo --noEmit` for type checking, `bun test` where relevant, and lightweight build scripts or `tsc` when they publish generated output.
- `packages/app` uses Vite for `dev`, `build`, and `serve`, with unit tests run through Bun plus Happy DOM and browser E2E tests run through Playwright.
- `packages/desktop` uses `electron-vite` for development/build and `electron-builder` for platform packaging, with `predev` and `prebuild` hooks preparing assets.
- `packages/web` uses Astro commands (`astro dev`, `astro build`, `astro preview`).
- `packages/enterprise` uses Vite and has a special `build:cloudflare` mode.
- `packages/console/app` uses Vite, but its `build` script also generates a sitemap and emits config/schema artifacts through the `opencode` package’s schema generator.

Testing is similarly package-scoped. The main runtime and several libraries use `bun test`; the browser app adds Playwright E2E tests; and some packages provide `test:ci` scripts that emit JUnit XML into `.artifacts/unit/junit.xml` for CI ingestion.

## SDK generation and OpenAPI

The JavaScript SDK has a distinctive build path. `packages/sdk/js/script/build.ts` starts a local OpenCode dev server command (`bun dev generate`) to emit an OpenAPI document, then feeds that into `@hey-api/openapi-ts` to generate typed client code under `src/v2/gen`. After generation it formats the output with Prettier, compiles with `bun tsc`, and removes the temporary `openapi.json`. This means the SDK is downstream of the server’s typed API declarations rather than hand-maintained.

## Database and migrations

OpenCode uses Drizzle for database tooling. `packages/opencode/package.json` exposes `db: bun drizzle-kit`, and the main CLI bootstrap in `src/index.ts` performs a one-time migration if the expected SQLite marker file does not exist, showing progress in the terminal. The build script embeds migration SQL into the compiled artifact by scanning timestamped migration directories. Console-related packages also expose `db`, `db-dev`, and `db-prod` commands through `sst shell`, suggesting separate hosted database workflows for SaaS infrastructure.

## Deployment and release paths

For cloud deployment, SST is the controlling layer. `sst.config.ts` defines the app as a Cloudflare-backed SST project and imports `infra/app.ts`, `infra/console.ts`, `infra/enterprise.ts`, and conditionally `infra/monitoring.ts`. `infra/app.ts` provisions a Cloudflare Worker API (`packages/function/src/api.ts`), a docs site from `packages/web`, and a static site deployment for `packages/app` built with `bun turbo build`. The `packages/function` worker uses Hono and Cloudflare Durable Objects, so deployment implies a worker/cloud runtime rather than a Node-only server.

For binary distribution, the top-level `install` script is important. It detects OS, architecture, musl vs glibc, and AVX2 support; selects the appropriate release archive; downloads from GitHub releases unless a local binary is supplied; and installs into `$HOME/.opencode/bin` by default. The script also supports explicit version pins and noninteractive path behavior. In practice, this means developers building release artifacts need the `packages/opencode` compiled binaries plus the release packaging expected by this installer.

## Practical build workflow

For routine local work, a typical flow is: `bun install` at the root, `bun run dev` for the CLI or `bun run dev:web` / `bun run dev:desktop` for a UI surface, `bun turbo typecheck` or package-local `typecheck` scripts for validation, and package-local `bun test` or Playwright commands for tests. For release or deployment work, inspect `packages/opencode/script/build.ts`, `packages/sdk/js/script/build.ts`, the relevant package build scripts, and `sst.config.ts` plus `infra/` to understand the exact output pipeline.
