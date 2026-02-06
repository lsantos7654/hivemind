# Bazel Skylib - APIs and Interfaces

## Repository Location
`/Users/santos/projects/bazel/bazel-skylib`

## Loading Modules

All modules use explicit loading pattern:
```starlark
load("@bazel_skylib//lib:<module>.bzl", "<module>")
load("@bazel_skylib//rules:<rule>.bzl", "<rule>")
```

---

## Library Modules (lib/)

### collections.bzl
**Purpose**: List manipulation utilities

```starlark
load("@bazel_skylib//lib:collections.bzl", "collections")
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `after_each` | `(separator, iterable)` | Insert separator after each item |
| `before_each` | `(separator, iterable)` | Insert separator before each item |
| `uniq` | `(iterable)` | Remove duplicates, preserve order |

**Examples**:
```starlark
collections.after_each(",", ["a", "b", "c"])    # ["a", ",", "b", ",", "c"]
collections.before_each("--flag=", ["x", "y"])  # ["--flag=", "x", "--flag=", "y"]
collections.uniq([1, 2, 2, 3, 1])               # [1, 2, 3]
```

---

### dicts.bzl
**Purpose**: Dictionary operations

```starlark
load("@bazel_skylib//lib:dicts.bzl", "dicts")
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `add` | `(*dictionaries, **kwargs)` | Merge dicts, later values override |
| `omit` | `(dictionary, keys)` | Return dict without specified keys |
| `pick` | `(dictionary, keys)` | Return dict with only specified keys |

**Examples**:
```starlark
dicts.add({"a": 1}, {"b": 2}, {"a": 3})  # {"a": 3, "b": 2}
dicts.omit({"a": 1, "b": 2}, ["b"])      # {"a": 1}
dicts.pick({"a": 1, "b": 2}, ["a", "c"]) # {"a": 1}
```

---

### paths.bzl
**Purpose**: POSIX-style path manipulation (no OS file access)

```starlark
load("@bazel_skylib//lib:paths.bzl", "paths")
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `basename` | `(p)` | Extract filename from path |
| `dirname` | `(p)` | Extract directory from path |
| `join` | `(path, *others)` | Join path components |
| `normalize` | `(path)` | Remove `.`, `..`, redundant slashes |
| `is_absolute` | `(path)` | Check if path is absolute |
| `relativize` | `(path, start)` | Make path relative to start |
| `split_extension` | `(p)` | Split into (root, extension) |
| `replace_extension` | `(p, new_ext)` | Change file extension |
| `starts_with` | `(path_a, path_b)` | Check ancestor relationship |
| `is_normalized` | `(str, look_for_same_level_references)` | Check if already normalized |

**Examples**:
```starlark
paths.basename("/foo/bar/baz.txt")           # "baz.txt"
paths.dirname("/foo/bar/baz.txt")            # "/foo/bar"
paths.join("foo", "bar", "baz.txt")          # "foo/bar/baz.txt"
paths.normalize("foo/./bar/../baz")          # "foo/baz"
paths.is_absolute("/foo")                    # True
paths.relativize("/foo/bar/baz", "/foo")     # "bar/baz"
paths.split_extension("/foo/bar.txt")        # ("/foo/bar", ".txt")
paths.replace_extension("foo.txt", ".md")    # "foo.md"
paths.starts_with("/foo/bar", "/foo")        # True
```

**Note**: Unix-style paths only. Windows paths with backslashes not fully supported.

---

### shell.bzl
**Purpose**: Safe shell command generation

```starlark
load("@bazel_skylib//lib:shell.bzl", "shell")
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `quote` | `(s)` | Escape string for shell |
| `array_literal` | `(iterable)` | Convert to shell array syntax |

**Examples**:
```starlark
shell.quote("hello world")    # "'hello world'"
shell.quote("it's")           # "'it'\\''s'"
shell.array_literal(["a","b"]) # "('a' 'b')"
```

**Use Case**: Safe genrule commands without shell injection.

---

### new_sets.bzl / sets.bzl
**Purpose**: Set implementation using dicts

