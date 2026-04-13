# Trafilatura — Build System

## Build System Type and Configuration Files

Trafilatura uses **setuptools** as its build backend, configured entirely through `pyproject.toml` (PEP 517/518 compliant). There are no `setup.py` or `setup.cfg` files.

**Key configuration files:**

| File | Purpose |
|------|---------|
| `pyproject.toml` | Build system, package metadata, dependencies, entry points, test configuration |
| `trafilatura/settings.cfg` | Runtime configuration (INI format, loaded via `ConfigParser`) |
| `.coveragerc` | pytest-cov coverage configuration |
| `.readthedocs.yaml` | ReadTheDocs documentation build configuration |
| `docs/requirements.txt` | Documentation build dependencies (Sphinx) |
| `compose.yml` | Docker Compose for containerized development/testing |

### `pyproject.toml` Structure

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "trafilatura"
dynamic = ["version"]           # version read from trafilatura.__version__
requires-python = ">=3.8"

[tool.setuptools]
packages = ["trafilatura"]      # single package

[tool.setuptools.package-data]
trafilatura = [
    "data/tei_corpus.dtd",      # TEI DTD schema
    "settings.cfg",             # default config
]

[project.scripts]
trafilatura = "trafilatura.cli:main"   # CLI entry point

[tool.pytest.ini_options]
testpaths = "tests/*test*.py"
```

## External Dependencies

### Core (Always Required)

| Package | Purpose | Version |
|---------|---------|---------|
| `certifi` | SSL certificate bundle for HTTPS | any |
| `charset_normalizer` | Character encoding detection | >= 3.4.0 |
| `courlan` | URL management, deduplication, UrlStore | >= 1.3.2 |
| `htmldate` | Date extraction from HTML | >= 1.9.2 |
| `justext` | Stop-word-based content extraction (fallback) | >= 3.0.1 |
| `lxml` | HTML/XML parsing and tree manipulation | >= 5.3.0 (or 4.9.2 on macOS/Python 3.8) |
| `urllib3` | HTTP client | >= 1.26, < 3 |

**Note**: `lxml` has a platform-specific pin: `lxml == 4.9.2` on macOS with Python ≤ 3.8, `lxml >= 5.3.0` otherwise.

### Optional (Install with `pip install trafilatura[all]`)

| Package | Purpose | Condition |
|---------|---------|-----------|
| `brotli` | Brotli response decompression | always |
| `cchardet` | Faster encoding detection | Python < 3.11 |
| `faust-cchardet` | Faster encoding detection (3.11+ fork) | Python >= 3.11 |
| `htmldate[speed]` | Faster date extraction | always |
| `py3langid` | Language detection (ISO 639-1) | always |
| `pycurl` | Faster downloads via libcurl | always |
| `urllib3[socks]` | SOCKS proxy support | always |
| `zstandard` | Zstd response decompression | >= 0.23.0 |

### Development Dependencies (`pip install trafilatura[dev]`)

| Package | Purpose |
|---------|---------|
| `flake8` | Code style linting |
| `mypy` | Static type checking |
| `pytest` | Test runner |
| `pytest-cov` | Test coverage |
| `types-lxml` | Type stubs for lxml |
| `types-urllib3` | Type stubs for urllib3 |

## Build Targets and Commands

### Installation

```bash
# Install from PyPI (core only)
pip install trafilatura

# Install with all optional add-ons (speed, language detection)
pip install trafilatura[all]

# Install from source (development)
git clone https://github.com/adbar/trafilatura
cd trafilatura
pip install -e ".[dev]"

# Build wheel/sdist
pip install build
python -m build
```

### Testing

```bash
# Run all tests (uses pytest.ini_options: testpaths = "tests/*test*.py")
pytest

# Run with coverage
pytest --cov=trafilatura --cov-report=html

# Run a specific test file
pytest tests/unit_tests.py

# Run with verbose output
pytest -v tests/metadata_tests.py

# Run evaluation against real web data
python tests/evaluate.py
```

The test suite is organized by module: `unit_tests.py`, `baseline_tests.py`, `cli_tests.py`, `downloads_tests.py`, `feeds_tests.py`, `filters_tests.py`, `metadata_tests.py`, `json_metadata_tests.py`, `deduplication_tests.py`, `sitemaps_tests.py`, `spider_tests.py`, `xml_tei_tests.py`, and `realworld_tests.py`.

### Documentation

```bash
# Install Sphinx and doc dependencies
pip install -r docs/requirements.txt

# Build HTML docs
cd docs
make html

# Build on ReadTheDocs (automated via .readthedocs.yaml)
```

### Linting and Type Checking

```bash
# Flake8 linting
flake8 trafilatura/

# Mypy type checking
mypy trafilatura/
```

## Runtime Configuration (`settings.cfg`)

The `settings.cfg` file (INI format) controls runtime defaults loaded into every `Extractor` instance. It can be overridden at the CLI with `--config-file` or programmatically via the `config` or `settingsfile` parameters:

```ini
[DEFAULT]
# Download settings
DOWNLOAD_TIMEOUT = 30        # HTTP request timeout in seconds
MAX_FILE_SIZE = 20000000     # Maximum file size to download (20 MB)
MIN_FILE_SIZE = 10           # Minimum file size (bytes)
SLEEP_TIME = 5.0             # Sleep between requests (seconds)
USER_AGENTS =                # One per line; empty = use default Trafilatura UA
COOKIE =                     # HTTP cookie for requests
MAX_REDIRECTS = 2            # Max HTTP redirects to follow

# Extraction thresholds
MIN_EXTRACTED_SIZE = 250     # Min chars for main text to be valid
MIN_EXTRACTED_COMM_SIZE = 1  # Min chars for comments to be valid
MIN_OUTPUT_SIZE = 1          # Min chars in final output
MIN_OUTPUT_COMM_SIZE = 1     # Min chars in final comment output
MAX_TREE_SIZE =              # Max lxml tree elements (empty = unlimited)
EXTRACTION_TIMEOUT = 30      # CLI file processing timeout (0 to disable)

# Deduplication
MIN_DUPLCHECK_SIZE = 100     # Min chars before checking duplicates
MAX_REPETITIONS = 2          # Max allowed repetitions of a text block

# Date extraction
EXTENSIVE_DATE_SEARCH = on   # Use extensive date search in htmldate

# Discovery
EXTERNAL_URLS = off          # Allow external URLs in feeds/sitemaps
```

## Python Version Support

Trafilatura officially supports Python **3.8 through 3.13** (as declared in `pyproject.toml` classifiers and `requires-python = ">=3.8"`). CI is run on all supported versions via GitHub Actions. Python 3.6 and 3.7 were dropped in version 2.0.0.

## Package Data

Two files are bundled with the package via `[tool.setuptools.package-data]`:
- `trafilatura/data/tei_corpus.dtd` — Used for XML-TEI output validation (`--validate-tei` CLI flag or `tei_validation=True` parameter)
- `trafilatura/settings.cfg` — Default configuration; loaded by `settings.use_config()` when no custom file is specified

The `py.typed` marker (PEP 561) declares the package as typed for mypy/type checkers.

## Versioning

Version is declared in `trafilatura/__init__.py` as `__version__ = "2.0.0"` and dynamically read by setuptools:

```toml
[tool.setuptools.dynamic]
version = {attr = "trafilatura.__version__"}
```

## Docker

A `compose.yml` is provided for containerized development and testing. Use `docker compose up` or `docker compose run` to execute tests in a controlled environment.
