# APIs and Interfaces

## Public API Overview

bazel-lib provides 29 public modules organized into functional categories. All APIs are accessed through `load()` statements from `@bazel_lib//lib:*.bzl`. The design philosophy emphasizes:

- Platform independence (no bash requirements)
- Hermetic operations (reproducible across environments)
- Composability (rules work together seamlessly)
- Type safety through providers

## File and Directory Operations

### copy_file

Hermetic file copying without shell dependencies.

**Load**:
```starlark
load("@bazel_lib//lib:copy_file.bzl", "copy_file")
```

**Usage**:
```starlark
copy_file(
    name = "copy_config",
    src = "config.json.template",
    out = "config.json",
    allow_symlink = True,  # Create symlink instead of copy on Unix
)
```

**Key Features**:
- Uses hermetic coreutils toolchain (no system cp)
- Supports DirectoryPathInfo for directory references
- Multiple copy_file rules can coexist in same package (improved from skylib)
- Optional symlink creation for space efficiency

### copy_directory

Copies entire directory trees recursively.

**Load**:
```starlark
load("@bazel_lib//lib:copy_directory.bzl", "copy_directory")
```

**Usage**:
```starlark
copy_directory(
    name = "copy_assets",
    src = "//src:assets",
    out = "dist/assets",
)
```

**Features**:
- Preserves directory structure
- Fast native implementation
- Works with TreeArtifact outputs

### copy_to_directory

Most powerful directory assembly rule - combines multiple sources with filtering.

**Load**:
```starlark
load("@bazel_lib//lib:copy_to_directory.bzl", "copy_to_directory")
```

**Usage**:
```starlark
copy_to_directory(
    name = "assemble_dist",
    srcs = [
        "//app:compiled_js",
        "//assets:images",
        ":vendor_libs",
    ],
    root_paths = [
        "app/dist",  # Strip this prefix from app outputs
        "assets/static",  # Strip this from assets
    ],
    include_external_repositories = ["npm_*"],
    exclude_patterns = [
        "**/*.map",  # Exclude source maps
        "test/**",   # Exclude test files
    ],
    replace_prefixes = {
        "old/path": "new/path",
    },
)
```

**Key Features**:
- Glob pattern matching (include/exclude)
- Path prefix manipulation
- External repository filtering
- Handles filegroups, tree artifacts, and individual files
- Performance-critical operations in Go binary

### copy_to_bin

Copies source files to bazel-bin for consumption by rules expecting outputs.

**Load**:
```starlark
load("@bazel_lib//lib:copy_to_bin.bzl", "copy_to_bin")
```

**Usage**:
```starlark
copy_to_bin(
    name = "copy_srcs",
    srcs = glob(["src/**/*.ts"]),
)
```

**Use Case**: Many tools expect inputs in output directories, not source tree.

### directory_path

Creates references to subdirectories within tree artifacts.

**Load**:
```starlark
load("@bazel_lib//lib:directory_path.bzl", "directory_path")
```

**Usage**:
```starlark
directory_path(
    name = "subdir_ref",
    directory = ":some_tree_artifact",
    path = "nested/subdirectory",
)
```

**Provider**: Exposes `DirectoryPathInfo` for downstream consumption.

## Build Action Rules

### run_binary

Executes a binary as a build action - platform-independent alternative to genrule.

**Load**:
```starlark
load("@bazel_lib//lib:run_binary.bzl", "run_binary")
```

**Usage**:
```starlark
run_binary(
    name = "generate_code",
    tool = "//tools:generator",
    srcs = ["schema.json"],
    outs = ["generated.ts"],
    args = [
        "--input=$(location schema.json)",
        "--output=$(location generated.ts)",
    ],
    env = {
        "CONFIG_PATH": "$(location config.yaml)",
    },
)
```

**Improvements over skylib**:
- Directory output support
- Better makevar expansion
- Environment variable support
- No shell required

### expand_template

Template file expansion with variable substitutions.

**Load**:
```starlark
load("@bazel_lib//lib:expand_template.bzl", "expand_template")
```

**Usage**:
```starlark
expand_template(
    name = "gen_config",
    template = "config.template.yaml",
    out = "config.yaml",
    substitutions = {
        "{{VERSION}}": "1.0.0",
        "{{API_URL}}": "https://api.example.com",
    },
    stamp_substitutions = {
        "{{BUILD_TIMESTAMP}}": "BUILD_TIMESTAMP",
        "{{GIT_COMMIT}}": "STABLE_GIT_COMMIT",
    },
)

# Or with inline template
expand_template(
    name = "gen_inline",
    template = [
        "# Generated file",
        "version: {{VERSION}}",
    ],
    out = "version.txt",
    substitutions = {"{{VERSION}}": "2.0.0"},
)
```

