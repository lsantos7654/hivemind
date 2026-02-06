# rules_img Build System

## Build System Type and Configuration

### Bazel (Bzlmod)

rules_img uses **Bazel** as its build system with **Bzlmod** (Bazel Modules) as the primary dependency management mechanism. WORKSPACE mode is still supported but bzlmod is the recommended approach for new projects.

**Supported Bazel Versions**:
- Bazel 7.4.0+
- Bazel 8.5.1+
- Bazel 9.0.0+

**Version Specification**: `.bazelversion` file specifies the required Bazel version

### Key Configuration Files

#### MODULE.bazel

The root MODULE.bazel defines the repository as a Bazel module:

```starlark
module(
    name = "rules_img",
    version = "0.3.4",
    compatibility_level = 1,
)
```

**Dependencies**:
- `bazel_skylib`: Starlark utility library
- `platforms`: Platform definitions
- `hermetic_launcher`: Hermetic executable launching

**Module Extensions**:
- `prebuilt_img_tool`: Registers prebuilt img tool binaries for different platforms
- `pull_tool`: Registers prebuilt pull_tool binaries

**Dev Dependencies** (not inherited by users):
- `rules_go`: Go language support
- `gazelle`: BUILD file generation
- `protobuf`: Protocol buffer support
- `rules_bazel_integration_test`: Integration testing framework
- `stardoc`: Documentation generation
- `buildifier_prebuilt`: Code formatting

#### .bazelrc

Primary Bazel configuration with common flags:

**Key Settings**:
```bash
# Import common config
try-import %workspace%/.bazelrc.common

# Compression algorithm
common --@rules_img//img/settings:compress=zstd

# Compression parallelism
common --@rules_img//img/settings:compression_jobs=auto

# Compression level
common --@rules_img//img/settings:compression_level=auto

# eStargz support
common --@rules_img//img/settings:estargz=enabled

# Push strategy
common --@rules_img//img/settings:push_strategy=eager

# Load strategy
common --@rules_img//img/settings:load_strategy=eager

# Load daemon
common --@rules_img//img/settings:load_daemon=docker

# Remote cache for lazy pushing
common --@rules_img//img/settings:remote_cache=grpcs://remote.buildbuddy.io

# Credential helper
common --@rules_img//img/settings:credential_helper=tweag-credential-helper

# Docker config path
common --@rules_img//img/settings:docker_config_path=/home/user/.docker/config.json
```

**.bazelrc.common**: Shared configuration imported by main .bazelrc

**CI Configuration**: `.github/workflows/ci.bazelrc` with CI-specific flags

### Build Settings and Flags

rules_img provides numerous configurable settings through Bazel's build settings API:

**Location**: `img/settings/BUILD.bazel`

**Compression Settings**:
- `compress`: Algorithm choice (gzip, zstd)
- `compression_jobs`: Parallel workers (1, auto, nproc, or number)
- `compression_level`: Quality level (0-9 for gzip, 1-4 for zstd, auto)

**Layer Settings**:
- `estargz`: Enable eStargz format (enabled/disabled/auto)
- `create_parent_directories`: Auto-create parent dirs (enabled/disabled/auto)

**Deployment Settings**:
- `push_strategy`: How to push images (eager/lazy/cas_registry/bes)
- `load_strategy`: How to load images (eager/lazy)
- `load_daemon`: Target daemon (docker/containerd/podman/generic)
- `stamp`: Build stamping (enabled/disabled/auto)

**Remote Settings**:
- `remote_cache`: Bazel remote cache URL
- `credential_helper`: gRPC credential helper
- `docker_config_path`: Path to Docker config for auth

## External Dependencies and Management

### Bazel Module Dependencies

**Direct Dependencies** (MODULE.bazel):
```starlark
bazel_dep(name = "bazel_skylib", version = "1.9.0")
bazel_dep(name = "platforms", version = "1.0.0")
bazel_dep(name = "hermetic_launcher", version = "0.0.4")
```

**Development Dependencies**:
```starlark
bazel_dep(name = "rules_go", version = "0.59.0", dev_dependency = True)
bazel_dep(name = "gazelle", version = "0.47.0", dev_dependency = True)
bazel_dep(name = "protobuf", version = "33.5", dev_dependency = True)
bazel_dep(name = "rules_bazel_integration_test", version = "0.37.1", dev_dependency = True)
bazel_dep(name = "rules_img_tool", version = "0.3.4", dev_dependency = True)
bazel_dep(name = "rules_img_pull_tool", version = "0.3.4", dev_dependency = True)
bazel_dep(name = "stardoc", version = "0.8.1", dev_dependency = True)
```

