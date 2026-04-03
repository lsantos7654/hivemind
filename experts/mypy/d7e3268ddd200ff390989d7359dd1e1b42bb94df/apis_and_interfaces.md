# Mypy APIs and Interfaces

## 1. Command-Line Interface

### `mypy` command

```bash
mypy [options] [files or packages]

# Check files
mypy mymodule.py

# Check a package
mypy -p mypackage

# Check a module
mypy -m mymodule

# Strict mode (enables many additional checks)
mypy --strict mymodule.py

# Common options
mypy --ignore-missing-imports mymodule.py
mypy --disallow-untyped-defs mymodule.py
mypy --python-version 3.11 mymodule.py
mypy --config-file myproject.ini mymodule.py
mypy --show-error-codes mymodule.py
mypy --pretty mymodule.py
```

### `dmypy` command (daemon)

```bash
dmypy start -- [mypy options]   # Start the daemon
dmypy run -- [files]            # Run a check (starts daemon if needed)
dmypy check [files]             # Check files (daemon must be running)
dmypy recheck                   # Re-check last set of files
dmypy stop                      # Stop the daemon
dmypy status                    # Show daemon status
dmypy suggest [function]        # Infer types for an unannotated function
dmypy inspect [location]        # Get type at a specific location
```

### `stubgen` command

```bash
stubgen foo.py                  # Generate stub for a Python file
stubgen -m urllib.parse         # Generate stub for a module
stubgen -p urllib               # Generate stubs for a package (recursive)
stubgen --doc-dir <DIR> -m curses  # Use Sphinx docs for C module signatures
stubgen -o out/ foo.py          # Write to specific output directory
```

### `stubtest` command

```bash
stubtest mypackage              # Test stubs against runtime behavior
stubtest --allowlist allowlist.txt mypackage
stubtest --generate-allowlist mypackage  # Generate initial allowlist
```

### `mypyc` command

```bash
mypyc mymodule.py               # Compile a module to a C extension
mypyc -p mypackage              # Compile a package
```

## 2. Programmatic Python API (`mypy.api`)

The simplest way to use mypy from Python code. Located at `mypy/api.py`.

```python
from mypy import api

# Run mypy with the same arguments as the CLI
result = api.run(["--strict", "mymodule.py"])
stdout, stderr, exit_code = result

if exit_code == 0:
    print("No type errors found")
else:
    print("Type errors:", stdout)

# Run dmypy programmatically
result = api.run_dmypy(["run", "--", "mymodule.py"])
stdout, stderr, exit_code = result
```

**Return type:** `tuple[str, str, int]` — `(normal_output, error_output, exit_status)`

**Note:** `run()` is thread-safe (uses `StringIO` internally). `run_dmypy()` is NOT thread-safe (temporarily replaces `sys.stdout`/`sys.stderr`).

## 3. `Options` Class (`mypy.options`)

All configuration is collected into an `Options` instance. This is how mypy's behavior is controlled programmatically.

```python
from mypy.options import Options

opts = Options()
opts.python_version = (3, 11)
opts.strict_optional = True
opts.disallow_untyped_defs = True
opts.ignore_missing_imports = True
opts.check_untyped_defs = True
opts.warn_return_any = True
opts.warn_unused_ignores = True
opts.show_error_codes = True
```

**Key option categories:**

| Category | Options |
|----------|---------|
| Strictness | `disallow_untyped_defs`, `disallow_incomplete_defs`, `disallow_untyped_calls`, `disallow_any_*`, `check_untyped_defs` |
| Import handling | `ignore_missing_imports`, `follow_imports`, `follow_untyped_imports`, `no_site_packages` |
| Warnings | `warn_unused_ignores`, `warn_return_any`, `warn_unreachable`, `warn_no_return`, `warn_redundant_casts` |
| Strictness extras | `strict_optional`, `strict_equality`, `strict_bytes`, `extra_checks` |
| Incremental | `incremental`, `cache_dir`, `skip_cache_mtime_checks` |
| Output | `show_error_codes`, `show_error_context`, `pretty`, `color_output`, `error_summary` |
| Error codes | `enable_error_code`, `disable_error_code` |
| Plugins | `plugins` (list of module paths or `module:attribute`) |

