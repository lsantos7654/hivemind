# Ruff Build System

## Build System Type

Ruff uses **Cargo** (Rust's standard build system and package manager) as the primary build tool, organized as a **Cargo workspace** with 47 member crates. The Python package on PyPI is built using **Maturin**, which wraps Cargo to produce Python extension modules.

## Configuration Files

| File | Purpose |
|------|---------|
| `Cargo.toml` | Workspace root: member list, shared dependencies, build profiles |
| `Cargo.lock` | Exact dependency versions (checked in for reproducible builds) |
| `rust-toolchain.toml` | Pins Rust toolchain to version 1.92 |
| `pyproject.toml` | Python package metadata (Maturin build backend) |
| `clippy.toml` | Clippy lint rules for the workspace |

## Build Profiles

The workspace root defines several custom Cargo profiles beyond the defaults:

| Profile | Purpose | Key settings |
|---------|---------|--------------|
| `dev` (default) | Fast incremental compilation | Debug symbols, no optimization |
| `release` | Production binary | LTO=fat, opt-level=3, strip=true |
| `profiling` | Performance profiling | Release + debug info, LTO=off |
| `minimal-size` | Small binary footprint | opt-level='s', strip=true |
| `fast-test` | Rapid test iteration | opt-level=1, incremental |
| `dist` | Distribution builds | LTO=fat, single codegen unit |

## Key Dependencies

### Runtime Dependencies

| Crate | Version | Purpose |
|-------|---------|---------|
| `salsa` | workspace | Incremental computation / caching |
| `rayon` | workspace | Data parallelism for file processing |
| `clap` | workspace | CLI argument parsing |
| `serde` + `serde_json` | workspace | Serialization/deserialization |
| `toml` | workspace | TOML config parsing |
| `regex` | workspace | Regular expression support |
| `crossbeam` | workspace | Lock-free concurrency primitives |
| `dashmap` | workspace | Concurrent hash maps |
| `rustc-hash` | workspace | Fast non-cryptographic hashing |
| `bincode` | workspace | Binary serialization (cache format) |
| `glob` | workspace | File glob pattern matching |
| `ignore` | workspace | .gitignore-aware directory traversal |
| `colored` | workspace | Terminal color output |
| `insta` | workspace | Snapshot testing |
| `test-case` | workspace | Parameterized tests |
| `datatest-stable` | workspace | Data-driven tests |

### Platform-Specific Allocators

```toml
# Linux/macOS
[target.'cfg(all(not(target_family = "wasm"), not(target_os = "windows")))'.dependencies]
tikv-jemallocator = { version = "0.6" }

# Windows
[target.'cfg(target_os = "windows")'.dependencies]
mimalloc = { version = "0.1" }
```

### Python Binding Dependencies

| Crate | Purpose |
|-------|---------|
| `pyo3` | Rust/Python bindings for the Python package |
| `maturin` | Build tool for producing the Python wheel |

## Build Commands

### Standard Rust Builds

```bash
# Debug build (fast compilation)
cargo build

# Release build (optimized, for benchmarking/distribution)
cargo build --release

# Build specific crate
cargo build -p ruff

# Build with all features
cargo build --all-features
```

### Running Tests

```bash
# Run all tests (all crates)
cargo test

# Run tests with nextest (faster parallel runner, recommended)
cargo nextest run

# Run tests for a specific crate
cargo test -p ruff_linter

# Run tests with output visible
cargo test -- --nocapture

# Run a specific test by name
cargo test test_name

# Review snapshot test changes (after test output changes)
cargo insta review

# Accept all snapshot changes
cargo insta accept
```

### Linting and Code Quality

```bash
# Run clippy (must pass with zero warnings)
cargo clippy --workspace --all-targets --all-features -- -D warnings

# Format Rust code
cargo fmt --all

# Check formatting without modifying files
cargo fmt --all -- --check
```

### Development Utilities (`cargo dev`)

The `ruff_dev` crate provides development automation:

```bash
# Regenerate all auto-generated files (schema, rule docs, registry)
cargo dev generate-all

# Generate only the JSON schema
RUFF_UPDATE_SCHEMA=1 cargo test

# Regenerate rule documentation
cargo dev generate-rules-table

# Print the AST for a Python snippet (debugging)
cargo dev print-ast <file.py>

# Print tokens for a Python snippet
cargo dev print-tokens <file.py>

# Round-trip format testing
cargo dev format-dev --stability-check <path>
```

### Python Package Build

```bash
# Install Maturin
pip install maturin

# Build Python extension in-place (development)
maturin develop

# Build Python wheel for distribution
maturin build --release

# Install into current venv
maturin develop --release
```

### Fuzzing

```bash
# Run parser fuzzer
cd fuzz
cargo fuzz run fuzz_parse
```

### Benchmarking

```bash
# Run benchmarks
cargo bench

# Run with profiling profile
cargo bench --profile profiling
```

## How to Build the CLI Binary

```bash
# Build the ruff binary
cargo build --release -p ruff

# The binary will be at:
./target/release/ruff

# Or run directly with cargo
cargo run -p ruff -- check path/to/python/
cargo run -p ruff -- format path/to/python/
```

## How to Build the Python Package

```bash
# Prerequisites
pip install maturin

# Development install (builds debug mode, installs into current venv)
maturin develop

# Production wheel
maturin build --release
# Output: target/wheels/ruff-*.whl

# Install the wheel
pip install target/wheels/ruff-*.whl
```

## How to Run the Full CI Check Suite

Based on CONTRIBUTING.md patterns:

```bash
# 1. Rust checks
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo fmt --all -- --check
cargo test
cargo nextest run

# 2. Snapshot tests
cargo insta review  # Review any changed snapshots

# 3. Schema validation (ensures ruff.schema.json is up to date)
RUFF_UPDATE_SCHEMA=1 cargo test -- schema

# 4. Python checks (if modifying Python wrapper)
uvx pre-commit run -a
```

## Dependency Management

All dependency versions are centralized in the workspace `[workspace.dependencies]` section of root `Cargo.toml`. Individual crates reference them with `{ workspace = true }` to avoid version drift across the monorepo.

The workspace uses **Resolver version 2** (`resolver = "2"`) for improved feature unification behavior.

## CI/CD

GitHub Actions workflows in `.github/workflows/` handle:
- Cross-platform builds (Linux, macOS, Windows)
- Tests on multiple Rust versions
- Python wheel building for all platforms via Maturin
- Publishing to PyPI on tag push
- Documentation deployment
