# Bun — Code Structure

## Annotated Directory Tree

```
bun/
├── src/                          # Primary Zig/C++ source
│   ├── main.zig                  # Entry point; dispatches to CLI
│   ├── bun.zig                   # Root module; re-exports core types
│   ├── cli.zig                   # Typer-style CLI dispatcher
│   ├── cli/                      # Per-command implementations
│   │   ├── run_command.zig       # `bun run`
│   │   ├── test_command.zig      # `bun test`
│   │   ├── build_command.zig     # `bun build`
│   │   ├── install_command.zig   # `bun install`
│   │   ├── add_command.zig       # `bun add`
│   │   ├── remove_command.zig    # `bun remove`
│   │   ├── update_command.zig    # `bun update`
│   │   ├── bunx_command.zig      # `bunx`
│   │   ├── repl_command.zig      # `bun repl`
│   │   ├── create_command.zig    # `bun create`
│   │   ├── init_command.zig      # `bun init`
│   │   ├── upgrade_command.zig   # `bun upgrade`
│   │   ├── publish_command.zig   # `bun publish`
│   │   ├── pack_command.zig      # `bun pack`
│   │   ├── patch_command.zig     # `bun patch`
│   │   ├── patch_commit_command.zig
│   │   ├── outdated_command.zig  # `bun outdated`
│   │   ├── audit_command.zig     # `bun audit`
│   │   ├── filter_run.zig        # `--filter` workspace runner
│   │   ├── multi_run.zig         # parallel script runner
│   │   ├── scan_command.zig      # `bun scan`
│   │   ├── why_command.zig       # `bun why`
│   │   ├── pm_pkg_command.zig    # `bun pm`
│   │   ├── pm_trusted_command.zig
│   │   ├── pm_version_command.zig
│   │   ├── pm_view_command.zig
│   │   ├── pm_why_command.zig
│   │   └── Arguments.zig         # CLI argument parsing
│   │
│   ├── bun.js/                   # JavaScript runtime layer
│   │   ├── VirtualMachine.zig    # Core VM: event loop, module loader, transpiler cache
│   │   ├── ModuleLoader.zig      # ES module / CJS loader
│   │   ├── HardcodedModule.zig   # Built-in module registry
│   │   ├── hot_reloader.zig      # ImportWatcher: hot/watch mode
│   │   ├── event_loop.zig        # Event loop implementation
│   │   ├── event_loop/           # Event loop sub-components
│   │   ├── ipc.zig               # IPC channel for child processes
│   │   ├── web_worker.zig        # Web Worker support
│   │   ├── Debugger.zig          # V8 inspector protocol adapter
│   │   ├── ConsoleObject.zig     # console.* implementation
│   │   ├── RuntimeTranspilerCache.zig  # Transpiler result cache
│   │   ├── SavedSourceMap.zig    # Source map storage
│   │   ├── jsc.zig               # JSC bindings root
│   │   ├── jsc/                  # JSC C++ binding wrappers
│   │   ├── bindings/             # C++ ↔ Zig bridge code
│   │   ├── api/                  # Bun.* API implementations
│   │   │   ├── BunObject.zig     # globalThis.Bun object (all Bun.* APIs)
│   │   │   ├── BunObject.bind.ts # Bindgen spec for BunObject
│   │   │   ├── server.zig        # Bun.serve / HTTP server
│   │   │   ├── server/           # Server sub-components
│   │   │   │   ├── WebSocketServerContext.zig
│   │   │   │   ├── StaticRoute.zig
│   │   │   │   ├── FileRoute.zig
│   │   │   │   ├── HTMLBundle.zig
│   │   │   │   └── SSLConfig.bindv2.ts
│   │   │   ├── JSBundler.zig     # Bun.build() JS API
│   │   │   ├── JSTranspiler.zig  # Bun.Transpiler JS API
│   │   │   ├── ffi.zig           # bun:ffi implementation
│   │   │   ├── glob.zig          # Bun.Glob
│   │   │   ├── html_rewriter.zig # HTMLRewriter
│   │   │   ├── filesystem_router.zig  # FileSystemRouter
│   │   │   ├── crypto.zig        # Bun.CryptoHasher, Bun.SHA*, etc.
│   │   │   ├── crypto/           # Crypto sub-implementations
│   │   │   ├── HashObject.zig    # Bun.hash (Wyhash, etc.)
│   │   │   ├── UnsafeObject.zig  # Bun.unsafe
│   │   │   ├── Timer.zig         # setTimeout/setInterval
│   │   │   ├── Timer/            # Timer sub-components
│   │   │   ├── cron.zig          # Bun.cron
│   │   │   ├── Archive.zig       # Bun.Archive (libarchive)
│   │   │   ├── TOMLObject.zig    # Bun.TOML
│   │   │   ├── YAMLObject.zig    # Bun.YAML
│   │   │   ├── JSONCObject.zig   # Bun.JSONC
│   │   │   ├── JSON5Object.zig   # Bun.JSON5
│   │   │   ├── MarkdownObject.zig # Bun.markdown
│   │   │   ├── FFIObject.zig     # Bun.FFI
│   │   │   ├── h2.classes.ts     # HTTP/2 class definitions
│   │   │   ├── sql.classes.ts    # Bun.sql class definitions
│   │   │   ├── valkey.classes.ts # Bun.valkey class definitions
│   │   │   └── bun/              # Sub-APIs
│   │   │       ├── subprocess.zig  # Bun.spawn / Bun.spawnSync
│   │   │       ├── subprocess/     # Subprocess sub-components
│   │   │       ├── socket.zig      # Bun.connect / Bun.listen
│   │   │       ├── socket/         # Socket sub-components
│   │   │       │   ├── Listener.zig
│   │   │       │   ├── Handlers.zig
│   │   │       │   ├── SocketAddress.zig
│   │   │       │   ├── tls_socket_functions.zig
│   │   │       │   └── WindowsNamedPipeContext.zig
│   │   │       ├── spawn.zig       # Low-level spawn primitives
│   │   │       ├── spawn/          # Spawn sub-components
│   │   │       ├── dns.zig         # Bun DNS resolver
│   │   │       ├── udp_socket.zig  # Bun.udpSocket
│   │   │       ├── Terminal.zig    # Bun.Terminal (PTY)
│   │   │       ├── process.zig     # Process management
│   │   │       ├── h2_frame_parser.zig  # HTTP/2 frame parser + HPACK
│   │   │       ├── lshpack.zig     # HPACK encoder/decoder wrapper
│   │   │       ├── ssl_wrapper.zig # BoringSSL wrapper
│   │   │       └── x509.zig        # X.509 certificate utilities
│   │   ├── node/                 # Node.js built-in module implementations
│   │   │   ├── node_fs.zig       # fs module
│   │   │   ├── node_fs_binding.zig
│   │   │   ├── node_fs_watcher.zig
│   │   │   ├── node_fs_stat_watcher.zig
│   │   │   ├── node_crypto_binding.zig
│   │   │   ├── node_net_binding.zig
│   │   │   ├── node_http_binding.zig
│   │   │   ├── node_process.zig  # process object
│   │   │   ├── node_os.zig       # os module
│   │   │   ├── node_assert.zig   # assert module
│   │   │   ├── node_zlib_binding.zig
│   │   │   ├── node_util_binding.zig
│   │   │   ├── node_error_binding.zig
│   │   │   ├── node_cluster_binding.zig
│   │   │   ├── buffer.zig        # Buffer class
│   │   │   ├── path.zig          # path module
│   │   │   ├── types.zig         # Node.js type utilities
│   │   │   ├── Stat.zig          # fs.Stats
│   │   │   ├── StatFS.zig        # fs.StatFs
│   │   │   └── net/              # net module sub-components
│   │   ├── modules/              # C++ module implementations
│   │   │   ├── NodeModuleModule.cpp  # node:module
│   │   │   ├── NodeTTYModule.cpp     # node:tty
│   │   │   ├── NodeUtilTypesModule.cpp
│   │   │   └── ObjectModule.cpp
│   │   ├── test/                 # Test runner internals
│   │   └── webcore/              # Web platform APIs
│   │       ├── Blob.zig          # Blob / BunFile
│   │       ├── fetch.zig         # fetch() implementation
│   │       ├── Request.zig       # Request class
│   │       ├── Response.zig      # Response class
│   │       ├── ReadableStream.zig
│   │       ├── TextEncoder.zig
│   │       ├── TextDecoder.zig
│   │       ├── Crypto.zig        # Web Crypto API
│   │       ├── CookieMap.zig     # Bun.Cookie
│   │       ├── S3Client.zig      # Bun.s3 / Bun.S3Client
│   │       ├── S3File.zig
│   │       └── encoding.zig      # TextEncoder/Decoder
│   │
│   ├── bundler/                  # Bundler implementation
│   │   ├── bundle_v2.zig         # Main bundler orchestrator (BundleV2)
│   │   ├── LinkerContext.zig     # Linker: tree-shaking, code splitting
│   │   ├── LinkerGraph.zig       # Dependency graph
│   │   ├── ParseTask.zig         # Per-file parse task
│   │   ├── BundleThread.zig      # Worker thread pool
│   │   ├── ThreadPool.zig        # Thread pool
│   │   ├── Graph.zig             # Module graph
│   │   ├── Chunk.zig             # Output chunk
│   │   ├── entry_points.zig      # Entry point handling
│   │   ├── AstBuilder.zig        # AST construction
│   │   ├── barrel_imports.zig    # Barrel import optimization
│   │   ├── HTMLImportManifest.zig
│   │   └── ServerComponentParseTask.zig
│   │
│   ├── install/                  # Package manager
│   │   ├── PackageManager.zig    # Main package manager
│   │   ├── PackageManager/       # PM sub-components
│   │   ├── lockfile.zig          # Lockfile (binary + text formats)
│   │   ├── lockfile/             # Lockfile sub-components
│   │   ├── install.zig           # Install orchestration
│   │   ├── dependency.zig        # Dependency resolution
│   │   ├── resolution.zig        # Version resolution
│   │   ├── npm.zig               # npm registry client
│   │   ├── PackageInstall.zig    # Package installation
│   │   ├── PackageInstaller.zig  # Installer orchestration
│   │   ├── lifecycle_script_runner.zig
│   │   ├── hoisted_install.zig   # Hoisted (flat) install mode
│   │   ├── isolated_install.zig  # Isolated install mode
│   │   ├── isolated_install/
│   │   ├── extract_tarball.zig   # Tarball extraction
│   │   ├── patch_install.zig     # Patch package support
│   │   ├── migration.zig         # Lockfile migration
│   │   ├── bin.zig               # Binary linking
│   │   ├── integrity.zig         # Package integrity verification
│   │   ├── repository.zig        # Git repository dependencies
│   │   ├── resolvers/            # Dependency resolvers
│   │   ├── pnpm.zig              # pnpm lockfile compatibility
│   │   ├── yarn.zig              # yarn lockfile compatibility
│   │   └── windows-shim/         # Windows binary shims
│   │
│   ├── shell/                    # Shell scripting (Bun.$)
│   │   ├── shell.zig             # Shell entry point
│   │   ├── interpreter.zig       # Shell interpreter
│   │   ├── Builtin.zig           # Built-in commands (cd, echo, ls, etc.)
│   │   ├── builtin/              # Per-builtin implementations
│   │   ├── ParsedShellScript.zig # Parsed shell AST
│   │   ├── states/               # Interpreter state machine
│   │   ├── IO.zig                # Shell I/O abstraction
│   │   ├── IOReader.zig
│   │   ├── IOWriter.zig
│   │   ├── subproc.zig           # Shell subprocess management
│   │   ├── EnvMap.zig            # Environment variable map
│   │   ├── braces.zig            # Brace expansion
│   │   └── util.zig
│   │
│   ├── bake/                     # Full-stack dev server (experimental)
│   │   ├── DevServer.zig         # Development server
│   │   ├── DevServer/            # DevServer sub-components
│   │   ├── FrameworkRouter.zig   # Framework-based routing
│   │   ├── production.zig        # Production build
│   │   ├── bun-framework-react/  # Built-in React framework
│   │   ├── client/               # Client-side HMR runtime
│   │   ├── server/               # Server-side rendering
│   │   ├── hmr-module.ts         # HMR module runtime
│   │   ├── hmr-runtime-client.ts
│   │   ├── hmr-runtime-server.ts
│   │   ├── bake.d.ts             # TypeScript types for Bake API
│   │   └── shared.ts
│   │
│   ├── css/                      # CSS parser and bundler
│   ├── js_parser.zig             # JavaScript parser
│   ├── js_lexer.zig              # JavaScript lexer
│   ├── js_printer.zig            # JavaScript code printer
│   ├── transpiler.zig            # Transpiler (TS/JSX → JS)
│   ├── resolver/                 # Module resolver
│   ├── http.zig                  # HTTP client
│   ├── http/                     # HTTP client sub-components
│   ├── dns.zig                   # DNS resolver
│   ├── env_loader.zig            # .env file loader
│   ├── glob.zig                  # Glob pattern matching
│   ├── sourcemap/                # Source map generation
│   ├── sql/                      # SQL (PostgreSQL) client
│   ├── valkey/                   # Valkey/Redis client
│   ├── s3/                       # S3 client
│   ├── napi/                     # Node-API (N-API) implementation
│   ├── codegen/                  # Code generation utilities
│   ├── create/                   # `bun create` templates
│   ├── init/                     # `bun init` scaffolding
│   ├── repl.zig                  # REPL implementation
│   ├── semver.zig                # Semver parsing/comparison
│   ├── semver/
│   ├── crash_handler.zig         # Crash reporting
│   ├── Global.zig                # Global state
│   ├── allocators.zig            # Custom allocators
│   ├── allocators/
│   ├── threading.zig             # Threading utilities
│   ├── threading/
│   ├── io/                       # I/O primitives
│   ├── async/                    # Async utilities
│   ├── collections.zig           # Custom collections
│   ├── collections/
│   ├── string.zig                # String utilities
│   ├── string/
│   ├── paths.zig                 # Path utilities
│   ├── paths/
│   ├── fs.zig                    # Filesystem utilities
│   ├── fs/
│   ├── sys.zig                   # System call wrappers
│   ├── sys/
│   ├── windows.zig               # Windows-specific code
│   ├── windows/
│   ├── linux.zig                 # Linux-specific code
│   ├── darwin.zig                # macOS-specific code
│   ├── runtime.js                # JS runtime bootstrap
│   ├── runtime.zig               # Runtime initialization
│   ├── bun.js.zig                # bun.js module root
│   ├── bake.zig                  # Bake module root
│   ├── bunfig.zig                # bunfig.toml parser
│   ├── options.zig               # Build/runtime options
│   ├── logger.zig                # Logging
│   ├── output.zig                # Output formatting
│   ├── fmt.zig                   # Formatting utilities
│   ├── url.zig                   # URL parsing
│   ├── sha.zig                   # SHA hashing
│   ├── hmac.zig                  # HMAC
│   ├── base64/                   # Base64 encoding
│   ├── unicode/                  # Unicode utilities
│   ├── zlib.zig                  # zlib compression
│   ├── brotli.zig                # Brotli compression
│   ├── HTMLScanner.zig           # HTML scanner
│   ├── Watcher.zig               # File watcher
│   ├── watcher/
│   ├── work_pool.zig             # Work pool
│   ├── pool.zig                  # Object pool
│   ├── ptr.zig                   # Pointer utilities
│   ├── ptr/
│   ├── memory.zig                # Memory utilities
│   ├── safety.zig                # Safety checks
│   ├── safety/
│   ├── analytics.zig             # Analytics
│   ├── analytics/
│   ├── perf.zig                  # Performance utilities
│   ├── Progress.zig              # Progress reporting
│   ├── StandaloneModuleGraph.zig # Single-file executable graph
│   ├── patch.zig                 # Patch file support
│   ├── ast.zig                   # AST types
│   ├── ast/
│   ├── import_record.zig         # Import record
│   ├── defines.zig               # Define substitution
│   ├── linker.zig                # Linker
│   ├── router.zig                # File system router
│   ├── api/                      # Generated API types
│   ├── deps/                     # Vendored C/C++ dependencies
│   ├── vm/                       # VM utilities
│   └── ...
│
├── packages/                     # npm packages shipped with Bun
│   ├── bun-types/                # @types/bun TypeScript definitions
│   │   ├── bun.d.ts              # Main Bun namespace types
│   │   ├── serve.d.ts            # Bun.serve / WebSocket types
│   │   ├── sqlite.d.ts           # bun:sqlite types
│   │   ├── ffi.d.ts              # bun:ffi types
│   │   ├── sql.d.ts              # Bun.sql (PostgreSQL) types
│   │   ├── shell.d.ts            # Bun.$ shell types
│   │   ├── redis.d.ts            # Bun.redis types
│   │   ├── s3.d.ts               # Bun.s3 types
│   │   ├── test.d.ts             # bun:test types
│   │   ├── globals.d.ts          # Global types
│   │   ├── fetch.d.ts            # fetch() extensions
│   │   ├── html-rewriter.d.ts    # HTMLRewriter types
│   │   ├── jsc.d.ts              # JSC internals
│   │   └── ...
│   ├── bun-usockets/             # uSockets bindings
│   ├── bun-uws/                  # uWebSockets bindings
│   ├── bun-types/                # TypeScript type definitions
│   ├── bun-vscode/               # VS Code extension
│   ├── bun-wasm/                 # WASM build
│   ├── bun-lambda/               # AWS Lambda adapter
│   ├── bun-debug-adapter-protocol/
│   ├── bun-inspector-protocol/
│   ├── bun-inspector-frontend/
│   ├── bun-error/                # Error page
│   ├── bun-native-bundler-plugin-api/  # Rust native plugin API
│   ├── bun-native-plugin-rs/     # Rust plugin SDK
│   ├── bun-plugin-svelte/        # Svelte plugin
│   ├── bun-plugin-yaml/          # YAML plugin
│   └── bun-release/              # Release tooling
│
├── cmake/                        # CMake build modules
│   ├── targets/                  # Build targets
│   ├── tools/                    # Tool setup (Zig, Rust, LLVM, etc.)
│   ├── analysis/                 # Static analysis (clang-tidy, etc.)
│   └── scripts/                  # Build scripts
│
├── test/                         # Test suite
├── bench/                        # Benchmarks
├── docs/                         # Documentation source
├── scripts/                      # Development scripts
├── misctools/                    # Miscellaneous tools
├── completions/                  # Shell completions
├── patches/                      # Dependency patches
├── CMakeLists.txt                # Root CMake build file
├── build.zig                     # Zig build file
├── package.json                  # Root package.json
├── bunfig.toml                   # Bun configuration
├── rust-toolchain.toml           # Rust toolchain pin
├── flake.nix                     # Nix flake
└── README.md
```

## Code Organization Patterns

- **Zig modules as structs**: Most Zig files define a single primary type using `const Foo = @This()`. This is the idiomatic Zig pattern for "class-like" modules.
- **Bindgen**: TypeScript `.bind.ts` and `.bindv2.ts` files define the JS↔Zig binding schema. The `codegen/` directory generates C++ glue code from these specs.
- **`.classes.ts` files**: Define JS class shapes (methods, getters, setters) that get code-generated into C++ bindings.
- **Ref-counting**: Most heap-allocated objects use `bun.ptr.RefCount` for deterministic memory management.
- **Thread-local heaps**: The bundler uses mimalloc thread-local heaps as arena allocators for parse/link tasks.
- **`bun.js/api/`**: All `Bun.*` JavaScript APIs are implemented here, with `BunObject.zig` as the central registry.
- **`bun.js/node/`**: Node.js compatibility layer — each Node.js built-in module has a corresponding Zig file.
- **`bun.js/webcore/`**: Web platform APIs (Blob, fetch, Request, Response, ReadableStream, TextEncoder, Crypto, etc.).
- **`packages/bun-types/`**: The canonical TypeScript type definitions for all Bun APIs, organized by feature area.
