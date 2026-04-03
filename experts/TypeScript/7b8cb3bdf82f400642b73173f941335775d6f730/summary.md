# TypeScript — Repository Summary

## Repository Purpose and Goals

TypeScript (`microsoft/TypeScript`) is Microsoft's open-source, statically typed superset of JavaScript. Its core purpose is to add optional static type checking to JavaScript, enabling developers to catch type errors at compile time rather than at runtime. TypeScript compiles ("transpiles") to plain JavaScript that runs in any browser or Node.js environment.

The repository contains the TypeScript compiler, language service, and tsserver — the full toolchain needed to build, check, and provide IDE support for TypeScript code.

**Important status note (as of commit 7b8cb3b):** TypeScript 6.0 is the *last JavaScript-based release*. Future TypeScript development (7.0+) is happening in a Go-based rewrite at `microsoft/typescript-go`. This repository is in maintenance mode — only critical crash fixes, security issues, and serious regressions are accepted.

## Key Features and Capabilities

- **Static type checking**: Interfaces, type aliases, union/intersection types, generics, conditional types, mapped types, template literal types, and more
- **Modern JavaScript transpilation**: Transforms ESNext syntax (decorators, async/await, generators, optional chaining, nullish coalescing) to older targets (ES5, ES2015, etc.)
- **Module system support**: CommonJS, ESModules, AMD, SystemJS, UMD, and Node16/NodeNext module resolution strategies
- **JSX/TSX support**: Compiles React JSX and other JSX flavors
- **Declaration files** (`.d.ts`): Generates type declaration files for libraries
- **Incremental compilation**: Builder programs with `.tsbuildinfo` for fast rebuilds
- **Project references**: Composite projects supporting large monorepos
- **Watch mode**: Automatic recompilation on file changes
- **Language service API**: Powers IDE features such as IntelliSense, go-to-definition, find all references, rename symbol, code fixes, and refactoring
- **tsserver**: A persistent server process used by editors (VS Code, Neovim, Emacs, etc.) over the Language Server Protocol (LSP) and its own JSON protocol
- **Type acquisition**: Automatic fetching of `@types/*` definitions
- **Standard library**: Comprehensive `.d.ts` type definitions covering ES5 through ESNext, DOM, WebWorker, and Node.js APIs

## Primary Use Cases and Target Audience

- **Application developers** who want type safety and IDE tooling for large JavaScript codebases
- **Library authors** who publish `.d.ts` type definitions for consumers
- **Build tooling authors** integrating the TypeScript compiler API into bundlers (webpack, Rollup, esbuild, Vite)
- **IDE/editor plugin authors** using `createLanguageService` or tsserver for editor features
- **Framework authors** (Angular, NestJS, etc.) using decorators and other TypeScript-specific features
- **JavaScript developers** seeking gradual adoption via `allowJs`, `checkJs`, and JSDoc type annotations

## High-Level Architecture Overview

The codebase is organized as a TypeScript monorepo with multiple packages compiled with project references:

1. **Compiler core** (`src/compiler/`): The heart of TypeScript — scanner, parser, binder, type checker, emitter, transformers, and program creation. ~100k+ lines. The type checker alone (`checker.ts`) is ~54,000 lines.

2. **Language Services** (`src/services/`): Higher-level editor services built on top of the compiler — completions, go-to-definition, find references, rename, diagnostics, code fixes, refactoring, inlay hints, formatting, etc. Exposes the `LanguageService` interface.

3. **tsserver** (`src/server/`): The persistent server process that wraps the language service and communicates with editors over JSON-based protocol or LSP. Handles project management, file watching, and multi-project sessions.

4. **tsc** (`src/tsc/`): The command-line compiler entry point. Delegates to `executeCommandLine`.

5. **Standard Library** (`src/lib/`): TypeScript's built-in `.d.ts` type definitions for JavaScript environments (ES5 through ESNext, DOM, WebWorker).

6. **Test Harness** (`src/harness/`): Infrastructure for running compiler conformance tests, fourslash tests, and project tests.

7. **Deprecated compatibility layer** (`src/deprecatedCompat/`): Re-exports with deprecation shims for the public API.

8. **Typings installer** (`src/typingsInstaller/`, `src/typingsInstallerCore/`): Automatically acquires `@types/*` packages for JavaScript projects.

The compilation pipeline flows: **Source text → Scanner (tokenizer) → Parser (AST) → Binder (symbol table) → Type Checker → Transformer → Emitter (JavaScript output)**.

## Related Projects and Dependencies

- **[microsoft/typescript-go](https://github.com/microsoft/typescript-go)**: The Go-based rewrite that will become TypeScript 7.0. This is where new features and general bug fixes should be submitted.
- **[DefinitelyTyped](https://github.com/DefinitelyTyped/DefinitelyTyped)**: Community-maintained `@types/*` type definitions
- **[tslib](https://github.com/microsoft/tslib)**: Runtime helpers emitted by TypeScript (`tslib` dev dependency)
- **[hereby](https://github.com/nicolo-ribaudo/hereby)**: The task runner used instead of Gulp for builds
- **[dprint](https://dprint.dev/)**: Formatter used to enforce code style
- **[esbuild](https://esbuild.github.io/)**: Used internally for bundling the language service for certain targets
