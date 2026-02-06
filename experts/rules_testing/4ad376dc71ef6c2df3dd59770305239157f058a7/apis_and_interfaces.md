# APIs and Interfaces

## Public API Entry Points

### analysis_test() - Analysis Phase Testing

The primary function for testing rule behavior during Bazel's analysis phase.

**Location**: `@rules_testing//lib:analysis_test.bzl`

**Signature**:
```python
analysis_test(
    name,
    target = None,
    targets = {},
    impl,
    attrs = {},
    attr_values = {},
    config_settings = {},
    aspects = [],
    testing_aspect = None,
    provider_subject_factories = []
)
```

**Parameters**:
- `name`: Test target name
- `target`: Single target or list/dict of targets under test (uses same config for all)
- `targets`: Dict of named targets with potentially different configs (see `attrs`)
- `impl`: Test implementation function with signature `impl(env, target)` or `impl(env, targets)`
- `attrs`: Custom attributes (either attribute objects or dict templates with special keys)
- `attr_values`: Values for custom attributes
- `config_settings`: Dict of flag->value to apply to target under test
- `aspects`: List of aspects to apply to target under test
- `testing_aspect`: Custom testing aspect (from `util.make_testing_aspect()`)
- `provider_subject_factories`: List of custom provider subject factories

**Usage Example**:
```python
load("@rules_testing//lib:analysis_test.bzl", "test_suite", "analysis_test")
load("@rules_testing//lib:util.bzl", "util")

def _test_my_rule(name):
    # Arrange: Create target under test
    util.helper_target(
        my_rule,
        name = name + "_subject",
        srcs = ["input.txt"],
        deps = [":lib"],
    )

    # Act: Run analysis test
    analysis_test(
        name = name,
        impl = _test_my_rule_impl,
        target = name + "_subject",
    )

def _test_my_rule_impl(env, target):
    # Assert: Verify behavior
    env.expect.that_target(target).default_outputs().contains("output.txt")
    env.expect.that_target(target).runfiles().contains_at_least(["data.txt"])
```

### unit_test() - Generic Starlark Testing

For testing Starlark code that doesn't require analysis phase or rules.

**Location**: `@rules_testing//lib:unit_test.bzl`

**Signature**:
```python
unit_test(name, impl, attrs = {})
```

**Parameters**:
- `name`: Test target name
- `impl`: Test function with signature `impl(env)`
- `attrs`: Optional custom attributes

**Usage Example**:
```python
load("@rules_testing//lib:unit_test.bzl", "unit_test")

def _test_parse_version(name):
    unit_test(
        name = name,
        impl = _test_parse_version_impl,
    )

def _test_parse_version_impl(env):
    result = parse_version("1.2.3")
    env.expect.that_dict(result).contains_exactly({
        "major": 1,
        "minor": 2,
        "patch": 3,
    })
```

### test_suite() - Test Aggregation

Collects multiple tests into a single test_suite target.

**Location**: `@rules_testing//lib:test_suite.bzl`

**Signature**:
```python
test_suite(
    name,
    tests = [],
    basic_tests = [],
    test_kwargs = {}
)
```

**Parameters**:
- `name`: Name of the suite
- `tests`: List of test setup functions (take `name` arg, may call `analysis_test()` or `unit_test()`)
- `basic_tests`: List of test impl functions (converted to unit_tests automatically)
- `test_kwargs`: Additional kwargs passed to all tests

**Usage Example**:
```python
load("@rules_testing//lib:test_suite.bzl", "test_suite")

def my_test_suite(name):
    test_suite(
        name = name,
        tests = [
            _test_my_rule,
            _test_my_rule_with_deps,
            _test_my_rule_windows,
        ],
        basic_tests = [
            _test_utility_function,
            _test_helper_logic,
        ]
    )

# In BUILD file:
# load(":my_tests.bzl", "my_test_suite")
# my_test_suite(name = "my_tests")
```

## Truth Assertion Library

### Expect Object - Assertion Factory

