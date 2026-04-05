# Hivemind Architecture Refactor Plan

## Context

An architecture audit by three experts (clean-architecture, software-architecture-patterns, cosmicpython) identified `core.py` as a God Module (~2000 lines, 60 functions, 9 concerns). Additional debt: no DI (functions resolve their own dependencies), cli.py imports 22 private functions, Provider takes untyped `dict`, the `config: AppConfig | None = None` pattern is a DI workaround, and `Any` is used throughout models.py because dataclasses lack built-in validation/serialization. Migrating to Pydantic eliminates `Any`, removes all manual `from_dict`/`to_dict` boilerplate, and types the Provider boundary for free.

## Phase 1: Migrate models.py to Pydantic

**Goal**: Replace dataclasses with Pydantic `BaseModel`. Eliminate all `Any` usage, delete all manual `from_dict`/`to_dict` methods.

### Step 1a: Add pydantic dependency
- `uv add pydantic`

### Step 1b: Convert each dataclass to BaseModel

Every model in `models.py` follows the same transformation:

```python
# BEFORE (dataclass + Any)
@dataclass
class RepoEntry:
    remote: str
    commit: str = ""
    ref_name: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RepoEntry:
        return cls(remote=data.get("remote", ""), ...)

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"remote": self.remote}
        ...
        return d

# AFTER (Pydantic — no Any, no manual methods)
class RepoEntry(BaseModel):
    remote: str
    commit: str = ""
    ref_name: str = ""
```

Models to convert (all in `models.py`):
- `RepoEntry` — drop `from_dict`, `to_dict`
- `TeamData` — drop `from_dict`, `to_dict`
- `ProviderSettings` — drop `from_dict`, `to_dict`. Note: `tools` field is `list[str] | dict[str, bool]` (union type — Pydantic handles this natively)
- `ProviderConfig` — drop `from_dict`, `to_dict`. Nested `ProviderSettings` validated automatically
- `HivemindConfig` — drop `from_dict`, `to_dict`. Nested `dict[str, ProviderConfig]` validated automatically
- `AppConfig` — drop `from_dict`, `to_dict`. Nested `dict[str, TeamData]` validated automatically
- `OperationResult` and subclasses (`UpdateResult`, `EnableResult`, `DisableResult`, `RedeployResult`, `SwitchProviderResult`, `AddExpertsResult`) — simple conversion, no from_dict/to_dict to remove
- `ProgressInfo` — simple conversion
- Keep `CancellationToken` as a regular class (it has behavior, not data)
- Keep `AnalysisHandle` as a dataclass for now (has mutable state + subprocess.Popen; moved in Phase 6)

### Step 1c: Update all call sites

Replace throughout codebase:
- `SomeModel.from_dict(data)` → `SomeModel.model_validate(data)` or `SomeModel(**data)`
- `instance.to_dict()` → `instance.model_dump(exclude_defaults=True)` (to match current behavior of omitting empty/default fields)
- `json.loads(text)` + `Model.from_dict(data)` → `Model.model_validate_json(text)` (single step)

Key call sites in `core.py`:
- `_load_config()` (line 112): `AppConfig.from_dict(data)` → `AppConfig.model_validate(data)`
- `_save_config()` (line 119): `config.to_dict()` → `config.model_dump(exclude_defaults=True)`
- `_load_hivemind()` (line 123): same pattern
- `_save_hivemind()` (line 128): same pattern
- `_load_private_repos()` (line 178): same pattern
- `_save_private_repos()` (line 189): same pattern

### Step 1d: Update providers.py

`Provider.__init__` currently takes `config: dict` and does `.get()` calls. With Pydantic models available, change to accept `ProviderConfig` directly (this absorbs Phase 4 from the original plan):
- `Provider.__init__(self, config: ProviderConfig, *, providers_dir: Path | None = None)`
- `self._settings: ProviderSettings` instead of `dict`
- All `self._settings.get("model", "")` → `self._settings.model`
- All `self._settings.get("tools", [])` → `self._settings.tools`
- `self._config.get("permissions")` → `self._config.permissions`
- `get_provider(name, provider_config: ProviderConfig, ...)` instead of `dict`
- In core.py `_get_provider()`: pass `prov` directly instead of `prov.to_dict()`

