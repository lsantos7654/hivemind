# Bazel Code Structure and Organization

## Complete Directory Tree Overview

The Bazel repository is organized into several major top-level directories:

```
bazel/
├── src/                      # Main source code
│   ├── main/                 # Core implementation
│   │   ├── cpp/             # C++ client launcher
│   │   ├── java/            # Java server implementation
│   │   ├── native/          # Native JNI code
│   │   ├── protobuf/        # Protocol buffer definitions
│   │   ├── starlark/        # Starlark built-in rules
│   │   └── tools/           # Internal build tools
│   ├── test/                # Test suites
│   └── tools/               # Developer tools
├── tools/                    # Bundled tools and runtime support
│   ├── jdk/                 # Java toolchain definitions
│   ├── cpp/                 # C++ toolchain support
│   ├── python/              # Python runtime support
│   ├── android/             # Android tools
│   ├── osx/                 # macOS-specific tools
│   └── build_defs/          # Build definition utilities
├── third_party/             # External dependencies
│   ├── java/                # Third-party Java libraries
│   ├── grpc/                # gRPC dependencies
│   ├── protobuf/            # Protocol Buffers
│   └── ijar/                # Interface JAR tool
├── scripts/                 # Build and release scripts
│   ├── bootstrap/           # Bootstrap build scripts
│   ├── packages/            # Packaging scripts
│   └── release/             # Release automation
├── examples/                # Example projects
├── site/                    # Documentation website source
├── MODULE.bazel             # Bzlmod module definition
├── BUILD                    # Root BUILD file
├── WORKSPACE                # Legacy workspace (deprecated)
├── compile.sh               # Bootstrap compilation script
└── .bazelrc                 # Default Bazel configuration
```

## Main Source Directory Structure (src/main)

### C++ Client Layer (src/main/cpp)

The C++ launcher provides the entry point for the Bazel command-line tool:

```
src/main/cpp/
├── main.cc                  # Entry point for Bazel binary
├── blaze.cc/.h              # Main client logic, server management
├── blaze_util.cc/.h         # Utility functions for client
├── blaze_util_posix.cc      # POSIX-specific utilities
├── blaze_util_darwin.cc     # macOS-specific utilities
├── blaze_util_linux.cc      # Linux-specific utilities
├── blaze_util_windows.cc    # Windows-specific utilities
├── startup_options.cc/.h    # Startup option parsing
├── bazel_startup_options.cc/.h  # Bazel-specific startup options
├── option_processor.cc/.h   # Command-line option processing
├── rc_file.cc/.h            # .bazelrc file parsing
├── archive_utils.cc/.h      # Archive extraction utilities
└── util/                    # Common utilities
    ├── file.cc/.h           # File system operations
    ├── strings.cc/.h        # String manipulation
    ├── logging.cc/.h        # Logging infrastructure
    └── path.cc/.h           # Path manipulation
```

The C++ client is responsible for:
- Parsing startup options from .bazelrc files and command line
- Starting and managing the Bazel server process
- Establishing gRPC connection to the server
- Extracting embedded tools from the Bazel binary
- Platform-specific file system and process operations

### Java Server Core (src/main/java/com/google/devtools)

The Java server contains the core build system logic:

```
src/main/java/com/google/devtools/
├── build/
│   ├── lib/                 # Main Bazel library
│   │   ├── runtime/         # Runtime and command infrastructure
│   │   │   ├── BlazeRuntime.java       # Core runtime orchestration
│   │   │   ├── BlazeModule.java        # Module extension point
│   │   │   ├── CommandEnvironment.java # Per-command context
│   │   │   ├── commands/               # Built-in commands
│   │   │   └── mobileinstall/          # Mobile installation
│   │   ├── packages/        # Package loading and BUILD file parsing
│   │   │   ├── Package.java            # Package representation
│   │   │   ├── Target.java             # Build target abstraction
│   │   │   ├── Rule.java               # Rule instance
│   │   │   ├── RuleClass.java          # Rule definition
│   │   │   ├── PackageFactory.java     # BUILD file interpreter
│   │   │   ├── StarlarkNativeModule.java # Native Starlark APIs
│   │   │   └── metrics/                # Package loading metrics
│   │   ├── analysis/        # Build analysis phase
│   │   │   ├── ConfiguredTarget.java   # Configured target
│   │   │   ├── RuleContext.java        # Rule analysis context
│   │   │   ├── AnalysisResult.java     # Analysis output
│   │   │   ├── config/                 # Build configurations
│   │   │   ├── constraints/            # Platform constraints
│   │   │   └── test/                   # Test infrastructure
│   │   ├── actions/         # Build action system
│   │   │   ├── Action.java             # Action interface
│   │   │   ├── Artifact.java           # Build artifact
│   │   │   ├── ActionExecutionContext.java
│   │   │   ├── ActionGraph.java        # Action dependency graph
│   │   │   ├── ActionLookupKey.java    # Skyframe key for actions
│   │   │   └── cache/                  # Action cache
│   │   ├── exec/            # Action execution
│   │   │   ├── SpawnRunner.java        # Spawn execution interface
│   │   │   ├── SpawnStrategy.java      # Execution strategy
│   │   │   ├── BinTools.java           # Binary tools management
│   │   │   ├── local/                  # Local execution
│   │   │   └── AbstractSpawnStrategy.java
│   │   ├── skyframe/        # Skyframe-specific implementations
│   │   │   ├── SkyframeExecutor.java   # Main Skyframe entry point
│   │   │   ├── PackageFunction.java    # Package loading function
│   │   │   ├── ConfiguredTargetFunction.java # Target analysis
│   │   │   ├── ActionExecutionFunction.java  # Action execution
│   │   │   ├── BuildDriver.java        # Build orchestration
│   │   │   └── serialization/          # Serialization support
│   │   ├── rules/           # Built-in rule implementations
│   │   │   ├── java/                   # Java rules
│   │   │   ├── cpp/                    # C++ rules
│   │   │   ├── python/                 # Python rules
│   │   │   ├── android/                # Android rules
│   │   │   ├── apple/                  # Apple platform rules
│   │   │   ├── proto/                  # Protocol buffer rules
│   │   │   ├── genrule/                # Generic rule
│   │   │   └── test/                   # Test rules
│   │   ├── remote/          # Remote execution and caching
│   │   │   ├── RemoteModule.java       # Remote execution module
│   │   │   ├── GrpcRemoteExecutor.java # gRPC executor client
│   │   │   ├── GrpcCacheClient.java    # Remote cache client
│   │   │   ├── ByteStreamUploader.java # Byte stream upload
│   │   │   ├── disk/                   # Disk cache
│   │   │   ├── http/                   # HTTP cache backend
│   │   │   └── circuitbreaker/         # Circuit breaker pattern
│   │   ├── query2/          # Query language implementations
│   │   │   ├── engine/                 # Query engine
│   │   │   ├── query/                  # Standard query (query)
│   │   │   ├── cquery/                 # Configured query (cquery)
│   │   │   └── aquery/                 # Action query (aquery)
│   │   ├── repository/      # External repository management
│   │   │   ├── RepositoryFunction.java
│   │   │   └── downloader/             # Repository downloader
│   │   ├── bazel/           # Bazel-specific implementations
│   │   │   ├── BazelMain.java          # Bazel entry point
│   │   │   ├── BazelRepositoryModule.java
│   │   │   ├── bzlmod/                 # Bzlmod module system
│   │   │   ├── rules/                  # Bazel-specific rules
│   │   │   └── coverage/               # Coverage support
│   │   ├── sandbox/         # Sandboxed execution
│   │   │   ├── SandboxModule.java
│   │   │   ├── LinuxSandboxedSpawnRunner.java
│   │   │   ├── DarwinSandboxedSpawnRunner.java
│   │   │   └── WindowsSandboxedSpawnRunner.java
│   │   ├── worker/          # Persistent worker support
│   │   │   ├── WorkerModule.java
│   │   │   ├── WorkerSpawnRunner.java
│   │   │   └── WorkerPool.java
│   │   ├── standalone/      # Standalone execution strategy
│   │   ├── dynamic/         # Dynamic execution (local+remote)
│   │   ├── vfs/             # Virtual file system
│   │   │   ├── FileSystem.java
│   │   │   ├── Path.java
│   │   │   ├── DigestHashFunction.java
│   │   │   └── inmemoryfs/             # In-memory file system
│   │   ├── cmdline/         # Command-line label parsing
│   │   ├── events/          # Event system
│   │   ├── profiler/        # Performance profiling
│   │   ├── metrics/         # Metrics collection
│   │   ├── clock/           # Clock abstraction
│   │   ├── util/            # Utilities
│   │   ├── shell/           # Shell command execution
│   │   ├── unix/            # Unix-specific code
│   │   ├── windows/         # Windows-specific code
│   │   └── server/          # gRPC server implementation
│   ├── skyframe/            # Skyframe evaluation framework
│   │   ├── SkyFunction.java            # Function interface
│   │   ├── SkyValue.java               # Value interface
│   │   ├── SkyKey.java                 # Key interface
│   │   ├── Evaluator.java              # Core evaluator
│   │   ├── ParallelEvaluator.java      # Parallel evaluation
│   │   ├── InMemoryGraph.java          # In-memory graph
│   │   ├── Version.java                # Graph versioning
│   │   └── state/                      # State machine framework
│   └── docgen/              # Documentation generation
├── common/
│   └── options/             # Command-line option framework
│       ├── OptionsParser.java
│       ├── Option.java
│       ├── OptionsBase.java
│       └── Converters.java
└── net/starlark/java/       # Starlark language implementation
    ├── eval/                # Evaluation engine
    │   ├── Starlark.java               # Main entry point
    │   ├── StarlarkThread.java         # Execution context
    │   ├── StarlarkFunction.java       # Function representation
    │   ├── StarlarkInt.java            # Integer type
    │   ├── StarlarkList.java           # List type
    │   ├── StarlarkDict.java           # Dictionary type
    │   └── Module.java                 # Module namespace
    ├── syntax/              # Parser and AST
    │   ├── Parser.java                 # Starlark parser
    │   ├── Lexer.java                  # Lexical analyzer
    │   ├── Expression.java             # AST nodes
    │   └── Resolver.java               # Name resolution
    ├── lib/                 # Built-in functions and types
    │   ├── StarlarkInt.java
    │   └── StarlarkJson.java
    ├── annot/               # Annotations for Starlark APIs
    └── cmd/                 # Command-line REPL
```

