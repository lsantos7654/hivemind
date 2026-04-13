# MarkItDown — Code Structure

## Annotated Directory Tree

```
markitdown/                          # Repository root
├── .devcontainer/                   # VS Code devcontainer configuration
├── .github/                         # GitHub Actions CI workflows
├── .pre-commit-config.yaml          # Pre-commit hook configuration
├── Dockerfile                       # Top-level Docker image for the CLI
├── README.md                        # Main project README with usage examples
├── packages/                        # Python monorepo packages
│   ├── markitdown/                  # Core library package
│   │   ├── pyproject.toml           # Build config, dependencies, optional extras
│   │   ├── README.md                # Package-level README
│   │   ├── ThirdPartyNotices.md     # Third-party license notices
│   │   ├── tests/                   # Test suite
│   │   │   ├── __init__.py
│   │   │   ├── _test_vectors.py     # Test vector definitions (expected outputs)
│   │   │   ├── test_cli_misc.py     # CLI-level miscellaneous tests
│   │   │   ├── test_cli_vectors.py  # CLI-level conversion tests
│   │   │   ├── test_docintel_html.py # Azure Document Intelligence tests
│   │   │   ├── test_module_misc.py  # Module-level miscellaneous tests
│   │   │   ├── test_module_vectors.py # Module-level conversion tests
│   │   │   ├── test_pdf_masterformat.py # PDF MasterFormat numbering tests
│   │   │   ├── test_pdf_memory.py   # PDF memory/streaming tests
│   │   │   ├── test_pdf_tables.py   # PDF table extraction tests
│   │   │   └── test_files/          # Test fixture files (PDFs, XLSX, DOCX, etc.)
│   │   └── src/
│   │       └── markitdown/          # Main Python package
│   │           ├── __about__.py     # Package version (__version__ = "0.1.6b2")
│   │           ├── __init__.py      # Public API exports
│   │           ├── __main__.py      # CLI entry point (markitdown command)
│   │           ├── _base_converter.py   # Abstract base classes
│   │           ├── _exceptions.py       # Exception hierarchy
│   │           ├── _markitdown.py       # Core MarkItDown orchestration class
│   │           ├── _stream_info.py      # StreamInfo dataclass
│   │           ├── _uri_utils.py        # URI parsing utilities
│   │           ├── py.typed             # PEP 561 marker (typed package)
│   │           ├── converter_utils/     # Shared conversion utilities
│   │           │   ├── __init__.py
│   │           │   └── docx/
│   │           │       ├── __init__.py
│   │           │       ├── pre_process.py   # DOCX pre-processing (strip unsupported elements)
│   │           │       └── math/            # Math equation handling for DOCX
│   │           └── converters/          # Individual converter implementations
│   │               ├── __init__.py      # Converter public re-exports
│   │               ├── _audio_converter.py      # WAV/MP3/M4A/MP4 → Markdown
│   │               ├── _bing_serp_converter.py  # Bing search results page → Markdown
│   │               ├── _csv_converter.py        # CSV → Markdown table
│   │               ├── _doc_intel_converter.py  # Azure Document Intelligence converter
│   │               ├── _docx_converter.py       # DOCX → Markdown (via mammoth)
│   │               ├── _epub_converter.py       # EPUB → Markdown
│   │               ├── _exiftool.py             # ExifTool metadata extraction helper
│   │               ├── _html_converter.py       # HTML → Markdown (via markdownify)
│   │               ├── _image_converter.py      # JPEG/PNG → Markdown (EXIF + LLM caption)
│   │               ├── _ipynb_converter.py      # Jupyter notebook → Markdown
│   │               ├── _llm_caption.py          # LLM image captioning helper
│   │               ├── _markdownify.py          # Custom markdownify subclass
│   │               ├── _outlook_msg_converter.py # Outlook .msg → Markdown
│   │               ├── _pdf_converter.py        # PDF → Markdown (pdfplumber + pdfminer)
│   │               ├── _plain_text_converter.py # Plain text / catch-all → Markdown
│   │               ├── _pptx_converter.py       # PPTX → Markdown (slides, tables, charts)
│   │               ├── _rss_converter.py        # RSS/Atom feeds → Markdown
│   │               ├── _transcribe_audio.py     # Speech-to-text helper
│   │               ├── _wikipedia_converter.py  # Wikipedia HTML → Markdown
│   │               ├── _xlsx_converter.py       # XLSX/XLS → Markdown tables
│   │               ├── _youtube_converter.py    # YouTube pages → Markdown (+ transcript)
│   │               └── _zip_converter.py        # ZIP archives → concatenated Markdown
│   ├── markitdown-mcp/              # MCP server package
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── Dockerfile               # Docker image for the MCP server
│   │   ├── tests/
│   │   └── src/
│   │       └── markitdown_mcp/
│   │           ├── __about__.py     # Version
│   │           ├── __init__.py
│   │           ├── __main__.py      # MCP server entry point (STDIO + HTTP/SSE)
│   │           └── py.typed
│   ├── markitdown-sample-plugin/    # Reference plugin demonstrating plugin interface
│   │   ├── pyproject.toml           # Declares entry-point "markitdown.plugin"
│   │   ├── README.md
│   │   ├── tests/
│   │   └── src/
│   │       └── markitdown_sample_plugin/
│   │           ├── __about__.py
│   │           ├── __init__.py
│   │           ├── _plugin.py       # register_converters() + RtfConverter implementation
│   │           └── py.typed
│   └── markitdown-ocr/              # OCR plugin package (documented in README)
│       ├── pyproject.toml
│       └── README.md
```

