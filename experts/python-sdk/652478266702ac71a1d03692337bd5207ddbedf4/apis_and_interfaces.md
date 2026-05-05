# MCP Python SDK — APIs and Interfaces

## Public APIs and Entry Points

### Top-Level Package (`mcp`)
```python
from mcp import (
    ClientSession, ClientSessionGroup,
    ServerSession,
    StdioServerParameters, stdio_client, stdio_server,
    McpError, UrlElicitationRequiredError,
    # All protocol types:
    Tool, Resource, SamplingMessage, CallToolRequest, ...
)
```

### FastMCP Server (Primary High-Level API)
```python
from mcp.server.fastmcp import FastMCP, Context
```

### Low-Level Server
```python
from mcp.server.lowlevel.server import Server
from mcp.server.models import InitializationOptions
```

### Client Transports
```python
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamable_http_client
from mcp.client.websocket import websocket_client
```

### Testing Utilities
```python
from mcp.shared.memory import (
    create_connected_server_and_client_session,
    create_client_server_memory_streams,
)
```

---

## Key Classes, Functions, and Types

### `FastMCP` (`mcp.server.fastmcp.server`)

The primary server class. Generic over `LifespanResultT`.

**Constructor parameters:**
- `name: str | None` — server name (default: "FastMCP")
- `instructions: str | None` — server instructions for LLMs
- `auth_server_provider: OAuthAuthorizationServerProvider | None` — full OAuth AS
- `token_verifier: TokenVerifier | None` — token-only verification (RS mode)
- `event_store: EventStore | None` — for StreamableHTTP event replay
- `host`, `port`, `mount_path`, `sse_path`, `message_path`, `streamable_http_path` — HTTP settings
- `json_response: bool` — return JSON instead of SSE for StreamableHTTP
- `stateless_http: bool` — new transport per request (no session state)
- `lifespan: Callable[[FastMCP], AsyncContextManager]` — startup/shutdown hook
- `auth: AuthSettings | None` — OAuth settings
- `transport_security: TransportSecuritySettings | None` — DNS rebinding protection

**Key methods:**
- `run(transport="stdio"|"sse"|"streamable-http")` — synchronous entry point
- `run_stdio_async()`, `run_sse_async()`, `run_streamable_http_async()` — async variants
- `sse_app(mount_path=None) -> Starlette` — ASGI app for SSE transport
- `streamable_http_app() -> Starlette` — ASGI app for StreamableHTTP transport
- `get_context() -> Context` — get current request context
- `add_tool(fn, name, title, description, annotations, structured_output)` — programmatic tool registration
- `remove_tool(name)` — remove a registered tool
- `add_resource(resource)` — add a `Resource` instance
- `add_prompt(prompt)` — add a `Prompt` instance

**Decorator methods:**
- `@mcp.tool(name, title, description, annotations, structured_output)` — register a tool
- `@mcp.resource(uri, name, title, description, mime_type)` — register a resource or template
- `@mcp.prompt(name, title, description)` — register a prompt
- `@mcp.completion()` — register a completion handler
- `@mcp.custom_route(path, methods, name)` — add custom HTTP routes (for OAuth callbacks, health checks)

**Settings** (`FastMCP.settings: Settings`): All settings configurable via `FASTMCP_*` environment variables (e.g., `FASTMCP_PORT=9000`, `FASTMCP_LOG_LEVEL=DEBUG`).

---

### `Context` (`mcp.server.fastmcp.server`)

Injected into tool/resource/prompt handlers via type annotation. Generic over `ServerSessionT`, `LifespanContextT`, `RequestT`.

```python
@mcp.tool()
async def my_tool(x: int, ctx: Context) -> str:
    await ctx.report_progress(50, 100, "halfway")
    data = await ctx.read_resource("resource://my-data")
    await ctx.log("info", "Processing...")
    result = await ctx.elicit("Enter your name", schema=MyModel)
    return str(x)
```

**Properties:**
- `request_id: str` — unique ID for the current request
- `client_id: str | None` — authenticated client ID (OAuth)
- `session` — underlying `ServerSession`
- `fastmcp: FastMCP` — the server instance

