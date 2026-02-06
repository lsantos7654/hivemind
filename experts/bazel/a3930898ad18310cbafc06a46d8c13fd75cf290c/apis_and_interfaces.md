# Bazel APIs and Interfaces

## Public APIs and Entry Points

### Command-Line Interface

The primary entry point for Bazel is the command-line tool with the general syntax:

```bash
bazel [<startup options>] <command> [<command options>] [<target patterns>]
```

**Core Commands**:
- `build`: Compile and link specified targets
- `test`: Build and run tests
- `run`: Build and execute a binary target
- `query`: Query the dependency graph
- `cquery`: Query the configured target graph
- `aquery`: Query the action graph
- `clean`: Remove build outputs
- `fetch`: Fetch external dependencies
- `sync`: Synchronize with external repositories
- `info`: Display runtime information
- `version`: Display version information
- `help`: Show help for commands

**Startup Options** (parsed before server starts):
```bash
--output_base=/path/to/base    # Server workspace directory
--host_jvm_args=-Xmx4g          # JVM memory settings
--batch                          # Don't use server (for CI)
--max_idle_secs=3600            # Server idle timeout
```

**Build Options**:
```bash
--compilation_mode=opt          # Optimization level (fastbuild, dbg, opt)
--cpu=k8                        # Target CPU architecture
--disk_cache=/path/to/cache     # Local disk cache
--remote_executor=grpc://host   # Remote execution backend
--jobs=8                        # Parallel build actions
--strategy=Javac=worker         # Action execution strategy
```

### BlazeModule Extension Point

BlazeModule is the primary extension point for adding functionality to Bazel. Modules can hook into numerous lifecycle events:

**src/main/java/com/google/devtools/build/lib/runtime/BlazeModule.java**:

```java
public abstract class BlazeModule {
  // Called once at Bazel startup before server initialization
  public void globalInit(OptionsParsingResult startupOptions) {}

  // Called when server starts
  public void blazeStartup(
      OptionsParsingResult startupOptions,
      BlazeVersionInfo versionInfo,
      UUID instanceId,
      FileSystem fileSystem,
      ServerDirectories serverDirectories) {}

  // Called before each command execution
  public void beforeCommand(CommandEnvironment env) {}

  // Called after command completion
  public void afterCommand() {}

  // Register command-line options
  public Iterable<Class<? extends OptionsBase>> getCommandOptions(Command command) {}

  // Register action execution strategies
  public void registerSpawnStrategies(
      SpawnStrategyRegistry.Builder registryBuilder,
      CommandEnvironment env) {}

  // Contribute to configured target analysis
  public void initializeRuleClasses(ConfiguredRuleClassProvider.Builder builder) {}

  // Register custom commands
  public Iterable<? extends BlazeCommand> getCommands() {}
}
```

**Example Module Implementation**:

```java
// RemoteModule provides remote execution and caching
public class RemoteModule extends BlazeModule {
  @Override
  public void registerSpawnStrategies(
      SpawnStrategyRegistry.Builder registryBuilder,
      CommandEnvironment env) {
    RemoteOptions remoteOptions = env.getOptions().getOptions(RemoteOptions.class);
    if (remoteOptions.remoteExecutor != null) {
      registryBuilder.registerStrategy(
          new RemoteSpawnStrategy(remoteExecutor, remoteCache));
    }
  }

  @Override
  public Iterable<Class<? extends OptionsBase>> getCommandOptions() {
    return ImmutableList.of(RemoteOptions.class);
  }
}
```

### Skyframe Function API

Skyframe is Bazel's incremental computation framework. All build logic is implemented as SkyFunctions:

**src/main/java/com/google/devtools/build/skyframe/SkyFunction.java**:

```java
public interface SkyFunction {
  /**
   * Computes a SkyValue from a SkyKey and its dependencies.
   *
   * @param skyKey The key for this computation
   * @param env Environment for requesting dependencies
   * @return The computed value, or null if dependencies are missing
   */
  @Nullable
  SkyValue compute(SkyKey skyKey, Environment env)
      throws SkyFunctionException, InterruptedException;
}
```

