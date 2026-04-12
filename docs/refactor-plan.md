# Hivemind Architecture Refactor Plan

## Principles

1. **Fail loudly** -- no silent fallbacks, no swallowed errors, no default substitutions
2. **Provider agnosticism** -- core modules never reference provider-specific types, models, or instructions
3. **Consistent error handling** -- public operations return `OperationResult`; validators enforce invariants

## Audit Sources

- Architecture team lead routing (team-lead-hivemind)
- expert-design-patterns-for-humans: Template Method pattern for Provider abstraction
- expert-pydantic: model validators for config and result consistency

---

## System Architecture

### Current Architecture

```
                        +-----------+
                        |   CLI     |  cli.py (Typer)
                        +-----+-----+
                              |
                        +-----+-----+
                        |   TUI     |  tui/app.py (Textual)
                        +-----+-----+
                              |
         +--------------------+--------------------+
         |                    |                    |
   +-----+-----+       +-----+-----+        +-----+-----+
   |  experts   |       |   teams   |        |  redeploy  |
   | experts.py |       | teams.py  |        | redeploy.py|
   +-----+------+       +-----+-----+        +-----+-----+
         |                    |                    |
         +--------------------+--------------------+
                              |
                    +---------+---------+
                    |   deployment.py   |
                    | deploy_agent()    |
                    | deploy_expert()   |
                    | update_librarian()|
                    +---------+---------+
                              |
              +---------------+---------------+
              |                               |
    +---------+---------+           +---------+---------+
    |    config.py      |           |   providers.py    |
    | load_config()     |           | Provider (ABC)    |
    | load_hivemind()   |           |   format_agent_md |
    | get_active_prov() |           |   format_lead_md  |
    +-------------------+           |   validate_engine |
                                    +--------+----------+
                                             |
                                   +---------+---------+
                                   |                   |
                            +------+------+    +-------+------+
                            |   Claude    |    |   OpenCode   |
                            |  Provider   |    |   Provider   |
                            +-------------+    +--------------+
```

### Layer Boundaries

```
+------------------------------------------------------------------+
|  UI Layer          CLI (Typer + Rich)  |  TUI (Textual)           |
|------------------------------------------------------------------+
|  Operations        experts.py | teams.py | redeploy.py            |
|------------------------------------------------------------------+
|  Deployment        deployment.py (agent files, librarian, symlinks)|
|------------------------------------------------------------------+
|  Provider          providers.py (abstract) -----> NO provider-    |
|  Abstraction       ClaudeProvider | OpenCodeProvider   specific   |
|                                                    types above    |
|                                                    this line      |
|------------------------------------------------------------------+
|  Config / Models   config.py | models.py (Pydantic)              |
|------------------------------------------------------------------+
|  Infrastructure    git.py | analysis.py | templates.py | crawler  |
+------------------------------------------------------------------+
```

### Data Flow

```
1. hivemind add <url>
   URL --> git.py (clone) --> analysis.py (AI analyze) --> experts/<name>/<commit>/

2. hivemind redeploy
   experts/<name>/HEAD/agent.md
     --> deployment.py (strip frontmatter, extract description)
       --> provider.format_agent_md(name, desc, body)   <-- provider boundary
         --> agents/expert-<name>.md

3. hivemind team create <name>
   expert summaries
     --> templates.py (batch prompt)
       --> analysis.py (single AI call)
         --> teams/<name>/lead.md
           --> provider.format_lead_md(...)              <-- provider boundary
             --> agents/team-lead-<name>.md
```

### Provider Abstraction (After Refactor)

```
Provider (ABC)
  Owns:
    - deploy_agent(), undeploy_agent()     Shared deployment pipeline
    - deploy_expert()                      Symlink management
    - _transform_body()                    Path placeholder resolution
    - init_dirs()                          Directory structure setup
    - validate_engine()                    Engine/model validation
    - get_context_append()                 Context injection

  Declares abstract:
    - format_agent_md(name, desc, body)    Expert agent formatting
    - format_lead_md(name, desc, body)     Lead agent formatting
    - format_librarian_md(body)            Librarian formatting
    - build_analysis_command(...)          AI engine command
    - build_query_command()               Librarian query command

  Knows NOTHING about:
    - list[str] vs dict[str, bool]         Tool config shapes
    - permissions                          OpenCode-only concept
    - YAML frontmatter structure           Provider-specific format
    - temperature defaults                 Provider-specific setting
    - tool names ("Edit" vs "edit")        Provider-specific casing


ClaudeProvider                         OpenCodeProvider
  tools: list[str]                       tools: dict[str, bool]
  _build_claude_frontmatter()            _build_opencode_frontmatter()
  format_agent_md -> list[str]           format_agent_md -> dict[str, bool]
  format_lead_md -> list[str] + Edit     format_lead_md -> dict + permissions
  format_librarian_md                    format_librarian_md
  build_analysis_command                 build_analysis_command
  build_query_command                    build_query_command + validate_engine
```

