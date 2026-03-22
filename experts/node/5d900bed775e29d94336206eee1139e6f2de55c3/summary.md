# Node.js — Summary

## Repository Purpose and Goals

Node.js is an open-source, cross-platform JavaScript runtime environment built on top of Google's V8 JavaScript engine and the libuv asynchronous I/O library. Its primary purpose is to execute JavaScript outside of the browser, enabling server-side application development, scripting, build tooling, and more. The project is hosted under the OpenJS Foundation and governed by a Technical Steering Committee (TSC) using an open governance model.

Node.js is at version **26.0.0-pre** (commit 5d900bed) — the current development trunk targeting the next major release. The module ABI version is 144, and Node-API supports versions 1–10 (default 8).

## Key Features and Capabilities

- **Asynchronous, event-driven I/O**: Non-blocking file system, networking, and process operations via libuv's event loop, enabling high-concurrency servers without threads.
- **CommonJS and ES Module support**: Full dual-module system — `require()` / `module.exports` (CJS) and `import` / `export` (ESM) with interoperability between both systems.
- **Built-in TypeScript support**: Native TypeScript type-stripping via the embedded `amaro` (SWC-based) parser — run `.ts` files directly without a separate compile step (`--experimental-strip-types` or default in v26+).
- **Built-in test runner**: `node:test` provides a full testing framework with describe/it, mocking, code coverage, snapshot testing, and multiple reporters.
- **SQLite integration**: `node:sqlite` wraps the bundled SQLite library for synchronous, built-in database operations.
- **QUIC/HTTP3 (experimental)**: `node:quic` module with `QuicEndpoint`, `QuicSession`, `QuicStream` and support for BBR/CUBIC/RENO congestion control.
- **Single Executable Applications (SEA)**: Build a self-contained executable from a Node.js script using `node:sea` and the `postject` tool.
- **Permission model**: `--permission` flag with fine-grained restrictions (`--allow-fs-read`, `--allow-fs-write`, `--allow-net`, `--allow-child-process`, etc.).
- **Watch mode**: `--watch` and `--watch-path` flags restart the process on file changes.
- **Worker Threads**: `node:worker_threads` for true multi-threading with shared memory (`SharedArrayBuffer`).
- **V8 Inspector / Debugger**: Full Chrome DevTools Protocol support via `--inspect` / `--inspect-brk`.
- **Web-compatible globals**: Built-in `fetch`, `WebSocket`, `EventSource`, `URL`, `URLSearchParams`, `TextEncoder/Decoder`, `ReadableStream`, `WritableStream`, `AbortController`, `crypto` (Web Crypto API), and more.
- **Module customization hooks**: ESM loader hooks (`resolve`, `load`, `initialize`) and CJS customization hooks for intercepting module loading.
- **Compile cache**: Automatic caching of compiled JavaScript/TypeScript to speed up startup (`--compile-cache`).

## Primary Use Cases and Target Audience

- **Server-side web development**: HTTP/HTTPS servers, REST and GraphQL APIs, real-time applications (WebSockets).
- **CLI tooling and build systems**: npm scripts, bundlers (webpack, esbuild, Vite), linters, test runners.
- **Scripting and automation**: File processing, DevOps automation, CI/CD scripts.
- **Microservices and cloud functions**: Lightweight, fast-starting event-driven services.
- **Desktop applications**: Via Electron or similar embeddings.
- **Embedded/IoT applications**: Android and iOS targets, WASI support.

Target audience spans from individual developers to large enterprises running production workloads, as well as runtime embedders building custom JavaScript environments.

## High-Level Architecture Overview

```
┌─────────────────────────────────────────────────┐
│                User JavaScript / TypeScript      │
├─────────────────────────────────────────────────┤
│           Built-in Standard Library (lib/)       │
│  (http, fs, stream, crypto, net, tls, worker…)  │
├─────────────────────────────────────────────────┤
│         Internal Modules (lib/internal/)         │
│  (bootstrap, module loaders, process, perf…)    │
├─────────────────────────────────────────────────┤
│          Node.js C++ Core (src/)                 │
│  (Environment, Realm, bindings, N-API, TLS…)    │
├──────────────────────┬──────────────────────────┤
│    V8 (JavaScript    │   libuv (async I/O,       │
│     engine, deps/v8) │   event loop, deps/uv)   │
├──────────────────────┴──────────────────────────┤
│   Supporting deps: OpenSSL, nghttp2, cares,      │
│   sqlite, zlib, zstd, brotli, undici, llhttp,   │
│   ngtcp2, ada, simdjson, googletest…            │
└─────────────────────────────────────────────────┘
```

The bootstrap sequence: `src/node_main.cc` → `src/node.cc:Start()` → initializes V8 platform → creates `NodeMainInstance` → sets up `Environment` and `Realm` → loads `lib/internal/bootstrap/node.js` → dispatches to a main entry in `lib/internal/main/` (e.g., `run_main_module.js`, `repl.js`, `test_runner.js`, `watch_mode.js`).

## Related Projects and Dependencies

- **V8** (`deps/v8`): Google's JavaScript engine providing JIT compilation, garbage collection, and the runtime VM.
- **libuv** (`deps/uv`): Cross-platform async I/O, timers, file system, DNS, networking, and the event loop.
- **OpenSSL** (`deps/openssl`): TLS/SSL, cryptography. Node.js ships its own build with FIPS support optional.
- **npm** (`deps/npm`): The default package manager, bundled with Node.js.
- **undici** (`deps/undici`): HTTP/1.1 and HTTP/2 client powering the global `fetch` API and `WebSocket`.
- **llhttp** (`deps/llhttp`): HTTP/1.1 parser.
- **nghttp2** (`deps/nghttp2`): HTTP/2 protocol implementation.
- **ngtcp2** (`deps/ngtcp2`): QUIC/HTTP3 transport protocol.
- **cares** (`deps/cares`): Asynchronous DNS resolution.
- **sqlite** (`deps/sqlite`): Embedded SQL database.
- **amaro** (`deps/amaro`): TypeScript type-stripping based on SWC.
- **ada** (`deps/ada`): WHATWG URL parser.
- **zlib / brotli / zstd** (`deps/`): Compression algorithms.
- **simdjson** (`deps/simdjson`): Fast SIMD-accelerated JSON parsing.
- **googletest** (`deps/googletest`): C++ unit test framework (used for cctest).
- **postject** (`deps/postject`): Injects resources into executables (used for SEA).