**Example SkyFunction**:

```java
public class PackageFunction implements SkyFunction {
  @Override
  public SkyValue compute(SkyKey skyKey, Environment env) throws PackageFunctionException {
    PackageIdentifier packageId = (PackageIdentifier) skyKey.argument();

    // Request BUILD file as dependency
    SkyKey buildFileKey = FileValue.key(packageId.getBuildFile());
    FileValue buildFileValue = (FileValue) env.getValue(buildFileKey);
    if (buildFileValue == null) {
      return null; // Dependencies not ready
    }

    // Parse BUILD file
    Package pkg = parseBuildFile(buildFileValue, env);
    return new PackageValue(pkg);
  }
}
```

### Starlark Rule Definition API

Rules are defined using Starlark, Bazel's Python-like extension language:

**Rule Definition**:

```python
# Define a rule
my_rule = rule(
    implementation = _my_rule_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = [".cc", ".h"]),
        "deps": attr.label_list(providers = [CcInfo]),
        "out": attr.output(),
    },
    provides = [DefaultInfo],
)

# Implementation function
def _my_rule_impl(ctx):
    # Access attributes
    srcs = ctx.files.srcs
    deps = ctx.attr.deps

    # Create actions
    output = ctx.actions.declare_file(ctx.attr.out.name)
    ctx.actions.run(
        outputs = [output],
        inputs = srcs,
        executable = ctx.executable._compiler,
        arguments = [src.path for src in srcs] + ["-o", output.path],
    )

    # Return providers
    return [
        DefaultInfo(files = depset([output])),
        MyCustomInfo(data = "value"),
    ]
```

### Repository Rule API

Repository rules fetch and configure external dependencies:

```python
def _my_repository_impl(repository_ctx):
    # Download external resource
    repository_ctx.download_and_extract(
        url = "https://example.com/dep.tar.gz",
        sha256 = "abc123...",
    )

    # Create BUILD file
    repository_ctx.file("BUILD", """
cc_library(
    name = "lib",
    srcs = glob(["**/*.cc"]),
    visibility = ["//visibility:public"],
)
""")

my_repository = repository_rule(
    implementation = _my_repository_impl,
    attrs = {
        "url": attr.string(mandatory = True),
    },
)
```

### Action API

Actions represent build steps. Rules create actions during analysis:

**src/main/java/com/google/devtools/build/lib/analysis/RuleContext.java**:

```java
// Creating a spawn action (external process execution)
SpawnAction action = new SpawnAction.Builder()
    .addInputs(inputs)
    .addOutputs(outputs)
    .setExecutable(compiler)
    .addCommandLine(
        CustomCommandLine.builder()
            .addAll(flags)
            .addExecPaths("-c", sourceFiles)
            .addExecPath("-o", outputFile)
            .build())
    .setMnemonic("CppCompile")
    .build(ruleContext);

ruleContext.registerAction(action);
```

**Starlark Action API**:

```python
# Run executable
ctx.actions.run(
    outputs = [output_file],
    inputs = input_files,
    executable = tool,
    arguments = args,
    mnemonic = "CustomAction",
)

# Run shell command
ctx.actions.run_shell(
    outputs = [output],
    inputs = inputs,
    command = "grep pattern input.txt > output.txt",
)

# Write file
ctx.actions.write(
    output = output_file,
    content = "Generated content",
)

# Expand template
ctx.actions.expand_template(
    template = template_file,
    output = output_file,
    substitutions = {"{{VAR}}": "value"},
)
```

## Key Classes, Functions, and Macros

### Package and Target System

**Package** (src/main/java/com/google/devtools/build/lib/packages/Package.java):
Represents a BUILD file and its targets.

```java
public class Package {
  private final PackageIdentifier packageIdentifier;
  private final Map<String, Target> targets;

  public Target getTarget(String name) throws NoSuchTargetException;
  public Collection<Target> getTargets();
  public PackageIdentifier getPackageIdentifier();
}
```

