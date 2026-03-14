# Claude Agent SDK for Python — APIs and Interfaces

## Public API Entry Points

All public symbols are exported from `claude_agent_sdk` (the top-level package). Users should import from `claude_agent_sdk` directly, never from `_internal` submodules.

```python
from claude_agent_sdk import (
    query,
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AssistantMessage,
    TextBlock,
    tool,
    create_sdk_mcp_server,
    HookMatcher,
    # ... etc
)
```

---

## Core Interfaces

### `query()` — One-Shot Async Generator

```python
async def query(
    prompt: str | AsyncIterable[dict[str, Any]],
    options: ClaudeAgentOptions | None = None,
    transport: Transport | None = None,
) -> AsyncIterator[Message]
```

The simplest way to interact with Claude. Yields `Message` objects as they arrive.

**Usage:**
```python
import asyncio
from claude_agent_sdk import query, AssistantMessage, TextBlock

async def main():
    async for message in query("Explain async/await in Python"):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)

asyncio.run(main())
```

**Multi-turn via AsyncIterable prompt:**
```python
async def prompts():
    yield {"role": "user", "content": "What is 2 + 2?"}
    yield {"role": "user", "content": "Now multiply that by 3"}

async for message in query(prompts()):
    ...
```

---

### `ClaudeSDKClient` — Bidirectional Streaming Client

```python
class ClaudeSDKClient:
    def __init__(
        self,
        options: ClaudeAgentOptions | None = None,
        transport: Transport | None = None,
    ) -> None
```

Full-featured client for interactive multi-turn conversations. Supports async context manager protocol.

**Key Methods:**

```python
# Connection lifecycle
async def connect(prompt: str | AsyncIterable[...] | None = None) -> None
async def disconnect() -> None

# Sending queries
async def query(
    prompt: str | AsyncIterable[...],
    session_id: str = "default"
) -> None

# Receiving responses
async def receive_response() -> AsyncIterator[Message]
async def receive_messages() -> AsyncIterator[Message]  # All messages including system

# Runtime control
async def interrupt() -> None
async def set_permission_mode(mode: PermissionMode) -> None
async def set_model(model: str | None) -> None

# File operations
async def rewind_files(user_message_id: str) -> None

# MCP control
async def get_mcp_status() -> McpStatusResponse
async def reconnect_mcp_server(server_name: str) -> None
async def toggle_mcp_server(server_name: str, enabled: bool) -> None

# Server info
async def get_server_info() -> dict[str, Any] | None

# Task management
async def stop_task(task_id: str) -> None
```

**Usage:**
```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock

async def main():
    options = ClaudeAgentOptions(model="claude-opus-4-5")

    async with ClaudeSDKClient(options=options) as client:
        # First turn
        await client.query("Write a hello world function in Python")
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)

        # Second turn (continues the conversation)
        await client.query("Now add docstrings to that function")
        async for msg in client.receive_response():
            ...
```

---

## Configuration: `ClaudeAgentOptions`

```python
@dataclass
class ClaudeAgentOptions:
    # Tool configuration
    tools: list[str] | None = None              # Allowlist of tools
    allowed_tools: list[str] | None = None       # Auto-approve these tools
    disallowed_tools: list[str] | None = None    # Block these tools
    permission_mode: PermissionMode | None = None # "default"|"acceptEdits"|"plan"|"bypassPermissions"
    can_use_tool: ToolPermissionCallback | None = None  # Custom permission callback

    # Model control
    model: str | None = None                    # Model override (e.g., "claude-opus-4-6")
    fallback_model: str | None = None           # Fallback if primary unavailable
    thinking: ThinkingConfig | None = None      # Extended thinking settings
    effort: str | None = None                   # Reasoning effort level

    # MCP servers
    mcp_servers: dict[str, McpServerConfig | str] | None = None  # MCP server configs or paths

    # Hooks
    hooks: dict[str, list[HookMatcher]] | None = None  # Event hooks

    # Session management
    continue_conversation: bool = False         # Continue most recent session
    resume: str | None = None                   # Resume specific session by ID
    fork_session: bool = False                  # Fork session for isolation

    # Execution limits
    max_turns: int | None = None                # Maximum conversation turns
    max_budget_usd: float | None = None         # Cost limit in USD
    max_buffer_size: int | None = None          # Max stdout buffer (default: 1MB)

    # Working directories
    cwd: str | None = None                      # Working directory for Claude
    add_dirs: list[str] | None = None           # Additional allowed directories

    # Plugins
    plugins: list[str] | None = None            # Plugin names to enable

    # Sandbox
    sandbox: SandboxConfig | None = None        # Bash command isolation settings

    # Environment
    env: dict[str, str] | None = None           # Environment variables for CLI
    extra_args: list[str] | None = None         # Extra CLI arguments
    cli_path: str | None = None                 # Custom CLI binary path

    # Output
    output_format: OutputFormat | None = None   # Structured output schema
    system_prompt: str | None = None            # System prompt override
    append_system_prompt: str | None = None     # Append to system prompt

    # Persistence
    enable_file_checkpointing: bool = False     # Track file state for rewind

    # Subagents
    agents: list[AgentDefinition] | None = None # Custom subagent definitions
```

