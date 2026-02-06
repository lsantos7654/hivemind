# rules_multirun APIs and Interfaces

## Public API Overview

The rules_multirun API consists of two main rules (`command` and `multirun`) and two factory functions for creating variants with custom configuration transitions. All public APIs are exported through `defs.bzl`.

## Loading the Rules

```starlark
load("@rules_multirun//:defs.bzl", "command", "multirun")

# Advanced features
load("@rules_multirun//:defs.bzl",
     "command_force_opt",
     "command_with_transition",
     "multirun_with_transition")
```

## Core Rules

### command Rule

The `command` rule wraps an executable target, allowing you to customize its execution with specific arguments, environment variables, and runtime dependencies.

**Signature:**
```starlark
command(
    name,
    command,
    arguments = [],
    environment = {},
    data = [],
    description = "",
    run_from_workspace_root = False,
)
```

**Attributes:**

- **name** (Name, required): A unique name for this target
- **command** (Label, required): The executable target to wrap (e.g., `:my_linter`)
- **arguments** (List[string], optional): Command-line arguments passed to the command. Supports `$(location)` expansion
- **environment** (Dict[string, string], optional): Environment variables to set. Supports `$(location)` expansion
- **data** (List[Label], optional): Runtime data dependencies available to the command
- **description** (string, optional): Custom description printed during multirun execution
- **run_from_workspace_root** (bool, optional, default=False): If true, command runs from workspace root (`BUILD_WORKSPACE_DIRECTORY`) instead of execution root

**Usage Example:**

```starlark
load("@rules_multirun//:defs.bzl", "command")
load("@rules_python//python:defs.bzl", "py_binary")

py_binary(
    name = "black_formatter",
    srcs = ["//tools:black.py"],
)

command(
    name = "format_python",
    command = ":black_formatter",
    arguments = ["--check", "$(location //src:main.py)"],
    environment = {
        "BLACK_CACHE_DIR": "/tmp/black_cache",
        "CONFIG_FILE": "$(location //:.black.toml)",
    },
    data = [
        "//src:main.py",
        "//:.black.toml",
    ],
    description = "Formatting Python files with Black",
)

# Can be run directly
# bazel run //:format_python
```

**Location Expansion:**

Both `arguments` and `environment` support `$(location)` expansion for referencing other Bazel targets:

```starlark
command(
    name = "lint_with_config",
    command = ":eslint",
    arguments = [
        "--config", "$(location //:eslint.config.js)",
        "$(location //src:app.js)",
    ],
    data = [
        "//:eslint.config.js",
        "//src:app.js",
    ],
)
```

**Special rlocation Expansion:**

For advanced use cases, you can use `$(rlocation)` syntax to get runfiles paths without shell escaping:

```starlark
command(
    name = "custom_script",
    command = ":my_script",
    arguments = ["$(rlocation @external_repo//path:file.txt)"],
    data = ["@external_repo//path:file.txt"],
)
```

### multirun Rule

The `multirun` rule composes multiple commands (or any executable targets) to run them in a single `bazel run` invocation, either sequentially or in parallel.

**Signature:**
```starlark
multirun(
    name,
    commands = [],
    jobs = 1,
    data = [],
    print_command = True,
    keep_going = False,
    buffer_output = False,
    forward_stdin = False,
)
```

**Attributes:**

- **name** (Name, required): A unique name for this target
- **commands** (List[Label], optional): List of executable targets to run (typically `command` targets, but can be any executable)
- **jobs** (int, optional, default=1): Concurrency level:
  - `1` (default): Sequential execution
  - `0`: Unlimited parallelism
  - `N > 1`: Up to N commands in parallel (though implementation treats any > 0 as unlimited)
- **data** (List[Label], optional): Additional runtime data dependencies
- **print_command** (bool, optional, default=True): Print command description before execution
- **keep_going** (bool, optional, default=False): Continue running subsequent commands after failure (sequential mode only)
- **buffer_output** (bool, optional, default=False): Buffer command output and print after completion (parallel mode only)
- **forward_stdin** (bool, optional, default=False): Forward stdin to all commands (parallel mode only)

