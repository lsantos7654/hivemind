# Claude Agent SDK for Python — Code Structure

## Annotated Directory Tree

```
repo/
├── src/
│   └── claude_agent_sdk/          # Main package
│       ├── __init__.py            # Public API surface — all exports
│       ├── client.py              # ClaudeSDKClient (bidirectional streaming)
│       ├── query.py               # query() function (one-shot async generator)
│       ├── types.py               # All type definitions (~1200 lines)
│       ├── _errors.py             # Exception hierarchy
│       ├── _version.py            # SDK version constant
│       ├── _cli_version.py        # Bundled CLI version constant
│       └── _internal/             # Private implementation details
│           ├── __init__.py
│           ├── client.py          # Core client logic (Query orchestration)
│           ├── message_parser.py  # Deserialize JSON messages → typed objects
│           ├── query.py           # Control protocol (JSON-RPC over stdio)
│           ├── sessions.py        # Session history access
│           ├── session_mutations.py # Session rename/tag operations
│           └── transport/
│               ├── __init__.py    # Transport ABC
│               └── subprocess_cli.py # CLI subprocess management
├── examples/                      # Runnable usage examples (16+ files)
│   ├── quick_start.py             # Basic usage: query() and options
│   ├── mcp_calculator.py          # Full MCP server with 6 calculator tools
│   ├── streaming_mode.py          # ClaudeSDKClient patterns (30+ cases)
│   ├── streaming_mode_trio.py     # Alternative trio backend
│   ├── hooks.py                   # Hook callback patterns
│   ├── tool_permission_callback.py# Permission callback implementation
│   ├── agents.py                  # Custom subagent definitions
│   ├── filesystem_agents.py       # Filesystem-scoped agents
│   ├── include_partial_messages.py# Partial streaming (StreamEvent)
│   ├── max_budget_usd.py          # Cost budgeting control
│   ├── setting_sources.py         # Configuration sources overview
│   ├── system_prompt.py           # System prompt variations
│   ├── tools_option.py            # Tools configuration patterns
│   ├── plugin_example.py          # Plugin integration
│   └── stderr_callback_example.py # Debugging/stderr logging
├── tests/                         # Unit tests
│   ├── test_client.py
│   ├── test_query.py
│   ├── test_message_parser.py
│   ├── test_transport.py
│   ├── test_sdk_mcp_integration.py
│   ├── test_tool_callbacks.py
│   ├── test_types.py
│   ├── test_sessions.py
│   ├── test_session_mutations.py
│   ├── test_errors.py
│   └── test_subprocess_buffering.py
├── e2e-tests/                     # End-to-end tests (require API key)
│   ├── test_mcp_tools.py
│   ├── test_hooks.py
│   ├── test_partial_messages.py
│   ├── test_tool_permissions.py
│   ├── test_structured_output.py
│   ├── test_sandbox.py
│   └── test_dynamic_control.py
├── scripts/                       # Build and release automation
│   ├── build_wheel.py             # Platform wheel builder
│   ├── initial-setup.sh           # Dev environment setup
│   └── generate-changelog.sh      # AI-powered changelog generator
├── .github/
│   └── workflows/                 # CI/CD (lint, test, publish)
├── pyproject.toml                 # Project metadata, deps, tool config
├── README.md                      # Main documentation
├── CHANGELOG.md                   # Version history
├── RELEASING.md                   # Release process documentation
└── CLAUDE.md                      # Development guidelines for AI assistants
```

## Module and Package Organization

The package follows a clean public/private split:

- **Public API** — Everything in `src/claude_agent_sdk/` at the top level (imported in `__init__.py`)
- **Private Implementation** — Everything under `_internal/` (prefixed with underscore, not for direct import)

The `__init__.py` is the single source of truth for what is exported to users. It explicitly imports and re-exports all public symbols.

## Main Source Files and Their Roles

### `src/claude_agent_sdk/__init__.py`
The public API surface. Exports:
- `query` — one-shot async generator function
- `ClaudeSDKClient` — bidirectional streaming client class
- `ClaudeAgentOptions` — main configuration dataclass
- All message types: `UserMessage`, `AssistantMessage`, `SystemMessage`, `ResultMessage`, `StreamEvent`, `RateLimitEvent`, `TaskStartedMessage`, `TaskProgressMessage`, `TaskNotificationMessage`
- Content block types: `TextBlock`, `ThinkingBlock`, `ToolUseBlock`, `ToolResultBlock`
- Tool primitives: `tool`, `create_sdk_mcp_server`, `SdkMcpTool`
- Hook types: `HookMatcher`, `HookContext`, `HookInput`, `HookCallback`, `HookJSONOutput`
- Session functions: `list_sessions`, `get_session_messages`, `rename_session`, `tag_session`
- Error types: `ClaudeSDKError`, `CLIConnectionError`, `CLINotFoundError`, `ProcessError`, `CLIJSONDecodeError`, `MessageParseError`
- Config types: `ThinkingConfig`, `McpSdkServerConfig`, `PermissionMode`, `OutputFormat`

