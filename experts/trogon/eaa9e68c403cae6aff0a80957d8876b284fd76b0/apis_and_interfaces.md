# Trogon — APIs and Interfaces

## Public Entry Points

Trogon's public API is intentionally minimal. All stable symbols are exported from `trogon/__init__.py`:

```python
from trogon import tui, Trogon
```

For Typer support:
```python
from trogon.typer import init_tui
```

---

## `tui()` — The Primary Decorator

```python
def tui(
    name: str | None = None,
    command: str = "tui",
    help: str = "Open Textual TUI.",
) -> Callable
```

A Click decorator that adds an interactive TUI subcommand to an existing Click application. It is designed to wrap a `@click.group()` or `@click.command()` and requires minimal code changes.

**Parameters:**
- `name` — Display name shown in the TUI header. Defaults to the Click app's name.
- `command` — The name of the subcommand that launches the TUI. Default: `"tui"`.
- `help` — Help text for the generated TUI subcommand.

**Usage with a Click Group (most common):**

```python
import click
from trogon import tui

@tui()
@click.group()
def cli():
    """My CLI tool."""
    pass

@cli.command()
@click.option("--name", "-n", help="Your name", required=True)
@click.option("--count", "-c", type=int, default=1, help="Times to greet")
def greet(name: str, count: int):
    """Greet someone."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")

if __name__ == "__main__":
    cli()
```

Invoking `python myscript.py tui` launches the TUI; all other subcommands work unchanged.

**Usage with a single Click Command:**

```python
@tui()
@click.command()
@click.option("--input", "-i", type=click.Path(exists=True))
@click.option("--verbose", is_flag=True)
def process(input: str, verbose: bool):
    """Process a file."""
    pass
```

For single commands, `tui()` internally wraps the command in a Click Group so that both `python myscript.py` (runs the command) and `python myscript.py tui` (opens the TUI) work.

---

## `Trogon` — Application Class

```python
class Trogon(App[None]):
    def __init__(
        self,
        cli: BaseCommand,
        app_name: str | None = None,
        command_name: str = "tui",
        post_run_command: list[str] | None = None,
        execute_on_exit: bool = False,
    )
```

The main Textual application. Can be used directly when the `@tui()` decorator pattern doesn't fit (e.g., programmatic integration).

**Parameters:**
- `cli` — The Click `BaseCommand` (Group or Command) to introspect and display.
- `app_name` — Name shown in the TUI header. Defaults to `cli.name`.
- `command_name` — Subcommand name that opened the TUI; used for display only.
- `post_run_command` — If set, this command list is executed via subprocess after the TUI exits when the user presses Ctrl+R.
- `execute_on_exit` — Set to `True` internally by the `tui` decorator when the user requests execution.

**Direct usage example:**

```python
from trogon import Trogon
import click

@click.group()
def cli():
    pass

# Launch TUI directly
app = Trogon(cli, app_name="My Tool")
app.run()
```

---

## `init_tui()` — Typer Adapter

```python
def init_tui(app: typer.Typer, name: str | None = None) -> None
```

Adds a `tui` subcommand to a Typer app. Internally converts the Typer app to a Click Group via `typer.main.get_group()` and applies the same TUI logic.

**Usage:**

```python
import typer
from trogon.typer import init_tui

cli = typer.Typer(help="My Typer CLI")
init_tui(cli)

@cli.command()
def hello(name: str):
    """Say hello."""
    typer.echo(f"Hello {name}")

if __name__ == "__main__":
    cli()
```

---

## Schema Introspection API

The introspection module is not officially public API but is stable enough for advanced use cases such as building alternative frontends or programmatic CLI analysis.

### `introspect_click_app()`

```python
from trogon.introspect import introspect_click_app

def introspect_click_app(app: BaseCommand) -> dict[CommandName, CommandSchema]
```

Recursively walks a Click app and returns a flat dictionary of all commands (including nested subcommands) keyed by `CommandName`.

### `CommandSchema`

```python
@dataclass
class CommandSchema:
    name: CommandName
    function: Callable
    options: list[OptionSchema]
    arguments: list[ArgumentSchema]
    subcommands: dict[CommandName, CommandSchema]
    parent: CommandSchema | None
    docstring: str
    is_group: bool

    @property
    def path_from_root(self) -> list[CommandName]:
        """Returns the full command path hierarchy from root."""
        ...
```

### `OptionSchema`

```python
@dataclass
class OptionSchema:
    name: list[str]          # e.g. ["--verbose", "-v"]
    type: click.ParamType    # click.STRING, click.INT, click.BOOL, Choice(...), etc.
    default: MultiValueParamData
    required: bool
    is_flag: bool
    is_boolean_flag: bool
    flag_value: Any
    counting: bool           # True for -vvv style counting options
    multiple: bool           # True if option can be repeated
    multi_value: bool        # True if nargs creates a tuple
    nargs: int
    help: str
    choices: list[str] | None
```

### `ArgumentSchema`

```python
@dataclass
class ArgumentSchema:
    name: str
    type: str               # String representation of the Click type
    required: bool
    default: MultiValueParamData
    multiple: bool
    choices: list[str] | None
    nargs: int
```

