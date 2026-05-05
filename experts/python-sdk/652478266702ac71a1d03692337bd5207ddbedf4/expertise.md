### Core Architecture
- `FastMCP` class — high-level server with `ToolManager`, `ResourceManager`, `PromptManager`, wraps low-level `MCPServer`
- `Server` class (`mcp.server.lowlevel.server`) — direct decorator-based handler registration for full protocol control
- `BaseSession` (`mcp.shared.session`) — JSON-RPC message loop over anyio memory streams; handles request correlation, cancellation, progress
- `ServerSession` and `ClientSession` — MCP-specific extensions of `BaseSession` with capability negotiation
- `RequestResponder` — context manager for responding to incoming requests; manages cancellation scope and completion tracking
- `ResponseRouter` — correlates JSON-RPC responses to in-flight requests by request ID
- `ContextVar`-based `request_context` in `Server` — makes current request accessible to nested code without explicit passing
- `SessionMessage` wrapper — carries `JSONRPCMessage` plus `MessageMetadata` through the transport layer
- Protocol version negotiation — `LATEST_PROTOCOL_VERSION = "2025-11-25"`, `SUPPORTED_PROTOCOL_VERSIONS` list, version mismatch raises `RuntimeError`

### FastMCP Decorator API
- `@mcp.tool(name, title, description, annotations, structured_output)` — registers a Python function as an MCP tool
- `@mcp.resource(uri, name, title, description, mime_type)` — registers static or template resources (URI params auto-detected)
- `@mcp.prompt(name, title, description)` — registers a prompt template
- `@mcp.completion()` — registers a completion handler for prompt/resource argument autocompletion
- `@mcp.custom_route(path, methods)` — adds arbitrary HTTP endpoints (health checks, OAuth callbacks) to the Starlette app
- `mcp.add_tool(fn, ...)`, `mcp.remove_tool(name)` — programmatic tool management
- `mcp.add_resource(resource)`, `mcp.add_prompt(prompt)` — programmatic registration

### Context Injection
- `Context` class — injected into tool/resource/prompt handlers via type annotation; generic over `ServerSessionT`, `LifespanContextT`, `RequestT`
- `find_context_parameter()` (`mcp.server.fastmcp.utilities.context_injection`) — inspects function signatures to locate `Context`-annotated parameter
- `Context.report_progress(progress, total, message)` — sends `ProgressNotification` to client
- `Context.read_resource(uri)` — reads a resource from within a tool handler
- `Context.elicit(message, schema)` — requests structured user input mid-execution
- `Context.elicit_url(message, url, elicitation_id)` — URL mode elicitation for out-of-band flows
- `Context.log(level, message, logger_name)` — sends `LoggingMessageNotification` to client
- `Context.close_sse_stream()` — closes SSE connection to trigger client reconnection
- `Context.request_id`, `Context.client_id`, `Context.session` — request metadata access

### Tool System
- `Tool` dataclass (`mcp.server.fastmcp.tools.base`) — holds `fn`, `name`, `description`, `parameters` (JSON schema), `fn_metadata`, `is_async`, `context_kwarg`, `annotations`, `output_schema`
- `ToolManager` — `add_tool()`, `remove_tool()`, `list_tools()`, `call_tool()` with context injection
- `FuncMetadata` and `func_metadata()` (`mcp.server.fastmcp.utilities.func_metadata`) — introspects Python function signatures to build Pydantic arg models and JSON schemas
- `ArgModelBase` — dynamically generated Pydantic model for tool arguments; `model_dump_one_level()` for one-level dict conversion
- `StrictJsonSchema` — raises exceptions instead of warnings for non-serializable types during schema generation
- `ToolAnnotations` — `readOnlyHint`, `destructiveHint`, `idempotentHint`, `openWorldHint` hints for clients
- `ToolExecution` — `taskSupport: TaskExecutionMode` ("forbidden"/"optional"/"required") for task-augmented execution
- `structured_output` parameter — `True` forces structured output, `False` forces unstructured, `None` auto-detects from return type
- `validate_and_warn_tool_name()` — validates tool names against MCP spec constraints

### Resource System
- `Resource` ABC (`mcp.server.fastmcp.resources.base`) — `uri`, `name`, `title`, `description`, `mime_type`, `async read() -> str | bytes`
- `FunctionResource` — lazy-loaded resource wrapping a callable; used by `@mcp.resource()` for non-template resources
- `TextResource`, `BinaryResource` — static content resources
- `FileResource` — reads from filesystem path via anyio
- `HttpResource` — fetches from HTTP URL via httpx
- `ResourceTemplate` — URI template resources (RFC 6570); auto-detected when URI contains `{param}` or function has params
- `ResourceManager` — `add_resource()`, `add_template()`, `list_resources()`, `list_templates()`, `get_resource(uri)`

### Prompt System
- `Prompt` dataclass (`mcp.server.fastmcp.prompts.base`) — `name`, `title`, `description`, `arguments`, `fn`; `from_function()` classmethod
- `PromptManager` — `add_prompt()`, `get_prompt()`, `list_prompts()`
- Prompt functions return `str`, `list[PromptMessage]`, or `GetPromptResult`

