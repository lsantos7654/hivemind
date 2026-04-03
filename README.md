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

### Experts

```
hivemind add <url>            # Clone, analyze, and create an expert
hivemind update [name]        # Fetch latest commits and re-analyze
hivemind enable <name>        # Enable a disabled expert
hivemind disable <name>       # Disable an expert
hivemind list                 # Show all experts and their status
hivemind query <question>     # Ask the librarian which expert(s) to use
```

### Teams

```
hivemind team create <name>               # Create a team with AI-generated lead
hivemind team list                        # List all teams
hivemind team show <name>                 # Show team details and roster
hivemind team add-expert <team> <expert>  # Add an expert to a team
hivemind team remove-expert <team> <ex>   # Remove an expert from a team
hivemind team delete <name>               # Delete a team
```

### System

```
hivemind status               # Full dashboard
hivemind redeploy             # Regenerate all agent files for active provider
hivemind provider list        # List available providers
hivemind provider switch <n>  # Switch active provider
hivemind provider show [n]    # Show provider configuration
hivemind crawl <url> <agent>  # Crawl a website and save docs for an expert
hivemind init                 # Set up directory structure and deploy agents
hivemind                      # Launch interactive TUI
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
  expert-bazel.md                  # expert agent
  team-lead-build-team.md          # team lead agent
  librarian.md                     # auto-generated catalog of all experts and teams

~/.cache/hivemind/
  repos/bazel/                     # cloned repository
  external_docs/bazel/             # crawled documentation (optional)
```

### Teams

A team groups related experts under a team lead. The team lead knows about
all experts on the roster and helps route questions to the right specialist.

```
teams/
  build-team/
    lead.md          # team lead agent body (AI-generated, self-managed)
    general.md       # high-level team notes and patterns
```

The team lead is a self-managing agent — it can update its own `lead.md`,
maintain `general.md` with lessons learned, and request roster changes via
the CLI.

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

Hivemind uses two config files:

- **`hivemind.json`** (tracked) — shared config: providers, repos
- **`config.json`** (gitignored) — local state: enabled/disabled experts, active provider, teams

After editing provider settings in `hivemind.json`, run `hivemind redeploy`
to regenerate agent files.

### Workspace Workflow

The main branch is the hivemind tool itself — code, expert knowledge, and
shared repos. Teams are gitignored on main because they're user-specific.

To track your own teams, create a personal branch:

```bash
git checkout -b santos        # your workspace branch
# remove teams/ from .gitignore
# commit your teams and config
```

Periodically merge main to get code and expert updates:

```bash
git merge main
```

This keeps main clean as a starting point while your branch holds your
workspace state (teams, config, etc.).

### The Librarian

The librarian is an auto-generated agent (`agents/librarian.md`) that knows
about every enabled expert and team. It's regenerated on `add`, `update`,
`enable`, `disable`, and `init`. Use `hivemind query` to ask it which expert
can help with a question, or let your AI assistant route to it automatically.

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
