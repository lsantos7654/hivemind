# rules_img Code Structure

## Complete Annotated Directory Tree

```
rules_img/
├── img/                          # Main Bazel rules module (public API)
│   ├── base/                     # Base image utilities
│   ├── constraints/              # Bazel platform constraints
│   ├── private/                  # Private implementation details
│   │   ├── common/               # Shared utilities
│   │   │   ├── build.bzl         # Build configuration and toolchains
│   │   │   ├── layer_helper.bzl  # Layer manipulation utilities
│   │   │   ├── media_types.bzl   # OCI media type constants
│   │   │   ├── transitions.bzl   # Platform transition helpers
│   │   │   └── write_index_json.bzl  # Image index JSON writer
│   │   ├── config/               # Configuration and version management
│   │   ├── conversion/           # OCI layout conversion utilities
│   │   ├── extensions/           # Bazel module extensions (bzlmod)
│   │   ├── integration_test_runner/  # Test infrastructure
│   │   ├── platforms/            # Platform detection and handling
│   │   ├── prebuilt/             # Prebuilt tool management
│   │   ├── providers/            # Provider definitions
│   │   │   ├── deploy_info.bzl   # DeployInfo provider
│   │   │   ├── index_info.bzl    # ImageIndexInfo provider
│   │   │   ├── layer_info.bzl    # LayerInfo provider
│   │   │   ├── manifest_info.bzl # ImageManifestInfo provider
│   │   │   └── pull_info.bzl     # PullInfo provider
│   │   ├── release/              # Release automation
│   │   ├── repository_rules/     # Repository rule implementations
│   │   │   └── pull.bzl          # Base image pull repository rule
│   │   ├── settings/             # Build settings and flags
│   │   ├── download_blobs.bzl    # Blob download implementation
│   │   ├── file_metadata.bzl     # File metadata helper
│   │   ├── image_toolchain.bzl   # Toolchain implementation
│   │   ├── import.bzl            # Import utilities
│   │   ├── index.bzl             # Image index rule implementation
│   │   ├── layer.bzl             # Layer rule implementation
│   │   ├── layer_from_tar.bzl    # Tar-to-layer conversion
│   │   ├── layer_path_hints.bzl  # Path hint utilities
│   │   ├── load.bzl              # Image load implementation
│   │   ├── manifest.bzl          # Image manifest implementation
│   │   ├── manifest_media_type.bzl  # Manifest media type handling
│   │   ├── multi_deploy.bzl      # Multi-operation deployment
│   │   ├── push.bzl              # Image push implementation
│   │   ├── resolved_toolchain.bzl # Toolchain resolution
│   │   ├── root_symlinks.bzl     # Root symlink handling
│   │   └── stamp.bzl             # Build stamping utilities
│   ├── settings/                 # Global settings BUILD files
│   ├── convert.bzl               # Public conversion API
│   ├── dependencies.bzl          # Dependency setup
│   ├── extensions.bzl            # Public module extensions
│   ├── image.bzl                 # Public image rules API
│   ├── image_toolchain.bzl       # Public toolchain API
│   ├── layer.bzl                 # Public layer rules API
│   ├── load.bzl                  # Public load rule API
│   ├── media_types.bzl           # Public media type constants
│   ├── multi_deploy.bzl          # Public multi_deploy API
│   ├── providers.bzl             # Public provider exports
│   ├── pull.bzl                  # Public pull rule API
│   ├── push.bzl                  # Public push rule API
│   └── repositories.bzl          # Repository setup for WORKSPACE
│
├── img_tool/                     # Go tool implementation (separate module)
│   ├── cmd/                      # Command-line tools
│   │   ├── bes/                  # Build Event Service backend
│   │   ├── compress/             # Compression utilities
│   │   ├── deploy/               # Unified deployment tool
│   │   ├── deploymetadata/       # Deployment metadata generation
│   │   ├── downloadblob/         # Blob download tool
│   │   ├── hash/                 # Hash computation utilities
│   │   ├── img/                  # Main CLI tool
│   │   ├── layer/                # Layer creation tool
│   │   ├── manifest/             # Manifest creation tool
│   │   └── registry/             # CAS-integrated registry server
│   ├── pkg/                      # Go libraries
│   │   ├── api/                  # Internal API definitions
│   │   ├── auth/                 # Registry authentication
│   │   ├── cas/                  # Content Addressable Storage client
│   │   ├── compress/             # Compression implementations
│   │   ├── containerd/           # Containerd API integration
│   │   ├── contentmanifest/      # Content manifest handling
│   │   ├── deployvfs/            # Virtual filesystem for deployments
│   │   ├── digestfs/             # Digest-based filesystem
│   │   ├── docker/               # Docker config parsing
│   │   ├── fileopener/           # File opening abstractions
│   │   ├── load/                 # Image loading implementation
│   │   ├── metadata/             # Metadata handling
│   │   ├── persistentworker/     # Bazel persistent worker support
│   │   ├── progress/             # Progress reporting
│   │   ├── proto/                # Protocol buffer definitions
│   │   │   ├── bazel/            # Bazel BES protobuf
│   │   │   ├── blobcache/        # Blob cache protocol
│   │   │   ├── build_event_service/ # BES protocol
│   │   │   └── remote-apis/      # Bazel Remote Execution API
│   │   ├── push/                 # Image push implementations
│   │   ├── serve/                # HTTP/gRPC server utilities
│   │   ├── tarcas/               # Tar + CAS integration
│   │   └── tree/                 # Directory tree utilities
│   ├── toolchain/                # Toolchain registration
│   ├── tools/                    # Build tooling
│   ├── BUILD.bazel               # Top-level build file
│   ├── MODULE.bazel              # Bazel module definition
│   ├── go.mod                    # Go module definition
│   ├── go.sum                    # Go dependency checksums
│   └── go_proto_library.bzl      # Protobuf library helpers
│
├── pull_tool/                    # Image pulling tool (separate module)
│   ├── cmd/                      # Pull command implementation
│   ├── pkg/                      # Pull-specific libraries
│   ├── pull/                     # Pull logic
│   │   └── private/
│   │       └── pull_bootstrap.bzl  # Pull bootstrapping
│   ├── BUILD.bazel
│   ├── MODULE.bazel
│   ├── go.mod
│   └── go.sum
│
├── docs/                         # Generated documentation
│   ├── visuals/                  # Diagrams and images
│   ├── convert.md                # Conversion documentation
│   ├── extensions.md             # Module extensions docs
│   ├── image.md                  # Image rules documentation
│   ├── layer.md                  # Layer rules documentation
│   ├── load.md                   # Load rule documentation
│   ├── migration-from-rules_oci.md  # Migration guide
│   ├── multi_deploy.md           # Multi-deploy documentation
│   ├── platforms.md              # Platform guide
│   ├── pull.md                   # Pull rule documentation
│   ├── push-strategies.md        # Push strategies guide
│   ├── push.md                   # Push rule documentation
│   └── templating.md             # Template expansion guide
│
├── e2e/                          # End-to-end integration tests and examples
│   ├── cc/                       # C++ example
│   ├── generic/                  # Generic examples
│   │   └── custom_distroless_base_image/  # Custom base image example
│   ├── go/                       # Go example
│   ├── js/                       # JavaScript/TypeScript example
│   ├── python/                   # Python example
│   └── workspace/                # WORKSPACE mode tests
│
├── tests/                        # Unit tests
│   ├── compression/              # Compression tests
│   ├── img_toolchain/            # Toolchain tests
│   └── ...
│
├── testdata/                     # Test data files
│
├── util/                         # Development utilities
│   ├── stardoc.bzl               # Documentation generation
│   └── nogo.go                   # Go static analysis config
│
├── .aspect/                      # Aspect Workflows configuration
│   └── workflows/
│
├── .bcr/                         # Bazel Central Registry configuration
│   ├── img_tool/                 # img_tool BCR metadata
│   ├── pull_tool/                # pull_tool BCR metadata
│   ├── metadata.template.json    # BCR metadata template
│   ├── source.template.json      # BCR source template
│   └── presubmit.yml             # BCR presubmit config
│
├── .github/                      # GitHub configuration
│   ├── actions/                  # Custom GitHub Actions
│   ├── logo/                     # Repository branding
│   ├── workflows/                # CI/CD workflows
│   │   ├── ci.yml                # Continuous integration
│   │   ├── publish.yaml          # Publishing workflow
│   │   ├── release.yaml          # Release automation
│   │   └── release_prep.sh       # Release preparation script
│   └── release.yml               # Release configuration
│
├── BUILD.bazel                   # Root build file
├── MODULE.bazel                  # Root Bazel module definition
├── MODULE.bazel.lock             # Module lock file
├── CONTRIBUTING.md               # Contribution guidelines
├── HACKING.md                    # Development guide
├── LICENSE                       # Apache 2.0 license
├── README.md                     # Main documentation
├── .bazelignore                  # Bazel ignore patterns
├── .bazelrc                      # Bazel configuration
├── .bazelrc.common               # Common Bazel config
├── .bazelversion                 # Required Bazel version
├── .envrc                        # direnv configuration
├── .gitignore                    # Git ignore patterns
├── .pre-commit-config.yaml       # Pre-commit hooks
├── flake.lock                    # Nix flake lock
├── flake.nix                     # Nix development environment
├── prebuilt_lockfile.json        # Prebuilt img_tool versions
├── pull_tool_lockfile.json       # Prebuilt pull_tool versions
├── renovate.json                 # Renovate bot configuration
└── 0001-protobuf-19679-rm-protoc-dep.patch  # Protobuf patch
```

