# RealWorld — Build System

## Build System Overview

This repository is not a compiled application — it is a **specification and test hub**. The build system covers two concerns:

1. **Documentation site** — an Astro + Starlight static site built with Bun
2. **Bruno collection generation** — a Bun script that converts Hurl test files into Bruno format

There is no application build step (no frontend or backend to compile). All commands are in the top-level `Makefile`.

## Build Configuration Files

| File | Purpose |
|------|---------|
| `Makefile` | Top-level task runner for all dev commands |
| `docs/astro.config.mjs` | Astro configuration: integrations, Starlight setup, sidebar nav, Vite plugins |
| `docs/package.json` | npm/Bun package manifest for the docs site |
| `docs/bun.lock` | Bun lockfile — pins all docs dependencies |
| `docs/tsconfig.json` | TypeScript configuration for the docs site |

## Makefile Targets

All Make targets are declared `.PHONY` (no file outputs).

### Bruno Collection Targets

```makefile
bruno-generate:
    bun specs/api/hurl-to-bruno.js

bruno-check:
    bun specs/api/hurl-to-bruno.js --check
```

- `bruno-generate` — runs `hurl-to-bruno.js` to regenerate the entire `specs/api/bruno/` directory from the Hurl source files. Run this any time Hurl tests are modified.
- `bruno-check` — runs the same generator script in check mode (`--check` flag). Used in CI (`bruno-check.yml` workflow) to verify the Bruno collection is in sync with the Hurl source. Fails if the Bruno output would differ from what is committed.

### Documentation Site Targets

```makefile
documentation-setup:
    cd docs && bun install

documentation-dev:
    cd docs && bun run dev

documentation-dev-host:
    cd docs && bun run dev --host

documentation-build:
    cd docs && bun run build

documentation-preview:
    cd docs && bun run preview

documentation-clean:
    rm -rf docs/.astro docs/dist docs/node_modules
```

- `documentation-setup` — installs all docs dependencies (Astro, Starlight, Tailwind, etc.) using Bun
- `documentation-dev` — starts local development server for the docs site (default port, localhost only)
- `documentation-dev-host` — same but binds to all network interfaces (useful for network testing or remote access)
- `documentation-build` — produces a production static site in `docs/dist/`
- `documentation-preview` — serves the built static site locally for preview before deploy
- `documentation-clean` — removes all generated artifacts and `node_modules`

## External Dependencies

### Docs Site (`docs/package.json`)

The docs site depends on:

- **Astro** — static site generator framework
- **@astrojs/starlight** — documentation theme built on Astro
- **@tailwindcss/vite** — Tailwind CSS integration via Vite plugin
- **Bun** — JavaScript runtime and package manager used for all docs commands

Key Vite plugins in `docs/astro.config.mjs`:
- `@tailwindcss/vite` — processes Tailwind CSS
- `removeMdExtension()` (custom, inline) — strips `.md` extensions from URLs during build for clean links

### Runtime Tools (not managed by this repo)

The following tools must be installed in the environment to use the test infrastructure. They are not declared as package dependencies — they are expected as system tools.

| Tool | Version | Purpose |
|------|---------|---------|
| **Hurl** | any | Run `specs/api/hurl/*.hurl` API tests against a backend |
| **Bruno CLI** (`bru`) | any | Run `specs/api/bruno/` collection against a backend |
| **Bun** | any | Execute `hurl-to-bruno.js` and build the docs site |
| **Playwright** | installed by implementation | Run `specs/e2e/*.spec.ts` tests |

Playwright is not installed by this repository — each frontend implementation installs its own Playwright version via npm/bun and extends `specs/e2e/playwright.base.ts`.

## How to Build and Test

### Build the Documentation Site

```bash
# Install dependencies first
make documentation-setup

# Start local dev server
make documentation-dev

# Build static site
make documentation-build
# Output in docs/dist/

# Preview the built site
make documentation-preview
```

### Run the API Test Suite Against a Backend

Using Hurl (the authoritative test runner):

```bash
# Run all Hurl tests against a local backend
HOST=http://localhost:3000/api ./specs/api/run-api-tests-hurl.sh

# Run against a specific host
HOST=http://localhost:8000 ./specs/api/run-api-tests-hurl.sh

# Run a single Hurl file
HOST=http://localhost:3000/api ./specs/api/run-api-tests-hurl.sh specs/api/hurl/auth.hurl
```

The `run-api-tests-hurl.sh` script sets `--jobs 1` (sequential execution, tests depend on state) and injects a `uid` variable for test isolation (default: `$(date +%s)$$`).

Using Bruno:

```bash
# Run all Bruno tests against a local backend
HOST=http://localhost:3000/api ./specs/api/run-api-tests-bruno.sh
```

### Regenerate the Bruno Collection

```bash
# After editing any hurl/*.hurl file
make bruno-generate

# Check if Bruno is in sync (CI check)
make bruno-check
```

### Run the Frontend E2E Tests (in an Implementation)

Frontend implementations must:

1. Copy or reference `specs/e2e/` into their project (or mount as a submodule)
2. Create a `playwright.config.ts` that extends `playwright.base.ts`:

```typescript
import { defineConfig } from '@playwright/test';
import { baseConfig } from './e2e/playwright.base';

export default defineConfig({
  ...baseConfig,
  use: { ...baseConfig.use, baseURL: 'http://localhost:3000' },
  webServer: {
    command: 'npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
```

3. Run Playwright:

```bash
# Against the demo backend (API_MODE=true by default)
npx playwright test

# Against a local fullstack implementation
API_MODE=false npx playwright test

# Against a custom backend URL
API_BASE=http://localhost:4000/api npx playwright test
```

## CI/CD Workflows

### `deploy-docs.yml`

Runs on push to main branch. Builds the Astro docs site and deploys to GitHub Pages (or similar static hosting).

### `bruno-check.yml`

Runs on every pull request. Executes `make bruno-check` to verify the Bruno collection in `specs/api/bruno/` matches what would be generated from the Hurl source files. Prevents the collection from getting out of sync.

### `codeql.yml`

Runs CodeQL static analysis for security vulnerability detection.

### `spammy-guardian.yml`

Bot-based workflow to manage spam issues and pull requests.

## Key Configuration Details

**`docs/astro.config.mjs`** — The custom `removeMdExtension()` Vite plugin strips `.md` from internal links during the build process, producing clean URLs like `/specifications/backend/endpoints` instead of `/specifications/backend/endpoints.md`.

**`specs/api/run-api-tests-hurl.sh`** — Two important environment variables:
- `HOST` — the backend base URL (default: `http://localhost:8000`)
- `UID_VAL` — unique identifier for test isolation (default: `$(date +%s)$$`), prevents test data conflicts when running multiple test runs against a shared backend

**`specs/e2e/helpers/config.ts`** — Two environment variables:
- `API_MODE` — when `false`, disables tests that use direct API calls or `page.route()` interception (for fullstack implementations that cannot use these techniques); defaults to `true`
- `API_BASE` — the backend API URL for direct API calls in tests; defaults to `https://api.realworld.show/api`