**Features**:
- Fast native binary implementation
- Build stamping integration
- Inline templates via list of strings
- Multiple substitution dictionaries

### output_files

Extracts specific outputs from multi-output rules.

**Load**:
```starlark
load("@bazel_lib//lib:output_files.bzl", "output_files")
```

**Usage**:
```starlark
output_files(
    name = "just_js",
    target = ":typescript_compile",
    paths = ["*.js"],  # Only JS files, not .d.ts
)
```

## Source Tree Integration

### write_source_files

Write generated files back to source tree with automatic verification.

**Load**:
```starlark
load("@bazel_lib//lib:write_source_files.bzl", "write_source_files")
```

**Basic Usage**:
```starlark
write_source_files(
    name = "write_generated",
    files = {
        "api/generated.ts": "//tools:api_codegen",
        "README.md": ":readme_generator",
    },
)
```

Run to update:
```bash
bazel run //:write_generated
```

**Advanced Usage**:
```starlark
write_source_files(
    name = "write_all",
    files = {
        "src/api.ts": "//codegen:api",
        "docs/api.md": "//codegen:docs",
    },
    suggested_update_target = "//:update_all",
    diff_test = True,  # Creates automatic test
    diff_test_failure_message = "Generated files out of date. Run: bazel run {{SUGGESTED_UPDATE_TARGET}}",
    executable = False,  # Files not executable
)

# Tree of update targets
write_source_files(
    name = "update_all",
    additional_update_targets = [
        "//frontend:write_generated",
        "//backend:write_generated",
        "//docs:write_generated",
    ],
)
```

**How It Works**:
1. Creates runnable target to copy files to source
2. Generates `diff_test` targets checking files are up-to-date
3. Test failures show exact command to update
4. Supports hierarchical update targets

**Use Cases**:
- Code generation (protobuf, OpenAPI, GraphQL)
- Documentation generation
- Lock file updates
- Formatted output synchronization

## Starlark Utility Functions

### utils

General-purpose utilities for common Bazel operations.

**Load**:
```starlark
load("@bazel_lib//lib:utils.bzl", "utils")
```

**Key Functions**:

```starlark
# Convert string to Label
label = utils.to_label("//foo:bar")

# Check if file exists in sources
if utils.file_exists("config.json"):
    # ...

# Detect Bazel version
if utils.is_bazel_7_or_greater():
    # Use Bazel 7+ features

# Check if bzlmod enabled
if utils.is_bzlmod_enabled():
    # Bzlmod-specific logic

# Path to workspace root from output dir
root_path = utils.path_to_workspace_root()

# Check if label is external
is_external = utils.is_external_label(label)

# Propagate common attributes to generated rules
attrs = utils.propagate_common_rule_attributes(ctx)
```

### paths

Path manipulation utilities for runfiles and repository paths.

**Load**:
```starlark
load("@bazel_lib//lib:paths.bzl", "paths")
```

**Functions**:

```starlark
# Convert to rlocation path (for runtime file lookup)
rloc = paths.to_rlocation_path(ctx, file)

# Get repository-relative path
repo_path = paths.to_repository_relative_path(file)

# Get output-relative path
out_path = paths.to_output_relative_path(file)

# Make path relative to file
rel_path = paths.relative_file("a/b/c.txt", "a/d/e.txt")  # "../d/e.txt"
```

**Bash Helper**:
```starlark
# Include in sh_binary or sh_test
load("@bazel_lib//lib:paths.bzl", "BASH_RLOCATION_FUNCTION")

sh_test(
    name = "test",
    srcs = ["test.sh"],
    deps = ["@bazel_tools//tools/bash/runfiles"],
    data = [":data_files"],
    env = {"RUNFILES_LIB": BASH_RLOCATION_FUNCTION},
)
```

### strings

String manipulation utilities.

**Load**:
```starlark
load("@bazel_lib//lib:strings.bzl", "chr", "ord", "hex", "split_args")
```

**Usage**:
```starlark
# Character conversions
c = chr(65)  # "A"
n = ord("A")  # 65
h = hex(255)  # "ff"

# Split shell-style arguments
args = split_args('--flag "value with spaces" --other')
# ["--flag", "value with spaces", "--other"]
```

### lists

Functional programming operations on lists.

**Load**:
```starlark
load("@bazel_lib//lib:lists.bzl", "lists")
```

