# Hivemind Crawl Module

Documentation crawler for `hivemind expert crawl <url> <agent>`. Probes
the site, picks discovery + extraction strategies, writes markdown to
`~/.cache/hivemind/external_docs/<agent>/`.

## Pipeline

```
probe_site(url)                   → SiteProfile
  ↓
[open browser session if needed]  → AsyncWebCrawler | None
  ↓
discover_urls(url, profile, ...)  → list[str]
  ↓
for each url (concurrent):
  extract_page(url, profile, ...) → markdown str
  ↓
write to <output_dir>/<slug>.md
```

Two orthogonal strategy axes — **discovery** and **extraction** — each
with three implementations. Both are picked from the `SiteProfile`. No
flags, no per-site config, no global state.

## Files

| File | Role |
|---|---|
| `__init__.py` | Public surface: `crawl_website`, `probe_site`, `SiteProfile`, `LeafProgress`, `BrowserUnavailableError`, `CrawlResult` |
| `probe.py` | Site classifier — fetches seed once, returns `SiteProfile` |
| `discovery.py` | URL discovery (sitemap / spider / browser-BFS), shared `_in_scope` filter |
| `browser.py` | Thin wrapper over `crawl4ai.AsyncWebCrawler`, raises `BrowserUnavailableError` if Chromium missing |
| `extractor.py` | Orchestrates pipeline, dispatches per-URL extraction, runs concurrent fetches |
| `urls.py` | Pure utilities: `normalize_url`, `deduplicate_urls`, `url_to_filename`, `CrawlResult` |
| `CRAWL.md` | This file |

## SiteProfile (`probe.py`)

```python
@dataclass(frozen=True)
class SiteProfile:
    seed_url: str
    seed_reachable: bool
    static_extraction_works: bool   # trafilatura on static HTML > 200 chars
    static_discovery_works: bool    # ≥ 3 in-scope <a> tags in static HTML
    sitemap_status: Literal["usable", "unusable", "missing"]
    has_md_source: bool             # /seed.md or /seed/index.md served as markdown
    detected_domain: str
```

Two derived dispatch keys:

```python
profile.discovery_strategy   →  "sitemap" | "spider" | "browser"
profile.extraction_strategy  →  "md" | "http" | "browser"
```

Probe runs **every crawl** (~3-4 cheap HTTP requests, no browser, < 2 s).

## Discovery channels (`discovery.py`)

| Strategy | When | How |
|---|---|---|
| **`sitemap`** | `sitemap_status == "usable"` | Streams `/sitemap.xml`, parses `<loc>` with `XMLPullParser`. Multi-leaf sitemaps stream concurrently (cap **3**). Memory stays flat — handles bazel.build's 64 MB leaves. |
| **`spider`** | static nav exists, no usable sitemap | `trafilatura.spider.focused_crawler` from seed via `asyncio.to_thread` |
| **`browser`** | JS-rendered nav, no usable sitemap | `crawl4ai.BFSDeepCrawlStrategy` (depth 2) over Playwright; FilterChain restricts to in-scope URLs |

Seed URL is **always** included in the result, so single-page crawls
always succeed regardless of sitemap state.

All channels feed through `_in_scope(url, netloc, base_path)` — same
filter rules everywhere (domain, path scope, language variants like
`/zh/` paths and `?hl=ko` query params).

### Sitemap streaming details

- Index file (small) loaded fully → enumerate leaf URLs
- Each leaf streamed via `httpx.stream("GET", ...)` + `XMLPullParser(["end"])`
- `<loc>` text drained and `elem.clear()`'d immediately after each
  emit — memory is flat regardless of leaf size
- `LeafProgress` dataclass updated in-place per chunk; CLI subscribes
  via `on_leaf_progress` callback to render a live trace
- **No site-specific bailout** — every leaf streams to completion.
  User can `Ctrl+C` if the live trace shows nothing useful is happening.

## Extraction channels (`extractor.py`)

| Strategy | When | How | Concurrency |
|---|---|---|---|
| **`md`** | `has_md_source` | GET `<url>.md` or `<url>/index.md` | 10 (httpx) |
| **`http`** | static HTML works | GET + `trafilatura.extract` | 10 (httpx) |
| **`browser`** | JS-only page | `crawl4ai.AsyncWebCrawler.arun()` → markdown | 3 (Chromium tabs) |

