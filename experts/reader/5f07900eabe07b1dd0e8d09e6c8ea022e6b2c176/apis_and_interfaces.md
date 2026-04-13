# Jina Reader — APIs and Interfaces

## Public HTTP API Entry Points

The live service exposes two domains:
- `https://r.jina.ai/` — URL-to-content conversion (backed by `CrawlerHost`)
- `https://s.jina.ai/` — Web search with content fetching (backed by `SearcherHost`)

When self-hosting, both endpoints are served on the same port (default `3000`) from a single Koa server.

---

## Crawl API (`r.jina.ai` / `CrawlerHost`)

### Endpoint Signatures

```
GET  https://r.jina.ai/{url}
POST https://r.jina.ai/
POST https://r.jina.ai/{url}
```

**GET**: The target URL is embedded in the path after `r.jina.ai/`.  
**POST**: The URL can be sent in the path or as `url` in the request body (form or JSON). Sending via POST body is required for URLs containing `#` hash-based routing.

### Basic Usage Examples

```bash
# Convert a URL to Markdown (default content format)
curl https://r.jina.ai/https://en.wikipedia.org/wiki/Artificial_intelligence

# JSON response
curl -H "Accept: application/json" https://r.jina.ai/https://example.com

# Streaming mode (most complete result at end)
curl -H "Accept: text/event-stream" https://r.jina.ai/https://example.com

# POST with hash-based routing SPA
curl -X POST https://r.jina.ai/ -d 'url=https://example.com/#/route'

# Full-page screenshot
curl -H "X-Respond-With: screenshot" https://r.jina.ai/https://example.com
```

### Request Headers (complete list)

| Header | Type | Default | Description |
|---|---|---|---|
| `Accept` | string | `text/plain` | Response format: `text/plain`, `application/json`, `text/event-stream` |
| `Authorization` | string | — | `Bearer <token>` for authenticated requests |
| `X-Respond-With` | string | `content` | Output format (see CONTENT_FORMAT enum below) |
| `X-Cache-Tolerance` | integer | 3600 | Cache tolerance in seconds |
| `X-No-Cache` | boolean | false | Bypass cache entirely (equiv. `X-Cache-Tolerance: 0`) |
| `X-Wait-For-Selector` | string | — | CSS selector to wait for before returning |
| `X-Target-Selector` | string | — | CSS selector to extract content from |
| `X-Remove-Selector` | string | — | CSS selector of elements to remove |
| `X-Keep-Img-Data-Url` | boolean | false | Keep data URLs instead of converting to object URLs |
| `X-Proxy-Url` | string | — | Custom proxy URL (`http://`, `https://`, `socks4://`, `socks5://`) |
| `X-Proxy` | string | — | Use managed proxy (optional 2-letter country code) |
| `X-Robots-Txt` | string | — | Enforce robots.txt; optionally specify bot UA |
| `DNT` | `1` | — | Do-Not-Track: prevents caching of this request |
| `X-Set-Cookie` | string | — | Set cookies in the headless browser (Set-Cookie syntax) |
| `X-With-Generated-Alt` | boolean | false | Generate alt text for images missing alt via VLM |
| `X-With-Images-Summary` | boolean | false | Add dedicated images summary section |
| `X-With-Links-Summary` | boolean | false | Add dedicated links summary section |
| `X-Retain-Images` | string | `all` | Image retention: `all`, `none`, `alt`, `all_p`, `alt_p` |
| `X-With-Iframe` | boolean | false | Expand iframe contents into main document |
| `X-With-Shadow-Dom` | boolean | false | Expand shadow DOM contents |
| `X-User-Agent` | string | — | Override User-Agent sent to target site |
| `X-Timeout` | integer | — | Request timeout in seconds (max 180) |
| `X-Locale` | string | — | Browser locale (e.g. `en-US`, `zh-CN`) |
| `X-Referer` | string | — | Custom referer header |
| `X-Token-Budget` | integer | — | Reject if token cost would exceed this value |
| `X-Respond-Timing` | string | — | When to return (see RESPOND_TIMING enum below) |
| `X-Engine` | string | `auto` | Rendering engine: `browser`, `direct`/`curl`, `cf-browser-rendering` |
| `X-Base` | string | `initial` | Base URL for relative links: `initial` or `final` |
| `X-Md-Heading-Style` | string | — | Markdown heading style: `setext` or `atx` |
| `X-Md-Hr` | string | — | Markdown HR separator text |
| `X-Md-Bullet-List-Marker` | string | — | Bullet marker: `-`, `+`, or `*` |
| `X-Md-Em-Delimiter` | string | — | Italic delimiter: `_` or `*` |
| `X-Md-Strong-Delimiter` | string | — | Bold delimiter: `**` or `__` |
| `X-Md-Link-Style` | string | — | Link style: `inlined`, `referenced`, or `discarded` |
| `X-Md-Link-Reference-Style` | string | — | Reference style: `full`, `collapsed`, `shortcut`, or `discarded` |

