# openai-node — Build System

## Build System Type and Configuration Files

The project uses **TypeScript** compiled via **tsc-multi** (a Stainless fork of the standard TypeScript compiler) to produce dual CommonJS and ESM outputs. Package management uses **Yarn 1.x** (Classic).

### Key Configuration Files

| File | Purpose |
|---|---|
| `package.json` | Package metadata, scripts, exports map, peer/dev dependencies |
| `tsconfig.json` | Development TypeScript config (type-checking only, `noEmit: true`) |
| `tsconfig.build.json` | Production build TypeScript config (emits to `dist/`) |
| `tsconfig.deno.json` | Deno-specific config (for `scripts/build-deno`) |
| `tsconfig.dist-src.json` | Config for distributing raw TS source in `dist/` |
| `tsc-multi.json` | Drives dual CJS + ESM compilation via `tsc-multi` tool |
| `jest.config.ts` | Jest test runner configuration |
| `eslint.config.mjs` | ESLint flat-config for linting |
| `jsr.json` | JSR (JavaScript Registry) package metadata for Deno/JSR publishing |

### `tsc-multi.json` — Dual CJS/ESM Build

```json
{
  "targets": [
    { "extname": ".js",  "module": "commonjs", "shareHelpers": "internal/tslib.js" },
    { "extname": ".mjs", "module": "esnext",   "shareHelpers": "internal/tslib.mjs" }
  ],
  "projects": ["tsconfig.build.json"]
}
```

This produces every source file as both `dist/<name>.js` (CommonJS `require()`) and `dist/<name>.mjs` (ESM `import`), with shared tslib helpers to minimize duplication.

### `package.json` `exports` Map

```json
{
  ".": {
    "import": "./dist/index.mjs",
    "require": "./dist/index.js"
  },
  "./*.mjs": { "default": "./dist/*.mjs" },
  "./*.js":  { "default": "./dist/*.js" },
  "./*":     { "import": "./dist/*.mjs", "require": "./dist/*.js" }
}
```

This enables `import OpenAI from 'openai'`, `const OpenAI = require('openai')`, and sub-path imports like `import { OpenAIRealtimeWebSocket } from 'openai/realtime/websocket'`.

## External Dependencies

### Production Dependencies
**Zero runtime dependencies.** The package.json `"dependencies": {}` is intentionally empty. The library relies only on:
- Global `fetch` (built into Node.js 18+, all modern browsers, Deno, Bun, Cloudflare Workers)
- Global `WebSocket` (browsers; for Node.js, the optional `ws` peer dep is used)
- Global `crypto.subtle` (for webhook HMAC verification)

### Peer Dependencies (optional)
- `ws ^8.18.0` — Node.js WebSocket library, required only for the Realtime API via `OpenAIRealtimeWS` (the `ws` transport, not the browser `WebSocket` one)
- `zod ^3.25 || ^4.0` — Required only if using `zodResponseFormat()`, `zodFunction()`, or `zodTextFormat()` helpers

### Dev Dependencies (partial list)
| Package | Purpose |
|---|---|
| `typescript 5.8.3` | TypeScript compiler |
| `tsc-multi` | Dual CJS/ESM build driver (from Stainless GitHub) |
| `@swc/jest` | Fast SWC-based Jest transform |
| `jest ^29` | Test framework |
| `eslint ^9` | Linting |
| `prettier ^3` | Code formatting |
| `ts-jest ^29` | TypeScript Jest integration |
| `zod ^3.25 || ^4.0` | Used in tests and helpers |
| `ws ^8.18.3` | WebSocket for tests |
| `@types/node ^20` | Node.js type definitions |
| `fast-check ^3` | Property-based testing |
| `publint ^0.2` | Package publishing validation |
| `@arethetypeswrong/cli` | TypeScript exports correctness checking |
| `deep-object-diff` | Test utilities |

## Build Targets and Commands

All commands are thin shell scripts in `scripts/`:

### `yarn build` → `./scripts/build`
Runs `tsc-multi` against `tsconfig.build.json`, producing `dist/` with both CJS and ESM outputs. Also typically runs `publint` and `@arethetypeswrong/cli` to validate the package before publishing.

### `yarn test` → `./scripts/test`
Runs Jest with the configuration in `jest.config.ts`. Uses `@swc/jest` for fast TypeScript transformation. Tests live in `tests/` and are excluded from `ecosystem-tests/`, `dist/`, `deno/`.

```bash
yarn test                    # Run all tests
yarn test tests/api.test.ts  # Run specific test file
```

### `yarn lint` → `./scripts/lint`
Runs ESLint using the flat config in `eslint.config.mjs`. Plugins: `@typescript-eslint`, `eslint-plugin-prettier`, `eslint-plugin-unused-imports`.

### `yarn format` / `yarn fix` → `./scripts/format`
Runs Prettier for code formatting.

### TypeScript Type-Check (Development)
```bash
yarn tsc --noEmit           # Type-check using tsconfig.json (dev config)
```

### `yarn tsn` → `ts-node -r tsconfig-paths/register`
Runs TypeScript files directly for quick testing of examples.

## How to Build

### Prerequisites
- Node.js 20+ (LTS)
- Yarn 1.22.x (`packageManager: "yarn@1.22.22"`)

### Install Dependencies
```bash
yarn install
```

### Build for Distribution
```bash
yarn build
# Produces dist/ with .js (CJS) and .mjs (ESM) files + .d.ts type declarations
```

The built output is in `dist/` and is what gets published to npm. The `main` field points to `dist/index.js` (CJS), `types` to `dist/index.d.ts`.

### Publishing
Publishing is done from the `dist/` directory (not the repo root), enforced by `prepublishOnly` which exits with an error:
```
echo 'to publish, run yarn build && (cd dist; yarn publish)' && exit 1
```
So the flow is:
```bash
yarn build
cd dist
yarn publish
```

## How to Test

```bash
yarn test                   # All tests
yarn test --watch           # Watch mode
```

Tests use `@swc/jest` for fast transformation. Module resolution aliases map `openai` → `./src/index.ts` and `openai/*` → `./src/*` so tests import directly from source.

### Ecosystem Tests
The `ecosystem-tests/` directory contains integration tests for various runtime environments (Vercel Edge, Cloudflare Workers, etc.). These are run separately and not part of the main Jest suite.

## Deno Support

A separate `scripts/build-deno` script produces a Deno-compatible output. JSR publishing metadata is in `jsr.json`. Deno users can install via:
```
deno add jsr:@openai/openai
```
or import directly:
```ts
import OpenAI from 'jsr:@openai/openai';
```

## TypeScript Configuration Details

**`tsconfig.json`** (development, type-check only):
- `target: "es2020"`, `lib: ["es2020"]`
- `module: "commonjs"`, `moduleResolution: "node"`
- All strict flags enabled: `strict`, `noImplicitAny`, `strictNullChecks`, `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`, `noImplicitOverride`
- `paths` aliases: `openai/*` → `./src/*`, `openai` → `./src/index.ts`

**`tsconfig.build.json`** (production):
- Similar to dev but configured to emit output to `dist/`
- Excludes test files and examples from the build output
