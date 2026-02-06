# rules_distroless Build System

## Build System Type and Configuration Files

`rules_distroless` uses **Bazel** as its build system, with full support for both modern **Bzlmod** (Bazel 6+) and legacy **WORKSPACE** systems.

### Primary Configuration Files

**MODULE.bazel** (Bzlmod - Recommended)
- Defines the module name: `rules_distroless`
- Sets compatibility level: `1`
- Declares all dependencies with pinned versions
- Configures module extensions for apt package management
- Sets up toolchains (yq, tar, zstd, bsdtar)

**WORKSPACE** (Legacy)
- Empty file for backwards compatibility
- Bzlmod is preferred; WORKSPACE will be removed in Bazel 9

**.bazelversion**
- Specifies minimum Bazel version required
- Currently requires Bazel 6.0+ (7.0+ recommended)

**.bazelrc**
- Build flags and configuration
- Defines `ci.bazelrc` import for CI environments
- Sets common flags for all commands
- Configures toolchain resolution

**.bazelignore**
- Lists directories to ignore during Bazel scanning
- Excludes generated files and external directories

## External Dependencies and Management

All dependencies are managed through Bzlmod in MODULE.bazel:

### Core Build Dependencies

```starlark
bazel_dep(name = "platforms", version = "0.0.10")
bazel_dep(name = "bazel_features", version = "1.20.0")
bazel_dep(name = "bazel_lib", version = "3.0.0-rc.0")
bazel_dep(name = "bazel_skylib", version = "1.5.0")
bazel_dep(name = "rules_java", version = "8.8.0")
bazel_dep(name = "rules_shell", version = "0.4.1")
```

**Purpose of each:**
- `platforms`: Platform definitions for cross-compilation
- `bazel_features`: Feature detection for Bazel versions
- `bazel_lib`: Common utilities (path manipulation, etc.)
- `bazel_skylib`: Standard library for Starlark
- `rules_java`: Java compilation for JavaKeyStore utility
- `rules_shell`: Shell script rules and toolchains

### Toolchain Dependencies

```starlark
bazel_dep(name = "gawk", version = "5.3.2.bcr.3")
bazel_dep(name = "tar.bzl", version = "0.6.0")
bazel_dep(name = "yq.bzl", version = "0.3.1")
```

**Toolchains Used:**
- **gawk**: AWK implementation for text processing (parsing control files)
- **tar (bsdtar)**: Tar archive creation and manipulation
- **yq**: YAML parsing for manifest files
- **zstd**: Compression (via bazel_lib)

These are hermetic toolchains, not system tools, ensuring reproducibility.

### Dev Dependencies (Testing/CI Only)

```starlark
bazel_dep(name = "gazelle", version = "0.34.0", dev_dependency = True)
bazel_dep(name = "buildifier_prebuilt", version = "8.0.1", dev_dependency = True)
bazel_dep(name = "rules_oci", version = "2.0.0", dev_dependency = True)
bazel_dep(name = "container_structure_test", version = "1.21.1", dev_dependency = True)
bazel_dep(name = "jq.bzl", version = "0.4.0", dev_dependency = True)
```

These are only needed for development and testing, not for users of the rules.

### Toolchain Registration

Toolchains are registered through module extensions:

```starlark
yq_toolchains = use_extension("@yq.bzl//yq:extensions.bzl", "yq")
use_repo(yq_toolchains, "yq_darwin_amd64", "yq_linux_amd64", ...)

tar_toolchains = use_extension("@tar.bzl//tar:extensions.bzl", "toolchains")
use_repo(tar_toolchains, "bsd_tar_toolchains")
```

This provides platform-specific toolchain implementations.

### Example Dependencies (Testing)

The MODULE.bazel includes example .deb packages for testing:

```starlark
http_archive = use_repo_rule("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "example-bullseye-ca-certificates",
    sha256 = "b2d488ad4d8d8adb3ba319fc9cb2cf9909fc42cb82ad239a26c570a2e749c389",
    urls = ["https://snapshot.debian.org/archive/debian/.../ca-certificates_20210119_all.deb"],
    build_file_content = 'exports_files(["data.tar.xz", "control.tar.xz"])',
)
```

## Build Targets and Commands

### User-Facing Targets

Users of `rules_distroless` primarily interact with it through the apt extension and distroless rules in their own BUILD files. The repository itself provides examples and tests.

### Development and Testing Targets

**Run All Tests:**
```bash
bazel test //...
```

**Run Specific Test Suites:**
```bash
bazel test //apt/tests/...          # APT resolution tests
bazel test //distroless/tests/...   # Distroless rule tests
bazel test //e2e/...                # End-to-end smoke tests
```

**Build Examples:**
```bash
bazel build //examples/debian_snapshot/...
bazel build //examples/ubuntu_snapshot/...
bazel build //examples/passwd:all
```

