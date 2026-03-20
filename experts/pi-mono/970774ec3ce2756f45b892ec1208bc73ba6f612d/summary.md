# Pi Monorepo — Summary

## Repository Purpose and Goals

Pi Monorepo (`pi-mono`, GitHub: `badlogic/pi-mono`) is a TypeScript monorepo providing a complete toolkit for building AI coding agents and managing LLM deployments. The project's stated philosophy is aggressive extensibility: keep the core minimal, ship powerful defaults, and let developers shape the tools to match their workflows rather than the other way around.

The central product is **pi** — a minimal terminal coding harness that lets users drive LLMs to read, write, edit, and execute code in a working directory. Unlike Claude Code or similar tools, pi ships without sub-agents, plan mode, permission popups, or MCP, deliberately leaving those as extension points for users to implement exactly how they want.

## Key Features and Capabilities

- **Multi-provider LLM API** (`@mariozechner/pi-ai`): A unified streaming API that normalises 20+ LLM providers (OpenAI, Anthropic, Google, Mistral, Bedrock, xAI, Groq, Cerebras, GitHub Copilot, Gemini CLI, Antigravity, and more) behind a single `stream()`/`complete()` interface. Includes OAuth support, cross-provider context handoffs, token/cost tracking, TypeBox-based tool schema validation, and partial-JSON streaming for tool arguments.

- **Agent runtime** (`@mariozechner/pi-agent-core`): A stateful `Agent` class built on pi-ai that handles the full agentic loop: tool execution (parallel or sequential), steering messages, follow-up queuing, `beforeToolCall`/`afterToolCall` hooks, custom message types via declaration merging, and a low-level `agentLoop()` generator for direct control.

- **Coding agent CLI** (`@mariozechner/pi-coding-agent`): The `pi` CLI binary. Runs in four modes: interactive TUI, print/non-interactive, JSON event stream, and RPC (stdin/stdout JSONL). Supports sessions with in-place branching, compaction, session tree navigation, fork, and export-to-HTML. Extensible via TypeScript extensions, skills (markdown instructions), prompt templates, themes, and pi packages (distributable via npm/git).

- **Extension system**: A rich event-driven API (`ExtensionAPI`) exposing 30+ typed events (`session_start`, `before_agent_start`, `tool_call`, `tool_result`, `context`, `model_select`, etc.), tool registration with TypeBox schemas, custom commands/shortcuts/CLI flags, UI primitives (select, confirm, input, notify, custom overlays, widgets, custom editor), and provider/model registration at runtime.

- **Terminal UI library** (`@mariozechner/pi-tui`): Component-based TUI framework with differential rendering, synchronized output (CSI 2026), inline image support (Kitty/iTerm2 protocols), overlay system, and built-in components: Text, Editor, Input, Markdown, SelectList, SettingsList, Loader, Image, Box, Container.

- **Slack bot** (`@mariozechner/pi-mom`): A self-managing Slack bot that delegates messages to the pi coding agent. Supports Docker sandboxing, per-channel memory (MEMORY.md), custom skills, scheduled events (cron/one-shot/immediate), and artifact sharing.

- **GPU pod management** (`@mariozechner/pi-pods`): CLI (`pi`) for setting up vLLM on remote GPU pods (DataCrunch, RunPod, Vast.ai), managing model deployments, and exposing OpenAI-compatible endpoints. Includes a standalone `pi-agent` chat CLI for testing deployed models.

- **Web UI** (`@mariozechner/pi-web-ui`): Web components for embedding AI chat interfaces in web applications.

## Primary Use Cases and Target Audience

- Developers who want a highly customisable AI coding assistant without forking a monolithic codebase
- Teams building custom coding agent workflows (sub-agents, plan mode, permission gates, git checkpointing) as extensions
- Developers integrating LLMs into their own applications via the SDK or RPC modes
- ML engineers deploying open-source models (Qwen, GLM, GPT-OSS) on GPU pods and testing them with an agent interface
- Teams who want a Slack-integrated AI assistant that self-manages its own tooling

## High-Level Architecture Overview

The monorepo follows a layered dependency graph:

```
pi-tui              (terminal rendering primitives)
pi-ai               (LLM provider abstraction + streaming)
pi-agent-core       (agent loop, tool execution, state)
pi-coding-agent     (CLI, sessions, extensions, tools, modes)
pi-mom              (Slack bot built on pi-coding-agent)
pi-pods             (GPU pod management, standalone)
pi-web-ui           (browser components, standalone)
```

The build order is: tui → ai → agent → coding-agent → mom → web-ui → pods.

`pi-coding-agent` exposes a public SDK (`createAgentSession`) and an RPC mode that speak to the agent layer. The extension system sits inside coding-agent and provides a safe, typed surface for third-party code to hook into every lifecycle event.

## Related Projects and Dependencies

- **TypeBox** (`@sinclair/typebox`): Used throughout for JSON schema definition and validation of tool parameters
- **Biome**: Linting and formatting (replaces ESLint + Prettier)
- **TypeScript native preview** (`@typescript/native-preview`, `tsgo`): Used for compilation
- **Vitest**: Test runner for all packages
- **Husky**: Git hooks (pre-commit checks)
- **concurrently**: Parallel dev-mode watch across packages
- **chalk**: Terminal colours in pi-coding-agent and pi-tui
- **marked**: Markdown parsing in pi-tui's Markdown component
- **jiti** (`@mariozechner/jiti`): TypeScript extension loading at runtime
- **undici**: HTTP client used in pi-coding-agent
- **yaml**: YAML parsing (session/config files)
- **photon-node** (`@silvia-odwyer/photon-node`): Image processing (resize, EXIF orientation) for clipboard image handling
- External: openclaw/openclaw is cited as a real-world SDK integration example
