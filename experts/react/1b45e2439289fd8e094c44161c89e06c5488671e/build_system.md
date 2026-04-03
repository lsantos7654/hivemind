# React Build System

## Build System Type

React uses a **Rollup-based custom build pipeline** organized under `scripts/rollup/`. It is not a standard CLI tool invocation—the build is driven by a custom Node.js orchestrator (`scripts/rollup/build.js`) that generates multiple bundle types per package based on definitions in `scripts/rollup/bundles.js`.

The repository uses **Yarn 1.22.22** as its package manager with workspaces. There is no Lerna; package versioning and releases are handled by custom scripts.

## Build Configuration Files

| File | Purpose |
|------|---------|
| `package.json` | Root: workspace config, npm scripts |
| `ReactVersions.js` | Single source of truth for all package versions |
| `scripts/rollup/build.js` | Main build orchestrator (27KB) |
| `scripts/rollup/build-all-release-channels.js` | Multi-channel build driver (16KB) |
| `scripts/rollup/bundles.js` | Bundle definitions (39KB) — specifies all output artifacts |
| `scripts/rollup/modules.js` | Module ID to path mappings |
| `scripts/rollup/packaging.js` | Post-build packaging and npm directory preparation |
| `scripts/rollup/forks.js` | Fork resolution for platform variants (16KB) |
| `scripts/rollup/plugins/` | Custom Rollup plugins |
| `babel.config.js` | Root Babel configuration |
| `babel.config-ts.js` | TypeScript Babel configuration |
| `babel.config-react-compiler.js` | React Compiler Babel config |
| `.eslintrc.js` | ESLint configuration (21KB) |

## External Dependencies and Management

All dependencies are managed via Yarn workspaces. Key build-time dependencies:

**Build toolchain:**
- `rollup` (3.x) — Module bundler
- `@babel/core` + plugins — JS/JSX/Flow transpilation
- `babel-plugin-transform-react-calls-components` — Internal optimization
- `google-closure-compiler` — Minification for production bundles
- `chalk`, `jest-snapshot` — Build utilities

**Type checking:**
- `flow-bin` — Flow type checker
- `@flow/strict` types throughout codebase

**Testing:**
- `jest` (29.x) — Test runner
- `@testing-library/react` — DOM testing utilities
- `puppeteer` — E2E browser testing (DevTools)
- `jest-environment-jsdom` — DOM environment for tests

**Code quality:**
- `eslint` + numerous plugins
- `prettier` — Code formatting
- `danger` — PR validation

## Build Targets and Bundle Types

React produces 12 distinct bundle types for different environments, defined in `scripts/rollup/bundles.js`:

| Bundle Type | Description |
|-------------|-------------|
| `NODE_ES2015` | Node.js, ES2015 syntax (no transpilation) |
| `ESM_DEV` | ES Modules, development (unminified) |
| `ESM_PROD` | ES Modules, production (minified) |
| `NODE_DEV` | CommonJS for Node.js, development |
| `NODE_PROD` | CommonJS for Node.js, production (Closure minified) |
| `NODE_PROFILING` | CommonJS with profiling hooks enabled |
| `BUN_DEV` | Bun runtime, development |
| `BUN_PROD` | Bun runtime, production |
| `FB_WWW_DEV/PROD/PROFILING` | Internal Meta www builds |
| `RN_OSS_DEV/PROD` | React Native OSS builds |
| `RN_FB_DEV/PROD` | React Native Facebook builds |
| `BROWSER_SCRIPT` | Direct `<script>` tag usage (UMD-like) |
| `CJS_DTS` | CommonJS TypeScript declaration files |
| `ESM_DTS` | ES Module TypeScript declaration files |

## Release Channels

React ships from multiple **release channels**, each with different feature flag configurations:

| Channel | Description |
|---------|-------------|
| `stable` | Published releases (v19.3.0) |
| `experimental` | Latest features, all flags enabled |
| `www-modern` | Meta internal: modern variant |
| `www-classic` | Meta internal: legacy variant |
| `xplat` | Meta internal: cross-platform |

The default build channel is `experimental`. The `build-all-release-channels.js` script builds all channels sequentially.

## Build Commands

From the root `package.json`:

```bash
# Build all packages (experimental channel by default)
yarn build

# Build for DevTools specifically
yarn build-for-devtools

# Build for Flight/Server Components (dev)
yarn build-for-flight-dev

# Build for Flight/Server Components (prod)
yarn build-for-flight-prod

# Build all channels (stable, experimental, www, etc.)
node scripts/rollup/build-all-release-channels.js
```

Direct Rollup build with options:

```bash
# Build a specific package
node scripts/rollup/build.js react

# Build with specific type
node scripts/rollup/build.js react --type=NODE_DEV

# Build with release channel
node scripts/rollup/build.js react --release-channel=stable
```

## Custom Rollup Plugins

Located in `scripts/rollup/plugins/`:

| Plugin | Purpose |
|--------|---------|
| `closure-plugin.js` | Integrates Google Closure Compiler for minification |
| `sizes-plugin.js` | Tracks bundle size and flags regressions |
| `use-forks-plugin.js` | Substitutes platform-specific fork files at build time |
| `dynamic-imports-plugin.js` | Handles dynamic import() statements |
| `external-runtime-plugin.js` | Extracts external runtime (Fizz streaming runtime) |
| `babel-plugin-transform-react-error-messages.js` | Replaces error messages with numeric codes in prod |

## Testing Infrastructure

### Jest Configuration

Tests are run via a custom CLI wrapper at `scripts/jest/jest-cli.js` that adds release channel awareness:

```bash
# Run tests for source (OSS)
yarn test

# Run tests for a specific release channel
yarn test --release-channel=stable

# Run tests for built artifacts
yarn test --build

# Run with persistent (concurrent) renderer
yarn test --persistent

# Run only specific test
yarn test packages/react/src/__tests__/ReactHooks-test.js
```

### Jest Config Files

| Config | Purpose |
|--------|---------|
| `scripts/jest/config.base.js` | Base Jest configuration |
| `scripts/jest/config.source.js` | Source code tests (OSS) |
| `scripts/jest/config.source-www.js` | Source tests with www flags |
| `scripts/jest/config.source-xplat.js` | Source tests with xplat flags |
| `scripts/jest/config.source-persistent.js` | Tests with persistent mode flags |
| `scripts/jest/config.build.js` | Tests against built artifacts |
| `scripts/jest/config.build-devtools.js` | DevTools build tests (3.8KB) |

### Test Utilities

- `scripts/jest/setupTests.js` — Global test setup (11KB): configures custom matchers, React testing utilities
- `scripts/jest/setupEnvironment.js` — DOM environment setup
- `scripts/jest/setupHostConfigs.js` — Host configuration setup for reconciler tests (8.8KB)
- `scripts/jest/TestFlags.js` — Runtime feature flags accessible in tests (4.1KB)
- `scripts/jest/preprocessor.js` — Babel/Flow source transformation (4.7KB)

### Test Environments

React test files can use JSDoc pragmas to select environments:

```js
// @jest-environment jsdom
// @jest-environment node
```

Feature gates in tests use `@gate` pragmas:

```js
// @gate enableViewTransition
it('should support view transitions', () => { ... });
```

## Code Quality Tools

```bash
# Run ESLint
yarn lint

# Run Prettier formatting
yarn prettier

# Run Flow type checking
yarn flow

# Extract error codes (after adding new error messages)
yarn extract-errors

# Validate versions are consistent
yarn version-check

# Manage feature flags
yarn flags
```

## Deployment / Release

The release process uses custom scripts in `scripts/release/`:

```bash
# Download experimental build from CI
yarn download-build

# Build all release channels for publishing
node scripts/rollup/build-all-release-channels.js

# Publish to npm (requires auth)
scripts/release/publish.js
```

Published packages go to npm under the `react` org. Experimental builds are published under `0.0.0-experimental-*` version tags.

## Build Output

Built artifacts go to:
- `build/node_modules/<package-name>/` — Structured as npm packages ready for publishing
- `build/oss-stable/` — Stable channel builds
- `build/oss-experimental/` — Experimental channel builds
- `build/facebook-www/` — Meta internal builds

Each package directory contains `cjs/` (CommonJS), `esm/` (ES Modules), and `umd/` (UMD) subdirectories as applicable.
