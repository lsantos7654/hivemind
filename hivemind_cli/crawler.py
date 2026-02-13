"""Core crawling logic using crawl4ai."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from math import inf
from pathlib import Path
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, AsyncUrlSeeder, SeedingConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


@dataclass
class CrawlResult:
    """Statistics from a crawl operation."""

    total_pages: int
    successful_pages: int
    failed_pages: int


def url_to_filename(url: str) -> str:
    """Convert a URL to a safe filename.

    Args:
        url: The URL to convert

    Returns:
        A safe filename based on the URL path
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    if not path:
        path = "index"

    # Replace non-alphanumeric characters (except hyphens) with underscores
    filename = re.sub(r"[^\w\-]", "_", path)

    return filename


def create_path_filter(url: str) -> FilterChain:
    """Create a filter that restricts crawling to the starting URL's path.

    Args:
        url: The starting URL

    Returns:
        FilterChain configured to only allow URLs under the starting path
    """
    parsed = urlparse(url)
    # Create pattern that matches the starting URL and anything under it
    base_pattern = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if not base_pattern.endswith("/"):
        base_pattern += "*"
    else:
        base_pattern += "*"

    return FilterChain([URLPatternFilter(patterns=[base_pattern])])


def is_sitemap_url(url: str) -> bool:
    """Check if a URL points to a sitemap.

    Args:
        url: The URL to check

    Returns:
        True if the URL appears to be a sitemap, False otherwise
    """
    url_lower = url.lower()
    return url_lower.endswith(".xml") or url_lower.endswith(".xml.gz") or "sitemap" in url_lower


def extract_domain_from_sitemap_url(sitemap_url: str) -> str:
    """Extract domain from sitemap URL.

    AsyncUrlSeeder.urls() requires a domain, not a full URL.

    Args:
        sitemap_url: The sitemap URL

    Returns:
        The domain (e.g., "example.com")
    """
    parsed = urlparse(sitemap_url)
    return parsed.netloc


def create_clean_docs_config(stream: bool = False) -> dict:
    """Create configuration for clean documentation extraction.

    Uses crawl4ai's three-stage filtering pipeline:
    1. Structural exclusion (excluded_tags + excluded_selector)
    2. Content filtering (PruningContentFilter removes boilerplate)
    3. Clean output (fit_markdown)

    Validated by crawl4ai expert as the recommended pattern.

    Args:
        stream: Whether to enable streaming mode

    Returns:
        Dictionary of configuration parameters for CrawlerRunConfig
    """
    return {
        "stream": stream,
        "verbose": False,
        # NO css_selector - let full page through for robust extraction

        # Stage 1: Structural exclusion via tags
        "excluded_tags": ["nav", "header", "footer", "aside", "form", "button", "script", "style", "iframe"],

        # Stage 1: Structural exclusion via CSS selectors
        # Enhanced patterns based on crawl4ai expert recommendations
        "excluded_selector": """
            nav, header, footer, aside,
            [class*='lang'], [class*='language'], [class*='i18n'], [class*='locale'],
            [class*='navigation'], [class*='sidebar'], [class*='menu'],
            [class*='breadcrumb'], [class*='crumb'],
            [class*='social'], [class*='share'],
            [id*='lang'], [id*='language'], [id*='nav'], [id*='menu'],
            [role='navigation'], [role='banner'], [role='contentinfo'],
            .language-selector, .lang-switcher, .locale-selector,
            .breadcrumb, .breadcrumbs
        """,

        # Remove overlays and popups
        "remove_overlay_elements": True,

        # Content quality filters
        "word_count_threshold": 10,
        "exclude_external_links": True,
        "exclude_social_media_links": True,

        # Stage 2 & 3: Content filtering → fit_markdown generation
        "markdown_generator": DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(
                threshold=0.48,           # Balanced threshold (default)
                threshold_type="dynamic", # Adapts based on tag importance
                min_word_threshold=10,    # Skip very short blocks
            )
        ),
    }


async def preview_sitemap(sitemap_url: str, max_pages: int | None) -> list[str]:
    """Preview which URLs would be crawled from a sitemap.

    Args:
        sitemap_url: The sitemap URL
        max_pages: Maximum number of pages to discover (None for no limit)

    Returns:
        List of URLs from the sitemap
    """
    domain = extract_domain_from_sitemap_url(sitemap_url)

    config = SeedingConfig(
        source="sitemap",
        max_urls=max_pages if max_pages is not None else 999999,
        verbose=False,
        extract_head=False,
    )

    seeder = AsyncUrlSeeder()
    results = await seeder.urls(domain=domain, config=config)

    # AsyncUrlSeeder returns list of dicts, extract URLs
    return [r["url"] for r in results if "url" in r]


