# MCP Python SDK — Summary

## Repository Purpose and Goals

The MCP Python SDK (`mcp` on PyPI) is the official Python implementation of the **Model Context Protocol (MCP)**, an open standard developed by Anthropic for connecting LLM applications to external data sources and tools in a secure, standardized way. The SDK's primary goal is to make it easy to build both MCP **servers** (which expose resources, tools, and prompts to LLMs) and MCP **clients** (which connect to those servers and consume their capabilities). It implements the full MCP specification, including all protocol messages, lifecycle events, and transport layers.

## Key Features and Capabilities

- **FastMCP high-level server API**: A decorator-based, ergonomic interface (`FastMCP`) for building MCP servers with minimal boilerplate. Supports `@tool()`, `@resource()`, and `@prompt()` decorators that auto-generate JSON schemas from Python type annotations.
- **Low-level server API**: A `Server` class in `mcp.server.lowlevel` for direct handler registration, giving full control over protocol handling.
- **Multiple transport layers**: stdio (subprocess), SSE (Server-Sent Events over HTTP), and Streamable HTTP (the modern bidirectional HTTP transport). WebSocket support is available as an optional extra.
- **Full client support**: `ClientSession` for connecting to any MCP server, `ClientSessionGroup` for aggregating multiple servers, and transport-specific client helpers (`stdio_client`, `sse_client`, `streamable_http_client`).
- **OAuth 2.1 authorization**: Complete OAuth server and resource server support via `OAuthAuthorizationServerProvider`, `TokenVerifier`, `AuthSettings`, and bearer-token middleware.
- **Elicitation**: Servers can interactively request structured input from users mid-tool-execution via `Context.elicit()` (form mode) and `Context.elicit_url()` (URL mode for out-of-band flows like OAuth).
- **Sampling**: Servers can request LLM completions from the client via `sampling/createMessage`, with tool-calling support in sampling responses.
- **Structured tool output**: Tools can declare `outputSchema` and return structured JSON alongside unstructured content blocks.
- **Experimental Tasks API**: Long-running tool calls can be augmented with task-based polling (`tasks/get`, `tasks/result`, `tasks/cancel`, `tasks/list`).
- **DNS rebinding protection**: `TransportSecuritySettings` and `TransportSecurityMiddleware` guard HTTP transports against DNS rebinding attacks, auto-enabled for localhost.
- **In-memory transport for testing**: `create_connected_server_and_client_session` and `create_client_server_memory_streams` enable fast, no-network unit tests.
- **CLI tooling**: `mcp` CLI (requires `mcp[cli]`) for running, inspecting, and installing MCP servers.

## Primary Use Cases and Target Audience

The SDK targets Python developers who want to:
1. **Build MCP servers** that expose data (files, databases, APIs) as resources and functionality as tools to LLM applications like Claude.
2. **Build MCP clients** that connect to one or more MCP servers and aggregate their capabilities.
3. **Integrate MCP into existing Python web applications** by mounting FastMCP as a Starlette/ASGI sub-application.
4. **Test MCP servers** using in-memory transports without running a real network server.

## High-Level Architecture Overview

The SDK is organized into three main layers:

1. **Protocol layer** (`mcp/types.py`): Pydantic v2 models for every MCP message type — requests, responses, notifications, content blocks, capabilities, and error codes. This is the single source of truth for the wire format.

2. **Session layer** (`mcp/shared/session.py`, `mcp/server/session.py`, `mcp/client/session.py`): `BaseSession` implements the JSON-RPC message loop over anyio memory streams. `ServerSession` and `ClientSession` extend it with MCP-specific request/response handling, capability negotiation, progress notifications, logging, and sampling.

3. **Application layer**: Two tiers:
   - **FastMCP** (`mcp/server/fastmcp/`): High-level decorator API with `ToolManager`, `ResourceManager`, `PromptManager`, and a `Context` object injected into handlers. Wraps the low-level `Server`.
   - **Low-level Server** (`mcp/server/lowlevel/server.py`): Direct decorator-based handler registration for full protocol control.

Transport adapters (`stdio.py`, `sse.py`, `streamable_http.py`, `websocket.py`) bridge the session layer to actual I/O. The auth subsystem (`mcp/server/auth/`) is a self-contained OAuth 2.1 implementation that integrates with Starlette middleware.

## Related Projects and Dependencies

- **anyio** (≥4.5): Async I/O abstraction (asyncio + trio backends)
- **pydantic** (≥2.11, <3): Data validation and JSON schema generation
- **pydantic-settings** (≥2.5.2): `Settings` class for `FASTMCP_*` environment variables
- **starlette** (≥0.27): ASGI framework for SSE and Streamable HTTP transports
- **httpx** (≥0.27.1): HTTP client for SSE and Streamable HTTP client transports
- **sse-starlette** (≥1.6.1): SSE response support
- **uvicorn** (≥0.31.1): ASGI server for running HTTP transports
- **pyjwt[crypto]** (≥2.10.1): JWT verification for OAuth bearer tokens
- **jsonschema** (≥4.20.0): Runtime JSON schema validation for tool inputs
- **typer** (optional, `mcp[cli]`): CLI framework
- **websockets** (optional, `mcp[ws]`): WebSocket transport
- **MCP specification**: https://modelcontextprotocol.io/specification/latest
- **Officially supported servers**: https://github.com/modelcontextprotocol/servers
