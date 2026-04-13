"""URL discovery for documentation sites.

Uses crawl4ai's AsyncUrlSeeder for sitemap-based discovery (pure HTTP,
no browser). Filters out language variants and non-content pages.
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from crawl4ai import AsyncUrlSeeder, SeedingConfig

from hivemind.crawl.urls import deduplicate_urls

logger = logging.getLogger(__name__)

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


def _is_language_variant(path: str) -> bool:
    """Check if a URL path is a non-English language variant."""
    path_lower = path.lower()
    return any(path_lower.startswith(prefix) for prefix in _LANGUAGE_PREFIXES)


def _matches_path_scope(path: str, base_path: str) -> bool:
    """Check if a URL path is under the base path scope.

    Handles both '/plugin-development' and '/plugin-development/' as
    equivalent scopes — matching '/plugin-development/server/database'.
    """
    scope = base_path.rstrip("/") + "/"
    return path == base_path or path.startswith(scope)


def _detect_sitemap_domain(urls: list[str]) -> str | None:
    """Detect the dominant domain in sitemap results.

    Sitemaps sometimes reference a different subdomain than the one
    the user passed (e.g. docs.nocobase.com sitemap contains
    v2.docs.nocobase.com URLs). Return the most common netloc.
    """
    if not urls:
        return None
    from collections import Counter

    counts = Counter(urlparse(u).netloc.lower() for u in urls)
    return counts.most_common(1)[0][0]


async def discover_urls(url: str, max_pages: int | None = None) -> list[str]:
    """Discover documentation URLs on a site via sitemap.

    Uses crawl4ai's AsyncUrlSeeder to parse sitemaps (pure HTTP, no browser).
    Filters out language variants and stays within the URL's path scope.

    Handles domain mismatches transparently — if the sitemap references a
    different subdomain (e.g. v2.docs.nocobase.com), the filter adapts.

    Args:
        url: The starting URL. If it has a non-root path (e.g. /docs/api/),
             only URLs under that path are returned.
        max_pages: Maximum number of URLs to return.

    Returns:
        Deduplicated list of discovered URLs.
    """
    parsed = urlparse(url)
    input_netloc = parsed.netloc.lower()
    base_path = parsed.path if parsed.path and parsed.path != "/" else "/"

    # Discover via sitemap
    async with AsyncUrlSeeder() as seeder:
        config = SeedingConfig(
            source="sitemap",
            max_urls=50000,  # fetch entire sitemap, filter after
            filter_nonsense_urls=True,
        )
        results = await seeder.urls(input_netloc, config)

    raw_urls = [item["url"] for item in results if "url" in item]
    logger.info("Sitemap discovery found %d raw URLs", len(raw_urls))

    # Detect the actual domain used in sitemap entries — it may differ
    # from the user-provided domain (e.g. v2.docs.nocobase.com vs docs.nocobase.com)
    sitemap_netloc = _detect_sitemap_domain(raw_urls) or input_netloc
    if sitemap_netloc != input_netloc:
        logger.info("Sitemap uses domain %s (input was %s)", sitemap_netloc, input_netloc)

    # Filter: matching domain, under path scope, not a language variant
    filtered = []
    for u in raw_urls:
        u_parsed = urlparse(u)
        if u_parsed.netloc.lower() != sitemap_netloc:
            continue
        if _is_language_variant(u_parsed.path):
            continue
        if base_path != "/" and not _matches_path_scope(u_parsed.path, base_path):
            continue
        filtered.append(u)

    urls = deduplicate_urls(filtered)

    if max_pages is not None:
        urls = urls[:max_pages]

    logger.info("After filtering: %d URLs", len(urls))
    return urls
