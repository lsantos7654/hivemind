# Hivemind

A CLI for managing expert agents in [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

Hivemind clones repositories, runs AI-powered analysis to generate knowledge docs, and wires up expert subagents that Claude Code can delegate to automatically. A built-in librarian keeps a catalog of all experts so Claude always knows who to ask.

## Install

```
uv tool install -e ~/projects/hivemind
hivemind init
```

## Usage

```
hivemind add <url>            # Add an expert from a git repo
hivemind update [name]        # Re-analyze with latest commits
hivemind query <question>     # Ask the librarian which expert to use
hivemind list                 # Show all experts
hivemind enable <name>        # Enable a disabled expert
hivemind disable <name>       # Disable an expert
hivemind status               # Full dashboard
```

### Adding an expert

```
hivemind add https://github.com/bazelbuild/bazel
```

This will clone the repo, run an AI analysis pass to generate knowledge docs (summary, code structure, build system, APIs), create a versioned expert definition, and register it with the librarian.

### Querying the librarian

```
hivemind query "how do I write a custom Bazel rule?"
```

Returns which expert(s) are best suited to answer, without starting a full Claude Code session.

### Updating experts

```
hivemind update           # update all enabled experts
hivemind update bazel     # update just one
```

Fetches latest commits, creates a new versioned snapshot, and re-runs AI analysis in parallel.

## How it works

```
~/.claude/
  agents/
    expert-bazel.md -> ../experts/bazel/HEAD/agent.md
    librarian.md
  experts/
    bazel/
      HEAD -> abc123def/
      abc123def/
        agent.md
        summary.md
        code_structure.md
        build_system.md
        apis_and_interfaces.md
~/.cache/hivemind/repos/
    bazel/
```

- **Experts** are versioned by commit hash. `HEAD` is a symlink to the active version.
- **Agent symlinks** in `~/.claude/agents/` point through `HEAD`, so Claude Code picks them up automatically.
- **The librarian** is regenerated on every `add`, `update`, and `init` — it's a catalog of all experts that Claude uses to route questions.
- **Repos** are cached in `~/.cache/hivemind/repos/` and symlinked into the project as `repos/`.

## Requirements

- Python 3.10+
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI (`claude`)
