# Markdowner — Code Structure

## Annotated Directory Tree

```
markdowner/
├── src/
│   ├── index.ts                  # Main worker entry point + Browser Durable Object
│   └── response.ts               # Static HTML help page template
├── .editorconfig                 # Editor formatting rules (tabs, LF, UTF-8)
├── .gitignore                    # Git ignore rules
├── .prettierrc                   # Prettier formatting configuration
├── code_of_conduct.md            # Project code of conduct
├── LICENSE                       # License file
├── package.json                  # npm package manifest and scripts
├── README.md                     # Project documentation and usage guide
├── tsconfig.json                 # TypeScript compiler configuration
├── worker-configuration.d.ts     # Auto-generated Cloudflare bindings types + Tweet types
└── wrangler.toml                 # Cloudflare Workers deployment configuration
```

## Module and Package Organization

The codebase is extremely lean — only two TypeScript source files. All application logic lives in `src/index.ts`, with the HTML help UI templated in `src/response.ts`.

There is no dedicated test directory or test files. No separate utility modules, no subdirectory groupings. The entire worker logic is one cohesive file, consistent with the single-purpose nature of the service.

## Main Source Directories and Their Purposes

### `src/`

The sole source directory. Contains:

- **`src/index.ts`** — The entire application logic:
  - The Cloudflare Worker default export (`fetch` handler)
  - The `Browser` Durable Object class with all methods
- **`src/response.ts`** — A single exported constant (`html`) containing a Tailwind CSS–styled HTML page rendered as the landing/help screen when no `url` parameter is provided.

## Key Files and Their Roles

### `src/index.ts`

The primary and most critical file. Contains two exported items:

#### Default Export — Worker Fetch Handler
```typescript
export default {
    async fetch(request: Request, env: Env) { ... }
}
```
- Reads the client IP from `cf-connecting-ip` header.
- Checks `Authorization: Bearer <token>` against `env.BACKEND_SECURITY_TOKEN` — if missing/wrong, applies rate limiting.
- Routes the request to the singleton `Browser` Durable Object (`env.BROWSER.idFromName('browser')`).

#### `Browser` Class — Durable Object
The stateful worker class that manages a persistent Puppeteer browser session. Key properties:
- `state: DurableObjectState` — Durable Object state accessor
- `env: Env` — Cloudflare environment bindings
- `keptAliveInSeconds: number` — tracks idle time for auto-shutdown
- `storage: DurableObjectStorage` — persistent key-value storage for alarm scheduling
- `browser: puppeteer.Browser | undefined` — the active Puppeteer browser instance
- `llmFilter: boolean` — whether LLM filtering is enabled for the current request
- `token: string` — auth token from current request

**Methods:**

| Method | Lines | Purpose |
|--------|-------|---------|
| `constructor(state, env)` | 36–43 | Initializes Durable Object state |
| `fetch(request)` | 45–81 | Main request handler — parses params, validates URL, dispatches to processSinglePage or crawlSubpages |
| `ensureBrowser()` | 83–110 | Launches or reconnects Puppeteer, retries up to 3 times, cleaning stale sessions |
| `crawlSubpages(baseUrl, enableDetailedResponse, contentType)` | 112–131 | Navigates to base URL, extracts up to 10 internal links, calls `getWebsiteMarkdown` in parallel |
| `processSinglePage(url, enableDetailedResponse, contentType)` | 134–152 | Processes a single URL and returns text or JSON response |
| `extractLinks(page, baseUrl)` | 154–160 | Runs `page.evaluate` to collect all `<a href>` links that start with the base URL |
| `getTweet(tweetID)` | 162–181 | Fetches tweet JSON from `cdn.syndication.twimg.com` with browser-like headers |
| `getWebsiteMarkdown({urls, enableDetailedResponse, classThis, env})` | 183–265 | Core orchestration: checks cache, handles Twitter URLs, fetches and processes pages, optionally applies LLM filter, writes to KV cache |
| `fetchAndProcessPage(url, enableDetailedResponse)` | 267–318 | Opens a new browser page, navigates to URL, runs in-browser JS to load Readability + Turndown and convert to markdown |
| `buildHelpResponse()` | 320–324 | Returns the HTML help page |
| `isValidUrl(url)` | 326–328 | Validates URL starts with `http://` or `https://` using a regex |
| `alarm()` | 330–341 | Cloudflare Durable Object alarm handler — increments idle timer, closes browser after 60 seconds of inactivity |

**Key constants:**
- `KEEP_BROWSER_ALIVE_IN_SECONDS = 60` — browser auto-closes after 60s idle
- `TEN_SECONDS = 10000` — alarm poll interval in milliseconds

