# MCP Python SDK — Code Structure

## Directory Tree

```
python-sdk/
├── src/
│   └── mcp/                          # Main package (installed as `mcp`)
│       ├── __init__.py               # Public re-exports: ClientSession, ServerSession, types, stdio helpers
│       ├── types.py                  # ALL Pydantic protocol models (wire format)
│       ├── py.typed                  # PEP 561 marker
│       ├── cli/                      # CLI tooling (requires mcp[cli])
│       │   ├── cli.py                # Typer app: `mcp run`, `mcp dev`, `mcp install`, `mcp version`
│       │   └── claude.py             # Claude Desktop / Claude Code integration helpers
│       ├── client/                   # Client-side implementation
│       │   ├── __init__.py
│       │   ├── __main__.py           # `python -m mcp.client` entry point
│       │   ├── session.py            # ClientSession — main client class
│       │   ├── session_group.py      # ClientSessionGroup — multi-server aggregation
│       │   ├── sse.py                # sse_client() context manager
│       │   ├── streamable_http.py    # streamable_http_client() context manager
│       │   ├── websocket.py          # websocket_client() context manager
│       │   ├── stdio/
│       │   │   └── __init__.py       # stdio_client(), StdioServerParameters
│       │   ├── auth/                 # Client-side OAuth helpers
│       │   └── experimental/
│       │       ├── task_handlers.py  # ExperimentalTaskHandlers — client task polling
│       │       └── tasks.py          # Task result retrieval helpers
│       ├── server/                   # Server-side implementation
│       │   ├── __init__.py           # Re-exports: FastMCP, Server
│       │   ├── __main__.py           # `python -m mcp.server` entry point
│       │   ├── session.py            # ServerSession — server-side session
│       │   ├── stdio.py              # stdio_server() context manager
│       │   ├── sse.py                # SseServerTransport — SSE transport handler
│       │   ├── streamable_http.py    # StreamableHTTPServerTransport + EventStore ABC
│       │   ├── streamable_http_manager.py  # StreamableHTTPSessionManager
│       │   ├── websocket.py          # WebSocket transport handler
│       │   ├── elicitation.py        # Elicitation result types + validation
│       │   ├── models.py             # InitializationOptions
│       │   ├── transport_security.py # TransportSecuritySettings + middleware
│       │   ├── validation.py         # Tool input JSON schema validation
│       │   ├── auth/                 # OAuth 2.1 authorization subsystem
│       │   │   ├── provider.py       # OAuthAuthorizationServerProvider protocol + token models
│       │   │   ├── settings.py       # AuthSettings, ClientRegistrationOptions
│       │   │   ├── routes.py         # create_auth_routes(), create_protected_resource_routes()
│       │   │   ├── errors.py         # OAuth error types
│       │   │   ├── json_response.py  # JSON response helpers
│       │   │   ├── handlers/         # OAuth endpoint handlers (authorize, token, register, revoke)
│       │   │   └── middleware/
│       │   │       ├── auth_context.py   # AuthContextMiddleware (stores auth in contextvar)
│       │   │       └── bearer_auth.py    # BearerAuthBackend + RequireAuthMiddleware
│       │   ├── experimental/         # Experimental server features
│       │   │   ├── request_context.py  # Experimental request context
│       │   │   ├── session_features.py # Experimental session features
│       │   │   ├── task_context.py     # Task execution context
│       │   │   ├── task_result_handler.py  # Task result storage/retrieval
│       │   │   └── task_support.py     # Task augmentation support
│       │   ├── fastmcp/              # High-level FastMCP API
│       │   │   ├── server.py         # FastMCP class + Context class + Settings + StreamableHTTPASGIApp
│       │   │   ├── exceptions.py     # ResourceError, ToolError, InvalidSignature
│       │   │   ├── tools/
│       │   │   │   ├── base.py       # Tool dataclass (internal registration info)
│       │   │   │   └── tool_manager.py  # ToolManager — add/remove/call tools
│       │   │   ├── resources/
│       │   │   │   ├── base.py       # Resource ABC
│       │   │   │   ├── types.py      # TextResource, BinaryResource, FunctionResource, FileResource, HttpResource
│       │   │   │   ├── templates.py  # ResourceTemplate — URI template resources
│       │   │   │   └── resource_manager.py  # ResourceManager
│       │   │   ├── prompts/
│       │   │   │   ├── base.py       # Prompt dataclass
│       │   │   │   └── manager.py    # PromptManager
│       │   │   └── utilities/
│       │   │       ├── func_metadata.py    # FuncMetadata, func_metadata() — schema generation
│       │   │       ├── context_injection.py  # find_context_parameter() — Context injection
│       │   │       ├── logging.py    # configure_logging(), get_logger()
│       │   │       └── types.py      # Image, Audio helper types for tool returns
│       │   └── lowlevel/             # Low-level server API
│       │       ├── server.py         # Server class — direct handler registration
│       │       ├── experimental.py   # ExperimentalHandlers
│       │       ├── func_inspection.py  # create_call_wrapper() — handler introspection
│       │       └── helper_types.py   # ReadResourceContents
│       ├── shared/                   # Shared client+server code
│       │   ├── session.py            # BaseSession — JSON-RPC message loop
│       │   ├── context.py            # RequestContext, LifespanContextT
│       │   ├── message.py            # SessionMessage, MessageMetadata
│       │   ├── memory.py             # create_connected_server_and_client_session(), create_client_server_memory_streams()
│       │   ├── auth.py               # OAuthToken, OAuthClientMetadata, OAuthClientInformationFull
│       │   ├── auth_utils.py         # Auth utility functions
│       │   ├── exceptions.py         # McpError, UrlElicitationRequiredError
│       │   ├── progress.py           # Progress notification helpers
│       │   ├── response_router.py    # ResponseRouter — correlates responses to requests
│       │   ├── version.py            # SUPPORTED_PROTOCOL_VERSIONS
│       │   ├── tool_name_validation.py  # validate_and_warn_tool_name()
│       │   ├── metadata_utils.py     # Metadata helpers
│       │   ├── _httpx_utils.py       # create_mcp_http_client()
│       │   └── experimental/         # Shared experimental features
│       └── os/                       # OS-specific utilities
│           ├── posix/utilities.py    # POSIX process helpers
│           └── win32/utilities.py    # Windows process helpers
├── tests/                            # Test suite
│   ├── client/                       # Client tests
│   ├── server/
│   │   ├── fastmcp/                  # FastMCP tests (tools, resources, prompts, auth)
│   │   └── ...
│   ├── shared/                       # Shared session/transport tests
│   └── issues/                       # Regression tests
├── examples/
│   ├── servers/                      # Example server implementations (uv workspace members)
│   ├── clients/                      # Example client implementations
│   └── snippets/                     # Quickstart code snippets (tested via pytest-examples)
├── docs/                             # MkDocs documentation source
│   ├── server.md                     # FastMCP server guide
│   ├── client.md                     # Client guide
│   ├── authorization.md              # OAuth guide
│   ├── low-level-server.md           # Low-level server guide
│   ├── testing.md                    # Testing guide
│   └── experimental/                 # Experimental features docs
├── scripts/                          # Development scripts
├── pyproject.toml                    # Project metadata, dependencies, tool config
├── uv.lock                           # Locked dependency tree
└── mkdocs.yml                        # Documentation site config
```