### Step 1e: Remove `Any` import
- Remove `from typing import Any` from `models.py` (only keep `IO`, `TYPE_CHECKING`)
- Verify no `Any` remains in models.py

**Verification**: `uv run hivemind expert list`, `uv run hivemind team list`, `uv run hivemind redeploy`, `uv run hivemind`

---

## Phase 2: Split core.py into modules

**Goal**: Break the god module into 6 focused modules. Backwards-compatible via re-exports from core.py.

### New modules (all under `hivemind_cli/`):

**`config.py`** — Config I/O, path constants, filesystem helpers, provider cache
- Path constants: `HIVEMIND_ROOT`, `CACHE_DIR`, `REPOS_DIR`, `REPOS_LINK`, `EXTERNAL_DOCS_DIR`, `EXTERNAL_DOCS_LINK`, `HIVEMIND_JSON`, `CONFIG_JSON`, `PRIVATE_REPOS_JSON`, `AGENTS_DIR`, `EXPERTS_DIR`, `COMMANDS_DIR`, `PRIVATE_EXPERTS_DIR`, `TEAMS_DIR`, `PROVIDERS_DIR`, `HIVEMIND_MD`
- Timeout constants: `GIT_CLONE_TIMEOUT`, `GIT_FETCH_TIMEOUT`, `GIT_LOCAL_TIMEOUT`
- Config I/O: `_load_json`, `_save_json`, `_load_config`, `_save_config`, `_load_hivemind`, `_save_hivemind`, `_load_teams`, `_save_teams`, `_load_repos`, `_save_repos`, `_load_private_repos`, `_save_private_repos`
- Provider cache: `_provider_cache`, `_get_provider`, `_invalidate_provider_cache`
- Progress helper: `_make_emit`
- Filesystem helpers: `_is_private_expert`, `_get_expert_dir`, `_get_repos_for_expert`, `_expert_names`, `_get_head_commit`, `_count_versions`, `_ensure_repos_link`, `_ensure_external_docs_link`

**`git.py`** — Git subprocess operations
- `_clone_repo`, `_resolve_latest_commit`, `_revert_checkout`, `commit_exists_in_repo`
- `_stage_for_analysis`, `_commit_analysis_results`, `_save_commit_to_repos`

**`analysis.py`** — AI analysis orchestration
- `_analyze_repo`, `_expected_analysis_files`, `start_analysis`, `finish_analysis`
- `_run_async_analysis`, `_read_analysis_error`, `_cleanup_log_files`
- `_make_cancellation_checker`, `_handle_async_cancellation`

**`deployment.py`** — Agent deployment, librarian, HIVEMIND.md
- `_deploy_agent`, `_undeploy_agent`, `_deploy_expert`, `_undeploy_expert`
- `redeploy_all_agents`, `_regenerate_hivemind_md`
- `_deploy_team_lead`, `_undeploy_team_lead`
- Librarian: `_librarian_dirty`, `_mark_librarian_dirty`, `_flush_librarian`, `_update_librarian`

**`experts.py`** — Expert lifecycle
- `update_expert`, `update_expert_async_internal`, `switch_version_async`, `get_git_versions`
- `enable_expert`, `disable_expert`, `delete_expert`
- `switch_provider`

**`teams.py`** — Team management
- `create_team`, `delete_team`, `update_team`
- `add_expert_to_team`, `add_experts_to_team`, `remove_expert_from_team`
- `_generate_expert_section`, `_remove_expert_section`
- `_create_expert_notes_stub`, `_refresh_expert_notes_header`, `_refresh_team_lead_body`

### core.py becomes a re-export facade:
```python
from hivemind_cli.config import *
from hivemind_cli.git import *
from hivemind_cli.analysis import *
from hivemind_cli.deployment import *
from hivemind_cli.experts import *
from hivemind_cli.teams import *
```

Each new module defines `__all__` listing every exported symbol (including underscore-prefixed ones for backwards compat).

