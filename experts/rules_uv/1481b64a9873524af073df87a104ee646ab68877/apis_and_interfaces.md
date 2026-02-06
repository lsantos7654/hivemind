# rules_uv - APIs and Interfaces

## Public APIs and Entry Points

Rules_uv provides two main entry points for users:

### pip_compile - Requirements Compilation

**Import**: `load("@rules_uv//uv:pip.bzl", "pip_compile")`

**Purpose**: Compiles `requirements.in` or `pyproject.toml` files into locked `requirements.txt` files with cryptographic hashes.

**Signature**:
```starlark
pip_compile(
    name,
    requirements_in = None,
    requirements_overrides = None,
    requirements_txt = None,
    target_compatible_with = None,
    python_platform = None,
    universal = False,
    args = None,
    extra_args = None,
    data = None,
    tags = None,
    size = None,
    timeout = None,
    env = None,
    **kwargs
)
```

**Parameters**:
- **name** (required): Name of the primary compilation target
- **requirements_in** (optional): Label for input file or list of requirement strings
  - Default: `"//:requirements.in"`
  - Can be a file path or inline list: `["requests==2.31.0", "flask~=3.0"]`
- **requirements_overrides** (optional): Label for overrides file (passed to `uv --overrides`)
- **requirements_txt** (optional): Label for output file
  - Default: `"//:requirements.txt"`
- **python_platform** (optional): Platform string for cross-platform compilation
  - Examples: `"x86_64-unknown-linux-gnu"`, `"aarch64-apple-darwin"`
- **universal** (optional): Use uv's `--universal` flag for platform-agnostic wheels
  - Default: `False`
- **target_compatible_with** (optional): Bazel platform constraints
- **args** (optional): Override default uv arguments
  - Default: `["--generate-hashes", "--emit-index-url", "--no-strip-extras"]`
- **extra_args** (optional): Additional arguments appended to defaults
- **data** (optional): Additional files needed during compilation
- **tags** (optional): Tags for the test target
  - Automatically includes `"requires-network"`
- **size** (optional): Test size (small/medium/large/enormous)
  - Default: `"small"`
- **timeout** (optional): Test timeout override
- **env** (optional): Dictionary of environment variables for uv
- **kwargs**: Additional attributes passed to underlying rules

**Targets Created**:
1. `[name]`: Executable target that updates requirements_txt
2. `[name].update`: Alias for compatibility with rules_python
3. `[name]_test`: Test that verifies requirements_txt is up-to-date

### create_venv - Virtual Environment Creation

**Import**: `load("@rules_uv//uv:venv.bzl", "create_venv")`

**Purpose**: Creates a new Python virtual environment and installs packages from requirements.txt.

**Signature**:
```starlark
create_venv(
    name,
    requirements_txt = None,
    target_compatible_with = None,
    destination_folder = None,
    site_packages_extra_files = [],
    uv_args = []
)
```

**Parameters**:
- **name** (required): Name of the venv creation target
- **requirements_txt** (optional): Label for requirements file
  - Default: `"//:requirements.txt"`
- **target_compatible_with** (optional): Bazel platform constraints
- **destination_folder** (optional): Default venv path
  - Default: `"venv"`
  - Can be overridden at runtime with command-line argument
- **site_packages_extra_files** (optional): Files to copy into site-packages
  - Useful for `sitecustomize.py`, `.pth` files
- **uv_args** (optional): Additional arguments passed to `uv pip install`

**Runtime Usage**:
```bash
# Use default destination
bazel run //:create_venv

# Specify custom destination
bazel run //:create_venv -- .venv
```

### sync_venv - Virtual Environment Synchronization

**Import**: `load("@rules_uv//uv:venv.bzl", "sync_venv")`

**Purpose**: Synchronizes an existing virtual environment to exactly match requirements.txt (removes extraneous packages).

**Signature**: Identical to `create_venv`

