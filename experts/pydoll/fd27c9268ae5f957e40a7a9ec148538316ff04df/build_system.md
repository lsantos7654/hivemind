# Pydoll: Build System

## Build System Type

Pydoll uses **Poetry** as its build and dependency management tool. The build backend is `poetry-core`. All project configuration lives in `pyproject.toml` at the repository root.

**Package name on PyPI**: `pydoll-python`  
**Current version**: `2.22.1`  
**Python requirement**: `^3.10`

## Configuration Files

| File | Purpose |
|---|---|
| `pyproject.toml` | Project metadata, dependencies, tool config (ruff, pytest, mypy, taskipy) |
| `poetry.lock` | Pinned dependency lock file (committed to repo) |
| `.python-version` | Python version for pyenv/asdf version managers |
| `codecov.yml` | Codecov coverage reporting configuration |
| `cz.yaml` | Commitizen conventional commit configuration |
| `mkdocs.yml` | MkDocs documentation site configuration |
| `.github/` | GitHub Actions CI workflow definitions |

## External Dependencies

### Runtime Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.10"
websockets = ">=14,<17"        # Async WebSocket client for CDP
aiohttp = "^3.9.5"             # Async HTTP (used in bundle resource fetching)
aiofiles = "^25.1.0"           # Async file I/O for screenshots, PDFs, zip bundles
typing_extensions = "^4.14.0"  # TypedDict, TypeAlias backports for Python 3.10
pydantic = "^2.0"              # Model validation for ExtractionModel
```

**Important**: `aiohttp` is listed as a dependency but the primary HTTP request mechanism for `tab.request` uses the **browser's built-in JavaScript fetch API** (executed via CDP `Runtime.evaluate`). `aiohttp` is used for fetching page resources during bundle saving.

### Development Dependencies

```toml
[tool.poetry.group.dev.dependencies]
ruff = "^0.7.1"                          # Linter + formatter (replaces flake8/isort/black)
pytest = "^8.3.3"                        # Test runner
taskipy = "^1.14.0"                      # Task runner (poetry run task <name>)
pytest-asyncio = "^0.24.0"              # Async test support
pytest-cov = "^6.0.0"                   # Coverage reports
aioresponses = "^0.7.7"                  # Mock aiohttp responses in tests
mkdocs = "^1.6.1"                        # Documentation site generator
mkdocs-material = "^9.6.11"             # Material theme for MkDocs
pymdown-extensions = "^10.14.3"         # Markdown extensions
mkdocstrings = {extras = ["python"], version = "^0.29.1"}  # Auto-docs from docstrings
griffe-typingdoc = "^0.2.8"            # Typing-based docstring griffe extension
mkdocs-static-i18n = "^1.3.0"          # i18n support for docs
```

## Build Targets and Commands

### Installing Dependencies

```bash
# Install all dependencies (including dev)
poetry install

# Install only runtime dependencies
poetry install --only main
```

### Taskipy Tasks (via `poetry run task <name>`)

Tasks are defined in `pyproject.toml` under `[tool.taskipy.tasks]`:

```toml
lint      = 'ruff check .; ruff check . --diff'
format    = 'ruff check . --fix; ruff format .'
test      = 'pytest -s -x --cov=pydoll -vv'
post_test = 'coverage html'
```

| Task | Command | Description |
|---|---|---|
| `lint` | `poetry run task lint` | Run ruff linter, show diff of fixable issues |
| `format` | `poetry run task format` | Auto-fix and format code with ruff |
| `test` | `poetry run task test` | Run full test suite with coverage |
| (auto) `post_test` | (runs after test) | Generate HTML coverage report |

### Running Tests Directly

```bash
# Full test suite with coverage
pytest -s -x --cov=pydoll -vv

# Run a specific test file
pytest tests/test_web_element.py -vv

# Run tests matching a pattern
pytest -k "test_shadow" -vv

# Generate HTML coverage report
coverage html
```

### Linting and Formatting

```bash
# Check linting issues
poetry run task lint

# Auto-fix and format
poetry run task format

# Or directly:
ruff check .
ruff format .
```

### Type Checking

```bash
mypy pydoll/
```

Mypy is configured in `pyproject.toml`:
```toml
[tool.mypy]
exclude = ["tests/"]
```

The `pydoll/py.typed` marker file (PEP 561) is included in the package to signal that the library ships inline type stubs.

## Ruff Configuration

```toml
[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
preview = true
select = ['I', 'F', 'E', 'W', 'PL', 'PT']
ignore = ['PLR0913', 'PLR0917', 'PLR0904', 'E701']
exclude = ['tests', 'tests/*']

[tool.ruff.format]
preview = true
quote-style = 'single'
docstring-code-format = true
docstring-code-line-length = 79
exclude = ['tests', 'tests/*']
```

Note: Lint rules are **not** enforced on the `tests/` directory.

## Pytest Configuration

```toml
[tool.pytest.ini_options]
pythonpath = "."
addopts = '-p no:warnings'
```

Tests are suppressed from emitting warnings by default (`-p no:warnings`). The root is added to `pythonpath` so `import pydoll` works from the test directory without installation.

## Continuous Integration

CI is defined in `.github/` with three workflows visible from the README badges:
- **tests.yml**: Runs `pytest` on push/PR
- **ruff-ci.yml**: Runs ruff linting
- **mypy.yml**: Runs mypy type checking

Code coverage is reported to Codecov (configured via `codecov.yml`).

## Building and Publishing

```bash
# Build wheel and sdist
poetry build

# Publish to PyPI (requires configured credentials)
poetry publish
```

The package name on PyPI is `pydoll-python`, not `pydoll`. Users install it with:
```bash
pip install pydoll-python
```

The `packages` config in `pyproject.toml` includes only the `pydoll/` directory:
```toml
packages = [{include = "pydoll"}]
include = ["pydoll/py.typed"]
```

## Documentation

Documentation is built with MkDocs + Material theme and published at `https://pydoll.tech/`.

```bash
# Serve docs locally
mkdocs serve

# Build docs site
mkdocs build
```

## Changelog Management

The project uses **Commitizen** (`cz.yaml`) for conventional commits and automated changelog generation. The `CHANGELOG.md` follows semantic versioning format with `Feat`, `Fix`, and `Refactor` sections per release.

## Version Management

Version is managed by Poetry in `pyproject.toml`. Bumping versions is typically done via Commitizen:
```bash
cz bump
```
