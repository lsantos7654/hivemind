# Scrapling — Code Structure

## Annotated Directory Tree

```
Scrapling/
├── scrapling/                    # Main Python package
│   ├── __init__.py               # Lazy-import public API: Selector, Fetcher, AsyncFetcher, StealthyFetcher, DynamicFetcher
│   ├── cli.py                    # Click-based CLI: `scrapling` entry point (install, shell, extract)
│   ├── parser.py                 # Core: Selector and Selectors classes
│   ├── py.typed                  # PEP 561 marker — full type hints
│   │
│   ├── core/                     # Shared internals
│   │   ├── __init__.py
│   │   ├── _types.py             # Re-exports typing constructs + custom type aliases
│   │   ├── _shell_signatures.py  # Type stubs/signatures for interactive shell
│   │   ├── ai.py                 # MCP server implementation (FastMCP)
│   │   ├── custom_types.py       # TextHandler, TextHandlers, AttributesHandler
│   │   ├── mixins.py             # SelectorsGeneration mixin (selector auto-generation)
│   │   ├── shell.py              # Convertor: HTML→Markdown/text for CLI and MCP
│   │   ├── storage.py            # StorageSystemMixin, SQLiteStorageSystem (adaptive storage)
│   │   ├── translator.py         # CSS-to-XPath translator (adapted from Parsel)
│   │   └── utils/
│   │       ├── __init__.py       # Re-exports all utilities
│   │       ├── _utils.py         # log, clean_spaces, flatten, _StorageTools, helpers
│   │       └── _shell.py         # Shell utilities: _CookieParser, _ParseHeaders
│   │
│   ├── engines/                  # Low-level fetch/browser engines
│   │   ├── __init__.py
│   │   ├── constants.py          # Shared constants (browser types, resource types, etc.)
│   │   ├── static.py             # FetcherSession, FetcherClient, AsyncFetcherClient (curl_cffi)
│   │   ├── _browsers/            # Browser engine internals
│   │   │   ├── __init__.py
│   │   │   ├── _base.py          # BaseBrowserEngine base class
│   │   │   ├── _config_tools.py  # Browser configuration helpers (context, page options)
│   │   │   ├── _controllers.py   # DynamicSession, AsyncDynamicSession (Playwright)
│   │   │   ├── _page.py          # Page interaction utilities
│   │   │   ├── _stealth.py       # StealthySession, AsyncStealthySession (Patchright)
│   │   │   ├── _types.py         # TypedDicts for PlaywrightSession, StealthSession params
│   │   │   └── _validators.py    # Parameter validation utilities
│   │   └── toolbelt/
│   │       ├── __init__.py       # Exports: ProxyRotator, Response, BaseFetcher
│   │       ├── convertor.py      # ResponseFactory: converts curl_cffi/playwright responses → Response
│   │       ├── custom.py         # Response (subclass of Selector), BaseFetcher, StatusText
│   │       ├── fingerprints.py   # Browser header/fingerprint generation (browserforge)
│   │       ├── navigation.py     # Browser navigation helpers
│   │       └── proxy_rotation.py # ProxyRotator, cyclic_rotation strategy
│   │
│   ├── fetchers/                 # High-level fetcher public API
│   │   ├── __init__.py           # Lazy imports: Fetcher, AsyncFetcher, FetcherSession, DynamicFetcher, etc.
│   │   ├── requests.py           # Fetcher, AsyncFetcher (thin wrappers over FetcherClient instances)
│   │   ├── chrome.py             # DynamicFetcher (wraps DynamicSession)
│   │   └── stealth_chrome.py     # StealthyFetcher (wraps StealthySession)
│   │
│   └── spiders/                  # Spider crawling framework
│       ├── __init__.py           # Exports: Spider, Request, Response, CrawlerEngine, CrawlResult, etc.
│       ├── spider.py             # Spider ABC — user-facing API, start(), stream(), pause()
│       ├── request.py            # Request dataclass with fingerprinting and pickle support
│       ├── engine.py             # CrawlerEngine — async crawler loop, semaphores, scheduling
│       ├── session.py            # SessionManager — session registry with lazy init
│       ├── scheduler.py          # Priority queue scheduler for Request objects
│       ├── result.py             # CrawlResult, CrawlStats, ItemList
│       ├── checkpoint.py         # Checkpoint serialization/deserialization (pause/resume)
│       ├── cache.py              # Development mode disk cache
│       └── robotstxt.py          # Robots.txt fetching and compliance checking
│
├── tests/                        # Test suite
├── docs/                         # Documentation source (ReadTheDocs)
├── agent-skill/                  # AI agent skill definitions
├── benchmarks.py                 # Performance benchmark script
├── cleanup.py                    # Utility to clean up Playwright processes
├── pyproject.toml                # Build metadata, dependencies, optional extras
├── setup.cfg                     # Supplemental setuptools config
├── MANIFEST.in                   # Source distribution manifest
├── Dockerfile                    # Multi-stage Docker image with all browsers
├── tox.ini                       # tox test automation config
├── pytest.ini                    # pytest configuration
├── ruff.toml                     # Ruff linter config
├── .bandit.yml                   # Bandit security scanner config
├── .readthedocs.yaml             # ReadTheDocs build config
└── .pre-commit-config.yaml       # Pre-commit hooks
```

