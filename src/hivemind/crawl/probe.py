"""Site capability probe.

Runs once per crawl and produces a SiteProfile that downstream stages
(discovery, extraction) dispatch on. Cheap by design: ~3-4 HTTP requests,
no browser.

Two capability questions get distinct answers:

* **Static extraction** — does running trafilatura on the seed's static
  HTML yield enough markdown to be useful? Drives extraction strategy.
* **Static discovery** — does the seed's static HTML expose enough
  in-scope content links for a spider to find siblings? Drives discovery
  strategy.

A site like bazel.build serves rich static-rendered article bodies but
ships its sidebar nav as JavaScript — so static extraction works while
static discovery doesn't. The probe needs to detect this asymmetry.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura

logger = logging.getLogger(__name__)

# Minimum trafilatura output length to trust static extraction. Below
# this we assume the page body is JS-rendered (or empty) and route to
# the browser. 200 chars catches stub pages while accepting genuine
# short articles.
_MIN_STATIC_EXTRACTION_CHARS = 200

# In-scope content anchors required to trust the static spider. Three is
# enough to skip past trivial header/footer links while catching SPA
# shells whose body is empty.
_MIN_STATIC_DISCOVERY_ANCHORS = 3

# Sitemap leaf size beyond which we give up entirely. Below this we
# stream-parse incrementally (see discovery._sitemap_discover), so even
# bazel's 64 MB leaves are usable. The hard ceiling is just runaway
# protection against pathological sitemaps.
_SITEMAP_LEAF_MAX_BYTES = 200 * 1024 * 1024

_PROBE_TIMEOUT = 10.0

SitemapStatus = Literal["usable", "unusable", "missing"]

_LANGUAGE_PATH_PREFIXES = (
    "zh",
    "cn",
    "ja",
    "ko",
    "de",
    "es",
    "fr",
    "pt",
    "ru",
    "it",
    "nl",
    "pl",
    "tr",
    "ar",
    "zh-cn",
    "zh-tw",
    "pt-br",
)

_HREF_RE = re.compile(rb"""<a\s+[^>]*?href\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
_SITEMAPINDEX_RE = re.compile(rb"<sitemapindex\b", re.IGNORECASE)
_SITEMAP_LOC_RE = re.compile(rb"<loc>\s*([^<\s]+)\s*</loc>", re.IGNORECASE)


@dataclass(frozen=True)
class SiteProfile:
    """Capability fingerprint for a crawl target."""

    seed_url: str
    seed_reachable: bool
    static_extraction_works: bool
    static_discovery_works: bool
    sitemap_status: SitemapStatus
    has_md_source: bool
    detected_domain: str

    @property
    def discovery_strategy(self) -> Literal["sitemap", "spider", "browser"]:
        """Best discovery channel for this site.

        Sitemap is always preferred when available — cheapest and works
        on JS sites because the XML is server-rendered. Spider works
        when the static HTML exposes in-scope nav. Browser is the last
        resort, used only when the in-scope nav is JS-rendered.
        """
        if self.sitemap_status == "usable":
            return "sitemap"
        if self.static_discovery_works:
            return "spider"
        return "browser"

    @property
    def extraction_strategy(self) -> Literal["md", "http", "browser"]:
        """Best per-page extraction channel.

        Source markdown when published; static HTML + trafilatura when
        the body renders without JS; browser render otherwise.
        """
        if self.has_md_source:
            return "md"
        if self.static_extraction_works:
            return "http"
        return "browser"


def _md_url(url: str) -> str:
    if url.endswith("/"):
        return url + "index.md"
    return url + ".md"


def _is_in_scope_anchor(href: str, seed_url: str, target_netloc: str, base_path: str, seed_path: str) -> bool:
    """Spider-style in-scope filter — would the trafilatura spider follow this href?"""
    if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
        return False
    absolute = urljoin(seed_url, href)
    parsed = urlparse(absolute)
    if parsed.netloc.lower() != target_netloc:
        return False
    path = parsed.path or "/"
    normalized = path.rstrip("/") or "/"
    if normalized == seed_path.rstrip("/"):
        return False  # self-canonical
    if "hl=" in (parsed.query or ""):
        return False  # devsite language variant
    if any(path.lower().startswith(f"/{lang}/") for lang in _LANGUAGE_PATH_PREFIXES):
        return False
    if any(path.startswith(prefix) for prefix in ("/_", "/static/", "/assets/", "/css/", "/js/")):
        return False
    return base_path == "/" or path == base_path or path.startswith(base_path.rstrip("/") + "/")


