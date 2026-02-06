# Bazel Repository: Complete Code Structure

## 1. Root Level Architecture

```
/Users/santos/projects/bazel/bazel/
├── src/                    # All source code and tests
├── tools/                  # Development and build tools
├── third_party/            # Vendored dependencies (grpc-java, jarjar)
├── docs/                   # Documentation (Markdown, versions)
├── examples/               # Example projects (deprecated)
├── scripts/                # Build and utility scripts
├── site/                   # Website/documentation sources
├── .github/                # GitHub workflows and CI configuration
├── .bazelci/               # Bazel CI configuration
├── .devcontainer/          # Development container setup
├── MODULE.bazel            # Bzlmod dependencies (463 lines)
├── .bazelrc                # Default build options (102 lines)
├── .bazelversion           # Version pinning (8.5.0)
├── compile.sh              # Bootstrap compilation script
└── {distdir,repositories,extensions}.bzl  # Root Bazel module files
```

## 2. Source Code Organization (src/)

```
src/
├── main/                   # Main source code
│   ├── java/              # Java implementation (~2M+ lines)
│   ├── starlark/          # Starlark built-in rules
│   ├── protobuf/          # Protocol buffer definitions (~20 files)
│   ├── native/            # Native C++ code (Darwin, Windows)
│   ├── cpp/               # C++ utilities
│   ├── tools/             # Build and generation tools
│   ├── res/               # Resources
│   └── conditions/        # Platform conditions
├── test/                   # Test suites
│   ├── java/              # Java unit tests (mirrors main/java)
│   ├── py/                # Python integration tests
│   ├── shell/             # Shell integration tests
│   ├── cpp/               # C++ tests
│   ├── native/            # Native code tests
│   └── testdata/          # Test fixtures and data
├── tools/                  # Build tools
│   ├── diskcache/         # Disk caching utilities
│   ├── bzlmod/            # Bzlmod tool support
│   ├── starlark/          # Starlark integration tools
│   ├── remote/            # Remote execution tools
│   ├── singlejar/         # JAR merging tool
│   ├── execlog/           # Execution logging tool
│   └── launcher/          # Windows launcher utility
├── java_tools/            # Java compilation and packaging tools
│   ├── buildjar/          # JAR builder
│   ├── singlejar/         # Single JAR tool
│   └── import_deps_checker/  # Import dependency checker
└── conditions/            # Platform-specific build conditions
```

## 3. Core Java Implementation

### Main Package: `com.google.devtools.build.lib`

**Location:** `/Users/santos/projects/bazel/bazel/src/main/java/com/google/devtools/build/lib/`

This is the core implementation containing 48+ major packages organized by architectural layer:

### Skyframe Layer (265 files)
**Path:** `lib/skyframe/`

The incremental computation framework:
- `SkyFunction` implementations: `PackageFunction`, `ConfiguredTargetFunction`, `ActionExecutionFunction`
- Evaluation engine: `AbstractParallelEvaluator`, `AbstractInMemoryMemoizingEvaluator`
- Graph management and cycle detection
- Dependency tracking and state management

Key files:
- `PackageFunction.java` - Load and parse BUILD files
- `ConfiguredTargetFunction.java` - Analyze targets
- `ActionExecutionFunction.java` - Run actions
- `AspectFunction.java` - Apply aspects
- `WorkspaceFileFunction.java` - Load WORKSPACE files

### Analysis Layer (128 files)
**Path:** `lib/analysis/`

Build graph analysis:
- `BuildView.java` - Main analysis coordinator
- `RuleContext.java` - Rule evaluation context
- `ConfiguredTarget.java` / `ConfiguredAspect.java` - Analysis results
- `ToolchainContext.java` / `ToolchainCollection.java` - Toolchain resolution
- `AspectCollection.java` / `AspectResolutionHelpers.java` - Aspect handling
- `CachingAnalysisEnvironment.java` - Caching layer

Subdirectories:
- `config/` - Configuration fragments and options
- `starlark/` - Starlark rule context implementation
- `constraints/` - Platform constraints
- `test/` - Test configuration

