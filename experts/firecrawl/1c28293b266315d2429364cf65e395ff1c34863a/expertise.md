### Python SDK (`firecrawl-py`)
- `Firecrawl` and `AsyncFirecrawl` class initialization and configuration
- `scrape()` method: all parameters including formats, actions, location, proxy, parsers, mobile, wait_for, only_main_content, max_age, store_in_cache, profile
- `interact()` method: browser interaction via prompt or code, language options (python/node/bash)
- `stop_interaction()` / `stop_interactive_browser()` aliases
- `search()` method: query, sources, categories, limit, tbs, location, scrape_options
- `crawl()` method: blocking crawl with poll_interval, all crawl options
- `start_crawl()`: async crawl, returns job ID
- `check_crawl_status()`, `cancel_crawl()`
- `crawl_and_watch()` with Watcher iteration
- `batch_scrape()` and `start_batch_scrape()`
- `map()`: URL discovery with search filter
- `extract()`: AI structured extraction with schema
- `agent()`: autonomous web agent
- `AsyncFirecrawl` and all async variants
- `Watcher` and `AsyncWatcher` classes for streaming crawl results
- v1 legacy client (`V1FirecrawlApp`, `AsyncV1FirecrawlApp`)
- `ScrapeOptions`, `CrawlRequest`, `Document`, `DocumentMetadata`, `SearchData`, `MapData` Pydantic types
- SDK version: 4.22.0 (from `apps/python-sdk/firecrawl/__init__.py`)
- `pyproject.toml` dependencies: requests, httpx, pydantic>=2.0, websockets, aiohttp

### JavaScript/TypeScript SDK (`@mendable/firecrawl-js`)
- `Firecrawl` unified class (extends v2 `FirecrawlClient`, adds `.v1` lazy accessor)
- `FirecrawlClient` v2 class
- `FirecrawlAppV1` legacy class
- `Watcher` class and `WatcherOptions`
- `scrape()`, `asyncScrape()`, `scrapeAndWatch()` methods
- `crawl()`, `asyncCrawl()`, `checkCrawlStatus()`, `cancelCrawl()`, `crawlAndWatch()`
- `batchScrape()`, `asyncBatchScrape()`
- `map()`, `search()`, `extract()`, `agent()`
- `interact()`, `stopInteraction()`
- tsup build output: CJS + ESM dual build
- pnpm as package manager

### Rust SDK (`firecrawl` crate v1.4.0)
- Crate modules: scrape, crawl, batch_scrape, search, map, extract, llmstxt, document, error, v2
- Async-first using tokio
- reqwest for HTTP, serde for serialization
- `Cargo.toml` dependencies

### REST API (v2)
- `POST /v2/scrape` — synchronous scrape, all request fields, response structure
- `POST /v2/crawl` — async crawl, job ID response
- `GET /v2/crawl/:id` — status polling, pagination with `next` cursor
- `GET /v2/crawl/:id` (WebSocket) — real-time streaming
- `DELETE /v2/crawl/:id` — cancellation
- `GET /v2/crawl/:id/errors` — per-URL error details
- `POST /v2/batch/scrape` — bulk async scraping
- `GET /v2/batch/scrape/:id` — batch status
- `POST /v2/map` — URL discovery
- `POST /v2/search` — web search with content
- `POST /v2/extract` — AI extraction, schema-guided
- `GET /v2/extract/:id` — extract job status
- `POST /v2/agent` — autonomous agent
- `GET /v2/agent/:id` — agent status
- `DELETE /v2/agent/:id` — agent cancel
- `POST /v2/scrape/:id/interact` — browser interaction
- `DELETE /v2/scrape/:id/browser` — terminate browser session
- `GET /v2/crawl/active` — list ongoing crawls
- `POST /v2/crawl/params-preview` — preview crawl params
- Credit and token usage endpoints

### API Server Architecture
- Express.js with TypeScript
- Zod schema validation for all request/response types (v2/types.ts)
- Multi-version routing: /v0, /v1, /v2
- Middleware chain: requestTimingMiddleware → authMiddleware → checkCreditsMiddleware → blocklistMiddleware → idempotencyMiddleware
- Controller pattern: thin handlers in `controllers/` call services in `lib/` and `services/`
- Job queue: BullMQ (Redis) for scrape jobs, RabbitMQ/NuQ for worker distribution
- OpenTelemetry distributed tracing via `lib/otel-tracer.ts`
- Pino structured logging via `lib/logger.ts`
- Sentry error monitoring integration
- Zero Data Retention (ZDR) support via `lib/zdr-helpers.ts`

