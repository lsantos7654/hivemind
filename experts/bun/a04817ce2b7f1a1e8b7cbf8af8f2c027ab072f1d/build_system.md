# Bun — Build System

## Build System Type and Configuration Files

Bun uses **CMake** as its primary build orchestrator, with **Zig** as the main compiler for Zig source, **Clang/LLVM** for C++ code, and **Rust** for native plugin components. The build is bootstrapped by a pre-installed `bun` binary (used for code generation scripts).

Key configuration files:
- **`CMakeLists.txt`** — Root CMake file. Parses version from `package.json`, sets C++23 standard, includes all tool setup and target modules.
- **`cmake/targets/BuildBun.cmake`** — Main build target definition. Declares all C/C++ dependencies, codegen steps, Zig compilation, and linking.
- **`cmake/tools/`** — Tool setup modules:
  - `SetupLLVM.cmake` — Requires LLVM 21.1.8 (enforced; mismatches cause runtime failures)
  - `SetupZig.cmake` — Auto-downloads and pins the Zig compiler version
  - `SetupRust.cmake` — Rust toolchain setup (pinned via `rust-toolchain.toml`)
  - `SetupBun.cmake` — Requires a pre-installed `bun` for codegen
  - `SetupEsbuild.cmake` — esbuild for JS bundling during build
  - `SetupWebKit.cmake` — Optional: clone/build WebKit/JSC locally
  - `SetupCcache.cmake` — Optional ccache integration
- **`cmake/targets/`** — Per-dependency build targets:
  - `BuildBoringSSL.cmake`, `BuildBrotli.cmake`, `BuildCares.cmake`, `BuildHighway.cmake`, `BuildLibDeflate.cmake`, `BuildLolHtml.cmake`, `BuildLshpack.cmake`, `BuildMimalloc.cmake`, `BuildZlib.cmake`, `BuildLibArchive.cmake`, `BuildHdrHistogram.cmake`, `BuildZstd.cmake`, `BuildTinyCC.cmake`, `BuildSQLite.cmake`, `BuildLibuv.cmake`
- **`build.zig`** — Zig build file (used for Zig-specific compilation options)
- **`package.json`** — Defines `bun run build`, `bun run build:release`, `bun run build:local`, `bun bd` (debug build + run), and other convenience scripts
- **`bunfig.toml`** — Bun runtime configuration for the build process itself
- **`rust-toolchain.toml`** — Pins the Rust toolchain version
- **`flake.nix`** / **`shell.nix`** — Nix flake for reproducible dev environment

## External Dependencies and Management

All C/C++ dependencies are built from source by CMake (fetched via `FetchContent` or git submodules):

