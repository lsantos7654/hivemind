# Bazel APIs and Interfaces

## 1. Public APIs and Entry Points

### Starlark Built-in Functions

Bazel exposes a comprehensive Starlark API for extending build functionality:

| Function | Purpose |
|----------|---------|
| `rule()` | Creates custom rule types with implementation functions, attributes, and providers |
| `aspect()` | Defines cross-cutting build logic that propagates across dependency graphs |
| `provider()` | Declares data types passed between rules via the provider system |
| `repository_rule()` | Defines external dependency management rules |
| `module_extension()` | Registers extensible build logic in Bzlmod |
| `attr.*` | Defines attribute schemas (label, string, bool, depset, etc.) |

The Starlark environment is managed by `StarlarkBuiltinsFunction` (`src/main/java/com/google/devtools/build/lib/skyframe/StarlarkBuiltinsFunction.java`) which evaluates the `@_builtins` pseudo-repository.

### Rule APIs

**RuleClass** (`src/main/java/com/google/devtools/build/lib/packages/RuleClass.java`)

Encapsulates metadata for rule types:
- Attributes with type validation and defaults
- Configuration transitions for modifying build flags
- Implicit outputs
- Required providers from dependencies
- Execution groups for parallelization

**RuleFunctionApi** (`src/main/java/com/google/devtools/build/lib/starlarkbuildapi/RuleFunctionApi.java`)

Represents callable rule objects created via `rule()`. Calling a rule during BUILD file evaluation creates target instances.

### BUILD File Syntax

BUILD files use Python-like syntax:
```starlark
# Rule declarations
cc_library(
    name = "foo",
    srcs = ["foo.cc"],
    hdrs = ["foo.h"],
    deps = ["//bar:baz"],
)

# Visibility constraints
package(default_visibility = ["//visibility:public"])

# File exports
exports_files(["data.txt"])

# File grouping
filegroup(
    name = "configs",
    srcs = glob(["*.yaml"]),
)
```

### Command-Line Interface

```bash
bazel <command> [<options>] [<targets>]
```

**Core Commands:**
| Command | Purpose |
|---------|---------|
| `build` | Build specified targets |
| `test` | Build and run tests |
| `run` | Build and run a single target |
| `query` | Analyze dependency graph |
| `cquery` | Query with configuration |
| `aquery` | Query action graph |
| `clean` | Remove build outputs |
| `info` | Display build information |
| `fetch` | Fetch external dependencies |
| `sync` | Sync external repositories |

## 2. Key Classes and Interfaces

### Runtime Architecture

**BlazeRuntime** (`src/main/java/com/google/devtools/build/lib/runtime/BlazeRuntime.java`)

Main runtime orchestrating the build process:
- Command dispatch and event handling
- Build state persistence
- Extension module loading (~35+ modules)
- Profiling and instrumentation
- Query environment setup

### Skyframe (Incremental Computation)

**SkyFunction** (`src/main/java/com/google/devtools/build/skyframe/SkyFunction.java`)

Core abstraction for incremental evaluation:
```java
public interface SkyFunction {
    SkyValue compute(SkyKey skyKey, Environment env)
        throws SkyFunctionException, InterruptedException;
}
```

Key implementations:
| Function | Purpose |
|----------|---------|
| `PackageFunction` | Load and parse BUILD files |
| `ConfiguredTargetFunction` | Analyze targets |
| `ActionExecutionFunction` | Execute build actions |
| `AspectFunction` | Apply aspects |
| `WorkspaceFileFunction` | Load WORKSPACE files |

**SkyValue** - Immutable result of SkyFunction evaluation, keyed by `SkyFunctionName`.

### Rule Context

**RuleContext** (`src/main/java/com/google/devtools/build/lib/analysis/RuleContext.java`)

Context object passed to rule implementations:

| Java Method | Starlark Access | Purpose |
|-------------|-----------------|---------|
| `getAttr()` | `ctx.attr` | Access attribute values |
| `getPrerequisites()` | `ctx.files` | Files from dependencies |
| `getExecutablePrerequisite()` | `ctx.executable` | Executable file access |
| `getAnalysisEnvironment()` | `ctx.actions` | Action creation interface |
| `createOutputArtifact()` | `ctx.outputs` | Output file declarations |
| `getBinDirectory()` | `ctx.bin_dir` | Binary output directory |
| `getRunfilesDirectory()` | `ctx.runfiles_dir` | Runfiles directory |

