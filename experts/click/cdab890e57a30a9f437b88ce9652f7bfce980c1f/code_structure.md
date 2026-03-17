# Click — Code Structure

## Directory Tree

```
click/                             # Repository root
├── CHANGES.rst                    # Changelog (user-facing release notes)
├── LICENSE.txt                    # BSD-3-Clause license
├── README.md                      # Project overview and quickstart
├── pyproject.toml                 # Build, dependencies, tool config
├── uv.lock                        # Pinned dependency lockfile
│
├── src/
│   └── click/                     # Main Python package
│       ├── __init__.py            # Public API surface (all exports)
│       ├── core.py                # Core classes: Command, Group, Context, Parameter
│       ├── decorators.py          # Decorator functions for CLI definition
│       ├── types.py               # Parameter type system
│       ├── exceptions.py          # Exception hierarchy
│       ├── formatting.py          # Help text formatting
│       ├── termui.py              # Terminal UI functions (echo, prompt, etc.)
│       ├── testing.py             # CliRunner and Result for unit tests
│       ├── parser.py              # Low-level argument parser
│       ├── utils.py               # Public utility functions
│       ├── globals.py             # Thread-local context stack
│       ├── shell_completion.py    # Shell completion subsystem
│       ├── _compat.py             # Platform compatibility (Windows/Unix)
│       ├── _termui_impl.py        # Terminal UI internals (pager, progress)
│       ├── _textwrap.py           # Custom text wrapping logic
│       ├── _winconsole.py         # Windows console color support
│       ├── _utils.py              # Internal sentinel values
│       └── py.typed               # PEP 561 type marker
│
├── tests/                         # Test suite
│   ├── conftest.py                # Pytest fixtures (CliRunner instance)
│   ├── test_basic.py              # Core command/group behavior
│   ├── test_commands.py           # Command invocation patterns
│   ├── test_chain.py              # Command chaining
│   ├── test_arguments.py          # Argument handling
│   ├── test_options.py            # Option handling (largest test file)
│   ├── test_defaults.py           # Default value resolution
│   ├── test_command_decorators.py # Decorator behavior
│   ├── test_context.py            # Context management
│   ├── test_custom_classes.py     # Custom parameter type classes
│   ├── test_normalization.py      # Option token normalization
│   ├── test_info_dict.py          # Introspection / to_info_dict()
│   ├── test_formatting.py         # HelpFormatter output
│   ├── test_termui.py             # Terminal UI functions
│   ├── test_types.py              # Type conversion and validation
│   ├── test_utils.py              # Utility functions
│   ├── test_parser.py             # Parser internals
│   ├── test_shell_completion.py   # Completion system
│   ├── test_testing.py            # Testing module self-tests
│   ├── test_imports.py            # Import surface checks
│   ├── test_compat.py             # Compatibility shims
│   └── typing/                    # Static type checking tests (mypy/pyright)
│
├── docs/                          # Sphinx documentation source
│   ├── conf.py                    # Sphinx configuration
│   ├── index.md                   # Documentation home
│   ├── quickstart.md              # Getting started guide
│   ├── api.md                     # API reference
│   ├── advanced.md                # Advanced usage
│   ├── parameters.md              # Parameter system docs
│   ├── option-decorators.md       # Option decorator reference
│   ├── exceptions.md              # Exception reference
│   └── ... (30+ .md / .rst files)
│
└── examples/                      # Example applications
    ├── aliases/                   # Command alias handling
    ├── colors/                    # ANSI color output
    ├── completion/                # Shell completion setup
    ├── complex/                   # Multi-file CLI application
    ├── imagepipe/                 # Pipeline/stdin handling
    ├── inout/                     # File input/output patterns
    ├── naval/                     # Complex multi-command game
    ├── repo/                      # Git-style repository tool
    ├── termui/                    # Interactive terminal demo
    └── validation/                # Input validation patterns
```

## Module Organization and Roles

### Public Package Surface — `src/click/__init__.py`

All public names are re-exported from `__init__.py`. Consumers import exclusively from the `click` namespace (e.g., `import click; click.command()`). This file is the single source of truth for the public API contract.

### Core Object Model — `src/click/core.py` (3,418 lines)

The most critical file in the codebase. Contains:

