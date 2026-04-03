# Bun — Repository Summary

## Purpose and Goals

Bun is an all-in-one toolkit for JavaScript and TypeScript applications designed to be a fast, drop-in replacement for Node.js. Its primary goals are extreme speed, developer ergonomics, and consolidation of the JavaScript toolchain. Instead of needing separate tools for running code, bundling, testing, and managing packages, Bun ships as a single executable that handles all of these.

Bun is built with Zig and uses JavaScriptCore (the WebKit JS engine) instead of V8, making it significantly faster at startup and execution for many workloads. Version 1.3.11 is the current release.

## Key Features and Capabilities

**JavaScript Runtime**
- Drop-in Node.js compatibility — runs most Node.js programs without modification
- Native TypeScript and JSX execution (no prior compilation needed)
- ES modules and CommonJS interoperability
- Web standard APIs (fetch, URL, Headers, WebSocket, ReadableStream, etc.)
- Node.js built-in compatibility (fs, path, crypto, net, http, https, etc.)

**Package Manager**
- `bun install` — npm/yarn-compatible, significantly faster than npm/yarn/pnpm
- `bun add`, `bun remove`, `bun update` for dependency management
- `bun.lock` binary lockfile format
- Workspace support, git dependencies, patch support
- `bun pack` / `bun publish` for publishing

**Bundler**
- `Bun.build()` programmatic API and `bun build` CLI
- Tree-shaking, code splitting, source maps
- CSS, HTML, and asset handling
- Plugins API for extensibility
- Hot Module Replacement (HMR) in dev server mode

**Test Runner**
- `bun test` — Jest-compatible runner built into the runtime
- `expect()`, `describe()`, `test()`, `it()`, `beforeAll`, `afterEach`, etc.
- Mocking (`jest.fn()`, `jest.spyOn()`)
- Snapshot testing
- Coverage reporting with `--coverage`

**Bun Shell**
- `Bun.$` template literal for shell scripting in JavaScript/TypeScript
- Cross-platform (replaces bash scripts in CI)
- Supports pipes, redirects, globbing

**Database Integrations**
- `bun:sqlite` — built-in SQLite with a high-performance Zig driver
- `Bun.sql()` — PostgreSQL client
- `Bun.redis()` — Redis/Valkey client
- `Bun.s3()` — AWS S3 client

**Other APIs**
- `bun:ffi` — call C functions from JavaScript without compiling native addons
- Workers — multi-threaded JavaScript with `Worker` API
- File system watcher (`Bun.watch`)
- Glob pattern matching (`Bun.Glob`)
- Password hashing (`Bun.password`)
- HTMLRewriter for streaming HTML manipulation
- N-API compatibility for existing native Node.js addons

## Primary Use Cases and Target Audience

**Target Audience**
- JavaScript/TypeScript developers who want faster tooling
- Teams looking to simplify their toolchain (replace Node + npm + Jest + webpack/esbuild)
- Backend developers building HTTP servers, APIs, or CLI tools
- Full-stack developers using frameworks like Next.js, Nuxt, or Astro (many now support Bun)

**Primary Use Cases**
- Server-side JavaScript/TypeScript applications (HTTP APIs, microservices)
- Build tooling and bundling pipelines
- Running tests in CI/CD with reduced overhead
- CLI tools written in TypeScript
- Monorepo dependency management
- Scripting and automation (replacing shell scripts with `Bun.$`)

## High-Level Architecture

Bun uses a three-layer architecture:

**Layer 1 — JavaScript APIs (top)**
The `Bun` global namespace exposes all Bun-specific functionality to JavaScript code. Type definitions live in `packages/bun-types` and `src/js/builtins.d.ts`.

**Layer 2 — C++ Bindings and JavaScriptCore**
JavaScriptCore (JSC) provides the JavaScript engine. The `src/bun.js/bindings/` directory contains ~250KB of C++ code wiring JSC to Bun's Zig runtime. Code generation via `.classes.ts` schema files produces type-safe bindings automatically.

**Layer 3 — Zig Runtime (bottom)**
The core runtime, including file I/O, networking, the event loop, the bundler, the package manager, module resolution, transpilation, and all system calls, is written in Zig. The `src/sys.zig` (~157K lines) module abstracts platform differences across Linux, macOS, and Windows.

**Threading Model**
- Single-threaded event loop (libuv-inspired, implemented in Zig)
- Worker threads for parallel JS execution
- Thread pool for parallel bundling/parsing tasks

## Related Projects and Dependencies

- **JavaScriptCore / WebKit** — JavaScript engine (vendored/prebuit, not in-tree)
- **mimalloc** — Default memory allocator for production builds
- **libuv-inspired event loop** — Custom implementation, not libuv itself
- **uWebSockets** (`bun-uws`, `bun-usockets`) — WebSocket implementation
- **SQLite** — Bundled SQLite library
- **BoringSSL / OpenSSL** — TLS support
- **zlib / zstd** — Compression
- **LZMA** — Compression support
- **capstone** — Disassembler (debug/profiling builds)
- **lol_html** — HTMLRewriter implementation (Cloudflare's Rust library)

**Published npm Packages**
- `bun-types` — TypeScript definitions for Bun APIs
- `@types/bun` — Alternative type package
- `bun-debug-adapter-protocol` — DAP integration
- `bun-native-bundler-plugin-api` — Native plugin development
- `bun-lambda` — AWS Lambda runtime
- `bun-wasm` — WebAssembly builds
- `bun-vscode` — VS Code extension
