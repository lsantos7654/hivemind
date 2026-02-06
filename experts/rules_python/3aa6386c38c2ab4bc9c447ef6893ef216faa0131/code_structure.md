# rules_python Code Structure

## Complete Annotated Directory Tree

```
rules_python/
├── python/                      # Core rules and public APIs
│   ├── api/                     # Public API for extending rules
│   │   ├── api.bzl              # Main API aggregator
│   │   ├── attr_builders.bzl    # Attribute builder utilities
│   │   ├── executables.bzl      # Builders for executable rules
│   │   ├── libraries.bzl        # Builders for library rules
│   │   └── rule_builders.bzl    # Low-level rule builders
│   ├── bin/                     # Binary utilities and wrappers
│   ├── cc/                      # C/C++ integration support
│   │   ├── py_cc_toolchain.bzl      # Python C extension toolchain
│   │   └── py_cc_toolchain_info.bzl # Provider for C headers/libs
│   ├── config_settings/         # Configuration settings and transitions
│   │   ├── config_settings.bzl      # Build settings definitions
│   │   ├── transition.bzl           # Python version transitions
│   │   └── private/py_args.bzl      # Argument parsing for transitions
│   ├── constraints/             # Platform constraints
│   ├── entry_points/            # Console script handling
│   │   └── py_console_script_binary.bzl  # Entry point wrapper rule
│   ├── extensions/              # Bzlmod module extensions
│   │   ├── python.bzl           # Python toolchain extension
│   │   ├── pip.bzl              # PyPI integration extension
│   │   └── config.bzl           # Configuration extension
│   ├── local_toolchains/        # Local system Python toolchains
│   ├── pip_install/             # Legacy pip integration (WORKSPACE)
│   │   ├── pip_repository.bzl       # Repository rule for pip
│   │   ├── requirements.bzl         # Requirements parsing
│   │   └── requirements_parser.bzl  # Parser implementation
│   ├── private/                 # Internal implementation details
│   │   ├── api/                 # Internal API implementations
│   │   ├── common/              # Common rule implementations
│   │   │   ├── py_binary_rule_bazel.bzl    # Binary rule internals
│   │   │   ├── py_library_rule_bazel.bzl   # Library rule internals
│   │   │   ├── py_test_rule_bazel.bzl      # Test rule internals
│   │   │   └── py_runtime_rule.bzl         # Runtime rule internals
│   │   ├── pypi/                # PyPI package management
│   │   │   ├── extension.bzl            # Main pip extension logic
│   │   │   ├── hub_builder.bzl          # Hub repository generation
│   │   │   ├── whl_library.bzl          # Individual package repos
│   │   │   ├── generate_whl_library_build_bazel.bzl  # BUILD file generation
│   │   │   ├── generate_group_library_build_bazel.bzl # Group target generation
│   │   │   ├── package_annotation.bzl   # Package customization
│   │   │   ├── evaluate_markers.bzl     # PEP 508 marker evaluation
│   │   │   ├── deps.bzl                 # Dependency resolution
│   │   │   ├── attrs.bzl                # Attribute definitions
│   │   │   ├── flags.bzl                # Feature flags
│   │   │   ├── config_settings.bzl      # PyPI config settings
│   │   │   └── env_marker_*.bzl         # Environment marker handling
│   │   ├── whl_filegroup/       # Wheel file extraction
│   │   ├── zipapp/              # Zipapp (PEX-like) support
│   │   ├── py_binary_macro.bzl      # Binary macro implementation
│   │   ├── py_library_macro.bzl     # Library macro implementation
│   │   ├── py_test_macro.bzl        # Test macro implementation
│   │   ├── py_binary_rule.bzl       # Binary rule definition
│   │   ├── py_library_rule.bzl      # Library rule definition
│   │   ├── py_test_rule.bzl         # Test rule definition
│   │   ├── py_runtime_macro.bzl     # Runtime macro
│   │   ├── py_runtime_rule.bzl      # Runtime rule
│   │   ├── py_runtime_pair_macro.bzl    # Runtime pair macro
│   │   ├── py_runtime_pair_rule.bzl     # Runtime pair rule
│   │   ├── py_info.bzl              # PyInfo provider implementation
│   │   ├── py_runtime_info.bzl      # PyRuntimeInfo provider
│   │   ├── py_executable.bzl        # Executable target support
│   │   ├── py_console_script_binary.bzl # Console script internals
│   │   ├── py_console_script_gen.bzl    # Console script generation
│   │   ├── py_package.bzl           # py_package rule
│   │   ├── py_wheel.bzl             # py_wheel rule implementation
│   │   ├── py_cc_toolchain_*.bzl    # C toolchain implementations
│   │   ├── toolchains_repo.bzl      # Toolchain repository generation
│   │   ├── toolchain_aliases.bzl    # Toolchain alias generation
│   │   ├── python_register_toolchains.bzl  # Toolchain registration
│   │   ├── hermetic_runtime_repo_setup.bzl # Hermetic runtime setup
│   │   ├── local_runtime_repo_setup.bzl    # Local runtime setup
│   │   ├── precompile.bzl           # Bytecode precompilation
│   │   ├── interpreter.bzl          # Interpreter utilities
│   │   ├── normalize_name.bzl       # Package name normalization
│   │   ├── version.bzl              # Version parsing
│   │   ├── full_version.bzl         # Full version handling
│   │   ├── common.bzl               # Common utilities
│   │   ├── util.bzl                 # General utilities
│   │   ├── text_util.bzl            # Text processing
│   │   └── [many more internal files]
│   ├── proto/                   # Protobuf support
│   ├── runfiles/                # Runfiles library
│   ├── runtime_env_toolchains/  # Runtime environment toolchains
│   ├── uv/                      # UV package manager integration
│   │   ├── private/             # UV implementation
│   │   │   ├── uv.bzl               # Main UV extension
│   │   │   ├── uv_repository.bzl    # UV repository rule
│   │   │   ├── uv_toolchain.bzl     # UV toolchain rule
│   │   │   ├── uv_toolchains_repo.bzl   # UV toolchains hub
│   │   │   ├── lock.bzl             # Lock file handling
│   │   │   └── current_toolchain.bzl    # Toolchain selection
│   │   ├── uv.bzl               # Public UV API
│   │   └── uv_toolchain*.bzl    # UV toolchain exports
│   ├── zipapp/                  # Zipapp executable support
│   ├── defs.bzl                 # Main public API aggregator
│   ├── py_binary.bzl            # py_binary macro
│   ├── py_library.bzl           # py_library macro
│   ├── py_test.bzl              # py_test macro
│   ├── py_runtime.bzl           # py_runtime macro
│   ├── py_runtime_pair.bzl      # py_runtime_pair macro
│   ├── py_import.bzl            # py_import rule
│   ├── py_info.bzl              # PyInfo provider export
│   ├── py_runtime_info.bzl      # PyRuntimeInfo provider export
│   ├── pip.bzl                  # Pip integration (WORKSPACE)
│   ├── packaging.bzl            # Wheel packaging rules
│   ├── proto.bzl                # Protobuf rules
│   ├── python.bzl               # Legacy Python rules export
│   ├── versions.bzl             # Supported Python versions
│   ├── features.bzl             # Feature flags
│   └── current_py_toolchain.bzl # Current toolchain accessor
│
├── gazelle/                     # Gazelle plugin for BUILD generation
│   ├── python/                  # Python-specific plugin code (Go)
│   │   ├── *.go                 # Plugin implementation
│   │   └── testdata/            # Test fixtures
│   ├── manifest/                # Manifest generation
│   ├── modules_mapping/         # Package name mapping
│   ├── pythonconfig/            # Configuration for Gazelle
│   ├── examples/                # Gazelle usage examples
│   └── docs/                    # Gazelle documentation
│
├── tools/                       # Build and runtime tools
│   ├── launcher/                # Python executable launcher
│   ├── precompiler/             # Python bytecode precompiler
│   ├── publish/                 # Publishing tools (twine)
│   ├── build_defs/              # Build definition helpers
│   └── private/                 # Internal tool implementations
│
├── tests/                       # Comprehensive test suite
│   ├── api/                     # API tests
│   ├── base_rules/              # Core rule tests
│   ├── pypi/                    # PyPI integration tests
│   ├── integration/             # Integration tests with Bazel
│   ├── toolchains/              # Toolchain tests
│   ├── py_wheel/                # Wheel building tests
│   ├── multi_pypi/              # Multi-hub tests
│   ├── modules/                 # Bzlmod module tests
│   └── [many more test categories]
│
├── examples/                    # Example projects
│   ├── bzlmod/                  # Bzlmod examples
│   ├── pip_parse/               # pip_parse example
│   ├── pip_parse_vendored/      # Vendored dependencies example
│   ├── wheel/                   # Wheel building example
│   ├── multi_python_versions/   # Multi-version example
│   └── build_file_generation/   # Gazelle example
│
├── docs/                        # Documentation source
│   ├── api/                     # API documentation
│   ├── pypi/                    # PyPI integration docs
│   ├── howto/                   # How-to guides
│   ├── _static/                 # Static assets
│   ├── _includes/               # Reusable doc snippets
│   ├── conf.py                  # Sphinx configuration
│   ├── getting-started.md       # Getting started guide
│   ├── extending.md             # Extension guide
│   ├── coverage.md              # Coverage guide
│   └── environment-variables.md # Environment variable reference
│
├── sphinxdocs/                  # Sphinx documentation tooling
│   ├── src/                     # Sphinx extensions
│   └── inventories/             # External doc inventories
│
├── private/                     # Top-level private utilities
│
├── .github/                     # GitHub configuration
│   ├── workflows/               # CI/CD workflows
│   └── ISSUE_TEMPLATE/          # Issue templates
│
├── .bazelci/                    # Bazel CI configuration
├── .bcr/                        # Bazel Central Registry templates
├── MODULE.bazel                 # Bzlmod module definition
├── WORKSPACE                    # Legacy workspace file
├── BUILD.bazel                  # Root build file
├── version.bzl                  # Version information
├── internal_dev_deps.bzl        # Dev dependencies
└── [configuration files]        # .bazelrc, .bazelversion, etc.
```

