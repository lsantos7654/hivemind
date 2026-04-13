# Scrapling — APIs and Interfaces

## Public Entry Points

All public classes are lazily importable from either the top-level package or their submodule:

```python
from scrapling import Selector, Fetcher, AsyncFetcher, StealthyFetcher, DynamicFetcher
from scrapling.fetchers import (
    Fetcher, AsyncFetcher, FetcherSession,
    DynamicFetcher, DynamicSession, AsyncDynamicSession,
    StealthyFetcher, StealthySession, AsyncStealthySession,
    ProxyRotator,
)
from scrapling.spiders import Spider, Request, Response, CrawlResult, SessionManager
from scrapling.parser import Selector, Selectors
```

---

## Parser API (`scrapling/parser.py`)

### `Selector`

The central class for HTML parsing and element selection. Wraps `lxml.html.HtmlElement`.

**Constructor:**
```python
Selector(
    content: str | bytes | None = None,   # HTML content to parse
    url: str = "",                         # URL for urljoin and adaptive storage scoping
    encoding: str = "utf-8",
    huge_tree: bool = True,               # Allows parsing large HTML without memory limits
    root: HtmlElement | None = None,       # Internal: pass lxml element directly
    keep_comments: bool = False,
    keep_cdata: bool = False,
    adaptive: bool = False,               # Enable adaptive element tracking
    storage: Any = SQLiteStorageSystem,   # Storage class (must be lru_cache-wrapped)
    storage_args: dict | None = None,     # Overrides for storage constructor
)
```
**Source**: `scrapling/parser.py:64`

#### Selection Methods

```python
# CSS selectors (Scrapy pseudo-elements supported)
elements = page.css('.product')                       # Returns Selectors
texts    = page.css('.product .title::text').getall() # List of strings
attr     = page.css('a::attr(href)').get()            # First string or None

# XPath selectors
elements = page.xpath('//div[@class="product"]')
texts    = page.xpath('//span/text()').getall()

# Adaptive variants (auto_save + adaptive flags)
page.css('.price', auto_save=True)       # Save element fingerprint to DB
page.css('.price', adaptive=True)        # On next run: relocate even if structure changed
page.css('.price', identifier='product-price')  # Explicit ID instead of selector string
```

**Source**: `scrapling/parser.py:564` (css), `scrapling/parser.py:624` (xpath)

#### `find_all()` — BeautifulSoup-style

```python
# By tag name
page.find_all('div')
page.find_all(['div', 'span'])                # Multiple tags

# By attributes (kwargs)
page.find_all('a', href='https://example.com')
page.find_all(class_='product')              # 'class_' mapped to 'class'

# By dict
page.find_all({'class': 'product'})

# By regex pattern
import re
page.find_all(re.compile(r'product-\d+'))    # Applied to element text

# By callable
page.find_all(lambda el: el.text.startswith('$'))

# Combined
page.find_all('div', {'data-id': '42'}, re.compile(r'\d+'))
```

**Source**: `scrapling/parser.py:694`

#### `find_by_text()` / `find_by_regex()`

```python
# Find element whose text exactly matches (case-insensitive by default)
el = page.find_by_text('Add to Cart')
# Partial match
els = page.find_by_text('Product', first_match=False, partial=True)

# Regex
el = page.find_by_regex(r'\$\d+\.\d{2}')
```

**Source**: `scrapling/parser.py:1090`, `scrapling/parser.py:1156`

#### DOM Traversal Properties

```python
el.parent          # Selector | None
el.children        # Selectors
el.siblings        # Selectors
el.next            # Selector | None  (next sibling)
el.previous        # Selector | None  (previous sibling)
el.path            # Selectors (ancestor chain to root)
el.below_elements  # Selectors (all descendants)
el.iterancestors() # Generator[Selector]
el.find_ancestor(lambda a: a.tag == 'table')  # First matching ancestor
```

**Source**: `scrapling/parser.py:385-438`

#### Element Properties

