# Firecrawl — Code Structure

## Annotated Directory Tree

```
firecrawl/                          # Monorepo root
├── apps/                           # All application code
│   ├── api/                        # *** MAIN BACKEND — TypeScript/Node.js Express API ***
│   │   ├── src/
│   │   │   ├── controllers/        # HTTP request handlers by API version
│   │   │   │   ├── v0/             # Legacy v0 API controllers (deprecated)
│   │   │   │   ├── v1/             # v1 API controllers
│   │   │   │   │   ├── scrape.ts           # POST /v1/scrape
│   │   │   │   │   ├── crawl.ts            # POST /v1/crawl
│   │   │   │   │   ├── crawl-status.ts     # GET /v1/crawl/:id
│   │   │   │   │   ├── crawl-status-ws.ts  # WS /v1/crawl/:id
│   │   │   │   │   ├── map.ts              # POST /v1/map
│   │   │   │   │   ├── search.ts           # POST /v1/search
│   │   │   │   │   ├── batch-scrape.ts     # POST /v1/batch/scrape
│   │   │   │   │   ├── extract.ts          # POST /v1/extract (AI extraction)
│   │   │   │   │   ├── deep-research.ts    # POST /v1/deep-research
│   │   │   │   │   ├── generate-llmstxt.ts # POST /v1/llmstxt
│   │   │   │   │   └── types.ts            # v1 Zod schemas and TypeScript types
│   │   │   │   └── v2/             # v2 API controllers (current default)
│   │   │   │       ├── scrape.ts           # POST /v2/scrape
│   │   │   │       ├── scrape-browser.ts   # POST /v2/scrape/:id/interact
│   │   │   │       ├── crawl.ts            # POST /v2/crawl
│   │   │   │       ├── crawl-status.ts     # GET /v2/crawl/:id
│   │   │   │       ├── crawl-status-ws.ts  # WS /v2/crawl/:id
│   │   │   │       ├── crawl-cancel.ts     # DELETE /v2/crawl/:id
│   │   │   │       ├── crawl-errors.ts     # GET /v2/crawl/:id/errors
│   │   │   │       ├── crawl-ongoing.ts    # GET /v2/crawl/active
│   │   │   │       ├── batch-scrape.ts     # POST /v2/batch/scrape
│   │   │   │       ├── map.ts              # POST /v2/map
│   │   │   │       ├── search.ts           # POST /v2/search
│   │   │   │       ├── extract.ts          # POST /v2/extract
│   │   │   │       ├── extract-status.ts   # GET /v2/extract/:id
│   │   │   │       ├── agent.ts            # POST /v2/agent
│   │   │   │       ├── agent-status.ts     # GET /v2/agent/:id
│   │   │   │       ├── agent-cancel.ts     # DELETE /v2/agent/:id
│   │   │   │       ├── browser.ts          # Browser session management
│   │   │   │       ├── f-search.ts         # Firecrawl-specific search
│   │   │   │       ├── x402-search.ts      # x402 micropayment search
│   │   │   │       ├── concurrency-check.ts
│   │   │   │       ├── credit-usage.ts / token-usage.ts
│   │   │   │       ├── scrape-status.ts    # GET /v2/scrape/:id (async scrape)
│   │   │   │       └── types.ts            # v2 Zod schemas and TypeScript types
│   │   │   ├── routes/             # Express router definitions
│   │   │   │   ├── v1.ts           # Mounts all v1 controller routes
│   │   │   │   ├── v2.ts           # Mounts all v2 controller routes + middleware
│   │   │   │   ├── v0.ts           # Legacy v0 routes
│   │   │   │   ├── admin.ts        # Admin/monitoring routes
│   │   │   │   └── shared.ts       # Shared middleware: auth, credits, blocklist, idempotency
│   │   │   ├── scraper/            # Core scraping logic
│   │   │   │   ├── scrapeURL/      # URL scraping pipeline (main engine)
│   │   │   │   │   ├── index.ts    # Entry point: scrapeURL() function
│   │   │   │   │   ├── error.ts    # Error types for scraping
│   │   │   │   │   ├── retryTracker.ts  # Retry and fallback logic
│   │   │   │   │   ├── engines/    # Pluggable scraping engine implementations
│   │   │   │   │   │   ├── index.ts       # Engine selection and feature flag routing
│   │   │   │   │   │   ├── fire-engine/   # Fire Engine (cloud-only, advanced proxy/CDP)
│   │   │   │   │   │   ├── playwright/    # Playwright microservice bridge
│   │   │   │   │   │   ├── fetch/         # Direct HTTP fetch engine
│   │   │   │   │   │   ├── pdf/           # PDF parsing engine
│   │   │   │   │   │   ├── document/      # Document conversion engine (DOCX etc.)
│   │   │   │   │   │   ├── index/         # Pre-indexed content engine
│   │   │   │   │   │   └── wikipedia/     # Wikipedia Enterprise API engine
│   │   │   │   │   ├── transformers/  # Post-scrape content transformers
│   │   │   │   │   │   ├── index.ts       # Transformer pipeline
│   │   │   │   │   │   ├── llmExtract.ts  # LLM-based JSON extraction
│   │   │   │   │   │   ├── agent.ts       # Agent transformer
│   │   │   │   │   │   ├── diff.ts        # Change tracking/diff
│   │   │   │   │   │   ├── audio.ts       # Audio content transformer
│   │   │   │   │   │   ├── performAttributes.ts  # Attribute extraction
│   │   │   │   │   │   ├── removeBase64Images.ts
│   │   │   │   │   │   ├── sendToSearchIndex.ts
│   │   │   │   │   │   └── uploadScreenshot.ts
│   │   │   │   │   ├── postprocessors/    # Final post-processing
│   │   │   │   │   │   ├── index.ts
│   │   │   │   │   │   └── youtube.ts     # YouTube-specific post-processor
│   │   │   │   │   └── lib/               # Shared scraping utilities
│   │   │   │   │       ├── fetch.ts       # Fetch utilities
│   │   │   │   │       ├── extractLinks.ts
│   │   │   │   │       ├── extractMetadata.ts
│   │   │   │   │       ├── extractImages.ts
│   │   │   │   │       ├── extractAttributes.ts
│   │   │   │   │       ├── extractSmartScrape.ts
│   │   │   │   │       ├── removeUnwantedElements.ts
│   │   │   │   │       ├── smartScrape.ts
│   │   │   │   │       ├── rewriteUrl.ts
│   │   │   │   │       ├── urlSpecificParams.ts
│   │   │   │   │       ├── abortManager.ts
│   │   │   │   │       └── cacheableLookup.ts
│   │   │   │   ├── WebScraper/     # Crawl orchestration layer
│   │   │   │   │   ├── crawler.ts       # Web crawler (BFS/DFS over URLs)
│   │   │   │   │   ├── sitemap.ts       # Sitemap parsing and processing
│   │   │   │   │   └── utils/
│   │   │   │   │       ├── blocklist.ts        # URL blocklist
│   │   │   │   │       ├── maxDepthUtils.ts    # Crawl depth control
│   │   │   │   │       └── engine-forcing.ts   # Force specific scrape engine
│   │   │   │   └── crawler/
│   │   │   │       └── sitemap.ts       # Sitemap crawler utilities
│   │   │   ├── lib/                # Shared library code
│   │   │   │   ├── entities.ts          # Core entity types (Document, PageOptions)
│   │   │   │   ├── crawl-redis.ts       # Redis operations for crawl state
│   │   │   │   ├── extract/             # AI extraction pipeline
│   │   │   │   │   ├── extraction-service.ts  # Main extraction service
│   │   │   │   │   ├── url-processor.ts
│   │   │   │   │   ├── build-prompts.ts
│   │   │   │   │   ├── build-document.ts
│   │   │   │   │   ├── reranker.ts
│   │   │   │   │   ├── extract-redis.ts
│   │   │   │   │   └── config.ts
│   │   │   │   ├── deep-research/       # Deep research feature
│   │   │   │   │   ├── research-manager.ts
│   │   │   │   │   ├── deep-research-service.ts
│   │   │   │   │   └── deep-research-redis.ts
│   │   │   │   ├── scrape-interact/     # Interactive browser sessions
│   │   │   │   │   ├── browser-agent.ts
│   │   │   │   │   ├── browser-service-client.ts
│   │   │   │   │   └── scrape-replay.ts
│   │   │   │   ├── generate-llmstxt/    # LLMs.txt generation
│   │   │   │   ├── branding/            # Brand extraction (logos, colors)
│   │   │   │   ├── html-to-markdown.ts  # HTML-to-Markdown conversion
│   │   │   │   ├── withAuth.ts          # Auth middleware helper
│   │   │   │   ├── permissions.ts       # Feature permission checks
│   │   │   │   ├── validateUrl.ts       # URL validation
│   │   │   │   ├── robots-txt.ts        # robots.txt parsing
│   │   │   │   ├── cost-tracking.ts     # LLM cost tracking
│   │   │   │   ├── concurrency-limit.ts
│   │   │   │   ├── engpicker.ts         # Engine picker (ML-based)
│   │   │   │   ├── logger.ts            # Pino logger setup
│   │   │   │   ├── otel-tracer.ts       # OpenTelemetry tracing
│   │   │   │   ├── zdr-helpers.ts       # Zero Data Retention helpers
│   │   │   │   ├── x402.ts              # x402 micropayment support
│   │   │   │   └── generic-ai.ts        # Generic AI client abstraction
│   │   │   ├── services/           # Background services and workers
│   │   │   │   ├── worker/         # BullMQ worker implementations
│   │   │   │   │   ├── scrape-worker.ts     # Main scrape job worker
│   │   │   │   │   ├── nuq.ts               # NuQ (RabbitMQ) worker
│   │   │   │   │   ├── nuq-worker.ts        # NuQ background worker
│   │   │   │   │   ├── team-semaphore.ts    # Team-level concurrency
│   │   │   │   │   └── nuq-prefetch-worker.ts
│   │   │   │   ├── billing/         # Credit and billing management
│   │   │   │   ├── webhook/         # Webhook dispatch
│   │   │   │   │   └── schema.ts    # Webhook payload schema
│   │   │   │   ├── logging/         # Request/job logging
│   │   │   │   ├── idempotency/     # Idempotency key handling
│   │   │   │   ├── indexing/        # Search indexing workers
│   │   │   │   ├── ledger/          # Credit ledger
│   │   │   │   ├── notification/    # Alert/notification services
│   │   │   │   ├── autumn/          # Autumn billing integration
│   │   │   │   ├── subscription/    # Subscription management
│   │   │   │   └── alerts/          # System alerts
│   │   │   ├── search/             # Web search backends
│   │   │   │   ├── index.ts             # Search entry point
│   │   │   │   ├── execute.ts           # Search execution
│   │   │   │   ├── fireEngine.ts        # Fire Engine search
│   │   │   │   ├── searxng.ts           # SearXNG integration
│   │   │   │   ├── transform.ts         # Search result transforms
│   │   │   │   └── v2/                  # v2 search backends
│   │   │   │       ├── index.ts
│   │   │   │       ├── fireEngine-v2.ts
│   │   │   │       ├── searxng.ts
│   │   │   │       └── ddgsearch.ts    # DuckDuckGo search
│   │   │   ├── types/              # Global TypeScript types
│   │   │   │   ├── branding.ts          # Brand profile types
│   │   │   │   └── parse-diff.d.ts
│   │   │   ├── types.ts            # Top-level job and queue type definitions
│   │   │   ├── utils/              # API utilities
│   │   │   │   └── integration.ts      # Third-party integration schema
│   │   │   ├── main/               # Server entry points and process harness
│   │   │   └── __tests__/          # Test suites
│   │   │       ├── snips/v1/       # v1 API snapshot tests
│   │   │       ├── snips/v2/       # v2 API snapshot tests
│   │   │       ├── e2e_withAuth/   # Auth e2e tests
│   │   │       ├── e2e_noAuth/     # No-auth e2e tests
│   │   │       └── deep-research/  # Deep research unit tests
│   │   ├── package.json        # npm scripts, Node.js dependencies
│   │   └── tsconfig.json       # TypeScript configuration
│   │
│   ├── python-sdk/             # *** Python SDK (firecrawl-py) ***
│   │   ├── firecrawl/
│   │   │   ├── __init__.py         # Public API: Firecrawl, AsyncFirecrawl, etc.
│   │   │   ├── client.py           # Main Firecrawl / AsyncFirecrawl aliases
│   │   │   ├── types.py            # Top-level type re-exports
│   │   │   ├── v2/                 # v2 client (default, actively developed)
│   │   │   │   ├── client.py       # FirecrawlClient class
│   │   │   │   ├── client_async.py # AsyncFirecrawlClient class
│   │   │   │   ├── types.py        # Pydantic models for all request/response types
│   │   │   │   ├── watcher.py      # Synchronous job watcher (Watcher class)
│   │   │   │   ├── watcher_async.py # AsyncWatcher class
│   │   │   │   ├── methods/        # Method implementations (scrape, crawl, search, etc.)
│   │   │   │   └── utils/          # HTTP client, error handler, etc.
│   │   │   ├── v1/                 # v1 client (feature-frozen)
│   │   │   └── firecrawl.backup.py # Backup of legacy client
│   │   ├── tests/              # SDK unit and integration tests
│   │   ├── pyproject.toml      # Build config and dependencies
│   │   └── README.md
│   │
│   ├── js-sdk/                 # *** JavaScript/TypeScript SDK (@mendable/firecrawl-js) ***
│   │   ├── firecrawl/
│   │   │   ├── src/
│   │   │   │   └── index.ts    # Unified entry: exports Firecrawl, FirecrawlClient, v2 types
│   │   │   ├── package.json
│   │   │   └── tsup.config.ts  # Build config (tsup bundler)
│   │   └── example*.ts/js      # Usage examples
│   │
│   ├── rust-sdk/               # *** Rust SDK (firecrawl crate) ***
│   │   ├── src/
│   │   │   ├── lib.rs          # Crate entry point
│   │   │   ├── scrape.rs       # Scrape functionality
│   │   │   ├── crawl.rs        # Crawl functionality
│   │   │   ├── search.rs       # Search functionality
│   │   │   ├── map.rs          # Map functionality
│   │   │   ├── extract.rs      # Extract functionality
│   │   │   ├── batch_scrape.rs # Batch scrape
│   │   │   ├── llmstxt.rs      # LLMs.txt generation
│   │   │   ├── document.rs     # Document types
│   │   │   ├── error.rs        # Error types
│   │   │   ├── serde_helpers.rs
│   │   │   └── v2/             # v2 implementation
│   │   ├── examples/           # Rust usage examples
│   │   └── Cargo.toml
│   │
│   ├── java-sdk/               # Java SDK
│   ├── elixir-sdk/             # Elixir SDK
│   │   ├── lib/                # Elixir implementation
│   │   └── test/
│   │
│   ├── playwright-service-ts/  # *** Playwright Browser Microservice ***
│   │   ├── api.ts              # HTTP server exposing /scrape endpoint
│   │   ├── helpers/
│   │   │   └── get_error.ts    # Error extraction from Playwright
│   │   └── Dockerfile
│   │
│   ├── go-html-to-md-service/  # Go service for fast HTML→Markdown conversion
│   ├── nuq-postgres/           # Custom PostgreSQL image for NuQ job queue
│   ├── redis/                  # Redis configuration and Dockerfile
│   │
│   ├── test-site/              # Astro-based test website for integration tests
│   │   └── src/pages/          # Test pages with various content types
│   │
│   ├── test-suite/             # End-to-end test suite and benchmarks
│   │   ├── index-benchmark/
│   │   ├── load-test-results/
│   │   └── data/
│   │
│   └── ui/
│       └── ingestion-ui/       # React + Vite ingestion UI
│           └── src/App.tsx     # Main React component
│
├── examples/                   # Usage examples and integrations
│   ├── hacker_news_scraper/    # Firecrawl vs BeautifulSoup comparison
│   ├── o3-web-crawler/         # OpenAI o3 + Firecrawl web crawler
│   ├── o4-mini-web-crawler/    # o4-mini crawler
│   ├── gemini-2.5-crawler/     # Gemini 2.5 integration
│   ├── llama-4-maverick-web-crawler/
│   ├── deepseek-v3-company-researcher/
│   ├── openai_swarm_firecrawl/ # OpenAI Swarm multi-agent example
│   ├── sales_web_crawler/      # Sales lead enrichment
│   ├── deep-research-apartment-finder/
│   └── ... (30+ examples)
│
├── docker-compose.yaml         # Full service orchestration
├── SELF_HOST.md                # Self-hosting guide
├── README.md                   # Project overview
└── CLAUDE.md                   # Claude-specific instructions
```