- **`BaseCommand`** — abstract base for all command types; defines `make_context()`, `invoke()`, `main()`, `get_help()`
- **`Command`** — concrete single command; manages `params` list, calls `invoke()` with resolved parameter values
- **`MultiCommand`** — abstract base for commands with subcommands; provides `list_commands()`, `get_command()`, `resolve_command()`
- **`Group`** — extends `MultiCommand`; stores commands in a dict, supports `@group.command()` registration, chain mode
- **`CommandCollection`** — merges multiple groups' commands under one namespace
- **`Context`** — execution environment; `__init__` accepts `info_name`, `parent`, `default_map`, `max_content_width`, `color`, `obj`, and many more; implements `__enter__`/`__exit__` for resource cleanup
- **`Parameter`** — abstract base; delegates to `ParamType` for conversion; handles `required`, `multiple`, `callback`
- **`Option`** — extends `Parameter`; handles `is_flag`, `flag_value`, `prompt`, `confirmation_prompt`, `hide_input`, `count`, `envvar`
- **`Argument`** — extends `Parameter`; handles `nargs=-1` variadic arguments
- **`ParameterSource`** (Enum) — `COMMANDLINE`, `ENVIRONMENT`, `DEFAULT`, `DEFAULT_MAP`, `PROMPT`

### Decorator Layer — `src/click/decorators.py` (551 lines)

Thin convenience wrappers that create Click objects and attach them to Python callables:

- `command()` / `group()` — create `Command` / `Group` instances
- `argument()` / `option()` — append parameters to the nearest `Command` via `__click_params__`
- `pass_context()` / `pass_obj()` / `pass_meta_key()` — inject context into callback signature
- `make_pass_decorator()` / `pass_meta_key()` — factory for custom context accessors
- `version_option()` / `help_option()` / `confirmation_option()` / `password_option()` — pre-built option composites

### Type System — `src/click/types.py` (1,209 lines)

All parameter types inherit from `ParamType`:

- `ParamType` — abstract base; key methods: `convert(value, param, ctx)`, `shell_complete(ctx, param, incomplete)`, `to_info_dict()`
- **Scalar types:** `StringParamType`, `IntParamType`, `FloatParamType`, `BoolParamType`, `UUIDParameterType`, `UnprocessedParamType`
- **Constrained types:** `IntRange(min, max, clamp)`, `FloatRange(min, max, clamp)`
- **Enumerated:** `Choice(choices, case_sensitive)`
- **I/O types:** `FileType`, `PathType`
- **Composite:** `Tuple(types)` — heterogeneous multi-value type
- **Temporal:** `DateTime(formats)`
- **Singleton instances:** `STRING`, `INT`, `FLOAT`, `BOOL`, `UUID`, `UNPROCESSED` — module-level instances for common use

### Exception Hierarchy — `src/click/exceptions.py` (308 lines)

```
Exception
└── ClickException              # .format_message(), .show(), .exit_code = 1
    ├── UsageError              # .exit_code = 2, .format_usage()
    │   ├── BadParameter        # .param, .param_hint
    │   │   └── MissingParameter
    │   ├── BadOptionUsage      # .option_name
    │   └── BadArgumentUsage    # .argument_name
    ├── NoSuchOption            # .option_name
    ├── FileError               # .ui_filename, .hint
    ├── Abort                   # .exit_code = 1 (silent)
    └── Exit                    # .code (configurable exit code)
```

### Formatting Engine — `src/click/formatting.py` (301 lines)

- `HelpFormatter` — stateful formatter; methods: `write_heading()`, `write_paragraph()`, `write_text()`, `write_dl()`, `write_usage()`, `section()` (context manager), `indent()` (context manager)
- `wrap_text(text, width, initial_indent, subsequent_indent, preserve_paragraphs)` — whitespace-normalizing wrapper
- `measure_table(rows)` — calculates column widths for two-column definition lists

### Terminal I/O — `src/click/termui.py` (883 lines) + `_termui_impl.py` (852 lines)

