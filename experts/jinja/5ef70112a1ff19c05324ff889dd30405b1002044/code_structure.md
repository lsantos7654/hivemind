# Jinja2 — Code Structure

## Annotated Directory Tree

```
jinja/                              # Repository root
├── src/
│   └── jinja2/                     # Main Python package
│       ├── __init__.py             # Public API re-exports
│       ├── _identifier.py          # Regex pattern for valid identifiers
│       ├── async_utils.py          # AsyncIO helpers (auto_await, auto_aiter, async_variant)
│       ├── bccache.py              # Bytecode cache base class + FileSystem + Memcached impls
│       ├── compiler.py             # AST → Python source code generator (CodeGenerator)
│       ├── constants.py            # Small constants (e.g. LOREM_IPSUM_WORDS)
│       ├── debug.py                # Exception rewriting for template-accurate tracebacks
│       ├── defaults.py             # Default delimiter strings, filters, tests, namespace, policies
│       ├── environment.py          # Environment, Template, TemplateExpression, TemplateStream
│       ├── exceptions.py           # Exception hierarchy
│       ├── ext.py                  # Extension base class + built-in extensions (i18n, debug, loopcontrols, do, profiler)
│       ├── filters.py              # Built-in template filters
│       ├── idtracking.py           # Identifier/variable scope tracking during compilation
│       ├── lexer.py                # Tokenizer (Lexer, TokenStream, Token)
│       ├── loaders.py              # Template loaders (FileSystem, Package, Dict, Function, etc.)
│       ├── meta.py                 # Template introspection (find_undeclared_variables, find_referenced_templates)
│       ├── nativetypes.py          # NativeEnvironment/NativeTemplate for Python-typed output
│       ├── nodes.py                # AST node definitions
│       ├── optimizer.py            # Constant-folding AST optimizer
│       ├── parser.py               # Token stream → AST parser
│       ├── py.typed                # PEP 561 marker (typed package)
│       ├── runtime.py              # Runtime context, loop, macro, undefined value types
│       ├── sandbox.py              # SandboxedEnvironment for untrusted template execution
│       ├── tests.py                # Built-in template tests (is defined, is number, etc.)
│       ├── utils.py                # Internal utilities: LRUCache, pass_context decorators, urlize, etc.
│       └── visitor.py              # NodeVisitor base class for AST traversal
├── tests/                          # pytest test suite
│   ├── conftest.py                 # Shared fixtures
│   ├── test_api.py                 # Environment and Template API tests
│   ├── test_async.py               # Async rendering tests
│   ├── test_async_filters.py       # Async filter tests
│   ├── test_bytecode_cache.py      # Bytecode cache tests
│   ├── test_compile.py             # Template compilation tests
│   ├── test_core_tags.py           # for/if/set/block/extends/include/import/macro/call/filter tags
│   ├── test_debug.py               # Traceback rewriting tests
│   ├── test_ext.py                 # Extension tests (i18n, loopcontrols, debug, do, profiler)
│   ├── test_filters.py             # Built-in filter tests
│   ├── test_idtracking.py          # Identifier scope tracking tests
│   ├── test_imports.py             # Template import/include tests
│   ├── test_inheritance.py         # Template inheritance tests
│   ├── test_lexnparse.py           # Lexer and parser tests
│   ├── test_loader.py              # Loader tests
│   ├── test_nativetypes.py         # NativeEnvironment tests
│   ├── test_nodes.py               # AST node tests
│   ├── test_pickle.py              # Pickle serialization tests
│   ├── test_regression.py          # Regression tests for historical bugs
│   ├── test_runtime.py             # Runtime behavior tests
│   ├── test_security.py            # Sandbox security tests
│   ├── test_tests.py               # Built-in template test (is X) tests
│   ├── test_utils.py               # Utility function tests
│   └── res/                        # Test resources
│       └── package.zip             # ZIP fixture for PackageLoader tests
├── docs/                           # Sphinx documentation source
│   ├── api.rst                     # Python API reference
│   ├── extensions.rst              # Extension writing guide
│   ├── integration.rst             # Framework integration notes
│   ├── nativetypes.rst             # NativeEnvironment docs
│   ├── sandbox.rst                 # Sandbox docs
│   ├── switching.rst               # Switching from Django/Mako/etc.
│   ├── templates.rst               # Template language reference
│   ├── tricks.rst                  # Tips and tricks
│   ├── conf.py                     # Sphinx configuration
│   └── examples/                   # Documented extension examples
│       ├── cache_extension.py      # Fragment cache extension example
│       └── inline_gettext_extension.py  # Inline i18n extension example
├── examples/basic/                 # Runnable usage examples
│   ├── cycle.py                    # Cycler helper demo
│   ├── translate.py                # i18n demo
│   ├── inheritance.py              # Template inheritance demo
│   ├── debugger.py                 # Debug extension demo
│   ├── test.py                     # Basic template rendering demo
│   ├── test_filter_and_linestatements.py
│   └── test_loop_filter.py
├── scripts/
│   └── generate_identifier_pattern.py  # Regenerates _identifier.py from Unicode data
├── pyproject.toml                  # Build system, dependencies, tool configuration
├── uv.lock                         # Locked dependency manifest (uv)
├── .pre-commit-config.yaml         # Pre-commit hook configuration
└── CHANGES.rst                     # Changelog
```