## Module and Package Organization

The codebase follows a clear layering strategy:

**Public Layer** (`python/*.bzl`): Top-level files that users import directly. These are macro wrappers that provide Python 2 deprecation checks and forward to internal implementations. Examples: `py_binary.bzl`, `py_library.bzl`, `defs.bzl`.

**Extension Layer** (`python/extensions/`): Bzlmod-specific code for module extension implementations. These handle repository rule generation and toolchain registration during Bazel's module resolution phase.

**API Layer** (`python/api/`): Public but volatile APIs for creating custom derived rules. Provides builders for executables, libraries, and rule definitions that can be extended by users.

**Private Implementation** (`python/private/`): All internal implementation details. This includes actual rule implementations, providers, helper functions, and platform-specific logic. Not intended for direct user consumption.

**PyPI Subsystem** (`python/private/pypi/`): Self-contained subsystem for all pip/PyPI integration, including requirement parsing, dependency resolution, wheel downloading, and BUILD file generation.

**Tooling** (`tools/`): Compiled or executable tools that run during builds, including the Python launcher and bytecode precompiler written in Python.

**Gazelle Plugin** (`gazelle/`): Go-based Gazelle plugin that runs as a separate binary, analyzing Python source and generating BUILD files.

## Main Source Directories and Their Purposes

