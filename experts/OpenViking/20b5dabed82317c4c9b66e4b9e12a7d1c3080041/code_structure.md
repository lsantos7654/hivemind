# OpenViking Code Structure

## Annotated Directory Tree

```
/repo
├── openviking/                    # Core Python library (primary package)
│   ├── __init__.py               # Public exports: SyncOpenViking, AsyncOpenViking, Session, clients
│   ├── sync_client.py            # SyncOpenViking: synchronous wrapper over AsyncOpenViking
│   ├── async_client.py           # AsyncOpenViking: core async API (embedded mode)
│   ├── client/                   # Client implementations
│   │   ├── local.py             # LocalClient: embedded in-process service
│   │   ├── http_client.py       # SyncHTTPClient / AsyncHTTPClient for server mode
│   │   └── protocol.py          # Client protocol (interface definition)
│   ├── core/                     # Domain model
│   │   ├── context.py           # Context: central domain object (URI, levels, metadata)
│   │   ├── directories.py       # VikingFS directory constants and URI builders
│   │   ├── enums.py             # Status enums, content level enums
│   │   └── exceptions.py        # Custom exception hierarchy
│   ├── message/                  # Message and content parts
│   │   ├── message.py           # Message: role + list of Parts
│   │   ├── part.py              # TextPart, ContextPart, ToolPart definitions
│   │   └── compression.py       # LLM-based message compression logic
│   ├── models/                   # Embedding model adapters
│   │   ├── base.py              # BaseEmbedder protocol
│   │   ├── openai_embedder.py   # OpenAI embeddings
│   │   ├── volcengine_embedder.py# Volcengine/Doubao embeddings
│   │   └── vikingdb_embedder.py # VikingDB-native embeddings
│   ├── parse/                    # Document parsing subsystem
│   │   ├── base.py              # BaseParser protocol and ParseResult
│   │   ├── registry.py          # Parser registry: extension → parser mapping
│   │   ├── parsers/
│   │   │   ├── markdown.py      # MarkdownParser: chapter splitting + merging
│   │   │   ├── pdf.py           # PDFParser: pdfplumber → markdown → MarkdownParser
│   │   │   ├── html.py          # HTMLParser: readabilipy → markdown → MarkdownParser
│   │   │   ├── text.py          # TextParser: plain text, JSON, YAML, XML
│   │   │   ├── code_repo.py     # CodeRepositoryParser: AST-based, 8 languages
│   │   │   ├── office.py        # DOCX/PPTX/XLSX parsers
│   │   │   ├── epub.py          # EPUB parser
│   │   │   └── media.py         # MediaParser: VLM-based image/video/audio
│   │   └── tree_builder.py      # TreeBuilder: moves parsed output into VikingFS
│   ├── prompts/                  # LLM prompt templates
│   │   ├── abstract.py          # L0 abstract generation prompt
│   │   ├── overview.py          # L1 overview generation prompt
│   │   ├── memory.py            # Memory extraction prompt
│   │   └── compression.py       # Session compression prompt
│   ├── pyagfs/                   # Python bindings for AGFS (Go filesystem)
│   │   ├── __init__.py          # Exports AGFSClient
│   │   └── client.py            # AGFS gRPC/IPC client wrapper
│   ├── retrieve/                 # Retrieval and search
│   │   ├── retriever.py         # Main retriever: semantic, text, hybrid
│   │   ├── reranker.py          # Optional reranking step
│   │   └── context_builder.py   # Builds ContextPart from search results
│   ├── server/                   # FastAPI HTTP server
│   │   ├── app.py               # FastAPI app factory, middleware, lifespan
│   │   ├── deps.py              # Dependency injection (get_service, auth)
│   │   └── routers/
│   │       ├── filesystem.py    # ls, mkdir, rm, mv, stat endpoints
│   │       ├── content.py       # read, abstract, overview endpoints
│   │       ├── resources.py     # add_resource, delete, query endpoints
│   │       ├── search.py        # find (semantic), grep, glob endpoints
│   │       ├── sessions.py      # session CRUD, add_message, commit
│   │       ├── relations.py     # Context relation/link management
│   │       ├── pack.py          # .ovpack import/export
│   │       ├── system.py        # status, health, wait endpoints
│   │       ├── observer.py      # Queue stats and observer management
│   │       ├── admin.py         # Admin: reindex, rebuild, cleanup
│   │       ├── debug.py         # Debug utilities
│   │       └── bot.py           # Vikingbot webhook/config endpoints
│   ├── service/                  # Core business logic
│   │   ├── service.py           # OpenVikingService: orchestrates all subsystems
│   │   ├── resource_service.py  # Resource lifecycle: add, delete, status
│   │   ├── search_service.py    # Search orchestration: semantic + text
│   │   ├── session_service.py   # Session management and memory extraction
│   │   └── observer_service.py  # Async queue coordination
│   ├── session/                  # Session domain
│   │   ├── session.py           # Session model with message history
│   │   └── memory_extractor.py  # LLM-based long-term memory extraction
│   ├── storage/                  # Storage layer
│   │   ├── vectordb/
│   │   │   ├── base.py          # VectorDB protocol
│   │   │   ├── local.py         # In-process local vector store
│   │   │   └── vikingdb.py      # Volcengine VikingDB cloud backend
│   │   ├── filesystem.py        # VikingFS wrapper (calls pyagfs)
│   │   ├── transaction.py       # Transaction manager: path locking, ACID ops
│   │   └── observer/
│   │       ├── semantic_queue.py# Async queue for L0/L1 generation
│   │       └── embedding_queue.py# Async queue for vector index building
│   ├── eval/                     # Evaluation framework
│   │   ├── datasets/            # Benchmark datasets
│   │   └── metrics/             # RAGAS-based metrics
│   ├── console/                  # Web UI for Vikingbot configuration
│   │   └── app.py               # Gradio-based console interface
│   └── utils/                    # Shared utilities
│       ├── hash.py              # xxhash-based content hashing
│       ├── uri.py               # URI parsing and construction helpers
│       ├── llm.py               # litellm wrapper with retry logic
│       └── config.py            # Config loading from ov.conf
├── openviking_cli/               # Python CLI wrapper
│   ├── __init__.py
│   └── main.py                  # Entry point: launches compiled Rust CLI binary
├── crates/                       # Rust workspace
│   └── ov_cli/
│       ├── Cargo.toml           # Rust crate manifest
│       └── src/
│           ├── main.rs          # CLI entry: clap-based command routing (1059 lines)
│           ├── commands/
│           │   ├── resource.rs  # add-resource, export, import
│           │   ├── fs.rs        # ls, tree, read, abstract, overview, mkdir, rm, mv
│           │   ├── search.rs    # find, grep, glob
│           │   ├── session.rs   # session new/list/add-message/commit
│           │   └── system.rs    # status, wait
│           └── tui/
│               ├── mod.rs       # TUI module entry
│               └── progress.rs  # Progress bars for long-running ops
├── bot/                          # Vikingbot: multi-channel AI agent
│   ├── vikingbot/
│   │   ├── __init__.py
│   │   ├── agent.py             # Core bot agent logic, 7 tools defined
│   │   ├── tools/               # OpenViking-backed tool implementations
│   │   │   ├── resource.py      # add_resource tool
│   │   │   ├── search.py        # find, grep, glob tools
│   │   │   └── memory.py        # memory search tool
│   │   ├── channels/            # Chat platform integrations
│   │   │   ├── telegram.py      # Telegram bot
│   │   │   ├── feishu.py        # Feishu/Lark bot
│   │   │   ├── dingtalk.py      # DingTalk bot
│   │   │   ├── slack.py         # Slack bot
│   │   │   └── qq.py            # QQ bot
│   │   └── config.py            # Bot configuration
│   ├── bridge/                   # WebSocket/WhatsApp bridge
│   ├── deploy/                   # Deployment configs
│   │   ├── docker/              # Docker compose files
│   │   ├── ecs/                 # Volcengine ECS scripts
│   │   └── vke/                 # Kubernetes (VKE) Helm charts
│   └── eval/                    # LoCoPo LLM evaluation framework
├── src/                          # C++ performance extensions
│   ├── store/                   # Custom storage backend
│   ├── index/                   # Indexing utilities
│   └── common/                  # Shared C++ utilities
├── third_party/
│   └── agfs/                    # AGFS git submodule (Go Agent Filesystem)
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests per module
│   ├── integration/             # End-to-end tests
│   ├── parse/                   # Parser correctness tests
│   ├── vectordb/                # Vector store tests
│   └── cli/                     # CLI command tests
├── examples/                     # Usage examples
│   ├── quick_start.py           # Basic Python API demo
│   ├── memory_demo.py           # Session memory workflow
│   ├── multi_tenant/            # Multi-tenant setup example
│   ├── openclaw-memory-plugin/  # OpenClaw integration example
│   └── skills/                  # Custom skill definitions
├── docs/
│   ├── en/                      # English documentation
│   └── zh/                      # Chinese documentation
├── setup.py                      # Multi-language build orchestration
├── pyproject.toml               # PEP 517/518 project metadata
├── Cargo.toml                   # Rust workspace root
├── Makefile                     # Build automation targets
├── Dockerfile                   # Multi-stage build (Go + Rust + Python)
├── README.md                    # English README
└── README_CN.md                 # Chinese README
```

