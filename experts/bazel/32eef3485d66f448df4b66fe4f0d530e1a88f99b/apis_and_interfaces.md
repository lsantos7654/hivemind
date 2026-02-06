# Bazel APIs and Interfaces

## Public APIs and Entry Points

### Starlark Built-in Functions

Bazel exposes a comprehensive Starlark API for extending build functionality through the global namespace available in BUILD and .bzl files.

**Core Extension Functions:**

| Function | Purpose | Location |
|----------|---------|----------|
| `rule()` | Creates custom rule types with implementation functions | Starlark global |
| `aspect()` | Defines cross-cutting build logic across dependencies | Starlark global |
| `provider()` | Declares data types passed between rules | Starlark global |
| `repository_rule()` | Defines external dependency management rules | Starlark global |
| `module_extension()` | Registers Bzlmod extension logic | Starlark global |
| `attr.*` | Attribute schema definitions (label, string, bool, etc.) | Starlark global |
| `select()` | Configurable attribute values based on configuration | Starlark global |

### Command-line Interface

Bazel provides a rich command-line interface for interacting with the build system:

**Primary Commands:**
```bash
bazel build <targets...>    # Build specified targets
bazel test <targets...>     # Build and run tests
bazel run <target>          # Build and run a binary target
bazel query <query>         # Query the dependency graph
bazel cquery <query>        # Query configured targets
bazel aquery <query>        # Query actions
bazel clean                 # Clean build outputs
bazel info                  # Display Bazel info
bazel version               # Show Bazel version
bazel shutdown              # Stop Bazel server
```

**Module Management (Bzlmod):**
```bash
bazel mod deps              # Display module dependency graph
bazel mod graph             # Show module dependency tree
bazel mod tidy              # Clean up unused dependencies
```

## Key Classes, Functions, and Macros

### Core Java Interfaces

#### RuleContext.java

Location: `src/main/java/com/google/devtools/build/lib/analysis/RuleContext.java`

The main context object provided to rule implementations during the analysis phase.

**Key Methods:**
```java
// Access rule attributes
<T> T attributes().get(String attrName, Type<T> type)

// Create actions
ActionRegistry actions()

// Access dependencies
List<? extends TransitiveInfoCollection> getPrerequisites(String attributeName)

// Report errors
void ruleError(String message)

// Create artifacts
Artifact createOutputArtifact()
Artifact createOutputArtifact(String name)
```

#### SkyFunction.java

Location: `src/main/java/com/google/devtools/build/skyframe/SkyFunction.java`

Interface for incremental computation in Skyframe.

**Core Method:**
```java
@Nullable
SkyValue compute(SkyKey skyKey, Environment env)
    throws SkyFunctionException, InterruptedException
```

**Implementation Pattern:**
```java
public class MyFunction implements SkyFunction {
  @Override
  public SkyValue compute(SkyKey skyKey, Environment env)
      throws InterruptedException {
    // Request dependencies
    SkyValue dep = env.getValue(depKey);
    if (dep == null) {
      return null; // Dependency not ready, will restart
    }
    // Compute result
    return new MySkyValue(dep);
  }
}
```

#### Action.java

Location: `src/main/java/com/google/devtools/build/lib/actions/Action.java`

Interface for executable build actions.

**Key Methods:**
```java
ActionResult execute(ActionExecutionContext context)
Iterable<Artifact> getInputs()
Iterable<Artifact> getOutputs()
String getMnemonic()
```

### Starlark API Interfaces

#### ctx (Rule Context in Starlark)

Available in rule implementation functions as the `ctx` parameter.

**Attributes Access:**
```python
ctx.attr.<attribute_name>  # Access rule attribute values
ctx.file.<attribute_name>  # Get single file from attribute
ctx.files.<attribute_name> # Get list of files from attribute
```

**Action Creation:**
```python
ctx.actions.run(
    outputs = [output_file],
    inputs = input_files,
    executable = tool,
    arguments = args,
)

ctx.actions.run_shell(
    outputs = [output_file],
    inputs = input_files,
    command = "echo hello > $@",
)

ctx.actions.write(
    output = ctx.actions.declare_file("file.txt"),
    content = "content",
)
```

**Artifact Management:**
```python
ctx.actions.declare_file(filename)  # Declare output file
ctx.actions.declare_directory(dirname)  # Declare output directory
```

#### Provider API

Define and use providers to pass information between rules:

```python
# Define a provider
MyInfo = provider(
    fields = {
        "data": "Data to pass",
        "files": "Depset of files",
    }
)

# Use in rule implementation
def _my_rule_impl(ctx):
    return [MyInfo(
        data = "value",
        files = depset(ctx.files.srcs),
    )]

# Access in dependent rules
def _consumer_impl(ctx):
    dep_info = ctx.attr.deps[0][MyInfo]
    data = dep_info.data
    files = dep_info.files
```

