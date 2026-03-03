# Joi Build System

## Build System Overview

Joi uses a straightforward Node.js-based build system centered around npm scripts and testing tools. The project targets modern Node.js environments (>= 20) and provides browser builds through webpack. The build system emphasizes testing, code quality, and backwards compatibility.

## Build System Type

**Package Manager**: npm (with `.npmrc` configuration for consistent behavior)

**Module System**: CommonJS (`require`/`module.exports`) for Node.js compatibility

**Testing Framework**: @hapi/lab with 100% code coverage requirement

**Code Quality**: @hapi/eslint-plugin with custom ESLint v9 flat config

**Browser Bundler**: Webpack 5 with Babel transpilation

**Type System**: TypeScript definitions (`.d.ts`) for type safety, but source is JavaScript

## Configuration Files

### Package Configuration (`package.json`)

```json
{
  "name": "joi",
  "version": "18.0.2",
  "main": "lib/index.js",           // Node.js entry point
  "types": "lib/index.d.ts",         // TypeScript definitions
  "browser": "dist/joi-browser.min.js", // Browser bundle
  "engines": {
    "node": ">= 20"                  // Minimum Node.js version
  },
  "files": [                         // Files included in npm package
    "lib/**/*",
    "dist/*"
  ]
}
```

Key metadata:
- **Repository**: `git://github.com/hapijs/joi`
- **License**: BSD-3-Clause
- **Keywords**: `schema`, `validation`

### ESLint Configuration (`eslint.config.js`)

Uses the modern ESLint v9 flat config format:

```javascript
const HapiPlugin = require('@hapi/eslint-plugin');

module.exports = [
  {
    ignores: ['browser', 'dist', 'sandbox.js']
  },
  ...HapiPlugin.configs.module
];
```

Leverages the standardized @hapi/eslint-plugin for consistent code style across the hapi ecosystem.

### NPM Configuration (`.npmrc`)

Contains npm-specific settings for consistent package management across development environments.

### CI/CD Configuration (`.github/workflows/ci-module.yml`)

```yaml
name: ci
on:
  push:
    branches: [master, v17]
  pull_request:
  workflow_dispatch:

jobs:
  test:
    uses: hapijs/.github/.github/workflows/ci-module.yml@min-node-20-hapi-21
```

Uses reusable workflow from the hapi organization for standardized CI across all hapi projects.

## External Dependencies

### Runtime Dependencies

```json
{
  "@hapi/address": "^5.1.1",      // Email, domain, URI, IP validation
  "@hapi/formula": "^3.0.2",      // Formula parsing for templates
  "@hapi/hoek": "^11.0.7",        // Utility functions (clone, merge, assert)
  "@hapi/pinpoint": "^2.0.1",     // Error location tracking
  "@hapi/tlds": "^1.1.1",         // Top-level domain list
  "@hapi/topo": "^6.0.2",         // Topological sorting
  "@standard-schema/spec": "^1.0.0" // Standard schema specification
}
```

All runtime dependencies are from the @hapi namespace, ensuring ecosystem consistency and controlled dependency management.

### Development Dependencies

```json
{
  "@hapi/bourne": "^3.0.0",       // JSON parsing security
  "@hapi/code": "^9.0.3",         // Assertion library for tests
  "@hapi/eslint-plugin": "^7.0.0", // Linting rules
  "@hapi/joi-legacy-test": "npm:@hapi/joi@15.x.x", // Legacy compatibility tests
  "@hapi/lab": "^26.0.0",         // Testing framework
  "@types/node": "^20.17.47",     // Node.js type definitions
  "typescript": "^5.8.3"          // TypeScript compiler for .d.ts validation
}
```

### Browser Build Dependencies (`browser/package.json`)

The browser build has its own isolated dependencies:

```json
{
  "@babel/core": "^7.21.0",
  "@babel/preset-env": "^7.20.2",
  "babel-loader": "^9.1.2",
  "webpack": "^5.76.1",
  "webpack-cli": "^5.0.1",
  "webpack-bundle-analyzer": "^3.4.1",
  "karma": "^6.4.1",               // Browser test runner
  "karma-chrome-launcher": "^3.1.1",
  "karma-mocha": "^2.0.1",
  "karma-webpack": "^5.0.0",
  "mocha": "^8.4.0"
}
```

## Build Targets and Commands

### Primary npm Scripts

**Testing**:
```bash
npm test
# Runs: lab -t 100 -a @hapi/code -L -Y
# -t 100: Requires 100% code coverage
# -a @hapi/code: Uses @hapi/code assertion library
# -L: Disables global leak detection
# -Y: Parallel test execution
```

```bash
npm run test-cov-html
# Runs: lab -r html -o coverage.html -a @hapi/code
# Generates HTML coverage report
```

**Publishing**:
```bash
npm run prepublishOnly
# Runs: cd browser && npm install && npm run build
# Automatically builds browser bundle before npm publish
```

