# rules_multirun Code Structure

## Complete Directory Tree

```
rules_multirun/
├── .bazelrc                      # Bazel configuration options
├── .bcr/                         # Bazel Central Registry metadata
│   ├── metadata.template.json   # BCR metadata template
│   ├── presubmit.yml            # BCR presubmit configuration
│   └── source.template.json     # BCR source template
├── .github/                      # GitHub workflows and automation
│   ├── workflows/
│   │   ├── create-release.yml   # Release automation workflow
│   │   └── main.yml             # CI workflow for tests
│   └── generate-notes.sh        # Release notes generation script
├── .gitignore                    # Git ignore patterns
├── .pre-commit-config.yaml       # Pre-commit hooks configuration
├── BUILD                         # Root BUILD file with visibility exports
├── LICENSE                       # Apache 2.0 license
├── MODULE.bazel                  # Bzlmod module definition
├── README.md                     # User-facing documentation
├── WORKSPACE                     # Legacy WORKSPACE configuration
├── WORKSPACE.bzlmod              # Minimal bzlmod WORKSPACE file
├── defs.bzl                      # Public API exports
├── command.bzl                   # Command rule implementation
├── multirun.bzl                  # Multirun rule implementation
├── doc/                          # Generated API documentation
│   ├── BUILD                     # Stardoc generation rules
│   └── README.md                 # Generated Stardoc documentation
├── internal/                     # Internal implementation details
│   ├── BUILD                     # Python binary for multirun executor
│   ├── constants.bzl             # Shared constants and utilities
│   └── multirun.py               # Python execution engine
└── tests/                        # Test suite
    ├── BUILD                     # Test targets and examples
    ├── custom_executable.bzl     # Custom rule for testing
    ├── transitions.bzl           # Test transition definitions
    ├── test.sh                   # Main test script
    ├── echo_hello.sh             # Test fixture
    ├── echo_hello2.sh            # Test fixture
    ├── echo_and_fail.sh          # Test fixture for error handling
    ├── echo_stdin.py             # Test fixture for stdin forwarding
    ├── echo_stdin2.py            # Test fixture for stdin forwarding
    ├── validate-args.sh          # Test fixture for argument passing
    ├── validate-env.sh           # Test fixture for environment variables
    ├── validate-chdir-location.sh # Test fixture for directory changes
    ├── default-pwd.sh            # Test fixture for default working directory
    └── workspace-pwd.sh          # Test fixture for workspace root execution
```

## Module and Package Organization

### Public API Layer (`/`)

**defs.bzl**: This is the primary entry point for users. It re-exports the main rules from `command.bzl` and `multirun.bzl`, providing a clean, stable API surface. Users should always import from this file rather than internal modules:

```starlark
load("@rules_multirun//:defs.bzl", "command", "multirun", "command_with_transition", "multirun_with_transition", "command_force_opt")
```

The module pattern (importing with underscores and re-exporting without) provides flexibility to refactor internal organization without breaking users.

### Rule Implementation Layer

**command.bzl** (194 lines): Contains the implementation of the `command` rule and its variants. Key components:
- `_command_impl`: The rule implementation function that generates bash wrapper scripts
- `_expand_and_quote`: Helper for safe shell expansion and quoting
- `command_with_transition`: Factory function for creating command rules with custom configuration transitions
- `_force_opt`: A built-in transition that forces compilation mode to "opt"
- `command` and `command_force_opt`: Concrete rule instances

**multirun.bzl** (251 lines): Implements the `multirun` rule and its variants. Key components:
- `_multirun_impl`: The rule implementation that generates JSON instructions and bash wrappers
- `_BinaryArgsEnvInfo`: Provider for passing args/env from binary rules to multirun
- `_binary_args_env_aspect`: Aspect that extracts args and env from executable targets
- `multirun_with_transition`: Factory function for creating multirun rules with configuration transitions
- `multirun`: The standard multirun rule instance

### Internal Implementation Layer (`internal/`)

**constants.bzl** (57 lines): Shared utilities and constants:
- `RUNFILES_PREFIX`: Bash script template for initializing the Bazel runfiles environment (v2 initialization)
- `CommandInfo`: Provider for passing command descriptions from command rules to multirun rules
- `update_attrs`: Helper for adding transition allowlist attributes when needed
- `rlocation_path`: Computes the runfiles lookup path for a file, handling external repositories correctly

