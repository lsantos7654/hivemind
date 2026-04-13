"""URL utilities and result types for crawling.

Pure functions with no external dependencies beyond stdlib.
"""

import re
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class CrawlResult:
    """Statistics from a crawl operation."""

    total_pages: int
    successful_pages: int
    failed_pages: int


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
        netloc=normalized.netloc.lower(),
    )

    path = normalized.path
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    normalized = normalized._replace(path=path)

    return normalized.geturl()


def deduplicate_urls(urls: list[str]) -> list[str]:
    """Deduplicate URLs preserving order."""
    seen: set[str] = set()
    result: list[str] = []
    for url in urls:
        norm = normalize_url(url)
        if norm not in seen:
            seen.add(norm)
            result.append(url)
    return result


def url_to_filename(url: str) -> str:
    """Convert a URL to a safe filename based on its path."""
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    if not path:
        path = "index"

    return re.sub(r"[^\w\-]", "_", path)
