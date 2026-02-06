# Bazel APIs and Interfaces

## Public APIs and Entry Points

### Command-Line Interface

The primary interface to Bazel is through command-line invocation. The bazel binary provides a unified interface to all build operations:

```bash
bazel [<startup-options>] <command> [<command-options>] [<target-patterns>]
```

**Core Commands**:
- `build` - Build specified targets
- `test` - Build and run tests
- `run` - Build and run a single target
- `clean` - Remove build outputs
- `query` - Query the dependency graph
- `cquery` - Query the configured target graph
- `aquery` - Query the action graph
- `info` - Display build information
- `version` - Show version information
- `help` - Display help information

**Module Commands** (Bzlmod):
- `mod deps` - Display module dependencies
- `mod graph` - Show dependency graph
- `mod tidy` - Clean up MODULE.bazel

**Advanced Commands**:
- `coverage` - Run tests with coverage
- `mobile-install` - Fast Android deployment
- `dump` - Dump internal state
- `analyze-profile` - Analyze build profiles
- `canonicalize-flags` - Normalize command flags

### Starlark Build Language

**BUILD Files**: Define build targets using a declarative syntax:

```python
# Example BUILD file
load("@rules_java//java:defs.bzl", "java_library", "java_binary")

java_library(
    name = "mylib",
    srcs = glob(["src/**/*.java"]),
    deps = [
        "//third_party/guava",
        "@maven//:com_google_protobuf_protobuf_java",
    ],
    visibility = ["//visibility:public"],
)

java_binary(
    name = "myapp",
    main_class = "com.example.Main",
    runtime_deps = [":mylib"],
)
```

**Target Patterns**:
- `//path/to:target` - Specific target
- `//path/to:all` - All targets in package
- `//path/to/...` - All targets recursively
- `:target` - Target in current package

### .bzl Files (Starlark Extensions)

Custom rules, macros, and functions defined in .bzl files:

```python
# Example .bzl file
def custom_macro(name, srcs, **kwargs):
    """A custom build macro."""
    native.filegroup(
        name = name + "_files",
        srcs = srcs,
    )
    native.genrule(
        name = name,
        srcs = [":" + name + "_files"],
        outs = [name + ".out"],
        cmd = "cat $(SRCS) > $@",
        **kwargs
    )

# Usage in BUILD file:
# load("//tools:custom.bzl", "custom_macro")
# custom_macro(name = "my_target", srcs = ["file1.txt", "file2.txt"])
```

## Key Classes and Functions

### Core Build System Classes

**BlazeRuntime** (`src/main/java/com/google/devtools/build/lib/runtime/BlazeRuntime.java`):
The central orchestrator managing the build lifecycle:

```java
public final class BlazeRuntime {
  // Initialize runtime with modules
  public static BlazeRuntime create(
      List<BlazeModule> blazeModules,
      BlazeDirectories directories,
      BinTools binTools,
      Clock clock) {...}
  
  // Execute a build command
  public BlazeCommandResult run(
      List<String> args,
      ExtendedEventHandler eventHandler,
      OutErr outErr,
      long firstContactTime) {...}
}
```

**BuildTool** (`src/main/java/com/google/devtools/build/lib/buildtool/BuildTool.java`):
Orchestrates analysis and execution phases:

```java
public final class BuildTool {
  // Main build execution method
  public BuildResult build(BuildRequest request) {...}
  
  // Runs the analysis phase
  private AnalysisResult runAnalysisPhase(
      BuildRequest request,
      LoadingResult loadingResult,
      BuildConfigurationCollection configurations) {...}
}
```

**Package** (`src/main/java/com/google/devtools/build/lib/packages/Package.java`):
Represents a parsed BUILD file:

```java
public class Package {
  // Get target by name
  public Target getTarget(String name) throws NoSuchTargetException {...}
  
  // Get all targets
  public ImmutableMap<String, Target> getTargets() {...}
  
  // Package metadata
  public PackageIdentifier getPackageIdentifier() {...}
}
```

