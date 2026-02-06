# Distroless Build System

## Build System Type and Configuration Files

**Primary Build System**: Bazel 8.0 (pinned in `.bazelversion`)

The distroless project uses Bazel with Bzlmod (Bazel's modern module system) for dependency management and builds OCI-compliant container images. The build system is designed for reproducibility, multi-architecture support, and efficient caching.

### Core Configuration Files

**`.bazelrc`**: Bazel configuration defining build flags, remote cache settings, and platform-specific options. Notable configurations include:
- Remote cache enablement for faster builds
- Platform-specific build settings
- Test output modes
- Optimization flags

**`MODULE.bazel`**: Bzlmod module definition declaring the project as the "distroless" module and specifying all external dependencies with pinned versions:

```starlark
module(name = "distroless")

bazel_dep(name = "bazel_skylib", version = "1.8.1")
bazel_dep(name = "rules_oci", version = "1.8.0")
bazel_dep(name = "rules_distroless", version = "0.5.3")
bazel_dep(name = "rules_python", version = "1.5.3")
bazel_dep(name = "rules_go", version = "0.57.0")
bazel_dep(name = "rules_rust", version = "0.63.0")
bazel_dep(name = "rules_cc", version = "0.2.0")
bazel_dep(name = "container_structure_test", version = "1.19.1")
# ... additional dependencies
```

**`MODULE.bazel.lock`**: Dependency resolution lockfile ensuring reproducible builds across environments. Generated automatically by Bazel.

**`WORKSPACE`**: Legacy Bazel workspace file, mostly empty as the project uses Bzlmod. Maintained for backward compatibility.

**`.bazelignore`**: Lists directories that Bazel should not scan, improving build performance.

### Module Extensions

**`private/extensions/busybox.bzl`**: Downloads busybox binaries for multiple architectures from official sources, creating repository rules for each variant:

```starlark
busybox = use_extension("//private/extensions:busybox.bzl", "busybox")
busybox.archive()
use_repo(busybox, "busybox_amd64", "busybox_arm", "busybox_arm64", ...)
```

**`private/extensions/node.bzl`**: Fetches Node.js binary distributions for supported versions (20, 22, 24) and architectures from nodejs.org.

**`private/repos/deb/deb.MODULE.bazel`**: Apt repository extension that processes YAML manifests (bookworm.yaml, trixie.yaml) and lockfiles, creating repository rules for each Debian package:

```starlark
include("//private/repos/deb:deb.MODULE.bazel")
```

This extension uses `rules_distroless` to download and extract .deb packages, exposing them as Bazel targets.

**`private/repos/java_temurin/java.MODULE.bazel`**: Declares Eclipse Adoptium (Temurin) Java distribution archives for specific versions and architectures.

## External Dependencies and Management

### Bazel Rules and Tooling

**`rules_oci` (v1.8.0)**: Provides `oci_image` and `oci_image_index` rules for constructing OCI-compliant container images and multi-architecture manifests. Core to all image building.

**`rules_distroless` (v0.5.3)**: Specialized rules for working with Debian packages, extracting files from .deb archives, and assembling distroless images. Provides the `apt.install` extension used in package manifests.

**`rules_python` (v1.5.3)**: Python toolchain integration for building Python applications and managing Python dependencies in examples.

**`rules_go` (v0.57.0)**: Go toolchain support used for building Go-based test utilities and examples.

**`rules_rust` (v0.63.0)**: Rust toolchain for Rust application examples.

**`rules_cc` (v0.2.0)**: C/C++ toolchain configuration.

**`rules_pkg` (v1.1.0)**: Provides `pkg_tar` rule for creating tarball archives of files, extensively used for layering files into images.

**`container_structure_test` (v1.19.1)**: Testing framework for validating container image contents, file permissions, and command availability.

**`aspect_bazel_lib` (v2.21.1)**: Utility functions and rules for common Bazel patterns.

**`gazelle` (v0.38.0)**: Go build file generator, used in example Go applications.

### Runtime Dependencies

**Debian Packages**: All Debian packages are sourced from either:
- **snapshot.debian.org**: Frozen snapshots for Debian 12 (Bookworm), providing reproducible builds
- **deb.debian.org**: Current repositories for Debian 13 (Trixie)

Package versions and checksums are locked in `private/repos/deb/*.lock.json` files.

**Eclipse Adoptium (Temurin)**: Java distributions are obtained from:
- GitHub Releases (for Debian 12): Direct downloads of .tar.gz archives
- Adoptium APT repository (for Debian 13): .deb packages from packages.adoptium.net

**Node.js**: Official binary distributions downloaded directly from nodejs.org/dist for versions 20, 22, and 24.

**Busybox**: Minimal shell environment for debug images, downloaded from busybox.net precompiled binaries.

## Build Targets and Commands

### Building Individual Images

Build a specific image variant:

```bash
# Build a single architecture image
bazel build //base:static_root_amd64_debian12

# Build a language runtime image
bazel build //java:java21_root_amd64_debian13

# Build a multi-architecture image index
bazel build //nodejs:nodejs22_root_debian12
```

### Building All Images

```bash
# Build everything (images, tests, examples)
bazel build //...
```

Note: This builds all defined targets but does not run tests marked "manual".

### Running Tests

The project uses the `knife` utility for comprehensive testing:

```bash
# Run all tests for current architecture
./knife test
```

This runs `bazel test` with architecture-specific filtering and appropriate timeouts.

Individual image tests:

```bash
# Test static image
bazel test //static:static_amd64_debian12_test --test_output=all

# Test base image
bazel test //base:base_amd64_debian12_test
```

Tests use `container_structure_test` to verify:
- Required files exist with correct permissions
- Commands are available (or absent, for minimal images)
- Environment variables are set correctly
- User/group configuration is correct
- OS release information matches expectations

### Package Management Commands

**Update Debian package snapshots**:

```bash
# Find latest snapshots and update YAML manifests
./knife update-snapshots

# Regenerate lockfiles for snapshot repos
./knife lock
```

**Update specific Java versions**:

```bash
./knife update-java-archives
```

**Update Node.js versions**:

```bash
./knife update-node-archives
```

**View current package versions**:

```bash
./knife deb-versions
```

### Loading Images Locally

To load an image into the local Docker daemon, define an `oci_tarball` target:

```starlark
load("@rules_oci//oci:defs.bzl", "oci_tarball")

oci_tarball(
    name = "local_build",
    image = "//base:static_root_amd64_debian12",
    repo_tags = ["my-static:latest"],
)
```

Then run:

```bash
bazel run //:local_build
```

This exports the image as a tarball and loads it into Docker.

### Code Quality Commands

**Lint Starlark files**:

```bash
./knife lint
```

Uses `buildifier` to format BUILD files and .bzl files according to Bazel style guidelines.

**Pre-commit hooks**:

```bash
pre-commit run --all-files
```

Configured in `.pre-commit-config.yaml` to run various linters and formatters.

## Building, Testing, and Deployment Workflow

### Local Development Workflow

1. **Modify package manifests**: Edit `private/repos/deb/*.yaml` to add/remove Debian packages
2. **Lock dependencies**: Run `./knife lock` to update lockfiles with specific versions
3. **Build images**: Run `bazel build //base:...` (or other package)
4. **Run tests**: Execute `./knife test` to validate changes
5. **Lint code**: Run `./knife lint` to ensure code style compliance

### Multi-Architecture Builds

Images are built for multiple architectures simultaneously. The BUILD files use comprehensions to generate targets for each architecture:

```starlark
[
    base_image(
        arch = arch,
        distro = distro,
        packages = BASE_PACKAGES[distro],
    )
    for distro in BASE_DISTROS
    for arch in BASE_ARCHITECTURES[distro]
]
```

Supported architectures:
- **amd64** (x86_64)
- **arm64** (aarch64, ARM v8)
- **arm** (armhf, ARM v7)
- **s390x** (IBM Z)
- **ppc64le** (PowerPC 64-bit little-endian)

Multi-architecture image indexes (manifest lists) aggregate architecture-specific images:

```starlark
oci_image_index(
    name = "base_root_debian12",
    images = [
        "base_root_amd64_debian12",
        "base_root_arm64_debian12",
        "base_root_arm_debian12",
        # ...
    ],
)
```

### Continuous Integration

**GitHub Actions** (`.github/workflows/`):

1. **ci.yaml**: Main CI pipeline
   - Runs on every PR and commit
   - Builds all images for all architectures
   - Runs test suite
   - Validates examples

2. **update-deb-package-snapshots.yml**: Automated package updates
   - Runs daily
   - Checks for new Debian snapshots
   - Updates manifests and lockfiles
   - Creates PR with changes

3. **update-deb-package-non-snapshots.yml**: Updates Debian 13 packages

4. **update-node-archives.yml**: Updates Node.js versions weekly

5. **update-temurin-packages.yml**: Updates Java Temurin packages

6. **examples.yaml**: Tests all example applications

7. **image-check.yaml**: Validates image metadata and signatures

8. **buildifier.yaml**: Enforces Starlark code style

### Release Process

**Cloud Build** (`.cloudbuild/cloudbuild.yaml`):

1. **Trigger**: Automatic on every commit to main branch

2. **Build phase**:
   - Builds all image variants
   - Runs test suite
   - Generates SBOMs (Software Bill of Materials)

3. **Sign phase**:
   - Signs all images with cosign using keyless signatures
   - Uses Google service account `keyless@distroless.iam.gserviceaccount.com`

4. **Push phase**:
   - Pushes images to `gcr.io/distroless/`
   - Applies multiple tags:
     - Version-specific tags (e.g., `debian12`, `latest`)
     - Architecture-specific tags (e.g., `latest-amd64`)
     - Commit-SHA-suffixed tags for version pinning

5. **Lifecycle tags** (`.cloudbuild/lifecycle_tag.yaml`):
   - Attaches metadata tags for image management
   - Marks images with support lifecycle information

### Tag Structure

The root `BUILD` file defines all published tags using dictionaries:

```python
STATIC = {
    "{REGISTRY}/{PROJECT_ID}/static:latest-amd64":
        "//static:static_root_amd64_debian13",
    "{REGISTRY}/{PROJECT_ID}/static:latest":
        "//static:static_root_debian13",
    # ... hundreds more mappings
}
```

Template variables:
- `{REGISTRY}`: gcr.io
- `{PROJECT_ID}`: distroless
- `{COMMIT_SHA}`: Git commit hash

### Verification

Users verify image authenticity with cosign:

```bash
cosign verify gcr.io/distroless/static-debian12:latest \
  --certificate-oidc-issuer https://accounts.google.com \
  --certificate-identity keyless@distroless.iam.gserviceaccount.com
```

### Testing Strategy

**Unit Tests**: Container structure tests in `testdata/*.yaml` files verify:
- File presence and permissions
- Command availability
- Environment variables
- User/group configuration

**Integration Tests**: Examples in `examples/` directory serve as integration tests, ensuring images work with real applications in Docker and Bazel contexts.

**Manual Tests**: Tagged with "manual" to exclude from `bazel test //...`:
- Architecture-specific tests run only on matching hardware
- Expensive or slow tests excluded from CI

**Cross-Architecture Testing**: CI matrix runs tests on amd64 and arm64 runners to validate multi-arch support.

### Debugging Failed Builds

1. **Check test output**: `bazel test <target> --test_output=all`
2. **Build and inspect locally**: `bazel run //:local_build` to load image into Docker
3. **Use debug images**: Replace `latest` with `debug` tag to get busybox shell
4. **Review lockfiles**: Ensure `*.lock.json` files are current
5. **Verify package availability**: Check if Debian packages exist in repositories
