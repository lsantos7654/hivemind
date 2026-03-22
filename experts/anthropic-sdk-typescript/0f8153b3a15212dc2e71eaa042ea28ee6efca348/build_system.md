# Build System: @anthropic-ai/sdk

## Build System Type and Configuration Files

The SDK uses a custom shell-script-driven build pipeline orchestrated around **TypeScript** and **tsc-multi**, a tool that compiles the same TypeScript source into multiple module formats simultaneously.

**Key configuration files:**

| File | Purpose |
|------|---------|
| `tsconfig.json` | Development/IDE config — strict TypeScript, no emit, includes `src/`, `tests/`, `examples/` |
| `tsconfig.build.json` | Build config — emits to `dist/`, references source under `dist/src/` |
| `tsconfig.dist-src.json` | Tsconfig embedded in `dist/src/` for source maps to resolve correctly |
| `tsconfig.deno.json` | Deno-specific tsconfig for the optional Deno build target |
| `tsc-multi.json` | tsc-multi config — declares two build targets: `.js` (CJS) and `.mjs` (ESM) |
| `jest.config.ts` | Jest config for test runner |
| `eslint.config.mjs` | ESLint flat config (TypeScript-ESLint + prettier plugin) |
| `.prettierrc.json` | Prettier formatting rules |

**tsc-multi configuration** (`tsc-multi.json`):
```json
{
  "targets": [
    { "extname": ".js",  "module": "commonjs", "shareHelpers": "internal/tslib.js"  },
    { "extname": ".mjs", "module": "esnext",   "shareHelpers": "internal/tslib.mjs" }
  ],
  "projects": ["tsconfig.build.json"]
}
```

This produces both CJS (`.js`) and ESM (`.mjs`) outputs from a single TypeScript compilation pass, with `tslib` helpers shared to reduce bundle size.

**TypeScript strictness** (`tsconfig.json`):
- `strict: true`, `noImplicitAny`, `strictNullChecks`, `strictFunctionTypes`, `exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`, `noImplicitOverride`, `noPropertyAccessFromIndexSignature`
- Target: `es2020`, lib: `es2020`, module: `commonjs` (dev), module: `esnext` (ESM build)
- Path aliases: `@anthropic-ai/sdk/*` → `./src/*` for tests/examples to import from source

## External Dependencies and Management

**Package manager**: `yarn` 1.22.22 (classic)

**Runtime dependencies** (installed in production):
```json
"dependencies": {
  "json-schema-to-ts": "^3.1.1"
}
```

**Optional peer dependencies**:
```json
"peerDependencies": {
  "zod": "^3.25.0 || ^4.0.0"
}
```
Zod is optional — structured output helpers (`helpers/zod.ts`, `helpers/beta/zod.ts`) require it, but the base SDK works without it.

**Development dependencies** (build/test only):
- `typescript` 5.8.3
- `tsc-multi` (custom fork from stainless-api GitHub release)
- `@swc/core` + `@swc/jest` — fast TypeScript transform for Jest
- `jest` ^29 + `ts-jest` ^29 — test runner
- `@types/jest`, `@types/node` ^20
- `@typescript-eslint/eslint-plugin` + `parser` 8.31.1
- `eslint` ^9 + `eslint-plugin-prettier`, `eslint-plugin-unused-imports`
- `prettier` ^3
- `nock` ^14 — HTTP mocking for tests
- `@modelcontextprotocol/sdk` ^1.24.2 — MCP types for dev/examples (not a runtime dep)
- `@arethetypeswrong/cli` — validates package exports correctness
- `publint` — validates npm package publishing
- `iconv-lite` — charset encoding utilities for tests
- `deep-object-diff` — used in tests

**Sub-package dependencies** are managed separately in each sub-package's own `package.json` and `yarn.lock`.

## Build Targets and Commands

### Main build commands (via `package.json` scripts):

| Command | Script | Description |
|---------|--------|-------------|
| `yarn build` | `./scripts/build-all` | Builds main SDK + all sub-packages |
| `yarn test` | `./scripts/test` | Runs Jest tests |
| `yarn lint` | `./scripts/lint` | Runs ESLint |
| `yarn format` | `./scripts/format` | Runs Prettier (format in place) |
| `yarn fix` | `./scripts/format` | Alias for format |

### How to Build

**Build the main SDK:**
```bash
yarn install
yarn build
# Output: dist/ directory with CJS (.js) and ESM (.mjs) files
```

**Build process** (`scripts/build`):
1. Validates version consistency (`scripts/utils/check-version.cjs`)
2. Clears and recreates `dist/` directory
3. Copies `src/`, `README.md`, `LICENSE`, `CHANGELOG.md`, `bin/cli`, `bin/migration-config.json` into `dist/`
4. Generates `dist/package.json` from source via `scripts/utils/make-dist-package-json.cjs` (rewrites export paths)
5. Runs `tsc-multi` to emit `.js` (CJS) and `.mjs` (ESM) files from `tsconfig.build.json`
6. Patches `index.js` for CJS backwards compat (`scripts/utils/fix-index-exports.cjs`)
7. Copies `tsconfig.dist-src.json` → `dist/src/tsconfig.json` for source map resolution
8. Runs `scripts/utils/postprocess-files.cjs` to patch import/require paths in output
9. Smoke-tests the output: `node -e 'require("@anthropic-ai/sdk")'` and `node -e 'import("@anthropic-ai/sdk")' --input-type=module`
10. Optionally runs `scripts/build-deno` if present

**Build all sub-packages** (`scripts/build-all`): runs `scripts/build` for the main SDK then iterates each directory in `packages/` and runs their local build scripts.

### How to Test

```bash
yarn test
# or directly:
./scripts/test
```

Jest configuration (`jest.config.ts`):
- Preset: `ts-jest/presets/default-esm`
- Transform: `@swc/jest` for fast compilation
- `moduleNameMapper`: maps `@anthropic-ai/sdk` and `@anthropic-ai/sdk/*` to `src/` for in-source testing
- Excludes: `ecosystem-tests/`, `dist/`, `deno/`, `deno_tests/`, `packages/`
- Test files: `tests/*.test.ts`

Sub-packages have their own `jest.config.ts` files.

### How to Lint and Format

```bash
yarn lint    # ESLint check
yarn format  # Prettier format (writes files)
```

ESLint uses the flat config format (`eslint.config.mjs`) with:
- `@typescript-eslint` for TypeScript rules
- `eslint-plugin-prettier` for format checking
- `eslint-plugin-unused-imports` for dead import detection

### Publishing

Publishing is done **from the `dist/` directory**, not the project root:
```bash
yarn build
cd dist
yarn publish
```

The `package.json` `prepublishOnly` script intentionally errors if you try to publish from the root to prevent accidental source publishes. The `bin/publish-npm` and `scripts/publish-packages.ts` scripts automate the process.

Release versioning uses **release-please** (`release-please-config.json`, `.release-please-manifest.json`) for automated changelog and version bump PRs.

### Mock Server for Development

```bash
./scripts/mock
```

Starts a Prism mock server based on the OpenAPI spec, enabling development and testing without hitting the real API.

### Breaking Change Detection

```bash
./scripts/detect-breaking-changes
```

Compares the current API surface against a baseline to detect breaking changes in the TypeScript public API.
