# Scrapling — Build System

## Build System Type and Configuration Files

Scrapling uses **setuptools** as its build backend, declared via PEP 517/518 in `pyproject.toml`.

### Primary Configuration Files

| File | Role |
|---|---|
| `pyproject.toml` | Build system declaration, project metadata, dependencies, optional extras, tool configuration (mypy, pyright) |
| `setup.cfg` | Supplemental setuptools config (options, package discovery) |
| `MANIFEST.in` | Controls files included in source distribution tarballs |
| `tox.ini` | Multi-environment test automation |
| `pytest.ini` | pytest configuration (asyncio mode, doctest modules, markers) |
| `ruff.toml` | Ruff linter configuration |
| `.bandit.yml` | Bandit security scanner configuration |
| `.pre-commit-config.yaml` | Pre-commit hooks (linting, type checking, security) |
| `.readthedocs.yaml` | ReadTheDocs documentation build configuration |

### `pyproject.toml` Key Sections

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "scrapling"
version = "0.4.5"           # Static (not dynamic) for better Docker layer caching
requires-python = ">=3.10"
```

The version is intentionally kept **static** (not `dynamic = ["version"]`) to enable better Docker layer caching during CI builds.

## External Dependencies

### Core (always installed with `pip install scrapling`)

| Package | Version | Purpose |
|---|---|---|
| `lxml` | ≥ 6.0.2 | HTML parsing and XPath evaluation |
| `cssselect` | ≥ 1.4.0 | CSS-to-XPath translation |
| `orjson` | ≥ 3.11.8 | Fast JSON serialization (10x standard library) |
| `tld` | ≥ 0.13.2 | TLD/domain extraction for adaptive storage scoping |
| `w3lib` | ≥ 2.4.1 | URL canonicalization, HTML entity handling |
| `typing_extensions` | any | Backports for older Python |

### `fetchers` extra (`pip install "scrapling[fetchers]"`)

| Package | Version | Purpose |
|---|---|---|
| `click` | ≥ 8.3.0 | CLI framework |
| `curl_cffi` | ≥ 0.15.0 | TLS-fingerprint-impersonating HTTP client with HTTP/3 support |
| `playwright` | == 1.58.0 | Browser automation (DynamicFetcher/Session) |
| `patchright` | == 1.58.2 | Patched Playwright with stealth capabilities (StealthyFetcher/Session) |
| `browserforge` | ≥ 1.2.4 | Browser fingerprint data generation |
| `apify-fingerprint-datapoints` | ≥ 0.12.0 | Fingerprint dataset for realistic browser emulation |
| `msgspec` | ≥ 0.20.0 | High-performance serialization used in spider engine |
| `anyio` | ≥ 4.12.1 | Async I/O abstraction for spider crawl engine |
| `protego` | ≥ 0.6.0 | Robots.txt parsing and compliance |

> **Note**: `playwright` and `patchright` are pinned to **exact versions** (`==`) to prevent compatibility issues with browser binaries.

### `ai` extra (`pip install "scrapling[ai]"`)

| Package | Version | Purpose |
|---|---|---|
| `mcp` | ≥ 1.26.0 | Model Context Protocol server framework |
| `markdownify` | ≥ 1.2.0 | HTML-to-Markdown conversion |
| `scrapling[fetchers]` | — | Transitive (all fetcher deps included) |

### `shell` extra (`pip install "scrapling[shell]"`)

| Package | Version | Purpose |
|---|---|---|
| `IPython` | ≥ 8.37 | Interactive Python shell for `scrapling shell` command |
| `markdownify` | ≥ 1.2.0 | HTML-to-Markdown conversion for extract command |
| `scrapling[fetchers]` | — | Transitive (all fetcher deps included) |

### `all` extra (`pip install "scrapling[all]"`)

Installs `scrapling[ai,shell]` which transitively includes all dependencies.

## Build Targets and Commands

### Installation

```bash
# Parser only (no browser/HTTP client)
pip install scrapling

# With HTTP fetchers and browser support
pip install "scrapling[fetchers]"
scrapling install              # Downloads Playwright/Patchright browser binaries
scrapling install --force      # Force re-download

# With MCP server for AI integration
pip install "scrapling[ai]"

# With interactive shell
pip install "scrapling[shell]"

# Everything
pip install "scrapling[all]"
```

Browser binary installation can also be triggered from Python:

```python
from scrapling.cli import install
install([], standalone_mode=False)           # Normal install
install(["--force"], standalone_mode=False)  # Force reinstall
```

### Testing

The test suite requires the `fetchers`, `ai`, and `shell` extras. Tests are split into three groups to avoid conflicts:

```bash
# Full test run via tox (all Python versions 3.10–3.13)
tox

# Run only browser tests (no parallelization to avoid browser conflicts)
pytest --cov=scrapling --cov-report=xml -k "DynamicFetcher or StealthyFetcher" --verbose

# Run async tests without parallelization (CI nested loop issues)
pytest --cov=scrapling --cov-report=xml -m "asyncio" -k "not (DynamicFetcher or StealthyFetcher)" --verbose --cov-append

# Run all other tests with parallelization (pytest-xdist)
pytest --cov=scrapling --cov-report=xml -m "not asyncio" -k "not (DynamicFetcher or StealthyFetcher)" -n auto --cov-append
```

The `pytest.ini` configures:
- `asyncio_mode = strict` — all async tests must be explicitly marked `@pytest.mark.asyncio`
- `--doctest-modules` — doctests are extracted from module docstrings and run as tests
- `-p no:warnings` — warnings are suppressed in test output

Reported coverage: **92%** as of the latest release.

### Docker

A Docker image containing all browsers is built and published automatically on each release:

```bash
# Pull from DockerHub
docker pull pyd4vinci/scrapling

# Pull from GitHub Container Registry
docker pull ghcr.io/d4vinci/scrapling:latest
```

The `Dockerfile` is multi-stage and includes system browser dependencies.

### Linting and Code Quality

```bash
# Ruff linter (configured in ruff.toml)
ruff check scrapling/

# Pre-commit (runs all hooks)
pre-commit run --all-files

# Type checking — both tools run on CI
mypy scrapling/       # config in pyproject.toml [tool.mypy], python_version = 3.10
pyright scrapling/    # config in pyproject.toml [tool.pyright], typeCheckingMode = "basic"

# Security scanning
bandit -c .bandit.yml -r scrapling/
```

### Building the Distribution

```bash
# Build wheel + source distribution
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## Documentation

Documentation is hosted on ReadTheDocs at https://scrapling.readthedocs.io, built from the `docs/` directory. The `.readthedocs.yaml` specifies the build environment and Python version.

```bash
# Build docs locally (if Sphinx is configured)
cd docs && make html
```

## CLI Entry Point

The `scrapling` command is registered as a console script in `pyproject.toml`:

```toml
[project.scripts]
scrapling = "scrapling.cli:main"
```

Available subcommands:
- `scrapling install [--force]` — Install browser binaries
- `scrapling shell` — Launch interactive IPython web scraping shell (requires `shell` extra)
- `scrapling extract get|fetch|stealthy-fetch <url> <output_file> [options]` — Zero-code content extraction

## Package Discovery

```toml
[tool.setuptools.packages.find]
where = ["."]
include = ["scrapling*"]
```

All packages matching `scrapling*` are auto-discovered from the repository root. The `MANIFEST.in` ensures non-Python files (type markers, database files) are included in source distributions.
