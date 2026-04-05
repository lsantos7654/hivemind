# Hivemind Codebase Audit & Strictness Plan

Full audit conducted 2026-04-03/04 using expert agents for Typer, Textual, Rich, Jinja2, architecture/security, and linting analysis.

---

## Table of Contents

- [Current Tooling State](#current-tooling-state)
- [Audit Findings by Severity](#audit-findings-by-severity)
- [Dict-to-Model Migration](#dict-to-model-migration)
- [Linting Strictness Plan](#linting-strictness-plan)
- [Mypy Strictness Plan](#mypy-strictness-plan)
- [Pre-commit Hardening](#pre-commit-hardening)
- [Test Suite Plan](#test-suite-plan)

---

## Current Tooling State

### Ruff (lint + format)

```toml
[tool.ruff]
target-version = "py310"
line-length = 120

[tool.ruff.lint]
select = [
    "E", "W", "F", "I", "UP", "B", "SIM", "RUF",
    "PIE", "PERF", "FURB", "RET", "PTH",
    "C4", "RSE", "ICN", "ERA", "LOG", "G",
]
ignore = ["E501", "SIM108", "RUF012"]
```

### Mypy

```toml
[tool.mypy]
python_version = "3.10"
show_error_codes = true
strict = false  # 7 of 14 strict flags enabled individually
ignore_missing_imports = true  # too broad — only crawl4ai needs this
```

Per-module overrides: TUI (`ignore_errors = true`), core/cli/crawler (relaxed `disallow_untyped_defs`).

### Pre-commit

Ruff lint+format, pre-commit-hooks (trailing whitespace, EOF, yaml/toml checks, large files, merge conflicts, mixed line endings), mypy via local hook with `uv run`.

---

## Audit Findings by Severity

### CRITICAL

| # | Area | Location | Issue |
|---|------|----------|-------|
| 1 | Architecture | `core.py:1139-1141`, `core.py:1616-1618` | **stdout/stderr file descriptors are swapped** in async subprocess calls — stdout goes to stderr file and vice versa, causing inverted error diagnostics |
| 2 | Architecture | `core.py` (multiple) | **Race condition in config.json** read-modify-write cycles (TOCTOU) — concurrent TUI operations can silently overwrite each other's config changes |

### HIGH

| # | Area | Location | Issue |
|---|------|----------|-------|
| 3 | Rich | `cli.py:702,723,749,800,896,1003,1055,1068,1084,1105` | **Markup injection**: `result['error']` interpolated unescaped inside `[error]...[/error]` tags — strings with `[` (e.g. `[Errno 13]`) break rendering. Fix: `from rich.markup import escape` |
| 4 | Rich | `cli.py:1178,1186,1278` | **Markup injection**: exception `{e}` unescaped in error markup — network/SSL exceptions contain brackets |
| 5 | Rich | `cli.py:443-460,928-943,1022-1040` | **Markup injection**: user config values (URLs, descriptions, paths) assembled unescaped into Panel markup |
| 6 | Architecture | `core.py` (all `read_text()`/`write_text()`) | **No `encoding="utf-8"`** on 30+ file I/O calls — non-UTF-8 locales will corrupt content |
| 7 | Architecture | `core.py:117-118` | **Non-atomic config writes** — interrupted writes leave config.json truncated/corrupt. Fix: write to `.tmp` then rename |
| 8 | Architecture | `core.py:450-477` | **Temp file leak** — if Popen raises in background mode, NamedTemporaryFile objects with `delete=False` leak permanently |
| 9 | Architecture | `core.py` (~600 lines) | **Massive duplication** between `update_expert`, `update_expert_async_internal`, and `switch_version_async` — extract shared helpers |
| 10 | Textual | `experts_pane.py:267`, `teams_screen.py:99`, `version_detail_screen.py:222` | **Double-fire bug**: `on_data_table_row_selected` duplicates the Enter binding — `action_show_details` fires twice per keypress |
| 11 | Textual | `form_modal.py:18`, `confirmation_modal.py:40` | **Private API usage**: `_bindings.bind()` is Textual internal — use `BINDINGS` class variable instead |
| 12 | Textual | `operations.py:152-175` | **`add_expert` spawns subprocess** instead of calling core function directly — no progress feedback, stdout discarded |
| 13 | Textual | `search_mixin.py:50` | **Dangerous default**: `_on_all_clear` calls `app.exit()` — any Screen subclass that forgets to override will exit the entire app on double-escape |

### MEDIUM

| # | Area | Location | Issue |
|---|------|----------|-------|
| 14 | Typer | `cli.py:93,122,843,950` | No explicit `rich_markup_mode="rich"` on Typer apps — works by default but should be intentional |
| 15 | Typer | `cli.py:99` | `install_traceback()` conflicts with Typer's built-in `pretty_exceptions` — two exception hooks running in parallel |
| 16 | Typer | `cli.py:60-81` | 7 fragmented `from hivemind_cli.core import` blocks — consolidate into one |
| 17 | Typer | `cli.py:989-993` | `--experts` is a comma-separated string instead of `list[str]` — breaks shell completion |
| 18 | Typer | `cli.py:1371-1462` | Compat aliases duplicate all parameter declarations — maintenance hazard. Use shared `Annotated` type aliases |
| 19 | Typer | `cli.py:1179,1187,1279` | `raise typer.Exit(1) from None` swallows the original exception cause |
| 20 | Rich | `cli.py:594-611` | `Live` with `refresh_per_second=4` AND manual `live.update()` every 0.25s — double refresh causing potential flicker |
| 21 | Rich | `cli.py:463-485` | Manual braille spinner instead of Rich's `Spinner`/`console.status()` |
| 22 | Rich | `cli.py:1284` | Crawl Summary table missing `box=box.ROUNDED` (all other tables use it) |
| 23 | Textual | `app.py:62-71` | Double data loading on mount — expert table rendered twice on startup |
| 24 | Textual | `version_detail_screen.py` | Parallel search implementation diverges from SearchMixin — two different search systems doing the same job |
| 25 | Textual | `operations.py:25-36` | Progress callback may not be thread-safe if called from non-loop thread. Textual DOM is not thread-safe — use `app.call_from_thread()` |
| 26 | Textual | `teams_screen.py:76`, `team_detail_screen.py:133,154` | Sync core functions called directly in async callbacks — blocks the event loop. Use `asyncio.to_thread()` |
| 27 | Textual | `base_screen.py:39` | `action_handle_escape` base is a no-op (`...`) — should `pop_screen()` by default |
| 28 | Jinja2 | `core.py:680-717` | Librarian body built with f-strings instead of a `.j2` template — only agent content not templated |
| 29 | Jinja2 | `templates.py:19` | `__import__("jinja2").StrictUndefined` — unidiomatic, just add to the normal import |
| 30 | Jinja2 | `templates.py:16-20` | `auto_reload=True` on static templates — wasted stat calls per render. Set `auto_reload=False` |
| 31 | Architecture | `core.py` (all subprocess calls) | **No subprocess timeouts** anywhere — hung git or AI process blocks indefinitely |
| 32 | Architecture | `crawler.py:325-327,371-372,423-424` | All exceptions silently swallowed with `except Exception: pass` — network errors invisible |
| 33 | Architecture | `providers.py` | `ClaudeProvider` and `OpenCodeProvider` have identical deploy/undeploy implementations — belongs in base `Provider` class |
| 34 | Architecture | `core.py:83-84` | `AnalysisHandle._stderr_file`/`_stdout_file` typed as `object` — should be `IO[str] | None` (fixed) |

### LOW

| # | Area | Location | Issue |
|---|------|----------|-------|
| 35 | Typer | All commands | Legacy `= typer.Argument(...)` style — should migrate to `Annotated` style (modern Typer idiom since 0.9+) |
| 36 | Typer | `cli.py:791-795` | `on_progress` callback redefined inside loop — move outside |
| 37 | Textual | `search_bar.py:13` | `query` reactive is dead code — never read by consumers |
| 38 | Textual | `experts_pane.py:89-101` | Double table refresh per operation (status + message both trigger full `update_experts`) |
| 39 | Textual | `app.py:56-127` | Manual tab system (~50 lines) — should use Textual's `TabbedContent` widget |
| 40 | Textual | `form_modal.py:48`, `confirmation_modal.py:57` | Redundant inner `Button` imports (already imported at module level) |
| 41 | Rich | Tables | No `max_width`/`overflow` on columns with long URLs, paths, descriptions |
| 42 | Rich | Panel borders | Inconsistent `border_style` (blue vs green) not documented in theme |
| 43 | Rich | `cli.py:1238` | `progress.console.log()` adds unwanted timestamps — should be `.print()` |
| 44 | Jinja2 | `core.py:2250`, `team_lead.md.j2:5` | `expert_sections` pre-joined before template — should pass as list, use `{% for %}` |
| 45 | Architecture | `core.py:240-276` | `_ensure_repos_link` and `_ensure_external_docs_link` are near-identical — extract shared helper |
| 46 | Architecture | `core.py:1877,2284` | Duplicate `shutil` import (already at module level) |

---

## Dict-to-Model Migration

### Problem

The codebase passes ~50 dicts by string key through core → cli → tui. No compile-time safety on key access. Mypy sees `dict` everywhere, can't verify attribute access, and bare `dict` without type args blocks `--strict`.

### Recommended approach: `@dataclass` (not pydantic)

- No new dependency
- Consistent with existing `tui/models.py`, `ProgressInfo`, `AnalysisHandle`
- JSON serialization via `dataclasses.asdict()` + `**kwargs` unpacking

### Models to create (`hivemind_cli/models.py`)

#### Config models (serialized to/from JSON)

```python
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
    deployed: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    experts_deployed: list[str] = field(default_factory=list)
    teams_deployed: list[str] = field(default_factory=list)

@dataclass
class SwitchProviderResult(OperationResult):
    old_provider: str = ""
    new_provider: str = ""
    already_active: bool = False
```

### Migration scope

| File | Changes |
|------|---------|
| `core.py` | `_load_config() -> AppConfig`, `_load_hivemind() -> HivemindConfig`, all operation functions return typed results instead of dicts |
| `providers.py` | `Provider.__init__(config: ProviderConfig)`, `get_provider()` takes `ProviderConfig` |
| `cli.py` | All callsites: `result["error"]` → `result.error`, `config["enabled"]` → `config.enabled` |
| `tui/operations.py` | Same callsite updates |
| `tui/app.py` | Config/repos loading uses models |
| `tui/models.py` | Move to shared `models.py` or re-export from there |

### Existing typed models (already dataclasses, no changes needed)

- `ProgressInfo` (core.py) — update phase progress
- `AnalysisHandle` (core.py) — subprocess handle
- `UpdatePhase` (core.py) — enum
- `CancellationToken` (core.py) — cancellation flag
- `ExpertRow` (tui/models.py) — table row data
- `VersionInfo` (tui/models.py) — git version data
- `ExpertStatus`, `OperationStatus` (tui/models.py) — enums

---

## Linting Strictness Plan

### Current ruff rules

Enabled: `E, W, F, I, UP, B, SIM, RUF, PIE, PERF, FURB, RET, PTH, C4, RSE, ICN, ERA, LOG, G`

### Tier 2 — Enable Soon (~68 violations, manual review)

| Rule | Violations | Notes |
|------|-----------|-------|
| **TC** | 15 | Move typing imports behind `TYPE_CHECKING` — unsafe-fix works |
| **TRY** | 12 | Exception hygiene — ignore `TRY003` (long exception messages) |
| **EM** | 6 | Exception message best practices |
| **C90** | 8 at max-complexity=15 | Start with `max-complexity = 15`, tighten later |
| **ARG** | 10 | Unused args — per-file ignore on `tui/` (Textual callbacks) |
| **T20** | 12 | Print statements — per-file ignore on `scripts/` |

### Tier 3 — Enable Later (high effort)

| Rule | Violations | Notes |
|------|-----------|-------|
| **ANN** | 58 | Missing type annotations — tackle alongside mypy strictness |
| **PL** | 105 (49 real) | 56 are `PLC0415` (intentional lazy imports) — ignore that rule |
| **S** | 70 (13 real) | 57 are subprocess false positives (`S603`/`S607`) — ignore those |
| **BLE001** | 27 | Blind except blocks — genuine smell |

### Skip

| Rule | Why |
|------|-----|
| **FBT** (31) | Boolean trap too noisy for CLI tools |
| **D** (100+) | Docstring enforcement not worth it |
| **SLF** (4) | Private member access often intentional |
| **COM812** | Conflicts with ruff format |

---

## Mypy Strictness Plan

### Current state

- 0 errors with current config
- 0 errors even under `--strict` for TUI (so `ignore_errors = true` is unnecessary)
- Only `crawl4ai` lacks type stubs (5 imports)
- 45 errors to full `--strict`: 44 bare `dict`/`Popen` type args + 1 untyped call

### Target config

```toml
[tool.mypy]
python_version = "3.10"
show_error_codes = true
strict = true

# Only crawl4ai lacks stubs
[[tool.mypy.overrides]]
module = "crawl4ai.*"
ignore_missing_imports = true

# core.py: relax until fully annotated
[[tool.mypy.overrides]]
module = "hivemind_cli.core"
disallow_untyped_defs = false
disallow_incomplete_defs = false
warn_return_any = false

# cli.py: thin layer, mostly unannotated
[[tool.mypy.overrides]]
module = "hivemind_cli.cli"
disallow_untyped_defs = false
disallow_incomplete_defs = false

# crawler.py: unannotated
[[tool.mypy.overrides]]
module = "hivemind_cli.crawler"
disallow_untyped_defs = false
disallow_incomplete_defs = false
```

### What `strict = true` adds (currently missing)

| Flag | Impact |
|------|--------|
| `disallow_any_generics` | Catches bare `dict`, `list`, `Popen` without type params — **44 current violations, eliminated by model migration** |
| `disallow_subclassing_any` | Catches subclassing untyped imports |
| `disallow_untyped_calls` | Prevents typed code from silently calling untyped functions |
| `disallow_untyped_decorators` | Typer/Rich have types so this is safe |
| `no_implicit_reexport` | Public API hygiene for `__init__.py` |
| `strict_equality` | Catches `1 == "1"` type bugs |
| `strict_bytes` | Correct `bytes`/`bytearray`/`memoryview` handling |
| `extra_checks` | Additional correctness checks |

### What to remove

- `ignore_missing_imports = true` globally → scope to `crawl4ai.*` only
- `ignore_errors = true` on TUI → remove entirely (0 errors under strict)
- `allow_untyped_globals = true` on core → models eliminate `[var-annotated]` errors

---

## Pre-commit Hardening

### Current hooks

Ruff lint+format, trailing-whitespace, end-of-file-fixer, check-yaml, check-toml, check-added-large-files, check-merge-conflict, mixed-line-ending, mypy (local).

### Hooks to add

| Hook | Why |
|------|-----|
| `no-commit-to-branch` (main) | Prevents accidental direct commits to main |
| `detect-private-key` | Project handles AI provider credentials |
| `check-json` | Has JSON config files but only validates yaml/toml |
| `check-ast` | Catches Python syntax errors in files mypy might skip |
| `debug-statements` | Catches stray `breakpoint()`/`pdb` |
| `check-symlinks` | Relevant — `experts/*/HEAD` are symlinks |
| `destroyed-symlinks` | Catches symlinks replaced by regular files |

### Fixes to apply

- `trailing-whitespace`: add `--markdown-linebreak-ext=md` (preserves markdown `<br>`)
- `trailing-whitespace` + `end-of-file-fixer`: exclude `experts/` (AI-generated, spurious diffs)
- Reorder: safety checks first → formatters → validators → mypy (slowest last)

### Target config

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      # Safety checks first
      - id: no-commit-to-branch
        args: [--branch, main]
      - id: check-merge-conflict
      - id: detect-private-key
      - id: check-added-large-files
      - id: check-symlinks
      - id: destroyed-symlinks
      # Formatters
      - id: trailing-whitespace
        args: [--markdown-linebreak-ext=md]
        exclude: '^experts/'
      - id: end-of-file-fixer
        exclude: '^experts/'
      - id: mixed-line-ending
        args: [--fix=lf]
      # Validators
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-ast
      - id: debug-statements

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.4
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: local
    hooks:
      - id: mypy
        name: mypy
        entry: uv run mypy hivemind_cli/
        language: system
        pass_filenames: false
        always_run: true
        require_serial: true
```

---

## Test Suite Plan

### Problem

Two regressions were introduced by linting auto-fixes:
1. `_load_json` crashed on empty files (`json.loads("")` → `JSONDecodeError`) — fixed
2. `_get_head_commit` returned `Path` instead of `str` after PTH115 auto-fix — fixed

No tests exist to prevent future regressions.

### Infrastructure

```toml
# pyproject.toml additions
[project.optional-dependencies]
dev = ["ruff>=0.11.0", "mypy>=1.15.0", "pre-commit>=4.0.0", "pytest>=8.0.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

### Layout

```
tests/
  __init__.py
  conftest.py          # core_paths fixture (monkeypatches module-level path constants)
  test_core.py         # filesystem/config tests + regression tests
  test_providers.py    # pure string function tests
```

### Key fixture: `core_paths`

Redirects all module-level path constants in `core.py` into `tmp_path` via `monkeypatch`. Tests never touch real project files.

### Regression tests

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

### Coverage targets

| Module | Functions to test |
|--------|------------------|
| `core.py` | `_load_json`, `_save_json`, `_load_config`, `_save_config`, `_expert_names`, `_is_private_expert`, `_get_expert_dir`, `_get_head_commit`, `_count_versions` |
| `providers.py` | `extract_description`, `strip_frontmatter`, `replace_expert_paths`, `get_provider` |

### Pre-commit hook

```yaml
- id: pytest
  name: pytest
  entry: uv run pytest --tb=short -q
  language: system
  pass_filenames: false
  always_run: true
```