## Module and Package Organization

### Public API Module (img/)

The `img/` directory contains the user-facing Bazel rules and is organized by functionality:

- **Layer Creation**: `layer.bzl` exports `image_layer`, `layer_from_tar`, and `file_metadata`
- **Image Building**: `image.bzl` exports `image_manifest` and `image_index`
- **Deployment**: `push.bzl`, `load.bzl`, and `multi_deploy.bzl` for pushing/loading images
- **Base Images**: `pull.bzl` for pulling base images via repository rules
- **Conversion**: `convert.bzl` for converting from rules_oci formats
- **Configuration**: `extensions.bzl` for bzlmod extensions

All public APIs are re-exports from the `private/` directory, following Bazel best practices.

### Private Implementation (img/private/)

Contains the actual rule implementations:

- **providers/**: Defines information containers passed between rules
- **repository_rules/**: Repository rules for external dependencies (base image pull)
- **common/**: Shared utilities for transitions, layer operations, and media types
- **settings/**: Build setting definitions and flag handling
- **config/**: Module version and configuration management
- **prebuilt/**: Prebuilt binary toolchain registration
- **platforms/**: Platform detection and compatibility logic

### Go Tool Module (img_tool/)

Separate Bazel module for Go implementations:

- **cmd/**: Executable commands, each in its own package
  - `img`: Main Swiss-army knife tool (layer, manifest, hash operations)
  - `deploy`: Unified push/load operations
  - `registry`: CAS-backed registry server
  - `bes`: Build Event Service with push integration

- **pkg/**: Reusable Go libraries organized by concern
  - Authentication, compression, CAS interaction
  - Containerd and Docker integrations
  - Protocol buffer definitions for Bazel APIs
  - Push strategies (eager, lazy, CAS, BES)

### Pull Tool Module (pull_tool/)

Dedicated module for base image pulling:

- Separate from main tool to minimize dependencies
- Handles registry authentication and manifest fetching
- Creates Bazel repository rules for base images

## Main Source Directories and Their Purposes

### /img - Bazel Rules (Starlark)

**Purpose**: User-facing API and Bazel rule definitions

**Key Responsibilities**:
- Define rule schemas (attributes, outputs, providers)
- Validate user inputs
- Construct Bazel actions invoking Go tools
- Handle platform transitions for multi-arch builds
- Manage toolchain resolution

**Notable Files**:
- `layer.bzl`: Layer creation rules
- `image.bzl`: Image manifest and index rules
- `push.bzl`, `load.bzl`: Deployment rules
- `providers.bzl`: Provider definitions

### /img/private - Implementation Details (Starlark)

**Purpose**: Private implementation separated from public API

**Key Responsibilities**:
- Implement rule logic
- Handle provider propagation
- Manage Bazel transitions
- Integrate with toolchains
- Process configuration flags

**Organization Pattern**:
- Each public rule has a corresponding `private/*.bzl` implementation
- Common utilities in `common/` subdirectory
- Providers in `providers/` subdirectory
- Settings and configuration in `settings/` and `config/`

### /img_tool/cmd - CLI Tools (Go)

**Purpose**: Command-line executables invoked by Bazel actions

**Key Tools**:

1. **img**: Main tool with subcommands
   - `layer`: Create compressed tar layers with metadata
   - `manifest`: Assemble image manifests
   - `hash`: Compute digests

2. **deploy**: Unified deployment tool
   - Handles push, load, and combined operations
   - Supports all push strategies
   - Integrates authentication

3. **registry**: CAS-integrated registry
   - Serves container images from Bazel's remote cache
   - Zero-copy blob serving
   - Optional upstream registry fallback

4. **bes**: Build Event Service backend
   - Receives Bazel build events
   - Extracts image metadata
   - Triggers async pushes

### /img_tool/pkg - Go Libraries

**Purpose**: Reusable Go code for tool implementations

**Key Packages**:

- **compress/**: Compression implementations (gzip, zstd, estargz)
- **cas/**: Content Addressable Storage client (gRPC)
- **push/**: Push strategy implementations
- **load/**: Image loading into containerd/docker
- **auth/**: Registry authentication (go-containerregistry integration)
- **containerd/**: Direct containerd API integration
- **metadata/**: OCI metadata parsing and generation
- **proto/**: Protocol buffer definitions for Bazel APIs

### /docs - Documentation

**Purpose**: Generated API documentation and guides

**Generation**: Created by Stardoc from .bzl source files

**Content Types**:
- Rule reference documentation (auto-generated)
- User guides (manually written)
- Architecture documentation
- Migration guides

### /e2e - Integration Tests

**Purpose**: Real-world usage examples and end-to-end tests

**Organization**: By programming language/use case
- Each directory is a complete Bazel workspace
- Demonstrates integration with language-specific rules
- Tests full build → push → load workflows

## Key Files and Their Roles

### Root Configuration

- **MODULE.bazel**: Bazel module definition, dependencies, toolchain registration
- **.bazelrc**: Bazel configuration (common flags, CI settings)
- **.bazelversion**: Required Bazel version (currently 7.4.0+)
- **BUILD.bazel**: Root build file, exports important files

### Tool Modules

- **img_tool/MODULE.bazel**: Separate module for Go tool, declares Go SDK dependency
- **pull_tool/MODULE.bazel**: Separate module for pull tool
- **img_tool/go.mod**: Go module dependencies
- **prebuilt_lockfile.json**: Prebuilt binary versions for different platforms
- **pull_tool_lockfile.json**: Prebuilt pull_tool versions

### Critical Implementation Files

- **img/private/layer.bzl**: Core layer creation logic (~350 lines)
- **img/private/manifest.bzl**: Image manifest assembly (~800 lines)
- **img/private/index.bzl**: Multi-platform index creation (~300 lines)
- **img/private/push.bzl**: Image push rule (~550 lines)
- **img/private/load.bzl**: Image load rule (~450 lines)
- **img/private/repository_rules/pull.bzl**: Base image pull repository rule

## Code Organization Patterns

### Separation of Concerns

1. **Public/Private Split**: Public API in `img/*.bzl`, implementation in `img/private/*.bzl`
2. **Rule/Tool Split**: Rules define actions, Go tools perform operations
3. **Module Separation**: Core rules, img_tool, and pull_tool are separate modules

### Provider-Based Architecture

Information flows through Bazel providers:
```
pull() → PullInfo → image_manifest → ImageManifestInfo → image_push
                  ↗ LayerInfo ↗
image_layer ↗
```

### Platform Transitions

Multi-platform builds use Bazel's configuration transitions:
```starlark
image_index(
    manifests = [":app"],
    platforms = ["linux/amd64", "linux/arm64"],  # Triggers platform transition
)
```

### Toolchain Pattern

Rules use toolchains for tool resolution:
```starlark
ctx.toolchains[TOOLCHAIN].img_tool  # Resolves to img binary
```

### Action Composition

Rules compose multiple Bazel actions:
1. Layer creation: file collection → tar creation → compression → metadata extraction
2. Manifest creation: layer metadata aggregation → config JSON → manifest JSON
3. Push: metadata download → registry checks → blob streaming

This structure enables maximum reusability, testability, and performance optimization while maintaining clear separation between user-facing APIs and implementation details.