**`--strict` mode** enables: `disallow_any_generics`, `disallow_untyped_calls`, `disallow_untyped_defs`, `disallow_incomplete_defs`, `check_untyped_defs`, `disallow_untyped_decorators`, `warn_redundant_casts`, `warn_unused_ignores`, `warn_return_any`, `no_implicit_reexport`, `strict_equality`, `extra_checks`.

## 4. `build()` Function (`mypy.build`)

Lower-level API for driving a complete type-check programmatically.

```python
from mypy.build import build
from mypy.modulefinder import BuildSource
from mypy.options import Options
from mypy.fscache import FileSystemCache

sources = [BuildSource("mymodule.py", "mymodule", None)]
options = Options()
fscache = FileSystemCache()

result = build(sources, options, fscache=fscache)
# result.errors: list of error strings
# result.files: dict[str, State] — per-module state
# result.types: dict[Expression, Type] — inferred types
```

## 5. Plugin API (`mypy.plugin`)

Plugins extend mypy's type checking for specific libraries or patterns.

### Plugin Entry Point

A plugin module must define a `plugin()` function:

```python
# mypackage/mypy_plugin.py
from mypy.plugin import Plugin

class MyPlugin(Plugin):
    def get_function_hook(self, fullname: str):
        if fullname == "mypackage.special_func":
            return my_func_hook
        return None

def plugin(version: str):
    return MyPlugin
```

Register in `mypy.ini`:
```ini
[mypy]
plugins = mypackage.mypy_plugin
```

### Plugin Hook Methods

All hooks on `Plugin` (inherited from `CommonPluginApi`):

| Hook | When called | Return type |
|------|------------|-------------|
| `get_type_analyze_hook(fullname)` | When a type expression is analyzed | `Callable[[AnalyzeTypeContext], Type] \| None` |
| `get_function_hook(fullname)` | After a function call is type-checked | `Callable[[FunctionContext], Type] \| None` |
| `get_function_signature_hook(fullname)` | Before a function call signature is matched | `Callable[[FunctionSigContext], CallableType] \| None` |
| `get_method_hook(fullname)` | After a method call is type-checked | `Callable[[MethodContext], Type] \| None` |
| `get_method_signature_hook(fullname)` | Before method signature match | `Callable[[MethodSigContext], CallableType] \| None` |
| `get_attribute_hook(fullname)` | When an attribute is accessed | `Callable[[AttributeContext], Type] \| None` |
| `get_class_decorator_hook(fullname)` | When a class decorator is analyzed | `Callable[[ClassDefContext], None] \| None` |
| `get_class_decorator_hook_2(fullname)` | Second pass class decorator hook | `Callable[[ClassDefContext], bool] \| None` |
| `get_base_class_hook(fullname)` | When a class is defined with this base | `Callable[[ClassDefContext], None] \| None` |
| `get_customize_class_mro_hook(fullname)` | To customize class MRO | `Callable[[ClassDefContext], None] \| None` |
| `get_metaclass_hook(fullname)` | When metaclass is analyzed | `Callable[[ClassDefContext], None] \| None` |
| `get_dynamic_class_hook(fullname)` | Dynamic class creation (e.g., `type()`) | `Callable[[DynamicClassDefContext], None] \| None` |
| `get_additional_deps(file)` | Add extra dependencies for a file | `list[tuple[int, str, int]]` |

### Plugin Context Objects

Key context types provided to hook callbacks:

- `FunctionContext`: `api` (checker API), `arg_types`, `arg_kinds`, `arg_names`, `callee_arg_names`, `default_return_type`, `context`
- `MethodContext`: same as `FunctionContext` plus `type` (receiver type)
- `AttributeContext`: `api`, `type` (object type), `default_attr_type`, `context`
- `ClassDefContext`: `api` (semantic analyzer API), `cls` (ClassDef node), `reason`

## 6. Error Codes (`mypy.errorcodes`)

Mypy uses typed error codes for filtering and suppression.

```python
from mypy.errorcodes import (
    ATTR_DEFINED,    # [attr-defined]
    NAME_DEFINED,    # [name-defined]
    ARG_TYPE,        # [arg-type]
    RETURN_VALUE,    # [return-value]
    ASSIGNMENT,      # [assignment]
    OVERRIDE,        # [override]
    UNION_ATTR,      # [union-attr]
    INDEX,           # [index]
    OPERATOR,        # [operator]
    RETURN,          # [return]
    CALL_OVERLOAD,   # [call-overload]
    IMPORT,          # [import]
    IMPORT_NOT_FOUND, # [import-not-found]
    MISC,            # [misc]
    NO_UNTYPED_DEF,  # [no-untyped-def]
    TYPE_ARG,        # [type-arg]
)
```