def _count_in_scope_anchors(body: bytes, seed_url: str, target_netloc: str, base_path: str, seed_path: str) -> int:
    """Count distinct in-scope content anchors in static HTML."""
    seen_paths: set[str] = set()
    for match in _HREF_RE.finditer(body):
        href = match.group(1).decode("ascii", errors="ignore")
        if not _is_in_scope_anchor(href, seed_url, target_netloc, base_path, seed_path):
            continue
        path_key = urlparse(urljoin(seed_url, href)).path.rstrip("/")
        if path_key in seen_paths:
            continue
        seen_paths.add(path_key)
        if len(seen_paths) >= _MIN_STATIC_DISCOVERY_ANCHORS:
            break
    return len(seen_paths)


async def _check_seed(
    client: httpx.AsyncClient, url: str, target_netloc: str, base_path: str, seed_path: str
) -> tuple[bool, bool, bool]:
    """Fetch the seed; return (reachable, static_extraction_works, static_discovery_works)."""
    try:
        response = await client.get(url, follow_redirects=True)
    except httpx.HTTPError as e:
        logger.info("Probe: seed unreachable: %s", e)
        return False, False, False
    if response.status_code >= 400:
        logger.info("Probe: seed returned %d", response.status_code)
        return False, False, False

    html = response.text
    body = response.content

    extracted = trafilatura.extract(html, output_format="markdown", favor_precision=True) or ""
    extraction_works = len(extracted) >= _MIN_STATIC_EXTRACTION_CHARS

    in_scope = _count_in_scope_anchors(body, str(response.url), target_netloc, base_path, seed_path)
    discovery_works = in_scope >= _MIN_STATIC_DISCOVERY_ANCHORS

    logger.info(
        "Probe seed: extract=%d chars (works=%s), in-scope-anchors=%d (works=%s)",
        len(extracted),
        extraction_works,
        in_scope,
        discovery_works,
    )
    return True, extraction_works, discovery_works


async def _check_sitemap(client: httpx.AsyncClient, base_url: str) -> SitemapStatus:
    """Classify the site's sitemap (usable / unusable / missing).

    The streaming discoverer can handle leaves of any size, so we only
    return ``unusable`` when we can affirmatively prove a leaf is over
    the hard ceiling. HEAD failures (common on devsites that reject
    HEAD on huge files) optimistically count as usable.
    """
    sitemap_url = f"{base_url}/sitemap.xml"
    try:
        response = await client.get(sitemap_url, follow_redirects=True)
    except httpx.HTTPError as e:
        logger.info("Probe: sitemap fetch failed: %s", e)
        return "missing"
    if response.status_code != 200:
        logger.info("Probe: /sitemap.xml returned %d", response.status_code)
        return "missing"

    body = response.content
    if not _SITEMAPINDEX_RE.search(body):
        return "usable"  # flat <urlset>

    leaf_match = _SITEMAP_LOC_RE.search(body)
    if not leaf_match:
        logger.info("Probe: sitemapindex with no <loc> entries")
        return "missing"

    leaf_url = leaf_match.group(1).decode("ascii", errors="ignore")
    try:
        head = await client.head(leaf_url, follow_redirects=True)
    except httpx.HTTPError as e:
        # Servers that reject HEAD on huge files (or are just slow to
        # respond to HEAD) shouldn't disqualify the sitemap. The
        # streaming discoverer will find out the real size.
        logger.info("Probe: sitemap leaf HEAD failed (%r) — assuming usable", e)
        return "usable"

    content_length = int(head.headers.get("content-length", "0") or 0)
    if content_length > _SITEMAP_LEAF_MAX_BYTES:
        logger.info("Probe: sitemap leaf %d bytes (> %d) → unusable", content_length, _SITEMAP_LEAF_MAX_BYTES)
        return "unusable"
    return "usable"


async def _check_md_source(client: httpx.AsyncClient, url: str) -> bool:
    try:
        response = await client.head(_md_url(url), follow_redirects=True)
    except httpx.HTTPError:
        return False
    if response.status_code != 200:
        return False
    content_type = response.headers.get("content-type", "").lower()
    return "markdown" in content_type or "text/plain" in content_type


async def probe_site(url: str) -> SiteProfile:
    """Build a SiteProfile for the given seed URL.

    Probe failures are recorded as the negative case in the profile,
    never raised. Downstream code can always trust it has a profile.
    """
    parsed = urlparse(url)
    target_netloc = parsed.netloc.lower()
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    seed_path = parsed.path or "/"
    base_path = seed_path

    async with httpx.AsyncClient(timeout=_PROBE_TIMEOUT) as client:
        reachable, extract_works, discover_works = await _check_seed(client, url, target_netloc, base_path, seed_path)
        sitemap_status: SitemapStatus = "missing"
        has_md = False
        if reachable:
            sitemap_status = await _check_sitemap(client, base_url)
            has_md = await _check_md_source(client, url)

    profile = SiteProfile(
        seed_url=url,
        seed_reachable=reachable,
        static_extraction_works=extract_works,
        static_discovery_works=discover_works,
        sitemap_status=sitemap_status,
        has_md_source=has_md,
        detected_domain=target_netloc,
    )
    logger.info("SiteProfile: %s", profile)
    return profile