**Target** (src/main/java/com/google/devtools/build/lib/packages/Target.java):
Base interface for build targets (rules, files, package groups).

```java
public interface Target {
  Label getLabel();
  Package getPackage();
  String getName();
  String getTargetKind();
}
```

**Rule** (src/main/java/com/google/devtools/build/lib/packages/Rule.java):
Represents a rule instance in a BUILD file.

```java
public class Rule implements Target {
  public RuleClass getRuleClass();
  public <T> T getAttr(String attrName, Type<T> type);
  public Label getLabel();
  public List<Label> getLabels();
}
```

### Configuration and Analysis

**ConfiguredTarget** (src/main/java/com/google/devtools/build/lib/analysis/ConfiguredTarget.java):
A target with a specific configuration (build settings).

```java
public interface ConfiguredTarget {
  Label getLabel();
  BuildConfiguration getConfiguration();

  // Get provider
  <P extends TransitiveInfoProvider> P getProvider(Class<P> providerClass);

  // Get Starlark provider
  Info get(Provider.Key providerKey);
}
```

**RuleContext** (src/main/java/com/google/devtools/build/lib/analysis/RuleContext.java):
Context provided to rule implementations during analysis.

```java
public final class RuleContext {
  // Access attributes
  public <T> T attributes().get(String attributeName, Type<T> type);

  // Get dependencies
  public List<ConfiguredTarget> getPrerequisites(String attributeName);

  // Create actions
  public void registerAction(Action action);

  // Create artifacts
  public Artifact createOutputArtifact();
  public Artifact createDerivedArtifact(PathFragment path);

  // Report errors
  public void ruleError(String message);
}
```

### Action and Execution

**Action** (src/main/java/com/google/devtools/build/lib/actions/Action.java):
Represents a build action (compilation, linking, etc.).

```java
public interface Action {
  ActionKey getKey();
  Collection<Artifact> getInputs();
  Collection<Artifact> getOutputs();

  ActionResult execute(ActionExecutionContext context)
      throws ActionExecutionException;
}
```

**Artifact** (src/main/java/com/google/devtools/build/lib/actions/Artifact.java):
Represents a file (input or output) in the build graph.

```java
public class Artifact {
  Path getPath();
  ArtifactRoot getRoot();
  PathFragment getExecPath();
  boolean isSourceArtifact();
  boolean isDerivedArtifact();
}
```

**Spawn** (src/main/java/com/google/devtools/build/lib/actions/Spawn.java):
Represents an external process execution request.

```java
public interface Spawn {
  ImmutableList<String> getArguments();
  ImmutableMap<String, String> getEnvironment();
  NestedSet<ActionInput> getInputFiles();
  Collection<? extends ActionInput> getOutputFiles();
  ResourceSet getLocalResources();
}
```

### Skyframe Core Types

**SkyKey** (src/main/java/com/google/devtools/build/skyframe/SkyKey.java):
Identifier for a Skyframe computation.

```java
public interface SkyKey {
  SkyFunctionName functionName();
  Object argument();
}
```

**SkyValue** (src/main/java/com/google/devtools/build/skyframe/SkyValue.java):
Result of a Skyframe computation.

```java
public interface SkyValue {
  // Marker interface - implementations contain computed data
}
```

## Usage Examples and Code Snippets

### Defining a Custom Rule

