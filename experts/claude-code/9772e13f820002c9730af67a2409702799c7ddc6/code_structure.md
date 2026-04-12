# Claude Code — Code Structure

## Annotated Directory Tree

```
claude-code/                            # Repository root
├── README.md                           # Project overview, install instructions, badge
├── CHANGELOG.md                        # Full version history (2,937+ lines, extensive)
├── LICENSE.md                          # License
├── SECURITY.md                         # Security policy and disclosure
├── demo.gif                            # Animated demo shown in README
│
├── .claude/                            # Project-level Claude Code configuration
│   └── commands/                       # Project slash commands (auto-loaded for this repo)
│       ├── commit-push-pr.md           # /commit-push-pr: commit + push + open PR
│       ├── dedupe.md                   # /dedupe: find duplicate GitHub issues
│       └── triage-issue.md             # /triage-issue: apply GitHub labels to issues
│
├── .claude-plugin/                     # Plugin marketplace metadata
│   └── marketplace.json                # Registry of all bundled plugins (13 entries)
│
├── plugins/                            # Official bundled plugins
│   ├── README.md                       # Plugin system overview, structure reference
│   ├── agent-sdk-dev/                  # Agent SDK project scaffolding + verification
│   │   ├── .claude-plugin/plugin.json  # Plugin manifest
│   │   ├── agents/                     # agent-sdk-verifier-py, agent-sdk-verifier-ts
│   │   └── commands/                   # /new-sdk-app interactive scaffold command
│   │
│   ├── claude-opus-4-5-migration/      # Automated migration from older model strings
│   │   └── skills/                     # claude-opus-4-5-migration skill
│   │
│   ├── code-review/                    # Multi-agent PR code review with confidence scoring
│   │   ├── .claude-plugin/             # Plugin manifest
│   │   └── commands/                   # /code-review command (5 parallel agents)
│   │
│   ├── commit-commands/                # Git workflow automation
│   │   ├── .claude-plugin/             # Plugin manifest
│   │   └── commands/
│   │       ├── commit.md               # /commit: auto-message commit
│   │       ├── commit-push-pr.md       # /commit-push-pr: full workflow
│   │       └── clean_gone.md           # /clean_gone: remove stale local branches
│   │
│   ├── explanatory-output-style/       # Educational insights via SessionStart hook
│   │   └── hooks/                      # SessionStart hook injects context
│   │
│   ├── feature-dev/                    # 7-phase structured feature development
│   │   ├── .claude-plugin/             # Plugin manifest
│   │   ├── agents/                     # code-explorer, code-architect, code-reviewer
│   │   └── commands/                   # /feature-dev orchestrator command
│   │
│   ├── frontend-design/                # Production-grade frontend design guidance
│   │   └── skills/                     # frontend-design auto-invoke skill
│   │
│   ├── hookify/                        # No-code custom hook creation system
│   │   ├── .claude-plugin/             # Plugin manifest
│   │   ├── agents/                     # conversation-analyzer agent
│   │   ├── commands/                   # /hookify, /hookify:list, /hookify:configure
│   │   ├── core/                       # Core hookify evaluation engine (Python)
│   │   ├── examples/                   # Example rule markdown files
│   │   ├── hooks/                      # The runtime hook evaluator scripts
│   │   ├── matchers/                   # Pattern matching logic
│   │   ├── skills/                     # writing-rules skill
│   │   └── utils/                      # Shared utilities
│   │
│   ├── learning-output-style/          # Interactive learning mode via SessionStart hook
│   │   └── hooks/                      # SessionStart hook
│   │
│   ├── plugin-dev/                     # 7-skill plugin development toolkit
│   │   ├── agents/                     # agent-creator, plugin-validator, skill-reviewer
│   │   ├── commands/                   # /plugin-dev:create-plugin 8-phase workflow
│   │   └── skills/                     # hook-dev, mcp-integration, plugin-structure,
│   │                                   # plugin-settings, command-dev, agent-dev,
│   │                                   # skill-dev (each with SKILL.md + resources)
│   │
│   ├── pr-review-toolkit/              # 6 specialized PR review agents
│   │   ├── .claude-plugin/             # Plugin manifest
│   │   ├── agents/                     # comment-analyzer, pr-test-analyzer,
│   │   │                               # silent-failure-hunter, type-design-analyzer,
│   │   │                               # code-reviewer, code-simplifier
│   │   └── commands/                   # /pr-review-toolkit:review-pr
│   │
│   ├── ralph-wiggum/                   # Autonomous iteration loops via Stop hook
│   │   ├── .claude-plugin/             # Plugin manifest
│   │   ├── commands/                   # /ralph-loop, /cancel-ralph
│   │   ├── hooks/                      # Stop hook that intercepts exit attempts
│   │   └── scripts/                    # Supporting shell scripts
│   │
│   └── security-guidance/              # Security pattern detection via PreToolUse hook
│       ├── .claude-plugin/             # Plugin manifest
│       └── hooks/
│           ├── hooks.json              # Hook registration (PreToolUse → Edit|Write|MultiEdit)
│           └── security_reminder_hook.py  # 9 security patterns, session-state tracking
│
├── examples/                           # Reference implementations
│   ├── hooks/
│   │   └── bash_command_validator_example.py  # PreToolUse hook: grep→rg, find→rg
│   ├── settings/
│   │   ├── README.md                   # Settings comparison table
│   │   ├── settings-lax.json           # Minimal restrictions (disable bypass mode)
│   │   ├── settings-strict.json        # Full restrictions (managed-only, no web)
│   │   └── settings-bash-sandbox.json  # Bash sandboxing configuration
│   └── mdm/
│       ├── README.md                   # MDM deployment guide
│       ├── managed-settings.json       # Minimal managed settings example
│       ├── macos/                      # Jamf/Kandji plist + mobileconfig
│       └── windows/                    # Intune PowerShell + ADMX/ADML for Group Policy
│
├── scripts/                            # GitHub automation scripts (TypeScript + Bash)
│   ├── gh.sh                           # Restricted gh CLI wrapper
│   ├── comment-on-duplicates.sh        # Posts duplicate issue comment
│   ├── edit-issue-labels.sh            # Add/remove GitHub issue labels
│   ├── auto-close-duplicates.ts        # TypeScript: auto-close confirmed duplicates
│   ├── backfill-duplicate-comments.ts  # TypeScript: batch backfill duplicate comments
│   ├── issue-lifecycle.ts              # TypeScript: stale/autoclose lifecycle logic
│   ├── lifecycle-comment.ts            # TypeScript: posts lifecycle comments
│   └── sweep.ts                        # TypeScript: batch issue processing
│
├── .github/
│   ├── ISSUE_TEMPLATE/                 # GitHub issue templates
│   └── workflows/
│       ├── claude.yml                  # @claude mention handler (issue_comment, PR review)
│       ├── claude-issue-triage.yml     # Auto-triage new issues + comments
│       ├── claude-dedupe-issues.yml    # Auto-detect duplicate issues
│       ├── auto-close-duplicates.yml   # Auto-close confirmed duplicates
│       ├── backfill-duplicate-comments.yml
│       ├── issue-lifecycle-comment.yml # stale/needs-repro lifecycle
│       ├── issue-opened-dispatch.yml   # Dispatch on new issue
│       ├── lock-closed-issues.yml      # Lock old closed issues
│       ├── log-issue-events.yml        # Event logging to Statsig
│       ├── non-write-users-check.yml   # Permissions gate
│       ├── remove-autoclose-label.yml  # Remove autoclose on activity
│       └── sweep.yml                   # Batch sweep for stale issues
│
├── .devcontainer/
│   ├── devcontainer.json               # VS Code devcontainer spec
│   ├── Dockerfile                      # node:20 base + Claude Code npm install
│   └── init-firewall.sh                # iptables/ipset network allowlist firewall
│
└── Script/
    └── run_devcontainer_claude_code.ps1  # Windows PowerShell devcontainer launcher
```

