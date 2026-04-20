# Hivemind Refactor Plan

## 1. Context

Hivemind manages AI subagents ("experts" and "teams") for a running opencode
instance. The current codebase has accumulated several layering problems:

- **Reload notification spread across ingresses.** A recent commit
  extracted `notify_opencode_reload()` into `mutations.py` and pushed the
  responsibility of calling it onto CLI (12 sites), TUI (7 sites), and MCP
  (centralized dispatcher hook). Adding a new mutation requires touching
  three ingresses.
- **Experts and team leads share no abstraction.** Both are agents written
  as `.md` files consumed by opencode, both have deploy/undeploy cycles,
  both appear in the librarian catalog — but teams can't be enabled /
  disabled, and adding a new kind of agent (local-directory-sourced,
  hand-authored, etc.) requires custom piping at every layer.
- **`Provider` abstraction is speculative.** The `Provider` class has ~20
  methods and exactly one concrete use (opencode). Multi-provider was
  never a product goal.
- **Agents have no durable memory.** Only team-scoped experts have notes
  (`notes.md` as a routing crib for team leads). Solo experts, team
  leads, and the orchestrator have no standard memory convention.
- **Workflow logic inlined in CLI.** `hivemind init` composes a bootstrap
  sequence (symlinks, deploy-all, update librarian, sweep stale,
  notify reload) that only exists inside the CLI command. TUI and MCP
  can't reuse it.
- **Mutable globals and cyclic imports.** `_librarian_dirty` at module
  scope in `deployment.py`; `provider.py` ↔ `server.py` cycle dodged by
  inline imports.

This refactor addresses all of the above in a single big-bang change.

## 2. Target architecture at a glance

```
                       ┌────────────────────────────────┐
                       │        AgentRegistry           │
                       │  hivemind.json (catalog, git)  │
                       │  config.json  (local overlay)  │
                       └──────────────┬─────────────────┘
                                      │
                                      ▼
              ┌─────────────────────────────────────────┐
              │            lifecycle.py                 │
              │  enable / disable / delete / refresh    │
              │  bootstrap_workspace / redeploy_all     │
              │   — kind-agnostic, uniform —            │
              │                                         │
              │  Mutation tail:                         │
              │    agent.deploy() / undeploy()          │
              │    regenerate_librarian()               │
              │    fire_post_mutation()  ──┐            │
              └──┬───────────────────┬─────┘│           │
                 │                   │      │           │
                 │ body-specific     │      │ one hook  │
                 ▼                   ▼      │           │
      ┌─────────────────┐    ┌──────────────┴─────┐     │
      │ agents/git_     │    │ agents/roster_     │     │
      │  analyzed.py    │    │  templated.py      │     │
      │                 │    │                    │     │
      │ create_git_     │    │ create_team        │     │
      │  expert         │    │ add_expert_to_team │     │
      │ update_git_     │    │ remove_expert_...  │     │
      │  expert         │    │ update_team        │     │
      │ switch_version  │    │                    │     │
      └─────────────────┘    └────────────────────┘     │
                                                        │
                             ┌──────────────────────────┴─────┐
                             │         hooks.py               │
                             │   post-mutation registry       │
                             │   fire / afire                 │
                             └──────────┬─────────────────────┘
                                        │
               ┌────────────────────────┼───────────────────────────┐
               ▼                        ▼                           ▼
      ┌────────────────┐        ┌────────────────┐        ┌──────────────────┐
      │ CLI listener   │        │ TUI listener   │        │ MCP listener     │
      │ sync:          │        │ sync:          │        │ async, 500ms     │
      │  opencode.     │        │  reload +      │        │  deferred:       │
      │   reload()     │        │  refresh panes │        │  reload + notify │
      └────────────────┘        └────────────────┘        │   tools changed  │
                                                         └──────────────────┘
  (each ingress registers once at startup; domain does not know who listens)

~/.config/opencode/hivemind/memory/     ◄── per-agent memory tree
  _orchestrator/{MEMORY,short,long}.md
  <agent>/{MEMORY,short,long}.md + topic files
```