```starlark
load("@bazel_skylib//lib:sets.bzl", "sets")
# or
load("@bazel_skylib//lib:new_sets.bzl", "sets")
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `make` | `(elements=None)` | Create set from list |
| `copy` | `(s)` | Deep copy of set |
| `to_list` | `(s)` | Convert set to list |
| `insert` | `(s, e)` | Add element (mutating) |
| `remove` | `(s, e)` | Remove element (mutating) |
| `contains` | `(a, e)` | Membership test |
| `is_equal` | `(a, b)` | Set equality |
| `is_subset` | `(a, b)` | Subset relationship |
| `disjoint` | `(a, b)` | No common elements |
| `intersection` | `(a, b)` | Common elements |
| `union` | `(*args)` | Combine sets |
| `difference` | `(a, b)` | Elements in a not in b |
| `length` | `(s)` | Number of elements |

**Examples**:
```starlark
s = sets.make([1, 2, 3])
sets.insert(s, 4)
sets.contains(s, 2)              # True
sets.union(s, sets.make([3, 4, 5]))  # {1, 2, 3, 4, 5}
sets.difference(s, sets.make([2]))   # {1, 3, 4}
```

---

### partial.bzl
**Purpose**: Functional programming - partial application

```starlark
load("@bazel_skylib//lib:partial.bzl", "partial")
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `make` | `(func, *args, **kwargs)` | Create partial with pre-bound args |
| `call` | `(partial, *args, **kwargs)` | Execute partial with extra args |
| `is_instance` | `(v)` | Check if value is a partial |

**Examples**:
```starlark
def greet(greeting, name, punct="!"):
    return greeting + " " + name + punct

hello = partial.make(greet, "Hello", punct="!!!")
partial.call(hello, "World")  # "Hello World!!!"
```

---

### types.bzl
**Purpose**: Type checking utilities

```starlark
load("@bazel_skylib//lib:types.bzl", "types")
```

| Function | Description |
|----------|-------------|
| `is_list(v)` | Check if v is a list |
| `is_string(v)` | Check if v is a string |
| `is_bool(v)` | Check if v is a boolean |
| `is_int(v)` | Check if v is an integer |
| `is_dict(v)` | Check if v is a dict |
| `is_tuple(v)` | Check if v is a tuple |
| `is_none(v)` | Check if v is None |
| `is_function(v)` | Check if v is callable |
| `is_depset(v)` | Check if v is a depset |
| `is_set(v)` | Check if v is a skylib set |

**Examples**:
```starlark
types.is_list([1, 2, 3])     # True
types.is_string("foo")       # True
types.is_dict({"a": 1})      # True
types.is_function(print)     # True
```

---

### structs.bzl
**Purpose**: Struct utilities

```starlark
load("@bazel_skylib//lib:structs.bzl", "structs")
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `to_dict` | `(s)` | Convert struct to dictionary |

**Example**:
```starlark
my_struct = struct(a = 1, b = 2)
structs.to_dict(my_struct)  # {"a": 1, "b": 2}
```

---

### versions.bzl
**Purpose**: Bazel version detection and comparison

```starlark
load("@bazel_skylib//lib:versions.bzl", "versions")
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `get` | `()` | Get current Bazel version |
| `parse` | `(bazel_version)` | Parse version string to tuple |
| `is_at_least` | `(threshold, version)` | version >= threshold |
| `is_at_most` | `(threshold, version)` | version <= threshold |
| `check` | `(minimum, maximum=None, version=None)` | Validate version range |

**Examples**:
```starlark
versions.get()                          # "7.0.0" (current Bazel)
versions.parse("5.0.0rc1 hash")         # (5, 0, 0)
versions.is_at_least("5.0", "6.0.0")    # True
versions.check(minimum = "5.0.0")       # Fails if Bazel < 5.0
```

---

### selects.bzl
**Purpose**: Enhanced select() syntax

```starlark
load("@bazel_skylib//lib:selects.bzl", "selects")
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `with_or` | `(input_dict, no_match_error=None)` | Allow OR'd condition keys |
| `with_or_dict` | `(input_dict)` | Return expanded dict (no select) |
| `config_setting_group` | `(name, match_any=[], match_all=[])` | Create AND/OR config groups |

**Examples**:
```starlark
# OR multiple conditions
deps = selects.with_or({
    ("//config:debug", "//config:test"): [":debug_deps"],
    "//conditions:default": [":default"],
})

