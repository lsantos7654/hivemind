# Bazel Skylib - Build System

## Build System Type
Bazel (with both bzlmod and legacy WORKSPACE support)

## Repository Location
`/Users/santos/projects/bazel/bazel-skylib`

## Module Configuration (MODULE.bazel)

```starlark
module(
    name = "bazel_skylib",
    version = "1.8.2",
    compatibility_level = 1,
)

# Toolchain registration for unittest framework
register_toolchains(
    "//toolchains/unittest:cmd_toolchain",   # Windows
    "//toolchains/unittest:bash_toolchain",  # Unix
)

# Production dependencies
bazel_dep(name = "platforms", version = "0.0.10")
bazel_dep(name = "rules_license", version = "1.0.0")

# Development-only dependencies
bazel_dep(name = "stardoc", version = "0.8.0", dev_dependency = True)
bazel_dep(name = "rules_pkg", version = "1.0.1", dev_dependency = True)
bazel_dep(name = "rules_testing", version = "0.6.0", dev_dependency = True)
bazel_dep(name = "rules_cc", version = "0.0.17", dev_dependency = True)
bazel_dep(name = "rules_shell", version = "0.3.0", dev_dependency = True)
```

## Depending on Skylib

### Using bzlmod (Bazel 6.0+ recommended)

In your `MODULE.bazel`:
```starlark
bazel_dep(name = "bazel_skylib", version = "1.8.2")
```

Then load modules directly:
```starlark
load("@bazel_skylib//lib:paths.bzl", "paths")
load("@bazel_skylib//rules:copy_file.bzl", "copy_file")
```

### Using WORKSPACE (Legacy)

In your `WORKSPACE`:
```python
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "bazel_skylib",
    sha256 = "...",  # Get from release page
    urls = [
        "https://mirror.bazel.build/github.com/bazelbuild/bazel-skylib/releases/download/1.8.2/bazel-skylib-1.8.2.tar.gz",
        "https://github.com/bazelbuild/bazel-skylib/releases/download/1.8.2/bazel-skylib-1.8.2.tar.gz",
    ],
)

# REQUIRED for unittest.bzl - registers toolchains
load("@bazel_skylib//:workspace.bzl", "bazel_skylib_workspace")
bazel_skylib_workspace()
```

## WORKSPACE Setup (workspace.bzl)

The `workspace.bzl` file provides essential setup:

```starlark
def bazel_skylib_workspace():
    """Registers toolchains required for unittest.bzl."""
    native.register_toolchains(
        "@bazel_skylib//toolchains/unittest:cmd_toolchain",
        "@bazel_skylib//toolchains/unittest:bash_toolchain",
    )
```

**Critical**: This call is REQUIRED if you use `unittest.bzl`. Without it, tests will fail with toolchain resolution errors.

## External Dependencies

### Production Dependencies
| Dependency | Version | Purpose |
|------------|---------|---------|
| platforms | 0.0.10 | Platform constraint definitions |
| rules_license | 1.0.0 | License metadata for compliance |

### Development Dependencies (not needed by users)
| Dependency | Version | Purpose |
|------------|---------|---------|
| stardoc | 0.8.0 | Documentation generation |
| rules_pkg | 1.0.1 | Release tarball creation |
| rules_testing | 0.6.0 | Extended test utilities |
| rules_cc | 0.0.17 | C++ toolchain for tests |
| rules_shell | 0.3.0 | Shell rule support |

## Build Targets and Commands

### Running Tests
```bash
# Run all tests
bazel test //...

# Run specific module tests
bazel test //tests:paths_test
bazel test //tests:shell_test
bazel test //tests:collections_test

# Run rule tests
bazel test //tests:copy_file_test
bazel test //tests:diff_test_test

# Run with specific Bazel version (using .bazelversion)
bazel test //...
```

### Building Documentation
```bash
# Generate all stardoc documentation
bazel build //docs:all
```

### Creating Distribution
```bash
# Build release tarball
bazel build //distribution:bazel-skylib-$(cat version.bzl | grep VERSION | cut -d'"' -f2).tar.gz
```

## Key BUILD Files

### Root BUILD File
Primary targets:
- `bzl_library` targets for each module
- `filegroup` for distribution packaging
- `filegroup` for test dependencies
- License declarations

```starlark
# Example structure
bzl_library(
    name = "lib",
    srcs = [":lib.bzl"],
    visibility = ["//visibility:public"],
)

filegroup(
    name = "test_deps",
    srcs = [
        "BUILD",
        "WORKSPACE",
        ":bzl_library",
        "//lib:test_deps",
        "//rules:test_deps",
    ],
)
```