## 3. Module layout

**New:**

```
src/hivemind/
├── agents/
│   ├── __init__.py            (re-exports Agent, AgentBody, registry API)
│   ├── base.py                (Agent class + AgentBody protocol)
│   ├── registry.py            (AgentRegistry, catalog + overlay join)
│   ├── memory.py              (memory dir conventions + stub scaffolding)
│   ├── git_analyzed.py        (body strategy: git clone + AI analysis)
│   └── roster_templated.py    (body strategy: team lead roster template)
├── lifecycle.py               (kind-agnostic verbs + bootstrap_workspace)
├── hooks.py                   (post-mutation registry)
├── runtime.py                 (RuntimeContext: attached / detached / test)
├── opencode.py                (opencode-specific funcs — was Provider class)
```

**Kept (modified):**

```
src/hivemind/
├── deployment.py     (librarian regeneration; deploy helpers called by Agent)
├── config.py         (JSON I/O primitives only)
├── analysis.py       (AI analysis subprocess — consumed by GitAnalyzedBody)
├── git.py            (git ops — consumed by GitAnalyzedBody)
├── models.py         (result types; memory types)
├── server.py         (server lifecycle — tightened, no cyclic dep)
├── templates.py      (existing + memory_section template)
├── cli.py            (thinned: dispatch + Rich rendering of progress events)
├── tui/…             (thinned; listener registration in app.on_mount)
└── mcp/
    ├── server.py     (listener registration at startup)
    ├── tools.py      (thinned; unified verbs)
    └── notify.py     (MCP-specific deferred-reload helpers)
```

**Deleted:**

```
src/hivemind/mutations.py            # replaced by hooks.py
src/hivemind/experts.py              # split into agents/git_analyzed.py + lifecycle.py
src/hivemind/teams.py                # split into agents/roster_templated.py + lifecycle.py
src/hivemind/redeploy.py             # absorbed into lifecycle.py
src/hivemind/provider.py             # collapsed into opencode.py (no class)
```

## 4. Data model

All agents — experts, team leads, future kinds — share one enable/disable
paradigm: added to the catalog (unlisted by default), explicitly enabled to
deploy, explicitly disabled to undeploy. Catalog presence is the only
cross-machine concept; enable state is local per machine.

**`hivemind.json`** — committed to git; shared catalog of all agent definitions:

```json
{
  "agents": {
    "chalk": {
      "kind": "git_analyzed",
      "body": {
        "remote": "https://github.com/chalk/chalk",
        "commit": "abc123",
        "ref_name": ""
      }
    },
    "architecture": {
      "kind": "roster_templated",
      "body": {
        "description": "System architecture and API design",
        "experts": ["chalk", "pydantic"]
      }
    }
  },
  "engine": { … existing engine settings … }
}
```

**`config.json`** — not committed; per-machine local overlay:

```json
{
  "enabled": ["chalk", "architecture"],
  "disabled": []
}
```

An agent's state is one of:

- **unlisted** — in catalog, not in either list. No deployed agent file.
  Backing files (cloned repo, team dir) may or may not exist.
- **enabled** — in catalog + `config.json:enabled`. Agent file deployed;
  backing files materialized.
- **disabled** — in catalog + `config.json:disabled`. No deployed agent
  file. Backing files preserved.

An `Agent` materializes by joining the catalog entry with the overlay
(enabled flag comes from `config.json`; body params come from `hivemind.json`).

**No `private` concept.** Dropped entirely in this refactor.
`PRIVATE_EXPERTS_DIR`, `private-repos.json`, `is_private_expert()`, and the
`private: list[str]` field in `config.json` all go away. All experts share
one `experts/<name>/` location and one `~/.cache/hivemind/repos/<name>`
cache. Simpler codebase; users who want private experts use a separate
hivemind workspace or a git-ignored fork.

**One-off migration** at `scripts/migrate_to_unified_config.py`:

- Reads existing `config.json`, `hivemind.json`, `repos.json`, `private-repos.json`, `teams.json`.
- Merges public + private repo entries into a single catalog (private experts
  become regular experts; any `PRIVATE_EXPERTS_DIR/<name>/` directories are
  moved to `EXPERTS_DIR/<name>/`).
- Teams migrate to the catalog with `kind: "roster_templated"`. Team dirs at
  `teams/<name>/` stay where they are.
- Builds unified `hivemind.json` (catalog) and `config.json` (overlay).
- **Namespace collision handling:** if the same name appears in both the
  expert set and the team set, purge *both* entries from the output, log what
  was purged, continue. User re-adds manually if needed. (User confirmed:
  collisions shouldn't exist in practice; if they do, purge.)
- Prints the legacy files it replaced so the user can delete them.
- Runs once manually; not invoked at runtime.

Per user's "no backcompat" preference, the application code only reads the
new shape.

## 5. Agent abstraction

```python
# agents/base.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class AgentBody(Protocol):
    kind: str                                    # "git_analyzed" | "roster_templated" | ...
    def render(self) -> str: ...                 # canonical markdown body
    def librarian_entry(self) -> str: ...        # one-agent entry in librarian.md
    def on_deploy(self) -> None: ...             # per-body deploy side effects
    def on_undeploy(self) -> None: ...           # inverse
    def on_delete(self) -> None: ...             # cleanup backing files
    # Optional (duck-typed):
    # async def refresh(self, *, on_progress=None) -> OperationResult: ...

@dataclass
class Agent:
    name: str
    body: AgentBody
    enabled: bool

    @property
    def kind(self) -> str: return self.body.kind

    @property
    def description(self) -> str: return extract_description(self.body.render())

    def render_for_deploy(self) -> str:
        """Canonical body + appended memory-instructions section."""
        from hivemind.agents.memory import render_memory_section
        return self.body.render() + "\n\n" + render_memory_section(self.name, self.kind)

    def deploy(self) -> None:
        from hivemind.opencode import format_agent, write_agent_file
        content = format_agent(self.kind, self.name, self.render_for_deploy())
        write_agent_file(self.kind, self.name, content)
        self.body.on_deploy()

    def undeploy(self) -> None:
        from hivemind.opencode import remove_agent_file
        remove_agent_file(self.kind, self.name)
        self.body.on_undeploy()
```

**Extension recipe (new agent kind):**

1. Create `agents/<new_kind>.py` with a body class implementing `AgentBody`.
2. Register the kind in `agents/registry.py` kind-dispatch map.
3. Export kind-specific creators from the body module (e.g. `create_<kind>_agent(...)`).
4. Add a single MCP tool for creation (`create_<kind>_agent`); lifecycle verbs work automatically.

## 6. Body strategies

### `GitAnalyzedBody` (was `experts.py`)

- Fields: `remote`, `commit`, `ref_name`. (No `private`.)
- Backing files at `experts/<name>/<commit>/*.md` with a `HEAD` symlink; cloned
  repo at `~/.cache/hivemind/repos/<name>`.
- `render()` — reads `experts/<name>/HEAD/agent.md`, strips frontmatter.
- `on_deploy()` — ensures repo is cloned; symlinks expert dir into opencode's experts location.
- `on_undeploy()` — removes the symlink. Repo cache preserved.
- `on_delete()` — deletes expert dir + cached repo.
- `refresh()` — git fetch + stage + AI analyze + new commit dir + move HEAD.
- Module also exposes: `create_git_expert(name, url, …)` (which adds to
  catalog as *unlisted*), `switch_version(name, commit)`, `get_git_versions(name)`,
  `commit_exists_in_repo(name, commit)`.

### `RosterTemplatedBody` (was `teams.py`)

- Fields: `description`, `experts` (roster).
- Backing files at `teams/<name>/lead.md` (template body) and `teams/<name>/expert-<e>/notes.md` per member.
- `render()` — reads `teams/<name>/lead.md`, injects current roster.
- `on_deploy()` — **ensures member experts' repos are cloned**
  (`clone_repo` for each roster member not already cached on disk). Team
  lead file deployment happens via `Agent.deploy()`. No symlink dir.
- `on_undeploy()` — removes team lead file. Member repos preserved.
- `on_delete()` — removes team dir. Member repos preserved.
- Module also exposes: `create_team(name, description, experts)` (adds to
  catalog as *unlisted*), `add_expert_to_team(team, expert)`,
  `add_experts_to_team(team, experts)`, `remove_expert_from_team(team, expert)`,
  `update_team(name, …)`.

**Teams follow the same unlisted / enabled / disabled paradigm as experts.**

- `create_team(...)` — adds the team to `hivemind.json` catalog. State:
  **unlisted**. No agent file deployed, no repo cloning.
- `enable_agent(team_name)` — moves to `config.json:enabled`. Clones any
  member repos not already cached (via `on_deploy`). Deploys the team
  lead agent file.
- `disable_agent(team_name)` — moves to `config.json:disabled`. Removes the
  team lead agent file (opencode can no longer route to it). Team dir,
  notes, and member repos preserved.
- Roster mutations (`add_expert_to_team`, etc.) on a disabled team return
  an error "team is disabled; enable before modifying".
- `delete_agent(team_name)` — removes from catalog entirely + removes team
  dir. Member expert repos are unaffected (other agents may depend on them).

Enabling a team does NOT auto-enable its member experts. Each expert
governs its own enabled state. If a team is enabled but a member is not,
the team lead's roster still lists the member by name; opencode handles
the missing-agent case on its own.

## 7. Memory system

### Filesystem layout

```
~/.config/opencode/hivemind/memory/
├── _orchestrator/           # user-facing opencode session, not a hivemind agent
│   ├── MEMORY.md            # index
│   ├── short_memory.md      # session/recent — bounded
│   ├── long_memory.md       # consolidated durable knowledge
│   └── <topic>.md           # per-topic pinned memories
└── <agent-name>/
    ├── MEMORY.md
    ├── short_memory.md
    ├── long_memory.md
    └── <topic>.md
```

### Lifecycle integration

- `enable_agent(name)` — ensures `memory/<name>/` exists with stub `MEMORY.md`
  (empty index), `short_memory.md` (empty), `long_memory.md` (empty). Idempotent.
- `disable_agent(name)` — leaves memory untouched.
- `delete_agent(name)` — preserves memory by default. `--purge-memory` flag
  (CLI) or `purge_memory: true` kwarg (MCP) to remove.
- `bootstrap_workspace()` — also ensures `_orchestrator/` memory exists.

### Agent.md memory section

Every deployed `agents/<id>.md` gets an appended section generated by
`templates/memory_section.md.j2`, parameterized by `{{ name }}` and `{{ kind }}`:

```markdown
## Memory

Your durable memory lives at `~/.config/opencode/hivemind/memory/{{ name }}/`.

- `short_memory.md` — your working context: recent observations, the current
  session's findings. Keep this file short; treat it as a scratchpad.
- `long_memory.md` — consolidated durable knowledge that has earned a place
  beyond the current session.
- `MEMORY.md` — index of pinned topic files; one line per entry.

### When to read
At the start of a session, scan `MEMORY.md` for relevant entries, then read
`short_memory.md` for recent context. Pull in `long_memory.md` or topic files
only when the subject at hand is covered by them.

### When to write
Add new observations to `short_memory.md`. When it exceeds ~400 lines, move the
oldest/least-relevant entries into `long_memory.md` (or break out a new topic
file, indexed in `MEMORY.md`) and prune `short_memory.md` back down.

{% if kind == "roster_templated" %}
### Team lead routing
When choosing which expert(s) to recommend, check each candidate's
`MEMORY.md` index and `short_memory.md` for recent work on the topic. Prefer
experts who have durable knowledge pinned in the relevant area.
{% endif %}
```

### Orchestrator memory

`~/.config/opencode/hivemind/memory/_orchestrator/` follows the same layout.
A separate `AGENTS.md` or opencode rules snippet (emitted by
`bootstrap_workspace` into opencode's rules directory) instructs the
orchestrator to read and update it using the same threshold convention.
The user-facing prompt is identical in shape to the big auto-memory block in
`~/.claude/CLAUDE.md`, adapted for opencode paths.

**The consolidation policy is prompt-level, not Python code.** Hivemind
provides the directory structure, the stub files, and the agent.md section
that explains the convention. The subagent decides when to consolidate.

## 8. Post-mutation hook registry

New module `src/hivemind/hooks.py`:

```python
Listener: TypeAlias = Callable[[], None] | Callable[[], Awaitable[None]]

def register_post_mutation(listener: Listener) -> None
def clear_post_mutation() -> None                   # tests
def fire_post_mutation() -> None                    # sync callers
async def afire_post_mutation() -> None             # async callers
```

- Listeners run in registration order.
- Per-listener exceptions are caught and logged — one bad subscriber cannot
  break a mutation.
- `fire_post_mutation` schedules async listeners via `asyncio.create_task` if
  a loop is running; otherwise `asyncio.run`.
- `afire_post_mutation` awaits async listeners inline and calls sync inline.

**Per-ingress listener registration** (once at startup):

- **CLI** (`cli.py` app init):
  `register_post_mutation(lambda: opencode.notify_instance_reload())`
- **TUI** (`HivemindApp.on_mount`): reload listener + pane-refresh listener.
- **MCP** (`register_tools(server)` startup): async listener that schedules
  the 500 ms deferred reload (existing `_deferred_reload` logic) + second
  listener for `notify_tools_changed`. The dispatcher-level `_MUTATION_TOOLS`
  enum and `_post_mutation_reload` branch are **removed**.

The MCP 500 ms deferral is preserved **structurally** — the MCP listener
itself is what defers, not the domain.

## 9. Lifecycle module (`lifecycle.py`)

Kind-agnostic verbs. Each reads from `AgentRegistry`, mutates, calls
`agent.deploy()` / `agent.undeploy()`, regenerates librarian, fires hook.

```python
def enable_agent(name: str) -> OperationResult
def disable_agent(name: str) -> OperationResult
def delete_agent(name: str, *, purge_memory: bool = False) -> OperationResult
async def refresh_agent(name: str, *, on_progress=None) -> OperationResult
def redeploy_all_agents() -> RedeployResult
async def bootstrap_workspace(*, on_progress=None) -> BootstrapResult
```

`bootstrap_workspace` replaces today's inlined `cli.init()` body (lines 464–521):
ensures opencode symlinks, regenerates `HIVEMIND.md`, deploys every enabled
agent, regenerates librarian, sweeps stale agent files, ensures orchestrator
memory, fires hook. Emits `ProgressInfo` events; the CLI renders them via
Rich. The five `_*_cli` progress wrappers are deleted.

## 10. Runtime context (`runtime.py`)

```python
@dataclass(frozen=True)
class RuntimeContext:
    mode: Literal["attached", "detached", "test"]
    server_url: str | None

def current_context() -> RuntimeContext: ...   # cached per-process
def set_context(ctx: RuntimeContext) -> None:  # explicit override (tests)
```

- `attached`: `is_server_running()` returned true at startup. Reload listeners
  perform real HTTP POSTs.
- `detached`: no running server. Reload listeners no-op; lifecycle still writes
  files and subsequent opencode launch picks them up.
- `test`: pytest fixtures set this; listeners no-op, file I/O redirected to
  tmpdir.

Resolves at ingress startup so all downstream code sees a stable value.
Replaces scattered `is_server_running()` calls and kills the
`provider.py` ↔ `server.py` cyclic import (provider no longer imports
`get_server_url`).

## 11. Opencode integration (collapse `provider.py`)

`provider.py` → delete. `Provider` class → delete. Opencode specifics move
to **module-level functions** in `src/hivemind/opencode.py`:

```python
# opencode.py
def validate_engine() -> ValidationResult
def format_agent(kind: str, name: str, body: str) -> str       # dispatches on kind
def write_agent_file(kind: str, name: str, content: str) -> None
def remove_agent_file(kind: str, name: str) -> None
def deploy_backing_dir(name: str, source: Path) -> None        # was deploy_expert
def undeploy_backing_dir(name: str) -> None
def notify_instance_reload() -> bool
def init_dirs(...) -> list[DirInitResult]
def build_analysis_command(...) -> list[str]
def build_query_command(...) -> list[str]
def start_server_command(port, hostname) -> list[str]
def launch_command(extra_args: list[str] | None) -> list[str]
def attach_command(server_url, extra_args) -> list[str]
def permissions() -> dict[str, Any]
def home_dir() -> Path
def teams_base_path() -> Path
def memory_dir() -> Path                                      # new
def orchestrator_memory_dir() -> Path                         # new
```

Callers do `from hivemind import opencode` and call `opencode.format_agent(...)`.
No `get_active_provider()`; no service locator. Constants (`home_dir`, `memory_dir`)
are module-level and lazily computed from opencode config discovery.

## 12. Ingress updates

### CLI (`cli.py`)

- Register post-mutation listener once at app init.
- Remove 12 manual `notify_opencode_reload()` calls + the import.
- Remove the five `_*_cli` helpers (`_deploy_agent_cli`, `_undeploy_agent_cli`,
  `_deploy_expert_cli`, `_clone_repo_cli`, `_update_librarian_cli`).
- `init()` command → calls `lifecycle.bootstrap_workspace(on_progress=...)` and
  renders events to Rich.
- `expert add` / `expert enable` / `expert disable` / … → call
  `lifecycle.enable_agent`, etc. **Remove `--private` flag from `expert add`.**
- **New** `team enable` / `team disable` commands.

### TUI (`tui/operations.py`, `tui/app.py`)

- Register two listeners (reload + pane refresh) in `HivemindApp.on_mount`.
- Remove 7 manual `notify_opencode_reload()` calls + the import.
- Update `operations.py` wrappers to call new `lifecycle.*` verbs; they stay
  thin (progress → Textual notifications).

### MCP (`mcp/tools.py`, `mcp/server.py`)

- Collapse to unified lifecycle tools + kind-specific creators:
  - **Unified:** `list_agents(kind?)`, `show_agent(name)`, `enable_agent(name)`,
    `disable_agent(name)`, `delete_agent(name, purge_memory?)`, `refresh_agent(name)`.
  - **Kind-specific creators:** `create_git_expert(url, ref)` (no `private`),
    `create_team(name, description, experts)`.
  - **Team roster:** `add_expert_to_team(team, expert)`, `remove_expert_from_team(team, expert)`.
  - **Knowledge:** `get_knowledge(expert, doc)`, `search_knowledge(query)`.
  - **System:** `status()`, `redeploy()`.
- **Remove** `_MUTATION_TOOLS` set and the dispatcher-level
  `_post_mutation_reload` branch.
- Register the two MCP listeners (deferred reload + tools-changed) at
  `register_tools(server)` startup, calling into `mcp/notify.py` helpers.

## 13. Migration sequence

One big-bang PR. No compat shims per user preference. Intermediate commits
do not need to be individually runnable; the whole PR lands together.

1. Create `hooks.py`, `runtime.py`, `opencode.py`. Collapse `provider.py` into
   `opencode.py` (flat functions; remove `Provider` class).
2. Create `agents/base.py`, `agents/registry.py`, `agents/memory.py`.
3. Port `experts.py` → `agents/git_analyzed.py`. Delete `experts.py`.
4. Port `teams.py` → `agents/roster_templated.py`. Delete `teams.py`.
5. Create `lifecycle.py` with unified verbs + `bootstrap_workspace`.
   Absorb `redeploy.py`; delete it.
6. Wire hook-firing into every mutation tail (git_analyzed + roster_templated
   + lifecycle).
7. Update `deployment.py`:
   - Remove `_librarian_dirty` global, `mark_librarian_dirty`, dirty-flag check.
     Replace with single `regenerate_librarian(config)`.
   - Adapt `deploy_agent` / `deploy_team_lead` / `update_librarian` to the new
     Agent model.
8. Update `cli.py`: register listener, remove 12 manual calls, remove five
   `_*_cli` helpers, rewrite `init()` to thin wrapper, add `team enable` /
   `team disable` commands, route all expert / team commands through
   `lifecycle.*`.
9. Update `tui/`: register two listeners in `on_mount`, remove 7 manual
   calls, route operations through `lifecycle.*`.
10. Update `mcp/`: collapse tools, remove `_MUTATION_TOOLS`, register listeners
    at startup.
11. Write `templates/memory_section.md.j2`; integrate into `Agent.render_for_deploy()`.
12. Write `scripts/migrate_to_unified_config.py`.
13. Delete `mutations.py`.
14. Run migration script on local machine to rebuild `hivemind.json` / `config.json`.
15. Smoke-test all three ingresses (see §14).

## 14. Verification

- `uv run pytest tests/` — existing tests should pass; update any that
  directly reference deleted modules.
- `Grep notify_opencode_reload` → 0 hits.
- `Grep _MUTATION_TOOLS` → 0 hits.
- `Grep "from hivemind.provider"` → 0 hits.
- `Grep "from hivemind.experts"` / `"from hivemind.teams"` / `"from hivemind.mutations"` / `"from hivemind.redeploy"` → 0 hits.
- End-to-end with opencode server running + TUI attached:
  1. `hivemind expert add <url>` → one `POST /global/dispose` in server logs; TUI refreshes.
  2. `hivemind team create <name> -d <desc> -e <experts>` → team agent deployed; dispose; TUI refreshes.
  3. `hivemind team disable <name>` → `agents/team-lead-<name>.md` removed; dispose.
  4. `hivemind team enable <name>` → file back; dispose.
  5. MCP `enable_agent` from live opencode session → tool result returns successfully; dispose fires ~500ms later; `ToolListChangedNotification` received.
  6. `hivemind init` → bootstraps workspace, creates orchestrator memory, deploys all enabled agents.
- **Memory smoke:** after `enable_agent`, confirm
  `~/.config/opencode/hivemind/memory/<name>/MEMORY.md` / `short_memory.md` /
  `long_memory.md` exist and are empty. After `delete_agent`, confirm the
  directory is preserved (and removed only with `--purge-memory`).
- **Bootstrap smoke:** on a fresh machine, running `hivemind init` from a
  cloned project produces a runnable workspace with all committed agents
  enabled.

## 15. Non-goals

- Not splitting opencode module into `AgentFormatter` / `AgentDeployer` /
  `InstanceNotifier` sub-modules. Flat `opencode.py` is fine; we can split
  later if it grows.
- Not adding a generic event bus with multiple event types — one post-mutation
  event is enough.
- Not implementing automatic memory consolidation in Python. The
  threshold-based compaction is the subagent's job, driven by agent.md prompt.
- Not adding test coverage beyond the smoke verification above. Broader test
  harness is a follow-up.
- Not adding DI for `opencode` module functions — they are module-level and
  overridable via monkeypatch in tests.
- Not implementing multi-provider support. The `Provider` abstraction is
  being removed, not preserved.

## 16. Confirmed decisions

All open questions resolved during design review:

1. **Teams follow the same unlisted / enabled / disabled paradigm as experts.**
   Catalog lives in `hivemind.json` (shared). Enable state in `config.json`
   (local). Enabling a team clones member repos and deploys the team lead.
2. **Orchestrator memory is in scope.** `bootstrap_workspace` creates
   `~/.config/opencode/hivemind/memory/_orchestrator/` and emits the
   opencode rules snippet instructing the orchestrator to use it.
3. **`short_memory.md` threshold: ~400 lines** (in the agent.md template).
4. **Namespace collisions:** migration purges both conflicting entries,
   logs what was purged, continues. (User confirmed collisions shouldn't
   exist in practice.)
5. **`private` is dropped entirely.** No `PRIVATE_EXPERTS_DIR`,
   `private-repos.json`, `is_private_expert()`, or `private` lists.
   Codebase simplified.
