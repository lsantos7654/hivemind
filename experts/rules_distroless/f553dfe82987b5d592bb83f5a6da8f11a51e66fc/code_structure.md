# rules_distroless Code Structure

## Complete Annotated Directory Tree

```
rules_distroless/
├── .aspect/                    # Aspect Workflows CI configuration
├── .bazelignore               # Bazel ignore patterns
├── .bazelrc                   # Bazel configuration flags
├── .bazelversion              # Required Bazel version (6.0+)
├── .bcr/                      # Bazel Central Registry metadata
│   ├── metadata.template.json # BCR package metadata
│   ├── source.template.json   # BCR source info
│   └── presubmit.yml          # BCR presubmit tests
├── .github/
│   └── workflows/             # GitHub Actions CI/CD
│       ├── ci.yaml            # Continuous integration
│       ├── release.yaml       # Release automation
│       ├── publish.yaml       # Publish to BCR
│       └── tag.yaml           # Version tagging
├── apt/                       # APT package management module
│   ├── BUILD.bazel            # Public visibility definitions
│   ├── defs.bzl               # Public API exports (dpkg_status, dpkg_statusd)
│   ├── apt.bzl                # Legacy WORKSPACE macro
│   ├── extensions.bzl         # Bzlmod module extension
│   ├── private/               # Private implementation details
│   │   ├── BUILD.bazel        # Shell script exports
│   │   ├── apt_deb_repository.bzl      # Repository metadata fetching
│   │   ├── apt_dep_resolver.bzl        # Dependency resolution algorithm
│   │   ├── deb_import.bzl              # .deb package import
│   │   ├── deb_resolve.bzl             # Manifest parsing & resolution
│   │   ├── deb_translate_lock.bzl      # Lockfile to BUILD translation
│   │   ├── deb_postfix.bzl             # Package postprocessing
│   │   ├── dpkg_status.bzl             # /var/lib/dpkg/status creation
│   │   ├── dpkg_status.sh              # dpkg_status implementation
│   │   ├── dpkg_statusd.bzl            # /var/lib/dpkg/status.d/ creation
│   │   ├── dpkg_statusd.sh             # dpkg_statusd implementation
│   │   ├── lockfile.bzl                # Lockfile data structure
│   │   ├── version.bzl                 # Debian version parsing
│   │   ├── version_constraint.bzl      # Version constraint parsing
│   │   ├── util.bzl                    # Utility functions
│   │   ├── starlark_codegen_utils.bzl  # Code generation helpers
│   │   ├── package.BUILD.tmpl          # Template for generated BUILD files
│   │   └── copy.sh.tmpl                # Template for copy scripts
│   └── tests/                 # APT module tests
│       ├── BUILD.bazel
│       ├── resolution_test.bzl         # Resolution test framework
│       ├── version_test.bzl            # Version parsing tests
│       └── resolution/                 # Test manifests
│           ├── clang.yaml
│           ├── security.yaml
│           ├── dependencies.yaml
│           ├── arch_all.yaml
│           └── empty.lock.json
├── distroless/                # System file generation module
│   ├── BUILD.bazel            # Public visibility
│   ├── defs.bzl               # Public API exports (all rules)
│   ├── dependencies.bzl       # External dependencies setup
│   ├── toolchains.bzl         # Toolchain registration
│   ├── private/               # Private implementation
│   │   ├── BUILD.bazel        # Script and Java file exports
│   │   ├── passwd.bzl         # /etc/passwd creation
│   │   ├── group.bzl          # /etc/group creation
│   │   ├── home.bzl           # Home directory creation
│   │   ├── cacerts.bzl        # CA certificate bundling
│   │   ├── cacerts.sh         # Certificate extraction script
│   │   ├── java_keystore.bzl  # Java keystore creation
│   │   ├── JavaKeyStore.java  # Java keystore utility
│   │   ├── locale.bzl         # Locale stripping
│   │   ├── locale.sh          # Locale extraction script
│   │   ├── os_release.bzl     # /etc/os-release creation
│   │   ├── flatten.bzl        # Tar archive flattening
│   │   ├── flatten.sh         # Flatten implementation
│   │   ├── tar.bzl            # Tar utilities & mtree builder
│   │   └── util.bzl           # Utility functions
│   └── tests/                 # Distroless module tests
│       ├── BUILD.bazel
│       └── asserts.bzl        # Test assertion helpers
├── examples/                  # Usage examples
│   ├── debian_snapshot/       # Debian snapshot example
│   │   ├── BUILD.bazel
│   │   ├── bullseye.yaml      # Package manifest
│   │   └── bullseye.lock.json # Lockfile
│   ├── ubuntu_snapshot/       # Ubuntu snapshot example
│   │   ├── BUILD.bazel
│   │   ├── noble.yaml
│   │   └── noble.lock.json
│   ├── group/                 # Group file example
│   ├── passwd/                # Passwd file example
│   ├── home/                  # Home directory example
│   ├── cacerts/               # CA certificates example
│   ├── java_keystore/         # Java keystore example
│   ├── locale/                # Locale example
│   ├── os_release/            # OS release example
│   ├── flatten/               # Flatten example
│   └── statusd/               # dpkg status.d example
├── e2e/                       # End-to-end tests
│   └── smoke/                 # Smoke tests
│       └── BUILD
├── BUILD.bazel                # Root build file
├── MODULE.bazel               # Bzlmod module definition
├── WORKSPACE                  # Legacy WORKSPACE (empty)
├── README.md                  # Project documentation
├── CONTRIBUTING.md            # Contribution guidelines
├── SECURITY.md                # Security policy
└── LICENSE                    # Apache 2.0 license
```

