# Jinja2 — Build System

## Build System Type

Jinja2 uses **Flit** as its build backend (`flit_core < 4`) with **uv** as the primary package and environment manager. The build system is declared in `pyproject.toml` following PEP 517/518.

```toml
[build-system]
requires = ["flit_core<4"]
build-backend = "flit_core.buildapi"

[tool.flit.module]
name = "jinja2"
```

Flit discovers the package from `src/jinja2/` and reads the version from the module's docstring header (or a `__version__` attribute). The current dev version is `3.2.0.dev`.

## Configuration Files

| File | Purpose |
|---|---|
| `pyproject.toml` | Single source of truth: build system, metadata, dependencies, all tool configs |
| `uv.lock` | Locked transitive dependencies for reproducible environments |
| `.pre-commit-config.yaml` | Pre-commit hooks (ruff formatting, linting) |
| `docs/conf.py` | Sphinx documentation configuration |
| `docs/Makefile` | Sphinx Makefile targets |

## External Dependencies

### Runtime Dependencies

| Package | Version | Purpose |
|---|---|---|
| `MarkupSafe` | `>= 3.0` | Safe HTML string (`Markup`) and `escape()` function; required at all times |

### Optional (i18n extra)

| Package | Version | Purpose |
|---|---|---|
| `Babel` | `>= 2.17` | Internationalization: locale data, `gettext` extraction, `{% trans %}` support |

Install with: `pip install Jinja2[i18n]`

### Development Dependency Groups

Declared as `[dependency-groups]` in `pyproject.toml` (uv-style), not `[project.optional-dependencies]`:

| Group | Key Packages | Purpose |
|---|---|---|
| `dev` | `ruff`, `tox`, `tox-uv` | Linting, formatting, test orchestration |
| `tests` | `pytest`, `pytest-timeout`, `trio` | Test runner + async test backend |
| `typing` | `mypy`, `pyright`, `pytest` | Static type checking |
| `docs` | `sphinx`, `pallets-sphinx-themes`, `sphinxcontrib-log-cabinet` | Documentation build |
| `docs-auto` | `sphinx-autobuild` | Live-reloading documentation server |
| `pre-commit` | `pre-commit`, `pre-commit-uv` | Git hooks |
| `gha-update` | `gha-update` | GitHub Actions pin updates |

Default groups (installed by `uv sync`): `dev`, `pre-commit`, `tests`, `typing`.

## Build Commands

### Install for Development

```bash
# Install with all default groups (dev, pre-commit, tests, typing)
uv sync

# Install with a specific group
uv sync --group docs
```

### Run Tests

```bash
# Run the full test suite
pytest

# Run with verbose output and short tracebacks
pytest -v --tb=short

# Run a specific test file
pytest tests/test_api.py

# Run tests via tox (all Python versions)
tox

# Run tests for a specific Python version
tox -e py3.13
tox -e py3.12
tox -e py3.11
tox -e py3.10
tox -e pypy3.11
```

Tox environments:

| Environment | Description |
|---|---|
| `py3.13`, `py3.12`, `py3.11`, `py3.10` | pytest on CPython versions |
| `pypy3.11` | pytest on PyPy |
| `style` | All pre-commit hooks via `pre-commit run --all-files` |
| `typing` | `mypy` static type checking |
| `docs` | Sphinx dirhtml build |
| `docs-auto` | Live sphinx-autobuild server |
| `update-actions` | Update GitHub Actions pins |
| `update-pre_commit` | Freeze/update pre-commit hook versions |
| `update-requirements` | Update `uv.lock` |

### Type Checking

```bash
# mypy (strict mode, src/ only)
mypy

# via tox
tox -e typing
```

mypy is configured with `strict = true`, `python_version = "3.10"` and applies only to `src/`. Pyright is also configured (`typeCheckingMode = "standard"`) but not in the default tox run.

### Linting and Formatting

```bash
# Run ruff (linting + formatting)
ruff check src/
ruff format src/

# Via pre-commit (all files)
pre-commit run --all-files

# Via tox
tox -e style
```

Ruff is configured in `pyproject.toml` with rules: `B` (bugbear), `E` (pycodestyle errors), `F` (pyflakes), `I` (isort), `UP` (pyupgrade), `W` (pycodestyle warnings). Fix mode is enabled. Isort uses `force-single-line = true`.

### Build Documentation

```bash
# Build HTML documentation (dirhtml format)
sphinx-build -E -W -b dirhtml docs docs/_build/dirhtml

# Or via tox
tox -e docs

# Live-reload server
tox -e docs-auto
```

### Build Distribution

```bash
# Build wheel and sdist using flit
flit build

# Or using uv's PEP 517 interface
uv build
```

The sdist includes: `docs/`, `examples/`, `tests/`, `CHANGES.rst`, `uv.lock`. The `docs/_build/` directory is excluded.

## Continuous Integration

Located in `.github/workflows/`:

| Workflow | File | Triggers |
|---|---|---|
| `tests.yaml` | Full test matrix | Push, PR |
| `pre-commit.yaml` | Style check | Push, PR |
| `publish.yaml` | PyPI release | Tag push |
| `lock.yaml` | Dependency lock update | Schedule |

The `tests.yaml` workflow runs pytest across CPython 3.10–3.13 and PyPy 3.11, and also runs mypy and Sphinx builds.

## pytest Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
filterwarnings = ["error"]
```

`filterwarnings = ["error"]` means any Python warning during tests is converted to an error — this is a strict configuration ensuring deprecation warnings are caught. The `pytest-timeout` plugin is included to prevent hanging tests. `trio` is included as an async backend for async tests (used in `test_async.py`).

## Coverage Configuration

```toml
[tool.coverage.run]
branch = true
source = ["jinja2", "tests"]

[tool.coverage.paths]
source = ["src", "*/site-packages"]

[tool.coverage.report]
exclude_also = [
    "if t.TYPE_CHECKING",
    "raise NotImplementedError",
    ": \\.{3}",
]
```

Branch coverage is enabled. `TYPE_CHECKING` guards, abstract methods, and `...` stubs are excluded from coverage reporting.
