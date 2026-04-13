# Crawlee for Python — Code Structure

## Top-Level Repository Layout

```
crawlee-python/
├── src/crawlee/            # Main package source (sole package in the repo)
├── tests/
│   ├── unit/               # Unit tests (pytest-asyncio, pytest-xdist)
│   └── e2e/                # End-to-end tests (require Apify platform credentials)
├── docs/                   # Documentation code examples and guides
│   ├── examples/           # Example scripts linked from the website
│   ├── guides/             # Guide-level docs with runnable code
│   ├── introduction/       # Introductory tutorial code
│   └── quick-start/        # Quick-start code examples
├── website/                # Docusaurus-based documentation website
├── pyproject.toml          # Build system, dependencies, tooling config
├── uv.lock                 # Locked dependency resolution (uv)
├── AGENTS.md               # Coding guidelines for programming agents
├── CLAUDE.md               # Notes for Claude AI coding assistant
├── CONTRIBUTING.md         # Contributor guidelines
├── CHANGELOG.md            # Version history
└── renovate.json           # Dependency update automation config
```

## Package Root: `src/crawlee/`

```
src/crawlee/
├── __init__.py             # Public top-level exports: Request, service_locator, HttpHeaders, etc.
├── _autoscaling/           # AutoscaledPool, Snapshotter, SystemStatus
├── _cli.py                 # CLI entry point (`crawlee create`)
├── _consts.py              # Package-level constants
├── _log_config.py          # Logging configuration helpers
├── _request.py             # Request model, RequestState enum, CrawleeRequestData, UserData
├── _service_locator.py     # ServiceLocator singleton
├── _types.py               # Shared types: BasicCrawlingContext, HttpHeaders, enums, protocols
├── _utils/                 # Internal utilities (crypto, file I/O, URL helpers, robots.txt, etc.)
├── browsers/               # BrowserPool and Playwright browser management
├── configuration.py        # Configuration (pydantic-settings BaseSettings)
├── crawlers/               # All crawler implementations
├── errors.py               # Public exception hierarchy
├── events/                 # EventManager, LocalEventManager, event type definitions
├── fingerprint_suite/      # Browser fingerprint and header generation
├── http_clients/           # Pluggable HTTP client implementations
├── otel/                   # OpenTelemetry instrumentation
├── project_template/       # Cookiecutter template for `crawlee create`
├── proxy_configuration.py  # ProxyConfiguration, ProxyInfo
├── request_loaders/        # RequestList, RequestLoader, RequestManager, SitemapRequestLoader
├── router.py               # Router (label-based request dispatch)
├── sessions/               # SessionPool, Session, cookie management
├── statistics/             # Statistics tracking, error snapshotter, error tracker
├── storage_clients/        # StorageClient backends (filesystem, memory, SQL, Redis)
└── storages/               # High-level Dataset, KeyValueStore, RequestQueue
```

## Key Subdirectories

### `crawlers/` — All Crawler Implementations

```
crawlers/
├── __init__.py             # Re-exports all public crawler/context types; lazy optional imports
├── _types.py               # Shared crawler type aliases
├── _basic/                 # BasicCrawler core
│   ├── _basic_crawler.py   # BasicCrawler class (1699 lines) — central request lifecycle
│   ├── _basic_crawling_context.py  # Re-exports BasicCrawlingContext from _types
│   ├── _context_pipeline.py        # ContextPipeline middleware chain
│   ├── _context_utils.py           # swapped_context helper
│   └── _logging_utils.py           # Error summarization helpers
├── _abstract_http/         # AbstractHttpCrawler (HTTP + parsing layer)
│   ├── _abstract_http_crawler.py   # Adds HTTP client, response parsing hooks
│   └── _abstract_http_parser.py    # AbstractHttpParser protocol
├── _http/                  # HttpCrawler (raw HTTP, no parsing)
│   └── _http_crawler.py
├── _beautifulsoup/         # BeautifulSoupCrawler
│   ├── _beautifulsoup_crawler.py
│   ├── _beautifulsoup_crawling_context.py
│   ├── _beautifulsoup_parser.py    # Wraps BS4
│   └── _utils.py
├── _parsel/                # ParselCrawler (XPath/CSS via parsel)
│   ├── _parsel_crawler.py
│   ├── _parsel_crawling_context.py
│   ├── _parsel_parser.py
│   └── _utils.py
├── _playwright/            # PlaywrightCrawler
│   ├── _playwright_crawler.py        # Extends BasicCrawler; manages BrowserPool
│   ├── _playwright_crawling_context.py
│   ├── _playwright_http_client.py    # Playwright-backed HttpClient implementation
│   ├── _playwright_post_nav_crawling_context.py
│   ├── _playwright_pre_nav_crawling_context.py
│   ├── _types.py                     # GotoOptions, etc.
│   └── _utils.py                     # block_requests, infinite_scroll helpers
└── _adaptive_playwright/   # AdaptivePlaywrightCrawler
    ├── _adaptive_playwright_crawler.py        # Extends PlaywrightCrawler with ML predictor
    ├── _adaptive_playwright_crawler_statistics.py
    ├── _adaptive_playwright_crawling_context.py
    ├── _rendering_type_predictor.py           # ML model for HTTP vs browser decision
    ├── _result_comparator.py                  # Compares HTTP and browser results
    └── _utils.py
```