The entry point for creating type-specific subjects.

**Location**: `@rules_testing//lib:truth.bzl`

**Creation**: Available as `env.expect` in test implementation functions

**Methods**:
- `that_target(target)` → `TargetSubject`
- `that_action(action)` → `ActionSubject`
- `that_file(file)` → `FileSubject`
- `that_str(string)` → `StrSubject`
- `that_int(integer)` → `IntSubject`
- `that_bool(boolean)` → `BoolSubject`
- `that_dict(dictionary)` → `DictSubject`
- `that_collection(list)` → `CollectionSubject`
- `that_depset_of_files(depset)` → `DepsetFileSubject`
- `that_struct(struct)` → `StructSubject`
- `that_value(value, factory=...)` → Custom subject via factory
- `where(details=...)` → Add context to subsequent assertions

### TargetSubject - Target Assertions

**Key Methods**:
```python
# Provider access
.provider(provider_key, provider_name=None, factory=None)
.has_provider(provider_key)

# Outputs
.default_outputs() -> CollectionSubject  # DefaultInfo files
.runfiles() -> RunfilesSubject           # DefaultInfo runfiles
.executable() -> FileSubject             # DefaultInfo executable
.data_runfiles() -> RunfilesSubject

# Actions
.action_generating(file) -> ActionSubject
.action_named(mnemonic) -> ActionSubject

# Attributes (requires TestingAspectInfo)
.attr(name, factory=None) -> Subject for attribute value
```

**Example**:
```python
def _test_impl(env, target):
    subject = env.expect.that_target(target)

    # Check outputs
    subject.default_outputs().contains("foo.out")

    # Check runfiles
    subject.runfiles().contains_at_least([
        "myworkspace/data.txt",
        "myworkspace/config.json"
    ])

    # Check providers
    my_info = subject.provider(MyInfo)
    env.expect.that_collection(my_info.values).contains_exactly([1, 2, 3])

    # Check actions
    subject.action_generating("foo.out").contains_flag_values([
        ("--flag", "value")
    ])
```

### ActionSubject - Action Assertions

**Key Methods**:
```python
.argv() -> CollectionSubject           # All arguments (formatted)
.actual -> Action                       # Raw action object

.contains_at_least_args(args)          # Check subset of args
.contains_exactly_args(args)           # Check exact args
.contains_none_of_args(args)           # Check args absent
.contains_flag_values(flag_value_pairs) # Check flag-value pairs

.mnemonic() -> StrSubject              # Action mnemonic
.env() -> DictSubject                  # Environment variables
.inputs() -> DepsetFileSubject         # Input files
.outputs() -> CollectionSubject        # Output files
.substitutions() -> DictSubject        # Template substitutions (for template actions)
```

**Example**:
```python
def _test_impl(env, target):
    action = env.expect.that_target(target).action_generating("foo.o")

    # Check compiler flags
    action.contains_flag_values([
        ("-O", "2"),
        ("-std", "c++17"),
        ("--input", "{bindir}/{package}/foo.cc")
    ])

    # Check inputs include header
    action.inputs().contains_predicate(
        matching.file_path_matches("*/foo.h")
    )

    # Check mnemonic
    action.mnemonic().equals("CppCompile")
```

### CollectionSubject - List/Collection Assertions

**Key Methods**:
```python
.contains(item)
.contains_exactly(items)
.contains_at_least(items)
.contains_none_of(items)
.contains_predicate(matcher)           # Using Matcher predicate
.contains_at_least_predicates(matchers)
.contains_exactly_predicates(matchers)

.has_size(expected_size)
.is_empty()
.is_in_order()                         # Elements in sorted order
```

**Example**:
```python
def _test_impl(env, target):
    files = env.expect.that_target(target).default_outputs()

    # Exact match
    files.contains_exactly(["foo.out", "bar.out"])

    # Subset match
    files.contains_at_least(["foo.out"])

    # Predicate match
    files.contains_predicate(
        matching.file_basename_contains(".out")
    )
```

