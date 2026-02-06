# rules_py Code Structure

## Complete Directory Tree

```
rules_py/
├── .aspect/                    # Aspect Workflows CI configuration
├── .bazelignore                # Directories excluded from Bazel processing
├── .bazelrc                    # Bazel configuration defaults
├── .bazelversion               # Pins Bazel version for the project
├── .bcr/                       # Bazel Central Registry submission metadata
│   ├── metadata.template.json  # BCR module metadata template
│   ├── presubmit.yml          # BCR validation configuration
│   ├── source.template.json   # Source archive template
│   └── patches/               # Patches applied for BCR releases
├── .github/                    # GitHub Actions CI/CD workflows
│   └── workflows/
│       ├── ci.yaml            # Main continuous integration
│       ├── publish.yaml       # Release publishing automation
│       ├── release.yml        # Release workflow
│       └── integrity.jq       # Integrity hash computation
├── BUILD.bazel                 # Root BUILD file with bzl_library targets
├── MODULE.bazel                # Bzlmod module configuration
├── Cargo.{toml,lock}          # Rust workspace configuration
├── LICENSE                     # Apache 2.0 license
├── README.md                   # Main project documentation
├── CONTRIBUTING.md             # Contribution guidelines
├── annotations.toml            # uv requirement annotations
├── requirements.{in,txt}       # Python dependencies for dev
├── uv.lock                     # uv lockfile for dev dependencies
├── gazelle_python.yaml         # Gazelle configuration
├── renovate.json               # Renovate bot configuration
│
├── bazel/                      # Bazel infrastructure and tooling
│   ├── BUILD.bazel            # Workspace-level utilities
│   ├── defs.bzl               # Common macro definitions
│   ├── defaults.bazelrc       # Default Bazel flags
│   ├── workspace_status.sh    # Workspace status script
│   ├── patches/               # Patches for dependencies
│   │   ├── BUILD.bazel
│   │   └── llvm_darwin_sysroot.patch
│   ├── platforms/             # Platform definitions
│   │   ├── BUILD.bazel        # Platform targets
│   │   ├── config/            # Configuration settings
│   │   ├── linkers/           # Linker toolchains
│   │   └── toolchains/        # Custom toolchain defs
│   ├── proto/                 # Protobuf configuration
│   │   ├── MODULE.bazel
│   │   └── .bazelrc
│   ├── release/               # Release automation
│   │   ├── BUILD.bazel
│   │   ├── release.bzl        # Release macros
│   │   ├── hashes.bzl         # Hash generation
│   │   └── create_release.sh  # Release script
│   └── rust/                  # Rust build configuration
│       ├── BUILD.bazel
│       ├── defs.bzl
│       ├── README.md
│       └── multi_platform_rust_binaries.bzl
│
├── doc/                        # Additional documentation
│   └── venv_linking.md        # Virtual environment linking guide
│
├── docs/                       # User-facing documentation
│   ├── migrating.md           # Migration guide from rules_python
│   ├── uv.md                  # uv dependency system documentation
│   └── virtual_deps.md        # Virtual dependency resolution
│
├── py/                         # Main Python rules implementation
│   ├── BUILD.bazel            # Public API targets
│   ├── defs.bzl               # Public API: py_library, py_binary, py_test
│   ├── extensions.bzl         # Bazel module extensions
│   ├── repositories.bzl       # Repository rules
│   ├── toolchains.bzl         # Toolchain registration helpers
│   │
│   ├── private/               # Private implementation details
│   │   ├── BUILD.bazel
│   │   ├── providers.bzl      # Custom providers
│   │   ├── py_binary.bzl      # py_binary implementation
│   │   ├── py_library.bzl     # py_library implementation
│   │   ├── py_pex_binary.bzl  # PEX format support
│   │   ├── py_pytest_main.bzl # pytest main generation
│   │   ├── py_unpacked_wheel.bzl  # Wheel extraction
│   │   ├── py_image_layer.bzl # OCI image layer support
│   │   ├── py_semantics.bzl   # Shared semantics/utilities
│   │   ├── transitions.bzl    # Python version transitions
│   │   ├── virtual.bzl        # Virtual dependency resolution
│   │   │
│   │   ├── py_venv/           # Virtualenv generation
│   │   │   ├── BUILD.bazel
│   │   │   ├── defs.bzl
│   │   │   ├── py_venv.bzl
│   │   │   └── types.bzl
│   │   │
│   │   ├── toolchain/         # Toolchain implementations
│   │   │   ├── BUILD.bazel
│   │   │   ├── autodetecting.bzl
│   │   │   ├── repo.bzl
│   │   │   ├── tools.bzl
│   │   │   └── types.bzl
│   │   │
│   │   └── release/           # Version and integrity management
│   │       ├── version.bzl
│   │       └── integrity.bzl
│   │
│   ├── tools/                 # Native Rust tools
│   │   ├── BUILD.bazel
│   │   ├── py/                # Core Python library (Rust)
│   │   │   ├── Cargo.toml
│   │   │   └── src/
│   │   │       ├── lib.rs
│   │   │       ├── venv.rs
│   │   │       ├── pth.rs
│   │   │       ├── interpreter.rs
│   │   │       └── unpack.rs
│   │   ├── venv_bin/          # Virtualenv creation tool
│   │   │   ├── Cargo.toml
│   │   │   └── src/main.rs
│   │   ├── unpack_bin/        # Wheel unpacking tool
│   │   │   ├── Cargo.toml
│   │   │   └── src/main.rs
│   │   ├── venv_shim/         # Virtualenv activation helper
│   │   │   ├── Cargo.toml
│   │   │   └── src/main.rs
│   │   ├── runfiles/          # Bazel runfiles library
│   │   │   ├── Cargo.toml
│   │   │   └── src/lib.rs
│   │   └── pex/               # PEX support tools
│   │       └── BUILD.bazel
│   │
│   ├── tests/                 # Test suites
│   │   ├── BUILD.bazel
│   │   ├── external-deps/     # External dependency tests
│   │   ├── import-pathing/    # Import path tests
│   │   ├── py_pex_binary_test/
│   │   ├── virtual/           # Virtual dependency tests
│   │   └── ...
│   │
│   └── unstable/              # Experimental/unstable APIs
│       └── defs.bzl
│
├── uv/                         # uv dependency management system
│   ├── BUILD.bazel
│   │
│   ├── private/               # Private uv implementation
│   │   ├── BUILD.bazel
│   │   ├── defs.bzl           # Core definitions
│   │   ├── extension.bzl      # Main uv module extension
│   │   ├── normalize_name.bzl # Package name normalization
│   │   ├── parse_whl_name.bzl # Wheel filename parsing
│   │   ├── sha1.bzl           # SHA1 hashing utilities
│   │   │
│   │   ├── host/              # Host platform detection
│   │   │   ├── BUILD.bazel
│   │   │   ├── extension.bzl
│   │   │   └── repository.bzl
│   │   │
│   │   ├── tomltool/          # TOML parsing (Rust binary)
│   │   │   ├── BUILD.bazel
│   │   │   ├── extension.bzl
│   │   │   └── toml.bzl
│   │   │
│   │   ├── venv_hub/          # Per-venv repository generation
│   │   │   ├── BUILD.bazel
│   │   │   └── repository.bzl
│   │   │
│   │   ├── hub/               # Multi-venv hub repository
│   │   │   └── repository.bzl
│   │   │
│   │   ├── whl_install/       # Wheel installation rule
│   │   │   ├── BUILD.bazel
│   │   │   ├── defs.bzl
│   │   │   ├── rule.bzl
│   │   │   └── repository.bzl
│   │   │
│   │   ├── sdist_build/       # Source distribution building
│   │   │   └── repository.bzl
│   │   │
│   │   ├── constraints/       # Platform/Python constraints
│   │   │   ├── BUILD.bazel
│   │   │   ├── defs.bzl
│   │   │   ├── repository.bzl
│   │   │   ├── platform/      # Platform constraints (os, cpu)
│   │   │   ├── python/        # Python version constraints
│   │   │   ├── abi/           # ABI tag constraints
│   │   │   └── venv/          # Venv selection
│   │   │
│   │   ├── py_entrypoint_binary/  # Entrypoint binary generation
│   │   │   ├── BUILD.bazel
│   │   │   └── defs.bzl
│   │   │
│   │   ├── manifest/          # Manifest generation
│   │   │   ├── BUILD.bazel
│   │   │   └── defs.bzl
│   │   │
│   │   └── uv/                # uv CLI wrapper
│   │       ├── BUILD.bazel
│   │       └── defs.bzl
│   │
│   └── unstable/              # Unstable uv APIs
│       └── extension.bzl      # Public extension API
│
├── examples/                   # Example projects demonstrating features
│   ├── py_binary/             # Basic py_binary usage
│   ├── py_test/               # Testing with py_test
│   ├── pytest/                # pytest integration
│   ├── py_venv/               # IDE virtualenv setup
│   ├── py_pex_binary/         # PEX executable creation
│   ├── django/                # Django application example
│   ├── multi_version/         # Multiple Python versions
│   ├── uv_pip_compile/        # uv dependency compilation
│   └── virtual_deps/          # Virtual dependency example
│
├── e2e/                        # End-to-end integration tests
│   ├── BUILD.bazel
│   ├── MODULE.bazel
│   ├── README.md
│   └── cases/                 # Individual test cases
│       ├── cross-repo-610/    # Cross-repository test
│       ├── interpreter-version-541/
│       └── oci/
│
├── third_party/                # Third-party code and licenses
│   └── com.github/
│
└── tools/                      # Workspace tools
    └── e2e/                   # E2E test tooling
        └── BUILD.bazel
```