**Difference from create_venv**:
- Uses `uv pip sync` instead of `uv pip install`
- More deterministic: removes packages not in requirements.txt
- Better for CI/CD where exact reproducibility matters
- Allows existing venv with `--allow-existing` flag

## Key Classes, Functions, and Macros

### pip_compile Implementation (uv/private/pip.bzl)

**Rule: pip_compile**

Internal rule that implements the compilation logic:

```starlark
pip_compile = rule(
    attrs = _COMMON_ATTRS | {
        "_template": attr.label(default = "//uv/private:pip_compile.sh", allow_single_file = True),
    },
    toolchains = ["@bazel_tools//tools/python:toolchain_type"],
    implementation = _pip_compile_impl,
    executable = True,
)
```

**Key Attributes**:
- `requirements_in`: Input requirements file (mandatory)
- `requirements_txt`: Output requirements file (mandatory)
- `python_platform`: Platform string for cross-compilation
- `universal`: Boolean for universal wheel selection
- `py3_runtime`: Optional explicit Python runtime
- `data`: Additional files for runfiles
- `uv_args`: Arguments passed to uv (default: hashes, index URL, preserve extras)
- `extra_args`: Additional arguments
- `env`: Environment variables dictionary
- `_uv`: Private attribute resolving to uv binary via rules_multitool

**Implementation Highlights**:
```starlark
def _pip_compile_impl(ctx):
    # Resolve Python runtime from toolchain
    py3_runtime = _python_runtime(ctx)

    # Extract Python version (major.minor.micro)
    version = _python_version(py3_runtime)

    # Build uv command arguments
    args = ctx.attr.uv_args + ctx.attr.extra_args
    args.append("--python={path}".format(path = python_interpreter_path(py3_runtime)))
    args.append("--python-version={version}".format(version = version))

    if ctx.attr.python_platform:
        args.append("--python-platform={platform}".format(platform = ctx.attr.python_platform))

    # Expand shell script template
    ctx.actions.expand_template(
        template = ctx.file._template,
        output = executable,
        substitutions = {
            "{{uv}}": ctx.executable._uv.short_path,
            "{{args}}": " \\\n    ".join(args),
            "{{requirements_in}}": ctx.file.requirements_in.short_path,
            "{{requirements_txt}}": ctx.file.requirements_txt.short_path,
        },
    )

    # Return executable with runfiles
    return [DefaultInfo(executable = executable, runfiles = runfiles)]
```

**Rule: pip_compile_test**

Similar to `pip_compile` but configured as a test:
- Uses `pip_compile_test.sh` template
- Includes `RunEnvironmentInfo` with `HOME` in inherited environment (for .netrc)
- Runs with `test = True` attribute
- Fails if requirements.txt doesn't match fresh compilation

### Venv Implementation (uv/private/venv.bzl)

**Rule: _venv (internal)**

```starlark
_venv = rule(
    attrs = {
        "destination_folder": attr.string(default = "venv"),
        "site_packages_extra_files": attr.label_list(default = [], allow_files = True),
        "requirements_txt": attr.label(mandatory = True, allow_single_file = True),
        "_uv": attr.label(default = "@multitool//tools/uv", executable = True, cfg = transition_to_target),
        "template": attr.label(allow_single_file = True),
        "uv_args": attr.string_list(default = []),
    },
    toolchains = ["@bazel_tools//tools/python:toolchain_type"],
    implementation = _venv_impl,
    executable = True,
)
```

**Template Expansion**:
```starlark
def _uv_template(ctx, template, executable):
    py_toolchain = ctx.toolchains["@bazel_tools//tools/python:toolchain_type"]

    ctx.actions.expand_template(
        template = template,
        output = executable,
        substitutions = {
            "{{uv}}": ctx.executable._uv.short_path,
            "{{requirements_txt}}": ctx.file.requirements_txt.short_path,
            "{{resolved_python}}": python_interpreter_path(py_toolchain.py3_runtime),
            "{{destination_folder}}": ctx.attr.destination_folder,
            "{{site_packages_extra_files}}": " ".join(["'" + f.short_path + "'" for f in ctx.files.site_packages_extra_files]),
            "{{args}}": " \\\n    ".join(ctx.attr.uv_args),
        },
    )
```