**StarlarkRuleContext** (`src/main/java/com/google/devtools/build/lib/analysis/starlark/StarlarkRuleContext.java`)

Wraps RuleContext for Starlark exposure.

### Provider System

**Provider** (`src/main/java/com/google/devtools/build/lib/packages/Provider.java`)

Type identifier and constructor for Info instances:
- **BuiltinProvider** - Native Java providers with serializable keys
- **StarlarkProvider** - User-defined providers created in .bzl files

**Info** (`src/main/java/com/google/devtools/build/lib/packages/Info.java`)

Actual provider instance holding typed data:
- **NativeInfo** - Java-backed providers with field annotations
- **StarlarkInfo** - Dictionary-based Starlark providers
- **StructImpl** - Generic structure with field access

**Core Built-in Providers:**

| Provider | Fields | Purpose |
|----------|--------|---------|
| `DefaultInfo` | files, files_to_run, runfiles | Standard outputs |
| `FileProvider` | transitive_files | Transitive file sets |
| `OutputGroupInfo` | output_groups | Named output groups |
| `InstrumentedFilesInfo` | instrumented_files | Coverage support |
| `RunEnvironmentInfo` | environment, inherited_environment | Runtime environment |

### Configuration System

**BuildOptions** (`src/main/java/com/google/devtools/build/lib/analysis/config/BuildOptions.java`)

Collects all configuration state:
```java
class BuildOptions {
    ImmutableMap<Class<? extends FragmentOptions>, FragmentOptions> options;
}
```

**ConfigurationTransition** (`src/main/java/com/google/devtools/build/lib/analysis/config/transitions/ConfigurationTransition.java`)

Modifies build flags per dependency:
- `PatchTransition` - Single configuration mapping
- `SplitTransition` - Multiple configurations from single dependency
- `NoTransition` - No modification

### Attribute System

**Attribute** (`src/main/java/com/google/devtools/build/lib/packages/Attribute.java`)

Defines rule attribute schemas.

**StarlarkAttrModuleApi** (`src/main/java/com/google/devtools/build/lib/starlarkbuildapi/StarlarkAttrModuleApi.java`)

Starlark `attr` module methods:
- `attr.string()` - String attributes
- `attr.int()` - Integer attributes
- `attr.bool()` - Boolean attributes
- `attr.label()` - Dependency labels
- `attr.label_list()` - List of dependencies
- `attr.output()` - Output file declaration
- `attr.output_list()` - List of outputs
- `attr.string_list()` - List of strings

## 3. Usage Examples

### Writing a Custom Rule

```starlark
def _my_rule_impl(ctx):
    # Access attributes
    srcs = ctx.files.srcs
    output = ctx.outputs.out

    # Create action
    ctx.actions.run(
        outputs = [output],
        inputs = srcs,
        executable = ctx.executable._tool,
        arguments = [f.path for f in srcs] + [output.path],
    )

    # Return provider
    return [DefaultInfo(files = depset([output]))]

my_rule = rule(
    implementation = _my_rule_impl,
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "out": attr.output(),
        "_tool": attr.label(
            executable = True,
            cfg = "exec",
            default = "//tools:my_tool",
        ),
    },
)
```

### Writing an Aspect

```starlark
def _my_aspect_impl(target, ctx):
    # Access target providers
    files = target[DefaultInfo].files

    # Collect from dependencies
    dep_files = []
    for dep in ctx.rule.attr.deps:
        if OutputGroupInfo in dep:
            dep_files.append(dep[OutputGroupInfo].collected)

    # Create output
    all_files = depset(
        direct = files.to_list(),
        transitive = dep_files,
    )

    return [OutputGroupInfo(collected = all_files)]

my_aspect = aspect(
    implementation = _my_aspect_impl,
    attr_aspects = ["deps"],  # Propagate to deps
    provides = [OutputGroupInfo],
)

# Usage: bazel build //pkg:target --aspects=//defs:my_aspect.bzl%my_aspect
```

### Using Providers

