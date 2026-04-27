"""Web crawling for documentation sites.

Probe-driven multi-strategy crawler. ``probe_site`` classifies the seed,
``discover_urls`` fans out via sitemap / spider / browser-BFS, and
``crawl_website`` orchestrates the whole pipeline.

Usage:
    hivemind expert crawl <url> <agent> [--max-pages N]
"""

from hivemind.crawl.browser import BrowserUnavailableError
from hivemind.crawl.discovery import LeafProgress
from hivemind.crawl.extractor import crawl_website
from hivemind.crawl.probe import SiteProfile, probe_site
from hivemind.crawl.urls import CrawlResult

__all__ = [
    "BrowserUnavailableError",
    "CrawlResult",
    "LeafProgress",
    "SiteProfile",
    "crawl_website",
    "probe_site",
]
