# Hivemind Architecture

Hivemind is a **patched-fork distribution of opencode** plus a Python
catalog manager that owns long-lived agents (experts, team leads,
hivemind-managed worker agents). Read this when:

- Adding a new capability and deciding which layer it belongs in.
- Touching anything that crosses a layer boundary.
- Diagnosing why something works differently than expected.
- Onboarding to the codebase.

## What hivemind actually is

Two halves, both built and shipped from this repo:

1. **The bundled opencode engine** — a fork of `sst/opencode` with
   ~18 patches under `third_party/patches/` and ~3 SDK-regen patches
   under `third_party/dep_patches/`. Pinned to a specific upstream
   tag in `MODULE.bazel` (`ext.opencode(version="1.4.3", sha256=...)`)
   and built hermetically by Bazel into a single `hivemind_engine`
   binary.
2. **The Python catalog manager (`src/hivemind/`)** — owns the agent
   catalog (which experts and teams exist, where their knowledge
   docs live, which version of an upstream repo each is pinned to),
   deploys agents into `~/.config/opencode/agents/`, and integrates
   with the engine over its HTTP API.

The `hivemind` CLI, the TUI, and the MCP server are three ingresses
into the same Python core. The opencode engine spawns the MCP server
as a subprocess on startup; the CLI and TUI are user-driven.

> **Why a fork instead of a sidecar?** The original v0 design treated
> opencode as an unmodifiable upstream and routed all integration
> through plugin ABIs. That worked for branding and slot rendering
> but couldn't deliver four critical hivemind properties: native
> WebSocket presence (substrate-level disconnect detection), a
> non-destructive `/global/reload-agents` endpoint that survives
> MCP subprocesses, the cross-session inbox, and the ephemeral
> session lifecycle. We now own the engine source. Patches are
> isolated commits in `dev/opencode/` and regenerated via
> `make dev-save`.

## Layout

```
hivemind/
├── src/hivemind/                       Python catalog manager
│   ├── agents/                         Agent kinds (body strategies)
│   │   ├── base.py                     Agent dataclass + AgentBody Protocol
│   │   ├── registry.py                 Single source of truth: load/CRUD
│   │   ├── git_analyzed.py             Cloned repo + AI-generated knowledge
│   │   ├── roster_templated.py         Team leads assembled from members
│   │   ├── system_templated.py         Hivemind-managed workers (curator, daemon)
│   │   ├── user_supplied.py            opencode/agents/<name>.md verbatim
│   │   └── memory.py                   Per-agent memory tree scaffolding
│   ├── crawl/                          External-doc ingestion (crawl4ai, trafilatura)
│   ├── mcp/                            MCP server (tools + prompts)
│   ├── templates/                      Jinja templates for agents + HIVEMIND.md
│   ├── tui/                            Textual TUI
│   ├── opencode.py                     Engine integration: deploy, format, HTTP
│   ├── lifecycle.py                    Kind-agnostic verbs: enable/disable/delete
│   ├── deployment.py                   Librarian + HIVEMIND.md regeneration
│   ├── config.py                       Path constants + JSON I/O
│   ├── constants.py                    Cross-module constants (no imports)
│   ├── models.py                       Pydantic models (typed catalog)
│   ├── hooks.py                        Post-mutation listener registry
│   ├── runtime.py                      attached/detached/test mode detection
│   ├── server.py                       opencode subprocess lifecycle
│   ├── git.py                          Git operations (clone, fetch, checkout)
│   ├── analysis.py                     AI analysis orchestration
│   ├── templates.py                    Jinja env + render helpers
│   └── cli.py                          Typer CLI
│
├── opencode/                           User-authored content slots
│   ├── agents/<name>.md                Hand-authored agent prompts
│   ├── commands/<name>.md              Slash commands (/foo)
│   ├── skills/<name>/SKILL.md          LLM-discovered skills
│   ├── config/                         Static config bundled into ~/.config/opencode
│   └── README.md                       Author-facing reference
│
├── third_party/
│   ├── patches/*.patch                 Engine source patches (applied at build)
│   ├── dep_patches/*.patch             SDK regen patches (touch packages/sdk/js/)
│   └── extensions.bzl                  Bazel ext that fetches+patches opencode
│
├── dev/opencode/                       Local clone for editing patches (gitignored)
├── docs/                               This file + sibling docs
├── tests/                              pytest tests for the Python core
├── tools/                              Bazel-side smoke tests
├── scripts/dev-opencode.py             clone/save/reset for the patch workflow
├── HIVEMIND.md                         Generated orchestrator instruction file
├── hivemind.json                       Catalog (engine settings + agents)
├── config.json                         Local overlay (enabled/disabled per machine)
├── MODULE.bazel                        Bazel module + version pins
└── Makefile                            install / update / engine / dev / dev-save
```

