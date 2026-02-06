# rules_python Repository Summary

## Repository Purpose and Goals

`rules_python` is the official Python support ruleset for the Bazel build system, providing comprehensive tooling for building, testing, and packaging Python projects within Bazel. This repository is maintained by the Bazel community and serves as the canonical implementation of Python rules for Bazel, offering both core build rules and advanced features for modern Python development workflows.

The primary mission is to enable hermetic, reproducible Python builds with proper dependency management, cross-platform support, and seamless integration with Python's ecosystem including PyPI, pip, and modern tooling like uv. The rules support both legacy WORKSPACE configurations and the modern Bzlmod (MODULE.bazel) approach, with Bzlmod being the recommended and more feature-rich option.

## Key Features and Capabilities

**Core Python Rules**: The repository provides the fundamental build rules `py_library`, `py_binary`, `py_test`, and `py_runtime` that form the foundation of Python support in Bazel. These rules handle Python source compilation, dependency resolution, and execution with proper isolation and hermetic behavior.

**PyPI Integration**: Comprehensive support for third-party dependencies through `pip.parse()` (Bzlmod) and `pip_parse()` (WORKSPACE) extensions. This includes requirements.txt parsing, dependency resolution, wheel installation, and multi-platform support. The system generates BUILD files for each package, handles transitive dependencies, and supports custom package annotations.

**Hermetic Python Toolchains**: Pre-built, standalone Python interpreters from the python-build-standalone project are automatically downloaded and configured, ensuring consistent Python versions across all platforms without relying on system Python. Versions 3.9 through 3.14 are supported, including experimental freethreaded builds.

**Advanced Packaging**: Full support for building Python wheels via `py_wheel` and `py_package` rules, enabling creation of distributable packages. Integration with twine allows direct publishing to PyPI from Bazel targets with proper version stamping and metadata generation.

**Gazelle Plugin**: Automatic BUILD file generation from Python code using the Gazelle plugin, which analyzes import statements and generates appropriate build targets and dependencies. This dramatically reduces manual BUILD file maintenance.

**UV Integration**: Experimental support for the modern uv package manager as an alternative to pip, offering faster package resolution and installation with better dependency handling.

**Precompiler Support**: Ability to precompile Python bytecode (.pyc files) to improve startup performance and protect source code. The precompiler tooling integrates with the build graph to ensure proper compilation across the entire dependency tree.

## Primary Use Cases and Target Audience

The target audience includes engineering teams building Python applications at scale, particularly those requiring:

- **Monorepo Management**: Large codebases with mixed-language projects where Python components need to integrate with Java, Go, C++, or other languages within a single build system
- **Reproducible Builds**: Organizations requiring hermetic builds with precise dependency control and version pinning across development, CI, and production environments
- **Cross-Platform Development**: Teams targeting multiple operating systems (Linux, macOS, Windows) and architectures (x86_64, aarch64, ppc64le, s390x, riscv64) with consistent toolchains
- **Enterprise Python**: Companies needing strong dependency isolation, security scanning, and audit trails for Python packages
- **Python Library Maintainers**: Developers building and distributing Python packages who want reproducible wheel builds and automated publishing workflows

## High-Level Architecture Overview

The architecture is structured around several key subsystems:

**Core Rules Layer** (`python/`): Contains the fundamental rule implementations including py_library_rule.bzl, py_binary_rule.bzl, and py_test_rule.bzl. These implement the actual Bazel rules with providers like PyInfo and PyRuntimeInfo for propagating information through the build graph.

**Extension Layer** (`python/extensions/`): Implements Bzlmod extensions for toolchain registration (python.bzl), pip integration (pip.bzl), and configuration management (config.bzl). These extensions handle repository rule generation and dependency fetching.

**PyPI Integration** (`python/private/pypi/`): A sophisticated subsystem for parsing requirements files, resolving dependencies, downloading wheels, and generating BUILD files. Key components include hub_builder.bzl for creating hub repositories and whl_library for individual package repositories.

**Toolchain Management** (`python/private/`): Infrastructure for registering and selecting Python toolchains, including support for hermetic runtimes, local system Python, and runtime environment toolchains. The toolchain selection mechanism handles cross-compilation and platform-specific configurations.

**Packaging System** (`python/packaging.bzl`, `python/private/py_wheel.bzl`): Complete implementation of PEP 427 wheel building with metadata generation, console script handling, and integration with twine for publishing.

**Gazelle Plugin** (`gazelle/`): A Go-based plugin that implements BUILD file generation by analyzing Python import graphs, managing modules_mapping for third-party packages, and supporting various Python project structures.

**Tools and Utilities** (`tools/`): Helper programs including the launcher (wrapper for Python executables), precompiler (for .pyc generation), and publishing tools (twine integration).

## Related Projects and Dependencies

The repository depends on several key Bazel ecosystem projects:

- **bazel_skylib**: Provides common Starlark utilities and testing infrastructure
- **rules_cc**: Used for C extension compilation and Python header linkage
- **bazel_features**: Enables feature detection across Bazel versions
- **platforms**: Standard platform definitions for cross-compilation
- **protobuf/rules_proto**: For py_proto_library support
- **stardoc**: Generates API documentation from Starlark source
- **python-build-standalone**: Source of hermetic Python interpreters (from Astral)
- **rules_go**: Required for building the Gazelle plugin

The project integrates with the broader Python ecosystem through support for:
- Standard requirements.txt and pyproject.toml files
- PEP 440 (version specifiers), PEP 427 (wheel format), PEP 517/518 (build systems)
- PyPI and alternative package indices
- pip, pip-tools, build, and uv package managers
- Modern Python features including type hints, async/await, and freethreaded execution

The rules are tested against Bazel versions 7.4.1, 8.0.0, and 9.0.0rc1, with support for both WORKSPACE and Bzlmod build configurations. The project follows semantic versioning and maintains backward compatibility in accordance with Bazel's compatibility policies.
