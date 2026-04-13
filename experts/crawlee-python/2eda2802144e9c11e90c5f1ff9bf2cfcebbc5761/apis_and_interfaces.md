# Crawlee for Python — APIs and Interfaces

## Public Entry Points

The `crawlee` package exposes these symbols from its top-level `__init__.py`:

```python
from crawlee import (
    Request,          # The core request model
    RequestOptions,   # TypedDict for constructing Request objects
    RequestState,     # IntEnum: UNPROCESSED, BEFORE_NAV, AFTER_NAV, REQUEST_HANDLER, DONE, ERROR_HANDLER, ERROR, SKIPPED
    service_locator,  # Global ServiceLocator instance
    HttpHeaders,      # Immutable, case-insensitive HTTP header mapping
    ConcurrencySettings,      # Autoscaling concurrency limits
    EnqueueStrategy,  # Literal: 'all' | 'same-domain' | 'same-hostname' | 'same-origin'
    Glob,             # URL glob pattern helper for include/exclude filters
    RequestTransformAction,   # Literal: 'skip' | 'unchanged'
    SkippedReason,    # Literal: 'robots_txt'
)
```

## Crawler Classes

All crawlers live in `crawlee.crawlers`. Import patterns:

```python
from crawlee.crawlers import (
    BasicCrawler, BasicCrawlerOptions, BasicCrawlingContext, ContextPipeline,
    HttpCrawler, HttpCrawlingContext, HttpCrawlingResult,
    BeautifulSoupCrawler, BeautifulSoupCrawlingContext,
    ParselCrawler, ParselCrawlingContext,
    PlaywrightCrawler, PlaywrightCrawlingContext,
    PlaywrightPreNavCrawlingContext, PlaywrightPostNavCrawlingContext,
    AdaptivePlaywrightCrawler, AdaptivePlaywrightCrawlingContext,
    AbstractHttpCrawler, AbstractHttpParser, HttpCrawlerOptions, ParsedHttpCrawlingContext,
)
```

### `BasicCrawler`
**File**: `src/crawlee/crawlers/_basic/_basic_crawler.py:247`

The foundational crawler. All others extend it.

```python
from crawlee.crawlers import BasicCrawler, BasicCrawlingContext

class MyCrawler(BasicCrawler[BasicCrawlingContext]):
    pass

crawler = BasicCrawler(
    request_handler=my_handler,
    max_request_retries=3,
    max_requests_per_crawl=100,
    max_session_rotations=10,
    max_crawl_depth=3,
    concurrency_settings=ConcurrencySettings(min_concurrency=1, max_concurrency=50),
    request_handler_timeout=timedelta(minutes=2),
    retry_on_blocked=True,
    use_session_pool=True,
    proxy_configuration=ProxyConfiguration(proxy_urls=['http://proxy:8080']),
    http_client=ImpitHttpClient(),
    abort_on_error=False,
    keep_alive=False,
    respect_robots_txt_file=False,
)

await crawler.run(['https://example.com'])
```

Key constructor parameters (all `NotRequired`):
- `request_handler` — async callable receiving the crawling context
- `max_request_retries` (default `3`)
- `max_requests_per_crawl` (default `None` = unlimited)
- `max_session_rotations` (default `10`)
- `max_crawl_depth` (default `None`)
- `concurrency_settings` — `ConcurrencySettings` object
- `request_handler_timeout` (default `timedelta(minutes=1)`)
- `retry_on_blocked` (default `True`)
- `use_session_pool` (default `True`)
- `proxy_configuration` — `ProxyConfiguration` instance
- `http_client` — any `HttpClient` subclass
- `storage_client` — any `StorageClient` subclass
- `respect_robots_txt_file` (default `False`)
- `abort_on_error` (default `False`)
- `keep_alive` (default `False`)
- `statistics_log_format` — `'table'` or `'inline'`

Key methods:
- `await crawler.run(requests: list[str | Request] | None)` — start crawling
- `await crawler.run_one(request: str | Request)` — run a single request
- `crawler.router` — the `Router` instance for handler registration

### `BeautifulSoupCrawler`
**File**: `src/crawlee/crawlers/_beautifulsoup/_beautifulsoup_crawler.py:22`