## Module and Package Organization

The codebase is organized into 5 distinct layers with clear separation of concerns:

### 1. Domain Layer (`openviking/core/`, `openviking/message/`, `openviking/session/`)
Core domain objects that all other layers depend on. The `Context` class is the central entity — it carries a URI, content levels (L0/L1/L2), metadata, and status. `Message` and its `Part` subtypes define the session conversation model.

### 2. Infrastructure Layer (`openviking/storage/`, `openviking/models/`, `openviking/pyagfs/`)
Storage abstractions — VectorDB backends, the VikingFS wrapper, transaction management, and model adapters. The transaction manager provides path-level locking for safe concurrent modification.

### 3. Processing Layer (`openviking/parse/`, `openviking/retrieve/`, `openviking/prompts/`)
Document ingestion (parsers), semantic processing (prompt templates + LLM calls for L0/L1), and retrieval logic (semantic search + reranking). The `SemanticQueue` and `EmbeddingQueue` in `openviking/storage/observer/` bridge parsing to indexing asynchronously.

### 4. Service Layer (`openviking/service/`)
`OpenVikingService` is the god object that wires together all infrastructure and processing components. Individual sub-services handle specific domains: resources, search, sessions, and observer coordination.

### 5. Interface Layer (`openviking/server/`, `openviking_cli/`, `crates/ov_cli/`)
Three interfaces expose the service: embedded Python API (`SyncOpenViking`/`AsyncOpenViking`), HTTP REST API (FastAPI), and CLI (Python wrapper launching compiled Rust binary).

