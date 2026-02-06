# rules_multirun Build System

## Build System Type

rules_multirun uses **Bazel** as its build system. The repository is itself a Bazel ruleset that extends Bazel's capabilities, and it uses Bazel to build, test, and validate itself. The project supports both modern **Bzlmod** (MODULE.bazel) and legacy **WORKSPACE** dependency management systems.

## Configuration Files

### Bzlmod Configuration (Recommended)

**MODULE.bazel** defines the module and its dependencies:

```starlark
module(
    name = "rules_multirun",
    version = "0",
    compatibility_level = 1,
)

bazel_dep(name = "rules_shell", version = "0.4.1")
bazel_dep(name = "bazel_skylib", version = "1.4.2")
bazel_dep(name = "rules_python", version = "0.36.0")

bazel_dep(
    name = "stardoc",
    version = "0.7.2",
    dev_dependency = True,
    repo_name = "io_bazel_stardoc",
)
```

**WORKSPACE.bzlmod** is minimal (35 bytes), just declaring the workspace name:
```starlark
workspace(name = "rules_multirun")
```

### Legacy WORKSPACE Configuration

**WORKSPACE** (1.4KB) provides the same dependencies using http_archive for projects not yet using Bzlmod:

```starlark
workspace(name = "rules_multirun")

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "bazel_skylib",
    sha256 = "74d544d96f4a5bb630d465ca8bbcfe231e3594e5aae57e1edbf17a6eb3ca2506",
    urls = [...],
)

http_archive(
    name = "rules_python",
    sha256 = "e85ae30de33625a63eca7fc40a94fea845e641888e52f32b6beea91e8b1b2793",
    strip_prefix = "rules_python-0.27.1",
    url = "...",
)

http_archive(
    name = "rules_shell",
    sha256 = "bc61ef94facc78e20a645726f64756e5e285a045037c7a61f65af2941f4c25e1",
    strip_prefix = "rules_shell-0.4.1",
    url = "...",
)
```

### Bazel Configuration

**.bazelrc** (503 bytes) contains build flags and settings. While the full content wasn't examined, it typically includes:
- Common build flags for all commands
- Test configuration (timeout settings, test output modes)
- Platform-specific settings
- CI-specific configurations
- Optimization flags

### Root BUILD File

**BUILD** (831 bytes) at the repository root exports key labels and defines package visibility. It likely includes:
- Visibility declarations for public rules
- Exports of the main .bzl files
- Possibly a target for running all tests
- Filegroup definitions for documentation

## External Dependencies

### Core Runtime Dependencies

**bazel_skylib** (1.4.2): Essential Starlark utility library providing:
- `shell.bzl`: Shell quoting functions used in command.bzl and multirun.bzl for safe shell script generation
- Provides foundation for portable Starlark code

**rules_python** (0.36.0): Python rules and runtime:
- Required for the py_binary target in internal/BUILD
- Provides the Python runfiles library used by multirun.py
- Manages Python toolchains and runtime

**rules_shell** (0.4.1): Shell rules for shell binaries and tests:
- Used in tests/BUILD for sh_binary and sh_test targets
- Provides consistent shell script execution across platforms

### Development Dependencies

**stardoc** (0.7.2): Documentation generator marked as dev_dependency:
- Used in doc/BUILD to generate API documentation from .bzl file docstrings
- Produces the doc/README.md markdown documentation
- Not required for runtime use of the rules

### Transitive Dependencies

The Python runfiles library (from rules_python) brings in:
- Python toolchain and interpreter
- Runfiles helper libraries

Bazel's implicit dependencies include:
- `@bazel_tools//tools/bash/runfiles`: Bash runfiles library for script initialization
- `@bazel_tools//tools/allowlists/function_transition_allowlist`: Required for configuration transitions

## Build Targets and Commands

### Building Documentation

Generate API documentation using Stardoc:
```bash
bazel build //doc:all
```

This produces markdown documentation in `bazel-bin/doc/README.md` from the docstrings in the .bzl files.

### Running Tests

Execute the comprehensive test suite:
```bash
bazel test //tests:test
```

This runs `tests/test.sh`, which validates:
- Parallel and sequential execution modes
- Argument and environment variable passing
- Output buffering and printing options
- stdin forwarding
- Error handling and keep_going behavior
- Configuration transitions
- Working directory handling
- Binary args/env extraction via aspects

Run specific test scenarios:
```bash
bazel run //tests:multirun_parallel
bazel run //tests:multirun_serial
bazel run //tests:multirun_echo_stdin < input.txt
```

### Building the Python Executor

