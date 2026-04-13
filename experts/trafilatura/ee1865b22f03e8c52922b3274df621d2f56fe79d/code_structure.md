# Trafilatura — Code Structure

## Annotated Directory Tree

```
trafilatura-repo/
├── pyproject.toml              # Build config, metadata, dependencies, entry points
├── README.md                   # Project overview, features, citations
├── HISTORY.md                  # Changelog (organized by version)
├── CONTRIBUTING.md             # Contribution guidelines
├── CITATION.cff                # Citation metadata
├── compose.yml                 # Docker Compose (for development/testing)
├── .coveragerc                 # Coverage configuration
├── .readthedocs.yaml           # ReadTheDocs build configuration
│
├── trafilatura/                # Main Python package
│   ├── __init__.py             # Public API exports, version declaration
│   ├── py.typed                # PEP 561 marker (typed package)
│   ├── settings.cfg            # Default configuration (INI format)
│   ├── data/
│   │   └── tei_corpus.dtd      # DTD schema for XML-TEI validation
│   │
│   ├── core.py                 # Main extraction pipeline & entry points
│   ├── settings.py             # Extractor/Document classes, constants, config
│   ├── main_extractor.py       # Custom content/comment extraction logic
│   ├── htmlprocessing.py       # HTML tree cleaning, tag conversion, node handling
│   ├── external.py             # Integration with readability-lxml and jusText
│   ├── baseline.py             # Fallback extractor (html2txt, paragraph scan)
│   ├── xml.py                  # XML/TEI/JSON/CSV/HTML output serialization
│   ├── xpaths.py               # All XPath expressions for content & metadata
│   │
│   ├── metadata.py             # Metadata extraction (meta tags, OG, JSON-LD, etc.)
│   ├── json_metadata.py        # JSON-LD schema.org parsing
│   │
│   ├── downloads.py            # HTTP download engine (urllib3/pycurl), batching
│   ├── utils.py                # HTML parsing, encoding, text filtering, language
│   │
│   ├── deduplication.py        # Simhash deduplication, fingerprinting, LRU cache
│   ├── sitemaps.py             # Sitemap discovery and URL extraction
│   ├── feeds.py                # RSS/Atom/JSON feed discovery and URL extraction
│   ├── spider.py               # Web crawling / spidering logic
│   │
│   ├── cli.py                  # argparse CLI definition and main() entry point
│   ├── cli_utils.py            # CLI pipelines: URL/file/batch/feed/sitemap processing
│   │
│   └── meta.py                 # Module-wide utilities: reset_caches()
│
├── tests/                      # Test suite
│   ├── unit_tests.py           # Core extraction unit tests
│   ├── baseline_tests.py       # Tests for baseline extractor
│   ├── cli_tests.py            # CLI argument and pipeline tests
│   ├── downloads_tests.py      # HTTP download tests
│   ├── feeds_tests.py          # Feed parsing tests
│   ├── filters_tests.py        # Text filter and deduplication tests
│   ├── metadata_tests.py       # Metadata extraction tests
│   ├── json_metadata_tests.py  # JSON-LD metadata tests
│   ├── deduplication_tests.py  # Simhash and dedup tests
│   ├── sitemaps_tests.py       # Sitemap tests
│   ├── spider_tests.py         # Spider/crawl tests
│   ├── xml_tei_tests.py        # XML/TEI output tests
│   ├── realworld_tests.py      # Tests against real web pages
│   ├── evaluate.py             # Evaluation script comparing extractors
│   ├── evaldata.py             # Evaluation data helpers
│   ├── resources/              # HTML fixtures and test resources
│   ├── eval/                   # Evaluation datasets
│   └── cache/                  # Cached test data
│
└── docs/                       # Sphinx documentation source
    ├── index.rst               # Docs index
    ├── quickstart.rst          # Getting started guide
    ├── installation.rst        # Installation instructions
    ├── usage-python.rst        # Python API usage docs
    ├── usage-cli.rst           # CLI usage docs
    ├── corefunctions.rst       # API reference for core functions
    ├── settings.rst            # Settings configuration docs
    ├── crawls.rst              # Crawling and spidering docs
    ├── downloads.rst           # Download engine docs
    ├── deduplication.rst       # Deduplication docs
    └── ...                     # Additional guides and tutorials
```

## Module and Package Organization

The `trafilatura` package contains 22 Python modules organized around four functional areas:

### 1. Extraction Core
- **`core.py`** — Central orchestration. Exports `extract()`, `bare_extraction()`, `extract_with_metadata()`. Implements `trafilatura_sequence()` (the extraction cascade) and `determine_returnstring()` (output format routing).
- **`settings.py`** — Data classes: `Extractor` (all extraction options, config-backed) and `Document` (holds all extracted content + metadata). Also holds module-wide constants: `PARALLEL_CORES`, `LRU_SIZE`, `MAX_LINKS`, `MANUALLY_CLEANED`, `MANUALLY_STRIPPED`, `TAG_CATALOG`, `JUSTEXT_LANGUAGES`.
- **`main_extractor.py`** — Custom extraction algorithms. Functions: `extract_content()`, `extract_comments()`, `handle_titles()`, `handle_formatting()`, `handle_paragraphs()`, `handle_table()`, `handle_lists()`. Uses XPath to identify body/comment zones.
- **`htmlprocessing.py`** — Pre-processing HTML trees. Functions: `tree_cleaning()`, `convert_tags()`, `process_node()`, `handle_textnode()`, `prune_unwanted_nodes()`, `delete_by_link_density()`, `link_density_test_tables()`, `build_html_output()`.
- **`external.py`** — Wraps third-party extractors. Functions: `try_readability()`, `compare_extraction()`. Uses `readability_lxml.Document` and `justext`.
- **`baseline.py`** — Last-resort extractor. Functions: `baseline()` (paragraph scan + JSON-LD body), `html2txt()` (simple HTML to text).
- **`xml.py`** — Output serialization. Functions: `control_xml_output()` (XML/TEI), `xmltotxt()` (text/markdown), `xmltocsv()` (CSV), `build_json_output()` (JSON), `build_html_output()` (HTML). TEI validation via DTD.