## Module and Package Organization

### Core Package: `markitdown`

The package follows a clean separation of concerns:

**Orchestration layer** (`_markitdown.py`):
- `MarkItDown` class: the single public entry point for all conversions.
- Manages the converter registry, plugin loading, global options (LLM client, exiftool path, etc.).
- Implements `convert()`, `convert_local()`, `convert_stream()`, `convert_uri()`, `convert_url()`, `convert_response()`.
- Delegates to `_get_stream_info_guesses()` for content-type detection via `magika` and MIME heuristics.
- Calls `_convert()` which iterates the sorted converter list, passing each a `StreamInfo` and binary stream.

**Abstraction layer** (`_base_converter.py`):
- `DocumentConverter`: abstract base with `accepts()` and `convert()` methods.
- `DocumentConverterResult`: holds the resulting `markdown` string and optional `title`. Has a deprecated `text_content` alias for `markdown`.

**Type metadata** (`_stream_info.py`):
- `StreamInfo`: frozen dataclass with fields: `mimetype`, `extension`, `charset`, `filename`, `local_path`, `url`. Supports `copy_and_update()` for non-destructive field merging.

**Exception hierarchy** (`_exceptions.py`):
- `MarkItDownException` (base)
  - `MissingDependencyException`: missing optional dependency
  - `UnsupportedFormatException`: no converter matched
  - `FileConversionException`: converter matched but failed; carries `List[FailedConversionAttempt]`
- `FailedConversionAttempt`: data class tracking which converter failed and its `exc_info`.

**CLI** (`__main__.py`):
- `main()`: `argparse`-based CLI. Accepts filename or stdin. Supports `-o` (output), `-x` (extension hint), `-m` (MIME hint), `-c` (charset hint), `-d`/`-e` (Document Intelligence), `-p` (plugins), `--list-plugins`, `--keep-data-uris`.

### Converter Module (`converters/`)

Each converter is a self-contained file following a consistent pattern:
1. Attempt optional-dependency import at module load time; store any `ImportError` as `_dependency_exc_info`.
2. Define `ACCEPTED_MIME_TYPE_PREFIXES` and `ACCEPTED_FILE_EXTENSIONS` constants.
3. Implement a `DocumentConverter` subclass with `accepts()` checking extension/mimetype (and occasionally URL or stream bytes) and `convert()` doing the actual work.
4. In `convert()`, re-raise `_dependency_exc_info` as `MissingDependencyException` if the optional package is absent.

**Special converters worth noting:**