**Verification**: `uv run hivemind expert list`, `uv run hivemind team list`, `uv run hivemind redeploy`, `uv run hivemind`

---

## Phase 3: Eliminate `config: AppConfig | None = None` pattern

**Goal**: Make `config` a required parameter. Callers load once and pass through.

**Functions to change** (remove `| None = None`, make required):
- `experts.py`: `enable_expert`, `disable_expert`, `delete_expert`, `switch_provider`
- `deployment.py`: `redeploy_all_agents`, `_regenerate_hivemind_md`, `_flush_librarian`, `_update_librarian`

**Callers to update**:
- `cli.py`: Add `config = _load_config()` at top of each command, pass to functions
- `tui/operations.py`: Already loads config — just pass it through
- Internal cross-module calls: Thread config from the function that already has it

**Verification**: Same as Phase 2

---

## Phase 4: Public API surface + extract `add()` from cli.py

**Goal**: (a) Rename private functions that are genuinely public API. (b) Move `add()` business logic into `experts.py`. (c) Update all imports to use specific modules.

### Step 3a: Make functions public (remove underscore)

In `config.py`:
- `_load_config` → `load_config`
- `_save_config` → `save_config`
- `_load_repos` → `load_repos`
- `_save_repos` → `save_repos`
- `_load_private_repos` → `load_private_repos`
- `_save_private_repos` → `save_private_repos`
- `_load_hivemind` → `load_hivemind`
- `_load_teams` → `load_teams`
- `_expert_names` → `expert_names`
- `_get_expert_dir` → `get_expert_dir`
- `_get_head_commit` → `get_head_commit`
- `_count_versions` → `count_versions`
- `_is_private_expert` → `is_private_expert`
- `_ensure_repos_link` → `ensure_repos_link`
- `_ensure_external_docs_link` → `ensure_external_docs_link`
- `_get_provider` → `get_active_provider`

Keep underscore aliases in `__all__` for backwards compat via core.py facade.

### Step 3b: Extract `add_expert()` from cli.py

Create in `experts.py`:
```python
def add_expert(
    url: str,
    ref: str | None = None,
    private: bool = False,
    on_progress: ProgressCallback | None = None,
) -> AddExpertResult:
```

Add to `models.py`:
```python
@dataclass
class AddExpertResult(OperationResult):
    name: str = ""
    commit: str = ""
    expert_dir: str = ""
```

### Step 3c: Update cli.py imports
```python
from hivemind_cli.config import load_config, load_repos, get_active_provider, ...
from hivemind_cli.experts import add_expert, enable_expert, ...
from hivemind_cli.deployment import redeploy_all_agents
from hivemind_cli.teams import create_team, delete_team, ...
```

### Step 3d: Update tui/ imports similarly

**Verification**: Full CLI command suite + TUI launch

---

## Phase 5: Move AnalysisHandle to analysis.py

**Goal**: Remove subprocess.Popen coupling from models.py.

- Move `AnalysisHandle` dataclass from `models.py` to `analysis.py`
- It already imports subprocess — the coupling is appropriate there
- Update imports in any file that uses `AnalysisHandle`

**Verification**: `uv run python -c "from hivemind_cli.analysis import AnalysisHandle; print('OK')"`

---

## What is NOT addressed (and why)

- **Protocol ports (ports.py)**: Deferred — only one implementation exists for git/filesystem/config. Protocols add ceremony without value until a second impl appears (e.g., in-memory for testing).
- **Event model**: The imperative call pattern (mark dirty → flush) works at this scale. Domain events would add significant complexity.

## Critical files
- `hivemind_cli/models.py` — Pydantic migration (Phase 1), AddExpertResult addition (Phase 4)
- `hivemind_cli/providers.py` — Provider.__init__ typing (Phase 1)
- `hivemind_cli/core.py` — split into 6 modules, becomes re-export facade (Phase 2)
- `hivemind_cli/cli.py` — import rewiring + add() extraction (Phase 4)
- `hivemind_cli/tui/operations.py` — import rewiring (Phase 4)
- `hivemind_cli/tui/app.py` — import rewiring (Phase 4)
- `pyproject.toml` — add pydantic dependency (Phase 1)
