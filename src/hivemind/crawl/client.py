"""Firecrawl client wrapper.

Provides crawl_website() and discover_urls() using the Firecrawl Python SDK.
Connects to the self-hosted instance by default.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from firecrawl import Firecrawl

from hivemind.crawl.service import FIRECRAWL_URL, ensure_firecrawl_running
from hivemind.crawl.urls import CrawlResult, deduplicate_urls, url_to_filename

if TYPE_CHECKING:
    from collections.abc import Callable


def _get_client() -> Firecrawl:
    """Create a Firecrawl client pointed at the self-hosted instance."""
    return Firecrawl(api_key="self-hosted", api_url=FIRECRAWL_URL)


def discover_urls(url: str, max_pages: int | None = None) -> list[str]:
    """Discover URLs on a site using Firecrawl's /map endpoint.

    Path-scoped by default: if the URL has a non-root path (e.g. /docs/),
    only URLs under that path are returned.

    Args:
        url: The starting URL.
        max_pages: Maximum number of URLs to discover.

    Returns:
        Deduplicated list of discovered URLs.
    """
    ensure_firecrawl_running()
    client = _get_client()

    kwargs: dict[str, int] = {}
    if max_pages is not None:
        kwargs["limit"] = max_pages

    result = client.map(url, **kwargs)
    urls = [link.url for link in result.links]
    return deduplicate_urls(urls)


def crawl_website(
    url: str,
    max_pages: int | None,
    output_dir: str,
    on_page_callback: Callable[[str, bool], None] | None = None,
) -> CrawlResult:
    """Crawl a website and save each page as markdown.

    Uses Firecrawl's /crawl endpoint which handles BFS discovery, JS rendering,
    anti-bot measures, and content cleaning internally.

    Args:
        url: The starting URL to crawl.
        max_pages: Maximum number of pages to crawl.
        output_dir: Directory to save markdown files.
        on_page_callback: Called after each page with (url, success).

    Returns:
        CrawlResult with statistics.
    """
    ensure_firecrawl_running()
    client = _get_client()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    kwargs: dict[str, object] = {
        "scrape_options": {
            "formats": ["markdown"],
            "onlyMainContent": True,
        },
    }
    if max_pages is not None:
        kwargs["limit"] = max_pages

    job = client.crawl(url, **kwargs)

    successful = 0
    failed = 0

    for doc in job.data:
        page_url = doc.metadata.url if doc.metadata else url
        if doc.markdown:
            filename = url_to_filename(page_url)
            filepath = output_path / f"{filename}.md"
            filepath.write_text(doc.markdown)
            successful += 1
            if on_page_callback:
                on_page_callback(page_url, True)
        else:
            failed += 1
            if on_page_callback:
                on_page_callback(page_url, False)

    return CrawlResult(
        total_pages=successful + failed,
        successful_pages=successful,
        failed_pages=failed,
    )