## Module and Package Organization

### `/py` - Core Python Rules

The heart of rules_py, containing all user-facing Python build rules:

- **Public API** (`defs.bzl`): Exports `py_library`, `py_binary`, `py_test`, and related macros
- **Private implementations** (`private/`): Rule logic, providers, and semantics
- **Toolchains** (`private/toolchain/`): Virtualenv and Python toolchain abstractions
- **Native tools** (`tools/`): High-performance Rust implementations for runtime operations

### `/uv` - Dependency Management

Complete alternative to rules_python's pip.parse():

- **Extension API** (`unstable/extension.bzl`): User-facing bzlmod extension
- **Private implementation** (`private/extension.bzl`): Core lockfile parsing and repository generation
- **Hub system** (`private/hub/`, `private/venv_hub/`): Multi-configuration dependency management
- **Constraints** (`private/constraints/`): Platform, Python version, and ABI selection logic
- **Installation** (`private/whl_install/`, `private/sdist_build/`): Package installation rules

### `/bazel` - Build Infrastructure

Workspace-level configuration and utilities:

- **Platform definitions**: Custom platforms and constraint values
- **Release tooling**: Scripts for creating and publishing releases
- **Rust integration**: Multi-platform Rust binary building

### `/examples` and `/e2e`

- **examples/**: User-friendly demonstrations of common patterns
- **e2e/**: Comprehensive integration tests simulating real-world usage

## Main Source Directories

### `/py/private/` - Rule Implementations

Contains the core rule implementations that differentiate rules_py from rules_python:

- `py_binary.bzl`: Binary launcher generation with virtualenv creation
- `py_library.bzl`: Source collection and import path management
- `py_venv/`: Virtualenv generation for IDE integration
- `transitions.bzl`: Python version selection via transitions

### `/py/tools/` - Rust Tools

Native tools for performance-critical operations:

- **venv_bin**: Creates virtualenvs using uv's virtualenv implementation
- **unpack_bin**: Extracts wheel files into site-packages layout
- **venv_shim**: Provides virtualenv activation and PATH manipulation
- **runfiles**: Locates files in Bazel runfiles tree

All tools use dependencies from the `uv` project for Python ecosystem compatibility.

### `/uv/private/` - Dependency Resolution Engine

Implements the complete dependency resolution and installation pipeline:

1. **extension.bzl**: Parses uv.lock files and creates repository rules
2. **whl_install/**: Selects and installs appropriate wheel for target platform
3. **sdist_build/**: Builds wheels from source distributions when needed
4. **venv_hub/**: Creates per-venv repositories with dependency graphs
5. **hub/**: Aggregates multiple venvs into a single configurable hub
6. **constraints/**: Platform and Python version constraint resolution

## Key Files and Their Roles

### Configuration Files

- **MODULE.bazel**: Bzlmod dependencies and toolchain registration
- **.bazelrc**: Default build flags and CI configuration
- **Cargo.toml**: Rust workspace configuration for native tools
- **uv.lock**: Development dependencies in uv lockfile format

### Core Rule Definitions

- **py/defs.bzl**: Primary user-facing API, exports all public rules and macros
- **py/private/py_binary.bzl**: Template-based launcher generation with virtualenv
- **py/private/virtual.bzl**: Virtual dependency resolution system
- **py/private/providers.bzl**: Custom Bazel providers for Python rules

### Extension Points

- **py/extensions.bzl**: Bzlmod extension for rules_py tooling
- **uv/unstable/extension.bzl**: Public uv extension API (experimental)
- **py/toolchains.bzl**: Helper macros for registering Python toolchains

## Code Organization Patterns

### Layered Architecture

The codebase follows a strict layering:
1. **Toolchain layer** (rules_python): Interpreter and base providers
2. **Rule layer** (rules_py): User-facing rules with new semantics
3. **Extension layer** (uv): Alternative dependency management

### Public vs Private APIs

- Public APIs are in top-level modules (`py/defs.bzl`, `uv/unstable/`)
- Implementation details live in `*/private/` directories
- Clear boundaries prevent accidental API dependencies

### Repository Rule Pattern

The uv system heavily uses repository rules to defer work:
- **Fetch repos**: http_file for downloading wheels/sdists
- **Build repos**: sdist_build for compiling from source
- **Install repos**: whl_install for selecting and unpacking wheels
- **Hub repos**: venv_hub and hub for aggregating dependencies

This pattern enables lazy evaluation and proper caching.