```python
el.tag          # str: 'div', '#text', etc.
el.text         # TextHandler: direct text of element (not children)
el.attrib       # AttributesHandler: read-only attribute mapping
el['href']      # TextHandler: shortcut for el.attrib['href']
el.html_content # TextHandler: inner HTML as string
el.body         # str|bytes: raw unparsed response body (on root Selector only)
el.url          # str: URL passed at construction
el.get_all_text(separator='\n', strip=False, ignore_tags=('script','style'))
```

#### Selector Generation

```python
el.generate_css_selector        # e.g., "div > ul > li:nth-of-type(2)"
el.generate_full_css_selector   # Full path from root
el.generate_xpath_selector      # e.g., "//div/ul/li[2]"
```

**Source**: `scrapling/core/mixins.py:59-85`

#### `find_similar()` — AutoScraper-like

```python
# Given one product element, find all similar products on the page
product = page.css('.product')[0]
all_products = product.find_similar(
    similarity_threshold=0.2,
    ignore_attributes=['href', 'src'],
    match_text=False,
)
```

**Source**: `scrapling/parser.py:1009`

#### Adaptive Engine Methods

```python
page.save(element, identifier='my-price')   # Save element fingerprint to storage
page.retrieve('my-price')                   # Return saved dict or None
page.relocate(element_dict, percentage=0)   # Find best matching element in current page
```

#### Text and JSON Operations

```python
el.json()                           # Parse body/text as JSON (uses orjson)
el.re(r'\d+')                       # Regex on element text → TextHandlers
el.re_first(r'\d+', default='0')    # First match or default
el.urljoin('/path/to/page')         # Absolute URL from relative
el.prettify()                       # Indented HTML string
el.has_class('active')              # bool
```

### `Selectors` (list subclass)

Propagates all `Selector` methods across collections. Key additions:

```python
selectors.css('.child')         # Runs css() on each element, returns flat Selectors
selectors.xpath('//a')
selectors.get()                 # First element's .get() or None
selectors.getall()              # List of .get() for each element
selectors.filter(lambda el: el.text == 'foo')  # Filter by predicate
selectors.attrib                # AttributesHandler of the first element
selectors[0]                    # Selector
selectors[1:3]                  # Selectors (slice returns Selectors, not list)
```

### `TextHandler` (str subclass — `scrapling/core/custom_types.py:29`)

All string returns are `TextHandler` instances, which are fully compatible with `str` and add:

```python
text.re(r'\d+')                         # → TextHandlers
text.re_first(r'\d+', default=None)     # → TextHandler | None
text.json()                             # → dict  (uses orjson)
text.clean()                            # Remove whitespace/consecutive spaces
text.get()                              # Returns self (Scrapy compatibility)
text.getall()                           # Returns self (Scrapy compatibility)
```

### `AttributesHandler` (read-only Mapping — `scrapling/core/custom_types.py:285`)

```python
el.attrib['class']              # → TextHandler
el.attrib.get('id', '')         # → TextHandler
el.attrib.search_values('active', partial=True)  # → Generator[AttributesHandler]
el.attrib.json_string           # → bytes (orjson serialization)
```

---

## Fetcher API (`scrapling/fetchers/`)

### `Fetcher` / `AsyncFetcher` — One-off HTTP requests

Stateless class-method API. Returns `Response` on every call.

```python
from scrapling.fetchers import Fetcher, AsyncFetcher

page = Fetcher.get('https://example.com', impersonate='chrome')
page = Fetcher.post('https://api.example.com/data', json={'key': 'value'})
page = Fetcher.put('https://example.com/resource', data='body')
page = Fetcher.delete('https://example.com/resource/1')

# Async
page = await AsyncFetcher.get('https://example.com')
```

**Class-level configuration** (applies to all subsequent calls):
```python
Fetcher.configure(
    adaptive=True,
    storage_args={'storage_file': '/tmp/my.db', 'url': 'https://example.com'},
    huge_tree=True,
    keep_comments=False,
)
```

