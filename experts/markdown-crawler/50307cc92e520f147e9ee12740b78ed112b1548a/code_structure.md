# markdown-crawler — Code Structure

## Annotated Directory Tree

```
markdown-crawler/                   ← Repository root
├── markdown_crawler/               ← Python package (installable)
│   ├── __init__.py                 ← Core library: all crawling logic, public API
│   └── cli.py                      ← CLI entry point (argparse wrapper)
├── img/                            ← Screenshot images for README
│   ├── ss_crawler.png              ← Screenshot of CLI crawl progress
│   ├── ss_dir.png                  ← Screenshot of output markdown directory
│   └── ss_markdown.png             ← Screenshot of a generated markdown file
├── example.py                      ← Standalone usage example script
├── README.md                       ← Project documentation
├── requirements.txt                ← Runtime dependencies (3 packages)
├── pyproject.toml                  ← PEP 517 build metadata, console script entry point
├── setup.py                        ← Legacy setuptools shim
├── LICENSE.txt                     ← MIT License
└── .gitignore                      ← Git ignore rules
```

## Module and Package Organization

The project is a **single-package Python library** with minimal code surface area. There are exactly two Python source files beyond the example script:

### `markdown_crawler/__init__.py` — Core Library (359 lines)

This is the heart of the project. All public functions, constants, and the entire execution model live here. It is directly importable as `from markdown_crawler import md_crawl`.

**Module-level constants (lines 34–40):**

```python
DEFAULT_BASE_DIR = 'markdown'          # Output directory name
DEFAULT_MAX_DEPTH = 3                  # How many link-levels deep to crawl
DEFAULT_NUM_THREADS = 5                # Worker thread count
DEFAULT_TARGET_CONTENT = ['article', 'div', 'main', 'p']  # Fallback content elements
DEFAULT_TARGET_LINKS = ['body']        # Elements scanned for outgoing links
DEFAULT_DOMAIN_MATCH = True            # Restrict to same domain by default
DEFAULT_BASE_PATH_MATCH = True         # Restrict to same path prefix by default
```

**Functions defined in `__init__.py`:**

| Function | Lines | Purpose |
|---|---|---|
| `is_valid_url(url)` | 46–52 | URL validation using `urllib.parse.urlparse`; checks for scheme + netloc |
| `normalize_url(url)` | 58–60 | Strips trailing slash and removes query/fragment to deduplicate URLs |
| `crawl(...)` | 66–155 | Single-page crawl: HTTP fetch, HTML parse, Markdown write, child URL extraction |
| `get_target_content(soup, target_content)` | 158–186 | Extracts HTML content via CSS selectors or heuristic fallback |
| `get_target_links(soup, base_url, ...)` | 189–227 | Finds outgoing links from the soup, applies domain/path filters |
| `worker(q, base_url, max_depth, ...)` | 233–270 | Thread worker: dequeues URLs, calls `crawl()`, enqueues children |
| `md_crawl(base_url, ...)` | 276–358 | Public API: validates args, creates directory, spawns threads, joins them |

**Module-level metadata (lines 16–19):**

```python
__version__ = '0.1'
__author__ = 'Paul Pierre (github.com/paulpierre)'
__copyright__ = "(C) 2023 Paul Pierre. MIT License."
__contributors__ = ['Paul Pierre']
```

Note: version in `__init__.py` is `'0.1'` while `pyproject.toml` declares `"0.0.8"` — a minor discrepancy.

### `markdown_crawler/cli.py` — CLI Entry Point (56 lines)

Thin wrapper that uses `argparse` to parse command-line arguments and calls `md_crawl()`. Imports all defaults from `__init__.py` for consistency. The `main()` function is registered as the `markdown-crawler` console script in `pyproject.toml`.

**Argument mapping (CLI flag → `md_crawl` parameter):**

| CLI Flag | Short | Default | `md_crawl` param |
|---|---|---|---|
| `--max-depth` | `-d` | `DEFAULT_MAX_DEPTH` (3) | `max_depth` |
| `--num-threads` | `-t` | `DEFAULT_NUM_THREADS` (5) | `num_threads` |
| `--base-dir` | `-b` | `DEFAULT_BASE_DIR` (`'markdown'`) | `base_dir` |
| `--debug` | `-e` | `False` | `is_debug` |
| `--target-content` | `-c` | `DEFAULT_TARGET_CONTENT` | `target_content` |
| `--target-links` | `-l` | `DEFAULT_TARGET_LINKS` | `target_links` |
| `--valid-paths` | `-v` | `None` | `valid_paths` |
| `--domain-match` | `-m` | `DEFAULT_DOMAIN_MATCH` | `is_domain_match` |
| `--base-path-match` | `-p` | `DEFAULT_BASE_PATH_MATCH` | `is_base_path_match` |
| `--links` | `-i` | `True` | `is_links` |
| `base_url` | (positional) | required | `base_url` |

### `example.py` — Usage Reference (7 lines)

A ready-to-run demonstration script showing typical usage against the Rick and Morty Fandom wiki:

```python
from markdown_crawler import md_crawl
url = 'https://rickandmorty.fandom.com/wiki/Evil_Morty'
md_crawl(url, max_depth=3, num_threads=5, base_dir='markdown',
         valid_paths=['/wiki'], target_content=['div#content'],
         is_domain_match=True, is_base_path_match=False, is_debug=True)
```

## Key Files and Their Roles

| File | Role |
|---|---|
| `markdown_crawler/__init__.py` | All business logic; the only file users need to understand to use the library |
| `markdown_crawler/cli.py` | CLI glue; maps argparse namespace to `md_crawl()` keyword arguments |
| `pyproject.toml` | Package metadata, Python version requirement (`>=3.4`), console script registration |
| `requirements.txt` | Minimal dependency list for `pip install -r` usage |
| `setup.py` | Legacy compatibility shim (`find_packages` call only) |
| `example.py` | Canonical usage demonstration; useful as a quick integration test |

## Code Organization Patterns

**Flat module design**: All logic is in a single `__init__.py`. There is no sub-module hierarchy, no separate utilities or models files. This is intentional for a small, focused library.

**Thread safety note**: The `already_crawled` set is shared across threads without a mutex. Python's GIL provides some protection against corruption of pure Python objects like sets, but the check-then-add pattern in `crawl()` (lines 79 and 90) is not atomic. A race condition could cause the same URL to be crawled twice if two threads dequeue it simultaneously.

**Lazy directory creation**: `os.makedirs(base_dir)` is called in `md_crawl()` before threads start. File existence is checked in `crawl()` with `os.path.exists(file_path)` as the idempotency guard for resume functionality.

**Logging**: Uses Python's standard `logging` module with the logger named `markdown_crawler` (`__name__`). `is_debug=True` sets level to `DEBUG`; otherwise `INFO`. Both `basicConfig` calls affect the root logger, so the library will affect the host application's logging configuration if called with `is_debug=True`.

**Politeness delay**: `time.sleep(1)` is called in `worker()` after each URL is processed (line 270), providing a 1-second delay per thread between requests to avoid hammering servers.

**URL file naming**: File names are derived by extracting `\w+` tokens from the URL path and joining with `-` (line 251). The root path produces the filename `index.md`.
