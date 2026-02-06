# rules_python APIs and Interfaces

## Public APIs and Entry Points

### Core Python Rules

The primary entry points are the standard Python build rules accessible via `@rules_python//python:defs.bzl`:

**py_library** - Creates a Python library target
```starlark
load("@rules_python//python:py_library.bzl", "py_library")

py_library(
    name = "mylib",
    srcs = ["mylib.py"],
    deps = [
        ":other_lib",
        "@pypi//numpy",
    ],
    imports = ["src"],  # Add to PYTHONPATH
    data = ["data.json"],
    visibility = ["//visibility:public"],
)
```

**py_binary** - Creates an executable Python program
```starlark
load("@rules_python//python:py_binary.bzl", "py_binary")

py_binary(
    name = "main",
    srcs = ["main.py"],
    main = "main.py",  # Entry point
    deps = [":mylib"],
    env = {"MY_VAR": "value"},
    python_version = "PY3",  # Must be PY3 (PY2 deprecated)
)
```

**py_test** - Creates a Python test target
```starlark
load("@rules_python//python:py_test.bzl", "py_test")

py_test(
    name = "mylib_test",
    srcs = ["mylib_test.py"],
    deps = [
        ":mylib",
        "@pypi//pytest",
    ],
    size = "small",  # small, medium, large, enormous
)
```

**py_runtime** - Defines a Python interpreter runtime
```starlark
load("@rules_python//python:py_runtime.bzl", "py_runtime")

py_runtime(
    name = "my_runtime",
    interpreter_path = "/usr/bin/python3",
    python_version = "PY3",
)
```

**py_runtime_pair** - Pairs PY2 and PY3 runtimes (PY2 support removed)
```starlark
load("@rules_python//python:py_runtime_pair.bzl", "py_runtime_pair")

py_runtime_pair(
    name = "runtime_pair",
    py3_runtime = ":my_runtime",
)
```

### PyPI Integration

**Module Extension (Bzlmod)** - Preferred method for modern projects
```starlark
# In MODULE.bazel
pip = use_extension("@rules_python//python/extensions:pip.bzl", "pip")

pip.parse(
    hub_name = "pypi",
    python_version = "3.11",
    requirements_lock = "//:requirements.txt",
    requirements_by_platform = {
        "//:requirements_linux.txt": "linux_*",
        "//:requirements_darwin.txt": "osx_*",
    },
    experimental_index_url = "https://pypi.org/simple",
    experimental_extra_index_urls = ["https://custom.pypi.org/simple"],
    envsubst = [
        "PIP_INDEX_URL",
    ],
)
use_repo(pip, "pypi")

# Override specific packages
pip.override(
    file = "numpy-1.26.0-cp311-cp311-linux_x86_64.whl",
    patches = ["//patches:numpy.patch"],
    patch_strip = 1,
)
```

**Repository Rule (WORKSPACE)** - Legacy method
```starlark
# In WORKSPACE
load("@rules_python//python:pip.bzl", "pip_parse")

pip_parse(
    name = "pypi",
    python_interpreter_target = "@python_3_11_host//:python",
    requirements_lock = "//:requirements.txt",
    quiet = False,
    timeout = 600,
)

load("@pypi//:requirements.bzl", "install_deps")
install_deps()
```

**Requirements Compilation** - Generate lock files
```starlark
load("@rules_python//python:pip.bzl", "compile_pip_requirements")

compile_pip_requirements(
    name = "requirements",
    src = "requirements.in",
    requirements_txt = "requirements.txt",
    requirements_darwin = "requirements_darwin.txt",
    requirements_linux = "requirements_linux.txt",
    requirements_windows = "requirements_windows.txt",
)
```

### Toolchain Registration

**Python Toolchain Extension (Bzlmod)**
```starlark
# In MODULE.bazel
python = use_extension("@rules_python//python/extensions:python.bzl", "python")

# Set default version
python.defaults(python_version = "3.11")

# Register specific toolchains
python.toolchain(python_version = "3.11")
python.toolchain(python_version = "3.12")

use_repo(python, "python_3_11", "python_3_12", "pythons_hub")

# Global overrides affecting all versions
python.override(
    available_python_versions = ["3.11", "3.12", "3.13"],
    minor_mapping = {
        "3.11": "3.11.10",
        "3.12": "3.12.7",
    },
)

# Single version overrides
python.single_version_override(
    python_version = "3.11",
    urls = ["https://custom-mirror.com/cpython-{version}-{platform}.tar.gz"],
    strip_prefix = "python",
)

# Platform-specific overrides
python.single_version_platform_override(
    platform = "linux-x86_64",
    python_version = "3.11",
    sha256 = "abc123...",
    urls = ["https://example.com/python-linux.tar.gz"],
)
```

