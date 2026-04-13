# Jina Reader — Code Structure

## Annotated Directory Tree

```
reader/
├── .github/                        # GitHub Actions CI/CD workflows
├── .vscode/                        # VSCode workspace settings
├── public/                         # Static assets served by the stand-alone server
├── src/                            # All TypeScript source code
│   ├── api/                        # Top-level RPC API controllers
│   │   ├── crawler.ts              # CrawlerHost: core URL-crawling RPC host
│   │   ├── searcher.ts             # SearcherHost: web search RPC host
│   │   └── serp.ts                 # SERP (Search Engine Results Page) API controller
│   │
│   ├── cloud-functions/            # Firebase Cloud Functions (serverless handlers)
│   │   ├── adaptive-crawler.ts     # Adaptive crawl scheduling cloud function
│   │   └── data-crunching.ts       # Background data processing cloud function
│   │
│   ├── db/                         # Firestore data model definitions
│   │   ├── adaptive-crawl-task.ts  # AdaptiveCrawlTask model
│   │   ├── crawled.ts              # Crawled: cached page snapshot metadata
│   │   ├── domain-blockade.ts      # DomainBlockade: abuse block records
│   │   ├── domain-profile.ts       # DomainProfile: per-domain behavior hints
│   │   ├── img-alt.ts              # ImgAlt: cached image alt-text records
│   │   ├── pdf.ts                  # PDFContent: cached PDF extraction results
│   │   └── searched.ts             # SERPResult: cached search result records
│   │
│   ├── dto/                        # Data Transfer Objects (request parameter parsing)
│   │   ├── adaptive-crawler-options.ts   # Options DTO for adaptive crawling
│   │   ├── crawler-options.ts            # CrawlerOptions: all request headers/params
│   │   ├── jina-embeddings-auth.ts       # Auth DTO (Bearer token + user resolution)
│   │   └── turndown-tweakable-options.ts # Markdown-rendering option pass-through
│   │
│   ├── lib/                        # Thin shared library utilities
│   │   └── transform-server-event-stream.ts  # OutputServerEventStream: SSE stream class
│   │
│   ├── services/                   # Business logic services
│   │   ├── alt-text.ts             # AltTextService: VLM image captioning
│   │   ├── async-context.ts        # AsyncLocalContext: request-scoped async storage
│   │   ├── blackhole-detector.ts   # BlackHoleDetector: infinite-loop/abuse detection
│   │   ├── brave-search.ts         # BraveSearchService: Brave Search API client
│   │   ├── canvas.ts               # CanvasService: image resize/export via @napi-rs/canvas
│   │   ├── cf-browser-rendering.ts # CFBrowserRendering: Cloudflare Browser Rendering
│   │   ├── curl.ts                 # CurlControl: libcurl-based HTTP side-loader
│   │   ├── errors.ts               # Custom application error classes
│   │   ├── finalizer.ts            # Finalizer: graceful shutdown handling
│   │   ├── geoip.ts                # GeoIPService: MaxMind-based IP geolocation
│   │   ├── jsdom.ts                # JSDomControl: server-side DOM processing (Linkedom)
│   │   ├── lm.ts                   # LmControl: ReaderLM/Gemini language model integration
│   │   ├── logger.ts               # GlobalLogger: pino-based structured logger
│   │   ├── minimal-stealth.js      # Puppeteer stealth plugin configuration (JS)
│   │   ├── misc.ts                 # MiscService: URL normalization and validation
│   │   ├── pdf-extract.ts          # PDFExtractor: pdfjs-dist PDF text extraction
│   │   ├── pseudo-transfer.ts      # PseudoTransfer: internal data transfer utility
│   │   ├── puppeteer.ts            # PuppeteerControl: headless Chrome scraping engine
│   │   ├── registry.ts             # RPCRegistry: KoaRPCRegistry configuration
│   │   ├── robots-text.ts          # RobotsTxtService: robots.txt fetching and checking
│   │   ├── serper-search.ts        # SerperSearchService and GoogleSearchExplicitOperatorsDto
│   │   ├── snapshot-formatter.ts   # SnapshotFormatter: PageSnapshot → FormattedPage
│   │   ├── temp-file.ts            # TempFileManager: temporary file lifecycle management
│   │   ├── threaded.ts             # ThreadedServiceRegistry: worker thread pool
│   │   └── serp/                   # Search provider implementations
│   │       ├── compat.ts           # WebSearchEntry: common search result interface
│   │       ├── google.ts           # Google direct search client
│   │       ├── internal.ts         # InternalJinaSerpService: Jina's internal SERP
│   │       ├── puppeteer.ts        # Puppeteer-based SERP scraping
│   │       └── serper.ts           # SerperGoogleSearchService, SerperBingSearchService
│   │
│   ├── stand-alone/                # Standalone server entry points
│   │   ├── crawl.ts                # CrawlStandAloneServer: Koa HTTP/2 server for r.jina.ai
│   │   ├── search.ts               # Search server entry point for s.jina.ai
│   │   └── serp.ts                 # SERP standalone server entry point
│   │
│   ├── utils/                      # Pure utility functions
│   │   ├── encoding.ts             # File reading with encoding detection
│   │   ├── get-function-url.ts     # Firebase Cloud Function URL helper
│   │   ├── ip.ts                   # IP address utilities
│   │   ├── markdown.ts             # Markdown post-processing helpers
│   │   ├── misc.ts                 # Miscellaneous helpers (tryDecodeURIComponent, etc.)
│   │   └── tailwind-classes.ts     # Tailwind CSS class names (for DOM cleaning)
│   │
│   ├── fetch.d.ts                  # TypeScript declarations for global fetch
│   ├── shared                      # Symlink/reference to thinapps-shared submodule
│   └── types.d.ts                  # Global type declarations
│
├── thinapps-shared/                # Git submodule: internal shared library (not open-sourced)
├── Dockerfile                      # Production Docker image definition
├── integrity-check.cjs             # Pre-build integrity verification script
├── package.json                    # Node.js package manifest
├── package-lock.json               # Lockfile
└── tsconfig.json                   # TypeScript compiler configuration
```

