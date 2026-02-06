# bazel-lib: Base Starlark Libraries for Bazel

## Overview

bazel-lib (formerly aspect_bazel_lib) is a comprehensive collection of base Starlark libraries and essential Bazel rules designed to simplify rule authoring and BUILD file management. Following its donation to the Linux Foundation, the project was renamed from "aspect_bazel_lib" to "bazel_lib" to enable broader community participation. This repository serves as a foundation for building custom rulesets and provides utilities that are too specialized or feature-rich for inclusion in the more conservative bazel-skylib project.

## Purpose and Goals

The primary goal of bazel-lib is to provide a rich set of utilities and rules that make Bazel more ergonomic and powerful without requiring extensive shell scripting or complex genrule definitions. It bridges the gap between bazel-skylib's minimal scope and the practical needs of ruleset authors and build engineers. The project focuses on:

- **Platform-agnostic operations**: Providing hermetic tools (like coreutils) that work consistently across Linux, macOS, and Windows without requiring bash
- **File and directory manipulation**: Comprehensive APIs for copying, moving, and transforming files and directories
- **Build action utilities**: Running binaries, expanding templates, and generating source files from build outputs
- **Starlark utilities**: Enhanced string, list, path, and encoding operations beyond bazel-skylib
- **Development workflows**: Tools like write_source_files for writing build outputs back to the source tree

## Key Features and Capabilities

bazel-lib provides over 25 public modules organized into several categories:

**File Operations**: copy_file, copy_to_bin, copy_directory, copy_to_directory, directory_path - hermetic file copying with DirectoryPathInfo support

**Build Actions**: run_binary (improved alternative to genrule), expand_template (template expansion with substitutions), output_files (extract specific outputs from targets)

**Source Tree Integration**: write_source_files - a sophisticated system for writing generated files back to source with automatic diff testing and update workflows

**Starlark Utilities**: utils (general helpers), paths (path manipulation), strings (string operations), lists (functional list operations), base64 (encoding/decoding), glob_match (pattern matching)

**Platform and Transition Support**: platform_utils, windows_utils, transitions (platform_transition_binary/test/filegroup for cross-compilation)

**Build Configuration**: stamping (build metadata), expand_make_vars (variable expansion), params_file (argument file generation)

**Testing**: bats (Bash Automated Testing System integration), resource_sets (test resource management)

**Bzlmod Extensions**: Toolchain registration for copy_directory, copy_to_directory, coreutils, expand_template, zstd, and bats

## Primary Use Cases and Target Audience

**Ruleset Authors**: Developers creating custom Bazel rules who need reliable utilities for file operations, path handling, and Starlark programming patterns

**Build Engineers**: Teams managing complex Bazel builds who need platform-independent operations and sophisticated file manipulation

**Polyglot Projects**: Organizations using Bazel across multiple languages and platforms who need consistent tooling without platform-specific scripts

**Code Generation Workflows**: Projects that generate source code, documentation, or configuration files and need to write them back to the repository with verification

**Migration from Genrule**: Teams replacing shell-based genrules with more maintainable and platform-independent alternatives

## Architecture Overview

bazel-lib follows a clear three-tier architecture:

1. **Public API Layer** (`lib/*.bzl`): Thin wrapper files that export symbols from private implementations, providing stable public APIs with comprehensive documentation

2. **Private Implementation Layer** (`lib/private/*.bzl`): Core Starlark implementations containing rule definitions, provider logic, and complex algorithms

3. **Native Tools Layer** (`tools/*/`): Go-based binaries (copy_directory, copy_to_directory, expand_template) that perform platform-specific operations efficiently, distributed as pre-built releases or compiled from source

The project uses bzlmod for dependency management (with WORKSPACE support for legacy users) and integrates with bazel_features for version-aware functionality. Toolchains are registered through module extensions, making the utilities available without explicit repository declarations.

## Dependencies and Related Projects

**Core Dependencies**:
- bazel_skylib (v1.8.1+): Foundation library for basic Starlark utilities
- bazel_features (v1.9.0+): Version detection and feature compatibility
- platforms (v0.0.10+): Platform constraint definitions
- rules_shell (v0.4.1+): Shell script support

**Development Dependencies**:
- rules_go (v0.59.0+) and gazelle (v0.40.0): For building Go-based tools from source
- buildifier_prebuilt: Code formatting and linting

**Related Projects**:
In version 3.0, several tools were split into separate modules - tar, jq, and yq now have their own dedicated repositories. This modularization allows users to depend only on the functionality they need.

**Relationship to bazel-skylib**: While bazel-skylib provides foundational utilities with a narrow, conservative scope, bazel-lib accepts feature requests and provides more opinionated, feature-rich alternatives. The two are complementary - bazel-lib depends on bazel-skylib and may eventually provide ABI-compatible replacements for some skylib functionality.

## Distribution Model

Releases are published to the Bazel Central Registry (BCR) as both source distributions and optimized packages with pre-built Go binaries. Users consuming from BCR get faster builds by avoiding Go compilation. Development versions can be used via git_override, but require Go toolchains for building tools from source. The project follows semantic versioning and maintains API stability guarantees through its compatibility_level declaration.
