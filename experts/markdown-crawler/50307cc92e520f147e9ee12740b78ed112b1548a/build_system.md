# markdown-crawler — Build System

## Build System Type

`markdown-crawler` uses **setuptools** as the build backend, configured via PEP 517/518 standards. There are two configuration files:

- **`pyproject.toml`** — the primary, modern configuration file (PEP 517 build metadata + project metadata)
- **`setup.py`** — a minimal legacy shim for compatibility with older pip versions

## Configuration Files

### `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "markdown-crawler"
version = "0.0.8"
authors = [
  { name="Paul Pierre", email="hi@paulpierre.com" },
]
description = "A multithreaded 🕸️ web crawler that recursively crawls a website and creates a 🔽 markdown file for each page"
readme = "README.md"
requires-python = ">=3.4"
classifiers = [
    "Programming Language :: Python :: 3",
    "License :: OSI Approved :: MIT License",
    "Operating System :: OS Independent",
]

[project.urls]
"Homepage" = "https://github.com/paulpierre/markdown-crawler"
"Bug Tracker" = "https://github.com/paulpierre/markdown-crawler/issues"
"Twitter" = "https://twitter.com/paulpierre"

[project.scripts]
markdown-crawler = "markdown_crawler.cli:main"
```

Key points:
- **Package version**: `0.0.8` (note: `__init__.py` has `__version__ = '0.1'`, a discrepancy)
- **Python requirement**: `>=3.4` (compatible with modern Python 3.x)
- **Console script**: `markdown-crawler` command maps to `markdown_crawler.cli:main`
- **No `[project.dependencies]`** section — runtime dependencies are declared only in `requirements.txt`, not in `pyproject.toml`. This means `pip install markdown-crawler` from PyPI will not auto-install dependencies unless the publisher uploaded the package with them declared. Users installing from source via `pip install .` will also need to manually install requirements.

### `setup.py`

```python
from setuptools import setup, find_packages

setup(
    name="markdown-crawler",
    packages=find_packages(exclude=['markdown']),
    include_package_data=True,
)
```

This is a minimal shim. `find_packages()` discovers the `markdown_crawler` package. The `exclude=['markdown']` prevents the output `markdown/` directory (where crawled files are saved) from being accidentally packaged. `include_package_data=True` enables inclusion of non-Python files if a `MANIFEST.in` were present (none exists currently).

### `requirements.txt`

```
beautifulsoup4
requests
markdownify
```

Three runtime dependencies, pinned to no specific version. All are well-established packages available on PyPI.

## External Dependencies

| Package | Purpose | Notes |
|---|---|---|
| `beautifulsoup4` | HTML parsing and CSS selector evaluation | Provides `BeautifulSoup` class; uses `html.parser` (stdlib) as the parser backend |
| `requests` | HTTP GET requests to fetch pages | Used for all network I/O; no async support |
| `markdownify` | HTML-to-Markdown conversion | By Matthew Tretter, MIT licensed; used via `from markdownify import markdownify as md` |

All three are standard, widely-available packages. The library uses only stdlib modules beyond these: `urllib.parse`, `threading`, `logging`, `queue`, `time`, `os`, `re`, and `typing`.

## Build Targets and Commands

### Install from PyPI

```bash
pip install markdown-crawler
```

After installation, the `markdown-crawler` CLI command is available in the active Python environment.

### Install from Source (development)

```bash
git clone https://github.com/paulpierre/markdown-crawler
cd markdown-crawler
pip install .
```

Or for editable/development install:

```bash
pip install -e .
```

### Install Dependencies Only

```bash
pip install -r requirements.txt
```

### Build a Distribution Package

```bash
pip install build
python -m build
```

This produces `dist/markdown_crawler-0.0.8.tar.gz` and `dist/markdown_crawler-0.0.8-py3-none-any.whl`.

### Publish to PyPI

```bash
pip install twine
twine upload dist/*
```

## Testing

There is **no test suite** in this repository. No `tests/` directory, no `pytest.ini`, no `tox.ini`, and no CI configuration files (GitHub Actions, etc.) are present. The `example.py` script serves as the only runnable demonstration.

To manually verify functionality:

```bash
python example.py
```

This crawls `https://rickandmorty.fandom.com/wiki/Evil_Morty` to depth 3 using 5 threads and writes Markdown files to `./markdown/`.

## How to Deploy / Use as a CLI

After installation:

```bash
# Basic usage
markdown-crawler https://en.wikipedia.org/wiki/Python_(programming_language)

# With options
markdown-crawler \
  --max-depth 3 \
  --num-threads 5 \
  --base-dir ./output \
  --target-content "div#content" \
  --valid-paths "/wiki" \
  --debug \
  https://en.wikipedia.org/wiki/Python_(programming_language)
```

## Version Notes

- `pyproject.toml` declares version `0.0.8`
- `markdown_crawler/__init__.py` declares `__version__ = '0.1'`
- These are inconsistent; the PyPI/package version (`0.0.8`) is the authoritative release version
