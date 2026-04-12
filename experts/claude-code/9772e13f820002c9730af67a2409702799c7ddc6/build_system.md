# Claude Code — Build System

## Build System Type

This repository has **no traditional build system** at its root. There is no `package.json`, `Makefile`, `CMakeLists.txt`, or `pyproject.toml` in the repository root. The content (plugins, examples, scripts) is consumed directly from source.

The repository is a **content and reference repository**. The Claude Code binary itself is built and distributed separately by Anthropic.

## External Dependencies

### Runtime Dependencies (for using Claude Code)
- **Node.js 18+**: Required to run the Claude Code CLI
- **npm**: Used for the deprecated installation path (`npm install -g @anthropic-ai/claude-code`)
- **Python 3.7+**: Required only for hook scripts (no third-party Python libraries needed — stdlib only)

### Plugin-Specific Dependencies
- **GitHub CLI (`gh`)**: Required for `commit-commands`, `code-review`, `pr-review-toolkit`, `feature-dev`, and repository automation scripts
- **`git`**: Required by all git-related commands and plugins
- **`jq`**: Used in firewall script and some shell scripts
- **`curl`**: Used in firewall script for GitHub IP range fetching and domain resolution

### DevContainer Dependencies (`.devcontainer/Dockerfile`)
Base image: `node:20`

Installed via `apt-get`:
- `git`, `gh`, `fzf`, `zsh`, `jq`, `nano`, `vim`
- `iptables`, `ipset`, `iproute2`, `dnsutils`, `aggregate` (for firewall)
- `less`, `procps`, `sudo`, `man-db`, `unzip`, `gnupg2`

Installed via `npm install -g`:
- `@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}` (default: `latest`)

Additional tooling:
- `git-delta` v0.18.2 (diff viewer)
- `zsh-in-docker` v1.2.0 (Zsh + Powerlevel10k setup)

## Installation Methods

### Recommended (official installers)
```bash
# macOS / Linux via curl
curl -fsSL https://claude.ai/install.sh | bash

# macOS / Linux via Homebrew
brew install --cask claude-code

# Windows via PowerShell
irm https://claude.ai/install.ps1 | iex

# Windows via WinGet
winget install Anthropic.ClaudeCode
```

### Deprecated (npm)
```bash
npm install -g @anthropic-ai/claude-code
```

### DevContainer
```bash
# Open in VS Code with Dev Containers extension
# Or use the Windows PowerShell script:
Script/run_devcontainer_claude_code.ps1
```

## GitHub Actions Workflows

The repository uses GitHub Actions extensively for automating issue management. All workflows use `anthropics/claude-code-action@v1`.

### Issue Triage (`claude-issue-triage.yml`)
- **Trigger**: `issues: [opened]`, `issue_comment: [created]`
- **What it does**: Runs `/triage-issue` slash command to apply GitHub labels
- **Model**: `claude-opus-4-6`
- **Timeout**: 10 minutes (inner 5 minutes)
- **Permissions**: `contents: read`, `issues: write`
- **Special env**: `CLAUDE_CODE_SCRIPT_CAPS: '{"edit-issue-labels.sh":2}'` (limits script invocations)

### Issue Deduplication (`claude-dedupe-issues.yml`)
- **Trigger**: `issues: [opened]`, `workflow_dispatch`
- **What it does**: Runs `/dedupe` to find and comment on duplicate issues
- **Model**: `claude-sonnet-4-5-20250929`
- **Timeout**: 10 minutes
- **Permissions**: `contents: read`, `issues: write`
- **Special env**: `CLAUDE_CODE_SCRIPT_CAPS: '{"comment-on-duplicates.sh":1}'`
- **Logging**: Posts event to Statsig on completion

### @claude Mention Handler (`claude.yml`)
- **Trigger**: `issue_comment`, `pull_request_review_comment`, `pull_request_review`, `issues: [opened, assigned]`
- **Condition**: Comment body must contain `@claude`
- **What it does**: Runs Claude Code with the mentioned context
- **Model**: `claude-sonnet-4-5-20250929`
- **Permissions**: `contents: read`, `pull-requests: read`, `issues: read`, `id-token: write`

