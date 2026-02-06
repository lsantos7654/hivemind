# rules_uv - Summary

## Overview

`rules_uv` is a Bazel ruleset that integrates [uv](https://github.com/astral-sh/uv), Astral's ultra-fast Python package installer and resolver, into the Bazel build system. This project provides Bazel rules to compile pip requirements files and generate Python virtual environments in a hermetic, reproducible manner within Bazel workflows.

## Purpose and Goals

The primary goal of rules_uv is to bridge the gap between uv's modern Python dependency management capabilities and Bazel's hermetic build paradigm. It enables developers to:

1. **Compile requirements files**: Transform `requirements.in` or `pyproject.toml` files into fully resolved `requirements.txt` files with locked dependencies and cryptographic hashes
2. **Generate virtual environments**: Create reproducible Python virtual environments based on locked requirements
3. **Validate dependencies**: Automatically test that requirements files are up-to-date through diff tests
4. **Support multi-platform builds**: Generate platform-specific requirements for Linux, macOS, and Windows from a single source

The ruleset emphasizes hermetic builds by downloading and managing uv binaries through `rules_multitool`, ensuring consistent tooling across all platforms and build environments.

## Key Features and Capabilities

### pip_compile Rule
The `pip_compile` macro creates Bazel targets that compile requirements files using uv:
- Generates requirements.txt with cryptographic hashes for security
- Supports platform-specific compilation (`--python-platform`)
- Handles requirements overrides for dependency customization
- Automatically creates a diff test to validate requirements are up-to-date
- Integrates with rules_python's Python toolchain system

### Virtual Environment Creation
Two complementary rules for venv management:
- `create_venv`: Creates a fresh virtual environment from requirements
- `sync_venv`: Synchronizes an existing venv to match requirements exactly
- Both support custom destination folders and site-packages customization
- Can inject custom files like `sitecustomize.py` or `.pth` files

### Multi-Platform Support
Rules_uv excels at cross-platform dependency management:
- Generate platform-specific requirements for different OS/architecture combinations
- Use Bazel's `select()` to choose appropriate requirements per platform
- Compatible with rules_python's multi-platform pip.parse configuration
- Supports uv's `--universal` flag for cross-platform compatible wheels

### Hermetic Binary Management
Uses rules_multitool to manage uv binaries:
- Automatically downloads platform-appropriate uv binaries (version 0.8.12)
- Supports Linux (x86_64, arm64), macOS (x86_64, arm64), and Windows (x86_64, arm64)
- Lockfile-based management ensures reproducible builds
- Binaries are verified with SHA256 checksums

## Primary Use Cases and Target Audience

### Target Users
- **Bazel users** who want modern Python dependency management without sacrificing hermetic builds
- **Python developers** migrating from pip-tools or poetry to Bazel
- **DevOps teams** managing multi-platform Python applications
- **Organizations** requiring reproducible, auditable Python builds

### Common Use Cases
1. **Monorepo Python projects**: Manage multiple Python projects with different dependency sets
2. **CI/CD pipelines**: Generate and validate locked dependencies as part of automated testing
3. **Cross-platform development**: Build Python applications that run on Linux, macOS, and Windows
4. **Security-conscious builds**: Use cryptographic hashes to verify dependency integrity
5. **Development environments**: Quickly create local virtual environments that match production dependencies

## High-Level Architecture

The ruleset follows a layered architecture:

**Public API Layer** (`uv/pip.bzl`, `uv/venv.bzl`):
- User-facing macros that provide ergonomic interfaces
- Handle default values and validation
- Create multiple related targets (main target, test target, update alias)

**Implementation Layer** (`uv/private/*.bzl`):
- Bazel rule implementations with full attribute definitions
- Shell script template expansion and substitution
- Runfiles management and Python toolchain integration

**Execution Layer** (`uv/private/*.sh`):
- Bash scripts that invoke uv with appropriate arguments
- Handle file I/O and error reporting
- Provide user-friendly terminal output

**Binary Management**:
- rules_multitool handles downloading and caching uv binaries
- Platform-specific binary selection through lockfile
- Transition rules ensure correct binary architecture

## Related Projects and Dependencies

### Core Dependencies
- **rules_python** (v0.34.0+): Provides Python toolchain and runtime infrastructure
- **rules_multitool** (v0.11.0+): Manages cross-platform binary downloads
- **bazel_skylib** (v1.4.1+): Provides utility functions for Starlark rules
- **platforms**: Bazel's platform constraint system

### Related Rulesets
- **rules_multirun**: Often used with rules_uv for parallel multi-platform builds
- **buildifier_prebuilt**: Development dependency for code formatting

### Upstream Project
- **uv** (astral-sh/uv): The underlying Python package installer and resolver
  - rules_uv currently pins to uv version 0.8.12
  - Provides the core functionality for dependency resolution and venv creation

### Integration Points
Rules_uv is designed to complement rules_python:
- Uses rules_python's Python toolchains for interpreter discovery
- Generated requirements.txt files work with rules_python's `pip.parse()`
- Shares the same Python version and platform configuration approaches

### Publishing and Distribution
- Published to the Bazel Central Registry (BCR) for bzlmod consumption
- Automated release workflow publishes to BCR on each tagged release
- Follows BCR best practices for versioning and compatibility levels

## Compatibility

- **Bazel**: Requires Bazel 6.x or later (tested with Bazel 7.x)
- **Python**: Works with Python 3.8+ through rules_python toolchains
- **Platforms**: Linux, macOS, and Windows on x86_64 and arm64 architectures
- **Build Systems**: Supports both bzlmod (MODULE.bazel) and legacy WORKSPACE