### Packages Layer (147 files)
**Path:** `lib/packages/`

Package loading and parsing:
- `PackageFactory.java` - Parses BUILD files
- `Package.java` / `Target.java` - Core data structures
- `Rule.java` / `Attribute.java` - Rule and attribute definitions
- `RuleClass.java` - Rule type definitions
- `Provider.java` / `BuiltinProvider.java` - Provider system
- `StarlarkDefinedAspect.java` / `AspectClass.java` - Aspect definitions
- `RuleClassProvider.java` - Rule registry

### Execution Layer
**Path:** `lib/exec/`

Action execution strategies:
- `BlazeExecutor.java` - Main execution orchestrator
- `SpawnRunner.java` / `AbstractSpawnStrategy.java` - Spawn execution interface
- `SpawnStrategyRegistry.java` - Strategy dispatch
- `ActionCacheChecker.java` - Cache validation
- `FileWriteStrategy.java` - Special file handling

### Runtime Layer
**Path:** `lib/runtime/`

Runtime environment and module system:
- `BlazeRuntime.java` - Main runtime coordinator (~150+ imports)
- `CommandEnvironment.java` / `CommandDispatcher.java` - Command execution
- `BlazeModule.java` / `BlazeService.java` - Modular extension system
- `BlazeOptionHandler.java` - Options processing
- `QueryRuntimeHelper.java` - Query command support

### Build Tool Layer
**Path:** `lib/buildtool/`

Build command orchestration:
- `BuildTool.java` - Main build orchestration
- `BuildRequest.java` - Build parameters
- `AqueryProcessor.java` - Action query processing
- `TargetValidator.java` - Target validation
- `SymlinkForest.java` - Symlink forest creation

### Actions Layer
**Path:** `lib/actions/`

Build action definitions:
- `Action.java` / `ActionTemplate.java` - Action abstraction
- `Artifact.java` - Output file representation
- `ActionGraph.java` - Action dependency graph
- `ActionKeyContext.java` - Action caching context

### Configuration Layer
**Path:** `lib/analysis/config/`

Configuration fragments and options:
- `BuildConfigurationValue.java` - Immutable configuration
- `BuildOptions.java` / `OptionsProvider.java` - Options management
- `Fragment.java` / `FragmentFactory.java` - Configuration fragments
- `CoreOptions.java` - Common build options
- `transitions/` - Configuration transition implementations

### Language-Specific Rules
**Path:** `lib/rules/`

Built-in rule implementations:
- `android/` - Android build rules
- `apple/` - Apple platform rules (iOS, macOS)
- `cpp/` - C++ compilation rules
- `java/` - Java compilation rules
- `python/` - Python rules
- `proto/` - Protocol buffer rules
- `filegroup/` - File grouping
- `genrule/` - Generic rules
- `test/` - Test execution support

### Specialized Modules

| Package | Purpose |
|---------|---------|
| `repository/` | External repository handling |
| `pkgcache/` | Package cache |
| `query2/` | Query engine (cquery, aquery, bquery) |
| `remote/` | Remote execution (gRPC-based) |
| `sandbox/` | Sandboxing strategies (Linux, macOS, Docker) |
| `worker/` | Persistent worker processes |
| `dynamic/` | Dynamic execution switching |
| `standalone/` | Standalone execution strategy |
| `server/` | gRPC server implementation |
| `shell/` | Shell invocation utilities |
| `unix/windows/platform/` | OS-specific implementations |
| `buildeventstream/` | Build event protocol |
| `buildeventservice/` | BES integration |
| `authandtls/` | Authentication and TLS |
| `bazel/` | Bazel-specific extensions |
| `vfs/` | Virtual file system abstraction |
| `util/` | General utilities |
| `events/` | Event system |
| `concurrent/` | Concurrency utilities |
| `profiler/` | Profiling infrastructure |
| `metrics/` | Metrics collection |
| `io/` | I/O utilities |

