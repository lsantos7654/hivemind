# Bun — Code Structure

## Annotated Directory Tree

```
bun/
├── src/                          # Primary source code (Zig, C++)
│   ├── bun.zig                   # Root module: allocators, Environment, error types
│   ├── main.zig                  # Entry point: crash handler, signals, CLI dispatch
│   ├── cli.zig                   # CLI argument parsing and command routing (76K lines)
│   ├── transpiler.zig            # TypeScript/JSX → JS transpilation (71K lines)
│   ├── fmt.zig                   # Code formatter (66K lines)
│   ├── options.zig               # Configuration and CLI options (87K lines)
│   ├── logger.zig                # Logging framework (55K lines)
│   ├── http.zig                  # HTTP server implementation (114K lines)
│   ├── router.zig                # FileSystemRouter (71K lines)
│   ├── fs.zig                    # File system operations (78K lines)
│   ├── sys.zig                   # System call wrappers / platform abstractions (157K)
│   ├── allocators.zig            # Memory allocators (mimalloc, debug, zero) (34K)
│   ├── js_lexer.zig              # JavaScript tokenizer/lexer (143K lines)
│   ├── js_parser.zig             # JavaScript parser (47K lines)
│   ├── js_printer.zig            # AST → JavaScript code generation (258K lines)
│   ├── patch.zig                 # npm patch functionality (62K lines)
│   ├── tracy.zig                 # Tracy profiler integration
│   │
│   ├── bun.js/                   # JavaScript runtime and JSC integration
│   │   ├── VirtualMachine.zig    # Core JS VM lifecycle management
│   │   ├── ModuleLoader.zig      # Module loading, caching, resolution dispatch
│   │   ├── event_loop.zig        # Event loop (tasks, microtasks, timers)
│   │   ├── jsc.zig               # JavaScriptCore Zig bindings
│   │   ├── ConsoleObject.zig     # console.{log,warn,error,...} (160K lines)
│   │   ├── HardcodedModule.zig   # Built-in module registry (bun:*, node:*)
│   │   ├── hot_reloader.zig      # Hot Module Replacement (HMR)
│   │   ├── ipc.zig               # Inter-process communication
│   │   ├── webWorker.zig         # Worker threads
│   │   ├── api/                  # API implementations (Server, WebSocket, etc.)
│   │   └── bindings/             # C++ ↔ JSC integration layer
│   │       ├── bindings.cpp      # Main C++ JSC bindings (250K lines)
│   │       ├── BunDebugger.cpp   # Chrome DevTools Protocol debugger
│   │       ├── BunCPUProfiler.cpp # CPU profiling
│   │       ├── headers.h         # Cross-language header declarations
│   │       └── *.cpp / *.h       # Domain-specific bindings
│   │
│   ├── bundler/                  # Bundler pipeline
│   │   ├── bundle_v2.zig         # Main bundler (entry: Bundler.bundle())
│   │   ├── Graph.zig             # Module dependency graph
│   │   ├── Chunk.zig             # Output chunk generation
│   │   ├── LinkerContext.zig     # Linker state and orchestration
│   │   ├── LinkerGraph.zig       # Linking phase: tree shaking, scope hoisting
│   │   ├── BundleThread.zig      # Parallel parse/link thread pool worker
│   │   ├── ParseTask.zig         # Per-file parse task
│   │   ├── entry_points.zig      # Entry point detection and handling
│   │   └── barrel_imports.zig    # Barrel import optimization (re-export collapsing)
│   │
│   ├── cli/                      # CLI command implementations
│   │   ├── Arguments.zig         # Top-level argument parsing (84K lines)
│   │   ├── build_command.zig     # `bun build`
│   │   ├── install_command.zig   # `bun install`
│   │   ├── add_command.zig       # `bun add`
│   │   ├── remove_command.zig    # `bun remove`
│   │   ├── init_command.zig      # `bun init`
│   │   ├── create_command.zig    # `bun create` (108K lines)
│   │   ├── bunx_command.zig      # `bunx` package runner
│   │   ├── pack_command.zig      # `bun pack`
│   │   ├── audit_command.zig     # `bun audit`
│   │   ├── run_command.zig       # `bun run`
│   │   ├── test_command.zig      # `bun test`
│   │   ├── upgrade_command.zig   # `bun upgrade`
│   │   └── exec.zig              # Process execution helpers
│   │
│   ├── install/                  # Package manager
│   │   ├── lockfile.zig          # bun.lock binary format (82K lines)
│   │   ├── PackageInstaller.zig  # Install orchestration (73K lines)
│   │   ├── PackageInstall.zig    # Single package installation (67K lines)
│   │   ├── npm.zig               # npm registry HTTP client (126K lines)
│   │   ├── dependency.zig        # Dependency spec parsing/resolution (54K lines)
│   │   ├── hosted_git_info.zig   # Git URL parsing / git dependency handling (68K)
│   │   ├── isolated_install.zig  # Isolated (hoisted-less) installs (58K lines)
│   │   ├── resolution.zig        # Resolution metadata types
│   │   └── semver.zig            # Semantic versioning parser
│   │
│   ├── resolver/                 # Module resolution engine
│   │   ├── resolver.zig          # Main resolver (Node.js-compatible) (201K lines)
│   │   ├── resolve_path.zig      # Platform-aware path resolution (73K lines)
│   │   ├── package_json.zig      # package.json parsing and exports resolution (94K)
│   │   └── tsconfig_json.zig     # tsconfig.json parsing and path aliases (22K)
│   │
│   ├── api/                      # Public API schema definitions
│   │   └── schema.zig            # API types and serialization (98K lines)
│   │
│   ├── js/                       # Built-in JavaScript/TypeScript modules
│   │   ├── bun/                  # Bun-specific JS modules
│   │   │   ├── *.ts              # Bun.* namespace implementations
│   │   │   └── *.js
│   │   ├── node/                 # Node.js compatibility shims
│   │   │   ├── fs.ts             # node:fs polyfill
│   │   │   ├── path.ts           # node:path
│   │   │   ├── crypto.ts         # node:crypto
│   │   │   └── *.ts / *.js       # Other node: modules
│   │   ├── internal/             # Internal runtime utilities (not user-facing)
│   │   ├── eval/                 # eval() support
│   │   ├── builtins.d.ts         # Type definitions for built-in APIs (39K lines)
│   │   └── private.d.ts          # Internal types
│   │
│   ├── sql/                      # SQLite integration
│   │   └── sqlite.zig            # bun:sqlite implementation
│   │
│   ├── valkey/                   # Redis/Valkey client
│   ├── s3/                       # AWS S3 client
│   ├── shell/                    # Bun.$ shell implementation
│   │   └── interpreter.zig       # Shell AST interpreter
│   ├── test/                     # Test runner infrastructure
│   │   └── runner.zig            # bun test runner
│   ├── watcher/                  # File system watching
│   │   ├── kqueue.zig            # macOS FSEvents / kqueue
│   │   └── inotify.zig           # Linux inotify
│   ├── css/                      # CSS parsing/handling
│   ├── unicode/                  # Unicode tables and utilities
│   ├── napi/                     # Node-API (N-API) compatibility
│   │   └── napi.zig              # N-API implementation
│   ├── async/                    # Async/await support primitives
│   └── windows.zig               # Windows-specific system calls (207K lines)
│
├── packages/                     # Published npm packages
│   ├── bun-types/                # TypeScript type definitions for Bun
│   ├── @types/bun/               # Alternative @types package
│   ├── bun-debug-adapter-protocol/ # Chrome DAP integration
│   ├── bun-inspector-protocol/   # Inspector/DevTools protocol
│   ├── bun-error/                # Error display utilities
│   ├── bun-native-bundler-plugin-api/ # Native (N-API) bundler plugins
│   ├── bun-plugin-svelte/        # Svelte framework plugin
│   ├── bun-plugin-yaml/          # YAML loader plugin
│   ├── bun-usockets/             # µSockets (WebSocket transport)
│   ├── bun-uws/                  # µWebSockets (WebSocket server)
│   ├── bun-vscode/               # VS Code extension
│   ├── bun-wasm/                 # WebAssembly builds
│   └── bun-lambda/               # AWS Lambda runtime
│
├── test/                         # Test suite
│   ├── js/                       # JavaScript API tests
│   │   ├── bun/                  # Tests for Bun-specific APIs
│   │   ├── node/                 # Node.js compatibility tests
│   │   ├── web/                  # Web platform API tests
│   │   └── internal/             # Internal tests
│   ├── cli/                      # CLI command tests
│   │   ├── install/              # Package manager tests
│   │   ├── run/                  # `bun run` tests
│   │   └── test/                 # `bun test` runner tests
│   ├── bundler/                  # Bundler/transpiler unit tests
│   ├── bake/                     # Dev server / HMR tests
│   ├── integration/              # End-to-end integration tests
│   ├── regression/               # Issue-number regression tests
│   │   └── issue/                # issue/XXXX.test.ts format
│   ├── napi/                     # N-API compatibility tests
│   ├── v8/                       # V8 C++ API compatibility tests
│   ├── snapshots/                # Snapshot test artifacts
│   └── harness.ts                # Shared test utilities (bunExe, bunEnv, tempDir)
│
├── docs/                         # User-facing documentation (MDX)
│   ├── index.mdx                 # Homepage
│   ├── installation.mdx          # Install instructions
│   ├── quickstart.mdx            # Getting started
│   ├── api/                      # API reference docs
│   ├── bundler/                  # Bundler docs
│   ├── runtime/                  # Runtime docs
│   ├── pm/                       # Package manager docs
│   ├── test/                     # Test runner docs
│   └── guides/                   # How-to guides
│
├── scripts/                      # Build and utility scripts
│   ├── utils.ts                  # Shared script utilities
│   ├── buildkite/                # CI pipeline scripts
│   └── *.ts / *.sh               # Various build helpers
│
├── .buildkite/                   # Buildkite CI/CD pipeline
│   └── pipelines/                # Pipeline YAML definitions
│
├── bench/                        # Benchmarks
│   ├── snippet/                  # Micro-benchmarks
│   └── linter/                   # Linting benchmarks
│
├── build.zig                     # Zig build system root
├── package.json                  # Workspace root (version 1.3.11)
├── tsconfig.base.json            # Base TypeScript config
├── tsconfig.json                 # Root TypeScript config
├── CLAUDE.md                     # Developer guide / contributor notes
└── README.md                     # Project README
```

