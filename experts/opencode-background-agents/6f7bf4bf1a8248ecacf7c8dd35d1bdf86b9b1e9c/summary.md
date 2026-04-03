# OpenCode Background Agents Plugin - Repository Summary

## Repository Purpose and Goals

The opencode-background-agents repository provides an async background delegation system for [OpenCode](https://github.com/sst/opencode), an AI-powered coding assistant. The core purpose is to solve the context window limitation problem that occurs during extended AI conversations, where important research and analysis can be lost when context compaction occurs.

This plugin implements a "waiter model" approach to task delegation - similar to how you don't follow a waiter to the kitchen but receive notification when your order is ready. Users can fire off research tasks to specialized agents and continue productive work while tasks run in isolated background sessions. Results are persisted to disk and survive context compaction, session restarts, and process crashes.

## Key Features and Capabilities

### Async Background Delegation
- **Non-blocking task delegation**: Launch research tasks and continue working without waiting
- **Persistent results**: All delegation outputs are saved to disk as markdown files with generated titles and descriptions
- **Context survival**: Results survive context compaction, session restarts, and crashes
- **Intelligent routing**: Automatically routes read-only agents to background sessions while preserving write-capable agents in the main session tree for proper undo/branching support

### Agent Safety and Validation
- **Read-only enforcement**: Only read-only agents (researcher, explore) can use background delegation to prevent data corruption from isolated write operations
- **Agent capability detection**: Automatically parses agent configurations to determine write capabilities and enforce appropriate tool usage
- **Permission-based routing**: Uses OpenCode's permission system to classify agents and route them to appropriate execution contexts

### Notification and Progress Tracking
- **Batched notifications**: Provides progress updates and completion notifications without overwhelming the user
- **Generated metadata**: Uses small language models to generate meaningful titles and descriptions for completed delegations
- **Status tracking**: Monitors delegation progress with timeout handling (15-minute limit)

### Storage and Retrieval
- **Project-scoped storage**: Uses git repository root commit hash for stable, cross-worktree storage directories
- **Searchable delegation history**: All delegations are tagged with auto-generated titles and descriptions for easy discovery
- **Markdown format**: Results are stored in a structured markdown format with metadata headers

## Primary Use Cases and Target Audience

### Target Users
- **AI coding assistants**: Developers using OpenCode for complex software engineering tasks
- **Research-heavy workflows**: Users who need to maintain context across extensive research sessions
- **Parallel task management**: Developers who want to delegate research while continuing to code or design

### Common Use Cases
- **Background research**: "Research OAuth2 PKCE best practices" while continuing to implement authentication
- **Codebase exploration**: "Find all API endpoints in the project" while working on documentation
- **Parallel analysis**: Launch multiple research tasks simultaneously and retrieve results as needed
- **Context preservation**: Maintain access to research results across session boundaries and context compactions

## High-Level Architecture Overview

### Core Components
1. **DelegationManager**: Central orchestrator managing the lifecycle of background tasks, from creation through completion and cleanup
2. **Agent Capability Detection**: System for parsing OpenCode agent configurations to determine read/write permissions and enforce appropriate tool usage
3. **Storage System**: Project-scoped file storage using git repository identity for cross-worktree consistency
4. **Notification System**: Batched progress updates and completion notifications integrated with OpenCode's session system

### Tool Interface
The plugin exposes three primary tools:
- `delegate(prompt, agent)`: Launch background tasks with immediate ID return
- `delegation_read(id)`: Retrieve completed results by readable ID
- `delegation_list()`: List all delegations with titles and status

### Integration Points
- **Hook System**: Integrates with OpenCode's experimental hooks for system prompt injection, compaction context, and tool execution interception
- **Event Handling**: Responds to session lifecycle events (idle, message updates) for delegation state management
- **Permission Integration**: Works with OpenCode's agent permission system to enforce tool usage constraints

### Storage Architecture
- **Project Identity**: Uses git root commit hash for stable project identification across renames and worktrees
- **Session Scoping**: Organizes delegations by root session ID for proper isolation and retrieval
- **Persistent Metadata**: Each delegation stored with generated title, description, status, and full result content

## Related Projects and Dependencies

### Core Dependencies
- **@opencode-ai/plugin**: OpenCode plugin API for tool creation and hook integration
- **@opencode-ai/sdk**: OpenCode SDK for client interactions and type definitions
- **unique-names-generator**: Human-readable ID generation for delegations (e.g., "swift-amber-falcon")

### Related Ecosystem
- **OCX (OpenCode Extension Manager)**: Package manager for OpenCode plugins, used for installation and distribution
- **KDCO Registry**: Plugin registry system that hosts and distributes this plugin alongside other productivity tools
- **kdco-workspace**: Comprehensive workspace bundle that includes background agents with specialist agents and planning tools

### Plugin Architecture
The plugin is structured as part of the kdco-primitives ecosystem, sharing common utilities for:
- Project identification and git repository handling
- Cross-platform shell command escaping
- Timeout management and promise utilities
- Logging integration with OpenCode's log panel
- Terminal detection and environment handling

### Installation and Distribution
Distributed through the KDCO Registry via OCX package manager, enabling one-command installation with automatic dependency management and registry-backed updates. Can also be manually installed by copying source files, though this requires manual dependency management.

The plugin represents a sophisticated solution to the fundamental challenge of maintaining context and enabling parallel work in AI-assisted development workflows, providing both immediate productivity benefits and long-term session resilience.