### `src/claude_agent_sdk/client.py`
Defines `ClaudeSDKClient`, the bidirectional streaming client. Acts as an async context manager. Delegates to `_internal/client.py` for the actual protocol work. Exposes user-facing async methods for query, receive, interrupt, model switching, permission modes, MCP control, file checkpointing, and task management.

### `src/claude_agent_sdk/query.py`
Defines the `query()` async generator function. Takes a prompt (string or `AsyncIterable[dict]`) and options, creates a transport, initializes the internal query controller, and yields `Message` objects as they arrive. Designed for simple, stateless use cases.

### `src/claude_agent_sdk/types.py`
The largest file (~1200 lines). Contains all dataclasses, TypedDicts, enums, and type aliases. Key sections:
- **Message types** — `UserMessage`, `AssistantMessage`, `SystemMessage`, `ResultMessage`, stream types
- **Content blocks** — `TextBlock`, `ThinkingBlock`, `ToolUseBlock`, `ToolResultBlock`
- **Options** — `ClaudeAgentOptions`, `ThinkingConfig`, permission configs, sandbox configs
- **Hook types** — `HookMatcher`, `HookInput`, `HookContext`, all hook event-specific types
- **MCP types** — `McpSdkServerConfig`, `SdkMcpTool`, `McpServerConfig`
- **Session types** — `SDKSessionInfo`, `SessionMessage`
- **Task types** — `TaskStartedMessage`, `TaskProgressMessage`, `TaskNotificationMessage`

### `src/claude_agent_sdk/_errors.py`
Defines the exception hierarchy:
- `ClaudeSDKError` — base class for all SDK exceptions
- `CLIConnectionError` — failed to connect to or launch CLI
- `CLINotFoundError` — CLI binary not found anywhere
- `ProcessError` — CLI process exited with error
- `CLIJSONDecodeError` — failed to parse JSON from CLI output
- `MessageParseError` — failed to deserialize a message into typed objects

### `src/claude_agent_sdk/_internal/client.py`
The core orchestration engine. Implements the `Query` class which:
- Manages the transport lifecycle
- Coordinates message reading, hook callbacks, MCP requests, permission callbacks
- Handles bidirectional control messages (hook responses, permission responses)
- Routes streaming events to callers
- Implements interrupt and task stop semantics

### `src/claude_agent_sdk/_internal/message_parser.py`
Pure deserialization logic. Takes raw JSON dicts from the CLI and converts them into typed Python dataclasses. Handles all message types, content block types, and streaming events. Raises `MessageParseError` for unknown or malformed messages.

### `src/claude_agent_sdk/_internal/query.py`
Implements the JSON-RPC style control protocol over stdio. Handles:
- Sending `initialize` messages to the CLI
- Dispatching `hook_callback` responses
- Routing `mcp_message` for in-process MCP tool execution
- Sending `can_use_tool` permission responses
- Writing prompt lines and end-of-input signaling

### `src/claude_agent_sdk/_internal/transport/subprocess_cli.py`
The `SubprocessCLITransport` class. Responsibilities:
- Locating the Claude Code CLI binary (bundled first, then PATH, then common locations)
- Spawning and managing the subprocess with correct arguments
- Streaming stdout lines as async messages
- Writing JSON to stdin with a write lock for thread-safety
- Handling end-of-input (closing stdin)
- Enforcing buffer size limits (`max_buffer_size`, default 1MB)
- Enforcing stream close timeouts (`CLAUDE_CODE_STREAM_CLOSE_TIMEOUT`, default 60s)

### `src/claude_agent_sdk/_internal/sessions.py`
Provides `list_sessions()` and `get_session_messages()` by invoking the CLI with `--output-format json` and parsing the results. Pure read operations against session storage.

### `src/claude_agent_sdk/_internal/session_mutations.py`
Provides `rename_session()` and `tag_session()` by invoking the CLI with appropriate mutation arguments.

## Code Organization Patterns

**Async-First Design:** All I/O-bound operations use `async`/`await`. The `anyio` library is used throughout for backend-agnostic async primitives (works with both `asyncio` and `trio`).

**Dataclass-Heavy Types:** All message types, option types, and result types are Python `@dataclass` instances rather than dicts, providing IDE autocompletion and static type checking.

**Private Module Prefix:** All implementation details that should not be imported directly by users use the `_internal` package or `_` prefix.

**Modern Type Hints:** The codebase uses PEP 604 union syntax (`str | None` not `Optional[str]`), built-in generics (`list[str]` not `List[str]`), and only imports from `typing` for advanced types like `Callable` and `Protocol`.

**Transport Abstraction:** The `Transport` ABC in `_internal/transport/__init__.py` allows the transport to be replaced for testing or alternative backends (e.g., mock transports in tests).

**Strict Mypy:** The project uses mypy in strict mode, ensuring full type coverage throughout the codebase.