## Module and Package Organization

### APT Module (`apt/`)

The APT module is organized into three layers:

**Public API Layer:**
- `defs.bzl`: Exports public rules (`dpkg_status`, `dpkg_statusd`)
- `apt.bzl`: Legacy macro for WORKSPACE users
- `extensions.bzl`: Modern Bzlmod extension entry point

**Private Implementation Layer (`apt/private/`):**
All implementation details are hidden in the private directory:
- **Repository Rules**: `deb_resolve.bzl`, `deb_import.bzl`, `deb_translate_lock.bzl`
- **Data Structures**: `lockfile.bzl`, `apt_deb_repository.bzl`
- **Algorithms**: `apt_dep_resolver.bzl`, `version.bzl`, `version_constraint.bzl`
- **Utilities**: `util.bzl`, `starlark_codegen_utils.bzl`
- **Shell Scripts**: `dpkg_status.sh`, `dpkg_statusd.sh`

**Test Layer (`apt/tests/`):**
- Unit tests for version parsing and resolution
- Integration tests with various package manifests

### Distroless Module (`distroless/`)

The distroless module follows a similar pattern:

**Public API Layer:**
- `defs.bzl`: Exports all public rules (8 rules total)
- `dependencies.bzl`: Helper for setting up dependencies
- `toolchains.bzl`: Toolchain registration

**Private Implementation Layer (`distroless/private/`):**
Each system file type has its own rule:
- **User Management**: `passwd.bzl`, `group.bzl`, `home.bzl`
- **Security**: `cacerts.bzl`, `java_keystore.bzl`
- **Localization**: `locale.bzl`
- **System Info**: `os_release.bzl`
- **Archive Utilities**: `flatten.bzl`, `tar.bzl`

**Shared Infrastructure:**
- `tar.bzl`: Provides mtree builder and tar utilities used by all rules
- `util.bzl`: Common helper functions

### Examples Directory (`examples/`)

Each subdirectory demonstrates a specific feature with:
- `BUILD.bazel`: Working example build file
- Supporting files (YAML manifests, lockfiles, etc.)
- Often used in integration tests

