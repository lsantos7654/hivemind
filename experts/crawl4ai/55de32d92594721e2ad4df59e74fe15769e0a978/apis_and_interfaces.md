# Crawl4AI APIs and Interfaces

## Public APIs and Entry Points

### AsyncWebCrawler - Core API

The primary interface for web crawling operations.

#### Basic Usage Pattern

```python
import asyncio
from crawl4ai import AsyncWebCrawler

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url="https://example.com")
        print(result.markdown)

asyncio.run(main())
```

#### Explicit Lifecycle Management

```python
async def long_running_app():
    crawler = AsyncWebCrawler()
    await crawler.start()

    # Use crawler multiple times
    result1 = await crawler.arun("https://example.com")
    result2 = await crawler.arun("https://another.com")

    await crawler.close()
```

### Key Classes and Methods

#### AsyncWebCrawler

**Constructor:**
```python
AsyncWebCrawler(
    config: BrowserConfig = None,           # Browser configuration
    crawler_strategy: AsyncCrawlerStrategy = None,  # Custom strategy
    base_directory: str = "~",              # Cache base directory
    thread_safe: bool = False,              # Thread-safe operations
    logger: AsyncLoggerBase = None          # Custom logger
)
```

**Main Methods:**

##### arun() - Single URL Crawling
```python
async def arun(
    url: str,                               # URL to crawl
    config: CrawlerRunConfig = None,        # Per-crawl configuration
    **kwargs                                # Deprecated: inline config
) -> CrawlResult
```

**Example:**
```python
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

browser_config = BrowserConfig(
    headless=True,
    verbose=True,
    extra_args=["--disable-gpu"]
)

crawl_config = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    word_count_threshold=50,
    excluded_tags=["nav", "footer"],
    wait_until="networkidle"
)

async with AsyncWebCrawler(config=browser_config) as crawler:
    result = await crawler.arun(
        url="https://example.com",
        config=crawl_config
    )
    print(result.markdown.raw_markdown)
```

##### arun_many() - Batch Crawling
```python
async def arun_many(
    urls: List[str],                        # URLs to crawl
    config: Union[CrawlerRunConfig, List[CrawlerRunConfig]] = None,
    dispatcher: BaseDispatcher = None,      # Custom dispatcher
    **kwargs
) -> List[CrawlResult]
```

**Example:**
```python
urls = [
    "https://example.com/page1",
    "https://example.com/page2",
    "https://example.com/page3"
]

results = await crawler.arun_many(urls, config=crawl_config)
for result in results:
    print(f"{result.url}: {len(result.markdown)} chars")
```

**Multi-Config Pattern:**
```python
from crawl4ai import MatchMode

configs = [
    CrawlerRunConfig(
        url_matcher=["*docs*", "*documentation*"],
        cache_mode=CacheMode.WRITE_ONLY,
        markdown_generator=DefaultMarkdownGenerator(
            options={"include_links": True}
        )
    ),
    CrawlerRunConfig(
        url_matcher=lambda url: 'blog' in url,
        cache_mode=CacheMode.BYPASS
    ),
    CrawlerRunConfig()  # Fallback for all other URLs
]

results = await crawler.arun_many(urls, config=configs)
```

##### aprocess_html() - Process HTML Without Fetching
```python
async def aprocess_html(
    html: str,                              # HTML content
    url: str = "",                          # Base URL for links
    config: CrawlerRunConfig = None
) -> CrawlResult
```

**Example:**
```python
html = "<html><body><h1>Test</h1></body></html>"
result = await crawler.aprocess_html(html, url="https://example.com")
```

##### awarmup() - Browser Warmup
```python
async def awarmup(max_turns: int = 1) -> None
```

Performs warmup sequence to initialize browser and cache.

### Configuration Classes

#### BrowserConfig

```python
from crawl4ai import BrowserConfig

config = BrowserConfig(
    # Browser Type
    browser_type: str = "chromium",         # "chromium", "firefox", "webkit", "undetected"
    headless: bool = True,                  # Run in headless mode

    # Browser Arguments
    extra_args: List[str] = [],             # Additional browser args
    user_agent: str = None,                 # Custom user agent
    viewport: Dict = {"width": 1920, "height": 1080},

    # Authentication & Profiles
    user_data_dir: str = None,              # Persistent profile directory
    use_persistent_context: bool = False,   # Reuse browser context

    # Proxy Settings
    proxy: str = None,                      # Proxy URL
    proxy_config: ProxyConfig = None,       # Advanced proxy config

    # Geolocation
    geolocation: GeolocationConfig = None,  # Set geolocation

    # Advanced
    accept_downloads: bool = False,         # Enable file downloads
    downloads_path: str = None,             # Download directory
    storage_state: str = None,              # Saved auth state

    # Debugging
    verbose: bool = False,                  # Enable verbose logging
    light_mode: bool = False,               # Minimal features mode
    text_mode: bool = False,                # Disable image loading
)
```

