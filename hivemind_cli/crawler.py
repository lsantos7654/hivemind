"""Core crawling logic using crawl4ai."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from math import inf
from pathlib import Path
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter


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


async def preview_crawl(url: str, max_pages: int) -> list[str]:
    """Preview which URLs would be crawled without actually crawling them.

    Uses prefetch mode for fast URL discovery (5-10x faster than full crawl).

    Args:
        url: The starting URL to crawl
        max_pages: Maximum number of pages to discover

    Returns:
        List of URLs that would be crawled
    """
    path_filter = create_path_filter(url)

    strategy = BFSDeepCrawlStrategy(
        max_depth=inf,
        max_pages=max_pages,
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
    max_pages: int,
    output_dir: str,
    on_page_callback: Callable[[str, bool], None] | None = None,
) -> CrawlResult:
    """Crawl a website and save each page as markdown.

    Uses structural filtering (CSS selectors + excluded tags) to remove
    navigation/UI chrome while preserving all documentation content.

    Args:
        url: The starting URL to crawl
        max_pages: Maximum number of pages to crawl
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
        max_pages=max_pages,
        include_external=False,
        filter_chain=path_filter,
    )

    # Configure crawler with structural filtering only (no aggressive content pruning)
    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        stream=True,
        verbose=False,
        # Target main content areas
        css_selector="main, article, .content, .documentation, .doc-content, .docs-content",
        # Remove UI chrome elements
        excluded_tags=["nav", "header", "footer", "aside", "form", "button"],
        remove_overlay_elements=True,
        # Keep ALL content - don't filter by word count
        word_count_threshold=0,
        # Remove social links but keep documentation links
        exclude_social_media_links=True,
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

                # Use raw_markdown (structural filtering only, no content pruning)
                filepath.write_text(page_result.markdown.raw_markdown)
                successful += 1
            else:
                failed += 1

    return CrawlResult(
        total_pages=total,
        successful_pages=successful,
        failed_pages=failed,
    )
