# Claude Code — APIs and Interfaces

## Slash Command API

Slash commands are Markdown files with YAML frontmatter. They are discovered automatically from `commands/` directories within plugins or from `.claude/commands/` in the project root.

### Command File Structure

```markdown
---
description: Short description shown in the command picker
allowed-tools: Bash(git status:*), Bash(gh pr create:*), Read, Grep
argument-hint: "[optional argument hint shown to user]"
---

# Optional heading

Body is the system prompt sent to Claude when the command is invoked.

Dynamic context injection:
- Current git status: !`git status`
- Current branch: !`git branch --show-current`

$ARGUMENTS is replaced with any text the user typed after /command-name.
```

### Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Displayed in command picker |
| `allowed-tools` | string | Comma-separated tool allowlist (supports glob patterns like `Bash(git *:*)`) |
| `argument-hint` | string | Hint text shown in picker for expected arguments |

### Dynamic Bash Injection

Use `!`bash command`` syntax to inject real-time output at command execution time:

```markdown
## Context
- Status: !`git status`
- Diff: !`git diff HEAD`
- Branch: !`git branch --show-current`
```

### Arguments

`$ARGUMENTS` is replaced with any text passed after the slash command:
```markdown
/triage-issue REPO: owner/repo ISSUE_NUMBER: 123 EVENT: issues
```

## Agent Definition API

Agents are Markdown files with YAML frontmatter in `agents/` directories.

### Agent File Structure

```markdown
---
name: agent-name
description: |
  When to use this agent. Use <example> blocks for reliable triggering:
  <example>
  User: "Verify my Python SDK application"
  assistant: [uses agent-sdk-verifier-py]
  </example>
model: claude-sonnet-4-5-20250929
color: purple
tools:
  - Bash
  - Read
  - Glob
  - Grep
  - Write
---

# Agent system prompt

Full instructions for the agent's behavior, focus areas, and output format.
```

### Agent Frontmatter Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Agent identifier (used for invocation) |
| `description` | string | When Claude should invoke this agent; `<example>` blocks improve trigger reliability |
| `model` | string | Claude model to use (e.g., `claude-sonnet-4-5-20250929`) |
| `color` | string | Display color in the UI |
| `tools` | array | Tools available to this agent |

## Hook System API

Hooks are external processes that intercept Claude Code tool calls. They receive JSON on stdin and communicate via exit codes.

### Hook Registration (`hooks.json`)

```json
{
  "description": "Human-readable hook description",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/my_hook.py"
          }
        ]
      }
    ]
  }
}
```

### Hook Events

| Event | When | Common Uses |
|-------|------|-------------|
| `PreToolUse` | Before any tool call | Validate, block, or warn about tool use |
| `PostToolUse` | After a tool call completes | Log, audit, post-process |
| `Stop` | When Claude wants to end the session | Enforce completion criteria, loop back |
| `SubagentStop` | When a subagent finishes | Inter-agent communication |
| `SessionStart` | At the beginning of a session | Inject context, set up environment |
| `SessionEnd` | When session ends | Cleanup, logging |
| `UserPromptSubmit` | When user submits a prompt | Validate or augment user input |
| `PreCompact` | Before context compaction | Preserve important context |
| `Notification` | System notifications | Custom notification handling |

### Hook Input JSON (stdin)

```json
{
  "session_id": "abc123",
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/path/to/file.py",
    "old_string": "old code",
    "new_string": "new code"
  }
}
```

### Hook Output Protocol (exit codes)

| Exit Code | Meaning |
|-----------|---------|
| `0` | Allow the tool call to proceed |
| `1` | Show stderr content to the **user** only (not Claude); allow the tool call |
| `2` | **Block** the tool call; show stderr content to **Claude** as feedback |

### Example Hook: Bash Command Validator

```python
#!/usr/bin/env python3
import json, re, sys

RULES = [
    (r"^grep\b(?!.*\|)", "Use 'rg' instead of 'grep'"),
]

def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") != "Bash":
        sys.exit(0)
    command = data.get("tool_input", {}).get("command", "")
    for pattern, message in RULES:
        if re.search(pattern, command):
            print(message, file=sys.stderr)
            sys.exit(2)  # Block with feedback to Claude
    sys.exit(0)

if __name__ == "__main__":
    main()
```
Source: `examples/hooks/bash_command_validator_example.py`

