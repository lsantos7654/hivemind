# Crawl4AI Code Structure

## Complete Directory Tree

```
crawl4ai/
├── __init__.py                           # Main package exports and API surface
├── __version__.py                        # Version string (0.8.0+)
├── async_webcrawler.py                   # Core AsyncWebCrawler orchestrator
├── async_crawler_strategy.py            # Crawler strategy implementations
├── async_configs.py                      # Configuration dataclasses (BrowserConfig, CrawlerRunConfig)
├── async_database.py                     # SQLite cache backend
├── async_dispatcher.py                   # Task dispatching with memory management
├── async_logger.py                       # Async logging infrastructure
├── async_url_seeder.py                   # URL discovery from sitemaps/Common Crawl
│
├── browser_adapter.py                    # Browser backend adapters (Playwright, Undetected)
├── browser_manager.py                    # Browser context and page lifecycle management
├── browser_profiler.py                   # Persistent browser profiles with auth
├── cache_context.py                      # Cache mode enums and context management
├── cache_validator.py                    # Smart cache validation with fingerprinting
│
├── models.py                             # Pydantic models (CrawlResult, MarkdownGenerationResult)
├── types.py                              # Type definitions and LLMConfig
├── config.py                             # Global configuration constants
├── utils.py                              # Utility functions (HTML processing, sanitization)
├── ssl_certificate.py                    # SSL certificate handling
├── user_agent_generator.py              # User agent rotation and generation
├── proxy_strategy.py                     # Proxy rotation strategies
│
├── extraction_strategy.py                # Extraction strategy base and implementations
├── chunking_strategy.py                  # Content chunking strategies
├── content_scraping_strategy.py          # HTML scraping and cleaning
├── content_filter_strategy.py            # Content filtering (BM25, Pruning, LLM)
├── markdown_generation_strategy.py       # Markdown conversion strategies
├── table_extraction.py                   # Table extraction with LLM support
│
├── adaptive_crawler.py                   # Adaptive crawling with information foraging
├── link_preview.py                       # Link scoring and preview
│
├── cli.py                                # Command-line interface (crwl command)
├── install.py                            # Post-install setup (crawl4ai-setup, crawl4ai-doctor)
├── migrations.py                         # Database migrations
├── model_loader.py                       # HuggingFace model loading utilities
├── prompts.py                            # LLM prompts for extraction
├── hub.py                                # CrawlerHub for managing crawler instances
├── docker_client.py                      # Python client for Docker API
│
├── components/
│   └── crawler_monitor.py                # Monitoring and metrics collection
│
├── crawlers/                             # Domain-specific crawler implementations
│   ├── __init__.py
│   ├── amazon_product/
│   │   ├── __init__.py
│   │   └── crawler.py                    # Amazon product scraper
│   └── google_search/
│       ├── __init__.py
│       └── crawler.py                    # Google search results scraper
│
├── deep_crawling/                        # Multi-page crawling strategies
│   ├── __init__.py
│   ├── base_strategy.py                  # Base classes for deep crawling
│   ├── bfs_strategy.py                   # Breadth-first search crawler
│   ├── dfs_strategy.py                   # Depth-first search crawler
│   ├── bff_strategy.py                   # Best-first search crawler
│   ├── filters.py                        # URL filtering (domain, pattern, content type)
│   ├── scorers.py                        # Link scoring (keyword, domain authority, freshness)
│   └── crazy.py                          # Experimental crawling strategies
│
├── html2text/                            # HTML to markdown conversion
│   ├── __init__.py
│   ├── cli.py                            # Standalone CLI for html2text
│   ├── __main__.py                       # Entry point for python -m crawl4ai.html2text
│   ├── config.py                         # html2text configuration
│   ├── _typing.py                        # Type hints
│   ├── elements.py                       # HTML element handlers
│   └── utils.py                          # Conversion utilities
│
├── js_snippet/                           # JavaScript injection snippets
│   └── *.js                              # Pre-built JS for page manipulation
│
├── legacy/                               # Deprecated synchronous crawler
│   ├── __init__.py
│   ├── cli.py                            # Old CLI interface
│   ├── web_crawler.py                    # Selenium-based synchronous crawler
│   ├── crawler_strategy.py              # Old strategy implementations
│   ├── database.py                       # Old cache system
│   ├── docs_manager.py                   # Documentation utilities
│   ├── version_manager.py                # Version checking
│   └── llmtxt.py                         # LLM text extraction
│
├── processors/                           # Content processors
│   └── pdf/
│       ├── __init__.py
│       ├── processor.py                  # PDF generation and processing
│       └── utils.py                      # PDF utilities
│
└── script/                               # C4A Script Language (DSL)
    ├── __init__.py                       # Public API exports
    ├── c4ai_script.py                    # Script parser and AST
    ├── c4a_compile.py                    # Compiler (script → CrawlerRunConfig)
    └── c4a_result.py                     # Result types and validation

deploy/docker/                            # Docker deployment
├── server.py                             # FastAPI server entry point
├── api.py                                # API endpoint handlers
├── schemas.py                            # Request/response schemas
├── auth.py                               # JWT authentication
├── crawler_pool.py                       # Browser pool management (3-tier)
├── job.py                                # Job queue and task management
├── monitor.py                            # Monitoring data collection
├── monitor_routes.py                     # Monitoring API endpoints
├── webhook.py                            # Webhook notifications
├── hook_manager.py                       # Custom hook execution sandbox
├── mcp_bridge.py                         # MCP server integration
├── utils.py                              # Shared utilities
└── tests/                                # Docker integration tests
    ├── test_1_basic.py
    ├── test_2_memory.py
    ├── test_3_pool.py
    ├── test_4_concurrent.py
    ├── test_5_pool_stress.py
    ├── test_6_multi_endpoint.py
    ├── test_7_cleanup.py
    ├── test_security_fixes.py
    └── run_security_tests.py

docs/                                     # Documentation and examples
├── examples/                             # Example scripts
│   ├── adaptive_crawling/                # Adaptive crawler examples
│   ├── async_webcrawler_multiple_urls_example.py
│   ├── deep_crawl_crash_recovery.py      # Crash recovery demo
│   ├── deepcrawl_example.py              # Deep crawl with BFS/DFS
│   ├── llm_extraction_example.py         # LLM-based extraction
│   ├── markdown_generation_example.py    # Custom markdown generation
│   ├── docker_example.py                 # Docker API usage
│   ├── browser_optimization_example.py   # Browser performance tuning
│   └── crawler_monitor_example.py        # Monitoring integration
│
├── blog/                                 # Release notes and blog posts
│   ├── release-v0.8.0.md                 # Latest release notes
│   ├── release-v0.7.8.md
│   └── release-v0.7.0.md
│
└── codebase/                             # Internal documentation
    ├── browser.md                        # Browser architecture
    └── cli.md                            # CLI documentation

tests/                                    # Test suite
├── memory/                               # Memory profiling tests
├── async_webcrawler_test.py             # Core crawler tests
├── extraction_strategy_test.py           # Extraction tests
├── deep_crawl_test.py                    # Deep crawl tests
└── WEBHOOK_TEST_README.md               # Webhook testing guide

scripts/                                  # Utility scripts
├── setup/                                # Installation scripts
└── analysis/                             # Analysis and profiling tools

```

