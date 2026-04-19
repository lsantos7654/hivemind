# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

```bash
uv tool install -e .          # Install CLI (editable)
uv run hivemind               # Launch TUI
uv run hivemind status        # Full dashboard
uv run hivemind redeploy      # Regenerate all agent files
uv run hivemind init          # Set up directory structure
```

Verify changes:
```bash
uv run pytest                              # run full test suite
uv run pytest tests/test_core.py::test_x   # run single test
uv run ruff check src/                     # lint
uv run ruff format src/                    # format
uv run mypy src/                           # type-check (strict; TUI + crawler relaxed)
uv run pre-commit run --all-files          # all hooks
uv run hivemind redeploy                   # smoke test: regenerate all agents
```

## Architecture

Hivemind is a context management layer that feeds expert knowledge into OpenCode.

### Core modules (`src/hivemind/`)

- **`config.py`** — Path constants, config I/O (`load_config`, `save_config`, `load_hivemind`, etc.), filesystem helpers (`expert_names`, `get_expert_dir`, `get_head_commit`), provider instance cache (`get_active_provider`).
- **`provider.py`** — Concrete `Provider` class for OpenCode. Handles frontmatter formatting, path transforms (`{EXPERTS_DIR}` → actual paths), `init_dirs()` symlink setup, analysis command building, server lifecycle, MCP config deployment.
- **`experts.py`** — Expert lifecycle: `enable_expert`, `disable_expert`, `delete_expert`, `update_expert`, `update_expert_async_internal`, `switch_version_async`.
- **`teams.py`** — Team management: `create_team`, `delete_team`, `update_team`, `add_expert_to_team`, `remove_expert_from_team`.
- **`deployment.py`** — Agent deployment (`deploy_agent`, `redeploy_all_agents`), librarian generation (`update_librarian`), HIVEMIND.md regeneration.
- **`redeploy.py`** — High-level redeploy entrypoint wiring deployment + templates together for CLI/TUI.
- **`git.py`** — Git subprocess operations: `clone_repo`, `resolve_latest_commit`, `stage_for_analysis`, `commit_analysis_results`.
- **`analysis.py`** — AI analysis orchestration: `start_analysis`, `finish_analysis`, `analyze_repo`, `run_async_analysis`.
- **`cli.py`** — Typer CLI with Rich output. Thin entrypoint over the modules above. Expert and team subcommand groups.
- **`models.py`** — Pydantic models for config schemas (`AppConfig`, `HivemindConfig`) and operation results (`OperationResult`, `UpdateResult`, etc.).
- **`templates.py`** — Jinja2 template rendering for agent/lead/hivemind content. Uses `PackageLoader` to find templates inside the package.
- **`crawler.py`** — Web documentation crawler for supplementing expert knowledge.

### TUI (`src/hivemind/tui/`)

Textual-based TUI with tabbed layout (Experts, Teams). `app.py` is the main app with `HivemindApp`. Screens in `screens/`, reusable widgets in `widgets/`. `VimDataTable` provides vim-style navigation.

### Data flow

1. `hivemind add <url>` → clones repo → runs AI analysis → generates 5 knowledge docs + `agent.md` in `experts/<name>/<commit>/`
2. `HEAD` symlink points to active commit version
3. Deploy reads `experts/<name>/HEAD/agent.md` → strips frontmatter → applies OpenCode frontmatter + path transforms → writes to `agents/expert-<name>.md`
4. Team leads deploy from `teams/<team>/lead.md` → `agents/team-lead-<team>.md`
5. Librarian aggregates all enabled experts + teams into `agents/librarian.md`
6. `HIVEMIND.md` = `hivemind_md_base()`

### Config files

- **`hivemind.json`** (tracked) — Engine settings (model, tools, temperature), repo registrations
- **`config.json`** (gitignored) — Enabled/disabled experts, teams

## Code Conventions

- Modern Python type hints (PEP 604): `str | None` not `Optional[str]`, `list[str]` not `List[str]`
- Only import from `typing` for `Callable`, `Protocol`, etc.
- No brittle meta-checks, no one-time migration commands in core CLI
- No backwards-compat shims, re-export facades, or alias layers — update callers directly
- Only editable installs supported (`uv tool install -e .`)
- When editing experts, edit `experts/<name>/HEAD/agent.md` then `hivemind redeploy`
- Templates in `templates.py` affect NEW agents only; existing agents deploy from their `lead.md` or `agent.md` files
