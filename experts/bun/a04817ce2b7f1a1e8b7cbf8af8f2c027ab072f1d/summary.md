# Bun — Summary

## Repository Purpose and Goals

Bun is an all-in-one JavaScript and TypeScript toolkit designed as a fast, drop-in replacement for Node.js. Its primary goal is to dramatically reduce startup times and memory usage while providing a complete development environment in a single executable. The project is developed by Oven SH and targets developers who want a faster, more integrated alternative to the fragmented Node.js ecosystem (Node + npm + Jest + esbuild + etc.).

## Key Features and Capabilities

- **JavaScript Runtime**: A high-performance JS/TS runtime built on JavaScriptCore (JSC) and written in Zig. Supports TypeScript and JSX natively without transpilation steps.
- **Package Manager** (`bun install`): A fast npm-compatible package manager with a binary lockfile (`bun.lockb`) and a text lockfile (`bun.lock`). Supports workspaces, lifecycle scripts, patch packages, overrides, and scoped registries.
- **Bundler** (`Bun.build`): A JavaScript/TypeScript bundler inspired by esbuild. Supports tree-shaking, code splitting, plugins, macros, CSS bundling, HTML imports, and single-file executables.
- **Test Runner** (`bun test`): A Jest-compatible test runner with built-in mocking, snapshot testing, DOM testing (via happy-dom), code coverage, and watch mode.
- **HTTP Server** (`Bun.serve`): A high-performance HTTP/HTTPS/WebSocket server powered by uWebSockets (uWS). Supports static routes, file routes, HTML bundle routes, and framework-based filesystem routing.
- **Built-in APIs**: `Bun.file` (file I/O), `Bun.spawn`/`Bun.spawnSync` (child processes), `Bun.connect`/`Bun.listen` (TCP/TLS sockets), `Bun.udpSocket` (UDP), `Bun.sql` (PostgreSQL), `Bun.redis`/`Bun.valkey` (Redis/Valkey), `Bun.s3` (S3), `bun:sqlite` (SQLite), `bun:ffi` (C FFI), `Bun.$` (shell scripting), `Bun.Glob`, `Bun.CryptoHasher`, `Bun.Transpiler`, `Bun.semver`, `Bun.color`, `Bun.CSRF`, `Bun.Terminal` (PTY), and more.
- **Bake** (full-stack dev server): An experimental full-stack framework integration layer with HMR, SSR, and React server components support.
- **Node.js Compatibility**: Extensive compatibility with Node.js built-in modules (`fs`, `path`, `crypto`, `http`, `net`, `os`, `stream`, `worker_threads`, `child_process`, etc.).
- **Shell Scripting** (`Bun.$`): A cross-platform shell scripting API using tagged template literals.
- **Watch Mode / Hot Reloading**: File watching via `ImportWatcher` with hot reload (`--hot`) and watch mode (`--watch`).

## Primary Use Cases and Target Audience

- Backend API servers and microservices
- Full-stack web applications (with Bake)
- CLI tools and scripts
- Package management in monorepos
- Test suites (migrating from Jest)
- Build pipelines (replacing esbuild/webpack)
- Developers wanting a single tool instead of Node + npm + Jest + esbuild

## High-Level Architecture Overview

Bun is written primarily in Zig (runtime, bundler, package manager, shell, HTTP server) with C++ bindings to JavaScriptCore (JSC). The build system uses CMake with Zig, Rust, and Bun itself as sub-tools. Key architectural layers:

1. **JavaScript VM** (`src/bun.js/VirtualMachine.zig`): One VM per thread, wraps JSC's `JSGlobalObject`. Manages the event loop, module loader, transpiler cache, source maps, hot reloader, and plugin runner.
2. **Bundler** (`src/bundler/`): Multi-threaded bundler using mimalloc thread-local heaps. `BundleV2` orchestrates parse tasks, linking, and chunk emission. `LinkerContext` handles tree-shaking and code splitting.
3. **Package Manager** (`src/install/`): `PackageManager` drives resolution, download, and installation. `Lockfile` stores the dependency graph in a binary format. Supports hoisted and isolated install modes.
4. **HTTP Server** (`src/bun.js/api/server.zig`): Built on uWebSockets. `AnyServer` dispatches to `StaticRoute`, `FileRoute`, `HTMLBundle.Route`, or `FrameworkRouter`.
5. **Shell** (`src/shell/`): A cross-platform shell interpreter with builtins, piping, brace expansion, and environment management.
6. **Bake** (`src/bake/`): Full-stack dev server with `DevServer`, `FrameworkRouter`, HMR runtime, and React server component support.
7. **Node.js Compat** (`src/bun.js/node/`): Zig implementations of Node.js built-in modules.

## Related Projects and Dependencies

- **JavaScriptCore** (WebKit) — JS engine
- **uWebSockets (uWS)** — HTTP/WebSocket server substrate
- **BoringSSL** — TLS/SSL
- **mimalloc** — Memory allocator
- **tinycc** — JIT C compiler for `bun:ffi`
- **lshpack** — HPACK encoder/decoder for HTTP/2
- **Zig** — Primary implementation language
- **Rust** — Used for some native bundler plugins (`bun-native-bundler-plugin-api`, `bun-native-plugin-rs`)
- **esbuild** — Inspiration for the bundler design