---

## Phase 1A: Safety Fixes

Bugs and silent fallbacks. No expert input needed -- direct implementation.

### 1A.1 -- Fix `_setup_symlink()` early return bug

**File:** `providers.py:912-915`

The function returns early after backing up a directory, skipping the symlink creation that follows. The symlink is never created.

```python
# BUG: early return skips symlink creation
elif link.is_dir():
    backup = link.with_name(link.name + ".bak")
    link.rename(backup)
    return InitResult(...)  # <-- returns before link.symlink_to(target)
```

**Fix:** Remove the early return. Fall through to `link.symlink_to(target)`.

### 1A.2 -- Fix `load_private_repos()` error swallowing

**File:** `config.py:236-240`

Currently catches `(OSError, json.JSONDecodeError)` and returns `{}`. Corrupt JSON silently loses all private expert registrations.

**Fix:** Only catch `FileNotFoundError`. Let `JSONDecodeError` propagate.

### 1A.3 -- Fix `_post_init_dirs()` JSON error suppression

**File:** `providers.py:831-833`

`contextlib.suppress(ValueError, OSError)` on reading `opencode.json`. Corrupt JSON is silently ignored and the file gets overwritten with only hivemind settings, destroying user config.

**Fix:** Only suppress `FileNotFoundError`. Let `json.JSONDecodeError` propagate with a clear error message.

### 1A.4 -- Fix `get_context_append()` silent swallowing

**File:** `providers.py:244-261`

Two `except (json.JSONDecodeError, AttributeError): pass` blocks silently ignore corrupt `context.json` and `overrides.json`. Agents deploy with missing context and no indication anything is wrong.

**Fix:** Remove the silent catches. Let corrupt JSON raise. Log a warning if files are missing (which is fine).

### 1A.5 -- Fix `validate_engine()` timeout behavior

**File:** `providers.py:660-662`

Returns `OperationResult(success=True)` on `subprocess.TimeoutExpired`. A hanging engine is treated as a valid engine.

**Fix:** Return `OperationResult(success=False, error="Model validation timed out -- check opencode connectivity")`.

### 1A.6 -- Narrow broad exception catches

**File:** `experts.py:357-359, 389-392`

`get_git_versions()` catches all `Exception` and returns empty list. `commit_exists_in_repo()` catches all `Exception` and returns `False`. Both hide real errors behind misleading results.

**Fix:** Narrow to `(subprocess.SubprocessError, OSError)`. Let programming bugs propagate.

---

## Phase 1B: Pydantic Model Hardening

Per expert-pydantic consultation.

### 1B.1 -- `OperationResult` error/success invariant

**File:** `models.py`

Add `@model_validator(mode='after')` on `OperationResult`:
- `success=False` requires `error` to be set
- `success=True` requires `error` to be `None`

All subclasses inherit this automatically. Requires auditing every `OperationResult(success=False)` call site to ensure `error=` is always provided.

### 1B.2 -- `RedeployResult` improvements

**File:** `models.py`

- Add `teams_failed: list[str] = []`
- Add `@model_validator(mode='after')` that derives `success = not failed and not teams_failed`
- Default `success = True` so it can be overridden by the validator

**File:** `redeploy.py`

- Populate `teams_failed` when `deploy_team_lead()` returns `False`
- Remove manual `success=True` -- let the validator derive it

### 1B.3 -- `ProviderConfig` active-provider validation

**File:** `models.py`

Add `@model_validator(mode='after')` gated on `info.context.get('strict')`:
- Validates `engine`, `home_dir`, `settings.model` are non-empty
- Only fires when called with `context={'strict': True}`

**File:** `config.py`

Update `get_active_provider()` to use `ProviderConfig.model_validate(raw, context={'strict': True})` so validation runs when activating a provider.

### 1B.4 -- Keep `tools: list[str] | dict[str, bool]`

Per expert-pydantic: Pydantic's smart union handles `list` vs `dict` unambiguously. No discriminated union or model split needed. Each provider casts to its own type internally.

---

## Phase 1C: Provider Abstraction Cleanup

Per expert-design-patterns-for-humans consultation. Pattern: **Template Method with abstract formatting methods, no hooks.**

### 1C.1 -- Delete `ToolsConfig` type alias

**File:** `providers.py:21`

Remove `ToolsConfig = list[str] | dict[str, bool]` entirely. No code should reference this union type.

### 1C.2 -- Make formatting methods abstract

**File:** `providers.py` (Provider base class)

Make `format_lead_md()` and `format_librarian_md()` abstract on the base class. Each provider implements them directly with native types. No shared hook machinery.