## Module and Package Organization

### Core Crawler Package (`crawl4ai/`)
The main package follows a flat structure at the top level with domain-specific subpackages. Key organizational principles:

1. **Async-First Design**: All main modules are prefixed with `async_` to distinguish from legacy synchronous code
2. **Strategy Pattern**: Extraction, chunking, filtering, and crawling strategies are pluggable
3. **Configuration Separation**: All configuration lives in `async_configs.py` as dataclasses
4. **Model Isolation**: Pydantic models are centralized in `models.py`

### Main Source Directories

#### `/crawl4ai/` - Core Library
- **Entry Point**: `__init__.py` exports the public API surface (~200 exports)
- **Orchestration**: `async_webcrawler.py` contains the main `AsyncWebCrawler` class
- **Configuration**: `async_configs.py` defines `BrowserConfig`, `CrawlerRunConfig`, `LLMConfig`, etc.
- **Browser Layer**: `browser_adapter.py`, `browser_manager.py`, `browser_profiler.py` handle browser lifecycle
- **Cache Layer**: `async_database.py`, `cache_context.py`, `cache_validator.py` manage caching
- **Content Processing**: `content_scraping_strategy.py`, `markdown_generation_strategy.py`, `table_extraction.py`
- **Extraction**: `extraction_strategy.py` with LLM, CSS, XPath, Regex, and Cosine strategies
- **Utilities**: `utils.py`, `user_agent_generator.py`, `ssl_certificate.py`, `prompts.py`