HTTP crawler with automatic BeautifulSoup parsing. Requires `crawlee[beautifulsoup]`.

```python
from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext

crawler = BeautifulSoupCrawler(
    parser='lxml',   # or 'html.parser', 'html5lib', 'lxml-xml'
    max_requests_per_crawl=50,
)

@crawler.router.default_handler
async def handler(context: BeautifulSoupCrawlingContext) -> None:
    soup = context.soup          # bs4.BeautifulSoup object
    title = soup.title.string
    await context.push_data({'url': context.request.url, 'title': title})
    await context.enqueue_links()

await crawler.run(['https://example.com'])
```

Additional context attribute: `context.soup` — the parsed `BeautifulSoup` object.

### `ParselCrawler`
**File**: `src/crawlee/crawlers/_parsel/_parsel_crawler.py`

HTTP crawler with Parsel (XPath/CSS) parsing. Requires `crawlee[parsel]`.

```python
from crawlee.crawlers import ParselCrawler, ParselCrawlingContext

crawler = ParselCrawler()

@crawler.router.default_handler
async def handler(context: ParselCrawlingContext) -> None:
    selector = context.selector   # parsel.Selector object
    title = selector.css('title::text').get()
    links = selector.xpath('//a/@href').getall()
```

### `HttpCrawler`
**File**: `src/crawlee/crawlers/_http/_http_crawler.py`

Raw HTTP crawler without automatic parsing. Provides the raw HTTP response.

```python
from crawlee.crawlers import HttpCrawler, HttpCrawlingContext

crawler = HttpCrawler()

@crawler.router.default_handler
async def handler(context: HttpCrawlingContext) -> None:
    body = await context.http_response.read()
    # context.http_response: HttpResponse protocol
```

### `PlaywrightCrawler`
**File**: `src/crawlee/crawlers/_playwright/_playwright_crawler.py:61`

Headless browser crawler. Requires `crawlee[playwright]` and `playwright install`.

```python
from crawlee.crawlers import PlaywrightCrawler, PlaywrightCrawlingContext

crawler = PlaywrightCrawler(
    browser_type='chromium',        # 'chromium', 'firefox', 'webkit'
    headless=True,
    browser_options={'args': ['--no-sandbox']},
    page_options={'viewport': {'width': 1280, 'height': 720}},
    max_requests_per_crawl=20,
)

@crawler.router.default_handler
async def handler(context: PlaywrightCrawlingContext) -> None:
    page = context.page             # playwright.async_api.Page
    title = await page.title()
    await context.enqueue_links()
    await context.push_data({'url': context.request.url, 'title': title})

await crawler.run(['https://example.com'])
```

Pre/post navigation hooks:

```python
@crawler.pre_navigation_hook
async def pre_nav(context: PlaywrightPreNavCrawlingContext) -> None:
    # context.page available before navigation
    await context.page.route('**/*.{png,jpg}', lambda route: route.abort())

@crawler.post_navigation_hook
async def post_nav(context: PlaywrightPostNavCrawlingContext) -> None:
    await context.page.wait_for_load_state('networkidle')
```

`PlaywrightCrawlingContext` additional attributes: `context.page`, `context.browser_controller`, `context.infinite_scroll()`, `context.block_requests(...)`.

### `AdaptivePlaywrightCrawler`
**File**: `src/crawlee/crawlers/_adaptive_playwright/_adaptive_playwright_crawler.py:80`

Intelligently switches between HTTP and browser rendering per URL based on an ML predictor. Requires `crawlee[adaptive-crawler]`.

```python
from crawlee.crawlers import AdaptivePlaywrightCrawler, AdaptivePlaywrightCrawlingContext

crawler = AdaptivePlaywrightCrawler(
    result_checker=lambda result: result.get('price') is not None,
    rendering_type_detection_ratio=0.1,  # fraction of URLs to test with both methods
)

@crawler.router.default_handler
async def handler(context: AdaptivePlaywrightCrawlingContext) -> None:
    # context may be HTTP or browser-based; uniform API
    await context.enqueue_links()
    await context.push_data({'url': context.request.url})
```

## Router and Request Handlers

**File**: `src/crawlee/router.py:20`

