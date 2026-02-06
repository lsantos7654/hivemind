# rules_uv - Build System

## Build System Type

Rules_uv uses **Bazel** as its build system, leveraging the modern **bzlmod** (Bazel modules) for dependency management. The project is structured as a Bazel module that can be consumed by other Bazel projects through the Bazel Central Registry (BCR).

### Bazel Version Requirements
- **Minimum**: Bazel 6.x
- **Recommended**: Bazel 7.x
- **Version Pinning**: Uses `.bazelversion` file to ensure consistency

### Module System
The project uses bzlmod exclusively:
- `MODULE.bazel` defines the module and its dependencies
- `WORKSPACE.bazel` exists but is empty (bzlmod-only)
- Compatibility level: 1 (indicates API stability guarantees)

## Configuration Files

### MODULE.bazel
The primary configuration file for the ruleset:

```starlark
module(
    name = "rules_uv",
    version = "0.0.0",
    compatibility_level = 1,
)

bazel_dep(name = "bazel_skylib", version = "1.4.1")
bazel_dep(name = "platforms", version = "0.0.8")
bazel_dep(name = "rules_multitool", version = "0.11.0")
bazel_dep(name = "rules_python", version = "0.34.0")

bazel_dep(name = "buildifier_prebuilt", version = "7.3.1", dev_dependency = True)

multitool = use_extension("@rules_multitool//multitool:extension.bzl", "multitool")
multitool.hub(lockfile = "//uv/private:uv.lock.json")
use_repo(multitool, "multitool")
```

**Key Components**:
- **Module identity**: Name, version (0.0.0 in development), compatibility level
- **Runtime dependencies**: Required for the rules to function
- **Dev dependencies**: Only needed for ruleset development (buildifier)
- **Extension configuration**: Sets up rules_multitool to manage uv binaries

### .bazelrc
Configures Bazel behavior and flags:
- Common flags shared across all commands
- Platform-specific configurations
- Performance optimizations
- CI-specific settings loaded from `.github/workflows/ci.bazelrc`

### BUILD.bazel Files
Multiple BUILD files organize the project:

**Root BUILD.bazel**: Exports license and documentation

**uv/BUILD.bazel**: Exports public API
```python
exports_files([
    "pip.bzl",
    "venv.bzl",
])
```

**uv/private/BUILD.bazel**: Exports private implementation files and templates
```python
exports_files([
    "pip.bzl",
    "venv.bzl",
    "interpreter_path.bzl",
    "transition_to_target.bzl",
    "create_venv.sh",
    "sync_venv.sh",
    "pip_compile.sh",
    "pip_compile_test.sh",
    "uv.lock.json",
])
```

## External Dependencies and Management

### Core Runtime Dependencies

**bazel_skylib (v1.4.1+)**
- Purpose: Provides common Starlark utilities
- Used for: Type checking (`types.is_list`), write_file rules
- Why needed: Standard library functions not in core Bazel

**platforms (v0.0.8+)**
- Purpose: Platform constraint definitions
- Used for: OS and CPU detection (linux, macos, windows, x86_64, arm64)
- Why needed: Multi-platform requirements.txt generation with `select()`

**rules_multitool (v0.11.0+)**
- Purpose: Cross-platform binary download and management
- Used for: Managing uv binaries across all supported platforms
- Why needed: Hermetic builds require bundled tooling, not PATH dependencies
- Configuration: Lockfile at `uv/private/uv.lock.json`

**rules_python (v0.34.0+)**
- Purpose: Python toolchain and runtime management
- Used for: Python interpreter discovery, PyRuntimeInfo provider, py3_runtime resolution
- Why needed: rules_uv needs to know which Python version to target
- User requirement: Users must declare rules_python in their MODULE.bazel

### Development Dependencies

**buildifier_prebuilt (v7.3.1)**
- Purpose: Bazel file formatting and linting
- Used for: Code quality enforcement
- Dev-only: Marked with `dev_dependency = True`

### Binary Dependencies (via rules_multitool)

The `uv.lock.json` file defines platform-specific uv binary downloads:

**Linux**:
- x86_64: `uv-x86_64-unknown-linux-gnu.tar.gz`
- arm64: `uv-aarch64-unknown-linux-musl.tar.gz`

**macOS**:
- x86_64: `uv-x86_64-apple-darwin.tar.gz`
- arm64: `uv-aarch64-apple-darwin.tar.gz`

**Windows**:
- x86_64: `uv-x86_64-pc-windows-msvc.zip`
- arm64: `uv-aarch64-pc-windows-msvc.zip`

All downloads come from GitHub releases (`github.com/astral-sh/uv/releases`), currently pinned to **uv version 0.8.12**.

Each binary entry includes:
- Download URL
- SHA256 checksum for integrity verification
- Platform constraints (os, cpu)
- Path to executable within archive

### Dependency Update Strategy

**Automated Updates**:
- GitHub Actions workflow `periodic-update-multitool.yml` runs periodically
- Checks for new uv releases
- Updates `uv.lock.json` automatically
- Creates pull requests for maintainer review

**Manual Updates**:
```bash
# Update all multitool binaries
bazel run @multitool//tools/updater
```

## Build Targets and Commands

### For End Users (Consuming the Ruleset)

**Compile Requirements**:
```bash
# Update requirements.txt from requirements.in
bazel run //:generate_requirements_txt

# Alternative syntax (compatibility with rules_python)
bazel run //:generate_requirements_txt.update

# Test that requirements.txt is up-to-date
bazel test //:generate_requirements_txt_test
```