### Transport Layer
- `stdio_server()` — async context manager yielding `(read_stream, write_stream)` for subprocess stdio
- `stdio_client(params: StdioServerParameters)` — spawns subprocess and connects via stdio
- `SseServerTransport` — SSE server transport; `connect_sse()` context manager
- `sse_client(url, headers, timeout, sse_read_timeout)` — SSE client context manager
- `StreamableHTTPServerTransport` — modern bidirectional HTTP transport with session IDs
- `StreamableHTTPSessionManager` — manages multiple StreamableHTTP sessions; `handle_request()` ASGI handler
- `streamable_http_client(url, headers, timeout)` — StreamableHTTP client context manager
- `websocket_client(url)` — WebSocket client (requires `mcp[ws]`)
- `MCP_SESSION_ID_HEADER`, `MCP_PROTOCOL_VERSION_HEADER`, `LAST_EVENT_ID_HEADER` — StreamableHTTP header constants
- `EventStore` ABC — implement for SSE event persistence and replay on reconnection
- `stateless_http=True` — creates new transport per request (no session state)

### Client API
- `ClientSession.initialize()` — performs MCP handshake, negotiates capabilities, sends `InitializedNotification`
- `ClientSession.call_tool(name, arguments, progress_callback)` — calls a tool with optional progress tracking
- `ClientSession.list_tools()`, `list_resources()`, `list_resource_templates()`, `list_prompts()` — capability enumeration
- `ClientSession.read_resource(uri)` — reads a resource by URI
- `ClientSession.get_prompt(name, arguments)` — retrieves a rendered prompt
- `ClientSession.complete(ref, argument, context)` — requests argument autocompletion
- `ClientSession.send_roots_list_changed()` — notifies server of filesystem roots change
- `SamplingFnT`, `ElicitationFnT`, `ListRootsFnT`, `LoggingFnT`, `MessageHandlerFnT` — callback protocols for client-side handlers
- `ClientSessionGroup` — aggregates tools/resources/prompts from multiple servers; handles naming collisions
- `SseServerParameters`, `StreamableHttpParameters`, `StdioServerParameters` — server connection parameter models

### OAuth 2.1 Authorization
- `OAuthAuthorizationServerProvider` — protocol for full OAuth AS implementation; methods: `get_client`, `register_client`, `authorize`, `load_authorization_code`, `exchange_authorization_code`, `load_access_token`, `load_refresh_token`, `exchange_refresh_token`, `revoke_token`
- `TokenVerifier` — protocol for resource-server-only token verification; `verify_token(token) -> AccessToken | None`
- `ProviderTokenVerifier` — wraps `OAuthAuthorizationServerProvider` as a `TokenVerifier`
- `AuthSettings` — `issuer_url`, `resource_server_url`, `required_scopes`, `client_registration_options`, `revocation_options`
- `ClientRegistrationOptions` — `enabled`, `client_secret_expiry_seconds`, `valid_scopes`, `default_scopes`
- `BearerAuthBackend` — Starlette authentication backend for bearer token extraction
- `RequireAuthMiddleware` — enforces authentication on specific routes with required scopes
- `AuthContextMiddleware` — stores authenticated user in contextvar for handler access
- `create_auth_routes()` — generates OAuth endpoint routes (authorize, token, register, revoke, metadata)
- `create_protected_resource_routes()` — generates RFC 8707 protected resource metadata endpoint
- `OAuthToken`, `AccessToken`, `RefreshToken`, `AuthorizationCode` — token model types
- `OAuthClientMetadata`, `OAuthClientInformationFull` — RFC 7591 client registration models

### Elicitation
- `ElicitationResult[T]` — union of `AcceptedElicitation[T]`, `DeclinedElicitation`, `CancelledElicitation`
- `AcceptedElicitation.data: T` — the validated Pydantic model instance
- `UrlElicitationResult` — union of `AcceptedUrlElicitation`, `DeclinedElicitation`, `CancelledElicitation`
- `_validate_elicitation_schema()` — enforces primitive-only field types in elicitation schemas
- `ElicitationCapability` — `form: FormElicitationCapability`, `url: UrlElicitationCapability`
- `URL_ELICITATION_REQUIRED = -32042` — error code for URL elicitation requirement
- `UrlElicitationRequiredError` — exception raised when URL elicitation is required

### Sampling
- `CreateMessageRequest` / `CreateMessageRequestParams` — server-to-client LLM sampling request
- `CreateMessageResult` — client's sampling response with `role`, `content`, `model`, `stopReason`
- `CreateMessageResultWithTools` — sampling response with tool use content blocks
- `SamplingMessage` — `role` + `content: SamplingMessageContentBlock | list[...]`
- `SamplingMessageContentBlock` — union of `TextContent | ImageContent | AudioContent | ToolUseContent | ToolResultContent`
- `ToolUseContent` — assistant's tool call in sampling (`name`, `id`, `input`)
- `ToolResultContent` — tool execution result in sampling (`toolUseId`, `content`, `isError`)
- `ModelPreferences` — `hints`, `costPriority`, `speedPriority`, `intelligencePriority`
- `ToolChoice` — `mode: "auto" | "required" | "none"` for sampling tool usage control
- `SamplingCapability` — `context: SamplingContextCapability`, `tools: SamplingToolsCapability`

