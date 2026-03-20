# Pi Monorepo — Build System

## Build System Type

The monorepo uses **npm workspaces** with **TypeScript** compiled by `tsgo` (the TypeScript native preview compiler, `@typescript/native-preview`). Linting and formatting is handled by **Biome**. Tests run with **Vitest**. Husky provides a pre-commit hook.

## Configuration Files

| File | Purpose |
|------|---------|
| `package.json` (root) | Workspace definition, root dev scripts |
| `tsconfig.base.json` | Shared TS base: `moduleResolution: bundler`, `target: ESNext`, `strict: true` |
| `tsconfig.json` (root) | Root tsconfig that includes all packages for project-wide type checking |
| `packages/*/tsconfig.build.json` | Per-package build tsconfig (extends base, sets `outDir: dist`, `rootDir: src`) |
| `biome.json` | Lint/format rules (replaces ESLint + Prettier) |
| `.husky/pre-commit` | Runs `npm run check` before each commit |
| `.github/workflows/ci.yml` | CI: install → build → check → test |
| `.github/workflows/build-binaries.yml` | Binary build workflow (Bun compile) |

## External Dependencies and Management

Dependencies are managed with `npm`. Each package has its own `package.json` with `dependencies` and `devDependencies`. The root `package.json` lists shared devDependencies and workspace-level overrides.

**Key dependency overrides** (root `package.json`):
```json
"overrides": {
  "rimraf": "6.1.2",
  "fast-xml-parser": "5.3.8",
  "gaxios": { "rimraf": "6.1.2" }
}
```

**Runtime dependencies by package:**

`@mariozechner/pi-ai`:
- `@sinclair/typebox` — JSON Schema + type generation
- `ajv` — schema validation
- `@aws-sdk/client-bedrock-runtime` (Bedrock provider, lazy-loaded)

`@mariozechner/pi-agent-core`:
- `@mariozechner/pi-ai` (peer dependency)
- `@sinclair/typebox`

`@mariozechner/pi-coding-agent`:
- `@mariozechner/pi-ai`, `@mariozechner/pi-agent-core`, `@mariozechner/pi-tui`
- `@mariozechner/jiti` — runtime TypeScript execution for extensions
- `chalk` — terminal colors
- `marked` — markdown parsing
- `diff` — diff generation for edit tool
- `yaml` — YAML parsing (session/config)
- `glob` — file globbing
- `ignore` — .gitignore-style pattern matching
- `minimatch` — glob pattern matching
- `file-type` — MIME type detection
- `extract-zip` — package install (git zip)
- `hosted-git-info` — parse git URLs for package manager
- `proper-lockfile` — file locking for concurrent session writes
- `strip-ansi` — strip ANSI for clipboard copy
- `undici` — HTTP client (version check, share/gist upload)
- `@silvia-odwyer/photon-node` — image processing (clipboard images)
- `@mariozechner/clipboard` — native clipboard (optional)

`@mariozechner/pi-tui`:
- `chalk` — terminal colors
- `@xterm/headless` — VirtualTerminal for testing

**Dev dependencies (root):**
- `@biomejs/biome` `2.3.5` — linter/formatter
- `@typescript/native-preview` `7.0.0-dev.20260120.1` — fast TS compiler (`tsgo`)
- `typescript` `^5.9.2` — standard TS (for web-ui which uses `tsc`)
- `concurrently` `^9.2.1` — parallel watch mode
- `husky` `^9.1.7` — git hooks
- `tsx` `^4.20.3` — run TS scripts directly
- `shx` `^0.4.0` — cross-platform shell commands in npm scripts

## Build Targets and Commands

### Root-Level Commands

```bash
npm install           # Install all workspace dependencies
npm run build         # Build all packages in dependency order (see below)
npm run dev           # Start all packages in watch mode (concurrently)
npm run check         # Biome check + tsgo type check + browser smoke check
npm run test          # Run tests across all workspaces
```

**Build order** (sequential, defined explicitly in root `package.json`):
```
tui → ai → agent → coding-agent → mom → web-ui → pods
```