**WORKSPACE Toolchain Registration**
```starlark
load("@rules_python//python:repositories.bzl", "python_register_toolchains")

python_register_toolchains(
    name = "python_3_11",
    python_version = "3.11.10",
    set_python_version_constraint = True,
    register_toolchains = True,
)
```

### Packaging and Distribution

**py_wheel** - Build Python wheels
```starlark
load("@rules_python//python:packaging.bzl", "py_wheel")

py_wheel(
    name = "my_wheel",
    distribution = "my_package",
    version = "1.0.0",
    python_tag = "py3",
    abi = "none",
    platform = "any",
    author = "Your Name",
    author_email = "you@example.com",
    description_file = "README.md",
    homepage = "https://github.com/user/repo",
    license = "Apache 2.0",
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
    ],
    requires = ["numpy>=1.20", "requests"],
    deps = [":my_package"],
    strip_path_prefixes = ["src"],
    twine = "@pypi//twine",  # Enable publishing
)
```

**py_package** - Collect transitive dependencies
```starlark
load("@rules_python//python:packaging.bzl", "py_package")

py_package(
    name = "pkg",
    packages = ["mypackage"],  # Only include these packages
    deps = [":main"],
)
```

**Publishing to PyPI**
```bash
# Publish wheel to PyPI
TWINE_USERNAME=__token__ TWINE_PASSWORD=pypi-*** \
    bazel run --stamp --embed_label=1.2.3 -- \
    //:my_wheel.publish --repository testpypi
```

### Console Script Binaries

**py_console_script_binary** - Create entry point executables
```starlark
load("@rules_python//python/entry_points:py_console_script_binary.bzl",
     "py_console_script_binary")

py_console_script_binary(
    name = "black_bin",
    pkg = "@pypi//black",
    # Automatically uses the 'black' entry point from black's metadata
)

# Custom entry point
py_console_script_binary(
    name = "custom_entry",
    pkg = "@pypi//my_package",
    script = "my_package.cli:main",  # module:function
)
```

### Wheel File Extraction

**whl_filegroup** - Extract files from wheels
```starlark
load("@rules_python//python:pip.bzl", "whl_filegroup")

whl_filegroup(
    name = "numpy_headers",
    whl_target = "@pypi//numpy:whl",
    pattern = "**/*.h",  # Extract header files
)
```

## Key Classes, Functions, and Macros

### Providers

**PyInfo** - Primary provider for Python dependencies
```starlark
PyInfo(
    transitive_sources = depset(...),  # All .py files
    imports = depset(...),             # PYTHONPATH additions
    has_py2_only_sources = False,
    has_py3_only_sources = True,
    uses_shared_libraries = False,
)
```

**PyRuntimeInfo** - Information about Python runtime
```starlark
PyRuntimeInfo(
    interpreter_path = "/path/to/python",
    interpreter = None,  # Or File object
    python_version = "PY3",
    stub_shebang = "#!/usr/bin/env python3",
    bootstrap_template = ":bootstrap_template.txt",
    coverage_tool = "@python_coverage//:coverage_tool",
)
```

**PyWheelInfo** - Wheel metadata
```starlark
PyWheelInfo(
    wheel = File(...),
    name_file = File(...),
)
```

### Toolchain Access

**current_py_toolchain** - Get the current Python toolchain
```starlark
load("@rules_python//python:current_py_toolchain.bzl", "current_py_toolchain")

def _my_rule_impl(ctx):
    py_toolchain = current_py_toolchain(ctx)
    python = py_toolchain.py3_runtime.interpreter
    # Use python interpreter in actions
```

### Extension APIs (for Custom Rules)

**Executable Builders** - Build custom executable rules
```starlark
load("@rules_python//python/api:executables.bzl", "executables")
load("@rules_python//python/api:attr_builders.bzl", "attrb")

def my_custom_binary_impl(ctx, base):
    providers = base(ctx)
    # Add custom behavior
    return providers

my_custom_binary_rule = executables.py_executable(
    implementation = my_custom_binary_impl,
    attrs = {
        "custom_attr": attrb.label(),
    },
)
```

