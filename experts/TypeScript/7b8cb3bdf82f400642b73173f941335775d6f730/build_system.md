# TypeScript — Build System

## Build System Overview

TypeScript uses **[hereby](https://github.com/nicolo-ribaudo/hereby)** as its task runner (replacing the old Gulp-based system). The main build file is `Herebyfile.mjs` in the repository root. Hereby is a lightweight task runner with a Makefile-like dependency model.

The TypeScript compiler **bootstraps itself** — the TypeScript sources are compiled by the previously-built version of TypeScript (the "LKG" — Last Known Good). The LKG compiler is stored in `lib/` in the published package and used as the bootstrap compiler for development.

## Build Tool Stack

| Tool | Role |
|------|------|
| `hereby` | Task runner (replaces Gulp) |
| `npm` (8.19.4) | Package manager |
| `node` (22.22.0) | JavaScript runtime for build scripts |
| TypeScript (self-hosted) | Compiles TypeScript sources |
| `esbuild` | Bundles language service for browser/min targets |
| `dprint` | Code formatter (TypeScript plugin) |
| `eslint` | Linter with custom rules |
| `mocha` | Test framework for unit tests |
| `c8` / `monocart-coverage-reports` | Code coverage |
| `playwright` | Browser integration tests |

## Key Configuration Files

| File | Purpose |
|------|---------|
| `Herebyfile.mjs` | All build task definitions |
| `package.json` | NPM scripts, dependencies, engine constraints |
| `src/tsconfig-base.json` | Shared TS compiler options for all sub-packages |
| `src/tsconfig.json` | Root tsconfig with project references to all sub-packages |
| `src/compiler/tsconfig.json` | Compiler-specific tsconfig |
| `src/services/tsconfig.json` | Services-specific tsconfig |
| `scripts/build/options.mjs` | Build command-line option parsing |
| `scripts/build/projects.mjs` | `buildProject()` / `watchProject()` helpers |
| `scripts/build/tests.mjs` | Test running helpers |
| `eslint.config.mjs` | ESLint flat config |
| `knip.jsonc` | Knip unused exports/deps config |

## External Dependencies

All dependencies are dev-only (TypeScript ships no runtime `dependencies`). Key ones:

| Package | Usage |
|---------|-------|
| `hereby` | Task runner |
| `esbuild` | Bundling `lib/typescript.js` for browser and min targets |
| `mocha` | Test runner |
| `chai` | Test assertions |
| `playwright` | Browser tests |
| `dprint` + `@dprint/typescript` | Code formatting |
| `eslint`, `typescript-eslint` | Linting with TypeScript-aware rules |
| `chokidar` | File watching in watch mode tasks |
| `diff` | Diffing baselines in tests |
| `glob` | File globbing in build scripts |
| `source-map-support` | Source map support for error reporting |
| `knip` | Dead code/dependency detection |
| `fast-xml-parser` | Parsing XML-like test fixtures |
| `@esfx/canceltoken` | Cancellation tokens in build tasks |
| `azure-devops-node-api` | Release pipeline integration |
| `@octokit/rest` | GitHub API for release scripts |

## Compiler Options (src/tsconfig-base.json)

All sub-packages inherit these settings:
- `target: "es2020"`, `module: "NodeNext"`, `moduleResolution: "NodeNext"`
- `strict: true` (with `strictBindCallApply: false`, `useUnknownInCatchVariables: false`)
- `emitDeclarationOnly: true` (source is not compiled to JS here; esbuild handles bundling)
- `isolatedDeclarations: true` (each file's types resolvable without cross-file inference)
- `composite: true` (project references)
- `preserveConstEnums: true`
- `noImplicitOverride: true`

## Build Targets and Commands

### NPM Scripts (via package.json)

```bash
npm run build            # Compile compiler + tests (hereby local + hereby tests)
npm run build:compiler   # hereby local — compile compiler sources only
npm run build:tests      # hereby tests — compile test harness
npm test                 # hereby runtests-parallel --light=false
npm run lint             # hereby lint
npm run format           # dprint fmt
npm run clean            # hereby clean
```

### Key Hereby Tasks

```bash
hereby local             # Full local build: lib + diagnostics + compiler + services + bundling
hereby scripts           # Build files in scripts/ directory
hereby lib               # Build standard library .d.ts files
hereby generate-diagnostics  # Regenerate diagnosticInformationMap.generated.ts from JSON
hereby build-src         # Compile all src/ TypeScript projects with tsc --build
hereby tsc               # Build the tsc bundle
hereby services          # Build the language services bundle
hereby dts-services      # Bundle .d.ts files for language services
hereby tsserver          # Build tsserver bundle
hereby min               # Build minified bundles
hereby tests             # Build test harness and test runner
hereby runtests          # Run tests sequentially
hereby runtests-parallel # Run tests in parallel (recommended)
hereby run-eslint-rules-tests  # Run ESLint rule tests
hereby lint              # Run ESLint
hereby knip              # Run knip dead code analysis
hereby check-format      # Verify dprint formatting
hereby clean             # Remove built artifacts
hereby watch-local       # Incremental watch build
hereby baseline-accept   # Accept new baselines (copy local → reference)
hereby diff              # Show diff between local and reference baselines
```

### Test Commands

```bash
# Run all tests (parallel, recommended)
hereby runtests-parallel

# Run specific test suite
hereby runtests --runner=compiler
hereby runtests --runner=conformance
hereby runtests --runner=fourslash
hereby runtests --runner=project
hereby runtests --runner=unittests

# Run tests matching a filter
hereby runtests --tests=someTest

# Accept updated baselines
hereby baseline-accept

# Show baseline diffs
hereby diff
```

## How to Build from Scratch

```bash
# 1. Install dependencies
npm ci

# 2. Build the compiler and all outputs
hereby local

# 3. Build the test harness
hereby tests

# 4. Run tests to verify
hereby runtests-parallel
```

## Build Pipeline Details

1. **`hereby scripts`** — Builds TypeScript files in `scripts/build/` using the bootstrap compiler.

2. **`hereby lib`** — Concatenates `src/lib/*.d.ts` files into `built/local/lib.*.d.ts` with copyright headers.

3. **`hereby generate-diagnostics`** — Runs `scripts/processDiagnosticMessages.mjs` to generate `src/compiler/diagnosticInformationMap.generated.ts` from `src/compiler/diagnosticMessages.json`.

4. **`hereby build-src`** — Runs `tsc --build src/tsconfig.json` to compile all project references. Output goes to `built/local/`.

5. **Bundling** — Uses esbuild to bundle `built/local/typescript/typescript.js` into `built/local/typescript.js` (the main distribution artifact). Separate tasks bundle the language service, min builds, etc.

6. **`hereby dts`** — Runs `dtsBundler.mjs` to merge all declaration files into a single `built/local/typescript.d.ts`, stripping `@internal` members.

7. **`hereby other-outputs`** — Copies diagnostic messages, types map, and localized strings to `built/local/`.

8. **`hereby local`** — Orchestrates all of the above into a complete local build.

## Deployment / Publishing

The `scripts/produceLKG.mjs` script copies `built/local/` artifacts to `lib/` (the LKG), which is what gets published to npm. The npm package includes `bin/`, `lib/`, `LICENSE.txt`, `README.md`, and `SECURITY.md` (as specified in `package.json#files`).

The `azure-pipelines.release.yml` and `azure-pipelines.release-publish.yml` define CI/CD for official releases.
