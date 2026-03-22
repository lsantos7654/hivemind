# Node.js — Code Structure

## Annotated Directory Tree

```
nodejs/node/
├── src/                        # C++ core source (primary Node.js runtime implementation)
│   ├── node.cc / node.h        # Main entry point and public embedding API
│   ├── node_main.cc            # Thin wrapper: int main() → node::Start()
│   ├── env.cc / env.h          # Environment class (per-isolate runtime state)
│   ├── env_properties.h        # Compile-time property list for Environment
│   ├── node_realm.cc/.h        # Realm class (principal/shadow realm support)
│   ├── node_main_instance.cc/.h # Bootstrap: creates Isolate, Environment, runs loop
│   ├── node_version.h          # Version defines (NODE_MAJOR=26, MODULE_VERSION=144)
│   ├── node_api.cc / node_api.h # Node-API (N-API) implementation layer
│   ├── js_native_api.h / .cc   # Raw JS Native API (C ABI for add-ons)
│   ├── js_native_api_types.h   # napi_env, napi_value, napi_status type defs
│   ├── node_api_types.h        # napi_module, napi_addon_register_func
│   ├── node_builtins.cc/.h     # Built-in module registry and compile cache
│   ├── node_binding.cc/.h      # Binding registration infrastructure
│   ├── node_external_reference.cc/.h # V8 external references for snapshots
│   ├── api/                    # Embedding API implementations
│   │   ├── async_resource.cc   # AsyncResource C++ API
│   │   ├── callback.cc         # Callback scope helpers
│   │   ├── embed_helpers.cc    # CommonEnvironmentSetup, SpinEventLoop
│   │   ├── encoding.cc         # Encoding utilities for embedders
│   │   ├── environment.cc      # CreateEnvironment, LoadEnvironment, FreeEnvironment
│   │   ├── exceptions.cc       # Exception handling helpers
│   │   ├── hooks.cc            # AtExit hooks
│   │   └── utils.cc            # Miscellaneous embedding utilities
│   ├── crypto/                 # Cryptographic subsystem (OpenSSL wrappers)
│   │   ├── crypto_aes.cc/.h    # AES ciphers
│   │   ├── crypto_argon2.cc/.h # Argon2 password hashing
│   │   ├── crypto_cipher.cc/.h # Generic cipher/decipher
│   │   ├── crypto_context.cc/.h # TLS SecureContext
│   │   ├── crypto_dh.cc/.h     # Diffie-Hellman
│   │   ├── crypto_ec.cc/.h     # Elliptic curve keys (ECDH, ECDSA)
│   │   ├── crypto_hash.cc/.h   # Digest/hash functions
│   │   ├── crypto_hkdf.cc/.h   # HKDF key derivation
│   │   ├── crypto_hmac.cc/.h   # HMAC
│   │   ├── crypto_kem.cc/.h    # Key Encapsulation Mechanisms (ML-KEM)
│   │   ├── crypto_keygen.cc/.h # Key generation (RSA, EC, etc.)
│   │   ├── crypto_keys.cc/.h   # Key object management
│   │   ├── crypto_pbkdf2.cc/.h # PBKDF2
│   │   ├── crypto_random.cc/.h # randomBytes, randomFill, etc.
│   │   ├── crypto_rsa.cc/.h    # RSA operations
│   │   ├── crypto_scrypt.cc/.h # Scrypt
│   │   ├── crypto_sig.cc/.h    # Sign/Verify
│   │   ├── crypto_tls.cc/.h    # TLS implementation (TLSWrap)
│   │   └── crypto_util.cc/.h   # Shared crypto helpers, WebCrypto support
│   ├── dataqueue/              # Data queue abstraction for streaming
│   ├── inspector_*.cc/.h       # V8 Inspector / debugger infrastructure
│   ├── node_buffer.cc/.h       # Buffer class implementation
│   ├── node_blob.cc/.h         # Blob implementation
│   ├── node_config_file.cc/.h  # .node_config file parsing
│   ├── node_contextify.cc/.h   # vm.Script, vm.createContext, sandbox
│   ├── node_crypto.cc/.h       # Main crypto module binding entry
│   ├── node_dotenv.cc/.h       # .env file parser
│   ├── node_errors.cc/.h       # Error creation helpers
│   ├── node_file.cc/.h         # fs module bindings
│   ├── node_http2.cc/.h        # HTTP/2 implementation (nghttp2 wrapper)
│   ├── node_http_parser.cc     # HTTP/1.x parser (llhttp wrapper)
│   ├── node_i18n.cc/.h         # Internationalization (ICU wrapper)
│   ├── node_locks.cc/.h        # Web Locks API
│   ├── node_process_*.cc       # process object methods, events, objects
│   ├── node_sea.cc/.h          # Single Executable Application support
│   ├── node_serdes.cc          # v8.serialize / v8.deserialize
│   ├── node_shadow_realm.cc/.h # ShadowRealm implementation
│   ├── node_snapshotable.cc/.h # Snapshot serialization infrastructure
│   ├── node_sqlite.cc/.h       # SQLite built-in module
│   ├── node_task_runner.cc/.h  # --run (package.json scripts) implementation
│   ├── node_trace_events.cc    # Trace Events API
│   ├── node_url.cc/.h          # WHATWG URL (ada-based)
│   ├── node_url_pattern.cc/.h  # URLPattern
│   ├── node_util.cc            # util module bindings
│   ├── node_wasi.cc/.h         # WASI (WebAssembly System Interface)
│   ├── node_wasm_web_api.cc/.h # WebAssembly streaming compilation
│   ├── node_webstorage.cc/.h   # localStorage / sessionStorage (SQLite-backed)
│   ├── node_worker.cc/.h       # Worker Threads implementation
│   ├── node_zlib.cc            # zlib/brotli/zstd bindings
│   ├── cares_wrap.cc/.h        # c-ares DNS resolver binding
│   ├── async_wrap.cc/.h        # AsyncResource, async_hooks tracking
│   ├── async_context_frame.cc/.h # AsyncLocalStorage frame tracking
│   ├── base_object.cc/.h       # Base class for GC-tracked C++ objects
│   ├── compile_cache.cc/.h     # Script/module compile cache
│   ├── stream_*.cc/.h          # C++ stream infrastructure (pipe, duplex, etc.)
│   ├── tcp_wrap.cc/.h          # TCP socket binding
│   ├── tls_wrap.cc/.h          # TLS socket wrapping
│   ├── udp_wrap.cc/.h          # UDP socket binding
│   ├── uv.cc                   # libuv integration helpers
│   └── aliased_buffer.h        # Shared memory buffer between C++ and JS
│
├── lib/                        # JavaScript standard library
│   ├── *.js                    # Public built-in modules (require('http'), etc.)
│   │   ├── assert.js           # Assertion module
│   │   ├── async_hooks.js      # Async hooks public API
│   │   ├── buffer.js           # Buffer public API
│   │   ├── child_process.js    # Child process spawning
│   │   ├── cluster.js          # Cluster (multi-process) module
│   │   ├── console.js          # Console output
│   │   ├── crypto.js           # Crypto module public API
│   │   ├── dgram.js            # UDP datagrams
│   │   ├── dns.js / dns/       # DNS resolution
│   │   ├── domain.js           # Domain error handling (legacy)
│   │   ├── events.js           # EventEmitter
│   │   ├── fs.js / fs/         # File system module
│   │   ├── http.js             # HTTP/1.x server and client
│   │   ├── http2.js            # HTTP/2 server and client
│   │   ├── https.js            # HTTPS module
│   │   ├── inspector.js        # Inspector/debugger API
│   │   ├── module.js           # Module system entry point
│   │   ├── net.js              # TCP/IPC sockets
│   │   ├── os.js               # Operating system info
│   │   ├── path.js / path/     # File path utilities
│   │   ├── perf_hooks.js       # Performance measurement
│   │   ├── process.js          # process global helpers
│   │   ├── quic.js             # QUIC (experimental)
│   │   ├── readline.js         # Interactive line reading
│   │   ├── repl.js             # Read-Eval-Print Loop
│   │   ├── sea.js              # Single Executable Application API
│   │   ├── sqlite.js           # SQLite module (proxies internalBinding)
│   │   ├── stream.js           # Stream base classes
│   │   ├── test.js             # Test runner public API (require('node:test'))
│   │   ├── tls.js              # TLS/SSL socket
│   │   ├── tty.js              # TTY streams
│   │   ├── url.js              # URL module (WHATWG and legacy)
│   │   ├── util.js             # Utilities (inspect, format, promisify, etc.)
│   │   ├── v8.js               # V8 engine internals
│   │   ├── vm.js               # Virtual machine contexts/scripts
│   │   ├── wasi.js             # WASI
│   │   ├── worker_threads.js   # Worker Threads public API
│   │   └── zlib.js             # Compression
│   └── internal/               # Private implementation modules (not directly importable)
│       ├── bootstrap/          # Runtime bootstrap code
│       │   ├── node.js         # Main bootstrap (sets up globals, process, etc.)
│       │   ├── realm.js        # Realm/BuiltinModule infrastructure
│       │   ├── shadow_realm.js # ShadowRealm bootstrap
│       │   ├── switches/       # Feature-gated setup (own/not-own process state, thread type)
│       │   └── web/            # Web globals injection
│       │       ├── exposed-wildcard.js      # URL, TextEncoder, AbortController, streams…
│       │       └── exposed-window-or-worker.js # fetch, WebSocket, EventSource…
│       ├── main/               # Per-execution-mode entry scripts
│       │   ├── run_main_module.js  # Normal script execution
│       │   ├── repl.js             # Interactive REPL
│       │   ├── test_runner.js      # --test mode
│       │   ├── watch_mode.js       # --watch mode
│       │   ├── worker_thread.js    # Worker thread bootstrap
│       │   ├── eval_string.js      # -e / --eval
│       │   ├── eval_stdin.js       # stdin eval
│       │   ├── inspect.js          # --inspect entry
│       │   ├── check_syntax.js     # --check
│       │   └── print_help.js       # --help
│       ├── modules/            # Module system
│       │   ├── cjs/loader.js   # CommonJS loader (require, Module._resolveFilename)
│       │   ├── esm/            # ES Module loader
│       │   │   ├── loader.js       # ModuleLoader, import() dispatch
│       │   │   ├── resolve.js      # ESM resolution algorithm
│       │   │   ├── load.js         # Module loading and source fetching
│       │   │   ├── hooks.js        # Loader hook chain management
│       │   │   ├── translators.js  # Source-to-module translation (JS, JSON, WASM, TS)
│       │   │   ├── module_job.js   # ModuleJob (individual module loading unit)
│       │   │   └── module_map.js   # Module cache map
│       │   ├── customization_hooks.js # register() and CJS/ESM hook APIs
│       │   ├── helpers.js          # Shared module utilities
│       │   ├── package_json_reader.js # package.json reading and type detection
│       │   ├── run_main.js         # Module.runMain()
│       │   └── typescript.js       # TypeScript type-stripping (amaro integration)
│       ├── streams/            # Stream internals
│       │   ├── readable.js         # Readable stream
│       │   ├── writable.js         # Writable stream
│       │   ├── duplex.js           # Duplex stream
│       │   ├── transform.js        # Transform stream
│       │   ├── pipeline.js         # stream.pipeline()
│       │   ├── compose.js          # stream.compose()
│       │   └── operators.js        # Stream operators (map, filter, etc.)
│       ├── crypto/             # Crypto module internals (JS side)
│       ├── process/            # process object implementation
│       │   ├── pre_execution.js    # Bootstrap preparation
│       │   ├── execution.js        # Script/eval execution helpers
│       │   ├── permission.js       # Permission model
│       │   └── promises.js         # Unhandled rejection handling
│       ├── test_runner/        # Built-in test runner internals
│       │   ├── test.js             # Test class, describe/it
│       │   ├── runner.js           # Test suite runner
│       │   ├── mock/               # Mock function and timer support
│       │   ├── reporter/           # Built-in reporters (tap, spec, junit, etc.)
│       │   └── coverage.js         # Code coverage
│       ├── inspector/          # Inspector/DevTools Protocol integration
│       ├── http2/              # HTTP/2 internal helpers
│       ├── async_local_storage/ # AsyncLocalStorage implementation
│       ├── worker/             # Worker thread internal messaging
│       ├── quic/               # QUIC implementation (JS side)
│       ├── perf/               # Performance API internals
│       ├── debugger/           # CLI debugger
│       └── per_context/        # Per-V8-context primitives (primordials, etc.)
│
├── deps/                       # Third-party dependencies (mostly vendored)
│   ├── v8/                     # V8 JavaScript engine
│   ├── uv/                     # libuv async I/O
│   ├── openssl/                # OpenSSL cryptography
│   ├── npm/                    # npm package manager
│   ├── undici/                 # HTTP client (fetch API)
│   ├── llhttp/                 # HTTP/1.x parser
│   ├── nghttp2/                # HTTP/2
│   ├── ngtcp2/                 # QUIC/HTTP3
│   ├── cares/                  # Async DNS
│   ├── sqlite/                 # SQLite database
│   ├── amaro/                  # TypeScript type-stripper (SWC-based)
│   ├── ada/                    # WHATWG URL parser
│   ├── zlib/ / brotli/ / zstd/ # Compression
│   ├── simdjson/               # SIMD JSON parser
│   └── googletest/             # C++ testing framework
│
├── test/                       # Test suite
│   ├── parallel/               # Most unit/integration tests
│   ├── sequential/             # Tests that must run sequentially
│   ├── addons/                 # Native add-on tests
│   ├── node-api/               # N-API tests
│   ├── js-native-api/          # JS Native API tests
│   ├── wpt/                    # Web Platform Tests
│   ├── fixtures/               # Test fixtures
│   ├── cctest/                 # C++ unit tests (googletest)
│   └── common/                 # Test helpers
│
├── doc/api/                    # API documentation (Markdown → HTML)
├── benchmark/                  # Performance benchmarks
├── tools/                      # Build and developer tools
│   ├── gyp/                    # GYP build system
│   ├── gyp_node.py             # Node.js GYP runner
│   ├── eslint/                 # ESLint tooling
│   ├── doc/                    # Doc generation tools
│   ├── icu/                    # ICU version management
│   └── inspector_protocol/     # Chrome DevTools Protocol codegen
├── node.gyp                    # Primary GYP build definition
├── node.gypi                   # Shared GYP variables
├── common.gypi                 # Shared compiler flags
├── Makefile                    # Unix build orchestration
├── vcbuild.bat                 # Windows build script
├── configure / configure.py    # Build configuration script
├── BUILD.gn                    # GN build (alternative, experimental)
├── node.gni                    # GN configuration
├── tsconfig.json               # TypeScript config for typings/
└── typings/                    # TypeScript type definitions for internal APIs
    ├── globals.d.ts
    ├── primordials.d.ts
    └── internalBinding/
```