## Module and Package Organization

All source code lives under `src/jinja2/` following the `src` layout convention. The package uses Python's standard module hierarchy with no sub-packages — all 25 modules are flat siblings under `jinja2/`.

### Public API Surface (`__init__.py`)

`src/jinja2/__init__.py` is purely a re-export module. It imports and re-exports every public symbol with `as SomeName` syntax so they appear as direct members of the `jinja2` namespace. The public exports are grouped as:

- **Bytecode caches**: `BytecodeCache`, `FileSystemBytecodeCache`, `MemcachedBytecodeCache`
- **Core**: `Environment`, `Template`
- **Exceptions**: `TemplateAssertionError`, `TemplateError`, `TemplateNotFound`, `TemplateRuntimeError`, `TemplatesNotFound`, `TemplateSyntaxError`, `UndefinedError`
- **Loaders**: `BaseLoader`, `ChoiceLoader`, `DictLoader`, `FileSystemLoader`, `FunctionLoader`, `ModuleLoader`, `PackageLoader`, `PrefixLoader`
- **Undefined types**: `ChainableUndefined`, `DebugUndefined`, `make_logging_undefined`, `StrictUndefined`, `Undefined`
- **Utilities**: `clear_caches`, `is_undefined`, `pass_context`, `pass_environment`, `pass_eval_context`, `select_autoescape`

## Key Files and Their Roles

### `environment.py` — Central Hub
The most important file. Defines:
- `Environment` — holds all configuration; drives lexing, parsing, compiling, caching, and rendering. Methods: `parse`, `lex`, `compile`, `compile_expression`, `compile_templates`, `get_template`, `select_template`, `get_or_select_template`, `from_string`, `overlay`, `add_extension`, `call_filter`, `call_test`, `getitem`, `getattr`, `preprocess`.
- `Template` — a loaded, compiled template. Methods: `render`, `render_async`, `stream`, `stream_async`, `generate`, `generate_async`, `make_module`, `make_module_async`, `new_context`.
- `TemplateExpression` — result of `compile_expression`; a callable that evaluates a single Jinja expression.
- `TemplateStream` — lazy string generator returned by `Template.stream()`.
- `OverlayEnvironment` — environment sharing state with a parent.

### `compiler.py` — Code Generation
Contains `CodeGenerator` (a `NodeVisitor` subclass) which emits Python source code from the AST. Key internal classes:
- `Frame` — tracks variable scope and flags during code generation.
- `DependencyFinderVisitor` — finds dependencies for optimization.
- Top-level function `generate(source, environment, name, filename, ...)` is the main entry point used by `Environment._generate`.

### `parser.py` — Template Parser
`Parser` converts a `TokenStream` into a `nodes.Template` AST. Key methods: `parse()`, `parse_statement()`, `parse_expression()`, `parse_primary()`. Extension `parse` hooks are called here.

### `lexer.py` — Tokenizer
`Lexer` tokenizes raw template strings. `TokenStream` wraps the token iterator with look-ahead (`current`, `look()`, `expect()`, `skip()`). The `get_lexer(environment)` function creates or retrieves a cached `Lexer` instance for the given environment configuration.

### `nodes.py` — AST Nodes
Defines the complete AST node hierarchy rooted at `Node`. Subclasses include `Stmt` (statements: `If`, `For`, `Macro`, `Block`, `Extends`, `Include`, `Import`, `Set`, `Assign`, `Output`, etc.) and `Expr` (expressions: `Name`, `Const`, `Add`, `Sub`, `Call`, `Filter`, `Test`, `Getattr`, `Getitem`, `Compare`, etc.). Each node carries `fields` and `attributes` lists. The `EvalContext` class tracks autoescaping context during codegen.

### `runtime.py` — Execution Runtime
Provides classes used inside rendered templates:
- `Context` — the variable context for a single render call; holds the variable stack, exported vars, and `call` / `derived` helpers.
- `LoopContext` / `AsyncLoopContext` — the `loop` variable inside `{% for %}` blocks; provides `loop.index`, `loop.cycle`, `loop.changed`, etc.
- `Macro` — callable objects produced by `{% macro %}` tags.
- `Undefined` (and subclasses `DebugUndefined`, `StrictUndefined`, `ChainableUndefined`) — sentinel value for missing variables.
- `IncludedTemplate` — the result of an `{% include %}` within a block.