**Functions: create_venv and sync_venv**

Wrapper functions that call `_venv` with different templates:

```starlark
def create_venv(name, requirements_txt = None, target_compatible_with = None,
                destination_folder = None, site_packages_extra_files = [], uv_args = []):
    _venv(
        name = name,
        destination_folder = destination_folder,
        site_packages_extra_files = site_packages_extra_files,
        requirements_txt = requirements_txt or "//:requirements.txt",
        target_compatible_with = target_compatible_with,
        uv_args = uv_args,
        template = Label("//uv/private:create_venv.sh"),
    )

def sync_venv(name, ...):
    # Same as create_venv but with different template
    _venv(..., template = Label("//uv/private:sync_venv.sh"))
```

### Helper Functions

**python_interpreter_path** (uv/private/interpreter_path.bzl):
```starlark
def python_interpreter_path(py3_runtime):
    """Returns path to Python interpreter, handling both hermetic and system toolchains."""
    if py3_runtime.interpreter:
        return py3_runtime.interpreter.short_path  # Hermetic
    return py3_runtime.interpreter_path  # System
```

**transition_to_target** (uv/private/transition_to_target.bzl):
```starlark
def _transition_to_target_impl(settings, _attr):
    """Ensures uv binary is built for target platform, not exec platform."""
    return {
        "//command_line_option:extra_execution_platforms": [
            str(platform) for platform in settings["//command_line_option:platforms"]
        ],
    }

transition_to_target = transition(
    implementation = _transition_to_target_impl,
    inputs = ["//command_line_option:platforms"],
    outputs = ["//command_line_option:extra_execution_platforms"],
)
```

## Usage Examples with Code Snippets

### Example 1: Basic Requirements Compilation

```starlark
# BUILD.bazel
load("@rules_uv//uv:pip.bzl", "pip_compile")

pip_compile(
    name = "requirements",
)
```

**Files needed**:
- `requirements.in`: Input file with unpinned dependencies
- `requirements.txt`: Output file (can be empty initially)

**Commands**:
```bash
# Update requirements.txt
bazel run //:requirements

# Verify requirements.txt is current
bazel test //:requirements_test
```

### Example 2: Multi-Platform Requirements

```starlark
# BUILD.bazel
load("@rules_multirun//:defs.bzl", "multirun")
load("@rules_uv//uv:pip.bzl", "pip_compile")

pip_compile(
    name = "requirements_linux",
    python_platform = "x86_64-unknown-linux-gnu",
    requirements_txt = "requirements_linux.txt",
)

pip_compile(
    name = "requirements_macos",
    python_platform = "aarch64-apple-darwin",
    requirements_txt = "requirements_macos.txt",
)

multirun(
    name = "requirements_all",
    commands = [
        ":requirements_linux",
        ":requirements_macos",
    ],
    jobs = 1,  # Sequential for cache reuse
)
```

**Usage**:
```bash
# Generate all platform-specific requirements
bazel run //:requirements_all

# Test all are up-to-date
bazel test //:requirements_linux_test //:requirements_macos_test
```

### Example 3: Inline Requirements

```starlark
# BUILD.bazel
load("@rules_uv//uv:pip.bzl", "pip_compile")

pip_compile(
    name = "tools",
    requirements_in = [
        "black==24.3.0",
        "ruff~=0.3.0",
        "mypy>=1.9.0",
    ],
    requirements_txt = "tools.txt",
)
```

### Example 4: Virtual Environment Creation