**Example - Undetected Browser:**
```python
config = BrowserConfig(
    browser_type="undetected",
    headless=True,
    extra_args=[
        "--disable-blink-features=AutomationControlled",
        "--disable-web-security"
    ]
)
```

#### CrawlerRunConfig

```python
from crawl4ai import CrawlerRunConfig, CacheMode

config = CrawlerRunConfig(
    # URL Matching (for multi-config)
    url_matcher: Union[List[str], Callable] = None,

    # Cache Control
    cache_mode: CacheMode = CacheMode.ENABLED,
    bypass_cache: bool = False,             # Deprecated: use cache_mode

    # Wait Conditions
    wait_until: str = "domcontentloaded",   # "load", "networkidle", etc.
    wait_for: str = None,                   # CSS selector to wait for
    delay_before_return_html: float = 0.1,  # Post-load delay

    # JavaScript Execution
    js_code: Union[str, List[str]] = None,  # Custom JS to execute
    js_only: bool = False,                  # Skip initial page load
    wait_for_images: bool = True,           # Wait for lazy images

    # Content Filtering
    word_count_threshold: int = 5,          # Min words per block
    excluded_tags: List[str] = ["nav", "footer", "header"],
    exclude_external_links: bool = False,
    exclude_social_media_links: bool = False,

    # Markdown Generation
    markdown_generator: MarkdownGenerationStrategy = None,

    # Extraction
    extraction_strategy: ExtractionStrategy = None,
    chunking_strategy: ChunkingStrategy = IdentityChunking(),

    # Content Filters
    content_filter: RelevantContentFilter = None,

    # CSS Selector Targeting
    css_selector: str = None,               # Extract specific element

    # Screenshots & PDFs
    screenshot: bool = False,               # Capture screenshot
    screenshot_wait_for: float = None,      # Wait before screenshot
    pdf: bool = False,                      # Generate PDF

    # Magic Mode (Auto-optimization)
    magic: bool = False,

    # Hooks (Custom code injection)
    hooks: Dict[str, str] = None,

    # Deep Crawling
    deep_crawl: bool = False,
    deep_crawl_strategy: DeepCrawlStrategy = None,

    # Virtual Scrolling
    virtual_scroll_config: VirtualScrollConfig = None,

    # Link Preview
    link_preview_config: LinkPreviewConfig = None,
    score_links: bool = False,

    # Prefetch Mode (v0.8.0+)
    prefetch: bool = False,                 # Fast URL discovery only

    # Session Management
    session_id: str = None,                 # Reuse browser session

    # Mean Delay (Rate Limiting)
    mean_delay: float = 0.1,                # Delay between requests
    max_range: float = 0.3,                 # Random delay range
)
```

### Extraction Strategies

#### LLMExtractionStrategy - LLM-Powered Extraction

```python
from crawl4ai import LLMExtractionStrategy, LLMConfig
from pydantic import BaseModel, Field

# Define schema
class Article(BaseModel):
    title: str = Field(description="Article title")
    author: str = Field(description="Author name")
    date: str = Field(description="Publication date")
    summary: str = Field(description="Brief summary")

# Configure strategy
strategy = LLMExtractionStrategy(
    llm_config=LLMConfig(
        provider="openai/gpt-4o",           # LiteLLM provider string
        api_token=os.getenv("OPENAI_API_KEY"),
        temperature=0.0,
        max_tokens=4000,
        # Retry configuration
        backoff_base_delay=2,
        backoff_max_attempts=5,
        backoff_exponential_factor=2
    ),
    schema=Article.schema(),                # Pydantic schema
    extraction_type="schema",               # "schema", "block", "inferred"
    instruction="Extract article metadata and content",
    input_format="markdown",                # "markdown", "html", "fit_markdown"
    verbose=True
)

config = CrawlerRunConfig(extraction_strategy=strategy)
result = await crawler.arun(url, config=config)
articles = json.loads(result.extracted_content)
```

#### JsonCssExtractionStrategy - CSS Selector Extraction

```python
from crawl4ai import JsonCssExtractionStrategy

schema = {
    "name": "Product List",
    "baseSelector": "div.product",
    "fields": [
        {
            "name": "title",
            "selector": "h2.product-title",
            "type": "text"
        },
        {
            "name": "price",
            "selector": "span.price",
            "type": "text"
        },
        {
            "name": "image",
            "selector": "img.product-image",
            "type": "attribute",
            "attribute": "src"
        },
        {
            "name": "rating",
            "selector": "div.rating",
            "type": "text"
        }
    ]
}

strategy = JsonCssExtractionStrategy(schema, verbose=True)
config = CrawlerRunConfig(extraction_strategy=strategy)
result = await crawler.arun(url, config=config)
products = json.loads(result.extracted_content)
```