**Usage Example - Sequential Execution:**

```starlark
load("@rules_multirun//:defs.bzl", "command", "multirun")

multirun(
    name = "lint_all",
    commands = [
        ":lint_python",
        ":lint_javascript",
        ":lint_css",
    ],
    # jobs = 1 is default (sequential)
)

# bazel run //:lint_all
# Runs each linter one after another
```

**Usage Example - Parallel Execution:**

```starlark
multirun(
    name = "lint_parallel",
    commands = [
        ":lint_python",
        ":lint_javascript",
        ":lint_css",
    ],
    jobs = 0,  # Run all in parallel
    buffer_output = True,  # Prevent interleaved output
)

# bazel run //:lint_parallel
# Runs all linters simultaneously
```

**Usage Example - Keep Going:**

```starlark
multirun(
    name = "format_all",
    commands = [
        ":format_python",
        ":format_javascript",
        ":format_go",
    ],
    keep_going = True,  # Don't stop on first failure
)

# Even if format_python fails, format_javascript and format_go still run
```

**Usage Example - stdin Forwarding:**

```starlark
command(
    name = "process1",
    command = ":processor1",
)

command(
    name = "process2",
    command = ":processor2",
)

multirun(
    name = "process_stdin",
    commands = [":process1", ":process2"],
    jobs = 0,
    forward_stdin = True,
)

# echo "input data" | bazel run //:process_stdin
# Both processors receive the same stdin input
```

## Advanced Rules

### command_force_opt Rule

A variant of `command` that forces the compilation mode of dependencies to "opt" (optimized). Useful when tools perform better with optimizations enabled.

**Usage:**

```starlark
load("@rules_multirun//:defs.bzl", "command_force_opt", "multirun")

command_force_opt(
    name = "heavy_linter_optimized",
    command = ":heavy_linter",
    arguments = ["--all"],
)

multirun(
    name = "lint",
    commands = [":heavy_linter_optimized"],
)
```

The `heavy_linter` and its dependencies will be built with `-c opt` regardless of the command-line flags.

**Alternative Import Pattern:**

```starlark
# Use force_opt version as default
load("@rules_multirun//:defs.bzl", "multirun", command = "command_force_opt")

command(
    name = "fast_tool",
    command = ":tool",
)
# This now uses command_force_opt
```

## Factory Functions for Custom Transitions

### command_with_transition Function

Creates a custom `command` rule variant with a specific configuration transition.

**Signature:**
```starlark
command_with_transition(cfg, allowlist = None, doc = None)
```

**Parameters:**

- **cfg**: A Bazel transition object (either a string like "target" or a transition() created with `transition()`)
- **allowlist** (optional): Label for transition allowlist (required for some Bazel versions)
- **doc** (optional): Custom documentation for the generated rule

**Returns:** A new rule that behaves like `command` but applies the transition

**Usage Example - Platform Transition:**

```starlark
load("@rules_multirun//:defs.bzl", "command_with_transition")

# Define a transition to AWS Lambda platform
def _lambda_transition_impl(settings, attr):
    return {"//command_line_option:platforms": ["//platforms:aws_lambda"]}

lambda_transition = transition(
    implementation = _lambda_transition_impl,
    inputs = [],
    outputs = ["//command_line_option:platforms"],
)

# Create custom command rule with the transition
command_lambda = command_with_transition(
    lambda_transition,
    "@bazel_tools//tools/allowlists/function_transition_allowlist",
)

# Use it in BUILD files
command_lambda(
    name = "deploy_function",
    command = ":deployment_script",
    arguments = ["--region", "us-west-2"],
)
```

**Usage Example - Compilation Mode Transition:**