### 2. Metadata
- **`metadata.py`** — Main metadata orchestrator. Exports `extract_metadata()`. Sub-functions: `examine_meta()`, `extract_opengraph()`, `extract_meta_json()`, `extract_title()`, `extract_author()`, `extract_url()`, `extract_sitename()`, `extract_catstags()`, `extract_license()`.
- **`json_metadata.py`** — Parses JSON-LD `schema.org` objects. Functions: `extract_json()`, `normalize_authors()`, `normalize_json()`, `extract_json_parse_error()`.
- **`xpaths.py`** — Central repository of all XPath expressions: `BODY_XPATH`, `COMMENTS_XPATH`, `AUTHOR_XPATHS`, `TITLE_XPATHS`, `CATEGORIES_XPATHS`, `TAGS_XPATHS`, `OVERALL_DISCARD_XPATH`, `PRECISION_DISCARD_XPATH`, `REMOVE_COMMENTS_XPATH`, etc.

### 3. Downloading and Discovery
- **`downloads.py`** — HTTP engine. Classes: `Response`. Functions: `fetch_url()`, `fetch_response()`, `buffered_downloads()`, `buffered_response_downloads()`, `add_to_compressed_dict()`, `load_download_buffer()`, `is_live_page()`. Supports urllib3 and pycurl.
- **`sitemaps.py`** — Sitemap parsing. Class: `SitemapObject`. Functions: `sitemap_search()`, `process_sitemap()`. Supports TXT and XML sitemaps, including gzipped, sitemap indexes, and xhtml:link tags.
- **`feeds.py`** — Feed discovery and parsing. Class: `FeedParameters`. Functions: `find_feed_urls()`. Handles RSS, Atom, and JSON Feed formats.
- **`spider.py`** — Web crawler. Class: `CrawlParameters`. Functions: `crawl_page()`, `focused_crawler()`. Respects `robots.txt`, uses `courlan.UrlStore` for domain-aware crawling.
- **`utils.py`** — Shared utilities: `load_html()`, `decode_file()`, `handle_compressed_file()`, `language_filter()`, `language_classifier()`, `check_html_lang()`, `normalize_unicode()`, `text_chars_test()`, `make_chunks()`, and many regex constants.
- **`deduplication.py`** — Content deduplication. Class: `Simhash`. Functions: `content_fingerprint()`, `duplicate_test()`, `generate_bow_hash()`, `sample_tokens()`, `is_similar_domain()`.

### 4. CLI and Meta
- **`cli.py`** — argparse CLI. Functions: `add_args()`, `parse_args()`, `map_args()`, `main()`, `process_args()`. Entry point: `trafilatura.cli:main`.
- **`cli_utils.py`** — CLI pipeline helpers. Functions: `examine()`, `write_result()`, `url_processing_pipeline()`, `file_processing_pipeline()`, `cli_discovery()`, `cli_crawler()`, `probe_homepage()`, `load_input_dict()`, `load_blacklist()`.
- **`meta.py`** — Module-wide LRU cache reset. Function: `reset_caches()`.

## Key Files and Their Roles

| File | Role |
|------|------|
| `trafilatura/__init__.py` | Defines `__version__ = "2.0.0"` and the public API (`__all__`) |
| `trafilatura/settings.py` | Houses `Extractor` + `Document` data classes and all module-level constants |
| `trafilatura/core.py` | The main orchestrator: `extract()`, `bare_extraction()`, `extract_with_metadata()` |
| `trafilatura/xpaths.py` | Single source of truth for all XPath expressions |
| `trafilatura/settings.cfg` | Default configuration: download timeouts, file sizes, extraction thresholds |
| `trafilatura/data/tei_corpus.dtd` | TEI DTD used for `--validate-tei` |
| `pyproject.toml` | Build system, dependencies, optional extras (`all`, `dev`), CLI entry point |

## Code Organization Patterns

- **Dataclass-like slots classes**: Both `Extractor` and `Document` use `__slots__` for memory efficiency and attribute validation. `Document` has `.as_dict()` and `.from_dict()` methods for dict interop.
- **Cascade extraction**: Extraction is multi-stage with fallbacks — primary extractor → external comparison (readability + jusText) → baseline. The cascade is transparent and configured via `Extractor.fast` and `Extractor.focus`.
- **Configuration via ConfigParser**: All tunable defaults live in `settings.cfg` and are loaded into `Extractor` via `_add_config()`. Custom config files are supported.
- **Optional dependency pattern**: All optional packages (`pycurl`, `py3langid`, `brotli`, `zstandard`, `cchardet`) are guarded by try/except imports with boolean flags (e.g., `HAS_PYCURL`, `LANGID_FLAG`).
- **Internal vs. public API**: `bare_extraction()` returns a `Document` object (Python-native). `extract()` returns a string. `extract_with_metadata()` returns a `Document` with metadata populated.
- **LRU caching**: Used extensively in `deduplication.py` and `utils.py` for performance. `meta.reset_caches()` provides a way to release memory.
- **Thread-safe downloads**: `ThreadPoolExecutor` for I/O-bound parallel downloads; `ProcessPoolExecutor` for CPU-bound batch processing in `cli_utils.py`.