```starlark
# BUILD.bazel
load("@rules_uv//uv:pip.bzl", "pip_compile")
load("@rules_uv//uv:venv.bzl", "create_venv")

pip_compile(name = "requirements")

create_venv(
    name = "venv",
    requirements_txt = "//:requirements.txt",
)
```

**Usage**:
```bash
# Create venv in ./venv
bazel run //:venv

# Create venv in custom location
bazel run //:venv -- .venv

# Activate venv
source .venv/bin/activate
```

### Example 5: Multiple Python Versions

```starlark
# MODULE.bazel
python = use_extension("@rules_python//python/extensions:python.bzl", "python")
python.toolchain(python_version = "3.10")
python.toolchain(python_version = "3.11")

# BUILD.bazel
load("@rules_uv//uv:pip.bzl", "pip_compile")

pip_compile(
    name = "requirements_py310",
    py3_runtime = "@python_3_10//:py3_runtime",
    requirements_txt = "requirements_3_10.txt",
)

pip_compile(
    name = "requirements_py311",
    py3_runtime = "@python_3_11//:py3_runtime",
    requirements_txt = "requirements_3_11.txt",
)
```

### Example 6: Requirements with Additional Data Files

```starlark
# BUILD.bazel
load("@rules_uv//uv:pip.bzl", "pip_compile")

pip_compile(
    name = "requirements",
    requirements_in = "//:requirements.in",
    requirements_txt = "//:requirements.txt",
    data = [
        "//:requirements.test.in",  # Referenced in requirements.in via -r
        "//:constraints.txt",       # Additional constraints
    ],
)
```

**requirements.in**:
```
flask>=3.0
-r requirements.test.in
-c constraints.txt
```

### Example 7: Custom Site-Packages Files

```starlark
# BUILD.bazel
load("@bazel_skylib//rules:write_file.bzl", "write_file")
load("@rules_uv//uv:venv.bzl", "create_venv")

write_file(
    name = "sitecustomize_gen",
    out = "sitecustomize.py",
    content = [
        "import sys",
        "print('Custom site initialized')",
    ],
)

create_venv(
    name = "venv",
    destination_folder = ".venv",
    site_packages_extra_files = [
        ":sitecustomize.py",
        "//config:custom.pth",
    ],
)
```

**Effect**: Files are copied into `site-packages/` and made writable automatically.

### Example 8: Platform-Specific Venv Selection

```starlark
# BUILD.bazel
load("@rules_uv//uv:pip.bzl", "pip_compile")
load("@rules_uv//uv:venv.bzl", "create_venv")

pip_compile(
    name = "requirements_linux",
    python_platform = "x86_64-unknown-linux-gnu",
    requirements_txt = "requirements_linux.txt",
)

pip_compile(
    name = "requirements_macos",
    python_platform = "aarch64-apple-darwin",
    requirements_txt = "requirements_macos.txt",
)

create_venv(
    name = "venv",
    requirements_txt = select({
        "@platforms//os:linux": ":requirements_linux.txt",
        "@platforms//os:osx": ":requirements_macos.txt",
    }),
)
```

**Result**: Venv uses platform-appropriate requirements automatically.

## Integration Patterns and Workflows

### Workflow 1: Development Cycle

```bash
# 1. Add dependency to requirements.in
echo "requests>=2.31.0" >> requirements.in

# 2. Compile to locked requirements.txt
bazel run //:requirements

# 3. Update local venv
bazel run //:venv

# 4. Activate and develop
source venv/bin/activate
python my_script.py

# 5. Before commit, ensure tests pass
bazel test //:requirements_test
```

### Workflow 2: CI/CD Integration

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Verify requirements are up-to-date
      - name: Check requirements
        run: bazel test //:requirements_test

      # Run application tests
      - name: Run tests
        run: bazel test //...
```

### Workflow 3: Integration with rules_python

```starlark
# MODULE.bazel
bazel_dep(name = "rules_python", version = "0.34.0")
bazel_dep(name = "rules_uv", version = "0.40.0")

