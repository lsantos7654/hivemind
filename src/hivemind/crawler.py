"""Web crawling via Firecrawl self-hosted instance.

Two modes:
- Firecrawl (default): Full crawling via self-hosted Firecrawl Docker service
- Raw markdown (--raw-markdown): Direct .md endpoint fetching for sites that serve source markdown

No fallbacks. If Firecrawl isn't running, fail fast with a clear error.
"""

import logging
import re
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import httpx
from firecrawl import Firecrawl

logger = logging.getLogger(__name__)

# --- Constants ---

FIRECRAWL_URL = "http://localhost:3002"
FIRECRAWL_HEALTH_ENDPOINT = f"{FIRECRAWL_URL}/v0/health/liveness"
FIRECRAWL_REPO_URL = "https://github.com/firecrawl/firecrawl.git"
FIRECRAWL_CLONE_DIR = Path.home() / ".cache" / "hivemind" / "firecrawl"
FIRECRAWL_COMPOSE_DIR = FIRECRAWL_CLONE_DIR / "repo"


class FirecrawlNotRunningError(Exception):
    """Raised when the Firecrawl service is not reachable."""


# --- URL utilities ---


def normalize_url(url: str) -> str:
    """Normalize URL for deduplication.

    - Remove fragment (#section)
    - Lowercase scheme and domain
    - Remove trailing slash (except root)
    """
    parsed = urlparse(url)
    normalized = parsed._replace(fragment="")
    normalized = normalized._replace(scheme=normalized.scheme.lower(), netloc=normalized.netloc.lower())

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
    """Convert a URL to a safe filename.

    Args:
        url: The URL to convert

    Returns:
        A safe filename based on the URL path
    """
    parsed = urlparse(url)
    path = parsed.path.strip("/")

    if not path:
        path = "index"

    # Replace non-alphanumeric characters (except hyphens) with underscores
    return re.sub(r"[^\w\-]", "_", path)


def is_sitemap_url(url: str) -> bool:
    """Check if a URL points to a sitemap."""
    url_lower = url.lower()
    return url_lower.endswith((".xml", ".xml.gz")) or "sitemap" in url_lower


# --- Result type ---


@dataclass
class CrawlResult:
    """Statistics from a crawl operation."""

    total_pages: int
    successful_pages: int
    failed_pages: int


# --- Firecrawl service management ---


def _get_firecrawl_client() -> Firecrawl:
    """Create a Firecrawl client pointed at the self-hosted instance."""
    return Firecrawl(api_key="self-hosted", api_url=FIRECRAWL_URL)


def is_firecrawl_running() -> bool:
    """Check if the Firecrawl service is reachable."""
    try:
        response = httpx.get(FIRECRAWL_HEALTH_ENDPOINT, timeout=5)
    except (httpx.ConnectError, httpx.TimeoutException):
        return False
    else:
        return response.status_code == 200


def ensure_firecrawl_running() -> None:
    """Check that Firecrawl is running. Raise if not."""
    if not is_firecrawl_running():
        msg = (
            "Firecrawl service is not running at " + FIRECRAWL_URL + ".\n"
            "Start it with: hivemind crawl start\n"
            "Then retry this command."
        )
        raise FirecrawlNotRunningError(msg)


def _ensure_firecrawl_repo() -> Path:
    """Clone the Firecrawl repo if not already present. Return compose dir."""
    if FIRECRAWL_COMPOSE_DIR.is_dir() and (FIRECRAWL_COMPOSE_DIR / "docker-compose.yaml").exists():
        return FIRECRAWL_COMPOSE_DIR

    FIRECRAWL_CLONE_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", FIRECRAWL_REPO_URL, str(FIRECRAWL_COMPOSE_DIR)],
        check=True,
        capture_output=True,
    )
    return FIRECRAWL_COMPOSE_DIR


