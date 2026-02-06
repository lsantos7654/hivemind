# Bazel Code Structure

## Complete Directory Tree

```
bazel/
├── .bazelci/               # Bazel CI configuration
├── .devcontainer/          # Development container setup
├── .gemini/                # Gemini AI configuration
├── .github/                # GitHub Actions, issue templates, workflows
├── docs/                   # Documentation in MDX format
├── examples/               # Example projects (cpp, java, python, go, shell, etc.)
├── scripts/                # Build and release scripts
├── site/                   # Website content
├── src/                    # Main source code
│   ├── conditions/         # Platform/feature detection
│   ├── java_tools/         # Java-specific build tools
│   │   ├── buildjar/       # Java compilation wrapper
│   │   ├── import_deps_checker/  # Dependency verification
│   │   ├── junitrunner/    # JUnit test runner
│   │   └── singlejar/      # JAR merging tool
│   ├── main/               # Core Bazel implementation
│   │   ├── cpp/            # C++ client (launcher/wrapper)
│   │   ├── java/           # Main Java implementation
│   │   ├── native/         # JNI native code
│   │   ├── protobuf/       # Protocol buffer definitions
│   │   ├── res/            # Resources (icons, manifests)
│   │   ├── starlark/       # Starlark built-in definitions
│   │   └── tools/          # Runtime tools
│   ├── test/               # Test suite
│   │   ├── cpp/            # C++ tests
│   │   ├── java/           # Java tests
│   │   ├── native/         # Native code tests
│   │   ├── py/             # Python tests
│   │   ├── shell/          # Shell integration tests
│   │   └── testdata/       # Test fixtures
│   └── tools/              # Additional build tools
│       ├── bzlmod/         # Bzlmod module system utilities
│       ├── diskcache/      # Disk cache utilities
│       ├── execlog/        # Execution log tools
│       ├── launcher/       # Windows launcher
│       ├── remote/         # Remote execution tools
│       ├── singlejar/      # Single JAR tool
│       └── workspacelog/   # Workspace logging
├── third_party/            # Third-party dependencies
│   ├── allocation_instrumenter/  # Memory profiling
│   ├── asm/                # ASM bytecode library
│   ├── chicory/            # WebAssembly runtime
│   ├── def_parser/         # Windows DEF file parser
│   ├── googleapis/         # Google API definitions
│   ├── grpc/               # gRPC C++ library
│   ├── grpc-java/          # gRPC Java library
│   ├── ijar/               # Interface JAR tool
│   ├── jarjar/             # JAR repackaging tool
│   ├── java/               # Java libraries
│   ├── pprof/              # Performance profiling
│   ├── protobuf/           # Protocol Buffers
│   ├── py/                 # Python libraries
│   └── remoteapis/         # Remote Execution API definitions
└── tools/                  # Build rule definitions and toolchains
    ├── allowlists/         # Feature allowlists
    ├── android/            # Android build rules
    ├── aquery_differ/      # Action graph comparison
    ├── bash/               # Bash runfiles library
    ├── build_defs/         # Build definition utilities
    ├── build_rules/        # Legacy build rules
    ├── buildstamp/         # Build timestamp injection
    ├── compliance/         # License compliance
    ├── coverage/           # Code coverage support
    ├── cpp/                # C++ toolchain and rules
    ├── ctexplain/          # Configuration transition explainer
    ├── distributions/      # Distribution packaging
    ├── genrule/            # Generic rule support
    ├── j2objc/             # Java to Objective-C transpiler
    ├── java/               # Java rules and toolchain
    ├── jdk/                # JDK configuration
    ├── objc/               # Objective-C/iOS rules
    ├── osx/                # macOS-specific rules
    ├── platforms/          # Platform definitions
    ├── proto/              # Protocol buffer rules
    ├── python/             # Python rules
    ├── sh/                 # Shell rules
    ├── test/               # Test infrastructure
    └── zip/                # ZIP/JAR utilities
```

## Module and Package Organization

### Core Java Implementation (`src/main/java/com/google/devtools/build/lib/`)

The main Bazel implementation is organized into approximately 50 major subsystems:

**Runtime and Execution Core**:
- `runtime/` - BlazeRuntime, command infrastructure, module system
- `buildtool/` - BuildTool, main build execution logic
- `exec/` - Action execution strategies and spawning
- `actions/` - Action types and action graph construction
- `skyframe/` - Incremental evaluation framework (Skyframe)

**Build Graph and Analysis**:
- `packages/` - Package, Target, Rule definitions and BUILD file parsing
- `analysis/` - Configured target graph, analysis phase logic
- `rules/` - Built-in rules (Java, C++, Python, Android, iOS, etc.)
- `cmdline/` - Label and target pattern parsing
- `query2/` - Query language implementation

**Language and Extension System**:
- `bazel/` - Bazel-specific implementations (vs. generic Blaze)
- `bazel/bzlmod/` - Bzlmod module system
- `bazel/rules/` - Bazel-specific rule implementations
- `starlarkbuildapi/` - Starlark API definitions
- `starlarkdebug/` - Starlark debugger
- `starlarkdocextract/` - Documentation extraction

**Remote Execution and Caching**:
- `remote/` - Remote execution and caching implementation
- `authandtls/` - Authentication and TLS for remote APIs

**File System and I/O**:
- `vfs/` - Virtual file system abstraction
- `unix/`, `windows/` - Platform-specific implementations
- `io/` - I/O utilities and file system watching