- `_html_converter.py` (`HtmlConverter`): foundation for many others; provides `convert_string()` for HTML string → Markdown, widely used by DocxConverter, XlsxConverter, PptxConverter, EpubConverter, and CsvConverter.
- `_markdownify.py` (`_CustomMarkdownify`): extends `markdownify.MarkdownConverter` to strip JavaScript links, truncate data URIs (unless `keep_data_uris=True`), escape URIs, and convert checkboxes.
- `_pdf_converter.py` (`PdfConverter`): two-pass strategy — attempts `pdfplumber`-based form/table extraction first, falls back to `pdfminer` for prose pages. Includes sophisticated column-detection logic for borderless tables and MasterFormat partial numbering merging.
- `_zip_converter.py` (`ZipConverter`): takes a back-reference to the parent `MarkItDown` instance to recursively convert each file in the archive.
- `_doc_intel_converter.py` (`DocumentIntelligenceConverter`): registered at the top of the priority stack when `docintel_endpoint` is provided; raises during `__init__` (not `convert()`) if azure dependencies are absent.
- `_youtube_converter.py` (`YouTubeConverter`): checks `stream_info.url` for `youtube.com/watch?` as part of `accepts()`; fetches transcript via `youtube-transcript-api` with retry logic.

### Converter Utilities (`converter_utils/`)

- `converter_utils/docx/pre_process.py`: Pre-processes DOCX streams before passing to `mammoth`, stripping or transforming elements that mammoth handles poorly (e.g., math equations).
- `converter_utils/docx/math/`: Handles MathML / OMML equation rendering within DOCX files.

## Key Files and Their Roles

| File | Role |
|---|---|
| `src/markitdown/__init__.py` | Defines `__all__`: `MarkItDown`, `DocumentConverter`, `DocumentConverterResult`, `StreamInfo`, all exceptions, priority constants |
| `src/markitdown/_markitdown.py` | Core orchestrator — `MarkItDown` class (783 lines) |
| `src/markitdown/_base_converter.py` | Abstract base classes for converters and results |
| `src/markitdown/_stream_info.py` | `StreamInfo` immutable dataclass |
| `src/markitdown/_exceptions.py` | Exception hierarchy |
| `src/markitdown/__main__.py` | CLI (`markitdown` command) |
| `src/markitdown/converters/__init__.py` | Re-exports all 20 built-in converter classes |
| `src/markitdown/converters/_pdf_converter.py` | Most complex converter (589 lines) — PDF extraction with table detection |
| `src/markitdown/converters/_pptx_converter.py` | PowerPoint converter with image captioning and chart support |
| `src/markitdown/converters/_html_converter.py` | HTML → Markdown; used as intermediary by many other converters |
| `src/markitdown/converters/_doc_intel_converter.py` | Azure Document Intelligence integration |
| `packages/markitdown-mcp/src/markitdown_mcp/__main__.py` | MCP server — STDIO and HTTP/SSE modes |
| `packages/markitdown-sample-plugin/src/markitdown_sample_plugin/_plugin.py` | RTF plugin — canonical plugin interface example |

## Code Organization Patterns

1. **Converter registry with priority sorting**: Converters stored as `List[ConverterRegistration]` (dataclass with `converter` and `priority` fields). Sorted by priority (`float`) using stable sort before each `_convert()` call. Default priority `0.0` (specific formats); `PlainTextConverter`, `HtmlConverter`, `ZipConverter` use `10.0` (generic catch-alls, tried last).

2. **Lazy optional dependency loading**: Each converter module-level `try/except ImportError` captures the exception to be re-raised as `MissingDependencyException` when `convert()` is actually called, rather than crashing at import time.

3. **Stream-position preservation contract**: All `accepts()` implementations must leave `file_stream` at its original position. Any reads inside `accepts()` must be followed by `file_stream.seek(cur_pos)`. The orchestrator asserts this invariant.

4. **Multiple StreamInfo guesses**: `_get_stream_info_guesses()` produces an ordered list of `StreamInfo` candidates (combining MIME hints, extension hints, and magika's content detection). The `_convert()` loop tries all registered converters for each guess in order, plus a final catch-all empty `StreamInfo()`.

5. **HTML as intermediate format**: DocxConverter, XlsxConverter, XlsConverter, PptxConverter, EpubConverter, and CsvConverter all produce HTML and then call `HtmlConverter.convert_string()` to generate the final Markdown.

6. **Plugin entry-point convention**: Plugins register via `[project.entry-points."markitdown.plugin"]` in `pyproject.toml`. The loaded module must expose `register_converters(markitdown: MarkItDown, **kwargs)`.