**`python/`**: The heart of the repository containing all Python-specific Bazel rules. Users primarily interact with top-level files here, while the private/ subdirectory contains the actual implementations.

**`python/private/pypi/`**: Complete PyPI integration system handling requirements.txt parsing, package downloading, BUILD file generation, and dependency graph resolution. This is effectively a pip replacement within Bazel.

**`python/extensions/`**: Bzlmod module extensions that integrate with Bazel's module system to provide toolchain registration and pip functionality in MODULE.bazel files.

**`gazelle/`**: Standalone Go program implementing a Gazelle plugin for automatic BUILD file generation from Python source code.

**`tools/`**: Runtime and build-time utilities including the launcher (wraps Python binaries with proper runfiles setup) and precompiler (generates .pyc files).

**`tests/`**: Extensive test coverage organized by feature area, including unit tests, integration tests, and tests that validate behavior across Bazel versions.

**`examples/`**: Working example projects demonstrating various features, serving both as documentation and as integration test cases.

**`docs/`**: Sphinx-based documentation source with extensive API references, how-to guides, and conceptual documentation.

## Key Files and Their Roles

**`MODULE.bazel`**: Defines the rules_python module for Bzlmod, including dependencies, toolchain configuration, and pip integration for internal use.

**`python/defs.bzl`**: Main entry point aggregating all public rules. Users typically import `py_library`, `py_binary`, etc. from here.

