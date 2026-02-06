# rules_img APIs and Interfaces

## Public APIs and Entry Points

rules_img provides a comprehensive Bazel API for building, deploying, and managing OCI container images. All public APIs are exported through `img/*.bzl` files.

### Loading the Rules

```starlark
# In MODULE.bazel
bazel_dep(name = "rules_img", version = "0.3.4")

# In BUILD.bazel files
load("@rules_img//img:layer.bzl", "image_layer", "layer_from_tar", "file_metadata")
load("@rules_img//img:image.bzl", "image_manifest", "image_index")
load("@rules_img//img:push.bzl", "image_push")
load("@rules_img//img:load.bzl", "image_load")
load("@rules_img//img:pull.bzl", "pull")  # Repository rule
load("@rules_img//img:multi_deploy.bzl", "multi_deploy")
load("@rules_img//img:convert.bzl", "image_manifest_from_oci_layout", "image_index_from_oci_layout")
```

## Key Classes, Functions, and Rules

### Layer Creation Rules

#### image_layer

Creates a container image layer from files, executables, and directories.

**Signature**:
```starlark
image_layer(
    name,
    srcs = {},
    symlinks = {},
    file_metadata = {},
    default_metadata = "",
    annotations = {},
    annotations_file = None,
    compress = "auto",
    estargz = "auto",
    create_parent_directories = "auto",
    include_runfiles = True,
)
```

**Attributes**:
- `name`: Target name (required)
- `srcs`: Dict mapping image paths to Bazel labels
  - Keys: Paths in image (e.g., `/app/bin/server`)
  - Values: Bazel targets (files or executables)
- `symlinks`: Dict mapping symlink paths to target paths
- `file_metadata`: Per-file metadata overrides (JSON-encoded)
- `default_metadata`: Default metadata for all files (JSON-encoded)
- `annotations`: Layer annotations (key-value pairs)
- `annotations_file`: File with KEY=VALUE annotations
- `compress`: Compression algorithm (`gzip`, `zstd`, `auto`)
- `estargz`: Enable eStargz format (`enabled`, `disabled`, `auto`)
- `create_parent_directories`: Auto-create parent dirs (`enabled`, `disabled`, `auto`)
- `include_runfiles`: Include executable runfiles (default: `True`)

**Outputs**:
- Default output: Compressed tar archive (`.tgz` or `.tar.zst`)
- Metadata file: JSON with digest, size, diff_id, media_type

**Providers**:
- `LayerInfo`: Contains layer metadata for downstream rules

**Example**:
```starlark
load("@rules_img//img:layer.bzl", "image_layer", "file_metadata")

# Simple layer
image_layer(
    name = "app_layer",
    srcs = {
        "/app/bin/server": "//cmd/server",
        "/app/config.json": ":config.json",
    },
)

# Layer with custom permissions
image_layer(
    name = "secure_layer",
    srcs = {
        "/etc/app/config": ":config",
        "/etc/app/secret": ":secret",
    },
    default_metadata = file_metadata(
        mode = "0644",
        uid = 1000,
        gid = 1000,
    ),
    file_metadata = {
        "/etc/app/secret": file_metadata(mode = "0600"),
    },
)

# Layer with symlinks
image_layer(
    name = "bin_layer",
    srcs = {
        "/usr/local/bin/app": "//cmd/app",
    },
    symlinks = {
        "/usr/bin/app": "/usr/local/bin/app",
    },
    compress = "zstd",
    estargz = "enabled",
)

# Layer with annotations
image_layer(
    name = "data_layer",
    srcs = {"/data": "@assets//:files"},
    annotations = {
        "org.opencontainers.image.description": "Application data",
        "com.example.version": "1.0.0",
    },
)
```

#### layer_from_tar

Creates a layer from an existing tar archive.

**Signature**:
```starlark
layer_from_tar(
    name,
    src,
    annotations = {},
    compress = "auto",
    estargz = "auto",
    optimize = True,
)
```

**Attributes**:
- `src`: Input tar file (can be compressed or uncompressed)
- `optimize`: Apply layer optimization (deduplication via hardlinks)

**Example**:
```starlark
load("@rules_img//img:layer.bzl", "layer_from_tar")

layer_from_tar(
    name = "vendor_layer",
    src = "@vendor_archive//file",
    compress = "zstd",
    optimize = True,
)
```

