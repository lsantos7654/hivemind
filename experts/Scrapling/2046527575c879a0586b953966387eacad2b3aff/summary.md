# Scrapling — Repository Summary

## Repository Purpose and Goals

Scrapling (version 0.4.5) is an adaptive web scraping framework for Python authored by Karim Shoair. Its stated mission is to make web scraping "effortless" across the full spectrum of use-cases—from a single HTTP request to a full-scale concurrent crawl—while simultaneously solving the two hardest recurring problems in web scraping:

1. **Anti-bot detection bypass**: Built-in support for impersonating browser TLS fingerprints, browser automation with fingerprint spoofing, and Cloudflare Turnstile/Interstitial solving.
2. **CSS/XPath selector fragility**: An "adaptive" engine that saves element fingerprints to a local SQLite database and can automatically relocate them after a website's HTML structure changes.

The project targets Python ≥ 3.10 and is published on PyPI as `scrapling` under the BSD-3-Clause license.

## Key Features and Capabilities

### Fetching Layer
- **`Fetcher` / `AsyncFetcher`**: Thin wrappers around `curl_cffi` that impersonate real browser TLS fingerprints and HTTP/3. Supports GET, POST, PUT, DELETE with per-request and per-session proxy configuration.
- **`FetcherSession`**: A persistent session class (sync + async context manager) that reuses connections, cookies, and TLS state across requests.
- **`DynamicFetcher` / `DynamicSession` / `AsyncDynamicSession`**: Full browser automation via Playwright (Chromium). Supports custom JavaScript, `page_action` callbacks, XHR capture, `network_idle` wait, resource blocking, CDP connection, and per-request timeouts.
- **`StealthyFetcher` / `StealthySession` / `AsyncStealthySession`**: Stealth-mode browser automation built on Patchright (a patched Playwright fork). Adds fingerprint randomization, canvas noise injection, WebRTC leak prevention, WebGL spoofing, and automatic Cloudflare challenge solving (`solve_cloudflare=True`).
- **`ProxyRotator`**: Thread-safe, pluggable proxy rotation supporting cyclic (default) or custom rotation strategies, both string URLs and Playwright-style dict proxies.

### Parsing Layer
- **`Selector`**: The central HTML-parsing class wrapping lxml. Supports CSS3 and XPath selectors (with full Scrapy pseudo-elements: `::text`, `::attr`), BeautifulSoup-style `find_all`/`find`, text search (`find_by_text`), regex search (`find_by_regex`), and DOM traversal (`parent`, `children`, `siblings`, `next`, `previous`, `path`, `iterancestors`).
- **`Selectors`**: A `list` subclass that propagates all `Selector` methods across collections, enabling chained queries.
- **`TextHandler`**: A `str` subclass adding `.re()`, `.re_first()`, `.json()`, `.clean()`, and other utilities. All text extraction returns `TextHandler` instances.
- **`AttributesHandler`**: A read-only `Mapping` backed by `MappingProxyType` for element attributes, with `.search_values()` and `.json_string` helpers.
- **Adaptive engine**: `Selector.css()` and `.xpath()` accept `auto_save=True` and `adaptive=True` flags. When `auto_save=True`, element metadata is stored in `elements_storage.db`. When `adaptive=True` on a subsequent run, the engine retrieves saved data and uses a multi-factor similarity algorithm (tag, text, attributes, path, parent, siblings) to relocate the element even after structural page changes.
- **Selector generation**: `generate_css_selector`, `generate_full_css_selector`, `generate_xpath_selector` properties auto-generate selectors for any element.
- **`find_similar()`**: Finds structurally similar elements (same tree depth, tag, parent chain) using attribute similarity scoring—inspired by AutoScraper but engine-agnostic.

