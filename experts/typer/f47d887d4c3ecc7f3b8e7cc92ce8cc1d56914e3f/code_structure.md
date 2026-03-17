# Typer — Code Structure

## Annotated Directory Tree

```
typer/                          # Root of the fastapi/typer repository
├── typer/                      # Main library package
│   ├── __init__.py             # Public API surface — re-exports all user-facing symbols
│   ├── __main__.py             # Enables `python -m typer` entry point
│   ├── main.py                 # Core: Typer class, get_command(), run(), launch()
│   ├── core.py                 # Click subclasses: TyperCommand, TyperGroup, TyperOption, TyperArgument
│   ├── models.py               # Data models: OptionInfo, ArgumentInfo, CommandInfo, TyperInfo, etc.
│   ├── params.py               # Public Option() and Argument() factory functions (with overloads)
│   ├── utils.py                # get_params_from_function(), parse_boolean_env_var(), error classes
│   ├── _types.py               # TyperChoice — overrides Click's Choice.normalize_choice() for enums
│   ├── _typing.py              # Typing compatibility shims (get_args, get_origin, Literal, etc.)
│   ├── rich_utils.py           # Rich-powered help formatter, traceback printer, style constants
│   ├── completion.py           # Shell completion wiring: install_callback, show_callback
│   ├── _completion_classes.py  # Completion shell class registration and initialization
│   ├── _completion_shared.py   # Shared completion helpers: Shells enum, install(), get_completion_script()
│   ├── cli.py                  # `typer` CLI tool: run scripts/modules as CLI apps
│   ├── testing.py              # CliRunner wrapping Click's CliRunner for Typer apps
│   ├── colors.py               # Color constants re-exported from click (e.g., typer.colors.RED)
│   └── py.typed                # PEP 561 marker — declares this package as typed
│
├── typer-slim/                 # Sub-package: Typer without Rich/shellingham
│   └── README.md
│
├── typer-cli/                  # Sub-package: just the `typer` CLI entry point
│   └── README.md
│
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── utils.py                # Shared test utilities
│   ├── test_tutorial/          # Tutorial-based integration tests (mirrors docs_src/)
│   ├── test_completion/        # Completion-specific tests
│   │   ├── test_completion.py
│   │   ├── test_completion_complete.py
│   │   ├── test_completion_complete_rich.py
│   │   ├── test_completion_install.py
│   │   ├── test_completion_show.py
│   │   ├── test_completion_path.py
│   │   ├── test_completion_option_colon.py
│   │   ├── test_completion_complete_no_help.py
│   │   ├── test_sanitization.py
│   │   ├── colon_example.py
│   │   ├── example_rich_tags.py
│   │   └── path_example.py
│   ├── test_cli/               # Tests for the `typer` CLI tool
│   │   ├── test_version.py
│   │   ├── test_help.py
│   │   ├── test_sub.py
│   │   ├── test_sub_help.py
│   │   ├── test_multi_app.py
│   │   ├── test_multi_app_sub.py
│   │   ├── test_multi_app_cli.py
│   │   ├── test_multi_func.py
│   │   ├── test_extending_app.py
│   │   ├── test_extending_empty_app.py
│   │   ├── test_func_other_name.py
│   │   ├── test_app_other_name.py
│   │   ├── test_doc.py
│   │   ├── test_empty_script.py
│   │   ├── test_not_python.py
│   │   ├── test_completion_run.py
│   │   └── test_sub_completion.py
│   ├── assets/                 # Asset scripts used in tests
│   │   ├── corner_cases.py
│   │   ├── type_error_no_rich.py
│   │   ├── type_error_normal_traceback.py
│   │   ├── completion_no_types.py
│   │   ├── completion_no_types_order.py
│   │   └── print_modules.py
│   ├── test_annotated.py       # Tests for Annotated-style parameter declarations
│   ├── test_type_conversion.py # Type coercion tests
│   ├── test_types.py           # Comprehensive type system tests
│   ├── test_rich_utils.py      # Rich formatting tests
│   ├── test_rich_markup_mode.py
│   ├── test_rich_import.py
│   ├── test_tracebacks.py      # Pretty exception formatting tests
│   ├── test_deprecation.py
│   ├── test_callback_warning.py
│   ├── test_ambiguous_params.py
│   ├── test_future_annotations.py  # from __future__ import annotations compat
│   ├── test_others.py
│   ├── test_suggest_commands.py
│   ├── test_prog_name.py
│   ├── test_param_meta_empty.py
│   ├── test_corner_cases.py
│   ├── test_exit_errors.py
│   └── test_launch.py
│
├── docs_src/                   # Source code for documentation examples
│   ├── first_steps/            # Tutorial: first_steps
│   ├── arguments/              # Tutorial: positional arguments
│   ├── options/                # Tutorial: named options
│   ├── options_autocompletion/ # Tutorial: custom autocompletion
│   ├── commands/               # Tutorial: commands and subcommands
│   ├── subcommands/            # Tutorial: subcommand trees
│   ├── parameter_types/        # Tutorial: type handling (enums, paths, files, etc.)
│   ├── multiple_values/        # Tutorial: list/tuple parameters
│   ├── progressbar/            # Tutorial: progress bars
│   ├── prompt/                 # Tutorial: interactive prompts
│   ├── printing/               # Tutorial: echo/secho output
│   ├── testing/                # Tutorial: testing with CliRunner
│   ├── typer_app/              # Tutorial: Typer app customization
│   ├── exceptions/             # Tutorial: exception handling
│   ├── launch/                 # Tutorial: launch (open URL/file)
│   ├── app_dir/                # Tutorial: application directory
│   ├── one_file_per_command/   # Tutorial: multi-file CLI structure
│   └── terminating/            # Tutorial: exit codes, Abort, Exit
│
├── docs/                       # MkDocs documentation source (markdown)
├── scripts/                    # Maintenance and CI scripts
├── data/                       # Auxiliary data files
├── pyproject.toml              # Build config, dependencies, tool config (PDM backend)
├── uv.lock                     # uv lockfile for reproducible installs
├── mkdocs.yml                  # Documentation site configuration
├── mkdocs.env.yml              # MkDocs environment-specific overrides
├── CONTRIBUTING.md
├── SECURITY.md
├── CITATION.cff
└── LICENSE                     # MIT license
```

