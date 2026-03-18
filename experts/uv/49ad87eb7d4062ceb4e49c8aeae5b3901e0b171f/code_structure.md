# uv - Code Structure

## Complete Annotated Directory Tree

```
uv/
├── .cargo/                         # Cargo build configuration
│   └── config.toml                # Platform-specific build settings
├── .github/                        # GitHub workflows and CI/CD
│   └── workflows/                 # Automated testing, releases, benchmarks
├── assets/                         # Project assets (badges, logos, images)
├── changelogs/                     # Historical changelog files
├── crates/                         # Rust workspace with 67 crates
│   ├── uv/                        # Main CLI binary crate
│   ├── uv-audit/                  # Security audit functionality
│   ├── uv-auth/                   # HTTP authentication handling
│   ├── uv-bench/                  # Benchmarking utilities
│   ├── uv-bin-install/            # Binary installation for tools
│   ├── uv-build/                  # Build utilities
│   ├── uv-build-backend/          # PEP 517 build backend implementation
│   ├── uv-build-frontend/         # PEP 517 build frontend
│   ├── uv-cache/                  # Global cache management
│   ├── uv-cache-info/             # Cache information types
│   ├── uv-cache-key/              # Cache key generation
│   ├── uv-cli/                    # CLI argument parsing (clap-based)
│   ├── uv-client/                 # HTTP client for PyPI APIs
│   ├── uv-configuration/          # Configuration types and parsing
│   ├── uv-console/                # Terminal output formatting
│   ├── uv-dev/                    # Development utilities
│   ├── uv-dirs/                   # Directory path resolution
│   ├── uv-dispatch/               # Build/resolve dispatch coordination
│   ├── uv-distribution/           # Distribution download and metadata
│   ├── uv-distribution-filename/  # Wheel/sdist filename parsing
│   ├── uv-distribution-types/     # Distribution type abstractions
│   ├── uv-extract/                # Archive extraction (tar, zip)
│   ├── uv-flags/                  # Feature flags
│   ├── uv-fs/                     # Filesystem utilities
│   ├── uv-git/                    # Git repository interaction
│   ├── uv-git-types/              # Git-related types
│   ├── uv-globfilter/             # Glob pattern filtering
│   ├── uv-installer/              # Package installation orchestration
│   ├── uv-install-wheel/          # Wheel installation into venv
│   ├── uv-keyring/                # OS keyring integration
│   ├── uv-logging/                # Logging and tracing
│   ├── uv-macros/                 # Procedural macros
│   ├── uv-metadata/               # Package metadata extraction
│   ├── uv-normalize/              # Package name normalization
│   ├── uv-once-map/               # Concurrent task deduplication
│   ├── uv-options-metadata/       # CLI options metadata
│   ├── uv-pep440/                 # PEP 440 version parsing
│   ├── uv-pep508/                 # PEP 508 dependency specifiers
│   ├── uv-performance-memory-allocator/ # Custom memory allocators
│   ├── uv-platform/               # Platform detection
│   ├── uv-platform-tags/          # PEP 425 platform tag generation
│   ├── uv-preview/                # Preview feature flags
│   ├── uv-publish/                # Package publishing to PyPI
│   ├── uv-pypi-types/             # PyPI API type definitions
│   ├── uv-python/                 # Python interpreter detection/management
│   ├── uv-redacted/               # Sensitive data redaction
│   ├── uv-requirements/           # Requirements parsing
│   ├── uv-requirements-txt/       # requirements.txt parser
│   ├── uv-resolver/               # PubGrub dependency resolver
│   ├── uv-scripts/                # Script execution support
│   ├── uv-settings/               # Settings and configuration
│   ├── uv-shell/                  # Shell detection and manipulation
│   ├── uv-small-str/              # Small string optimization
│   ├── uv-state/                  # Application state management
│   ├── uv-static/                 # Static data and environment vars
│   ├── uv-test/                   # Testing utilities
│   ├── uv-tool/                   # Tool management (pipx-like)
│   ├── uv-torch/                  # PyTorch-specific handling
│   ├── uv-trampoline/             # Windows executable trampolines
│   ├── uv-trampoline-builder/     # Trampoline builder utilities
│   ├── uv-types/                  # Shared trait definitions
│   ├── uv-unix/                   # Unix-specific functionality
│   ├── uv-version/                # Version information
│   ├── uv-virtualenv/             # Virtual environment creation
│   ├── uv-warnings/               # User-facing warnings
│   ├── uv-windows/                # Windows-specific functionality
│   └── uv-workspace/              # Workspace management
├── docs/                           # MkDocs documentation
│   ├── concepts/                  # Conceptual documentation
│   ├── getting-started/           # Getting started guides
│   ├── guides/                    # How-to guides
│   ├── pip/                       # pip interface documentation
│   └── reference/                 # Reference documentation
├── python/                         # Python source for maturin build
├── scripts/                        # Development and build scripts
├── test/                          # Integration test fixtures
├── Cargo.toml                     # Workspace manifest
├── Cargo.lock                     # Dependency lock file
├── pyproject.toml                 # Python package metadata (maturin)
├── uv.lock                        # uv project lock file
├── mkdocs.yml                     # Documentation site configuration
├── README.md                      # Project README
├── CONTRIBUTING.md                # Contribution guidelines
├── BENCHMARKS.md                  # Performance benchmarks
├── CHANGELOG.md                   # Release changelog
├── STYLE.md                       # Code style guide
├── SECURITY.md                    # Security policy
└── LICENSE-{MIT,APACHE}          # Dual license files
```