### POST Body Parameters (additional, allowed only for POST)

When using `POST`, these parameters can be sent as `application/json` or `application/x-www-form-urlencoded`:

| Parameter | Type | Description |
|---|---|---|
| `url` | string | Target URL to crawl |
| `html` | string | Supply raw HTML instead of fetching a URL |
| `pdf` | string | Base64-encoded PDF content |
| `respondWith` | string | Same as `X-Respond-With` header |
| `targetSelector` | string/string[] | CSS selector(s) for content extraction |
| `waitForSelector` | string/string[] | CSS selector(s) to wait for |
| `removeSelector` | string/string[] | CSS selector(s) for elements to remove |
| `injectFrameScript` | string[] | Script URLs or inline scripts to inject into frames |
| `injectPageScript` | string[] | Script URLs or inline scripts to inject into main page |
| `viewport` | object | `{ width, height, deviceScaleFactor, isMobile, ... }` |
| `jsonSchema` | object | JSON Schema for structured extraction (used with `readerlm-v2`) |
| `instruction` | string | Natural language instruction (used with `readerlm-v2`) |

### Output Format (`X-Respond-With` / `respondWith`)

Controlled by the `CONTENT_FORMAT` enum (`src/dto/crawler-options.ts:8`):

```typescript
export enum CONTENT_FORMAT {
    CONTENT    = 'content',      // Default: Readability-extracted prose (Markdown)
    MARKDOWN   = 'markdown',     // Full-page Turndown Markdown (no Readability filter)
    HTML       = 'html',         // documentElement.outerHTML
    TEXT       = 'text',         // document.body.innerText
    PAGESHOT   = 'pageshot',     // Full-page screenshot URL (redirects to signed URL)
    SCREENSHOT = 'screenshot',   // Viewport screenshot URL
    VLM        = 'vlm',          // Gemini VLM-based markdown conversion
    READER_LM  = 'readerlm-v2', // Jina ReaderLM language model
}
```

Multiple formats can be combined (comma-separated or space-separated) and returned as a JSON or SSE bundle.

### Respond Timing (`X-Respond-Timing`)

Controlled by the `RESPOND_TIMING` enum (`src/dto/crawler-options.ts:26`):

```typescript
export enum RESPOND_TIMING {
    HTML             = 'html',             // Return raw unrendered HTML immediately
    VISIBLE_CONTENT  = 'visible-content',  // Return when any content becomes visible
    MUTATION_IDLE    = 'mutation-idle',    // Wait for DOM mutations to settle (0.2s idle)
    RESOURCE_IDLE    = 'resource-idle',    // Wait for non-media resources to finish
    MEDIA_IDLE       = 'media-idle',       // Wait for all resources including media
    NETWORK_IDLE     = 'network-idle',     // Full networkidle0 (most complete, slowest)
}
```

### JSON Response Structure (`FormattedPage`)

Defined at `src/services/snapshot-formatter.ts:22`:

```typescript
interface FormattedPage {
    title?: string;
    description?: string;
    url?: string;
    content?: string;         // Readability-extracted prose (Markdown)
    publishedTime?: string;   // Article published time (from Readability)
    html?: string;            // Raw HTML (when respondWith includes 'html')
    text?: string;            // Inner text (when respondWith includes 'text')
    screenshotUrl?: string;   // Signed URL to screenshot PNG
    screenshot?: Buffer;
    pageshotUrl?: string;     // Signed URL to full-page screenshot
    pageshot?: Buffer;
    links?: { [k: string]: string } | [string, string][];
    images?: { [k: string]: string } | [string, string][];
    warning?: string;
    usage?: { tokens?: number; };
}
```

---

## Search API (`s.jina.ai` / `SearcherHost`)