## Module and Package Organization

### Core Package (`typer/`)

The library is organized into tightly coupled layers:

**Public surface layer** (`__init__.py`, `params.py`):
- `__init__.py` re-exports all user-facing symbols. Users only need `import typer` or `from typer import ...`.
- `params.py` contains `Option()` and `Argument()` — the two factory functions users call. Both use `@overload` extensively (three overloads each: `parser=`, `click_type=`, and default) to provide precise type checking depending on how a custom type is supplied.

**Application model layer** (`main.py`, `models.py`):
- `models.py` defines data containers (`OptionInfo`, `ArgumentInfo`, `CommandInfo`, `TyperInfo`, `ParameterInfo`, `ParamMeta`, `DeveloperExceptionConfig`) and type aliases (`NoneType`, `AnyType`, `Required`). No logic here — pure data.
- `main.py` is the heart of the library. The `Typer` class lives here, along with `get_command()` (the main translation function), `run()`, and `launch()`. It handles all the type-hint introspection and Click IR generation.

**Click integration layer** (`core.py`):
- Subclasses Click's `Command`, `Group`, `Option`, and `Argument` as `TyperCommand`, `TyperGroup`, `TyperOption`, and `TyperArgument`. These subclasses integrate Rich formatting, `suggest_commands` (did-you-mean), markup mode, and pretty exception config.

**Typing utilities** (`_typing.py`, `_types.py`, `utils.py`):
- `_typing.py` provides shims for `get_args`, `get_origin`, `get_type_hints`, `Annotated`, `Literal`, `is_union`, `is_literal_type`, and `literal_values` to handle Python version compatibility.
- `_types.py` defines `TyperChoice` — overrides Click's `Choice.normalize_choice()` to use `enum.value` rather than `enum.name` for CLI display.
- `utils.py` provides `get_params_from_function()` (the introspection entry point), error classes for misconfigured annotations, and `parse_boolean_env_var()`.

**Presentation layer** (`rich_utils.py`):
- Conditionally imported (lazy, not at module level — enforced by ruff TID253). Contains all Rich rendering logic: `rich_format_help()`, `rich_format_error()`, `rich_abort_error()`, and a large set of style constants (colors, padding, panel borders) that users can override globally.

**Completion layer** (`completion.py`, `_completion_classes.py`, `_completion_shared.py`):
- `_completion_shared.py` defines the `Shells` enum and provides `install()` and `get_completion_script()`.
- `_completion_classes.py` registers completion handlers per shell.
- `completion.py` provides `get_completion_inspect_parameters()`, `install_callback`, and `show_callback` that are injected into every Typer command automatically.

**CLI tool** (`cli.py`):
- The `typer` executable entry point. Dynamically loads Python files or modules, extracts a `Typer` app or plain function, wraps it if necessary, and runs it. `TyperCLIGroup` extends `TyperGroup` to lazily discover and register the `run` subcommand.

## Code Organization Patterns

1. **Lazy Rich imports**: `rich_utils` is never imported at module level. The ruff `TID253` rule bans it outside of functions, ensuring Rich is only loaded when actually rendering help or errors.
2. **`Default()` sentinel**: A `DefaultPlaceholder` wrapper distinguishes "the user explicitly set `None`" from "the user didn't set anything" in `TyperInfo` and `CommandInfo`.
3. **Overloads for custom types**: `Option()` and `Argument()` have three `@overload` signatures each to give accurate return types when `parser=`, `click_type=`, or neither is provided.
4. **`annotated-doc` integration**: `Doc("")` strings inside `Annotated[..., Doc("help text")]` are extracted by the `annotated_doc` library and used as help text, enabling docstring-style parameter documentation inline with the type annotation.
5. **`TYPER_USE_RICH` env var**: Controls whether Rich is enabled at all. When `TYPER_USE_RICH=0`, `HAS_RICH` is `False` and `DEFAULT_MARKUP_MODE` is `None`, disabling all Rich formatting.
6. **`TYPER_RICH_MARKUP_MODE` env var**: Can override markup mode at runtime to `"markdown"`, `"rich"`, or empty/unset.