# Create reusable config group
selects.config_setting_group(
    name = "opt_unix",
    match_all = [":opt", ":unix"],
)
```

---

### unittest.bzl
**Purpose**: Comprehensive testing framework

```starlark
load("@bazel_skylib//lib:unittest.bzl", "unittest", "asserts", "analysistest", "loadingtest")
```

#### Unit Testing
```starlark
def _my_test(ctx):
    env = unittest.begin(ctx)
    asserts.equals(env, expected, actual)
    asserts.true(env, condition)
    asserts.false(env, condition)
    return unittest.end(env)

my_test = unittest.make(_my_test)
```

#### Analysis Testing
```starlark
def _analysis_test(ctx):
    env = analysistest.begin(ctx)
    target = ctx.attr.target_under_test
    # ... verify providers and actions
    return analysistest.end(env)

my_analysis_test = analysistest.make(
    _analysis_test,
    attrs = {"target_under_test": attr.label()},
)
```

#### Assertions (asserts module)
| Function | Description |
|----------|-------------|
| `equals(env, expected, actual)` | Assert equality |
| `true(env, condition)` | Assert truthy |
| `false(env, condition)` | Assert falsy |
| `expect_failure(env, ...)` | Expect analysis failure |

---

### subpackages.bzl
**Purpose**: native.subpackages() wrapper (Bazel 5.0+)

```starlark
load("@bazel_skylib//lib:subpackages.bzl", "subpackages")
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `supported` | `()` | Check if native.subpackages() available |
| `all` | `(exclude=[], allow_empty=False, fully_qualified=True)` | List subpackages |
| `exists` | `(relative_path)` | Check if subpackage exists |

**Examples**:
```starlark
if subpackages.supported():
    pkgs = subpackages.all()  # ["//foo", "//bar"]
    subpackages.exists("foo")  # True if foo/BUILD exists
```

---

### modules.bzl
**Purpose**: bzlmod module extension helpers (Bazel 6.0+)

```starlark
load("@bazel_skylib//lib:modules.bzl", "modules")
```

| Function | Signature | Description |
|----------|-----------|-------------|
| `as_extension` | `(macro, doc=None)` | Wrap WORKSPACE macro as extension |
| `use_all_repos` | `(module_ctx, reproducible=False)` | Extension metadata helper |

**Example**:
```starlark
def rules_foo_deps():
    http_archive(name = "foo", ...)

rules_foo_deps_ext = modules.as_extension(rules_foo_deps)
```

---

## Build Rules (rules/)

### copy_file
**Purpose**: Copy single files

```starlark
load("@bazel_skylib//rules:copy_file.bzl", "copy_file")

copy_file(
    name = "copy_config",
    src = "config.template",      # Source file (required)
    out = "config.actual",        # Output path (required)
    is_executable = False,        # Make executable
    allow_symlink = True,         # Allow symlink instead of copy
)
```

---

### copy_directory
**Purpose**: Recursively copy directories

```starlark
load("@bazel_skylib//rules:copy_directory.bzl", "copy_directory")

copy_directory(
    name = "copy_assets",
    src = "assets",               # Source directory (required)
    out = "dist/assets",          # Output path (required)
)
```

---

### write_file
**Purpose**: Generate text files

```starlark
load("@bazel_skylib//rules:write_file.bzl", "write_file")

write_file(
    name = "version_file",
    out = "VERSION",              # Output file (required)
    content = ["1.0.0\n"],        # Content lines (required)
    is_executable = False,        # Make executable
)
```

---

### run_binary
**Purpose**: Execute binary as build action (no shell)

```starlark
load("@bazel_skylib//rules:run_binary.bzl", "run_binary")

run_binary(
    name = "process",
    tool = ":my_tool",            # Executable (required)
    srcs = ["input.txt"],         # Input files
    outs = ["output.txt"],        # Output files (required)
    args = [
        "$(location input.txt)",
        "$(location output.txt)",
    ],
    env = {"DEBUG": "1"},         # Environment variables
)
```

---

### diff_test
**Purpose**: Test comparing two files

```starlark
load("@bazel_skylib//rules:diff_test.bzl", "diff_test")

diff_test(
    name = "compare_outputs",
    file1 = ":generated_output",  # First file (required)
    file2 = "expected_output",    # Second file (required)
    failure_message = "Files differ",
)
```

---

### build_test
**Purpose**: Test that targets build successfully

