# Trafilatura — Summary

## Repository Purpose and Goals

Trafilatura (version 2.0.0) is a Python package and command-line tool designed for **discovering and extracting text data from the Web**. Its primary goal is to turn raw HTML into structured, meaningful data by focusing on the actual content while filtering out recurring noise (headers, footers, navigation menus, ads). The name is an Italian word for "wire drawing", symbolizing the refinement and conversion process.

The project originated as a PhD project at the crossroads of linguistics and NLP, initially developed to create text databases for research at the Berlin-Brandenburg Academy of Sciences (DWDS and ZDL units). It is now a production-grade package (Apache 2.0 license since v1.8.0, previously GPLv3+) actively used by companies such as HuggingFace, IBM, and Microsoft Research, as well as academic institutions.

## Key Features and Capabilities

- **Web discovery**: Support for sitemaps (TXT, XML) and feeds (ATOM, JSON, RSS), with smart crawling and URL management (filtering and deduplication via the `courlan` library).
- **Parallel downloads**: Efficient, polite processing of download queues using `urllib3` or optionally `pycurl`, with configurable retry strategies, timeout, SSL handling, and SOCKS proxy support.
- **Robust content extraction**: Multi-stage cascade — a primary custom extractor, followed by comparison with third-party algorithms (readability-lxml, jusText), and a baseline fallback. Supports paragraphs, titles, lists, quotes, code, line breaks, and inline formatting.
- **Metadata extraction**: Title, author, date (via `htmldate`), site name, URL, description, categories, tags, license, and page type — sourced from OpenGraph, JSON-LD, Dublin Core, Twitter Cards, HTML meta tags, and XPath heuristics.
- **Multiple output formats**: TXT (plain text), Markdown, CSV, JSON, XML, and XML-TEI (validated against the TEI DTD).
- **Content filtering**: Language detection (via `py3langid`), deduplication (Simhash + LRU cache), URL and author blacklisting, XPath-based pruning.
- **Configurable precision/recall**: Three extraction focus modes — "balanced" (default), "precision" (less noise), and "recall" (more text).
- **Optional add-ons**: Language detection (`py3langid`), faster character detection (`cchardet`/`faust-cchardet`), brotli/zstd compression support, pycurl for faster downloads.

## Primary Use Cases and Target Audience

- **NLP/linguistics researchers** building web corpora for language studies.
- **Data engineers** constructing large-scale training datasets for ML/LLM pipelines.
- **Web scraping developers** who need a high-quality article extractor without boilerplate.
- **Journalists and information analysts** collecting and archiving web content.
- **Academic institutions** doing computational social science or digital humanities research.

Typical workflows include: downloading and extracting text from a single URL, batch-processing lists of URLs, crawling websites via sitemaps or feeds, and building deduplicated text corpora.

## High-Level Architecture Overview

The library is organized around three pillars:

1. **Downloading** (`downloads.py`): `fetch_url()` / `fetch_response()` handle HTTP with urllib3 or pycurl. Batch downloads use `buffered_downloads()` with `ThreadPoolExecutor`. URL queues are managed domain-aware via `courlan.UrlStore`.

2. **Extraction** (`core.py`, `main_extractor.py`, `external.py`, `baseline.py`): The main entry point is `extract()` or `bare_extraction()`. Extraction follows a cascade:
   - `tree_cleaning()` — remove boilerplate HTML elements
   - `convert_tags()` — map HTML tags to internal TEI-like schema
   - `extract_content()` / `extract_comments()` — custom XPath + heuristic extractor
   - `compare_extraction()` — compare against readability-lxml and jusText
   - `baseline()` — last-resort paragraph-level extraction
   - Language and deduplication filters
   - `determine_returnstring()` — serialize to requested format

3. **Metadata** (`metadata.py`): `extract_metadata()` collects title, author, date, URL, sitename, description, categories, tags, image, license, and pagetype from OpenGraph, JSON-LD, Dublin Core, itemprop, and HTML heuristics.

Discovery features in `sitemaps.py`, `feeds.py`, and `spider.py` handle crawling workflows. The CLI in `cli.py` / `cli_utils.py` exposes all functionality via argparse.

## Related Projects and Dependencies

**Core dependencies**: `lxml` (HTML/XML parsing), `urllib3` (HTTP), `certifi` (SSL), `charset_normalizer` (encoding detection), `courlan` (URL management), `htmldate` (date extraction), `justext` (stopword-based content extraction).

**Optional dependencies**: `py3langid` (language detection), `pycurl` (faster downloads), `brotli`/`zstandard` (compression), `cchardet`/`faust-cchardet` (faster encoding detection).

**Ecosystem packages** from the same author: `htmldate`, `courlan`, `trafilatura-gui` (GUI, removed in 2.0).

**Academic citation**: Barbaresi, A. "Trafilatura: A Web Scraping Library and Command-Line Tool for Text Discovery and Extraction", ACL/IJCNLP 2021. DOI: 10.18653/v1/2021.acl-demo.15.
