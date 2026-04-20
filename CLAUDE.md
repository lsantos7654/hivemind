# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

```bash
uv tool install -e .          # Install CLI (editable)
uv run hivemind               # Launch opencode (attaches to running server if present)
uv run hivemind tui           # Open TUI dashboard
uv run hivemind status        # Full dashboard
uv run hivemind redeploy      # Regenerate all agent files
uv run hivemind init          # Set up opencode dirs + orchestrator memory
```

Verify changes:
```bash
uv run pytest                              # run full test suite
uv run pytest tests/test_core.py::test_x   # run single test
uv run ruff check src/                     # lint
uv run ruff format src/                    # format
uv run mypy src/                           # type-check
uv run pre-commit run --all-files          # all hooks
uv run hivemind redeploy                   # smoke test: regenerate all agents
```

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
  `notify_instance_reload()` (POSTs `/global/dispose`). Caches
  `HivemindConfig` and the validation result per process. OpenCode is the
  only backend; the old provider abstraction is gone.
- **`config.py`** — Path constants + JSON I/O primitives (`load_config`,
  `save_config`, `load_hivemind`, `save_hivemind`, `load_json`,
  `save_json`). Filesystem helpers (`expert_names`, `get_expert_dir`,
  `get_head_commit`, `ensure_repos_link`, `ensure_external_docs_link`).
- **`models.py`** — Pydantic models. `AppConfig` (enabled/disabled only;
  `config.json`), `HivemindConfig` (engine settings + agent catalog;
  `hivemind.json`), `CatalogEntry` (discriminated union body:
  `GitAnalyzedParams | RosterTemplatedParams`, dispatched via a
  `mode="before"` validator), operation result types.
- **`hooks.py`** — post-mutation listener registry.
  `register_post_mutation(listener)` + `fire_post_mutation()` /
  `afire_post_mutation()`. Per-ingress listeners: CLI does a sync
  `/global/dispose` POST, TUI does reload + pane refresh, MCP does a sync
  POST (accepts the session interrupt — see "MCP mutation semantics"
  below).
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
   listeners POST `/global/dispose` to invalidate opencode's agent
   cache.
3. Librarian aggregates every `registry.enabled()` agent into
   `agents/librarian.md` via each body's `.librarian_entry()`.
4. `HIVEMIND.md` is generated once at `bootstrap_workspace()` from
   `templates/hivemind.md.j2`.

### Config files

- **`hivemind.json`** (tracked) — engine settings + agent catalog
  (`agents: dict[str, CatalogEntry]`).
- **`config.json`** (gitignored) — local overlay (`enabled`/`disabled`
  agent names on this machine).

## MCP mutation semantics

Mutations via MCP almost always end with `Tool execution aborted`. This
is expected, not a failure. Opencode's `/global/dispose` finalizer
(`mcp/index.ts:527-548`) SIGTERMs the hivemind MCP subprocess as part
of invalidating every `InstanceState`. The mutation lands on disk
*before* the abort — after the user types `continue` to resume, the
new state is visible. `HIVEMIND.md` instructs main to warn the user
before any mutation and verify with a read-only call after resumption.
Do not try to engineer around this; the race is inherent to opencode's
API.

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
- Only editable installs supported (`uv tool install -e .`).
- When editing experts, edit `experts/<name>/HEAD/agent.md` then
  `hivemind redeploy` (MCP mutations abort; prefer CLI for manual
  edits).
- Templates in `templates.py` affect NEW agents only; existing agents
  deploy from their `lead.md` or `agent.md` files.

## When changing MCP-server code

The `hivemind mcp` subprocess is spawned once by opencode and held for
the life of the opencode instance. After editing anything under
`src/hivemind/mcp/` (or anything imported by the MCP handlers),
**restart opencode** so the subprocess loads the new bytecode. The
repo ships as an editable install (`uv tool install -e .`), so source
edits are live — but the subprocess has to restart to re-import.