## The two halves, in detail

### Half 1 — The bundled engine (`third_party/`)

The engine is a fork of `sst/opencode` v1.4.3, applied as commits
on top of the upstream tag in `dev/opencode/`. The Bazel
`external_engines` extension (`third_party/extensions.bzl`) fetches
the upstream tarball at build time, applies every `dep_patches/*.patch`
and `patches/*.patch` in numeric order, and bun-compiles the result
into a single binary at `@opencode_src//:hivemind_engine`.

**Two patch tiers:**

| Tier | Touches | Rebuild cost | Frequency |
|---|---|---|---|
| `dep_patches/*.patch` | `package.json`, `bun.lock`, `packages/sdk/js/**` | `@opencode_node_modules` + `@opencode_src` invalidate (~30 s) | Rare — usually only SDK regens |
| `patches/*.patch` | source files (TypeScript) | `@opencode_src` only (~3 s) | Common |

The split exists because the SDK is read at bundle time through a
`node_modules` symlink that resolves into the `opencode_node_modules`
external repo, NOT `opencode_src`. SDK changes that land only as
code patches are silently ignored at bundle time even though they
appear correctly in the source tree.

**Patch authoring workflow** (`make dev` / `make dev-save`):

```
make dev            Clone opencode at the pinned version into dev/opencode,
                    create branch `hivemind`, replay every patch as one commit
                    each (dep_patches first, then patches).
…edit & commit in dev/opencode…
make dev-save       Regenerate third_party/patches/*.patch from those commits.
                    Routes each patch by what it touches (dep manifest →
                    dep_patches/, source file → patches/). Fails if a single
                    commit touches both.
make engine         Rebuild the engine binary.
make dev-reset      Wipe dev/opencode and re-clone from scratch.
```

The patches in numeric order today (subjects abbreviated):

| # | Tier | Subject |
|---|---|---|
| 0001 | code | Rewrite the TUI exit "Continue" suggestion to `hivemind` |
| 0002 | code | Rebrand the OPENCODE wordmark + TUI logo to HIVEMIND |
| 0003 | code | Inline connection indicator into home + sidebar footers |
| 0004 | code | Non-destructive agent reload endpoint (`/global/reload-agents`) |
| 0005 | code | Hardened opencode config defaults |
| 0006 | code | Bake `bash.sudo *: deny` into `Permission.fromConfig` |
| 0007 | code | Per-session inbox with deferred delivery |
| 0008 | code | `Session.fork` accepts optional `parentID` and permission |
| 0009 | code | Task tool accepts `source_session_id` |
| 0010 | code | Background Task mode + lifecycle (Task tool) |
| 0011 | dep  | SDK gen: `backgroundTasks` endpoint + `SessionBackgroundChanged` |
| 0012 | code | TUI `session_footer` slot + dual-slot home-footer plugin |
| 0013 | code | Switch HTTP listener to native `Bun.serve` |
| 0014 | dep  | SDK gen: `liveSessions` endpoint + `LiveSessionsChanged` event |
| 0015 | code | Per-client WebSocket presence and focus tracking |
| 0016 | code | Extend `reload-agents` to invalidate Skill and Command state |
| 0017 | code | TUI SSE loop: catch transient errors and reconnect |
| 0018 | code | Session metadata column |
| 0019 | code | File-write hook + hivemind memory-compaction auto-spawn |
| 0020 | dep  | SDK gen: ephemeral on Session + create/fork inputs |
| 0021 | code | Ephemeral subagent sessions |