## Usage Examples with Code Snippets

### Example 1: Simple Custom Rule

Create a rule that generates a text file:

```python
# my_rules.bzl

def _file_generator_impl(ctx):
    """Implementation of file_generator rule."""
    # Declare output file
    output = ctx.actions.declare_file(ctx.label.name + ".txt")

    # Create action to write file
    ctx.actions.write(
        output = output,
        content = ctx.attr.content,
    )

    # Return providers
    return [
        DefaultInfo(files = depset([output])),
    ]

# Define the rule
file_generator = rule(
    implementation = _file_generator_impl,
    attrs = {
        "content": attr.string(
            doc = "Content to write to file",
            mandatory = True,
        ),
    },
)
```

**Usage in BUILD file:**
```python
load("//:my_rules.bzl", "file_generator")

file_generator(
    name = "my_file",
    content = "Hello, Bazel!",
)
```

### Example 2: Rule with Dependencies

Create a rule that processes files from dependencies:

```python
# processor.bzl

def _processor_impl(ctx):
    """Process all files from dependencies."""
    # Collect files from deps
    input_files = []
    for dep in ctx.attr.deps:
        input_files.extend(dep[DefaultInfo].files.to_list())

    # Declare output
    output = ctx.actions.declare_file(ctx.label.name + "_processed.txt")

    # Create processing action
    ctx.actions.run(
        outputs = [output],
        inputs = input_files,
        executable = ctx.executable._processor_tool,
        arguments = [f.path for f in input_files] + [output.path],
    )

    return [DefaultInfo(files = depset([output]))]

processor = rule(
    implementation = _processor_impl,
    attrs = {
        "deps": attr.label_list(
            doc = "Dependencies to process",
            allow_files = True,
        ),
        "_processor_tool": attr.label(
            default = "//tools:processor",
            executable = True,
            cfg = "exec",
        ),
    },
)
```

### Example 3: Aspect for Code Analysis

Create an aspect that collects information across the dependency graph:

```python
# analysis.bzl

def _analysis_aspect_impl(target, ctx):
    """Collect source files from entire dependency tree."""
    # Start with direct sources
    sources = depset(ctx.rule.files.srcs if hasattr(ctx.rule.files, "srcs") else [])

    # Collect from dependencies
    for dep in ctx.rule.attr.deps if hasattr(ctx.rule.attr, "deps") else []:
        if AnalysisInfo in dep:
            sources = depset(transitive = [sources, dep[AnalysisInfo].sources])

    return [AnalysisInfo(sources = sources)]

# Define provider
AnalysisInfo = provider(
    fields = {"sources": "Transitive sources"},
)

# Define aspect
analysis_aspect = aspect(
    implementation = _analysis_aspect_impl,
    attr_aspects = ["deps"],
)
```

**Apply aspect:**
```bash
bazel build //pkg:target --aspects=//:analysis.bzl%analysis_aspect \
    --output_groups=analysis_info
```

### Example 4: Repository Rule for External Dependencies

```python
# repo_rules.bzl

def _custom_repo_impl(repository_ctx):
    """Fetch and configure external dependency."""
    # Download archive
    repository_ctx.download_and_extract(
        url = repository_ctx.attr.url,
        sha256 = repository_ctx.attr.sha256,
    )

    # Generate BUILD file
    repository_ctx.file("BUILD", """
cc_library(
    name = "lib",
    srcs = glob(["**/*.cc"]),
    hdrs = glob(["**/*.h"]),
    visibility = ["//visibility:public"],
)
""")

custom_repo = repository_rule(
    implementation = _custom_repo_impl,
    attrs = {
        "url": attr.string(mandatory = True),
        "sha256": attr.string(mandatory = True),
    },
)
```

**Usage in MODULE.bazel:**
```python
custom_repo(
    name = "my_dep",
    url = "https://example.com/archive.tar.gz",
    sha256 = "abc123...",
)
```

## Integration Patterns and Workflows

### Pattern 1: Custom Language Support

To add support for a new language:

1. **Define file extensions and toolchain:**
```python
# my_lang_toolchain.bzl

def _my_lang_toolchain_impl(ctx):
    return [platform_common.ToolchainInfo(
        compiler = ctx.file.compiler,
        runtime = ctx.file.runtime,
    )]

my_lang_toolchain = rule(
    implementation = _my_lang_toolchain_impl,
    attrs = {
        "compiler": attr.label(allow_single_file = True),
        "runtime": attr.label(allow_single_file = True),
    },
)
```

