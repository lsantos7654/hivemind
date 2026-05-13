<pre align="center">
█  █ ▀█▀ █  █ █▀▀█   █▄ ▄█ ▀█▀ █▀▀▄ █▀▀▄
█^^█  █  █__█ █^^^   █_█_█  █  █__█ █__█
▀~~▀ ▀▀▀  ▀▀  ▀▀▀▀   ▀   ▀ ▀▀▀ ▀~~▀ ▀▀▀
</pre>

Agent catalog manager for [OpenCode](https://opencode.ai) — clone repos, run
AI-powered analysis, deploy expert subagents with structured knowledge docs and
a shared memory system. The built-in librarian knows every expert so the
assistant always knows who to ask.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

## Quick Start

```bash
hivemind expert add https://github.com/koajs/koa  # clone + analyze → enabled
```

That's it. The expert is analyzed, deployed, and ready — spawn it with
`Task(subagent_type="expert-koa", ...)`.

## Install

Requires only [bazelisk](https://github.com/bazelbuild/bazelisk). The Python
toolchain, PyPI deps, bun, and the patched opencode engine are all built
hermetically.

```bash
git clone https://github.com/lsantos7654/hivemind.git
cd hivemind
make install     # builds CLI + engine, symlinks ~/.local/bin/hivemind
hivemind init    # bootstraps workspace
```

Make sure `~/.local/bin` is on your `PATH`. Python edits in
`src/hivemind/*.py` are live without rebuild.

| Command | What it does |
|---------|-------------|
| `make install` | First-time: build CLI + engine, symlink launcher |
| `make update` | After `git pull` or engine version bump |
| `make test` | Full suite: unit + lint + typecheck + engine smoke |
| `make clean` | `bazel clean` + remove launcher symlink |

## Commands

```
hivemind expert add <url> [--ref <ref>]        # clone + analyze, enabled by default
hivemind expert update <name>                   # fetch latest commit, re-analyze
hivemind expert switch-version <name> <ref>     # pin to tag/branch/commit
hivemind expert enable <name>                   # deploy agent file + symlink repo
hivemind expert disable <name>                  # remove agent file, keep data
hivemind expert delete <name> [--purge-memory]
hivemind expert list                            # table: name, status, HEAD, remote
hivemind expert show <name>                     # detail panel
hivemind expert crawl <url> <agent> [--max-pages N]
```

Two lifecycle states:

| State | Meaning |
|-------|---------|
| enabled | Deployed as a subagent, repo cloned + symlinked |
| disabled | Undeployed, backing data preserved |

### Teams

```
hivemind team create <name> -d <description> -e <expert,...>
hivemind team list
hivemind team show <name>
hivemind team add-expert <team> <expert,...>
hivemind team remove-expert <team> <expert>
hivemind team delete <team> [--force]
hivemind team enable <name>
hivemind team disable <name>
```

Team leads route questions to roster members by reading each expert's memory
tree. Creating a team lands as enabled; roster mutations are fast (no curator
needed).

### Server

```
hivemind server start [--port N] [--hostname H]
hivemind server stop
hivemind server status
```

Server mode keeps the engine alive as a background process. Benefits:
MCP subprocess survives session close, agent validation is cached once,
multiple TUI sessions share the same session tree, catalog mutations reload
agents without tearing down your conversation.

### System

```
hivemind status               # engine, model, server, expert/team counts
hivemind redeploy              # regenerate every enabled agent + librarian from catalog
hivemind tui                   # Textual-based TUI dashboard (Experts / Teams tabs)
hivemind mcp                   # MCP server (stdio transport)
hivemind init                  # setup symlinks, deploy agents, register MCP
hivemind                       # launch opencode (attaches to server if running)
hivemind -- -s ses_xxx         # forward args to opencode (-- separator required)
```

## How It Works

### Expert Structure

Each expert is a versioned directory with AI-generated knowledge docs:

```
experts/
  koa/
    HEAD -> a3930898ad18/          # symlink to active version
    a3930898ad18/
      agent.md                     # expert prompt body
      summary.md                   # repository overview
      code_structure.md            # annotated directory tree
      build_system.md              # build tooling and dependencies
      apis_and_interfaces.md       # public APIs and usage patterns
      description.md               # hand-editable summary (preserved across updates)
      expertise.md                 # hand-editable expertise claims (preserved across updates)
```

`description.md` and `expertise.md` are preserved across updates — the curator
regenerates the other four files.

### Deployed Layout

```
~/.config/opencode/
  agents/
    expert-koa.md               # expert agent
    team-lead-hivemind.md       # team lead agent
    librarian.md                # auto-generated catalog
  experts/                      # symlinks to ~/.cache/hivemind/experts/
  commands/                     # symlinked from opencode/commands/
  skills/                       # symlinked from opencode/skills/
  hivemind/memory/<name>/       # per-agent memory tree

~/.cache/hivemind/
  repos/koa/                    # cloned repository
  external_docs/koa/            # crawled documentation (optional)
  experts/koa/<commit>/         # analysis doc versions
  server.json / server.log      # server lifecycle state
```

### Teams

Teams group experts under a team lead (`roster_templated` kind). The lead's
prompt is assembled from a Jinja2 template plus one section per roster member:

```
teams/
  hivemind/
    expert-bazel.md             # per-expert routing reference
    expert-rich.md              # ...
    description.md              # team description
    lead.md                     # generated team-lead prompt
    notes.md                    # team-lead's self-managed notes
```

Per-expert sections are written by `hivemind-expert-curator` during team
creation.

### The Librarian

`librarian.md` knows every enabled expert and team. Regenerated automatically
on `enable`, `disable`, `delete`, and `redeploy`. Spawn it with
`Task(subagent_type="librarian", ...)`.

### Memory System

Each enabled agent owns a durable memory tree at
`~/.config/opencode/hivemind/memory/<name>/`:

```
short_memory.md    # working context — appended to on every reply
long_memory.md     # consolidated knowledge promoted by the daemon
<topic>.md         # topic files (daemon-created)
```

**Compaction**: `hivemind-memory-daemon` auto-promotes entries from
`short_memory.md` to `long_memory.md` (or new topic files) when the byte
threshold is crossed. Triggered by the file-write hook — never invoked manually.

The orchestrator (your main session) writes to
`~/.config/opencode/hivemind/memory/_orchestrator/`.

### Configuration

Two config files in the repo root:

| File | Tracked? | Purpose |
|------|----------|---------|
| `hivemind.json` | Yes | Engine settings + agent catalog (shared) |
| `config.json` | No | Per-machine enabled/disabled agent names |

After editing `hivemind.json`, run `hivemind redeploy`.

### External Documentation

```bash
hivemind expert crawl https://docs.example.com my-expert
```

Probes the site, picks sitemap / spider / Playwright, and saves clean markdown
to `~/.cache/hivemind/external_docs/<agent>/`. Experts read from that path
natively. JS-rendered sites need Chromium — run `uv run playwright install
chromium` once.

## Shell Completion

```bash
hivemind --install-completion
```

All commands support tab completion for expert and team names.

## Requirements

- [bazelisk](https://github.com/bazelbuild/bazelisk) on your `PATH`
- `~/.local/bin` on your `PATH`
