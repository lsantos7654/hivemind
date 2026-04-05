# markdown-crawler — APIs and Interfaces

## Public API

The library exposes a single public function as its primary API:

```python
from markdown_crawler import md_crawl
```

Everything else in `__init__.py` is a helper intended for internal use, though there are no access controls preventing direct use.

---

## `md_crawl()` — Main Entry Point

**Location**: `markdown_crawler/__init__.py:276`

```python
def md_crawl(
    base_url: str,
    max_depth: Optional[int] = DEFAULT_MAX_DEPTH,          # default: 3
    num_threads: Optional[int] = DEFAULT_NUM_THREADS,      # default: 5
    base_dir: Optional[str] = DEFAULT_BASE_DIR,            # default: 'markdown'
    target_links: Union[str, List[str]] = DEFAULT_TARGET_LINKS,       # default: ['body']
    target_content: Union[str, List[str]] = None,
    valid_paths: Union[str, List[str]] = None,
    is_domain_match: Optional[bool] = None,                # default resolves to True
    is_base_path_match: Optional[bool] = None,             # default resolves to True
    is_debug: Optional[bool] = False,
    is_links: Optional[bool] = False
) -> None
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `base_url` | `str` | required | The seed URL to start crawling from |
| `max_depth` | `int` | `3` | Maximum link depth to recurse. Depth 0 = seed URL only |
| `num_threads` | `int` | `5` | Number of concurrent worker threads |
| `base_dir` | `str` | `'markdown'` | Output directory path for Markdown files; created if missing |
| `target_links` | `str` or `List[str]` | `['body']` | CSS selectors of elements to scan for outgoing links. Comma-separated string or list |
| `target_content` | `str` or `List[str]` | `None` | CSS selectors for the content to extract and convert. If `None`, uses heuristic (largest text block among `article`, `div`, `main`, `p`) |
| `valid_paths` | `str` or `List[str]` | `None` | Allowlist of URL path prefixes. Only URLs matching one of these paths are followed. Comma-separated string or list |
| `is_domain_match` | `bool` | `True` | If `True`, only follow links on the same domain as `base_url` |
| `is_base_path_match` | `bool` | `True` | If `True`, only follow links whose path starts with the `base_url`'s path |
| `is_debug` | `bool` | `False` | Enable `DEBUG`-level logging (very verbose) |
| `is_links` | `bool` | `False` | If `False`, `<a>` tags are stripped from the Markdown output |

**Raises:**
- `ValueError: '❌ Domain match must be True if base match is set to True'` — when `is_domain_match=False` and `is_base_path_match=True`
- `ValueError: '❌ Base URL is required'` — when `base_url` is falsy
- `ValueError: '❌ Invalid base URL'` — when `base_url` fails URL validation (no scheme or netloc)

**Return**: `None`. Output is written to disk in `base_dir`.

---

## Internal Helper Functions

### `crawl()` — Single-Page Crawl

**Location**: `markdown_crawler/__init__.py:66`

```python
def crawl(
    url: str,
    base_url: str,
    already_crawled: set,
    file_path: str,
    target_links: Union[str, List[str]] = DEFAULT_TARGET_LINKS,
    target_content: Union[str, List[str]] = None,
    valid_paths: Union[str, List[str]] = None,
    is_domain_match: Optional[bool] = DEFAULT_DOMAIN_MATCH,
    is_base_path_match: Optional[bool] = DEFAULT_BASE_PATH_MATCH,
    is_links: Optional[bool] = False
) -> List[str]
```

Fetches `url`, writes Markdown to `file_path` (skips if file exists), and returns a list of discovered child URLs. Returns `[]` on request error or non-HTML response.

### `get_target_content()` — HTML Content Extractor

**Location**: `markdown_crawler/__init__.py:158`

```python
def get_target_content(
    soup: BeautifulSoup,
    target_content: Union[List[str], None] = None
) -> str  # Returns HTML string, or False if empty
```

If `target_content` is provided, uses `soup.select(target)` to find matching elements and concatenates their HTML. If `None`, falls back to scanning all `article`, `div`, `main`, `p` elements and returning the one with the most text characters.

### `get_target_links()` — Link Extractor

**Location**: `markdown_crawler/__init__.py:189`

```python
def get_target_links(
    soup: BeautifulSoup,
    base_url: str,
    target_links: List[str] = DEFAULT_TARGET_LINKS,
    valid_paths: Union[List[str], None] = None,
    is_domain_match: Optional[bool] = DEFAULT_DOMAIN_MATCH,
    is_base_path_match: Optional[bool] = DEFAULT_BASE_PATH_MATCH
) -> List[str]
```

Scans the BeautifulSoup tree for all `<a href>` tags within elements matching `target_links`. Resolves relative URLs against `base_url` with `urllib.parse.urljoin`. Applies domain, base-path, and `valid_paths` filtering before returning the list.

### `worker()` — Thread Worker

**Location**: `markdown_crawler/__init__.py:233`

```python
def worker(
    q: object,          # queue.Queue instance
    base_url: str,
    max_depth: int,
    already_crawled: set,
    base_dir: str,
    target_links: Union[List[str], None] = DEFAULT_TARGET_LINKS,
    target_content: Union[List[str], None] = None,
    valid_paths: Union[List[str], None] = None,
    is_domain_match: bool = None,
    is_base_path_match: bool = None,
    is_links: Optional[bool] = False
) -> None
```

Runs as the target of each `threading.Thread`. Loops while the queue is non-empty, dequeuing `(depth, url)` tuples. Discards tuples where `depth > max_depth`. Derives `file_path` from the URL path. Calls `crawl()` and enqueues returned child URLs at `depth + 1`. Sleeps 1 second per iteration.

### `is_valid_url()` — URL Validator

**Location**: `markdown_crawler/__init__.py:46`

```python
def is_valid_url(url: str) -> bool
```

Returns `True` if `url` has both a scheme and a netloc per `urllib.parse.urlparse`.

### `normalize_url()` — URL Normalizer

**Location**: `markdown_crawler/__init__.py:58`

```python
def normalize_url(url: str) -> str
```

Strips trailing slashes from the path and removes query strings and fragments. Used after extracting child URLs in `worker()` to deduplicate before enqueuing.

---

## Module-Level Constants (importable)

All defaults are exported from `markdown_crawler` and used by `cli.py`:

```python
from markdown_crawler import (
    DEFAULT_BASE_DIR,          # 'markdown'
    DEFAULT_MAX_DEPTH,         # 3
    DEFAULT_NUM_THREADS,       # 5
    DEFAULT_TARGET_CONTENT,    # ['article', 'div', 'main', 'p']
    DEFAULT_TARGET_LINKS,      # ['body']
    DEFAULT_DOMAIN_MATCH,      # True
    DEFAULT_BASE_PATH_MATCH,   # True
    BANNER,                    # ASCII art string
)
```

---

## CLI Interface

Installed as `markdown-crawler` console script. Full usage:

```
markdown-crawler [-h]
                 [--max-depth MAX_DEPTH] [-d]
                 [--num-threads NUM_THREADS] [-t]
                 [--base-dir BASE_DIR] [-b]
                 [--debug] [-e]
                 [--target-content TARGET_CONTENT] [-c]
                 [--target-links TARGET_LINKS] [-l]
                 [--valid-paths VALID_PATHS] [-v]
                 [--domain-match] [-m]
                 [--base-path-match] [-p]
                 [--links] [-i]
                 base_url
