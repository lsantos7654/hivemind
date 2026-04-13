"""Web crawling for documentation sites.

Uses crawl4ai for URL discovery (sitemap parsing) and trafilatura for
HTML-to-markdown extraction. Pure Python, no Docker, no browser.

Usage:
    hivemind expert crawl <url> <agent> [--max-pages N]
"""

from hivemind.crawl.extractor import crawl_website
from hivemind.crawl.urls import CrawlResult

__all__ = [
    "CrawlResult",
    "crawl_website",
]