def start_firecrawl() -> None:
    """Start the Firecrawl Docker service.

    Clones the repo if needed, writes a minimal .env, and runs docker compose up.
    """
    if is_firecrawl_running():
        return

    compose_dir = _ensure_firecrawl_repo()

    # Write minimal .env if it doesn't exist
    env_file = compose_dir / ".env"
    if not env_file.exists():
        env_file.write_text("PORT=3002\nHOST=0.0.0.0\nUSE_DB_AUTHENTICATION=false\nBULL_AUTH_KEY=hivemind\n")

    subprocess.run(
        ["docker", "compose", "up", "-d"],
        cwd=str(compose_dir),
        check=True,
    )


def stop_firecrawl() -> None:
    """Stop the Firecrawl Docker service."""
    if not FIRECRAWL_COMPOSE_DIR.is_dir():
        return

    subprocess.run(
        ["docker", "compose", "down"],
        cwd=str(FIRECRAWL_COMPOSE_DIR),
        check=True,
    )


# --- Firecrawl-powered crawling ---


def discover_urls(url: str, max_pages: int | None = None) -> list[str]:
    """Discover URLs on a site using Firecrawl's /map endpoint.

    Args:
        url: The starting URL
        max_pages: Maximum number of URLs to discover (None for default limit)

    Returns:
        List of discovered URLs
    """
    ensure_firecrawl_running()
    client = _get_firecrawl_client()

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
    """Crawl a website using Firecrawl and save each page as markdown.

    Uses Firecrawl's /crawl endpoint which handles BFS discovery, JS rendering,
    anti-bot measures, and content cleaning internally.

    Args:
        url: The starting URL to crawl
        max_pages: Maximum number of pages to crawl (None for no limit)
        output_dir: Directory to save markdown files
        on_page_callback: Optional callback called after each page (url, success)

    Returns:
        CrawlResult with statistics
    """
    ensure_firecrawl_running()
    client = _get_firecrawl_client()
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


# --- Raw markdown mode ---


def _raw_markdown_url(url: str) -> str:
    """Return the raw markdown URL for a given page URL.

    Some doc sites (rspress-based) serve source markdown at:
    - <url>.md        for regular pages (no trailing slash)
    - <url>index.md   for directory-style URLs (trailing slash)
    """
    if url.endswith("/"):
        return url + "index.md"
    return url + ".md"


def _is_markdown_response(text: str) -> bool:
    return bool(text) and not text.strip().startswith("<")


async def crawl_urls_raw_markdown(
    urls: list[str],
    output_dir: str,
    on_page_callback: Callable[[str, bool], None] | None = None,
) -> CrawlResult:
    """Fetch raw markdown for each URL by appending .md to the URL path.

    Used for sites that support a .md suffix endpoint (e.g. rspress-based docs).
    Much faster and more accurate than browser-based scraping since it retrieves
    the source markdown directly.

    Args:
        urls: List of page URLs to fetch
        output_dir: Directory to save markdown files
        on_page_callback: Optional callback called after each page (url, success)

    Returns:
        CrawlResult with statistics
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    urls = deduplicate_urls(urls)

    successful = 0
    failed = 0

    async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
        for page_url in urls:
            md_url = _raw_markdown_url(page_url)
            try:
                response = await client.get(md_url)
                if response.status_code == 200 and _is_markdown_response(response.text):
                    filename = url_to_filename(page_url)
                    filepath = output_path / f"{filename}.md"
                    filepath.write_text(response.text)
                    successful += 1
                    if on_page_callback:
                        on_page_callback(page_url, True)
                    continue
            except (httpx.TimeoutException, httpx.ConnectError, httpx.HTTPStatusError):
                pass  # transient HTTP failure
            except OSError:
                raise  # disk write failure is non-transient
            except Exception as e:
                logger.warning("Unexpected error crawling %s: %s", page_url, e)
            failed += 1
            if on_page_callback:
                on_page_callback(page_url, False)

    return CrawlResult(
        total_pages=len(urls),
        successful_pages=successful,
        failed_pages=failed,
    )