**`python/pip.bzl`**: Exports pip integration functions (`pip_parse`, `compile_pip_requirements`) for WORKSPACE users.

**`python/extensions/python.bzl`**: Bzlmod extension for registering Python toolchains from hermetic or local sources.

**`python/extensions/pip.bzl`**: Bzlmod extension for integrating PyPI dependencies via `pip.parse()`.

**`python/private/pypi/extension.bzl`**: Core pip extension implementation handling requirement parsing and repository generation.

**`python/private/pypi/hub_builder.bzl`**: Generates the hub repository (e.g., @pypi) that aggregates all pip packages with alias targets.

**`python/private/py_binary_macro.bzl`**: Macro implementation for py_binary, handling Python 2 deprecation and forwarding to the rule.

**`python/private/py_info.bzl`**: Implementation of the PyInfo provider, the key provider for propagating Python dependencies.

**`python/versions.bzl`**: Defines all supported Python versions with download URLs and checksums for hermetic interpreters.

**`python/packaging.bzl`**: Exports `py_wheel`, `py_package`, and related packaging rules for building distributable wheels.

**`gazelle/python/*.go`**: Go implementation of the Gazelle plugin's Python support, including import analysis and BUILD generation.

**`tools/launcher/launcher.py`**: Python script that wraps executables to set up runfiles and environment properly before execution.

**`.bazelrc`**: Project-wide Bazel configuration including platform settings, feature flags, and build options.

## Code Organization Patterns

The repository follows several consistent patterns:

**Macro + Rule Pattern**: Public macros (e.g., `py_binary.bzl`) wrap internal rules (e.g., `py_binary_rule.bzl`) to provide deprecation warnings, default value transformations, and convenience features while keeping rule implementations clean.

**Provider-Based Architecture**: Information flows through the build graph via providers (PyInfo, PyRuntimeInfo, PyWheelInfo) rather than direct attribute access, enabling proper encapsulation.

**Repository Rule Generation**: Complex setup logic (toolchain registration, pip integration) uses repository rules to generate BUILD files and workspaces dynamically at analysis time.

**Platform Abstraction**: Platform-specific logic is isolated using Bazel's select() and platform/constraint system, with utilities in `python/private/platform_info.bzl`.

**Extensibility via Builders**: The `python/api/` directory provides builder APIs that construct rule definitions, allowing users to create derived rules without modifying core code.

**Test Co-location**: Tests are organized by feature rather than strictly mirroring source structure, with each test directory containing BUILD files and test data.

The overall design prioritizes hermetic builds, cross-platform support, and extensibility while maintaining backward compatibility with existing Bazel Python projects.