## Main Source Directories and Their Purposes

### `/apt` - Package Management
Primary purpose: Fetch, resolve, and import Debian/Ubuntu packages

**Key Responsibilities:**
- Parse YAML manifests specifying packages
- Fetch repository metadata (Packages, Release files)
- Resolve package dependencies
- Generate lockfiles for reproducibility
- Import .deb files as Bazel targets

**Entry Points:**
- Bzlmod users: `use_extension("@rules_distroless//apt:extensions.bzl", "apt")`
- WORKSPACE users: `load("@rules_distroless//apt:apt.bzl", "apt")`

### `/distroless` - System File Generation
Primary purpose: Create Linux system files from scratch

**Key Responsibilities:**
- Generate passwd, group, os-release files
- Create filesystem structures (home directories)
- Process security certificates
- Manipulate tar archives
- Strip and optimize locale data

**Entry Points:**
- `load("@rules_distroless//distroless:defs.bzl", "passwd", "group", ...)`

### `/examples` - Documentation and Testing
Primary purpose: Living documentation and integration tests

Shows complete workflows:
1. Define packages in YAML
2. Generate lockfiles
3. Use packages in builds
4. Create system files
5. Combine into images

## Key Files and Their Roles

### Core Configuration Files

**MODULE.bazel** (4KB)
- Defines the `rules_distroless` Bazel module
- Lists all dependencies with versions
- Sets up toolchain extensions (yq, tar, zstd)
- Includes example repositories for testing

**BUILD.bazel** (Root)
- Minimal root build file
- Exports license and documentation

**.bazelrc** (2KB)
- Bazel build flags and settings
- CI configuration overrides
- Platform-specific settings

### Critical Implementation Files

**apt/extensions.bzl** (210 lines)
- Main entry point for Bzlmod users
- Implements `_distroless_extension` module extension
- Defines `install` tag class with attributes
- Orchestrates package resolution and import

**apt/private/deb_resolve.bzl** (300+ lines)
- Repository rule for dependency resolution
- Parses YAML manifests using yq
- Calls dependency resolver
- Generates lockfiles

**apt/private/apt_dep_resolver.bzl**
- Core dependency resolution algorithm
- Handles version constraints
- Resolves transitive dependencies
- Manages architecture-specific packages

**distroless/private/tar.bzl**
- Mtree builder for tar archives
- Creates filesystem entries with permissions
- Used by all distroless rules
- Abstracts tar toolchain

## Code Organization Patterns

### Separation of Public and Private APIs

The codebase strictly separates public and private APIs:
- Public: `defs.bzl`, `apt.bzl`, `extensions.bzl`
- Private: Everything in `private/` directories

This allows implementation changes without breaking users.

### Repository Rule Pattern

Package resolution uses Bazel repository rules:
1. `deb_resolve`: Resolves dependencies, creates lockfile
2. `deb_translate_lock`: Translates lockfile to BUILD files
3. `deb_import`: Downloads individual .deb packages

This enables lazy fetching and proper caching.

### Shell Script Integration

Complex operations use shell scripts:
- Written in portable POSIX shell
- Invoked via `ctx.actions.run()`
- Use toolchains (bsdtar, gawk) instead of assuming system tools
- Templates end in `.tmpl` for codegen

### Mtree-Based Archive Creation

All tar creation uses mtree specifications:
```starlark
mtree = tar_lib.create_mtree()
mtree.add_dir("/etc", mode = "0755")
mtree.entry("/etc/passwd", "file", content = "...")
tar(name = "output", mtree = mtree.content())
```

This ensures:
- Reproducible builds (fixed timestamps, permissions)
- Proper ordering
- Correct ownership

### Test Organization

Tests follow Bazel conventions:
- Unit tests: Starlark analysis tests
- Integration tests: Real package resolution
- E2E tests: Full workflows
- Examples serve as integration tests

The structure promotes modularity, testability, and maintainability while following Bazel best practices.
