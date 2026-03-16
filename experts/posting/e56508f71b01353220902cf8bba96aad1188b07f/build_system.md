# Posting — Build System

## Build System Type

Posting uses **Hatchling** as its build backend, configured via `pyproject.toml` (PEP 517/518 compliant). The project manager is **uv** (recommended) with `pip`/`pipx` as alternatives.

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata, dependencies, build config, tool config |
| `uv.lock` | Locked dependency tree for reproducible installs |
| `.python-version` | Pins Python to 3.11.7 for development |
| `Makefile` | Convenience targets for common developer tasks |
| `mkdocs.yml` | Documentation site build configuration |

## Project Metadata (`pyproject.toml`)

```toml
[project]
name = "posting"
version = "2.9.2"
description = "The modern API client that lives in your terminal."
requires-python = ">=3.11"
readme = "README.md"
license = { text = "Apache License Version 2.0" }

[project.scripts]
posting = "posting.__main__:cli"
```

The package entry point maps the `posting` CLI command to `posting.__main__:cli` (the click group).

## External Dependencies

### Production Dependencies

```toml
[project.dependencies]
click = ">=8.1.7"
click-default-group = ">=1.2.4"
httpx = {version = "0.28.1", extras = ["brotli"]}   # PINNED exact version
openapi-pydantic = ">=0.5.0"
pyperclip = ">=1.9.0"
pydantic = ">=2.9.2"
pyyaml = ">=6.0.2"
pydantic-settings = ">=2.4.0"
python-dotenv = ">=1.0.1"
watchfiles = ">=0.24.0"
textual = {version = "6.1.0", extras = ["syntax"]}  # PINNED exact version
textual-autocomplete = "4.0.6"                       # PINNED exact version
xdg-base-dirs = ">=6.0.1"
```

**Notable pinning:** `httpx`, `textual`, and `textual-autocomplete` are pinned to exact versions. httpx is pinned because Posting monkeypatches `httpx._main` to prevent CLI loading (`sys.modules['httpx._main'] = None` in `__init__.py`), and this patch is tied to the specific version's internal structure.

### Development Dependencies

```toml
[tool.hatch.envs.default.dependencies]
textual-dev = ">=1.5.1"
pytest = ">=8.3.3"
jinja2 = ">=3.1.4"
syrupy = ">=4.7.2"
pytest-xdist = ">=3.6.1"
pytest-cov = ">=5.0.0"
pytest-textual-snapshot = ">=0.4.0"
mkdocs-material = ">=9.5.39"
pyinstrument = ">=4.7.3"
```

## Build Targets and Commands

### Installation (End Users)

```bash
# Recommended: uv tool install (isolated)
uv tool install posting

# Alternative: pipx
pipx install posting

# Alternative: pip (global or venv)
pip install posting
```

### Development Setup

```bash
# Clone and install dev dependencies
git clone https://github.com/darrenburns/posting
cd posting
uv sync                          # Creates .venv and installs all deps

# Activate virtual environment
source .venv/bin/activate        # Unix/macOS
.venv\Scripts\activate           # Windows

# Run the TUI
posting

# Run with Textual devtools (hot reload, DOM inspector)
TEXTUAL=devtools,debug posting
```

### Running Tests

```bash
# Run all tests (via Makefile)
make test

# Update UI snapshots (when intentional UI changes are made)
make test-snapshot-update

# CI mode
make test-ci

# Directly via pytest
uv run pytest
uv run pytest tests/test_curl_import.py           # Specific test file
uv run pytest -k "test_basic_get"                  # Specific test by name
uv run pytest -n auto                              # Parallel execution (pytest-xdist)
uv run pytest --snapshot-update                    # Update snapshots
uv run pytest --cov=posting --cov-report=html      # Coverage report
```

**Makefile targets:**
```makefile
test:               pytest tests/ -x
test-snapshot-update: pytest tests/ --snapshot-update
test-ci:            pytest tests/ --ci
```

### Building for Distribution

```bash
# Build wheel and sdist
uv build
# or
python -m build

# Output in dist/
# posting-2.9.2-py3-none-any.whl
# posting-2.9.2.tar.gz
```

### Documentation

```bash
# Install mkdocs-material
uv sync

# Serve docs locally
mkdocs serve

# Build static docs site
mkdocs build
# Output in site/
```

## Test Architecture

The test suite uses two distinct strategies:

### 1. Unit/Integration Tests
Standard pytest tests for non-UI logic:
- `test_curl_import.py` — parses cURL command strings, verifies `RequestModel` output
- `test_curl_export.py` — converts `RequestModel` to cURL, verifies string output
- `test_postman_import.py` — parses Postman JSON, verifies collection structure
- `test_open_api_import.py` — parses OpenAPI specs, verifies collection structure
- `test_urls.py` — URL utilities (path param extraction, protocol insertion)
- `test_variables.py` — variable substitution (`$VAR` / `${VAR}` patterns)
- `test_files.py` — file naming validation (DOS names, length limits)

### 2. Snapshot Tests (`test_snapshots.py`)
Uses `pytest-textual-snapshot` and `syrupy` to capture terminal screenshots of the TUI and compare against stored baselines. Each test launches a `PostingApp` fixture, performs interactions, and asserts the screen matches the snapshot PNG.

- Snapshots are stored in `tests/__snapshots__/test_snapshots/`
- Marked with `@pytest.mark.serial` for tests requiring serial execution
- Update with `--snapshot-update` flag when UI changes are intentional

```python
# Example snapshot test pattern
async def test_method_selector(snap_compare, tmp_path):
    async with PostingApp(collection_dir=tmp_path) as app:
        await app.press("tab")  # navigate to method selector
        assert await snap_compare(app)
```

## Python Version Requirement

Minimum: **Python 3.11** (required for modern type syntax used throughout codebase)
Pinned development version: **3.11.7** (via `.python-version`)

## Package Structure

```
src/
└── posting/           # Source layout (PEP 517 src layout)
    ├── __init__.py    # Package marker + public API exports
    └── ...
```

Uses `src/` layout (src-layout) to prevent accidental imports of the package during testing without installation.

## Notable Build Considerations

1. **httpx monkeypatch:** `src/posting/__init__.py` sets `sys.modules['httpx._main'] = None` immediately on import. This prevents httpx's CLI (`rich`, `click` extras) from loading unnecessarily. This is why httpx is pinned to an exact version.

2. **SCSS compilation:** `posting.scss` is used for widget styling. Textual handles SCSS compilation at runtime — no separate CSS compilation step is needed.

3. **Tree-sitter syntax highlighting:** Enabled via `textual[syntax]` extra, which includes tree-sitter grammars. No separate tree-sitter compilation step needed.

4. **Startup timing:** `src/posting/_start_time.py` captures `time.time()` at import time. This module is imported before anything else in `__main__.py` to measure startup latency accurately.
