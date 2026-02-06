# Distroless Code Structure

## Complete Annotated Directory Tree

```
distroless/
├── .bazelrc                      # Bazel configuration (remote cache, build flags)
├── .bazelversion                 # Pinned Bazel version (currently 8.0)
├── .bazelignore                  # Directories excluded from Bazel scanning
├── MODULE.bazel                  # Bzlmod module definition and dependencies
├── MODULE.bazel.lock             # Dependency lock file
├── WORKSPACE                     # Legacy Bazel workspace file (minimal)
├── BUILD                         # Root BUILD file defining all image tags and push targets
├── distro.bzl                    # Architecture variant definitions (arm v7/v8)
├── knife                         # CLI utility for package updates and testing
├── knife.d/                      # Supporting scripts for knife utility
│   ├── update_java_versions.sh  # Java package version updater
│   ├── update_java_archives.sh  # Java distribution archive generator
│   └── update_node_archives.js  # Node.js archive updater
│
├── common/                       # Shared configuration and assets
│   ├── BUILD.bazel              # Common file tarballs (passwd, group, tmp, etc.)
│   ├── variables.bzl            # Shared constants (UIDs, OS release info)
│   ├── passwd                   # User database file (root, nobody, nonroot)
│   ├── group                    # Group database file
│   ├── nsswitch.conf            # Name service switch configuration
│   └── os_release_debian*.yaml  # OS release file templates per distro
│
├── static/                       # Minimal static binary base images
│   ├── BUILD                    # Image targets for all variants
│   ├── static.bzl               # Image construction macros
│   ├── config.bzl               # Package lists and architecture configs
│   ├── nsswitch.conf            # Static image-specific nsswitch
│   └── testdata/                # Container structure tests
│       ├── static.yaml          # Tests for static image contents
│       ├── debug.yaml           # Tests for busybox presence
│       ├── debian12.yaml        # Debian 12 OS release tests
│       ├── debian13.yaml        # Debian 13 OS release tests
│       └── check_certs.go       # Certificate validation test binary
│
├── base/                        # Base images with glibc and OpenSSL
│   ├── BUILD                    # Image targets for base/base-nossl variants
│   ├── base.bzl                 # Image construction macros
│   ├── config.bzl               # Package lists (with/without SSL)
│   ├── test.sh                  # Integration test script
│   ├── README.md                # Base image documentation
│   └── testdata/                # Container structure tests
│       ├── base.yaml            # Standard base image tests
│       └── debug.yaml           # Debug variant tests
│
├── cc/                          # C/C++ runtime images
│   ├── BUILD                    # C++ image targets
│   ├── cc.bzl                   # Image construction macros
│   ├── config.bzl               # C++ runtime package lists (libgcc, libstdc++)
│   └── README.md                # C++ image documentation
│
├── java/                        # Java runtime images
│   ├── BUILD                    # Java image targets (base, versions 17/21/25)
│   ├── java.bzl                 # Image construction macros
│   ├── config.bzl               # Java package lists per distro
│   ├── jre_ver.bzl              # Java version metadata utilities
│   └── README.md                # Java image usage documentation
│
├── python3/                     # Python 3 runtime images
│   ├── BUILD                    # Python image targets
│   ├── python.bzl               # Image construction macros
│   ├── config.bzl               # Python package lists
│   └── README.md                # Python image documentation
│
├── nodejs/                      # Node.js runtime images
│   ├── BUILD                    # Node.js image targets (v20/22/24)
│   ├── nodejs.bzl               # Image construction macros
│   ├── config.bzl               # Node.js version and architecture configs
│   └── README.md                # Node.js image documentation
│
├── private/                     # Internal implementation details
│   ├── stamp.bash               # Build stamping utilities
│   ├── extensions/              # Bazel module extensions
│   │   ├── busybox.bzl         # Busybox download extension
│   │   └── node.bzl            # Node.js download extension
│   ├── repos/                   # Package repository definitions
│   │   ├── deb/                # Debian package manifests
│   │   │   ├── deb.MODULE.bazel        # Apt repository module extension
│   │   │   ├── bookworm.yaml           # Debian 12 base packages
│   │   │   ├── bookworm.lock.json      # Debian 12 lockfile
│   │   │   ├── bookworm_java.yaml      # Debian 12 Java packages
│   │   │   ├── bookworm_python.yaml    # Debian 12 Python packages
│   │   │   ├── trixie.yaml             # Debian 13 base packages
│   │   │   ├── trixie.lock.json        # Debian 13 lockfile
│   │   │   ├── trixie_adoptium.yaml    # Debian 13 Adoptium repo
│   │   │   ├── trixie_java.yaml        # Debian 13 Java packages
│   │   │   └── package.BUILD.tmpl      # Package BUILD template
│   │   └── java_temurin/       # Eclipse Temurin Java distributions
│   │       └── java.MODULE.bazel       # Temurin archive module
│   ├── oci/                     # OCI image construction utilities
│   │   ├── defs.bzl            # Public API (java_image, go_image, etc.)
│   │   ├── java_image.bzl      # Java-specific image rules
│   │   ├── cc_image.bzl        # C++ image rules
│   │   ├── go_image.bzl        # Go image rules
│   │   ├── rust_image.bzl      # Rust image rules
│   │   ├── sign_and_push.bzl   # Cosign signing and registry push
│   │   └── digest.bzl          # Image digest utilities
│   ├── pkg/                     # Package metadata generation
│   │   ├── debian_spdx.bzl     # SPDX SBOM generation for Debian packages
│   │   └── oci_image_spdx.bzl  # SPDX SBOM generation for images
│   ├── util/                    # Shared utility functions
│   │   ├── deb.bzl             # Debian package label construction
│   │   ├── extract.bzl         # Archive extraction utilities
│   │   ├── java_cacerts.bzl    # Java keystore utilities
│   │   └── merge_providers.bzl # Provider merging helpers
│   └── tools/                   # Build-time tools
│       └── lifecycle/           # Image lifecycle tag management
│           ├── defs.bzl        # Lifecycle tagging rules
│           └── tag.bzl         # Tag attachment logic
│
├── experimental/                # Experimental features
│   └── busybox/                # Busybox integration
│       ├── BUILD               # Busybox tarball targets per architecture
│       └── commands.bzl        # Busybox command extraction
│
├── examples/                    # Usage examples and integration tests
│   ├── BUILD                   # Example build targets
│   ├── go/                     # Go application example
│   │   ├── Dockerfile          # Multi-stage Docker build
│   │   ├── BUILD               # Bazel build configuration
│   │   ├── main.go             # Sample Go application
│   │   └── main_test.go        # Go tests
│   ├── java/                   # Java application example
│   │   ├── Dockerfile          # Multi-stage Docker build
│   │   ├── BUILD               # Bazel build configuration
│   │   ├── HelloJava.java      # Sample Java application
│   │   └── testdata/           # Container structure tests
│   ├── python3/                # Python application example
│   │   ├── Dockerfile          # Multi-stage Docker build
│   │   ├── BUILD               # Bazel build configuration
│   │   └── hello.py            # Sample Python script
│   ├── nodejs/                 # Node.js examples
│   │   ├── Dockerfile          # Multi-stage Docker build
│   │   ├── BUILD               # Bazel build configuration
│   │   ├── hello.js            # Simple Node.js script
│   │   ├── hello_http.js       # HTTP server example
│   │   └── node-express/       # Express.js application example
│   ├── cc/                     # C/C++ examples
│   │   ├── BUILD               # Bazel build configuration
│   │   ├── Dockerfile          # Multi-stage Docker build
│   │   ├── hello.c             # C application
│   │   ├── hello_cc.cc         # C++ application
│   │   └── testdata/           # Container tests
│   ├── rust/                   # Rust example
│   │   └── Dockerfile          # Multi-stage Docker build
│   └── nonroot/                # Non-root user examples
│       └── testdata/           # Non-root user tests
│
├── .github/                     # GitHub configuration
│   ├── workflows/              # CI/CD workflow definitions
│   │   ├── ci.yaml             # Main build and test workflow
│   │   ├── ci.bazelrc          # CI-specific Bazel config
│   │   ├── examples.yaml       # Example testing workflow
│   │   ├── image-check.yaml    # Image validation workflow
│   │   ├── buildifier.yaml     # Starlark linting
│   │   ├── config-diff.yaml    # Configuration diff checking
│   │   ├── update-deb-package-snapshots.yml      # Auto-update Debian snapshots
│   │   ├── update-deb-package-non-snapshots.yml  # Auto-update Debian current
│   │   ├── update-node-archives.yml              # Auto-update Node.js versions
│   │   ├── update-temurin-packages.yml           # Auto-update Java Temurin
│   │   └── scorecards-analysis.yml               # OpenSSF Scorecard
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   │   ├── actionable-debian-cve.md       # Debian CVE reports
│   │   ├── actionable-non-debian-cve.md   # Non-Debian CVE reports
│   │   └── bug_report.md                  # General bug reports
│   └── dependabot.yml          # Dependabot configuration
│
├── .cloudbuild/                # Cloud Build configuration
│   ├── cloudbuild.yaml         # Main build pipeline
│   ├── lifecycle_tag.yaml      # Lifecycle tagging pipeline
│   ├── lifecycle_tag.sh        # Lifecycle tagging script
│   └── release.sh              # Release script
│
├── cosign.pub                  # Cosign public key (legacy)
├── LICENSE                     # Apache 2.0 license
├── README.md                   # Main documentation
├── CONTRIBUTING.md             # Contribution guidelines
├── PACKAGE_METADATA.md         # dpkg metadata structure documentation
├── RELEASES.md                 # Release process documentation
├── SUPPORT_POLICY.md           # Image support lifecycle policy
├── SECURITY.md                 # Security disclosure policy
├── .pre-commit-config.yaml     # Pre-commit hook configuration
└── .travis.yml                 # Travis CI configuration (legacy)
```

