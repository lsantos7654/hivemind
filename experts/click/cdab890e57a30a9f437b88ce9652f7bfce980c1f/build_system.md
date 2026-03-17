# Click — Build System

## Build System Type

Click uses **Flit** as its build backend and **uv** as its primary package manager. All project configuration lives in a single `pyproject.toml` file at the repository root (no `setup.py` or `setup.cfg`).

## Configuration File: `pyproject.toml`

### Build Backend

```toml
[build-system]
requires = ["flit_core>=3.11,<4"]
build-backend = "flit_core.buildapi"
```

Flit is a minimal, PEP 517-compliant build backend. It reads metadata from `src/click/__init__.py` (the `__version__` and `__doc__` attributes) and produces wheel and sdist distributions. No `MANIFEST.in` or complex build scripts are needed.

### Project Metadata

```toml
[project]
name = "click"
version = "8.3.dev"
description = "Composable command line interface toolkit"
requires-python = ">=3.10"
license = {file = "LICENSE.txt"}
```

### Runtime Dependencies

```toml
[project.optional-dependencies]
# colorama is a runtime dependency on Windows only
```

Click has **zero mandatory runtime dependencies**. The only optional dependency is `colorama` on Windows systems (declared as a platform conditional in the package metadata), which translates ANSI escape codes for legacy Windows consoles.

### Development Dependency Groups

```toml
[dependency-groups]
dev = ["tox", "tox-uv"]

docs = [
    "sphinx",
    "myst-parser",
    "pallets-sphinx-themes",
    "sphinx-tabs",
    "sphinxcontrib-log-cabinet",
]

tests = ["pytest", "pytest-timeout"]

typing = ["mypy", "pyright"]
```

Groups are managed with uv's dependency group feature rather than `extras`. Install with:

```bash
uv sync --group tests      # Install test dependencies
uv sync --group docs       # Install docs dependencies
uv sync --group typing     # Install type checking tools
uv sync --group dev        # Install tox orchestrator
```

## Tool Configuration

### Pytest

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
filterwarnings = [
    "error",           # All warnings become errors
    "ignore::pytest.PytestUnraisableExceptionWarning",
]
```

Tests are located in `tests/`. The strict `filterwarnings = ["error"]` policy ensures deprecation warnings are caught immediately.

### Coverage

```toml
[tool.coverage.run]
branch = true
source = ["click", "tests"]

[tool.coverage.paths]
source = ["src", "*/site-packages"]
```

Branch coverage is enabled. Coverage maps both source and installed paths.

### Ruff (Linter)

```toml
[tool.ruff]
src = ["src"]
fix = true

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "W", "B"]
```

Rule sets:
- `E` — pycodestyle errors
- `F` — Pyflakes (undefined names, unused imports)
- `I` — isort (import ordering)
- `UP` — pyupgrade (modern Python syntax)
- `W` — pycodestyle warnings
- `B` — flake8-bugbear (likely bugs and design issues)

### MyPy

```toml
[tool.mypy]
python_version = "3.10"
files = ["src/click", "tests/typing"]
strict = true
```

Strict mode enables all optional checks: `disallow_untyped_defs`, `warn_return_any`, `warn_unused_ignores`, etc. Only `tests/typing/` is included in the mypy check (not the full test suite).

### Pyright

```toml
[tool.pyright]
pythonVersion = "3.10"
include = ["src/click", "tests/typing"]
```

Both mypy and pyright are used to maximize type-safety coverage across different type checkers used by consumers.

## Build Targets and Commands

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=click --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_basic.py

# Run with verbose output
uv run pytest -v

# Run specific test by name
uv run pytest -k "test_basic_command"
```

### Linting and Formatting

```bash
# Run ruff linter (with auto-fix)
uv run ruff check src tests

# Run ruff formatter
uv run ruff format src tests

# Check only (no auto-fix)
uv run ruff check --no-fix src tests
```

### Type Checking

```bash
# MyPy strict check
uv run mypy

# Pyright check
uv run pyright
```

### Building the Package

```bash
# Build wheel and sdist
uv build

# Output goes to dist/
# dist/click-8.3.dev-py3-none-any.whl
# dist/click-8.3.dev.tar.gz
```

### Building Documentation

```bash
# Install doc dependencies first
uv sync --group docs

# Build HTML docs (from docs/ directory)
uv run sphinx-build -W docs docs/_build/html

# Or via make
cd docs && make html
```

### Tox (Multi-Python Testing)

```bash
# Run all tox environments
uv run tox

# Run specific environment
uv run tox -e py313
uv run tox -e docs
uv run tox -e typing
```

Tox environments correspond to Python versions `3.10`–`3.14` and `pypy3.11`, as well as `docs` and `typing` environments.

## Installing for Development

```bash
# Clone and install in editable mode with all dev extras
git clone https://github.com/pallets/click
cd click

# Install all groups
uv sync --group dev --group tests --group typing

# Or with pip
pip install -e ".[dev]"
```

The `src/` layout (PEP 517 source layout) means the package is only importable after installation or when using `uv run`. This prevents accidentally importing from the source directory instead of an installed version.

## CI/CD

The project uses GitHub Actions for continuous integration. The CI matrix tests:
- Python versions: 3.10, 3.11, 3.12, 3.13, 3.14
- PyPy 3.11
- Platforms: Linux (primary), with Windows/macOS for compatibility

Checks run on every PR and push:
1. `pytest` across the version matrix
2. `mypy` + `pyright` type checks
3. `ruff` lint check
4. Sphinx docs build

## Package Distribution

Click is distributed on PyPI as `click`. The package:
- Is a pure Python package (no compiled extensions)
- Includes a `py.typed` PEP 561 marker, declaring full typing support for consumers
- Ships no binary files—only `.py` source files
- Uses `flit_core` which automatically includes all `src/click/*.py` files in the wheel