### Starlark Integration

**Starlark Interpreter** (`src/main/java/net/starlark/java/eval/`):

```java
// Starlark evaluation
public class Starlark {
  // Evaluate a Starlark file
  public static Object eval(
      ParserInput input,
      Module module,
      StarlarkThread thread) throws SyntaxError, EvalException {...}
  
  // Call a Starlark function
  public static Object call(
      StarlarkThread thread,
      Object fn,
      Object... positionals) throws EvalException, InterruptedException {...}
}
```

**Rule Definition**:

```java
public final class RuleClass {
  // Define a rule with attributes
  public static class Builder {
    public Builder add(Attribute attr) {...}
    public Builder setConfiguredTargetFunction(
        ConfiguredTargetFactory<?, ?, ?> factory) {...}
    public RuleClass build(String name, String key) {...}
  }
}
```

### Action System

**Action** (`src/main/java/com/google/devtools/build/lib/actions/Action.java`):
Interface for build actions:

```java
public interface Action extends ActionExecutionMetadata {
  // Execute this action
  ActionResult execute(ActionExecutionContext actionExecutionContext)
      throws ActionExecutionException, InterruptedException;
  
  // Get inputs
  NestedSet<Artifact> getInputs();
  
  // Get outputs  
  ImmutableSet<Artifact> getOutputs();
}
```

**SpawnAction** (common action type):

```java
SpawnAction.Builder builder = new SpawnAction.Builder()
    .addInput(sourceFile)
    .addOutput(outputFile)
    .setExecutable(compiler)
    .addCommandLine(CommandLine.of(compileFlags))
    .setMnemonic("Compile")
    .build(ruleContext);
```

### Provider System

**TransitiveInfoProvider** - Base interface for passing information between rules:

```java
// Example: JavaInfo provider
public final class JavaInfo implements TransitiveInfoProvider {
  public NestedSet<Artifact> getRuntimeClasspath() {...}
  public NestedSet<Artifact> getCompileClasspath() {...}
  public ImmutableList<JavaSourceJarsProvider> getSourceJars() {...}
}
```

**Starlark Providers**:

```python
# Define a custom provider
MyInfo = provider(fields = ["data", "deps"])

# Create an instance
def _my_rule_impl(ctx):
    return [MyInfo(data = ctx.file.src, deps = ctx.attr.deps)]
```

## Usage Examples and Patterns

### Building a Java Application

```python
# BUILD file
load("@rules_java//java:defs.bzl", "java_binary", "java_library")

java_library(
    name = "server_lib",
    srcs = glob(["src/main/java/**/*.java"]),
    resources = glob(["src/main/resources/**"]),
    deps = [
        "//third_party/guava",
        "//third_party/netty",
        "@maven//:com_google_protobuf_protobuf_java",
    ],
)

java_binary(
    name = "server",
    main_class = "com.example.server.Main",
    runtime_deps = [":server_lib"],
    jvm_flags = ["-Xmx4g"],
)

java_test(
    name = "server_test",
    srcs = glob(["src/test/java/**/*.java"]),
    deps = [
        ":server_lib",
        "@maven//:junit_junit",
        "@maven//:org_mockito_mockito_core",
    ],
)
```

**Build and Run**:
```bash
# Build the binary
bazel build //:server

# Run the binary
bazel run //:server -- --port=8080

# Run tests
bazel test //:server_test
```

### Creating a Custom Rule

```python
# custom_rule.bzl
def _my_rule_impl(ctx):
    # Access attributes
    srcs = ctx.files.srcs
    out = ctx.actions.declare_file(ctx.label.name + ".out")
    
    # Create an action
    ctx.actions.run_shell(
        inputs = srcs,
        outputs = [out],
        command = "cat {} > {}".format(
            " ".join([f.path for f in srcs]),
            out.path,
        ),
    )
    
    # Return providers
    return [
        DefaultInfo(files = depset([out])),
        OutputGroupInfo(logs = depset([out])),
    ]

my_rule = rule(
    implementation = _my_rule_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
    },
)
```