async def preview_crawl(url: str, max_pages: int | None) -> list[str]:
    """Preview which URLs would be crawled without actually crawling them.

    Uses prefetch mode for fast URL discovery (5-10x faster than full crawl).

    Args:
        url: The starting URL to crawl
        max_pages: Maximum number of pages to discover (None for no limit)

    Returns:
        List of URLs that would be crawled
    """
    path_filter = create_path_filter(url)

    strategy = BFSDeepCrawlStrategy(
        max_depth=inf,
        max_pages=max_pages if max_pages is not None else inf,
        include_external=False,
        filter_chain=path_filter,
    )

    config = CrawlerRunConfig(
        prefetch=True,  # Only extract URLs, skip content processing
        deep_crawl_strategy=strategy,
        verbose=False,
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(url=url, config=config)
        return [result.url for result in results if result.success]


async def crawl_website(
    url: str,
    max_pages: int | None,
    output_dir: str,
    on_page_callback: Callable[[str, bool], None] | None = None,
) -> CrawlResult:
    """Crawl a website and save each page as markdown.

    Uses structural filtering (CSS selectors + excluded tags) to remove
    navigation/UI chrome while preserving all documentation content.

    Args:
        url: The starting URL to crawl
        max_pages: Maximum number of pages to crawl (None for no limit)
        output_dir: Directory to save markdown files
        on_page_callback: Optional callback called after each page (url, success)

    Returns:
        CrawlResult with statistics
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create path filter to restrict to starting URL's path
    path_filter = create_path_filter(url)

    # Create BFS strategy with path filtering
    strategy = BFSDeepCrawlStrategy(
        max_depth=inf,
        max_pages=max_pages if max_pages is not None else inf,
        include_external=False,
        filter_chain=path_filter,
    )

    # Configure crawler with multi-layer content filtering for clean docs
    config_params = create_clean_docs_config(stream=True)
    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        **config_params,
    )

    successful = 0
    failed = 0
    total = 0

    async with AsyncWebCrawler() as crawler:
        # Use streaming mode to process results as they arrive
        async for page_result in await crawler.arun(url=url, config=config):
            total += 1

            if on_page_callback:
                on_page_callback(page_result.url, page_result.success)

            if page_result.success:
                filename = url_to_filename(page_result.url)
                filepath = output_path / f"{filename}.md"

                # Use fit_markdown for cleanest output (boilerplate removed)
                filepath.write_text(page_result.markdown.fit_markdown)
                successful += 1
            else:
                failed += 1

    return CrawlResult(
        total_pages=total,
        successful_pages=successful,
        failed_pages=failed,
    )


async def crawl_from_sitemap(
    sitemap_url: str,
    max_pages: int | None,
    output_dir: str,
    on_page_callback: Callable[[str, bool], None] | None = None,
) -> CrawlResult:
    """Crawl URLs from a sitemap and save each page as markdown.

    Uses structural filtering (CSS selectors + excluded tags) to remove
    navigation/UI chrome while preserving all documentation content.

    Args:
        sitemap_url: The sitemap URL
        max_pages: Maximum number of pages to crawl (None for no limit)
        output_dir: Directory to save markdown files
        on_page_callback: Optional callback called after each page (url, success)

    Returns:
        CrawlResult with statistics
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Step 1: Get URLs from sitemap
    urls = await preview_sitemap(sitemap_url=sitemap_url, max_pages=max_pages)

    if not urls:
        return CrawlResult(total_pages=0, successful_pages=0, failed_pages=0)

    # Step 2: Configure crawler with multi-layer content filtering for clean docs
    config_params = create_clean_docs_config(stream=True)
    config = CrawlerRunConfig(**config_params)

    successful = 0
    failed = 0
    total = 0

    async with AsyncWebCrawler() as crawler:
        # Use arun_many to crawl all URLs from sitemap
        async for page_result in await crawler.arun_many(urls=urls, config=config):
            total += 1

            if on_page_callback:
                on_page_callback(page_result.url, page_result.success)

            if page_result.success:
                filename = url_to_filename(page_result.url)
                filepath = output_path / f"{filename}.md"

                # Use fit_markdown for cleanest output (boilerplate removed)
                filepath.write_text(page_result.markdown.fit_markdown)
                successful += 1
            else:
                failed += 1

    return CrawlResult(
        total_pages=total,
        successful_pages=successful,
        failed_pages=failed,
    )
