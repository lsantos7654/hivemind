# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run

```bash
uv tool install -e .          # Install CLI (editable)
uv run hivemind               # Launch TUI
uv run hivemind status        # Full dashboard
uv run hivemind redeploy      # Regenerate all agent files
uv run hivemind init          # Set up provider directory structure
```

No test suite exists. Verify changes by importing and running CLI commands:
```bash
uv run python -c "from hivemind_cli.core import redeploy_all_agents; print('OK')"
uv run hivemind expert list
uv run hivemind team list
uv run hivemind redeploy
```

## Architecture

Hivemind is a context management layer that feeds expert knowledge into any AI coding platform (Claude Code, OpenCode) via a provider abstraction.

### Core modules (`hivemind_cli/`)

- **`core.py`** (~2000 lines) — All business logic: expert CRUD, team management, repo cloning, AI analysis, agent deployment, librarian generation, HIVEMIND.md regeneration. Functions prefixed with `_` are internal helpers.
- **`cli.py`** (~1500 lines) — Typer CLI with Rich output. Thin layer over core.py functions. Expert and team subcommand groups.
- **`providers.py`** (~900 lines) — Abstract `Provider` base class with `ClaudeProvider` and `OpenCodeProvider`. Handles frontmatter formatting, path transforms (`{EXPERTS_DIR}` → actual paths), `init_dirs()` symlink setup, analysis command building.
- **`templates.py`** (~650 lines) — All prompt templates and agent body templates. `hivemind_md_base()` generates HIVEMIND.md content. `team_lead_template()` / `team_lead_prompt()` for team leads. `agent_md_template()` / `create_expert_prompt()` / `update_expert_prompt()` for experts.
- **`crawler.py`** — Web documentation crawler for supplementing expert knowledge.

### TUI (`hivemind_cli/tui/`)

Textual-based TUI with tabbed layout (Experts, Teams). `app.py` is the main app with `HivemindApp`. Screens in `screens/`, reusable widgets in `widgets/`. `VimDataTable` provides vim-style navigation.

### Data flow

1. `hivemind add <url>` → clones repo → runs AI analysis → generates 5 knowledge docs + `agent.md` in `experts/<name>/<commit>/`
2. `HEAD` symlink points to active commit version
3. Deploy reads `experts/<name>/HEAD/agent.md` → strips frontmatter → applies provider-specific frontmatter + path transforms → writes to `agents/expert-<name>.md`
4. Team leads deploy from `teams/<team>/lead.md` → `agents/team-lead-<team>.md`
5. Librarian aggregates all enabled experts + teams into `agents/librarian.md`
6. `HIVEMIND.md` = `hivemind_md_base()` + provider `instructions.md`

### Config files

- **`hivemind.json`** (tracked) — Provider settings, repo registrations
- **`config.json`** (gitignored) — Enabled/disabled experts, active provider, teams
- **`providers/<name>/context.json`** — Per-agent-type context appended at deploy time
- **`providers/<name>/instructions.md`** — Orchestration instructions appended to HIVEMIND.md

## Code Conventions

- Modern Python type hints (PEP 604): `str | None` not `Optional[str]`, `list[str]` not `List[str]`
- Only import from `typing` for `Callable`, `Protocol`, etc.
- No brittle meta-checks, no one-time migration commands in core CLI
- When editing experts, edit `experts/<name>/HEAD/agent.md` then `hivemind redeploy`
- Templates in `templates.py` affect NEW agents only; existing agents deploy from their `lead.md` or `agent.md` files