### Endpoint Signatures

```
GET  https://s.jina.ai/{query}
POST https://s.jina.ai/
GET  https://s.jina.ai/search?q={query}
POST https://s.jina.ai/search
```

Authentication is **required** for search (unlike crawl which allows anonymous use with rate limits).

### Basic Usage Examples

```bash
# Simple web search
curl -H "Authorization: Bearer jina_..." \
  "https://s.jina.ai/When%20was%20Jina%20AI%20founded"

# JSON response
curl -H "Authorization: Bearer jina_..." \
  -H "Accept: application/json" \
  "https://s.jina.ai/latest%20AI%20research"

# In-site search
curl -H "Authorization: Bearer jina_..." \
  "https://s.jina.ai/documentation?site=jina.ai"

# Search without fetching page content (titles/URLs only)
curl -H "Authorization: Bearer jina_..." \
  -H "X-Respond-With: no-content" \
  "https://s.jina.ai/my+query"

# Streaming search results
curl -H "Authorization: Bearer jina_..." \
  -H "Accept: text/event-stream" \
  "https://s.jina.ai/my+query"
```

### Search-Specific Query Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `q` | string | (path) | Search query (alternative to path encoding) |
| `count` / `num` | integer | 10 | Number of results to return (0–20) |
| `type` | string | `web` | Search type: `web`, `images`, `news` |
| `provider` | string | `google` | Search provider: `google` or `bing` |
| `gl` | string | — | Country code for geolocation (e.g., `us`, `gb`) |
| `hl` | string | — | Language code (e.g., `en`, `zh-cn`) |
| `location` | string | — | Location string for local search |
| `page` | integer | 1 | Result page number |
| `fallback` | boolean | true | Enable fallback to shorter queries if no results |
| `site` | string | — | Restrict to a specific domain (in-site search) |

All standard crawler headers (`X-Respond-With`, `X-Cache-Tolerance`, `X-Timeout`, etc.) are also accepted on search requests and apply to the individual page fetches.

The special `X-Respond-With: no-content` value returns search results without fetching page content (just title, URL, snippet).

### Search Response Structure

Each search result is a `FormattedPage` extended with:
```typescript
interface FormattedPage {
    title?: string;
    url?: string;           // URL Source
    description?: string;   // Search snippet/description
    content?: string;       // Full page content (Markdown)
    source?: string;        // Domain/source name
    date?: string;          // Publication date
    favicon?: string;       // Base64 data URL of favicon (when X-With-Favicons: true)
    imageUrl?: string;      // For image results
    imageWidth?: number;
    imageHeight?: number;
    siteLinks?: any[];
    usage?: { tokens?: number };
}
```

When `Accept: application/json`, returns an array of up to N `FormattedPage` objects.

---

## Key Classes and Their Interfaces

### `CrawlerHost` (`src/api/crawler.ts:76`)

The primary crawling controller. All methods except the RPC-decorated ones are available for internal use:

```typescript
class CrawlerHost extends RPCHost {
    // Core pipeline: yields PageSnapshot objects incrementally
    async *iterSnapshots(url: URL, crawlOpts?: ExtraScrappingOptions, crawlerOpts?: CrawlerOptions): AsyncGenerator<PageSnapshot | undefined>

    // Cache-aware scraping pipeline
    async *cachedScrap(url: URL, crawlOpts?: ExtraScrappingOptions, crawlerOpts?: CrawlerOptions): AsyncGenerator<PageSnapshot | undefined>

    // Parallel multi-URL scraping
    async *scrapMany(urls: URL[], options?: ExtraScrappingOptions, crawlerOpts?: CrawlerOptions): AsyncGenerator<(PageSnapshot | undefined)[]>

    // Simple one-shot crawl (waits for good-enough result)
    async simpleCrawl(mode: string, url: URL, opts?: ExtraScrappingOptions): Promise<FormattedPage>

    // Get the final (last) snapshot
    async getFinalSnapshot(url: URL, opts?: ExtraScrappingOptions, crawlerOptions?: CrawlerOptions): Promise<PageSnapshot | undefined>

    // Format a snapshot into the requested output format
    async formatSnapshot(crawlerOptions: CrawlerOptions, snapshot: PageSnapshot, nominalUrl?: URL, urlValidMs?: number, scrappingOptions?: ScrappingOptions): Promise<FormattedPage>

    // URL cache query
    async *queryCache(urlToCrawl: URL, cacheTolerance: number): AsyncGenerator<CacheEntry | undefined>

    // Store a snapshot in cache
    async setToCache(urlToCrawl: URL, snapshot: PageSnapshot): Promise<Crawled>

    // Configure ExtraScrappingOptions from CrawlerOptions
    async configure(opts: CrawlerOptions): Promise<ExtraScrappingOptions>
}
```

