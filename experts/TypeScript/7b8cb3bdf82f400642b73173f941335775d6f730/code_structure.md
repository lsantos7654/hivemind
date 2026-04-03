# TypeScript — Code Structure

## Annotated Directory Tree

```
TypeScript/
├── AGENTS.md                  # Critical: coding agent instructions (maintenance mode notice)
├── CONTRIBUTING.md            # Contribution guide (note: new features → typescript-go)
├── Herebyfile.mjs             # Main build script — defines all hereby tasks
├── eslint.config.mjs          # ESLint configuration
├── knip.jsonc                 # Knip dead-code analysis config
├── package.json               # NPM package metadata; bin: tsc, tsserver
├── scripts/                   # Build and release tooling scripts
│   ├── build/                 # Build utilities (projects.mjs, tests.mjs, utils.mjs, options.mjs)
│   ├── eslint/                # Custom ESLint rules for the TypeScript codebase
│   ├── hooks/                 # Git hooks
│   ├── processDiagnosticMessages.mjs  # Generates diagnosticInformationMap.generated.ts
│   ├── dtsBundler.mjs         # Bundles .d.ts files for distribution
│   ├── produceLKG.mjs         # Produces the "last known good" compiler bootstrap
│   ├── generateLocalizedDiagnosticMessages.mjs
│   └── checkPackageSize.mjs
├── src/                       # All TypeScript source code
│   ├── tsconfig.json          # Root tsconfig with project references
│   ├── tsconfig-base.json     # Shared compiler options (target: ES2020, module: NodeNext)
│   ├── compiler/              # Core compiler pipeline
│   ├── services/              # Language service (IDE features)
│   ├── server/                # tsserver (editor server process)
│   ├── tsc/                   # tsc CLI entry point
│   ├── typescript/            # Public package entry point (re-exports ts namespace)
│   ├── lib/                   # Standard library .d.ts definitions
│   ├── harness/               # Test harness infrastructure
│   ├── testRunner/            # Test runner and test types
│   ├── deprecatedCompat/      # Deprecated API compat shims
│   ├── typingsInstaller/      # Type acquisition (node-based)
│   ├── typingsInstallerCore/  # Type acquisition (shared core)
│   ├── watchGuard/            # Process watchdog for tsserver
│   └── jsTyping/              # JS project typing analysis
├── tests/                     # Test cases and baselines
│   ├── cases/
│   │   ├── compiler/          # Compiler conformance tests (.ts files with @-directives)
│   │   ├── conformance/       # Broader conformance tests
│   │   ├── fourslash/         # Fourslash editor tests (completions, go-to-def, etc.)
│   │   ├── project/           # Project compilation tests
│   │   ├── transpile/         # transpileModule tests
│   │   └── unittests/         # Unit tests
│   ├── baselines/
│   │   ├── reference/         # Committed baseline outputs (expected results)
│   │   └── local/             # Locally-generated outputs (gitignored, diff against reference)
│   └── lib/                   # Test helper libraries
└── bin/
    ├── tsc                    # tsc executable wrapper
    └── tsserver               # tsserver executable wrapper
```

## Module and Package Organization

The codebase uses TypeScript project references (`composite: true`) so each subdirectory under `src/` is its own compilation unit. All projects share `src/tsconfig-base.json` settings: target ES2020, module NodeNext, `emitDeclarationOnly: true`, `isolatedDeclarations: true`, `strict: true`.

Imports between packages use the `_namespaces/` barrel-file pattern: each subdirectory has a `_namespaces/ts.ts` (or similar) that re-exports everything from that package's files, enabling other packages to import from it with a single import.

## Core Source Directories

### `src/compiler/` — The Compiler Pipeline

The largest and most critical directory (~100k+ lines total).

| File | Purpose |
|------|---------|
| `scanner.ts` | Lexical scanner/tokenizer. Produces `SyntaxKind` tokens from source text. Exports `Scanner` interface and `createScanner()`. |
| `parser.ts` (~10,823 lines) | Recursive-descent parser. Converts token stream into AST (`SourceFile` nodes). Handles error recovery. |
| `binder.ts` | Symbol binding pass. Walks the AST to create the symbol table, assigns `NodeFlags`, builds control flow graph. |
| `checker.ts` (~54,434 lines) | Type checker. The largest file in the codebase. Type inference, type compatibility, overload resolution, assignability, narrowing, generics instantiation. Exports `createTypeChecker()`. |
| `emitter.ts` | Code emitter. Takes the transformed AST and produces JavaScript (and source maps). Exports `createPrinter()`, `emitFiles()`. |
| `transformer.ts` | Orchestrates the transformation pipeline (AST → AST). |
| `transformers/` | Individual transformation passes: |
| `transformers/es2015.ts` | Transforms ES2015 features to ES5 (classes, arrow functions, destructuring, etc.) |
| `transformers/jsx.ts` | Transforms JSX to `React.createElement` calls or the new JSX transform |
| `transformers/esDecorators.ts` | Transforms TC39 stage-3 decorators |
| `transformers/legacyDecorators.ts` | Transforms TypeScript's legacy `@decorator` syntax |
| `transformers/module/` | Module format transformations (CommonJS, AMD, UMD, SystemJS, ESM) |
| `transformers/declarations.ts` | Generates `.d.ts` declaration files |
| `factory/nodeFactory.ts` | AST node factory — `createXxx` functions for every node type |
| `factory/nodeTests.ts` | Type guard functions — `isXxx(node)` for every node type |
| `types.ts` (~10,670 lines) | All public type definitions: `SyntaxKind`, `Node`, `SourceFile`, `Program`, `TypeChecker`, `CompilerOptions`, `Type`, `Symbol`, etc. |
| `program.ts` | `createProgram()` — the main entry point for compilation. Manages source file loading, module resolution, and the overall compilation state. |
| `commandLineParser.ts` | Parses `tsconfig.json` and command-line arguments into `ParsedCommandLine` / `CompilerOptions`. |
| `moduleNameResolver.ts` | Module resolution logic (Classic, Node, Node16, NodeNext, Bundler strategies). |
| `core.ts` | Utility functions: arrays, maps, strings, paths. |
| `path.ts` | Cross-platform path utilities. |
| `sys.ts` | System abstraction layer (`ts.sys`) — file I/O, process, environment. |
| `debug.ts` | Debug utilities, assertions, tracing. |
| `diagnosticMessages.json` | Source of truth for all diagnostic messages (errors/warnings). |
| `diagnosticInformationMap.generated.ts` | Generated from `diagnosticMessages.json` by `processDiagnosticMessages.mjs`. |
| `builder.ts` / `builderState.ts` | Incremental compilation state and builder programs. |
| `tsbuild.ts` | Solution builder (`tsc --build`) for project references. |
| `watch.ts` | Watch mode implementation. |
| `performance.ts` | Performance measurement utilities. |
| `tracing.ts` | Detailed tracing output for performance analysis. |
| `sourcemap.ts` | Source map generation. |

