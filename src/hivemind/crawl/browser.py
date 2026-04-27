"""Browser-rendering wrapper around crawl4ai's AsyncWebCrawler.

Two responsibilities, both gated behind a shared crawler context so we
launch Chromium at most once per crawl invocation:

* ``browser_bfs_discover`` — run a BFS deep-crawl from the seed and
  return in-scope URLs the static spider could not reach.
* ``browser_extract`` — render a single URL and return clean markdown
  via crawl4ai's built-in markdown generator.

Raises ``BrowserUnavailableError`` from the context manager when
Chromium isn't installed; callers map that to an actionable CLI error
("run ``uv run playwright install chromium``").
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any

from crawl4ai import (
    AsyncWebCrawler,
    BFSDeepCrawlStrategy,
    BrowserConfig,
    CacheMode,
    CrawlerRunConfig,
)
from crawl4ai.deep_crawling.filters import DomainFilter, FilterChain, URLPatternFilter

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

logger = logging.getLogger(__name__)

# Browser BFS depth. Two levels is enough to fan out from a section
# index to its children; more wastes time on cross-section noise.
_BFS_MAX_DEPTH = 2

# Per-page render timeout (ms) for crawl4ai. devsites with heavy JS
# routinely take 3-5s for the first paint; 30s leaves headroom.
_PAGE_TIMEOUT_MS = 30000


class BrowserUnavailableError(RuntimeError):
    """Chromium is not installed or failed to launch."""


@asynccontextmanager
async def browser_session() -> AsyncIterator[AsyncWebCrawler]:
    """Open a single shared AsyncWebCrawler for a crawl invocation."""
    config = BrowserConfig(headless=True, browser_type="chromium", verbose=False)
    crawler = AsyncWebCrawler(config=config)
    try:
        await crawler.__aenter__()
    except Exception as e:
        # crawl4ai surfaces a wide variety of Playwright errors here
        # (BrowserType.launch, missing executable, etc.). Treat them all
        # as "browser unavailable" so the CLI can give one clear hint.
        raise BrowserUnavailableError(str(e)) from e
    try:
        yield crawler
    finally:
        await crawler.__aexit__(None, None, None)


def _result_url(result: Any) -> str | None:
    """Pull the canonical URL off a crawl4ai CrawlResult, tolerating shape drift."""
    return getattr(result, "url", None) or getattr(result, "redirected_url", None)


def _result_markdown(result: Any) -> str:
    """Extract markdown text from a crawl4ai CrawlResult.

    crawl4ai returns either a MarkdownGenerationResult (with a
    ``raw_markdown`` attribute) or a bare string depending on version.
    """
    md = getattr(result, "markdown", None)
    if md is None:
        return ""
    raw = getattr(md, "raw_markdown", None)
    if raw is not None:
        return str(raw)
    return str(md)


async def browser_bfs_discover(
    crawler: AsyncWebCrawler,
    seed: str,
    max_pages: int,
    domain: str,
    base_path: str,
) -> list[str]:
    """Render ``seed`` and return in-scope URLs reachable via BFS.

    The ``domain`` and ``base_path`` filters run inside crawl4ai's
    FilterChain so the BFS budget isn't wasted on out-of-scope top-nav.
    Caller still re-applies the canonical ``_in_scope`` filter for
    consistency with sitemap/spider channels.
    """
    filters: list[object] = [DomainFilter(allowed_domains=[domain])]
    if base_path != "/":
        # Glob match: include base_path itself and anything beneath it.
        scope_glob = f"*{base_path.rstrip('/')}*"
        filters.append(URLPatternFilter(patterns=[scope_glob]))

    strategy = BFSDeepCrawlStrategy(
        max_depth=_BFS_MAX_DEPTH,
        max_pages=max_pages,
        include_external=False,
        filter_chain=FilterChain(filters=filters),
    )
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        deep_crawl_strategy=strategy,
        page_timeout=_PAGE_TIMEOUT_MS,
        wait_until="domcontentloaded",
        scan_full_page=True,
        verbose=False,
        stream=False,
    )
    result = await crawler.arun(url=seed, config=config)
    # When deep_crawl_strategy is set, arun returns a container of one
    # result per crawled URL.
    urls: list[str] = []
    for entry in result:
        u = _result_url(entry)
        if u:
            urls.append(u)
    logger.info("Browser BFS from %s: %d URLs", seed, len(urls))
    return urls


async def browser_extract(crawler: AsyncWebCrawler, url: str) -> str:
    """Render a single URL via the browser; return its markdown."""
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=_PAGE_TIMEOUT_MS,
        wait_until="domcontentloaded",
        scan_full_page=True,
        verbose=False,
        stream=False,
    )
    result = await crawler.arun(url=url, config=config)
    # arun returns a container even for single-page calls.
    for entry in result:
        md = _result_markdown(entry)
        if md:
            return md
    return ""