### RunfilesSubject - Runfiles Assertions

**Key Methods**:
```python
.contains(path)
.contains_exactly(paths)
.contains_at_least(paths)
.contains_none_of(paths)
.contains_predicate(matcher)
.contains_at_least_predicates(matchers)
.contains_exactly_predicates(matchers)

.paths() -> CollectionSubject          # All runfiles paths
.actual -> runfiles                     # Raw runfiles object
```

**Example**:
```python
def _test_impl(env, target):
    runfiles = env.expect.that_target(target).runfiles()

    # Check specific files
    runfiles.contains_at_least([
        "myworkspace/bin/tool",
        "myworkspace/data/config.txt"
    ])

    # Check with predicate
    runfiles.contains_predicate(
        matching.str_matches("*/config.txt")
    )
```

### FileSubject - File Assertions

**Key Methods**:
```python
.path() -> StrSubject                  # File.path
.short_path() -> StrSubject            # File.short_path
.basename() -> StrSubject              # File.basename
.extension() -> StrSubject             # File.extension
.equals(other_file)
.actual -> File                        # Raw File object
```

### DictSubject - Dictionary Assertions

**Key Methods**:
```python
.contains_exactly(expected_dict)
.contains_at_least(subset_dict)
.keys() -> CollectionSubject
.get(key, factory=None) -> Subject for value
```

### StrSubject - String Assertions

**Key Methods**:
```python
.equals(expected)
.contains(substring)
.split(sep) -> CollectionSubject
.matches(pattern)                      # Glob-style pattern with *
```

### IntSubject - Integer Assertions

**Key Methods**:
```python
.equals(expected)
.is_greater_than(threshold)
.is_at_least(minimum)
.is_at_most(maximum)
```

### BoolSubject - Boolean Assertions

**Key Methods**:
```python
.equals(expected)
.is_true()
.is_false()
```

## Matcher System - Predicate-Based Matching

**Location**: `@rules_testing//lib:truth.bzl` (via `matching` export)

### Built-in Matchers

```python
# File matchers
matching.file_basename_contains(substr)
matching.file_path_matches(pattern)    # Glob pattern with *
matching.file_short_path_equals(path)

# String matchers
matching.str_matches(pattern)          # Glob pattern with *
matching.equals_wrapper(value)         # Convert value to matcher

# Composition
matching.all(*matchers)                # AND semantics
matching.any(*matchers)                # OR semantics
```

### Custom Matcher

```python
matching.custom_matcher(desc, predicate_func)
```

**Example**:
```python
# Custom matcher for files larger than size
def file_size_greater_than(min_size):
    return matching.custom_matcher(
        desc = "file size > {}".format(min_size),
        match = lambda f: f.size > min_size
    )

def _test_impl(env, target):
    env.expect.that_target(target).default_outputs().contains_predicate(
        file_size_greater_than(1024)
    )
```

## Utility Functions

### util.helper_target()

Wraps target definition with tags to hide from `//...` and `:all`.

**Location**: `@rules_testing//lib:util.bzl`

**Signature**:
```python
util.helper_target(rule, **kwargs)
```

**Example**:
```python
def _test_setup(name):
    util.helper_target(
        my_library,
        name = name + "_lib",
        srcs = ["lib.cc"],
    )
```

### util.runfiles_paths()

Converts runfiles object to list of workspace-relative paths.

**Signature**:
```python
util.runfiles_paths(workspace_name, runfiles) -> list[str]
```

**Example**:
```python
def _test_impl(env, target):
    runfiles = target[DefaultInfo].default_runfiles
    paths = util.runfiles_paths(env.ctx.workspace_name, runfiles)
    env.expect.that_collection(paths).contains("myworkspace/data.txt")
```

### util.merge_kwargs()

Merges multiple kwarg dicts, concatenating lists.

**Signature**:
```python
util.merge_kwargs(*kwargs_dicts) -> dict
```