```python
from crawlee.crawlers import HttpCrawler, HttpCrawlingContext
from crawlee.router import Router

# Inline with crawler
crawler = HttpCrawler()

@crawler.router.default_handler
async def default(context: HttpCrawlingContext) -> None: ...

@crawler.router.handler(label='detail')
async def detail(context: HttpCrawlingContext) -> None: ...

# Or as standalone Router passed to crawler
router: Router[HttpCrawlingContext] = Router()

@router.default_handler
async def default(context: HttpCrawlingContext) -> None: ...

crawler = HttpCrawler(request_handler=router)
```

Request labels are set via `Request.from_url('https://...', label='detail')` or `context.add_requests(['https://...'], label='detail')`.

## `BasicCrawlingContext` — The Handler Interface

**File**: `src/crawlee/_types.py` (dataclass at approximately line 350+)

Every request handler receives a context object. `BasicCrawlingContext` provides:

```python
context.request          # Request object (url, method, headers, user_data, label, etc.)
context.session          # Session | None — current session
context.proxy_info       # ProxyInfo | None
context.log              # logging.Logger for the current request
context.crawler          # reference to the crawler instance

# Async helpers
await context.push_data(data, dataset_name=None)  # Save to Dataset
await context.add_requests(requests, label=None, strategy='same-hostname', include=[], exclude=[])
await context.enqueue_links(selector='a', label=None, strategy='same-hostname', include=[], exclude=[])
await context.get_key_value_store(name=None)       # Returns KeyValueStoreInterface
response = await context.send_request(url, method='GET', headers=None, payload=None)
state = await context.use_state(default={})       # Persistent state dict
```

## `Request` Model

**File**: `src/crawlee/_request.py:1`

```python
from crawlee import Request

# Factory methods
request = Request.from_url('https://example.com', label='detail', headers={'X-Custom': 'value'})
request = Request.from_url('https://example.com', method='POST', payload=b'{"key":"value"}')

# Attributes
request.url           # str
request.unique_key    # str (used for deduplication)
request.method        # HttpMethod literal
request.headers       # HttpHeaders
request.payload       # bytes | None
request.user_data     # UserData (label stored here; Crawlee metadata in user_data['__crawlee'])
request.label         # str | None (shortcut for user_data.label)
request.id            # str (UUID)
request.loaded_url    # str | None (final URL after redirects)
```

Deduplication is based on `unique_key` (defaults to normalized URL). Override with `unique_key='custom-key'` to allow duplicate URLs or prevent duplicates across differently-labeled requests.

## Storage APIs

### `Dataset`
**File**: `src/crawlee/storages/_dataset.py:33`

```python
from crawlee.storages import Dataset

dataset = await Dataset.open(name='results')     # or id='...'

# Write
await dataset.push_data({'url': 'https://...', 'price': 9.99})
await dataset.push_data([{'a': 1}, {'a': 2}])   # batch

# Read
page = await dataset.get_data(limit=100, offset=0, desc=False)
# page.items: list[dict], page.total: int, page.count: int

async for item in dataset.iterate_items():
    print(item)

# Export
await dataset.export_to('results.json', content_type='json')
await dataset.export_to('results.csv', content_type='text/csv')
await dataset.write_to('results.json', content_type='json')

await dataset.drop()   # Delete the dataset
```

### `KeyValueStore`
**File**: `src/crawlee/storages/_key_value_store.py`

```python
from crawlee.storages import KeyValueStore

kvs = await KeyValueStore.open(name='state')

await kvs.set_value('key', {'data': 123})
await kvs.set_value('screenshot', b'...png...', content_type='image/png')
value = await kvs.get_value('key')         # Returns the stored value or None
value = await kvs.get_value('key', default={})

async for key in kvs.iterate_keys():
    print(key)

await kvs.drop()
```

### `RequestQueue`
**File**: `src/crawlee/storages/_request_queue.py:33`

```python
from crawlee.storages import RequestQueue

rq = await RequestQueue.open(name='my-queue')

await rq.add_request('https://example.com')
await rq.add_request(Request.from_url('https://example.com', label='detail'))
await rq.add_requests(['https://a.com', 'https://b.com'])

# Used internally by BasicCrawler; direct access rarely needed
request = await rq.fetch_next_request()
await rq.mark_request_as_handled(request)
await rq.reclaim_request(request)

info = await rq.get_info()
# info.total_request_count, info.handled_request_count, info.pending_request_count
```