#### `/crawl4ai/deep_crawling/` - Multi-Page Crawling
Implements graph traversal algorithms for crawling multiple linked pages:
- `base_strategy.py`: Abstract base classes `DeepCrawlStrategy` and `DeepCrawlDecorator`
- `bfs_strategy.py`: Breadth-first search with depth limiting and state persistence
- `dfs_strategy.py`: Depth-first search for focused crawling
- `bff_strategy.py`: Best-first search using link scoring
- `filters.py`: URL filtering by domain, pattern, content type, relevance, SEO factors
- `scorers.py`: Link prioritization using keywords, domain authority, freshness, path depth

#### `/crawl4ai/html2text/` - Markdown Conversion
Custom HTML-to-markdown converter optimized for LLM consumption:
- Fork of the popular html2text library with Crawl4AI-specific enhancements
- Handles tables, code blocks, images, links with citation numbering
- Configurable options for link handling, image alt text, and whitespace

#### `/crawl4ai/crawlers/` - Domain-Specific Crawlers
Pre-built crawlers for common use cases:
- `amazon_product/`: Product scraper with price, reviews, specifications
- `google_search/`: Search result extraction with metadata

#### `/crawl4ai/script/` - C4A Script Language
Domain-specific language for declarative crawling:
- Lark-based parser for custom scripting language
- Compiles to `CrawlerRunConfig` objects
- Supports variables, conditionals, loops, and custom actions

#### `/crawl4ai/legacy/` - Deprecated Code
Selenium-based synchronous crawler (deprecated, will be removed):
- Maintained only for backward compatibility
- Users are encouraged to migrate to async version

#### `/crawl4ai/processors/` - Content Processors
Specialized processors for different output formats:
- `pdf/`: PDF generation from crawled content

#### `/crawl4ai/components/` - Reusable Components
- `crawler_monitor.py`: Real-time monitoring with metrics collection

### Deployment Directory (`deploy/docker/`)

Production-ready Docker deployment with FastAPI server:

- **API Layer**: `server.py` (FastAPI app), `api.py` (endpoint handlers), `schemas.py` (request/response models)
- **Security**: `auth.py` (JWT tokens), hook sandboxing, file:// URL blocking
- **Browser Pool**: `crawler_pool.py` implements 3-tier pooling (permanent/hot/cold pages)
- **Job Management**: `job.py` handles async task queue with priority scheduling
- **Monitoring**: `monitor.py` + `monitor_routes.py` provide real-time dashboard and WebSocket streaming
- **Webhooks**: `webhook.py` for event notifications
- **Hooks**: `hook_manager.py` executes user-provided Python hooks in sandboxed environment
- **MCP Bridge**: `mcp_bridge.py` exposes crawler as MCP server for AI assistants

## Key Files and Their Roles

### `crawl4ai/__init__.py` (230 lines)
- **Role**: Public API definition and exports
- **Exports**: ~70 classes, functions, and enums
- **Responsibility**: Gateway to all crawler functionality
- **Pattern**: Re-exports from submodules with explicit `__all__` list

### `crawl4ai/async_webcrawler.py` (~2000 lines)
- **Role**: Main crawler orchestrator
- **Class**: `AsyncWebCrawler`
- **Key Methods**:
  - `arun()`: Single URL crawling
  - `arun_many()`: Batch crawling with dispatching
  - `awarmup()`: Browser warmup and initialization
  - `aprocess_html()`: Process HTML without network fetch
- **Lifecycle**: Supports both context manager and explicit start/close
- **Integration**: Coordinates browser, cache, extraction, and markdown generation

### `crawl4ai/async_configs.py` (~1000 lines)
- **Role**: Configuration dataclasses
- **Classes**:
  - `BrowserConfig`: Browser settings, user agent, headers, viewport
  - `CrawlerRunConfig`: Per-crawl configuration with extraction strategies
  - `LLMConfig`: LLM provider settings with retry/backoff
  - `ProxyConfig`: Proxy rotation configuration
  - `SeedingConfig`: URL discovery configuration
  - `VirtualScrollConfig`: Infinite scroll handling
  - `LinkPreviewConfig`: Link scoring and preview
- **Pattern**: Immutable dataclasses with validation