### `src/response.ts`

Exports a single string constant `html` — a fully self-contained HTML page with:
- Tailwind CSS (loaded from CDN)
- A URL input form with a "Convert to Markdown" button
- Inline JavaScript (`redirectToMD`) that redirects to `/?url=<input>&enableDetailedResponse=true`
- Documentation sections for required parameters, optional parameters, and response types

Also contains commented-out plain-text documentation of the API (lines 97–115) for easy reference.

### `worker-configuration.d.ts`

Auto-generated by `wrangler types` (`npm run cf-typegen`). Defines:
- `Env` interface — all Cloudflare binding types:
  - `BROWSER: DurableObjectNamespace` — the Browser Durable Object namespace
  - `MYBROWSER: BrowserWorker` — the Browser Rendering API binding
  - `MD_CACHE: KVNamespace` — the KV cache namespace
  - `RATELIMITER: any` — the rate limiter binding
  - `AI: Ai` — Cloudflare Workers AI binding
  - `BACKEND_SECURITY_TOKEN: string` — secret for bypassing rate limits
- `TweetBase` interface — base tweet shape from Twitter syndication API
- `Tweet` interface — full tweet object (extends `TweetBase`) with photos, video, quoted tweets, etc.
- `declare const Readability`, `TurndownService`, `document` — ambient declarations allowing the in-page evaluation code to reference browser globals without TypeScript errors

### `wrangler.toml`

Cloudflare Workers deployment manifest:
- `name = "markdowner"` — worker name
- `main = "src/index.ts"` — entry point
- `compatibility_date = "2023-09-04"` — Workers runtime compatibility date
- `compatibility_flags = ["nodejs_compat"]` — enables Node.js compatibility layer
- `browser = { binding = "MYBROWSER" }` — Browser Rendering API
- `[[durable_objects.bindings]]` — maps `BROWSER` to the `Browser` class
- `[[migrations]]` — Durable Object migration tagged `v1`
- `[[kv_namespaces]]` — `MD_CACHE` bound to KV namespace ID `3186489f943d409a9b772d876a58a73e`
- `[[unsafe.bindings]]` — `RATELIMITER` with `{ limit: 10, period: 60 }`
- `[ai]` — Workers AI `AI` binding

### `package.json`

Minimal npm manifest:
- `name: "browser-rendering"` (internal package name, not the public-facing name)
- `version: "0.0.0"`
- `private: true`
- Scripts: `deploy` (wrangler deploy), `dev`/`start` (wrangler dev), `cf-typegen` (wrangler types)
- Dev dependencies: `@cloudflare/workers-types`, `typescript`, `wrangler`

### `tsconfig.json`

TypeScript configuration:
- `target: "es2021"`, `module: "es2022"`
- `types: ["@cloudflare/workers-types"]` — global Cloudflare type injection
- `strict: true` — all strict checks enabled
- `noEmit: true` — TypeScript used for type checking only; Wrangler handles compilation
- `jsx: "react"` — JSX support (for `react-tweet` types)
- `moduleResolution: "node"`

## Code Organization Patterns

### Durable Object Pattern
The architecture follows the standard Cloudflare Durable Objects pattern: the stateless Worker entry point acts as a thin router that delegates all stateful work to a single named Durable Object instance (`idFromName('browser')`). This ensures a single, persistent browser session across requests rather than spinning up a new browser for every request.

### In-Browser Script Injection Pattern
Rather than bundling Readability and Turndown as server-side dependencies, the code dynamically injects script tags into the rendered page and executes `page.evaluate()` to run conversion logic inside the browser context. This allows the full browser DOM to be available to Readability (which relies on `document`) and avoids complex Node.js/Worker compatibility issues with these libraries.

### Cache-Aside Pattern
Every page conversion checks `env.MD_CACHE.get(id)` before processing. The cache key combines the URL with flags (`-detailed`, `-llm`) to differentiate variants. Results are written back with a 1-hour TTL. Twitter content uses the tweet ID as the cache key.

### Promise.all Parallelism
The `getWebsiteMarkdown` method processes all URLs concurrently using `Promise.all(urls.map(...))`, enabling efficient multi-page crawling even for up to 10 subpages.

### Alarm-Based Lifecycle Management
Browser idle time is tracked via `keptAliveInSeconds`, reset on each request. The Durable Object alarm fires every 10 seconds to increment this counter. After 60 seconds of inactivity the browser is closed and `this.browser` is set to `undefined`, allowing garbage collection while keeping the Durable Object alive for future requests.
