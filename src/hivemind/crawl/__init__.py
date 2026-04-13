"""Web crawling via Firecrawl self-hosted instance.

One mode: Firecrawl. No fallbacks. If the service isn't running, fail fast.

Usage:
    hivemind crawl start                          # Start the Docker service
    hivemind expert crawl <url> <agent>           # Crawl a site
    hivemind crawl stop                           # Stop the Docker service
"""

from hivemind.crawl.client import crawl_website, discover_urls
from hivemind.crawl.service import (
    FIRECRAWL_URL,
    FirecrawlNotRunningError,
    is_firecrawl_running,
    start_firecrawl,
    stop_firecrawl,
)
from hivemind.crawl.urls import CrawlResult

__all__ = [
    "FIRECRAWL_URL",
    "CrawlResult",
    "FirecrawlNotRunningError",
    "crawl_website",
    "discover_urls",
    "is_firecrawl_running",
    "start_firecrawl",
    "stop_firecrawl",
]