## Module and Package Organization

The codebase follows a **layered architecture** with clear separation of concerns:

| Layer | Location | Responsibility |
|---|---|---|
| **Entry points** | `src/stand-alone/` | HTTP server bootstrap, Koa setup, port binding |
| **API controllers** | `src/api/` | RPC method definitions, request routing, response formatting |
| **DTOs** | `src/dto/` | Input validation and casting from HTTP headers/body |
| **Services** | `src/services/` | All business logic: crawling, search, LM, caching |
| **DB models** | `src/db/` | Firestore document definitions with serialization |
| **Utilities** | `src/utils/` | Pure functions, no side effects |
| **Lib** | `src/lib/` | Reusable stream/transport utilities |

## Main Source Directories and Their Purposes

### `src/api/` — RPC API Controllers

Contains the two main **RPC hosts** that are registered with the Koa RPC registry and handle all HTTP traffic:

- **`crawler.ts`** (`CrawlerHost`): The core crawling controller. Exposes HTTP endpoints (`GET`/`POST` on `/:url`). Orchestrates the full pipeline: URL validation → cache lookup → curl side-load → Puppeteer rendering → snapshot formatting. Contains `iterSnapshots()` (the main async generator pipeline), `cachedScrap()`, `scrapMany()` (parallel multi-URL scraping), and `setToCache()`/`queryCache()`.

- **`searcher.ts`** (`SearcherHost`): The search controller. Exposes HTTP endpoints on `/:query` (and `/search`). Delegates to search provider services to get URLs, then calls `CrawlerHost.scrapMany()` to fetch content, organizes results, and streams/returns them.

- **`serp.ts`**: A specialized SERP API controller that exposes raw search results without full page content fetching.

### `src/services/` — Business Logic

The most significant service files:

- **`puppeteer.ts`** (`PuppeteerControl`): ~1335 lines. Manages a pool of headless Chrome browsers. Implements `scrap(url, opts)` as an async generator that yields `PageSnapshot` objects as they progress through page-load stages. Injects Readability.js into pages, handles stealth, proxy configuration, and page lifecycle.

- **`snapshot-formatter.ts`** (`SnapshotFormatter`): ~865 lines. Converts `PageSnapshot` → `FormattedPage` for any output mode. Owns the Turndown conversion pipeline (with GFM tables, strikethrough, task lists, highlighted code blocks), integrates PDF extraction and alt-text generation.

