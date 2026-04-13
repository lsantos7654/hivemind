# MarkItDown — APIs and Interfaces

## Public API (`markitdown` package)

All public symbols are exported from `packages/markitdown/src/markitdown/__init__.py`:

```python
from markitdown import (
    MarkItDown,
    DocumentConverter,
    DocumentConverterResult,
    StreamInfo,
    MarkItDownException,
    MissingDependencyException,
    FailedConversionAttempt,
    FileConversionException,
    UnsupportedFormatException,
    PRIORITY_SPECIFIC_FILE_FORMAT,
    PRIORITY_GENERIC_FILE_FORMAT,
)
```

---

## `MarkItDown` Class

**Location**: `src/markitdown/_markitdown.py:93`

The central orchestrator. Instantiate once, call `convert()` many times.

### Constructor

```python
MarkItDown(
    *,
    enable_builtins: bool | None = None,   # Default True; set False for manual setup
    enable_plugins: bool | None = None,    # Default False; set True to load installed plugins

    # Passed through to built-in converters:
    llm_client=None,                        # OpenAI-compatible client for image captioning
    llm_model: str | None = None,           # Model name, e.g. "gpt-4o"
    llm_prompt: str | None = None,          # Custom caption prompt (optional)
    exiftool_path: str | None = None,       # Explicit path to ExifTool binary
    style_map: str | None = None,           # mammoth style_map for DOCX heading styles

    # Azure Document Intelligence (optional):
    docintel_endpoint: str | None = None,   # If set, registers DocumentIntelligenceConverter
    docintel_credential=None,               # AzureKeyCredential | TokenCredential (default: DefaultAzureCredential)
    docintel_file_types=None,               # List[DocumentIntelligenceFileType] to restrict file types
    docintel_api_version: str | None = None, # Override API version (default: "2024-07-31-preview")

    # Networking:
    requests_session=None,                  # Custom requests.Session (default: auto-created)
)
```