```python
# my_rules.bzl

def _my_binary_impl(ctx):
    """Implementation of my_binary rule."""
    # Collect all source files from srcs and deps
    all_srcs = ctx.files.srcs
    transitive_deps = depset(
        transitive = [dep[DefaultInfo].files for dep in ctx.attr.deps]
    )

    # Declare output executable
    executable = ctx.actions.declare_file(ctx.label.name)

    # Create compilation action
    ctx.actions.run(
        outputs = [executable],
        inputs = depset(all_srcs, transitive = [transitive_deps]),
        executable = ctx.executable._compiler,
        arguments = [
            "--output", executable.path,
            "--sources"] + [f.path for f in all_srcs],
        mnemonic = "CompileMyBinary",
        progress_message = "Compiling %s" % ctx.label,
    )

    # Return providers
    return [
        DefaultInfo(
            files = depset([executable]),
            executable = executable,
            runfiles = ctx.runfiles(files = [executable]),
        ),
    ]

my_binary = rule(
    implementation = _my_binary_impl,
    attrs = {
        "srcs": attr.label_list(
            allow_files = [".my"],
            doc = "Source files",
        ),
        "deps": attr.label_list(
            providers = [DefaultInfo],
            doc = "Dependencies",
        ),
        "_compiler": attr.label(
            default = "//tools:my_compiler",
            executable = True,
            cfg = "exec",
        ),
    },
    executable = True,
    doc = "Builds a custom binary",
)
```

### Using the Rule

```python
# BUILD file

load("//rules:my_rules.bzl", "my_binary")

my_binary(
    name = "hello",
    srcs = ["hello.my", "utils.my"],
    deps = [":common_lib"],
)

my_binary(
    name = "common_lib",
    srcs = ["lib.my"],
)
```

### Creating a Repository Rule

```python
# repos.bzl

def _http_archive_impl(repository_ctx):
    """Downloads and extracts an archive."""
    # Download the archive
    repository_ctx.download_and_extract(
        url = repository_ctx.attr.urls,
        sha256 = repository_ctx.attr.sha256,
        stripPrefix = repository_ctx.attr.strip_prefix,
    )

    # Apply patches if specified
    for patch in repository_ctx.attr.patches:
        repository_ctx.patch(patch, strip = repository_ctx.attr.patch_strip)

    # Create or use provided BUILD file
    if repository_ctx.attr.build_file:
        repository_ctx.symlink(repository_ctx.attr.build_file, "BUILD.bazel")
    elif repository_ctx.attr.build_file_content:
        repository_ctx.file("BUILD.bazel", repository_ctx.attr.build_file_content)

http_archive = repository_rule(
    implementation = _http_archive_impl,
    attrs = {
        "urls": attr.string_list(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "strip_prefix": attr.string(),
        "patches": attr.label_list(default = []),
        "patch_strip": attr.int(default = 0),
        "build_file": attr.label(allow_single_file = True),
        "build_file_content": attr.string(),
    },
)
```

### Implementing a Custom Provider

```python
# providers.bzl

# Define provider
MyInfo = provider(
    doc = "Information about my custom aspect",
    fields = {
        "transitive_data": "depset of collected data",
        "direct_data": "list of data from this target",
    },
)

# Use provider in rule
def _my_library_impl(ctx):
    # Collect transitive data
    transitive_data = [dep[MyInfo].transitive_data for dep in ctx.attr.deps]

    my_info = MyInfo(
        transitive_data = depset(
            ctx.attr.data,
            transitive = transitive_data,
        ),
        direct_data = ctx.attr.data,
    )

    return [my_info, DefaultInfo(files = depset(ctx.files.srcs))]

my_library = rule(
    implementation = _my_library_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "data": attr.string_list(),
        "deps": attr.label_list(providers = [MyInfo]),
    },
)
```

### Implementing an Aspect

```python
# aspects.bzl

def _collect_sources_impl(target, ctx):
    """Aspect that collects all source files transitively."""
    # Sources directly on this target
    direct_sources = []
    if hasattr(ctx.rule.attr, 'srcs'):
        direct_sources = ctx.rule.files.srcs

    # Sources from dependencies
    transitive_sources = []
    for dep in getattr(ctx.rule.attr, 'deps', []):
        if SourceFilesInfo in dep:
            transitive_sources.append(dep[SourceFilesInfo].transitive_sources)

    # Combine into depset
    all_sources = depset(
        direct_sources,
        transitive = transitive_sources,
    )

    return [SourceFilesInfo(transitive_sources = all_sources)]

SourceFilesInfo = provider(fields = ['transitive_sources'])

collect_sources = aspect(
    implementation = _collect_sources_impl,
    attr_aspects = ['deps'],  # Propagate along deps edges
)
```

