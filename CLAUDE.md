# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

`bazelisk` is the only required system dependency. Everything else (Python
toolchain, PyPI deps, bun, opencode source, patches) is fetched and built
hermetically by Bazel.

```bash
make install            # Build + symlink ~/.local/bin/hivemind (first-time setup)
make update             # Pull, rebuild, refresh launcher
make test               # bazel test //...
make engine             # Rebuild the bun-compiled engine only
make clean              # bazel clean + remove launcher symlink

hivemind                # Launch opencode (attaches to running server if present)
hivemind tui            # Open TUI dashboard
hivemind status         # Full dashboard
hivemind -- -s ses_xxx  # Forward args to opencode (explicit -- separator)
```

Source edits in `src/hivemind/*.py` are live without rebuild — the Bazel
launcher uses a runfiles tree of symlinks to workspace source. Only
`pyproject.toml`, `uv.lock`, a `third_party/patches/*.patch`, or an engine
version bump in `MODULE.bazel` requires `make update`.

Verify changes:
```bash
bazelisk test //...                                      # full Bazel test suite
bazelisk test //tests:test_core                          # single test target
bazelisk run //src/hivemind:hivemind -- redeploy         # smoke: regenerate agents
```

Lint/format/type-check tools (`ruff`, `mypy`, `pre-commit`) are pinned in
`pyproject.toml` and locked in `uv.lock`, but not exposed as Bazel targets.
Install them however you prefer (e.g., `brew install ruff mypy pre-commit`).

### User-supplied opencode content

Three slots under `opencode/` for user-authored content; see
`opencode/README.md` for the full author-facing reference.

- `opencode/commands/<name>.md` — slash commands invoked as `/<name>`.
  Symlinked into `~/.config/opencode/commands/`.
- `opencode/skills/<name>/SKILL.md` — LLM-discovered skills. Symlinked
  into `~/.config/opencode/skills/`.
- `opencode/agents/<name>.md` — hand-authored agent prompts. Auto-
  registered in the catalog as `user_supplied` agents on every
  redeploy; `enable_agent` deploys the file verbatim into
  `~/.config/opencode/agents/<name>.md`.

`hivemind redeploy` re-establishes the symlinks and reconciles the
catalog with `opencode/agents/`. All three flows are idempotent —
drop / edit / remove a file then redeploy, no separate `hivemind init`
required.

### Patching opencode

The bundled engine is a patched fork. Patches live in
`third_party/patches/*.patch` and are applied at build time. To author or
edit a patch:

```bash
make dev            # Clone opencode into dev/opencode and apply patches as commits
# ... edit dev/opencode and commit changes on top ...
make dev-save       # Regenerate third_party/patches/*.patch from those commits
make engine         # Rebuild the engine to pick up the new patch set
make dev-reset      # Wipe dev/opencode and re-clone from scratch
```

`scripts/dev-opencode.py` drives this workflow.

## Architecture

Hivemind is an agent catalog manager for opencode. It curates a shared
catalog of domain-expert agents (`git_analyzed` — cloned repos + AI-generated
knowledge docs) and team-lead agents (`roster_templated` — assembled from a
roster of member experts) and keeps the deployed opencode `agents/*.md`
files in sync with that catalog.

### Core modules (`src/hivemind/`)

- **`opencode.py`** — OpenCode integration. Module-level functions (not a
  class) for frontmatter formatting, agent-file deployment, engine
  validation, analysis-command building, server lifecycle, and
  `notify_instance_reload()` (POSTs `/global/reload-agents`). Caches
  `HivemindConfig` and the validation result per process. OpenCode is the
  only backend; the old provider abstraction is gone.
- **`config.py`** — Path constants + JSON I/O primitives (`load_config`,
  `save_config`, `load_hivemind`, `save_hivemind`, `load_json`,
  `save_json`). Filesystem helpers (`expert_names`, `get_expert_dir`,
  `get_head_commit`, `ensure_repos_link`, `ensure_external_docs_link`).
- **`constants.py`** — Cross-module constants: cache/opencode dirs,
  analysis-file contracts (`ANALYSIS_DOCS`, `DESCRIPTION_FILENAME`,
  `EXPERTISE_FILENAME`), template placeholders (`{EXPERTS_DIR}`,
  `{TEAMS_DIR}`, `{CACHE_DIR}`), subprocess timeouts. Exists to break the
  old `config.py`↔providers circular import.
