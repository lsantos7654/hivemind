# Jina Reader — Summary

## Repository Purpose and Goals

Jina Reader (`jina-ai/reader`) is the open-source codebase behind the production services at `https://r.jina.ai` (URL-to-LLM-friendly-content conversion) and `https://s.jina.ai` (web search with full-content retrieval). Its stated goal is to give LLMs and AI agents "better input" by transforming arbitrary web content — HTML pages, PDFs, SPAs, shadow-DOM-heavy sites — into clean, structured Markdown that downstream models can reason over effectively.

Every commit is deployed directly to the live `r.jina.ai` endpoint, making this the single authoritative production codebase.

## Key Features and Capabilities

- **URL-to-Markdown conversion (`r.jina.ai`)**: Accepts any URL and returns LLM-friendly Markdown. Handles JavaScript-rendered SPAs via a headless Chromium/Puppeteer pipeline, falls back to a fast `libcurl`-based side-loader when browser rendering is unnecessary, and supports a Cloudflare Browser Rendering engine as a third option.
- **PDF extraction**: Reads arbitrary PDFs from any URL (or uploaded base64-encoded PDFs) using `pdfjs-dist`, extracting structured text with layout-aware heuristics.
- **Web search (`s.jina.ai`)**: Accepts a natural-language query, searches via Serper (Google/Bing), fetches and converts the top N results with the same reader pipeline, and returns them in a single structured response.
- **Streaming mode**: Supports `text/event-stream` (`Accept: text/event-stream`) for incremental delivery. Each subsequent event carries more complete content; the last event is the most accurate.
- **Multiple output formats**: `content` (default, Mozilla Readability-extracted prose), `markdown` (full-page Turndown conversion), `html` (raw DOM), `text` (inner text), `screenshot` (PNG URL), `pageshot` (full-page screenshot), `readerlm-v2` (processed by Jina's in-house ReaderLM language model), and combinations thereof.
- **Image alt-text generation**: When `X-With-Generated-Alt: true` is set, images without alt text are captioned by a VLM (Vertex Gemini) and embedded as Markdown alt attributes, enabling text-only LLMs to incorporate images into reasoning.
- **Caching layer**: Results are cached in Firebase Firestore (metadata) and Firebase Cloud Storage (snapshot files, screenshots). Cache lifetime is 1 hour for freshness; records are retained for 7 days. The `X-Cache-Tolerance` and `X-No-Cache` headers control cache behavior.
- **Rate limiting and metering**: Token-based billing with per-UID and per-IP rate limiting. Anonymous users are limited to 20 requests/minute; authenticated users are limited by tier policy.
- **Robots.txt enforcement**: Optional `X-Robots-Txt` header causes the service to fetch and respect the target site's `robots.txt`.
- **Anti-abuse domain blockades**: Domains exhibiting abusive behavior (e.g., CAPTCHA loops, excessive redirects) are automatically blocked for configurable periods and stored in Firestore.
- **Proxy support**: Built-in managed proxy pool (`X-Proxy` header) and custom proxy pass-through (`X-Proxy-Url`), with GeoIP-based country selection.
- **CSS selector targeting**: `X-Target-Selector` and `X-Wait-For-Selector` headers allow precise content extraction from complex pages, including waiting for dynamic content to appear.
- **Shadow DOM and iframe expansion**: Optional inclusion of shadow-DOM content and iframe content via `X-With-Shadow-Dom` / `X-With-Iframe`.
- **Markdown customization**: Full Turndown option pass-through (`X-Md-Heading-Style`, `X-Md-Hr`, `X-Md-Bullet-List-Marker`, etc.).

## Primary Use Cases and Target Audience

- **AI agent and RAG pipeline developers** who need clean, token-efficient content from arbitrary URLs instead of raw HTML.
- **LLM application builders** implementing web grounding — using `s.jina.ai` to give LLMs up-to-date world knowledge.
- **Self-hosters** running their own Reader instance via Docker for private or high-volume use cases.
- **Researchers** studying HTML-to-Markdown pipelines, PDF extraction at scale, or browser automation at production quality.

## High-Level Architecture Overview

The system is a Node.js/TypeScript HTTP service built on the **Koa** web framework with an RPC abstraction layer provided by the internal `civkit` library. Dependency injection uses **tsyringe** with the `@singleton()` pattern throughout.

Two primary API controllers handle requests:
- `CrawlerHost` (`src/api/crawler.ts`) — handles all `r.jina.ai`-style URL crawling.
- `SearcherHost` (`src/api/searcher.ts`) — handles all `s.jina.ai`-style search queries, delegating individual URL fetching to `CrawlerHost`.

Behind these controllers, a layered rendering pipeline operates:
1. **curl side-loader** (`CurlControl`) — fast first-pass HTTP fetch impersonating Chrome via `libcurl-impersonate`.
2. **Puppeteer/headless Chrome** (`PuppeteerControl`) — JavaScript rendering for SPAs and complex pages.
3. **JSDom/Linkedom** (`JSDomControl`) — server-side DOM processing, Readability parsing, and selector-based narrowing.
4. **SnapshotFormatter** — converts raw `PageSnapshot` objects into the requested `FormattedPage` output format using Turndown, PDF extraction, or LM-based rendering.
5. **Firebase** — provides both the Firestore cache database and Cloud Storage for snapshot/screenshot persistence.

The stand-alone server entry point (`src/stand-alone/crawl.ts`) starts a Koa HTTP/2 server on port 3000. A companion `src/stand-alone/search.ts` starts the search variant.

## Related Projects and Dependencies

- **`thinapps-shared`** (git submodule, not open-sourced): Internal shared library providing secrets management, Firebase wrappers, common LLM/VLM clients, rate limiting, and proxy provisioning.
- **`civkit`**: Internal RPC and service utility library (published on npm). Provides `RPCHost`, `KoaServer`, `AsyncService`, `FancyFile`, `HashManager`, `Defer`, decorators, and more.
- **`@mozilla/readability`**: Mozilla's Readability.js injected into headless pages for content extraction.
- **`puppeteer` + `puppeteer-extra`**: Headless Chrome automation.
- **`turndown` + `turndown-plugin-gfm`**: HTML-to-Markdown conversion.
- **`linkedom`**: Fast server-side DOM parser used for HTML narrowing and analysis.
- **`pdfjs-dist`**: PDF text extraction.
- **`node-libcurl`**: libcurl bindings for fast HTTP fetching with Chrome impersonation.
- **`@napi-rs/canvas`**: Server-side canvas for image resizing before VLM captioning.
- **Firebase Admin SDK**: Firestore and Cloud Storage integration.
- **`tiktoken`**: Token counting for billing/charge calculations.
- **`openai` SDK** (v4): Used for certain LM integrations.
