# Trafilatura — APIs and Interfaces

## Public API (Python)

The public API is declared in `trafilatura/__init__.py:23`:

```python
from trafilatura import (
    bare_extraction,
    baseline,
    extract,
    extract_metadata,
    extract_with_metadata,
    fetch_response,
    fetch_url,
    html2txt,
    load_html,
)
```

---

## Core Extraction Functions

### `extract()` — `trafilatura/core.py:351`

The primary user-facing function. Returns extracted text as a string.

```python
def extract(
    filecontent: Any,                          # HTML string, bytes, or lxml tree
    url: Optional[str] = None,                # URL for metadata and relative link resolution
    record_id: Optional[str] = None,          # Custom ID added to metadata
    fast: bool = False,                        # Skip external extractor comparison
    favor_precision: bool = False,            # Prefer less text, less noise
    favor_recall: bool = False,               # Prefer more text, possibly more noise
    include_comments: bool = True,            # Extract HTML comments sections
    output_format: str = "txt",               # "csv","html","json","markdown","txt","xml","xmltei"
    tei_validation: bool = False,             # Validate XML-TEI output against DTD
    target_language: Optional[str] = None,   # ISO 639-1 code; discard wrong-language docs
    include_tables: bool = True,              # Extract <table> content
    include_images: bool = False,             # Extract image references (experimental)
    include_formatting: bool = False,         # Preserve bold/italic/etc.
    include_links: bool = False,              # Preserve hyperlinks (experimental)
    deduplicate: bool = False,                # Filter duplicate text blocks
    date_extraction_params: Optional[Dict] = None,  # Params for htmldate
    with_metadata: bool = False,              # Include metadata in output
    only_with_metadata: bool = False,         # Discard docs missing title/url/date
    url_blacklist: Optional[Set[str]] = None, # Discard these URLs
    author_blacklist: Optional[Set[str]] = None,  # Discard these authors
    settingsfile: Optional[str] = None,       # Path to custom settings.cfg
    prune_xpath: Optional[Any] = None,        # XPath(s) to remove before extraction
    config: Any = DEFAULT_CONFIG,             # ConfigParser object
    options: Optional[Extractor] = None,      # Full Extractor object (overrides all above)
) -> Optional[str]:
```

**Returns**: Extracted text string in the chosen format, or `None` if extraction failed or filters excluded the document.

**Example:**
```python
import trafilatura

html = trafilatura.fetch_url("https://example.com/article")
text = trafilatura.extract(html)

# With metadata in JSON format
result = trafilatura.extract(html, output_format="json", with_metadata=True)

# Precision mode, Markdown output
result = trafilatura.extract(html, favor_precision=True, output_format="markdown")

# Language filter (discard non-German content)
result = trafilatura.extract(html, target_language="de")
```

---

### `bare_extraction()` — `trafilatura/core.py:131`

Lower-level function that returns a `Document` object (Python-native) instead of a formatted string. Preferred for programmatic access to all extracted fields.

```python
def bare_extraction(
    filecontent: Any,
    url: Optional[str] = None,
    fast: bool = False,
    favor_precision: bool = False,
    favor_recall: bool = False,
    include_comments: bool = True,
    output_format: str = "python",       # "python" = return Document object
    target_language: Optional[str] = None,
    include_tables: bool = True,
    include_images: bool = False,
    include_formatting: bool = False,
    include_links: bool = False,
    deduplicate: bool = False,
    date_extraction_params: Optional[Dict] = None,
    with_metadata: bool = False,
    only_with_metadata: bool = False,
    url_blacklist: Optional[Set[str]] = None,
    author_blacklist: Optional[Set[str]] = None,
    prune_xpath: Optional[Any] = None,
    config: Any = DEFAULT_CONFIG,
    options: Optional[Extractor] = None,
) -> Optional[Union[Document, Dict]]
```

**Returns**: A `Document` instance (or `None`). Use `.as_dict()` to get a plain dict.

