# Spider — Summary

## Repository Purpose and Goals

Spider is a high-performance, open-source web crawling and scraping library written in Rust. The project's primary goal is to be the fastest web crawler available for Rust, capable of collecting millions of pages within seconds. It provides building blocks for data curation workloads, offering everything from simple HTTP crawling to AI-powered autonomous browser automation.

The repository is organized as a Cargo workspace (version 2.48.35) containing eight crates: `spider` (core library), `spider_cli` (command-line tool), `spider_agent` (AI autonomous agent), `spider_agent_types` (pure data types), `spider_agent_html` (HTML processing), `spider_utils` (CSS/XPath selector utilities), `spider_worker` (distributed worker), and `spider_mcp` (MCP server).

## Key Features and Capabilities

**Core Crawling:**
- Concurrent multi-threaded crawling with configurable depth, limits, and budgets
- Broadcast channel subscription for real-time page streaming as crawl proceeds
- `crawl()` (link gathering) and `scrape()` (HTML storage) modes
- Robots.txt compliance, domain/subdomain filtering, blacklist/whitelist rules
- Cron scheduling for recurring crawls

**Browser Automation:**
- Headless Chrome rendering via `chromey` (CDP-based) for JavaScript-heavy SPAs
- WebDriver support (Chrome, Firefox, Edge) via `thirtyfour`
- Smart mode: HTTP first, auto-upgrades to Chrome only when JS rendering is detected
- Chrome network interception, stealth/anti-fingerprinting, screenshot capture

**Spider Cloud Integration:**
- Managed crawling infrastructure with anti-bot bypass and proxy rotation
- Five cloud modes: Proxy, Api, Unblocker, Fallback, Smart (auto-detect bot protection)
- Browser Cloud: remote headless Chrome via CDP WebSocket (`wss://browser.spider.cloud`)
- Returns pages as raw HTML, Markdown, CommonMark, plain text, or bytes

**AI / LLM Features:**
- OpenAI and Gemini integrations for dynamic browser script generation
- Remote multimodal engine for LLM-driven HTML extraction from any OpenAI-compatible endpoint
- `spider_agent`: autonomous agent for web research with search, fetch, extract, and synthesize

**Performance Optimizations:**
- Linux io_uring for async I/O (default on Linux)
- NUMA-aware thread pinning, TCP fast-open, zero-copy parsing, SIMD JSON
- Adaptive concurrency (AIMD), per-domain rate limiting, request coalescing
- Priority URL frontier, hedged requests, mmap bloom filter for URL deduplication
- HTTP/2 multiplexing tracker, ETag cache, robots.txt cross-crawl TTL cache

**Advanced Agent Features (spider_agent):**
- Tool calling schema (OpenAI-compatible function calling)
- HTML diff mode: 50–70% token reduction by sending only page changes
- Planning mode: multi-step plans reduce LLM round-trips
- Parallel synthesis: analyze N pages in a single LLM call
- Confidence tracking for smarter retry decisions
- Self-healing selectors: auto-repair failed CSS selectors via LLM diagnosis
- Schema generation: auto-generate JSON schemas from example outputs
- Concurrent chains: dependency-graph-based parallel action execution
- Dynamic skill system for web challenge solving (CAPTCHA, grids, etc.)

## Primary Use Cases and Target Audience

**Primary Users:**
- Rust backend developers building data pipelines and web scraping systems
- AI/ML engineers building LLM training data collection or RAG pipelines
- DevOps teams needing scheduled site monitoring or content extraction
- Security researchers performing site reconnaissance

**Use Cases:**
- Large-scale web indexing and link discovery
- Structured data extraction from e-commerce, job boards, news sites
- AI agent workflows: search → fetch → extract → synthesize
- Competitor intelligence and price monitoring
- Academic/research data collection
- WARC archiving for web preservation

## High-Level Architecture Overview

```
spider_agent_types   (pure data types, minimal deps)
       ↓
spider_agent_html    (HTML cleaning via lol_html)
       ↓
spider_agent         (AI agent runtime: LLM, search, browser, automation engine)
       ↓
spider               (core crawling library)
       ↓
spider_cli           (CLI binary)   spider_worker (distributed worker)   spider_mcp (MCP server)
spider_utils         (CSS/XPath selector utilities, used independently)
```

The core `spider` crate exposes a `Website` builder that drives crawling through a configurable `Configuration` struct. Pages are processed concurrently via `tokio` tasks; results are delivered through tokio broadcast channels (`subscribe()`). Feature flags gate optional subsystems (Chrome, AI, caching, distributed) with zero overhead when disabled.

## Related Projects and Dependencies

- **spider-nodejs**: `@spider-rs/spider-rs` — Node.js bindings
- **spider-py**: `spider_rs` — Python bindings
- **Spider Cloud**: `https://spider.cloud` — managed crawling SaaS
- **chromey**: Spider's CDP/Chrome protocol library (used for headless Chrome)
- **spider_fingerprint**: Browser fingerprinting for anti-detection
- **spider_firewall**: Firewall crate to prevent crawling bad sites
- **spider_skills**: Dynamic skill system for web challenge solving
- **llm_models_spider**: LLM model capabilities and pricing data
- **reqwest**: HTTP client (default); `wreq` as alternative with built-in impersonation
- **lol_html**: Fast streaming HTML rewriting (used in `spider_agent_html`)
- **thirtyfour**: WebDriver client library
- **tokio**: Async runtime (re-exported)