## Module and Package Organization

**Top-Level Organization**: The repository follows a Bazel monorepo pattern with language-specific packages (base/, cc/, java/, python3/, nodejs/, static/) that are siblings to shared infrastructure (common/, private/, experimental/).

**Image Type Separation**: Each image type lives in its own package with consistent structure:
- `BUILD` - Defines all image targets using comprehensions
- `*.bzl` - Contains Starlark macros for image construction
- `config.bzl` - Declares package lists, architectures, and distros
- `README.md` - Usage documentation
- `testdata/` - Container structure test configurations

**Private Implementation**: The `private/` directory encapsulates internal implementation details not intended for external consumption, including Bazel module extensions, package repository definitions, utility functions, and build tools.

## Main Source Directories and Their Purposes

**`static/`**: Foundation layer for all other images. Builds minimal images containing only base-files, timezone data, CA certificates, and essential system files. Does not include glibc or any dynamic libraries - suitable only for statically-linked binaries.

**`base/`**: Adds glibc, OpenSSL (libssl3), and essential runtime libraries on top of static images. Includes `base-nossl` variant for applications that don't need TLS. Primary target for dynamically-linked applications without specific runtime dependencies.

**`cc/`**: Extends base images with C++ standard library (libstdc++), libgcc, and C runtime components. Target for C/C++ compiled applications requiring standard library support.