### Browser Build Commands (`browser/` directory)

```bash
npm run build
# Webpack production build → dist/joi-browser.min.js

npm run build-dev
# Webpack development build (unminified, with source maps)

npm run build-analyze
# Generates bundle analysis (stats.json)

npm run postbuild-analyze
# Opens webpack-bundle-analyzer UI

npm test
# Runs Karma tests in headless Chrome
```

### Webpack Configuration Highlights

**Production Build** (`browser/webpack.config.js`):
- Mode: production (minification enabled)
- Entry: `../lib/index.js`
- Output: `dist/joi-browser.min.js`
- Babel transpilation via `babel-loader` with `@babel/preset-env`
- Target: Modern browsers (configured via browserslist)

**Test Build** (`browser/webpack.mocha.js`):
- Mode: development
- Source maps enabled
- Mocha test loader integration

**Karma Configuration** (`browser/karma.conf.js`):
- Runs tests in headless Chrome
- Uses webpack for bundling test files
- Generates coverage reports

## Benchmark System

The `benchmarks/` directory contains performance regression testing:

**Setup**:
```bash
npm run bench-update
# Establishes baseline performance metrics
```

**Execution**:
```bash
npm run bench
# Compares current performance against baseline
# Highlights regressions >10% in red
```

**Purpose**: Detect performance regressions during development, not for comparing Joi to other libraries.

## How to Build

### For Node.js Development

1. **Clone repository**:
   ```bash
   git clone git://github.com/hapijs/joi
   cd joi
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run tests**:
   ```bash
   npm test
   ```

4. **Lint code**:
   ```bash
   npx eslint lib/
   ```

### For Browser Build

1. **Navigate to browser directory**:
   ```bash
   cd browser
   ```

2. **Install browser-specific dependencies**:
   ```bash
   npm install
   ```

3. **Build for production**:
   ```bash
   npm run build
   # Outputs to: dist/joi-browser.min.js
   ```

4. **Build for development**:
   ```bash
   npm run build-dev
   ```

5. **Run browser tests**:
   ```bash
   npm test
   ```

6. **Analyze bundle size**:
   ```bash
   npm run build-analyze
   npm run postbuild-analyze
   ```

### Type Definition Validation

The TypeScript definitions are validated automatically:

```bash
npx tsc --noEmit lib/index.d.ts
```

TypeScript compiler ensures `.d.ts` files are syntactically correct and type-safe.

## Testing Strategy

### Unit Tests

- **Framework**: @hapi/lab
- **Assertions**: @hapi/code
- **Coverage**: 100% required (`-t 100` flag)
- **Location**: `test/` directory mirrors `lib/` structure
- **Execution**: Parallel (`-Y` flag) for performance

### Browser Tests

- **Framework**: Mocha (via Karma)
- **Runner**: Karma with Chrome headless
- **Bundling**: Webpack with Babel
- **Location**: `browser/tests/`

### Performance Tests

- **Framework**: Custom benchmarking suite
- **Baseline**: Stored performance snapshots
- **Detection**: Highlights >10% regressions
- **Location**: `benchmarks/`

### Legacy Compatibility Tests

The project includes `@hapi/joi@15.x.x` as a dev dependency for testing backwards compatibility and migration paths.

## Deployment

### NPM Publishing

1. **Pre-publish hook** automatically runs:
   ```bash
   cd browser && npm install && npm run build
   ```
   This ensures the browser bundle is always fresh.

2. **Published files** (defined in `package.json`):
   - `lib/**/*` - All source files and TypeScript definitions
   - `dist/*` - Browser bundle

3. **Version management**: Follows semantic versioning (currently 18.0.2)

### CI/CD Pipeline

GitHub Actions workflow triggers on:
- Push to `master` or `v17` branches
- Pull requests
- Manual workflow dispatch

The workflow uses a reusable hapi.js organization workflow that:
- Runs tests on Node.js 20+
- Enforces 100% code coverage
- Validates linting rules
- Ensures TypeScript definitions are valid

## Build Optimization

### Code Splitting

The library is designed as a single bundle for both Node.js and browsers. No code splitting is used to maintain simplicity and reduce overhead.

### Tree Shaking

The CommonJS module format limits tree-shaking capabilities, but the browser build uses webpack's optimization to eliminate dead code.

### Minification

Browser builds use webpack's production mode with Terser minification for optimal bundle size.

### Polyfills

Browser build includes polyfills for Node.js-specific features like `Buffer` via webpack configuration (`assert`, `util` packages).

## Development Workflow

1. Make code changes in `lib/`
2. Run `npm test` to ensure 100% coverage
3. Run linter: `npx eslint lib/`
4. Update browser build: `cd browser && npm run build`
5. Test browser build: `cd browser && npm test`
6. Run benchmarks to detect regressions: `npm run bench`
7. Update TypeScript definitions if API changed
8. Commit changes and open PR

The CI pipeline automatically validates all checks before merging.
