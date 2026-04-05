# Markdowner — Repository Summary

## Repository Purpose and Goals

Markdowner (`dhravya/markdowner`) is a fast, open-source tool that converts any website into LLM-ready markdown data. It was created as an alternative to proprietary solutions like Jina Reader (`r.jina.ai`) and Firecrawl, which are either expensive, limited, or difficult to self-host. The primary motivation is to produce clean, structured markdown output so that LLM queries over web content yield better, more accurate responses.

The project powers the Supermemory AI application, where users store website content and query it with AI. By normalizing ingested web content into predictable markdown format, the system improves LLM response quality significantly.

## Key Features and Capabilities

- **Website-to-Markdown Conversion**: Fetches any URL and converts its HTML into clean markdown using Mozilla Readability (for article extraction) and Turndown (for HTML-to-Markdown conversion).
- **Detailed Response Mode**: When `enableDetailedResponse=true`, converts the full document HTML (minus scripts, styles, iframes, and noscript elements) instead of just the article body.
- **Subpage Crawler**: With `crawlSubpages=true`, discovers and crawls up to 10 internal subpages of a given domain, returning an array of markdown results.
- **LLM Filtering**: Optional post-processing step (`llmFilter=true`) that passes the raw markdown through Cloudflare's AI (`@cf/qwen/qwen1.5-14b-chat-awq`) to remove ads, irrelevant content, and noise — producing a cleaner, denser output.
- **Twitter/X.com Special Handling**: Detects Twitter/X URLs, fetches tweet data from the Twitter syndication API, and formats tweet text, images, timestamps, likes, and retweets into a structured markdown string.
- **KV Caching**: All converted pages are cached in Cloudflare KV (`MD_CACHE`) with a 1-hour TTL, preventing redundant browser launches and reducing latency.
- **Rate Limiting**: Built-in rate limiter (10 requests per 60 seconds per IP) protects the service from abuse; bypassed by requests carrying a valid `BACKEND_SECURITY_TOKEN`.
- **Dual Response Formats**: Returns plain text or JSON depending on the `Content-Type` request header (`text/plain` vs `application/json`).
- **Self-Hostable**: Designed for straightforward deployment to Cloudflare Workers — clone, install, create KV namespace, update `wrangler.toml`, and deploy.

## Primary Use Cases and Target Audience

**Use cases:**
- Feeding clean website content to LLMs for summarization, Q&A, and retrieval-augmented generation (RAG) pipelines.
- Archiving web content in a structured, queryable format for AI memory applications.
- Bulk crawling documentation sites or knowledge bases for ingestion into vector databases.
- Extracting tweet content in a machine-readable format.

**Target audience:**
- AI application developers building RAG systems, chatbots, or knowledge bases over web content.
- Developers building tools similar to Supermemory that require structured web content ingestion.
- Teams wanting a self-hosted alternative to Jina Reader or Firecrawl.

## High-Level Architecture Overview

Markdowner is a **Cloudflare Workers** application with three main layers:

1. **Worker Entry Point** (`src/index.ts` — default export `fetch` function): Receives HTTP requests, enforces rate limiting, and routes all requests to the `Browser` Durable Object by looking up (or creating) a singleton browser instance via `env.BROWSER.idFromName('browser')`.

2. **Browser Durable Object** (`Browser` class in `src/index.ts`): A Cloudflare Durable Object that maintains a long-lived Puppeteer browser session (kept alive for up to 60 seconds of inactivity via alarms). It handles:
   - Parsing and validating query parameters (`url`, `enableDetailedResponse`, `crawlSubpages`, `llmFilter`).
   - Launching/reconnecting a browser via `@cloudflare/puppeteer`.
   - Fetching pages and running in-browser JavaScript to invoke Readability and Turndown.
   - Caching results in Cloudflare KV.
   - Optional LLM post-processing via Cloudflare AI.

3. **Help Response** (`src/response.ts`): A static HTML page served when no `url` parameter is provided, containing a usage UI and documentation.

**Cloudflare services used:**
- **Browser Rendering API** (`MYBROWSER` binding) — headless browser execution
- **Durable Objects** (`BROWSER` binding) — stateful, persistent browser session management
- **KV Namespace** (`MD_CACHE`) — caching of converted pages
- **Rate Limiting** (`RATELIMITER`) — 10 req/60s per IP
- **Workers AI** (`AI`) — optional LLM filtering via `@cf/qwen/qwen1.5-14b-chat-awq`

## Related Projects and Dependencies

- **[Supermemory](https://git.new/memory)** — the AI app that Markdowner was originally built to serve.
- **[@cloudflare/puppeteer](https://developers.cloudflare.com/browser-rendering/)** — Cloudflare's Puppeteer integration for headless browser rendering within Workers.
- **[Mozilla Readability](https://github.com/mozilla/readability)** — dynamically loaded inside the browser page (`https://unpkg.com/@mozilla/readability/Readability.js`) to extract article content.
- **[Turndown](https://github.com/mixmark-io/turndown)** — dynamically loaded inside the browser page (`https://unpkg.com/turndown/dist/turndown.js`) to convert HTML to Markdown.
- **[react-tweet](https://github.com/vercel/react-tweet)** — provides the `Tweet` TypeScript type for Twitter syndication API responses.
- **[Wrangler](https://github.com/cloudflare/workers-sdk)** — Cloudflare's CLI toolchain used for development, type generation, and deployment.
- **[Jina Reader](https://r.jina.ai)** / **[Firecrawl](https://firecrawl.dev)** — proprietary alternatives that Markdowner was designed to replace.
