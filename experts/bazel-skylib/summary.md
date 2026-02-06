# Bazel Skylib - Repository Summary

## Overview

Bazel-skylib is the official standard library for the Bazel build system, maintained by the Bazel team at Google. It provides a comprehensive collection of Starlark functions and build rules that address common patterns in build rule development, serving as a centralized, tested, and well-documented implementation of utilities that would otherwise be duplicated across projects.

**Repository**: https://github.com/bazelbuild/bazel-skylib
**Version**: 1.8.2
**License**: Apache 2.0
**Location**: /Users/santos/projects/bazel/bazel-skylib

## Purpose and Goals

Skylib exists to solve problems that occur frequently across different Bazel projects. Rather than forcing individual projects to implement utilities locally, skylib provides production-ready implementations following Bazel best practices. The library maintains a high bar for inclusion:

1. **Wide Necessity**: Code must demonstrate need across multiple projects, not just local convenience
2. **Interface Simplicity**: Functions provide simple interfaces to complex implementations
3. **Interface Generality**: Functions must serve reasonable use cases without excessive parameter complexity
4. **Algorithmic Efficiency**: Optimal algorithms appropriate for Starlark's interpreted nature
5. **Platform Independence**: Rules work across Linux, macOS, and Windows without shell dependencies

## Key Features and Capabilities

### Library Modules (lib/)
- **Data Structures**: Collections manipulation, dictionary operations, set implementations
- **Path Utilities**: POSIX-style path manipulation (basename, dirname, join, normalize)
- **Shell Utilities**: Safe shell quoting and command generation
- **Type System**: Type checking utilities for Starlark's dynamic typing
- **Testing Framework**: Comprehensive unit, analysis, and loading phase testing
- **Version Management**: Bazel version detection and comparison
- **Configuration**: Select utilities and config setting groups
- **Functional Programming**: Partial application support

### Build Rules (rules/)
- **File Operations**: copy_file, copy_directory, write_file, expand_template
- **Execution**: run_binary, native_binary
- **Testing**: diff_test, build_test, analysis_test
- **Configuration**: Common build settings (int_flag, string_flag, bool_flag)
- **Directory Handling**: Modern directory metadata rules (new in 1.7.0)

### Tooling
- **Gazelle Plugin**: Automatic bzl_library generation for Starlark files
- **Documentation**: Stardoc integration for API documentation

## Target Audience

1. **Rule Developers**: Building custom Bazel rules needing utility functions
2. **Build System Teams**: Creating complex build systems requiring standardized utilities
3. **Project Maintainers**: Leveraging proven implementations over ad-hoc solutions
4. **CI/CD Engineers**: Using build_test and diff_test for validation pipelines

## Architecture Overview

Skylib is organized into two primary areas:

- **lib/**: Starlark utility modules exported as structs containing related functions
- **rules/**: Practical build rules solving real-world problems

Each module is independently loadable, enforcing explicit dependencies:
```starlark
load("@bazel_skylib//lib:paths.bzl", "paths")
load("@bazel_skylib//rules:copy_file.bzl", "copy_file")
```

The deprecated `lib.bzl` bulk import is no longer supported - direct module imports are required.

## Related Projects and Dependencies

**Core Dependencies** (production):
- `platforms` (0.0.10) - Platform definitions
- `rules_license` (1.0.0) - License declarations

**Development Dependencies**:
- `stardoc` - Documentation generation
- `rules_pkg` - Release packaging
- `rules_testing` - Test utilities
- `rules_cc` - C++ toolchain
- `rules_shell` - Shell rule support

## Version Compatibility

- **Minimum Bazel**: 4.0 (with caveats)
- **Recommended Bazel**: 6.0+ (full bzlmod support)
- **bzlmod**: First-class citizen with MODULE.bazel
- **WORKSPACE**: Legacy support via workspace.bzl

## Usage Example

```starlark
# MODULE.bazel
bazel_dep(name = "bazel_skylib", version = "1.8.2")

# BUILD.bazel
load("@bazel_skylib//lib:paths.bzl", "paths")
load("@bazel_skylib//rules:copy_file.bzl", "copy_file")

copy_file(
    name = "copy_config",
    src = "config.template",
    out = "config.actual",
)
```

## Key Design Decisions

1. **Module-based Loading**: Each .bzl file exports a struct, preventing namespace pollution
2. **Platform-aware Rules**: Automatic Bash/cmd.exe selection for cross-platform support
3. **Toolchain System**: unittest.bzl uses toolchains for platform-specific test execution
4. **Deprecation Strategy**: Old APIs deprecated but maintained for compatibility (old_sets.bzl)
5. **Testing Philosophy**: Three-tier testing (unit, analysis, loading) for comprehensive coverage
