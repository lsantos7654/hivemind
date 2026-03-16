# Trogon — Code Structure

## Annotated Directory Tree

```
trogon/                          # Repository root
├── pyproject.toml               # Poetry build config, metadata, dependencies
├── README.md                    # Project overview, quick-start, screenshots
├── CHANGELOG.md                 # Version history
├── LICENSE                      # MIT license
├── .github/
│   └── workflows/
│       └── tests.yml            # CI: pytest on Ubuntu/macOS/Windows, Python 3.9–3.13
├── docs/                        # (minimal) documentation assets
├── examples/
│   ├── demo.py                  # Click Group with multiple subcommands demo
│   ├── nogroup_demo.py          # Single Click command (no group) demo
│   └── typer_example.py         # Typer integration demo
├── tests/
│   ├── test_help.py             # Tests for the @tui() decorator and help text
│   └── test_run_command.py      # Tests for UserCommandData.to_cli_args/to_cli_string
└── trogon/                      # Main Python package
    ├── __init__.py              # Public API: exports `tui`, `Trogon`
    ├── trogon.py                # Trogon app class + CommandBuilder screen
    ├── introspect.py            # Click schema introspection system
    ├── run_command.py           # User-input data models & CLI string builder
    ├── typer.py                 # Typer adapter (`init_tui`)
    ├── detect_run_string.py     # Detects how the process was invoked
    ├── constants.py             # Package-wide constants (title, URLs)
    ├── trogon.scss              # Textual CSS (SCSS) styling for all widgets
    └── widgets/
        ├── __init__.py          # Widget package init (re-exports public widgets)
        ├── form.py              # CommandForm — scrollable parameter form widget
        ├── parameter_controls.py # ParameterControls — per-parameter widget
        ├── command_tree.py      # CommandTree — sidebar command navigator
        ├── command_info.py      # CommandInfo — modal info/metadata dialog
        ├── multiple_choice.py   # MultipleChoice — checkbox list widget
        └── about.py             # AboutDialog — about/credits modal
```

## Module and Package Organization

The package follows a flat-ish structure with a single `widgets/` sub-package. There is no deep nesting; the core responsibilities are split across 7 top-level modules and 6 widget modules.

### `trogon/` — Core Package

#### `__init__.py`
The public surface of the library. Exports exactly two symbols:

```python
from trogon.trogon import Trogon
from trogon.trogon import tui
```

All user code should import from here, not from sub-modules.

#### `introspect.py`
The **schema extraction layer**. Contains all logic for walking a Click application's internal command tree and converting it to Trogon's own typed dataclasses.

Key types defined here:
- `CommandName` — `NewType` alias for `str`, used as a typed identifier
- `MultiValueParamData` — thin wrapper around a tuple of values; used for defaults and form output
- `ArgumentSchema` — dataclass for a positional CLI argument
- `OptionSchema` — dataclass for a `--flag` / `-f` option
- `CommandSchema` — dataclass for a complete command, holding lists of the above plus nested sub-commands

Key function:
- `introspect_click_app(app: BaseCommand) -> dict[CommandName, CommandSchema]` — the top-level entry point; builds the full schema dict recursively

Internal helpers in this module traverse Click's internal param structures (`click.Option`, `click.Argument`, `click.Group`, `click.Command`) using Click's public attributes (`params`, `commands`, `type`, `nargs`, `is_flag`, etc.).

#### `run_command.py`
The **user-data model layer**. Defines what the form captures from the user at runtime, independently of Textual.

Key types:
- `UserOptionData` — name list + value tuple + reference back to `OptionSchema`
- `UserArgumentData` — name + value tuple + reference back to `ArgumentSchema`
- `UserCommandData` — top-level aggregate; holds lists of the above plus an optional nested `subcommand`

