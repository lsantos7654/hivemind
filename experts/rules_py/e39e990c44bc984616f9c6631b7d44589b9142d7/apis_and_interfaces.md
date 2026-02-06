# rules_py APIs and Interfaces

## Public APIs and Entry Points

### Core Python Rules (`@aspect_rules_py//py:defs.bzl`)

The main public API surface provides drop-in replacements for rules_python rules:

```python
load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_library", "py_test", "py_venv")
```

## Key Rules and Macros

### py_library

Collects Python source files and dependencies into a reusable library.

**Signature**:
```python
py_library(
    name,
    srcs = [],
    deps = [],
    imports = [],
    data = [],
    visibility = None,
)
```

**Attributes**:
- `name`: Target name
- `srcs`: List of `.py` files
- `deps`: Python library dependencies (other `py_library` or `py_binary` targets)
- `imports`: Import paths to add to `PYTHONPATH` (relative to workspace root)
- `data`: Non-Python files available at runtime

**Example**:
```python
py_library(
    name = "mylib",
    srcs = ["mylib.py"],
    deps = [
        "@pypi//requests",
        "//utils:common",
    ],
    imports = ["."],
)
```

**Provider output**: `PyInfo` (compatible with rules_python)

### py_binary

Creates an executable Python program with an isolated virtualenv.

**Signature**:
```python
py_binary(
    name,
    srcs = [],
    main = None,
    deps = [],
    data = [],
    env = {},
    python_version = None,
    venv = None,
    resolutions = None,
    imports = [],
    interpreter_options = [],
    package_collisions = "error",
)
```

**Key attributes**:
- `main`: Entry point file (suffix of a file in srcs). If absent, uses `[name].py` or the single file in srcs
- `env`: Environment variables to set at runtime
- `python_version`: Python version to use (e.g., "3.9", "3.12")
- `venv`: uv venv configuration name (when using uv extension)
- `resolutions`: Virtual dependency resolutions (see virtual_deps.md)
- `interpreter_options`: Flags passed to Python interpreter (e.g., `["-u", "-O"]`)
- `package_collisions`: How to handle name collisions ("error", "ignore", "warning")

**Automatic targets created**:
- `{name}`: The executable binary
- `{name}.venv`: IDE-compatible virtualenv (run with `bazel run {name}.venv`)

**Example**:
```python
py_binary(
    name = "server",
    srcs = ["server.py"],
    main = "server.py",
    deps = [
        "@pypi//flask",
        "@pypi//gunicorn",
        "//app:handlers",
    ],
    env = {
        "PORT": "8080",
        "LOG_LEVEL": "info",
    },
    python_version = "3.12",
)
```

**Run the binary**:
```bash
bazel run //:server
```

**Generate virtualenv for IDE**:
```bash
bazel run //:server.venv
# Creates a virtualenv symlink at bazel-bin/server.venv
# Point your IDE Python interpreter to bazel-bin/server.venv/bin/python
```

### py_test

Identical to `py_binary` but integrated with Bazel's test framework.

**Signature**:
```python
py_test(
    name,
    srcs = [],
    main = None,
    deps = [],
    data = [],
    pytest_main = False,
    size = None,
    timeout = None,
    flaky = False,
    **kwargs,
)
```

**Additional attributes**:
- `pytest_main`: If True, generates a pytest main entrypoint automatically
- `size`: Test size ("small", "medium", "large", "enormous")
- `timeout`: Test timeout ("short", "moderate", "long", "eternal")
- `flaky`: Allow test to be retried if it fails

**Example with unittest**:
```python
py_test(
    name = "unit_test",
    srcs = ["unit_test.py"],
    deps = [
        ":mylib",
        "@pypi//mock",
    ],
)
```

**Example with pytest**:
```python
py_test(
    name = "integration_test",
    srcs = ["test_integration.py"],
    pytest_main = True,  # Auto-generates pytest runner
    deps = [
        ":mylib",
        "@pypi//pytest",
        "@pypi//pytest_asyncio",
    ],
    data = ["testdata/config.json"],
    size = "medium",
)
```

### py_venv (py_venv_link)

Creates a virtualenv symlink for IDE integration.

**Signature**:
```python
py_venv(
    name,
    srcs = [],
    deps = [],
    data = [],
    imports = [],
)
```

This is automatically created as `{binary_name}.venv` when you define a `py_binary` or `py_test`.

**Manual usage**:
```python
py_venv(
    name = "dev_venv",
    deps = [
        "@pypi//ipython",
        "@pypi//black",
        "@pypi//mypy",
        "//src:myapp",
    ],
)
```

Then run: `bazel run //:dev_venv`

## Advanced Rules

### py_pex_binary

Creates a Python executable in PEX (Python EXecutable) format.

**Signature**:
```python
load("@aspect_rules_py//py:defs.bzl", "py_pex_binary")

py_pex_binary(
    name,
    binary,
    zip_safe = True,
)
```