**Source**: `scrapling/fetchers/requests.py:13`, `scrapling/engines/toolbelt/custom.py:150`

### `FetcherSession` — Persistent HTTP session

```python
from scrapling.fetchers import FetcherSession

# Sync context manager
with FetcherSession(
    impersonate='chrome',            # Browser to impersonate for TLS fingerprint
    stealthy_headers=True,           # Generate realistic browser headers
    http3=False,                     # Enable HTTP/3
    timeout=30,
    retries=3,
    retry_delay=1,
    proxy='http://proxy:8080',
    proxy_rotator=ProxyRotator([...]),
    follow_redirects='safe',
) as session:
    page1 = session.get('https://example.com')
    page2 = session.post('https://example.com/api', json={'q': 'test'})

# Async context manager (same class is context-aware)
async with FetcherSession(http3=True) as session:
    page = await session.get('https://example.com')
```

**Source**: `scrapling/engines/static.py:49`

### `DynamicFetcher` / `DynamicSession` — Full browser automation

```python
from scrapling.fetchers import DynamicFetcher, DynamicSession

# One-off
page = DynamicFetcher.fetch('https://example.com',
    headless=True,
    disable_resources=True,     # Block fonts, images, etc. for speed
    network_idle=True,          # Wait until no network activity
    load_dom=True,              # Wait for full JS execution
    timeout=30000,              # ms
    wait=500,                   # Extra wait after load (ms)
    wait_selector='.price',     # Wait for CSS selector to appear
    wait_selector_state='visible',
    page_action=lambda page: page.click('#cookie-accept'),  # Playwright automation
    cookies=[{'name': 'session', 'value': 'abc', 'domain': 'example.com'}],
    extra_headers={'X-Custom': 'value'},
    proxy={'server': 'http://proxy:8080', 'username': 'user', 'password': 'pass'},
    real_chrome=False,          # Use installed Chrome instead of bundled Chromium
    cdp_url='http://localhost:9222',  # Connect to existing browser via CDP
    google_search=True,         # Set Google as referer
    capture_xhr=True,           # Capture XHR/fetch responses
    blocked_domains={'ads.example.com'},
)

# Session (keeps browser open)
with DynamicSession(headless=True, max_pages=5) as session:
    page1 = session.fetch('https://example.com/page1')
    page2 = session.fetch('https://example.com/page2')
    print(session.get_pool_stats())   # busy/free/error counts

# Async session
async with AsyncDynamicSession(headless=True) as session:
    page = await session.fetch('https://example.com')
```

**Source**: `scrapling/fetchers/chrome.py:7`, `scrapling/engines/_browsers/_controllers.py`

### `StealthyFetcher` / `StealthySession` — Anti-bot stealth mode

```python
from scrapling.fetchers import StealthyFetcher, StealthySession

# One-off — solves Cloudflare Turnstile automatically
page = StealthyFetcher.fetch('https://protected.com',
    headless=True,
    solve_cloudflare=True,      # Automatically solve Cloudflare challenges
    hide_canvas=True,           # Canvas fingerprint noise
    block_webrtc=True,          # WebRTC leak prevention
    allow_webgl=True,           # Keep WebGL enabled (WAFs check for it)
    user_data_dir='/path/to/profile',  # Persist browser profile
    # All DynamicFetcher params are also accepted
)

# Session
with StealthySession(headless=True, solve_cloudflare=True) as session:
    page = session.fetch('https://nopecha.com/demo/cloudflare', google_search=False)
```

**Source**: `scrapling/fetchers/stealth_chrome.py:7`, `scrapling/engines/_browsers/_stealth.py`

### `ProxyRotator`

```python
from scrapling.fetchers import ProxyRotator

rotator = ProxyRotator(
    proxies=[
        'http://proxy1:8080',
        {'server': 'http://proxy2:8080', 'username': 'user', 'password': 'pass'},
    ],
    strategy=cyclic_rotation,   # Default; or provide custom callable
)

# Use with any session
with FetcherSession(proxy_rotator=rotator) as session:
    page = session.get('https://example.com')
```

