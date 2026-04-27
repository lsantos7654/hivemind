Expert knowledge areas based on Crawl4AI repository analysis:

### Core Web Crawling
- **AsyncWebCrawler API**: Main orchestrator class with arun(), arun_many(), aprocess_html() methods
- **Browser Automation**: Playwright/Patchright integration, undetected browser mode, multi-browser support
- **Session Management**: Persistent contexts, browser profiles, cookie handling, authentication state
- **Cache System**: Multi-level caching with SQLite backend, cache validation, fingerprinting, bypass modes
- **Async Architecture**: asyncio-based concurrent crawling, task dispatching, memory-adaptive scheduling

### Content Extraction & Processing
- **Markdown Generation**: Clean, LLM-ready markdown with DefaultMarkdownGenerator, citation numbering
- **Content Filtering**: Heuristic pruning (PruningContentFilter), BM25-based relevance (BM25ContentFilter)
- **HTML Cleaning**: BeautifulSoup/lxml-based cleaning, tag exclusion, content scraping strategies
- **Table Extraction**: LLMTableExtraction with intelligent chunking for massive tables
- **Media Extraction**: Images (including srcset, picture), videos, audio, lazy-loaded content

### Structured Data Extraction
- **LLM Extraction**: LLMExtractionStrategy with Pydantic schemas, supports 100+ providers via LiteLLM
- **CSS/XPath Extraction**: JsonCssExtractionStrategy, JsonXPathExtractionStrategy for selector-based scraping
- **Cosine Similarity**: Semantic extraction using embeddings and clustering (CosineStrategy)
- **Regex Extraction**: Pattern-based content extraction (RegexExtractionStrategy)
- **Chunking Strategies**: Content splitting with RegexChunking, TopicChunking, IdentityChunking

### Advanced Crawling Strategies
- **Deep Crawling**: BFS, DFS, Best-First search strategies for multi-page crawling
- **Adaptive Crawling**: Information foraging with statistical/embedding-based stopping criteria
- **URL Filtering**: Domain filters, pattern matching, content type filters, SEO filters
- **Link Scoring**: Keyword relevance, domain authority, freshness, path depth scoring
- **Crash Recovery**: State persistence with resume_state and on_state_change callbacks (v0.8.0+)

### Configuration & Settings
- **BrowserConfig**: Browser type, headless mode, viewport, user agent, proxy, geolocation
- **CrawlerRunConfig**: Cache mode, wait conditions, JS execution, hooks, extraction strategies
- **LLMConfig**: Provider configuration, retry logic, backoff strategies, temperature, max_tokens
- **ProxyConfig**: Proxy rotation, authentication, per-domain proxy assignment

### Browser Integration Features
- **Custom Hooks**: JavaScript injection at 8 pipeline stages (on_page_context_created, before_goto, after_goto, etc.)
- **Wait Conditions**: CSS selectors, network idle, load events, custom delays
- **JavaScript Execution**: Custom JS code execution, wait_for_images, lazy load handling
- **Virtual Scrolling**: Infinite scroll support with VirtualScrollConfig
- **Screenshots & PDFs**: Page capture, viewport configuration, wait conditions

### Docker Deployment
- **REST API**: FastAPI server with /crawl, /crawl/stream, /md, /llm, /html endpoints
- **Browser Pooling**: 3-tier pool (permanent/hot/cold) with automatic management
- **Monitoring**: Real-time dashboard, WebSocket streaming, Prometheus metrics
- **Authentication**: JWT token-based API security
- **Hooks System**: Sandboxed Python hook execution with security controls
- **MCP Integration**: Model Context Protocol server for AI assistant integration

### Installation & Setup
- **pip Installation**: Basic, with optional features ([torch], [transformer], [cosine], [pdf], [all])
- **Post-install Setup**: crawl4ai-setup for browser installation, NLTK data download
- **Diagnostics**: crawl4ai-doctor for installation verification
- **Docker Deployment**: Pre-built images, docker-compose configuration, cloud deployment patterns

