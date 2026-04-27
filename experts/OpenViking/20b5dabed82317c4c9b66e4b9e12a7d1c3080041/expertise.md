### Core Architecture
- OpenViking's "filesystem paradigm" for AI context management
- The three-tier L0/L1/L2 content model: abstract (<200 tokens), overview (<1000 tokens), full content
- VikingFS — URI-based virtual filesystem with `viking://` scheme
- URI namespaces: `viking://resources/`, `viking://memories/`, `viking://agent/`, `viking://session/`
- AGFS (Agent Filesystem) Go submodule and its role as the storage backbone
- Async semantic processing pipeline: parse → tree build → semantic queue → LLM L0/L1 generation → embedding
- Observer/queue architecture: `SemanticQueue` and `EmbeddingQueue`
- Transaction management and path-level locking for concurrent operations
- Multi-backend storage: local VectorDB vs. Volcengine VikingDB cloud

### Python API (`openviking` package)
- `SyncOpenViking` — synchronous embedded client
- `AsyncOpenViking` — async embedded client
- `SyncHTTPClient` / `AsyncHTTPClient` — remote server clients
- `Session` domain model and session lifecycle
- `client.initialize()` / `client.close()` / context manager usage
- Resource management: `add_resource()`, `rm()`, `mv()`, `export()`, `import_pack()`
- Content access: `read()`, `abstract()`, `overview()`
- Filesystem operations: `ls()`, `tree()`, `mkdir()`, `stat()`
- Search: `find()` (semantic), `grep()` (regex), `glob()` (patterns), `search()` (context-aware)
- Session API: `create_session()`, `add_message()`, `commit_session()`, `list_sessions()`
- `wait_processed()` — blocking wait for background indexing
- Public exports from `openviking/__init__.py`
- Protocol-based client interface (`openviking/client/protocol.py`)

### Configuration (`ov.conf`)
- JSON config file at `~/.openviking/ov.conf`
- Server settings: host, port, api_key, CORS
- Storage settings: workspace path, VectorDB backend (local/Volcengine), AGFS backend
- Embedding settings: provider, model, api_key, base_url for dense embeddings
- VLM settings: provider, model for vision-language tasks and media processing
- Reranking: enable/disable, model configuration
- Parser settings: PDF strategy (local/VLM), code languages, max file sizes
- Retrieval settings: top_k, rerank_top_k, threshold
- Semantic settings: concurrent LLM calls, max tokens per level
- Logging: level, file path, rotation policy
- Environment variable overrides: `OV_WORKSPACE`, `OV_PORT`, `OV_API_KEY`

### Document Parsers (`openviking/parse/`)
- `MarkdownParser` — single-pass chapter splitting, optional merging
- `PDFParser` — pdfplumber → markdown → MarkdownParser pipeline
- `HTMLParser` — readabilipy extraction → markdownify → MarkdownParser
- `TextParser` — plain text, JSON, YAML, XML
- `CodeRepositoryParser` — AST-based with tree-sitter for 8 languages (Python, JS, TS, Java, Go, C++, Rust, C#)
- `OfficeParser` — DOCX, PPTX, XLSX via python-docx/pptx/openpyxl
- `EPUBParser` — ebooklib-based EPUB handling
- `MediaParser` — VLM-based image/video/audio analysis
- Parser registry: extension → parser class mapping (`openviking/parse/registry.py`)
- `BaseParser` protocol for custom parser implementation
- `ParseResult` structure returned by all parsers
- `TreeBuilder` — moves parsed output into VikingFS hierarchy

### Search and Retrieval (`openviking/retrieve/`)
- Semantic vector search with configurable similarity threshold
- Regex-based grep across VikingFS content
- Glob pattern matching for file path discovery
- Context-aware search using session history
- Reranker integration for improved result quality
- `ContextBuilder` — assembles `ContextPart` objects from search results
- Multi-level search: can search L0 index for fast lookup, drill into L2 for details

### Session and Memory (`openviking/session/`)
- `Session` model with role-based message history
- Message parts: `TextPart`, `ContextPart`, `ToolPart`
- Automatic session compression using LLM summarization
- Long-term memory extraction via `MemoryExtractor` LLM pipeline
- Memory storage at `viking://memories/` namespace
- Session commit: archive conversation + extract persistent memories
- Multi-tenant session isolation

### REST API Server (`openviking/server/`)
- FastAPI app factory in `openviking/server/app.py`
- Dependency injection via `openviking/server/deps.py`
- Router groups: filesystem, content, resources, search, sessions, relations, pack, system, observer, admin, debug, bot
- Authentication via API key header
- OpenAPI docs at `/docs`
- Health check endpoint

### Rust CLI (`crates/ov_cli/`)
- `ov` command compiled from Rust using clap for argument parsing
- Commands: add-resource, export, import, ls, tree, read, abstract, overview, mkdir, rm, mv, find, grep, glob, session (new/list/add-message/commit/delete), system (status/wait)
- Progress bars via `indicatif` for long-running operations
- Output formats: JSON (`--output json`) and table (`--output table`)
- `openviking_cli/` Python package wraps the Rust binary

### Build System
- Multi-language polyglot build: Go 1.22+ (AGFS), Rust 1.88+ (CLI), C++ with CMake (extensions), Python 3.10+
- `setup.py` orchestrates all build steps as custom `build_ext`
- `pyproject.toml` for PEP 517/518 compliant packaging
- `Makefile` for `make deps`, `make build`, `make test`, `make docker-build`
- Multi-stage `Dockerfile` handling all language toolchains
- `Cargo.toml` workspace root for Rust crates
- AGFS as git submodule in `third_party/agfs/`

### Vikingbot (`bot/vikingbot/`)
- 7 built-in agent tools backed by OpenViking context database
- Tool list: add_resource, find, grep, glob, read_content (L0/L1/L2), list_fs, search_memories
- Multi-channel support: Telegram, Feishu/Lark, DingTalk, Slack, QQ, WebSocket
- Web console UI via Gradio at port 18791
- Built on Nanobot framework
- Optional Langfuse observability tracing
- Optional sandbox execution and FUSE filesystem mounting
- Deployment: Docker Compose, Kubernetes (VKE), Volcengine ECS

### Storage Backends
- Local VectorDB: in-process vector storage (no external dependencies)
- Volcengine VikingDB: cloud vector database backend
- AGFS local backend: local filesystem-based agent filesystem
- AGFS S3 backend: S3-compatible object storage
- C++ extensions for performance-critical storage operations

### Embedding and LLM Integration
- litellm unified interface for OpenAI, Volcengine/Doubao, Anthropic, and other providers
- Dense embedding with `doubao-embedding-vision-250615` (Volcengine default)
- VLM for media processing: `doubao-seed-2-0-pro-260215` (Volcengine default)
- Optional reranking models
- Configurable concurrent LLM calls for semantic processing
- Retry logic in `openviking/utils/llm.py`

### Evaluation (`openviking/eval/`)
- RAGAS-based evaluation framework for LLM pipelines
- LoCoPo evaluation in `bot/eval/`
- Benchmark datasets and retrieval quality metrics

### Deployment and Operations
- Embedded mode: direct Python library usage
- Server mode: standalone HTTP server on port 1933 (default)
- Docker: `docker build -t openviking:latest .`
- Kubernetes: Helm charts in `bot/deploy/vke/`
- Queue monitoring via `/api/v1/observer/stats`
- Admin operations: reindex, rebuild, cleanup via `/api/v1/admin/`
- Transaction replay and recovery
