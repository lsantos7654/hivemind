# Hivemind

A CLI for managing expert agents across AI coding platforms.

Hivemind clones repositories, runs AI-powered analysis to generate structured
knowledge docs, and deploys expert subagents that your AI coding assistant can
delegate to automatically. A built-in librarian keeps a catalog of all experts
so the assistant always knows who to ask.

Works with [Claude Code](https://docs.anthropic.com/en/docs/claude-code),
[OpenCode](https://opencode.ai), and is extensible to other platforms via a
provider abstraction.

## Install

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/lsantos7654/hivemind.git
uv tool install -e ./hivemind
hivemind init
```

If you already have the repo elsewhere, point `uv tool install -e` at that path instead.

## Quick Start

```bash
# Add an expert from any git repo
hivemind add https://github.com/bazelbuild/bazel

# Query the librarian
hivemind query "how do I write a custom Bazel rule?"
```

That's it. The expert is now available as a subagent in your AI coding
assistant. When you ask a question about Bazel, the assistant can delegate
to the expert, which has access to structured knowledge docs and the full
source code.

## Commands

### Core Workflow

```
hivemind add <url>            # Clone, analyze, and create an expert
hivemind update [name]        # Fetch latest commits and re-analyze
hivemind enable <name>        # Enable a disabled expert
hivemind disable <name>       # Disable an expert
hivemind list                 # Show all experts and their status
hivemind status               # Full dashboard (symlinks, repos, experts)
```

### Querying

```
hivemind query <question>     # Ask the librarian which expert(s) to use
```

### Provider Management

```
hivemind provider list        # List available providers and their status
hivemind provider switch <n>  # Switch active provider
hivemind provider show [n]    # Show detailed provider configuration
hivemind redeploy             # Regenerate all agent files for active provider
```

### Other

```
hivemind crawl <url> <agent>  # Crawl a website and save docs for an expert
hivemind tui                  # Interactive terminal UI
hivemind init                 # Set up directory structure and deploy agents
```

## How It Works

### Expert Structure

Each expert is a versioned directory with AI-generated knowledge docs:

```
experts/
  bazel/
    HEAD -> a3930898ad18/          # symlink to active version
    a3930898ad18/
      agent.md                     # expert definition (platform-neutral)
      summary.md                   # repository overview
      code_structure.md            # annotated directory tree
      build_system.md              # build tooling and dependencies
      apis_and_interfaces.md       # public APIs and usage patterns
```

The `agent.md` file uses `{EXPERTS_DIR}` placeholders for paths. At deploy
time, these are replaced with the provider's actual paths (e.g.,
`~/.claude/experts` or `~/.config/opencode/experts`).

### Deployed Layout

When you run `hivemind init` or `hivemind redeploy`, agent files are generated
with provider-specific frontmatter and written to the `agents/` directory,
which is symlinked into the provider's home:

```
agents/
  expert-bazel.md                  # generated file with provider frontmatter
  librarian.md                     # auto-generated catalog of all experts

~/.cache/hivemind/
  repos/bazel/                     # cloned repository
  external_docs/bazel/             # crawled documentation (optional)
```

### Providers

Hivemind supports multiple AI coding platforms via a provider abstraction.
Each provider defines:

- How agent files are formatted (YAML frontmatter differs per platform)
- How the analysis engine is invoked (e.g., `claude -p` vs `opencode run`)
- Where files are deployed (`~/.claude/` vs `~/.config/opencode/`)

The active provider is set in `config.json` and can be switched at any time:

```bash
hivemind provider switch opencode
hivemind redeploy
```

### Configuration

Provider settings live in `config.json` (not tracked by git):

```json
{
  "active_provider": "claude",
  "providers": {
    "claude": {
      "enabled": true,
      "engine": "claude -p --verbose --dangerously-skip-permissions",
      "home_dir": "~/.claude",
      "settings": {
        "model": "sonnet",
        "tools": ["Read", "Grep", "Glob", "Bash"]
      }
    },
    "opencode": {
      "enabled": true,
      "engine": "opencode run",
      "home_dir": "~/.config/opencode",
      "settings": {
        "model": "github-copilot/claude-sonnet-4",
        "temperature": 0.1,
        "tools": {"read": true, "grep": true, "glob": true, "bash": true}
      }
    }
  }
}
```

Settings are global -- all agents share the same model and tools. After
editing `config.json`, run `hivemind redeploy` to regenerate agent files.

### The Librarian

The librarian is an auto-generated agent (`agents/librarian.md`) that knows
about every enabled expert. It's regenerated on `add`, `update`, `enable`,
`disable`, and `init`. Use `hivemind query` to ask it which expert can help
with a question, or let your AI assistant route to it automatically.

### External Documentation

You can supplement an expert's knowledge with crawled web documentation:

```bash
hivemind crawl https://docs.example.com/sitemap.xml my-expert
```

Crawled docs are stored in `~/.cache/hivemind/external_docs/<name>/` and
referenced by the expert agent as a secondary knowledge source.

## Shell Completion

```bash
hivemind --install-completion
```

All commands support tab completion for expert names and provider names.

## Requirements

- Python 3.10+
- An AI coding platform CLI: [Claude Code](https://docs.anthropic.com/en/docs/claude-code) or [OpenCode](https://opencode.ai)