### CLI Interface
- **crwl Command**: Rich CLI with deep crawl support, LLM extraction, output format selection
- **Deep Crawl Options**: --deep-crawl bfs/dfs, --max-pages, --max-depth
- **Browser Options**: --headless, --screenshot, --proxy, --user-agent
- **Cache Control**: --bypass-cache, --cache-mode
- **Content Filtering**: --css-selector, --exclude-tags, --word-count-threshold

### Python API Patterns
- **Context Managers**: `async with AsyncWebCrawler() as crawler:` pattern
- **Explicit Lifecycle**: await crawler.start(), await crawler.close() for long-running apps
- **Multi-Config**: Different CrawlerRunConfig for different URL patterns via url_matcher
- **Batch Processing**: arun_many() with custom dispatchers and rate limiting
- **Memory Management**: MemoryAdaptiveDispatcher for resource-aware task scheduling

### Integration Patterns
- **RAG Systems**: Clean markdown extraction for vector databases, document loaders
- **AI Agents**: Structured data extraction with Pydantic schemas for agent tools
- **Data Pipelines**: Async batch crawling with arun_many(), cache management
- **LLM Training**: High-quality markdown generation with content filtering
- **E-commerce Scraping**: Domain-specific crawlers (amazon_product, google_search)

### Error Handling & Reliability
- **Retry Logic**: Exponential backoff for LLM calls, configurable via LLMConfig
- **Cache Fallback**: Smart cache validation with graceful degradation
- **Error Context**: Detailed error messages with stack traces, network logs
- **Crash Recovery**: Deep crawl state persistence for long-running crawls
- **Memory Monitoring**: Automatic memory tracking and optimization recommendations

### Performance Optimization
- **Prefetch Mode**: 5-10x faster URL discovery by skipping markdown/extraction (v0.8.0+)
- **Browser Pool**: Reusable browser contexts for faster crawling
- **Content Caching**: Multi-level cache with fingerprint validation
- **Concurrent Crawling**: Parallel URL processing with memory-adaptive dispatching
- **Resource Management**: Automatic browser cleanup, memory pressure monitoring

### Security Features
- **Hook Sandboxing**: Restricted execution environment for custom hooks
- **File URL Blocking**: Prevents local file inclusion attacks in Docker API
- **Proxy Support**: Secure proxy authentication, rotation strategies
- **SSL Certificate Handling**: Certificate extraction and validation
- **Rate Limiting**: Domain-specific throttling to avoid detection

### Debugging & Monitoring
- **Verbose Logging**: Detailed logging with AsyncLogger, configurable verbosity
- **Network Inspection**: Request/response capture, console message logging
- **Browser Screenshots**: Visual debugging with screenshot capture
- **Performance Metrics**: Memory usage, timing, task statistics
- **Monitoring Dashboard**: Real-time visualization of crawl operations (Docker)

### Data Models & Types
- **CrawlResult**: Complete crawl output with HTML, markdown, media, links, metadata
- **MarkdownGenerationResult**: Multiple markdown variants (raw, fit, citations)
- **Link Objects**: Internal/external link classification with metadata
- **Media Objects**: Structured image/video/audio data with attributes
- **TokenUsage**: LLM token tracking for cost monitoring

### Legacy & Deprecated Features
- **Synchronous Crawler**: Selenium-based WebCrawler (deprecated, in crawl4ai/legacy/)
- **Backward Compatibility**: Inline kwargs in arun() (deprecated, use CrawlerRunConfig)
- **PyPDF2**: Replaced with pypdf in v0.7.8

### Version-Specific Features
- **v0.8.0**: Crash recovery, prefetch mode, security fixes (hooks disabled by default)
- **v0.7.8**: Bug fixes, HTML input format for LLM extraction, Pydantic v2 compatibility
- **v0.7.7**: Monitoring dashboard, browser pooling, WebSocket streaming
- **v0.7.5**: Docker hooks system, function-based hooks API, HTTPS preservation
- **v0.7.4**: LLMTableExtraction with chunking, dispatcher bug fixes
- **v0.7.3**: Undetected browser support, multi-config, memory monitoring
- **v0.7.0**: Adaptive crawling, virtual scroll, link analysis, async URL seeder