**Library Builders** - Build custom library rules
```starlark
load("@rules_python//python/api:libraries.bzl", "libraries")

my_custom_library = libraries.py_library(
    implementation = _my_impl,
    attrs = {...},
)
```

### Utility Functions

**normalize_name** - Normalize PyPI package names
```starlark
load("@rules_python//python:pip.bzl", "pip_utils")

normalized = pip_utils.normalize_name("Django-REST-Framework")
# Returns: "django_rest_framework"
```

**Package Annotations** - Customize pip packages
```starlark
load("@rules_python//python:pip.bzl", "package_annotation")

package_annotation(
    additive_build_content = """
cc_library(
    name = "extra_lib",
    srcs = ["native.c"],
)
""",
    copy_files = {
        "//patches:config.py": "my_package/config.py",
    },
    copy_executables = {
        "//tools:binary": "my_package/bin/tool",
    },
    data = ["@extra_dep//..."],
    data_exclude_glob = ["**/*.so"],
)
```

## Usage Examples with Code Snippets

### Basic Python Application

```starlark
# BUILD.bazel
load("@rules_python//python:py_library.bzl", "py_library")
load("@rules_python//python:py_binary.bzl", "py_binary")
load("@rules_python//python:py_test.bzl", "py_test")

py_library(
    name = "calculator",
    srcs = ["calculator.py"],
    visibility = ["//visibility:public"],
)

py_binary(
    name = "app",
    srcs = ["main.py"],
    deps = [
        ":calculator",
        "@pypi//click",
    ],
    main = "main.py",
)

py_test(
    name = "calculator_test",
    srcs = ["calculator_test.py"],
    deps = [
        ":calculator",
        "@pypi//pytest",
    ],
)
```

### Multi-Platform PyPI Dependencies

```starlark
# MODULE.bazel
pip = use_extension("@rules_python//python/extensions:pip.bzl", "pip")

pip.parse(
    hub_name = "pypi",
    python_version = "3.11",
    requirements_by_platform = {
        "//:requirements.txt": "linux_*,osx_*",
        "//:requirements_windows.txt": "windows_*",
        "//:requirements_mac_arm.txt": "osx_aarch64",
    },
)
use_repo(pip, "pypi")
```

### Building and Publishing Wheels

```starlark
# BUILD.bazel
load("@rules_python//python:packaging.bzl", "py_package", "py_wheel")

py_package(
    name = "my_pkg_files",
    packages = ["mypackage"],
    deps = [":mylib"],
)

py_wheel(
    name = "wheel",
    distribution = "my-package",
    version = "1.2.3",
    deps = [":my_pkg_files"],
    requires = [
        "numpy>=1.20",
        "requests>=2.28",
    ],
    python_requires = ">=3.9",
    twine = "@pypi//twine",
)
```

```bash
# Build wheel
bazel build //:wheel

# Publish to PyPI
TWINE_USERNAME=__token__ \
TWINE_PASSWORD=pypi-*** \
bazel run --stamp --embed_label=1.2.3 //:wheel.publish
```

### Custom Python Toolchain

```starlark
# toolchains/BUILD.bazel
load("@rules_python//python:py_runtime.bzl", "py_runtime")
load("@rules_python//python:py_runtime_pair.bzl", "py_runtime_pair")

py_runtime(
    name = "custom_py3_runtime",
    interpreter_path = "/custom/path/python3",
    python_version = "PY3",
)

py_runtime_pair(
    name = "custom_runtime_pair",
    py3_runtime = ":custom_py3_runtime",
)

toolchain(
    name = "custom_toolchain",
    toolchain = ":custom_runtime_pair",
    toolchain_type = "@rules_python//python:toolchain_type",
)
```

```starlark
# MODULE.bazel
register_toolchains("//toolchains:custom_toolchain")
```

### Using Gazelle for BUILD Generation

```starlark
# BUILD.bazel
load("@rules_python_gazelle_plugin//manifest:defs.bzl", "gazelle_python_manifest")
load("@rules_python_gazelle_plugin//modules_mapping:def.bzl", "modules_mapping")
load("@bazel_gazelle//:def.bzl", "gazelle", "gazelle_binary")

# Generate modules mapping for third-party deps
modules_mapping(
    name = "modules_map",
    wheels = ["@pypi//:all_wheels"],
)

# Generate manifest
gazelle_python_manifest(
    name = "gazelle_python_manifest",
    modules_mapping = ":modules_map",
    pip_repository_name = "pypi",
    requirements = "//:requirements.txt",
)

# Custom Gazelle binary with Python plugin
gazelle_binary(
    name = "gazelle_bin",
    languages = [
        "@rules_python_gazelle_plugin//python",
    ],
)

# Gazelle target
gazelle(
    name = "gazelle",
    gazelle = ":gazelle_bin",
    mode = "fix",
)
```