- **`models.py`** — Pydantic models. `AppConfig` (enabled/disabled only;
  `config.json`), `HivemindConfig` (engine settings + agent catalog;
  `hivemind.json`), `CatalogEntry` (discriminated union body:
  `GitAnalyzedParams | RosterTemplatedParams`, dispatched via a
  `mode="before"` validator), operation result types.
- **`hooks.py`** — post-mutation listener registry.
  `register_post_mutation(listener)` + `fire_post_mutation()` /
  `afire_post_mutation()`. Per-ingress listeners: CLI does a sync
  `/global/reload-agents` POST, TUI does reload + pane refresh, MCP
  does a sync POST. Reloads are non-destructive — they don't tear down
  the in-flight session; see "MCP mutation semantics" below.
- **`runtime.py`** — `RuntimeContext` (`attached` / `detached` / `test`)
  detected once at ingress startup via `is_server_running()`. Decouples
  opencode from the server module to kill the old circular import.
- **`lifecycle.py`** — kind-agnostic verbs: `enable_agent`,
  `disable_agent`, `delete_agent`, `refresh_agent`,
  `redeploy_all_agents`, `bootstrap_workspace`. Mutations flip
  `config.json:enabled/disabled`, call `Agent.deploy()`/`undeploy()`,
  regenerate librarian, fire the post-mutation hook.
  **`enable_agent` does NOT call `validate_engine`** — enable just
  deploys files; only the creators (`create_git_expert`,
  `update_git_expert`) spawn opencode, so only they validate. This keeps
  the MCP handler fast (~5 ms vs ~900 ms with validation).
- **`deployment.py`** — `regenerate_librarian()` (rebuilds
  `agents/librarian.md` from `registry.enabled()`) and
  `regenerate_hivemind_md()` (rebuilds `HIVEMIND.md` from the Jinja
  template).
- **`cli.py`** — Typer CLI. Thin dispatch; registers the sync reload
  listener at import. No more `_*_cli` print wrappers; progress
  rendering lives in `AnalysisProgress` + `_render_progress()`.
- **`server.py`** — opencode server lifecycle (`start_server`,
  `stop_server`, `is_server_running`, `get_server_url`). State file at
  `~/.cache/hivemind/server.json`.
- **`git.py`** — git subprocess ops (`clone_from_remote`,
  `resolve_latest_commit`, `stage_for_analysis`, `commit_analysis_results`,
  `revert_checkout`, `create_staging_dir`).
- **`analysis.py`** — AI analysis orchestration (`run_async_analysis`,
  `make_cancellation_checker`, `handle_async_cancellation`).
- **`templates.py`** — Jinja2 rendering (`PackageLoader`).

### `crawl/` package (`src/hivemind/crawl/`)

External-doc ingestion that backs `hivemind crawl <url> <expert>`. URL
discovery (`discovery.py`), browser automation via crawl4ai/Playwright
(`browser.py`), trafilatura-based content extraction (`extractor.py`),
URL normalization (`urls.py`), and reachability probing (`probe.py`).
Output lands in `~/.cache/hivemind/external_docs/<expert>/` and is
exposed to the expert as a secondary knowledge source. mypy is relaxed
for this subpackage (see `pyproject.toml`) because crawl4ai/trafilatura
lack type stubs.

### `agents/` package

- **`base.py`** — `Agent` dataclass (name + body + enabled) +
  `AgentBody` Protocol (`kind`, `render`, `librarian_entry`,
  `on_deploy`, `on_undeploy`, `on_delete`, `to_catalog`). Also holds
  `run_coro_sync(coro)` — runs an async coroutine from a sync caller
  that may itself be nested inside a running event loop (via a
  short-lived worker thread when needed). Required for the MCP handler
  path, where `enable_agent` is sync but called from an async context.
- **`registry.py`** — single source of truth for agent CRUD. Loads
  `hivemind.json` + `config.json`, joins into `{name: Agent}`, provides
  `all_agents / get / by_kind / enabled / set_enabled / add / remove /
  save_body`. Uses `isinstance` on the discriminated `CatalogEntry.body`
  to dispatch concrete body classes.