#### file_metadata

Helper function for specifying file attributes.

**Signature**:
```starlark
file_metadata(
    mode = None,
    uid = None,
    gid = None,
    uname = None,
    gname = None,
    mtime = None,
    pax_records = None,
)
```

**Returns**: JSON-encoded string with metadata

**Example**:
```starlark
load("@rules_img//img:layer.bzl", "file_metadata")

metadata = file_metadata(
    mode = "0755",
    uid = 1000,
    gid = 1000,
    uname = "appuser",
    gname = "appgroup",
    mtime = 0,  # Reproducible builds
)
```

### Image Building Rules

#### image_manifest

Builds a single-platform OCI container image from layers.

**Signature**:
```starlark
image_manifest(
    name,
    base = None,
    layers = [],
    config_fragment = None,
    entrypoint = None,
    cmd = None,
    env = {},
    labels = {},
    user = None,
    working_dir = None,
    stop_signal = None,
    platform = None,
    created = None,
    annotations = {},
    annotations_file = None,
    build_settings = {},
    stamp = "auto",
)
```

**Attributes**:
- `base`: Optional base image (from `pull()` or another `image_manifest`)
- `layers`: List of layer targets (created by `image_layer`)
- `config_fragment`: JSON file with additional config
- `entrypoint`: List of strings (container entrypoint)
- `cmd`: List of strings (default command)
- `env`: Dict of environment variables
- `labels`: Dict of image labels
- `user`: User to run as (e.g., `"1000:1000"`)
- `working_dir`: Working directory
- `stop_signal`: Stop signal (e.g., `"SIGTERM"`)
- `platform`: Target platform (e.g., `"linux/amd64"`)
- `created`: Creation timestamp (RFC 3339)
- `annotations`: Manifest annotations (supports templating)
- `build_settings`: Template variables for annotation expansion
- `stamp`: Build stamping (`enabled`, `disabled`, `auto`)

**Outputs**:
- Default: Manifest JSON file
- Output groups:
  - `digest`: Image digest (sha256:...)
  - `oci_layout`: Complete OCI layout directory
  - `oci_tarball`: OCI layout as tar archive

**Providers**:
- `ImageManifestInfo`: Contains manifest metadata

**Example**:
```starlark
load("@rules_img//img:image.bzl", "image_manifest")

image_manifest(
    name = "app",
    base = "@ubuntu",
    layers = [
        ":base_layer",
        ":app_layer",
    ],
    entrypoint = ["/app/bin/server"],
    cmd = ["--port=8080"],
    env = {
        "PORT": "8080",
        "LOG_LEVEL": "info",
    },
    labels = {
        "org.opencontainers.image.title": "My App",
        "org.opencontainers.image.version": "1.0.0",
    },
    user = "1000:1000",
    working_dir = "/app",
)

# Build from scratch (no base image)
image_manifest(
    name = "minimal",
    layers = [":rootfs_layer"],
    entrypoint = ["/bin/sh"],
)

# With templating
image_manifest(
    name = "stamped_app",
    layers = [":app_layer"],
    annotations = {
        "build.timestamp": "{{.BUILD_TIMESTAMP}}",
        "git.commit": "{{.BUILD_SCM_REVISION}}",
        "registry": "{{.REGISTRY}}",
    },
    build_settings = {
        "REGISTRY": "//settings:registry",
    },
    stamp = "enabled",
)
```

#### image_index

Creates a multi-platform OCI image index from platform-specific manifests.

**Signature**:
```starlark
image_index(
    name,
    manifests = [],
    platforms = [],
    annotations = {},
    annotations_file = None,
    build_settings = {},
    stamp = "auto",
)
```

**Usage Patterns**:

1. **Explicit Manifests** (manual multi-platform):
```starlark
image_index(
    name = "multiarch_app",
    manifests = [
        ":app_linux_amd64",
        ":app_linux_arm64",
        ":app_darwin_amd64",
    ],
)
```

2. **Platform Transitions** (automatic multi-platform):
```starlark
image_index(
    name = "multiarch_app",
    manifests = [":app"],  # Single manifest
    platforms = [
        "//:linux_amd64",
        "//:linux_arm64",
    ],
)
```