### `SearcherHost` (`src/api/searcher.ts:46`)

```typescript
class SearcherHost extends RPCHost {
    // Fetch and stream search results with content
    async *fetchSearchResults(mode: string, searchResults?: FormattedPage[], options?: ExtraScrappingOptions, crawlerOptions?: CrawlerOptions, count?: number): AsyncGenerator<FormattedPage[]>

    // Search with automatic fallback to shorter queries
    async searchWithFallback(params: SerperSearchQueryParams & { variant, provider? }, useFallback: boolean, noCache: boolean): Promise<{ results, query, tryTimes }>

    // Cached search query
    async cachedSearch(variant: 'web' | 'news' | 'images', query: Record<string, any>, noCache?: boolean): Promise<WebSearchEntry[]>

    // Reorganize results, prioritizing qualified pages
    reOrganizeSearchResults(searchResults: FormattedPage[], count?: number): FormattedPage[]
}
```

### `PuppeteerControl` (`src/services/puppeteer.ts`)

```typescript
interface PageSnapshot {
    title: string;
    description?: string;
    href: string;
    html: string;
    htmlSignificantlyModifiedByJs?: boolean;
    shadowExpanded?: string;    // Shadow DOM expansion
    text: string;
    status?: number;
    statusText?: string;
    parsed?: Partial<ReadabilityParsed> | null;
    screenshot?: Buffer;
    pageshot?: Buffer;
    imgs?: ImgBrief[];
    pdfs?: string[];           // URLs/paths to detected PDFs
    childFrames?: PageSnapshot[];
    isIntermediate?: boolean;  // True if more snapshots will follow
    isFromCache?: boolean;
    lastMutationIdle?: number;
}

interface ScrappingOptions {
    proxyUrl?: string;
    cookies?: Cookie[];
    favorScreenshot?: boolean;
    waitForSelector?: string | string[];
    minIntervalMs?: number;
    overrideUserAgent?: string;
    timeoutMs?: number;
    locale?: string;
    referer?: string;
    extraHeaders?: Record<string, string>;
    injectFrameScripts?: string[];
    injectPageScripts?: string[];
    viewport?: Viewport;
    proxyResources?: boolean;
    sideLoad?: { impersonate: { [url: string]: { status, body?, contentType } } };
}
```

### `ExtraScrappingOptions` (`src/api/crawler.ts:53`)

Extends `ScrappingOptions` with additional fields:
```typescript
interface ExtraScrappingOptions extends ScrappingOptions {
    withIframe?: boolean | 'quoted';
    withShadowDom?: boolean;
    targetSelector?: string | string[];
    removeSelector?: string | string[];
    keepImgDataUrl?: boolean;
    engine?: string;           // ENGINE_TYPE value
    allocProxy?: string;       // Proxy allocation hint/country
    private?: boolean;         // Disables caching
    countryHint?: string;      // GeoIP-derived country hint
}
```

### `SnapshotFormatter` (`src/services/snapshot-formatter.ts:76`)

```typescript
class SnapshotFormatter extends AsyncService {
    async formatSnapshot(mode: string, snapshot: PageSnapshot, nominalUrl?: URL, urlValidMs?: number): Promise<FormattedPage>

    async createSnapshotFromFile(url: URL, file: FancyFile, contentType: string, fileName?: string): Promise<PageSnapshot>
}
```

### `JSDomControl` (`src/services/jsdom.ts:16`)

```typescript
class JSDomControl extends AsyncService {
    // Apply selector-based narrowing to a snapshot
    async narrowSnapshot(snapshot: PageSnapshot | undefined, options?: ExtraScrappingOptions): Promise<PageSnapshot | undefined>

    // Analyze HTML for token count and title (fast, no full parse)
    async analyzeHTMLTextLite(html: string): Promise<{ tokens: number; title?: string }>

    // Strip non-content elements for LM consumption
    async cleanHTMLforLMs(html: string, removeSelectorStr?: string): Promise<string>
}
```