### Go Module Dependencies

**img_tool/go.mod**:
```go
module github.com/bazel-contrib/rules_img/img_tool

go 1.25

require (
    github.com/google/go-containerregistry/...  // Container registry operations
    github.com/containerd/containerd/...        // Containerd API
    google.golang.org/grpc/...                  // gRPC for CAS/BES
    github.com/klauspost/compress/...           // High-performance compression
    google.golang.org/protobuf/...              // Protocol buffers
)
```

**Key Go Dependencies**:
- **go-containerregistry**: OCI image manipulation, registry authentication
- **containerd**: Direct containerd API access for incremental loading
- **gRPC**: Remote API communication (CAS, BES)
- **protobuf**: Protocol buffer serialization
- **compress**: Parallel compression (pgzip, zstd)

### Toolchain Management

**Prebuilt Binaries**:
- `prebuilt_lockfile.json`: Specifies prebuilt img_tool versions for each platform
- `pull_tool_lockfile.json`: Specifies prebuilt pull_tool versions

**Toolchain Registration**:
```starlark
# Prebuilt toolchain (default for users)
register_toolchains("@img_toolchain//:all")

# Source-built toolchain (for development)
register_toolchains("@rules_img_tool//toolchain:all", dev_dependency = True)
```

**Platform Support**:
- linux-amd64
- linux-arm64
- darwin-amd64
- darwin-arm64
- windows-amd64

### Base Image Dependencies

Managed through repository rules in user MODULE.bazel:

```starlark
pull = use_repo_rule("@rules_img//img:pull.bzl", "pull")

pull(
    name = "ubuntu",
    digest = "sha256:...",
    registry = "index.docker.io",
    repository = "library/ubuntu",
    tag = "24.04",
)
```

**Shallow Pulling**: Only manifests and configs are downloaded during repository rule execution; layer blobs are retrieved on-demand.

## Build Targets and Commands

### Main Build Targets

**All Targets**:
```bash
bazel build //...                    # Build everything in rules_img
bazel build @rules_img_tool//...     # Build all Go tools
```

**Specific Go Tools**:
```bash
bazel build @rules_img_tool//cmd/img        # Main CLI tool
bazel build @rules_img_tool//cmd/registry   # CAS registry
bazel build @rules_img_tool//cmd/bes        # BES server
bazel build @rules_img_tool//cmd/deploy     # Deployment tool
```

**User Image Targets**:
```bash
bazel build //my:image              # Build image manifest
bazel build //my:image_index        # Build multi-platform index
```

### Testing Commands

**Unit Tests**:
```bash
bazel test //...                    # All tests
bazel test //img/...                # Rules tests
bazel test @rules_img_tool//...     # Go tool tests
bazel test --test_output=all //...  # Verbose output
```

**Integration Tests**:
```bash
cd e2e/go && bazel test //...       # Go integration tests
cd e2e/cc && bazel test //...       # C++ integration tests
cd e2e/python && bazel test //...   # Python integration tests
```

**Bazel Version Tests**:
```bash
bazel test --config=bazel7 //...    # Test with Bazel 7.x
bazel test --config=bazel8 //...    # Test with Bazel 8.x
bazel test --config=bazel9 //...    # Test with Bazel 9.x
```

### Deployment Commands

**Push Images**:
```bash
bazel run //my:push                 # Push image to registry
bazel run //my:push -- --tag v1.2.3 # Push with override tag
```

**Load Images**:
```bash
bazel run //my:load                 # Load into default daemon
bazel run //my:load -- --platform linux/amd64  # Load specific platform
```

**Multi-Deploy**:
```bash
bazel run //my:deploy               # Combined push and load
```

### Development Commands

**Code Formatting**:
```bash
bazel run //util:buildifier.fix     # Format Bazel files (fix mode)
bazel test //util:buildifier.check  # Check formatting (test mode)
```

**BUILD File Generation**:
```bash
bazel run //util:gazelle            # Update BUILD files for Go code
bazel run //util:gazelle -- update-repos -from_file=img_tool/go.mod  # Update Go deps
```

