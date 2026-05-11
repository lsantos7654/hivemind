# Hivemind

Agent catalog manager for [OpenCode](https://opencode.ai). Clones repositories,
runs AI-powered analysis to generate structured knowledge docs, and deploys
expert subagents. A built-in librarian keeps a catalog of every expert so the
assistant always knows who to ask.

## Install

Requires only [bazelisk](https://github.com/bazelbuild/bazelisk). The Python
toolchain, PyPI dependencies, bun, and the patched opencode engine are all
fetched and built hermetically by Bazel.

```bash
git clone https://github.com/lsantos7654/hivemind.git
cd hivemind
make install     # bazelisk builds CLI + patched engine; symlinks ~/.local/bin/hivemind
hivemind init
```

Make sure `~/.local/bin` is on your `PATH`.

`make install` builds the Python CLI launcher and the patched opencode engine
binary via Bazel, then symlinks the launcher into `~/.local/bin/hivemind`. The
launcher's runfiles tree contains symlinks to workspace source — Python edits
in `src/hivemind/*.py` are live without rebuild.

- `make update` — rebuild after `git pull` or a dependency/engine version bump
- `make clean` — bazel clean + remove the launcher symlink

## Quick Start

```bash
# Add an expert (clones + AI-analyzes; lands as unlisted)
hivemind expert add https://github.com/bazelbuild/bazel

# Deploy it as a subagent
hivemind expert enable bazel

# In your opencode session, spawn it:
#   Task(subagent_type="expert-bazel", ...)
```

Expert names prepend `expert-` to form the subagent type. After `enable`,
the expert has access to structured knowledge docs and the full cloned
source — start there with `Read`/`Grep`/`Bash` before spawning a Task.

## Workflows

### Standalone

```bash
hivemind    # single process: engine runs in-process, exits when you quit
```

- Simplest setup — one command, no background processes
- Backing state (agents, config) lives on disk; mutations persist and are
  picked up on the next launch

### Server / Client

```bash
hivemind server start     # starts a persistent background engine
hivemind                  # attaches to the running server
hivemind server stop      # SIGTERM → clean shutdown
hivemind server status    # port, PID, uptime, provider, log path
```

Server mode keeps the engine alive as a background process
(`~/.cache/hivemind/server.json` tracks state). Benefits:

- **MCP subprocess survives session close** — no restart cost on reconnect
- **Agent validation cached once**, not per-launch (~800 ms saved)
- **Multiple TUI sessions** attach to the same session tree; focus state
  broadcast via WebSocket `/presence`
- **Non-destructive reload** — catalog mutations (`enable`/`disable`/`update`)
  notify the running server via `POST /global/reload-agents`; agents reload
  from disk without tearing down your in-flight conversation or MCP
  subprocesses

The default port is 4040 (`hivemind.json:server.port`). Adjust with
`hivemind server start --port 4096` or change the `hostname`/`port` fields in
`hivemind.json`.

## Commands

### Experts

```
hivemind expert add <url> [--ref <ref>]        # clone + analyze, lands unlisted
hivemind expert update <name>                   # fetch latest commit, re-analyze
hivemind expert switch-version <name> <ref>     # pin to tag/branch/commit
hivemind expert enable <name>                   # deploy agent file + symlink repo
hivemind expert disable <name>                  # remove agent file, keep data
hivemind expert delete <name> [--force] [--purge-memory]
hivemind expert list                            # table: name, status, HEAD, versions, remote
hivemind expert show <name>                     # detail panel
hivemind expert crawl <url> <agent> [--max-pages N]   # crawl docs site into ~/.cache/hivemind/external_docs/<agent>/
```

Three lifecycle states:

| State | Meaning |
|-------|---------|
| unlisted | In catalog, not deployed — the agent lands here after `add` |
| enabled | Deployed as a subagent, repo cloned + symlinked |
| disabled | Undeployed, backing data preserved |

`add`, `update`, and `switch-version` are slow (AI analysis in-session).
For MCP-based use, spawn `hivemind-expert-curator` in `background` mode
instead — see `~/.config/opencode/agents/hivemind-expert-curator.md`.

### Teams

```
hivemind team create <name> -d <description> -e <expert,...>   # lands unlisted
hivemind team list
hivemind team show <name>
hivemind team add-expert <team> <expert,...>
hivemind team remove-expert <team> <expert>
hivemind team delete <team> [--force]
hivemind team enable <name>         # deploy team-lead agent
hivemind team disable <name>
```

Team leads route questions to the right roster member by reading each
expert's memory tree. Roster mutations (`add-expert`/`remove-expert`) are
fast — no curator needed.

### Server

```
hivemind server start [--port N] [--hostname H]
hivemind server stop
hivemind server status
```

### System

```
hivemind status               # engine, model, server, expert/team counts
hivemind redeploy              # regenerate every enabled agent + librarian from catalog
hivemind tui                   # Textual-based TUI dashboard (Experts / Teams tabs)
hivemind mcp                   # MCP server (stdio transport)
hivemind init                  # setup symlinks, deploy agents, register MCP in opencode.json
hivemind                       # launch opencode (attaches to server if running)
hivemind -- -s ses_xxx         # forward args to opencode (-- separator required)
```

`hivemind redeploy` re-generates every enabled agent file, the librarian,
and `HIVEMIND.md` from the current catalog. Also re-symlins `opencode/`
(commands, skills, user-supplied agents) into opencode's home directory.

`hivemind init` bootstraps the workspace: symlinks `agents/`, `commands/`,
`skills/`, and `AGENTS.md` into `~/.config/opencode/`, registers the hivemind
MCP server in `opencode.json`, and deploys all enabled agents. Safe to re-run.

## How It Works

### Memory System

Each enabled agent owns a durable memory tree at
`~/.config/opencode/hivemind/memory/<name>/`:

```
short_memory.md    # working context — appended to on every reply
long_memory.md     # consolidated knowledge promoted by the daemon
<topic>.md         # topic files (daemon-created, descriptive filenames)
```

The orchestrator (your main session) writes to
`~/.config/opencode/hivemind/memory/_orchestrator/`.

**Compaction**: `hivemind-memory-daemon` (a `system_templated` agent)
automatically promotes durable entries from `short_memory.md` into
`long_memory.md` or new topic files when `short_memory.md` exceeds
`hivemind.json:memory.compaction_threshold_bytes`. Triggered by the
file-write hook — experts don't invoke it manually. One-shot per trigger.

**Agent contract**: The memory section in each deployed agent's prompt
(rendered from `templates/memory_section.md.j2`) enforces that the last
action of every reply is a `Write` to `short_memory.md`. Experts discover
topic files by listing the directory — descriptive filenames serve as the
index.

**Team leads** read each roster member's memory tree before routing, using
`short_memory.md` + topic files to decide which expert(s) to engage.

### Expert Structure

Each expert is a versioned directory with AI-generated knowledge docs:

```
experts/
  bazel/
    HEAD -> a3930898ad18/          # symlink to active version
    a3930898ad18/
      agent.md                     # expert prompt body
      summary.md                   # repository overview
      code_structure.md            # annotated directory tree
      build_system.md              # build tooling and dependencies
      apis_and_interfaces.md       # public APIs and usage patterns
      description.md               # one-paragraph hand-editable summary
      expertise.md                 # hand-editable expertise claims
```

`description.md` and `expertise.md` are preserved across updates —
the curator regenerates the other four analysis files.

### Deployed Layout

When you run `hivemind init` or `hivemind redeploy`, agent files are written
and symlinked into `~/.config/opencode/`:

```
~/.config/opencode/
  agents/
    expert-bazel.md               # expert agent
    team-lead-hivemind.md         # team lead agent
    librarian.md                  # auto-generated catalog
  experts/                        # symlinks to ~/.cache/hivemind/experts/
  commands/                       # symlinked from opencode/commands/
  skills/                         # symlinked from opencode/skills/
  hivemind/memory/<name>/         # per-agent memory tree

~/.cache/hivemind/
  repos/bazel/                    # cloned repository
  external_docs/bazel/            # crawled documentation (optional)
  experts/bazel/<commit>/         # analysis doc versions
  server.json / server.log        # server lifecycle state
```

### Teams

Teams group experts under a team lead (`roster_templated` kind). The team
lead's prompt is assembled from a Jinja2 template (`templates/agents/`) plus
one section per roster member:

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
creation. Roster mutations (`add-expert-to-team`/`remove-expert-from-team`)
are fast MCP tools and don't need the curator.

### The Librarian

`librarian.md` knows every enabled expert and team. Regenerated automatically
on `enable`, `disable`, `delete`, and `redeploy`. In an opencode session:

```
Task(subagent_type="librarian", ...)
```

The librarian is read-only (`Read`/`Grep`/`Glob` tools only).

### Configuration

Two config files in the repo root:

- **`hivemind.json`** (tracked) — engine settings (`model`, `home_dir`,
  `server`, `tools`, `temperature`) + agent catalog
- **`config.json`** (gitignored) — per-machine enabled/disabled agent names

After editing `hivemind.json` (agent catalog entries), run `hivemind redeploy`.

### External Documentation

```bash
hivemind expert crawl https://docs.example.com my-expert
```

Probes the site, picks the appropriate strategy (sitemap / spider / Playwright
for JS-rendered sites), and saves clean markdown to
`~/.cache/hivemind/external_docs/<agent>/`. Experts read from that path
natively (it's in their `external_directory` allowlist). Browser-rendered
sites need Chromium — run `uv run playwright install chromium` once.

### Workspace Workflow

The default branch holds the hivemind tool itself plus the shared expert
catalog. To track your own teams:

```bash
git checkout -b santos
# commit your teams and config
git merge main     # periodically, for catalog + code updates
```

## Shell Completion

```bash
hivemind --install-completion
```

All commands support tab completion for expert and team names.

## Requirements

- [bazelisk](https://github.com/bazelbuild/bazelisk) on your `PATH` (only system dep)
- `~/.local/bin` on your `PATH` (where `make install` drops the launcher)
