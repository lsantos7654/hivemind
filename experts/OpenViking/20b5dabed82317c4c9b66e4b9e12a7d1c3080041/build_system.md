# OpenViking Build System

## Build System Type and Overview

OpenViking uses a **multi-language polyglot build system** that must compile and bundle four distinct language runtimes into a single Python package:

1. **AGFS Server** — Go 1.22+ (Agent Filesystem backend)
2. **Rust CLI** — Rust 1.88+ (the `ov` command-line tool)
3. **C++ Extensions** — GCC 9+ or Clang 11+ (performance-critical storage)
4. **Python Package** — Python 3.10+ (the main `openviking` library)

The orchestration layer is `setup.py` (using setuptools with custom `build_ext` commands), assisted by a `Makefile` for dependency checking and convenience targets.

## Configuration Files

| File | Purpose |
|------|---------|
| `setup.py` | Custom `build_ext` steps: calls Go build, cargo build, cmake, then copies artifacts |
| `pyproject.toml` | PEP 517/518 metadata: project name, version, dependencies, entry points |
| `Cargo.toml` | Rust workspace root for `crates/ov_cli` |
| `crates/ov_cli/Cargo.toml` | Rust crate manifest with CLI dependencies (clap, tokio, serde, etc.) |
| `Makefile` | Convenience targets: `deps`, `build`, `test`, `clean`, `docker-build` |
| `Dockerfile` | Multi-stage Docker build (Go builder → Rust builder → Python final image) |
| `CMakeLists.txt` | CMake config for C++ extensions in `src/` |

## External Dependencies

### Python Dependencies (from `pyproject.toml`)

**Core runtime:**
- `pydantic>=2.0` — Data validation and serialization
- `fastapi>=0.128.0` — REST API framework
- `uvicorn` — ASGI server
- `httpx` — Async HTTP client
- `litellm>=1.0.0` — Unified LLM interface (OpenAI, Anthropic, Volcengine, etc.)
- `openai>=1.0.0` — OpenAI API client
- `volcengine-python-sdk[ark]` — Volcengine/ByteDance model SDK
- `xxhash` — Fast content hashing
- `apscheduler` — Task scheduling for observer queues