## Module and Package Organization

### Top-level Package (`scrapling/__init__.py`)

Uses a **lazy import** pattern via `__getattr__`. None of the heavy dependencies (Playwright, curl_cffi, etc.) are loaded on `import scrapling`. Only `from scrapling import Selector` (or similar) triggers the actual import of the relevant submodule. This design keeps startup time minimal and allows the core parser to be installed without fetcher dependencies.

```python
# scrapling/__init__.py:13-32
_LAZY_IMPORTS = {
    "Fetcher": ("scrapling.fetchers", "Fetcher"),
    "Selector": ("scrapling.parser", "Selector"),
    ...
}
```

The same pattern is used in `scrapling/fetchers/__init__.py` and `scrapling/engines/toolbelt/__init__.py`.

### Core Layer (`scrapling/core/`)

| File | Role |
|---|---|
| `_types.py` | Centralizes all typing imports and defines custom type aliases (`SUPPORTED_HTTP_METHODS`, `ProxyType`, `extraction_types`, etc.) to avoid repetition across files |
| `custom_types.py` | `TextHandler` (str subclass), `TextHandlers` (list subclass), `AttributesHandler` (read-only mapping). These are the return types for virtually all text/attribute extraction |
| `mixins.py` | `SelectorsGeneration` mixin added to `Selector`; contains `generate_css_selector`, `generate_xpath_selector`, `generate_full_css_selector` |
| `storage.py` | `StorageSystemMixin` ABC and `SQLiteStorageSystem` (thread-safe, WAL mode, lru_cache wrapped) for the adaptive element fingerprint storage |
| `translator.py` | CSS-to-XPath translation adapted from Parsel (BSD license); used by `Selector.css()` |
| `shell.py` | `Convertor` class that converts `Response` objects to Markdown, text, or HTML for CLI extract command and MCP server |
| `ai.py` | Full MCP server definition using `FastMCP`; provides `get`, `fetch`, `stealthy_fetch`, session management tools for AI integrations |

### Engine Layer (`scrapling/engines/`)

The engine layer is split into two tiers:

**HTTP engine** (`engines/static.py`):
- `_ConfigurationLogic` (ABC): Manages session defaults (headers, proxy, timeout, impersonation, retry logic).
- `FetcherSession`: Inherits `_ConfigurationLogic`; wraps `curl_cffi.requests.Session` for sync requests.
- `AsyncFetcherClient` / `FetcherClient`: Stateless one-shot request helpers that create a session per call.

**Browser engine** (`engines/_browsers/`):
- `_base.py`: `BaseBrowserEngine` base class with shared browser setup logic.
- `_controllers.py`: `DynamicSession` / `AsyncDynamicSession` using standard Playwright.
- `_stealth.py`: `StealthySession` / `AsyncStealthySession` using Patchright with additional stealth patches.
- `_config_tools.py`: Builds Playwright `BrowserContext` and page configurations from session parameters.
- `_types.py`: `PlaywrightSession`, `StealthSession`, `RequestsSession`, `GetRequestParams`, `DataRequestParams` TypedDicts that define the full parameter surface.

**Shared toolbelt** (`engines/toolbelt/`):
- `custom.py`: `Response` (inherits `Selector`—every fetched page is immediately usable as a selector), `BaseFetcher` (class-variable-based config, `configure()` classmethod), `StatusText`.
- `convertor.py`: `ResponseFactory` normalizes raw `curl_cffi` and Playwright responses into a unified `Response` object.
- `fingerprints.py`: Uses `browserforge` + `apify-fingerprint-datapoints` to generate realistic browser headers.
- `proxy_rotation.py`: `ProxyRotator` with `cyclic_rotation` default strategy and lock-based thread safety.

