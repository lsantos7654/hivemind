"""Core crawling logic using crawl4ai."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from math import inf
from pathlib import Path
from urllib.parse import urlparse

import httpx

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, AsyncUrlSeeder, SeedingConfig
from crawl4ai.content_filter_strategy import PruningContentFilter
from crawl4ai.deep_crawling import BFSDeepCrawlStrategy
from crawl4ai.deep_crawling.filters import FilterChain, URLPatternFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


def normalize_url(url: str) -> str:
    """Normalize URL for deduplication.

    - Remove fragment (#section)
    - Lowercase scheme and domain
    - Remove trailing slash (except root)
    """
    parsed = urlparse(url)
    normalized = parsed._replace(fragment="")
    normalized = normalized._replace(
        scheme=normalized.scheme.lower(),
        netloc=normalized.netloc.lower()
    )

    path = normalized.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    normalized = normalized._replace(path=path)

    return normalized.geturl()


def deduplicate_urls(urls: list[str]) -> list[str]:
    """Deduplicate URLs preserving order."""
    seen = set()
    result = []
    for url in urls:
        norm = normalize_url(url)
        if norm not in seen:
            seen.add(norm)
            result.append(url)
    return result


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
    urls = [r["url"] for r in results if "url" in r]
    return deduplicate_urls(urls)


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
        discovered_urls = [result.url for result in results if result.success]
        return deduplicate_urls(discovered_urls)


async def crawl_website(
    url: str,
    max_pages: int | None,
    output_dir: str,
    on_page_callback: Callable[[str, bool], None] | None = None,
) -> CrawlResult:
    """Crawl a website by discovering URLs first, then crawling each.

    This two-phase approach avoids BFS early termination issues:
    1. Discovery: Fast BFS prefetch to find all URLs
    2. Execution: Crawl all discovered URLs (no BFS recursion)

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

    # Phase 1: Discovery (fast BFS prefetch)
    discovered_urls = await preview_crawl(url=url, max_pages=max_pages)

    # Phase 2: Execution (crawl all discovered URLs)
    successful = 0
    failed = 0
    config = CrawlerRunConfig(**create_clean_docs_config(stream=True))

    async with AsyncWebCrawler() as crawler:
        async for page_result in await crawler.arun_many(
            urls=discovered_urls,
            config=config
        ):
            if on_page_callback:
                on_page_callback(page_result.url, page_result.success)

            if page_result.success and page_result.markdown:
                filename = url_to_filename(page_result.url)
                filepath = output_path / f"{filename}.md"
                filepath.write_text(page_result.markdown.fit_markdown)
                successful += 1
            else:
                failed += 1

    return CrawlResult(
        total_pages=len(discovered_urls),
        successful_pages=successful,
        failed_pages=failed,
    )


def _raw_markdown_url(url: str) -> str:
    """Return the raw markdown URL for a given page URL.

    Rspress serves source markdown at:
    - <url>.md        for regular pages (no trailing slash)
    - <url>index.md   for directory-style URLs (trailing slash)
    """
    if url.endswith("/"):
        return url + "index.md"
    return url + ".md"


def _is_markdown_response(text: str) -> bool:
    return bool(text) and not text.strip().startswith("<")


async def supports_raw_markdown(url: str) -> bool:
    """Check if a site serves raw markdown by appending .md to URLs.

    Some documentation sites (e.g. rspress-based) expose a .md endpoint
    for each page that returns clean source markdown instead of rendered HTML.

    Args:
        url: A page URL to probe

    Returns:
        True if the site returns non-HTML content for <url>.md or <url>index.md
    """
    md_url = _raw_markdown_url(url)
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
            response = await client.get(md_url)
            if response.status_code == 200 and _is_markdown_response(response.text):
                return True
    except Exception:
        pass
    return False


async def crawl_urls_raw_markdown(
    urls: list[str],
    output_dir: str,
    on_page_callback: Callable[[str, bool], None] | None = None,
) -> CrawlResult:
    """Fetch raw markdown for each URL by appending .md to the URL path.

    Used for sites that support a .md suffix endpoint (e.g. rspress-based docs).
    Much faster and more accurate than browser-based scraping since it retrieves
    the source markdown directly.

    Args:
        urls: List of page URLs to fetch
        output_dir: Directory to save markdown files
        on_page_callback: Optional callback called after each page (url, success)

    Returns:
        CrawlResult with statistics
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Deduplicate URLs (e.g. /foo/ and /foo are the same page)
    urls = deduplicate_urls(urls)

    successful = 0
    failed = 0

    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        for page_url in urls:
            md_url = _raw_markdown_url(page_url)
            try:
                response = await client.get(md_url)
                if response.status_code == 200 and _is_markdown_response(response.text):
                    filename = url_to_filename(page_url)
                    filepath = output_path / f"{filename}.md"
                    filepath.write_text(response.text)
                    successful += 1
                    if on_page_callback:
                        on_page_callback(page_url, True)
                    continue
            except Exception:
                pass
            failed += 1
            if on_page_callback:
                on_page_callback(page_url, False)

    return CrawlResult(
        total_pages=len(urls),
        successful_pages=successful,
        failed_pages=failed,
    )


async def crawl_with_fallback(
    urls: list[str],
    output_dir: str,
    on_page_callback: Callable[[str, bool], None] | None = None,
) -> CrawlResult:
    """Try raw markdown first, fall back to browser for failures.

    This handles the "empty parent" edge case where /get-started/
    doesn't exist but /get-started/installation/ does.

    Args:
        urls: List of page URLs to fetch
        output_dir: Directory to save markdown files
        on_page_callback: Optional callback called after each page (url, success)

    Returns:
        CrawlResult with statistics
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    urls = deduplicate_urls(urls)
    successful = 0
    failed_urls: list[str] = []

    # Phase 1: Try raw markdown for all URLs
    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        for page_url in urls:
            md_url = _raw_markdown_url(page_url)
            try:
                response = await client.get(md_url)
                if response.status_code == 200 and _is_markdown_response(response.text):
                    filename = url_to_filename(page_url)
                    filepath = output_path / f"{filename}.md"
                    filepath.write_text(response.text)
                    successful += 1
                    if on_page_callback:
                        on_page_callback(page_url, True)
                    continue
            except Exception:
                pass

            # Track failures for browser retry
            failed_urls.append(page_url)

    # Phase 2: Retry failures with browser rendering
    if failed_urls:
        config = CrawlerRunConfig(**create_clean_docs_config(stream=True))

        async with AsyncWebCrawler() as crawler:
            async for page_result in await crawler.arun_many(
                urls=failed_urls,
                config=config
            ):
                if page_result.success and page_result.markdown:
                    filename = url_to_filename(page_result.url)
                    filepath = output_path / f"{filename}.md"
                    filepath.write_text(page_result.markdown.fit_markdown)
                    successful += 1
                    if on_page_callback:
                        on_page_callback(page_result.url, True)
                else:
                    if on_page_callback:
                        on_page_callback(page_result.url, False)

    failed = len(urls) - successful

    return CrawlResult(
        total_pages=len(urls),
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