```starlark
# Define custom provider
MyInfo = provider(
    doc = "Custom information from my rule",
    fields = {
        "data": "String data",
        "files": "depset of files",
    },
)

def _producer_impl(ctx):
    return [
        MyInfo(
            data = "value",
            files = depset([ctx.file.src]),
        ),
        DefaultInfo(files = depset([ctx.file.src])),
    ]

def _consumer_impl(ctx):
    # Access provider from dependency
    info = ctx.attr.dep[MyInfo]
    print("Data:", info.data)

    return [DefaultInfo(files = info.files)]

producer = rule(
    implementation = _producer_impl,
    attrs = {"src": attr.label(allow_single_file = True)},
)

consumer = rule(
    implementation = _consumer_impl,
    attrs = {"dep": attr.label(providers = [MyInfo])},
)
```

### Repository Rules

```starlark
def _my_repo_impl(ctx):
    # Download and extract archive
    ctx.download_and_extract(
        url = ctx.attr.url,
        sha256 = ctx.attr.sha256,
        stripPrefix = ctx.attr.strip_prefix,
    )

    # Create BUILD file
    ctx.file("BUILD.bazel", """
cc_library(
    name = "lib",
    srcs = glob(["src/*.c"]),
    hdrs = glob(["include/*.h"]),
    visibility = ["//visibility:public"],
)
""")

my_repo = repository_rule(
    implementation = _my_repo_impl,
    attrs = {
        "url": attr.string(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "strip_prefix": attr.string(),
    },
)
```

### Module Extensions (Bzlmod)

```starlark
# In MODULE.bazel
bazel_dep(name = "my_dep", version = "1.0")

my_ext = use_extension("@my_dep//:extensions.bzl", "my_ext")
my_ext.configure(feature = "enabled")
use_repo(my_ext, "configured_repo")

# In extensions.bzl
def _my_ext_impl(mctx):
    for mod in mctx.modules:
        for tag in mod.tags.configure:
            # Create repository based on configuration
            _create_repo(name = "configured_repo", feature = tag.feature)

_configure = tag_class(attrs = {"feature": attr.string()})

my_ext = module_extension(
    implementation = _my_ext_impl,
    tag_classes = {"configure": _configure},
)
```

## 4. Integration Patterns

### Rule Composition

Rules compose through:
1. **Dependency attributes** - Rules declare dependencies on other rule outputs
2. **Provider passing** - Rules export structured data via providers
3. **Configuration transitions** - Rules apply different build flags to dependencies
4. **Execution groups** - Parallel action execution on compatible platforms

### Action Types

| Action | Purpose | Method |
|--------|---------|--------|
| `run` | Execute arbitrary command | `ctx.actions.run()` |
| `run_shell` | Execute shell command | `ctx.actions.run_shell()` |
| `write` | Create file with content | `ctx.actions.write()` |
| `expand_template` | Template substitution | `ctx.actions.expand_template()` |
| `symlink` | Create symbolic link | `ctx.actions.symlink()` |
| `declare_file` | Declare output file | `ctx.actions.declare_file()` |
| `declare_directory` | Declare output directory | `ctx.actions.declare_directory()` |

### Remote Execution Integration

Remote execution delegates actions via:
- **Action serialization** - Artifacts and commands marshaled to remote systems
- **Content-addressed storage** - Artifacts indexed by content digest
- **Caching** - Results cached and reused across builds
- **Sandboxing** - Environment isolation on remote workers

### Caching Architecture

Multi-level caching:
1. **In-memory cache** - Skyframe value graph in memory
2. **Action cache** - Previous action outputs by input hash
3. **Content-addressed storage** - Artifacts indexed by content digest
4. **Disk cache** - Local persistent cache
5. **Remote cache** - Distributed artifact sharing

## 5. Configuration Options

### Build Flags

```bash
# Compilation mode
--compilation_mode=[fastbuild|dbg|opt]
-c [fastbuild|dbg|opt]

# Platform configuration
--platforms=//my:platform
--host_platform=//my:host_platform
--cpu=k8

# Toolchain selection
--extra_toolchains=//my:toolchain

# Output directories
--symlink_prefix=my-
--output_base=/path/to/output

# Caching
--disk_cache=/path/to/cache
--remote_cache=grpcs://...
--remote_executor=grpcs://...

# Parallelism
--jobs=16
--local_cpu_resources=8

# Visibility
--check_visibility=true
```