---

## Custom Tool Integration (MCP)

### `@tool` Decorator

```python
def tool(
    name: str,
    description: str,
    input_schema: dict[str, Any] | type,
) -> Callable[[ToolHandler], SdkMcpTool[Any]]
```

Marks a Python async function as a Claude-callable tool.

```python
from claude_agent_sdk import tool

@tool(
    name="get_weather",
    description="Get current weather for a city",
    input_schema={"city": str, "units": str}
)
async def get_weather(args: dict[str, Any]) -> dict[str, Any]:
    city = args["city"]
    units = args.get("units", "celsius")
    # ... fetch weather ...
    return {
        "content": [{"type": "text", "text": f"Weather in {city}: 22°{units[0].upper()}"}]
    }
```

### `create_sdk_mcp_server()`

```python
def create_sdk_mcp_server(
    name: str,
    version: str = "1.0.0",
    tools: list[SdkMcpTool[Any]] | None = None,
) -> McpSdkServerConfig
```

Creates an in-process MCP server configuration from a list of tools.

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeSDKClient, ClaudeAgentOptions

@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args):
    return {"content": [{"type": "text", "text": str(args["a"] + args["b"])}]}

@tool("multiply", "Multiply two numbers", {"a": float, "b": float})
async def multiply(args):
    return {"content": [{"type": "text", "text": str(args["a"] * args["b"])}]}

server = create_sdk_mcp_server("calculator", tools=[add, multiply])

options = ClaudeAgentOptions(
    mcp_servers={"calculator": server},
    allowed_tools=["mcp__calculator__add", "mcp__calculator__multiply"],
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("What is 15 * 8?")
    async for msg in client.receive_response():
        ...
```

---

## Hook System

### `HookMatcher`

```python
@dataclass
class HookMatcher:
    matcher: str | None = None        # Pattern to match (e.g., tool name)
    hooks: list[HookCallback] = ...   # Callback functions
    timeout: float | None = None      # Per-hook timeout in seconds
```

### Hook Callback Signature

```python
HookCallback = Callable[
    [HookInput, str | None, HookContext],
    Awaitable[HookJSONOutput]
]
```

Arguments:
- `HookInput` — TypedDict with `tool_name`, `tool_input`, `session_id`, `hook_event_name`, and event-specific fields
- `str | None` — tool_use_id (if applicable)
- `HookContext` — context with `session_id` and a `send_message()` helper

### Supported Hook Events

| Event | Trigger | Can Block? |
|---|---|---|
| `PreToolUse` | Before any tool call | Yes (deny/approve) |
| `PostToolUse` | After successful tool call | No |
| `PostToolUseFailure` | After failed tool call | No |
| `UserPromptSubmit` | When user submits a prompt | No |
| `Stop` | When session stops | No |
| `SubagentStop` | When subagent stops | No |
| `PreCompact` | Before context compaction | No |
| `Notification` | For notifications | No |
| `SubagentStart` | When subagent starts | No |
| `PermissionRequest` | On permission requests | Yes |

### Hook Usage Example

```python
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher

async def block_dangerous_commands(input_data, tool_use_id, context):
    command = input_data.get("tool_input", {}).get("command", "")
    if "rm -rf" in command or "sudo" in command:
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Dangerous command blocked by policy",
            }
        }
    return {}

async def log_tool_use(input_data, tool_use_id, context):
    print(f"Tool used: {input_data['tool_name']}")
    return {}

