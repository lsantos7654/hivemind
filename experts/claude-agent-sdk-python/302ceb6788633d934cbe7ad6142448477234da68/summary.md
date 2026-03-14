# Claude Agent SDK for Python — Summary

## Repository Purpose and Goals

The Claude Agent SDK for Python (`claude-agent-sdk`) is Anthropic's official Python library for building applications that interact with Claude Code, their AI-powered code assistant. The SDK enables developers to programmatically query Claude Code for coding assistance, file operations, and agentic task execution—either as simple one-shot queries or as multi-turn interactive conversations.

The primary goal is to provide a high-level, Pythonic interface that abstracts away the complexity of the underlying Claude Code CLI subprocess management, JSON control protocol, message streaming, and tool integration, letting developers focus on building intelligent coding assistants and automation workflows.

## Key Features and Capabilities

**Two Interaction Modes:**
- `query()` — Simple async generator for stateless, one-shot interactions
- `ClaudeSDKClient` — Bidirectional, stateful client for multi-turn conversations with full runtime control

**Custom Tool Integration via MCP:**
- In-process MCP (Model Context Protocol) server support
- `@tool` decorator for defining Python functions as Claude-callable tools
- `create_sdk_mcp_server()` for composing tool servers
- No subprocess overhead—tools execute directly in-process

**Hooks System:**
- Event-driven interception of agent behavior
- Events: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `UserPromptSubmit`, `Stop`, `SubagentStop`, `PreCompact`, `Notification`, `SubagentStart`, `PermissionRequest`
- Typed hook inputs and outputs with per-event semantics

**Permission and Security Model:**
- Four permission modes: `default`, `acceptEdits`, `plan`, `bypassPermissions`
- Tool allowlisting (`allowed_tools`) and denylisting (`disallowed_tools`)
- Custom permission callbacks (`can_use_tool`)
- Sandbox configuration for bash command isolation (network/filesystem restrictions)

**Advanced Features:**
- Extended thinking/reasoning (`ThinkingConfig`)
- Structured output support
- File checkpointing and state rewind
- Session management (list, rename, tag)
- Model switching during conversation
- MCP server runtime control (reconnect, toggle)
- Task management and interrupt support
- Partial message streaming
- Rate limit tracking and events
- Subagent definitions and spawning

## Primary Use Cases and Target Audience

**Target Audience:** Python developers building AI-powered coding tools, automation pipelines, and developer productivity applications on top of Claude Code.

**Primary Use Cases:**
1. **Automated Code Review** — Query Claude to analyze, refactor, or review code files
2. **AI-Assisted Development** — Build interactive coding assistants with custom tools
3. **CI/CD Integration** — Run code generation or analysis tasks in pipelines
4. **Custom Agentic Workflows** — Chain multiple Claude operations with hooks and permissions
5. **IDE Plugin Backends** — Power coding assistant features in editors
6. **Testing and QA Automation** — Use Claude to generate tests or validate implementations

## High-Level Architecture Overview

The SDK is structured around a clean layered architecture:

```
User Code (query() / ClaudeSDKClient)
        ↓
Internal Client (_internal/client.py)
        ↓
Control Protocol (_internal/query.py)
        ↓
Transport Layer (_internal/transport/subprocess_cli.py)
        ↓
Claude Code CLI (bundled binary)
        ↓
Anthropic API
```

The **Transport Layer** manages the subprocess lifecycle, stdin/stdout communication, and buffering. The **Control Protocol** implements a JSON-RPC style messaging schema over stdio. The **Internal Client** orchestrates message parsing, hook delivery, MCP routing, and permission callbacks. The two public interfaces (`query()` and `ClaudeSDKClient`) wrap this internals with ergonomic async Python APIs.

The SDK bundles the Claude Code CLI binary directly in the wheel package, eliminating external installation requirements. The CLI is detected first as the bundled binary, then falls back to system PATH and common install locations.

## Related Projects and Dependencies

**Core Runtime Dependencies:**
- `anyio >= 4.0.0` — Platform-agnostic async I/O (supports both asyncio and trio backends)
- `mcp >= 0.1.0` — Model Context Protocol implementation for tool integration
- `typing_extensions >= 4.0.0` — Backported typing utilities for Python < 3.11

**Related Anthropic Projects:**
- **Claude Code CLI** — The underlying AI coding assistant that this SDK wraps
- **Anthropic Python SDK** — Lower-level API client for direct model access (separate project)
- **MCP (Model Context Protocol)** — Open protocol for tool/resource integration

**Platform Support:**
- Python 3.10+
- Linux (x86_64, aarch64)
- macOS (arm64, x86_64)
- Windows (amd64)
