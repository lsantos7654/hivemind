# jsdiff — Build System

## Build System Type and Configuration Files

jsdiff uses a multi-step build pipeline driven by npm scripts in `package.json`, with Yarn 4 (Berry) as the package manager. There is no Makefile, Grunt, or Gulp; all automation is through `yarn <script>`.

**Key configuration files:**

| File | Purpose |
|------|---------|
| `package.json` | Script definitions, exports map, devDependencies, nyc coverage config |
| `tsconfig.json` | TypeScript compiler settings (strict, ES module target) |
| `rollup.config.mjs` | Bundles ESM output → UMD `dist/diff.js` for browsers |
| `.babelrc` | Babel config: `@babel/preset-env` + `babel-plugin-istanbul` for test coverage |
| `runtime.js` | `@babel/register` hook loaded before Mocha so tests run via Babel |
| `eslint.config.mjs` | ESLint flat config using `@eslint/js` + `typescript-eslint` |
| `karma.conf.js` | Karma browser test runner (uses webpack + mocha + sourcemap-loader) |
| `.yarnrc.yml` | Yarn 4 configuration |

## External Dependencies

**Runtime dependencies:** None. The published package has zero runtime dependencies.

**Development dependencies** (from `package.json`):

| Package | Purpose |
|---------|---------|
| `typescript` (^5.9.3) | TypeScript compiler (`tsc`) |
| `rollup` (^4.59.0) | UMD bundle creation |
| `uglify-js` (^3.19.3) | Minification of `dist/diff.js` → `dist/diff.min.js` |
| `@babel/core`, `@babel/preset-env`, `@babel/register` | Transpile compiled JS for Mocha tests; enable coverage instrumentation |
| `babel-plugin-istanbul` | Inject Istanbul coverage counters via Babel |
| `mocha` (^11.7.5) | Test runner |
| `chai` (^6.2.2) | Assertion library used in tests |
| `nyc` (^18.0.0) | Coverage reporting (requires 100% coverage on all metrics) |
| `cross-env` (^10.1.0) | Set `NODE_ENV=test` cross-platform |
| `eslint` (^10.0.2) | Linting |
| `typescript-eslint` (^8.56.1) | TypeScript-aware ESLint rules |
| `@eslint/js` (^10.0.1) | ESLint recommended rules |
| `globals` (^17.4.0) | Global variable definitions for ESLint |
| `tsd` (^0.33.0) | Type-level testing (`test-d/*.test-d.ts`) |
| `@arethetypeswrong/cli` (`attw`) (^0.18.2) | Validates package exports map is correctly typed |
| `karma` + plugins | Browser-based test runner (optional, not part of primary `test` script) |
| `webpack` + `webpack-dev-server` | Used by Karma for browser tests |
| `@colors/colors` (^1.6.0) | Used in `examples/node_example.js` |

## Build Targets and Commands

### Full build

```bash
yarn build
```

Runs the following steps in sequence:
1. `yarn lint` — ESLint
2. `yarn generate-esm` — TypeScript → ESM (`libesm/`)
3. `yarn generate-cjs` — TypeScript → CJS (`libcjs/`)
4. `yarn check-types` — tsd type tests + attw exports validation
5. `yarn run-rollup` — ESM → UMD bundle (`dist/diff.js`)
6. `yarn run-uglify` — Minify to `dist/diff.min.js`

### Individual steps

```bash
# Compile TypeScript to ESM (libesm/)
yarn generate-esm
# Equivalent to:
yarn tsc --module nodenext --outDir libesm --target es6
# Also writes libesm/package.json with { "type": "module", "sideEffects": false }

# Compile TypeScript to CJS (libcjs/)
yarn generate-cjs
# Equivalent to:
yarn tsc --module commonjs --outDir libcjs
# Also writes libcjs/package.json with { "type": "commonjs", "sideEffects": false }

# Type checking (no emit)
yarn check-types         # runs tsd + attw

# tsd type tests
yarn run-tsd
# Equivalent to:
yarn tsd --typings libesm/ && yarn tsd --files test-d/

# Exports map validation
yarn run-attw
# Equivalent to:
yarn attw --pack --entrypoints . && yarn attw --pack --entrypoints lib/diff/word.js --profile node16

# Rollup UMD bundle
yarn run-rollup          # Input: libesm/index.js → Output: dist/diff.js (name: "Diff")

# Minify
yarn run-uglify          # Input: dist/diff.js → Output: dist/diff.min.js

# Lint
yarn lint                # eslint across all TypeScript source
```

### Testing

```bash
# Run full test suite (build + unit tests + coverage)
yarn test
# Equivalent to: yarn build && cross-env NODE_ENV=test yarn run-mocha

# Run Mocha directly (requires prior build)
yarn run-mocha
# Equivalent to:
mocha --require ./runtime 'test/**/*.js'

# Clean all build artifacts
yarn clean
# Equivalent to:
rm -rf libcjs/ libesm/ dist/ coverage/ .nyc_output/
```

The `runtime.js` file registers `@babel/register` so Mocha can run the compiled JavaScript through Babel (for Istanbul instrumentation). Tests are written in CommonJS JavaScript and import from the compiled `libcjs/` output.

### Coverage

nyc (Istanbul v2) is configured in `package.json` with **100% required** for all four metrics:

```json
"nyc": {
  "check-coverage": true,
  "branches": 100,
  "lines": 100,
  "functions": 100,
  "statements": 100
}
```

Coverage reports are generated in `lcov` and `text` formats. Source maps are disabled (`"sourceMap": false`) and instrumentation is done via Babel plugin rather than nyc's built-in instrumentation (`"instrument": false`).

### Browser testing

```bash
# Karma browser tests (not part of the main test script)
karma start karma.conf.js
```

The `karma.conf.js` uses webpack to bundle the tests and the library source, with `karma-mocha` and `karma-mocha-reporter`. This is separate from the Node.js test suite and is used for browser compatibility verification.

## How to Build, Test, and Deploy

### Development workflow

```bash
# 1. Install dependencies
yarn install

# 2. Full build + test cycle
yarn test

# 3. Just compile TypeScript (faster iteration)
yarn generate-esm && yarn generate-cjs

# 4. Lint only
yarn lint
```

### Publishing

The published package (npm name: `diff`) includes:
- `libcjs/` — CJS build with type declarations
- `libesm/` — ESM build with type declarations
- `dist/diff.js` and `dist/diff.min.js` — UMD browser bundles
- `runtime.js` — re-exported for tests (`.npmignore` excludes test files)

The `package.json` `exports` map provides condition-based resolution:
- `"import"` → `libesm/index.js` (types: `libesm/index.d.ts`)
- `"require"` → `libcjs/index.js` (types: `libcjs/index.d.ts`)
- `"browser"` / `"unpkg"` → `dist/diff.js`

The `attw` tool validates that this exports map is correct for Node16 and Bundler resolution modes before publishing.
