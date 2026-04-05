# Markdowner — APIs and Interfaces

## Public API Entry Points

Markdowner exposes a single HTTP endpoint (the deployed Cloudflare Worker URL). The public instance is at `https://md.dhr.wtf`, but self-hosted instances will have their own URL.

### Base Endpoint

```
GET /?url=<target-url>[&enableDetailedResponse=true][&crawlSubpages=true][&llmFilter=true]
```

All interactions are HTTP GET requests. No POST, PUT, PATCH, or DELETE methods are supported (returns `405 Method Not Allowed`).

---

## API Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | string | The full URL to convert into markdown. Must start with `http://` or `https://`. |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enableDetailedResponse` | boolean | `false` | When `true`, converts the full document HTML (minus scripts/styles/iframes/noscript) instead of just the article-extracted content. Produces more verbose output that includes navigation, headers, and other non-article elements. |
| `crawlSubpages` | boolean | `false` | When `true`, navigates to the base URL, extracts up to 10 internal links (same domain), and converts all of them. **Requires JSON content type** (`Content-Type: application/json`). |
| `llmFilter` | boolean | `false` | When `true`, passes the raw markdown through `@cf/qwen/qwen1.5-14b-chat-awq` to remove ads, irrelevant content, and noise. Consumes 60 additional rate limit tokens per request. |

### Request Headers

| Header | Values | Description |
|--------|--------|-------------|
| `Content-Type` | `text/plain` (default) or `application/json` | Controls response format |
| `Authorization` | `Bearer <BACKEND_SECURITY_TOKEN>` | Optional. Bypasses rate limiting entirely for trusted backend callers. |

---

## Response Formats

### Text Response (default, `Content-Type: text/plain`)

Returns raw markdown as a plain string body.

```bash
curl 'https://md.dhr.wtf/?url=https://example.com'
```

**Response:**
```
Example Domain
==============

This domain is for use in illustrative examples in documents...
```

### JSON Response (`Content-Type: application/json`)

Returns a JSON array of objects, each with `url` and `md` properties.

```bash
curl 'https://md.dhr.wtf/?url=https://example.com' \
  -H 'Content-Type: application/json'
```

**Response:**
```json
[
  {
    "url": "https://example.com",
    "md": "Example Domain\n==============\n\nThis domain is for use..."
  }
]
```

### Subpage Crawl Response (always JSON)

Crawling subpages always returns a JSON array regardless of `Content-Type` header.

```bash
curl 'https://md.dhr.wtf/?url=https://docs.example.com&crawlSubpages=true' \
  -H 'Content-Type: application/json'
```

**Response:**
```json
[
  { "url": "https://docs.example.com/", "md": "..." },
  { "url": "https://docs.example.com/getting-started", "md": "..." },
  { "url": "https://docs.example.com/api", "md": "..." }
]
```

### No URL Response (Help Page)

When no `url` parameter is provided, returns an HTML help page (`Content-Type: text/html;charset=UTF-8`) with a UI form and documentation.

---

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `400` | Bad request — invalid URL, or `crawlSubpages=true` without JSON content type |
| `405` | Method Not Allowed — non-GET request |
| `429` | Rate limit exceeded (also embedded as `md: "Rate limit exceeded"` in JSON responses) |
| `500` | Could not start browser instance |

---

## Key Classes and Functions

### Worker Default Export (`src/index.ts:5–21`)

```typescript
export default {
    async fetch(request: Request, env: Env)
}
```

**Behavior:**
1. Reads `cf-connecting-ip` header for rate limit key.
2. Checks `Authorization: Bearer <token>` against `env.BACKEND_SECURITY_TOKEN`.
3. If unauthorized, calls `env.RATELIMITER.limit({ key: ip })`.
4. Forwards request to Browser Durable Object: `env.BROWSER.idFromName('browser')`.

---

### `Browser` Class — Durable Object (`src/index.ts:26–341`)

#### `fetch(request: Request)` — `src/index.ts:45`

Main request dispatcher inside the Durable Object.

```typescript
async fetch(request: Request): Promise<Response>
```

Parses query parameters, validates inputs, and dispatches to:
- `this.crawlSubpages(url, enableDetailedResponse, contentType)` — when `crawlSubpages=true`
- `this.processSinglePage(url, enableDetailedResponse, contentType)` — otherwise

