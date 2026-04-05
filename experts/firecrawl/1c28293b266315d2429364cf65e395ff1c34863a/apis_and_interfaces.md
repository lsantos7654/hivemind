# Firecrawl — APIs and Interfaces

## REST API Overview

Base URL: `https://api.firecrawl.dev` (cloud) or `http://localhost:3002` (self-hosted)

Authentication: `Authorization: Bearer fc-YOUR_API_KEY` header on all requests.

API versions: `/v1` (stable), `/v2` (current default). The Python and JS SDKs default to v2.

---

## Python SDK — Primary Interface

Package: `firecrawl-py`  
Import: `from firecrawl import Firecrawl, AsyncFirecrawl`  
Source: `apps/python-sdk/firecrawl/`

### Initialization

```python
from firecrawl import Firecrawl

# Cloud service
app = Firecrawl(api_key="fc-YOUR_API_KEY")

# Self-hosted
app = Firecrawl(api_key="any-key", api_url="http://localhost:3002")

# Environment variable: FIRECRAWL_API_KEY
app = Firecrawl()
```

`FirecrawlClient.__init__` (v2, `apps/python-sdk/firecrawl/v2/client.py:68`):
- `api_key: Optional[str]` — API key (or `FIRECRAWL_API_KEY` env var)
- `api_url: str` — Base URL (default: `https://api.firecrawl.dev`)
- `timeout: Optional[float]` — Request timeout in seconds
- `max_retries: int` — Maximum retries (default: 3)
- `backoff_factor: float` — Exponential backoff factor (default: 0.5)

### `scrape()` — Scrape a Single URL

```python
result = app.scrape(
    'https://example.com',
    formats=['markdown', 'html', 'screenshot'],
    only_main_content=True,
    wait_for=2000,          # Wait 2s for JS
    actions=[
        {"type": "click", "selector": "#button"},
        {"type": "wait", "milliseconds": 1000},
    ],
    mobile=True,
    parsers=['pdf', 'docx'],
    location={"country": "US"},
    timeout=60000,
    block_ads=True,
    proxy="stealth",
    max_age=3600,           # Cache max age in seconds
    store_in_cache=True,
)

print(result.markdown)          # Markdown content
print(result.html)              # Raw HTML
print(result.screenshot)        # Base64 screenshot URL
print(result.metadata.title)    # Page title
print(result.metadata.scrape_id) # Scrape ID (for interact)
```

Signature (`apps/python-sdk/firecrawl/v2/client.py:111`):
```python
def scrape(
    self,
    url: str,
    *,
    formats: Optional[List[FormatOption]] = None,  # 'markdown'|'html'|'rawHtml'|'screenshot'|'screenshot@fullScreen'|'links'|'json'|'changeTracking'
    headers: Optional[Dict[str, str]] = None,
    include_tags: Optional[List[str]] = None,
    exclude_tags: Optional[List[str]] = None,
    only_main_content: Optional[bool] = None,
    timeout: Optional[int] = None,          # Milliseconds
    wait_for: Optional[int] = None,         # Milliseconds
    mobile: Optional[bool] = None,
    parsers: Optional[List[str]] = None,    # ['pdf', 'docx']
    actions: Optional[List[...]] = None,    # Browser actions
    location: Optional[Location] = None,
    skip_tls_verification: Optional[bool] = None,
    remove_base64_images: Optional[bool] = None,
    fast_mode: Optional[bool] = None,
    block_ads: Optional[bool] = None,
    proxy: Optional[str] = None,            # 'basic'|'stealth'
    max_age: Optional[int] = None,          # Cache TTL in seconds
    store_in_cache: Optional[bool] = None,
    profile: Optional[Dict[str, Any]] = None, # Browser profile
    integration: Optional[str] = None,
) -> Document
```

### `interact()` — Browser Interaction

After scraping, keep the browser session and interact with the page:

```python
# 1. Scrape a page (keeps browser alive)
result = app.scrape("https://amazon.com")
scrape_id = result.metadata.scrape_id

# 2. Interact via natural language prompt
response = app.interact(scrape_id, prompt="Search for 'mechanical keyboard'")

# 3. Interact via code
response = app.interact(
    scrape_id,
    code="document.querySelector('#input').value = 'hello'",
    language="node"  # 'python'|'node'|'bash'
)
```

Signature (`apps/python-sdk/firecrawl/v2/client.py:191`):
```python
def interact(
    self,
    job_id: str,
    code: Optional[str] = None,
    *,
    prompt: Optional[str] = None,
    language: Literal["python", "node", "bash"] = "node",
    timeout: Optional[int] = None,  # 1-300 seconds
    origin: Optional[str] = None,
) -> BrowserExecuteResponse
```

