# Code Structure and Organization

## Directory Tree

```
bazel-lib/
├── .aspect/                    # Aspect CLI configuration
├── .bcr/                       # Bazel Central Registry metadata
├── .github/                    # CI/CD workflows and issue templates
├── BUILD.bazel                 # Root build file with gazelle and formatting targets
├── MODULE.bazel                # Bzlmod module definition with dependencies
├── bzl_library.bzl             # Custom bzl_library rule with doc extraction
├── deps.bzl                    # Go dependencies for WORKSPACE users
│
├── lib/                        # Main library code (PUBLIC API)
│   ├── base64.bzl              # Base64 encoding/decoding utilities
│   ├── bats.bzl                # Bash Automated Testing System integration
│   ├── copy_directory.bzl      # Copy directory trees hermetically
│   ├── copy_file.bzl           # Copy individual files (skylib fork with enhancements)
│   ├── copy_to_bin.bzl         # Copy source files to bazel-bin
│   ├── copy_to_directory.bzl   # Assemble directory trees from multiple sources
│   ├── directory_path.bzl      # DirectoryPathInfo provider for directory references
│   ├── expand_make_vars.bzl    # Expand make variables in strings
│   ├── expand_template.bzl     # Template expansion with substitutions
│   ├── extensions.bzl          # Bzlmod module extensions for toolchains
│   ├── glob_match.bzl          # Glob pattern matching utilities
│   ├── host_repo.bzl           # Host platform detection repository rule
│   ├── lists.bzl               # Functional list operations (map, filter, find, etc.)
│   ├── output_files.bzl        # Extract specific outputs from targets
│   ├── params_file.bzl         # Generate parameter files for long command lines
│   ├── paths.bzl               # Path manipulation (rlocation, repository-relative, etc.)
│   ├── platform_utils.bzl      # Platform constraint utilities
│   ├── repo_utils.bzl          # Repository rule utilities
│   ├── repositories.bzl        # Repository rule definitions for toolchains
│   ├── resource_sets.bzl       # Test resource set management
│   ├── run_binary.bzl          # Run binaries as build actions (skylib fork)
│   ├── stamping.bzl            # Build stamping and version information
│   ├── strings.bzl             # String utilities (chr, ord, hex, split_args)
│   ├── transitions.bzl         # Platform transition rules for cross-compilation
│   ├── utils.bzl               # General-purpose utilities (to_label, file_exists, etc.)
│   ├── windows_utils.bzl       # Windows-specific path and command utilities
│   ├── write_source_files.bzl  # Write build outputs to source tree with diff testing
│   │
│   ├── private/                # Private implementation details (DO NOT IMPORT DIRECTLY)
│   │   ├── *.bzl               # Rule implementations, helpers, providers
│   │   └── *_toolchain.bzl     # Toolchain definitions and implementations
│   │
│   └── tests/                  # Unit tests and integration tests
│       ├── *_test.bzl          # Starlark unit tests using skylib unittest
│       ├── *_tests.bzl         # Test suites
│       ├── copy_to_directory_bin_action/  # Action tests
│       ├── copy_directory_bin_action/     # Action tests
│       ├── external_test_repo/            # External dependency test repo
│       ├── stamping/                      # Stamping tests
│       └── write_source_files/            # Write source files tests
│
├── tools/                      # Native Go tools for performance-critical operations
│   ├── common/                 # Shared Go code (copy utilities, file operations)
│   │   ├── copy.go             # Cross-platform file copying with clonefile support
│   │   ├── file.go             # File utility functions
│   │   ├── clonefile_*.go      # Platform-specific optimizations (Darwin, Linux)
│   │   └── BUILD.bazel
│   │
│   ├── copy_directory/         # Hermetic directory copying tool
│   │   ├── main.go
│   │   └── BUILD.bazel
│   │
│   ├── copy_to_directory/      # Directory assembly tool with filtering
│   │   ├── main.go
│   │   └── BUILD.bazel
│   │
│   ├── expand_template/        # Template expansion binary
│   │   ├── main.go
│   │   └── BUILD.bazel
│   │
│   └── release/                # Release automation
│       ├── release.bzl
│       └── hashes.bzl
│
├── platforms/                  # Platform configuration
│   └── config/
│       └── defs.bzl            # Platform constraint definitions
│
├── shlib/                      # Shell library utilities
│   ├── lib/
│   │   └── assertions.sh       # Bash assertion functions for testing
│   └── tests/                  # Shell library tests
│
├── e2e/                        # End-to-end integration tests
│   ├── api_entries/            # API surface tests
│   ├── copy_action/            # Copy action integration tests
│   ├── copy_to_directory/      # Copy to directory integration tests
│   ├── coreutils/              # Coreutils toolchain tests
│   ├── external_copy_to_directory/  # External workspace tests
│   ├── smoke/                  # Smoke tests
│   └── write_source_files/     # Write source files integration tests
│
└── docs/                       # (Generated documentation published separately)
```

## Module Organization

### Public API Structure

All public APIs follow a consistent pattern:

1. **Thin wrapper in `lib/*.bzl`**: Exports symbols from private implementations
2. **Documentation at top level**: Public files contain comprehensive docstrings
3. **No direct logic**: Public files use `load()` and simple assignments