## Module and Package Organization

This repository does not contain a Node.js or Python package in the traditional sense (no `package.json` or `setup.py` at the root). Instead it is organized as a **content repository** with three distinct module types:

### 1. Slash Commands (Markdown)
Located in `plugins/*/commands/` and `.claude/commands/`. Each command is a `.md` file with YAML frontmatter:
```yaml
---
description: Human-readable description
allowed-tools: Bash(git status:*), Bash(gh pr create:*)
argument-hint: "[optional argument description]"
---
```
The body is the system prompt for the command. Dynamic context is injected with `!`-prefixed bash expressions (e.g., `!`git status``).

### 2. Agent Definitions (Markdown)
Located in `plugins/*/agents/`. Each agent is a `.md` file with YAML frontmatter:
```yaml
---
name: agent-name
description: When/how Claude should invoke this agent
model: claude-sonnet-4-5-20250929
color: purple
tools: [Bash, Read, Glob, Grep]
---
```
The body is the agent's system prompt.

### 3. Hook Scripts (Python/Shell)
Located in `plugins/*/hooks/` and `examples/hooks/`. Hook scripts receive JSON on stdin and communicate via exit codes. The `hooks.json` file in each plugin registers hooks with matchers.

### 4. Skills (Markdown)
Located in `plugins/*/skills/`. Each skill has a `SKILL.md` with YAML frontmatter:
```yaml
---
description: Trigger phrases and activation conditions
context: fork|inline
---
```
Skills use progressive disclosure: metadata → core SKILL.md → bundled reference docs.

## Code Organization Patterns

**Plugin isolation**: Each plugin is fully self-contained under `plugins/<name>/`. Plugins use `${CLAUDE_PLUGIN_ROOT}` to reference their own files portably, avoiding hardcoded paths.

**Markdown-as-configuration**: Commands, agents, and skills are authored as markdown files with YAML frontmatter rather than as code. This makes them human-readable, version-controllable, and easy to customize without programming knowledge.

**Multi-agent parallelism**: Complex workflows (code review, feature dev, issue dedup) spawn multiple parallel agents. Commands orchestrate these via natural language instructions to Claude.

**Hook exit code protocol**: Hooks signal intent via exit codes rather than stdout. Exit 0 = allow, 1 = show stderr to user only, 2 = block tool and show stderr to Claude.

**Session-scoped state**: Hooks that need cross-invocation state (like `security_reminder_hook.py`) write JSON to `~/.claude/` with session IDs as discriminators, with periodic cleanup of files older than 30 days.
