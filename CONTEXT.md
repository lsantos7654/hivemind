# Session context

Handoff note for the next session. This file summarises the current state
of the codebase, what we did to get here, and what's still open, so you
can resume without replaying the full transcript.

## What this codebase is

Hivemind is an agent catalog manager for opencode. Users register
"experts" (git-backed repos, AI-analyzed into knowledge docs) and
"teams" (team-lead agents assembled from rosters of members); hivemind
keeps the deployed `agents/*.md` files opencode reads in sync with that
catalog. CLI + TUI + MCP surfaces all route through the same
`lifecycle.py` verbs.

## Current state (2026-04-20)

- **Architecture landed.** The big layering refactor plus a subsequent
  Pydantic-params pass are in place. `refactor.md` has the full plan.
- **Tests:** 27/27 passing.
- **Pre-commit:** all hooks green (ruff, ruff-format, mypy).
- **Catalog:** 89 agents in `hivemind.json`; `bazel` is the only one
  enabled locally (`config.json`).
- **Opencode server:** running on `127.0.0.1:4096` (PID tracked in
  `~/.cache/hivemind/server.json`).

## How to resume

```bash
uv run pytest tests/           # confirm baseline
uv run hivemind status         # dashboard
uv run hivemind expert list    # 89 agents, 1 enabled
```

Then read:

1. `refactor.md` — the big-picture architectural plan. Covers the layering
   model, post-mutation hook registry, Agent abstraction, memory system,
   config split, and open follow-ups.
2. `CLAUDE.md` — module-by-module orientation + code conventions.
3. `HIVEMIND.md` — what the orchestrator sees in-session. Includes the
   MCP mutation abort-and-continue section.
4. `todo.md` — user's personal TODO.

## Known constraints (gotchas)

- **MCP mutations interrupt the session.** Every mutation tool
  (`enable_agent`, `disable_agent`, `delete_agent`, `refresh_agent`,
  `create_git_expert`, `create_team`, `add_expert_to_team`,
  `remove_expert_from_team`, `redeploy`) will end with "Tool execution
  aborted". The mutation lands on disk before the abort. Main should
  warn the user, the user types `continue`, then main verifies with a
  read-only call. Documented in `HIVEMIND.md`. Do not try to fix; the
  race is inherent to opencode's `/global/dispose` primitive (see
  `refactor.md` for the expert-opencode analysis).
- **Mutations from the `Bash` tool inside opencode also abort.** Same
  underlying race. Only mutations from a terminal *outside* opencode are
  race-free.
- **Restart opencode after editing MCP-server code.** The `hivemind mcp`
  subprocess is spawned once by opencode and holds its bytecode for the
  life of the instance. Source is an editable install (`uv tool install
  -e .`), so edits are live — but the subprocess re-imports only after
  restart.
- **`enable_agent` deliberately skips `validate_engine`.** Previously
  added ~900 ms to the handler, which blew the MCP response-flush
  window. Creators still validate (`create_git_expert`,
  `update_git_expert`), and `opencode.validate_engine` caches its
  result per process.

## Open follow-ups

### From `refactor.md` (architectural)

- **Provider-class split.** The old `Provider` was collapsed into flat
  module functions in `opencode.py`. A further split into
  `AgentFormatter` / `AgentDeployer` / `InstanceNotifier` was flagged
  but not done. Worth it only if `opencode.py` grows much further.
- **Proper DI.** `get_active_provider` is gone, but `opencode` is still
  imported as a module everywhere. Tests monkeypatch module functions.
  Full DI is a separate undertaking.
- **Dynamic MCP tools.** The cleanest fix for the dispose race is to
  serve experts as dynamic MCP tools via `notifications/tools/list_changed`
  on the live stdio channel — no file-cache invalidation needed. Big
  refactor; would require modelling agent bodies as tool schemas, which
  is a poor fit for markdown knowledge docs. Noted, out of scope.

### From `todo.md` (user)

- MCP tool for updating agents / picking a specific version/tag/commit.
- Background agents as a plugin.
- Orchestrator memory under `~/.config/opencode/` (scaffold exists in
  `opencode.orchestrator_memory_dir()` + `agents/memory.ensure_orchestrator_memory`;
  bootstrap_workspace() calls it; nothing prompts the orchestrator to
  use it yet).