```starlark
def _debug_transition_impl(settings, attr):
    return {"//command_line_option:compilation_mode": "dbg"}

debug_transition = transition(
    implementation = _debug_transition_impl,
    inputs = [],
    outputs = ["//command_line_option:compilation_mode"],
)

command_debug = command_with_transition(debug_transition)

command_debug(
    name = "debug_tool",
    command = ":analyzer",
)
# The analyzer will be built with debug symbols
```

### multirun_with_transition Function

Creates a custom `multirun` rule variant with a specific configuration transition applied to all commands.

**Signature:**
```starlark
multirun_with_transition(cfg, allowlist = None)
```

**Parameters:**

- **cfg**: A Bazel transition object
- **allowlist** (optional): Label for transition allowlist

**Returns:** A new rule that behaves like `multirun` but transitions all commands

**Usage Example - Multi-Platform Deployment:**

```starlark
load("@rules_multirun//:defs.bzl", "multirun_with_transition")

def _production_transition_impl(settings, attr):
    return {"//command_line_option:platforms": ["//platforms:production"]}

production_transition = transition(
    implementation = _production_transition_impl,
    inputs = [],
    outputs = ["//command_line_option:platforms"],
)

deploy_production = multirun_with_transition(
    production_transition,
    "@bazel_tools//tools/allowlists/function_transition_allowlist",
)

deploy_production(
    name = "deploy_all_services",
    commands = [
        ":deploy_api",
        ":deploy_frontend",
        ":deploy_worker",
    ],
    jobs = 0,
)
# All deploy commands transition to production platform
```

## Integration Patterns

### Pattern 1: Linting and Formatting Workflow

```starlark
load("@rules_multirun//:defs.bzl", "command", "multirun")

# Define individual linters
command(
    name = "lint_python",
    command = "@pip//pylint",
    arguments = ["src/"],
)

command(
    name = "lint_javascript",
    command = "//tools:eslint",
    arguments = ["--max-warnings=0", "web/"],
)

command(
    name = "format_check_python",
    command = "@pip//black",
    arguments = ["--check", "src/"],
)

command(
    name = "format_check_js",
    command = "//tools:prettier",
    arguments = ["--check", "web/"],
)

# Compose into workflows
multirun(
    name = "lint",
    commands = [":lint_python", ":lint_javascript"],
    jobs = 0,  # Parallel
)

multirun(
    name = "format_check",
    commands = [":format_check_python", ":format_check_js"],
    jobs = 0,
)

multirun(
    name = "ci_checks",
    commands = [":lint", ":format_check"],
    # Sequential - run all lints, then all format checks
)

# Usage:
# bazel run //:lint             # Just linting
# bazel run //:format_check     # Just format checking
# bazel run //:ci_checks        # Full CI validation
```

### Pattern 2: Multi-Environment Deployment

```starlark
load("@rules_multirun//:defs.bzl", "command", "multirun")

command(
    name = "deploy_us_east",
    command = "//deploy:deploy_script",
    arguments = ["--region=us-east-1"],
    environment = {"ENV": "production"},
)

command(
    name = "deploy_us_west",
    command = "//deploy:deploy_script",
    arguments = ["--region=us-west-2"],
    environment = {"ENV": "production"},
)

command(
    name = "deploy_eu_west",
    command = "//deploy:deploy_script",
    arguments = ["--region=eu-west-1"],
    environment = {"ENV": "production"},
)

multirun(
    name = "deploy_all_regions",
    commands = [
        ":deploy_us_east",
        ":deploy_us_west",
        ":deploy_eu_west",
    ],
    jobs = 0,  # Deploy to all regions in parallel
    buffer_output = True,  # Keep deployment logs separate
)

# bazel run //:deploy_all_regions
```

### Pattern 3: Conditional Execution with Wrapper Scripts