### Example Hook: Security Pattern Detection

The security-guidance plugin's `security_reminder_hook.py` demonstrates:
- Pattern detection across 9 security concerns (command injection, XSS, eval, pickle, etc.)
- Session-scoped state to avoid repeat warnings (`~/.claude/security_warnings_state_<session_id>.json`)
- Path-based and content-based pattern matching
- 30-day cleanup of stale state files

Key pattern types from `plugins/security-guidance/hooks/security_reminder_hook.py:31`:
- `path_check`: Lambda that evaluates the file path (e.g., `.github/workflows/*.yml`)
- `substrings`: List of strings to find in the file content (e.g., `["eval(", "exec("]`)

## Skill API

Skills provide auto-loading context and guidance. They use progressive disclosure.

### Skill File Structure (SKILL.md)

```markdown
---
description: |
  Trigger phrases: "create a hook", "add a PreToolUse hook"
  This skill should be used when [conditions].
context: fork
---

# Core skill content

Essential reference material (~1,500-2,000 words). Links to:
- [Detailed Reference](./resources/references/detailed-guide.md)
- [Working Examples](./resources/examples/example.py)
```

### Frontmatter Fields

| Field | Type | Values |
|-------|------|--------|
| `description` | string | Trigger phrases and activation conditions |
| `context` | string | `fork` (new context) or `inline` (injected inline) |
| `agent` | string | Optional: agent to invoke alongside skill |

## Plugin Manifest API (`plugin.json`)

```json
{
  "name": "plugin-name",
  "description": "Human-readable description",
  "version": "1.0.0",
  "author": {
    "name": "Author Name",
    "email": "author@example.com"
  }
}
```

## Marketplace Registry (`.claude-plugin/marketplace.json`)

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "marketplace-name",
  "version": "1.0.0",
  "description": "Marketplace description",
  "owner": {"name": "Anthropic", "email": "support@anthropic.com"},
  "plugins": [
    {
      "name": "plugin-name",
      "description": "Plugin description",
      "source": "./plugins/plugin-name",
      "category": "development|productivity|security|learning"
    }
  ]
}
```

Source: `.claude-plugin/marketplace.json`

## Settings API

### Settings Hierarchy (lowest to highest priority)
1. User settings: `~/.claude/settings.json`
2. Project settings: `.claude/settings.json`
3. Project local: `.claude/settings.local.json`
4. Enterprise/MDM managed: system-level `managed-settings.json`

### Key Settings Fields

```json
{
  "permissions": {
    "disableBypassPermissionsMode": "disable",
    "ask": ["Bash"],
    "deny": ["WebSearch", "WebFetch"],
    "allow": ["Read", "Grep"],
    "additionalDirectories": ["/path/to/extra/dir"]
  },
  "allowManagedPermissionRulesOnly": true,
  "allowManagedHooksOnly": true,
  "strictKnownMarketplaces": [],
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": false,
    "allowUnsandboxedCommands": false,
    "excludedCommands": [],
    "network": {
      "allowUnixSockets": [],
      "allowAllUnixSockets": false,
      "allowLocalBinding": false,
      "allowedDomains": [],
      "httpProxyPort": null,
      "socksProxyPort": null
    },
    "enableWeakerNestedSandbox": false
  }
}
```

Source: `examples/settings/settings-strict.json`, `examples/settings/settings-bash-sandbox.json`

### Permission Rules Syntax

```json
{
  "permissions": {
    "allow": [
      "Bash(git status:*)",         // Allow git status and any subcommands
      "Bash(git commit *)",          // Allow git commit with any flags
      "Read(/path/to/file.txt)"      // Allow reading specific file
    ],
    "deny": [
      "WebFetch",                    // Block all web fetch
      "Bash(rm -rf *)"               // Block dangerous rm
    ],
    "ask": [
      "Bash"                         // Require approval for all Bash
    ]
  }
}
```

## GitHub Actions Integration (`claude-code-action@v1`)

```yaml
- uses: anthropics/claude-code-action@v1
  with:
    anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    claude_args: "--model claude-opus-4-6"
    github_token: ${{ secrets.GITHUB_TOKEN }}
    allowed_non_write_users: "*"
    prompt: "/triage-issue REPO: ${{ github.repository }} ISSUE_NUMBER: ${{ github.event.issue.number }}"
  env:
    GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    CLAUDE_CODE_SCRIPT_CAPS: '{"edit-issue-labels.sh":2}'
