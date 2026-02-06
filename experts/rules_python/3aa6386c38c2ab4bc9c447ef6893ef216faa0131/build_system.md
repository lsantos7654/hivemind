# rules_python Build System

## Build System Type and Configuration Files

`rules_python` is built using Bazel itself and uses the Bzlmod module system as the primary configuration mechanism, with legacy WORKSPACE support maintained for backward compatibility.

**Primary Configuration Files:**

- **`MODULE.bazel`**: The main Bzlmod module definition file declaring the module name (`rules_python`), version, and compatibility level. This file configures all dependencies, registers Python toolchains, sets up pip integration, and defines development dependencies. It includes extensive platform configuration for pip's multi-platform wheel resolution.

- **`WORKSPACE`**: Legacy WORKSPACE file for non-Bzlmod builds. Contains http_archive declarations for dependencies and calls to repository rules for setup.

- **`WORKSPACE.bzlmod`**: Special file for loading additional WORKSPACE content when using Bzlmod, primarily used for development and testing scenarios that can't be expressed purely in Bzlmod.

- **`BUILD.bazel`**: Root build file defining top-level targets, file groups, and package visibility rules.

- **`.bazelrc`**: Comprehensive Bazel configuration including:
  - Platform definitions for Linux, macOS, and Windows
  - Build and test flags
  - CI-specific configurations
  - Remote execution settings
  - Feature flags (e.g., `--enable_bzlmod`)
  - Python-specific flags like `--python_version`

- **`.bazelversion`**: Pinned Bazel version (currently Bazel 7+) ensuring consistent builds across environments.

- **`version.bzl`**: Defines the rules_python version string used throughout the codebase.

**Additional Configuration:**

- **`.bazelci/presubmit.yml`**: Buildkite CI configuration defining test matrices across Bazel versions, Python versions, and platforms.
- **`.bcr/`**: Bazel Central Registry templates for publishing releases to BCR.
- **`.github/workflows/`**: GitHub Actions workflows for CI, releases, and mypy type checking.
- **`.pre-commit-config.yaml`**: Pre-commit hooks for code formatting (buildifier) and linting.
- **`.readthedocs.yml`**: ReadTheDocs configuration for documentation builds.

## External Dependencies and Management

Dependencies are managed through Bzlmod's `bazel_dep()` declarations in MODULE.bazel:

**Core Dependencies:**
- **`bazel_skylib@1.8.2`**: Provides common Starlark utilities, testing infrastructure, and helper rules.
- **`bazel_features@1.21.0`**: Feature detection across Bazel versions for compatibility.
- **`rules_cc@0.1.5`**: C/C++ rules for compiling Python C extensions and linking libpython.
- **`platforms@0.0.11`**: Standard platform definitions for cross-compilation.
- **`protobuf@29.0-rc2`**: Protocol buffer support for `py_proto_library` (optional).

**Documentation Dependencies:**
- **`stardoc@0.7.2`**: Generates API documentation from Starlark docstrings and rule definitions.

**Development Dependencies** (marked with `dev_dependency = True`):
- **`rules_bazel_integration_test@0.27.0`**: Framework for testing against multiple Bazel versions.
- **`rules_testing@0.6.0`**: Advanced testing utilities and assertion libraries.
- **`rules_shell@0.3.0`**: Shell script testing support.
- **`rules_multirun@0.9.0`**: Running multiple targets in parallel.
- **`bazel_ci_rules@1.0.0`**: CI infrastructure rules.
- **`rules_pkg@1.0.1`**: Packaging and archive creation.
- **`rules_go@0.41.0`**: Required for building the Gazelle plugin (Go implementation).

**Python Toolchains:**

The repository uses `python` extension from `python/extensions/python.bzl` to register hermetic Python interpreters. These are fetched from the python-build-standalone project:

```starlark
python.toolchain(python_version = "3.11")
use_repo(python, "python_3_11", "pythons_hub")
```

Supported versions include 3.9, 3.10, 3.11, 3.12, 3.13, and 3.14 across multiple platforms and architectures.

**PyPI Dependencies:**

The `pip` extension handles third-party Python packages. For the project itself, it installs internal tools and documentation dependencies:

```starlark
pip.parse(
    hub_name = "rules_python_publish_deps",
    python_version = "3.11",
    requirements_by_platform = {
        "//tools/publish:requirements_darwin.txt": "osx_*",
        "//tools/publish:requirements_linux.txt": "linux_*",
        "//tools/publish:requirements_windows.txt": "windows_*",
    },
)
```

Requirements files specify packages like:
- `twine`: For publishing wheels to PyPI
- `sphinx`, `sphinx-rtd-theme`: For documentation generation
- `build`, `installer`, `wheel`: For wheel building infrastructure
- `pip-tools`: For requirements compilation

**UV Integration:**

The experimental `uv` extension provides the uv package manager as a registered toolchain:

```starlark
uv = use_extension("//python/uv:uv.bzl", "uv")
uv.default(version = "0.6.3", base_url = "https://github.com/astral-sh/uv/releases/download")
```

Platform-specific binaries are downloaded for Linux, macOS, and Windows across multiple architectures.

## Build Targets and Commands

**Core Build Targets:**

The repository provides several categories of build targets:

**Documentation Targets:**
```bash
# Build Sphinx documentation
bazel build //docs:docs

# Build API reference documentation
bazel build //docs:api_reference

# Build Stardoc-generated documentation
bazel build //python:py_binary_docs
```

**Testing Targets:**
```bash
# Run all tests
bazel test //...

# Run tests for a specific area
bazel test //tests/pypi/...
bazel test //tests/base_rules/...

# Run integration tests with specific Bazel version
bazel test //tests/integration/... --config=bazel7
```