**Attributes**:
- `binary`: A `py_binary` target to package
- `zip_safe`: Whether to create a zip file or directory

**Example**:
```python
py_binary(
    name = "app_bin",
    srcs = ["main.py"],
    deps = ["@pypi//requests"],
)

py_pex_binary(
    name = "app.pex",
    binary = ":app_bin",
)
```

### py_pytest_main

Generates a pytest main entrypoint file.

**Signature**:
```python
py_pytest_main(name)
```

This is automatically used when `pytest_main = True` in `py_test`.

**Manual usage**:
```python
py_pytest_main(name = "pytest_runner")

py_test(
    name = "test",
    srcs = [
        "test_foo.py",
        "test_bar.py",
        ":pytest_runner",  # Uses generated main
    ],
    main = "pytest_runner.py",
    deps = ["@pypi//pytest"],
)
```

### py_image_layer

Creates OCI image layers from a Python binary for containerization.

**Signature**:
```python
load("@aspect_rules_py//py:defs.bzl", "py_image_layer")

py_image_layer(
    name,
    binary,
)
```

**Example with rules_oci**:
```python
load("@aspect_rules_py//py:defs.bzl", "py_binary", "py_image_layer")
load("@rules_oci//oci:defs.bzl", "oci_image", "oci_tarball")

py_binary(
    name = "app",
    srcs = ["app.py"],
    deps = ["@pypi//flask"],
)

py_image_layer(
    name = "app_layer",
    binary = ":app",
)

oci_image(
    name = "image",
    base = "@distroless_python",
    tars = [":app_layer"],
    entrypoint = ["/app"],
)

oci_tarball(
    name = "tarball",
    image = ":image",
    repo_tags = ["myapp:latest"],
)
```

## uv Extension API (`@aspect_rules_py//uv/unstable:extension.bzl`)

The uv dependency management system provides an alternative to rules_python's `pip.parse()`.

### Extension Configuration

**In MODULE.bazel**:
```python
uv = use_extension("@aspect_rules_py//uv/unstable:extension.bzl", "uv")

# Step 1: Declare a hub (central dependency repository)
uv.declare_hub(
    hub_name = "pypi",  # Name of your dependency hub
)

# Step 2: Declare virtual environments within the hub
uv.declare_venv(
    hub_name = "pypi",
    venv_name = "default",  # Name of this venv
)

# Step 3: Associate a lockfile with the venv
uv.lockfile(
    hub_name = "pypi",
    venv_name = "default",
    src = "//:uv.lock",  # Path to uv.lock file
)

# Step 4: (Optional) Annotate requirements
uv.unstable_annotate_requirements(
    hub_name = "pypi",
    venv_name = "default",
    src = "//:annotations.toml",
)

# Step 5: (Optional) Override requirements with Bazel targets
uv.override_requirement(
    hub_name = "pypi",
    venv_name = "default",
    requirement = "mypackage",
    target = "//third_party/py:mypackage",
)

# Step 6: Make the hub available
use_repo(uv, "pypi")
```

**In .bazelrc**:
```
# Set default venv for all builds
common --@pypi//venv=default
```

### Using Dependencies

**In BUILD files**:
```python
py_binary(
    name = "app",
    srcs = ["app.py"],
    deps = [
        "@pypi//requests",
        "@pypi//flask",
    ],
    venv = "default",  # Optional: override default venv
)
```

### Multiple Virtual Environments

```python
# In MODULE.bazel
uv.declare_venv(hub_name = "pypi", venv_name = "prod")
uv.lockfile(hub_name = "pypi", venv_name = "prod", src = "//:uv-prod.lock")

uv.declare_venv(hub_name = "pypi", venv_name = "dev")
uv.lockfile(hub_name = "pypi", venv_name = "dev", src = "//:uv-dev.lock")

# In BUILD file
py_binary(
    name = "app_prod",
    srcs = ["app.py"],
    deps = ["@pypi//flask"],
    venv = "prod",  # Uses production dependencies
)

py_test(
    name = "app_test",
    srcs = ["app_test.py"],
    deps = [
        "@pypi//flask",
        "@pypi//pytest",
    ],
    venv = "dev",  # Includes dev dependencies
)
```

### Annotations File Format

**annotations.toml**:
```toml
version = "0.0.0"

[[package]]
name = "psycopg2-binary"
native = true  # Has C extensions

[[package]]
name = "numpy"
native = true
build-dependencies = [
    {name = "cython"},
    {name = "setuptools"},
]

[[package]]
name = "mypy"
entry-points.console-scripts = { mypy = "mypy.__main__:console_entry" }
```

**Annotation purposes**:
- `native = true`: Marks packages with C/C++/Rust extensions
- `build-dependencies`: Additional packages needed to build from sdist
- `entry-points.console-scripts`: Declare command-line entry points