Use in inline suppression:
```python
x: int = "hello"  # type: ignore[assignment]
```

Enable/disable in config:
```ini
[mypy]
enable_error_code = truthy-bool, redundant-expr
disable_error_code = import-untyped
```

## 7. Configuration File Format

### `pyproject.toml`

```toml
[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = false
warn_unused_ignores = true
show_error_codes = true

[[tool.mypy.overrides]]
module = "third_party_module.*"
ignore_missing_imports = true
```

### `mypy.ini` / `setup.cfg`

```ini
[mypy]
python_version = 3.11
strict = True
warn_unused_ignores = True

[mypy-third_party_module.*]
ignore_missing_imports = True
```

### `tox.ini`

```ini
[mypy]
python_version = 3.11
```

## 8. Type System Classes (`mypy.types`)

For plugin and tool authors working with mypy's type objects:

```python
from mypy.types import (
    Type,           # Abstract base for all types
    ProperType,     # Base for "proper" (non-alias) types
    Instance,       # A class instantiation: e.g., list[int]
    UnionType,      # A | B
    TupleType,      # tuple[int, str]
    CallableType,   # (int) -> str
    LiteralType,    # Literal[42]
    TypeVarType,    # T
    AnyType,        # Any
    NoneType,       # None
    TypedDictType,  # TypedDict
    get_proper_type,  # Dereference type aliases
)
```

Common pattern in plugins:
```python
from mypy.types import get_proper_type, Instance, UnionType

def my_hook(ctx):
    t = get_proper_type(ctx.default_return_type)
    if isinstance(t, Instance):
        print(t.type.fullname)  # e.g., "builtins.list"
    return ctx.default_return_type
```

## 9. AST Node Classes (`mypy.nodes`)

Key classes for plugin authors working with the AST:

```python
from mypy.nodes import (
    TypeInfo,       # Class type info: MRO, methods, attributes
    FuncDef,        # Function definition
    ClassDef,       # Class definition
    MypyFile,       # Module (top-level file)
    Var,            # Variable or parameter
    Decorator,      # @decorator syntax
    SymbolTable,    # dict-like mapping of names to SymbolTableNode
    SymbolTableNode, # Entry in a symbol table
    OverloadedFuncDef,  # @overload group
    TypeAlias,      # type alias definition
    AssignmentStmt, # x = y
    FuncBase,       # base for FuncDef and OverloadedFuncDef
)
```

## 10. `dmypy` Daemon — `suggest` and `inspect`

The daemon provides two advanced analysis commands:

### `suggest` — Infer types for unannotated functions

```bash
dmypy suggest mymodule:my_function
dmypy suggest --json mymodule:my_function  # JSON output for pyannotate
dmypy suggest --callsites mymodule:my_function
```

### `inspect` — Get type at a position

```bash
dmypy inspect mymodule.py:10:5           # Type at line 10, col 5
dmypy inspect mymodule.py:10:5 --show attrs  # Attribute names
dmypy inspect mymodule.py:10:5 --show definition
```

## 11. `mypyc` Compilation API (`mypyc.build`)

```python
# In setup.py for compiling your own package with mypyc:
from mypyc.build import mypycify

setup(
    ext_modules=mypycify(["mypackage/__init__.py", "mypackage/module.py"]),
)
```

`mypycify()` returns a list of `setuptools.Extension` objects. The function:
1. Runs mypy to type-check the specified files
2. Generates C code from the IR
3. Returns compiled extension descriptors

## 12. Integration Patterns

### Pre-commit hook

```yaml
# .pre-commit-config.yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v2.0.0
  hooks:
  - id: mypy
    additional_dependencies: [types-requests]
```

### GitHub Actions

```yaml
- uses: python/mypy@v2
  with:
    args: --strict mypackage/
```

### VS Code (Pylance/mypy extension)

Configure in `.vscode/settings.json`:
```json
{
  "mypy-type-checker.args": ["--config-file", "mypy.ini"]
}
```

### pytest integration

```bash
pip install pytest-mypy
pytest --mypy
```

### Per-file inline type ignore

```python
x: int = "oops"  # type: ignore[assignment]
from typing import cast
y = cast(int, some_value)  # Explicit cast
```