- **`memory.py`** — per-agent memory tree scaffolding at
  `~/.config/opencode/hivemind/memory/<name>/`
  (`MEMORY.md`, `short_memory.md`, `long_memory.md`,
  plus the orchestrator's `_orchestrator/` tree). `ensure_agent_memory`
  is called on enable.
- **`git_analyzed.py`** — `GitAnalyzedBody` (holds typed
  `GitAnalyzedParams`) with protocol methods. Body-specific creators /
  mutators at module scope: `create_git_expert`, `update_git_expert`,
  `switch_version`, `get_git_versions`, `commit_exists_in_repo`.
- **`roster_templated.py`** — `RosterTemplatedBody` (holds typed
  `RosterTemplatedParams`) with protocol methods. Body-specific
  mutators: `create_team`, `update_team`, `add_expert_to_team`,
  `add_experts_to_team`, `remove_expert_from_team`. Roster mutations
  check `agent.enabled` and reject with "team is disabled" otherwise.

### TUI (`src/hivemind/tui/`)

Textual-based TUI with tabbed layout (Experts, Teams). `app.py` registers
two post-mutation listeners in `on_mount` (reload + pane refresh).
`operations.py` holds thin async wrappers translating `ProgressInfo`
events into Textual notifications. `VimDataTable` provides vim-style
navigation.

### MCP (`src/hivemind/mcp/`)

- **`tools.py`** — unified lifecycle surface (`list_agents`,
  `show_agent`, `enable_agent`, `disable_agent`, `delete_agent`,
  `refresh_agent`) + kind-specific creators (`create_git_expert`,
  `create_team`) + team roster tools + knowledge reads
  (`get_knowledge`, `search_knowledge`) + `status`/`redeploy`.
  Post-mutation listeners registered in `register_tools()`. There is NO
  `_MUTATION_TOOLS` dispatcher-level hook anymore; domain mutations fire
  the shared `hivemind.hooks` event themselves.
- **`notify.py`** — `notify_tools_changed(server)` sends
  `ToolListChangedNotification` over the live MCP stdio.
- **`server.py`** — `create_server()` builds the MCP `Server` instance.
- **`prompts.py`** — MCP prompt registrations.

### Deleted modules (do not reintroduce)

`provider.py`, `experts.py`, `teams.py`, `redeploy.py`, `mutations.py` —
all folded into the current layout. `get_active_provider()` is gone;
opencode functions are module-level and importable directly.

### Data flow

1. `hivemind expert add <url>` (CLI) or `create_git_expert` (MCP) →
   clones repo to staging → `run_async_analysis()` generates
   `agent.md` + knowledge docs in `experts/<name>/<commit>/` → moved to
   final location → `HEAD` symlink points to active commit →
   `registry.add(agent)` writes the catalog entry to `hivemind.json`.
   Agent lands in the catalog as **unlisted**. Call `enable_agent` to
   deploy.
2. `enable_agent(name)` → flips `config.json:enabled` →
   `agent.deploy(agents_dir)` → `opencode.format_agent()` +
   `opencode.write_agent_file()` → `body.on_deploy()` (ensures repo is
   cloned + symlinks into opencode's `experts/` dir) →
   `regenerate_librarian()` → `fire_post_mutation()` → post-mutation
   listeners POST `/global/reload-agents` to refresh opencode's agent
   cache without disposing the in-flight session (custom endpoint
   added by `//third_party/patches/0004-Non-destructive-agent-reload-endpoint.patch`).
3. Librarian aggregates every `registry.enabled()` agent into
   `agents/librarian.md` via each body's `.librarian_entry()`.
4. `HIVEMIND.md` is generated once at `bootstrap_workspace()` from
   `templates/hivemind.md.j2`.

### Config files

- **`hivemind.json`** (tracked) — engine settings + agent catalog
  (`agents: dict[str, CatalogEntry]`).
- **`config.json`** (gitignored) — local overlay (`enabled`/`disabled`
  agent names on this machine).

## Patched engine: runtime + presence

The bundled engine is a patched opencode fork. Two things in
`third_party/patches/` are non-obvious enough that future work
should know about them up front:

### Native `Bun.serve` HTTP listener (patch 0017)

Upstream opencode runs Hono on `@hono/node-server` (Node http compat
on Bun). The fork swaps it for native `Bun.serve` —
`createBunWebSocket()` from `hono/bun` for WebSocket upgrades, and
`Bun.serve({ fetch, websocket, port, hostname })` for the listener.
Why: native uSockets/EPOLLRDHUP delivers `req.signal.abort` and
WebSocket close events synchronously; the Node http compat layer
batches socket-close events behind unrelated I/O and was the root
cause of a long disconnect-detection iteration (eleven dead-end
patches before the substrate switch).

`MODULE.bazel:52` pins `ext.bun(version = "1.3.11")` and the
adjacent `ext.opencode(version = "1.4.3", sha256 = ...)` pin the
opencode source. Bump the two in lockstep — opencode's
`package.json:packageManager` declares the Bun version it expects.

### Per-client WebSocket presence (patches 0018 + 0019)

Each connected TUI owns one long-lived WebSocket on `/presence`
for the life of the process. The connection itself is the presence
beacon — when it closes (clean exit, SIGINT, kill, network drop),
the WebSocket protocol's CLOSE frame triggers `onClose` on the
server synchronously and the entry is removed from `_clients`.
Focus updates ride on the same channel as JSON messages:

```
client → server:  { "type": "focus", "sessionID": "ses_..." | null }
```

Server-side state lives in
`packages/opencode/src/server/routes/presence.ts:_clients` (keyed
by the underlying `ServerWebSocket`, not Hono's per-callback
`WSContext` wrapper). Two consumers:

- `GET /global/live-sessions` returns `{ sessions: string[] }` —
  the deduplicated focus values across all clients. Used by the
  TUI footer's "● N sessions" pill on mount.
- `session.live.changed` bus event fires on every mutation. The
  TUI footer subscribes for live updates.

The "● N subagents" pill is **per-TUI**, not derived from
`_clients`. The TUI fetches `client.session.children(focused)`
on focus change and counts. Refetched on `session.created` /
`session.deleted` events whose `parentID` matches the focused
session.

Patch 0018 (`dep_patches/`) regenerates the SDK to expose
`client.global.liveSessions()` and the
`EventSessionLiveChanged` type. Don't introduce a parallel
non-WebSocket channel for presence — the substrate gives reliable
disconnect detection and there's no leak class to mitigate.

Tests for the presence model live at
`packages/opencode/test/server/presence.test.ts`. They spin
native `Bun.serve` with real `WebSocket` clients (no `app.request`
fake-fetch) and exercise the close-frame path. If you add to the
presence model, test against real `Bun.serve`; in-process
fake-fetch hides the disconnect bugs.

## MCP mutation semantics

Mutations via MCP return cleanly without interrupting the session. The
hivemind engine is a patched fork of opencode that exposes
`POST /global/reload-agents` (added by
`//third_party/patches/0004-Non-destructive-agent-reload-endpoint.patch`) which
re-reads `agents/*.md` for every active instance via
`Config.invalidateState()` + `Agent.reload()` — neither calls
`Instance.dispose()`, so MCP subprocesses survive.

History note: until this patch landed, the only invalidation primitive
opencode upstream exposed was `POST /global/dispose`, which tore down
every cached `InstanceState` finalizer including the SIGTERM-the-MCP
finalizer at `mcp/index.ts:527-548`. That killed the in-flight tool
call and required the user to type `continue` to resume.

## Code Conventions

- Modern Python type hints (PEP 604): `str | None`, `list[str]`, etc.
- `from __future__ import annotations` at the top of every module.
- Imports used only for typing live under `if TYPE_CHECKING:` — ruff's
  TC003 rule enforces this.
- Use `typing.assert_never(x)` for exhaustiveness on discriminated
  unions (see `agents/registry.py:_body_from_catalog`,
  `opencode.py:format_agent`, `opencode.py:agent_filename`).
- **Body params are typed.** All `Any` / `dict[str, object]` usages that
  cross the agent-body layer have been replaced with Pydantic
  `GitAnalyzedParams` / `RosterTemplatedParams`. Don't reintroduce loose
  dicts for body params. Remaining `Any` usages are at JSON I/O
  boundaries (generic `load_json`/`save_json`, opencode's own
  `opencode.json` / `tui.json` dicts).
- No backwards-compat shims, re-export facades, or alias layers —
  update callers directly.
- Bazel produces a launcher whose runfiles are symlinks to workspace source — Python edits in `src/hivemind/*.py` are live without rebuild. Only `pyproject.toml` / `uv.lock` / patch / engine-version changes need `make update`.
- When editing experts, edit `experts/<name>/HEAD/agent.md` then
  `hivemind redeploy`. (MCP mutations are non-destructive now, but the
  CLI is still convenient for manual edits.)
- Templates in `templates.py` affect NEW agents only; existing agents
  deploy from their `lead.md` or `agent.md` files.

## When changing MCP-server code

The `hivemind mcp` subprocess is spawned once by opencode and held for
the life of the opencode instance. After editing anything under
`src/hivemind/mcp/` (or anything imported by the MCP handlers),
**restart opencode** so the subprocess loads the new bytecode. The
launcher's runfiles tree is live (symlinks to workspace source), so
source edits are visible immediately — but the subprocess still has to
restart to re-import.