## Code Organization Patterns

### Naming Conventions
- **`node_<module>.cc/.h`** — C++ implementation of a built-in module (e.g., `node_file.cc` for `fs`, `node_buffer.cc` for `Buffer`).
- **`<module>_wrap.cc/.h`** — Thin C++ wrappers around C libraries (e.g., `tcp_wrap.cc`, `tls_wrap.cc`).
- **`<name>-inl.h`** — Inline method implementations for headers (included at bottom of `.h` files).
- **`lib/internal/`** — JavaScript modules that are internal implementation details, not directly `require()`-able by user code.
- **`lib/internal/bootstrap/`** — Code that runs during the very first bootstrap phase before any user code.
- **`lib/internal/main/`** — Entry-point scripts selected based on CLI flags.
- **`primordials`** — Frozen references to built-in JavaScript objects/methods, preventing prototype pollution attacks on the runtime itself.

### Architecture Patterns
- **`internalBinding('name')`** — Bridge from JavaScript to C++; registers C++ bindings accessible from JS internal modules.
- **`BaseObject`** — Base C++ class (`src/base_object.h`) for objects tracked by V8's garbage collector.
- **`AsyncWrap`** — Extends `BaseObject` with async resource tracking for `async_hooks`.
- **Environment** (`src/env.h`) — Holds all per-isolate state: binding objects, options, timers, cleanup hooks, etc.
- **Realm** (`src/node_realm.h`) — Supports multiple JavaScript realms (principal + shadow realms) sharing an isolate.