### Starlark Built-ins (src/main/starlark/builtins_bzl)

Built-in Starlark rules and implementations:

```
src/main/starlark/builtins_bzl/
├── common/
│   ├── cc/                  # C++ rule implementations
│   ├── java/                # Java rule implementations
│   ├── python/              # Python rule implementations
│   ├── proto/               # Protocol buffer rules
│   ├── objc/                # Objective-C rules
│   └── exports.bzl          # Exported symbols
└── bazel/                   # Bazel-specific builtins
```

## Tools Directory (tools/)

Runtime support libraries and toolchain definitions:

```
tools/
├── jdk/                     # Java Development Kit support
│   ├── BUILD                # JDK toolchain definitions
│   └── default_java_toolchain.bzl
├── cpp/                     # C++ toolchain
│   ├── cc_configure.bzl     # C++ auto-configuration
│   ├── cc_toolchain_config.bzl
│   └── unix_cc_configure.bzl
├── python/                  # Python runtime
│   ├── runfiles/            # Runfiles library
│   └── toolchain.bzl
├── android/                 # Android SDK/NDK support
├── osx/                     # macOS-specific tools
├── build_defs/              # Build definition utilities
│   ├── repo/                # Repository rules
│   ├── pkg/                 # Packaging rules
│   └── hash/                # Hash utilities
├── bash/                    # Bash runfiles library
├── test/                    # Test infrastructure
├── zip/                     # ZIP file utilities
└── defaults/                # Default settings
```

## Key Files and Their Roles

### Build Configuration Files

- **MODULE.bazel**: Declares Bazel's own dependencies using the Bzlmod system. Specifies versions for protobuf, gRPC, Skylib, and dozens of other dependencies.

- **BUILD**: Root BUILD file that defines top-level targets including the main Bazel binary, distribution archives, and license declarations.

- **.bazelrc**: Default Bazel configuration with recommended flags for building Bazel itself, including compiler options, test settings, and platform configurations.

- **repositories.bzl**: Defines external repository dependencies, particularly for embedded JDK distributions used when bundling Bazel with Java runtime.

### Bootstrap Scripts

- **compile.sh**: Main bootstrap script that builds Bazel from scratch without requiring Bazel. Can also use an existing Bazel binary to build a new version.

- **scripts/bootstrap/compile.sh**: Lower-level bootstrap that compiles just enough Java code to get a minimal working Bazel binary.

- **scripts/bootstrap/bootstrap.sh**: Handles the full bootstrap process including building native code and packaging.

### Entry Points

- **src/main/cpp/main.cc**: C++ entry point for the `bazel` command. Parses startup options and launches the server.

- **src/main/java/com/google/devtools/build/lib/bazel/BazelMain.java**: Java entry point for the Bazel server. Initializes all modules and starts the runtime.

- **src/main/java/com/google/devtools/build/lib/runtime/BlazeRuntime.java**: Core runtime that orchestrates the entire build process, manages the server lifecycle, and coordinates between modules.

## Code Organization Patterns

### Modular Architecture

Bazel uses a module system where functionality is organized into BlazeModule implementations. Each module:
- Registers command-line options
- Provides extension hooks at various lifecycle points
- Can contribute command implementations
- Registers strategies for action execution

Over 50 modules provide features like:
- Remote execution (RemoteModule)
- Coverage reporting (BazelCoverageReportModule)
- Profiling (CommandProfilerModule)
- Platform-specific behavior (BazelFileSystemModule)

### Skyframe-Based Computation

All incremental computation uses Skyframe, a framework for parallel memoized evaluation:
- Each computation is a SkyFunction that takes a SkyKey and returns a SkyValue
- Dependencies are declared dynamically during computation
- Skyframe automatically tracks dependencies and recomputes only what's needed
- Examples: PackageFunction, ConfiguredTargetFunction, ActionExecutionFunction

### Package/Target/Action Model

Bazel's build model has clear separation of concerns:
1. **Package Loading**: Parse BUILD files into Package objects containing Target instances
2. **Analysis**: Transform Targets into ConfiguredTargets with resolved dependencies
3. **Action Graph Construction**: ConfiguredTargets produce Actions representing build steps
4. **Execution**: Actions are executed to produce Artifacts

### Virtual File System Abstraction

All file operations go through the VFS abstraction (FileSystem, Path):
- Enables in-memory file systems for testing
- Supports case-insensitive file systems
- Allows file system overlays and unions
- Provides consistent behavior across platforms

### Separation of Bazel vs Blaze

The codebase maintains separation between:
- **lib**: Core build system logic, platform-agnostic
- **bazel**: Bazel-specific implementations and entry points

This allows the core to potentially support other build systems while keeping Bazel-specific behavior isolated.