```starlark
load("@bazel_skylib//rules:build_test.bzl", "build_test")

build_test(
    name = "all_targets_build",
    targets = [                   # Targets to verify (required, non-empty)
        "//foo:lib",
        "//bar:binary",
    ],
)
```

---

### expand_template
**Purpose**: Template substitution

```starlark
load("@bazel_skylib//rules:expand_template.bzl", "expand_template")

expand_template(
    name = "config",
    template = "config.in",       # Template file (required)
    out = "config.txt",           # Output file (required)
    substitutions = {             # Key-value replacements (required)
        "{{VERSION}}": "1.0.0",
        "{{BUILD_ID}}": "abc123",
    },
)
```

---

### select_file
**Purpose**: Extract single file from multi-output target

```starlark
load("@bazel_skylib//rules:select_file.bzl", "select_file")

select_file(
    name = "extracted",
    srcs = ":multi_output_target",  # Target with outputs (required)
    subpath = "path/to/file.txt",   # Relative path (required)
)
```

---

### native_binary / native_test
**Purpose**: Wrap pre-built executables

```starlark
load("@bazel_skylib//rules:native_binary.bzl", "native_binary", "native_test")

native_binary(
    name = "my_tool",
    src = "prebuilt/tool",        # Pre-built executable (required)
    out = "tool.exe",             # Output name (default: name.exe)
    data = [":runtime_deps"],     # Runfiles
    env = {"HOME": "/tmp"},       # Environment
)

native_test(
    name = "my_tool_test",
    src = "prebuilt/test_runner",
)
```

---

### common_settings
**Purpose**: Standard build settings

```starlark
load("@bazel_skylib//rules:common_settings.bzl",
     "int_flag", "int_setting",
     "bool_flag", "bool_setting",
     "string_flag", "string_setting",
     "string_list_flag", "string_list_setting",
     "repeatable_string_flag")

string_flag(
    name = "log_level",
    values = ["debug", "info", "warn", "error"],  # Allowed values
    make_variable = "LOG_LEVEL",                   # Make variable name
)

bool_flag(
    name = "enable_debug",
)

int_flag(
    name = "opt_level",
)
```

**Usage in BUILD**:
```starlark
config_setting(
    name = "debug_mode",
    flag_values = {":log_level": "debug"},
)
```

---

### Directory Rules (rules/directory/)
**Purpose**: Directory metadata handling (v1.7.0+)

```starlark
load("@bazel_skylib//rules/directory:directory.bzl", "directory")
load("@bazel_skylib//rules/directory:glob.bzl", "directory_glob")
load("@bazel_skylib//rules/directory:subdirectory.bzl", "subdirectory")

directory(
    name = "my_dir",
    srcs = glob(["**/*"]),
)

directory_glob(
    name = "only_py",
    directory = ":my_dir",
    include = ["**/*.py"],
    exclude = ["*_test.py"],
)
```

---

## bzl_library Rule

**Purpose**: Aggregate Starlark sources for documentation and dependency tracking

```starlark
load("@bazel_skylib//:bzl_library.bzl", "bzl_library")

bzl_library(
    name = "my_rules",
    srcs = ["my_rules.bzl"],
    deps = [
        "@bazel_skylib//lib:paths",
        "@bazel_skylib//lib:shell",
    ],
)
```

---

## Best Practices

### Path Safety
```starlark
# Always use shell.quote for user input in commands
cmd = "echo " + shell.quote(user_input)
```

### Type Checking
```starlark
# Validate inputs in macros
if not types.is_list(deps):
    fail("deps must be a list")
```

### Version Compatibility
```starlark
# Check Bazel version early
versions.check(minimum = "5.0.0")
```

### Configuration
```starlark
# Use with_or for cleaner selects
deps = selects.with_or({
    ("//config:a", "//config:b"): [":ab_deps"],
    "//conditions:default": [":default"],
})
```

---

## Anti-Patterns to Avoid

1. **Bulk imports**: Don't use deprecated `lib.bzl`
2. **Shell injection**: Always use `shell.quote()`
3. **Assuming paths**: Use `paths.normalize()` for comparisons
4. **Missing toolchains**: Call `bazel_skylib_workspace()` for unittest
5. **Direct private imports**: Never import from `rules/private/`