These cluster into five themes: **branding** (0001, 0002, 0003,
0017), **safety hardening** (0005, 0006), **catalog/reload integration**
(0004, 0016), **session graph + cross-session features** (0007,
0008, 0009, 0010, 0011, 0014, 0015), **memory + cleanup** (0018,
0019, 0020, 0021), and **substrate** (0013). Patch 0013 is the
load-bearing one: native `Bun.serve` (vs `@hono/node-server` on
Bun) is what makes `req.signal.abort` and WebSocket close events
fire synchronously, which everything in the session-graph theme
depends on.

### Half 2 — The Python catalog manager (`src/hivemind/`)

The catalog has four agent kinds, each backed by an `AgentBody`
strategy (see `agents/base.py`). The strategy decides how the
deployed `agents/<name>.md` body is produced and how kind-specific
side effects (cloning repos, managing team dirs, etc.) play out at
deploy / undeploy time.

| Kind | Body source | Examples |
|---|---|---|
| `git_analyzed` | Cloned upstream repo + AI-generated knowledge docs at `experts/<name>/<commit>/` (HEAD symlink picks active version) | Every `expert-<X>` agent |
| `roster_templated` | Jinja `team_lead.md.j2` rendered against per-member section files at `teams/<name>/expert-<expert>.md` | Every `team-lead-<X>` agent |
| `system_templated` | Jinja template under `templates/agents/<name>.md.j2` | `hivemind-expert-curator`, `hivemind-memory-daemon`, `hivemind-crawler` |
| `user_supplied` | `opencode/agents/<name>.md` verbatim | Anything dropped into the slot |
| `librarian` | Auto-generated catalog of every enabled agent | Single agent: `librarian` |

**Single source of truth**: `agents/registry.py`. Loads
`hivemind.json` (the catalog) and `config.json` (the local
enabled/disabled overlay), joins them into `{name: Agent}`, and
provides the CRUD surface. Mutations always flow through
`lifecycle.py`'s kind-agnostic verbs (`enable_agent`,
`disable_agent`, `delete_agent`, `refresh_agent`,
`redeploy_all_agents`, `bootstrap_workspace`). Each verb:

1. Mutates the registry (flip enabled state, or remove).
2. Calls `Agent.deploy()` / `Agent.undeploy()`, which writes the
   `agents/<name>.md` file via `opencode.format_agent()` +
   `opencode.write_agent_file()` and runs the body's
   `on_deploy()` / `on_undeploy()` hooks.
3. Regenerates `agents/librarian.md` via
   `deployment.regenerate_librarian()`.
4. Fires `hooks.fire_post_mutation()` so listeners (CLI/TUI/MCP)
   can notify the engine.

Body-specific creators / mutators (`create_git_expert`,
`update_git_expert`, `switch_version`, `create_team`,
`add_expert_to_team`, …) live in the per-body modules and also
fire the post-mutation hook at their tail.

## Engine ↔ catalog integration

Three integration points, all in `opencode.py`:

1. **Filesystem deploys** — agent files written to
   `~/.config/opencode/agents/<name>.md`. Knowledge directories
   symlinked into `~/.config/opencode/experts/`.
2. **`/global/reload-agents` POST** — non-destructive engine
   reload (added by patch 0004). Re-reads `agents/*.md` for every
   active instance via `Config.invalidateState()` + `Agent.reload()`.
   Critically does **not** call `Instance.dispose()`, so MCP
   subprocesses survive the reload mid-tool-call.
3. **Engine subprocess lifecycle** — `server.py` starts and
   stops the bundled engine (`hivemind serve` under the hood).
   State persisted at `~/.cache/hivemind/server.json` so
   subsequent `hivemind` invocations attach to the running server.

### Why `/global/reload-agents` instead of `/global/dispose`?

Upstream opencode only exposed `POST /global/dispose` for cache
invalidation — that endpoint tears down every cached `InstanceState`
finalizer including the SIGTERM-the-MCP finalizer. That killed any
in-flight MCP tool call (the user had to type `continue` to resume).
Patch 0004 added `/global/reload-agents` to invalidate just the
agent cache; patch 0016 extended it to also invalidate Skill and
Command state. MCP mutations are now fully non-destructive.

## Post-mutation hook

`hooks.py` is a tiny listener registry. Each ingress registers one
listener at startup:

| Ingress | Listener |
|---|---|
| CLI (`cli.py`) | Sync POST to `/global/reload-agents` |
| TUI (`tui/app.py`) | Sync POST + pane refresh |
| MCP (`mcp/tools.py`) | Sync POST + `ToolListChangedNotification` |

Per-listener exceptions are caught and logged — one bad subscriber
cannot break a mutation. The reload is deferred 0 ms (CLI/TUI) or
inlined (MCP) since the patched reload endpoint is non-destructive.

## Runtime context

`runtime.py` exposes a `RuntimeContext` resolved once at ingress
startup. Three modes:

- **`attached`** — an opencode server is running; reload
  listeners post HTTP.
- **`detached`** — no server running; reload listeners no-op.
  Mutations still write files, which opencode picks up on next
  launch.
- **`test`** — pytest-controlled; listeners no-op, filesystem
  confined to tmpdir.

Downstream code reads a stable value instead of scattering
`is_server_running()` calls.

## MCP server (`src/hivemind/mcp/`)

Spawned once by opencode at startup and held for the life of the
opencode instance. Exposes:

**Read/query** — `list_agents`, `show_agent`, `status`.

**Lifecycle (fast, no AI)** — `enable_agent`, `disable_agent`,
`delete_agent`, `refresh_agent`, `redeploy`,
`add_expert_to_team`, `remove_expert_from_team`.

**Curator-scoped pipeline** — four `prep_*` / `finalize_*` pairs
that the `hivemind-expert-curator` subagent uses for the slow
operations (`create_git_expert`, `update_git_expert`,
`switch_version`, `create_team`). The pipeline runs in the
curator's own session so MCP doesn't time out. The blocking
`update_agent` / `switch_version` / `create_team` MCP tools have
been removed.

**Cross-session** — `list_sessions`, `send_message`,
`delete_session`. Cross-session forking-with-context goes through
opencode's native `Task(source_session_id=..., subagent_type=..., …)`
primitive (patches 0008/0009), not an MCP tool — that way the
orchestrator gets standard ctrl-x-down drill-down.

**When changing MCP-server code:** the subprocess is spawned once
and held. Restart opencode after editing anything under
`src/hivemind/mcp/` so the subprocess loads the new bytecode.
(The launcher's runfiles tree is symlinked source, so source
edits are visible immediately — but Python only re-imports on
process start.)

## TUI (`src/hivemind/tui/`)

Textual-based, two-tab layout (Experts, Teams). On mount, registers
two post-mutation listeners (reload + pane refresh).
`operations.py` holds thin async wrappers that translate
`ProgressInfo` events into Textual notifications. `VimDataTable`
provides vim-style navigation.

## User-supplied content slots (`opencode/`)

Three drop-in directories for user-authored opencode content. Drop
a file in the right subdirectory and run `hivemind redeploy` —
wiring is idempotent, so additions and removals go live without
`hivemind init`.

| Slot | Invocation | Body shape | Loaded from |
|---|---|---|---|
| `commands/<name>.md` | User types `/<name>` | Prompt template with `$ARGUMENTS` / `$1` / `$2` | `~/.config/opencode/commands/` (symlink) |
| `skills/<name>/SKILL.md` | LLM picks autonomously | Reference material (instructions, doc links) | `~/.config/opencode/skills/` (symlink) |
| `agents/<name>.md` | `Task(subagent_type=...)` after `enable_agent` | Whole agent prompt with frontmatter, verbatim | catalog → `~/.config/opencode/agents/` |

Commands and skills are symlinked verbatim. Agents go through the
catalog as `user_supplied` entries; `enable_agent` deploys them.
See `opencode/README.md` for the full author-facing reference.

## Build system

`bazelisk` is the only required system dependency. Everything else
(Python toolchain, PyPI deps via `uv.lock`, bun, opencode source,
patches) is fetched and built hermetically by Bazel.

```
make install   Build + symlink ~/.local/bin/hivemind (first-time setup)
make update    Pull, rebuild, refresh launcher
make test      bazel test //...
make engine    Rebuild the bun-compiled engine only
make clean     bazel clean + remove launcher symlink
```

Bazel produces a launcher whose runfiles are symlinks to workspace
source, so Python edits in `src/hivemind/*.py` are live without
rebuild. Only `pyproject.toml` / `uv.lock` / a patch / an engine
version bump in `MODULE.bazel` requires `make update`.