### `filters.py` — Built-in Filters
Implements all built-in Jinja2 filters as plain Python functions registered in the `FILTERS` dict. Notable filters: `do_abs`, `do_attr`, `do_batch`, `do_capitalize`, `do_center`, `do_count`, `do_default`, `do_dictsort`, `do_filesizeformat`, `do_first`, `do_float`, `do_forceescape`, `do_format`, `do_groupby`, `do_indent`, `do_int`, `do_items`, `do_join`, `do_last`, `do_list`, `do_lower`, `do_map`, `do_max`, `do_min`, `do_pprint`, `do_random`, `do_reject`, `do_rejectattr`, `do_replace`, `do_reverse`, `do_round`, `do_safe`, `do_select`, `do_selectattr`, `do_slice`, `do_sort`, `do_string`, `do_striptags`, `do_sum`, `do_title`, `do_tojson`, `do_trim`, `do_truncate`, `do_unique`, `do_upper`, `do_urlencode`, `do_urlize`, `do_wordcount`, `do_wordwrap`, `do_xmlattr`. Many have async variants via `@async_variant`.

### `tests.py` — Built-in Template Tests
Implements all built-in Jinja2 `is` tests as Python functions registered in the `TESTS` dict. Examples: `test_callable`, `test_defined`, `test_divisibleby`, `test_eq`, `test_escaped`, `test_even`, `test_filter`, `test_float`, `test_ge`, `test_gt`, `test_in`, `test_integer`, `test_iterable`, `test_le`, `test_lt`, `test_mapping`, `test_ne`, `test_none`, `test_number`, `test_odd`, `test_sameas`, `test_sequence`, `test_string`, `test_test`, `test_undefined`, `test_upper`, `test_lower`.

### `ext.py` — Extension System
`Extension` base class plus built-in extensions:
- `InternationalizationExtension` — `{% trans %}` tag, `_`, `gettext`, `ngettext`, `pgettext`, `npgettext` globals.
- `DebugExtension` — `{% debug %}` tag.
- `LoopControlsExtension` — `{% break %}` and `{% continue %}` in loops.
- `ExprStmtExtension` — `{% do expr %}` statement.
- `ProfilerExtension` — for template-level profiling.

### `loaders.py` — Template Loading
- `BaseLoader` — abstract base with `get_source(env, template)` → `(source, filename, uptodate)`.
- `FileSystemLoader` — loads from one or more filesystem directories.
- `PackageLoader` — loads from a Python package's data files.
- `DictLoader` — loads from a plain Python dict.
- `FunctionLoader` — loads via a user-supplied callable.
- `PrefixLoader` — routes by template name prefix to sub-loaders.
- `ChoiceLoader` — tries loaders in sequence.
- `ModuleLoader` — loads from pre-compiled module files.

### `bccache.py` — Bytecode Cache
- `BytecodeCache` — abstract base; subclasses implement `get_bucket` and `set_bucket`.
- `Bucket` — holds the compiled `CodeType` for one template plus checksum validation.
- `FileSystemBytecodeCache` — stores `.cache` files on disk.
- `MemcachedBytecodeCache` — stores in a Memcached-compatible backend.

### `sandbox.py` — Sandboxed Execution
`SandboxedEnvironment` overrides `getitem` and `getattr` to block access to unsafe Python internals. Tracks mutable operations and raises `SecurityError` when restricted methods (`add`, `clear`, `pop`, etc.) are called on mutable containers. Defines `MAX_RANGE = 100000` to limit `range()` size.

### `nativetypes.py` — Native Python Types Output
`NativeEnvironment` and `NativeTemplate` use `NativeCodeGenerator` (skips `str()` wrapping) and `native_concat` (which calls `ast.literal_eval` on the result) to render templates to actual Python types.

### `meta.py` — Introspection
`find_undeclared_variables(ast)` — returns the set of variable names looked up from context. `find_referenced_templates(ast)` — yields template names referenced via `{% extends %}`, `{% include %}`, `{% import %}`.

### `utils.py` — Utilities
`LRUCache`, `pass_context`, `pass_eval_context`, `pass_environment`, `select_autoescape`, `Cycler`, `Joiner`, `Namespace`, `is_undefined`, `clear_caches`, `htmlsafe_json_dumps`, `urlize`, `url_quote`, `pformat`, `generate_lorem_ipsum`, `missing` sentinel, `internalcode` decorator.

## Code Organization Patterns

- **Visitor pattern** (`visitor.py`) — `NodeVisitor` dispatches `visit_<NodeClass>` methods used by the compiler, optimizer, and meta module.
- **Pass-arg decorators** — `@pass_context`, `@pass_eval_context`, `@pass_environment` mark filter/test/global callables to receive runtime state.
- **`@async_variant`** — pairs a sync and async implementation of a filter; the wrapper checks `environment.is_async` at call time.
- **`missing` sentinel** — used to distinguish "not provided" from `None` in optional parameters throughout the codebase.
- **TYPE_CHECKING guards** — heavy use of `if t.TYPE_CHECKING:` blocks to import types only for static analysis, keeping runtime imports minimal.
- **`internalcode` decorator** — marks functions that should be excluded from Jinja's template traceback rewriting (`debug.py` checks `CodeType` membership in `internal_code`).