### Scraping Engine Pipeline
- Engine selection in `scraper/scrapeURL/engines/index.ts`
- Available engines: `fire-engine;chrome-cdp`, `fire-engine;chrome-cdp;stealth`, `fire-engine;tlsclient`, `playwright`, `fetch`, `pdf`, `document`, `index`, `wikipedia`
- Engine feature flags (e.g., actions require fire-engine or playwright)
- Retry and fallback logic in `scraper/scrapeURL/retryTracker.ts`
- Transformer pipeline for post-processing: llmExtract, diff, agent, audio, attributes, screenshot upload
- Postprocessors: YouTube-specific handling
- Engine utilities: URL rewriting, smart scrape, cache lookup, abort management

### Crawler (Site-Level)
- `scraper/WebScraper/crawler.ts` — BFS crawl with depth control
- Sitemap parsing in `scraper/WebScraper/sitemap.ts`
- URL blocklist in `scraper/WebScraper/utils/blocklist.ts`
- Max depth utilities in `scraper/WebScraper/utils/maxDepthUtils.ts`
- Engine forcing per URL pattern

### AI / LLM Features
- LLM extract transformer: `scraper/scrapeURL/transformers/llmExtract.ts`
- Generic AI client: `lib/generic-ai.ts`
- Extraction pipeline: `lib/extract/extraction-service.ts`
- Deep research: `lib/deep-research/`
- Branding extraction: `lib/branding/` (logos, colors)
- LLMs.txt generation: `lib/generate-llmstxt/`
- Prompt generation for crawl: `generateCrawlerOptionsFromPrompt`
- Cost tracking: `lib/cost-tracking.ts`
- JSON format scraping via `formats: ['json']` + prompt/schema

### Search Backends
- FireEngine search (cloud only)
- SearXNG integration (self-hostable)
- DuckDuckGo search fallback
- Google search (default)
- v2 search routed through `src/search/v2/`

### Docker Compose / Self-Hosting
- Service definitions: api, playwright-service, redis, rabbitmq, nuq-postgres
- Environment variable configuration
- Resource limits (CPUs, RAM)
- Optional services (Fire Engine, Supabase, SearXNG)
- `SELF_HOST.md` step-by-step guide
- Common env vars: USE_DB_AUTHENTICATION, PLAYWRIGHT_MICROSERVICE_URL, OPENAI_API_KEY, SEARXNG_ENDPOINT, PROXY_SERVER, NUM_WORKERS_PER_QUEUE

### SDK Integration Patterns
- MCP server: `npx -y firecrawl-mcp` with `FIRECRAWL_API_KEY`
- CLI: `npx -y firecrawl-cli@latest init --all --browser`
- Skill/agent integration with Claude Code, OpenCode, Antigravity
- Multi-agent examples (OpenAI Swarm, LangChain, etc.)
- AI integrations shown in `examples/` directory (30+ examples)

### Output Formats and Data Structures
- `Document` type fields: markdown, html, rawHtml, screenshot, links, json, metadata, changeTracking
- `DocumentMetadata` fields: title, description, url, statusCode, scrapeId, proxyUsed, ogTitle, ogImage, publishedTime, favicon, etc.
- Webhook payload structure for async jobs
- Crawl status response: status (scraping/completed/failed), total, completed, creditsUsed, data, next (pagination cursor)
- Search result structure: url, title, markdown, description

### Configuration Options
- Proxy: basic vs stealth
- Location: country, languages array
- Parsers: pdf, docx
- Cache: maxAge (seconds), storeInCache
- Rate limiting and concurrency per team
- Zero Data Retention mode
- Custom headers per scrape request
- Browser profile for persistent state

### Advanced Features
- x402 micropayment protocol for premium endpoints
- Idempotency keys for request deduplication
- Concurrency check endpoint
- Credit usage historical tracking
- Token usage tracking
- Agent signup flow (enterprise)
- Branding profile extraction (logos, colors)
- Change tracking / diff between scrapes
