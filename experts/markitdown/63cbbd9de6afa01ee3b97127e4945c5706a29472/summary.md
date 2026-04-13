# MarkItDown — Repository Summary

## Repository Purpose and Goals

MarkItDown is a lightweight Python utility created by Microsoft's AutoGen Team (primary author: Adam Fourney) for converting a wide variety of file formats and web resources into Markdown text. Its central purpose is to make document content accessible to Large Language Models (LLMs) and downstream text-analysis pipelines. The library is intentionally focused on fidelity for LLM consumption — not pixel-perfect human-readable rendering — preserving structure (headings, lists, tables, links) while keeping output token-efficient.

The project occupies a similar niche to the older `textract` library but differs in that it targets Markdown output specifically because mainstream LLMs (GPT-4o, Claude, etc.) are trained on large volumes of Markdown and understand it natively.

## Key Features and Capabilities

- **Broad format support**: PDF, PPTX, DOCX, XLSX/XLS, HTML, CSV, JSON, XML, plain text, images (JPEG/PNG), audio (WAV/MP3/M4A/MP4), YouTube URLs, RSS feeds, ePubs, ZIP archives, Jupyter notebooks (.ipynb), Outlook .msg files, Wikipedia pages, and Bing SERP pages.
- **Stream-based I/O**: All converters work directly from binary file streams. No temporary files are created during conversion.
- **Content-type inference**: Uses Google's `magika` library plus MIME-type and extension heuristics to auto-detect file types. Multiple ordered "guesses" are tried when the type is ambiguous.
- **LLM image descriptions**: When an OpenAI-compatible `llm_client` and `llm_model` are provided, images embedded in PPTX slides, standalone image files, and (via the OCR plugin) PDF/DOCX/XLSX embedded images are sent to the LLM for captioning.
- **Azure Document Intelligence**: Optional high-quality extraction via Azure AI Document Intelligence for PDFs, Office formats, and images — replaces local converters when configured.
- **Plugin system**: Third-party converters can be registered via Python packaging entry-points (`markitdown.plugin` group). Plugins are opt-in and loaded lazily.
- **Priority-based converter pipeline**: Converters are tried in priority order. Plugins can inject converters at any priority position relative to built-ins.
- **MCP server**: The companion `markitdown-mcp` package exposes MarkItDown as a Model Context Protocol (MCP) server, enabling integration with LLM applications like Claude Desktop via STDIO or HTTP/SSE transport.
- **CLI**: A `markitdown` command-line tool accepts files, stdin, and URI arguments; supports output to file and optional hints for MIME type, charset, and extension.
- **Docker support**: The repository ships a Dockerfile for containerized use.

## Primary Use Cases and Target Audience

- **AI/LLM developers** building pipelines that need to ingest unstructured documents as context.
- **RAG (Retrieval-Augmented Generation) systems** requiring document ingestion into vector stores.
- **Automation engineers** converting large document repositories to searchable Markdown.
- **MCP integrations** where Claude Desktop or similar tools need to fetch and read arbitrary files.
- **Data scientists** pre-processing Excel spreadsheets, PDFs, or presentations for text analysis.

## High-Level Architecture Overview

The repository is a Python monorepo under `packages/` containing four packages:

1. **`markitdown`** — The core library. Exposes the `MarkItDown` class which orchestrates conversion using a registry of `DocumentConverter` subclasses. Each converter implements two methods: `accepts()` (quick determination of whether it handles a given stream) and `convert()` (actual Markdown production). The `MarkItDown._convert()` method iterates registered converters sorted by priority, trying each until one succeeds.

2. **`markitdown-mcp`** — A minimal MCP server wrapping `MarkItDown` using the `mcp` SDK and `FastMCP`. Exposes a single `convert_to_markdown(uri)` tool. Supports both STDIO and HTTP/SSE transports via `uvicorn`+`starlette`.

3. **`markitdown-sample-plugin`** — A reference plugin demonstrating the plugin interface. Adds RTF file support via the `striprtf` library. Shows how to implement `register_converters()` and a `DocumentConverter` subclass.

4. **`markitdown-ocr`** — A separately distributed plugin (not in this monorepo's `packages/` tree but documented in the README) that adds OCR support for embedded images in Office documents using `llm_client`/`llm_model`.

## Related Projects and Dependencies

- **`magika`** (Google): Content-type detection from binary content.
- **`beautifulsoup4`** + **`markdownify`**: HTML parsing and HTML-to-Markdown conversion.
- **`charset-normalizer`**: Character encoding detection for text streams.
- **`defusedxml`**: Safe XML/HTML parsing to avoid XML bomb attacks.
- **`requests`**: HTTP fetching for URIs; MarkItDown sets an `Accept: text/markdown` preference header.
- **`pdfminer.six`** + **`pdfplumber`**: PDF text and table extraction.
- **`mammoth`**: DOCX-to-HTML conversion.
- **`python-pptx`**: PowerPoint parsing.
- **`pandas`** + **`openpyxl`** / **`xlrd`**: Excel spreadsheet reading.
- **`olefile`**: Outlook .msg parsing.
- **`pydub`** + **`SpeechRecognition`**: Audio transcription.
- **`youtube-transcript-api`**: YouTube transcript fetching.
- **`azure-ai-documentintelligence`** + **`azure-identity`**: Azure AI integration.
- **`mcp`**: Model Context Protocol SDK (used by `markitdown-mcp`).
- **`hatchling`** + **`hatch`**: Build system and project management.
- **`textract`** (inspiration only): Predecessor tool in the same space.