## Integration Patterns and Workflows

### Remote Execution Integration

Bazel implements the Remote Execution API (REAPI) for distributed builds:

**Configuration**:
```bash
# .bazelrc
build --remote_executor=grpc://remote.example.com:8980
build --remote_cache=grpc://cache.example.com:8980
build --remote_download_minimal  # Download only necessary outputs
```

**Remote Execution Flow**:
1. Action is ready for execution
2. Bazel computes action cache key (input hashes + command)
3. Check remote cache for cached result
4. If miss, upload inputs to Content Addressable Storage (CAS)
5. Send execution request with input root digest
6. Remote worker downloads inputs, executes action
7. Worker uploads outputs to CAS
8. Bazel downloads required outputs

### Build Event Protocol (BEP)

Bazel publishes structured build events for integration with CI/CD:

```bash
# Stream build events
bazel build --build_event_json_file=bep.json //target

# Stream to remote service
bazel build --bes_backend=grpcs://bes.example.com //target
```

**BEP Events Include**:
- Build started/finished
- Target configured/built/completed
- Test summary and results
- Action execution statistics
- Build metrics and timing

### Query Language Integration

Bazel's query languages enable automated analysis:

**Query** (dependency graph):
```bash
# Find all dependencies
bazel query 'deps(//my:target)'

# Find reverse dependencies
bazel query 'rdeps(//..., //my:lib)'

# Find build files
bazel query 'buildfiles(//...)'

# Complex queries
bazel query 'kind(cc_library, //java/...)'
```

**Cquery** (configured targets):
```bash
# Query with configuration
bazel cquery 'deps(//my:target)' --platforms=//platforms:linux

# Show configurations
bazel cquery '//my:target' --output=graph
```

**Aquery** (action graph):
```bash
# Show all actions
bazel aquery '//my:target'

# Filter by mnemonic
bazel aquery 'mnemonic("CppCompile", deps(//my:target))'
```

## Configuration Options and Extension Points

### Toolchain API

Toolchains provide language-specific build tools:

```python
# Define toolchain type
java_toolchain_type = toolchain_type()

# Define toolchain
def _java_toolchain_impl(ctx):
    return [platform_common.ToolchainInfo(
        javac = ctx.attr.javac,
        java_runtime = ctx.attr.java_runtime,
    )]

java_toolchain = rule(
    implementation = _java_toolchain_impl,
    attrs = {
        "javac": attr.label(executable = True, cfg = "exec"),
        "java_runtime": attr.label(),
    },
    provides = [platform_common.ToolchainInfo],
)

# Use toolchain in rule
def _java_binary_impl(ctx):
    toolchain = ctx.toolchains["//tools:java_toolchain_type"]
    # Use toolchain.javac, toolchain.java_runtime
```

### Transition API

Transitions change build configurations:

```python
# Define transition
def _platform_transition_impl(settings, attr):
    return {
        "//command_line_option:platforms": attr.platform,
    }

platform_transition = transition(
    implementation = _platform_transition_impl,
    inputs = [],
    outputs = ["//command_line_option:platforms"],
)

# Use in rule
my_rule = rule(
    implementation = _impl,
    attrs = {
        "platform": attr.label(),
        "deps": attr.label_list(cfg = platform_transition),
    },
)
```

### Configuration Settings

```python
# Define custom configuration
config_setting(
    name = "debug_build",
    values = {"compilation_mode": "dbg"},
)

# Use in select()
cc_binary(
    name = "app",
    srcs = ["main.cc"],
    copts = select({
        ":debug_build": ["-DDEBUG"],
        "//conditions:default": ["-DNDEBUG"],
    }),
)
```

Bazel's API surface is extensive and designed for extensibility while maintaining determinism and performance. The Starlark APIs provide safe, hermetic rule definitions, while the Java APIs enable deep integration for advanced use cases.