## Module and Package Organization

### Workspace Structure

uv is organized as a Cargo workspace with 67 member crates, following a modular architecture where each crate has a single, well-defined responsibility. The workspace uses path dependencies to enable tight integration while maintaining clear boundaries.

**Workspace Configuration** (`Cargo.toml`):
- Defines workspace members in `crates/*` (excluding special crates like `uv-trampoline`)
- Sets common metadata (edition = "2024", rust-version = "1.92.0")
- Declares workspace-level dependencies with version pinning
- Configures lints (clippy pedantic warnings, unsafe code warnings)
- Defines build profiles (release, profiling, fast-build, no-debug, minimal-size, dist)

### Crate Categories

**1. Core Functionality Crates:**
- `uv`: Main binary with CLI implementation and command orchestration
- `uv-cli`: Command-line interface definitions using clap
- `uv-resolver`: PubGrub-based dependency resolution engine
- `uv-installer`: High-level package installation orchestration
- `uv-dispatch`: Coordination layer for build and resolve operations

**2. Python Standards Implementation:**
- `uv-pep440`: Version specifiers (PEP 440)
- `uv-pep508`: Dependency specifiers (PEP 508)
- `uv-platform-tags`: Platform tags (PEP 425)
- `uv-build-frontend`: Build frontend (PEP 517)
- `uv-build-backend`: Build backend (PEP 517)

**3. Distribution Management:**
- `uv-distribution`: Download and metadata extraction
- `uv-distribution-types`: Type definitions for wheels/sdists
- `uv-distribution-filename`: Filename parsing
- `uv-install-wheel`: Low-level wheel installation
- `uv-extract`: Archive extraction utilities

**4. Network and Caching:**
- `uv-client`: HTTP client for PyPI and indexes
- `uv-cache`: Global cache implementation
- `uv-cache-key`: Cache key generation
- `uv-cache-info`: Cache metadata types
- `uv-auth`: Authentication and credentials

**5. Python Environment Management:**
- `uv-python`: Python interpreter detection and management
- `uv-virtualenv`: Virtual environment creation
- `uv-tool`: Tool installation and management
- `uv-scripts`: Script execution support

**6. Configuration and Settings:**
- `uv-settings`: Configuration file parsing
- `uv-configuration`: Configuration types
- `uv-workspace`: Workspace and pyproject.toml handling
- `uv-requirements`: Requirements parsing
- `uv-requirements-txt`: requirements.txt specific parsing

