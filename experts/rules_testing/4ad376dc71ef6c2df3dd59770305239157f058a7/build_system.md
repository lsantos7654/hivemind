# Build System and Configuration

## Build System Type

rules_testing uses **Bazel** as its build system and is specifically designed to test Bazel itself. The project supports both modern bzlmod (MODULE.bazel) and legacy WORKSPACE configurations, with bzlmod being the recommended approach.

## Configuration Files

### MODULE.bazel - Modern Bzlmod Configuration

The primary configuration for bzlmod users:

```starlark
module(
    name = "rules_testing",
    version = "0.0.1",
    compatibility_level = 1,
)

bazel_dep(name = "platforms", version = "0.0.6")
bazel_dep(name = "bazel_skylib", version = "1.3.0")
bazel_dep(name = "rules_license", version = "0.0.4")
```

**Runtime Dependencies**:
- `platforms`: Platform constraint definitions
- `bazel_skylib`: Starlark utilities library
- `rules_license`: License compliance rules

**Development Dependencies** (not needed by users):
- `stardoc`: Documentation generation from Starlark
- `rules_python`: For Python-based doc tooling
- `rules_shell`: Shell script support

The module also configures Python toolchains for documentation:
- Python 3.11 toolchain
- pip extension with `docs-pypi` hub for Sphinx dependencies

### WORKSPACE.bazel - Legacy Configuration

For users not yet on bzlmod, WORKSPACE.bazel provides http_archive declarations for all dependencies:

```starlark
workspace(name = "rules_testing")

http_archive(
    name = "bazel_skylib",
    sha256 = "bc283cdfcd526a52c3201279cda4bc298652efa898b10b4db0837dc51652756f",
    urls = ["https://github.com/bazelbuild/bazel-skylib/releases/download/1.7.1/bazel-skylib-1.7.1.tar.gz"],
)

http_archive(
    name = "io_bazel_stardoc",
    sha256 = "fabb280f6c92a3b55eed89a918ca91e39fb733373c81e87a18ae9e33e75023ec",
    urls = ["https://github.com/bazelbuild/stardoc/releases/download/0.7.1/stardoc-0.7.1.tar.gz"],
)

# Additional dependencies...
```

The WORKSPACE setup includes initialization for:
- rules_java (for Stardoc)
- com_google_protobuf (for protocol buffers)
- rules_python (for documentation)
- rules_license (for license compliance)

### .bazelrc - Bazel Configuration

Project-wide Bazel settings controlling build behavior, test execution, and CI configuration. Common settings likely include:
- Test output configuration
- Coverage settings
- Platform configurations
- CI-specific flags

### .bazelignore

Specifies directories that Bazel should ignore when traversing the workspace. Typically includes generated directories and external tool outputs.

## External Dependencies

### Direct Runtime Dependencies

1. **bazel_skylib** (v1.3.0+)
   - Purpose: Foundational Starlark utilities
   - Used for: Path manipulation, type checking, dict operations, collections
   - Critical functions: `paths.join()`, `types.is_list()`, `dicts.add()`

2. **platforms** (v0.0.6+)
   - Purpose: Standard platform constraint definitions
   - Used for: Cross-platform testing, configuration transitions
   - Provides: `@platforms//os:*`, `@platforms//cpu:*`, etc.

3. **rules_license** (v0.0.4+)
   - Purpose: License compliance
   - Used for: Ensuring proper licensing in generated outputs

### Development-Only Dependencies

1. **stardoc** (v0.7.1+)
   - Purpose: Generate documentation from Starlark code
   - Used by: `docgen/` for API reference generation
   - Output: Markdown API documentation

2. **rules_python** (v1.8.0+)
   - Purpose: Python toolchain and pip integration
   - Used for: Running Sphinx documentation builds
   - Provides: Python 3.11 interpreter

3. **rules_shell** (v0.4.0+)
   - Purpose: Shell script rules
   - Used for: Build and test scripts

4. **Python packages** (via pip, docs/requirements.txt):
   - `sphinx`: Documentation generation
   - `sphinx-rtd-theme`: ReadTheDocs theme
   - `myst-parser`: Markdown parsing for Sphinx
   - Additional Sphinx extensions

### Transitive Dependencies

- **rules_java**: Required by Stardoc
- **com_google_protobuf**: Required by Stardoc
- **rules_cc**: May be pulled in for C++ toolchains

## Build Targets and Commands

### Building the Library

The library is pure Starlark, so there's no traditional "build" step. However, you can verify the library loads correctly:

```bash
# Verify all targets are buildable
bazel build //...

# Build specific library targets
bazel build //lib:all
```

### Running Tests

```bash
# Run all tests
bazel test //...

# Run tests in a specific package
bazel test //tests:all
bazel test //tests/matching:all

# Run a specific test
bazel test //tests:truth_tests_suite
```

### Documentation Generation

```bash
# Build API documentation
bazel build //docs:all

# Generate docs with Sphinx (requires Python)
bazel build //docs:sphinx_build

# View generated documentation
# Output typically in bazel-bin/docs/
```

### Code Quality Checks

```bash
# Add license headers to all files
./addlicense.sh

# Format Starlark code (if buildifier is installed)
bazel run //:buildifier
```

### End-to-End Tests

```bash
# Run bzlmod integration tests
bazel test //e2e/bzlmod:all
```

## Development Workflow

### Setting Up a Development Environment

1. **Clone the repository**:
```bash
git clone https://github.com/bazelbuild/rules_testing.git
cd rules_testing
```

2. **Verify setup**:
```bash
bazel test //...
```

3. **Generate documentation locally**:
```bash
bazel build //docs:sphinx_build
```

### Making Changes

1. **Edit `.bzl` files** in `lib/` or `lib/private/`
2. **Add/update tests** in `tests/`
3. **Update documentation** in `docs/source/` if adding new features
4. **Run tests** to verify changes:
```bash
bazel test //tests:all
```

### Testing Changes Against Another Project

To test rules_testing changes in another project:

1. **Using local_path_override** (bzlmod):
```python
# In the consuming project's MODULE.bazel
local_path_override(
    module_name = "rules_testing",
    path = "/path/to/local/rules_testing",
)
```

2. **Using local_repository** (WORKSPACE):
```python
# In the consuming project's WORKSPACE
local_repository(
    name = "rules_testing",
    path = "/path/to/local/rules_testing",
)
```

### Release Process

Based on RELEASING.md, the release process likely involves:

1. Update CHANGELOG.md with version and date
2. Update version in MODULE.bazel
3. Create a git tag
4. Push to GitHub
5. GitHub Actions automatically creates release artifacts
6. Submit to Bazel Central Registry

## Continuous Integration

### .bazelci/ Configuration

Contains Buildkite CI configuration for running tests across:
- Multiple Bazel versions
- Multiple platforms (Linux, macOS, Windows)
- Different configurations (bzlmod vs WORKSPACE)

### .github/ Workflows

GitHub Actions workflows for:
- Running tests on pull requests
- Building and publishing documentation
- Creating release artifacts
- Running linters and formatters

### CI Test Matrix

Tests are run across:
- **Bazel versions**: Latest stable, rolling releases, LTS versions
- **Platforms**: Ubuntu, macOS, Windows
- **Configurations**: bzlmod enabled/disabled
- **Python versions**: For documentation builds

## Build Performance

### Caching

Bazel's caching is leveraged for:
- Analysis results
- Test execution (tests are cached if inputs haven't changed)
- Documentation generation

### Incremental Builds

Being pure Starlark, the library benefits from Bazel's analysis caching. Changes to one file only re-analyze affected targets.

### Remote Execution

The project is compatible with Bazel remote execution for:
- Distributed test execution
- Shared build caches
- Faster CI builds

## Distribution and Consumption

### As a Bazel Module (Recommended)

Users add to MODULE.bazel:
```python
bazel_dep(name = "rules_testing", version = "0.8.0", dev_dependency = True)
```

### As a WORKSPACE Dependency

Users add to WORKSPACE:
```python
http_archive(
    name = "rules_testing",
    sha256 = "...",
    urls = ["https://github.com/bazelbuild/rules_testing/releases/download/v0.8.0/rules_testing-v0.8.0.tar.gz"],
)

load("@rules_testing//lib:unittest.bzl", "unittest")
# Additional setup...
```

### Via Bazel Central Registry

The project is published to BCR (Bazel Central Registry), allowing automatic version resolution and transitive dependency management in bzlmod.

## Special Build Features

### Analysis Test Infrastructure

The build system includes special support for analysis tests:
- Custom test rule implementation
- Aspect-based target introspection
- Configuration transition support

### Documentation Pipeline

Multi-stage documentation build:
1. Stardoc extracts docstrings from `.bzl` files
2. Templates in `docgen/` format the output
3. Sphinx combines with hand-written guides
4. Published to ReadTheDocs

### Self-Testing

The project tests itself using its own testing framework, demonstrating:
- Real-world usage patterns
- Framework capabilities
- Dogfooding to ensure quality