**Platform Definitions** (in BUILD.bazel):
```starlark
platform(
    name = "linux_amd64",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
)

platform(
    name = "linux_arm64",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:aarch64",
    ],
)
```

**Outputs**:
- Default: Image index JSON file
- Output groups: `digest`, `oci_layout`, `oci_tarball`

**Providers**:
- `ImageIndexInfo`: Contains index metadata

### Deployment Rules

#### image_push

Pushes images to a container registry.

**Signature**:
```starlark
image_push(
    name,
    image,
    registry,
    repository,
    tag = "latest",
    digest_file = None,
    push_strategy = "auto",
)
```

**Attributes**:
- `image`: Image target (`image_manifest` or `image_index`)
- `registry`: Registry host (e.g., `"ghcr.io"`)
- `repository`: Image repository (e.g., `"my-org/my-app"`)
- `tag`: Image tag (supports templating)
- `digest_file`: Output file for image digest
- `push_strategy`: Override push strategy (`eager`, `lazy`, `cas_registry`, `bes`, `auto`)

**Execution**:
```bash
bazel run //:push_target
bazel run //:push_target -- --tag v1.2.3  # Override tag
```

**Example**:
```starlark
load("@rules_img//img:push.bzl", "image_push")

image_push(
    name = "push",
    image = ":app",
    registry = "ghcr.io",
    repository = "my-org/my-app",
    tag = "latest",
)

# Multi-platform push
image_push(
    name = "push_multiarch",
    image = ":multiarch_app",
    registry = "ghcr.io",
    repository = "my-org/my-app",
    tag = "{{.VERSION}}",  # Templated tag
)

# With digest output
image_push(
    name = "push_with_digest",
    image = ":app",
    registry = "docker.io",
    repository = "myuser/myapp",
    digest_file = "image_digest.txt",
)
```

#### image_load

Loads images into a container daemon (Docker, containerd, Podman).

**Signature**:
```starlark
image_load(
    name,
    image,
    repository,
    tag = "latest",
    load_strategy = "auto",
    load_daemon = "auto",
)
```

**Attributes**:
- `image`: Image target to load
- `repository`: Local repository name
- `tag`: Local tag
- `load_strategy`: Override load strategy (`eager`, `lazy`, `auto`)
- `load_daemon`: Target daemon (`docker`, `containerd`, `podman`, `generic`, `auto`)

**Execution**:
```bash
bazel run //:load_target
bazel run //:load_target -- --platform linux/amd64  # Select platform from index
```

**Example**:
```starlark
load("@rules_img//img:load.bzl", "image_load")

image_load(
    name = "load",
    image = ":app",
    repository = "localhost/my-app",
    tag = "dev",
)

# Load into specific daemon
image_load(
    name = "load_containerd",
    image = ":app",
    repository = "localhost/my-app",
    tag = "dev",
    load_daemon = "containerd",
)
```

#### multi_deploy

Combines multiple push and load operations into a single command.

**Signature**:
```starlark
multi_deploy(
    name,
    push = [],
    load = [],
)
```

**Example**:
```starlark
load("@rules_img//img:multi_deploy.bzl", "multi_deploy")

multi_deploy(
    name = "deploy",
    push = [":push_prod"],
    load = [":load_dev"],
)

# Run both operations
bazel run //:deploy
```

### Base Image Rules

#### pull (Repository Rule)

Pulls base images from container registries.

**Signature**:
```starlark
pull(
    name,
    registry,
    repository,
    tag = None,
    digest = None,
)
```

**Usage in MODULE.bazel**:
```starlark
pull = use_repo_rule("@rules_img//img:pull.bzl", "pull")

pull(
    name = "ubuntu",
    digest = "sha256:1e622c5f073b4f6bfad6632f2616c7f59ef256e96fe78bf6a595d1dc4376ac02",
    registry = "index.docker.io",
    repository = "library/ubuntu",
    tag = "24.04",
)

pull(
    name = "cuda",
    digest = "sha256:f353ffca86e0cd93ab2470fe274ecf766519c24c37ed58cc2f91d915f7ebe53c",
    registry = "index.docker.io",
    repository = "nvidia/cuda",
    tag = "12.8.1-cudnn-devel-ubuntu20.04",
)
```