### Protocol Types (`mcp.types`)
- `LATEST_PROTOCOL_VERSION = "2025-11-25"`, `DEFAULT_NEGOTIATED_VERSION = "2025-03-26"`
- `ContentBlock` — `TextContent | ImageContent | AudioContent | ResourceLink | EmbeddedResource`
- `TextContent`, `ImageContent`, `AudioContent` — basic content types with `annotations` and `_meta`
- `EmbeddedResource` — resource contents embedded in prompt/tool results
- `ResourceLink` — resource reference in tool results (not guaranteed in `resources/list`)
- `Tool` — `name`, `title`, `description`, `inputSchema`, `outputSchema`, `annotations`, `execution`
- `Resource` — `uri`, `name`, `title`, `description`, `mimeType`, `size`, `icons`, `annotations`
- `ResourceTemplate` — `uriTemplate` (RFC 6570), `name`, `description`, `mimeType`
- `Prompt` — `name`, `title`, `description`, `arguments: list[PromptArgument]`
- `ClientCapabilities` — `sampling`, `elicitation`, `roots`, `tasks`, `experimental`
- `ServerCapabilities` — `logging`, `prompts`, `resources`, `tools`, `completions`, `tasks`
- `Task` — `taskId`, `status: TaskStatus`, `statusMessage`, `createdAt`, `lastUpdatedAt`, `ttl`, `pollInterval`
- `TaskStatus` — `"working" | "input_required" | "completed" | "failed" | "cancelled"`
- `JSONRPCMessage` — root model union of `JSONRPCRequest | JSONRPCNotification | JSONRPCResponse | JSONRPCError`
- Error codes: `PARSE_ERROR=-32700`, `INVALID_REQUEST=-32600`, `METHOD_NOT_FOUND=-32601`, `INVALID_PARAMS=-32602`, `INTERNAL_ERROR=-32603`, `CONNECTION_CLOSED=-32000`

### Experimental Tasks API
- `ExperimentalTaskHandlers` — client-side task polling handlers
- `ClientTasksCapability` — `list`, `cancel`, `requests` (sampling + elicitation)
- `ServerTasksCapability` — `list`, `cancel`, `requests.tools.call`
- `GetTaskRequest` / `GetTaskResult` — `tasks/get` — poll task status
- `GetTaskPayloadRequest` / `GetTaskPayloadResult` — `tasks/result` — retrieve completed task result
- `CancelTaskRequest` / `CancelTaskResult` — `tasks/cancel`
- `ListTasksRequest` / `ListTasksResult` — `tasks/list` with pagination
- `TaskStatusNotification` — `notifications/tasks/status` — push status updates
- `TaskMetadata` — `ttl` field in `RequestParams.task` to request task-augmented execution
- `TaskExecutionMode` — `"forbidden" | "optional" | "required"` on `ToolExecution.taskSupport`

### Transport Security
- `TransportSecuritySettings` — `enable_dns_rebinding_protection`, `allowed_hosts`, `allowed_origins`
- `TransportSecurityMiddleware` — validates `Host` and `Origin` headers; auto-enabled for localhost (`127.0.0.1`, `localhost`, `::1`)
- Wildcard port patterns in `allowed_hosts` (e.g., `"127.0.0.1:*"`)

### Testing
- `create_connected_server_and_client_session(server, raise_exceptions=True)` — primary testing utility; works with both `FastMCP` and low-level `Server`
- `create_client_server_memory_streams()` — lower-level bidirectional anyio memory stream pair
- `pytest-xdist` — parallel test execution (`--numprocesses auto`)
- `inline-snapshot` — snapshot testing for tool results
- `pytest-examples` — tests code examples embedded in documentation
- 100% code coverage enforced (`fail_under = 100`)

### CLI (`mcp` command, requires `mcp[cli]`)
- `mcp run server.py` — run an MCP server file
- `mcp dev server.py` — run with MCP Inspector for interactive testing
- `mcp install server.py --name "My Server"` — install into Claude Desktop
- `mcp version` — show SDK version
- `FASTMCP_*` environment variables — configure any `Settings` field without code changes

### Build and Packaging
- `hatchling` build backend with `uv-dynamic-versioning` for git-tag-based versions
- `uv` workspace — `examples/clients/*`, `examples/servers/*`, `examples/snippets` as workspace members
- Python ≥ 3.10 required; tested on 3.10, 3.11, 3.12, 3.13
- `pyproject.toml` — single config file for metadata, deps, ruff, pyright, pytest, coverage
- `ruff` — linter + formatter (line length 120, rules: C4, C90, E, F, I, PERF, PL, UP)
- `pyright` strict mode for `src/mcp`, `tests`, `examples/servers`
