# python-patterns — Build System

## Build System Type and Configuration Files

The project uses **setuptools** as its build backend, declared via PEP 517 in `pyproject.toml`. All project metadata, tool configuration (pytest, coverage, mypy, flake8, tox), and dependency management are consolidated in this single file.

### Key Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Single source of truth: build config, project metadata, dev deps, pytest/coverage/mypy/flake8/tox settings |
| `requirements-dev.txt` | Flat dev requirements list (used with pip-sync via the Makefile's `pyupgrade` target) |
| `Makefile` | Convenience targets for linting and dependency sync (requires activated venv) |
| `pytest_local.ini` | Alternative pytest config for local development (disables `--doctest-modules` for faster iteration) |
| `.travis.yml` | Travis CI pipeline configuration |
| `.github/workflows/lint_python.yml` | GitHub Actions workflow for Python linting |
| `.github/workflows/lint_pr.yml` | GitHub Actions workflow for PR title linting |
| `config_backup/` | Legacy configs (`setup.cfg`, `tox.ini`, `.coveragerc`) kept as historical reference |

## External Dependencies

### Runtime Dependencies

**None.** The `pyproject.toml` declares `dependencies = []`. All pattern implementations rely solely on the Python standard library:
- `queue.Queue` — used in `pool.py` for the ObjectPool
- `weakref.WeakValueDictionary` — used in `flyweight.py` for the card pool
- `copy.copy`, `copy.deepcopy` — used in `memento.py`
- `abc.ABC`, `abc.abstractmethod` — used in `composite.py`, `chain_of_responsibility.py`, `blackboard.py`
- `functools.update_wrapper` — used in `lazy_evaluation.py`
- `typing` module — used throughout for type annotations
- `random` — used in `abstract_factory.py` (random animal) and `blackboard.py`
- `inspect.signature` — used in `mvc.py` router

### Development Dependencies (from `pyproject.toml [project.optional-dependencies] dev`)

```
mypy>=?                # Static type checking
pipx>=1.7.1            # Tool isolation
pyupgrade              # Upgrade Python syntax to modern idioms
pytest>=6.2.0          # Test runner (also runs doctests via --doctest-modules)
pytest-cov>=2.11.0     # Coverage plugin
pytest-randomly>=3.1.0 # Randomize test ordering (seed=1234 by default)
black>=25.1.0          # Code formatter (line length 88 in Makefile)
build>=1.2.2           # PEP 517 build frontend
isort>=5.7.0           # Import sorter (profile=black)
flake8>=7.1.0          # Style linter
tox>=4.25.0            # Test environment manager
```

The `requirements-dev.txt` is a simpler flat list used with pip-sync (without version pins):
```
flake8
black
isort
pytest
pytest-randomly
mypy
pyupgrade
tox
```

## Build Targets and Commands

### Installing the Package

```bash
# Install in editable mode with all dev dependencies
pip install -e ".[dev]"

# Or sync from requirements-dev.txt (via Makefile):
make pyupgrade  # runs: pip-sync requirements-dev.txt
```

### Running Tests

The primary test command is configured in `pyproject.toml`:

```bash
# Full test suite (doctests + unit tests + coverage):
pytest

# This runs with these options from [tool.pytest.ini_options]:
#   --doctest-modules         — discovers and runs all doctests in patterns/
#   --randomly-seed=1234      — reproducible random ordering
#   --cov=patterns            — measure coverage of the patterns package
#   --cov-report=term-missing — show missing lines in terminal
```

```bash
# Local dev run (without doctest-modules, using pytest_local.ini):
pytest -c pytest_local.ini

# Run only unit tests (no doctests):
pytest tests/

# Run a specific test file:
pytest tests/creational/test_factory.py

# Run tests with verbose output:
pytest -v

# Run a specific doctest:
python -m doctest patterns/creational/factory.py -v
```

### Running Individual Pattern Files (Doctests)

Since every pattern file is executable:

```bash
python patterns/creational/factory.py
python patterns/behavioral/observer.py
python patterns/structural/facade.py
# etc.
```

### Linting

```bash
# Full lint pipeline (black + isort + flake8):
make pylinter

# Or individual tools:
black .
isort --atomic --profile black .
flake8 --max-line-length 120 --ignore E266,E731,W503 --exclude venv* .

# Via lint.sh (bash-compatible shell):
./lint.sh
```

**Flake8 configuration** (from `pyproject.toml [tool.flake8]`):
- `max-line-length = 120`
- `ignore = ["E266", "E731", "W503"]` (block comments, lambda assignment, line break before binary operator)
- `exclude = ["venv*"]`

**Black configuration**: Default settings (line length 88 in the Makefile, but no `[tool.black]` section in pyproject.toml — Makefile overrides to 88, while pyproject uses Black's default).

### Static Type Checking

```bash
mypy patterns/
# Uses [tool.mypy] config:
#   python_version = "3.12"
#   ignore_missing_imports = true
```

### Coverage Reporting

```bash
# Coverage runs automatically with pytest (via pytest-cov)
# To get HTML report:
pytest --cov=patterns --cov-report=html
# Opens: coverage_html_report/index.html
```

Coverage configuration in `[tool.coverage.run]`:
- `branch = true` — branch coverage enabled
- `dynamic_context = "test_function"` — per-test coverage attribution
- `parallel = true` — parallel coverage data collection
- Excluded lines: `def __repr__`, `raise AssertionError`, `raise NotImplementedError`, `if __name__ == "__main__":`, `@abstractmethod`

### Tox Environments

```bash
tox          # Run all environments
tox -e py312 # Run Python 3.12 environment only
```

Tox config (in `pyproject.toml [tool.tox]`):
- `envlist = py312, cov-report`
- `skip_missing_interpreters = true`
- `usedevelop = true`

## Python Version Requirements

- **Minimum**: Python 3.10 (`requires-python = ">=3.10"`)
- **Tested on**: 3.10, 3.11, 3.12, 3.13
- The codebase uses `match`/`case`-era syntax compatibility and `from __future__ import annotations` in several files for forward reference support
- `union type hints` like `Union[type[BaseException], None]` in `pool.py:46` use the `types.TracebackType` import for proper typing

## Package Building and Distribution

```bash
# Build source distribution and wheel:
python -m build

# Outputs to dist/:
#   python_patterns-0.1.0.tar.gz
#   python_patterns-0.1.0-py3-none-any.whl
```

The `[tool.setuptools]` config specifies `packages = ["patterns"]` — only the main patterns package is included (not tests or config_backup).