### Spider Framework
- **`Spider`** (abstract base class): Scrapy-like API (`start_urls`, async `parse` callback, `Request`/`Response`). Configurable concurrency, per-domain throttling, download delays, and blocked-request detection/retry.
- **`SessionManager`**: Unified session registry for mixing `FetcherSession`, `StealthySession`, and `DynamicSession` in a single spider with request routing by session ID (`sid`).
- **Pause/Resume**: Checkpoint-based persistence via `crawldir` parameter; press Ctrl+C for graceful shutdown with automatic state saving, resume by re-running with the same directory.
- **Streaming mode**: `spider.stream()` yields items as an async generator for real-time consumption.
- **Development mode**: Caches responses to disk on first run, replays them on subsequent runs.
- **Robots.txt compliance**: Optional `robots_txt_obey` flag with per-domain caching.
- **Export**: `result.items.to_json()` and `result.items.to_jsonl()` using `orjson`.

### CLI and Shell
- `scrapling shell`: Interactive IPython shell with pre-loaded Scrapling integration, curl-to-Scrapling conversion, and in-browser preview.
- `scrapling extract get|fetch|stealthy-fetch <url> <output>`: Zero-code extraction to `.txt`, `.md`, or `.html` files with optional CSS selector targeting.
- `scrapling install [--force]`: Downloads browser binaries for fetcher/browser dependencies.

### MCP Server
- `scrapling[ai]` extra installs an MCP (Model Context Protocol) server (`scrapling.core.ai`) for use with AI tools (Claude, Cursor, etc.). The server exposes browser and HTTP fetch tools with content pre-extracted before returning to the AI, reducing token usage.

## Primary Use Cases and Target Audience

- Web scrapers and data engineers needing to extract data from anti-bot-protected sites.
- Developers who want Scrapy-like spider architecture without Scrapy's complexity.
- AI/LLM application developers integrating live web data via the MCP server.
- Teams building production crawlers that need pause/resume, proxy rotation, and multi-session support.

## High-Level Architecture Overview

```
scrapling/
├── parser.py          # Selector / Selectors — the HTML parsing core
├── fetchers/          # High-level fetcher classes (thin wrappers over engines)
├── engines/           # Low-level HTTP and browser engine implementations
│   ├── static.py      # curl_cffi-based HTTP session engine
│   ├── _browsers/     # Playwright/Patchright browser engine
│   └── toolbelt/      # Shared utilities: Response, BaseFetcher, ProxyRotator, fingerprints
├── spiders/           # Spider framework: Spider, Request, CrawlerEngine, SessionManager
├── core/              # Shared types, custom_types, storage, mixins, shell utilities, MCP AI
└── cli.py             # Click-based CLI
```

Data always flows `Fetcher → Response (subclass of Selector) → Selectors/TextHandler`.

## Related Projects and Dependencies

| Dependency | Role |
|---|---|
| `lxml` ≥ 6.0.2 | HTML parsing backend |
| `cssselect` ≥ 1.4.0 | CSS-to-XPath translation (adapted from Parsel) |
| `orjson` ≥ 3.11.8 | Fast JSON serialization |
| `tld` ≥ 0.13.2 | TLD extraction for adaptive storage scoping |
| `w3lib` ≥ 2.4.1 | URL/HTML utilities |
| `curl_cffi` ≥ 0.15.0 | TLS-fingerprint-impersonating HTTP client (fetchers extra) |
| `playwright` 1.58.0 | Browser automation for `DynamicFetcher` (fetchers extra) |
| `patchright` 1.58.2 | Patched Playwright for stealth mode (fetchers extra) |
| `browserforge` ≥ 1.2.4 | Browser fingerprint generation (fetchers extra) |
| `anyio` ≥ 4.12.1 | Async I/O abstraction for spider engine (fetchers extra) |
| `protego` ≥ 0.6.0 | Robots.txt parsing (fetchers extra) |
| `mcp` ≥ 1.26.0 | MCP server (ai extra) |
| `markdownify` ≥ 1.2.0 | HTML-to-Markdown (ai/shell extra) |
| `IPython` ≥ 8.37 | Interactive shell (shell extra) |
| `msgspec` ≥ 0.20.0 | Serialization for spider engine (fetchers extra) |