## Configuration

**File**: `src/crawlee/configuration.py:20`

```python
from crawlee.configuration import Configuration
from crawlee import service_locator

config = Configuration(
    purge_on_start=True,
    storage_dir='./my-storage',
    log_level='DEBUG',
    request_handler_timeout=timedelta(minutes=5),
)
service_locator.set_configuration(config)

# All CRAWLEE_* environment variables are automatically read
# e.g. CRAWLEE_LOG_LEVEL=DEBUG, CRAWLEE_STORAGE_DIR=./storage
```

## Proxy Configuration

**File**: `src/crawlee/proxy_configuration.py:56`

```python
from crawlee.proxy_configuration import ProxyConfiguration

# Static list of proxies (round-robin + tier fallback)
proxy_config = ProxyConfiguration(
    proxy_urls=['http://user:pass@proxy1:8080', 'http://user:pass@proxy2:8080'],
)

# Dynamic proxy selector
async def get_proxy(request, session_id, tier):
    return f'http://proxy-service.com/{session_id}'

proxy_config = ProxyConfiguration(new_url_function=get_proxy)

# Pass to crawler
crawler = BeautifulSoupCrawler(proxy_configuration=proxy_config)
```

## HTTP Clients

**File**: `src/crawlee/http_clients/_base.py:75`

```python
from crawlee.http_clients import ImpitHttpClient, HttpxHttpClient, CurlImpersonateHttpClient

# Default
crawler = BeautifulSoupCrawler(http_client=ImpitHttpClient())

# httpx-based (requires crawlee[httpx])
crawler = BeautifulSoupCrawler(http_client=HttpxHttpClient(http2=True))

# curl-cffi (requires crawlee[curl-impersonate])
crawler = BeautifulSoupCrawler(http_client=CurlImpersonateHttpClient(impersonate='chrome124'))
```

Custom HTTP client — implement `HttpClient`:

```python
from crawlee.http_clients import HttpClient, HttpResponse

class MyHttpClient(HttpClient):
    async def crawl(self, request, session, proxy_info, statistics) -> HttpCrawlingResult: ...
    async def send_request(self, url, method, headers, payload, session, proxy_info) -> HttpResponse: ...
```

## Custom Storage Client

**File**: `src/crawlee/storage_clients/_base/`

```python
from crawlee.storage_clients import FileSystemStorageClient, MemoryStorageClient, SqlStorageClient, RedisStorageClient
from crawlee import service_locator

# Use memory storage (no disk writes; useful for testing)
service_locator.set_storage_client(MemoryStorageClient())

# Use SQLite
from crawlee.storage_clients import SqlStorageClient
service_locator.set_storage_client(SqlStorageClient('sqlite+aiosqlite:///crawlee.db'))

# Use PostgreSQL
service_locator.set_storage_client(SqlStorageClient('postgresql+asyncpg://user:pass@host/db'))

# Use Redis
service_locator.set_storage_client(RedisStorageClient(host='localhost', port=6379))
```

## Request Loaders

**File**: `src/crawlee/request_loaders/`

```python
from crawlee.request_loaders import RequestList, SitemapRequestLoader

# Static list
loader = RequestList(['https://a.com', 'https://b.com'])
crawler = BeautifulSoupCrawler(request_manager=loader)

# Sitemap
sitemap_loader = SitemapRequestLoader('https://example.com/sitemap.xml')
crawler = BeautifulSoupCrawler(request_manager=sitemap_loader)
```

## Custom `ContextPipeline` (Advanced)

**File**: `src/crawlee/crawlers/_basic/_context_pipeline.py:57`

Used to create custom crawler types by extending the context step-by-step:

```python
from crawlee.crawlers import BasicCrawler, BasicCrawlingContext, ContextPipeline
from dataclasses import dataclass
from collections.abc import AsyncGenerator

@dataclass
class MyCrawlingContext(BasicCrawlingContext):
    extra_data: dict

async def my_middleware(context: BasicCrawlingContext) -> AsyncGenerator[MyCrawlingContext, None]:
    # setup
    yield MyCrawlingContext(**context.__dict__, extra_data={'computed': True})
    # teardown

pipeline = ContextPipeline().compose(my_middleware)
crawler = BasicCrawler(_context_pipeline=pipeline)
```