### util.make_testing_aspect()

Creates a custom testing aspect that applies over other aspects.

**Signature**:
```python
util.make_testing_aspect(aspects=[]) -> aspect
```

**Example**:
```python
my_testing_aspect = util.make_testing_aspect(aspects=[my_aspect])

analysis_test(
    name = "test_aspect_behavior",
    target = ":subject",
    testing_aspect = my_testing_aspect,
    impl = _test_impl,
)
```

## Configuration Options

### Custom Attributes in Tests

Tests can define custom attributes for accessing additional data:

**Using attribute objects**:
```python
analysis_test(
    name = "test",
    target = ":subject",
    impl = _test_impl,
    attrs = {
        "platform": attr.string(default="linux"),
    },
    attr_values = {
        "platform": select({
            "@platforms//os:windows": "windows",
            "//conditions:default": "linux",
        })
    }
)
```

**Using dict templates** (for targets under test):
```python
analysis_test(
    name = "test_multi_config",
    targets = {
        "linux": ":subject",
        "windows": ":subject",
    },
    attrs = {
        "linux": {
            "@config_settings": {"@platforms//os:os": "linux"},
        },
        "windows": {
            "@config_settings": {"@platforms//os:os": "windows"},
        },
    },
    impl = _test_impl,
)
```

### Provider Subject Factories

For custom providers, register a subject factory:

**Define factory**:
```python
def _my_info_subject_new(info, meta):
    # ... subject implementation
    return struct(...)

MyInfoSubject = struct(new = _my_info_subject_new)
```

**Register with test**:
```python
analysis_test(
    name = "test",
    target = ":subject",
    impl = _test_impl,
    provider_subject_factories = [
        struct(
            type = MyInfo,
            name = "MyInfo",
            factory = MyInfoSubject.new
        )
    ]
)
```

**Use in test**:
```python
def _test_impl(env, target):
    # Factory is automatically used
    my_info = env.expect.that_target(target).provider(MyInfo)
    # my_info is now a MyInfoSubject
```

## Integration Patterns

### Testing Cross-Platform Behavior

```python
def _test_cross_platform(name):
    util.helper_target(my_binary, name = name + "_subject", ...)

    analysis_test(
        name = name,
        targets = {
            "linux": name + "_subject",
            "windows": name + "_subject",
        },
        attrs = {
            "linux": {"@config_settings": {"@platforms//os:os": "linux"}},
            "windows": {"@config_settings": {"@platforms//os:os": "windows"}},
        },
        impl = _test_cross_platform_impl,
    )

def _test_cross_platform_impl(env, targets):
    # Both built with different configs
    linux_exe = env.expect.that_target(targets.linux).executable()
    windows_exe = env.expect.that_target(targets.windows).executable()

    linux_exe.short_path().contains("my_binary")
    windows_exe.short_path().contains("my_binary.exe")
```

### Testing with Aspects

```python
def _test_aspect_actions(name):
    util.helper_target(my_library, name = name + "_lib", ...)

    my_testing_aspect = util.make_testing_aspect(aspects=[my_aspect])

    analysis_test(
        name = name,
        target = name + "_lib",
        testing_aspect = my_testing_aspect,
        impl = _test_aspect_impl,
    )

def _test_aspect_impl(env, target):
    # Access actions created by the aspect
    action = env.expect.that_target(target).action_named("MyAspectAction")
    action.mnemonic().equals("MyAspectAction")
```

### Parameterized Testing

```python
def _make_test(test_name, input_value, expected_output):
    def _test_func(name):
        analysis_test(
            name = name,
            impl = lambda env, target: _test_impl(
                env, target, input_value, expected_output
            ),
            target = name + "_subject",
        )
    return _test_func

def my_test_suite(name):
    test_suite(
        name = name,
        tests = [
            _make_test("test_case_1", "input1", "output1"),
            _make_test("test_case_2", "input2", "output2"),
            _make_test("test_case_3", "input3", "output3"),
        ]
    )
```
