This expert provides comprehensive knowledge about the Bazel build system repository, including:

### Core Architecture
- **Skyframe Evaluation Framework**: Incremental computation engine, dependency tracking, parallel evaluation, SkyFunction/SkyKey/SkyValue API, graph versioning
- **Client-Server Architecture**: C++ client launcher (src/main/cpp), Java server (src/main/java), gRPC communication, persistent server process
- **BlazeModule System**: Extension points, lifecycle hooks, module registration, 50+ built-in modules
- **Build Phases**: Loading (BUILD file parsing), Analysis (configured target creation), Execution (action running)

### Starlark Language
- **Language Implementation**: Parser (net/starlark/java/syntax), Evaluator (net/starlark/java/eval), built-in types and functions
- **Rule Definition API**: rule(), attr types, implementation functions, providers, aspects
- **Repository Rules**: repository_rule(), external dependency fetching, MODULE.bazel, Bzlmod
- **Built-in Rules**: Implementations in src/main/starlark/builtins_bzl for cc_*, java_*, py_*, proto_*

### Build System Internals
- **Package Loading**: BUILD file parsing (PackageFunction), target graph construction, label resolution
- **Analysis Phase**: ConfiguredTarget creation, dependency resolution, RuleContext API, action graph construction
- **Action Execution**: Spawn execution, execution strategies (local, remote, sandboxed, worker), action caching
- **Artifact Management**: Artifact class, output tree structure, derived vs source artifacts

### Advanced Features
- **Remote Execution**: REAPI implementation, GrpcRemoteExecutor, remote caching, ByteStreamUploader, CAS operations
- **Sandboxing**: Linux sandboxing (namespace-based), macOS sandbox-exec, Windows-based isolation
- **Persistent Workers**: WorkerModule, worker pools, worker protocol, JSON/protobuf communication
- **Dynamic Execution**: Local + remote racing, fallback strategies
- **Toolchains**: Toolchain resolution, platform constraints, execution platforms, target platforms
- **Configuration**: BuildConfiguration, configuration transitions, config_setting, select()
- **Query Languages**: query/cquery/aquery implementations, QueryEnvironment, query functions

### Java Implementation Details
- **Packages System** (src/main/java/com/google/devtools/build/lib/packages): Package, Target, Rule, RuleClass, RuleClassProvider
- **Analysis** (lib/analysis): ConfiguredTarget, RuleContext, AspectContext, Provider system
- **Actions** (lib/actions): Action interface, Spawn, Artifact, ActionGraph, ActionExecutionContext
- **Skyframe** (lib/skyframe): SkyframeExecutor, SkyFunctions (Package, ConfiguredTarget, Action execution)
- **Execution** (lib/exec): SpawnRunner, SpawnStrategy, local/remote/sandbox executors
- **VFS** (lib/vfs): FileSystem abstraction, Path, DigestHashFunction, in-memory FS
- **Runtime** (lib/runtime): BlazeRuntime, CommandEnvironment, BlazeCommand implementations
- **Remote** (lib/remote): Remote execution client, cache client, build event uploader

### C++ Client
- **Client Launcher**: main.cc entry point, server process management, startup option parsing
- **Platform Support**: POSIX/Linux/macOS/Windows implementations, blaze_util platform-specific code
- **Option Processing**: .bazelrc parsing, command-line option handling, rc file inheritance

### Build Configuration
- **Bzlmod**: MODULE.bazel dependencies, version resolution, module extensions, lockfiles
- **Bootstrap**: compile.sh self-hosting build, bootstrap without Bazel, multi-phase compilation
- **Testing**: Unit tests (src/test/java), integration tests (src/test/shell), test infrastructure
- **Distribution**: Release packaging, embedded JDK, platform-specific binaries

### Extension Points
- **Custom Rules**: Starlark rule() API, attribute definitions, implementation functions, provider propagation
- **Repository Rules**: External dependency management, http_archive, local_repository, git_repository
- **Aspects**: Aspect definition, attribute propagation, transitive information collection
- **Providers**: Provider definition, DefaultInfo, language-specific info providers (CcInfo, JavaInfo, PyInfo)
- **Transitions**: Configuration transitions, platform transitions, custom flag changes
- **Toolchain API**: Toolchain definition, toolchain resolution, multi-platform builds

### Query and Analysis
- **Query Language**: Dependency queries, pattern matching, function composition
- **Cquery**: Configured target queries, configuration-aware analysis
- **Aquery**: Action graph queries, filtering by mnemonic/inputs/outputs
- **Build Event Protocol**: BEP event stream, integration with CI/CD, JSON/binary formats

### Code Navigation
- **Key Directories**: src/main/cpp (client), src/main/java (server), src/main/starlark (builtins), tools/ (toolchains), third_party/ (dependencies)
- **Build Files**: MODULE.bazel (dependencies), BUILD (targets), .bazelrc (configuration)
- **Entry Points**: main.cc (C++ client), BazelMain.java (Java server), BlazeRuntime.java (core orchestration)
