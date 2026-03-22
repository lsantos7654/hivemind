# TypeBox — Build System

## Build System Type

TypeBox uses **Deno** as its development runtime and task runner. All build, test, format, and publish workflows are driven by Deno tasks defined in `deno.jsonc`. The task implementations live in `tasks.ts` (Deno entry point) and the `task/` directory.

There is no `package.json` in the source repository — the npm `package.json` is **generated at build time** by the `build` task using the `tasksmith` library. The project therefore has no npm-based dev dependencies; everything is resolved through Deno's URL-based import system.

## Configuration Files

### `deno.jsonc` — Primary configuration
Defines all task scripts, import aliases, formatter settings, excluded paths, and TypeScript compiler options:

```jsonc
{
  "tasks": {
    "bench": "deno run -A tasks.ts bench",
    "build": "deno run -A tasks.ts build",
    "clean": "deno run -A tasks.ts clean",
    "fast": "deno run -A tasks.ts fast",       // Watch mode tests (no type check)
    "format": "deno run -A tasks.ts format",
    "local": "deno run -A tasks.ts local",     // Build to adjacent project
    "metrics": "deno run -A tasks.ts metrics",
    "native": "deno run -A tasks.ts native",   // Build with TypeScript native (tsgo)
    "publish": "deno run -A tasks.ts publish",
    "range": "deno run -A tasks.ts range",
    "report": "deno run -A tasks.ts report",   // Test coverage report
    "start": "deno run -A tasks.ts start",     // Run example
    "syntax": "deno run -A tasks.ts syntax",   // Regenerate parser code
    "test": "deno run -A tasks.ts test",
    "turing": "deno run -A tasks.ts turing",   // Type-level Turing completeness test
    "website": "deno run -A tasks.ts website"  // Serve docs site locally
  }
}
```

The import map section maps TypeBox's own package paths for use within Deno:

```jsonc
"imports": {
  "typebox/compile": "./src/compile/index.ts",
  "typebox/error":   "./src/error/index.ts",
  "typebox/format":  "./src/format/index.ts",
  "typebox/guard":   "./src/guard/index.ts",
  "typebox/schema":  "./src/schema/index.ts",
  "typebox/system":  "./src/system/index.ts",
  "typebox/value":   "./src/value/index.ts",
  "typebox/type":    "./src/type/index.ts",
  "typebox":         "./src/index.ts"
}
```

Formatter config (applied by `deno fmt`):
```jsonc
"fmt": {
  "semiColons": false,
  "singleQuote": true,
  "trailingCommas": "never",
  "lineWidth": 240
}
```

### `tsconfig.json` — TypeScript compiler configuration
Used for IDE type checking and non-Deno contexts:

```json
{
  "compilerOptions": {
    "strict": true,
    "target": "ES2020",
    "module": "ESNext",
    "noEmit": true,
    "allowImportingTsExtensions": true,
    "exactOptionalPropertyTypes": true,
    "paths": { ... }   // mirrors deno.jsonc import map
  }
}
```

The compiler targets **ES2020** for output, uses strict mode, and enforces `exactOptionalPropertyTypes` for maximum type accuracy.

### `deno.lock` — Lock file
Auto-managed by Deno; pins all URL-imported dependencies to exact content hashes.

## External Dependencies

TypeBox has minimal external runtime dependencies. All are fetched via Deno URLs, pinned in `deno.lock`:

| Dependency | Version | Import alias | Purpose |
|---|---|---|---|
| `tasksmith` | 0.9.9 | `tasksmith` | Task runner utilities (build, test, publish) |
| `parsebox` | 0.11.0 | `parsebox` | Parser combinators for the TypeScript DSL parser (syntax task) |

Documentation website dependencies (development only, not included in npm package):