```
Provider (abstract)
  Owns: deploy_agent, _transform_body, init_dirs, validate_engine, get_context_append
  Declares abstract: format_agent_md, format_lead_md, format_librarian_md,
                     build_analysis_command, build_query_command
  Knows nothing about: list[str] vs dict[str, bool], permissions, tool names
```

### 1C.3 -- Delete `_lead_extra_tools()` from base class

**File:** `providers.py`

Each provider's `format_lead_md()` handles tool additions locally:
- Claude: appends `"Edit"` to its `list[str]`
- OpenCode: sets `{"edit": True}` in its `dict[str, bool]`

### 1C.4 -- Delete `_lead_extra_permissions()` from base class

**File:** `providers.py`

Only OpenCode uses permissions. OpenCode's `format_lead_md()` handles them locally. Claude never references permissions. No base-class hook needed.

### 1C.5 -- Move `LIBRARIAN_DESCRIPTION` to module level

**File:** `providers.py`

Move from `Provider.LIBRARIAN_DESCRIPTION` class constant to a module-level constant. Both providers reference it directly in their `format_librarian_md()`.

### 1C.6 -- Rename internal formatting methods

- `ClaudeProvider._format_agent_md_internal()` -> `ClaudeProvider._build_claude_frontmatter()`
- `OpenCodeProvider._format_agent_md_internal()` -> `OpenCodeProvider._build_opencode_frontmatter()`

Each takes provider-native types only. No shared signature.

### 1C.7 -- Fix `ClaudeProvider.build_query_command()`

**File:** `providers.py:599`

Hardcodes `"claude"` binary. Change to `shlex.split(self._engine)[0]`, matching the pattern in `build_analysis_command()`.

### 1C.8 -- Apply `_transform_body()` to librarian

**File:** `providers.py`

Both `ClaudeProvider._format_librarian_md_internal()` and `OpenCodeProvider._format_librarian_md_internal()` skip `_transform_body()` on the librarian body. Apply it consistently. If the librarian body ever contains `{EXPERTS_DIR}` or `{TEAMS_DIR}` placeholders, they will now be resolved correctly.

### 1C.9 -- Consistent frontmatter description quoting

Always YAML-quote the `description` field in frontmatter. Currently quoted for librarian, unquoted for experts -- inconsistent across both providers.

### 1C.10 -- Temperature default constant

**File:** `providers.py`

Define `_DEFAULT_TEMPERATURE: float = 0.1` at module level. Use it in both OpenCode formatting methods instead of inline `if temperature is not None else 0.1`.

---

## Phase 1D: Dead Code Cleanup

### 1D.1 -- Delete `status_symlinks()` and `SymlinkCheck`

**Files:** `providers.py`, `models.py`

`status_symlinks()` is never called. `SymlinkCheck` model is only referenced by it. Delete both.

### 1D.2 -- Deduplicate `_setup_symlink()`

**Files:** `providers.py`, `cli.py`

Two implementations with similar but not identical logic. Keep the `providers.py` version (returns `InitResult`), delete the `cli.py` version, and have CLI import from providers.

### 1D.3 -- Remove redundant `import json as _json`

**File:** `providers.py`

`_post_init_dirs()` methods in both providers re-import `json as _json` locally. Module already imports `json` at line 13. Use the module-level import.

### 1D.4 -- Fix docstring provider reference

**File:** `experts.py:225`

Docstring references `~/.claude/experts/<name>`. Should be generic: `experts/<name>`.

### 1D.5 -- Derive `cache_base_path` from config

**File:** `providers.py:214-220`

Currently hardcodes `Path.home() / ".cache" / "hivemind"`. Should use `CACHE_DIR` from `config.py`. If circular import is an issue, extract shared path constants into a `constants.py` module that both can import from.

---

## Execution Order

```
1A (safety)  -->  1B (models)  -->  1C (provider abstraction)  -->  1D (cleanup)
```

- **1A first**: independent safety fixes, reduces risk for everything after
- **1B second**: model hardening affects how callers construct results, must happen before 1C changes callers
- **1C third**: biggest structural change, touches providers.py and all callers
- **1D last**: cleanup is independent, lowest risk

## Verification

After each phase:

```bash
uv run pytest
uv run ruff check src/
uv run ruff format src/
uv run mypy src/
uv run pre-commit run --all-files
uv run hivemind redeploy  # smoke test: all agents deploy correctly
```

## Risk Areas

- **1C is highest risk** -- changing the abstract interface means updating every caller in `deployment.py`, `redeploy.py`, `teams.py`, and `cli.py`
- **1B.1 `OperationResult` validator** -- every `OperationResult(success=False)` in the codebase must include `error=`. Need to audit all construction sites before enabling the validator.
- **1B.3 `ProviderConfig` validation** -- must only fire for the active provider. Inactive providers in hivemind.json may have empty fields.

## Estimated Scope

- ~12 files touched
- ~400-600 lines changed (mostly `providers.py`)
- No new dependencies
- Existing tests should still pass