---

## Configuration Options and Extension Points

### `CrawlerOptions` DTO (`src/dto/crawler-options.ts:284`)

The `CrawlerOptions` class (from `civkit`'s `AutoCastable`) is the single source of truth for all request configuration. Key methods on instances:

```typescript
class CrawlerOptions extends AutoCastable {
    respondWith: string;            // CONTENT_FORMAT value(s)
    withGeneratedAlt: boolean;
    retainImages?: string;          // IMAGE_RETENTION_MODES
    withLinksSummary: boolean;
    withImagesSummary: boolean;
    noCache: boolean;
    cacheTolerance?: number;        // Seconds
    targetSelector?: string[];
    waitForSelector?: string[];
    removeSelector?: string[];
    proxy?: string;                 // 'none' | country code | 'country+'
    proxyUrl?: string;
    setCookies?: Cookie[];
    engine?: string;                // ENGINE_TYPE
    respondTiming?: string;         // RESPOND_TIMING
    timeout?: number;               // Seconds
    locale?: string;
    viewport?: Viewport;
    doNotTrack?: boolean;
    robotsTxt?: string;
    tokenBudget?: number;
    base?: 'initial' | 'final';
    markdown?: TurnDownTweakableOptions;
    injectFrameScript?: string[];
    injectPageScript?: string[];
    noGfm?: boolean;
    jsonSchema?: object;
    instruction?: string;

    // Helper methods
    isCacheQueryApplicable(): boolean
    isSnapshotAcceptableForEarlyResponse(snapshot: PageSnapshot): boolean
    browserIsNotRequired(): boolean
    isRequestingCompoundContentFormat(): boolean
}
```

### Integration Patterns

**Pattern 1: Simple programmatic crawl**
```typescript
import { container } from 'tsyringe';
import { CrawlerHost } from './src/api/crawler';
import { CrawlerOptions } from './src/dto/crawler-options';

const crawler = container.resolve(CrawlerHost);
await crawler.serviceReady();

const result = await crawler.simpleCrawl(
    'markdown',
    new URL('https://example.com'),
    { timeoutMs: 30_000 }
);
console.log(result.content);
```

**Pattern 2: Streaming snapshots**
```typescript
const crawlerOptions = CrawlerOptions.from({ respondWith: 'content' });
const crawlOpts = await crawler.configure(crawlerOptions);

for await (const snapshot of crawler.iterSnapshots(new URL('https://example.com'), crawlOpts, crawlerOptions)) {
    if (snapshot?.parsed?.content) {
        console.log('Got content:', snapshot.parsed.content.slice(0, 200));
    }
}
```

**Pattern 3: Parallel multi-URL crawl**
```typescript
const urls = [
    new URL('https://example.com'),
    new URL('https://another.com'),
];
for await (const snapshots of crawler.scrapMany(urls, crawlOpts, crawlerOptions)) {
    for (const [i, snap] of snapshots.entries()) {
        if (snap?.title) console.log(`${i}: ${snap.title}`);
    }
}
```

**Pattern 4: Custom HTML input (no network fetch)**
```typescript
const crawlerOptions = CrawlerOptions.from({
    respondWith: 'markdown',
    html: '<html><body><h1>Hello</h1><p>World</p></body></html>',
});
// Pass a fake URL as identifier
for await (const snap of crawler.cachedScrap(new URL('https://example.com/fake'), {}, crawlerOptions)) {
    if (snap) {
        const formatted = await crawler.formatSnapshot(crawlerOptions, snap, new URL('https://example.com/fake'));
        console.log(formatted.content);
    }
}
```

### Output Server Event Stream (`src/lib/transform-server-event-stream.ts`)

`OutputServerEventStream` is the SSE stream class used for streaming responses:
```typescript
const stream = new OutputServerEventStream();
stream.write({ event: 'data', data: formattedPage });
stream.write({ event: 'error', data: { message: '...' } });
stream.end();
```

### Search Provider Interface (`src/services/serp/compat.ts`)

All search providers conform to `WebSearchEntry`:
```typescript
interface WebSearchEntry {
    title: string;
    link: string;
    snippet?: string;
    // Provider-specific additional fields
}
```

Providers implement `webSearch()`, `imageSearch()`, and `newsSearch()` methods and are selected in `SearcherHost.iterProviders()`.