2. **Create compilation rule:**
```python
def _my_lang_library_impl(ctx):
    toolchain = ctx.toolchains["//my_lang:toolchain_type"]

    outputs = []
    for src in ctx.files.srcs:
        output = ctx.actions.declare_file(
            src.basename.replace(".mylang", ".o")
        )
        outputs.append(output)

        ctx.actions.run(
            outputs = [output],
            inputs = [src],
            executable = toolchain.compiler,
            arguments = [src.path, "-o", output.path],
        )

    return [DefaultInfo(files = depset(outputs))]
```

### Pattern 2: Custom Test Runner

```python
# test_rules.bzl

def _custom_test_impl(ctx):
    # Create test script
    test_script = ctx.actions.declare_file(ctx.label.name + "_test.sh")

    ctx.actions.write(
        output = test_script,
        content = """#!/bin/bash
set -e
{executable} {args}
""".format(
            executable = ctx.executable.test_binary.short_path,
            args = " ".join(ctx.attr.test_args),
        ),
        is_executable = True,
    )

    # Return test execution info
    return [
        DefaultInfo(executable = test_script),
        testing.TestEnvironment({
            "TEST_VAR": ctx.attr.test_var,
        }),
    ]

custom_test = rule(
    implementation = _custom_test_impl,
    test = True,
    attrs = {
        "test_binary": attr.label(executable = True, cfg = "exec"),
        "test_args": attr.string_list(),
        "test_var": attr.string(),
    },
)
```

### Pattern 3: Code Generation

```python
# codegen.bzl

def _codegen_impl(ctx):
    # Input files
    inputs = ctx.files.srcs

    # Output directory
    output_dir = ctx.actions.declare_directory(ctx.label.name + "_generated")

    # Generate code
    ctx.actions.run(
        outputs = [output_dir],
        inputs = inputs,
        executable = ctx.executable._codegen_tool,
        arguments = [
            "--input=" + ",".join([f.path for f in inputs]),
            "--output=" + output_dir.path,
            "--template=" + ctx.file.template.path,
        ],
        input_manifests = [ctx.file.template],
    )

    return [
        DefaultInfo(files = depset([output_dir])),
        OutputGroupInfo(
            generated_sources = depset([output_dir]),
        ),
    ]
```

## Configuration Options and Extension Points

### Build Configuration

Configure Bazel behavior through flags and options:

**Common Build Flags:**
```bash
--compilation_mode=opt           # Optimize for performance
--cpu=x86_64                      # Target CPU architecture
--define key=value                # Define custom variables
--copt=-DMY_FLAG                  # C++ compiler flag
--linkopt=-lmy_lib                # Linker flag
```

**Remote Execution Configuration:**
```bash
--remote_executor=grpc://host:port
--remote_cache=grpc://host:port
--remote_timeout=60s
```

### Extension Points

#### 1. BlazeModule System

Extend Bazel's core functionality by implementing `BlazeModule`:

```java
public class MyModule extends BlazeModule {
  @Override
  public void serverInit(OptionsParsingResult startupOptions,
                         ServerBuilder builder) {
    // Register custom command
    builder.addCommand(new MyCommand());
  }

  @Override
  public void beforeCommand(CommandEnvironment env) {
    // Hook before command execution
  }
}
```

#### 2. Custom Commands

Implement custom Bazel commands:

```java
@Command(
  name = "mycommand",
  options = {MyCommandOptions.class},
  help = "My custom command"
)
public class MyCommand implements BlazeCommand {
  @Override
  public BlazeCommandResult exec(CommandEnvironment env,
                                  OptionsParsingResult options) {
    // Command implementation
    return BlazeCommandResult.success();
  }
}
```

#### 3. Starlark Built-ins Injection

Add custom built-ins to Starlark environment via `@_builtins`:

```python
# In src/main/starlark/builtins_bzl/common/exports.bzl

exported_toplevels = {
    "my_function": _my_function_impl,
}

exported_rules = {
    "my_rule": _my_rule,
}
```

### Configuration Transitions

Change build configuration for specific dependencies:

```python
def _my_transition_impl(settings, attr):
    return {
        "//command_line_option:compilation_mode": "opt",
        "//command_line_option:cpu": "x86_64",
    }

my_transition = transition(
    implementation = _my_transition_impl,
    inputs = [],
    outputs = [
        "//command_line_option:compilation_mode",
        "//command_line_option:cpu",
    ],
)

def _rule_with_transition_impl(ctx):
    # This rule's deps will be built with transitioned config
    pass

rule_with_transition = rule(
    implementation = _rule_with_transition_impl,
    attrs = {
        "deps": attr.label_list(cfg = my_transition),
    },
)
```

This comprehensive API reference provides the foundation for extending Bazel with custom rules, aspects, and build logic tailored to specific project needs.
