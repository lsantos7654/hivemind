# OpenViking APIs and Interfaces

## Public Python API

The main package exports from `openviking/__init__.py`:

```python
from openviking import (
    SyncOpenViking,       # Synchronous client (recommended for scripts)
    AsyncOpenViking,      # Async client (for async applications)
    Session,              # Session domain model
    SyncHTTPClient,       # HTTP client for connecting to remote server
    AsyncHTTPClient,      # Async HTTP client for remote server
)
```

### SyncOpenViking (Primary Embedded Client)

The synchronous wrapper over `AsyncOpenViking`. Use this for scripts, notebooks, and non-async applications.

```python
import openviking as ov

# Create client in embedded mode (spins up local server)
client = ov.SyncOpenViking(
    path="./data",              # Workspace directory
    config_path="~/.openviking/ov.conf",  # Optional config file
)
client.initialize()             # Start embedded service

# Always close when done
client.close()

# Or use as context manager
with ov.SyncOpenViking(path="./data") as client:
    ...
```

### Resource Management

```python
# Add a resource (local path or URL)
result = client.add_resource(
    path="https://docs.example.com",  # or local path
    wait=True,                         # Block until processed
    timeout=300,                       # Seconds to wait
)
root_uri = result["root_uri"]         # e.g., "viking://resources/docs.example.com"

# Add local directory
result = client.add_resource(path="./my-docs", wait=True)

# Delete a resource
client.rm(uri="viking://resources/my-docs")

# Export resource as .ovpack file
client.export(uri="viking://resources/my-docs", output_path="./my-docs.ovpack")

# Import from .ovpack file
client.import_pack(path="./my-docs.ovpack")

# Wait for all background processing to complete
client.wait_processed(timeout=300)
```

### Filesystem Operations (VikingFS)

All context is organized in a virtual filesystem with `viking://` URIs:

```python
# List directory contents
entries = client.ls(uri="viking://resources")
# Returns: list of {uri, name, type, size, ...}

# Recursive listing
entries = client.ls(uri="viking://resources/my-docs", recursive=True)

# Get tree structure
tree = client.tree(uri="viking://resources/my-docs")
# Returns: nested tree of directories and files

# Create directory
client.mkdir(uri="viking://resources/custom-namespace")

# Move/rename
client.mv(src="viking://resources/old-name", dst="viking://resources/new-name")

# Remove (recursive)
client.rm(uri="viking://resources/my-docs")

# Get file metadata
stat = client.stat(uri="viking://resources/my-docs/readme.md")
```

### Three-Level Content Access

Every resource in VikingFS has three content levels:

```python
uri = "viking://resources/my-docs/chapter1.md"

# L0: Compact abstract (<200 tokens) — fast semantic search & navigation
abstract = client.abstract(uri)
print(abstract)  # e.g., "This chapter covers authentication patterns..."

# L1: Navigational overview (<1000 tokens) — decision context
overview = client.overview(uri)
print(overview)  # Structured summary with section headings

# L2: Full content — detailed reading
content = client.read(uri)
print(content)   # Complete document content
```

### Search and Retrieval

```python
# Semantic (vector) search
results = client.find(
    query="authentication best practices",
    target_uri="viking://resources",   # Scope the search
    threshold=0.7,                      # Minimum similarity score
    limit=10,                           # Max results
)
for r in results.resources:
    print(f"{r.uri}: {r.score:.4f}")
    print(f"  Abstract: {r.abstract}")

# Context-aware search (uses session history for better results)
results = client.search(
    query="how does the login flow work?",
    session_id="my-session",
)

# Regex search
matches = client.grep(
    pattern=r"def authenticate\(",
    uri="viking://resources/my-codebase",
)

# Glob pattern search
paths = client.glob(
    pattern="**/*.py",
    uri="viking://resources/my-codebase",
)
```

### Session Management

Sessions track conversations and automatically extract long-term memories.

```python
# Create a session
session = client.create_session(session_id="user-123-session-1")

# Or get existing session
session = client.get_session(session_id="user-123-session-1")

# Add messages (role: "user" | "assistant" | "system" | "tool")
client.add_message(
    session_id="user-123-session-1",
    role="user",
    content="What are the main features of OpenViking?",
)
client.add_message(
    session_id="user-123-session-1",
    role="assistant",
    content="OpenViking provides three-tier context management...",
)

# Commit session: archives conversation + extracts long-term memories
# Extracted memories are written to viking://memories/
client.commit_session(session_id="user-123-session-1")

# List sessions
sessions = client.list_sessions()

# Delete session
client.delete_session(session_id="user-123-session-1")
```

### Memory Access

Long-term memories extracted from sessions are stored at `viking://memories/`:

```python
# Search memories
results = client.find(
    query="user preferences about dark mode",
    target_uri="viking://memories",
)

# List all memories
entries = client.ls(uri="viking://memories")

# Read a specific memory
content = client.read(uri="viking://memories/user-preferences.md")
```

## Async Client (AsyncOpenViking)

For use in async applications (same API, all methods are `async`):

```python
import asyncio
import openviking as ov

async def main():
    client = ov.AsyncOpenViking(path="./data")
    await client.initialize()

    result = await client.add_resource("https://example.com", wait=True)
    results = await client.find("example query")

    await client.close()

asyncio.run(main())
```

## HTTP Client (Remote Server Mode)

Connect to a running OpenViking server instead of embedded mode:

```python
import openviking as ov

client = ov.SyncHTTPClient(
    base_url="http://localhost:1933",
    api_key="your-api-key",         # From server config
)

# Same API as SyncOpenViking
result = client.add_resource("./docs", wait=True)
results = client.find("query")
```

## REST API (FastAPI Server)