### lib/BUILD File
```starlark
bzl_library(
    name = "paths",
    srcs = ["paths.bzl"],
    visibility = ["//visibility:public"],
)

bzl_library(
    name = "shell",
    srcs = ["shell.bzl"],
    visibility = ["//visibility:public"],
)

# ... one target per module
```

### rules/BUILD File
```starlark
bzl_library(
    name = "copy_file",
    srcs = ["copy_file.bzl"],
    deps = ["//rules/private:copy_file_private"],
    visibility = ["//visibility:public"],
)

# ... one target per rule
```

## Toolchain System

### Purpose
The unittest framework requires platform-specific test execution (Bash on Unix, cmd.exe on Windows).

### Toolchain Registration
Two toolchains are registered:
1. `//toolchains/unittest:bash_toolchain` - Unix systems
2. `//toolchains/unittest:cmd_toolchain` - Windows systems

### Toolchain Implementation
```
toolchains/unittest/
├── BUILD           # Toolchain registration
├── defs.bzl        # unittest_toolchain rule definition
├── bash.sh.tpl     # Unix test script template
└── cmd.bat.tpl     # Windows batch script template
```

### Usage in Tests
Tests created with `unittest.make()` automatically:
1. Resolve the appropriate toolchain
2. Generate platform-specific test scripts
3. Execute using the platform's shell

## Loading Modules

### Correct Pattern (Individual Loading)
```starlark
# Load specific modules
load("@bazel_skylib//lib:paths.bzl", "paths")
load("@bazel_skylib//lib:shell.bzl", "shell")
load("@bazel_skylib//lib:dicts.bzl", "dicts")

# Load specific rules
load("@bazel_skylib//rules:copy_file.bzl", "copy_file")
load("@bazel_skylib//rules:write_file.bzl", "write_file")
```

### Deprecated Pattern (Bulk Loading)
```starlark
# This DOES NOT WORK anymore
load("@bazel_skylib//:lib.bzl", "paths", "shell")  # ERROR!
```

The `lib.bzl` file exists but is deprecated and will fail if used.

## Version Management

### Version File (version.bzl)
```starlark
version = "1.8.2"
```

### Checking Version Programmatically
```starlark
load("@bazel_skylib//:version.bzl", "version")

if version != "1.8.2":
    fail("Expected skylib 1.8.2")
```

## Dependency Graph Overview

```
User Project
    │
    └── bazel_skylib (1.8.2)
            │
            ├── platforms (0.0.10)
            │
            └── rules_license (1.0.0)
```

No transitive dependencies beyond these two lightweight packages.

## Building and Testing

### Full Test Suite
```bash
bazel test //...
```

### Specific Test Categories
```bash
# Library module tests
bazel test //tests:collections_test //tests:dicts_test //tests:paths_test

# Rule tests
bazel test //tests:copy_file_test //tests:diff_test_test

# Directory rule tests
bazel test //tests/directory/...
```

### CI Configuration
CI runs via Buildkite (`.bazelci/presubmit.yml`) testing:
- Multiple Bazel versions
- Linux, macOS, Windows platforms
- Both bzlmod and WORKSPACE modes

## Bazel Version Requirements

### Minimum Version
- Bazel 4.0+ (basic functionality)
- Bazel 5.0+ (subpackages.bzl)
- Bazel 6.0+ (full bzlmod support, modules.bzl)

### Version File
`.bazelversion` specifies the development Bazel version.

### Checking Compatibility
```starlark
load("@bazel_skylib//lib:versions.bzl", "versions")

versions.check(minimum = "5.0.0")  # Fails if Bazel < 5.0.0
```

## Release Process

1. Update `version.bzl` with new version
2. Update `CHANGELOG.md` with changes
3. Update `MODULE.bazel` version field
4. Create git tag
5. Build distribution tarball
6. Upload to GitHub releases
7. Submit to Bazel Central Registry

See `docs/maintainers_guide.md` for detailed release procedures.

## Gazelle Plugin Setup

For automatic `bzl_library` generation:

### WORKSPACE
```python
load("@bazel_skylib_gazelle_plugin//:workspace.bzl", "bazel_skylib_gazelle_plugin_workspace")
bazel_skylib_gazelle_plugin_workspace()

load("@bazel_skylib_gazelle_plugin//:setup.bzl", "bazel_skylib_gazelle_plugin_setup")
bazel_skylib_gazelle_plugin_setup()
```

### BUILD
```starlark
load("@bazel_gazelle//:def.bzl", "DEFAULT_LANGUAGES", "gazelle", "gazelle_binary")

gazelle_binary(
    name = "gazelle_bin",
    languages = DEFAULT_LANGUAGES + ["@bazel_skylib_gazelle_plugin//bzl"],
)

gazelle(name = "gazelle", gazelle = ":gazelle_bin")
```

### Running Gazelle
```bash
bazel run //:gazelle
```