## Data flow: adding a new git-analyzed expert

```
hivemind expert add <url>            (CLI)
       │
       ▼
git_analyzed.create_git_expert       (clone repo to staging)
       │
       ▼
analysis.run_async_analysis          (AI generates agent.md + knowledge docs
                                      under experts/<name>/<commit>/)
       │
       ▼
HEAD symlink → active commit
       │
       ▼
registry.add(agent)                  (writes catalog entry to hivemind.json
                                      as UNLISTED — not yet enabled)
       │
       ▼
enable_agent(name)                   (separate user step, or auto in TUI)
       │
       ├── flips config.json:enabled
       ├── Agent.deploy(agents_dir)
       │     ├── opencode.format_agent → opencode.write_agent_file
       │     └── body.on_deploy (clone repo + symlink into experts/)
       ├── deployment.regenerate_librarian
       └── hooks.fire_post_mutation
                 │
                 └── listener POSTs /global/reload-agents
                       │
                       ▼
                       Engine re-reads agents/*.md without dispose
                       Active TUI sees new agent via reload event
```

## Configuration files

- **`hivemind.json`** (tracked) — engine settings + agent catalog
  (`agents: dict[str, CatalogEntry]`).
- **`config.json`** (gitignored) — local overlay
  (`enabled` / `disabled` agent names on this machine).
- **`HIVEMIND.md`** (tracked) — generated orchestrator instruction
  file. Rendered from `templates/hivemind.md.j2` at
  `bootstrap_workspace()` time. Symlinked into
  `~/.config/opencode/AGENTS.md`.

## Code conventions

- Modern Python type hints (PEP 604): `str | None`, `list[str]`.
- `from __future__ import annotations` at the top of every module.
- Imports used only for typing under `if TYPE_CHECKING:` (ruff TC003
  enforces).
- `typing.assert_never(x)` for exhaustiveness on discriminated
  unions.
- All `Any` / `dict[str, object]` usages that cross the agent-body
  layer have been replaced with Pydantic `GitAnalyzedParams` /
  `RosterTemplatedParams`. Don't reintroduce loose dicts there.
- **No backwards-compat shims, re-export facades, or alias layers**
  — update callers directly. Modules deleted in past refactors
  (`provider.py`, `experts.py`, `teams.py`, `redeploy.py`,
  `mutations.py`) must not be reintroduced.

## Where does a new capability go?

| If it's… | It lives in… |
|---|---|
| A new agent kind (alongside git_analyzed, roster_templated, …) | New file in `src/hivemind/agents/<kind>.py` implementing the `AgentBody` Protocol; register in `registry._body_from_catalog`; add a `*Params` Pydantic model to `models.py` |
| A new lifecycle verb (alongside enable/disable/refresh) | `src/hivemind/lifecycle.py`; expose via CLI, TUI, MCP |
| A new MCP tool exposed to opencode agents | `src/hivemind/mcp/tools.py`; restart the opencode subprocess to reload |
| A new opencode behavior we can build on the existing public API | Stays out — use `src/hivemind/opencode.py` to integrate |
| A new opencode behavior that needs engine internals | New patch via `make dev` / `make dev-save` workflow |
| A user-authored slash command / skill / agent | `opencode/{commands,skills,agents}/`, then `hivemind redeploy` |
| A new AI-driven workflow run by an existing agent | Edit `experts/<name>/HEAD/agent.md` then `hivemind redeploy`, or rev the git_analyzed source |

## Out of scope

- **Multi-host** — single-machine by design. No remote attach, no
  cross-machine session discovery.
- **Multi-engine support** — opencode is the only backend. The old
  provider abstraction has been removed; do not reintroduce it.
- **Speculative shared utilities** — extract shared code only when
  a second consumer needs it. Inline first, refactor when warranted.

## See also

- `docs/MEMORY_DAEMON.md` — memory tree + auto-compaction architecture
- `docs/WORKFLOW_SCENARIO.md` — the canonical 9-PR Graphite-stack
  scenario hivemind is built for
- `opencode/README.md` — user-supplied content slot reference
- `HIVEMIND.md` — generated orchestrator instructions
- `AGENTS.md` — repo-level instructions for AI contributors
- `scripts/dev-opencode.py` — patch authoring workflow
