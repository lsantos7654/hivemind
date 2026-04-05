# markdown-crawler — Repository Summary

## Repository Purpose and Goals

`markdown-crawler` (PyPI: `markdown-crawler`, version `0.0.8`) is a multithreaded Python web crawler that recursively traverses websites and converts each HTML page into a Markdown file. Created by Paul Pierre (@paulpierre), the library's primary motivation is to prepare web content for Large Language Model (LLM) consumption — specifically for RAG (Retrieval Augmented Generation) pipelines and LLM fine-tuning workflows.

The core insight behind the project is that Markdown is human-readable, preserves document structure (headings, tables, images, links), and produces a smaller footprint than raw HTML — making it ideal as an intermediate representation when chunking and indexing documents for LLMs.

## Key Features and Capabilities

- **Multithreaded crawling**: Uses Python's `threading` module with a configurable number of worker threads (default: 5) and a shared `queue.Queue` to parallelize HTTP requests.
- **Recursive depth control**: Crawls child links up to a configurable `max_depth` (default: 3 levels deep).
- **Resume / incremental mode**: Skips writing a Markdown file if it already exists on disk, allowing interrupted crawls to be continued.
- **CSS selector targeting**: The `target_content` parameter accepts CSS selectors (e.g., `div#content`, `article`) to extract only the relevant portion of each page; if omitted, falls back to a heuristic that picks the largest text element.
- **Link scope control**: `target_links` restricts which HTML elements are scanned for outgoing links (default: `body`). `valid_paths` allows an allowlist of URL path prefixes. `is_domain_match` and `is_base_path_match` provide coarse domain/path filtering.
- **HTML-to-Markdown conversion**: Delegates to the `markdownify` library, preserving inline images within `<td>`, `<th>`, `<a>`, and `<figure>` tags.
- **Link stripping**: The `is_links=False` flag can strip `<a>` tags from the output Markdown via markdownify's `strip` option.
- **Script/style stripping**: Automatically removes `<script>` and `<style>` tags via BeautifulSoup before conversion.
- **URL normalization**: Strips trailing slashes and fragments so duplicates are not re-crawled.
- **Verbose/debug logging**: Configurable via the `is_debug` flag; uses Python's standard `logging` module.
- **CLI interface**: Ships a `markdown-crawler` console script for immediate use without writing Python code.

## Primary Use Cases and Target Audience

The README explicitly lists the intended use cases:

1. **RAG (Retrieval Augmented Generation)**: Normalize large websites into chunked Markdown documents for vector-store ingestion (by header, paragraph, or sentence).
2. **LLM fine-tuning**: Generate a corpus of structured Markdown as a pre-processing step before extracting Q&A pairs with GPT-3.5 or similar models.
3. **Agent knowledge bases**: Build domain-specific knowledge corpora for autonomous agents (e.g., integrating with Microsoft AutoGen).
4. **Online/continuous RAG**: Combine with a SERP API to scrape and index top search results on the fly as a chatbot learning mechanism.

The target audience is ML engineers, AI application developers, and researchers who need to convert web documentation, wikis, or knowledge bases into LLM-ready text files.

## High-Level Architecture Overview

The library has a minimal, single-module architecture:

```
markdown_crawler/
├── __init__.py   ← All core logic (crawl, worker, md_crawl, helpers)
└── cli.py        ← argparse-based CLI wrapper around md_crawl()
```

The execution model follows a **thread pool + shared queue** pattern:

1. `md_crawl()` is the public entry point. It validates inputs, creates the output directory, initializes a `queue.Queue` with the seed URL at depth 0, then spawns `num_threads` `threading.Thread` objects each running the `worker()` function.
2. `worker()` continuously dequeues `(depth, url)` tuples. For each URL, it derives a filesystem path, calls `crawl()`, and enqueues discovered child URLs at `depth + 1`. It sleeps 1 second between requests to be polite.
3. `crawl()` handles a single URL: fetches with `requests.get()`, parses with BeautifulSoup, writes the Markdown file (if not already present), and returns a list of child URLs.
4. A `set` (`already_crawled`) shared across all threads tracks visited URLs to prevent duplicate processing. No lock is used around this set — a minor thread-safety concern in the current implementation.

## Related Projects and Dependencies

| Dependency | Purpose |
|---|---|
| `beautifulsoup4` | HTML parsing and CSS selector queries |
| `requests` | HTTP GET requests |
| `markdownify` | HTML-to-Markdown conversion (by Matthew Tretter, MIT licensed) |

The README mentions integration potential with:
- **Microsoft AutoGen** — for building expert agents from crawled corpora
- **SERP APIs** — for online RAG pipelines
- Any LLM inference framework (OpenAI GPT, Mistral, etc.) for downstream processing