**Source**: `scrapling/engines/toolbelt/proxy_rotation.py:39`

---

## Spider Framework API (`scrapling/spiders/`)

### `Spider` — Abstract Base Class

```python
from scrapling.spiders import Spider, Request, Response

class MySpider(Spider):
    name = "my_spider"                    # Required
    start_urls = ["https://example.com/"]

    # Concurrency
    concurrent_requests = 4               # Global semaphore
    concurrent_requests_per_domain = 2    # Per-domain semaphore (0=unlimited)
    download_delay = 0.5                  # Seconds between requests

    # Features
    robots_txt_obey = False
    development_mode = False              # Cache responses to disk
    development_cache_dir = None          # Directory for cache

    # Fingerprinting for deduplication
    fp_include_kwargs = False
    fp_include_headers = False
    fp_keep_fragments = False

    # Logging
    logging_level = logging.DEBUG
    log_file = "spider.log"              # Optional file logging

    # Blocked request handling
    max_blocked_retries = 3

    async def parse(self, response: Response):
        # Must be an async generator
        for item in response.css('.product'):
            yield {'title': item.css('h2::text').get()}

        next_link = response.css('.next a')
        if next_link:
            yield response.follow(next_link[0]['href'])

    # Optional lifecycle hooks
    async def on_start(self, resuming: bool = False): pass
    async def on_close(self): pass
    async def on_error(self, request: Request, error: Exception): pass
    async def on_scraped_item(self, item: dict) -> dict | None:
        # Return None to drop item silently
        return item
    async def is_blocked(self, response: Response) -> bool:
        return response.status in {401, 403, 429, 503}
    async def retry_blocked_request(self, request: Request, response: Response) -> Request:
        return request  # Modify and return for retry
```

**Source**: `scrapling/spiders/spider.py:65`

#### `configure_sessions()` — Multi-session setup

```python
def configure_sessions(self, manager: SessionManager) -> None:
    manager.add("fast", FetcherSession(impersonate="chrome"))
    manager.add("stealth", AsyncStealthySession(headless=True), lazy=True)
    # lazy=True: browser opened only when first request with sid="stealth" arrives
```

**Source**: `scrapling/spiders/spider.py:211`

#### Running and Streaming

```python
# Synchronous run (blocks until done)
result: CrawlResult = MySpider().start(use_uvloop=False)
print(f"Items: {len(result.items)}")
print(result.stats.to_dict())
result.items.to_json("output.json")
result.items.to_jsonl("output.jsonl")

# Pause/resume
spider = MySpider(crawldir="./crawl_state")
result = spider.start()  # Press Ctrl+C to pause; rerun to resume

# Streaming (async context)
async def main():
    spider = MySpider()
    async for item in spider.stream():
        print(item)
        print(spider.stats.requests_count)  # Real-time stats during stream
```

**Source**: `scrapling/spiders/spider.py:271-323`

### `Request`

```python
from scrapling.spiders import Request

req = Request(
    url="https://example.com/page/2",
    sid="stealth",                   # Session ID to route through
    callback=self.parse_detail,      # Callable or None (defaults to spider.parse)
    priority=10,                     # Higher = processed first
    dont_filter=False,               # Allow duplicate requests
    meta={'category': 'electronics'},
    # All extra kwargs are forwarded to the session's fetch()
    headers={'Referer': 'https://example.com'},
    timeout=60000,
)
```

**Source**: `scrapling/spiders/request.py:25`

### `Response` (in spider context)

Inherits from `Selector`. Adds:

```python
response.status            # int: HTTP status code
response.reason            # str: e.g., "OK"
response.headers           # dict
response.cookies           # dict or tuple of dicts
response.history           # list of redirect responses
response.meta              # dict: passed from Request.meta
response.request           # Request: the request that generated this response
response.captured_xhr      # list[Response]: XHR captures if capture_xhr=True
response.body              # bytes: raw response body

# Create a follow-up request (inherits parent request's sid, callback, meta)
new_req = response.follow('/next-page', sid='stealth', callback=self.parse_detail)
```