`extract_page` falls through gracefully — e.g. if `.md` 404s for a
specific URL, retries via `http`. The browser session (when needed) is
opened once per crawl and shared across all extraction tasks.

## Caps & timeouts

| Constant | Value | Where |
|---|---|---|
| `--max-pages` | unlimited | CLI flag, user-controlled |
| `_DISCOVERY_DEFAULT_CAP` | 500 | `discovery.py` — applied when `--max-pages` is not set |
| `_SITEMAP_LEAF_CONCURRENCY` | 3 | `discovery.py` — parallel sitemap leaf streams |
| `_SITEMAP_STREAM_TIMEOUT` | 120 s | `discovery.py` — per-leaf hard ceiling |
| `_HTTP_CONCURRENCY` | 10 | `extractor.py` — concurrent httpx fetches |
| `_BROWSER_CONCURRENCY` | 3 | `extractor.py` — concurrent Chromium tabs |
| `_BFS_MAX_DEPTH` | 2 | `browser.py` — browser BFS depth from seed |
| `_PROBE_TIMEOUT` | 10 s | `probe.py` |
| `_MIN_STATIC_EXTRACTION_CHARS` | 200 | `probe.py` — trafilatura output length to trust static HTML |
| `_MIN_STATIC_DISCOVERY_ANCHORS` | 3 | `probe.py` — in-scope `<a>` count to trust static spider |
| `_SITEMAP_LEAF_MAX_BYTES` | 200 MB | `probe.py` — pathological-sitemap protection |

## Observability

`crawl_website` accepts three callbacks:

```python
on_phase_callback(phase: str, info: dict[str, object])
    # phases: "probe", "discover", "extract_start", "done"

on_leaf_progress(leaf: LeafProgress)
    # called per chunk during sitemap streaming;
    # leaf.status: "queued" | "streaming" | "done" | "failed"
    # leaf.bytes_read, leaf.in_scope_hits update in place

on_page_callback(url: str, success: bool)
    # called per URL after extraction
```

CLI (`cli.py:crawl`) subscribes to all three and renders a Rich `Live`
block showing probe results, per-leaf streaming progress, and an
extraction progress bar with the last 5 completed paths.

## Errors

- `BrowserUnavailableError` — Chromium not installed. Raised by
  `browser_session()` context manager, caught by the CLI which prints
  the `playwright install chromium` hint.
- Per-page extraction failures are logged and counted; one bad URL
  doesn't kill the crawl.
- Per-leaf streaming failures (`httpx.HTTPError`, etc.) are logged and
  counted; one bad leaf doesn't kill discovery.

## Adding a new strategy

To add a new discovery channel (e.g. RSS, OPML):

1. Add a probe field to `SiteProfile` if a new capability needs detecting.
2. Add a new `Literal` value to `discovery_strategy`.
3. Implement `_<name>_discover(...) -> list[str]` in `discovery.py`.
4. Add a branch in `discover_urls`.
5. The `_in_scope` filter still applies — no scope-handling code needed.

Same shape for extraction channels in `extractor.py`.

## Verification

End-to-end via CLI on real sites (no unit tests for the crawler module):

```bash
# Sitemap path on a static docs site
bazelisk run //src/hivemind:hivemind -- expert crawl https://trafilatura.readthedocs.io/en/latest/ trafilatura --max-pages 5

# Sitemap path on a hostile devsite (multi-leaf, multi-MB)
bazelisk run //src/hivemind:hivemind -- expert crawl https://bazel.build/extending bazel --max-pages 15

# Spider path (no sitemap, static nav)
bazelisk run //src/hivemind:hivemind -- expert crawl https://example.com/docs/ example --max-pages 10

# Browser path (JS-rendered nav, no sitemap)
bazelisk run //src/hivemind:hivemind -- expert crawl https://cloud.google.com/storage/docs cloud --max-pages 5
```

Static checks:

```bash
ruff check src/hivemind/crawl/
mypy src/hivemind/crawl/
bazelisk test //...
```