**`BasicCrawler`** (`src/crawlee/crawlers/_basic/_basic_crawler.py`) is the central class. It owns the entire request lifecycle: dequeuing from `RequestManager`, running the `ContextPipeline`, dispatching to `Router` handlers, retrying on errors, rotating sessions, persisting state, and updating `Statistics`.

### `storages/` — High-Level Storage API

```
storages/
├── _base.py                # Storage abstract base class with open() factory pattern
├── _dataset.py             # Dataset: append-only tabular storage
├── _key_value_store.py     # KeyValueStore: arbitrary blob storage by key
├── _request_queue.py       # RequestQueue: URL queue with deduplication
├── _storage_instance_manager.py  # StorageInstanceManager: caches open instances
└── _utils.py               # validate_storage_name helper
```

All storage classes follow the same pattern: `await StorageClass.open(name='...')` returns a cached instance managed by `StorageInstanceManager`. The actual I/O is delegated to a `StorageClient` backend.

### `storage_clients/` — Storage Backends

```
storage_clients/
├── _base/                  # Abstract StorageClient, DatasetClient, KVSClient, RQClient
├── _file_system/           # FileSystemStorageClient — default, writes to ./storage/
├── _memory/                # MemoryStorageClient — in-process, no disk I/O
├── _sql/                   # SqlStorageClient — SQLAlchemy async (SQLite or PostgreSQL)
├── _redis/                 # RedisStorageClient — Redis backend
└── models.py               # Pydantic models shared across backends
```

### `http_clients/` — HTTP Client Backends

```
http_clients/
├── _base.py                # HttpClient ABC, HttpResponse Protocol, HttpCrawlingResult
├── _impit.py               # ImpitHttpClient (default; TLS fingerprint impersonation)
├── _httpx.py               # HttpxHttpClient (httpx-based; optional)
└── _curl_impersonate.py    # CurlImpersonateHttpClient (curl-cffi; optional)
```

Each HTTP client implements two key methods:
- `crawl(request, session, proxy_info, statistics)` — used internally by crawler pipeline.
- `send_request(url, ...)` — used by handlers via `context.send_request()`.

### `browsers/` — Browser Pool Management

```
browsers/
├── _browser_pool.py              # BrowserPool: manages multiple browser instances
├── _browser_controller.py        # BrowserController ABC
├── _playwright_browser_controller.py  # Playwright implementation
├── _browser_plugin.py            # BrowserPlugin ABC
├── _playwright_browser_plugin.py # Launches Playwright instances with fingerprinting
└── _playwright_browser.py        # Wraps a Playwright Browser instance
```

`BrowserPool` is used by `PlaywrightCrawler`. It multiplexes page creation across N browser instances, enabling parallel page processing without excessive memory use.

### `sessions/` — Session Management

```
sessions/
├── _session_pool.py     # SessionPool: manages rotating session objects
├── _session.py          # Session: cookies, headers, error/retire counters
├── _cookies.py          # Cookie helpers and Playwright cookie type adapters
└── _models.py           # Pydantic session models
```

`SessionPool` allocates and rotates `Session` objects on each request. A session tracks how many errors/blocks it has encountered and retires itself when thresholds are exceeded. Sessions are persisted to `KeyValueStore` for cross-run continuity.

### `_autoscaling/` — Concurrency Control

```
_autoscaling/
├── autoscaled_pool.py   # AutoscaledPool: runs tasks with dynamic concurrency
├── snapshotter.py       # Snapshotter: samples CPU/memory/event-loop metrics
└── system_status.py     # SystemStatus: translates snapshots to overload signals
```

`AutoscaledPool` is driven by `ConcurrencySettings` (min/max/desired concurrency, max tasks per minute). It polls `SystemStatus` periodically and scales concurrency up or down.

### `fingerprint_suite/` — Anti-Bot Fingerprinting

