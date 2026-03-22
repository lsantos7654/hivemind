# Biome — Repository Summary

## Purpose and Goals

Biome is a high-performance, unified toolchain for web development written entirely in Rust. It aims to replace multiple JavaScript ecosystem tools — primarily Prettier (formatter), ESLint (linter), and related utilities — with a single, fast, and well-integrated tool. The project's tagline is "one toolchain for your web project," and it targets developers who want formatting, linting, and code transformation without the overhead of running separate Node.js-based tools.

Biome is the successor to Rome Tools and was forked and rebranded in 2023. The repository lives at `github.com/biomejs/biome` and the tool is published as `@biomejs/biome` on npm.

## Key Features and Capabilities

- **Multi-language support**: JavaScript, TypeScript, JSX, TSX, JSON, JSONC, CSS, GraphQL, HTML (experimental), YAML (experimental), Markdown (experimental), and GritQL pattern language.
- **Formatter**: Fast, opinionated code formatter comparable to Prettier with high compatibility for JS/TS/CSS/JSON/GraphQL. Produces deterministic output and has an IR-based design.
- **Linter**: Hundreds of lint rules organized into categories (a11y, complexity, correctness, nursery, performance, security, style, suspicious). Rules support auto-fix and safe/unsafe fix modes.
- **Analyzer / Assist**: Code actions beyond simple lint fixes, including import organization (organize imports), unused suppression detection, and GritQL-based code search/transformation.
- **LSP Server**: Full Language Server Protocol implementation (using `tower-lsp-server`) for editor integration via VS Code extension and other LSP-compatible editors.
- **Daemon mode**: Persistent background server process (started with `biome start`) that caches workspace state for fast incremental processing.
- **WASM build**: `biome_wasm` crate compiles Biome's workspace API to WebAssembly, enabling use in browser-based tools (e.g., the online playground at `biomejs.dev/playground`).
- **JS API**: `@biomejs/js-api` npm package wraps the WASM build for programmatic use from JavaScript/TypeScript.
- **JSON RPC backend**: `@biomejs/backend-jsonrpc` enables TypeScript clients to communicate with the Biome daemon over JSON RPC.
- **Migration support**: `biome migrate` command with subcommands for migrating from ESLint, Prettier, and between Biome versions.
- **GritQL search**: `biome search` command supporting pattern-based code search using the GritQL language.
- **Plugin system**: Early-stage plugin support via GritQL-based plugins (`.grit` files).
- **VCS integration**: Optional git integration to apply operations only to changed files.

## Primary Use Cases and Target Audience

- Front-end and full-stack web developers who want a single, zero-config (or minimal-config) tool replacing ESLint + Prettier.
- CI pipelines needing fast, consistent formatting and linting checks.
- Editor/IDE integrations via the LSP.
- Build tool integrations via the WASM or JS API.
- Developers migrating from ESLint or Prettier configurations.

## High-Level Architecture

Biome is organized as a Rust Cargo workspace with ~90 crates plus Node.js packages. The key layers are:

1. **Syntax layer** (`biome_rowan`, per-language `*_syntax` and `*_factory` crates): Lossless, immutable green/red tree representation (inspired by rust-analyzer's `rowan`). Every language has its own syntax node types.
2. **Parser layer** (per-language `*_parser` crates): Error-tolerant, lossless parsers that produce the syntax tree. The JS parser also handles TypeScript, JSX.
3. **Semantic layer** (per-language `*_semantic` crates): Binding resolution, scope analysis, control flow graphs.
4. **Formatter layer** (`biome_formatter` + per-language `*_formatter` crates): IR-based formatter with `FormatElement` IR nodes.
5. **Analyzer layer** (`biome_analyze` + per-language `*_analyze` crates): Lint rules and assist actions, using the `Rule` trait with optional code actions.
6. **Service layer** (`biome_service`): The `Workspace` trait — the central API for CLI and LSP, managing open documents, settings, and dispatching to parsers/formatters/analyzers.
7. **CLI layer** (`biome_cli`): Command-line interface using `bpaf` for argument parsing, traversal engine for batch file processing.
8. **LSP layer** (`biome_lsp`): Language Server implementation bridging LSP protocol to the `Workspace` API.
9. **WASM layer** (`biome_wasm`): `wasm-bindgen` bindings exposing the Workspace API to JavaScript.
10. **Configuration** (`biome_configuration`): Strongly-typed configuration deserialization for `biome.json`, including overrides and extends.

## Related Projects and Dependencies

- **rome**: The predecessor project (archived).
- **rowan**: Biome forks this as `biome_rowan` for its green/red tree infrastructure.
- **GritQL / grit-pattern-matcher**: Pattern language used for code search; integrated via the `biome_grit_patterns` crate.
- **boa_engine**: JavaScript engine used to execute plugin scripts.
- **tower-lsp-server**: Async LSP server framework.
- **bpaf**: Argument parsing library for the CLI.
- **wasm-bindgen**: Rust-to-WASM bindings generation.
- **schemars**: JSON Schema generation for the configuration schema.
- **insta**: Snapshot testing framework used extensively for parser/formatter/analyzer tests.
- **rayon**: Data parallelism for multi-threaded file traversal.