**Example:**
```python
doc = trafilatura.bare_extraction(html, with_metadata=True)
if doc:
    print(doc.title)
    print(doc.author)
    print(doc.date)
    print(doc.text)
    print(doc.url)
    d = doc.as_dict()   # convert to dict
```

---

### `extract_with_metadata()` — `trafilatura/core.py:447`

Convenience wrapper: like `extract()` but always sets `with_metadata=True` and returns a `Document` object.

```python
def extract_with_metadata(
    filecontent: Any,
    url: Optional[str] = None,
    # ... same signature as extract() minus record_id, only_with_metadata
) -> Optional[Document]
```

---

### `extract_metadata()` — `trafilatura/metadata.py:485`

Metadata-only extraction — no content extraction. Returns a `Document` with all metadata fields populated.

```python
def extract_metadata(
    filecontent: Union[HtmlElement, str],  # HTML string or parsed tree
    default_url: Optional[str] = None,
    date_config: Optional[Any] = None,
    extensive: bool = True,                # Extensive date search
    author_blacklist: Optional[Set[str]] = None,
) -> Document
```

**Example:**
```python
from trafilatura import extract_metadata
doc = extract_metadata(html, default_url="https://example.com/page")
print(doc.title, doc.author, doc.date, doc.sitename)
```

---

## Download Functions

### `fetch_url()` — `trafilatura/downloads.py:263`

Download a URL and return the HTML as a decoded string.

```python
def fetch_url(
    url: str,
    no_ssl: bool = False,             # Disable SSL verification
    config: ConfigParser = DEFAULT_CONFIG,
    options: Optional[Extractor] = None,
) -> Optional[str]
```

**Example:**
```python
html = trafilatura.fetch_url("https://example.com")
if html:
    text = trafilatura.extract(html)
```

---

### `fetch_response()` — `trafilatura/downloads.py:291`

Download a URL and return a full `Response` object (with status, headers, raw bytes).

```python
def fetch_response(
    url: str,
    *,
    decode: bool = False,
    no_ssl: bool = False,
    with_headers: bool = False,
    config: ConfigParser = DEFAULT_CONFIG,
) -> Optional[Response]
```

**Example:**
```python
from trafilatura import fetch_response
resp = fetch_response("https://example.com", decode=True, with_headers=True)
if resp and resp.status == 200:
    print(resp.html)
    print(resp.headers)
```

---

### `buffered_downloads()` — `trafilatura/downloads.py:419`

Multi-threaded batch download generator.

```python
def buffered_downloads(
    bufferlist: List[str],           # List of URLs
    download_threads: int,           # Number of threads
    options: Optional[Extractor] = None,
) -> Generator[Tuple[str, str], None, None]   # yields (url, html_string)
```

**Example:**
```python
from trafilatura.downloads import buffered_downloads

urls = ["https://example.com/1", "https://example.com/2"]
for url, html in buffered_downloads(urls, download_threads=4):
    if html:
        text = trafilatura.extract(html)
```

---

## Utility Functions

### `load_html()` — `trafilatura/utils.py`

Parse HTML from string, bytes, or gzipped bytes into an lxml `HtmlElement`.

```python
def load_html(htmlobject: Any) -> Optional[HtmlElement]
```

### `html2txt()` — `trafilatura/baseline.py`

Simple HTML-to-text conversion (no content extraction heuristics).

```python
def html2txt(content: Any) -> Optional[str]
```

### `baseline()` — `trafilatura/baseline.py:25`

Last-resort paragraph extractor.

```python
def baseline(filecontent: Any) -> Tuple[_Element, str, int]
# Returns: (body_element, text_string, text_length)
```

---

## Data Classes

### `Document` — `trafilatura/settings.py:207`

Container for all extracted information. All fields default to `None`.