## Module and Package Organization

### Core Principle: Feature-Based Organization

Bun organizes source code by feature domain rather than by language or layer. Each major capability (install, bundler, resolver, cli) gets its own top-level directory under `src/`. This makes it easy to find all code related to a feature.

### Language Distribution

- **Zig** (~681K+ lines): Core runtime, bundler, package manager, transpiler, all I/O
- **C++** (~300K+ lines): JavaScriptCore bindings (`src/bun.js/bindings/`)
- **TypeScript** (~39K+ lines): Built-in JS module implementations (`src/js/`), type definitions
- **JavaScript**: Some built-in modules in `src/js/`

### Key Files by Role

| Role | File |
|------|------|
| Binary entry point | `src/main.zig` |
| Global namespace/utilities | `src/bun.zig` |
| CLI parsing root | `src/cli/Arguments.zig` |
| JS VM core | `src/bun.js/VirtualMachine.zig` |
| Module loading | `src/bun.js/ModuleLoader.zig` |
| Bundler entry | `src/bundler/bundle_v2.zig` |
| Package install | `src/install/PackageInstaller.zig` |
| Module resolution | `src/resolver/resolver.zig` |
| Type definitions | `packages/bun-types/` |
| Test utilities | `test/harness.ts` |

## Code Organization Patterns

### `.classes.ts` Bindgen Schema Files
Bun uses code generation to produce type-safe C++ ↔ JavaScript class bindings. Files named `*.classes.ts` define the schema for JS class prototypes backed by Zig/C++. Examples:
- `src/bun.js/api/jest.classes.ts` — test runner classes
- `src/bun.js/api/sql.classes.ts` — SQLite/PostgreSQL classes
- `src/bun.js/api/server.classes.ts` — HTTP server classes

### Platform Abstraction via `sys.zig`
All system calls flow through `src/sys.zig`. Platform-specific code is gated by `builtin.os.tag` at compile time. Windows-specific implementations are in `src/windows.zig`.

### Built-in JS Modules (`src/js/`)
JavaScript and TypeScript files in `src/js/` are compiled into the binary. The `node/` subdirectory contains compatibility shims for Node.js APIs. The `bun/` subdirectory contains Bun-specific module implementations. These are referenced via `bun:*` and `node:*` import specifiers.

### Test Harness Pattern
All test files import from `harness.ts` which provides:
- `bunExe()` — path to the current bun executable under test
- `bunEnv` — environment variables for subprocess spawning
- `tempDir()` — isolated temporary directories
- Snapshot normalization utilities
