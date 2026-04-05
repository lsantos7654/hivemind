# Hivemind Architecture Plan

Consolidated plan from the codebase audit (AUDIT.md) and architecture team consultation (clean-architecture, design-patterns, Azure architecture-center experts). Dated 2026-04-04. Revised after expert plan review (same date).

---

## Table of Contents

- [Current State Summary](#current-state-summary)
- [Architecture Diagrams](#architecture-diagrams)
- [Decisions](#decisions)
- [Phase 1: Data Models + Critical Bugs + Tests](#phase-1-data-models--critical-bugs--tests)
- [Phase 2: Config Layer + Provider Cleanup](#phase-2-config-layer--provider-cleanup)
- [Phase 3: Librarian Service](#phase-3-librarian-service)
- [Phase 4: Pipeline Extraction](#phase-4-pipeline-extraction)
- [Phase 5: Service Layer (Strangler Fig)](#phase-5-service-layer-strangler-fig)
- [Phase 6: Linting, Mypy, Pre-commit, Tests](#phase-6-linting-mypy-pre-commit-tests)
- [Anti-Patterns Identified](#anti-patterns-identified)
- [Design Pattern Findings](#design-pattern-findings)
- [Strengths to Preserve](#strengths-to-preserve)

---

## Current State Summary

| Module | LOC | Role | Health |
|--------|-----|------|--------|
| `core.py` | 2,496 | All business logic | **God module** — config I/O, expert CRUD, teams, deployment, analysis, symlinks, librarian |
| `cli.py` | 1,463 | Typer CLI | Thin wrapper, mostly good. Markup injection bugs (#3–5 in AUDIT.md) |
| `providers.py` | 924 | Provider abstraction | Well-designed ABC. Some duplication between subclasses |
| `templates.py` | 129 | Jinja2 loader | Clean |
| `crawler.py` | 512 | Web crawler | No tests, silent exception swallowing |
| `tui/` | 2,720 | Textual TUI | Functional but mypy disabled, some Textual anti-patterns |
| **Total** | **~7,750** | | |

### Key problems

1. **God module** — `core.py` has 6+ responsibilities and ~50 private functions
2. **No data models** — ~50 raw dicts passed by string key through the entire stack
3. **Chatty I/O** — `delete_expert()` triggers 5+ JSON reads; `_get_provider()` re-reads config on every call
4. **Sync/async duplication** — `update_expert` and `update_expert_async_internal` are ~1,000 lines of near-identical code
5. **No caching** — librarian fully rebuilt from disk on every mutation (9 call sites)
6. **Critical bugs** — swapped stdout/stderr file descriptors, TOCTOU race on config.json

---

## Architecture Diagrams

### Current

```
┌──────────────────────────────────────────────────────────┐
│                        cli.py                            │
│                   (Typer CLI, 1,463 LOC)                 │
│              Thin wrapper — calls core.py                │
└──────────────────────────┬───────────────────────────────┘
                           │ direct function calls
                           ▼
┌──────────────────────────────────────────────────────────┐
│                   core.py (GOD MODULE)                   │
│                       2,496 LOC                          │
│                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │ Config I/O   │ │ Expert CRUD  │ │ Team Management  │ │
│  │ _load_*()    │ │ enable/      │ │ create/delete/   │ │
│  │ _save_*()    │ │ disable/     │ │ add/remove       │ │
│  │ (5+ reads    │ │ delete/      │ │ expert           │ │
│  │  per op!)    │ │ update       │ │                  │ │
│  └──────────────┘ └──────────────┘ └──────────────────┘ │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ │
│  │ Deployment   │ │ AI Analysis  │ │ Librarian Gen    │ │
│  │ _deploy_*()  │ │ start/finish │ │ _update_librarian│ │
│  │ _undeploy_*  │ │ subprocess   │ │ (full rebuild    │ │
│  │ symlinks     │ │ management   │ │  on EVERY op)    │ │
│  └──────────────┘ └──────────────┘ └──────────────────┘ │
│  ┌──────────────┐ ┌────────────────────────────────────┐ │
│  │ Git Ops      │ │ update_expert x2 (~1000 LOC)       │ │
│  │ clone/fetch  │ │ sync version + async version        │ │
│  │ subprocess   │ │ (near-identical duplication!)        │ │
│  └──────────────┘ └────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────┘
                           │ _get_provider() re-reads config every call
                           ▼
┌──────────────────────────────────────────────────────────┐
│                   providers.py (924 LOC)                 │
│                  ┌──────────────┐                        │
│                  │ Provider ABC │                        │
│                  └──────┬───────┘                        │
│            ┌────────────┴────────────┐                   │
│    ┌───────▼────────┐     ┌─────────▼─────────┐         │
│    │ ClaudeProvider  │     │ OpenCodeProvider  │         │
│    │ (duplicated     │     │ (duplicated       │         │
│    │  deploy/lead)   │     │  deploy/lead)     │         │
│    └────────────────┘     └───────────────────┘         │
└──────────────────────────────────────────────────────────┘

         ┌──────────────┐            ┌──────────────┐
         │ hivemind.json│            │  config.json  │
         │ (shared,     │            │ (local,       │
         │  tracked)    │            │  gitignored)  │
         └──────────────┘            └──────────────┘
```

### Target

```
┌──────────────┐    ┌──────────────┐
│    cli.py    │    │   tui/app.py │
└──────┬───────┘    └──────┬───────┘
       │                   │
       └─────────┬─────────┘
                 │ calls CoreService protocol
                 ▼
┌──────────────────────────────────────────────┐
│          core.py  (composition root)         │
│     Wires ports to use cases. ~200 LOC.      │
└──────────────────┬───────────────────────────┘
                   │
       ┌───────────┼───────────┬──────────────┐
       ▼           ▼           ▼              ▼
┌────────────┐┌──────────┐┌──────────┐┌─────────────┐
│  Expert    ││  Team    ││ Deploy   ││  Update     │
│  Service   ││  Service ││ Service  ││  Pipeline   │
│ enable     ││ create   ││ agent    ││ (shared     │
│ disable    ││ delete   ││ expert   ││  phases,    │
│ delete     ││ add/rm   ││ librarian││  sync+async │
│            ││          ││          ││  wrappers)  │
└─────┬──────┘└────┬─────┘└────┬─────┘└──────┬──────┘
      │            │           │              │
      └────────────┴─────┬─────┴──────────────┘
                         │ depends on ports (protocols)
                         ▼
┌──────────────────────────────────────────────┐
│                    PORTS                      │
│                                              │
│  ProjectConfigRepo   UserConfigRepo          │
│  GitService          ExpertFileStore         │
│  ProviderService (= existing Provider ABC)   │
└──────────────────┬───────────────────────────┘
                   │ implemented by
                   ▼
┌──────────────────────────────────────────────┐
│                  ADAPTERS                     │
│                                              │
│  JsonProjectConfig    JsonUserConfig         │
│  (hivemind.json)      (config.json)          │
│                                              │
│  SubprocessGit        FilesystemExpertStore   │
│  ClaudeProvider       OpenCodeProvider        │
└──────────────────────────────────────────────┘

         ┌──────────────────────────────┐
         │          ENTITIES            │
         │  Expert  Team  RepoEntry     │
         │  Version  AnalysisHandle     │
         │  AppConfig  HivemindConfig   │
         │  OperationResult variants    │
         │  (typed dataclasses, no I/O) │
         └──────────────────────────────┘
```

### Data Flow (unchanged, but typed)

```
  experts/<name>/HEAD/agent.md
         │
         │ read + strip frontmatter
         ▼
  provider.format_agent_md()       ← receives Provider via port, not _get_provider()
         │
         │ add provider-specific frontmatter
         ▼
  agents/expert-<name>.md  ──→  AI coding assistant reads
```

---

## Decisions

Resolved during plan review. These are binding for all phases.

### Error handling contract

Two-tier rule (from clean-architecture expert, grounded in the reference implementation):

- **Infrastructure failures** (network, disk, subprocess crash): use cases **raise exceptions**. `cli.py` catches at each Typer command boundary. TUI async workers catch in `try/except` and post error messages to the Textual app. Never convert these to `OperationResult(success=False)` — that hides tracebacks.
- **Expected domain outcomes** (already enabled, already up-to-date, expert not found): return typed **`OperationResult` subclasses** with boolean discriminators (`already_enabled`, `already_up_to_date`, etc.). These are valid business states the CLI/TUI presents differently, not failures.

### AnalysisHandle disposition

Keep it. It is already the return type of `start_analysis()` at `core.py:543` and consumed by `finish_analysis()` at `core.py:601`. The prior note flagging it as unused was incorrect. Move from `core.py:76` into `models.py`. Current fields are correct. It instantiates the **Command pattern** (encapsulates an in-flight action, not a frozen state snapshot). Add behavioral methods in Phase 4: `poll()`, `wait()`, `cancel()`, `close()`.

### Ports structure

Use a **flat `ports.py`** file, not a sub-package. Five Protocol definitions (~60-80 lines) don't justify 4 files + `__init__.py`. Promote to sub-package only if interface count exceeds ~10-12.

### Phase 2 migration path

**Update all call sites simultaneously.** No shims. A shim that internally calls `_load_config()` is identical to current behavior with extra indirection — defeats the Phase 2 goal. Six call sites total (3 in `cli.py`, 3 in `tui/operations.py`). Each CLI command gains one `config = _load_config()` at the top.

### Phase 3 / Phase 2 dependency

Phase 3 **can land before Phase 2**. `flush()` initially calls `_load_config()` internally (reduces 9 rebuilds to 1, still one config read). After Phase 2, `flush()` gains `config: AppConfig` parameter and the internal load is removed. Full chatty I/O elimination in the librarian path requires both phases.

### `RedeployResult.deployed` field

Remove it. Redundant with `experts_deployed` + `teams_deployed`.

### `ProviderSettings.tools` deserialization

The `list[str] | dict[str, bool]` union type requires a `from_dict()` class method for JSON deserialization. Plain `dataclasses.asdict()` handles serialization, but reading JSON back needs runtime type dispatch.

---

## Phase 1: Data Models + Critical Bugs + Tests

**Goal**: Type safety foundation + fix active correctness issues + regression tests before refactoring.

### 1a. Create `hivemind_cli/models.py`

Dataclass models for all JSON schemas and operation results. No new dependencies — consistent with existing `ProgressInfo`, `AnalysisHandle`, and `tui/models.py`.

#### Config models

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class RepoEntry:
    """A repository registration in hivemind.json."""
    remote: str
    commit: str = ""
    ref_name: str = ""

@dataclass
class TeamData:
    """A team definition in config.json."""
    description: str
    experts: list[str] = field(default_factory=list)

@dataclass
class ProviderSettings:
    """Provider-specific settings."""
    model: str = ""
    tools: list[str] | dict[str, bool] = field(default_factory=list)
    temperature: float | None = None

@dataclass
class ProviderConfig:
    """Provider configuration from hivemind.json."""
    engine: str = ""
    home_dir: str = ""
    settings: ProviderSettings = field(default_factory=ProviderSettings)
    permissions: dict[str, Any] | None = None

@dataclass
class HivemindConfig:
    """Full hivemind.json schema."""
    providers: dict[str, ProviderConfig] = field(default_factory=dict)
    repos: dict[str, RepoEntry] = field(default_factory=dict)

@dataclass
class AppConfig:
    """Full config.json schema."""
    enabled: list[str] = field(default_factory=list)
    disabled: list[str] = field(default_factory=list)
    active_provider: str = ""
    teams: dict[str, TeamData] = field(default_factory=dict)
```

#### Operation result models

```python
@dataclass
class OperationResult:
    """Base result for all operations."""
    success: bool
    error: str | None = None

@dataclass
class UpdateResult(OperationResult):
    new_commit: str = ""
    old_commit: str | None = None
    already_up_to_date: bool = False
    cancelled: bool = False

@dataclass
class EnableResult(OperationResult):
    already_enabled: bool = False

@dataclass
class DisableResult(OperationResult):
    already_disabled: bool = False

@dataclass
class RedeployResult(OperationResult):
    failed: list[str] = field(default_factory=list)
    experts_deployed: list[str] = field(default_factory=list)
    teams_deployed: list[str] = field(default_factory=list)

@dataclass
class SwitchProviderResult(OperationResult):
    old_provider: str = ""
    new_provider: str = ""
    already_active: bool = False
```

#### Migration scope

| File | Change |
|------|--------|
| `core.py` | `_load_config() -> AppConfig`, `_load_hivemind() -> HivemindConfig`, all ops return typed results |
| `providers.py` | `Provider.__init__(config: ProviderConfig)` |
| `cli.py` | `result["error"]` -> `result.error`, `config["enabled"]` -> `config.enabled` |
| `tui/operations.py` | Same callsite updates |
| `tui/models.py` | Move shared models to `models.py`, re-export or merge |

### 1b. Fix critical bugs

| # | Bug | Location | Fix |
|---|-----|----------|-----|
| 1 | **stdout/stderr file descriptors swapped** | `core.py:1139-1141`, `core.py:1616-1618` | Swap the fd assignments |
| 2 | **TOCTOU race on config.json** | `core.py` (multiple read-modify-write cycles) | Atomic write: write to `.tmp` then `os.rename()` |

### 1c. Fix high-severity bugs

| # | Bug | Location | Fix |
|---|-----|----------|-----|
| 3–5 | **Rich markup injection** | `cli.py` (10+ sites) | `from rich.markup import escape`, wrap all interpolated values |
| 6 | **No `encoding="utf-8"`** on file I/O | `core.py` (30+ sites) | Add `encoding="utf-8"` to all `read_text()`/`write_text()` calls |
| 7 | **Non-atomic config writes** | `core.py:117-118` | Write to `.tmp`, then `os.rename()` (same fix as #2) |
| 8 | **Temp file leak** | `core.py:450-477` | Wrap in try/finally to clean up `NamedTemporaryFile` on Popen failure |
| 9 | **Crawler silent exceptions** | `crawler.py:369-370,421-422` | Narrow `except Exception: pass` to `httpx.*` types; let `OSError` propagate; add `logging.debug/warning`. The probe in `supports_raw_markdown` (line 323) is correctly silenced. |
| 10 | **No subprocess timeouts** | `core.py` (all `subprocess.run`) | git clone: 300s, git fetch: 60s, git local ops: 15s, AI analysis: no timeout. Catch `TimeoutExpired` alongside `CalledProcessError`. |
| 11 | **TUI double-fire bug** | `experts_pane.py:267`, `teams_screen.py:99`, `version_detail_screen.py:222` | `on_data_table_row_selected` duplicates Enter binding — fires twice per keypress |
| 12 | **TUI private API usage** | `form_modal.py:18`, `confirmation_modal.py:40` | `_bindings.bind()` is Textual internal — use `BINDINGS` class variable |
| 13 | **TUI sync in async** | `teams_screen.py:76`, `team_detail_screen.py:133,154` | Sync core functions in async callbacks block the event loop — use `asyncio.to_thread()` |

### 1d. Regression tests (before any refactoring)

Set up `pytest` and write regression tests for known bugs:

```
tests/
  __init__.py
  conftest.py          # core_paths fixture (monkeypatches module-level path constants)
  test_core.py         # regression tests + filesystem/config tests
  test_providers.py    # pure string function tests
```

```python
def test_load_json_empty_file(tmp_path):
    """REGRESSION: empty config.json must not crash."""
    p = tmp_path / "empty.json"
    p.write_text("")
    assert _load_json(p) == {}

def test_get_head_commit_returns_str(tmp_path):
    """REGRESSION: must return str, not Path."""
    expert = tmp_path / "expert"
    expert.mkdir()
    (expert / "abc123").mkdir()
    (expert / "HEAD").symlink_to("abc123")
    result = _get_head_commit(expert)
    assert isinstance(result, str)
```

### 1e. `_emit()` helper for progress callbacks

Collapse 20+ scattered `if on_progress: on_progress(ProgressInfo(...))` guard sites into a closure:

```python
def _make_emit(name: str, on_progress: ProgressCallback | None):
    def _emit(phase: UpdatePhase, message: str, **kwargs) -> None:
        if on_progress:
            on_progress(ProgressInfo(expert_name=name, phase=phase, message=message, **kwargs))
    return _emit
```

Purely mechanical substitution — zero behavioral change, reduces noise before Phase 4's pipeline extraction.

---

## Phase 2: Config Layer + Provider Cleanup

**Goal**: Eliminate chatty I/O, fix provider duplication.

### 2a. Config loaded once per invocation

Replace ~30-40 scattered `_load_config()` / `_load_hivemind()` calls with a single load at the top of each CLI command, passed through the call graph.

```python
# Before (chatty — 5+ reads per operation)
def delete_expert(name: str) -> dict:
    config = _load_config()          # read 1
    ...
    _save_config(config)             # write 1
    repos = _load_repos()            # read 2 (calls _load_hivemind)
    ...
    teams = _load_teams()            # read 3 (calls _load_config again!)
    ...
    _update_librarian()              # read 4+ (re-reads config + all agent files)

# After (one read, one write)
def delete_expert(name: str, config: AppConfig, hivemind: HivemindConfig) -> OperationResult:
    ...  # operate on passed-in config objects
    _save_config(config)             # single write at end
```

### 2b. Provider cleanup (quick wins from design-patterns expert)

| Fix | Location | Detail |
|-----|----------|--------|
| Add `@abstractmethod` to `_format_agent_md_internal` | `providers.py:250` | Currently raises `NotImplementedError` without enforcement |
| Promote `deploy_agent`/`undeploy_agent` to base | `providers.py:535,759` | Byte-for-byte identical in both subclasses |
| Extract `format_lead_md` duplication | `providers.py:428,658` | Add `_extra_lead_tools() -> list[str]` hook in base, override in subclasses |

### 2c. Provider session cache (Flyweight)

```python
# Before — reconstructed on every call
def _get_provider() -> Provider:
    config = _load_config()      # disk read
    hivemind = _load_hivemind()  # disk read
    return get_provider(...)

# After — cached for session
_provider_cache: Provider | None = None

def _get_provider(config: AppConfig, hivemind: HivemindConfig) -> Provider:
    global _provider_cache
    if _provider_cache is None:
        _provider_cache = get_provider(config, hivemind)
    return _provider_cache
```

---

## Phase 3: Librarian Service

**Goal**: Eliminate redundant full-rebuild on every mutation.

### Problem

`_update_librarian()` reads every enabled expert's `agent.md` + `summary.md` from disk, rebuilds the full catalog string, and writes `agents/librarian.md`. Called from 9 separate sites:

- `enable_expert`, `disable_expert`, `delete_expert`
- `create_team`, `delete_team`, `update_team`
- `add_expert_to_team`, `remove_expert_from_team`
- `redeploy_all_agents`

### Solution: dirty flag + deferred regeneration

```python
class LibrarianService:
    def __init__(self) -> None:
        self._dirty = False

    def mark_dirty(self) -> None:
        self._dirty = True

    def flush(self, config: AppConfig, hivemind: HivemindConfig, provider: Provider) -> None:
        if self._dirty:
            self._regenerate(config, hivemind, provider)
            self._dirty = False
```

Top-level functions call `librarian.mark_dirty()` after mutations, and `librarian.flush()` once at the end. For `redeploy_all_agents`, one regeneration instead of N.

> **Phase dependency note**: Phase 3 can land before Phase 2. Initially `flush()` calls `_load_config()` internally (reduces 9 rebuilds to 1, still one config read). After Phase 2 lands, `flush()` gains `config: AppConfig` and `hivemind: HivemindConfig` parameters and the internal load is removed. This is a one-line signature change at that point.

---

## Phase 4: Pipeline Extraction

**Goal**: Eliminate ~1,000 lines of sync/async duplication.

### Problem

Three functions implement the same 4-phase workflow:
- `update_expert` (sync, lines 737–977)
- `update_expert_async_internal` (async, lines 980–1314)
- `switch_version_async` (async variant, lines 1315–1820)

### Solution: shared phase pipeline with factory entry points

`switch_version_async` enters the pipeline after `clone_or_fetch` and `resolve_commit` (the target commit is already known). Use factory class methods to model the two entry points:

```python
class UpdatePhaseRunner:
    """Shared update logic. Driven by sync or async caller."""

    @classmethod
    def for_update(cls, name: str, git: GitService) -> "UpdatePhaseRunner":
        """Full pipeline: clone_or_fetch → resolve → stage → analyze → commit → deploy."""
        ...

    @classmethod
    def for_version_switch(cls, name: str, target_commit: str) -> "UpdatePhaseRunner":
        """Partial pipeline: stage → analyze → commit → deploy. Commit already known."""
        ...

    # Shared phases (called by both entry points)
    def stage_version(self, name: str, commit: str) -> Path: ...
    def analyze(self, name: str, commit_dir: Path, provider: Provider) -> None: ...
    def commit_version(self, name: str, commit: str) -> None: ...
    def update_head(self, name: str, commit: str) -> None: ...
    def deploy(self, name: str, provider: Provider) -> None: ...

# Sync wrapper (CLI)
def update_expert(name: str, ...) -> UpdateResult:
    runner = UpdatePhaseRunner.for_update(name, SubprocessGit())
    ...

# Async wrapper (TUI)
async def update_expert_async(name: str, ...) -> UpdateResult:
    runner = UpdatePhaseRunner.for_update(name, SubprocessGit())
    await asyncio.to_thread(runner.stage_version, ...)
    ...

# Version switch (TUI)
async def switch_version_async(name: str, commit: str, ...) -> UpdateResult:
    runner = UpdatePhaseRunner.for_version_switch(name, commit)
    await asyncio.to_thread(runner.stage_version, ...)
    ...
```

Also fixes: blocking `subprocess.run()` calls in async path (git fetch/rev-parse/checkout should use `asyncio.to_thread` or `asyncio.create_subprocess_exec`).

---

## Phase 5: Service Layer (Strangler Fig)

**Goal**: Decompose `core.py` into use-case modules behind a protocol boundary.

### Strategy

Per the Azure Architecture Center's Strangler Fig pattern: `cli.py` is already the facade. Introduce a `CoreService` protocol between `cli.py` and `core.py`, then extract concerns one at a time.

### Target file structure

```
hivemind_cli/
├── models.py              # Phase 1 — all dataclasses
├── ports.py               # All Protocol interfaces (flat file, ~60-80 lines)
├── use_cases/
│   ├── expert/            # enable, disable, delete, add
│   ├── update/            # UpdatePhaseRunner + sync/async wrappers
│   ├── team/              # create, delete, add/remove expert
│   └── deploy/            # deploy_agent, redeploy_all, LibrarianService
├── adapters/
│   ├── json_project_config.py   # reads/writes hivemind.json
│   ├── json_user_config.py      # reads/writes config.json
│   ├── filesystem_store.py      # experts/ dir operations
│   └── subprocess_git.py        # wraps subprocess git calls
├── core.py                # Composition root — wires ports to use cases (~200 LOC)
├── providers.py           # Stays as-is (well-designed)
├── templates.py           # Stays as-is
├── cli.py                 # Updated in Phase 2 to pass config; calls core.py public API
├── crawler.py             # Stays as-is
└── tui/                   # Unchanged
```

### Migration order (within this phase)

1. Define `CoreService` protocol matching current `core.py` public functions
2. `cli.py` imports `CoreService` — initially just `core.py` implementing it
3. Extract `ConfigStore` adapter (eliminates `_load_*`/`_save_*` from core)
4. Extract `DeploymentService` (eliminates `_deploy_*`/`_undeploy_*` from core)
5. Extract `GitService` adapter (eliminates subprocess git calls from core)
6. Extract `AnalysisService` (eliminates subprocess AI calls from core)
7. `core.py` becomes composition root only

---

## Phase 6: Linting, Mypy, Pre-commit, Tests

Detailed plans for each are in [AUDIT.md](AUDIT.md). Summary:

### Linting (ruff)

- **Tier 2 — enable soon** (~68 violations): `TC`, `TRY`, `EM`, `C90` (max-complexity=15), `ARG`, `T20`
- **Tier 3 — enable later**: `ANN` (58), `PL` (49 real), `S` (13 real), `BLE001` (27)
- **Skip**: `FBT`, `D`, `SLF`, `COM812`

### Mypy

- Target: `strict = true`
- 44 of 45 strict violations are bare `dict`/`Popen` — **eliminated by Phase 1 model migration**
- Remove `ignore_errors = true` on TUI (0 errors under strict already)
- Scope `ignore_missing_imports` to `crawl4ai.*` only

### Pre-commit

Add: `no-commit-to-branch`, `detect-private-key`, `check-json`, `check-ast`, `debug-statements`, `check-symlinks`, `destroyed-symlinks`. Reorder hooks: safety first, formatters, validators, mypy last. Full target config in AUDIT.md.

### Tests

- Framework: `pytest >= 8.0.0`
- Layout: `tests/conftest.py` (core_paths fixture), `test_core.py`, `test_providers.py`
- Regression tests for known bugs (empty config crash, `_get_head_commit` returning Path)
- Coverage targets: `_load_json`, `_save_json`, `_expert_names`, `_get_head_commit`, `extract_description`, `strip_frontmatter`, `get_provider`

---

## Anti-Patterns Identified

From the Azure Architecture Center expert, grounded in the antipatterns catalog:

| Anti-Pattern | Evidence | Severity |
|---|---|---|
| **Chatty I/O** | `delete_expert` = 5+ JSON reads across 3 files, no batching | High |
| **Synchronous I/O** | CLI path uses `time.sleep(1)` busy-wait; async path has blocking `subprocess.run()` for git ops | High |
| **Busy Database** (filesystem analog) | `_update_librarian()` full-scans N expert files on every mutation, 9 call sites | High |
| **No Caching** | Provider rebuilt every call; librarian fully re-parsed on every enable/disable/team change | High |
| **No Compensating Transaction** | HEAD symlink update + repos.json write are not atomic — crash between them = inconsistent state | Medium |

---

## Design Pattern Findings

From the design-patterns expert, grounded in GoF pattern definitions:

| Pattern | Status | Recommendation |
|---|---|---|
| **Template Method** (`Provider.init_dirs`) | Correctly applied | Keep as-is |
| **Template Method** (`_format_agent_md_internal`) | Missing `@abstractmethod` | Add decorator |
| **Strategy** (abstract methods on Provider) | Correctly applied | Keep as-is |
| **Observer** (`ProgressCallback`) | Single-observer, callback-style | Fine for current use; extract `_emit()` helper for 15 scattered call sites |
| **Flyweight** (`_get_provider()`) | Missing — rebuilds on every call | Add session cache |
| **Facade** (`enable_expert()`) | Implicit — mixes sequencing with inline config mutation | Clarify boundary |
| **Command** (deploy chain) | Not present | Premature for now; add transaction wrapper instead of full Command objects |
| **Bridge** (provider path construction) | Not present | Forward-looking; add `PathResolver` if a third provider is added |

### Provider duplication (highest-priority refactor)

| Duplication | Lines | Fix |
|---|---|---|
| `deploy_agent` identical in both providers | `providers.py:535` / `providers.py:759` | Promote to base |
| `undeploy_agent` identical in both providers | Same area | Promote to base |
| `format_lead_md` duplicated | `providers.py:428` / `providers.py:658` | Base method + `_extra_lead_tools()` hook |

---

## Strengths to Preserve

These are well-designed and should not be disrupted during refactoring:

1. **Provider ABC** (`providers.py`) — clean abstraction, easy to add platforms
2. **Versioned expert knowledge** — commit-based snapshots with HEAD symlink
3. **Jinja2 templates** — clean separation of generation logic from templates
4. **TUI** — functional vim keybindings, search, lazy loading
5. **Platform-neutral agent format** — `agent.md` deployed to any provider via frontmatter transform
6. **Team lead self-management** — leads can update their own `lead.md`
7. **Two-config split** — `hivemind.json` (shared) vs `config.json` (local) is the right domain distinction

---

## Verification

After each phase, run:

```bash
uv run hivemind expert list
uv run hivemind team list
uv run hivemind redeploy
uv run hivemind status
uv run python -c "from hivemind_cli.core import redeploy_all_agents; print('OK')"
```

---

## Sources

- **AUDIT.md** — Full codebase audit (2026-04-03/04) with expert agents for Typer, Textual, Rich, Jinja2, architecture, and linting
- **expert-node.js-clean-architecture** — Clean architecture decomposition analysis (layering, entities, ports, composition root)
- **expert-design-patterns-for-humans** — GoF pattern audit (Template Method, Strategy, Observer, Flyweight, Command)
- **expert-architecture-center** — Azure antipatterns catalog + Strangler Fig decomposition strategy + Cache-Aside, CQRS, Pipes and Filters applicability