### `search()` — Web Search with Content

```python
results = app.search(
    "firecrawl web scraping",
    limit=5,
    sources=["web", "news"],
    categories=["technology"],
    location="US",
    tbs="qdr:d",  # Time-based search (past day)
    scrape_options=ScrapeOptions(formats=['markdown']),
)
for item in results.data:
    print(item.url, item.title, item.markdown)
```

### `crawl()` — Full Site Crawl (Blocking)

```python
from firecrawl.types import ScrapeOptions

job = app.crawl(
    'https://firecrawl.dev',
    limit=100,
    max_discovery_depth=3,
    exclude_paths=['*/blog/*'],
    include_paths=['*/docs/*'],
    allow_subdomains=True,
    scrape_options=ScrapeOptions(formats=['markdown']),
    webhook="https://your-server.com/webhook",
    poll_interval=5,   # Seconds between status checks
    timeout=300000,    # Total timeout in milliseconds
)
print(job.total_count, job.credits_used)
for doc in job.data:
    print(doc.metadata.url, doc.markdown[:200])
```

### `start_crawl()` — Async Crawl (Non-blocking)

```python
crawl_job = app.start_crawl('https://firecrawl.dev', limit=100)
print(crawl_job.id)  # Use this ID to check status

# Check status later
status = app.check_crawl_status(crawl_job.id)

# Or use Watcher
from firecrawl import Watcher
watcher = app.start_crawl_and_watch('https://firecrawl.dev', limit=100)
for doc in watcher:
    print(doc.url)
```

### `batch_scrape()` — Bulk URL Scraping

```python
job = app.batch_scrape(
    ['https://firecrawl.dev', 'https://docs.firecrawl.dev'],
    formats=['markdown'],
    poll_interval=2,
)
for doc in job.data:
    print(doc.metadata.url, doc.markdown[:200])
```

### `map()` — URL Discovery

```python
result = app.map(
    'https://firecrawl.dev',
    search='documentation',  # Filter by keyword
    limit=100,
)
print(result.links)  # List of discovered URLs
```

### `extract()` — AI-Powered Structured Extraction

```python
result = app.extract(
    ['https://firecrawl.dev', 'https://docs.firecrawl.dev'],
    prompt="Extract the pricing plans and features",
    schema={
        "type": "object",
        "properties": {
            "plan_name": {"type": "string"},
            "price": {"type": "number"},
            "features": {"type": "array", "items": {"type": "string"}},
        }
    },
    allow_external_links=True,
)
print(result.data)  # Structured dict matching schema
```

### `agent()` — Autonomous Web Agent

```python
result = app.agent(
    "Find the top 5 AI companies by funding in 2024",
    max_steps=10,
)
print(result.data)
print(result.sources)  # URLs visited
```

### Async Client

```python
from firecrawl import AsyncFirecrawl
import asyncio

async def main():
    app = AsyncFirecrawl(api_key="fc-YOUR_API_KEY")
    result = await app.scrape('https://firecrawl.dev', formats=['markdown'])
    print(result.markdown)
    
    # Async crawl
    async for doc in app.crawl_stream('https://firecrawl.dev', limit=50):
        print(doc.url)

asyncio.run(main())
```

---

## JavaScript/TypeScript SDK

Package: `@mendable/firecrawl-js`  
Import: `import Firecrawl from '@mendable/firecrawl-js'`  
Source: `apps/js-sdk/firecrawl/src/index.ts`

```typescript
import Firecrawl from '@mendable/firecrawl-js';

const app = new Firecrawl({ apiKey: "fc-YOUR_API_KEY" });

// Scrape
const result = await app.scrape('https://firecrawl.dev');
console.log(result.markdown);

// Search
const search = await app.search("firecrawl scraping", { limit: 5 });

// Crawl (blocking, polls internally)
const crawl = await app.crawl('https://firecrawl.dev', { limit: 100 });

// Async crawl (returns job ID)
const job = await app.asyncCrawl('https://firecrawl.dev', { limit: 100 });
const status = await app.checkCrawlStatus(job.id);

// Crawl with WebSocket streaming
const watcher = app.crawlAndWatch('https://firecrawl.dev', { limit: 100 });
watcher.on('document', (doc) => console.log(doc.url));
watcher.on('done', (final) => console.log('Done!'));

// Map
const map = await app.map('https://firecrawl.dev');

// Extract
const extract = await app.extract(['https://firecrawl.dev'], {
    prompt: "Extract pricing information",
    schema: { type: "object", properties: { price: { type: "number" } } }
});

// Interact
const scrapeResult = await app.scrape("https://amazon.com");
await app.interact(scrapeResult.metadata.scrapeId, {
    prompt: "Search for mechanical keyboard"
});

// Access legacy v1 client
app.v1.scrapeUrl('https://firecrawl.dev', { formats: ['markdown'] });
```