When running as a server (`openviking-server`), the REST API is available at `http://localhost:1933`.

### Filesystem Endpoints

```
GET  /api/v1/fs/ls?uri={uri}&recursive={bool}
GET  /api/v1/fs/tree?uri={uri}
GET  /api/v1/fs/stat?uri={uri}
POST /api/v1/fs/mkdir          Body: {"uri": "..."}
POST /api/v1/fs/rm             Body: {"uri": "..."}
POST /api/v1/fs/mv             Body: {"src": "...", "dst": "..."}
```

### Content Endpoints

```
GET  /api/v1/content/read?uri={uri}
GET  /api/v1/content/abstract?uri={uri}
GET  /api/v1/content/overview?uri={uri}
```

### Resource Endpoints

```
POST /api/v1/resources/add     Body: {"path": "...", "wait": true}
DELETE /api/v1/resources/delete Body: {"uri": "..."}
GET  /api/v1/resources/status?uri={uri}
POST /api/v1/resources/export  Body: {"uri": "...", "output_path": "..."}
POST /api/v1/resources/import  Body: {"path": "..."}
```

### Search Endpoints

```
POST /api/v1/search/find       Body: {"query": "...", "target_uri": "...", "threshold": 0.7, "limit": 10}
POST /api/v1/search/grep       Body: {"pattern": "...", "uri": "..."}
POST /api/v1/search/glob       Body: {"pattern": "...", "uri": "..."}
```

### Session Endpoints

```
POST /api/v1/sessions/create   Body: {"session_id": "..."}
GET  /api/v1/sessions/list
GET  /api/v1/sessions/get?session_id={id}
POST /api/v1/sessions/add-message  Body: {"session_id": "...", "role": "...", "content": "..."}
POST /api/v1/sessions/commit   Body: {"session_id": "..."}
DELETE /api/v1/sessions/delete Body: {"session_id": "..."}
```

### System Endpoints

```
GET  /api/v1/system/status
GET  /api/v1/system/health
POST /api/v1/system/wait       Body: {"timeout": 300}
GET  /api/v1/observer/stats
```

## Rust CLI Interface

The `ov` CLI (compiled Rust binary) mirrors the Python API:

```bash
# Resource management
ov add-resource <PATH> [--wait] [--timeout 300]
ov export <URI> --output <FILE>
ov import <FILE>

# Filesystem navigation
ov ls <URI> [--recursive]
ov tree <URI>
ov stat <URI>
ov mkdir <URI>
ov rm <URI>
ov mv <SRC> <DST>

# Content access
ov read <URI>
ov abstract <URI>
ov overview <URI>

# Search
ov find <QUERY> [--target <URI>] [--threshold 0.7] [--limit 10]
ov grep <PATTERN> <URI>
ov glob <PATTERN> [--uri <URI>]

# Sessions
ov session new [--session-id <ID>]
ov session list
ov session add-message --session-id <ID> --role <ROLE> --content <TEXT>
ov session commit --session-id <ID>
ov session delete --session-id <ID>

# System
ov system status
ov system wait [--timeout 300]

# Output format
ov find "query" --output json    # JSON output for scripting
ov ls viking://resources --output table  # Table output
```

## Document Parser Extension Points

Custom parsers can be registered via the parser registry:

```python
from openviking.parse.base import BaseParser, ParseResult
from openviking.parse.registry import register_parser

class MyCustomParser(BaseParser):
    @property
    def supported_extensions(self) -> list[str]:
        return [".myext"]

    async def parse(self, path: str, **kwargs) -> ParseResult:
        # Return structured ParseResult with file tree
        ...

register_parser(MyCustomParser())
```

## Configuration Extension Points

Key configuration sections in `ov.conf`:

```json
{
  "parsers": {
    "pdf": {
      "strategy": "local"   // "local" or "vlm"
    },
    "code": {
      "max_file_size_kb": 500,
      "languages": ["python", "typescript", "java"]
    }
  },
  "retrieval": {
    "top_k": 20,
    "rerank_top_k": 5,
    "enable_rerank": false
  },
  "semantic": {
    "concurrent_llm_calls": 5,
    "abstract_max_tokens": 200,
    "overview_max_tokens": 1000
  }
}
```

## URI Scheme Reference

All context is addressed using `viking://` URIs:

| URI Pattern | Description |
|-------------|-------------|
| `viking://resources/` | Root of all imported resources |
| `viking://resources/{name}/` | A specific imported resource |
| `viking://memories/` | Long-term memories extracted from sessions |
| `viking://agent/{space}/skills/{name}` | Agent skill definitions |
| `viking://session/{user}/{session_id}/` | Session-scoped context |

Each URI can be appended with:
- No suffix — the node itself (directory listing or file content)
- `/.abstract.md` — L0 abstract file
- `/.overview.md` — L1 overview file
- `/content.md` or original extension — L2 full content (leaf nodes)

## Vikingbot Tool Interface

The 7 built-in tools available to Vikingbot agents:

```python
# Tool 1: Add resource
add_resource(path: str) -> str  # URI of created resource

# Tool 2: Semantic search
find(query: str, target_uri: str = "viking://resources", threshold: float = 0.7) -> list[ContextResult]

# Tool 3: Regex search
grep(pattern: str, uri: str) -> list[GrepMatch]

# Tool 4: Glob search
glob(pattern: str, uri: str = "viking://resources") -> list[str]

# Tool 5: Read content at specified level
read_content(uri: str, level: str = "L2") -> str  # level: "L0", "L1", "L2"

# Tool 6: List filesystem
list_fs(uri: str, recursive: bool = False) -> list[FSEntry]

# Tool 7: Search memories
search_memories(query: str) -> list[ContextResult]
```