#### CosineStrategy - Semantic Similarity Extraction

```python
from crawl4ai import CosineStrategy

strategy = CosineStrategy(
    semantic_filter="machine learning tutorials",
    word_count_threshold=50,
    max_dist=0.2,                           # Clustering threshold
    linkage_method="ward",                  # Clustering method
    top_k=3,                                # Top K clusters
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

config = CrawlerRunConfig(extraction_strategy=strategy)
result = await crawler.arun(url, config=config)
```

### Markdown Generation

#### DefaultMarkdownGenerator with Content Filters

```python
from crawl4ai import (
    DefaultMarkdownGenerator,
    PruningContentFilter,
    BM25ContentFilter
)

# Pruning Filter (Heuristic-based)
generator = DefaultMarkdownGenerator(
    content_filter=PruningContentFilter(
        threshold=0.48,                     # Relevance threshold
        threshold_type="fixed",             # "fixed" or "dynamic"
        min_word_threshold=0
    )
)

# BM25 Filter (Query-based)
generator = DefaultMarkdownGenerator(
    content_filter=BM25ContentFilter(
        user_query="latest AI research",
        bm25_threshold=1.0
    )
)

config = CrawlerRunConfig(markdown_generator=generator)
result = await crawler.arun(url, config=config)
print(result.markdown.fit_markdown)     # Filtered markdown
```

### Deep Crawling Strategies

#### BFS Deep Crawl

```python
from crawl4ai import BFSDeepCrawlStrategy, URLPatternFilter, KeywordRelevanceScorer

strategy = BFSDeepCrawlStrategy(
    max_depth=3,                            # Maximum depth
    max_pages=20,                           # Maximum pages
    allow_offsite=False,                    # Stay on domain

    # URL Filtering
    filter_chain=FilterChain([
        URLPatternFilter(patterns=["*/blog/*", "*/article/*"]),
        DomainFilter(allowed_domains=["example.com"])
    ]),

    # Link Scoring
    scorer=KeywordRelevanceScorer(
        keywords=["technology", "AI", "machine learning"],
        threshold=0.3
    ),

    # Crash Recovery (v0.8.0+)
    resume_state=None,                      # Resume from saved state
    on_state_change=lambda state: save_to_redis(state),  # Callback
)

config = CrawlerRunConfig(
    deep_crawl=True,
    deep_crawl_strategy=strategy
)

result = await crawler.arun("https://example.com", config=config)
```

#### DFS Deep Crawl

```python
from crawl4ai import DFSDeepCrawlStrategy

strategy = DFSDeepCrawlStrategy(
    max_depth=5,
    max_pages=50,
    priority_order="relevance",             # "relevance" or "appearance"
)
```

#### Best-First Crawl

```python
from crawl4ai import BestFirstCrawlingStrategy, CompositeScorer

strategy = BestFirstCrawlingStrategy(
    max_pages=30,
    scorer=CompositeScorer([
        KeywordRelevanceScorer(keywords=["AI"], weight=0.5),
        DomainAuthorityScorer(weight=0.3),
        FreshnessScorer(weight=0.2)
    ])
)
```

### Adaptive Crawling

```python
from crawl4ai import AdaptiveCrawler, AdaptiveConfig

adaptive_config = AdaptiveConfig(
    confidence_threshold=0.7,               # Stop when confident
    max_depth=5,
    max_pages=50,
    strategy="statistical"                  # or "embedding"
)

async with AsyncWebCrawler() as crawler:
    adaptive = AdaptiveCrawler(crawler, adaptive_config)
    state = await adaptive.digest(
        start_url="https://news.example.com",
        query="latest technology news"
    )

    print(f"Crawled {len(state.crawled_urls)} pages")
    print(f"Confidence: {state.metrics.get('confidence', 0)}")
```

### Hooks System

```python
from crawl4ai import hooks_to_string

# Define hooks as Python functions
async def on_page_context_created(page, context, **kwargs):
    """Block images to speed up crawling"""
    await context.route("**/*.{png,jpg,jpeg,gif,webp}",
                       lambda route: route.abort())
    return page

async def before_goto(page, context, url, **kwargs):
    """Add custom headers"""
    await page.set_extra_http_headers({
        'X-Custom-Header': 'value'
    })
    return page

async def after_goto(page, context, url, **kwargs):
    """Wait for custom condition"""
    await page.wait_for_selector(".content-loaded")
    return page

# Convert to string format (for REST API)
hooks_code = hooks_to_string({
    "on_page_context_created": on_page_context_created,
    "before_goto": before_goto,
    "after_goto": after_goto
})

# Use with crawler
config = CrawlerRunConfig(hooks={
    "on_page_context_created": on_page_context_created,
    "before_goto": before_goto,
    "after_goto": after_goto
})
```

