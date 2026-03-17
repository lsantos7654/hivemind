# Typer — APIs and Interfaces

## Public API Entry Points

All public symbols are re-exported from `typer/__init__.py`. Users should `import typer` or `from typer import ...`.

### The `Typer` Class (`typer/main.py`)

The central object. Instantiated to create an app; commands are registered via decorators.

```python
app = typer.Typer(
    name: str | None = Default(None),
    cls: type[TyperGroup] | None = Default(None),
    invoke_without_command: bool = Default(False),
    no_args_is_help: bool = Default(False),
    subcommand_metavar: str | None = Default(None),
    chain: bool = Default(False),
    result_callback: Callable[..., Any] | None = Default(None),
    # Command-level settings
    context_settings: dict[Any, Any] | None = Default(None),
    callback: Callable[..., Any] | None = Default(None),
    help: str | None = Default(None),
    epilog: str | None = Default(None),
    short_help: str | None = Default(None),
    options_metavar: str = Default("[OPTIONS]"),
    add_help_option: bool = Default(True),
    hidden: bool = Default(False),
    deprecated: bool = Default(False),
    # Rich settings
    rich_markup_mode: MarkupMode = Default(None),  # "markdown" | "rich" | None
    rich_help_panel: str | None = Default(None),
    # Exception formatting
    pretty_exceptions_enable: bool = True,
    pretty_exceptions_show_locals: bool = True,
    pretty_exceptions_short: bool = True,
)
```

**Key `Typer` methods:**

| Method | Signature | Description |
|---|---|---|
| `command()` | `@app.command(name=None, *, help=None, ...)` | Decorator to register a function as a CLI command |
| `callback()` | `@app.callback(...)` | Decorator to register a group-level callback |
| `add_typer()` | `app.add_typer(typer_instance, *, name=None, ...)` | Mount a sub-app as a subcommand group |
| `__call__()` | `app(args=None, prog_name=None, ...)` | Invoke the app — converts to Click and runs |

### `typer.run()` — Single-function apps

```python
def run(function: Callable[..., Any]) -> None:
    """Run a function as a single-command CLI app immediately."""
```

Convenience shortcut: `typer.run(main)` is equivalent to creating a `Typer()`, registering `main`, and calling the app.

```python
import typer

def main(name: str, count: int = 1):
    for _ in range(count):
        typer.echo(f"Hello, {name}!")

if __name__ == "__main__":
    typer.run(main)
```

### `typer.Option()` and `typer.Argument()` (`typer/params.py`)

The two parameter-specification functions. Both return `OptionInfo` or `ArgumentInfo` objects that Typer inspects during command registration.

**`Option()` — named CLI option (`--name`)**:

```python
# Annotated style (preferred)
def main(name: Annotated[str, typer.Option(help="Your name", envvar="MY_NAME")]):
    ...

# Default-value style (legacy)
def main(name: str = typer.Option("World", help="Your name")):
    ...
```

Key `Option()` parameters:
- `default` — default value (first positional arg in default style)
- `*param_decls` — explicit option names, e.g. `"--name"`, `"-n"`
- `help` — help text (also extracted from `Doc("")` in `Annotated`)
- `envvar` — environment variable name(s)
- `prompt` / `confirmation_prompt` / `hide_input` — interactive prompting
- `show_default` — show default value in help (`True` by default)
- `is_eager` — process before other options (used for `--version`)
- `callback` — `Callable[[Context, Parameter, value], value]`
- `autocompletion` — `Callable[[ctx, args, incomplete], list[str | tuple[str,str]]]`
- `min` / `max` / `clamp` — numeric range validation
- `parser` — `Callable[[str], Any]` custom string parser
- `click_type` — `click.ParamType` for full custom type
- `rich_help_panel` — group this option under a named Rich panel in help
- `count` — flag that counts occurrences (`-vvv` → 3)
- `hidden` — hide from help text

**`Argument()` — positional CLI argument**:

```python
def main(name: Annotated[str, typer.Argument(help="Name to greet")]):
    ...
```

Shares all parameters with `Option()` except prompt/confirmation/hide_input/count/allow_from_autoenv.

### Type System — Supported Python Types

Typer maps Python types to Click param types automatically (`typer/main.py`, `get_click_type()`):

| Python Type | CLI Behavior |
|---|---|
| `str` | String argument |
| `int` | Integer with validation |
| `float` | Float with validation |
| `bool` | Flag (`--flag` / `--no-flag`) for `Option`, `True`/`False` for `Argument` |
| `pathlib.Path` | Path via `TyperPath` (custom `click.Path` subclass) |
| `datetime.datetime` | Datetime with configurable format strings |
| `uuid.UUID` | UUID string parsed to `uuid.UUID` |
| `enum.Enum` subclass | Choice from enum values (using `TyperChoice` — values, not names) |
| `typing.Optional[T]` | Optional parameter (default `None`) |
| `typing.List[T]` / `list[T]` | Multiple values — can be passed multiple times |
| `typing.Tuple[T, ...]` / `tuple` | Fixed-arity or variadic tuples |
| `typing.Literal["a", "b"]` | Choices from literal values |
| `typer.FileText` | `io.TextIOWrapper` read mode |
| `typer.FileTextWrite` | `io.TextIOWrapper` write mode |
| `typer.FileBinaryRead` | `io.BufferedReader` binary read |
| `typer.FileBinaryWrite` | `io.BufferedWriter` binary write |

### `typer.Context` (`typer/models.py`)

Subclass of `click.Context`. Declare as a parameter type to inject the Click context:

```python
def main(ctx: typer.Context, name: str):
    if ctx.invoked_subcommand is None:
        typer.echo(f"Hello {name}")
```

