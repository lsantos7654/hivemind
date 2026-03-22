# Chalk — Build System

## Build System Type

Chalk uses **npm scripts** as its build system — there is no transpilation, bundling, or compilation step. The source is published directly as written (pure ESM JavaScript). `package.json` defines two scripts:

```json
"scripts": {
  "test": "xo && c8 ava && tsd",
  "bench": "matcha benchmark.js"
}
```

Because Chalk 5 is ESM-only and targets Node.js ≥ 12.17.0, no build step is needed. The `source/` directory is what gets published to npm.

## Configuration Files

| File | Purpose |
|------|---------|
| `package.json` | Package manifest, npm scripts, `xo`/`c8`/`tsd` config |
| `.editorconfig` | Editor formatting (indentation, line endings) |
| `.gitattributes` | `text=auto` for consistent line endings in git |
| `.npmrc` | `save-exact=true` — pins all dev dependency versions |
| `.github/workflows/main.yml` | GitHub Actions CI pipeline |

## External Dependencies

### Runtime Dependencies

**None.** All runtime code is self-contained. Two packages are vendored directly into `source/vendor/`:

| Vendor path | Origin package | Role |
|-------------|---------------|------|
| `source/vendor/ansi-styles/` | `ansi-styles` (chalk org) | ANSI escape codes and color-conversion math |
| `source/vendor/supports-color/` | `supports-color` (chalk org) | Terminal color-capability detection |

Vendoring avoids a dependency tree at install time, reduces cold-start overhead, and ensures exact versions are pinned in the repository.

### Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `ava` | ^3.15.0 | Test runner |
| `c8` | ^7.10.0 | V8-native code coverage (wraps ava invocation) |
| `tsd` | ^0.19.0 | TypeScript definition type-checking |
| `xo` | ^0.57.0 | Opinionated ESLint-based linter |
| `matcha` | ^0.7.0 | Benchmark runner (used only for `npm run bench`) |
| `@types/node` | ^16.11.10 | Node.js type definitions for TypeScript |
| `color-convert` | ^2.0.1 | HSL→hex conversion in `examples/rainbow.js` only |
| `execa` | ^6.0.0 | Spawning child processes in tests |
| `log-update` | ^5.0.0 | Animated terminal output in `examples/rainbow.js` only |
| `yoctodelay` | ^2.0.0 | Promise-based delay in `examples/rainbow.js` only |

## Build Targets and Commands

### `npm test`

Runs three tools in sequence:

```sh
xo && c8 ava && tsd
```

1. **`xo`** — Lint all JavaScript files using the project's XO configuration. Custom rules in `package.json` disable a few XO defaults:
   - `unicorn/prefer-string-slice` — off (chalk uses `substring`)
   - `@typescript-eslint/consistent-type-imports` — off
   - `@typescript-eslint/consistent-type-exports` — off
   - `@typescript-eslint/consistent-type-definitions` — off
   - `unicorn/expiring-todo-comments` — off

2. **`c8 ava`** — Run the AVA test suite under c8 coverage instrumentation. Coverage reports are generated in `text` and `lcov` formats. The `source/vendor/` directory is excluded from coverage measurement:
   ```json
   "c8": {
     "reporter": ["text", "lcov"],
     "exclude": ["source/vendor"]
   }
   ```
   AVA discovers test files automatically. The test suite is in `test/*.js`.

3. **`tsd`** — Type-check the TypeScript declaration file (`source/index.d.ts`) against the type-level tests in `source/index.test-d.ts`. This ensures exported types are correct without requiring a full TypeScript compilation.

### `npm run bench`

```sh
matcha benchmark.js
```

Runs micro-benchmarks defined in `benchmark.js` using the `matcha` framework. Measures style application for 1, 2, and 3 chained styles in both uncached and cached (pre-bound) forms, as well as newline handling and nested style scenarios.

## How to Build

There is no build step. To prepare for local development:

```sh
# Install dev dependencies
npm install

# Run linting + tests + type-checks
npm test

# Run benchmarks
npm run bench
```

The package published to npm contains:
- `source/` directory (all `.js` and `.d.ts` files, excluding `source/index.test-d.ts`)
- `readme.md`, `license`, `package.json`

This is controlled by the `"files"` field in `package.json`:
```json
"files": [
  "source",
  "!source/index.test-d.ts"
]
```

## How to Test

AVA test files are in `test/`. Each file is an independent test module:

```sh
# Run full test suite with coverage
npm test

# Run only AVA tests (no lint, no tsd)
npx ava

# Run a specific test file
npx ava test/chalk.js

# Run with verbose output
npx ava --verbose
```

Test files use Node.js `import` and AVA's `test()` function. The main test file (`test/chalk.js`) sets `chalk.level = 3` explicitly to ensure ANSI codes are always emitted regardless of the host terminal's actual capabilities.

The `test/_fixture.js` file supports tests that need to spawn a child process (used to test color detection in controlled environments via `execa`).

## CI Pipeline

GitHub Actions (`.github/workflows/main.yml`) runs on every push and pull request:

- **Matrix:** Node.js 14, 16, 18 on `ubuntu-latest`
- **Steps:**
  1. `actions/checkout@v4`
  2. `actions/setup-node@v4` with the matrix Node version
  3. `npm install`
  4. `npm test`
  5. Upload coverage to Codecov (only on Node 16, using `codecov/codecov-action@v2`)

## Node.js Version Requirements

```json
"engines": {
  "node": "^12.17.0 || ^14.13 || >=16.0.0"
}
```

The lower bound of 12.17.0 is the first Node.js 12 release with full ESM support (`--experimental-vm-modules` stability). Node.js 14.13 was the first 14.x with stable ESM. Node.js 16+ has full ESM support.

**Important:** Chalk 5 is ESM-only. Projects using TypeScript or CommonJS bundlers that cannot consume ESM should use Chalk 4 instead.