## `EnqueueStrategy` and `Glob` Filtering

```python
from crawlee import EnqueueStrategy, Glob

await context.enqueue_links(
    strategy='same-domain',              # 'all', 'same-domain', 'same-hostname', 'same-origin'
    include=[Glob('https://example.com/products/**')],
    exclude=[re.compile(r'/login'), Glob('**/admin/**')],
    limit=100,
)
```

## `ConcurrencySettings`

**File**: `src/crawlee/_types.py:105`

```python
from crawlee import ConcurrencySettings

settings = ConcurrencySettings(
    min_concurrency=1,          # never go below this
    max_concurrency=50,         # never go above this
    desired_concurrency=10,     # target at startup
    max_tasks_per_minute=300,   # rate limit
)
crawler = BeautifulSoupCrawler(concurrency_settings=settings)
```

## CLI Interface

**File**: `src/crawlee/_cli.py:24`

Entry point: `crawlee` (installed as script via `[project.scripts]`).

```bash
# Create new project
crawlee create my-scraper
# Prompts for: crawler type, HTTP client, package manager, start URL, Apify integration

# Print version
crawlee --version
```

## Error Types

**File**: `src/crawlee/errors.py`

| Exception | When raised |
|---|---|
| `SessionError` | Triggers session rotation (separate from `max_request_retries`) |
| `ProxyError(SessionError)` | Proxy is blocked or malfunctions |
| `HttpStatusCodeError` | Non-2xx HTTP status |
| `HttpClientStatusCodeError(HttpStatusCodeError)` | 4xx client errors |
| `ServiceConflictError` | Attempted double-initialization of a service |
| `RequestHandlerError` | Wraps exception from user handler, includes context |
| `ContextPipelineInitializationError` | Exception in middleware setup phase |
| `ContextPipelineFinalizationError` | Exception in middleware teardown phase |
| `ContextPipelineInterruptedError` | Middleware signals request should be skipped |
| `RequestCollisionError` | Request conflicts with required resources |
| `UserDefinedErrorHandlerError` | Error handler itself threw |

## OpenTelemetry Instrumentation

**File**: `src/crawlee/otel/crawler_instrumentor.py`

```python
from crawlee.otel import CrawlerInstrumentor

CrawlerInstrumentor().instrument()
# Now all crawler pipeline steps are wrapped in OTel spans
```

Requires `crawlee[otel]`.

## Integration Patterns

### Minimal scraper

```python
import asyncio
from crawlee.crawlers import BeautifulSoupCrawler, BeautifulSoupCrawlingContext

async def main() -> None:
    crawler = BeautifulSoupCrawler(max_requests_per_crawl=10)

    @crawler.router.default_handler
    async def handler(context: BeautifulSoupCrawlingContext) -> None:
        await context.push_data({'url': context.request.url, 'title': context.soup.title.string})
        await context.enqueue_links()

    await crawler.run(['https://example.com'])

asyncio.run(main())
```

### Multiple handlers by label

```python
@crawler.router.handler(label='listing')
async def listing(context: BeautifulSoupCrawlingContext) -> None:
    for link in context.soup.select('a.product'):
        await context.add_requests([link['href']], label='detail')

@crawler.router.handler(label='detail')
async def detail(context: BeautifulSoupCrawlingContext) -> None:
    await context.push_data({'price': context.soup.select_one('.price').text})
```

### Persistent state across requests

```python
@crawler.router.default_handler
async def handler(context: BeautifulSoupCrawlingContext) -> None:
    state = await context.use_state({'count': 0})
    state['count'] += 1
```

### Error and failed-request handlers

```python
@crawler.error_handler
async def on_error(context: BeautifulSoupCrawlingContext, error: Exception) -> Request | None:
    context.log.warning(f'Error: {error}')
    return None  # or return a modified Request to retry

@crawler.failed_request_handler
async def on_failed(context: BeautifulSoupCrawlingContext, error: Exception) -> None:
    await context.push_data({'url': context.request.url, 'error': str(error)})
```