**Create Virtual Environment**:
```bash
# Create venv in default location (./venv)
bazel run //:create_venv

# Create venv in custom location
bazel run //:create_venv -- /path/to/venv

# Sync existing venv to match requirements exactly
bazel run //:sync_venv
```

**Multi-Platform Workflows**:
```bash
# Generate requirements for multiple platforms (with rules_multirun)
bazel run //:generate_requirements_lock

# Run all platform-specific compilations in sequence
# (jobs=1 allows uv cache reuse)
```

### For Ruleset Development

**Code Formatting**:
```bash
# Format all Bazel files
bazel run @buildifier_prebuilt//:buildifier

# Check formatting without modifying
bazel run @buildifier_prebuilt//:buildifier_test
```

**Testing**:
```bash
# Run all tests
bazel test //...

# Run example tests
bazel test //examples/...

# Test specific example
bazel test //examples/typical:all
```

**Building Examples**:
```bash
# Run example pip compilation
bazel run //examples/typical:generate_requirements_txt

# Create example venv
bazel run //examples/typical:create-venv
```

## How to Build, Test, and Deploy

### Building the Ruleset

Rules_uv is a pure Starlark ruleset with no compilation step. "Building" means:
1. Loading the module into your workspace
2. Resolving dependencies via bzlmod
3. Downloading uv binaries via rules_multitool

**For consumers**:
```starlark
# In your MODULE.bazel
bazel_dep(name = "rules_uv", version = "X.Y.Z")
bazel_dep(name = "rules_python", version = "0.34.0")
```

**For development**:
```bash
# Clone the repository
git clone https://github.com/theoremlp/rules_uv.git
cd rules_uv

# Test that everything works
bazel test //...

# Run examples
bazel run //examples/typical:generate_requirements_txt
```

### Testing Strategy

**Test Categories**:

1. **Diff Tests**: Automatically created by `pip_compile`
   - Verify requirements.txt matches requirements.in
   - Run with `--no-cache` for reproducibility
   - Tagged with `requires-network` (downloads packages)

2. **Example Validation**: Examples serve as integration tests
   - Each example is a complete workspace
   - Tests multi-platform scenarios
   - Validates different configuration options

3. **CI Testing**: GitHub Actions workflows
   - Tests on Linux, macOS, Windows
   - Tests with multiple Bazel versions
   - Tests with multiple Python versions

**Running Tests**:
```bash
# All tests
bazel test //...

# Specific size categories
bazel test --test_size_filters=small //...

# With network access (for pip tests)
bazel test --test_tag_filters=requires-network //...

# Without network access
bazel test --test_tag_filters=-requires-network //...
```

### Deployment and Release Process

**Version Numbering**:
- Semantic versioning (MAJOR.MINOR.PATCH)
- Development versions use 0.0.0
- Released versions follow semver conventions

**Release Steps**:
1. **Prepare Release**: Run `release_prep.sh` script
   - Updates version numbers
   - Validates MODULE.bazel
   - Ensures tests pass

2. **Create Tag**: Tag commit with version
   ```bash
   git tag vX.Y.Z
   git push origin vX.Y.Z
   ```

3. **Automated Workflows**:
   - `release.yml`: Creates GitHub release
   - `publish-to-bcr.yml`: Submits to Bazel Central Registry
   - BCR automation in `.bcr/` directory

4. **BCR Publication**:
   - Automated via `publish-to-bcr` GitHub Action
   - Creates pull request in bazelbuild/bazel-central-registry
   - Includes metadata, source archive, and MODULE.bazel
   - After merge, available to all Bazel users

**Auto-Release**:
- `automation-autorelease.yml` can trigger releases automatically
- Based on commit patterns or schedule
- Follows conventional commits for version bumps

### Integration with CI/CD

**GitHub Actions Workflows**:

**`ci.yml`**: Main CI pipeline
- Runs on push and pull requests
- Tests across multiple platforms
- Validates examples
- Checks code formatting with buildifier

**`periodic-update-multitool.yml`**: Dependency updates
- Runs on schedule (weekly/monthly)
- Updates uv binary versions
- Creates PRs for maintainer review

**CI Configuration**:
- Uses `ci.bazelrc` for CI-specific flags
- Caches Bazel outputs for faster builds
- Runs hermetically (no external network dependencies except for downloads)

### Local Development Workflow

**Setup**:
```bash
# Install Bazelisk (auto-manages Bazel versions)
# Available via package managers or from GitHub releases

# Clone and enter directory
git clone https://github.com/theoremlp/rules_uv.git
cd rules_uv
```

**Iterative Development**:
```bash
# Make changes to .bzl files
vim uv/private/pip.bzl

# Test changes with examples
bazel run //examples/typical:generate_requirements_txt

# Run tests
bazel test //...

# Format code
bazel run @buildifier_prebuilt//:buildifier
```

**Testing Changes in External Projects**:
```starlark
# In consuming project's MODULE.bazel
bazel_dep(name = "rules_uv", version = "0.0.0")
local_path_override(
    module_name = "rules_uv",
    path = "/path/to/local/rules_uv",
)
```

### Performance Considerations

**Build Performance**:
- Rules are analysis-time only (no compilation)
- uv binary downloads are cached by rules_multitool
- Bazel's action cache prevents redundant uv invocations

**Test Performance**:
- Diff tests are `size = "small"` by default
- Can override with `size` parameter
- Network-dependent tests can be slow on first run
- uv's cache (`~/.cache/uv`) speeds up subsequent runs

**Multi-Platform Optimization**:
- Use `rules_multirun` with `jobs = 1` to reuse uv cache
- First platform population benefits subsequent platforms
- Alternative: run in parallel (`jobs = 0`) if cold cache doesn't matter