**Code Quality:**
```bash
bazel run @buildifier_prebuilt//:buildifier        # Format Starlark
bazel run @buildifier_prebuilt//:buildifier-check  # Check formatting
```

### Lockfile Generation

When users configure apt.install, they can generate lockfiles:

```bash
# In user's workspace
bazel run @<repo_name>//:lock
```

For example, with the example configuration:
```bash
bazel run @bullseye//:lock
```

This generates `bullseye.lock.json` next to the `bullseye.yaml` manifest.

### Release Targets

**Generate Release Archive:**
```bash
# Handled by GitHub Actions
# See .github/workflows/release.yaml
```

## How to Build, Test, and Deploy

### Initial Setup

1. **Clone the repository:**
```bash
git clone https://github.com/bazel-contrib/rules_distroless.git
cd rules_distroless
```

2. **Ensure Bazel is installed:**
```bash
# .bazelversion specifies the required version
# bazelisk will automatically download it
bazelisk version
```

3. **Fetch dependencies:**
```bash
# Dependencies are fetched automatically on first build
bazel fetch //...
```

### Development Workflow

**1. Make code changes**

Edit `.bzl` files in `apt/` or `distroless/` directories.

**2. Format code**
```bash
bazel run @buildifier_prebuilt//:buildifier
```

**3. Run tests**
```bash
bazel test //...
```

**4. Test with examples**
```bash
bazel build //examples/debian_snapshot:all
bazel build //examples/passwd:passwd_tar
```

**5. Run end-to-end tests**
```bash
bazel test //e2e/smoke/...
```

### Testing User Scenarios

To test as a user would use the rules:

**Using Bzlmod (in your own workspace):**

1. Add to MODULE.bazel:
```starlark
bazel_dep(name = "rules_distroless", version = "0.5.1")

# For local testing, use local_path_override:
local_path_override(
    module_name = "rules_distroless",
    path = "/path/to/local/rules_distroless",
)
```

2. Configure apt.install:
```starlark
apt = use_extension("@rules_distroless//apt:extensions.bzl", "apt")
apt.install(
    name = "debian",
    manifest = "//:packages.yaml",
)
use_repo(apt, "debian")
```

3. Use in BUILD.bazel:
```starlark
load("@rules_distroless//distroless:defs.bzl", "passwd")

passwd(
    name = "passwd",
    entries = [
        dict(uid = 0, gid = 0, home = "/root", shell = "/bin/bash", username = "root"),
    ],
)
```

### Continuous Integration

CI is handled by GitHub Actions (.github/workflows/):

**ci.yaml** - Runs on every PR and push:
- Runs `bazel test //...` on multiple platforms
- Checks code formatting with buildifier
- Tests with multiple Bazel versions
- Uses `.github/workflows/ci.bazelrc` for CI-specific flags

**release.yaml** - Triggered on tags:
- Creates GitHub release
- Generates release archive
- Runs release preparation script

**publish.yaml** - Publishes to Bazel Central Registry:
- Triggered after successful release
- Updates BCR with new version

### Deployment/Publishing

Publishing happens through the Bazel Central Registry:

**Manual Process:**
1. Update version in relevant files
2. Create and push a git tag: `git tag v0.x.y && git push origin v0.x.y`
3. GitHub Actions automatically creates release
4. Submit PR to Bazel Central Registry (automated)

**BCR Metadata:**
- `.bcr/metadata.template.json`: Package metadata
- `.bcr/source.template.json`: Source archive info
- `.bcr/presubmit.yml`: BCR validation tests

### Performance Considerations

**Caching:**
- Repository rules are cached based on their inputs
- Package downloads are cached in Bazel's repository cache
- Use `--repository_cache` to share cache across workspaces

**Optimization:**
- Use lockfiles to avoid re-resolution
- Pin snapshot archive URLs for stability
- Use `resolve_transitive = False` if you know exact dependencies

**Remote Execution:**
- All rules are compatible with remote execution
- Shell scripts use toolchains, not system tools
- No network access during action execution (only repository rules)

### Common Build Commands

```bash
# Full test suite
bazel test //...

# Build all examples
bazel build //examples/...

# Check formatting
bazel run @buildifier_prebuilt//:buildifier-check

# Update all lockfiles (examples)
bazel run @bullseye//:lock
bazel run @noble//:lock

# Clean build
bazel clean --expunge

# Test with specific Bazel version
bazelisk use 6.5.0
bazel test //...
```

### Troubleshooting

**Problem: Tests fail with "command not found"**
- Solution: Tests use toolchains, not system tools. Ensure toolchains are registered.

**Problem: Package resolution fails**
- Solution: Check network connectivity and repository URLs. Use snapshot archives.

**Problem: Lockfile out of date**
- Solution: Regenerate with `bazel run @<repo>//:lock`

**Problem: Build is slow**
- Solution: Use lockfiles, enable repository cache, consider remote caching

The build system is designed for reproducibility and hermeticity, ensuring consistent builds across environments and time.
