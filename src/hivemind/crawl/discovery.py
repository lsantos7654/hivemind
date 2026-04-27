"""URL discovery for documentation sites.

Profile-driven dispatch over three discovery channels:

* ``sitemap`` — incremental XML stream-parse of /sitemap.xml (and any
  leaves it points to). Cheapest channel, preferred whenever the site
  publishes a sitemap. Handles 64 MB+ leaves like bazel.build's by
  streaming chunks through ``xml.etree.ElementTree.XMLPullParser``.
  Multi-leaf sitemaps are streamed concurrently.
* ``spider`` — trafilatura's focused_crawler from the seed page; works
  for static-rendered docs sites whose nav is in the HTML.
* ``browser`` — crawl4ai's BFSDeepCrawlStrategy via Playwright; the
  fallback when both the sitemap and the static HTML come up empty.

The seed URL is always included so single-page crawls always succeed.
All channels feed through the same ``_in_scope`` filter so scope
semantics stay consistent.
"""

from __future__ import annotations

import asyncio
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, cast
from urllib.parse import urlparse

from trafilatura.spider import focused_crawler

from hivemind.crawl.browser import browser_bfs_discover
from hivemind.crawl.urls import deduplicate_urls

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable

    import httpx
    from crawl4ai import AsyncWebCrawler

    from hivemind.crawl.probe import SiteProfile

logger = logging.getLogger(__name__)

# Upper bound on discovery when --max-pages is not set, so a crawl on a
# large site without a usable sitemap can't run unbounded.
_DISCOVERY_DEFAULT_CAP = 500

# Concurrent sitemap leaves to stream. Bazel's index has 5 leaves of
# 64 MB each; 3-way parallelism gets us a ~3x speedup without
# overwhelming a typical home connection.
_SITEMAP_LEAF_CONCURRENCY = 3

# Per-leaf streaming timeout. Leaves can be tens of MB; 120s is enough
# for a 64 MB file on a typical connection but bounded so a hung server
# doesn't stall the whole crawl.
_SITEMAP_STREAM_TIMEOUT = 120.0

# Common language path prefixes to exclude from doc site crawls.
_LANGUAGE_PREFIXES = (
    "/zh/",
    "/cn/",
    "/ja/",
    "/ko/",
    "/de/",
    "/es/",
    "/fr/",
    "/pt/",
    "/ru/",
    "/it/",
    "/nl/",
    "/pl/",
    "/tr/",
    "/ar/",
    "/zh-cn/",
    "/zh-tw/",
    "/pt-br/",
)

# XML tags we extract from sitemaps. Stripped of any namespace prefix.
_SITEMAP_LOC_TAG = "loc"

LeafStatus = Literal["queued", "streaming", "done", "failed"]


@dataclass
class LeafProgress:
    """Live progress info for a single sitemap leaf.

    Emitted via the discovery progress callback so the CLI can render a
    Live trace of what's currently being streamed and how many in-scope
    URLs each leaf has found so far.
    """

    index: int  # 0-based position in the sitemap index
    total: int  # total number of leaves
    url: str  # leaf URL being streamed
    status: LeafStatus
    bytes_read: int = 0
    in_scope_hits: int = 0
    error: str | None = None


def _is_language_variant(path: str) -> bool:
    path_lower = path.lower()
    return any(path_lower.startswith(prefix) for prefix in _LANGUAGE_PREFIXES)


def _matches_path_scope(path: str, base_path: str) -> bool:
    """Match '/scope' or '/scope/anything' but not unrelated paths."""
    scope = base_path.rstrip("/") + "/"
    return path == base_path or path.startswith(scope)


def _in_scope(candidate: str, target_netloc: str, base_path: str) -> bool:
    """Domain + path-scope + language-variant filter shared by every channel."""
    parsed = urlparse(candidate)
    if parsed.netloc.lower() != target_netloc:
        return False
    if _is_language_variant(parsed.path):
        return False
    # devsite-style language variants encode locale in a query param
    # (?hl=ko, ?hl=zh-cn). Skip those — they duplicate the canonical page.
    if "hl=" in (parsed.query or ""):
        return False
    return base_path == "/" or _matches_path_scope(parsed.path, base_path)