**Notes:**
- When `exiftool_path` is not provided, MarkItDown auto-discovers `exiftool` in well-known system paths (`/usr/bin`, `/usr/local/bin`, `/opt/homebrew/bin`, etc.) via `shutil.which`.
- The `requests.Session` is pre-configured with `Accept: text/markdown, text/html;q=0.9, ...` to request Markdown from servers that support it (e.g., Cloudflare's Markdown-for-Agents feature).

### Primary Conversion Methods

#### `convert(source, *, stream_info=None, **kwargs) → DocumentConverterResult`

**Location**: `src/markitdown/_markitdown.py:252`

Universal entry point. Dispatches based on `source` type:

| `source` type | Dispatches to |
|---|---|
| `str` starting with `http:`, `https:`, `file:`, `data:` | `convert_uri()` |
| `str` (local path) | `convert_local()` |
| `pathlib.Path` | `convert_local()` |
| `requests.Response` | `convert_response()` |
| Binary file-like object (BinaryIO) | `convert_stream()` |

```python
from markitdown import MarkItDown

md = MarkItDown()

# Local file
result = md.convert("report.pdf")

# URL
result = md.convert("https://en.wikipedia.org/wiki/Python_(programming_language)")

# Path object
from pathlib import Path
result = md.convert(Path("spreadsheet.xlsx"))

# Binary stream
with open("doc.docx", "rb") as f:
    result = md.convert(f)

print(result.markdown)
```

#### `convert_local(path, *, stream_info=None, **kwargs) → DocumentConverterResult`

**Location**: `src/markitdown/_markitdown.py:302`

Converts a local file path (str or Path). Builds `StreamInfo` from filename/extension, opens in binary mode, then delegates to `_convert()`.

#### `convert_stream(stream, *, stream_info=None, **kwargs) → DocumentConverterResult`

**Location**: `src/markitdown/_markitdown.py:339`

Converts a binary file-like object. If the stream is not seekable, buffers into `io.BytesIO` first. Requires binary mode — `io.TextIOBase` instances are rejected.

```python
import io
data = open("file.pdf", "rb").read()
result = md.convert_stream(io.BytesIO(data), stream_info=StreamInfo(extension=".pdf"))
```

#### `convert_uri(uri, *, stream_info=None, mock_url=None, **kwargs) → DocumentConverterResult`

**Location**: `src/markitdown/_markitdown.py:405`

Handles `file:`, `data:`, `http:`, and `https:` URIs. For `data:` URIs, decodes base64 content and passes as a stream.

#### `convert_response(response, *, stream_info=None, **kwargs) → DocumentConverterResult`

**Location**: `src/markitdown/_markitdown.py:466`

Converts a `requests.Response` object. Extracts MIME type and filename from `content-type` and `content-disposition` headers.

#### `convert_url()` — alias for `convert_uri()`

**Location**: `src/markitdown/_markitdown.py:386`

Kept for backward compatibility. Will likely be deprecated in the future.

### Converter Registration Methods

#### `register_converter(converter, *, priority=PRIORITY_SPECIFIC_FILE_FORMAT) → None`

**Location**: `src/markitdown/_markitdown.py:641`

Registers a `DocumentConverter` with the given priority. Lower priority values are tried first. Within the same priority, later registrations are tried first (due to `insert(0, ...)`).

```python
md = MarkItDown()
md.register_converter(MyCustomConverter(), priority=0.0)
```

#### `enable_builtins(**kwargs) → None`

**Location**: `src/markitdown/_markitdown.py:140`

Registers all built-in converters. Called automatically unless `enable_builtins=False` was passed to the constructor. Can only be called once.

#### `enable_plugins(**kwargs) → None`

**Location**: `src/markitdown/_markitdown.py:232`

Loads all installed plugins (via `entry_points(group="markitdown.plugin")`) and calls each plugin's `register_converters(self, **kwargs)`. Can only be called once.

### Priority Constants

```python
PRIORITY_SPECIFIC_FILE_FORMAT = 0.0   # Default; tried first
PRIORITY_GENERIC_FILE_FORMAT  = 10.0  # Catch-alls (PlainText, HTML, Zip); tried last
```

Plugins can use any float value. A plugin with priority `9.0` runs after built-in specific converters but before generic catch-alls.

---

## `DocumentConverterResult` Class

**Location**: `src/markitdown/_base_converter.py:5`

```python
class DocumentConverterResult:
    markdown: str           # The converted Markdown text
    title: Optional[str]    # Document title (if available)

    # Deprecated alias for markdown (kept for compatibility)
    @property
    def text_content(self) -> str: ...
    @text_content.setter
    def text_content(self, markdown: str): ...

    def __str__(self) -> str: ...  # Returns self.markdown
```

**Construction**:

```python
DocumentConverterResult(markdown="# Hello\n\nWorld", title="My Doc")
```

New code should use `.markdown` directly. The `.text_content` property is soft-deprecated.

---

## `DocumentConverter` Abstract Base Class

**Location**: `src/markitdown/_base_converter.py:42`

```python
class DocumentConverter:
    def accepts(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> bool:
        """Return True if this converter should attempt this document.
        MUST NOT change file_stream position (must reset if it reads)."""
        raise NotImplementedError(...)

    def convert(
        self,
        file_stream: BinaryIO,
        stream_info: StreamInfo,
        **kwargs: Any,
    ) -> DocumentConverterResult:
        """Convert the stream to Markdown.
        Raises MissingDependencyException, FileConversionException."""
        raise NotImplementedError(...)
```

Both methods receive the same `file_stream` (positioned at `cur_pos`) and `StreamInfo`. After `convert()` returns, `_convert()` seeks back to `cur_pos`.

---

## `StreamInfo` Dataclass

**Location**: `src/markitdown/_stream_info.py:5`

```python
@dataclass(kw_only=True, frozen=True)
class StreamInfo:
    mimetype:   Optional[str] = None   # e.g., "application/pdf"
    extension:  Optional[str] = None   # e.g., ".pdf" (with leading dot)
    charset:    Optional[str] = None   # e.g., "utf-8"
    filename:   Optional[str] = None   # e.g., "report.pdf"
    local_path: Optional[str] = None   # Absolute path if read from disk
    url:        Optional[str] = None   # URL if fetched from network

    def copy_and_update(self, *args: StreamInfo, **kwargs) -> StreamInfo:
        """Immutable update: returns a new StreamInfo merging current fields
        with fields from positional StreamInfo args and keyword overrides.
        Only non-None values overwrite existing fields."""
```

---

## Exception Hierarchy

**Location**: `src/markitdown/_exceptions.py`

```
MarkItDownException (base)
├── MissingDependencyException   # Required optional package not installed
├── UnsupportedFormatException   # No converter accepted the file
└── FileConversionException      # Converter accepted but failed
    └── .attempts: List[FailedConversionAttempt]
        └── .converter: DocumentConverter
        └── .exc_info: tuple (type, value, traceback)
```

### Usage in error handling

```python
from markitdown import MarkItDown, UnsupportedFormatException, MissingDependencyException

md = MarkItDown()
try:
    result = md.convert("unknown.bin")
except UnsupportedFormatException:
    print("File type not supported")
except MissingDependencyException as e:
    print(f"Install missing dependency: {e}")
```

---

## Plugin Interface

**Location**: `packages/markitdown-sample-plugin/src/markitdown_sample_plugin/_plugin.py`

A plugin is a Python package that:

1. Declares an entry-point in `pyproject.toml`:
   ```toml
   [project.entry-points."markitdown.plugin"]
   my_plugin = "my_plugin_package"
   ```

2. Exposes at the module level:
   ```python
   __plugin_interface_version__ = 1  # Required: current interface version

   def register_converters(markitdown: MarkItDown, **kwargs) -> None:
       """Called by MarkItDown.enable_plugins() to register converters."""
       markitdown.register_converter(MyConverter())
   ```

3. Implements one or more `DocumentConverter` subclasses.

### Complete Plugin Example

```python
from markitdown import MarkItDown, DocumentConverter, DocumentConverterResult, StreamInfo
from typing import BinaryIO, Any

__plugin_interface_version__ = 1

def register_converters(markitdown: MarkItDown, **kwargs):
    markitdown.register_converter(RtfConverter())

class RtfConverter(DocumentConverter):
    def accepts(self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs: Any) -> bool:
        extension = (stream_info.extension or "").lower()
        mimetype = (stream_info.mimetype or "").lower()
        return extension == ".rtf" or mimetype in ("text/rtf", "application/rtf")

    def convert(self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs: Any) -> DocumentConverterResult:
        import locale
        from striprtf.striprtf import rtf_to_text
        encoding = stream_info.charset or locale.getpreferredencoding()
        text = file_stream.read().decode(encoding)
        return DocumentConverterResult(markdown=rtf_to_text(text))
```

---

## MCP Server API

**Location**: `packages/markitdown-mcp/src/markitdown_mcp/__main__.py`

The MCP server exposes a single tool via `FastMCP`:

```python
@mcp.tool()
async def convert_to_markdown(uri: str) -> str:
    """Convert a resource described by an http:, https:, file: or data: URI to markdown"""
    return MarkItDown(enable_plugins=check_plugins_enabled()).convert_uri(uri).markdown
```

**Plugin enablement**: Set environment variable `MARKITDOWN_ENABLE_PLUGINS=true` (or `1`, `yes`) to enable plugins in the MCP server.

### Transport Options

```bash
# STDIO (default — for MCP clients like Claude Desktop)
markitdown-mcp

# HTTP + SSE transport
markitdown-mcp --http                           # Binds to 127.0.0.1:3001
markitdown-mcp --http --host 0.0.0.0 --port 8080  # Custom host/port (WARNING: no auth)

# Deprecated alias for --http
markitdown-mcp --sse
```

HTTP routes:
- `GET /sse` — SSE transport endpoint
- `POST /mcp` — Streamable HTTP transport
- `POST /messages/` — SSE message posting

---

## CLI Interface

**Location**: `src/markitdown/__main__.py`

```
markitdown [OPTIONS] [FILENAME]

  If FILENAME is omitted, reads from stdin.

Options:
  -v, --version            Show version and exit
  -o, --output FILE        Write Markdown to FILE (default: stdout)
  -x, --extension EXT      Hint about file extension (e.g., "pdf", ".pdf")
  -m, --mime-type MIME     Hint about MIME type (e.g., "application/pdf")
  -c, --charset CHARSET    Hint about charset (e.g., "UTF-8")
  -d, --use-docintel       Use Azure Document Intelligence
  -e, --endpoint URL       Azure Document Intelligence endpoint (required with -d)
  -p, --use-plugins        Enable installed 3rd-party plugins
  --list-plugins           List installed plugins and exit
  --keep-data-uris         Keep base64 data URIs in output (default: truncate)
```

**Examples**:

```bash
# Convert local file to stdout
markitdown report.pdf

# Convert with output file
markitdown report.pdf -o report.md

# Pipe input
cat report.pdf | markitdown

# Convert with type hint (stdin)
cat unknown_file | markitdown -x .pdf

# Use Azure Document Intelligence
markitdown report.pdf -d -e "https://my-instance.cognitiveservices.azure.com/"

# Enable plugins
markitdown document.rtf --use-plugins

# List installed plugins
markitdown --list-plugins
```

---

## Integration Patterns

### LLM-Powered Image Description

```python
from markitdown import MarkItDown
from openai import OpenAI

client = OpenAI()
md = MarkItDown(
    llm_client=client,
    llm_model="gpt-4o",
    llm_prompt="Describe this image in detail for accessibility purposes.",
)

# Images in PPTX slides and standalone image files
result = md.convert("presentation.pptx")
print(result.markdown)
```

### Azure Document Intelligence

```python
from markitdown import MarkItDown
from azure.core.credentials import AzureKeyCredential

md = MarkItDown(
    docintel_endpoint="https://my-instance.cognitiveservices.azure.com/",
    docintel_credential=AzureKeyCredential("my-api-key"),
    # Optionally restrict file types:
    # docintel_file_types=[DocumentIntelligenceFileType.PDF]
)
result = md.convert("contract.pdf")
```

### Converting from a URL

```python
from markitdown import MarkItDown, StreamInfo

md = MarkItDown()

# HTTP URL
result = md.convert("https://en.wikipedia.org/wiki/Python_(programming_language)")

# YouTube URL (with transcript if youtube-transcript-api is installed)
result = md.convert("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

# Provide a stream_info override (e.g., force a specific extension)
result = md.convert(
    "https://example.com/download",
    stream_info=StreamInfo(extension=".pdf")
)
```

### Custom `requests.Session`

```python
import requests
from markitdown import MarkItDown

session = requests.Session()
session.headers["Authorization"] = "Bearer my-token"
md = MarkItDown(requests_session=session)
result = md.convert("https://private-api.example.com/document.pdf")
```

### DOCX Style Map (mammoth)

```python
from markitdown import MarkItDown

# Custom mammoth style_map for heading translation
style_map = "p[style-name='Section Title'] => h1:fresh"
md = MarkItDown(style_map=style_map)
result = md.convert("document.docx")
```

### `keep_data_uris` Option

```python
from markitdown import MarkItDown

md = MarkItDown()

# By default, data: URIs are truncated in the output.
# To preserve them (e.g., for inline image embedding):
result = md.convert("presentation.pptx", keep_data_uris=True)
```

### Minimal Custom Converter (Extension Pattern)

```python
from markitdown import MarkItDown, DocumentConverter, DocumentConverterResult, StreamInfo
from typing import BinaryIO, Any

class CsvWithHeaderConverter(DocumentConverter):
    """Converts CSV, adding a custom 'Data Table' header."""

    def accepts(self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs: Any) -> bool:
        return (stream_info.extension or "").lower() == ".csv"

    def convert(self, file_stream: BinaryIO, stream_info: StreamInfo, **kwargs: Any) -> DocumentConverterResult:
        import csv, io
        text = file_stream.read().decode(stream_info.charset or "utf-8")
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            return DocumentConverterResult(markdown="")
        header = "| " + " | ".join(rows[0]) + " |"
        sep = "| " + " | ".join(["---"] * len(rows[0])) + " |"
        body = "\n".join("| " + " | ".join(row) + " |" for row in rows[1:])
        return DocumentConverterResult(
            markdown=f"## Data Table\n\n{header}\n{sep}\n{body}"
        )

md = MarkItDown(enable_builtins=False)   # Skip built-ins for demo
md.register_converter(CsvWithHeaderConverter())
result = md.convert("data.csv")
```

---

## Configuration Options Summary

| Parameter | Where | Description |
|---|---|---|
| `enable_builtins` | `MarkItDown()` | Enable built-in converters (default: `True`) |
| `enable_plugins` | `MarkItDown()` | Enable installed plugins (default: `False`) |
| `llm_client` | `MarkItDown()` or `convert()` | OpenAI-compatible client for image captioning |
| `llm_model` | `MarkItDown()` or `convert()` | LLM model name |
| `llm_prompt` | `MarkItDown()` or `convert()` | Custom captioning prompt |
| `exiftool_path` | `MarkItDown()` or `EXIFTOOL_PATH` env | Explicit path to ExifTool binary |
| `style_map` | `MarkItDown()` or `convert()` | mammoth DOCX style map |
| `docintel_endpoint` | `MarkItDown()` | Azure Document Intelligence endpoint URL |
| `docintel_credential` | `MarkItDown()` | Azure credential (default: `DefaultAzureCredential`) |
| `docintel_file_types` | `MarkItDown()` | List of `DocumentIntelligenceFileType` to use with AzureDocIntel |
| `requests_session` | `MarkItDown()` | Custom `requests.Session` for HTTP requests |
| `keep_data_uris` | `convert()` kwargs | Preserve base64 data URIs in HTML/PPTX output |
| `youtube_transcript_languages` | `convert()` kwargs | Language preference list for YouTube transcripts |
| `MARKITDOWN_ENABLE_PLUGINS` | env var (MCP server) | Enable plugins in the MCP server process |