```python
class Document:
    # Metadata
    title: Optional[str]
    author: Optional[str]
    url: Optional[str]
    hostname: Optional[str]
    description: Optional[str]
    sitename: Optional[str]
    date: Optional[str]          # ISO 8601 format
    categories: Optional[List[str]]
    tags: Optional[List[str]]
    fingerprint: Optional[str]   # Content hash (base64)
    id: Optional[str]            # Custom record ID
    license: Optional[str]       # e.g., "CC BY 4.0"
    image: Optional[str]         # OG/meta image URL
    pagetype: Optional[str]      # e.g., "article"
    filedate: Optional[str]      # Extraction date

    # Content
    body: _Element               # lxml element containing extracted content
    comments: Optional[str]      # Extracted comments as text
    commentsbody: _Element       # lxml element for comments
    raw_text: Optional[str]      # Text before output formatting
    text: Optional[str]          # Final text in output format
    language: Optional[str]      # Detected language code

    # Methods
    def as_dict(self) -> Dict[str, Optional[str]]: ...
    def from_dict(cls, data: Dict) -> 'Document': ...
    def clean_and_trim(self) -> None: ...
```

### `Extractor` — `trafilatura/settings.py:63`

Stores all extraction configuration. Can be passed directly to skip option parsing overhead.

```python
class Extractor:
    config: ConfigParser
    format: str              # Output format
    fast: bool               # Skip external extractor comparison
    focus: str               # "balanced" | "precision" | "recall"
    comments: bool
    formatting: bool
    links: bool
    images: bool
    tables: bool
    dedup: bool
    lang: Optional[str]      # Target language
    url: Optional[str]
    with_metadata: bool
    only_with_metadata: bool
    tei_validation: bool
    date_params: Dict
    author_blacklist: Set[str]
    url_blacklist: Set[str]
    # Size thresholds (from config):
    min_extracted_size: int
    min_output_size: int
    min_output_comm_size: int
    min_extracted_comm_size: int
    min_duplcheck_size: int
    max_repetitions: int
    max_file_size: int
    min_file_size: int
    max_tree_size: Optional[int]
```

### `Response` — `trafilatura/downloads.py:104`

HTTP response container.

```python
class Response:
    data: bytes
    html: Optional[str]
    status: int
    url: str
    headers: Optional[Dict[str, str]]

    def decode_data(self, decode: bool) -> None: ...
    def store_headers(self, headerdict: Dict) -> None: ...
    def as_dict(self) -> Dict: ...
```

---

## Discovery and Crawling APIs

### `find_feed_urls()` — `trafilatura/feeds.py`

Find all feed URLs from a website homepage or known feed URL.

```python
def find_feed_urls(url: str, target_lang: Optional[str] = None) -> List[str]
```

### `sitemap_search()` — `trafilatura/sitemaps.py`

Discover and collect URLs from a website's sitemaps.

```python
def sitemap_search(
    url: str,
    target_lang: Optional[str] = None,
    external: bool = False,
    config: ConfigParser = DEFAULT_CONFIG,
) -> List[str]
```

### `focused_crawler()` — `trafilatura/spider.py`

Crawl a website starting from a URL, respecting `robots.txt`.

```python
def focused_crawler(
    homepage: str,
    max_seen_urls: int = 10,
    max_known_urls: int = 100000,
    todo: Optional[UrlStore] = None,
    known_links: Optional[UrlStore] = None,
    lang: Optional[str] = None,
    config: ConfigParser = DEFAULT_CONFIG,
    rules: Optional[RobotFileParser] = None,
    proxies: Optional[Dict] = None,
    sleep_time: int = 5,
    prune_xpath: Optional[str] = None,
) -> Tuple[UrlStore, UrlStore]   # (todo, known)
```

---

## Command-Line Interface

The CLI is invoked via `trafilatura` (installed entry point: `trafilatura.cli:main`).

### Input Modes (mutually exclusive)

```bash
# Single URL
trafilatura -u https://example.com/article

# Batch from file (one URL per line)
trafilatura -i urls.txt

# Directory of HTML files
trafilatura --input-dir /path/to/htmlfiles/

# Read from stdin
echo '<html>...' | trafilatura
```

### Navigation / Discovery