## Code Organization Patterns

- **Protocol-based interfaces**: Storage backends, embedders, and parsers use Python `Protocol` classes for interface contracts without inheritance
- **Async-first design**: Core service is async; `SyncOpenViking` wraps it with `asyncio.run()`
- **Registry pattern**: `parse/registry.py` maps file extensions to parser classes
- **Dependency injection**: FastAPI server uses `deps.py` to inject `OpenVikingService` into route handlers
- **Observer/queue pattern**: Semantic and embedding processing uses async queues decoupled from the synchronous parse/import path
- **URI-based addressing**: All resources, memories, and sessions are addressed via `viking://` URIs — parseable by `openviking/utils/uri.py`
- **Configuration-driven**: All backends, models, and server settings are driven by `ov.conf` (JSON), loaded at startup

## Key Files and Their Roles

| File | Role |
|------|------|
| `openviking/__init__.py` | Public API surface — everything a user imports |
| `openviking/service/service.py` | Central orchestrator — the system's backbone |
| `openviking/core/context.py` | Central domain entity — the "file" in the filesystem |
| `openviking/storage/observer/semantic_queue.py` | Async L0/L1 generation — key to scalable ingestion |
| `openviking/parse/parsers/code_repo.py` | Most complex parser — AST extraction for 8 languages |
| `openviking/server/app.py` | FastAPI app setup and all router registration |
| `crates/ov_cli/src/main.rs` | Rust CLI — 1059 lines of clap-based command handling |
| `setup.py` | Orchestrates Go/Rust/C++/Python multi-language build |
| `bot/vikingbot/agent.py` | 7 agent tools backed by OpenViking context database |