# Use rules_uv to generate requirements
pip = use_extension("@rules_python//python/extensions:pip.bzl", "pip")
pip.parse(
    hub_name = "pip",
    python_version = "3.11",
    requirements_lock = "//:requirements.txt",  # Generated by rules_uv
)
use_repo(pip, "pip")
```

```starlark
# BUILD.bazel
load("@pip//:requirements.bzl", "requirement")
load("@rules_python//python:defs.bzl", "py_binary")
load("@rules_uv//uv:pip.bzl", "pip_compile")

# Use rules_uv to manage requirements.txt
pip_compile(name = "requirements")

# Use rules_python to consume it
py_binary(
    name = "app",
    srcs = ["app.py"],
    deps = [
        requirement("flask"),
        requirement("requests"),
    ],
)
```

### Workflow 4: Monorepo with Multiple Projects

```starlark
# //backend/BUILD.bazel
load("@rules_uv//uv:pip.bzl", "pip_compile")

pip_compile(
    name = "requirements",
    requirements_in = "requirements.in",
    requirements_txt = "requirements.txt",
)

# //frontend/BUILD.bazel
pip_compile(
    name = "requirements",
    requirements_in = "requirements.in",
    requirements_txt = "requirements.txt",
)

# //tools/BUILD.bazel
pip_compile(
    name = "requirements",
    requirements_in = ["black", "ruff", "mypy"],
    requirements_txt = "requirements.txt",
)
```

Each project maintains independent requirements with isolated compilation.

## Configuration Options and Extension Points

### Environment Variables

**Passed via `env` parameter**:
```starlark
pip_compile(
    name = "requirements",
    env = {
        "PIP_INDEX_URL": "https://pypi.custom.org/simple",
        "UV_EXTRA_INDEX_URL": "https://private.pypi.org/simple",
        "UV_NO_CACHE": "1",
    },
)
```

**Inherited from environment** (pip_compile_test only):
- `HOME`: Needed for `.netrc` authentication

### Custom uv Arguments

**Override defaults**:
```starlark
pip_compile(
    name = "requirements",
    args = [
        "--no-generate-hashes",  # Skip hashes
        "--no-annotate",         # Skip comments
    ],
)
```

**Extend defaults**:
```starlark
pip_compile(
    name = "requirements",
    extra_args = [
        "--index-url=https://pypi.org/simple",
        "--trusted-host=pypi.org",
    ],
)
```

### Requirements Overrides

```starlark
# BUILD.bazel
pip_compile(
    name = "requirements",
    requirements_overrides = "overrides.txt",
)
```

**overrides.txt**:
```
# Force specific version
numpy==1.24.0

# Exclude problematic package
--no-binary :all:
```

### Platform Constraints

```starlark
pip_compile(
    name = "requirements_linux",
    target_compatible_with = [
        "@platforms//os:linux",
    ],
)
```

This target will only build/test on Linux platforms.

### Test Configuration

```starlark
pip_compile(
    name = "requirements",
    size = "medium",        # More time for large dependency sets
    timeout = "long",       # Override timeout
    tags = ["manual"],      # Exclude from wildcard tests
)
```

### Extension via Wrapping

Users can wrap rules_uv macros for organization-specific defaults:

```starlark
# //build_defs:python.bzl
load("@rules_uv//uv:pip.bzl", _pip_compile = "pip_compile")

def pip_compile(name, **kwargs):
    """Company-specific pip_compile with defaults."""
    _pip_compile(
        name = name,
        env = kwargs.pop("env", {}) | {
            "PIP_INDEX_URL": "https://pypi.company.com/simple",
        },
        extra_args = kwargs.pop("extra_args", []) + [
            "--cert=/etc/ssl/certs/company-ca.pem",
        ],
        tags = kwargs.pop("tags", []) + ["requires-vpn"],
        **kwargs
    )
```