```

### Key Action Inputs

| Input | Description |
|-------|-------------|
| `anthropic_api_key` | Anthropic API key |
| `claude_args` | Additional CLI arguments (e.g., `--model`) |
| `github_token` | GitHub token for repo access |
| `allowed_non_write_users` | `"*"` allows anyone to trigger |
| `prompt` | The slash command or instruction to run |

### Key Environment Variables

| Variable | Description |
|----------|-------------|
| `CLAUDE_CODE_SCRIPT_CAPS` | JSON map: script name → max invocations |
| `GH_TOKEN` | GitHub token used by `gh` CLI inside Claude |
| `CLAUDE_CONFIG_DIR` | Override config directory location |
| `ENABLE_SECURITY_REMINDER` | `"0"` disables security hook (default: `"1"`) |
| `ANTHROPIC_AUTH_TOKEN` | Alternative API key env var |
| `API_TIMEOUT_MS` | Override default request timeout |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` | Enable PID namespace isolation on Linux |
| `CLAUDE_CODE_SCRIPT_CAPS` | Per-script invocation limits |
| `CLAUDE_CODE_PERFORCE_MODE` | Fail on read-only files with p4 edit hint |
| `CLAUDE_CODE_CERT_STORE` | `"bundled"` to use only bundled CA certs |
| `OTEL_LOG_USER_PROMPTS` | Enable user prompt logging in OTEL traces |

## Hookify Rule Format

The hookify plugin provides a no-code rule format for creating hooks:

```markdown
---
name: block-dangerous-rm
enabled: true
event: bash          # bash | file | stop | prompt | all
pattern: rm\s+-rf    # Simple regex (single condition)
action: block        # block | warn
---

Message shown when rule triggers. Supports **markdown**.
```

Multi-condition rules:
```markdown
---
name: api-key-in-typescript
enabled: true
event: file
action: warn
conditions:
  - field: file_path         # file_path | new_text | old_text | content | command | user_prompt
    operator: regex_match    # regex_match | contains | equals | not_contains | starts_with | ends_with
    pattern: \.tsx?$
  - field: new_text
    operator: regex_match
    pattern: (API_KEY|SECRET)\s*=\s*["']
---

Warning message body here.
```

Source: `plugins/hookify/README.md`

## Integration Patterns

### Parallel Agent Orchestration

Commands spawn multiple agents simultaneously using natural language:

```markdown
# In a command file
Launch 4 parallel agents to review the pull request:
- Agent 1: Check CLAUDE.md compliance
- Agent 2: Detect bugs introduced in this PR
- Agent 3: Analyze git history for context
- Agent 4: Review test coverage
```

Score and filter results: "Only report issues with confidence ≥ 80."

### Session State in Hooks

```python
# Pattern from security_reminder_hook.py
session_id = input_data.get("session_id", "default")
state_file = os.path.expanduser(f"~/.claude/my_state_{session_id}.json")

# Load state
if os.path.exists(state_file):
    with open(state_file) as f:
        state = json.load(f)

# Save state
with open(state_file, "w") as f:
    json.dump(state, f)
```

Source: `plugins/security-guidance/hooks/security_reminder_hook.py:129-180`

### Portable Plugin Paths

Always use `${CLAUDE_PLUGIN_ROOT}` in `hooks.json` to reference plugin files:

```json
{
  "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/my_hook.py"
}
```

This ensures the hook works regardless of where the plugin is installed.