### `src/services/` — Language Service (IDE Features)

Provides the `LanguageService` interface consumed by editors via tsserver or directly.

| File/Directory | Purpose |
|------|---------|
| `services.ts` | `createLanguageService()` implementation — the main Language Service factory |
| `types.ts` | `LanguageService` and `LanguageServiceHost` interface definitions |
| `completions.ts` | Code completion (IntelliSense) — `getCompletionsAtPosition()` |
| `goToDefinition.ts` | Go-to-definition, go-to-type-definition |
| `findAllReferences.ts` | Find all references / find all implementations |
| `rename.ts` | Rename symbol across files |
| `documentHighlights.ts` | Document highlights (highlight all occurrences in file) |
| `navigationBar.ts` | File outline / navigation bar |
| `navigateTo.ts` | Workspace symbol search |
| `inlayHints.ts` | Inlay hints (type annotations, parameter names) |
| `codefixes/` | ~50+ individual code fix providers (add missing import, fix typos, convert syntax, etc.) |
| `refactors/` | Refactoring actions (extract function, convert to arrow, add/remove braces, etc.) |
| `formatting/` | Code formatting |
| `completions.ts` | Auto-import completions |
| `organizeImports.ts` | Organize/sort imports |
| `transpile.ts` | `transpileModule()` and `transpileDeclaration()` — single-file transpilation |
| `documentRegistry.ts` | Shared source file cache across multiple language service instances |
| `callHierarchy.ts` | Call hierarchy (incoming/outgoing calls) |
| `breakpoints.ts` | Breakpoint resolution for debuggers |

### `src/server/` — tsserver

The persistent background process used by most editors.

| File | Purpose |
|------|---------|
| `session.ts` | Main request/response handler — processes editor commands |
| `editorServices.ts` | Project management — creates/manages TypeScript projects |
| `project.ts` | Represents a single TypeScript project (config-based or inferred) |
| `protocol.ts` | TypeScript Server Protocol message type definitions |
| `scriptInfo.ts` | In-memory tracking of open files and their versions |
| `utilities.ts` | Server-specific utilities |

### `src/lib/` — Standard Library

Contains `.d.ts` type definitions for JavaScript environments:
- `es5.d.ts`, `es2015.*.d.ts` through `esnext.*.d.ts` — ECMAScript APIs
- `dom.generated.d.ts` — DOM browser API (generated)
- `decorators.d.ts`, `decorators.legacy.d.ts` — Decorator metadata
- `libs.json` — Master list controlling which lib files are included

### `src/harness/` — Test Infrastructure

Provides virtual file system, compiler wrappers, and fourslash support for tests.

### `tests/cases/` — Test Cases

- `compiler/` and `conformance/`: Plain `.ts` files with `// @option: value` directives. The test runner compiles them and diffs `.js` output + error messages against `tests/baselines/reference/`.
- `fourslash/`: Rich editor tests using the fourslash syntax (`[|caret|]` markers) to test completions, go-to-def, rename, etc.
- `unittests/`: Mocha-based unit tests for specific compiler subsystems.

## Code Organization Patterns

1. **Namespace barrel files**: Every package exports via `_namespaces/ts.ts` which re-exports all internal modules. External packages import from `"../compiler/_namespaces/ts.js"` rather than individual files.

2. **`@internal` annotations**: Many exported symbols are marked `/** @internal */`. These are excluded from the public `.d.ts` bundle by `dtsBundler.mjs`. Only symbols without `@internal` form the public API.

3. **`const enum`**: Extensively used for `SyntaxKind`, `NodeFlags`, `TypeFlags`, `SymbolFlags`, etc. These are inlined at compile time for performance but require special handling for external consumers.

4. **Generated files**: `diagnosticInformationMap.generated.ts` and `diagnosticMessages.generated.json` are auto-generated from `diagnosticMessages.json`. The DOM type definitions are also generated.

5. **Feature flags vs transforms**: Language features are implemented as AST transformations in `src/compiler/transformers/`. Each ES version gets its own file.
