# Claude Code — Repository Summary

## Repository Purpose and Goals

Claude Code is Anthropic's official agentic coding tool that lives in the terminal, understands codebases, and helps developers code faster through natural language commands. It bridges conversational AI with practical software engineering workflows: executing routine tasks, explaining complex code, handling git operations, reviewing pull requests, and integrating with IDEs and GitHub Actions — all without leaving the terminal.

The repository (`anthropics/claude-code`) is primarily a **reference and extension repository**, not the source code for the Claude Code binary itself (which is closed-source and distributed via npm, Homebrew, and official installers). The repo contains:

- Official plugin examples and a bundled plugin marketplace
- Example hooks, settings, and MDM deployment templates
- GitHub Actions workflows that automate issue triage and deduplication using Claude Code itself
- A devcontainer configuration for sandboxed development environments
- Project-level slash commands used internally by Anthropic for this repository

## Key Features and Capabilities

**Core Claude Code tool (distributed externally):**
- Terminal-native interactive REPL with full codebase context
- Slash commands for common workflows (commit, review, explore)
- Plugin system with custom slash commands, agents, skills, and hooks
- MCP (Model Context Protocol) server integration for external tools
- Sandboxed Bash execution with configurable permission rules
- Enterprise-grade settings hierarchy (user → project → enterprise managed)
- VS Code, JetBrains, and GitHub integrations
- Session persistence, worktree support, and subagent orchestration
- Voice input (push-to-talk), focus mode, and brief mode
- OAuth and API key authentication; AWS Bedrock and Google Vertex AI support

**This repository specifically provides:**
- 13 official plugins covering development workflows, code review, security, git automation, and learning modes
- Example hook scripts (Python-based PreToolUse validators)
- Example settings JSON files for lax, strict, and sandboxed enterprise configurations
- MDM deployment templates (Jamf, Kandji, Intune, Group Policy, ADMX)
- DevContainer with hardened network firewall (iptables/ipset) for sandboxed AI coding
- GitHub Actions automation: issue triage, duplicate detection, lifecycle management

## Primary Use Cases and Target Audience

**Target audience:** Software developers (individual and enterprise) using the terminal for day-to-day coding, along with DevOps and security teams deploying Claude Code across organizations.

**Primary use cases:**
- AI-assisted coding, refactoring, debugging, and code explanation in the terminal
- Automated PR review with multi-agent confidence scoring
- Git workflow automation (commit, push, PR creation, branch cleanup)
- Feature development with structured 7-phase exploration/design/implementation workflow
- Plugin development and customization
- Enterprise deployment with managed settings and MDM integration
- Self-hosted GitHub automation (issue triage, deduplication, lifecycle management)

## High-Level Architecture Overview

The repository is organized around three main concerns:

1. **Plugin system** (`plugins/`): Each plugin is a self-contained directory with a `plugin.json` manifest, optional `commands/`, `agents/`, `skills/`, `hooks/`, and `.mcp.json`. Plugins are discovered from a marketplace registry (`.claude-plugin/marketplace.json`).

2. **Examples** (`examples/`): Standalone reference implementations for hooks (Python scripts) and settings (JSON configurations for various permission levels), plus MDM deployment templates.

3. **Repository automation** (`.github/workflows/`, `scripts/`, `.claude/commands/`): GitHub Actions workflows that use Claude Code itself (via `anthropics/claude-code-action@v1`) for issue triage, deduplication, and lifecycle management.

The hooks system is central to extension: hooks are external processes that receive JSON on stdin and communicate back via exit codes (0 = allow, 1 = show stderr to user, 2 = block tool and show stderr to Claude). Hook events include `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `PreCompact`, and `Notification`.

## Related Projects and Dependencies

- **`anthropics/claude-code-action`**: GitHub Action that wraps Claude Code for CI/CD automation
- **`@anthropic-ai/claude-code`**: npm package (deprecated install method, still functional)
- **`@anthropic-ai/sdk`**: Underlying Anthropic API client
- **Model Context Protocol (MCP)**: Standard for connecting Claude Code to external tools via stdio/SSE/HTTP
- **GitHub CLI (`gh`)**: Required for PR creation and GitHub operations in many plugins
- **Python 3.7+**: Required for hook scripts
- **Node.js 18+**: Runtime requirement for Claude Code