def _strip_namespace(tag: str) -> str:
    """``{http://...}loc`` → ``loc``."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _drain_locs(parser: ET.XMLPullParser) -> list[str]:
    """Drain ready end-events from the parser; return collected <loc> texts."""
    locs: list[str] = []
    for event in parser.read_events():
        # XMLPullParser yields (event_str, Element); the stub is loose.
        _, elem = cast("tuple[str, ET.Element]", event)
        if _strip_namespace(elem.tag) == _SITEMAP_LOC_TAG and elem.text:
            locs.append(elem.text.strip())
        elem.clear()
    return locs


async def _stream_locs_with_progress(
    client: httpx.AsyncClient,
    url: str,
    progress: LeafProgress,
    on_progress: Callable[[LeafProgress], None] | None,
) -> AsyncIterator[str]:
    """Stream-parse XML; yield <loc>s and update ``progress`` in place.

    Calling ``on_progress(progress)`` after each chunk lets the CLI
    render a live view without us needing to buffer state for it.
    """
    parser = ET.XMLPullParser(["end"])
    progress.status = "streaming"
    if on_progress:
        on_progress(progress)
    async with client.stream("GET", url, timeout=_SITEMAP_STREAM_TIMEOUT) as response:
        response.raise_for_status()
        async for chunk in response.aiter_bytes():
            parser.feed(chunk)
            progress.bytes_read += len(chunk)
            for loc in _drain_locs(parser):
                yield loc
            if on_progress:
                on_progress(progress)


def _parse_locs_sync(body: bytes) -> list[str]:
    """Eager parse of a small sitemap (used for the index file itself)."""
    parser = ET.XMLPullParser(["end"])
    parser.feed(body)
    return _drain_locs(parser)


async def _stream_one_leaf(
    client: httpx.AsyncClient,
    progress: LeafProgress,
    target_netloc: str,
    base_path: str,
    on_progress: Callable[[LeafProgress], None] | None,
    netloc_box: list[str],  # mutable single-element holder for sniffed netloc
    netloc_lock: asyncio.Lock,
) -> list[str]:
    """Stream one leaf to completion; return its in-scope URLs.

    ``netloc_box`` is shared across all leaves so the first leaf to see
    a real <loc> sets the canonical netloc. Other leaves read it and
    apply the same filter.
    """
    found: list[str] = []
    try:
        async for loc in _stream_locs_with_progress(client, progress.url, progress, on_progress):
            if not netloc_box[0]:
                detected = urlparse(loc).netloc.lower()
                if detected:
                    async with netloc_lock:
                        if not netloc_box[0]:
                            netloc_box[0] = detected
            current_netloc = netloc_box[0] or target_netloc
            if _in_scope(loc, current_netloc, base_path):
                found.append(loc)
                progress.in_scope_hits += 1
        progress.status = "done"
    except Exception as e:
        progress.status = "failed"
        progress.error = repr(e)
        logger.warning("Sitemap leaf %s failed: %s", progress.url, e)
    if on_progress:
        on_progress(progress)
    return found


async def _sitemap_discover(
    client: httpx.AsyncClient,
    seed_url: str,
    target_netloc: str,
    base_path: str,
    max_pages: int,
    on_progress: Callable[[LeafProgress], None] | None,
) -> tuple[list[str], str]:
    """Stream-parse sitemap(index) and return in-scope URLs.

    Multi-leaf sitemaps are streamed concurrently (cap
    ``_SITEMAP_LEAF_CONCURRENCY``). No site-specific bailout — all
    leaves stream to completion or fail individually. The CLI renders
    progress so the user can ``Ctrl+C`` if it's running long.

    Returns:
        (urls, sitemap_netloc). The netloc is sniffed from the first
        seen ``<loc>`` so subdomain mismatches are transparent.
    """
    parsed = urlparse(seed_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    sitemap_url = f"{base_url}/sitemap.xml"

    response = await client.get(sitemap_url, follow_redirects=True)
    response.raise_for_status()
    is_index = b"<sitemapindex" in response.content[:2048]
    leaf_urls = _parse_locs_sync(response.content) if is_index else [sitemap_url]

    # Build progress objects up front so the CLI can render the full
    # leaf list immediately, even before streams start.
    leaves = [LeafProgress(index=i, total=len(leaf_urls), url=u, status="queued") for i, u in enumerate(leaf_urls)]
    if on_progress:
        for leaf in leaves:
            on_progress(leaf)

    netloc_box: list[str] = [""]
    netloc_lock = asyncio.Lock()
    semaphore = asyncio.Semaphore(_SITEMAP_LEAF_CONCURRENCY)

    async def _bounded(leaf: LeafProgress) -> list[str]:
        async with semaphore:
            return await _stream_one_leaf(
                client,
                leaf,
                target_netloc,
                base_path,
                on_progress,
                netloc_box,
                netloc_lock,
            )

    results = await asyncio.gather(*(_bounded(leaf) for leaf in leaves))

    collected: list[str] = []
    for leaf_urls_found in results:
        collected.extend(leaf_urls_found)
        if len(collected) >= max_pages:
            collected = collected[:max_pages]
            break

    sitemap_netloc = netloc_box[0] or target_netloc
    logger.info("Sitemap discovery: %d in-scope URLs from %d leaf(s)", len(collected), len(leaf_urls))
    return collected, sitemap_netloc


async def _spider_discover(seed: str, target_netloc: str, base_path: str, max_pages: int) -> list[str]:
    """Trafilatura focused_crawler from ``seed`` (sync; called via to_thread)."""
    todo: list[str] | None = None
    known: list[str] | None = None
    while True:
        todo, known = await asyncio.to_thread(
            focused_crawler,
            seed,
            max_seen_urls=max_pages,
            todo=todo,
            known_links=known,
        )
        in_scope_known = [u for u in (known or []) if _in_scope(u, target_netloc, base_path)]
        if not todo or len(in_scope_known) >= max_pages:
            break
    in_scope = [u for u in (known or []) if _in_scope(u, target_netloc, base_path)]
    logger.info("Spider discovery: %d in-scope URLs", len(in_scope))
    return in_scope


async def _browser_discover(
    crawler: AsyncWebCrawler, seed: str, target_netloc: str, base_path: str, max_pages: int
) -> list[str]:
    """BFS discovery via the rendered DOM."""
    raw = await browser_bfs_discover(
        crawler,
        seed,
        max_pages=max_pages,
        domain=target_netloc,
        base_path=base_path,
    )
    in_scope = [u for u in raw if _in_scope(u, target_netloc, base_path)]
    logger.info("Browser discovery: %d in-scope URLs (from %d raw)", len(in_scope), len(raw))
    return in_scope


async def discover_urls(
    url: str,
    profile: SiteProfile,
    max_pages: int | None,
    client: httpx.AsyncClient,
    browser: AsyncWebCrawler | None,
    on_leaf_progress: Callable[[LeafProgress], None] | None = None,
) -> list[str]:
    """Discover URLs starting from ``url`` using the strategy in ``profile``.

    Args:
        url: The seed URL.
        profile: Capability profile chosen by ``probe_site``.
        max_pages: Maximum URLs to return. ``None`` means no user-imposed
            limit; channels still respect ``_DISCOVERY_DEFAULT_CAP``.
        client: Shared httpx client used by the sitemap streamer.
        browser: Open AsyncWebCrawler if the strategy needs browser
            discovery. Pass ``None`` if no browser is available.
        on_leaf_progress: Called whenever a sitemap leaf transitions
            state or makes streaming progress. CLI uses this to render
            a live view; library callers can ignore.

    Returns:
        Deduplicated list of in-scope URLs, seed first.
    """
    parsed = urlparse(url)
    input_netloc = parsed.netloc.lower()
    base_path = parsed.path if parsed.path and parsed.path != "/" else "/"

    cap = max_pages if max_pages is not None else _DISCOVERY_DEFAULT_CAP

    strategy = profile.discovery_strategy

    sitemap_netloc = input_netloc
    discovered: list[str] = []

    if strategy == "sitemap":
        discovered, sitemap_netloc = await _sitemap_discover(
            client,
            url,
            input_netloc,
            base_path,
            cap,
            on_leaf_progress,
        )
    elif strategy == "spider":
        discovered = await _spider_discover(url, input_netloc, base_path, cap)
    elif strategy == "browser":
        if browser is None:
            msg = "browser strategy selected but no browser session provided"
            raise RuntimeError(msg)
        discovered = await _browser_discover(browser, url, input_netloc, base_path, cap)

    seed_url = parsed._replace(netloc=sitemap_netloc).geturl() if sitemap_netloc != input_netloc else url
    urls = deduplicate_urls([seed_url, *discovered])

    if max_pages is not None:
        urls = urls[:max_pages]

    logger.info("Discovery (%s): %d URLs after filtering", strategy, len(urls))
    return urls