## Module and Package Organization

### API Server (`apps/api/src/`)

The API server follows a **Controller → Route → Service → Scraper** layered architecture:

- **`controllers/`** — Thin HTTP handlers. Parse/validate requests with Zod, call services, return responses.
- **`routes/`** — Express router mounts with middleware chains (auth, rate limiting, credits).
- **`lib/`** — Pure business logic: crawl state, extraction pipelines, auth helpers, URL validation.
- **`scraper/`** — Core scraping engine. `scrapeURL/` contains the multi-engine pipeline; `WebScraper/` handles site-level crawl orchestration.
- **`search/`** — Search backends: FireEngine, SearXNG, DuckDuckGo.
- **`services/`** — Background workers, billing, webhooks, logging, notifications.
- **`types.ts`** — Shared job/queue type definitions used by both the API and workers.

### Python SDK (`apps/python-sdk/firecrawl/`)

- `v2/` is the primary, actively developed client; `v1/` is feature-frozen.
- Methods are separated into individual modules under `v2/methods/` (scrape, crawl, batch, search, map, extract, agent, browser, usage).
- Pydantic v2 is used for all type validation and serialization.
- Both sync (`FirecrawlClient`) and async (`AsyncFirecrawlClient`) clients are provided.

### JavaScript SDK (`apps/js-sdk/firecrawl/src/`)

- Single `index.ts` entry point that exports `Firecrawl` (unified), `FirecrawlClient` (v2), `FirecrawlAppV1` (v1).
- Built with `tsup` to produce both CJS and ESM outputs.

## Code Organization Patterns

1. **Zod schemas for validation** — All API request/response types are Zod schemas in `types.ts` files, co-located with controllers.
2. **Engine feature flags** — `engines/index.ts` uses environment variables to determine which engines are available at runtime.
3. **Multi-version API** — v0 (legacy), v1 (stable), v2 (current) controllers coexist. Routes are mounted at `/v0`, `/v1`, `/v2`.
4. **Job queue decoupling** — Scrape jobs are enqueued to BullMQ/RabbitMQ; workers pick them up asynchronously. Results stored in Redis or GCS.
5. **Transformer pipeline** — Post-scrape transformers in `scrapeURL/transformers/` apply sequential content transformations (LLM extract, diff, screenshots, etc.).