| Dependency | Purpose |
|---|---|
| **BoringSSL** | TLS/SSL (replaces OpenSSL) |
| **Brotli** | Brotli compression |
| **c-ares** | Async DNS resolution |
| **Highway** | SIMD utilities |
| **libdeflate** | Fast DEFLATE/zlib |
| **lol_html** (LolHtml) | HTML rewriting (Cloudflare's Rust library) |
| **lshpack** | HPACK encoder/decoder for HTTP/2 |
| **mimalloc** | High-performance memory allocator |
| **zlib** | zlib compression |
| **libarchive** | Archive extraction (tar, zip, etc.) |
| **HdrHistogram** | Histogram for performance metrics |
| **zstd** | Zstandard compression |
| **TinyCC** | JIT C compiler for `bun:ffi` (disabled on Windows ARM64) |
| **SQLite** | Embedded SQL database for `bun:sqlite` |
| **libuv** | Async I/O (Windows only; POSIX uses native syscalls) |
| **JavaScriptCore (JSC)** | JavaScript engine (pre-built binary; optional local build) |
| **uWebSockets (uWS)** | HTTP/WebSocket server (via `packages/bun-uws/`) |
| **uSockets** | Socket layer for uWS (via `packages/bun-usockets/`) |

JavaScript/TypeScript dependencies are managed by `bun install` using `bun.lock` (text lockfile) and `bun.lockb` (binary lockfile).

Rust dependencies are managed by Cargo (`Cargo.toml` in `packages/bun-native-bundler-plugin-api/` and `packages/bun-native-plugin-rs/`).

## Build Targets and Commands

### Primary build commands (via `package.json` scripts)

```bash
bun run build           # Debug build → ./build/debug/bun-debug
bun run build:release   # Release build → ./build/release/bun
bun run build:release:asan  # Release + AddressSanitizer
bun run build:local     # Debug build with local WebKit/JSC
bun bd <args>           # Build debug + run (e.g., bun bd test foo.test.ts)
```

### CMake build variants

The `cmake/targets/BuildBun.cmake` defines several binary variants:
- `bun-debug` — Debug build (default for development)
- `bun-profile` — Profile build (release with debug info)
- `bun` — Stripped release build
- `bun-asan` — AddressSanitizer build
- `bun-valgrind` — Valgrind build
- `bun-asan-valgrind` — Combined ASAN + Valgrind
- `bun-assertions` — Release with assertions enabled
- `bun-*-test` — Test variants (any of the above + `-test` suffix)

### Codegen steps (run automatically during build)

Several TypeScript scripts run during the build to generate C++ and Zig glue code:

- **`src/codegen/generate-classes.ts`** — Reads `**/*.classes.ts` files and generates `ZigGeneratedClasses*` (C++ ↔ Zig bindings for JSC classes)
- **`src/codegen/generate-jssink.ts`** — Generates `JSSink.cpp`/`.h` for ReadableStream sinks
- **`src/codegen/cppbind.ts`** — Generates Zig bindings for C++ functions marked `[[ZIG_EXPORT]]`
- **`src/codegen/bundle-modules.ts`** — Bundles built-in JS modules (`node:fs`, `bun:ffi`, etc.) into the binary
- **`src/codegen/bundle-functions.ts`** — Bundles globally-accessible JS functions (ReadableStream, WritableStream, etc.)
- **Bindgen v2** (`*.bind.ts`, `*.bindv2.ts`) — Generates type-safe JS↔Zig conversion code

Codegen output goes to `./build/debug/codegen/` (or `./build/release/codegen/`). In release/CI builds, codegen files are embedded in the binary (`CODEGEN_EMBED=ON`). In development, they are read from disk at runtime (enabling faster iteration on JS built-ins without full Zig recompilation).

## How to Build

### Prerequisites

1. **LLVM 21.1.8** — Required. Install via Homebrew (`brew install llvm@21`), apt, or manually.
2. **A pre-installed `bun`** — Required for codegen scripts. Install via `curl -fsSL https://bun.com/install | bash`.
3. **Rust** — Required for native plugin components. Pinned via `rust-toolchain.toml`.
4. **CMake ≥ 3.24**, **Ninja**, **Go**, **Ruby** — Build tooling.
5. **ccache** (optional) — Speeds up incremental C++ builds.
6. **Zig** — Auto-downloaded by `SetupZig.cmake`; no manual install needed.

### Build steps

```bash
# Clone the repository
git clone https://github.com/oven-sh/bun
cd bun

# Install JS dependencies (needed for codegen scripts)
bun install

# Debug build (recommended for development)
bun run build
# Binary: ./build/debug/bun-debug

# Release build
bun run build:release
# Binary: ./build/release/bun

# Nix alternative (reproducible environment)
nix develop
export CMAKE_SYSTEM_PROCESSOR=$(uname -m)
bun bd
```

### Testing

```bash
bun test                          # Run all tests with bun test runner
bun run build && bun-debug test   # Run tests with debug build
bun bd test foo.test.ts           # Run specific test file with debug build
```

The test suite lives in `test/`. Tests use `bun:test` (Jest-compatible API).

### Deploying / Installing

```bash
# Install from the official install script
curl -fsSL https://bun.com/install | bash

# Upgrade an existing installation
bun upgrade

# Upgrade to canary (latest main commit)
bun upgrade --canary

# Install via npm
npm install -g bun

# Install via Homebrew
brew tap oven-sh/bun && brew install bun

# Docker
docker pull oven/bun
```

### Development workflow tips

- **Zig changes**: ~2.5 min rebuild. Batch changes; use the debugger (CodeLLDB in VSCode).
- **JS built-in changes** (`src/js/**/*.ts`): Run `bun run build` — much faster than Zig recompilation.
- **C++ changes**: Faster than Zig (C++ is many compilation units vs. Zig's single unit).
- **Debug logging**: `BUN_DEBUG_<scope>=1` enables scoped debug logs. `BUN_DEBUG_QUIET_LOGS=1` suppresses all non-explicit logs. `BUN_DEBUG=<path>.log` dumps to file.
- **AddressSanitizer**: Enabled by default in debug builds on Linux/macOS. Disable with `-Denable_asan=false` in `BuildBun.cmake` if needed.
- **Local WebKit/JSC**: `bun run build:local` clones WebKit into `./vendor/WebKit` and builds JSC locally. Output goes to `./build/debug-local/`. WebKit folder is 8GB+.
- **PR builds**: `bunx bun-pr <pr-number>` downloads a release build from a GitHub Actions artifact.
