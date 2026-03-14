# OpenViking Repository Summary

## Repository Purpose and Goals

OpenViking is an open-source **Agent-native Context Database** developed by Beijing Volcano Engine Technology Co., Ltd. (ByteDance). It is designed specifically to solve context fragmentation in AI agent systems by adopting a "filesystem paradigm" to unify the organization of memories, resources, and skills needed by agents.

The core philosophy is **"Data in, Context out"** — transforming raw data (documents, web pages, code, media) into high-quality, structured context that AI agents can efficiently retrieve and utilize. Rather than treating context management as a traditional RAG (Retrieval-Augmented Generation) problem with flat vector databases, OpenViking models all context as a hierarchical filesystem using URIs, enabling agents to navigate information the same way humans navigate a file system.

**Primary Goals:**
- Unify fragmented context stores (memories, resources, skills) into one coherent system
- Reduce token consumption by exposing multiple granularity levels of every document
- Enable AI agents to autonomously navigate and retrieve context without human guidance
- Support seamless scaling from local development to cloud deployment
- Enable automatic learning through session memory extraction

## Key Features and Capabilities

- **Three-tier context model (L0/L1/L2)**: Every document is automatically decomposed into a compact abstract (L0, <200 tokens), a navigational overview (L1, <1000 tokens), and the full content (L2). Agents request only what they need.
- **VikingFS — Agent Filesystem**: A URI-based virtual filesystem (`viking://resources/`, `viking://memories/`, `viking://agent/`, `viking://session/`) that organizes all context hierarchically.
- **Multi-format document parsers**: Handles Markdown, PDF, HTML, plain text, JSON/YAML/XML, Office documents (DOCX/PPTX/XLSX), EPUB, code repositories (Python, JS/TS, Java, Go, C++, Rust, C#), and media files (images, video, audio via VLM).
- **Semantic processing pipeline**: Asynchronous, bottom-up L0/L1 generation using LLMs; decoupled from parsing for performance.
- **Session memory**: Conversation sessions are automatically compressed, archived, and long-term memories are extracted via LLM summarization.
- **Multi-backend embedding**: Supports OpenAI, Volcengine, and other providers via litellm; optional reranking.
- **REST API server**: FastAPI-based HTTP server with 12+ router groups covering all operations.
- **Rust CLI**: Full-featured command-line interface (`ov`) for all operations.
- **Vikingbot integration**: A multi-channel AI agent (Telegram, Feishu, DingTalk, Slack, QQ, WebSocket) with 7 built-in tools for context management.
- **Observability**: Queue monitoring, retrieval trajectory visualization, optional Langfuse tracing.

## Primary Use Cases and Target Audience

**Target audience**: AI agent developers, LLM application engineers, and researchers building context-heavy applications.

**Use cases:**
1. **Knowledge base for AI agents**: Import documentation, codebases, or web content and let agents retrieve context on demand
2. **Long-term agent memory**: Sessions are committed to extract and retain important information across conversations
3. **Multi-tenant agent systems**: Isolated namespaces per user/organization with shared resources
4. **Code repository Q&A**: Import GitHub repos with AST-level parsing for precise code navigation
5. **Document intelligence**: Batch import and query across mixed document types (PDF, HTML, DOCX)
6. **Chatbot backends**: Vikingbot provides ready-made channel integrations with automatic memory management

## High-Level Architecture Overview

OpenViking is a multi-language system with four main layers:

1. **Storage Layer**: VikingFS (Go-based Agent Filesystem, AGFS submodule) stores the hierarchical file structure; VikingDB (Volcengine vector database with local fallback) stores embeddings; custom C++ extensions handle performance-critical operations.

2. **Processing Pipeline**: Document parsers extract structure without LLM involvement. The SemanticQueue then processes files asynchronously — collecting child abstracts, calling LLMs concurrently to generate L0/L1 files, and writing vector indexes bottom-up.

3. **Service Layer**: `OpenVikingService` orchestrates all components. Exposed via embedded Python API (`SyncOpenViking`/`AsyncOpenViking`), HTTP REST API (FastAPI), and a compiled Rust CLI binary.

4. **Agent Layer**: Vikingbot provides a production-ready multi-channel agent that uses the context database as its memory system, with dedicated tools for all search and retrieval operations.

## Related Projects and Dependencies

- **AGFS (Agent Filesystem)**: Go-based filesystem in `third_party/agfs/` (git submodule) — the storage backbone
- **litellm**: Unified LLM routing across OpenAI, Volcengine, Anthropic, and others
- **tree-sitter**: AST-based code parsing for 8 programming languages
- **pdfplumber / readabilipy**: PDF and HTML extraction
- **FastAPI / uvicorn**: REST API server
- **Nanobot**: Base framework for Vikingbot agent implementation
- **VikingDB**: Volcengine vector database (cloud backend option)
- **RAGAS**: LLM pipeline evaluation framework
- **Langfuse**: Optional observability and tracing for bot deployments
- **python-telegram-bot, lark-oapi, dingtalk-stream, slack-sdk, qq-botpy**: Chat channel integrations