options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [HookMatcher(matcher="Bash", hooks=[block_dangerous_commands])],
        "PostToolUse": [HookMatcher(hooks=[log_tool_use])],
    }
)
```

---

## Message Types

All messages yielded by `query()` and `receive_response()` are typed dataclass instances:

```python
@dataclass
class AssistantMessage:
    content: list[TextBlock | ThinkingBlock | ToolUseBlock]
    message_id: str | None = None

@dataclass
class UserMessage:
    content: list[ToolResultBlock | TextBlock]

@dataclass
class SystemMessage:
    content: str

@dataclass
class ResultMessage:
    subtype: str              # "success" | "error"
    cost_usd: float | None
    duration_ms: int | None
    session_id: str | None
    stop_reason: str | None
    usage: UsageInfo | None

@dataclass
class StreamEvent:            # Partial streaming (fine-grained)
    event_type: str           # "text_delta" | "input_json_delta" | etc.
    data: dict[str, Any]

@dataclass
class RateLimitEvent:
    status: str               # "allowed" | "allowed_warning" | "rejected"
    window_type: str          # "5h" | "7d" | "overage"

@dataclass
class TaskStartedMessage:
    task_id: str
    description: str | None

@dataclass
class TaskProgressMessage:
    task_id: str
    progress: float | None
    message: str | None

@dataclass
class TaskNotificationMessage:
    task_id: str
    notification: str
```

### Content Block Types

```python
@dataclass
class TextBlock:
    text: str

@dataclass
class ThinkingBlock:
    thinking: str

@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]

@dataclass
class ToolResultBlock:
    tool_use_id: str
    content: str | list[dict[str, Any]]
    is_error: bool = False
```

---

## Session Management

```python
from claude_agent_sdk import list_sessions, get_session_messages, rename_session, tag_session

# List all sessions
sessions: list[SDKSessionInfo] = await list_sessions()
for s in sessions:
    print(s.session_id, s.title, s.created_at)

# Get messages in a session
messages: list[SessionMessage] = await get_session_messages(session_id)

# Rename a session
await rename_session(session_id, "My Refactoring Session")

# Tag a session
await tag_session(session_id, ["refactor", "backend", "urgent"])
```

---

## Error Handling

```python
from claude_agent_sdk import (
    ClaudeSDKError,
    CLIConnectionError,
    CLINotFoundError,
    ProcessError,
    CLIJSONDecodeError,
    MessageParseError,
)

try:
    async for msg in query("Hello"):
        ...
except CLINotFoundError:
    print("Claude Code CLI not found — install it or set cli_path")
except CLIConnectionError as e:
    print(f"Failed to connect: {e}")
except ProcessError as e:
    print(f"CLI process failed with exit code {e.exit_code}")
except ClaudeSDKError as e:
    print(f"SDK error: {e}")
```

---

## Integration Patterns

### Permission Callback Pattern

```python
from claude_agent_sdk import ClaudeAgentOptions

async def my_permission_check(tool_name: str, tool_input: dict) -> bool:
    # Block file writes outside the project directory
    if tool_name == "Write":
        path = tool_input.get("file_path", "")
        return path.startswith("/my/project/")
    return True

options = ClaudeAgentOptions(can_use_tool=my_permission_check)
```

### Structured Output Pattern

```python
from claude_agent_sdk import ClaudeAgentOptions, OutputFormat

schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "issues": {"type": "array", "items": {"type": "string"}},
        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
    },
    "required": ["summary", "issues", "severity"],
}

options = ClaudeAgentOptions(output_format=OutputFormat(schema=schema))

async for msg in query("Review this code for security issues: ...", options=options):
    if isinstance(msg, ResultMessage) and msg.structured_output:
        result = msg.structured_output
        print(f"Severity: {result['severity']}")
```

### Sandboxed Bash Execution

```python
from claude_agent_sdk import ClaudeAgentOptions, SandboxConfig

options = ClaudeAgentOptions(
    sandbox=SandboxConfig(
        network_access=False,          # Block network access
        allowed_paths=["/tmp", "/workspace"],  # Restrict filesystem
    )
)
```

### Partial Streaming Pattern

```python
from claude_agent_sdk import query, ClaudeAgentOptions, StreamEvent

options = ClaudeAgentOptions(enable_partial_messages=True)

async for msg in query("Write a long essay about Python", options=options):
    if isinstance(msg, StreamEvent):
        if msg.event_type == "text_delta":
            print(msg.data.get("text", ""), end="", flush=True)
```