### Watcher (JS SDK)

```typescript
import { Watcher } from '@mendable/firecrawl-js';

const watcher = new Watcher(crawlId, { apiKey: 'fc-...' });
watcher.on('document', (doc) => { ... });
watcher.on('done', (status) => { ... });
watcher.on('error', (err) => { ... });
```

---

## REST API Endpoints (v2)

All v2 endpoints are defined in `apps/api/src/routes/v2.ts` and `apps/api/src/controllers/v2/`.

### POST `/v2/scrape`
Scrape a single URL synchronously.

**Request body:**
```json
{
  "url": "https://example.com",
  "formats": ["markdown", "html", "screenshot", "links", "json"],
  "onlyMainContent": true,
  "includeTags": ["article", "main"],
  "excludeTags": ["nav", "footer"],
  "waitFor": 2000,
  "timeout": 30000,
  "mobile": false,
  "actions": [
    {"type": "click", "selector": "#button"},
    {"type": "wait", "milliseconds": 1000},
    {"type": "screenshot"},
    {"type": "write", "text": "hello", "selector": "#input"},
    {"type": "press", "key": "Enter"},
    {"type": "scroll", "direction": "down", "amount": 500},
    {"type": "executeJavascript", "script": "window.scrollTo(0,0)"}
  ],
  "location": {"country": "US", "languages": ["en-US"]},
  "parsers": ["pdf"],
  "removeBase64Images": true,
  "blockAds": true,
  "proxy": "stealth",
  "maxAge": 3600,
  "storeInCache": true,
  "skipTlsVerification": false,
  "zeroDataRetention": false
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "markdown": "# Page Title\n...",
    "html": "<html>...</html>",
    "rawHtml": "<html>...</html>",
    "screenshot": "https://...",
    "links": ["https://..."],
    "json": {},
    "metadata": {
      "title": "Page Title",
      "description": "...",
      "url": "https://example.com",
      "statusCode": 200,
      "scrapeId": "uuid-v7",
      "proxyUsed": "basic"
    }
  }
}
```

### POST `/v2/crawl`
Start a crawl job (async). Returns a job ID.

**Request body:**
```json
{
  "url": "https://firecrawl.dev",
  "limit": 100,
  "maxDiscoveryDepth": 3,
  "excludePaths": ["*/blog/*"],
  "includePaths": ["*/docs/*"],
  "allowSubdomains": false,
  "allowExternalLinks": false,
  "ignoreSitemap": false,
  "sitemap": "include",
  "ignoreQueryParameters": false,
  "deduplicateSimilarUrls": true,
  "delay": 0,
  "maxConcurrency": 5,
  "prompt": "Only crawl product pages",
  "webhook": "https://your-server.com/webhook",
  "scrapeOptions": { "formats": ["markdown"] },
  "zeroDataRetention": false
}
```

**Response:**
```json
{ "success": true, "id": "crawl-uuid", "url": "/v2/crawl/crawl-uuid" }
```

### GET `/v2/crawl/:id`
Check crawl status and retrieve results (paginated).

**Response:**
```json
{
  "success": true,
  "status": "completed",
  "total": 50,
  "completed": 50,
  "creditsUsed": 50,
  "expiresAt": "2024-...",
  "next": "/v2/crawl/id?skip=10",
  "data": [{ "markdown": "...", "metadata": { "url": "..." } }]
}
```

### GET `/v2/crawl/:id` (WebSocket)
Stream crawl results in real time.

### DELETE `/v2/crawl/:id`
Cancel an in-progress crawl.

### POST `/v2/map`
Discover all URLs on a site.

**Request:**
```json
{ "url": "https://firecrawl.dev", "search": "docs", "limit": 5000, "includeSitemap": true }
```

**Response:**
```json
{ "success": true, "links": ["https://firecrawl.dev/docs/..."] }
```

### POST `/v2/search`
Search the web and get page content.

**Request:**
```json
{
  "query": "firecrawl web scraping",
  "limit": 5,
  "tbs": "qdr:d",
  "location": "US",
  "sources": ["web"],
  "scrapeOptions": { "formats": ["markdown"] }
}
```

