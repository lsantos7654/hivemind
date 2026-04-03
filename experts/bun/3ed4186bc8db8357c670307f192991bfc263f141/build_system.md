# Bun — Build System

## Build System Type

Bun uses the **Zig build system** (`build.zig`) as its primary build orchestrator. The Zig build system handles compilation of all Zig and C/C++ source files, cross-compilation targets, feature flags, and linking. JavaScriptCore (the JS engine) is pre-built separately using CMake and provided as a static library.

## Configuration Files

| File | Purpose |
|------|---------|
| `build.zig` | Root Zig build file — all targets, options, cross-compilation |
| `package.json` | NPM workspace root — dev tooling scripts and workspace config |
| `tsconfig.base.json` | Base TypeScript compiler config |
| `tsconfig.json` | Workspace TypeScript config |
| `.buildkite/` | CI/CD pipeline definitions |
| `CMakeLists.txt` | CMake configuration for building JavaScriptCore |

## Build Profiles

Bun supports multiple build profiles controlled by `--profile` or script aliases:

| Profile | Description | Use Case |
|---------|-------------|----------|
| `debug` | Unoptimized, assertions enabled, debug allocator | Day-to-day development |
| `debug-local` | Debug with locally built WebKit | Working on JSC bindings |
| `release` | Fully optimized, size-minimized | Production releases |
| `release-local` | Release with locally built WebKit | Performance profiling |
| `debug-no-asan` | Debug without AddressSanitizer | Faster debug builds |
| `release-asan` | Release with ASAN | Memory safety CI |

## Build Commands

All commands are run from the repository root using Bun (or Node.js):

```bash
# Quick debug build (shorthand)
bun bd

# Full debug build
bun run build:debug

# Release build (production)
bun run build:release

# CI release build
bun run build:ci

# ASAN (AddressSanitizer) build for memory leak detection
bun run build:asan

# Debug build with local WebKit
bun run build:local

# Release build with local WebKit
bun run build:release:local

# Incremental compilation (watch mode)
bun run watch

# Zig type/syntax check without compiling
bun run zig:check

# Build JavaScriptCore only
bun run jsc:build
```

## Running Tests

```bash
# Run a specific test file with debug build
bun bd test <path-to-test-file>

# Run tests matching a pattern (fuzzy match)
bun bd test <pattern>

# Run tests matching a name filter
bun bd test -t "filter string"

# Run in watch mode
bun bd test --watch

# Run with release build
bun run test

# Run Node.js compatibility tests
bun run node:test

# Run with coverage
bun bd test --coverage
```

## Code Formatting and Linting

```bash
# Format TypeScript/JavaScript (prettier)
bun run fmt

# Format Zig code
bun run fmt:zig

# Lint JavaScript/TypeScript (oxlint)
bun run lint

# Clean all build artifacts
bun run clean
```

## External Dependencies

### Compiled into the Binary

| Dependency | Purpose | Notes |
|------------|---------|-------|
| JavaScriptCore | JS engine | Pre-built static library from WebKit |
| mimalloc | Memory allocator | Production builds; fast general allocator |
| SQLite | Embedded database | Bundled SQLite for `bun:sqlite` |
| BoringSSL / OpenSSL | TLS/crypto | TLS for fetch, Bun.serve HTTPS |
| zlib | Compression | gzip, deflate |
| zstd | Compression | `bun:zstd` module |
| LZMA | Compression | Decompression support |
| lol_html | HTML rewriting | Cloudflare's Rust-based HTMLRewriter |
| µSockets | WebSocket transport | Low-level socket primitives |
| µWebSockets | WebSocket server | High-performance WS |
| capstone | Disassembler | Debug and profiling builds only |
| Tracy | Profiler | Optional profiling integration |

### Development-Only Dependencies (package.json)

| Package | Purpose |
|---------|---------|
| `typescript` 6.0.2 | Type checking TypeScript sources |
| `esbuild` | Bundling build scripts |
| `react` + `react-dom` | JSX testing |
| `prettier` | Code formatting |
| `oxlint` | Fast JavaScript linter |
| `@types/node` | Node.js type definitions |

## Build Targets

### Platform Targets

Bun supports 4 primary platforms:

| Platform | Architectures | Notes |
|----------|---------------|-------|
| Linux | x86_64, aarch64 | Minimum kernel 5.1 (recommended 5.6+) |
| macOS | x86_64 (Intel), aarch64 (Apple Silicon) | Minimum macOS 13.0 |
| Windows | x86_64, aarch64 | Minimum Windows 10 RS5 (Build 1809) |
| WebAssembly | wasm32 | `bun-wasm` package |

### CPU Feature Variants

On x86_64, Bun ships multiple binary variants:

| Variant | CPU Features | Use Case |
|---------|-------------|----------|
| `bun` (default) | AVX2 + BMI + LZCNT | Modern CPUs (2013+) |
| `bun-baseline` | SSE4.2 only | Older CPUs, VMs, CI |

The baseline build is automatically selected at runtime if AVX2 is not detected.

### Build Outputs

| Profile | Output Path |
|---------|-------------|
| debug | `./build/debug/bun-debug` |
| release | `./build/release/bun` |

## How the Build Works

### 1. Zig Compilation Phase
`build.zig` orchestrates compilation:
- Reads build options (`--profile`, `--build-type`, feature flags)
- Compiles all Zig source files in `src/`
- Compiles C++ files in `src/bun.js/bindings/` using Zig's C++ compilation support
- Links against pre-built JavaScriptCore static library

### 2. JavaScript Built-in Bundling
Built-in JavaScript/TypeScript modules in `src/js/` are bundled and embedded into the Zig binary as byte arrays. This happens during the build process and makes all `bun:*` and `node:*` modules available without filesystem access.

### 3. Code Generation (Bindgen)
`.classes.ts` files are processed to generate Zig and C++ glue code for JavaScript class bindings. This happens before Zig compilation and the outputs are checked into the repository.

### 4. Linking
The final binary is statically linked, producing a single executable with no runtime shared library dependencies (except system libraries like libc on Linux).

## CI/CD Pipeline

Bun uses **Buildkite** for CI/CD, defined in `.buildkite/`:

- Separate pipelines per platform (Linux, macOS, Windows)
- Parallel compilation across multiple instances
- Test execution across multiple Linux distributions
- Release artifact publishing to GitHub releases and the CDN
- Benchmark tracking for performance regressions
- ASAN builds for memory safety validation

## Special Build Flags

```bash
# Build with AddressSanitizer
zig build --profile release-asan

# Build with Fuzzilli fuzzing support
zig build --fuzzilli

# Build with verbose logging even in release
zig build --logs

# Control optimization level
zig build --build-type MinSizeRel
zig build --build-type RelWithDebInfo
```

## Dependency Management for Development

Bun uses itself as its package manager for the development workspace. Running `bun install` in the repository root will install all TypeScript tooling dependencies. The `bun.lock` file tracks exact versions.

For the compiled C/C++ dependencies (JSC, mimalloc, etc.), Bun downloads pre-built artifacts as part of the build process rather than building them from source each time. Building JavaScriptCore from source is reserved for `build:local` variants.
