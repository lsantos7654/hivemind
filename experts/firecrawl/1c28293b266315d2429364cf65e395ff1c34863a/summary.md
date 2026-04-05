# Firecrawl — Repository Summary

## Repository Purpose and Goals

Firecrawl is an open-source web scraping, crawling, and data extraction platform designed to power AI agents and LLM-based applications with clean, structured web data. Created by Mendable.ai, it serves as both a self-hostable backend and a managed cloud service (firecrawl.dev). The core goal is to abstract away the complexity of web scraping — proxy rotation, JavaScript rendering, rate limit handling, content cleaning — and return LLM-ready output (Markdown, JSON, HTML, screenshots) with industry-leading reliability across 96%+ of the web.

## Key Features and Capabilities

- **Scrape**: Converts any URL to Markdown, HTML, structured JSON, screenshots, or raw HTML. Supports JavaScript-heavy pages via Chrome CDP and Playwright. Handles PDFs, DOCX, and other document formats.
- **Crawl**: Full-site crawling starting from a root URL. Supports depth limits, path include/exclude filters, sitemap parsing, subdomain traversal, and webhook notifications when jobs complete.
- **Batch Scrape**: Asynchronously scrape thousands of URLs concurrently with status polling or WebSocket updates.
- **Search**: Web search with full-page content extraction from results. Backends include Google, SearXNG, DuckDuckGo, and FireEngine.
- **Map**: Rapidly discover all URLs on a website, leveraging sitemaps and crawl data.
- **Extract**: AI-powered structured data extraction from one or many URLs using an LLM with a JSON schema prompt.
- **Agent**: Autonomous AI agent that gathers data from the web based on a natural-language description.
- **Interact**: Scrape a page, keep the browser session alive, then interact with it via AI prompts or code (click, scroll, type, search).
- **Actions**: Pre-scrape browser automation — click, wait, scroll, write, press, take screenshots, execute JavaScript.
- **Change Tracking / Diff**: Track content changes on pages over time.
- **LLMs.txt Generation**: Generate `llms.txt` files for AI-friendly site metadata.

## Primary Use Cases and Target Audience

- **AI application developers** building RAG pipelines, agents, or LLM-powered tools that need real-time or bulk web data.
- **Data engineers** who need reliable, structured extraction from arbitrary URLs at scale.
- **Researchers and analysts** needing company intelligence, market research, news monitoring, or job board aggregation.
- **Self-hosters** who require full control over data residency and scraping infrastructure.
- **MCP/Claude Code users** who want to connect any MCP-compatible AI agent to the web.

## High-Level Architecture Overview

Firecrawl is a **microservices monorepo** (`apps/`) orchestrated via Docker Compose:

1. **API Server** (`apps/api`) — TypeScript/Node.js Express application. Exposes REST endpoints under `/v1` and `/v2`. Validates requests with Zod, checks auth/credits (Supabase or local), then enqueues jobs or processes them inline.

2. **Job Queue Workers** — BullMQ workers (backed by Redis) handle scrape jobs. A separate NuQ worker system backed by RabbitMQ + PostgreSQL provides additional queue management. Workers call the `scrapeURL` pipeline which selects from available scraping engines.

3. **Scraping Engine Pipeline** (`apps/api/src/scraper/scrapeURL/`) — Multi-engine, retry-aware pipeline. Engines include:
   - `fire-engine;chrome-cdp` — Proprietary cloud engine (managed service only)
   - `playwright` — Delegates to the Playwright microservice
   - `fetch` — Direct HTTP fetch with TLS handling
   - `pdf` / `document` — File type-specific parsers
   - `index` — Pre-indexed document store
   - `wikipedia` — Wikipedia Enterprise API

4. **Playwright Microservice** (`apps/playwright-service-ts`) — Isolated TypeScript service running Playwright browsers, used for JS-heavy pages.

5. **Go HTML-to-Markdown Service** (`apps/go-html-to-md-service`) — High-performance HTML-to-Markdown conversion.

6. **Redis** — Job state, crawl metadata, rate limiting, caching.

7. **RabbitMQ** — Message broker for NuQ worker distribution.

8. **PostgreSQL** (`apps/nuq-postgres`) — Job persistence and NuQ queue state.

9. **Client SDKs** — Python (`firecrawl-py`), JavaScript/TypeScript (`@mendable/firecrawl-js`), Rust (`firecrawl`), Java, Elixir. Each SDK wraps the HTTP REST API.

10. **Ingestion UI** (`apps/ui/ingestion-ui`) — React-based web UI for the API.

## Related Projects and Dependencies

- **firecrawl-mcp** — MCP server for connecting Claude and other MCP clients to Firecrawl via `npx -y firecrawl-mcp`.
- **firecrawl-cli** — CLI tool (`npx -y firecrawl-cli@latest`) for agent integration.
- **SearXNG** — Optional self-hosted search backend for the `/search` API.
- **Supabase** — Optional database/auth backend for API key management and team credits.
- **OpenAI / Ollama** — LLM backends for AI features (extract, agent, JSON scrape format). Configurable via `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OLLAMA_BASE_URL`.
- **Sentry** — Error monitoring.
- **OpenTelemetry** — Distributed tracing.
- **Bull/BullMQ** — Redis-backed job queue for scrape workers.
- **Autumn** — Billing/credits service.
- **x402** — Coinbase micropayment protocol for premium endpoints.
