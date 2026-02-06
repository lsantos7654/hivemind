# rules_py Summary

## Overview

`aspect_rules_py` (commonly referred to as `rules_py`) is Aspect Build's modern Bazel ruleset for Python development. It serves as a next-generation alternative to the canonical `rules_python`, providing enhanced ergonomics, better IDE integration, and improved compatibility with standard Python tooling. The project is maintained by Aspect Build and available at https://github.com/aspect-build/rules_py.

## Purpose and Goals

rules_py reimplements the core Python rules (`py_library`, `py_binary`, `py_test`) on top of rules_python's toolchain layer, with the primary goal of making Python development in Bazel feel more natural and aligned with ecosystem conventions. The ruleset addresses long-standing ergonomic and correctness issues in rules_python while maintaining API compatibility for smooth migration.

Key design goals include:
- **Hermetic isolation**: Run Python in isolated mode to prevent sandbox escapes and system package pollution
- **Standard virtualenv layout**: Use conventional `site-packages` folder structure instead of manipulating `sys.path`
- **IDE-first development**: Generate proper virtualenvs that work seamlessly with PyCharm, VSCode, and other editors
- **Bash-based launchers**: Remove dependency on system Python interpreters for launching binaries
- **Cross-platform builds**: First-class support for building Python applications for different target platforms

## Key Features

### Enhanced Python Rules

The ruleset provides drop-in replacements for standard Bazel Python rules with improved runtime behavior:
- `py_library`: Manages Python source files and dependencies with proper import path handling
- `py_binary`: Creates executable Python programs with isolated virtualenv environments
- `py_test`: Identical to py_binary but integrated with Bazel's test framework, includes pytest support
- `py_venv_link`: Generates IDE-compatible virtualenv symlinks for development

### uv Integration (Experimental)

rules_py includes a complete alternative dependency management system built on Astral's `uv` lockfiles:
- **Multi-configuration support**: Define multiple "venvs" (virtual environments) within a single dependency hub
- **Cross-build capability**: Build Python wheels for different target platforms from any host
- **Hermetic source builds**: Compile source distributions (sdists) using Bazel's hermetic toolchains
- **Lazy resolution**: Downloads and builds happen at build time, not repository configuration time
- **Automatic cycle handling**: Detects and resolves circular dependencies without user intervention
- **Override system**: Replace locked requirements with first-party Bazel targets for development

### Native Tools

The project includes several Rust-based tools for high-performance operations:
- **venv_bin**: Creates and manages Python virtual environments
- **unpack_bin**: Efficiently extracts and installs wheel files
- **venv_shim**: Provides virtualenv activation and path management
- **runfiles library**: Handles Bazel runfiles for proper file location in executables

These tools leverage the `uv` Rust libraries for compatibility and performance.

## Target Audience

rules_py is designed for:
- **Python teams** adopting Bazel or experiencing friction with rules_python
- **Monorepo developers** needing reliable cross-platform Python builds
- **Organizations** requiring hermetic, reproducible Python builds at scale
- **IDE users** who want proper autocomplete and navigation in their Python projects
- **Teams** building containerized Python applications with precise dependency control

## High-Level Architecture

The architecture consists of three main layers:

**Toolchain Layer** (inherited from rules_python):
- Python interpreter registration and version management
- Platform-specific toolchain resolution
- Hermetic Python runtime distribution

**Rule Implementation Layer** (rules_py):
- Reimplemented py_library, py_binary, py_test with virtualenv-based semantics
- Bash-based launcher templates that create isolated Python environments
- Virtualenv generation for IDE integration
- Support for multiple Python versions via toolchain transitions

**Dependency Management Layer** (uv subsystem):
- Lockfile-based dependency resolution using uv.lock format
- Hub/venv architecture enabling multiple dependency configurations
- Wheel installation and sdist building as Bazel actions
- Platform-aware dependency selection for cross-compilation

## Related Projects and Dependencies

**Core Dependencies**:
- `rules_python` (v1.0.0+): Provides Python toolchains and base providers
- `bazel_lib` (v3.0.0+): Common utilities for file operations and transitions
- `bazel_skylib` (v1.4.2+): Standard Bazel library functions
- `with_cfg.bzl` (v0.14.1+): Configuration and transition support

**Development Tools**:
- `uv` (Astral): Fast Python package installer and resolver (integrated as Rust library)
- `rules_rust` (v0.68.1+): For building the native Rust tooling
- `toolchains_llvm`: For cross-platform C extension compilation

**Complementary Projects**:
- `aspect-gazelle`: Pre-compiled Gazelle extension for BUILD file generation
- `rules_oci`: For building container images with py_image_layer
- `tools_telemetry`: Limited usage reporting to Aspect Build

## Relationship to rules_python

rules_py is a compatible layer that sits on top of rules_python's toolchain implementation. It reuses Python interpreter toolchains but provides entirely new implementations of the end-user rules. Projects can use rules_py's rules while still using rules_python's `pip.parse()` for dependencies, or they can adopt the uv-based dependency system for additional benefits. The philosophy differs from rules_python's Google-internal focus by prioritizing alignment with standard Python ecosystem tools and workflows.
