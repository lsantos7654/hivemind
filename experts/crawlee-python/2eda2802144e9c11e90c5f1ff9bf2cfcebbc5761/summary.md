# Crawlee for Python — Summary

## Repository Purpose and Goals

Crawlee for Python (`crawlee`) is a production-ready web scraping and browser automation library developed and maintained by [Apify Technologies](https://apify.com). It is the Python port of the original TypeScript/JavaScript Crawlee library. The project's primary goals are to:

- Provide a **unified, end-to-end framework** for web crawling and scraping that abstracts away low-level details (request deduplication, retries, concurrency, storage).
- Make crawlers **appear human-like** and slip past modern bot-protection systems by default, using fingerprint generation, proxy rotation, and session management.
- Offer both **HTTP-based** (fast, lightweight) and **browser-based** (JavaScript-capable) crawling under a single consistent API.
- Support running locally and on the **Apify cloud platform** with minimal configuration changes.

Current version: **1.6.2** (commit 2eda2802144e9c11e90c5f1ff9bf2cfcebbc5761). Requires Python ≥ 3.10.

## Key Features and Capabilities

- **Multiple crawler types**: `BeautifulSoupCrawler`, `ParselCrawler`, `HttpCrawler` for HTTP-only crawling; `PlaywrightCrawler` for headless browser crawling; `AdaptivePlaywrightCrawler` that automatically chooses between HTTP and browser rendering per URL.
- **Automatic parallel crawling**: An `AutoscaledPool` adjusts concurrency based on real-time CPU and memory metrics.
- **Persistent storage**: Three built-in storage abstractions — `Dataset` (append-only tabular results), `KeyValueStore` (arbitrary key/value blobs), `RequestQueue` (URL queue with deduplication). Backends include filesystem, memory, SQLite, PostgreSQL, and Redis.
- **Proxy rotation and session management**: `ProxyConfiguration` with tiered proxy support and `SessionPool` that rotates cookies/sessions when blocked.
- **Anti-bot fingerprinting**: `FingerprintGenerator` and `HeaderGenerator` backed by `browserforge` to generate realistic browser fingerprints and headers.
- **Request routing**: `Router` dispatches requests to typed handlers based on a `label` field — similar to URL patterns in Scrapy but more explicit.
- **robots.txt compliance**: Optional `respect_robots_txt_file` mode.
- **OpenTelemetry instrumentation**: Optional `otel` extra provides a `CrawlerInstrumentor` for distributed tracing.
- **CLI scaffolding**: `crawlee create <project>` generates a project from cookiecutter templates for each crawler type.
- **Pluggable HTTP clients**: Ships with `ImpitHttpClient` (default, powered by `impit`), `HttpxHttpClient`, and `CurlImpersonateHttpClient` for TLS fingerprint impersonation.
- **State persistence**: Crawl state is persisted across interruptions so runs can resume rather than restart.
- **Full type-hint coverage**: Written with `pydantic` models and TypeVar generics throughout; targets Astral's `ty` type checker.

## Primary Use Cases and Target Audience

Crawlee targets Python developers who need to:

1. Scrape structured data from static HTML websites at scale (using `BeautifulSoupCrawler` or `ParselCrawler`).
2. Automate JavaScript-heavy SPAs or sites with complex interactions (using `PlaywrightCrawler`).
3. Intelligently mix HTTP and browser-based crawling in a single run to maximize throughput (using `AdaptivePlaywrightCrawler`).
4. Build production scrapers that handle retries, proxy rotation, rate-limiting, and bot evasion without hand-rolling all the plumbing.
5. Export collected data to machine-readable formats (JSON, CSV) or persist it to cloud storage.

The library is appropriate for individual developers, data-engineering teams, and cloud scraping workflows deployed on the Apify platform.

## High-Level Architecture Overview

```
BasicCrawler[TCrawlingContext, TStatisticsState]   ← core request lifecycle
├── AbstractHttpCrawler                            ← adds HTTP client pipeline
│   ├── HttpCrawler                                ← raw HTTP responses
│   ├── BeautifulSoupCrawler                       ← BS4-parsed HTML
│   └── ParselCrawler                              ← Parsel/XPath/CSS
└── PlaywrightCrawler                              ← headless browser
    └── AdaptivePlaywrightCrawler                  ← auto-selects HTTP vs browser
```

**Context Pipeline (Middleware)**: Each crawler type progressively enriches a `CrawlingContext` object as the request moves through the pipeline — from `BasicCrawlingContext` (URL, session, helpers) to `HttpCrawlingContext` (raw response) to `BeautifulSoupCrawlingContext` (parsed `soup`). Middlewares are async generators that wrap the next stage.

**Service Locator**: A global `ServiceLocator` singleton (`service_locator`) owns `Configuration`, `EventManager`, `StorageClient`, and `StorageInstanceManager`. Components obtain shared services through it. Double-initialization raises `ServiceConflictError`.

**Autoscaling**: `AutoscaledPool` monitors CPU/memory via a `Snapshotter` and `SystemStatus`, adjusting the number of concurrently running request handlers.

**Storage Layer**: High-level `Dataset`, `KeyValueStore`, and `RequestQueue` classes delegate to pluggable `StorageClient` implementations. A `StorageInstanceManager` caches instances by name/ID.

**Event System**: `EventManager` (and `LocalEventManager`) manages lifecycle events (persist-state, crawlee-status, abort) via `pyee`-backed event emitters.

## Related Projects and Dependencies

- **Crawlee for JS/TS**: The original TypeScript implementation at `github.com/apify/crawlee`.
- **Apify SDK for Python**: Cloud deployment layer built on top of Crawlee.
- **Playwright** (`playwright>=1.27.0`): Browser automation backend.
- **impit** (`impit>=0.8.0`): Default HTTP client providing TLS fingerprint impersonation.
- **httpx** (`httpx>=0.27.0`, optional): Alternative async HTTP client.
- **curl-cffi** (`curl-cffi>=0.9.0`, optional): cURL-based TLS impersonation HTTP client.
- **beautifulsoup4** + **lxml** / **html5lib** (optional): HTML parsing.
- **parsel** (optional): XPath/CSS selector parsing (same library Scrapy uses).
- **browserforge** + **apify_fingerprint_datapoints** (optional): Realistic browser fingerprint data.
- **scikit-learn** + **jaro-winkler** (optional): ML-based rendering-type prediction in `AdaptivePlaywrightCrawler`.
- **SQLAlchemy** + **aiosqlite** / **asyncpg** (optional): SQL storage backends.
- **redis** (optional): Redis storage backend.
- **opentelemetry-*** (optional): Distributed tracing instrumentation.
- **pydantic** / **pydantic-settings**: Data modelling and environment-based configuration.
- **tldextract**, **yarl**, **protego**: URL parsing and robots.txt handling.