## 4. Starlark Language Implementation

### Java Implementation
**Path:** `src/main/java/net/starlark/java/`

```
net/starlark/java/
├── cmd/       # Starlark REPL/CLI
├── eval/      # Starlark interpreter
├── lib/       # Standard library
├── syntax/    # Parser and AST
├── types/     # Type system
└── annot/     # Annotations for exposing Java to Starlark
```

### Built-in Starlark Rules
**Path:** `src/main/starlark/builtins_bzl/`

```
builtins_bzl/
├── common/              # Shared built-ins
│   ├── cc/             # C++ rules
│   ├── java/           # Java rules
│   ├── python/         # Python rules
│   ├── objc/           # Objective-C rules
│   └── xcode/          # Xcode support
├── bazel/               # Bazel-specific rules
│   ├── cc/
│   ├── java/
│   ├── python/
│   └── objc/
├── exports.bzl          # Exports and aliases
├── paths.bzl            # Path utilities
├── util.bzl             # General utilities
└── builtin_exec_platforms.bzl  # Execution platform definitions
```

These are packaged as a ZIP and loaded via `StarlarkBuiltinsFunction.java`.

## 5. Protocol Buffer Definitions

**Path:** `src/main/protobuf/`

Key protocol definitions (~20 files):
- `build.proto` - Core build action protocol
- `action_cache.proto` - Action caching
- `spawn.proto` - Spawn execution protocol
- `execution_graph.proto` - Execution graph representation
- `command_line.proto` - Command line representation
- `crosstool_config.proto` - Toolchain configuration
- `extra_actions_base.proto` - Extra action protocol
- `buildeventstream.proto` - Build event streaming
- `java_compilation.proto` - Java compilation info
- `strategy_policy.proto` - Execution strategy selection
- `stardoc_output.proto` - Documentation output
- `crash_debugging.proto` - Crash report data

## 6. Development Tools

**Path:** `/Users/santos/projects/bazel/bazel/tools/`

### Build Infrastructure
- `build_defs/` - Reusable build rule definitions
- `build_rules/` - Build rule helpers
- `defaults/` - Default configuration
- `buildstamp/` - Build stamping

### Language Toolchains
- `cpp/` - C++ toolchain rules and helpers
- `java/` - Java toolchain rules
- `python/` - Python tools
- `objc/` - Objective-C tools
- `android/` - Android build tools
- `proto/` - Protocol buffer tools
- `bash/` - Bash utilities (runfiles)
- `sh/` - Shell utilities
- `jdk/` - JDK configuration and tools

### Testing and Coverage
- `test/` - Test execution utilities (CoverageOutputGenerator)
- `coverage/` - Coverage tools

### Distribution and Release
- `distributions/` - Package distribution rules (debian/)
- `zip/` - ZIP file utilities
- `launcher/` - Executable launcher
- `mini_tar/` - Minimal TAR implementation

### Development Support
- `intellij/` - IDE integration
- `def_parser/` - Definition parser
- `aquery_differ/` - Action query diff tool
- `ctexplain/` - Configuration transition explainer
- `compliance/` - License compliance checking
- `allowlists/` - Feature allowlists

## 7. Test Organization

**Path:** `src/test/`

### Unit Tests (Java)
**Path:** `src/test/java/com/google/devtools/build/lib/`

Mirrors main Java structure with test classes:
- `BuildViewTest.java`
- `ConfiguredTargetFunctionTest.java`
- `PackageFactoryTest.java`
- etc.

### Integration Tests
- `src/test/shell/bazel/` - Bazel command integration tests
- `src/test/shell/integration/` - System integration tests
- `src/test/py/bazel/` - Python test utilities

### Test Data
- `src/test/testdata/` - Test fixtures
- `src/test/res/` - Test resources

## 8. Entry Points and Key Classes

### Main Entry Point
**File:** `src/main/java/com/google/devtools/build/lib/bazel/Bazel.java`