**Document parsing:**
- `pdfplumber` — PDF text extraction
- `readabilipy` — HTML readability extraction
- `markdownify` — HTML-to-Markdown conversion
- `tree-sitter` + language grammars — AST-based code parsing (Python, JS, TS, Java, C++, Rust, Go, C#)
- `python-docx`, `python-pptx`, `openpyxl` — Office document formats
- `ebooklib` — EPUB parsing
- `pdfminer-six` — Advanced PDF mining

**Storage/embedding:**
- `numpy` — Vector operations
- VikingDB SDK (bundled or installed separately for cloud backend)

**Bot/channels:**
- `python-telegram-bot` — Telegram integration
- `lark-oapi` — Feishu/Lark integration
- `dingtalk-stream` — DingTalk integration
- `slack-sdk` — Slack integration
- `qq-botpy` — QQ bot integration
- `websockets` — WebSocket bridge
- `python-socketio` — Socket.IO support
- `gradio` — Web console UI

**Development/evaluation:**
- `pytest`, `pytest-asyncio` — Test framework
- `mypy` — Type checking
- `ruff` — Linting and formatting
- `ragas` — LLM pipeline evaluation
- `langfuse` — Optional observability tracing

### Rust Dependencies (from `crates/ov_cli/Cargo.toml`)
- `clap` — Command-line argument parsing
- `tokio` — Async runtime
- `serde`, `serde_json` — Serialization
- `reqwest` — HTTP client for API calls
- `indicatif` — Progress bars for TUI

### Go Dependencies (AGFS submodule)
- Standard library + filesystem/gRPC packages (managed by Go modules in `third_party/agfs/`)

### System Requirements
- Go 1.22+
- Rust 1.88+ (via rustup)
- GCC 9+ or Clang 11+ (for C++ extensions)
- CMake 3.14+
- Python 3.10+

## Build Targets and Commands

### Local Development Build

```bash
# Check all build dependencies are present
make deps

# Full build (Go + Rust + C++ + Python package)
make build

# Or directly with pip (triggers setup.py)
pip install -e .

# Build only the Rust CLI
cd crates/ov_cli && cargo build --release

# Build only the AGFS Go server
cd third_party/agfs && go build ./...

# Build only C++ extensions
mkdir build && cd build && cmake .. && make
```

### Python Package Install

```bash
# Development install (editable)
pip install -e ".[dev]"

# Production install with all optional extras
pip install -e ".[bot,eval,office]"

# Install from PyPI (when published)
pip install openviking
```

### Testing

```bash
# Run all tests
make test
# or
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests (requires running server)
pytest tests/integration/

# Parser tests
pytest tests/parse/

# VectorDB tests
pytest tests/vectordb/

# CLI tests
pytest tests/cli/

# With coverage
pytest --cov=openviking tests/
```

### Docker Build

```bash
# Multi-stage build (handles Go, Rust, Python in one image)
make docker-build
# or
docker build -t openviking:latest .

# Run server in container
docker run -p 1933:1933 -v $(pwd)/data:/data openviking:latest

# Docker Compose for bot + server + observability
cd bot/deploy/docker && docker compose up
```

### Running the Server

```bash
# Start HTTP server (default port 1933)
openviking-server --config ~/.openviking/ov.conf

# Or with environment variables
OV_WORKSPACE=./data OV_PORT=1933 openviking-server
```

### CLI Usage After Build

```bash
# Verify CLI is available
ov --version

# Initialize workspace
ov system status

# Add a resource and wait for processing
ov add-resource ./docs --wait --timeout 300

# Search
ov find "authentication patterns"
```

### Vikingbot

```bash
# Start the bot gateway
vikingbot gateway start

# Start chat server
vikingbot chat start

# Start web console (port 18791)
vikingbot console start
```

## Build Artifact Locations

After a full build, the following artifacts are embedded in the Python package:

| Artifact | Source | Destination |
|----------|--------|-------------|
| AGFS binary | `third_party/agfs/` (Go build) | `openviking/pyagfs/bin/agfs` |
| Rust CLI binary | `crates/ov_cli/target/release/ov` | `openviking_cli/bin/ov` |
| C++ `.so` extensions | `build/` (CMake) | `openviking/storage/_ext*.so` |

## Configuration for Runtime

The main runtime configuration is `~/.openviking/ov.conf` (JSON):

```json
{
  "server": {
    "host": "0.0.0.0",
    "port": 1933,
    "api_key": "your-api-key"
  },
  "storage": {
    "workspace": "./data",
    "vectordb": {
      "name": "context",
      "backend": "local"
    },
    "agfs": {
      "backend": "local"
    }
  },
  "embedding": {
    "dense": {
      "provider": "volcengine",
      "model": "doubao-embedding-vision-250615",
      "api_key": "your-key",
      "base_url": "https://ark.cn-beijing.volces.com/api/v3"
    }
  },
  "vlm": {
    "provider": "volcengine",
    "model": "doubao-seed-2-0-pro-260215",
    "api_key": "your-key"
  },
  "rerank": {
    "enabled": false
  },
  "log": {
    "level": "INFO",
    "file": "./logs/openviking.log",
    "rotation": "10 MB"
  }
}
```

## Deployment

### Kubernetes (VKE)
Helm charts in `bot/deploy/vke/` with PVC support for NAS/TOS persistent storage.

### Volcengine ECS
Shell scripts in `bot/deploy/ecs/` for ECS instance setup.

### Environment Variables
Key environment variables (override `ov.conf`):
- `OV_WORKSPACE` — Data directory path
- `OV_PORT` — Server port
- `OV_API_KEY` — Server authentication key
- `OV_EMBEDDING_API_KEY` — Embedding model API key
- `OV_VLM_API_KEY` — Vision LLM API key
- `LANGFUSE_HOST`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` — Observability (optional)