- **`jsdom.ts`** (`JSDomControl`): ~390 lines. Server-side HTML processing using Linkedom. Key methods: `narrowSnapshot()` (applies selector-based filtering), `analyzeHTMLTextLite()` (token counting, title extraction), `cleanHTMLforLMs()` (strips non-content tags).

- **`curl.ts`** (`CurlControl`): ~456 lines. Wraps `node-libcurl` with Chrome-impersonating headers. The `sideLoad(url, opts)` method performs a fast HTTP fetch (with decompression for gzip/brotli/zstd) before triggering Puppeteer, avoiding browser launch overhead for simple pages.

- **`pdf-extract.ts`** (`PDFExtractor`): ~378 lines. Uses `pdfjs-dist` to extract text from PDFs. Handles layout-aware column detection (based on standard deviation of x-coordinates) and rotation detection.

- **`lm.ts`** (`LmControl`): Integrates Jina's `readerlm-v2` model and Google's Gemini for vision-based page reading. Provides async generators that stream LM output chunks as partial `PageSnapshot` updates.

- **`alt-text.ts`** (`AltTextService`): Captions images using Vertex Gemini 2.0 Flash via `ImageInterrogationManager`. Caches results in `ImgAlt` Firestore collection.

- **`threaded.ts`** (`ThreadedServiceRegistry`): Manages a Node.js worker thread pool. The `@Threaded()` decorator (used on `JSDomControl.actualNarrowSnapshot`) offloads CPU-intensive DOM work to worker threads.

### `src/dto/` — Data Transfer Objects

**`crawler-options.ts`** is the most important DTO file (~727 lines). `CrawlerOptions` extends `AutoCastable` (from `civkit`) and defines every configurable request parameter with its OpenAPI documentation, type, default value, and validation. Notable enums defined here:

- `CONTENT_FORMAT`: `content`, `markdown`, `html`, `text`, `pageshot`, `screenshot`, `vlm`, `readerlm-v2`
- `ENGINE_TYPE`: `auto`, `browser`, `curl`, `cf-browser-rendering`
- `RESPOND_TIMING`: `html`, `visible-content`, `mutation-idle`, `resource-idle`, `media-idle`, `network-idle`

### `src/db/` — Firestore Models

Each file exports a Firestore-backed model class. The most used are:
- **`crawled.ts`** (`Crawled`): Stores URL digest, creation time, availability flags for snapshot/screenshot/pageshot, and JS-modification metadata.
- **`searched.ts`** (`SERPResult`): Stores query digest and raw search provider response.
- **`domain-blockade.ts`** (`DomainBlockade`): Records blocked domains with expiry timestamps.

### `src/stand-alone/` — Entry Points

**`crawl.ts`** is the main production entry point. It instantiates `CrawlStandAloneServer` (extends `KoaServer`), sets up middleware (CORS, body parsing, compression, asset serving), and starts both an HTTP/1.1 and an HTTP/2 server. Default port is `3000` (overridable via `PORT` env var).

## Code Organization Patterns

1. **Dependency injection via tsyringe**: All services are `@singleton()` classes registered with `container`. Constructors declare their dependencies as typed parameters. `container.resolve(SomeClass)` produces fully wired instances.

2. **`AsyncService` base class**: Most services extend `civkit`'s `AsyncService`. They implement `async init()` and call `this.emit('ready')` when ready. Dependent services call `await this.dependencyReady()` before proceeding.

3. **Decorator-based RPC routing**: HTTP endpoints are declared with `@Method({ proto: { http: { action, path } } })` on controller methods. The path pattern `'::url'` means "capture everything after the host as a URL parameter".

4. **Async generator pipelines**: Crawling is entirely async-generator-based (`yield*`, `for await`). This allows incremental delivery of partial results (streaming mode) and clean composition of pipeline stages.

5. **Batched Firestore writes**: Both `CrawlerHost` and `SearcherHost` collect cache records in `batchedCaches[]` arrays and flush them in batches every ~10 seconds to reduce Firestore write costs.

6. **Thread boundary awareness**: The `@Threaded()` decorator in `jsdom.ts` marks methods that run in worker threads. These methods cannot accept non-serializable arguments (hence the `sideLoad: undefined` stripping in `JSDomControl.narrowSnapshot`).