**multirun.py** (151 lines): The Python execution engine that actually runs the commands. Key components:
- `Command`: NamedTuple representing a command to execute
- `_run_command`: Executes a single command with proper environment setup, with special handling for Windows (requires bash)
- `_perform_concurrently`: Parallel execution with output buffering and stdin forwarding support
- `_perform_serially`: Sequential execution with keep_going support
- `_forward_stdin`: Thread function for forwarding stdin to multiple processes
- `_script_path`: Resolves runfiles paths using the Python runfiles library
- `_main`: Entry point that loads JSON instructions and orchestrates execution

**BUILD** (internal): Defines the `py_binary` target for the multirun executor, with dependencies on the Python runfiles library.

## Main Source Directories

### `/` (Root Directory)
Contains the public API and core rule implementations. This is where all user-facing .bzl files live. The separation between public (defs.bzl) and implementation (command.bzl, multirun.bzl) follows Bazel best practices.

### `/internal`
Contains implementation details that users should not directly depend on. The Python execution engine and shared utilities live here. The BUILD file marks most targets with restricted visibility.

### `/doc`
Contains generated API documentation produced by Stardoc. The BUILD file defines rules that generate markdown documentation from the docstrings in the .bzl files.

### `/tests`
Comprehensive test suite demonstrating all features. Tests use shell scripts and Python scripts as fixtures, with a main test.sh script that validates all behavior. The BUILD file shows practical examples of using the rules.

### `/.bcr`
Bazel Central Registry integration files for publishing the module. Contains templates for metadata and source declarations, along with presubmit configuration for BCR validation.

### `/.github`
CI/CD automation including test workflows (main.yml) and release automation (create-release.yml). The generate-notes.sh script creates release notes from git history.

## Key Files and Their Roles

### Configuration Files

**.bazelrc** (503 bytes): Bazel configuration including build flags, test options, and platform-specific settings. Likely includes settings for reproducible builds and common flags for CI.

**MODULE.bazel** (366 bytes): Bzlmod module definition declaring dependencies on bazel_skylib (1.4.2), rules_python (0.36.0), rules_shell (0.4.1), and stardoc (0.7.2 dev dependency). Sets compatibility level to 1.

**WORKSPACE** (1.4KB): Legacy workspace configuration using http_archive for all dependencies. Maintained for users not yet on Bzlmod.

**WORKSPACE.bzlmod** (35 bytes): Minimal workspace file that just declares the workspace name, deferring to MODULE.bazel for dependencies.

### Entry Points

**defs.bzl**: The main entry point for all users. Imports and re-exports command, command_force_opt, command_with_transition, multirun, and multirun_with_transition.

**internal/multirun.py**: The runtime entry point. When a multirun target executes, this script is invoked with a JSON instructions file and extra command-line arguments.

### Documentation

**README.md** (2.4KB): User-facing documentation with quick-start examples, usage patterns for transitions, and installation instructions. Points to the generated API docs in the doc/ directory.

**doc/README.md** (5.7KB): Generated Stardoc documentation with complete API reference for all rules and functions, including attribute descriptions, types, and default values.

## Code Organization Patterns

### Provider Pattern
The codebase uses Bazel providers for passing information between rules:
- `CommandInfo`: Passes custom descriptions from command rules to multirun
- `_BinaryArgsEnvInfo`: Internal provider for extracting args/env from binaries
- `RunEnvironmentInfo`: Standard Bazel provider for environment variables
- `DefaultInfo`: Standard provider for files, runfiles, and executables

### Aspect Pattern
The `_binary_args_env_aspect` in multirun.bzl demonstrates the aspect pattern, allowing multirun to inspect and extract args and env attributes from command targets, even when those commands are themselves wrappers around other binaries.

### Factory Pattern
Both `command_with_transition` and `multirun_with_transition` are factory functions that create rule instances with specific configurations. This enables users to define project-specific variants without duplicating implementation code.

### Runfiles Pattern
Extensive use of Bazel's runfiles mechanism ensures all dependencies are available at runtime:
- Analysis phase: Rules merge runfiles from all dependencies
- Execution phase: Generated scripts initialize runfiles using `RUNFILES_PREFIX`
- Python script: Uses runfiles.Rlocation() to find executables

### JSON Instruction Pattern
The multirun rule generates a JSON file containing all execution instructions (commands, args, env, jobs settings, etc.). This cleanly separates the analysis phase (Starlark) from the execution phase (Python), with a well-defined interface between them.

### Script Generation Pattern
Both command and multirun rules generate bash wrapper scripts that:
1. Initialize the runfiles environment
2. Set environment variables
3. Change directories if needed
4. Delegate to the actual executable

This pattern provides a consistent entry point regardless of the underlying implementation language.