Key methods on `UserCommandData`:
- `to_cli_args() -> list[str]` — produces shell-argument list (for `subprocess` or Click's `standalone_mode`)
- `to_cli_string() -> str` — produces human-readable command preview string

#### `trogon.py`
The **application layer**. Contains two Textual classes:

1. `Trogon(App[None])` — extends `textual.app.App`; the top-level TUI application. Accepts the Click app, the schema dict (computed via `introspect_click_app`), and configuration (app name, command name, post-run command). Pushes `CommandBuilder` as its initial screen. After `run()` returns, optionally re-invokes the CLI command if `execute_on_exit` is set.

2. `CommandBuilder(Screen[None])` — the main screen. Composes the full layout:
   - Left sidebar: `CommandTree` (for Groups) or absent (for single Commands)
   - Main area: `CommandForm` inside a scrollable container
   - Bottom bar: command preview (rendered via `Static`)
   - Bindings: Ctrl+R (run), Ctrl+T (focus tree), Ctrl+S (search), F1 (about), F2 (command info)

Also defines the `tui()` decorator function, which wraps `click.group()` or `click.command()` with a `tui` subcommand that launches Trogon.

#### `typer.py`
Minimal Typer adapter. Exports `init_tui(app: typer.Typer, name: str | None = None)`. Uses `typer.main.get_group(app)` to convert the Typer app to a Click Group, then calls the same `tui` decorator logic.

#### `detect_run_string.py`
Utility that determines the string the user should type to re-invoke the current process (e.g., `python script.py`, `python -m mypackage`, or the installed entry-point name). Uses `sys.orig_argv` and `ctypes` for robust detection across invocation styles. Returns a `str` consumed by `CommandBuilder` for display in the preview pane.

#### `constants.py`
Three package-level constants:
- `APP_TITLE = "Trogon"`
- `PACKAGE_NAME = "trogon"`
- `TEXTUAL_URL = "https://github.com/Textualize/textual"`
- `ORGANIZATION_NAME = "T"`

#### `trogon.scss`
Textual SCSS stylesheet. Defines layout, colors, typography, and sizing for every widget in the application. Uses Textual CSS variables and pseudo-classes (`:focus`, `:hover`, `:disabled`). Loaded automatically by the `Trogon` app via `CSS_PATH`.

### `trogon/widgets/` — Widget Sub-Package

#### `form.py` — `CommandForm`
A `Widget` subclass. Acts as the container for all parameter controls for the currently selected command. Responsibilities:
- Composes a search `Input` at the top
- Groups parameters by ancestry (options inherited from parent Click Groups appear separately)
- Instantiates one `ParameterControls` per option/argument
- Forwards `ParameterControls.Changed` messages upward as `CommandForm.Changed`
- Exposes `get_values() -> UserCommandData` to extract current form state
- Implements `apply_filter(query: str)` to show/hide controls based on the search bar

#### `parameter_controls.py` — `ParameterControls`
A `Widget` subclass. Renders the appropriate Textual control(s) for a single `OptionSchema` or `ArgumentSchema`. Control selection logic:
- `BOOL` type or `is_flag=True` → `Checkbox`
- `Choice` type with `multiple=True` → `MultipleChoice`
- `Choice` type (single) → `Select`
- All other types (STRING, INT, FLOAT, UUID, Path, File, IntRange, FloatRange) → `Input`
- `nargs > 1` → multiple `Input` widgets side by side
- `multiple=True` (non-Choice) → dynamic list of controls with an "+ Add value" `Button`

Emits `ParameterControls.Changed` with the current `MultiValueParamData` when any child control changes.

#### `command_tree.py` — `CommandTree`
A `Tree` subclass. Populates itself from the `dict[CommandName, CommandSchema]` produced by introspection. Group nodes are rendered in a distinct style. Emits `Tree.NodeHighlighted` which `CommandBuilder` listens to for switching the active command in the form.

#### `command_info.py` — `CommandInfo`
A `ModalScreen` subclass. Displays detailed metadata about the currently selected command in a tabbed layout:
- **Description tab** — command docstring/help text
- **Metadata tab** — `DataTable` with rows for name, parent, subcommands, is_group, argument count, option count

#### `multiple_choice.py` — `MultipleChoice`
A `Widget` subclass. Renders a vertical list of `Checkbox` widgets, one per choice string. Supports keyboard navigation (Up/Down arrows). Emits `MultipleChoice.Changed` with the list of selected values. Used exclusively by `ParameterControls` for `Choice` options with `multiple=True`.

#### `about.py` — `AboutDialog`
A `ModalScreen` subclass. Displays the Trogon logo, version, description, and links to the project GitHub and Textual. Dismisses on any keypress.

## Code Organization Patterns

- **Schema-first design** — Trogon separates introspection (pure data extraction) from presentation (Textual widgets). The schema dataclasses in `introspect.py` have no Textual imports, making them independently testable and reusable.
- **Textual message passing** — Widgets communicate upward via typed `Message` subclasses (`ParameterControls.Changed`, `CommandForm.Changed`) rather than direct method calls, following Textual's recommended event-driven pattern.
- **Dataclass-heavy modeling** — `CommandSchema`, `OptionSchema`, `ArgumentSchema`, `UserCommandData`, etc. are all `@dataclass` instances, providing clean attribute access and easy construction in tests.
- **Single CSS file** — All styling lives in `trogon.scss`, loaded at the app level. No inline styles or per-widget CSS.
- **Thin public API** — The `__init__.py` exports only `tui` and `Trogon`. All schema types are importable from `trogon.introspect` but are not considered stable public API.