### Declaring Entrypoints

```python
# In MODULE.bazel
uv.declare_entrypoint(
    requirement = "black",
    name = "black",
    entrypoint = "black:patched_main",
)

# In BUILD file
load("@pypi//:defs.bzl", "py_entrypoint_binary")

py_entrypoint_binary(
    name = "black_tool",
    requirement = "black",
    entrypoint = "black",
)
```

### Cross-Platform Builds

```python
# Define target platform
platform(
    name = "linux_arm64",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:aarch64",
    ],
    flags = [
        "--@aspect_rules_py//uv/private/constraints/platform:platform_libc=glibc",
        "--@aspect_rules_py//uv/private/constraints/platform:platform_version=2.35",
    ],
)

# Build for target platform
py_binary(
    name = "app",
    srcs = ["app.py"],
    deps = ["@pypi//numpy"],  # Will select appropriate wheel
)

# Cross-compile
bazel build --platforms=//:linux_arm64 //:app
```

## Integration Patterns

### Virtual Dependency Resolution

Handle dependency version conflicts using virtual dependencies:

```python
load("@aspect_rules_py//py:defs.bzl", "py_binary", "resolutions")

py_binary(
    name = "app",
    srcs = ["app.py"],
    deps = [
        "//lib:uses_django_4_1",
        "//api:uses_django_4_2",
    ],
    # Resolve conflicting Django versions
    resolutions = resolutions({
        "django": "@django_4_2",
    }),
)
```

See `docs/virtual_deps.md` for full documentation.

### Gazelle Integration

Generate BUILD files automatically:

**In root BUILD.bazel**:
```python
# gazelle:map_kind py_library py_library @aspect_rules_py//py:defs.bzl
# gazelle:map_kind py_binary py_binary @aspect_rules_py//py:defs.bzl
# gazelle:map_kind py_test py_test @aspect_rules_py//py:defs.bzl
```

Run: `bazel run //:gazelle`

### Python Version Selection

```python
# Use specific Python version
py_binary(
    name = "app_py39",
    srcs = ["app.py"],
    python_version = "3.9",
)

py_binary(
    name = "app_py312",
    srcs = ["app.py"],
    python_version = "3.12",
)
```

**Register multiple toolchains in MODULE.bazel**:
```python
python = use_extension("@rules_python//python/extensions:python.bzl", "python")
python.toolchain(python_version = "3.9", is_default = True)
python.toolchain(python_version = "3.12", is_default = False)
```

## Configuration Options

### Package Collision Handling

```python
py_binary(
    name = "app",
    srcs = ["app.py"],
    deps = ["@pypi//multiple", "@pypi//packages"],
    package_collisions = "warning",  # "error" | "warning" | "ignore"
)
```

### Interpreter Options

```python
py_binary(
    name = "app",
    srcs = ["app.py"],
    interpreter_options = [
        "-u",  # Unbuffered output
        "-O",  # Optimize bytecode
        "-B",  # Don't write .pyc files
    ],
)
```

### Environment Variables

```python
py_binary(
    name = "app",
    srcs = ["app.py"],
    env = {
        "LOG_LEVEL": "$(LOG_LEVEL)",  # Expand from --action_env
        "CONFIG_PATH": "$(location config.json)",  # Expand from data
    },
    data = ["config.json"],
)
```

## Extension Points

### Custom Toolchains

Create custom Python toolchains:

```python
load("@aspect_rules_py//py:toolchains.bzl", "py_toolchain")

py_toolchain(
    name = "my_python_toolchain",
    python = "@python_3_11//:python",
    files = "@python_3_11//:files",
    interpreter_version_info = {
        "major": "3",
        "minor": "11",
        "micro": "0",
    },
)
```

### Virtual Dependency Providers

Implement custom dependency resolution:

```python
load("@aspect_rules_py//py/private:providers.bzl", "PyVirtualInfo")

def _virtual_resolver_impl(ctx):
    return [PyVirtualInfo(
        targets = {
            "package_name": ctx.attr.resolution,
        }
    )]
```

## Best Practices

### Dependency Management

1. **Use a single hub**: One `@pypi` hub for all dependencies
2. **Multiple venvs**: Separate prod/dev/test dependency sets
3. **Lock everything**: Always use uv.lock for reproducibility
4. **Annotate native packages**: Mark C extensions in annotations.toml

### Build Performance

1. **Minimize imports**: Only add necessary import paths
2. **Use data sparingly**: Large data files slow down caching
3. **Split libraries**: Smaller targets enable better parallelism
4. **Cache venvs**: Reuse `.venv` targets for IDE work

### Testing Strategy

1. **Use pytest_main**: Simplifies test file discovery
2. **Size tests appropriately**: Set size/timeout for reliability
3. **Isolate test data**: Use data attribute, not hard-coded paths
4. **Test multiple versions**: Ensure compatibility across Python versions
