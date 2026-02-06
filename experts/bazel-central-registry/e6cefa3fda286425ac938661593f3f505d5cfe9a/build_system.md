# Bazel Central Registry - Build System

## Build System Type and Configuration

The Bazel Central Registry uses **Bazel with Bzlmod** (Bazel's native external dependency system) as its build system. This is notable because the BCR itself uses the modern dependency management approach it provides infrastructure for. The repository has an **empty WORKSPACE file**, signifying exclusive use of Bzlmod for dependency management.

### Primary Build Configuration Files

**MODULE.bazel** (root level):
```starlark
module(
    name = "bazel_central_registry",
    version = "0.0.0",
    compatibility_level = 1,
)

bazel_dep(name = "aspect_bazel_lib", version = "2.22.5")
bazel_dep(name = "aspect_rules_js", version = "2.9.2")
bazel_dep(name = "buildozer", version = "8.2.1")
bazel_dep(name = "rules_nodejs", version = "6.7.3")
bazel_dep(name = "rules_python", version = "1.8.3")
bazel_dep(name = "rules_shell", version = "0.6.1")
```

This defines the BCR's own dependencies, demonstrating real-world Bzlmod usage.

**BUILD Files**:
- Root `BUILD`: Validates all metadata.json files against metadata.schema.json using ajv (from npm)
- `tools/BUILD`: Defines Python binaries and libraries for registry management

**.bazelversion**:
```
6
```
Specifies the minimum required Bazel version (Bazel 6.x).

**.bazelignore**:
```
modules
tools/bzlmod_migration_test_examples
```
Excludes the massive modules directory from Bazel's workspace scanning for performance, since modules are data, not build targets.

## External Dependencies and Management

### Python Dependencies

The BCR uses **rules_python** with pip for Python dependency management:

**tools/requirements.in** (unpinned dependencies):
```
click
networkx
numpy
pyyaml
requests
scipy
validators
bazel-runfiles
fastmcp
```

**tools/requirements_lock.txt** (pinned dependencies, ~97KB):
Generated lockfile ensuring reproducible builds with exact versions and transitive dependencies.

**Python Toolchain Configuration** (in MODULE.bazel):
```starlark
python = use_extension("@rules_python//python/extensions:python.bzl", "python")
python.toolchain(
    is_default = True,
    python_version = "3.11",
    ignore_root_user_error = True,
)

pip = use_extension("@rules_python//python/extensions:pip.bzl", "pip")
pip.parse(
    hub_name = "pip",
    python_version = "3.11",
    requirements_lock = "//tools:requirements_lock.txt",
)
```

This sets up Python 3.11 as the default toolchain and parses the locked requirements.

### Node.js and npm Dependencies

**rules_nodejs** and **aspect_rules_js** manage JavaScript dependencies:

**tools/package.json**:
```json
{
  "dependencies": {
    "ajv-cli": "^5.0.0"
  }
}
```

**tools/pnpm-lock.yaml**: Lockfile for npm dependencies using pnpm (performant npm).

**Node Toolchain Configuration** (in MODULE.bazel):
```starlark
node = use_extension("@rules_nodejs//nodejs:extensions.bzl", "node", dev_dependency = True)
node.toolchain(node_version = "20.18.0")

npm = use_extension("@aspect_rules_js//npm:extensions.bzl", "npm", dev_dependency = True)
npm.npm_translate_lock(
    name = "npm",
    pnpm_lock = "//tools:pnpm-lock.yaml",
)
```

The ajv-cli tool validates JSON schemas (metadata.json files).

### Build Tools

**buildozer** (8.2.1): Bazel BUILD file manipulation tool, exposed via:
```starlark
buildozer_binary = use_extension("@buildozer//:buildozer_binary.bzl", "buildozer_binary")
use_repo(buildozer_binary, "buildozer_binary")
```

Used by module_analyzer.py for programmatic BUILD file analysis.

### CI Scripts

The BCR downloads presubmit scripts from the bazelbuild/continuous-integration repository:

```starlark
BAZEL_CI_COMMIT = "c323cb207d8bbde0ff23f6705dc5aafb085df924"

http_file(
    name = "bazelci_py_file",
    integrity = "sha256-ZO7sqCW2aaH+aj0ncBBFa9yL+KpL1421wvW32PSS1CA=",
    downloaded_file_path = "bazelci.py",
    urls = ["https://raw.githubusercontent.com/bazelbuild/continuous-integration/%s/buildkite/bazelci.py" % BAZEL_CI_COMMIT],
)

http_file(
    name = "bcr_presubmit_py_file",
    integrity = "sha256-T2txNFVlX2Cm+OSmu4YIgtvmKwGGDNaCrO+cvCNjmwA=",
    downloaded_file_path = "bcr_presubmit.py",
    urls = ["https://raw.githubusercontent.com/bazelbuild/continuous-integration/%s/buildkite/bazel-central-registry/bcr_presubmit.py" % BAZEL_CI_COMMIT],
)
```

These scripts drive the BCR presubmit system.

## Build Targets and Commands

### Tool Binaries

All tools are built as `py_binary` targets in `tools/BUILD`:

```starlark
py_binary(
    name = "add_module",
    srcs = ["add_module.py"],
    deps = [":bcr_validation", ":registry"],
)

py_binary(
    name = "bcr_validation",
    srcs = ["bcr_validation.py"],
    deps = [":attestations", ":registry", ":slsa", ":verify_stable_archives", requirement("requests")],
)

py_binary(
    name = "calc_integrity",
    srcs = ["calc_integrity.py"],
    deps = [":registry", requirement("validators")],
)

py_binary(
    name = "update_integrity",
    srcs = ["update_integrity.py"],
    deps = [":registry", requirement("click")],
)

py_binary(
    name = "module_selector",
    srcs = ["module_selector.py"],
    deps = [":registry"],
)

py_binary(
    name = "module_analyzer",
    srcs = ["module_analyzer.py"],
    data = ["@buildozer_binary//:buildozer.exe"],
    deps = [":module_selector", requirement("networkx"), requirement("numpy"), requirement("scipy"), requirement("bazel-runfiles")],
)

py_binary(
    name = "mcp_server",
    srcs = ["mcp_server.py"],
    deps = [":registry", requirement("fastmcp")],
)
```

### Validation Targets

The root `BUILD` file generates test targets for all metadata.json files:

```starlark
load("@npm//tools:ajv-cli/package_json.bzl", ajv = "bin")

_METADATA_FILES = glob(["modules/*/metadata.json"])

[
    ajv.ajv_test(
        name = "test_metadata." + s.removesuffix("/metadata.json"),
        args = [
            "validate",
            "-s", "$(execpath metadata.schema.json)",
            "-d", "$(execpath %s)" % s,
        ],
        data = [s, "metadata.schema.json"],
    )
    for s in _METADATA_FILES
]
```

This creates 977+ test targets (one per module) that validate metadata against the JSON schema.

### Test Targets

```starlark
sh_test(
    name = "update_integrity_test",
    srcs = ["update_integrity_test.sh"],
    data = [":update_integrity"],
)

py_test(
    name = "version_test",
    srcs = ["version_test.py"],
    deps = ["registry"],
)

py_test(
    name = "module_selector_test",
    srcs = ["module_selector_test.py"],
    deps = ["module_selector"],
)
```

### Python Requirements Compilation

```starlark
compile_pip_requirements_3_11(
    name = "requirements",
    requirements_in = "requirements.in",
    requirements_txt = "requirements_lock.txt",
)
```

This target regenerates the lockfile when requirements.in changes.

## How to Build, Test, and Deploy

### Building Tools

Build any tool binary:
```bash
bazel build //tools:add_module
bazel build //tools:bcr_validation
bazel build //tools:module_analyzer
```

Run a tool directly:
```bash
bazel run //tools:add_module
bazel run //tools:calc_integrity -- https://example.com/archive.tar.gz
bazel run //tools:update_integrity -- --version 1.2.3 module_name
bazel run //tools:module_selector -- --select "rules_*@latest"
bazel run //tools:module_analyzer -- --top_n 50
bazel run //tools:mcp_server
```

### Running Validation

Validate a specific module version:
```bash
bazel run //tools:bcr_validation -- --check foo@1.0.0
```

Validate all versions of a module:
```bash
bazel run //tools:bcr_validation -- --check foo
```

Validate all metadata:
```bash
bazel run //tools:bcr_validation -- --check_all_metadata
```

Fix issues automatically (e.g., update github_user_id):
```bash
bazel run //tools:bcr_validation -- --check_metadata foo --fix
```

Skip specific validations:
```bash
bazel run //tools:bcr_validation -- --check foo@1.0.0 --skip_validation url_stability
```

### Testing Metadata Schema

Test all metadata.json files:
```bash
bazel test //...
```

Test a specific module's metadata:
```bash
bazel test //:test_metadata.modules/rules_python
```

### Testing Tools

Run unit tests:
```bash
bazel test //tools:version_test
bazel test //tools:module_selector_test
bazel test //tools:update_integrity_test
```

### Adding a New Module

Interactive wizard:
```bash
bazel run //tools:add_module
```

This prompts for:
- Module name
- Module version
- Source URL
- Homepage
- Maintainer information
- Build and test targets

It automatically:
- Creates directory structure
- Downloads and validates source archive
- Calculates integrity hashes
- Generates MODULE.bazel, source.json, metadata.json, presubmit.yml

### Local Testing of Module Changes

Test against a local BCR copy:
```bash
# In your project that uses the module
bazel shutdown
bazel build \
  --enable_bzlmod \
  --registry="file:///path/to/bazel-central-registry" \
  --lockfile_mode=off \
  @module-to-test//:target
```

Reproduce presubmit environment:
```bash
bazel run //tools:setup_presubmit_repos -- --module foo@1.2.3
```

### Mirroring the Registry

Get all source URLs for mirroring:
```bash
bazel run //tools:print_all_src_urls > urls.txt
```

Sync to Google Cloud Storage (BCR maintainers only):
```bash
./tools/sync_to_gcs.sh
```

### Pre-commit Hooks

The repository uses pre-commit for local validation:

**.pre-commit-config.yaml**:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.5
    hooks:
      - id: ruff
      - id: ruff-format
```

Install hooks:
```bash
pip install pre-commit
pre-commit install
```

Run manually:
```bash
pre-commit run --all-files
```

### GitHub Actions Integration

The BCR uses GitHub Actions for CI/CD:

**Key Workflows:**
- `presubmit.yaml`: Runs bcr_presubmit.py on PRs (triggers Buildkite jobs)
- `review_prs.yml`: Automated approval via bazel-io bot
- `notify_maintainers.yml`: Pings module maintainers on PRs
- `generate_module_diff.yml`: Shows changes between module versions
- `skip_check.yml`: Processes @bazel-io skip_check comments

The presubmit system runs on Bazel CI infrastructure (Buildkite) across multiple platforms:
- Linux: debian11, ubuntu2204, rockylinux8
- macOS: macos (latest)
- Windows: windows (latest)

With multiple Bazel versions: 6.x, 7.x, 8.x, 9.x

### Incompatible Flags Testing

The BCR tests modules against future Bazel incompatible flags:

```bash
# Defined in incompatible_flags.yml
incompatible_flags:
  "--incompatible_config_setting_private_default_visibility":
    - 6.x
    - 7.x
    - 8.x
  "--incompatible_autoload_externally=":
    - 7.x
    - 8.x
```

These flags are tested using Bazelisk's `--migrate` feature during presubmit.

Skip incompatible flags testing in a PR:
```
# Comment on PR
@bazel-io skip_check incompatible_flags
```

### Deployment

The BCR is deployed automatically:
1. PRs merge to `main` branch
2. GitHub Actions trigger registry sync to https://bcr.bazel.build/
3. Frontend rebuild triggers update https://registry.bazel.build/

The registry is served as static files from Google Cloud Storage, making it highly available and cacheable.

## Build System Philosophy

The BCR's build system embodies several key principles:

1. **Dogfooding**: Uses Bzlmod exclusively, demonstrating real-world usage
2. **Reproducibility**: Locked dependencies (requirements_lock.txt, pnpm-lock.yaml)
3. **Validation-First**: Extensive validation before any changes merge
4. **Tooling as Code**: All registry operations exposed as Bazel targets
5. **Cross-Platform**: Tests across Linux, macOS, Windows with multiple Bazel versions
6. **Immutability**: Add-only policy enforced through validation
7. **Performance**: .bazelignore excludes 977+ module directories from scanning

This build system ensures the BCR maintains high quality, reproducible, and reliable infrastructure for the entire Bazel ecosystem.