**Note**: Only manifests and configs are downloaded, not layer blobs (shallow pull).

**Usage in Manifests**:
```starlark
image_manifest(
    name = "app",
    base = "@ubuntu",
    layers = [":app_layer"],
)
```

## Integration Patterns and Workflows

### Basic Workflow: Single-Platform Image

```starlark
# 1. Define base image in MODULE.bazel
pull = use_repo_rule("@rules_img//img:pull.bzl", "pull")

pull(
    name = "alpine",
    digest = "sha256:...",
    registry = "index.docker.io",
    repository = "library/alpine",
    tag = "3.19",
)

# 2. Create layers in BUILD.bazel
load("@rules_img//img:layer.bzl", "image_layer")

image_layer(
    name = "app_layer",
    srcs = {
        "/app/server": "//cmd/server",
        "/app/config": ":config.json",
    },
)

# 3. Build image
load("@rules_img//img:image.bzl", "image_manifest")

image_manifest(
    name = "app",
    base = "@alpine",
    layers = [":app_layer"],
    entrypoint = ["/app/server"],
    env = {"PORT": "8080"},
)

# 4. Deploy
load("@rules_img//img:push.bzl", "image_push")
load("@rules_img//img:load.bzl", "image_load")

image_push(
    name = "push",
    image = ":app",
    registry = "ghcr.io",
    repository = "my-org/app",
    tag = "latest",
)

image_load(
    name = "load",
    image = ":app",
    repository = "localhost/app",
    tag = "dev",
)
```

### Multi-Platform Workflow

```starlark
# 1. Pull multi-arch base image
pull(
    name = "ubuntu",
    registry = "index.docker.io",
    repository = "library/ubuntu",
    digest = "sha256:...",  # Index digest
    tag = "24.04",
)

# 2. Create platform-independent layers
image_layer(
    name = "app_layer",
    srcs = {"/app/server": "//cmd/server"},  # Binary built for target platform
)

# 3. Create single manifest (will be built for multiple platforms)
image_manifest(
    name = "app",
    base = "@ubuntu",
    layers = [":app_layer"],
    entrypoint = ["/app/server"],
)

# 4. Create multi-platform index with platform transitions
load("@rules_img//img:image.bzl", "image_index")

image_index(
    name = "multiarch_app",
    manifests = [":app"],
    platforms = [
        "//:linux_amd64",
        "//:linux_arm64",
    ],
)

# 5. Push multi-platform image
image_push(
    name = "push_multiarch",
    image = ":multiarch_app",
    registry = "ghcr.io",
    repository = "my-org/app",
    tag = "latest",
)
```

### Language-Specific Integration

#### Go Application

```starlark
load("@rules_go//go:def.bzl", "go_binary")
load("@rules_img//img:layer.bzl", "image_layer")
load("@rules_img//img:image.bzl", "image_manifest")

go_binary(
    name = "server",
    srcs = ["main.go"],
    pure = "on",  # Static binary
)

image_layer(
    name = "app_layer",
    srcs = {"/server": ":server"},
)

image_manifest(
    name = "app",
    layers = [":app_layer"],
    entrypoint = ["/server"],
)
```

#### C++ Application

```starlark
load("@rules_cc//cc:defs.bzl", "cc_binary")
load("@rules_img//img:layer.bzl", "image_layer")

cc_binary(
    name = "app",
    srcs = ["main.cc"],
    linkstatic = True,
)

image_layer(
    name = "app_layer",
    srcs = {
        "/usr/local/bin/app": ":app",
        "/usr/local/lib": "@system_libs//:libs",
    },
)

image_manifest(
    name = "image",
    base = "@debian",
    layers = [":app_layer"],
    entrypoint = ["/usr/local/bin/app"],
)
```

#### Python Application

```starlark
load("@rules_python//python:defs.bzl", "py_binary")
load("@rules_img//img:layer.bzl", "image_layer")

py_binary(
    name = "app",
    srcs = ["main.py"],
    deps = [":requirements"],
)

image_layer(
    name = "app_layer",
    srcs = {
        "/app/main": ":app",
    },
    include_runfiles = True,  # Include Python dependencies
)

image_manifest(
    name = "image",
    base = "@python",
    layers = [":app_layer"],
    entrypoint = ["/app/main"],
)
```