**7. Platform Support:**
- `uv-platform`: Platform detection
- `uv-unix`: Unix-specific code
- `uv-windows`: Windows-specific code
- `uv-fs`: Cross-platform filesystem utilities
- `uv-shell`: Shell detection and manipulation

**8. Infrastructure and Utilities:**
- `uv-normalize`: Package name normalization
- `uv-once-map`: Concurrent task deduplication
- `uv-types`: Shared traits
- `uv-console`: Terminal output
- `uv-logging`: Logging infrastructure
- `uv-warnings`: User-facing warnings
- `uv-redacted`: Sensitive data redaction
- `uv-macros`: Procedural macros
- `uv-small-str`: String optimization

**9. Specialized Features:**
- `uv-audit`: Security vulnerability auditing
- `uv-publish`: Package publishing
- `uv-torch`: PyTorch-specific optimizations
- `uv-git`: Git repository interaction
- `uv-keyring`: OS keyring integration
- `uv-preview`: Preview feature management

**10. Development and Testing:**
- `uv-dev`: Development utilities
- `uv-bench`: Benchmarking tools
- `uv-test`: Test utilities and helpers

## Main Source Directories and Their Purposes

### `/crates/uv/src/` - Main Binary

```
src/
├── bin/                    # Binary entry points
│   ├── uv.rs              # Main uv binary
│   └── uvw.rs             # Windows GUI variant
├── commands/               # Command implementations
│   ├── auth/              # Authentication commands
│   ├── pip/               # pip-compatible interface commands
│   │   ├── compile.rs     # pip compile
│   │   ├── install.rs     # pip install
│   │   ├── sync.rs        # pip sync
│   │   ├── list.rs        # pip list
│   │   ├── show.rs        # pip show
│   │   ├── freeze.rs      # pip freeze
│   │   ├── uninstall.rs   # pip uninstall
│   │   ├── tree.rs        # pip tree
│   │   └── operations.rs  # Shared operations
│   ├── project/           # Project management commands
│   │   ├── init.rs        # uv init
│   │   ├── add.rs         # uv add
│   │   ├── remove.rs      # uv remove
│   │   ├── lock.rs        # uv lock
│   │   ├── sync.rs        # uv sync
│   │   ├── run.rs         # uv run
│   │   ├── tree.rs        # uv tree
│   │   ├── export.rs      # uv export
│   │   └── mod.rs         # Project operations
│   ├── python/            # Python version management
│   ├── tool/              # Tool management (pipx-like)
│   ├── workspace/         # Workspace commands
│   ├── venv.rs            # Virtual environment creation
│   ├── publish.rs         # Package publishing
│   ├── cache_*.rs         # Cache management commands
│   ├── self_update.rs     # Self-update functionality
│   └── mod.rs             # Command dispatcher
├── lib.rs                  # Library exports and shared logic
├── settings.rs             # Settings aggregation (109KB - complex)
├── printer.rs              # Output formatting
├── logging.rs              # Logging setup
└── child.rs                # Child process management
```

### `/crates/uv-resolver/src/` - Dependency Resolution

```
src/
├── pubgrub/                # PubGrub algorithm implementation
├── lock/                   # Lockfile generation and management
├── resolver/               # Main resolver logic
├── candidate_selector.rs   # Version selection
├── dependency_provider.rs  # Dependency provider trait
├── error.rs                # Resolution errors
├── manifest.rs             # Dependency manifests
├── preferences.rs          # Version preferences
├── prerelease.rs           # Pre-release handling
├── exclusions.rs           # Package exclusions
├── fork_strategy.rs        # Resolution forking
└── lib.rs                  # Public API
```

### `/crates/uv-installer/src/` - Installation

Core package installation orchestration that coordinates between resolver, downloader, and wheel installer.

### `/crates/uv-client/src/` - HTTP Client

PyPI and package index HTTP client with authentication, retries, and caching headers.

### `/crates/uv-python/src/` - Python Management

Python interpreter discovery, installation, version management, and environment detection.

## Key Files and Their Roles

### Root Configuration Files