Public API in `termui.py`:
- `echo(message, file, nl, err, color)` — write to stdout/stderr with optional color
- `style(text, fg, bg, bold, dim, underline, etc.)` — ANSI escape code wrapping
- `secho(message, **styles)` — `style()` + `echo()` combined
- `prompt(text, default, hide_input, confirmation_prompt, type, value_proc, etc.)`
- `confirm(text, default, abort, prompt_suffix, show_default, err)`
- `progressbar(iterable, length, label, width, fill_char, empty_char, bar_template, etc.)`
- `edit(text, editor, env, require_save, extension)` — open system editor
- `echo_via_pager(text_or_generator, color)` — paginated output
- `getchar(echo)` — single raw character input
- `clear()`, `pause()`, `launch(url, wait, locate)`

Internals in `_termui_impl.py`: `ProgressBar` class, pager implementation, `_default_text_stdout()`, editor launching, `getchar()` platform implementations.

### Testing Harness — `src/click/testing.py` (577 lines)

- `CliRunner(charset, env, echo_input, mix_stderr)` — test context factory
  - `invoke(cli, args, input, env, catch_exceptions, color, **extra)` — runs a command
  - `isolated_filesystem(temp_dir)` — context manager for temp directory
- `Result` — captures `output`, `exit_code`, `exception`, `exc_info`, `return_value`
- `BytesIOCopy`, `_default_text_stdout` — internal stream helpers

### Low-Level Parser — `src/click/parser.py` (532 lines)

Adapted from Python's `optparse`. Handles raw tokenization before Click's type conversion:
- `_OptionParser` — core parser class
- `_Argument`, `_Option` — parser-level descriptors
- `split_opt()`, `normalize_opt()` — token processing
- `_process_opts()`, `_process_args_for_options()`, `_process_args_for_args()` — parsing stages

### Shell Completion — `src/click/shell_completion.py` (667 lines)

- `ShellComplete` — abstract base; subclasses: `BashComplete`, `ZshComplete`, `FishComplete`, `PowerShellComplete`
- `CompletionItem(value, type, help)` — a single completion suggestion
- `shell_complete(cli, ctx_args, prog_name, complete_var, complete_instr)` — entry point called by shells
- Type-based completion via `ParamType.shell_complete()`

### Context Globals — `src/click/globals.py` (67 lines)

Thread-local `_local` object maintains a stack of active `Context` objects:
- `push_context(ctx)`, `pop_context()` — stack management
- `get_current_context(silent=False)` — retrieve active context
- `resolve_color_default(color=None)` — resolve color from current context

### Platform Compatibility — `src/click/_compat.py` (622 lines)

- `open_stream(filename, mode, encoding, errors, atomic)` — cross-platform file opener
- `get_text_stderr()`, `get_text_stdout()`, `get_binary_stdout()`, `get_binary_stderr()`
- `_default_text_stdin()`, `_default_text_stdout()`, `_default_text_stderr()`
- `isatty(stream)`, `should_strip_ansi(stream, color)`
- `get_terminal_size()` — terminal dimension detection
- `_is_binary_reader()`, `_is_binary_writer()` — stream type detection

### Internal Utilities — `src/click/_utils.py` (36 lines)

- `_default_text_stdout()`, `_default_text_stderr()` — stream accessors
- `UNSET` — sentinel object for "no value provided"
- `FLAG_NEEDS_VALUE` — sentinel for flags requiring a value token

## Code Organization Patterns

**Private vs public naming:** Files prefixed with `_` (`_compat.py`, `_termui_impl.py`, `_textwrap.py`, `_winconsole.py`, `_utils.py`) are internal implementation details not part of the public API. The public API is exclusively what appears in `__init__.py`.

**Separation of concerns:** Terminal I/O is split: user-facing functions in `termui.py`, platform-specific internals in `_termui_impl.py` and `_compat.py`. Similarly, public utilities are in `utils.py` while internal helpers are in `_utils.py`.

**Eager vs lazy evaluation:** Options can be marked `is_eager=True` (e.g., `--version`, `--help`) to process before other parameters. Callbacks receive `value` and may call `ctx.exit()`.

**`__click_params__` protocol:** Decorator functions like `@option` and `@argument` append `Parameter` instances to a list stored as `func.__click_params__`. The `@command` decorator reads this list and assigns it to the `Command.params` in reverse order.

**`to_info_dict()` pattern:** All major Click objects (`Command`, `Option`, `Argument`, `ParamType`, `Context`) implement `to_info_dict()` returning a plain dict representation, enabling documentation generation and introspection tools.