### `crawl4ai/models.py` (~800 lines)
- **Role**: Core data models
- **Classes**:
  - `CrawlResult`: Complete crawl result with HTML, markdown, media, links
  - `MarkdownGenerationResult`: Markdown variants (raw, fit, citations)
  - `CrawlerTaskResult`: Dispatcher task result with metrics
  - `CrawlStats`: Crawl statistics and timing
  - `TokenUsage`: LLM token tracking
- **Pattern**: Pydantic models with computed properties

### `crawl4ai/extraction_strategy.py` (~3000 lines)
- **Role**: Data extraction strategies
- **Base Class**: `ExtractionStrategy` (abstract)
- **Implementations**:
  - `NoExtractionStrategy`: Pass-through
  - `LLMExtractionStrategy`: LLM-powered extraction with chunking
  - `CosineStrategy`: Clustering-based extraction with embeddings
  - `JsonCssExtractionStrategy`: CSS selector-based JSON extraction
  - `JsonXPathExtractionStrategy`: XPath-based extraction
  - `JsonLxmlExtractionStrategy`: lxml-based extraction
  - `RegexExtractionStrategy`: Pattern matching extraction
- **Features**: Parallel processing, async support, error handling

### `crawl4ai/browser_manager.py` (~1000 lines)
- **Role**: Browser context and page lifecycle
- **Class**: `BrowserManager`
- **Responsibilities**:
  - Browser instance creation and cleanup
  - Context management (persistent vs ephemeral)
  - Page pooling and reuse
  - CDP (Chrome DevTools Protocol) integration
  - Network request/response interception
- **Pattern**: Async context manager

### `crawl4ai/async_dispatcher.py` (~800 lines)
- **Role**: Task dispatching with resource management
- **Classes**:
  - `BaseDispatcher`: Abstract dispatcher interface
  - `MemoryAdaptiveDispatcher`: Memory-aware task scheduling
  - `SemaphoreDispatcher`: Simple semaphore-based limiting
  - `RateLimiter`: Per-domain rate limiting with exponential backoff
- **Features**: Memory monitoring, priority queues, domain throttling

### `crawl4ai/adaptive_crawler.py` (~1200 lines)
- **Role**: Intelligent adaptive crawling
- **Class**: `AdaptiveCrawler`
- **Strategy**: Statistical or embedding-based information foraging
- **Features**:
  - Query expansion with LLM
  - Semantic gap analysis
  - Coverage estimation using alpha shapes
  - Saturation detection (know when to stop crawling)
- **State**: Serializable `CrawlState` with persistence

### `deploy/docker/server.py` (~600 lines)
- **Role**: FastAPI production server
- **Endpoints**:
  - `/crawl`: Batch crawling with hooks
  - `/crawl/stream`: Streaming crawl results
  - `/md`: Markdown-only extraction
  - `/llm`: LLM-powered Q&A
  - `/html`, `/screenshot`, `/pdf`: Content format conversions
  - `/monitor/*`: Monitoring dashboard and metrics
  - `/playground`: Interactive testing UI
- **Features**: JWT auth, rate limiting, browser pooling, Prometheus metrics

## Code Organization Patterns

### Strategy Pattern Usage
Every major subsystem uses the Strategy pattern:
1. **Extraction**: Pluggable `ExtractionStrategy` implementations
2. **Crawling**: `AsyncCrawlerStrategy` with Playwright/Undetected backends
3. **Markdown**: `MarkdownGenerationStrategy` with filtering
4. **Content Filter**: `RelevantContentFilter` (Pruning, BM25, LLM)
5. **Chunking**: `ChunkingStrategy` for content splitting
6. **Deep Crawl**: `DeepCrawlStrategy` (BFS, DFS, BestFirst)

### Async/Await Throughout
- All I/O operations are async (HTTP, browser, database)
- Uses `asyncio.gather()` for concurrent operations
- Context managers (`async with`) for resource management
- Background tasks with `asyncio.create_task()`

### Configuration as Data
- Dataclasses for configuration (not dict-based)
- Immutable by default (frozen=True where appropriate)
- Validation via Pydantic or dataclass validators
- Separation of browser config vs crawl config

### Error Handling
- Exceptions are caught at appropriate levels
- Retry logic with exponential backoff for LLM calls
- Graceful degradation (e.g., cache fallback)
- Detailed error context in results

### Modularity
- Small, focused modules (single responsibility)
- Clear interfaces between layers
- Minimal coupling (dependency injection where possible)
- Easy to test in isolation

This organization makes Crawl4AI highly extensible while maintaining a clean public API for users.