```bash
# Generate BUILD files
bazel run //:gazelle
```

### Precompiling Python Bytecode

```starlark
# BUILD.bazel
load("@rules_python//python:py_binary.bzl", "py_binary")

py_binary(
    name = "optimized_app",
    srcs = ["main.py"],
    deps = [":mylib"],
    precompile = "enabled",  # or "if_generated_source"
    precompile_optimize_level = 2,  # 0, 1, or 2
)
```

## Integration Patterns and Workflows

### Monorepo Integration Pattern

```starlark
# Root MODULE.bazel - shared Python configuration
python = use_extension("@rules_python//python/extensions:python.bzl", "python")
python.toolchain(python_version = "3.11")

pip = use_extension("@rules_python//python/extensions:pip.bzl", "pip")
pip.parse(
    hub_name = "pypi",
    python_version = "3.11",
    requirements_lock = "//:requirements.txt",
)
```

```starlark
# Team-specific BUILD files can reference @pypi//...
# //services/api/BUILD.bazel
py_binary(
    name = "api_server",
    deps = [
        "//libs/common",
        "@pypi//fastapi",
        "@pypi//uvicorn",
    ],
)

# //ml_models/BUILD.bazel
py_library(
    name = "model",
    deps = [
        "//libs/common",
        "@pypi//tensorflow",
        "@pypi//numpy",
    ],
)
```

### Multi-Python Version Testing

```starlark
# tests/BUILD.bazel
load("@rules_python//python/config_settings:transition.bzl", "py_test_suite")

py_test_suite(
    name = "all_python_versions",
    tests = [":my_test"],
    python_versions = ["3.9", "3.10", "3.11", "3.12"],
)
```

### Cross-Compilation Workflow

```starlark
# Build for different platforms
bazel build //:app --platforms=@platforms//os:linux --cpu=x86_64
bazel build //:app --platforms=@platforms//os:linux --cpu=aarch64
bazel build //:app --platforms=@platforms//os:osx --cpu=x86_64
bazel build //:app --platforms=@platforms//os:osx --cpu=arm64
bazel build //:app --platforms=@platforms//os:windows --cpu=x86_64
```

## Configuration Options and Extension Points

### Environment Variables

**Build-time:**
- `RULES_PYTHON_REPO_DEBUG`: Enable debug logging for repository rules
- `RULES_PYTHON_REPO_DEBUG_VERBOSITY`: Set verbosity level (0-3)
- `RULES_PYTHON_PIP_ISOLATED`: Run pip in isolated mode

**Runtime:**
- `PYTHONPATH`: Additional import paths (automatically managed by rules)
- `PYTHONBREAKPOINT`: Debugger to use (inherited by py_binary)
- `PYTHON_BOOTSTRAP_IMPL`: Bootstrap implementation (python or script)

### Build Flags

**Python version selection:**
```bash
bazel build --//python/config_settings:python_version=3.11 //:app
```

**Bootstrap implementation:**
```bash
bazel build --//python/config_settings:bootstrap_impl=script //:app
```

**Precompilation:**
```bash
bazel build --//python/config_settings:precompile=enabled //:app
```

### Rule Attributes for Extension

Common extension attributes available in custom rules:

- `srcs`: Source files
- `deps`: Dependencies (propagate PyInfo)
- `data`: Runtime data files
- `imports`: PYTHONPATH additions
- `srcs_version`: Python version compatibility
- `python_version`: Target Python version
- `env`: Environment variables
- `args`: Program arguments
- `main`: Main entry point file
- `stamp`: Enable build stamping

### Custom Toolchain Integration

Implement custom toolchains by:
1. Creating py_runtime with custom interpreter
2. Wrapping in py_runtime_pair
3. Defining toolchain() target
4. Registering via register_toolchains()
5. Using target_settings for conditional selection

This comprehensive API surface enables users to build, test, package, and distribute Python applications with full control over dependencies, toolchains, and build configurations.