Example pattern from `lib/copy_file.bzl`:
```starlark
load("//lib/private:copy_file.bzl", _copy_file = "copy_file")
copy_file = _copy_file
```

### Private Implementation Pattern

Private implementations in `lib/private/*.bzl` contain:

- Rule implementations (`_foo_impl` functions)
- Provider definitions
- Helper functions and constants
- Toolchain resolution logic
- Complex algorithms

Files are named to match their public counterparts with additional `_toolchain.bzl` files for toolchain definitions.

### Test Organization

Tests are co-located with implementation in `lib/tests/`:

- **Unit tests**: Use `skylib`'s `unittest.bzl` framework, named `*_test.bzl`
- **Integration tests**: Subdirectories with BUILD files testing complex scenarios
- **Test utilities**: Helper rules and macros like `generate_outputs.bzl`

### Go Tools Organization

Native tools in `tools/` follow Go project structure:

- **main.go**: Entry point with CLI parsing
- **BUILD.bazel**: go_binary targets with go_library dependencies
- **common/**: Shared utilities used across multiple tools

Tools are built with `rules_go` and distributed as pre-compiled binaries in releases.

## Key Files and Their Roles

### Root Configuration

**MODULE.bazel** (84 lines)
- Declares module name, compatibility level, and Bazel version requirements
- Defines runtime dependencies (bazel_features, bazel_skylib, platforms, rules_shell)
- Configures toolchain module extensions
- Contains dev dependencies for building tools from source (rules_go, gazelle)
- Uses IS_RELEASE flag to control dev dependency inclusion in BCR releases

**BUILD.bazel** (Root)
- Gazelle configuration for Go dependency management
- Buildifier targets for code formatting
- Convenience targets for repository maintenance

**bzl_library.bzl**
- Custom implementation that extends skylib's bzl_library
- Generates starlark_doc_extract targets for API validation
- Ensures public APIs list all dependencies correctly
- Critical for maintaining documentation quality

**deps.bzl**
- WORKSPACE-style Go dependency declarations
- Generated by gazelle update-repos
- Required only when using git_override or WORKSPACE mode

### Core Public APIs

**lib/copy_file.bzl** and **lib/copy_directory.bzl**
- Hermetic file/directory copying using coreutils toolchain
- No shell dependencies, works on Windows without bash
- Support DirectoryPathInfo provider

**lib/copy_to_directory.bzl**
- Most complex rule in the project
- Assembles output directories from multiple sources with filtering
- Supports include/exclude patterns, path transformations
- Backed by Go binary for performance

**lib/run_binary.bzl**
- Alternative to native.genrule() without shell requirements
- Better makevar expansion than skylib version
- Supports directory outputs
- Key for platform-independent code generation

**lib/write_source_files.bzl** (226 lines)
- Sophisticated macro generating multiple targets
- Creates update targets (bazel run) and diff_test targets
- Supports tree structures with `additional_update_targets`
- Customizable error messages with template substitution
- Critical for workflows involving code generation

**lib/utils.bzl** and **lib/paths.bzl**
- Most frequently used utilities
- Path manipulation, label conversion, version detection
- Platform-agnostic path handling with runfiles support

**lib/transitions.bzl**
- Platform transition rules for cross-compilation
- `platform_transition_binary`, `platform_transition_test`, `platform_transition_filegroup`
- Essential for multi-platform builds

### Module Extensions

**lib/extensions.bzl**
- Defines `toolchains` and `host` module extensions
- Registers toolchains for copy_directory, copy_to_directory, coreutils, expand_template, bats, zstd
- Implements BFS traversal for toolchain dependency resolution
- Enables bzlmod users to automatically get required toolchains

**lib/repositories.bzl**
- Repository rule implementations
- Toolchain registration functions
- Version and URL constants for external tools
- Critical for WORKSPACE users

## Code Organization Patterns

### Separation of Concerns

1. **API Layer**: Public files in `lib/*.bzl` provide stable interfaces
2. **Implementation Layer**: Private files handle complex logic
3. **Tooling Layer**: Go binaries handle performance-critical operations
4. **Testing Layer**: Separate test files and directories verify functionality

### Provider Pattern

Rules use custom providers for passing information:

- `DirectoryPathInfo`: Represents directory references
- `WriteSourceFileInfo`: Tracks write_source_file targets
- Standard Bazel providers: DefaultInfo, OutputGroupInfo, RunEnvironmentInfo

### Toolchain Pattern

Performance-critical operations use toolchains:

- `copy_directory_toolchain_type`: Platform-specific copy_directory binaries
- `copy_to_directory_toolchain_type`: Directory assembly binaries
- `coreutils_toolchain_type`: Hermetic coreutils (cp, mkdir, etc.)
- `expand_template_toolchain_type`: Template expansion binaries

### Macro vs Rule Pattern

- **Macros**: Used for convenience and generating multiple related targets (write_source_files, expand_template)
- **Rules**: Used for core functionality requiring analysis-time logic
- **Library structs**: Used for pure functions (base64.encode, utils.to_label)

### Documentation Pattern

Every public file includes:

- Module-level docstring explaining purpose
- Usage examples with starlark code blocks
- Links to related functionality
- Args documentation with types and defaults

This structure makes bazel-lib easy to navigate, extend, and maintain while providing clear separation between public APIs and internal implementation details.