**Validation errors returned:**
- `405` if not GET
- `400` if `crawlSubpages=true` without JSON content type
- `400` if URL is invalid
- `500` if browser can't start

---

#### `ensureBrowser()` — `src/index.ts:83`

```typescript
async ensureBrowser(): Promise<boolean>
```

Ensures a live Puppeteer browser connection exists. Retries up to 3 times on failure, closing stale sessions between retries.

```typescript
this.browser = await puppeteer.launch(this.env.MYBROWSER);
```

---

#### `getWebsiteMarkdown(options)` — `src/index.ts:183`

Core orchestration method. Processes one or more URLs concurrently.

```typescript
async getWebsiteMarkdown({
    urls: string[];
    enableDetailedResponse: boolean;
    classThis: Browser;
    env: Env;
}): Promise<Array<{ url: string; md: string }>>
```

**Flow for each URL:**
1. Check rate limit (if not using backend token).
2. Build cache key: `url + ('-detailed' if detailed) + ('-llm' if llmFilter)`.
3. Check `env.MD_CACHE.get(id)` — return cached result if found.
4. If Twitter/X URL: call `getTweet(tweetID)` and format result.
5. Otherwise: call `fetchAndProcessPage(url, enableDetailedResponse)`.
6. If `llmFilter=true`: run through `@cf/qwen/qwen1.5-14b-chat-awq` via `env.AI.run(...)`.
7. Write result to `env.MD_CACHE.put(id, md, { expirationTtl: 3600 })`.
8. Return `{ url, md }`.

---

#### `fetchAndProcessPage(url, enableDetailedResponse)` — `src/index.ts:267`

```typescript
async fetchAndProcessPage(
    url: string,
    enableDetailedResponse: boolean
): Promise<string>
```

Opens a new browser page, navigates with `waitUntil: 'networkidle0'`, then runs:

```javascript
// Inside page.evaluate():
// 1. Injects Readability.js and Turndown.js as script tags
// 2. Waits for both scripts to load
// 3. Creates a Readability instance:
const reader = new Readability(document.cloneNode(true), {
    charThreshold: 0,
    keepClasses: true,
    nbTopCandidates: 500,
});
const article = reader.parse();

// 4. Creates a TurndownService instance
const turndownService = new TurndownService();

// 5. For detailed mode: clones document, removes script/style/iframe/noscript
// 6. Converts to markdown:
const markdown = turndownService.turndown(
    enableDetailedResponse ? documentWithoutScripts : article.content
);
```

Returns the markdown string. Closes the page after conversion.

---

#### `crawlSubpages(baseUrl, enableDetailedResponse, contentType)` — `src/index.ts:112`

```typescript
async crawlSubpages(
    baseUrl: string,
    enableDetailedResponse: boolean,
    contentType: string
): Promise<Response>
```

1. Opens a page and navigates to `baseUrl`.
2. Calls `extractLinks(page, baseUrl)` to collect all same-domain links.
3. Deduplicates and limits to first 10 links.
4. Calls `getWebsiteMarkdown({ urls: uniqueLinks, ... })`.
5. Returns JSON array response.

---

#### `extractLinks(page, baseUrl)` — `src/index.ts:154`

```typescript
async extractLinks(
    page: puppeteer.Page,
    baseUrl: string
): Promise<string[]>
```

Runs `page.evaluate()` to collect all `<a href>` links starting with `baseUrl`.

---

#### `getTweet(tweetID)` — `src/index.ts:162`

```typescript
async getTweet(tweetID: string): Promise<Tweet>
```

Fetches tweet data from the Twitter syndication API:
```
https://cdn.syndication.twimg.com/tweet-result?id=<tweetID>&lang=en&features=...
```

Returns a `Tweet` object with fields: `text`, `user`, `photos`, `created_at`, `favorite_count`, `conversation_count`.

The formatted markdown output includes:
```
Tweet from @<username>

<tweet text>
Images: <url>, <url>
Time: <created_at>, Likes: <count>, Retweets: <count>

raw: <full JSON>
```

---

#### `alarm()` — `src/index.ts:330`

```typescript
async alarm(): Promise<void>
```

Durable Object alarm handler. Called every 10 seconds via `storage.setAlarm()`. Increments `keptAliveInSeconds` by 10. When it reaches 60, closes the browser and sets `this.browser = undefined`.

---