**Usage**:
```python
# BUILD file
load("//tools:custom_rule.bzl", "my_rule")

my_rule(
    name = "combined",
    srcs = ["file1.txt", "file2.txt"],
)
```

### Query Examples

**Dependency Analysis**:
```bash
# Find all dependencies of a target
bazel query "deps(//path/to:target)"

# Find reverse dependencies
bazel query "rdeps(//..., //path/to:target)"

# Find all Java tests
bazel query 'kind("java_test", //...)'

# Find test dependencies
bazel query "tests(//path/to:lib)"
```

**Configuration Query**:
```bash
# Show configured target graph
bazel cquery "//path/to:target"

# Show configuration differences
bazel cquery "//path/to:target" --output=transitions
```

**Action Query**:
```bash
# Show all actions for a target
bazel aquery "//path/to:target"

# Show specific action type
bazel aquery 'mnemonic("Javac", //...)'
```

## Integration Patterns and Workflows

### Remote Execution Setup

```python
# .bazelrc
build --remote_executor=grpcs://remote.buildexecutor.com
build --remote_cache=grpcs://remote.cache.com
build --remote_timeout=3600
build --jobs=100
```

**Programmatic Access**:
```java
// Remote execution client configuration
RemoteOptions options = new RemoteOptions();
options.remoteExecutor = "grpcs://remote.buildexecutor.com";
options.remoteCache = "grpcs://remote.cache.com";

RemoteModule remoteModule = new RemoteModule();
```

### Build Event Protocol Integration

Subscribe to build events for CI/CD integration:

```bash
# Stream build events to file
bazel build //... --build_event_json_file=build_events.json

# Stream to remote endpoint
bazel build //... \
  --bes_backend=grpcs://buildeventservice.googleapis.com \
  --bes_results_url=https://source.cloud.google.com/results/invocations/
```

**Event Processing**:
```java
// Subscribe to build events
public class MyBuildEventSubscriber {
  @Subscribe
  public void buildStarted(BuildStartingEvent event) {...}
  
  @Subscribe
  public void targetComplete(TargetCompleteEvent event) {...}
  
  @Subscribe  
  public void buildComplete(BuildCompleteEvent event) {...}
}
```

### Repository Rules (External Dependencies)

```python
# repositories.bzl
def _download_dep_impl(repository_ctx):
    repository_ctx.download_and_extract(
        url = "https://example.com/archive.tar.gz",
        sha256 = "abc123...",
    )
    repository_ctx.file("BUILD", """
filegroup(
    name = "all_files",
    srcs = glob(["**"]),
    visibility = ["//visibility:public"],
)
    """)

download_dep = repository_rule(
    implementation = _download_dep_impl,
)
```

## Configuration Options and Extension Points

### Startup Options
Set when launching Bazel server:
```bash
bazel --output_base=/custom/path --max_idle_secs=3600 build //...
```

### Build Options
Set for individual commands:
```bash
bazel build --compilation_mode=opt --copt=-O3 --cpu=k8 //...
```

### Aspects (Cross-Cutting Analysis)

```python
def _coverage_aspect_impl(target, ctx):
    # Collect coverage data from dependencies
    return [CoverageInfo(...)]

coverage_aspect = aspect(
    implementation = _coverage_aspect_impl,
    attr_aspects = ["deps"],
)
```

**Usage**:
```bash
bazel build --aspects=//tools:coverage.bzl%coverage_aspect //...
```

### Toolchain System

```python
# Define a toolchain
my_toolchain = rule(
    implementation = _my_toolchain_impl,
    attrs = {
        "compiler": attr.label(executable = True, cfg = "exec"),
        "runtime": attr.label(),
    },
    provides = [platform_common.ToolchainInfo],
)
```

The Bazel API surface emphasizes declarative configuration, composability through providers, and extensibility through Starlark, enabling users to build complex build graphs while maintaining incremental build performance.
