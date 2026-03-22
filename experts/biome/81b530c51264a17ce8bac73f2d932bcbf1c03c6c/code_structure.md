# Biome — Code Structure

## Top-Level Layout

```
biome/
├── Cargo.toml                  # Workspace manifest; lists all crate members and shared deps
├── Cargo.lock
├── rust-toolchain.toml         # Pins Rust toolchain (1.94.0); also targets wasm32-unknown-unknown
├── justfile                    # Task runner (just); defines build, test, codegen, format targets
├── .biome.json                 # Biome's own configuration for linting/formatting JS/TS in the repo
├── rustfmt.toml                # Rust formatting config
├── clippy.toml                 # Clippy lint configuration
├── package.json                # Root pnpm workspace config for JS packages
├── pnpm-workspace.yaml         # Lists JS package workspace members
├── crates/                     # All Rust crates (~90 crates)
├── xtask/                      # Code generation and tooling crates
├── packages/                   # Node.js/TypeScript packages
├── benchmark/                  # Benchmark scripts vs Prettier/ESLint
├── scripts/                    # Miscellaneous shell scripts
└── plugins/                    # Example GritQL plugin files
```

## `crates/` — Rust Crate Organization

Crates follow a consistent naming pattern: `biome_<language>_<component>` or `biome_<component>`.

### Core Infrastructure Crates

| Crate | Purpose |
|-------|---------|
| `biome_rowan` | Lossless green/red syntax tree library (fork of `rowan`). Provides `SyntaxNode`, `SyntaxToken`, `AstNode` traits |
| `biome_text_size` | `TextSize` and `TextRange` types for byte-offset tracking |
| `biome_text_edit` | `TextEdit` type representing a list of atomic text changes |
| `biome_line_index` | Line/column ↔ byte-offset conversion |
| `biome_unicode_table` | Unicode property tables for the lexer |
| `biome_string_case` | String case conversion utilities (camelCase, snake_case, etc.) |
| `biome_fs` | `FileSystem` abstraction (`OsFileSystem`, `MemoryFileSystem`) |
| `biome_glob` | Glob pattern matching for file inclusion/exclusion |
| `biome_console` | Console output formatting with markup and color support |
| `biome_markup` | Markup language for styled terminal output |
| `biome_diagnostics` | Core diagnostic types, rendering, and display |
| `biome_diagnostics_categories` | Diagnostic category registry and macros |
| `biome_diagnostics_macros` | Proc macros for `#[derive(Diagnostic)]` |
| `biome_suppression` | Suppression comment parsing (`// biome-ignore`) |
| `biome_flags` | Feature flags for experimental features |

### Parser Infrastructure

| Crate | Purpose |
|-------|---------|
| `biome_parser` | Base parser infrastructure: `Parser` trait, event-based parsing, error recovery utilities |
| `biome_ungrammar` | Parser for `.ungram` grammar definition files |

### Formatter Infrastructure

| Crate | Purpose |
|-------|---------|
| `biome_formatter` | Core formatter IR (`FormatElement`), `Format`/`FormatRule` traits, `Printer` |
| `biome_formatter_test` | Shared test utilities for formatter snapshot tests |

### Analyzer Infrastructure

| Crate | Purpose |
|-------|---------|
| `biome_analyze` | Core analyzer: `Rule` trait, `RuleCategories`, `AnalysisFilter`, `ControlFlowGraph` |
| `biome_analyze_macros` | Proc macros: `#[rule]`, `#[action]` attributes for rule definitions |
| `biome_control_flow` | Control flow graph construction and analysis |
| `biome_aria` | WAI-ARIA specification data for accessibility rules |
| `biome_aria_metadata` | Generated ARIA metadata tables |
| `biome_rule_options` | Types for configurable rule options |
| `biome_ruledoc_utils` | Utilities for lint rule documentation validation |

### Configuration

| Crate | Purpose |
|-------|---------|
| `biome_configuration` | Strongly-typed `biome.json` configuration deserialization; also houses generated rule configs |
| `biome_configuration_macros` | Proc macros for configuration derive |
| `biome_deserialize` | Custom deserialization framework (not using serde directly for config) |
| `biome_deserialize_macros` | `#[derive(Deserializable)]` and `#[derive(Merge)]` macros |

### Service and CLI

| Crate | Purpose |
|-------|---------|
| `biome_service` | `Workspace` trait + `WorkspaceServer` implementation; central API for all tooling |
| `biome_cli` | CLI entry point: command parsing, traversal engine, reporters |
| `biome_lsp` | Language Server Protocol implementation using `tower-lsp-server` |
| `biome_lsp_converters` | Conversions between LSP types and Biome internal types |
| `biome_module_graph` | Module graph tracking imports/exports for cross-file analysis |
| `biome_project_layout` | Project structure detection (monorepos, `package.json` discovery) |
| `biome_package` | Package manifest parsing (`package.json`, `tsconfig.json`) |
| `biome_resolver` | Module specifier resolution (Node.js-style) |
| `biome_migrate` | Configuration migration analyzers (ESLint → Biome, version upgrades) |
| `biome_plugin_loader` | Plugin system: loads `.grit` plugin files |
| `biome_wasm` | WASM bindings via `wasm-bindgen` exposing the Workspace API to JS |

### Language-Specific Crates (per-language pattern)

Each supported language follows the pattern `biome_<lang>_{syntax,factory,parser,formatter,analyze,semantic}`:

**JavaScript / TypeScript / JSX / TSX** (most complete):
- `biome_js_syntax` — all AST node types for JS/TS/JSX
- `biome_js_factory` — AST node factory/builder functions
- `biome_js_parser` — extremely fast, error-tolerant JS/TS/JSX parser
- `biome_js_formatter` — JS/TS/JSX formatter
- `biome_js_analyze` — JS/TS lint rules (a11y, complexity, correctness, nursery, performance, security, style, suspicious)
- `biome_js_semantic` — binding, scope, and semantic model for JS/TS
- `biome_js_runtime` — JS runtime utilities (globals, environments)
- `biome_js_transform` — code transformations (distinct from lint fixes)
- `biome_js_type_info` — type inference system for JS/TS
- `biome_js_type_info_macros` — proc macros for type info
- `biome_jsdoc_comment` — JSDoc comment parsing

**CSS**: `biome_css_{syntax,factory,parser,formatter,analyze,semantic}`

**JSON**: `biome_json_{syntax,factory,parser,formatter}`, `biome_json_analyze`, `biome_json_value`

**GraphQL**: `biome_graphql_{syntax,factory,parser,formatter,analyze,semantic}`

**HTML** (experimental): `biome_html_{syntax,factory,parser,formatter,analyze}`

**YAML** (experimental): `biome_yaml_{syntax,factory,parser,formatter}`

**Markdown** (experimental): `biome_markdown_{syntax,factory,parser,formatter}`

**GritQL** (pattern language): `biome_grit_{syntax,factory,parser,formatter}`, `biome_grit_patterns`

**Tailwind CSS** (utility class sorting): `biome_tailwind_{syntax,factory,parser}`

## `xtask/` — Code Generation Tools

```
xtask/
├── codegen/    # Main code generator: run via `cargo run -p xtask_codegen`
│               # Generates: analyzer rule registries, configuration structs,
│               # grammar code, TypeScript bindings, JSON schema, ESLint migrators
├── coverage/   # Coverage test runner (CommonMark conformance, etc.)
├── glue/       # Shared utilities for xtask crates
└── rules_check/ # Validates lint rule documentation quality
```

## `packages/` — Node.js/TypeScript Packages

```
packages/
├── @biomejs/
│   ├── biome/               # Main npm package (CLI binary wrapper)
│   ├── backend-jsonrpc/     # TypeScript JSON RPC client for the daemon
│   │   └── src/workspace.ts # Auto-generated workspace API types
│   ├── js-api/              # High-level JS/TS API wrapping WASM
│   │   └── src/
│   │       ├── common.ts    # BiomeCommon class (formatContent, lintContent, etc.)
│   │       ├── index.ts     # Biome class with Distribution enum
│   │       ├── nodejs.ts    # Node.js-specific Biome class
│   │       ├── bundler.ts   # Bundler-specific Biome class
│   │       └── web.ts       # Web-specific Biome class
│   ├── wasm-bundler/        # WASM build for bundlers (auto-generated)
│   ├── wasm-nodejs/         # WASM build for Node.js (auto-generated)
│   ├── wasm-web/            # WASM build for browser (auto-generated)
│   ├── cli-darwin-arm64/    # Platform-specific CLI binary packages
│   ├── cli-darwin-x64/
│   ├── cli-linux-arm64/
│   ├── cli-linux-x64/
│   ├── cli-win32-arm64/
│   └── cli-win32-x64/
├── aria-data/               # ARIA specification data (JS)
├── prettier-compare/        # Tool for comparing Biome and Prettier output
└── tailwindcss-config-analyzer/ # Generates Tailwind preset for import sorting
```

## Key Source Files

| File | Role |
|------|------|
| `crates/biome_service/src/workspace.rs` | Defines the `Workspace` trait — the central API surface |
| `crates/biome_service/src/lib.rs` | `App` struct and `WorkspaceRef` enum |
| `crates/biome_cli/src/lib.rs` | `CliSession` struct; dispatches commands |
| `crates/biome_cli/src/commands/mod.rs` | `BiomeCommand` enum and `biome_command()` function |
| `crates/biome_formatter/src/lib.rs` | `Format`, `FormatRule`, `FormatElement` — core formatter traits |
| `crates/biome_rowan/src/lib.rs` | Syntax tree foundation |
| `crates/biome_analyze/src/lib.rs` | `Rule` trait and analyzer infrastructure |
| `crates/biome_configuration/src/lib.rs` | `Configuration` struct (top-level biome.json shape) |
| `crates/biome_wasm/src/lib.rs` | WASM-exposed `Workspace` struct |
| `packages/@biomejs/js-api/src/common.ts` | `BiomeCommon` class — JS API entry point |

## Code Organization Patterns

- **Per-language crate groups**: Each language has 4–7 crates (syntax, factory, parser, formatter, analyze, semantic). This keeps compilation units small and enforces clean layering.
- **Generated code**: Many files in `*_analyze` crates (`registry.rs`, `assists.rs`, `lint.rs`) are generated by `xtask_codegen`. Never edit these directly.
- **Snapshot testing with `insta`**: Parsers, formatters, and analyzers use `.snap` files in `tests/snapshots/` or `src/snapshots/` directories. Update with `cargo insta review`.
- **Spec test pattern**: Lint rules have `tests/specs/<rule_category>/<rule_name>/` directories with input files. Test output is captured as snapshots.
- **Ungram grammars**: Language grammars are defined in `.ungram` files (e.g., `crates/biome_js_syntax/src/generated/js.ungram`) and used to generate syntax node code.
