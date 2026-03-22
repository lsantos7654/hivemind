# Biome — Build System

## Build System Overview

Biome uses a dual build system:
- **Rust/Cargo** for all core crate compilation (formatter, parser, analyzer, CLI, LSP, WASM)
- **pnpm** (Node.js package manager) for the TypeScript/JavaScript packages

The `justfile` (task runner using `just`) orchestrates common tasks combining both systems.

## Prerequisites

- Rust stable toolchain (pinned to 1.94.0 via `rust-toolchain.toml`)
- `rustup` with the `wasm32-unknown-unknown` target for WASM builds
- `just` task runner
- `pnpm` for Node.js packages
- `cargo-insta` for snapshot testing
- `wasm-bindgen-cli` (version 0.2.105) for WASM bindings generation
- `wasm-opt` for WASM size optimization

Install all development tools:
```bash
just install-tools
# Equivalent to:
cargo install cargo-binstall
cargo binstall cargo-insta wasm-opt
cargo binstall wasm-bindgen-cli --version 0.2.105
pnpm install
```

## Cargo Workspace Configuration

`Cargo.toml` at the root defines a workspace with:
- `members = ["crates/*", "xtask/codegen", "xtask/coverage", "xtask/glue", "xtask/rules_check"]`
- Resolver version 2
- All shared dependencies declared under `[workspace.dependencies]` and referenced with `{ workspace = true }` in member crates
- Edition 2024 for all crates
- Strict clippy lints applied workspace-wide via `[workspace.lints.clippy]` and `[workspace.lints.rust]`

### Build Profiles

| Profile | Purpose |
|---------|---------|
| `dev` | Debug builds with line-table-only debug info; packages use no debug |
| `release` | Production builds |
| `debugging` | Inherits dev but with full debug info |
| `release-with-debug` | Release with debug info for profiling |
| WASM-specific: `dev.package.biome_wasm` uses `opt-level = "s"`, `release.package.biome_wasm` uses `opt-level = 3` |

## Key Build Commands

### Building the CLI

```bash
# Debug build
cargo build -p biome_cli

# Release build
cargo build -p biome_cli --release
# Binary at: target/release/biome (or target/release/biome.exe on Windows)
```

### Building WASM

Three WASM targets are supported (bundler, nodejs, web):

```bash
# Development builds
just build-wasm-bundler-dev
just build-wasm-node-dev
just build-wasm-web-dev

# Release builds (includes wasm-opt optimization)
just build-wasm-bundler
just build-wasm-node
just build-wasm-web
```

Each WASM build:
1. `cargo build --lib --target wasm32-unknown-unknown -p biome_wasm`
2. `wasm-bindgen` to generate JS/TS bindings into `packages/@biomejs/wasm-{target}/`
3. `wasm-opt` (release only) to optimize the `.wasm` binary size with `-Os` flag

## Code Generation (`xtask`)

Code generation is critical in this codebase — many files are auto-generated and must not be edited manually.

```bash
# Run all code generators (rarely needed locally)
just gen-all
# This runs:
#   cargo run -p xtask_codegen -- all
#   just gen-configuration
#   just gen-migrate
#   just gen-bindings
#   just format

# Generate analyzer rule registries (registry.rs, lint.rs, assists.rs per language)
just gen-rules
# cargo run -p xtask_codegen -- analyzer

# Generate configuration structs and documentation
just gen-configuration
# cargo run -p xtask_codegen --features configuration -- configuration

# Generate ESLint migration code
just gen-migrate
# cargo run -p xtask_codegen --features configuration -- migrate-eslint

# Generate JSON schema for biome.json
just gen-schema
# cargo codegen-schema  (custom cargo alias)

# Generate TypeScript type bindings from Rust types
just gen-types
# cargo run -p xtask_codegen --features schema -- bindings

# Generate grammar code from .ungram files
just gen-grammar
# cargo run -p xtask_codegen -- grammar

# Generate formatter boilerplate for a language
just gen-formatter
# cargo run -p xtask_codegen -- formatter

# Generate CSS baseline data from web-features
just gen-css-baseline
# cargo run -p xtask_codegen --features xtask_codegen/external_data -- css-baseline

# Generate Tailwind CSS preset
just gen-tw   # (in packages/tailwindcss-config-analyzer)
```

## Testing

### Run All Tests

```bash
just test
# cargo test --no-fail-fast
```

### Test a Specific Crate

```bash
just test-crate biome_js_analyze
# cargo test -p biome_js_analyze --no-fail-fast
```

### Test a Specific Lint Rule

```bash
just test-lintrule noVar
# Runs the named rule across all analyze crates
```

### Snapshot Testing

Biome uses `insta` for snapshot-based tests. When output changes:
```bash
cargo insta review    # Interactive review of snapshot changes
cargo insta accept    # Accept all pending snapshot changes
```

Snapshot files live in `tests/snapshots/` or `src/snapshots/` within each crate.

### Quick Tests

```bash
just test-quick biome_js_parser
# cargo test -p biome_js_parser --test quick_test -- quick_test --nocapture --ignored
```

### Documentation Tests

```bash
just test-doc
# cargo test --doc
```

### Markdown Conformance

```bash
just test-markdown-conformance
# cargo run -p xtask_coverage -- --suites=markdown/commonmark
```

## Formatting and Linting

```bash
# Format Rust + TOML + JS/TS
just format
# cargo format && pnpm format

# Run clippy
just lint
# cargo lint

# Validate lint rule documentation
just lint-rules
# cargo run -p rules_check
```

## Creating New Lint Rules

The `justfile` provides scaffolding commands for new lint rules:

```bash
just new-js-lintrule MyRuleName       # Creates JS lint rule + runs gen-analyzer
just new-js-assistrule MyRuleName     # Creates JS assist rule
just new-css-lintrule MyRuleName
just new-json-lintrule MyRuleName
just new-graphql-lintrule MyRuleName
just new-html-lintrule MyRuleName
just move-rule MyRuleName targetGroup # Promotes rule from nursery to a stable group
```

## CI Readiness Check

Before submitting a PR, run the full CI pipeline locally:
```bash
just ready
# Runs: gen-all, documentation, lint, test, test-doc
# Also verifies no uncommitted changes remain after codegen
```

## Node.js Packages

The `pnpm-workspace.yaml` defines the workspace including all packages under `packages/`.

```bash
pnpm install          # Install all JS dependencies
pnpm format           # Format JS/TS files
pnpm changeset        # Create a changelog entry (or: just new-changeset)
```

## External Dependencies (Notable)

| Dependency | Version | Purpose |
|------------|---------|---------|
| `rayon` | 1.11 | Data parallelism for file traversal |
| `tokio` | 1.49 | Async runtime for LSP daemon |
| `tower-lsp-server` | 0.23 | LSP server framework |
| `bpaf` | 0.9.24 | CLI argument parsing |
| `schemars` | 1.2.1 | JSON schema generation |
| `serde` / `serde_json` | 1.x | Serialization |
| `insta` | 1.46 | Snapshot testing |
| `boa_engine` | 0.21 | JS engine for plugin execution |
| `grit-pattern-matcher` | 0.5.1 | GritQL pattern evaluation |
| `mimalloc` / `tikv-jemallocator` | — | Alternative allocators for performance |
| `crossbeam` | 0.8 | Lock-free data structures and channels |
| `dashmap` | 6.1 | Concurrent hash map |
| `smallvec` | 1.15 | Small-size-optimized Vec |
| `rustc-hash` | 2.1 | Fast non-cryptographic hashing |