```starlark
# BUILD file
command(
    name = "conditional_test",
    command = ":wrapper_script",
    environment = {
        "ACTUAL_COMMAND": "$(rlocation //tests:actual_test)",
        "RUN_INTEGRATION": "true",
    },
    data = ["//tests:actual_test"],
)

# wrapper_script.sh
#!/bin/bash
if [ "$RUN_INTEGRATION" = "true" ]; then
    exec "$ACTUAL_COMMAND"
else
    echo "Skipping integration tests"
    exit 0
fi
```

### Pattern 4: Working Directory Control

```starlark
command(
    name = "run_in_workspace",
    command = ":script",
    run_from_workspace_root = True,
)

# The script will run with CWD = workspace root
# Useful for tools that modify source files
```

## Configuration Options

### Execution Mode Selection

```starlark
# Sequential (default) - commands run one after another
multirun(
    name = "sequential",
    commands = [":cmd1", ":cmd2"],
)

# Parallel - all commands run simultaneously
multirun(
    name = "parallel",
    commands = [":cmd1", ":cmd2"],
    jobs = 0,
)
```

### Output Control

```starlark
# Unbuffered (default) - output appears immediately
multirun(
    name = "unbuffered",
    commands = [":cmd1", ":cmd2"],
    jobs = 0,
)

# Buffered - output appears after each command completes
multirun(
    name = "buffered",
    commands = [":cmd1", ":cmd2"],
    jobs = 0,
    buffer_output = True,
)

# Silent - no command printing
multirun(
    name = "silent",
    commands = [":cmd1", ":cmd2"],
    print_command = False,
)
```

### Error Handling

```starlark
# Fail-fast (default) - stop on first error
multirun(
    name = "strict",
    commands = [":cmd1", ":cmd2", ":cmd3"],
)

# Keep-going - run all commands even if some fail
multirun(
    name = "best_effort",
    commands = [":cmd1", ":cmd2", ":cmd3"],
    keep_going = True,
)
# Exit code will be non-zero if any command failed
```

## Extension Points

### Custom Executable Rules

You can pass any executable target to `multirun`, not just `command` targets:

```starlark
sh_binary(
    name = "my_script",
    srcs = ["script.sh"],
)

py_binary(
    name = "my_tool",
    srcs = ["tool.py"],
)

multirun(
    name = "run_both",
    commands = [":my_script", ":my_tool"],
)
```

### Binary Args and Env Extraction

If you define args and env directly on binaries, multirun can extract them via aspects:

```starlark
sh_binary(
    name = "configured_tool",
    srcs = ["tool.sh"],
    args = ["--verbose"],
    env = {"LOG_LEVEL": "debug"},
)

multirun(
    name = "run_tool",
    commands = [":configured_tool"],
)
# The tool runs with --verbose and LOG_LEVEL=debug
```

### Custom Providers

The `CommandInfo` provider allows custom description strings:

```starlark
command(
    name = "lint_typescript",
    command = "//tools:tslint",
    description = "🔍 Linting TypeScript files...",
)

multirun(
    name = "lint",
    commands = [":lint_typescript"],
)
# Output will show: 🔍 Linting TypeScript files...
```

## Common Patterns and Best Practices

1. **Parallel for independent operations**: Use `jobs = 0` for linters, formatters, or deployments that don't interfere with each other

2. **Sequential for dependent operations**: Use default sequential mode when commands must run in order or modify shared state

3. **Buffer output in parallel mode**: Always use `buffer_output = True` with `jobs = 0` to prevent interleaved output

4. **Keep-going for formatters**: Use `keep_going = True` when you want to see all issues, not just the first failure

5. **Custom descriptions for clarity**: Add `description` attributes to make multirun output more user-friendly

6. **Location expansion for portability**: Always use `$(location)` for file references instead of hardcoded paths

7. **Data dependencies for runtime files**: Include all files needed at runtime in `data` attribute for proper runfiles handling

8. **Workspace root for source modifications**: Use `run_from_workspace_root = True` for tools that write to source files (formatters, code generators)