**Available Hook Points:**
1. `on_browser_created`: After browser launch
2. `on_page_context_created`: After context creation
3. `before_goto`: Before navigation
4. `after_goto`: After page load
5. `before_retrieve_html`: Before HTML extraction
6. `before_return_html`: Before final processing
7. `on_execution_started`: Start of crawl
8. `on_error`: Error handling

### CrawlResult Object

```python
class CrawlResult:
    url: str                                # Crawled URL
    html: str                               # Raw HTML
    cleaned_html: str                       # Cleaned HTML
    fit_html: str                           # Filtered HTML (if content filter used)

    # Markdown variants
    markdown: MarkdownGenerationResult      # Markdown object
    # - markdown.raw_markdown
    # - markdown.markdown_with_citations
    # - markdown.fit_markdown
    # - markdown.references_markdown

    # Extracted data
    extracted_content: str                  # JSON from extraction strategy
    media: Dict[str, List[Dict]]           # Images, videos, audio
    links: Dict[str, List[Dict]]           # Internal, external links

    # Metadata
    metadata: dict                          # Page metadata
    ssl_certificate: SSLCertificate        # SSL info
    response_headers: dict                  # HTTP headers
    status_code: int                        # HTTP status
    redirected_url: str                     # Final URL after redirects

    # Optional outputs
    screenshot: str                         # Base64 screenshot
    pdf: bytes                              # PDF bytes
    mhtml: str                              # MHTML archive
    tables: List[Dict]                      # Extracted tables

    # Debug info
    network_requests: List[Dict]            # Network activity
    console_messages: List[Dict]            # Console logs
    js_execution_result: Dict               # JS execution results

    # Status
    success: bool                           # Crawl success
    error_message: str                      # Error details

    # Cache info
    cache_status: str                       # "hit", "miss", "hit_validated"
    cached_at: float                        # Cache timestamp
```

## CLI Interface

### crwl Command

```bash
# Basic crawl
crwl https://example.com

# Output formats
crwl https://example.com -o markdown
crwl https://example.com -o json
crwl https://example.com -o html

# Deep crawl
crwl https://example.com --deep-crawl bfs --max-pages 20
crwl https://example.com --deep-crawl dfs --max-depth 5

# LLM extraction
crwl https://example.com -q "Extract all product information"

# Browser options
crwl https://example.com --headless false --screenshot

# Cache control
crwl https://example.com --bypass-cache
crwl https://example.com --cache-mode write-only

# Proxy
crwl https://example.com --proxy http://proxy:8080

# Advanced
crwl https://example.com \
  --css-selector "article.content" \
  --exclude-tags nav,footer \
  --wait-for ".content-loaded" \
  --js-code "document.querySelector('.accept').click()"
```

## Docker REST API

### Endpoints

#### POST /crawl - Batch Crawling
```python
import requests

response = requests.post(
    "http://localhost:11235/crawl",
    json={
        "urls": ["https://example.com"],
        "priority": 10,
        "crawler_params": {
            "headless": True,
            "page_timeout": 30000
        },
        "extra": {
            "word_count_threshold": 50,
            "extraction_strategy": {
                "type": "JsonCssExtractionStrategy",
                "schema": {...}
            }
        },
        "hooks": {
            "before_goto": "async def hook(page, **kw): ..."
        }
    }
)

if response.status_code == 200:
    results = response.json()["results"]
```

#### GET /crawl/stream - Streaming Crawl
```python
import httpx

async with httpx.AsyncClient() as client:
    async with client.stream(
        "POST",
        "http://localhost:11235/crawl/stream",
        json={"urls": urls, "extra": {...}}
    ) as response:
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = json.loads(line[6:])
                print(data["url"], data["status"])
```

#### POST /md - Markdown Extraction
```python
response = requests.post(
    "http://localhost:11235/md",
    json={"url": "https://example.com"}
)
markdown = response.text
```

#### POST /llm - LLM Q&A
```python
response = requests.post(
    "http://localhost:11235/llm",
    json={
        "url": "https://example.com",
        "question": "What is the main topic?",
        "provider": "openai/gpt-4o",
        "api_token": "..."
    }
)
answer = response.json()["answer"]
```

The API is designed for progressive disclosure - simple tasks require minimal configuration, while advanced features are available through optional parameters.