### POST `/v2/batch/scrape`
Batch scrape multiple URLs asynchronously.

**Request:**
```json
{
  "urls": ["https://a.com", "https://b.com"],
  "formats": ["markdown"],
  "webhook": "https://your-server.com/hook"
}
```

### POST `/v2/extract`
AI-powered structured extraction from URLs.

**Request:**
```json
{
  "urls": ["https://firecrawl.dev"],
  "prompt": "Extract pricing information",
  "schema": {
    "type": "object",
    "properties": { "price": { "type": "number" } }
  },
  "allowExternalLinks": false,
  "enableWebSearch": false,
  "agent": { "model": "fire-1" }
}
```

### GET `/v2/extract/:id`
Check extract job status.

### POST `/v2/agent`
Run autonomous AI agent.

**Request:**
```json
{
  "prompt": "Find top AI companies by funding",
  "maxSteps": 10,
  "model": "fire-1"
}
```

### POST `/v2/scrape/:id/interact`
Interact with a live browser session from a previous scrape.

**Request:**
```json
{
  "prompt": "Click the login button",
  "code": "document.querySelector('#login').click()",
  "language": "node"
}
```

### DELETE `/v2/scrape/:id/browser`
Terminate a browser session.

---

## Key TypeScript Types (API)

Defined in `apps/api/src/controllers/v2/types.ts`:

```typescript
// Scraping engines available
type Engine =
  | "fire-engine;chrome-cdp"
  | "fire-engine(retry);chrome-cdp"
  | "fire-engine;chrome-cdp;stealth"
  | "fire-engine;tlsclient"
  | "playwright"
  | "fetch"
  | "pdf"
  | "document"
  | "index"
  | "wikipedia";

// Output formats
type FormatOption =
  | "markdown" | "html" | "rawHtml"
  | "screenshot" | "screenshot@fullScreen"
  | "links" | "json" | "changeTracking";

// Browser actions
type ScrapeAction =
  | { type: "wait"; milliseconds: number }
  | { type: "screenshot" }
  | { type: "click"; selector: string }
  | { type: "write"; text: string; selector: string }
  | { type: "press"; key: string }
  | { type: "scroll"; direction: "up"|"down"; amount?: number }
  | { type: "executeJavascript"; script: string };
```

---

## Configuration and Extension Points

### Engine Selection

Engines are enabled via environment variables (`apps/api/src/scraper/scrapeURL/engines/index.ts`):
- `FIRE_ENGINE_BETA_URL` — Enables Fire Engine (cloud-only)
- `PLAYWRIGHT_MICROSERVICE_URL` — Enables Playwright (default: `http://playwright-service:3000/scrape`)
- `WIKIPEDIA_ENTERPRISE_USERNAME` + `WIKIPEDIA_ENTERPRISE_PASSWORD` — Enables Wikipedia engine

### LLM Configuration

AI features (extract, JSON format, agent) use:
- `OPENAI_API_KEY` + optional `OPENAI_BASE_URL` (any OpenAI-compatible endpoint)
- `OLLAMA_BASE_URL` — Local Ollama server
- `MODEL_NAME` — Override default model
- `MODEL_EMBEDDING_NAME` — Override embedding model

### Webhook Notifications

All async jobs (crawl, batch scrape, extract) support a `webhook` parameter:
- String URL — POST to this URL on completion
- `WebhookConfig` object — `{ url, headers, metadata }`

Webhook payload includes job status, credits used, and optionally the document data.

### Zero Data Retention (ZDR)

Set `zeroDataRetention: true` on scrape/crawl requests to ensure no content is stored server-side. Enabled per-team via flags. Affects which features are available (extract and agent do not support ZDR).

### Proxy Configuration

`proxy` field on scrape requests:
- `"basic"` — Standard proxy rotation
- `"stealth"` — Advanced anti-detection proxy (fire-engine only in cloud)

Self-hosted: configure `PROXY_SERVER`, `PROXY_USERNAME`, `PROXY_PASSWORD`.

### Search Backends

The `/search` API supports multiple backends:
- Google (default, direct)
- SearXNG (configure `SEARXNG_ENDPOINT`)
- DuckDuckGo (fallback)
- FireEngine search (cloud only)

### x402 Micropayments

Premium search endpoints support the x402 payment protocol (Coinbase). Enabled via `X402_PAY_TO_ADDRESS` and `X402_ENDPOINT_PRICE_USD` env vars.