**`java/`**: Provides Java runtime environments. Includes `java-base` (just OpenJDK JRE libraries) and versioned images (`java17`, `java21`, `java25`) with complete JDK distributions from Eclipse Adoptium (Temurin) or Debian packages.

**`python3/`**: Python 3 runtime images including interpreter, standard library, and essential Python packages. Based on Debian's python3 packages.

**`nodejs/`**: Node.js runtime images with specific major versions (20, 22, 24). Downloads official Node.js binary distributions and layers them onto base images. Includes npm for package management within build stages.

**`common/`**: Shared assets and configuration files used across all images including passwd/group files (defining root, nobody, nonroot users), OS release files, CA certificate bundles, and basic filesystem structure (tmp/, home/, etc.).

**`private/repos/`**: Package source definitions. `deb/` contains YAML manifests declaring required Debian packages with lockfiles (*.lock.json) ensuring reproducible builds. `java_temurin/` defines Java distribution archives.

**`private/oci/`**: OCI image construction abstractions providing language-specific convenience wrappers (java_image, go_image, etc.) around rules_oci, plus signing and push automation.

**`examples/`**: Working demonstrations showing Docker multi-stage build patterns and Bazel integration for each supported language runtime. Includes container structure tests validating example functionality.

## Key Files and Their Roles

