# Trogon — Build System

## Build System Type

Trogon uses **Poetry** as its build and dependency management system. The single source of truth is `pyproject.toml`, which declares all project metadata, dependencies, optional extras, and development dependencies.

The build backend is `poetry-core`:

```toml
[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

## Configuration Files

| File | Purpose |
|---|---|
| `pyproject.toml` | Poetry project config: metadata, deps, extras, scripts, tool config |
| `.github/workflows/tests.yml` | GitHub Actions CI pipeline |

There is no `setup.py`, `setup.cfg`, `Makefile`, or `tox.ini`.

## Project Metadata (`pyproject.toml`)

```toml
[tool.poetry]
name = "trogon"
version = "0.6.0"
description = "Easily convert your Click CLI app into a powerful terminal application"
license = "MIT"
authors = ["Darren Burns <darren@textualize.io>"]
readme = "README.md"
homepage = "https://github.com/Textualize/trogon"
repository = "https://github.com/Textualize/trogon"
```

Supported Python versions: `>=3.9, <4.0`

## External Dependencies

### Runtime Dependencies

| Package | Version Constraint | Role |
|---|---|---|
| `textual` | `>=2.1.2` | TUI framework; provides App, Screen, Widget, CSS engine, reactive system |
| `click` | `>=8.0.0` | CLI framework being introspected; required at runtime for type checking |

### Optional Dependencies

| Extra | Package | Version | Role |
|---|---|---|---|
| `typer` | `typer` | `>=0.9.0` | Typer app adapter via `init_tui`; only needed if the user's CLI is built with Typer |

Install with Typer support:
```bash
pip install trogon[typer]
```

### Development Dependencies

| Package | Role |
|---|---|
| `mypy` | Static type checking |
| `black` | Code formatting |
| `pytest` | Test runner |
| `textual-dev` | Textual devtools (CSS hot-reload, console logging) |

## Build Targets and Commands

### Installation

**Using pip (from PyPI):**
```bash
pip install trogon
# With Typer support:
pip install trogon[typer]
```

**Using Poetry (from source):**
```bash
git clone https://github.com/Textualize/trogon
cd trogon
poetry install
# With Typer extra:
poetry install --extras typer
```

### Running Tests

```bash
# With Poetry
poetry run pytest

# Or directly if in the Poetry virtualenv
pytest

# Run a specific test file
pytest tests/test_run_command.py

# Run with verbose output
pytest -v
```

Tests are located in `tests/`:
- `tests/test_help.py` — tests for the `@tui()` decorator: verifies it adds a "tui" subcommand with correct name and help text; tests for both Click Groups and single Commands
- `tests/test_run_command.py` — tests for `UserCommandData.to_cli_args()` and `to_cli_string()`: verifies correct conversion of user-entered option/argument values into CLI argument lists and display strings

### Type Checking

```bash
poetry run mypy trogon/
```

Mypy configuration is in `pyproject.toml` under `[tool.mypy]` (if present).

### Code Formatting

```bash
poetry run black trogon/ tests/ examples/
# Check only (no changes):
poetry run black --check trogon/ tests/ examples/
```

### Building for Distribution

```bash
# Build wheel and sdist
poetry build

# Output: dist/trogon-0.6.0-py3-none-any.whl
#         dist/trogon-0.6.0.tar.gz
```

### Publishing to PyPI

```bash
poetry publish
```

## Continuous Integration

CI is defined in `.github/workflows/tests.yml` and runs on every push and pull request.

**Matrix:**
- OS: `ubuntu-latest`, `macos-latest`, `windows-latest`
- Python: `3.9`, `3.10`, `3.11`, `3.12`, `3.13`

**Steps per job:**
1. Check out code
2. Set up Python with the target version
3. Install Poetry
4. `poetry install` (installs runtime + dev deps)
5. `poetry run pytest`

## Running Examples Locally

After installing from source with Poetry:

```bash
# Click Group demo (multiple subcommands)
poetry run python examples/demo.py tui

# Single command demo
poetry run python examples/nogroup_demo.py tui

# Typer demo (requires typer extra)
poetry install --extras typer
poetry run python examples/typer_example.py tui
```

## Development Workflow with Textual DevTools

For working on the TUI styling and layout, Textual's devtools provide hot-reloading of CSS:

```bash
# Install textual-dev
poetry install  # already included in dev deps

# Run with devtools console
textual run --dev examples/demo.py tui
```

This enables:
- Live CSS reloading when `trogon.scss` is edited
- Textual console for logging Widget state
- DOM inspector