**Async methods:**
- `report_progress(progress, total=None, message=None)` — send progress notification
- `read_resource(uri) -> Iterable[ReadResourceContents]` — read a resource
- `elicit(message, schema: type[BaseModel]) -> ElicitationResult` — request structured input
- `elicit_url(message, url, elicitation_id) -> UrlElicitationResult` — URL mode elicitation
- `log(level, message, logger_name=None)` — send log message to client
- `close_sse_stream()` — close SSE stream to trigger client reconnection

---

### `ClientSession` (`mcp.client.session`)

Main client class for connecting to MCP servers.

**Constructor:**
```python
ClientSession(
    read_stream, write_stream,
    read_timeout_seconds=None,
    sampling_callback=None,      # SamplingFnT
    elicitation_callback=None,   # ElicitationFnT
    list_roots_callback=None,    # ListRootsFnT
    logging_callback=None,       # LoggingFnT
    message_handler=None,        # MessageHandlerFnT
    client_info=None,
    sampling_capabilities=None,
    experimental_task_handlers=None,
)
```

**Key async methods:**
- `initialize() -> InitializeResult` — perform MCP handshake
- `call_tool(name, arguments=None, progress_callback=None) -> CallToolResult`
- `list_tools() -> ListToolsResult`
- `read_resource(uri) -> ReadResourceResult`
- `list_resources() -> ListResourcesResult`
- `list_resource_templates() -> ListResourceTemplatesResult`
- `get_prompt(name, arguments=None) -> GetPromptResult`
- `list_prompts() -> ListPromptsResult`
- `complete(ref, argument, context=None) -> CompleteResult`
- `send_roots_list_changed()` — notify server of roots change
- `send_progress_notification(progress_token, progress, total, message)`
- `get_server_capabilities() -> ServerCapabilities | None`

---

### `ClientSessionGroup` (`mcp.client.session_group`)

Aggregates multiple MCP servers into a single interface.

```python
async with ClientSessionGroup() as group:
    await group.connect_to_server(StdioServerParameters(command="python", args=["server.py"]))
    await group.connect_to_server(SseServerParameters(url="http://localhost:8000/sse"))
    tools = await group.list_tools()
    result = await group.call_tool("tool_name", {"arg": "value"})
```

---

### Transport Context Managers

**stdio (subprocess)**:
```python
from mcp.client.stdio import stdio_client, StdioServerParameters

params = StdioServerParameters(
    command="python",
    args=["server.py"],
    env={"MY_VAR": "value"},
)
async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
```

**SSE**:
```python
from mcp.client.sse import sse_client

async with sse_client("http://localhost:8000/sse", headers={"Authorization": "Bearer token"}) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
```

**Streamable HTTP** (modern, preferred):
```python
from mcp.client.streamable_http import streamable_http_client

async with streamable_http_client("http://localhost:8000/mcp") as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
```

---

### Low-Level Server (`mcp.server.lowlevel.server.Server`)

For full protocol control:

```python
from mcp.server.lowlevel.server import Server
import mcp.types as types

server = Server("my-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [types.Tool(name="my_tool", description="...", inputSchema={...})]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.ContentBlock]:
    return [types.TextContent(type="text", text="result")]

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]: ...

@server.read_resource()
async def handle_read_resource(uri: AnyUrl) -> str | bytes: ...

@server.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]: ...

@server.get_prompt()
async def handle_get_prompt(name: str, arguments: dict[str, str] | None) -> types.GetPromptResult: ...

@server.completion()
async def handle_completion(ref, argument, context) -> types.Completion | None: ...

# Run with stdio
async with stdio_server() as (read, write):
    await server.run(read, write, server.create_initialization_options())
```

---

### OAuth Authorization (`mcp.server.auth`)