```bash
# Discover and fetch URLs from feeds
trafilatura --feed https://example.com

# Discover and fetch URLs from sitemaps
trafilatura --sitemap https://example.com

# Crawl (fixed depth)
trafilatura --crawl https://example.com

# Combined sitemap + crawl
trafilatura --explore https://example.com

# Probe for extractable content (print URLs)
trafilatura --probe https://example.com
```

### Output Formats

```bash
# Plain text (default)
trafilatura -u https://example.com

# Markdown
trafilatura -u https://example.com --markdown
# or: --output-format markdown

# JSON
trafilatura -u https://example.com --json

# XML
trafilatura -u https://example.com --xml

# XML-TEI with validation
trafilatura -u https://example.com --xmltei --validate-tei

# CSV
trafilatura -u https://example.com --csv

# HTML
trafilatura -u https://example.com --html

# Write to directory
trafilatura -i urls.txt -o /output/dir/ --json
```

### Extraction Options

```bash
# Include metadata
trafilatura -u URL --with-metadata

# Only output docs with title+url+date
trafilatura -i urls.txt --only-with-metadata

# Fast mode (skip external extractor fallback)
trafilatura -u URL --fast

# Precision / recall mode
trafilatura -u URL --precision
trafilatura -u URL --recall

# Language filter
trafilatura -i urls.txt --target-language de

# Include formatting (bold/italic)
trafilatura -u URL --formatting

# Deduplication
trafilatura -i urls.txt --deduplicate

# Custom config
trafilatura -u URL --config-file my_settings.cfg

# URL blacklist
trafilatura -i urls.txt --blacklist blacklisted_urls.txt

# Parallel threads
trafilatura -i urls.txt --parallel 8

# Archived (Internet Archive fallback)
trafilatura -u URL --archived
```

---

## Configuration and Extension Points

### Custom Configuration File

Create a custom `settings.cfg` overriding any defaults:

```ini
[DEFAULT]
DOWNLOAD_TIMEOUT = 60
MAX_FILE_SIZE = 5000000
MIN_EXTRACTED_SIZE = 500
EXTENSIVE_DATE_SEARCH = off
USER_AGENTS =
    "Mozilla/5.0 (compatible; MyBot/1.0)"
```

Use it in Python:
```python
from trafilatura.settings import use_config
config = use_config("my_settings.cfg")
text = trafilatura.extract(html, config=config)
```

Or pass a pre-built `ConfigParser` directly.

### Using `Extractor` for Repeated Calls (Performance)

For batch processing, build an `Extractor` once and reuse it to avoid repeated config parsing:

```python
from trafilatura.settings import Extractor

options = Extractor(
    output_format="json",
    with_metadata=True,
    fast=True,
    precision=True,
    lang="en",
)

for html in html_list:
    result = trafilatura.extract(html, options=options)
```

### XPath Pruning

Remove specific parts of the HTML before extraction:

```python
result = trafilatura.extract(
    html,
    prune_xpath=['//div[@class="sidebar"]', '//nav']
)
```

### Deduplication

```python
from trafilatura.deduplication import content_fingerprint, duplicate_test

# Generate a fingerprint for deduplication
fp = content_fingerprint("some text content")

# Reset all caches (free memory in long-running processes)
from trafilatura.meta import reset_caches
reset_caches()
```

### URL Store and Batch Downloading

```python
from trafilatura.downloads import add_to_compressed_dict, load_download_buffer, buffered_downloads

# Build URL store from list
url_store = add_to_compressed_dict(
    ["https://example.com/1", "https://example.com/2"],
    blacklist={"https://example.com/bad"}
)

# Draw download buffer (respects domain back-off)
bufferlist, url_store = load_download_buffer(url_store, sleep_time=5.0)

# Download with 4 threads
for url, html in buffered_downloads(bufferlist, download_threads=4):
    if html:
        print(trafilatura.extract(html, url=url))
```

### `reset_caches()` — `trafilatura/meta.py:15`

Clears all LRU caches across the module (useful for long-running processes to release memory):

```python
from trafilatura.meta import reset_caches
reset_caches()
```
