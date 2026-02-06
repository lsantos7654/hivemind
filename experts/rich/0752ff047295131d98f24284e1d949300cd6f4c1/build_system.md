# Rich Build System and Development Workflow

## Build System Overview

Rich uses **Poetry** as its build system and dependency manager, configured via `pyproject.toml`. Poetry provides reproducible builds, dependency resolution, and packaging functionality. The project follows modern Python packaging standards using `poetry-core` as the PEP 517 build backend.

## Package Configuration (pyproject.toml)

### Package Metadata

```toml
[tool.poetry]
name = "rich"
version = "14.3.2"
description = "Render rich text, tables, progress bars, syntax highlighting, markdown and more to the terminal"
authors = ["Will McGugan <willmcgugan@gmail.com>"]
license = "MIT"
homepage = "https://github.com/Textualize/rich"
documentation = "https://rich.readthedocs.io/en/latest/"
```

**Python Version Support**: Python 3.8 through 3.14 (forward-compatible)

**Classifiers**: Production/Stable status, Console Environment, IPython Framework integration

### Dependencies

**Runtime Dependencies** (minimal):
- `python` >= 3.8.0
- `pygments` ^2.13.0 - Powers all syntax highlighting
- `markdown-it-py` >= 2.2.0 - Markdown parsing engine
- `ipywidgets` >= 7.5.1, <9 (optional, for Jupyter support)

**Optional Features**:
```toml
[tool.poetry.extras]
jupyter = ["ipywidgets"]
```

Install with Jupyter support: `pip install rich[jupyter]`

**Development Dependencies**:
- `pytest` ^7.0.0 - Testing framework
- `pytest-cov` ^3.0.0 - Coverage reporting
- `mypy` ^1.11 - Static type checking
- `black` ^22.6 - Code formatting
- `attrs` ^21.4.0 - Testing utilities
- `pre-commit` ^2.17.0 - Git hooks
- `typing-extensions` >= 4.0.0, <5.0 - Type hint backports

### Build Backend

```toml
[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"
```

Uses the modern `poetry-core` build backend, compatible with PEP 517/518.

## Installation Methods

### End Users

**Via pip** (recommended):
```bash
pip install rich
```

**Via Poetry** (for projects using Poetry):
```bash
poetry add rich
```

**From source** (development):
```bash
git clone https://github.com/Textualize/rich.git
cd rich
poetry install
```

### Testing Installation

After installation, verify Rich works:
```bash
python -m rich
```

This runs the `__main__.py` module which displays a demo of Rich's capabilities.

## Development Workflow

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/Textualize/rich.git
cd rich

# Install with development dependencies
poetry install

# Install pre-commit hooks
pre-commit install
```

### Code Quality Tools

**Type Checking with mypy**:

Configuration in `pyproject.toml`:
```toml
[tool.mypy]
files = ["rich"]
show_error_codes = true
strict = true
enable_error_code = ["ignore-without-code", "redundant-expr", "truthy-bool"]
```

Rich uses strict mypy settings with comprehensive type coverage. Ignored imports for external packages without stubs (pygments, IPython, ipywidgets).

Run type checking:
```bash
poetry run mypy rich
```

**Code Formatting with Black**:

Configuration in `pyproject.toml`:
```toml
[tool.isort]
profile = "black"
```

Rich uses Black's opinionated formatting with isort configured to be Black-compatible.

Format code:
```bash
poetry run black rich
poetry run isort rich
```

**Pre-commit Hooks** (`.pre-commit-config.yaml`):

Automated checks before commits:
- Code formatting (Black)
- Import sorting (isort)
- Type checking (mypy)
- Linting and other checks

Hooks run automatically on `git commit` or manually:
```bash
pre-commit run --all-files
```

## Testing

### Test Configuration

Pytest configuration in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
```

Additional configuration in `tox.ini` and `.coveragerc` for coverage settings.

### Running Tests

**Run full test suite**:
```bash
poetry run pytest
```

**Run with coverage**:
```bash
poetry run pytest --cov=rich --cov-report=html
```

**Run specific test file**:
```bash
poetry run pytest tests/test_console.py
```

**Run specific test**:
```bash
poetry run pytest tests/test_console.py::test_print
```

### Test Structure

Tests located in `tests/` directory:
- `test_*.py` - Unit tests for corresponding modules
- `conftest.py` - Shared pytest fixtures
- `render.py` - Test rendering utilities
- Snapshot testing for rendered output verification

Coverage configured via `.coveragerc`:
- Excludes: pragma comments, type checking blocks, debugging code
- Target: High coverage across all modules

## Documentation

### Documentation System

**Sphinx-based documentation** with Read the Docs theme:

Configuration in `docs/source/conf.py`:
- Auto-generated API docs from docstrings
- Napoleon extension for Google/NumPy style docstrings
- Intersphinx for linking to external docs
- Copy button extension for code blocks

### Building Documentation

**Using Makefile** (Linux/macOS):
```bash
cd docs
make html
```

**Using make.bat** (Windows):
```bash
cd docs
make.bat html
```

Documentation generated in `docs/build/html/`.

### Documentation Deployment

Documentation automatically built and deployed to Read the Docs:
- Configuration: `.readthedocs.yml`
- URL: https://rich.readthedocs.io/
- Automatic rebuilds on commits to main branch

## Performance Benchmarking

### Benchmark Suite

Located in `benchmarks/`:
- `benchmarks.py` - Main benchmark suite
- `snippets.py` - Code snippets for benchmarking

**ASV Configuration** (`asv.conf.json`):

Uses Airspeed Velocity (ASV) for performance regression testing:
```bash
asv run
asv publish
asv preview
```

Tracks performance across commits to detect regressions.

## Build Targets and Commands

### Common Development Commands

| Command | Purpose |
|---------|---------|
| `poetry install` | Install dependencies |
| `poetry run pytest` | Run tests |
| `poetry run mypy rich` | Type check |
| `poetry run black rich` | Format code |
| `poetry build` | Build distribution packages |
| `poetry publish` | Publish to PyPI |
| `pre-commit run --all-files` | Run all pre-commit checks |

### Building Distribution

**Build wheel and sdist**:
```bash
poetry build
```

Output in `dist/`:
- `rich-14.3.2-py3-none-any.whl` (wheel)
- `rich-14.3.2.tar.gz` (source distribution)

**Publishing** (maintainers only):
```bash
poetry publish
```

Requires PyPI credentials configured in Poetry.

## Continuous Integration

**GitHub Actions** workflows in `.github/workflows/`:
- Run tests on multiple Python versions (3.8-3.14)
- Run type checking with mypy
- Check code formatting with Black
- Build documentation
- Coverage reporting to codecov.io

## Additional Tools

**Tox** (`tox.ini`): Multi-environment testing (legacy, gradually being replaced by Poetry scripts)

**Git Hooks** via pre-commit: Ensures code quality before commits

**FAQ System**: YAML-based FAQ in `faq.yml` with tooling in `questions/` and `.faq/`

## Summary

Rich's build system emphasizes:
- **Simplicity**: Poetry handles all dependency and build management
- **Quality**: Strict type checking, formatting, and testing requirements
- **Reproducibility**: Locked dependencies via `poetry.lock`
- **Developer Experience**: Pre-commit hooks catch issues early
- **Minimal Runtime Dependencies**: Only 2 required dependencies (pygments, markdown-it-py)

The streamlined build process enables contributors to quickly get started while maintaining high code quality standards.