**`MODULE.bazel`**: Bzlmod module definition declaring all external dependencies (rules_oci, rules_distroless, rules_python, etc.) and configuring module extensions for downloading busybox, Node.js, and Java distributions.

**`BUILD`** (root): Master image registry defining all published tags. Uses comprehensions to generate hundreds of target mappings from image name/tag combinations to internal build targets. Includes `sign_and_push_all` target for release automation.

**`knife`**: Developer utility script providing commands for package updates (`lock`, `update-snapshots`), testing (`test`), linting (`lint`), and version inspection (`deb-versions`). Critical for maintaining package lockfiles.

**`distro.bzl`**: Defines architecture variant mappings (arm -> v7, arm64 -> v8) and lists of supported Debian distributions. Referenced throughout build files.

**`common/variables.bzl`**: Declares shared constants including user IDs (ROOT=0, NONROOT=65532, NOBODY=65534), image variant lists (DEBUG_MODE, USERS), and OS release file templates.

**`private/util/deb.bzl`**: Provides `deb.package()`, `deb.data()`, and `deb.version()` functions for constructing Debian package target labels with architecture and distribution alias handling.

**`private/repos/deb/*.yaml`**: Package manifests declaring which Debian packages to include. `bookworm.yaml` and `trixie.yaml` define base packages, while `*_java.yaml` and `*_python.yaml` specify language-specific dependencies.

**`private/repos/deb/*.lock.json`**: Generated lockfiles containing exact package versions, SHAs, and download URLs for reproducible builds. Updated via `knife lock` command.

## Code Organization Patterns

**Macro-Based Image Generation**: Rather than manually defining each image variant, the codebase uses Starlark list comprehensions and macros. For example, `base/BUILD` uses a comprehension iterating over distros, architectures, and user variants to generate dozens of targets from a single macro call.

**Configuration Separation**: Package lists, architecture support, and distro definitions live in `config.bzl` files separate from build logic in `BUILD` and implementation in `*.bzl` macros. This allows easy updates to supported packages or architectures.

**Layered Image Construction**: Images are built hierarchically by layering tarballs. Static image is constructed from individual tarballs (base-files, netbase, tzdata, passwd, group, etc.). Higher-level images reference lower-level images as base and add additional tarballs.

**Testing Integration**: Each image directory includes `testdata/*.yaml` files using container-structure-test framework. Tests verify file presence, permissions, command availability, and OS release information. Tests are tagged with architecture to run only on matching hardware.

**Variant Proliferation**: The pattern `(tag_base, debug_mode, user)` in `VARIANTS` combined with distro and architecture lists generates complete matrix of image targets. Root BUILD file translates these to registry tags using template substitution.

**Module Extensions**: Bzlmod extensions in `private/extensions/` handle downloading and extracting external archives (busybox, Node.js) at module loading time, creating repository rules for each architecture variant.
