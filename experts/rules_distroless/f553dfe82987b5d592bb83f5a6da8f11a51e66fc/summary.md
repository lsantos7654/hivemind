# rules_distroless Summary

## Repository Purpose and Goals

`rules_distroless` is a Bazel ruleset that provides helper rules to create minimal, distroless Linux/Debian installations from scratch. The project aims to replace traditional Linux system administration commands like `apt-get install`, `passwd`, `groupadd`, `useradd`, and `update-ca-certificates` with Bazel-native build rules. This enables reproducible, hermetic, and version-controlled construction of container base images and Linux filesystems.

The ruleset is primarily funded to support Google's distroless container images project, making it production-ready and battle-tested. It's currently in beta status but is already being used successfully in production by companies like Google and Arize AI.

## Key Features and Capabilities

The core capabilities of `rules_distroless` can be divided into two main areas:

### APT Package Management
The `apt` module provides sophisticated Debian package resolution and installation:
- **Package Resolution**: Automatically resolves package dependencies from Debian/Ubuntu repositories
- **Lockfile Support**: Generates reproducible lockfiles to freeze package versions
- **Snapshot Archives**: Supports Debian/Ubuntu snapshot services for truly reproducible builds
- **Multi-Architecture**: Handles multiple architectures (amd64, arm64, armhf, etc.) simultaneously
- **Transitive Dependencies**: Optionally resolves and includes all transitive dependencies
- **Bzlmod Extension**: Modern Bazel module extension for easy integration

### System File Generation
The `distroless` module provides rules for creating essential Linux system files:
- **passwd**: Create `/etc/passwd` files with user definitions
- **group**: Create `/etc/group` files with group definitions
- **home**: Create home directories with proper permissions and ownership
- **cacerts**: Bundle CA certificates for SSL/TLS
- **java_keystore**: Generate Java keystores from CA certificates
- **locale**: Extract and strip locale data from libc packages
- **os_release**: Generate `/etc/os-release` files for OS identification
- **flatten**: Merge multiple tar archives into a single archive
- **dpkg_status/dpkg_statusd**: Create package database files for vulnerability scanners

## Primary Use Cases and Target Audience

The primary use case is building minimal, secure container base images (distroless containers) that contain only the application and its runtime dependencies, without a full operating system. This approach significantly reduces attack surface, image size, and vulnerability exposure.

**Target Audience:**
- Organizations building distroless/minimal container images
- Teams requiring reproducible Linux filesystem construction
- Security-conscious users wanting minimal attack surfaces
- Bazel users working with containerized applications
- Infrastructure teams maintaining container base images

**Common Workflows:**
1. Define required packages in a YAML manifest
2. Generate a lockfile to freeze versions
3. Use Bazel rules to construct system files
4. Combine everything into a container image using rules_oci
5. Rebuild deterministically months or years later

## High-Level Architecture Overview

The architecture follows a clear separation of concerns:

**Layer 1: Package Resolution (`apt/private/`)**
- `deb_resolve.bzl`: Repository rule that parses manifests and resolves dependencies
- `apt_dep_resolver.bzl`: Dependency resolution algorithm
- `apt_deb_repository.bzl`: Fetches and parses Debian repository metadata
- `lockfile.bzl`: Lockfile generation and management

**Layer 2: Package Import (`apt/private/`)**
- `deb_import.bzl`: Downloads and imports .deb packages as Bazel repositories
- `deb_translate_lock.bzl`: Translates lockfiles into Bazel BUILD files

**Layer 3: Public APIs**
- `apt/extensions.bzl`: Bzlmod module extension for modern usage
- `apt/apt.bzl`: Legacy WORKSPACE macro
- `distroless/defs.bzl`: Public API for system file generation rules

**Layer 4: System File Rules (`distroless/private/`)**
- Individual rule implementations for each system file type
- Shell scripts for complex operations (locale stripping, certificate bundling)
- Tar archive manipulation using bsdtar toolchain

The system is designed to work entirely within Bazel's repository and action framework, ensuring hermetic builds and proper caching. All operations are reproducible given the same inputs.

## Related Projects and Dependencies

**Core Dependencies:**
- **Bazel**: Build system (version 6.0+, 7.0+ recommended)
- **bazel_skylib**: Standard library for Starlark
- **rules_shell**: Shell toolchains for Starlark
- **tar.bzl**: Tar archive manipulation
- **bazel_lib**: Common utilities for Bazel rules
- **yq.bzl**: YAML parsing toolchain
- **gawk**: AWK implementation for text processing

**Related Projects:**
- **GoogleContainerTools/distroless**: The original distroless container images project
- **bazel-contrib/distroless**: Community-maintained distroless images using these rules
- **rules_oci**: OCI image rules for creating container images
- **rules_docker**: Legacy Docker rules (being replaced by rules_oci)

**External Services:**
- **snapshot.debian.org**: Debian snapshot archive service
- **snapshot.ubuntu.com**: Ubuntu snapshot archive service

The ruleset integrates seamlessly with the Bazel ecosystem, particularly with rules_oci for container image construction. It follows Bazel best practices including proper toolchain usage, hermetic execution, and repository rule conventions. The project uses the Bazel Central Registry (BCR) for distribution and maintains compatibility with both Bzlmod and legacy WORKSPACE systems.
