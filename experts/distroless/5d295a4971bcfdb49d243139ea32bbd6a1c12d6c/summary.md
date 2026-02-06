# Distroless Container Images - Summary

## Repository Purpose and Goals

The GoogleContainerTools/distroless repository provides language-focused minimal container base images that contain only application runtime dependencies, without package managers, shells, or traditional Linux distribution utilities. The project's primary goal is to reduce container image attack surface and improve security by restricting container contents to precisely what's necessary for application execution.

Distroless represents a best practice employed by Google and other tech companies for production container deployments. By eliminating unnecessary utilities and binaries, distroless images provide cleaner vulnerability scanning results (fewer false positives in CVE scans), reduced attack surface, and simplified provenance tracking. The smallest distroless image (`gcr.io/distroless/static-debian12`) is approximately 2 MiB, representing about 50% of Alpine's size and less than 2% of standard Debian's footprint.

## Key Features and Capabilities

**Multi-Architecture Support**: Images are built for amd64, arm64, arm (v7), s390x, and ppc64le architectures using OCI manifests, with architecture-specific variants accessible via tag suffixes (e.g., `latest-amd64`).

**Language Runtime Images**: The project provides specialized base images for multiple language ecosystems including:
- Static binaries (Go, Rust) - `static-debian12/13`
- C/C++ applications with runtime libraries - `cc-debian12/13`
- Java (OpenJDK and Eclipse Temurin distributions) - `java17`, `java21`, `java25`
- Python 3 - `python3-debian12/13`
- Node.js (versions 20, 22, 24) - `nodejs20/22/24-debian12/13`

**Variant Options**: Every image offers four tag variants:
- `latest` - Root user, production build
- `nonroot` - Non-root user (UID 65532) for enhanced security
- `debug` - Includes busybox shell for debugging
- `debug-nonroot` - Combines debug tools with non-root user

**Debian Version Support**: Images track two Debian releases simultaneously (currently Debian 12 Bookworm and Debian 13 Trixie), with automated snapshot updates ensuring security patches are incorporated regularly.

**Security Features**: All images are signed with cosign using ephemeral keyless signatures (verified via `cosign verify` with Google's service account). Images include CA certificates for TLS connections and maintain a unique dpkg metadata structure in `/var/lib/dpkg/status.d/` for CVE scanner compatibility.

## Primary Use Cases and Target Audience

**Production Microservices**: Organizations building cloud-native applications benefit from reduced image sizes, faster deployment times, and improved security posture. The project is used by major platforms including Kubernetes (since v1.15), Knative, Tekton, and Teleport.

**Multi-Stage Docker Builds**: Developers use distroless as the final stage in Docker multi-stage builds, compiling applications in full build environments then copying only the binary and runtime dependencies into minimal distroless images.

**Security-Conscious Deployments**: Teams requiring minimal attack surface, simplified compliance auditing, and reduced vulnerability exposure use distroless images to eliminate unnecessary binaries that could be exploited.

**Container Optimization**: Engineers seeking to minimize container image sizes for bandwidth-constrained environments, edge deployments, or large-scale orchestration benefit from distroless images' compact footprint.

## High-Level Architecture Overview

The project uses Bazel as its build system with a sophisticated modular architecture:

**Image Hierarchy**: Images build upon each other - `static` provides the base (base-files, CA certs, tzdata, users), `base` adds OpenSSL libraries, `cc` includes glibc and libstdc++, and language-specific images layer runtime environments on top.

**Package Management**: Debian packages are sourced from snapshot.debian.org (for Debian 12) and current repositories (for Debian 13), with lockfiles ensuring reproducible builds. The `knife` utility manages package snapshot updates and lockfile generation.

**Build System Organization**: Bazel MODULE.bazel defines dependencies (rules_oci, rules_distroless, rules_python, rules_go, etc.), while individual language directories (base/, cc/, java/, nodejs/, python3/, static/) contain BUILD files defining image targets using Starlark macros.

**OCI Image Construction**: The build process uses rules_oci to create OCI-compliant images and multi-architecture image indexes. Images are constructed by layering tarballs containing Debian packages, configuration files, and runtime assets.

**Automated Releases**: GitHub Actions workflows automatically update package snapshots, rebuild images, and push to gcr.io/distroless with cosign signatures on every commit. Tags include standard variants (latest, nonroot, debug) plus commit-SHA-suffixed tags for versioning.

## Related Projects and Dependencies

**Build Dependencies**:
- **Bazel**: Core build system (version specified in .bazelversion)
- **rules_oci**: OCI container image construction rules
- **rules_distroless**: Custom distroless-specific Bazel rules for creating custom images
- **rules_python**, **rules_go**, **rules_rust**: Language-specific toolchain rules
- **container_structure_test**: Container validation framework

**Runtime Components**:
- **Debian packages**: Base system libraries from Debian 12 (Bookworm) and Debian 13 (Trixie)
- **Eclipse Adoptium (Temurin)**: Java runtime distributions (via both GitHub releases and apt repository)
- **Node.js**: Official binary distributions from nodejs.org
- **Busybox**: Minimal shell environment for debug images

**Related Projects**:
- **rules_distroless**: Companion project providing Bazel rules for users to create custom distroless images with additional packages
- **Docker**: Compatible with Docker multi-stage builds for easy adoption
- **cosign**: Sigstore's container signing tool for image verification
- **Jib**: Google's containerization tool supporting distroless images directly

The project maintains separation between image building (this repository) and custom image creation (rules_distroless), allowing users to either consume pre-built images from gcr.io or build customized variants using the same underlying infrastructure.
