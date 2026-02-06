# rules_img Repository Summary

## Purpose and Goals

`rules_img` is a modern Bazel ruleset for building OCI (Open Container Initiative) compliant container images with advanced performance optimizations. Originally developed by Tweag, it provides a high-performance alternative to traditional container build tools by embracing Bazel's "Build without the Bytes" philosophy and leveraging remote execution capabilities. The primary goal is to minimize data transfer between build machines, remote caches, and container registries while maintaining full hermetic and reproducible builds.

## Key Features and Capabilities

### Performance Optimizations

The ruleset implements several groundbreaking optimizations that distinguish it from other container build tools:

- **Shallow Base Image Pulling**: Unlike traditional approaches that download entire base images (potentially 10+ GB for images like CUDA), rules_img only downloads manifests and configs during the repository rule phase. Actual layer blobs are retrieved on-demand during push operations or skipped entirely when using advanced push strategies.

- **Single-Action Layer Creation**: Layers are produced with both blob content and metadata (digest, size, diff ID) in a single Bazel action, making them more efficient for remote build execution and reducing action graph complexity.

- **Layer Deduplication**: Uses hardlinks to deduplicate identical files within layers, resulting in smaller container images without sacrificing compatibility.

- **eStargz Support**: First-class support for enhanced stargz format enables lazy pulling at container runtime, allowing containers to start before all layers are downloaded. Combined with containerd's stargz-snapshotter, this reduces startup time from minutes to seconds for large images.

- **Incremental Loading**: Direct containerd API integration enables loading only new or changed layers into container daemons, avoiding full image re-uploads during iterative development.

### Advanced Push Strategies

rules_img offers four sophisticated push strategies, each optimized for different scenarios:

1. **Eager Push**: Traditional approach downloading all layers locally then uploading to registry (works with any standard registry)
2. **Lazy Push**: Checks registry first, skips existing blobs, streams missing blobs directly from Bazel's remote cache
3. **CAS Registry Push**: Uses a special registry directly integrated with Bazel's Content Addressable Storage for zero-copy deployments
4. **BES Push**: Performs image pushes as side-effects of Build Event Service uploads, enabling async pushes with zero client overhead

### Core Capabilities

- **OCI Compliance**: Builds standard OCI images compatible with Docker, containerd, Podman, and all OCI-compliant runtimes
- **Bazel Native**: Fully hermetic builds without Docker daemon dependency
- **Multi-Platform Support**: Native cross-platform builds using Bazel platform transitions
- **Remote Build Execution**: Designed for RBE and Content Addressable Storage integration
- **Flexible Compression**: Supports gzip and zstd compression with configurable parallelism and quality levels
- **Template Expansion**: Dynamic image annotations and labels with build stamping support

## Primary Use Cases and Target Audience

### Target Audience

- **Platform Engineers** building infrastructure for large-scale containerized deployments
- **DevOps Teams** optimizing CI/CD pipelines for container builds and deployments
- **Organizations Using Bazel** that want consistent, reproducible container builds integrated with their build system
- **Companies with Large Images** (ML/AI workloads with CUDA, scientific computing) that need to optimize bandwidth and storage
- **Remote Execution Users** leveraging Bazel's RBE capabilities for distributed builds

### Use Cases

1. **Large-Scale CI/CD**: Organizations with thousands of builds per day benefit from BES push strategy and efficient caching
2. **Development Workflows**: Fast iteration with CAS registry and incremental loading (only changed layers transferred)
3. **Multi-Architecture Builds**: Building container images for multiple platforms (amd64, arm64, etc.) from a single BUILD file
4. **Monorepo Container Builds**: Integrating container builds with other Bazel-built artifacts (Go, Java, C++, Python, etc.)
5. **Air-Gapped Environments**: Hermetic builds with explicit dependency management
6. **Bandwidth-Constrained Environments**: Shallow pulling and lazy push strategies minimize data transfer

## High-Level Architecture Overview

### Dual-Module Structure

The repository uses a sophisticated dual-module architecture:

- **rules_img** (main module): Contains Bazel rules, extensions, providers, and public API written in Starlark
- **rules_img_tool** (img_tool/ subdirectory): Separate Bazel module containing Go implementations of command-line tools
- **rules_img_pull_tool** (pull_tool/ subdirectory): Separate module for base image pulling utilities

This separation enables independent versioning, better dependency management, and allows Go tools to be distributed as prebuilt binaries or built from source.

### Provider System

rules_img uses Bazel providers to pass information between rules:

- **LayerInfo**: Metadata about image layers (digest, size, compression, diff ID)
- **ImageManifestInfo**: Single-platform image information (config, layers, platform)
- **ImageIndexInfo**: Multi-platform image index information
- **PullInfo**: Base image metadata from pulled images
- **DeployInfo**: Push/load operation metadata

### Build Flow

1. **Base Image Pull**: Repository rules fetch only manifests and configs (not blobs)
2. **Layer Creation**: `image_layer` rule packages files into compressed tar archives with metadata
3. **Image Assembly**: `image_manifest` combines base image layers with new layers and config
4. **Multi-Platform Indexing**: `image_index` combines manifests for different platforms
5. **Deployment**: `image_push` or `image_load` rules deploy images using configured strategy

### Tool Architecture

Go tools in `img_tool/` provide the heavy lifting:

- **cmd/img**: Main CLI tool for layer creation, manifest assembly, and image operations
- **cmd/registry**: CAS-integrated registry server for zero-copy deployments
- **cmd/bes**: Build Event Service backend with image push support
- **cmd/deploy**: Unified deployment tool for push and load operations
- **pkg/**: Reusable Go libraries for compression, CAS interaction, OCI operations, authentication, etc.

## Related Projects and Dependencies

### Core Dependencies

- **Bazel**: Build system (7.0+, 8.0+, 9.0+)
- **bazel_skylib**: Standard library for Starlark utilities
- **platforms**: Bazel platform definitions
- **hermetic_launcher**: Hermetic executable launching

### Go Dependencies (in img_tool/)

- **go-containerregistry**: Google's container registry library for OCI operations and authentication
- **containerd**: Direct API integration for incremental image loading
- **gRPC/protobuf**: Remote API communication for CAS and BES
- **klauspost/compress**: High-performance compression libraries

### Related Bazel Projects

- **rules_oci**: Alternative OCI image rules with different architectural approach (uses OCI layout everywhere)
- **rules_docker**: Archived predecessor project
- **rules_pkg**: Tar and packaging rules
- **rules_distroless**: Minimal base image creation

### Comparison with rules_oci

While both build OCI images, rules_img takes a provider-based approach optimized for performance, whereas rules_oci uses OCI image layout as the universal interchange format. rules_img's approach enables shallow pulling, single-action layers, advanced push strategies, and better RBE integration, but requires custom tooling. rules_oci prioritizes simplicity and using off-the-shelf prebuilt tools.

### Container Registry Integrations

Works with standard container registries:
- Docker Hub
- GitHub Container Registry (ghcr.io)
- Google Container Registry (gcr.io, pkg.dev)
- Amazon ECR
- Azure ACR
- Harbor
- Any OCI-compliant registry

### Development Environment

- **Nix**: Reproducible development environment (optional but recommended)
- **pre-commit**: Code quality hooks
- **Buildifier**: Bazel file formatting
- **Gazelle**: Automatic BUILD file generation
- **Stardoc**: API documentation generation

rules_img represents a significant advancement in container image build technology, bringing enterprise-grade performance optimizations and Bazel's hermetic build philosophy to containerization workflows.
