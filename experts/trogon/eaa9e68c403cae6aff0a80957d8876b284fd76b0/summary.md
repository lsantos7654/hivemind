# Trogon — Repository Summary

## Purpose and Goals

Trogon is a Python library that automatically generates interactive terminal user interfaces (TUIs) for command-line applications built with [Click](https://click.palletsprojects.com/). Its core goal is to eliminate the friction of remembering complex CLI flags and arguments by introspecting a Click application's schema at runtime and presenting the user with a navigable, form-based interface for constructing and executing commands.

The project is developed by Textualize, the same team behind the [Textual](https://github.com/Textualize/textual) TUI framework, and is published at version 0.6.0 (Beta) under the MIT license.

## Key Features and Capabilities

- **Automatic TUI Generation** — No manual widget definitions required. Trogon reads the Click command tree and generates an interactive screen with appropriate form controls (text inputs, checkboxes, dropdowns, multi-choice lists) for every option and argument.
- **Full CLI Introspection** — Supports Click Groups, nested sub-commands, positional arguments, flags, counting options (`-vvv`), multiple-value options, choices, file/path types, integer/float ranges, and boolean flags.
- **Real-time Command Preview** — A preview pane at the bottom of the screen shows the exact CLI invocation string as the user fills in the form, so they can copy it or verify it before running.
- **In-process Command Execution** — The constructed command can be executed directly from the TUI with a single keystroke (Ctrl+R), keeping the entire workflow inside the terminal.
- **Command Tree Navigation** — For Click Groups with many subcommands, a sidebar tree widget allows rapid navigation and selection.
- **Search / Filter** — A search bar filters visible parameters by name and help text.
- **Typer Support** — A thin adapter (`init_tui`) integrates with [Typer](https://typer.tiangolo.com/) apps by converting them to Click Groups internally.
- **Zero-annotation Decorator** — Adding `@tui()` above a Click group or command is the only change required to the existing codebase.

## Primary Use Cases and Target Audience

- **CLI tool authors** who want to ship a discoverable, user-friendly interface alongside their command-line tool without maintaining separate documentation or GUI code.
- **Developer tooling teams** building internal CLIs (deployment scripts, data-processing tools, database utilities) where occasional users benefit from a guided interface.
- **End users of Click-based tools** who prefer a form-based exploration over reading `--help` output.
- **Rapid prototyping** — Developers can introspect and test their CLI options interactively before settling on final parameter names.

## High-Level Architecture

Trogon is composed of four conceptual layers that work together in a pipeline:

1. **Introspection Layer** (`introspect.py`) — Recursively walks the Click command tree and produces a typed schema representation (`CommandSchema`, `OptionSchema`, `ArgumentSchema`). This layer has no Textual dependency and can be used independently.

2. **Data Model Layer** (`run_command.py`) — Defines `UserCommandData`, `UserOptionData`, and `UserArgumentData` — plain dataclasses that capture the values a user has entered into the form. These classes implement `to_cli_args()` and `to_cli_string()` to produce the actual shell invocation.

3. **Application / Screen Layer** (`trogon.py`) — The `Trogon` Textual application and `CommandBuilder` screen. Trogon initialises the app, passes the schema to the screen, and on exit optionally executes the command. CommandBuilder composes the full UI: command tree (left sidebar), scrollable parameter form (center), command info dialog (modal), and command preview (bottom bar).

4. **Widget Layer** (`widgets/`) — Self-contained Textual widgets: `CommandForm` (hosts all parameter controls and the search bar), `ParameterControls` (single option or argument with auto-selected control type), `CommandTree` (tree sidebar), `CommandInfo` (modal info sheet), `MultipleChoice` (checkbox list for `Choice` with `multiple=True`), `AboutDialog`.

Styling is defined in `trogon.scss`, compiled via Textual's SCSS pipeline.

## Related Projects and Dependencies

| Dependency | Role |
|---|---|
| [Textual](https://github.com/Textualize/textual) ≥ 2.1.2 | TUI framework providing App, Screen, Widget, CSS engine, reactive system |
| [Click](https://click.palletsprojects.com/) ≥ 8.0.0 | CLI framework whose apps Trogon introspects |
| [Typer](https://typer.tiangolo.com/) ≥ 0.9.0 (optional) | FastAPI-style CLI framework; Trogon converts Typer apps to Click Groups |
| [Rich](https://github.com/Textualize/rich) | Indirect dependency via Textual; used for markup rendering |

Development tooling includes `pytest`, `mypy`, `black`, and `textual-dev` (for the Textual devtools). CI runs on Ubuntu, macOS, and Windows across Python 3.9–3.13.