**Usage**:
```starlark
# Map transformation
doubled = lists.map(lambda x: x * 2, [1, 2, 3])  # [2, 4, 6]

# Filter
evens = lists.filter(lambda x: x % 2 == 0, [1, 2, 3, 4])  # [2, 4]

# Find first match
found = lists.find(lambda x: x > 5, [1, 8, 3, 10])  # 8

# Check all elements
all_positive = lists.every(lambda x: x > 0, [1, 2, 3])  # True

# Check any element
has_negative = lists.some(lambda x: x < 0, [1, -2, 3])  # True

# Remove duplicates
unique = lists.unique([1, 2, 2, 3, 1])  # [1, 2, 3]

# Pick specific indices
selected = lists.pick([10, 20, 30, 40], [0, 2])  # [10, 30]

# Ensure single element
value = lists.once([42])  # 42 (fails if list has != 1 element)
```

### base64

Base64 encoding/decoding.

**Load**:
```starlark
load("@bazel_lib//lib:base64.bzl", "base64")
```

**Usage**:
```starlark
encoded = base64.encode("hello world")
decoded = base64.decode(encoded)  # "hello world"
```

### glob_match

Glob pattern matching for filtering.

**Load**:
```starlark
load("@bazel_lib//lib:glob_match.bzl", "glob_match", "is_glob")
```

**Usage**:
```starlark
# Check if string is glob pattern
has_glob = is_glob("*.txt")  # True
has_glob = is_glob("file.txt")  # False

# Match path against pattern
matches = glob_match("**/*.js", "src/app/main.js")  # True
matches = glob_match("test/**", "test/unit/foo.js")  # True
matches = glob_match("*.py", "script.js")  # False
```

## Platform and Build Configuration

### transitions

Cross-compilation support via platform transitions.

**Load**:
```starlark
load("@bazel_lib//lib:transitions.bzl",
     "platform_transition_binary",
     "platform_transition_test",
     "platform_transition_filegroup")
```

**Usage**:
```starlark
# Build binary for different platform
platform_transition_binary(
    name = "linux_binary",
    binary = ":my_app",
    target_platform = "@platforms//os:linux",
)

# Run test on specific platform
platform_transition_test(
    name = "windows_test",
    binary = ":my_test",
    target_platform = "@platforms//os:windows",
)

# Transition files to target platform
platform_transition_filegroup(
    name = "arm_libs",
    srcs = [":native_libs"],
    target_platform = "@platforms//cpu:arm64",
)
```

### stamping

Build metadata injection.

**Load**:
```starlark
load("@bazel_lib//lib:stamping.bzl", "stamp_build_setting")
```

**Usage with expand_template**: (shown above in expand_template section)

Variables available:
- `BUILD_TIMESTAMP`: Build time
- `BUILD_USER`: User running build
- `STABLE_GIT_COMMIT`: Git commit hash
- Custom variables via workspace_status_command

## Configuration and Extension Points

### Bzlmod Extensions

**Load**:
```starlark
# In MODULE.bazel
bazel_lib_toolchains = use_extension("@bazel_lib//lib:extensions.bzl", "toolchains")

# Register specific toolchains
bazel_lib_toolchains.copy_directory()
bazel_lib_toolchains.copy_to_directory()
bazel_lib_toolchains.coreutils()
bazel_lib_toolchains.zstd()
bazel_lib_toolchains.expand_template()
bazel_lib_toolchains.bats()

# Optional version pinning
bazel_lib_toolchains.coreutils(version = "0.0.26")
```

## Integration Patterns

### With rules_js/rules_ts

```starlark
load("@bazel_lib//lib:copy_to_bin.bzl", "copy_to_bin")

# Copy TS sources to bin for transpilation
copy_to_bin(
    name = "ts_srcs",
    srcs = glob(["src/**/*.ts"]),
)

ts_project(
    name = "compile",
    srcs = [":ts_srcs"],
    # ...
)
```

### With protobuf

```starlark
load("@bazel_lib//lib:write_source_files.bzl", "write_source_files")

# Write generated protos to source
write_source_files(
    name = "write_protos",
    files = {
        "src/generated": ":proto_compile",
    },
)
```

### With rules_docker

```starlark
load("@bazel_lib//lib:copy_to_directory.bzl", "copy_to_directory")

copy_to_directory(
    name = "docker_context",
    srcs = [
        ":app_binary",
        ":config_files",
        "//static:assets",
    ],
)

container_image(
    name = "image",
    directory = ":docker_context",
    # ...
)
```

### Multi-platform Builds

```starlark
load("@bazel_lib//lib:transitions.bzl", "platform_transition_binary")

[platform_transition_binary(
    name = "app_" + platform,
    binary = ":app",
    target_platform = "@platforms//os:" + platform,
) for platform in ["linux", "macos", "windows"]]
```

These APIs provide comprehensive building blocks for sophisticated Bazel build configurations while maintaining platform independence and hermetic operation.