### Advanced: Custom Base Image

```starlark
# Create base image from scratch
image_layer(
    name = "rootfs",
    srcs = {
        "/etc/passwd": ":passwd",
        "/etc/group": ":group",
        "/lib/x86_64-linux-gnu": "@debian_libs//:libs",
    },
)

image_manifest(
    name = "base",
    layers = [":rootfs"],
)

# Use custom base
image_manifest(
    name = "app",
    base = ":base",
    layers = [":app_layer"],
)
```

### Advanced: Layer Optimization

```starlark
# Separate frequently-changing and stable layers
image_layer(
    name = "deps_layer",  # Rarely changes
    srcs = {"/app/vendor": "@vendor//:libs"},
)

image_layer(
    name = "app_layer",  # Changes frequently
    srcs = {"/app/bin": "//cmd/app"},
)

image_manifest(
    name = "app",
    base = "@base",
    layers = [
        ":deps_layer",    # Bottom layer (cached)
        ":app_layer",     # Top layer (rebuilt often)
    ],
)
```

## Configuration Options and Extension Points

### Global Configuration (.bazelrc)

```bash
# Compression
common --@rules_img//img/settings:compress=zstd
common --@rules_img//img/settings:compression_level=3
common --@rules_img//img/settings:compression_jobs=nproc

# eStargz
common --@rules_img//img/settings:estargz=enabled

# Push strategy
common --@rules_img//img/settings:push_strategy=lazy
common --@rules_img//img/settings:remote_cache=grpc://cache:9092

# Load configuration
common --@rules_img//img/settings:load_daemon=containerd
common --@rules_img//img/settings:load_strategy=lazy

# Build stamping
common --@rules_img//img/settings:stamp=enabled
build --stamp  # Enable Bazel stamping
```

### Per-Target Configuration

```starlark
# Override compression per layer
image_layer(
    name = "fast_layer",
    srcs = {...},
    compress = "gzip",  # Override global default
    estargz = "disabled",
)

# Override push strategy per push
image_push(
    name = "fast_push",
    image = ":app",
    registry = "localhost:5000",
    repository = "app",
    push_strategy = "cas_registry",  # Override global
)
```

### Template Expansion

Supports Go templates in annotations and tags:

**Built-in Variables** (with `stamp = "enabled"`):
- `{{.BUILD_TIMESTAMP}}`: Unix timestamp
- `{{.BUILD_USER}}`: Build user
- `{{.BUILD_HOST}}`: Build hostname
- `{{.BUILD_SCM_REVISION}}`: Git commit SHA
- `{{.BUILD_SCM_STATUS}}`: Git working tree status

**Custom Variables** (via `build_settings`):
```starlark
string_flag(
    name = "version",
    build_setting_default = "dev",
)

image_manifest(
    name = "app",
    layers = [":app_layer"],
    annotations = {
        "version": "{{.VERSION}}",
        "git": "{{.BUILD_SCM_REVISION}}",
    },
    build_settings = {
        "VERSION": ":version",
    },
    stamp = "enabled",
)

image_push(
    name = "push",
    image = ":app",
    registry = "ghcr.io",
    repository = "my-org/app",
    tag = "{{.VERSION}}",  # Dynamic tag
)
```

**Usage**:
```bash
bazel run //:push --//myapp:version=v1.2.3
```

### Extensibility

**Custom Toolchains**: Override img_tool with custom build:
```starlark
# MODULE.bazel
local_path_override(
    module_name = "rules_img_tool",
    path = "./my_custom_img_tool",
)

register_toolchains("@rules_img_tool//toolchain:all")
```

**Custom Push Strategies**: Implement in Go and integrate with `cmd/deploy`.

**Provider Extensions**: Access providers in custom rules:
```starlark
load("@rules_img//img:providers.bzl", "ImageManifestInfo", "LayerInfo")

def _my_custom_rule_impl(ctx):
    manifest_info = ctx.attr.image[ImageManifestInfo]
    # Use manifest_info.digest, manifest_info.config, etc.
```

rules_img provides a comprehensive, flexible API for container image builds fully integrated with Bazel's build graph, enabling reproducible, cacheable, and efficient container builds at any scale.