### Fetcher Layer (`scrapling/fetchers/`)

Thin wrappers that expose the final public API. They:
1. Accept user keyword arguments.
2. Merge class-level parser configuration (`_generate_parser_arguments()`).
3. Instantiate the relevant session from the engine layer, using it as a context manager.
4. Return a `Response` object.

### Spider Layer (`scrapling/spiders/`)

| File | Role |
|---|---|
| `spider.py` | `Spider` ABC — defines the user extension API (`parse`, `configure_sessions`, lifecycle hooks) and runs crawl via `CrawlerEngine` through `anyio.run()` |
| `engine.py` | `CrawlerEngine` — the async crawl loop; manages `asyncio.Semaphore` for concurrency, domain-level throttling, Scheduler interaction, checkpoint saves, and item collection |
| `request.py` | `Request` — carries URL, session ID, callback, priority, meta, extra kwargs; includes SHA-1 fingerprinting for deduplication and pickle support (callbacks stored by name) |
| `session.py` | `SessionManager` — ordered dict of named sessions; supports `lazy=True` init (browser sessions opened only when first used) |
| `scheduler.py` | Priority queue (heapq) for ordering `Request` objects; tracks seen fingerprints for deduplication |
| `checkpoint.py` | Serializes/deserializes pending URLs to disk for pause/resume |
| `cache.py` | Saves `Response` bodies to disk (development mode) |
| `robotstxt.py` | Fetches and parses `robots.txt` using `protego`; per-domain LRU cache |
| `result.py` | `CrawlStats` dataclass, `ItemList` (list with `to_json`/`to_jsonl`), `CrawlResult` dataclass |

## Key Files and Their Roles

- **`scrapling/parser.py`** — The most important file. Contains `Selector` (1194 lines) and `Selectors`. All HTML interaction flows through here.
- **`scrapling/engines/toolbelt/custom.py`** — Defines `Response` (the universal return type from all fetchers) and `BaseFetcher` (configuration base for all fetcher classes).
- **`scrapling/spiders/spider.py`** — User-facing spider API; the entry point for all crawls.
- **`scrapling/core/storage.py`** — Adaptive element storage; the SQLite database enabling element relocation across website changes.
- **`scrapling/core/ai.py`** — MCP server (~828 lines); the AI integration layer.
- **`scrapling/cli.py`** — CLI (~637 lines); the `scrapling` command entry point.

## Code Organization Patterns

1. **Lazy imports everywhere**: Top-level `__init__.py` and `fetchers/__init__.py` use `__getattr__` to defer imports until first access. This is critical for keeping base install (parser only) lightweight.

2. **Class-variable configuration on fetchers**: `BaseFetcher` uses class-level variables (`adaptive`, `huge_tree`, `storage`, etc.) mutated via `configure()` classmethod, making per-fetcher global configuration easy to set once before any requests.

3. **`Response` inherits `Selector`**: Every fetched page is immediately traversable as an HTML selector without an extra parse step. This is the key design choice enabling the fluent `page.css('.x').getall()` API.

4. **`__slots__` used extensively**: `Selector`, `TextHandler`, `TextHandlers`, `AttributesHandler`, and `ProxyRotator` all use `__slots__` to reduce per-instance memory overhead.

5. **Lazy property initialization**: `Selector.tag`, `.text`, `.attrib` are cached only on first access (stored in `__slots__` with `None` sentinels), avoiding initialization overhead when not used.

6. **`lru_cache` on storage classes**: `SQLiteStorageSystem` is wrapped with `@lru_cache(1)` so that storage instances are shared across multiple `Selector` instances with the same parameters. The same pattern is used for hash computation and robots.txt.

7. **ABC + abstract methods**: `Spider.parse()` is `@abstractmethod`; `StorageSystemMixin.save()` and `.retrieve()` are abstract. Users must implement them.

8. **TypedDicts for engine parameters**: All browser and HTTP session constructor parameters are defined as TypedDicts (`PlaywrightSession`, `StealthSession`, `RequestsSession`) enabling IDE autocompletion and type checking across the codebase.