### Per-Package Commands

Each package exposes these scripts:
```bash
npm run build         # tsgo -p tsconfig.build.json (or tsc for web-ui)
npm run dev           # tsgo --watch
npm run clean         # shx rm -rf dist
npm run test          # vitest --run
npm run check         # (web-ui only) tsc --noEmit
```

`coding-agent` also has:
```bash
npm run build:binary  # Build standalone Bun-compiled binary
npm run copy-assets   # Copy theme JSON, HTML export templates, WASM to dist/
```

### Release Commands

```bash
npm run version:patch   # Bump all packages patch, sync cross-refs, reinstall
npm run version:minor   # Same for minor
npm run version:major   # Same for major
npm run release:patch   # node scripts/release.mjs patch (full release: version + publish)
npm run release:minor
npm run release:major
npm run publish:dry     # Dry-run npm publish for all packages
```

### Development Workflow

```bash
# Watch all packages in parallel
npm run dev

# Run pi from sources (from repo root)
./pi-test.sh

# Run tests (skips LLM tests without API keys)
./test.sh

# Lint + format + type check (requires build first)
npm run build && npm run check
```

## How to Build

**Full build from scratch:**
```bash
npm install
npm run build
```

**Individual package build (e.g., coding-agent):**
```bash
cd packages/coding-agent
npm run build
```

Note: `coding-agent` depends on compiled `.d.ts` from `tui`, `ai`, and `agent`. Build those first or use the root build script.

## How to Test

Tests use **Vitest**. Each package has a `vitest.config.ts`.

```bash
# All tests from repo root (skips LLM-dependent tests without keys)
./test.sh

# Tests for a specific package
cd packages/ai && npx vitest --run

# With API keys for live LLM tests
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export GEMINI_API_KEY=...
cd packages/ai && npx vitest --run
```

`packages/ai/test/` contains ~35 test files covering:
- All provider streaming and tool use
- Token counting, cost tracking
- Abort and error handling
- Cross-provider context handoff
- Context overflow handling
- Unicode surrogate pair edge cases
- OAuth token flows
- Partial tool argument streaming
- Thinking/reasoning blocks

`packages/agent/test/` covers:
- Agent loop event sequences
- Tool execution (parallel/sequential)
- E2E tests with real LLMs

## How to Deploy / Publish

**Publish all packages to npm:**
```bash
npm run publish          # runs prepublishOnly (clean + build + check) then npm publish -ws
npm run publish:dry      # dry run
```

**Build standalone binary** (Bun compile):
```bash
cd packages/coding-agent
npm run build:binary     # outputs dist/pi binary
```

The binary build pipeline:
1. Build all packages
2. `bun build --compile ./dist/bun/cli.js --outfile dist/pi`
3. Copy assets (themes, HTML templates, WASM) alongside binary

## CI Pipeline

`.github/workflows/ci.yml`:
1. `npm install` — install all dependencies
2. `npm run build` — compile all packages
3. `npm run check` — Biome + tsgo type check + browser smoke
4. `npm run test` — Vitest across all workspaces

`.github/workflows/build-binaries.yml`:
- Builds standalone binaries using Bun compile for Linux/macOS/Windows

## Environment Variables for Build

| Variable | Purpose |
|----------|---------|
| `PI_SKIP_VERSION_CHECK` | Skip startup version check in tests |
| `ANTHROPIC_API_KEY` | Required for Anthropic provider tests |
| `OPENAI_API_KEY` | Required for OpenAI provider tests |
| `GEMINI_API_KEY` | Required for Google provider tests |
| `XAI_API_KEY` | Required for xAI provider tests |
| `GROQ_API_KEY` | Required for Groq provider tests |
| `MISTRAL_API_KEY` | Required for Mistral provider tests |
| `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_BASE_URL` | Azure OpenAI tests |
| `GOOGLE_CLOUD_PROJECT` + `GOOGLE_CLOUD_LOCATION` | Vertex AI tests |
| `HF_TOKEN` | HuggingFace token (pi-pods model downloads) |