- Explicit attached/detached runtime strategies (scaffold exists in
  `runtime.RuntimeContext`; not yet surfaced as behavior difference).
- Fix `hivemind` no-arg splash — the ASCII banner shows stale "opencode"
  info (see `todo.md` for the example).

## Recent work summary

Ordered chronologically in this session:

1. **Audit + big refactor** of the hivemind codebase. Consulted
   architecture team (expert-architecture-center,
   expert-design-patterns-for-humans, expert-system-design-primer).
   Introduced the `agents/` package (`base`, `registry`, `memory`,
   `git_analyzed`, `roster_templated`), `lifecycle.py`, `hooks.py`,
   `runtime.py`, `opencode.py`. Deleted `provider.py`, `experts.py`,
   `teams.py`, `redeploy.py`, `mutations.py`. Config split into
   shared-committed `hivemind.json` (catalog) and local
   `config.json` (enabled/disabled overlay). Memory tree at
   `~/.config/opencode/hivemind/memory/`. Migrated existing
   `hivemind.json` / `config.json` / `private-repos.json` / `teams.json`
   via `scripts/migrate_to_unified_config.py` (one-off, ran once).
2. **MCP dispose race.** Tried an in-process asyncio defer, then a
   detached-grandchild subprocess hack, then accepted the abort.
   Final shape: sync POST at the MCP listener + documented
   abort-and-continue in `HIVEMIND.md`.
3. **`validate_engine` optimization.** Cached per process
   (`_engine_validated` in `opencode.py`) + removed from
   `lifecycle.enable_agent`. Handler latency 900 ms → 5 ms.
4. **`run_coro_sync` helper** (`agents/base.py`). Fixed an
   `asyncio.run() cannot be called from a running event loop` crash
   when `GitAnalyzedBody.on_deploy` (sync) was invoked from an MCP
   handler (async). Thread-pool offload when a loop is already running.
5. **Pydantic params conversion.** `GitAnalyzedParams` and
   `RosterTemplatedParams` in `models.py` with `extra="forbid"` and
   `validate_assignment=True`. `CatalogEntry.body` is a discriminated
   union with a `mode="before"` validator that dispatches on `kind`.
   Body classes hold `self.params: <Params model>`; internal accesses
   go through `self.params.commit`, `self.params.experts`, etc.
   External accessors (`tui/app.py`) updated.
6. **Pre-commit pass.** TC003 imports moved under `TYPE_CHECKING`,
   PERF401 / C416 / ERA001 / F841 / E501 fixes, `assert_never` for
   exhaustiveness, `ToolHandler` type alias in `mcp/tools.py` to fix
   the `no-any-return` mypy warning. All hooks green.
7. **HIVEMIND.md update.** Added the "Agent lifecycle — read this first"
   section, the "MCP mutations will interrupt the session — expected"
   section, updated MCP tool names, updated CLI command list, added
   "Mutations interrupt, reads don't" to Key Principles.

## Files to look at first

- `refactor.md` — the architectural plan (~400 lines; go here for *why*)
- `CLAUDE.md` — module guide (rewritten this session)
- `HIVEMIND.md` — what the orchestrator sees; documents the mutation
  abort flow
- `src/hivemind/lifecycle.py` — kind-agnostic mutation verbs
- `src/hivemind/agents/base.py` — Agent + Protocol + `run_coro_sync`
- `src/hivemind/agents/registry.py` — CRUD source of truth
- `src/hivemind/hooks.py` — post-mutation hook registry
- `src/hivemind/models.py` — `GitAnalyzedParams`, `RosterTemplatedParams`,
  `CatalogEntry` discriminated union
- `src/hivemind/mcp/tools.py` — MCP tool surface + listener registration

## Backup / safety notes

- Pre-migration `hivemind.json` and `config.json` backed up at
  `/tmp/hivemind-migration-test/` (from the first migration). The
  current `hivemind.json` shape is the target shape — don't roll back
  unless intentional.
- No git commits were made during this session; all work is in the
  working tree. User should review + commit.
