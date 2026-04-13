"""Content extraction and crawl orchestration.

For each URL, tries the raw .md endpoint first (source markdown). If
the site doesn't serve one, falls back to fetching HTML and extracting
clean markdown via trafilatura.

Pure Python, no browser, no Docker.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import trafilatura

from hivemind.crawl.discovery import discover_urls
from hivemind.crawl.urls import CrawlResult, url_to_filename

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

# Max concurrent HTTP requests to avoid hammering doc sites.
_CONCURRENCY = 10


def _md_url(url: str) -> str:
    """Derive the raw markdown URL for a page.

    /plugin-development       → /plugin-development.md
    /plugin-development/      → /plugin-development/index.md
    """
    if url.endswith("/"):
        return url + "index.md"
    return url + ".md"


def _looks_like_markdown(text: str) -> bool:
    """Quick check that a response body is markdown, not HTML."""
    stripped = text.lstrip()
    if not stripped:
        return False
    # HTML documents start with < (doctype, html tag, etc.)
    return not stripped.startswith("<")


def _extract_from_html(html: str, url: str) -> str | None:
    """Extract clean markdown from HTML using trafilatura."""
    return trafilatura.extract(
        html,
        url=url,
        output_format="markdown",
        include_formatting=True,
        favor_precision=True,
        include_tables=True,
        include_links=False,
        include_comments=False,
    )


async def _fetch_and_extract(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    url: str,
    output_path: Path,
    on_page_callback: Callable[[str, bool], None] | None,
) -> bool:
    """Get markdown for a single URL. Returns True on success.

    Tries the raw .md endpoint first. If the site serves source
    markdown there, we use it directly — it's always higher quality
    than any extraction. Otherwise, fetches the HTML page and extracts
    content via trafilatura.
    """
    markdown: str | None = None

    async with semaphore:
        # Try raw .md first
        try:
            md_response = await client.get(_md_url(url))
            if md_response.status_code == 200 and _looks_like_markdown(md_response.text):
                markdown = md_response.text
                logger.debug("Raw .md hit for %s", url)
        except httpx.HTTPError:
            pass  # .md endpoint doesn't exist, move on

        # Fall back to HTML extraction
        if not markdown:
            try:
                response = await client.get(url)
                response.raise_for_status()
            except (httpx.HTTPError, httpx.InvalidURL) as e:
                logger.warning("Failed to fetch %s: %s", url, e)
                if on_page_callback:
                    on_page_callback(url, False)
                return False

            markdown = _extract_from_html(response.text, url)

    if not markdown:
        logger.warning("No content extracted from %s", url)
        if on_page_callback:
            on_page_callback(url, False)
        return False

    filename = url_to_filename(url)
    filepath = output_path / f"{filename}.md"
    filepath.write_text(markdown)

    if on_page_callback:
        on_page_callback(url, True)
    return True


async def crawl_website(
    url: str,
    max_pages: int | None,
    output_dir: str,
    on_page_callback: Callable[[str, bool], None] | None = None,
) -> CrawlResult:
    """Discover URLs, fetch content, write markdown to disk.

    For each discovered URL, tries the raw .md endpoint first for
    source-quality markdown. Falls back to HTML extraction via
    trafilatura when raw markdown isn't available.

    Args:
        url: The starting URL to crawl.
        max_pages: Maximum number of pages to crawl.
        output_dir: Directory to save markdown files.
        on_page_callback: Called after each page with (url, success).

    Returns:
        CrawlResult with statistics.
    """
    urls = await discover_urls(url, max_pages=max_pages)

    if not urls:
        return CrawlResult(total_pages=0, successful_pages=0, failed_pages=0)

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    semaphore = asyncio.Semaphore(_CONCURRENCY)

    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        tasks = [_fetch_and_extract(client, semaphore, page_url, output_path, on_page_callback) for page_url in urls]
        results = await asyncio.gather(*tasks)

    successful = sum(results)
    failed = len(results) - successful

    return CrawlResult(
        total_pages=len(urls),
        successful_pages=successful,
        failed_pages=failed,
    )