**Tool Targets:**
```bash
# Build the launcher tool
bazel build //tools/launcher:launcher

# Build the precompiler
bazel build //tools/precompiler:precompiler

# Build Gazelle plugin
bazel build //gazelle:gazelle
```

**Example Targets:**
```bash
# Build example applications
bazel build //examples/bzlmod:main
bazel build //examples/wheel:example_minimal_package
```

**Utility Targets:**
```bash
# Print Python toolchain checksums
bazel run //python/private:print_toolchains_checksums

# Compile requirements files
bazel run //tools:compile_pip_requirements

# Format all Starlark files
bazel run //:format

# Run pre-commit hooks
bazel run //:pre-commit
```

## How to Build, Test, and Deploy

**Building from Source:**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/bazel-contrib/rules_python.git
   cd rules_python
   ```

2. **Install prerequisites:**
   - Bazel 7.4.1+ (specified in `.bazelversion`)
   - Python 3.9+ for development tools
   - Go 1.20+ for Gazelle plugin development

3. **Build all targets:**
   ```bash
   bazel build //...
   ```

4. **Build specific components:**
   ```bash
   bazel build //python:all
   bazel build //gazelle:all
   bazel build //tools:all
   ```

**Testing:**

1. **Run unit tests:**
   ```bash
   bazel test //tests/...
   ```

2. **Run integration tests:**
   ```bash
   # Test against multiple Bazel versions
   bazel test //tests/integration/... --config=bazel7
   bazel test //tests/integration/... --config=bazel8
   ```

3. **Run platform-specific tests:**
   ```bash
   # Test with specific Python version
   bazel test //tests/... --//python/config_settings:python_version=3.11

   # Test with different platforms
   bazel test //tests/... --platforms=@platforms//os:linux
   ```

4. **Run Gazelle tests:**
   ```bash
   bazel test //gazelle/...
   ```

5. **Run mypy type checking:**
   ```bash
   # Via GitHub Actions workflow or locally
   bazel test //sphinxdocs/tests:mypy_test
   ```

**Development Workflow:**

1. **Make code changes** in appropriate directories (e.g., `python/`, `gazelle/`)

2. **Format code:**
   ```bash
   # Format with buildifier
   bazel run //:format

   # Or use pre-commit
   pre-commit run --all-files
   ```

3. **Run relevant tests:**
   ```bash
   bazel test //tests/base_rules/...  # If modifying core rules
   bazel test //tests/pypi/...        # If modifying pip integration
   ```

4. **Update documentation:**
   ```bash
   # Rebuild docs
   bazel build //docs:docs

   # View generated docs
   python -m http.server --directory bazel-bin/docs/docs 8000
   ```

5. **Run full CI locally:**
   ```bash
   # Test across Bazel versions
   bazel test --config=bazel7 //...
   bazel test --config=bazel8 //...
   ```

**Creating a Release:**

1. **Update version information:**
   - Edit `version.bzl` to set new version
   - Update `CHANGELOG.md` with release notes
   - Update compatibility notes in documentation

2. **Create release archive:**
   ```bash
   # Generate archive and release notes
   .github/workflows/create_archive_and_notes.sh VERSION
   ```

3. **Test release candidate:**
   ```bash
   # Build and test release artifacts
   bazel build //...
   bazel test //...
   ```

4. **Publish to GitHub:**
   - Create GitHub release with generated artifacts
   - Tag release with version number
   - Upload release archive and release notes

5. **Publish to Bazel Central Registry:**
   - Submit PR to BCR with updated metadata
   - Use templates from `.bcr/` directory
   - Wait for BCR maintainer approval

**Using in Other Projects:**

**Bzlmod (recommended):**
```starlark
# In MODULE.bazel
bazel_dep(name = "rules_python", version = "0.36.0")

python = use_extension("@rules_python//python/extensions:python.bzl", "python")
python.toolchain(python_version = "3.11")
use_repo(python, "python_3_11")

pip = use_extension("@rules_python//python/extensions:pip.bzl", "pip")
pip.parse(
    hub_name = "pypi",
    python_version = "3.11",
    requirements_lock = "//:requirements.txt",
)
use_repo(pip, "pypi")
```

**WORKSPACE (legacy):**
```starlark
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "rules_python",
    sha256 = "...",
    strip_prefix = "rules_python-0.36.0",
    url = "https://github.com/bazel-contrib/rules_python/releases/download/0.36.0/rules_python-0.36.0.tar.gz",
)

load("@rules_python//python:repositories.bzl", "py_repositories", "python_register_toolchains")
py_repositories()

python_register_toolchains(
    name = "python_3_11",
    python_version = "3.11",
)

load("@rules_python//python:pip.bzl", "pip_parse")
pip_parse(
    name = "pypi",
    python_interpreter_target = "@python_3_11_host//:python",
    requirements_lock = "//:requirements.txt",
)
```

**Continuous Integration:**

The project uses Buildkite CI configured in `.bazelci/presubmit.yml`:
- Tests across Bazel 7.4.1, 8.0.0, and 9.0.0rc1
- Tests across Python 3.9, 3.10, 3.11, 3.12, 3.13, 3.14
- Tests on Linux (x86_64, aarch64), macOS (x86_64, arm64), and Windows
- Integration tests for Bzlmod and WORKSPACE
- Documentation build validation
- Release artifact generation

GitHub Actions supplement with:
- Mypy type checking on Python code
- Pre-commit hook validation
- Automated release publishing
- Documentation deployment to ReadTheDocs
