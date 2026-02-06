# rules_py Build System

## Build System Type

rules_py is built using **Bazel with Bzlmod** (Bazel's modern dependency management system). The project requires **Bazel 6.4.0+** as specified in `.bazelversion`. The repository demonstrates modern Bazel practices including:

- Bzlmod module system via `MODULE.bazel` (not legacy WORKSPACE)
- Hermetic toolchain management
- Multi-platform Rust binary compilation
- Module extensions for custom configuration

## Configuration Files

### MODULE.bazel

The primary build configuration file defining:

```starlark
module(
    name = "aspect_rules_py",
    compatibility_level = 1,
)
```

**Key dependencies**:
- `rules_python` (v1.0.0): Base Python toolchains and providers
- `bazel_lib` (v3.0.0): File operations and utilities
- `bazel_skylib` (v1.4.2): Standard Bazel macros
- `with_cfg.bzl` (v0.14.1): Configuration support
- `rules_rust` (v0.68.1): For building native Rust tools
- `rules_cc` (v0.2.16): C++ toolchain support
- `tar.bzl` (v0.5.5): Archive handling

**Toolchain configuration**:
```starlark
# Python toolchains from rules_python
bazel_dep(name = "rules_python", version = "1.0.0")

# Rust toolchains for native tools
bazel_dep(name = "rules_rust", version = "0.68.1")
rust.toolchain(
    edition = "2024",
    versions = ["1.88.0"],
    extra_target_triples = [
        "aarch64-apple-darwin",
        "x86_64-apple-darwin",
        "aarch64-unknown-linux-musl",
        "x86_64-unknown-linux-musl",
    ],
)

# LLVM toolchains for cross-compilation
bazel_dep(name = "toolchains_llvm_bootstrapped", version = "0.2.5")
```

**Module extensions**:
- `py_tools`: Registers rules_py native tools and PEX support
- `uv`: Configures the experimental uv dependency system
- `tomltool`: Provides TOML parsing binary for multiple platforms
- `host`: Detects host platform for default constraint values

### .bazelrc

Defines default build flags and CI configuration:

**Import hierarchy**:
```
.bazelrc (root)
├── bazel/defaults.bazelrc (workspace defaults)
└── .github/workflows/ci.bazelrc (CI-specific flags)
```

**Key settings**:
- `common --enable_bzlmod`: Enable modern module system
- `common --noenable_workspace`: Disable legacy WORKSPACE
- Platform-specific configurations for macOS, Linux, Windows
- Test output and caching behavior
- Telemetry configuration (aspect_tools_telemetry)

### Cargo.toml

Rust workspace configuration for native tools:

```toml
[workspace]
resolver = "2"
members = [
    "py/tools/py",
    "py/tools/venv_bin",
    "py/tools/unpack_bin",
    "py/tools/venv_shim",
    "py/tools/runfiles",
]
```

**Key dependencies from uv**:
- `uv-virtualenv`: Virtual environment creation
- `uv-install-wheel`: Wheel installation logic
- `uv-extract`: Archive extraction
- `uv-python`: Python interpreter detection
- `uv-pypi-types`: PyPI metadata types

All uv dependencies are pinned to a specific git revision for reproducibility.

## External Dependencies

### Bazel Dependencies (Bzlmod)

**Production dependencies**:
- `rules_python` (1.0.0): Python interpreter toolchains, PyInfo provider
- `bazel_lib` (3.0.0): copy_to_directory, expand_template, transitions
- `bazel_skylib` (1.4.2): Common Starlark utilities
- `with_cfg.bzl` (0.14.1): Configuration flags and settings
- `rules_cc` (0.2.16): C/C++ compilation for native extensions
- `tar.bzl` (0.5.5): Archive extraction for wheels and sdists
- `aspect_tools_telemetry` (0.3.3): Usage telemetry reporting

**Development dependencies** (dev_dependency = True):
- `rules_rust` (0.68.1): Rust toolchain for native tools
- `toolchains_llvm_bootstrapped` (0.2.5): LLVM/Clang for cross-compilation
- `gazelle` (0.45.0): BUILD file generation
- `rules_pkg` (1.1.0): Release packaging
- `rules_rs` (0.0.26): Cargo integration
- `rules_multitool` (1.9.0): Multi-version tool management
- Compression libraries: `bzip2`, `xz`, `zstd` for archive support

### Rust Dependencies (Cargo)

**Core uv libraries** (from astral-sh/uv):
- `uv-virtualenv`: Create Python virtual environments
- `uv-install-wheel`: Install wheel files into venvs
- `uv-extract`: Extract tar.gz, zip archives
- `uv-python`: Detect and manage Python installations
- `uv-pypi-types`: PyPI metadata parsing
- `uv-distribution-filename`: Parse wheel filenames

**Utility crates**:
- `clap` (4.5.20): CLI argument parsing
- `itertools` (0.13.0): Iterator utilities
- `miette` (7.2): Error reporting
- `thiserror` (1.0.64): Error derive macros
- `tempfile` (3.13.0): Temporary file handling

**Patches**:
- `reqwest-middleware`, `reqwest-retry`: Custom patches from astral-sh for HTTP handling

### Python Dependencies (Development)

Located in `requirements.txt` and `uv.lock`:
- Build tools: `setuptools`, `build`
- Testing: `pytest`, `coverage`
- Type checking: `mypy`
- Documentation generation dependencies

## Build Targets and Commands

### Building the Project

```bash
# Build all production code
bazel build //...

# Build native Rust tools
bazel build //py/tools/venv_bin
bazel build //py/tools/unpack_bin

# Build with specific platform
bazel build --platforms=@bazel_tools//platforms:linux_x86_64 //py/tools/...
```

### Running Tests

```bash
# Run all tests
bazel test //...

# Run specific test suite
bazel test //py/tests/...
bazel test //uv/private/...

# Run end-to-end tests
bazel test //e2e/...

# Run with coverage
bazel coverage //py/tests/...
```

### Code Generation

```bash
# Update BUILD files with Gazelle
bazel run //:gazelle

# Update MODULE.bazel.lock
bazel mod deps

# Format Starlark files
bazel run //:buildifier
```

### Development Workflow

```bash
# Run pre-commit hooks
pre-commit install
pre-commit run --all-files

# Build and test everything locally
bazel test //... --test_output=errors

# Update Rust dependencies
cd py/tools/venv_bin && cargo update
bazel run @rules_rs//tools/lock:cargo
```

## Build Outputs

### Native Tool Binaries

Multi-platform Rust binaries are built and released:

**Target platforms**:
- `x86_64-apple-darwin` (macOS Intel)
- `aarch64-apple-darwin` (macOS Apple Silicon)
- `x86_64-unknown-linux-musl` (Linux x86_64)
- `aarch64-unknown-linux-musl` (Linux ARM64)

**Outputs** (in `bazel-bin/py/tools/`):
- `venv_bin/venv_bin` - Virtualenv creation
- `unpack_bin/unpack_bin` - Wheel extraction
- `venv_shim/venv_shim` - Venv activation helper

These are packaged in releases and made available via the `py_tools` extension.

### Starlark Rules

The main build artifact is the collection of `.bzl` files providing:
- `@aspect_rules_py//py:defs.bzl` - Public rule definitions
- `@aspect_rules_py//uv/unstable:extension.bzl` - uv extension
- Toolchain implementations in `//py/private/toolchain/`

### Documentation

Generated API documentation published to:
- Bazel Central Registry: https://registry.bazel.build/docs/aspect_rules_py
- GitHub Pages: https://docs.aspect.build/rulesets/rules_py/

## Testing Strategy

### Unit Tests

Located in `//py/tests/`:
- Import path resolution tests
- Virtual dependency tests
- External dependency integration
- PEX binary generation tests

### Integration Tests

End-to-end tests in `//e2e/cases/`:
- Cross-repository dependency tests
- Interpreter version selection
- OCI image layer generation
- Platform transition tests

### Example-based Testing

Each example in `//examples/` is built and tested in CI:
- `py_binary`: Basic binary execution
- `pytest`: Test framework integration
- `django`: Web framework integration
- `multi_version`: Multiple Python version support

## Deployment and Release

### Release Process

1. **Version bump**: Update version in MODULE.bazel and release files
2. **Build artifacts**: GitHub Actions builds multi-platform binaries
3. **Create release**: Tag pushed to GitHub triggers release workflow
4. **Publish to BCR**: Automated submission to Bazel Central Registry
5. **Generate integrity hashes**: Computed via `bazelisk mod hash`

### Release Artifacts

Each release includes:
- Source archive with integrity hash
- Pre-built native tool binaries for all platforms
- BCR metadata files
- Changelog and migration notes

### CI/CD Pipeline

**GitHub Actions workflows**:
- `ci.yaml`: Runs tests on Linux, macOS, Windows
- `publish.yaml`: Publishes release artifacts
- `release.yml`: Creates GitHub release and BCR submission
- `new_issue.yaml`: Issue triage automation

**Build matrix**:
- Bazel versions: Latest stable + rolling
- Operating systems: Ubuntu, macOS (Intel + ARM), Windows
- Python versions: 3.9, 3.10, 3.11, 3.12

## Common Build Patterns

### Override for Development

```bash
# Use local rules_py in other projects
echo 'common --override_repository=aspect_rules_py=/path/to/rules_py' >> ~/.bazelrc
```

### Cross-compilation Example

```python
# Build for Linux from macOS
bazel build \
    --platforms=//bazel/platforms:linux_x86_64 \
    --extra_toolchains=@toolchains_llvm_bootstrapped//toolchain:all \
    //py/tools/venv_bin
```

### Rust Tool Development

```bash
# Edit Rust source
vim py/tools/venv_bin/src/main.rs

# Rebuild with Bazel
bazel build //py/tools/venv_bin

# Or use cargo for faster iteration
cd py/tools/venv_bin
cargo build --release
```

### Testing Against Multiple Python Versions

```python
# Configure in MODULE.bazel
python.toolchain(python_version = "3.9", is_default = True)
python.toolchain(python_version = "3.12", is_default = False)

# Use in BUILD.bazel
py_test(
    name = "test_3_9",
    python_version = "3.9",
    ...
)

py_test(
    name = "test_3_12",
    python_version = "3.12",
    ...
)
```