**Sandboxing and Isolation**:
- `sandbox/` - Build action sandboxing (Linux, macOS, Windows)
- `worker/` - Persistent worker processes

**Build Event Protocol**:
- `buildeventstream/` - Build event streaming
- `buildeventservice/` - Build event service integration

**Utilities and Infrastructure**:
- `util/` - Common utilities
- `collect/` - Custom collections
- `concurrent/` - Concurrency utilities
- `profiler/` - Performance profiling
- `events/` - Event bus and logging
- `graph/` - Graph algorithms
- `clock/` - Time abstraction
- `shell/` - Command execution
- `server/` - Bazel server (daemon) implementation

### Starlark Language Runtime (`src/main/java/net/starlark/java/`)

The embedded Starlark interpreter:
- `eval/` - Expression evaluation, interpreter core
- `syntax/` - Parser and AST
- `lib/` - Built-in functions and types
- `annot/` - Annotations for Java-Starlark interop
- `cmd/` - Standalone Starlark command-line tool
- `spelling/` - Spell checking for error messages

### C++ Client (`src/main/cpp/`)

The native launcher that starts the Java server:
- `blaze.cc` - Main entry point
- `blaze_util.cc` - Utility functions
- `option_processor.cc` - Command-line option processing
- `rc_file.cc` - .bazelrc file parsing
- `blaze_util_*.cc` - Platform-specific implementations (Linux, Darwin, Windows, POSIX)
- `main.cc` - Program entry point
- `archive_utils.cc` - Archive extraction

### Build Rules (`tools/` and `src/main/java/.../rules/`)

**Java Rules** (`tools/java/`, `src/main/java/.../rules/java/`):
- Core rules: java_library, java_binary, java_test
- Advanced: java_import, java_plugin, java_proto_library

**C++ Rules** (`tools/cpp/`, `src/main/java/.../rules/cpp/`):
- Core rules: cc_library, cc_binary, cc_test
- Toolchain: cc_toolchain, cc_toolchain_suite
- Features: cc_import, cc_proto_library

**Python Rules** (`tools/python/`, `src/main/java/.../rules/python/`):
- py_library, py_binary, py_test
- Python toolchain configuration

**Android Rules** (`src/main/java/.../rules/android/`):
- android_library, android_binary, android_test
- APK packaging and resource processing

**Apple/iOS Rules** (`tools/objc/`, `src/main/java/.../rules/objc/`):
- objc_library, objc_binary
- ios_application, macos_application
- Apple toolchain integration

**Generic Rules**:
- genrule - Generic rule for arbitrary commands
- filegroup - File collection
- sh_binary, sh_test, sh_library - Shell scripts
- alias - Target aliasing

## Key Files and Their Roles

### Root Level Configuration

**MODULE.bazel** (18KB): Bzlmod module definition declaring Bazel's own dependencies using the new module system. Specifies ~40 direct dependencies including abseil-cpp, protobuf, grpc, rules_java, rules_python, etc.

**BUILD** (8.8KB): Root BUILD file defining Bazel's build structure, including source filegroups, distribution artifacts, and bootstrap packaging.

**compile.sh** (2.7KB): Bootstrap script for building Bazel from source without an existing Bazel binary. Orchestrates the bootstrap process.

**.bazelrc** (4.7KB): Default Bazel configuration defining remote execution settings, platform configurations, and common build flags.

### Entry Points

**src/main/java/com/google/devtools/build/lib/bazel/Bazel.java**: Main class that initializes and starts the Bazel runtime. Defines the list of BlazeModule implementations that provide Bazel's functionality.

**src/main/cpp/main.cc**: C++ entry point that launches the Java-based Bazel server process.

**src/main/java/com/google/devtools/build/lib/runtime/BlazeRuntime.java**: Core runtime that manages the build lifecycle, command dispatch, and module coordination.

**src/main/java/com/google/devtools/build/lib/buildtool/BuildTool.java**: Orchestrates the analysis and execution phases of a build.

### Critical Infrastructure

**src/main/java/com/google/devtools/build/lib/skyframe/**: Skyframe incremental computation framework - the heart of Bazel's performance. Implements a parallel evaluation DAG with automatic invalidation.

**src/main/java/com/google/devtools/build/lib/packages/PackageFactory.java**: Parses and evaluates BUILD files to create Package objects.

**src/main/java/com/google/devtools/build/lib/bazel/rules/BazelRuleClassProvider.java**: Registry of all available rule types and their implementations.

## Code Organization Patterns

**Module System**: Bazel uses a module-based architecture where functionality is added through BlazeModule implementations. Modules can contribute commands, options, rules, and lifecycle hooks. This enables features to be composed without tight coupling.

**Provider Pattern**: Information flows between rules through Provider objects (TransitiveInfoProvider), enabling type-safe communication without coupling rule implementations.

**Skyframe Pattern**: Core logic is implemented as SkyFunction instances that compute values based on dependencies, enabling automatic parallelization and incremental computation.

**Immutability**: Extensive use of immutable data structures (Guava ImmutableList, ImmutableMap, ImmutableSet) for thread safety and efficient memoization.

**Platform Abstraction**: File system operations go through the VFS abstraction layer, enabling sandboxing, remote file systems, and in-memory testing.

**Protocol Buffers**: Used for data serialization, remote communication, and persistent data structures.

**Language Separation**: The codebase maintains clear separation between the build system logic (Java), the client wrapper (C++), and the extension language (Starlark).