### Custom Build Settings

```starlark
# Define build setting
bool_flag = rule(
    implementation = _bool_flag_impl,
    build_setting = config.bool(flag = True),
)

# Use in rules
def _my_rule_impl(ctx):
    if ctx.attr._my_flag[BuildSettingInfo].value:
        # Feature enabled
        pass
```

### Select Statements

```starlark
cc_library(
    name = "lib",
    srcs = ["common.cc"] + select({
        "@platforms//os:linux": ["linux.cc"],
        "@platforms//os:macos": ["macos.cc"],
        "//conditions:default": ["generic.cc"],
    }),
)
```

## 6. Extension Points

### BlazeModule

Java extension point for Bazel modules (`src/main/java/com/google/devtools/build/lib/runtime/BlazeModule.java`):

```java
public abstract class BlazeModule {
    public void beforeCommand(CommandEnvironment env) {}
    public void afterCommand() {}
    public void registerActionContexts(
        ModuleActionContextRegistry.Builder builder) {}
    public void registerSpawnStrategies(
        SpawnStrategyRegistry.Builder builder) {}
}
```

### SpawnStrategy

Execution strategy interface:
- `StandaloneSpawnStrategy` - Local execution
- `LinuxSandboxedStrategy` - Linux sandbox
- `DarwinSandboxedStrategy` - macOS sandbox
- `RemoteSpawnRunner` - Remote execution
- `DynamicSpawnStrategy` - Hybrid local/remote

### Query Functions

Extend query language with custom functions via `QueryEnvironment`.

## 7. Best Practices

### Rule Design Principles

**Do:**
- Separate analysis from execution (keep analysis deterministic)
- Use providers for rule-to-rule communication
- Declare all dependencies explicitly
- Avoid side effects in rule implementations
- Cache expensive computations

**Don't:**
- Access global mutable state
- Hardcode paths (breaks portability)
- Create excessive runfiles
- Ignore transitive closures
- Assume specific execution environments

### Performance Considerations

1. **Minimize Skyframe restarts** - Batch dependency requests
2. **Reduce action counts** - Batch operations where possible
3. **Manage output sizes** - Consider compression and caching
4. **Use parallelization** - Leverage execution groups and remote execution
5. **Avoid large in-memory data** - During analysis phase

### Common Mistakes

| Mistake | Impact | Solution |
|---------|--------|----------|
| Missing dependencies | Build failures | Use `depset` for transitive deps |
| Configuration assumptions | Cross-platform failures | Use configuration fragments |
| Provider type errors | Runtime errors | Check provider presence |
| Runfiles omission | Runtime failures | Include all runtime deps |
| Missing validation | Silent failures | Add attribute constraints |

## 8. API Quick Reference

### Actions API

```starlark
# Run command
ctx.actions.run(
    outputs = [output_file],
    inputs = input_files,
    executable = tool,
    arguments = args,
    mnemonic = "MyAction",
    progress_message = "Processing %s" % input_file.short_path,
)

# Run shell command
ctx.actions.run_shell(
    outputs = [output_file],
    inputs = input_files,
    command = "cat $1 > $2",
    arguments = [input_file.path, output_file.path],
)

# Write file
ctx.actions.write(
    output = output_file,
    content = "file contents",
    is_executable = False,
)

# Expand template
ctx.actions.expand_template(
    template = template_file,
    output = output_file,
    substitutions = {"{VAR}": "value"},
)
```

### File API

```starlark
# Declare output file
output = ctx.actions.declare_file(ctx.label.name + ".out")

# Declare output directory
output_dir = ctx.actions.declare_directory(ctx.label.name + "_dir")

# Get file from label
file = ctx.file.src

# Get files from label_list
files = ctx.files.srcs
```

### Depset API

```starlark
# Create depset
files = depset(direct = [file1, file2])

# Merge depsets
all_files = depset(
    direct = my_files,
    transitive = [dep[DefaultInfo].files for dep in ctx.attr.deps],
)

# Convert to list (expensive)
file_list = files.to_list()
```
