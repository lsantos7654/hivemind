"""Crawl orchestration and per-page extraction.

Top-level flow:

    probe_site(url)                    → SiteProfile
    optional browser_session()         → AsyncWebCrawler (only if needed)
    discover_urls(url, profile, …)     → list[str]
    extract_page(url, profile, …)      per URL, dispatched on profile

Per-URL extraction tries source markdown when published, falls back to
httpx + trafilatura on static HTML, and finally renders via the shared
browser when the page is JS-only.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import AsyncExitStack
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import trafilatura

from hivemind.crawl.browser import browser_extract, browser_session
from hivemind.crawl.discovery import discover_urls
from hivemind.crawl.probe import SiteProfile, probe_site
from hivemind.crawl.urls import CrawlResult, url_to_filename

if TYPE_CHECKING:
    from collections.abc import Callable

    from crawl4ai import AsyncWebCrawler

    from hivemind.crawl.discovery import LeafProgress

logger = logging.getLogger(__name__)

# httpx fan-out for the static channels.
_HTTP_CONCURRENCY = 10
# Browser concurrency — Chromium tabs are ~80MB each; keep this low.
_BROWSER_CONCURRENCY = 3


def _md_url(url: str) -> str:
    """Raw markdown URL for a doc page (Hugo / mkdocs publish these)."""
    if url.endswith("/"):
        return url + "index.md"
    return url + ".md"


def _looks_like_markdown(text: str) -> bool:
    stripped = text.lstrip()
    if not stripped:
        return False
    return not stripped.startswith("<")


def _extract_from_html(html: str, url: str) -> str | None:
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


async def _try_md_endpoint(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        response = await client.get(_md_url(url))
    except httpx.HTTPError:
        return None
    if response.status_code == 200 and _looks_like_markdown(response.text):
        return response.text
    return None


async def _try_html_extraction(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        response = await client.get(url)
        response.raise_for_status()
    except (httpx.HTTPError, httpx.InvalidURL) as e:
        logger.warning("HTML fetch failed for %s: %s", url, e)
        return None
    return _extract_from_html(response.text, url)


async def extract_page(
    url: str,
    profile: SiteProfile,
    client: httpx.AsyncClient,
    browser: AsyncWebCrawler | None,
    http_sem: asyncio.Semaphore,
    browser_sem: asyncio.Semaphore,
) -> str | None:
    """Get markdown for a single URL using the strategy in ``profile``.

    Each strategy can fall through to the next when its primary channel
    yields nothing — keeps coverage high even when the per-page
    behavior diverges from what the seed-based probe predicted.
    """
    strategy = profile.extraction_strategy

    if strategy == "md":
        async with http_sem:
            md = await _try_md_endpoint(client, url)
        if md:
            return md
        # `.md` works for the seed but may 404 elsewhere — fall back.
        async with http_sem:
            return await _try_html_extraction(client, url)

    if strategy == "http":
        async with http_sem:
            return await _try_html_extraction(client, url)

    # browser
    if browser is None:
        msg = "browser extraction requested but no browser session provided"
        raise RuntimeError(msg)
    async with browser_sem:
        md = await browser_extract(browser, url)
    if md:
        return md
    # Fallback: a JS site sometimes static-renders specific pages.
    async with http_sem:
        return await _try_html_extraction(client, url)


async def _process_url(
    url: str,
    profile: SiteProfile,
    client: httpx.AsyncClient,
    browser: AsyncWebCrawler | None,
    http_sem: asyncio.Semaphore,
    browser_sem: asyncio.Semaphore,
    output_path: Path,
    on_page_callback: Callable[[str, bool], None] | None,
) -> bool:
    markdown = await extract_page(url, profile, client, browser, http_sem, browser_sem)
    if not markdown:
        logger.warning("No content extracted from %s", url)
        if on_page_callback:
            on_page_callback(url, False)
        return False

    filename = url_to_filename(url)
    (output_path / f"{filename}.md").write_text(markdown)
    if on_page_callback:
        on_page_callback(url, True)
    return True


async def crawl_website(
    url: str,
    max_pages: int | None,
    output_dir: str,
    on_page_callback: Callable[[str, bool], None] | None = None,
    on_phase_callback: Callable[[str, dict[str, object]], None] | None = None,
    on_leaf_progress: Callable[[LeafProgress], None] | None = None,
) -> CrawlResult:
    """Probe, discover, extract, write. Returns aggregate statistics.

    The optional ``on_phase_callback`` is invoked after each high-level
    stage completes, with the phase name and a dict of details. The CLI
    uses it to render the live trace; library callers can ignore it.
    Phases: ``"probe"``, ``"discover"``, ``"extract_start"``, ``"done"``.

    The optional ``on_leaf_progress`` is invoked whenever a sitemap leaf
    transitions state or makes streaming progress. CLI uses this to show
    a live per-leaf table; library callers can ignore.

    Raises ``BrowserUnavailableError`` when the chosen profile needs the
    browser but Chromium isn't installed.
    """
    profile = await probe_site(url)
    if on_phase_callback:
        on_phase_callback("probe", {"profile": profile})

    needs_browser = profile.discovery_strategy == "browser" or profile.extraction_strategy == "browser"

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    http_sem = asyncio.Semaphore(_HTTP_CONCURRENCY)
    browser_sem = asyncio.Semaphore(_BROWSER_CONCURRENCY)

    async with AsyncExitStack() as stack:
        browser: AsyncWebCrawler | None = None
        if needs_browser:
            # browser_session() raises BrowserUnavailableError if Chromium
            # isn't installed; let the CLI map it to an actionable message.
            browser = await stack.enter_async_context(browser_session())

        client = await stack.enter_async_context(
            httpx.AsyncClient(follow_redirects=True, timeout=30),
        )

        urls = await discover_urls(
            url,
            profile,
            max_pages,
            client,
            browser,
            on_leaf_progress=on_leaf_progress,
        )
        if on_phase_callback:
            on_phase_callback("discover", {"count": len(urls), "strategy": profile.discovery_strategy})

        if not urls:
            return CrawlResult(total_pages=0, successful_pages=0, failed_pages=0)

        if on_phase_callback:
            on_phase_callback(
                "extract_start",
                {"count": len(urls), "strategy": profile.extraction_strategy},
            )

        tasks = [
            _process_url(u, profile, client, browser, http_sem, browser_sem, output_path, on_page_callback)
            for u in urls
        ]
        results = await asyncio.gather(*tasks)

    successful = sum(results)
    failed = len(results) - successful
    if on_phase_callback:
        on_phase_callback("done", {"successful": successful, "failed": failed})

    return CrawlResult(
        total_pages=len(urls),
        successful_pages=successful,
        failed_pages=failed,
    )