**`OAuthAuthorizationServerProvider`** (protocol to implement):
```python
class MyOAuthProvider(OAuthAuthorizationServerProvider):
    async def get_client(self, client_id: str) -> OAuthClientInformationFull | None: ...
    async def register_client(self, info: OAuthClientInformationFull) -> None: ...
    async def authorize(self, client, params: AuthorizationParams) -> str: ...  # returns auth code
    async def load_authorization_code(self, client, code: str) -> AuthorizationCode | None: ...
    async def exchange_authorization_code(self, client, code: AuthorizationCode) -> OAuthToken: ...
    async def load_access_token(self, token: str) -> AccessToken | None: ...
    async def load_refresh_token(self, client, token: str) -> RefreshToken | None: ...
    async def exchange_refresh_token(self, client, old_token, scopes) -> OAuthToken: ...
    async def revoke_token(self, token: AccessToken | RefreshToken) -> None: ...
```

**`TokenVerifier`** (for resource-server-only mode):
```python
class MyVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None: ...
```

**`AuthSettings`**:
```python
AuthSettings(
    issuer_url="https://auth.example.com",
    resource_server_url="https://mcp.example.com",
    required_scopes=["mcp:read", "mcp:write"],
    client_registration_options=ClientRegistrationOptions(enabled=True),
)
```

---

### Elicitation (`mcp.server.elicitation`)

```python
from mcp.server.elicitation import ElicitationResult, AcceptedElicitation, DeclinedElicitation, CancelledElicitation
from pydantic import BaseModel

class UserInput(BaseModel):
    name: str
    age: int

@mcp.tool()
async def get_user_info(ctx: Context) -> str:
    result: ElicitationResult[UserInput] = await ctx.elicit("Please provide your info", schema=UserInput)
    match result.action:
        case "accept":
            return f"Hello {result.data.name}, age {result.data.age}"
        case "decline":
            return "User declined"
        case "cancel":
            return "Cancelled"
```

Only primitive field types (`str`, `int`, `float`, `bool`) and their `Optional` variants are allowed in elicitation schemas.

---

### Testing (`mcp.shared.memory`)

```python
from mcp.shared.memory import create_connected_server_and_client_session
from mcp.server.fastmcp import FastMCP
from mcp.client.session import ClientSession

app = FastMCP("Test")

@app.tool()
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@pytest.fixture
async def client() -> AsyncGenerator[ClientSession]:
    async with create_connected_server_and_client_session(app, raise_exceptions=True) as session:
        yield session

async def test_add(client: ClientSession):
    result = await client.call_tool("add", {"a": 1, "b": 2})
    assert result.content[0].text == "3"
```

---

### Resource Types (`mcp.server.fastmcp.resources.types`)

- `TextResource` — static text content
- `BinaryResource` — static binary content
- `FunctionResource` — lazy-loaded via callable (used by `@mcp.resource()`)
- `FileResource` — reads from filesystem path
- `HttpResource` — fetches from HTTP URL

---

### Tool Return Types

Tools can return:
- `str` → `TextContent`
- `bytes` → `BlobResourceContents`
- `Image` (from `mcp.server.fastmcp.utilities.types`) → `ImageContent`
- `Audio` → `AudioContent`
- Pydantic `BaseModel` → structured JSON output (when `outputSchema` is set)
- `list[ContentBlock]` → multiple content blocks
- `CallToolResult` → full control

---

### Configuration and Extension Points

- **`FASTMCP_*` env vars**: Override any `Settings` field (e.g., `FASTMCP_PORT=9000`, `FASTMCP_HOST=0.0.0.0`, `FASTMCP_LOG_LEVEL=DEBUG`, `FASTMCP_STATELESS_HTTP=true`).
- **`lifespan` parameter**: Async context manager for startup/shutdown (database connections, background tasks).
- **`event_store: EventStore`**: Implement the `EventStore` ABC to persist SSE events for StreamableHTTP reconnection replay.
- **`custom_route` decorator**: Add arbitrary HTTP endpoints (health checks, OAuth callbacks) to the FastMCP Starlette app.
- **`session_manager` property**: Access `StreamableHTTPSessionManager` for advanced ASGI mounting (e.g., multiple FastMCP servers in one FastAPI app).
- **`warn_on_duplicate_tools/resources/prompts`**: Control duplicate registration warnings.
- **`structured_output` parameter on `@tool()`**: `True` forces structured output, `False` forces unstructured, `None` auto-detects from return type annotation.