Build the internal multirun Python script:
```bash
bazel build //internal:multirun
```

This creates the executable used by all multirun targets at runtime.

### Running Examples

Execute example multirun targets from tests:
```bash
# Run two commands in parallel
bazel run //tests:multirun_parallel

# Run commands with custom descriptions
bazel run //tests:multirun_serial_description

# Run with output buffering
bazel run //tests:multirun_parallel_with_output

# Run commands from workspace root
bazel run //tests:workspace_pwd_cmd
```

### Validation Commands

**Pre-commit hooks** (.pre-commit-config.yaml):
The repository uses pre-commit hooks for code quality. Typical checks likely include:
- Buildifier for formatting .bzl and BUILD files
- Linters for Python code
- Documentation validation

Run pre-commit checks:
```bash
pre-commit run --all-files
```

**CI Validation** (.github/workflows/main.yml):
The GitHub workflow runs on pull requests and pushes, executing:
- `bazel test //...` to run all tests
- Potentially multiple Bazel versions or platforms
- Pre-commit validation
- BCR validation if pushing to BCR

## Deployment and Distribution

### Bazel Central Registry (BCR)

The `.bcr/` directory contains templates for publishing to the Bazel Central Registry:

**presubmit.yml**: Defines validation tests that BCR runs before accepting new versions:
```yaml
# Example structure (actual content may vary)
tasks:
  - bazel test //...
  - bazel build //...
```

**metadata.template.json**: Template for BCR metadata including:
- Module name and version
- Maintainer information
- Homepage and documentation URLs

**source.template.json**: Template for source archive information:
- Integrity hash (sha256)
- URL for the source archive
- Strip prefix for archive extraction

### Release Process

The release workflow (.github/workflows/create-release.yml) automates:
1. Tag creation for new versions
2. Source archive generation
3. Release notes generation (using generate-notes.sh)
4. GitHub release publishing
5. BCR submission preparation

Manual release steps:
```bash
# Create a new tag
git tag v0.14.0
git push origin v0.14.0

# GitHub Actions will:
# - Create release archive
# - Generate release notes
# - Publish to GitHub releases
# - Optionally submit to BCR
```

### Installation for Users

**Bzlmod users** add to MODULE.bazel:
```starlark
bazel_dep(name = "rules_multirun", version = "0.13.0")
```

**WORKSPACE users** add http_archive declaration:
```starlark
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "rules_multirun",
    sha256 = "...",
    url = "https://github.com/keith/rules_multirun/archive/refs/tags/v0.13.0.tar.gz",
)
```

Then load dependencies per the WORKSPACE file instructions.

## Testing Strategy

### Test Structure

The **tests/** directory contains a comprehensive integration test suite:

1. **Shell test fixtures** for validation:
   - `validate-args.sh`: Verifies argument passing
   - `validate-env.sh`: Verifies environment variables
   - `validate-chdir-location.sh`: Tests location expansion and directory handling
   - `echo_hello.sh`, `echo_hello2.sh`: Simple output tests
   - `echo_and_fail.sh`: Error handling tests

2. **Python test fixtures**:
   - `echo_stdin.py`, `echo_stdin2.py`: stdin forwarding validation

3. **Main test script** (`test.sh`):
   - Orchestrates execution of all test scenarios
   - Validates output and exit codes
   - Tests parallel and sequential modes
   - Verifies edge cases and error conditions

4. **Example BUILD targets**:
   - Demonstrate all rule features and attributes
   - Serve as integration tests when run
   - Provide working examples for documentation

### Test Coverage

The test suite validates:
- ✓ Parallel execution (jobs = 0)
- ✓ Sequential execution (default)
- ✓ Keep-going on failure
- ✓ Output buffering
- ✓ Command printing control
- ✓ Argument passing and expansion
- ✓ Environment variable setting and expansion
- ✓ stdin forwarding to multiple commands
- ✓ Configuration transitions
- ✓ Working directory control (workspace root vs execution root)
- ✓ Binary args/env extraction via aspects
- ✓ Custom descriptions
- ✓ Location expansion in arguments and environment
- ✓ Runtime data dependencies

### CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/main.yml`) runs on:
- Pull requests
- Pushes to main branch
- Manual triggers

Typical CI steps:
1. Checkout code
2. Set up Bazel (potentially multiple versions)
3. Run `bazel test //...`
4. Run pre-commit validation
5. Test on multiple platforms (Linux, macOS, possibly Windows)
6. Validate BCR integration

The CI ensures all tests pass before merging and validates that the rules work across different Bazel versions and platforms.