**Documentation Generation**:
```bash
bazel run //docs:update             # Generate/update all docs
bazel test //docs:all               # Verify docs are up-to-date
```

### Advanced Build Options

**Compilation Modes**:
```bash
bazel build -c opt //...            # Optimized build
bazel build -c fastbuild //...      # Fast build (default)
bazel build -c dbg //...            # Debug build
```

**Remote Execution**:
```bash
bazel build --remote_executor=grpc://executor:9092 //...
bazel build --remote_cache=grpc://cache:9092 //...
```

**Build Stamping**:
```bash
bazel build --stamp //my:image      # Include build info
bazel build --nostamp //my:image    # Reproducible builds
```

**Platform-Specific Builds**:
```bash
bazel build --platforms=//my:linux_arm64 //my:image
bazel build --platforms=@platforms//os:macos //my:image
```

## How to Build, Test, and Deploy

### Initial Setup

**1. Install Bazel**:
```bash
# Install Bazelisk (manages Bazel versions)
npm install -g @bazel/bazelisk
# OR
brew install bazelisk
```

**2. Clone Repository**:
```bash
git clone https://github.com/bazel-contrib/rules_img.git
cd rules_img
```

**3. Development Environment (Optional but Recommended)**:
```bash
# Using Nix
nix develop

# OR manually install:
# - Bazel
# - Go 1.25+
# - pre-commit
pre-commit install
```

### Building from Source

**Build All Components**:
```bash
# Build main rules
bazel build //img/...

# Build Go tools from source
bazel build @rules_img_tool//...

# Build pull tool
bazel build @rules_img_pull_tool//...
```

**Build Specific Tools**:
```bash
bazel build @rules_img_tool//cmd/img:img
bazel run @rules_img_tool//cmd/img -- --help
```

### Testing Workflow

**1. Pre-commit Checks**:
```bash
pre-commit run --all-files
```

**2. Unit Tests**:
```bash
bazel test //...
```

**3. Integration Tests**:
```bash
# Test all language examples
bazel test //e2e/...

# Test specific language
cd e2e/go && bazel test //...
cd e2e/cc && bazel test //...
```

**4. Verify Documentation**:
```bash
bazel test //docs:all
```

### Development with Module Overrides

For local development of tools:

**MODULE.bazel**:
```starlark
local_path_override(
    module_name = "rules_img_tool",
    path = "./img_tool",
)

register_toolchains(
    "@rules_img_tool//toolchain:all",
    dev_dependency = True,
)
```

### Deployment Workflow

**1. Build Image**:
```bash
bazel build //my:app_image
```

**2. Test Locally**:
```bash
bazel run //my:app_load
docker run localhost:5000/my/app:latest
```

**3. Push to Registry**:
```bash
# Configure authentication
docker login ghcr.io

# Push
bazel run //my:app_push
```

**4. Multi-Platform Build**:
```bash
bazel build //my:multiarch_app
bazel run //my:multiarch_push
```

### CI/CD Integration

**GitHub Actions Example**:
```yaml
- name: Build and Test
  run: |
    bazel test //...

- name: Build Images
  run: |
    bazel build //my:images

- name: Push to Registry
  run: |
    bazel run //my:push
  env:
    DOCKER_CONFIG: ${{ secrets.DOCKER_CONFIG }}
```

### Release Process

**1. Version Bump**:
```bash
# Update MODULE.bazel version
# Update prebuilt lockfiles
```

**2. Build Release Artifacts**:
```bash
bazel build //img/private/release:all
```

**3. Tag Release**:
```bash
git tag v0.3.4
git push origin v0.3.4
```

**4. Publish to BCR**:
```bash
# Create PR to Bazel Central Registry
# Uses .bcr/ configuration
```

### Performance Optimization

**Build Performance**:
```bash
# Use remote cache
bazel build --remote_cache=grpc://cache:9092 //...

# Parallel builds
bazel build --jobs=8 //...

# Disk cache
bazel build --disk_cache=/path/to/cache //...
```

**Image Performance**:
```bash
# Use zstd compression
bazel build --@rules_img//img/settings:compress=zstd //my:image

# Parallel compression
bazel build --@rules_img//img/settings:compression_jobs=nproc //my:image

# Enable eStargz
bazel build --@rules_img//img/settings:estargz=enabled //my:image
```

The build system is designed for maximum flexibility while maintaining hermetic, reproducible builds. All external dependencies are explicitly versioned and managed through Bazel's module system.
