# Marked — Build System

## Build System Type and Configuration Files

Marked uses a **custom Node.js build pipeline** combining TypeScript compilation and esbuild bundling, orchestrated through `npm scripts` defined in `package.json`.

**Key configuration files:**

| File | Purpose |
|------|---------|
| `package.json` | NPM scripts, engine requirements (`node >= 20`), exports map |
| `tsconfig.json` | TypeScript compiler configuration for source compilation |
| `tsconfig-type-test.json` | Separate TypeScript config for type-level tests (`test/types/marked.ts`) |
| `esbuild.config.js` | esbuild bundler configuration (ESM + UMD outputs with UMD wrapper plugin) |
| `eslint.config.js` | ESLint flat config for code quality |
| `.releaserc.json` | semantic-release configuration for automated versioning and publishing |
| `vercel.json` | Deployment configuration for the documentation site at marked.js.org |

## External Dependencies

### Production Dependencies
**None.** Marked ships with zero runtime dependencies. The published package only contains compiled JavaScript (`lib/`) and the CLI (`bin/`).

### Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `typescript` | `5.9.3` | TypeScript compilation |
| `dts-bundle-generator` | `^9.5.1` | Bundles all `.d.ts` type declarations into a single `lib/marked.d.ts` |
| `esbuild` | `^0.27.4` | Fast JavaScript bundler (builds ESM and UMD outputs) |
| `esbuild-plugin-umd-wrapper` | `^3.0.0` | Wraps ESM output in UMD format with library name `marked` |
| `eslint` | `^10.0.3` | Linting |
| `@markedjs/eslint-config` | `^1.0.14` | Shared ESLint rules for the markedjs org |
| `@markedjs/testutils` | `17.0.1-2` | Test utilities shared across the markedjs organization |
| `commonmark` | `0.31.2` | CommonMark spec implementation used for compliance testing |
| `markdown-it` | `14.1.1` | Used as a comparison parser in benchmarks |
| `recheck` | `^4.5.0` | ReDoS (Regular Expression Denial of Service) vulnerability detection |
| `cheerio` | `1.2.0` | HTML parsing used in spec test comparison |
| `highlight.js` | `^11.11.1` | Used in benchmarks and test demos |
| `marked-highlight` | `^2.2.3` | marked extension used during documentation build |
| `marked-man` | `^2.1.0` | Converts `man/marked.1.md` to a Unix man page |
| `rimraf` | `^6.1.3` | Cross-platform `rm -rf` for build reset |
| `semantic-release` + plugins | Various | Automated changelog, NPM publish, GitHub releases |
| `tslib` | `^2.8.1` | TypeScript helper library |
| `titleize` | `^4.0.0` | Used in documentation build script |
| `@arethetypeswrong/cli` (`attw`) | `^0.18.2` | Validates TypeScript package exports correctness |
| `cross-env` | `^10.1.0` | Cross-platform environment variable setting |

## Build Targets and Commands

### Full Build

```sh
npm run build
```

Runs three steps in sequence:
1. `build:esbuild` — Bundle TypeScript → JS
2. `build:types` — Compile TypeScript types
3. `build:man` — Generate man page

### Individual Build Steps

```sh
# 1. Bundle JavaScript (runs esbuild.config.js)
npm run build:esbuild
# Output: lib/marked.esm.js, lib/marked.umd.js (both minified with source maps)

# 2. Compile TypeScript + bundle types
npm run build:types
# Equivalent to: tsc && dts-bundle-generator --export-referenced-types --project tsconfig.json -o lib/marked.d.ts src/marked.ts
# Output: lib/marked.d.ts

# 3. Generate man page
npm run build:man
# Equivalent to: marked-man man/marked.1.md > man/marked.1
# Output: man/marked.1

# 4. Build documentation site (requires full build first)
npm run build:docs
# Equivalent to: npm run build && node docs/build.js
# Output: public/ directory (the marked.js.org documentation site)

# Clean build artifacts
npm run build:reset
# Equivalent to: rimraf ./lib ./public
```

### How esbuild.config.js Works

The esbuild config builds two outputs from the single entry point `src/marked.ts`:

```js
// ESM output
esbuild.build({
  entryPoints: ['src/marked.ts'],
  format: 'esm',
  outfile: 'lib/marked.esm.js',
  bundle: true,
  minify: true,
  sourcemap: true,
});

// UMD output (using esbuild-plugin-umd-wrapper with libraryName: 'marked')
esbuild.build({
  entryPoints: ['src/marked.ts'],
  format: 'umd',
  outfile: 'lib/marked.umd.js',
  bundle: true,
  minify: true,
  sourcemap: true,
  plugins: [umdWrapper({ libraryName: 'marked' })],
});
```

Both outputs include a license banner with the version number (read from `package.json` or `SEMANTIC_RELEASE_NEXT_VERSION` env var).

## How to Build, Test, and Deploy

### Building

```sh
# Install dependencies
npm install

# Full build (JS bundles + types + man page)
npm run build

# Build only JS bundles (faster iteration)
npm run build:esbuild
```

### Testing

```sh
# Full test suite (build + all checks)
npm test
# Runs: build:reset → build:docs → test:specs → test:unit → test:umd → test:cjs → test:types → test:lint

# Run only failing/focused tests (uses Node.js --test-only flag)
npm run test:only

# Individual test suites:
npm run test:specs        # CommonMark + GFM spec compliance tests
npm run test:unit         # Unit tests for Lexer, Parser, Hooks, instance, CLI
npm run test:umd          # UMD bundle smoke test
npm run test:cjs          # CommonJS interop test
npm run test:types        # TypeScript type correctness + attw package checks
npm run test:lint         # ESLint check

# Update spec test fixtures (downloads latest CommonMark/GFM specs)
npm run test:update

# Performance benchmark (requires full build)
npm run bench

# ReDoS vulnerability scan
npm run test:redos

# Display active lexer regex rules
npm run rules
```

### Engine Requirements

- **Node.js**: >= 20 (uses native `node --test` runner, ESM modules, Worker Threads)
- **Browser**: Baseline Widely Available (modern browsers)

### Release / Deployment

Releases are fully automated via `semantic-release` triggered by CI on push to the main branch:
1. Analyzes commits using `@semantic-release/commit-analyzer` (conventional commits)
2. Generates release notes (`@semantic-release/release-notes-generator`)
3. Updates `CHANGELOG.md` and `package.json` version (`@semantic-release/npm`)
4. Publishes to NPM with provenance (`publishConfig.provenance: true`)
5. Creates a GitHub release (`@semantic-release/github`)
6. Commits the updated files back to the repo (`@semantic-release/git`)

The `.releaserc.json` file controls the semantic-release configuration. The `SEMANTIC_RELEASE_NEXT_VERSION` environment variable is used during the build to embed the correct version in the bundle banner.

### CI/CD

GitHub Actions workflow at `.github/workflows/tests.yml` runs the full test suite on push and pull requests.

### Package Exports

The `package.json` exports map specifies:
```json
{
  "main": "./lib/marked.esm.js",      // Node.js (ESM)
  "module": "./lib/marked.esm.js",    // Bundler (ESM)
  "browser": "./lib/marked.umd.js",   // Browser (UMD)
  "types": "./lib/marked.d.ts",       // TypeScript
  "exports": {
    ".": { "types": "./lib/marked.d.ts", "default": "./lib/marked.esm.js" },
    "./bin/marked": "./bin/marked.js",
    "./package.json": "./package.json"
  }
}
```

The published package (`files`) includes only `bin/`, `lib/`, and `man/`.