**`Cargo.toml`** (16KB):
- Workspace manifest defining all 67 member crates
- Centralized dependency version management
- Build profiles (release with LTO, profiling without LTO)
- Clippy lint configuration
- Cross-crate dependency declarations

**`pyproject.toml`** (3.8KB):
- Python package metadata for PyPI distribution
- Maturin build configuration
- Bindings type: "bin" (ships compiled Rust binary)
- Module name and build manifest path
- Rooster changelog configuration

**`uv.lock`** (171KB):
- uv's own dependency lockfile
- Demonstrates dogfooding of uv's lockfile format
- Pins exact versions for reproducible builds

**`Cargo.lock`** (190KB):
- Rust dependency lockfile
- Ensures reproducible Rust builds

**`mkdocs.yml`** (11KB):
- Documentation site configuration
- Navigation structure
- Material theme customization
- Plugin configuration (search, redirects, git revision dates)

### Build and Development Files

**`rust-toolchain.toml`**:
- Specifies exact Rust toolchain version
- Ensures consistent builds across environments

**`clippy.toml`** (2.2KB):
- Clippy linter configuration
- Project-specific lint rules

**`rustfmt.toml`**:
- Rust code formatting rules

**`.cargo/config.toml`**:
- Platform-specific build configuration
- Target-specific settings

**`dist-workspace.toml`** (3.9KB):
- cargo-dist configuration for releases
- Binary distribution settings

### Main Entry Points

**`crates/uv/src/bin/uv.rs`**:
- Main binary entry point
- Parses CLI arguments via uv-cli
- Dispatches to command handlers
- Sets up logging and error handling

**`crates/uv/src/lib.rs`** (109KB):
- Core library functionality
- Command implementations
- Shared utilities
- Re-exports for public API

**`crates/uv-cli/src/lib.rs`**:
- CLI structure definition using clap
- Subcommand enums and argument structs
- Global options and flags
- Custom value parsers

### Critical Implementation Files

**`crates/uv/src/settings.rs`** (152KB):
- Massive settings aggregation and resolution
- Combines CLI args, config files, env vars
- Per-command setting structures
- Complex precedence logic

**`crates/uv-resolver/src/resolver.rs`**:
- Main dependency resolution algorithm
- PubGrub integration
- Fork handling for conflicting requirements

**`crates/uv-installer/src/plan.rs`**:
- Installation plan generation
- Determines what to install/uninstall/upgrade

**`crates/uv-distribution/src/source/mod.rs`**:
- Distribution download orchestration
- Metadata extraction from wheels/sdists

**`crates/uv-python/src/discovery.rs`**:
- Python interpreter discovery
- Version detection and validation

## Code Organization Patterns

### Layered Architecture

1. **CLI Layer** (`uv`, `uv-cli`): User interface and command parsing
2. **Command Layer** (`uv/src/commands/*`): Business logic for each command
3. **Orchestration Layer** (`uv-dispatch`, `uv-installer`): High-level coordination
4. **Core Services** (`uv-resolver`, `uv-distribution`, `uv-python`): Domain logic
5. **Infrastructure** (`uv-client`, `uv-cache`, `uv-fs`): Low-level utilities
6. **Standards** (`uv-pep440`, `uv-pep508`, etc.): Python spec implementations

### Dependency Flow

- Upper layers depend on lower layers
- Cross-cutting concerns handled by shared crates (`uv-types`, `uv-fs`, `uv-logging`)
- No circular dependencies due to careful trait-based design
- Traits defined in `uv-types` to break cycles

### Testing Structure

- Unit tests in each crate's `src/` alongside code
- Integration tests in crate-level `tests/` directories
- Snapshot testing via insta crate
- Test utilities in `uv-test` crate
- Large integration test suite in main `uv` crate
- Test fixtures in `/test` directory

### Documentation Structure

- Inline doc comments (`///`) for API documentation
- Crate-level documentation in `lib.rs` or `README.md`
- User documentation in `/docs` using MkDocs
- Contributing guide, benchmarks, changelog at root
- Per-crate README for public crates