**Source**: `scrapling/engines/toolbelt/custom.py:28`

### `CrawlResult` and `CrawlStats`

```python
result.items              # ItemList (list subclass)
result.items.to_json("out.json", indent=True)
result.items.to_jsonl("out.jsonl")
result.stats              # CrawlStats dataclass
result.paused             # bool: True if stopped via Ctrl+C
result.completed          # bool: not paused

# CrawlStats fields
stats.requests_count
stats.failed_requests_count
stats.blocked_requests_count
stats.items_scraped
stats.items_dropped
stats.elapsed_seconds
stats.requests_per_second
stats.response_status_count   # {'status_200': 42, 'status_404': 1, ...}
stats.sessions_requests_count # {'fast': 30, 'stealth': 12}
stats.domains_response_bytes
stats.cache_hits, stats.cache_misses
stats.to_dict()            # Full stats as plain dict
```

**Source**: `scrapling/spiders/result.py`

---

## Storage / Adaptive Engine API (`scrapling/core/storage.py`)

To use a custom storage backend:

```python
from functools import lru_cache
from scrapling.core.storage import StorageSystemMixin

@lru_cache(1)  # Required: must be lru_cache-wrapped
class MyStorage(StorageSystemMixin):
    def __init__(self, url=None, **kwargs):
        super().__init__(url)

    def save(self, element: HtmlElement, identifier: str) -> None:
        # Serialize and store element metadata
        ...

    def retrieve(self, identifier: str) -> dict | None:
        # Return stored element dict or None
        ...

# Use with Selector
page = Selector(html, adaptive=True, storage=MyStorage, storage_args={'url': 'https://example.com'})
```

**Source**: `scrapling/core/storage.py:14`

---

## Configuration Patterns

### Global fetcher configuration

```python
from scrapling.fetchers import StealthyFetcher

StealthyFetcher.configure(
    adaptive=True,                     # Enable adaptive element tracking globally
    adaptive_domain='https://example.com',  # Scope storage to this domain
    storage_args={'storage_file': 'my.db'},
)
page = StealthyFetcher.fetch('https://example.com')
products = page.css('.product', auto_save=True)  # Saved for future runs
# Next run on modified page:
products = page.css('.product', adaptive=True)   # Auto-relocated
```

**Source**: `scrapling/engines/toolbelt/custom.py:193`

### Parser-only usage (no fetcher)

```python
from scrapling.parser import Selector

with open('page.html') as f:
    page = Selector(f.read(), url='https://example.com')

titles = page.css('h1::text').getall()
```

### Async fetcher patterns

```python
import asyncio
from scrapling.fetchers import AsyncFetcher, AsyncStealthySession

async def scrape():
    async with AsyncStealthySession(headless=True, max_pages=3) as session:
        tasks = [session.fetch(url) for url in urls]
        print(session.get_pool_stats())
        pages = await asyncio.gather(*tasks)
    return pages

asyncio.run(scrape())
```

---

## MCP Server Integration (`scrapling/core/ai.py`)

The MCP server is started via the CLI:

```bash
scrapling mcp
```

Tools exposed to AI clients:
- `get(url, ...)` — HTTP GET via `FetcherSession`
- `fetch(url, ...)` — Browser fetch via `AsyncDynamicSession`
- `stealthy_fetch(url, ...)` — Stealth browser fetch via `AsyncStealthySession`
- `create_session(session_type, ...)` — Create a persistent browser session
- `close_session(session_id)` — Close a session
- `list_sessions()` — List open sessions
- `session_get(session_id, url, ...)` — GET using open session
- `session_fetch(session_id, url, ...)` — Browser fetch using open session

All tools return `ResponseModel` with `status`, `content` (Markdown/text/HTML), and `url`.

**Source**: `scrapling/core/ai.py:36-828`