Defines `BAZEL_MODULES` - list of all runtime modules (~35+):
- FileSystem, Repository, Workspace, Diff Awareness
- Remote execution, Workers, Sandbox, Dynamic execution
- Build event service, Profiling, Metrics
- Rule implementations (CC, Java, Python, etc.)

### Runtime Orchestrator
**File:** `src/main/java/com/google/devtools/build/lib/runtime/BlazeRuntime.java`

Central coordination point managing:
- File system and workspace setup
- Module initialization
- Command parsing and execution
- Signal handling
- Options processing
- Event bus management

### Build Coordination
Key classes:
- `BuildView` (analysis/) - Orchestrates analysis phase
- `BlazeExecutor` (exec/) - Orchestrates execution phase
- `SequencedSkyframeExecutor` (skyframe/) - Graph evaluation

## 9. Layer Architecture

### Command Layer (runtime, buildtool)
- `CommandDispatcher` - Routes commands
- `CommandEnvironment` - Per-command state
- 50+ command implementations

### Analysis Layer (analysis, packages, skyframe)
- `BuildView.doAnalysis()` - Main analysis entry
- `ConfiguredTargetFunction` (skyframe) - Evaluates targets
- `RuleContext` - Provides analysis context to rules
- **Output:** ConfiguredTarget objects with providers/outputs

### Execution Layer (exec, actions, sandbox, remote)
- `BlazeExecutor.executeBuild()` - Main execution entry
- `ActionExecutionFunction` (skyframe) - Executes actions
- `SpawnRunner` / `SpawnStrategy` - Executes processes

**Execution backends:**
- `StandaloneSpawnStrategy` (local execution)
- `LinuxSandboxedStrategy`, `DarwinSandboxedStrategy`
- `RemoteSpawnRunner` (gRPC-based)
- `DockerSandboxedStrategy`
- `DynamicSpawnStrategy` (hybrid)

### Skyframe Layer (incremental computation)
- `SkyFunction` interface - Computation nodes
- `SkyKey` - Node identifiers
- `NodeEntry` - Memoized results
- `AbstractParallelEvaluator` - Parallel evaluation
- Graph persistence for incremental builds

## 10. Code Organization Patterns

### Interface vs Implementation
- Most packages follow provider/context pattern
- Starlark interfaces separate from Java implementations
- Example: `CcToolchainProvider` (interface) vs implementation classes

### Visibility and Package Boundaries
- Public API classes: Provider types, RuleContext, AnalysisEnvironment
- Internal classes: Function implementations, details
- Strict package hierarchies control coupling

### Plugin/Extension Architecture
- `BlazeModule` - Extensibility point (35+ modules)
- `ModuleActionContextRegistry` - Pluggable action contexts
- `RuleClassProvider` - Pluggable rule definitions
- `QueryEnvironment` - Pluggable query functions
- `SpawnStrategyRegistry` - Pluggable execution strategies

### Configuration System
- `BuildOptions` - Immutable, flattened options
- `Fragment` - Per-configuration-aspect of build options
- `Transition` - Configuration mutation points
- `OptionsDiff` - Configuration change tracking

## 11. External Dependencies

### Third-party Locations
- `third_party/grpc-java/` - gRPC bindings
- `third_party/jarjar/` - JAR transformation
- `third_party/protobuf/` - Protocol buffers
- `third_party/googleapis/` - Google API definitions
- `third_party/remoteapis/` - Remote Execution API

### Key Maven Dependencies
- **Guava** - Collections and utilities
- **Protocol Buffers** - Data serialization
- **gRPC** - Remote execution protocol
- **Netty** - Network transport
- **Truth** - Testing framework

## 12. File Counts by Package

| Package | Java Files |
|---------|------------|
| skyframe/ | ~265 |
| packages/ | ~147 |
| analysis/ | ~128 |
| exec/ | ~50 |
| actions/ | ~80 |
| runtime/ | ~60 |
| rules/ | ~200+ (across language subdirs) |
| query2/ | ~40 |
| remote/ | ~60 |
| sandbox/ | ~30 |