```

---

## Usage Examples

### Basic library usage

```python
from markdown_crawler import md_crawl

md_crawl('https://en.wikipedia.org/wiki/Python_(programming_language)')
# Writes .md files to ./markdown/ up to depth 3 using 5 threads
```

### RAG document preparation with content targeting

```python
from markdown_crawler import md_crawl

md_crawl(
    'https://docs.python.org/3/',
    max_depth=2,
    num_threads=8,
    base_dir='./docs_corpus',
    target_content=['div.body'],      # Only extract the main doc body
    target_links=['div.sphinxsidebarwrapper', 'div.body'],  # Follow sidebar + body links
    valid_paths=['/3/library', '/3/reference'],  # Only crawl library and reference sections
    is_domain_match=True,
    is_base_path_match=False,         # Allow any path in the domain
    is_debug=False,
    is_links=True                     # Preserve links in output
)
```

### Crawl a wiki with path restriction

```python
from markdown_crawler import md_crawl

md_crawl(
    'https://rickandmorty.fandom.com/wiki/Evil_Morty',
    max_depth=3,
    num_threads=5,
    base_dir='markdown',
    valid_paths=['/wiki'],
    target_content=['div#content'],
    is_domain_match=True,
    is_base_path_match=False,
    is_debug=True
)
```

### CLI equivalent of the above

```bash
markdown-crawler \
  -d 3 -t 5 -b markdown \
  -c "div#content" \
  -v "/wiki" \
  -m \
  -e \
  https://rickandmorty.fandom.com/wiki/Evil_Morty
```

---

## Configuration Options and Extension Points

### Output file naming

File names are derived at `worker()` line 251:
```python
file_name = '-'.join(re.findall(r'\w+', urllib.parse.urlparse(url).path))
file_name = 'index' if not file_name else file_name
file_path = f'{base_dir.rstrip("/") + "/"}{file_name}.md'
```
The URL path `/wiki/Evil_Morty` becomes `wiki-Evil_Morty.md`. The root URL becomes `index.md`.

### Content extraction extension

To target specific HTML elements, pass CSS selectors to `target_content`. Multiple selectors can be passed as a list and their HTML is concatenated:

```python
target_content=['div#main-content', 'article.post-body']
```

### markdownify options

The `md()` call in `crawl()` at line 129 uses:
```python
output = md(
    content,
    keep_inline_images_in=['td', 'th', 'a', 'figure'],
    strip=strip_elements   # ['a'] if is_links=False, else []
)
```

These options are hardcoded; to customize markdownify behavior (e.g., heading style, bullet character), you would need to modify `__init__.py` directly or fork the library.

### Resumable crawls

The `crawl()` function skips file writing if `os.path.exists(file_path)` (line 112). Running `md_crawl()` against the same `base_dir` a second time will only process URLs whose output files are missing, enabling resumable crawls after interruption.