### `typer.CallbackParam` (`typer/models.py`)

Subclass of `click.Parameter`. Declare as a parameter type in `callback=` functions:

```python
def version_callback(ctx: typer.Context, param: typer.CallbackParam, value: bool):
    if value:
        typer.echo("v1.0.0")
        raise typer.Exit()
```

### `get_command()` — Convert to Click (`typer/main.py`)

```python
from typer.main import get_command

click_app = get_command(app)  # Returns click.BaseCommand
click_app(["--help"])
```

Useful for advanced Click integration, WSGI wrapping, or passing a Typer app where a Click command is expected.

## Testing Interface (`typer/testing.py`)

```python
from typer.testing import CliRunner

runner = CliRunner()

def test_app():
    result = runner.invoke(app, ["--name", "Alice"])
    assert result.exit_code == 0
    assert "Hello, Alice!" in result.output
```

`CliRunner.invoke(app: Typer, args, input, env, catch_exceptions, color, **extra)` automatically calls `get_command(app)` before invoking Click's runner, so you pass a `Typer` instance directly (not a Click command).

## Shell Completion

Every Typer app automatically gets `--install-completion` and `--show-completion` options injected:

```bash
myapp --install-completion      # installs completion for detected shell
myapp --install-completion bash # install for bash specifically
myapp --show-completion         # print the completion script
```

Supported shells: `bash`, `zsh`, `fish`, `powershell`.

Custom completion for a parameter:
```python
def complete_names(ctx, args, incomplete):
    names = ["Alice", "Bob", "Charlie"]
    return [n for n in names if n.startswith(incomplete)]

def main(name: Annotated[str, typer.Argument(autocompletion=complete_names)]):
    ...
```

For completion items with help text, return `(value, help_text)` tuples.

## Rich Help Panels

Group parameters into labeled panels in help output:

```python
def main(
    name: Annotated[str, typer.Option(rich_help_panel="Required")],
    output: Annotated[Path, typer.Option(rich_help_panel="Output Options")],
    verbose: Annotated[bool, typer.Option(rich_help_panel="Output Options")] = False,
):
    ...
```

Markup mode is set on the `Typer()` instance:
```python
app = typer.Typer(rich_markup_mode="markdown")   # render Markdown in docstrings
app = typer.Typer(rich_markup_mode="rich")        # render Rich markup in docstrings
app = typer.Typer(rich_markup_mode=None)          # plain text
```

## Pretty Exceptions

```python
app = typer.Typer(
    pretty_exceptions_enable=True,       # show Rich traceback on unhandled exceptions
    pretty_exceptions_show_locals=True,  # include local variables in traceback
    pretty_exceptions_short=True,        # show only last frame
)
```

Set `pretty_exceptions_enable=False` to fall back to Python's default traceback.

## Subcommand Trees

```python
app = typer.Typer()
items_app = typer.Typer()
app.add_typer(items_app, name="items")

@items_app.command("list")
def items_list():
    typer.echo("Listing items")

@items_app.command("create")
def items_create(name: str):
    typer.echo(f"Creating {name}")
```

Results in: `myapp items list` and `myapp items create NAME`.

## Rich Styling Configuration (`typer/rich_utils.py`)

Module-level constants can be overridden globally before app invocation:

```python
import typer.rich_utils as ru

ru.STYLE_OPTION = "bold blue"
ru.STYLE_SWITCH = "bold green"
ru.MAX_WIDTH = 100
ru.COLOR_SYSTEM = "256"
ru.STYLE_ERRORS_PANEL_BORDER = "bold red"
```

Key constants:
- `STYLE_OPTION`, `STYLE_SWITCH`, `STYLE_NEGATIVE_OPTION`, `STYLE_NEGATIVE_SWITCH`
- `STYLE_METAVAR`, `STYLE_USAGE`, `STYLE_USAGE_COMMAND`
- `STYLE_HELPTEXT_FIRST_LINE`, `STYLE_HELPTEXT`, `STYLE_OPTION_HELP`
- `STYLE_OPTION_DEFAULT`, `STYLE_OPTION_ENVVAR`
- `STYLE_ERRORS_PANEL_BORDER`, `STYLE_ABORTED`, `STYLE_DEPRECATED`
- `STYLE_COMMANDS_TABLE_FIRST_COLUMN`
- `MAX_WIDTH`, `COLOR_SYSTEM`, `FORCE_TERMINAL`
- `ALIGN_OPTIONS_PANEL`, `ALIGN_COMMANDS_PANEL`, `ALIGN_ERRORS_PANEL`
- Table style constants: `STYLE_OPTIONS_TABLE_*`, `STYLE_COMMANDS_TABLE_*`

## Exit Codes and Control Flow

```python
raise typer.Exit(code=0)    # clean exit
raise typer.Exit(code=1)    # error exit
raise typer.Abort()         # aborted (prints "Aborted." and exits with code 1)
```

Both `Exit` and `Abort` are re-exported from `click.exceptions`.

## `typer.launch()` — Open URLs or Files

```python
typer.launch("https://typer.tiangolo.com")          # open URL in browser
typer.launch("/path/to/file.txt", locate=True)      # open file manager at location
```

Wraps `click.launch()`.

## `Doc("")` Integration (`annotated-doc`)

Help text can be written as a `Doc("")` inside `Annotated`, enabling IDE hover documentation:

```python
from typing import Annotated
from annotated_doc import Doc
import typer

def main(
    name: Annotated[str, typer.Argument(), Doc("The name to greet")],
    count: Annotated[int, typer.Option(), Doc("Number of greetings")] = 1,
):
    ...
```

Typer extracts the `Doc` string and uses it as help text.