```
fingerprint_suite/
├── _fingerprint_generator.py   # FingerprintGenerator (and DefaultFingerprintGenerator)
├── _header_generator.py        # HeaderGenerator for consistent HTTP headers
├── _browserforge_adapter.py    # Adapter for browserforge data
├── _consts.py                  # Constants (browser/OS lists, etc.)
└── _types.py                   # Type aliases for fingerprint options
```

### `request_loaders/` — Request Sources

```
request_loaders/
├── _request_loader.py          # RequestLoader ABC
├── _request_manager.py         # RequestManager ABC (extends RequestLoader with add/reclaim)
├── _request_list.py            # RequestList: static in-memory list
├── _request_manager_tandem.py  # RequestManagerTandem: combines list + queue
└── _sitemap_request_loader.py  # SitemapRequestLoader: parses XML sitemaps
```

`RequestQueue` inherits from both `Storage` and `RequestManager`. The crawler accepts any `RequestManager` as input.

### `events/` — Event System

```
events/
├── _event_manager.py        # EventManager ABC
├── _local_event_manager.py  # LocalEventManager: schedules persist-state events
└── _types.py                # Event type literals and event data models
```

### `statistics/` — Metrics and Error Tracking

```
statistics/
├── _statistics.py           # Statistics class: tracks requests/errors/timing
├── _error_snapshotter.py    # Captures and saves error snapshots to KVS
├── _error_tracker.py        # ErrorTracker: groups and summarizes errors
└── _models.py               # StatisticsState pydantic model
```

### `_types.py` — Central Type Definitions

`src/crawlee/_types.py` (824 lines) defines the critical `BasicCrawlingContext` dataclass and all related protocol types:
- `BasicCrawlingContext` — contains `request`, `session`, `proxy_info`, `send_request`, `push_data`, `add_requests`, `enqueue_links`, `get_key_value_store`, `use_state`, `log`, `crawler`.
- `HttpHeaders` — immutable, case-insensitive header mapping (Pydantic `RootModel`).
- `ConcurrencySettings`, `EnqueueLinksKwargs`, `PushDataKwargs`, `AddRequestsKwargs`.
- `EnqueueLinksFunction`, `AddRequestsFunction`, `ExtractLinksFunction` protocols.
- `RequestHandlerRunResult` — used in `AdaptivePlaywrightCrawler` to track handler side effects.

## Test Layout

```
tests/
├── unit/
│   ├── _autoscaling/         # AutoscaledPool tests
│   ├── _statistics/          # Statistics tests
│   ├── _utils/               # Utility function tests
│   ├── browsers/             # BrowserPool tests
│   ├── crawlers/             # Per-crawler unit tests
│   ├── events/               # Event system tests
│   ├── fingerprint_suite/    # Fingerprint generation tests
│   ├── http_clients/         # HTTP client mock tests
│   ├── otel/                 # OTel instrumentation tests
│   ├── proxy_configuration/  # ProxyConfiguration tests
│   ├── request_loaders/      # RequestList/RequestQueue tests
│   ├── sessions/             # Session and SessionPool tests
│   ├── storage_clients/      # Per-backend storage tests
│   ├── storages/             # Dataset/KVS/RQ integration tests
│   ├── conftest.py           # Shared fixtures
│   ├── server.py             # Local test HTTP server (uvicorn)
│   └── utils.py              # Test utilities
└── e2e/
    └── project_template/     # Tests that build and run the CLI project template
```

## Code Organization Patterns

1. **Private-by-convention naming**: All implementation modules use `_` prefix (e.g., `_basic_crawler.py`). Public symbols are re-exported from `__init__.py`.
2. **`@docs_group` decorator**: Tags classes and functions into documentation groups (`'Crawlers'`, `'Storages'`, `'Configuration'`, `'Errors'`, etc.) for the API reference website.
3. **Lazy optional imports via `try_import`**: Classes backed by optional extras (beautifulsoup, playwright, redis, etc.) are wrapped in `with _try_import(...)` so missing extras raise helpful `ImportError` messages only when the class is actually used.
4. **Generic crawlers**: `BasicCrawler[TCrawlingContext, TStatisticsState]` uses bounded TypeVars so subclasses can refine both the context type and statistics state.
5. **Async-first**: All I/O paths are `async`/`await`. The `asyncio_mode = 'auto'` pytest setting means no `@pytest.mark.asyncio` decorators are needed.
6. **Pydantic models everywhere**: `Request`, `Configuration`, `CrawleeRequestData`, `UserData`, `Session`, `StorageClient` models are all Pydantic v2 `BaseModel` or `BaseSettings` subclasses.
