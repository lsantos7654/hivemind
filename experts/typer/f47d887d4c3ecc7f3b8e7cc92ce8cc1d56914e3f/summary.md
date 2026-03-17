# Typer — Summary

## Repository Purpose and Goals

Typer is a Python library for building CLI (command-line interface) applications using Python type hints as the single source of truth. Created by Sebastián Ramírez (tiangolo), the same author as FastAPI, Typer is designed to be the "FastAPI of CLIs." Its core philosophy is that developers should declare their CLI parameters using standard Python type annotations, and Typer translates those annotations into a fully functional CLI with help text, validation, shell completion, and rich terminal output — all automatically.

The project is hosted at `github.com/fastapi/typer` and documented at `https://typer.tiangolo.com`. As of commit `f47d887`, the library version is **0.24.1**, supporting Python 3.10–3.14.

## Key Features and Capabilities

- **Type-hint-driven CLI generation**: Function parameters annotated with standard Python types (`str`, `int`, `bool`, `Path`, `Enum`, `datetime`, `UUID`, `Optional`, `List`, etc.) are automatically converted to CLI arguments and options.
- **Intuitive `Annotated` style**: Parameters are declared using `typing.Annotated` with `typer.Option()` or `typer.Argument()` inside the annotation, keeping defaults separate and making intent explicit.
- **Rich terminal output**: Integrates with the Rich library for beautifully formatted help panels, colored output, error messages in styled panels, and Markdown/Rich markup in docstrings.
- **Shell autocompletion**: Automatic tab-completion support for Bash, Zsh, Fish, and PowerShell via `shellingham` for shell detection and Click's completion backend.
- **Subcommand trees**: Nest multiple `Typer` apps together with `app.add_typer(sub_app, name="sub")` to build arbitrarily complex command hierarchies.
- **Pretty exceptions**: Configurable exception formatting using Rich tracebacks with `pretty_exceptions_enable`, `pretty_exceptions_show_locals`, and `pretty_exceptions_short` flags.
- **Testing support**: `typer.testing.CliRunner` wraps Click's CliRunner to invoke `Typer` apps in tests directly.
- **`typer` CLI tool**: A `typer` command-line utility that can run any Python script or module as a CLI app, even if the script doesn't use Typer internally.
- **Custom type parsers**: Support for `parser=` (a `Callable[[str], Any]`) or `click_type=` (a `click.ParamType`) for fully custom type handling.
- **Environment variable support**: Any option can be wired to environment variables via `envvar=`.
- **Progress bars**: Wraps Click's `progressbar` for simple terminal progress output.
- **File and path types**: `FileText`, `FileTextWrite`, `FileBinaryRead`, `FileBinaryWrite`, and a custom `TyperPath` for filesystem parameters.

## Primary Use Cases and Target Audience

**Primary use cases:**
- Building production CLIs for Python applications, data pipelines, DevOps tooling, and system administration scripts.
- Rapidly prototyping CLI interfaces for existing Python functions.
- Running Python scripts as CLIs without modifying the scripts (via the `typer` tool).
- Building multi-command CLI tools with subcommands, grouped help panels, and shell completion.

**Target audience:**
- Python developers who want ergonomic, type-safe CLI development.
- Teams building internal tooling where consistent help text and input validation are important.
- FastAPI users who want a familiar pattern for CLI development.

## High-Level Architecture Overview

Typer is implemented as a thin, opinionated layer on top of [Click](https://click.palletsprojects.com/) (≥8.2.1). Its architecture follows a three-phase pipeline:

1. **Declaration**: The developer decorates functions with `@app.command()`. Typer inspects the function signature using `inspect` and `typing.get_type_hints()` to extract `ParamMeta` objects for each parameter. `Option()` and `Argument()` in the signature (or `Annotated`) provide metadata like defaults, help text, env vars, validators, and completers.

2. **Translation**: `typer/main.py` converts the `Typer` app instance and its registered commands into Click `Command`/`Group` objects (`TyperCommand`, `TyperGroup`, `TyperOption`, `TyperArgument` — defined in `typer/core.py`). This is done by `get_command(app: Typer) -> click.BaseCommand`.

3. **Execution**: The resulting Click command tree is invoked normally, with Typer's Rich-enabled formatters (`typer/rich_utils.py`) replacing Click's default help formatter for styled output.

## Related Projects and Dependencies

| Dependency | Role |
|---|---|
| `click >=8.2.1` | Underlying CLI engine — parsing, completion, formatting |
| `rich >=12.3.0` | Terminal styling, help panel rendering, traceback formatting |
| `shellingham >=1.3.0` | Shell detection for completion installation |
| `annotated-doc >=0.0.2` | Extracts `Doc("")` strings from `Annotated` for help text |

**Related projects:**
- **FastAPI** — sister project by the same author, uses similar `Annotated`-based API pattern.
- **typer-slim** — a sub-package (in `typer-slim/`) that installs Typer without Rich and shellingham, for minimal deployments.
- **typer-cli** — a sub-package (in `typer-cli/`) providing just the `typer` CLI entry point.
- **rich-click** — a separate community project with similar Rich integration goals (Typer's `rich_utils.py` credits its origin).