### `MultiValueParamData`

```python
@dataclass
class MultiValueParamData:
    values: tuple[Any, ...]  # Tuple of values (single-value params use a 1-tuple)
```

---

## User Data / Command Execution API

### `UserCommandData`

```python
@dataclass
class UserCommandData:
    name: CommandName
    options: list[UserOptionData]
    arguments: list[UserArgumentData]
    subcommand: UserCommandData | None = None

    def to_cli_args(self) -> list[str]:
        """Convert to a list of shell arguments (for subprocess or Click)."""
        ...

    def to_cli_string(self) -> str:
        """Convert to a human-readable command preview string."""
        ...
```

**Example:**

```python
from trogon.run_command import UserCommandData, UserOptionData, MultiValueParamData

data = UserCommandData(
    name="greet",
    options=[
        UserOptionData(name=["--name"], value=("Alice",), option_schema=...),
        UserOptionData(name=["--count"], value=("3",), option_schema=...),
    ],
    arguments=[],
)

print(data.to_cli_args())    # ["greet", "--name", "Alice", "--count", "3"]
print(data.to_cli_string())  # "greet --name Alice --count 3"
```

---

## Keyboard Bindings (CommandBuilder Screen)

| Key | Action |
|---|---|
| `Ctrl+R` | Execute the currently built command and exit the TUI |
| `Ctrl+T` | Focus the command tree sidebar |
| `Ctrl+S` | Focus the search/filter input in the form |
| `F1` | Open the About dialog |
| `F2` | Open the Command Info dialog for the selected command |
| `Escape` | Close a modal dialog |

---

## Widget APIs (Internal / Extension Points)

### `CommandForm`

```python
class CommandForm(Widget):
    def get_values(self) -> UserCommandData: ...
    def apply_filter(self, query: str) -> None: ...
    def focus(self) -> None: ...

    class Changed(Message):
        """Posted when any parameter value changes."""
        command_data: UserCommandData
```

### `ParameterControls`

```python
class ParameterControls(Widget):
    def get_values(self) -> MultiValueParamData: ...
    def apply_filter(self, query: str) -> None: ...

    class Changed(Message):
        """Posted when the control value changes."""
        value: MultiValueParamData
        option_schema: OptionSchema | ArgumentSchema
```

### `CommandTree`

```python
class CommandTree(Tree[CommandSchema]):
    """Tree widget populated from the introspected command schema dict."""
```

Emits standard Textual `Tree.NodeHighlighted` events with the `CommandSchema` as the node data.

---

## Integration Patterns and Workflows

### Pattern 1: Standard `@tui()` Usage (Recommended)

The simplest and most common pattern:

```python
from trogon import tui
import click

@tui()
@click.group()
def cli():
    pass
```

### Pattern 2: Custom TUI Command Name

```python
@tui(command="ui", help="Launch interactive UI")
@click.group()
def cli():
    pass
# Now run with: python script.py ui
```

### Pattern 3: Programmatic Use Without Decorator

```python
from trogon import Trogon

# cli is any click.BaseCommand
app = Trogon(cli, app_name="My App")
app.run()
# After run(), check app.execute_on_exit and app.post_run_command
# to determine if the user requested execution
```

### Pattern 4: Typer Integration

```python
import typer
from trogon.typer import init_tui

app = typer.Typer()
init_tui(app, name="My Typer App")

@app.command()
def main(name: str, count: int = 1):
    pass
```

### Pattern 5: Standalone Introspection

```python
from trogon.introspect import introspect_click_app

schema = introspect_click_app(my_cli_group)
for name, cmd in schema.items():
    print(f"{name}: {len(cmd.options)} options, {len(cmd.arguments)} args")
    print(f"  path: {cmd.path_from_root}")
```

---

## Configuration Options and Extension Points

### CSS Customization

Trogon's visual styling is defined in `trogon/trogon.scss`. While not officially an extension point, the file can be forked or overridden by subclassing `Trogon` and setting `CSS_PATH` to a custom stylesheet.

### Subclassing `Trogon`

`Trogon` is a standard Textual `App` subclass. Advanced users can subclass it to:
- Override `CSS_PATH` for custom styling
- Add additional key bindings
- Mount additional widgets alongside `CommandBuilder`

```python
from trogon.trogon import Trogon

class MyTrogon(Trogon):
    CSS_PATH = "my_custom_style.scss"
```

### Click Type Support Matrix

| Click Type | Widget Used |
|---|---|
| `STRING` | `Input` |
| `INT` | `Input` (numeric) |
| `FLOAT` | `Input` (numeric) |
| `BOOL` / flag | `Checkbox` |
| `Choice` (single) | `Select` dropdown |
| `Choice` (multiple) | `MultipleChoice` checkboxes |
| `Path` | `Input` |
| `File` | `Input` |
| `UUID` | `Input` |
| `IntRange` | `Input` |
| `FloatRange` | `Input` |
| Tuple (nargs > 1) | Multiple `Input` side by side |
| Counting (`-vvv`) | `Input` (integer) |