### Other Lifecycle Workflows
- `auto-close-duplicates.yml`: Auto-closes confirmed duplicate issues
- `issue-lifecycle-comment.yml`: Posts stale/needs-repro lifecycle comments
- `issue-opened-dispatch.yml`: Dispatches event on new issue
- `lock-closed-issues.yml`: Locks old closed issues
- `log-issue-events.yml`: Logs events to Statsig for analytics
- `non-write-users-check.yml`: Permission gate for non-write users
- `remove-autoclose-label.yml`: Removes autoclose label on new activity
- `sweep.yml`: Batch sweep for stale issue processing
- `backfill-duplicate-comments.yml`: Backfills duplicate comments in bulk

## Scripts Directory

TypeScript and shell scripts in `scripts/` support the GitHub automation workflows:

```bash
# Shell scripts (no compilation needed)
scripts/gh.sh                    # Restricted gh CLI wrapper (security boundary)
scripts/comment-on-duplicates.sh # Posts a comment listing duplicates
scripts/edit-issue-labels.sh     # Adds/removes labels on an issue

# TypeScript scripts (run with ts-node or similar, no build artifact produced)
scripts/auto-close-duplicates.ts
scripts/backfill-duplicate-comments.ts
scripts/issue-lifecycle.ts
scripts/lifecycle-comment.ts
scripts/sweep.ts
```

## DevContainer Firewall (`init-firewall.sh`)

The devcontainer includes a strict network firewall that runs on container start via `postStartCommand: "sudo /usr/local/bin/init-firewall.sh"`.

**What it does:**
1. Flushes all existing iptables rules
2. Restores Docker internal DNS rules (127.0.0.11)
3. Allows DNS (UDP/53), SSH (TCP/22), and localhost
4. Fetches GitHub IP ranges from `https://api.github.com/meta` and adds to ipset
5. Resolves and allows: `registry.npmjs.org`, `api.anthropic.com`, `sentry.io`, `statsig.anthropic.com`, `statsig.com`, `marketplace.visualstudio.com`, `vscode.blob.core.windows.net`, `update.code.visualstudio.com`
6. Sets default policy to DROP for INPUT, FORWARD, OUTPUT
7. Verifies firewall: confirms `example.com` is blocked and `api.github.com` is reachable

## Building and Testing Plugins

Plugins have no build step. To test a plugin locally:

```bash
# Test a plugin by pointing Claude Code at its directory
cc --plugin-dir /path/to/plugin-name

# Or install from the bundled marketplace
# In a Claude Code session:
/plugin install plugin-name@claude-code-plugins
```

## Hook Script Testing

```bash
# Test a hook manually by simulating stdin input
echo '{"tool_name": "Bash", "tool_input": {"command": "grep foo bar.txt"}}' | \
  python3 examples/hooks/bash_command_validator_example.py
# Exit code 2 means hook blocked the tool

# Use the plugin-dev toolkit's utilities (if installed):
./validate-hook-schema.sh hooks/hooks.json
./test-hook.sh my-hook.sh test-input.json
./hook-linter.sh my-hook.sh
```

## Settings Deployment

For enterprise MDM deployment, settings are copied to the platform-specific location:

| Platform | Path |
|----------|------|
| macOS (system) | `/Library/Application Support/ClaudeCode/managed-settings.json` |
| Windows (system) | `C:\Program Files\ClaudeCode\managed-settings.json` |
| macOS (MDM plist) | `com.anthropic.claudecode` preference domain via Jamf/Kandji |
| Windows (GPO) | `HKLM\SOFTWARE\Policies\ClaudeCode\Settings` (REG_SZ, JSON string) |

Settings at the system/enterprise level take highest precedence and cannot be overridden by users.
