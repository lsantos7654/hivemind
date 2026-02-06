# Bazel Code Structure

## Repository Overview

The Bazel repository is organized as a multi-language project with Java as the primary implementation language for the build system core, C++ for the native launcher and performance-critical components, Starlark for built-in rules and macros, and extensive test suites in Shell, Java, and Python.

## Complete Directory Tree

```
bazel/
├── .bazelci/              # Bazel CI configuration
├── .github/               # GitHub Actions workflows and issue templates
├── docs/                  # Legacy documentation (migrated to site/)
├── examples/              # Example projects (DEPRECATED - see bazelbuild/examples)
├── scripts/               # Build and release scripts
│   ├── bootstrap/         # Bootstrap build scripts (compile.sh, bootstrap.sh)
│   ├── packages/          # Package creation (deb, rpm, chocolatey, MSI)
│   ├── docs/              # Documentation generation tools
│   └── release/           # Release automation
├── site/                  # Official documentation (bazel.build website)
│   └── en/
│       ├── about/         # Project overview and roadmap
│       ├── basics/        # Core concepts (hermeticity, artifact-based builds)
│       ├── concepts/      # BUILD files, labels, platforms, visibility
│       ├── configure/     # Configuration and toolchains
│       ├── docs/          # User manual, command reference
│       ├── extending/     # Rules, macros, aspects, Starlark
│       └── external/      # Bzlmod, external dependencies
├── src/
│   ├── main/
│   │   ├── cpp/           # Native Bazel client and launcher (C++)
│   │   ├── java/          # Core Bazel implementation (Java)
│   │   │   ├── com/google/devtools/build/
│   │   │   │   ├── lib/   # Main build system library
│   │   │   │   ├── skyframe/   # Skyframe incremental evaluation
│   │   │   │   └── docgen/     # Documentation generation
│   │   │   └── net/starlark/   # Starlark language implementation
│   │   ├── native/        # Platform-specific native code (darwin, windows)
│   │   ├── protobuf/      # Protocol buffer definitions
│   │   └── starlark/      # Starlark built-in rules and builtins_bzl
│   ├── test/              # Test suites
│   │   ├── java/          # Java unit and integration tests
│   │   ├── shell/         # Shell-based integration tests
│   │   ├── py/            # Python tests (mostly for Bazel itself)
│   │   └── cpp/           # C++ unit tests
│   ├── tools/             # Build tools and utilities
│   │   ├── bzlmod/        # Bzlmod implementation tools
│   │   ├── launcher/      # Windows launcher
│   │   ├── singlejar/     # JAR combining tool
│   │   └── remote/        # Remote execution tools
│   └── java_tools/        # Java-specific build tools
│       ├── buildjar/      # Java compilation
│       ├── junitrunner/   # JUnit test runner
│       └── import_deps_checker/  # Dependency checker
├── third_party/           # Third-party dependencies and patches
├── tools/                 # Embedded tools distributed with Bazel
│   ├── android/           # Android build rules
│   ├── build_defs/        # Build definition utilities
│   ├── cpp/               # C++ toolchain configuration
│   ├── jdk/               # JDK configuration and toolchains
│   ├── python/            # Python rules
│   ├── proto/             # Protocol buffer rules
│   └── test/              # Test infrastructure
├── MODULE.bazel           # Bzlmod module definition
├── MODULE.bazel.lock      # Dependency lock file
├── BUILD                  # Root BUILD file
├── .bazelrc               # Default Bazel configuration
├── compile.sh             # Bootstrap compilation script
└── WORKSPACE              # Legacy workspace file (being phased out)
```

## Main Source Directories

### src/main/cpp/ - Native Client and Launcher

The C++ codebase implements the Bazel client binary that users invoke from the command line. It manages the server process, handles command-line parsing, and provides platform-specific implementations.

**Key Files:**
- `main.cc` - Entry point for the Bazel binary
- `blaze.cc` - Main client logic, server communication
- `option_processor.cc` - Command-line option parsing
- `startup_options.cc` - Startup option handling
- `workspace_layout.cc` - Workspace detection and configuration
- `util/` - Platform-agnostic utilities (file operations, MD5, strings, paths)

**Platform-specific subdirectories:**
- `util/` contains platform-specific implementations:
  - `file_posix.cc`, `file_windows.cc` - File system operations
  - `path_posix.cc`, `path_windows.cc` - Path manipulation
  - `errors_posix.cc`, `errors_windows.cc` - Error handling

### src/main/java/com/google/devtools/build/lib/ - Core Build System

The heart of Bazel, implementing the build system in Java. This is organized into numerous packages, each with specific responsibilities.

#### Key Packages and Their Roles:

**lib/runtime/** - Bazel server runtime
- `BlazeRuntime.java` - Main server runtime, manages the build lifecycle
- `BlazeModule.java` - Module system for extending Bazel
- `CommandDispatcher.java` - Dispatches commands to handlers
- `commands/` - Command implementations (build, test, query, run, etc.)

**lib/analysis/** - Build analysis phase
- `RuleContext.java` - Context provided to rule implementations during analysis
- `ConfiguredTarget.java` - A target with a specific configuration
- `AnalysisEnvironment.java` - Environment for rule analysis
- `Aspect.java` - Cross-cutting analysis concerns
- `actions/` - Action creation and registration

**lib/actions/** - Build action system
- `Action.java` - Interface for executable build actions
- `ActionExecutionContext.java` - Context for action execution
- `Artifact.java` - Build artifacts (inputs and outputs)
- `ActionGraph.java` - Graph of actions and their dependencies
- `SpawnAction.java` - Actions that spawn processes

**lib/packages/** - BUILD file loading and package management
- `Package.java` - Represents a loaded BUILD file
- `Rule.java` - A rule instance from a BUILD file
- `Target.java` - Base class for buildable targets
- `RuleClass.java` - Definition of a rule type
- `Attribute.java` - Rule attribute definitions
- `PackageFactory.java` - Creates Package instances from BUILD files
- `StarlarkSemanticsOptions.java` - Starlark language options

**lib/skyframe/** - Skyframe integration (Bazel-specific SkyFunctions)
- `SkyframeExecutor.java` - Main entry point for Skyframe evaluation
- `PackageFunction.java` - Loads and evaluates BUILD files
- `ConfiguredTargetFunction.java` - Analyzes configured targets
- `ActionExecutionFunction.java` - Executes actions
- `FileFunction.java` - Tracks file system state

**lib/exec/** - Action execution
- `SpawnRunner.java` - Interface for executing spawns
- `StandaloneSpawnStrategy.java` - Local execution strategy
- `BinTools.java` - Embedded tool management
- `ModuleActionContextRegistry.java` - Registers execution strategies

**lib/sandbox/** - Build sandboxing
- `SandboxModule.java` - Sandboxing infrastructure
- `LinuxSandboxedSpawnRunner.java` - Linux sandbox using namespaces
- `DarwinSandboxedSpawnRunner.java` - macOS sandbox using sandbox-exec
- `WindowsSandboxedSpawnRunner.java` - Windows sandbox

**lib/remote/** - Remote execution and caching
- `RemoteModule.java` - Remote execution module
- `RemoteExecutionService.java` - Manages remote execution
- `RemoteCache.java` - Remote caching implementation
- `GrpcRemoteExecutor.java` - gRPC-based remote execution client

**lib/query2/** - Query engine
- `engine/` - Core query evaluation engine
- `query/` - Traditional `bazel query` implementation
- `cquery/` - Configured query (cquery) implementation
- `aquery/` - Action query (aquery) implementation

**lib/rules/** - Built-in rule implementations
- `android/` - Android rules
- `apple/` - Apple platform rules (being migrated to rules_apple)
- `cpp/` - C++ rules (being migrated to rules_cc)
- `java/` - Java rules (being migrated to rules_java)
- `python/` - Python rules (being migrated to rules_python)
- `proto/` - Protocol buffer rules
- `genrule/` - Generic rule for custom commands
- `repository/` - Repository rules for external dependencies

**lib/bazel/** - Bazel-specific implementations
- `BazelMain.java` - Bazel's main entry point
- `BazelRepositoryModule.java` - Repository management
- `bzlmod/` - Bzlmod (MODULE.bazel) implementation
- `repository/` - Repository rule implementations
- `rules/` - Bazel-specific rule implementations

**lib/buildeventstream/** - Build Event Protocol (BEP)
- `BuildEventStreamer.java` - Streams build events
- `BuildEventTransport.java` - Transport for build events
- `BuildEvent.java` - Base class for build events

**lib/vfs/** - Virtual File System
- `FileSystem.java` - Abstract file system interface
- `Path.java` - File system paths
- `FileSystemUtils.java` - File system utilities
- `inmemoryfs/` - In-memory file system for testing

### src/main/java/com/google/devtools/build/skyframe/ - Skyframe Framework

Skyframe is Bazel's incremental evaluation framework, providing the foundation for fast, incremental builds.

**Key Files:**
- `SkyFunction.java` - Interface for evaluating SkyKeys to SkyValues
- `SkyKey.java` - Keys in the evaluation graph
- `SkyValue.java` - Values in the evaluation graph
- `SkyFunctionEnvironment.java` - Environment provided to SkyFunctions
- `InMemoryMemoizingEvaluator.java` - In-memory evaluation and caching
- `AbstractParallelEvaluator.java` - Parallel evaluation engine
- `NodeEntry.java` - Entry in the Skyframe graph
- `Version.java` - Versioning for incremental evaluation

### src/main/java/net/starlark/ - Starlark Language

The Starlark language implementation, used for BUILD files and .bzl extensions.

**Packages:**
- `java/eval/` - Starlark interpreter and evaluation
  - `Starlark.java` - Main entry point for Starlark evaluation
  - `StarlarkThread.java` - Execution thread
  - `Module.java` - Starlark module (namespace)
  - `StarlarkFunction.java` - Function definitions
- `java/syntax/` - Starlark parser and AST
  - `Parser.java` - Parser for Starlark code
  - `Expression.java` - Expression AST nodes
  - `Statement.java` - Statement AST nodes
- `java/annot/` - Annotations for exposing Java APIs to Starlark
  - `StarlarkBuiltin.java` - Marks Starlark built-in types
  - `StarlarkMethod.java` - Exposes Java methods to Starlark
- `java/lib/` - Standard Starlark libraries
- `java/spelling/` - Spelling suggestion for undefined names

### src/main/starlark/ - Built-in Starlark Rules

Starlark implementations of built-in rules and builtins.

**Directory structure:**
- `builtins_bzl/` - Built-in Starlark code loaded by Bazel
  - `common/` - Common builtins across Bazel flavors
    - `cc/` - C++ built-in implementations
    - `java/` - Java built-in implementations
    - `python/` - Python built-in implementations
    - `objc/` - Objective-C built-in implementations
  - `bazel/` - Bazel-specific builtins
  - `exports.bzl` - Exports of built-in symbols
- `docgen/` - Starlark files for documentation generation

### src/main/protobuf/ - Protocol Buffer Definitions

Protocol buffer definitions for Bazel's internal data structures and APIs.

**Key proto files:**
- `build.proto` - Build file representation
- `command_line.proto` - Command-line options
- `action_cache.proto` - Action cache data structures
- `execution_statistics.proto` - Execution metrics
- `remote_execution_log.proto` - Remote execution logs
- `spawn.proto` - Spawn definitions
- `worker_protocol.proto` - Persistent worker protocol
- `failure_details.proto` - Detailed failure information
- `bazel_flags.proto` - Bazel flag definitions

### tools/ - Embedded Tools

Tools that are embedded in Bazel and distributed with it.

**Key directories:**
- `cpp/` - C++ toolchain configuration
  - `cc_configure.bzl` - C++ toolchain auto-configuration
  - `unix_cc_toolchain_config.bzl` - Unix C++ toolchain
  - `windows_cc_configure.bzl` - Windows C++ toolchain
- `jdk/` - JDK configuration and toolchains
  - `default_java_toolchain.bzl` - Default Java toolchain
  - `local_java_repository.bzl` - Local JDK repository rule
- `build_defs/` - Build definition utilities
  - `repo/` - Repository rules (http_archive, git_repository, etc.)
  - `hash/` - Hashing utilities
  - `pkg/` - Package creation rules
- `python/` - Python rules and toolchain
- `android/` - Android build support
- `test/` - Test infrastructure

## Code Organization Patterns

### Bazel Module System

Bazel uses a module system (`BlazeModule`) to organize functionality:
- Each major feature is implemented as a module
- Modules can contribute commands, options, and build phases
- Modules are loaded and initialized at startup
- Examples: `RemoteModule`, `SandboxModule`, `BazelRepositoryModule`

### Skyframe Integration Pattern

Bazel integrates with Skyframe through `SkyFunction` implementations:
- Each build phase has corresponding SkyFunctions
- Functions request dependencies through the environment
- Skyframe handles caching, invalidation, and parallelization
- Pattern: `PackageFunction`, `ConfiguredTargetFunction`, `ActionExecutionFunction`

### Rule Implementation Pattern

Rules are defined through:
1. `RuleClass` definition (attributes, outputs, constraints)
2. `ConfiguredTargetFactory` implementation (analysis logic)
3. Provider creation (passing information to dependents)
4. Action registration (defining what to execute)

### Starlark API Exposure

Java APIs are exposed to Starlark through annotations:
- `@StarlarkBuiltin` marks types visible in Starlark
- `@StarlarkMethod` exposes methods to Starlark
- Parameter types are automatically converted
- Return values are wrapped for Starlark consumption

### Testing Organization

Tests are organized by type:
- Unit tests: `src/test/java/` - JUnit tests for individual components
- Integration tests: `src/test/shell/` - Bash-based end-to-end tests
- Starlark tests: `src/main/starlark/tests/` - Starlark-based rule tests
- Analysis tests: `src/test/java/.../analysis/` - Tests for rule analysis

## Key Files and Their Roles

- **MODULE.bazel** - Bzlmod module definition, declares dependencies
- **BUILD** - Root BUILD file, defines Bazel itself as a build target
- **.bazelrc** - Default Bazel configuration for building Bazel
- **compile.sh** - Bootstrap script to compile Bazel from source
- **distdir.bzl**, **repositories.bzl** - External dependency definitions
- **src/main/java/com/google/devtools/build/lib/bazel/BazelMain.java** - Main entry point
- **src/main/cpp/main.cc** - Native binary entry point
- **src/BUILD** - Defines the Bazel server JAR and native components

This organization reflects Bazel's layered architecture, separating concerns across loading, analysis, execution, and supporting infrastructure while maintaining clear module boundaries and extensibility through the plugin system.
