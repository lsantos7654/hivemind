# Typer — Build System

## Build System Type

Typer uses **PDM** (Python Dependency Manager) as its build backend via `pdm-backend`. The `pyproject.toml` is the single configuration file for all build, dependency, test, lint, and coverage settings.

**Key configuration file:** `pyproject.toml`

```toml
[build-system]
requires = ["pdm-backend"]
build-backend = "pdm.backend"

[tool.pdm]
version = { source = "file", path = "typer/__init__.py" }
distribution = true
```

The package version is read directly from `typer/__init__.py` (`__version__ = "0.24.1"`), so bumping the version in `__init__.py` is the single source of truth.

## External Dependencies

### Runtime Dependencies

Declared under `[project].dependencies`:

| Package | Version Constraint | Role |
|---|---|---|
| `click` | `>=8.2.1` | Core CLI engine — parsing, completion, command/group model |
| `rich` | `>=12.3.0` | Terminal formatting, help panels, traceback rendering |
| `shellingham` | `>=1.3.0` | Shell detection for completion installation |
| `annotated-doc` | `>=0.0.2` | Extracts `Doc("")` strings from `Annotated` for help text |

### Development Dependency Groups

PDM supports named dependency groups (`[dependency-groups]`):

**`tests` group** (used for CI testing):
```
coverage[toml] >=7.13
mypy >=1.19.1
ty >=0.0.9
pytest >=9.0.0
pytest-cov >=4.0.0
pytest-sugar >=0.9.5
pytest-xdist >=1.32.0
rich >=12.3.0
ruff >=0.15.0
shellingham >=1.3.0
```

**`docs` group** (for building the MkDocs documentation site):
```
cairosvg >=2.8.2
griffe-typingdoc >=0.3.0
griffe-warnings-deprecated >=1.1.0
markdown-include-variants >=0.0.8
mdx-include >=1.4.1
mkdocs-macros-plugin >=1.5.0
mkdocs-material >=9.7.1
mkdocs-redirects >=1.2.1
mkdocstrings[python] >=0.30.1
pillow >=11.3.0
pyyaml >=5.3.1
```

**`github-actions` group** (for GitHub Actions CI scripts):
```
httpx >=0.27.0
pydantic >=2.5.3
pydantic-settings >=2.1.0
pygithub >=2.3.0
smokeshow >=0.5.0
```

**`dev` group** (includes tests + docs, plus `prek >=0.3.2`).

### Lockfile

`uv.lock` provides a fully reproducible environment. When using `uv`, all installs are pinned to exact versions via this lockfile.

## Python Version Support

```toml
requires-python = ">=3.10"
```

Supported: Python 3.10, 3.11, 3.12, 3.13, 3.14.

## Build Targets and Included Files

```toml
[tool.pdm.build]
source-includes = [
    "tests/",
    "docs_src/",
    "scripts/",
]
```

When building a source distribution (sdist), PDM includes the test suite, documentation examples, and scripts. The wheel distribution contains only the `typer/` package.

## How to Build, Test, and Deploy

### Setting Up the Environment

Using `uv` (recommended based on `uv.lock` presence):
```bash
uv sync --group dev       # Install all dev dependencies from lockfile
uv sync --group tests     # Install only test dependencies
```

Using PDM directly:
```bash
pdm install --dev         # Install all groups
pdm install -G tests      # Install only the tests group
```

### Running Tests

```bash
# Run the full test suite
pytest

# Run with coverage
coverage run -m pytest
coverage combine
coverage report

# Run tests in parallel (pytest-xdist)
pytest -n auto

# Run a specific test file
pytest tests/test_annotated.py

# Run tutorial tests
pytest tests/test_tutorial/

# Run completion tests
pytest tests/test_completion/

# Run CLI tool tests
pytest tests/test_cli/
```

### Linting and Type Checking

```bash
# Lint with ruff
ruff check typer/ tests/ docs_src/
ruff format typer/ tests/ docs_src/

# Type check with mypy (strict mode)
mypy typer/

# Type check with ty (new Astral type checker)
ty check typer/
```

Key ruff rules enabled: `E`, `W` (pycodestyle), `F` (pyflakes), `I` (isort), `B` (bugbear), `C4` (comprehensions), `UP` (pyupgrade), `TID` (tidy-imports).

Notable ruff constraints:
- `TID251`: `rich` must not be imported directly — use `typer.rich_utils` instead.
- `TID252`: Relative imports are allowed.
- `TID253`: `typer.rich_utils` must not be imported at module level (only inside functions for lazy loading). Exception: `typer/rich_utils.py` itself.
- `shellingham.detect_shell` must not be used directly — use `typer._completion_shared._get_shell_name` instead.

### Pre-commit Hooks

```bash
pre-commit install   # Install hooks
pre-commit run --all-files  # Run all hooks
```

`.pre-commit-config.yaml` is present in the repo.

### Building the Package

```bash
# Build wheel and sdist
pdm build

# Or with uv
uv build
```

### Building Documentation

```bash
# Serve docs locally
mkdocs serve

# Build docs site
mkdocs build
```

### Coverage Configuration

```toml
[tool.coverage.run]
parallel = true
data_file = "coverage/.coverage"
source = ["docs_src", "tests", "typer"]
omit = ["typer/_typing.py"]
context = '${CONTEXT}'
relative_files = true
```

Coverage tracks `docs_src/` examples too (they are executed as part of the test suite). `typer/_typing.py` is excluded from coverage since it handles Python compatibility edge cases.

### Entry Points

```toml
[project.scripts]
typer = "typer.cli:main"
```

After installation, the `typer` executable maps to `typer.cli:main`. This enables:
```bash
typer my_script.py run --help
typer my_module run --arg value
```

### Environment Variables Affecting Build/Test Behavior

| Variable | Effect |
|---|---|
| `TYPER_USE_RICH` | Set to `0`/`false` to disable Rich integration entirely |
| `TYPER_RICH_MARKUP_MODE` | Override markup mode: `markdown`, `rich`, or empty |
| `TERMINAL_WIDTH` | Override terminal width for Rich output |
| `_TYPER_FORCE_DISABLE_TERMINAL` | Force disable terminal output (used in tests) |
| `_TYPER_COMPLETE_TEST_DISABLE_SHELL_DETECTION` | Disable shell detection in completion tests |
| `CONTEXT` | Coverage context label (set in CI per run type) |