#### `isValidUrl(url)` — `src/index.ts:326`

```typescript
isValidUrl(url: string): boolean
```

Validates using: `/^(http|https):\/\/[^ "]+$/.test(url)`

---

## Environment Interface (`worker-configuration.d.ts`)

```typescript
interface Env {
    BROWSER: DurableObjectNamespace;         // Browser Durable Object
    MYBROWSER: BrowserWorker;               // Browser Rendering API
    MD_CACHE: KVNamespace;                  // Cache for converted pages
    RATELIMITER: any;                       // Rate limiter binding
    AI: Ai;                                 // Workers AI binding
    BACKEND_SECURITY_TOKEN: string;         // Token for bypassing rate limits
}
```

---

## Integration Patterns and Workflows

### Basic Webpage to Markdown

```bash
# Plain text response
curl 'https://md.dhr.wtf/?url=https://blog.example.com/post'

# JSON response
curl 'https://md.dhr.wtf/?url=https://blog.example.com/post' \
  -H 'Content-Type: application/json'
```

### Full Site Crawl

```bash
curl 'https://md.dhr.wtf/?url=https://docs.example.com&crawlSubpages=true' \
  -H 'Content-Type: application/json'
# Returns up to 10 pages as JSON array
```

### Clean LLM-Ready Content

```bash
# Remove ads and noise via AI filtering
curl 'https://md.dhr.wtf/?url=https://news.example.com/article&llmFilter=true'
```

### Full Document (Not Article-Only)

```bash
# Include navigation, headers, etc.
curl 'https://md.dhr.wtf/?url=https://example.com&enableDetailedResponse=true'
```

### Twitter/X Handling

```bash
# Converts tweet to structured markdown
curl 'https://md.dhr.wtf/?url=https://x.com/user/status/1234567890'
```

### Backend Integration (Bypass Rate Limiting)

```bash
curl 'https://md.dhr.wtf/?url=https://example.com' \
  -H 'Authorization: Bearer <BACKEND_SECURITY_TOKEN>'
```

### Python Integration Example

```python
import httpx

def url_to_markdown(url: str, detailed: bool = False, json_format: bool = False) -> str | list:
    params = {"url": url}
    if detailed:
        params["enableDetailedResponse"] = "true"
    
    headers = {}
    if json_format:
        headers["Content-Type"] = "application/json"
    
    resp = httpx.get("https://md.dhr.wtf/", params=params, headers=headers)
    resp.raise_for_status()
    
    if json_format:
        return resp.json()
    return resp.text
```

---

## Configuration Options and Extension Points

### Rate Limiting Configuration

Configured in `wrangler.toml` via the `[[unsafe.bindings]]` block:
```toml
[[unsafe.bindings]]
name = "RATELIMITER"
type = "ratelimit"
namespace_id = "1002"
simple = { limit = 10, period = 60 }
```
Change `limit` and `period` to adjust the rate limit window.

### KV Cache TTL

The cache expiration is hardcoded at 3600 seconds (1 hour) in `src/index.ts:261`:
```typescript
await env.MD_CACHE.put(id, md, { expirationTtl: 3600 });
```
To change the TTL, modify this value before deploying.

### Browser Keep-Alive Duration

```typescript
const KEEP_BROWSER_ALIVE_IN_SECONDS = 60;  // src/index.ts:23
const TEN_SECONDS = 10000;                  // src/index.ts:24
```

Adjust `KEEP_BROWSER_ALIVE_IN_SECONDS` to control how long the browser stays alive between requests.

### LLM Model Selection

The LLM filter uses `@cf/qwen/qwen1.5-14b-chat-awq` (hardcoded in `src/index.ts:247`):
```typescript
await env.AI.run('@cf/qwen/qwen1.5-14b-chat-awq', { prompt: `...` })
```
Replace with any model ID available in Cloudflare Workers AI.

### Subpage Crawl Limit

The maximum number of subpages is hardcoded to 10 in `src/index.ts:118`:
```typescript
const uniqueLinks = Array.from(new Set(links)).splice(0, 10);
```

### Readability Configuration

In `fetchAndProcessPage` (`src/index.ts:287`):
```typescript
const reader = new Readability(document.cloneNode(true), {
    charThreshold: 0,
    keepClasses: true,
    nbTopCandidates: 500,
});
```
These options can be tuned for different content types.