| Dependency | Version | Purpose |
|---|---|---|
| `react` | 19.1.1 | Website UI |
| `react-dom` | 19.1.1 | Website rendering |
| `react-router-dom` | 7.8.2 | Website routing |
| `react-three/fiber` | 9.3.0 | Website 3D rendering |
| `three` | 0.180.0 | 3D graphics for website |
| `marked` | 16.2.1 | Markdown rendering for docs |
| `prismjs` | 1.30.0 | Syntax highlighting for docs |

## Build Targets and Commands

### `deno task build`
Compiles the library into an npm-publishable ESM package at `target/build/`. The `BuildPackage()` function in `tasks.ts` calls `Task.build.esm('src', { ... })` from `tasksmith`, which:

1. Transpiles all `.ts` source from `src/` into `.js` + `.d.ts` files
2. Uses TypeScript **5.9.3** (pinned compiler version)
3. Writes output to `target/build/`
4. Copies `license` and `readme.md` into the package
5. Generates `package.json` with:
   ```json
   {
     "name": "typebox",
     "version": "1.1.6",
     "description": "Json Schema Type Builder with Static Type Resolution for TypeScript",
     "keywords": ["typescript", "jsonschema"],
     "license": "MIT",
     "author": "sinclairzx81"
   }
   ```

The package exports multiple entry points matching the import path aliases:
- `typebox` → `src/index.ts`
- `typebox/value` → `src/value/index.ts`
- `typebox/schema` → `src/schema/index.ts`
- `typebox/compile` → `src/compile/index.ts`
- `typebox/format` → `src/format/index.ts`
- `typebox/guard` → `src/guard/index.ts`
- `typebox/system` → `src/system/index.ts`
- `typebox/error` → `src/error/index.ts`

### `deno task test`
Runs all tests under `test/jsonschema/` and `test/typebox/` using Deno's built-in test runner. Accepts an optional filter argument:
```bash
deno task test
deno task test -- object   # filter to tests matching "object"
```

### `deno task fast`
Same as `test` but with `--watch` and `--no-check` flags for rapid iterative development.

### `deno task format`
Runs `deno fmt src test/typebox` to format source and test files according to the formatter config in `deno.jsonc`.

### `deno task clean`
Deletes the `target/` directory.

### `deno task bench`
Runs the benchmark suite (implemented in `task/bench/`).

### `deno task syntax`
Regenerates the parser code for the Script DSL (implemented in `task/syntax/`). This is a code-generation step using `parsebox`.

### `deno task native`
Builds the package using the TypeScript native compiler (`tsgo latest`) via `Task.tsgo()`. Used for forward-compatibility testing with the upcoming Go-based TypeScript compiler.

### `deno task publish`
Tags the current git commit with the version number and pushes the tag to origin:
```typescript
await Task.shell(`git tag ${version}`)
await Task.shell(`git push origin ${version}`)
```
After building, the package is published to npm from `target/build/`.

### `deno task website`
Builds and serves the documentation website from `docs/` locally (React + Three.js SPA).

### `deno task metrics`
Reports bundle size metrics for the compiled output.

### `deno task report`
Runs tests with coverage reporting.

### `deno task range`
Tests TypeBox across different TypeScript compiler version ranges.

### `deno task turing`
Runs a type-level Turing completeness test to verify the type system's expressiveness.

## How to Build and Test (Quick Reference)

```bash
# Install Deno (if not installed)
curl -fsSL https://deno.land/install.sh | sh

# Run tests
deno task test

# Run tests in watch mode (no type checking for speed)
deno task fast

# Build npm package
deno task build
# Output: target/build/

# Clean build output
deno task clean

# Format source code
deno task format

# Run benchmarks
deno task bench

# Serve documentation website
deno task website

# Build for local testing in an adjacent project
deno task local
# Output: ../build-test/node_modules/typebox
```

## Deployment

The library is published to npm as `typebox`. The publish workflow is:
1. `deno task build` — compile to `target/build/`
2. `cd target/build && npm publish` (or via `deno task publish` which tags + pushes, triggering CI)

There is a GitHub Actions workflow (`.github/workflows/build.yml`) for CI testing on push.