## Module and Package Organization

The package is split into four top-level sub-packages under `src/mcp/`:

### `mcp.types` — Protocol Models
Single file containing all Pydantic v2 models for the MCP wire format. Every JSON-RPC message, capability, content block, and result type lives here. Key types: `Tool`, `Resource`, `Prompt`, `ContentBlock`, `CallToolResult`, `ClientCapabilities`, `ServerCapabilities`, `JSONRPCMessage`, `SamplingMessage`, `Task`.

### `mcp.server` — Server Implementation
- **`fastmcp/server.py`**: `FastMCP` is the primary entry point for server authors. It owns `ToolManager`, `ResourceManager`, `PromptManager`, and wraps a low-level `MCPServer`. The `Context` class (injected into tool/resource/prompt handlers) provides `report_progress()`, `read_resource()`, `elicit()`, `elicit_url()`, `log()`, and session access.
- **`fastmcp/tools/base.py`**: `Tool` dataclass holds the registered function, its Pydantic-derived JSON schema (`parameters`), async flag, context kwarg name, and optional `outputSchema`.
- **`fastmcp/utilities/func_metadata.py`**: `FuncMetadata` and `func_metadata()` introspect Python function signatures to build Pydantic arg models and JSON schemas. `ArgModelBase` is the generated model base. Handles structured output schema generation.
- **`lowlevel/server.py`**: `Server` class with decorator methods (`list_tools()`, `call_tool()`, `list_resources()`, `read_resource()`, `list_prompts()`, `get_prompt()`, `completion()`, `progress_notification()`). Manages `request_context` contextvar.
- **`auth/provider.py`**: `OAuthAuthorizationServerProvider` protocol — implementors provide `authorize()`, `load_client()`, `register_client()`, `load_access_token()`, `load_refresh_token()`, `exchange_refresh_token()`, `revoke_token()`.

### `mcp.client` — Client Implementation
- **`session.py`**: `ClientSession` extends `BaseSession`. Provides `initialize()`, `call_tool()`, `list_tools()`, `read_resource()`, `list_resources()`, `get_prompt()`, `list_prompts()`, `complete()`, `send_roots_list_changed()`. Accepts callbacks: `sampling_callback`, `elicitation_callback`, `list_roots_callback`, `logging_callback`.
- **`session_group.py`**: `ClientSessionGroup` aggregates tools/resources/prompts from multiple servers. Handles naming collisions via user-provided hooks. Supports `SseServerParameters`, `StreamableHttpParameters`, `StdioServerParameters`.

### `mcp.shared` — Shared Infrastructure
- **`session.py`**: `BaseSession` — the core JSON-RPC engine. Manages in-flight requests via `ResponseRouter`, handles cancellation via `CancelledNotification`, dispatches progress notifications. `RequestResponder` is a context manager for responding to incoming requests.
- **`memory.py`**: `create_connected_server_and_client_session()` — the primary testing utility. Creates bidirectional anyio memory streams and runs server + client in a task group.

## Code Organization Patterns

- **Decorator-based handler registration**: Both `FastMCP` and low-level `Server` use Python decorators (`@mcp.tool()`, `@server.list_tools()`) to register handlers, following the FastAPI/Starlette pattern.
- **Context injection**: `find_context_parameter()` inspects function signatures for a `Context`-annotated parameter and injects it automatically — no explicit passing required.
- **Pydantic everywhere**: All protocol messages, settings, tool parameters, and resource models use Pydantic v2. `func_metadata()` generates Pydantic models dynamically from function signatures.
- **anyio for async**: All async code uses anyio primitives (`MemoryObjectReceiveStream`, `MemoryObjectSendStream`, `CancelScope`, task groups) for asyncio/trio compatibility.
- **Transport abstraction**: Transports produce/consume `SessionMessage` objects (wrapping `JSONRPCMessage`) over anyio memory streams. The session layer is transport-agnostic.
- **Contextvar-based request context**: `Server` stores the current `RequestContext` in a `ContextVar`, making it accessible to nested code without explicit threading.
