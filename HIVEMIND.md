# Hivemind Expert System

Expert agents are managed centrally via the `hivemind` CLI. Source of truth: `~/projects/hivemind`.

## Managing Experts

```
hivemind expert list              # See all experts and their status
hivemind expert show <name>       # Show expert details
hivemind expert add <url>         # Register, clone, AI-analyze, and create expert agent
hivemind expert enable <name>     # Enable an expert (clones repo + deploys agent)
hivemind expert disable <name>    # Disable an expert (removes agent)
hivemind expert delete <name>     # Delete an expert entirely
hivemind expert update [name]     # Fetch latest commits and re-analyze with AI
hivemind expert query <question>  # Ask the librarian which expert(s) can help
hivemind status                   # Full dashboard
hivemind init                     # Set up provider directory structure and enable agents
hivemind redeploy                 # Regenerate all agent files for the active provider
hivemind provider list            # List available providers and their status
hivemind provider switch          # Switch active provider
hivemind provider show            # Show detailed provider configuration
```

## Managing Teams

```
hivemind team list                          # List all teams
hivemind team create <name>                 # Create a team with AI-generated lead
hivemind team show <name>                   # Show team details and roster
hivemind team add-expert <team> <expert>    # Add an expert to a team
hivemind team remove-expert <team> <expert> # Remove an expert from a team
hivemind team delete <name>                 # Delete a team
```

## Managing Projects

```
hivemind project list                       # List all projects
hivemind project create <name>              # Create a project with AI-generated lead
hivemind project show <name>                # Show project details
hivemind project set <name>                 # Set the active project (updates HIVEMIND.md)
hivemind project clear                      # Clear the active project
hivemind project add-team <project> <team>  # Assign a team to a project
hivemind project remove-team <project> <team> # Remove a team from a project
hivemind project add-repo <project> <repo>  # Associate a repo with a project
hivemind project delete <name>              # Delete a project
```

## Architecture

Hivemind supports multiple AI coding platforms via a provider abstraction. The active
provider determines where agents are deployed and how analysis commands are built.

- Shared config: `hivemind.json` → `providers.<name>.settings` + `repos` + `teams` + `projects`
- Local state: `config.json` → `enabled`, `disabled`, `active_provider`, `active_project`
- Expert definitions: `experts/<name>/HEAD/agent.md` (platform-neutral body, no frontmatter)
- Versioned knowledge: `experts/<name>/<commit>/` (HEAD symlink points to active version)
- Agent files: Generated at deploy time with provider-specific frontmatter
- Librarian: `agents/librarian.md` — auto-generated catalog of all experts, teams, and projects
- Team context: `teams/<team>/` — general.md, private.md, experts/*.md (managed by team lead)
- Project context: `projects/<project>/` — overview.md, context.md, project.md
- Slash commands: `commands/`
- Fetched repos: `~/.cache/hivemind/repos/<name>`

When editing experts, edit `experts/<name>/HEAD/agent.md` — then run `hivemind redeploy`
to regenerate deployed agent files with the correct provider frontmatter.

## Code Quality Principles

**Avoid Brittle Meta-Checks and Transient Features:**

- Never add validation that checks for specific keywords, phrasing, or formatting
- No CLI commands for one-time migrations or template updates
- No "health check" features that validate against current implementation details
- Comments and features should never mention meta design decisions that become outdated
- Aim for lean code: minimize noise and prevent creation of dead code
- If something is only useful for a single migration, use a standalone script in `scripts/` instead of adding to core CLI
- Core codebase should only contain features that stay relevant as the project matures

**Modern Python Type Hints:**

- ALWAYS use modern Python type hints (PEP 604, Python 3.10+)
- Use `a | b` instead of `Optional[a]` or `Union[a, b]`
- Use `list[str]` instead of `List[str]`
- Use `dict[str, int]` instead of `Dict[str, int]`
- Use `tuple[int, ...]` instead of `Tuple[int, ...]`
- NEVER import from `typing` module for basic types (List, Dict, Optional, Union, Tuple)
- Only import from `typing` for advanced types like `Callable`, `Protocol`, etc. when needed

## General Notes

- always use `builtin cd` instead of `cd` to avoid issues with zoxide

## Shell Navigation

ONLY the `cd` command needs the `builtin` prefix: `builtin cd /some/path`
NEVER use `builtin` with any other command. `builtin uv`, `builtin python`, `builtin git` are ALL WRONG.
Correct: `uv run ...`, `python ...`, `git ...` — no `builtin` prefix.
The ONLY reason `cd` needs `builtin` is because zoxide overrides it.

## Orchestration models

Two orchestration modes are available. Choose based on task complexity:

| | Subagents (default) | Agent Teams |
|---|---|---|
| **How** | Agent tool spawns focused workers | Full Claude Code sessions with shared task list |
| **Communication** | Results return to orchestrator only | Teammates message each other directly |
| **Best for** | Focused tasks, quick lookups, isolated work | Cross-domain work, parallel exploration, debate |
| **Cost** | Lower — results summarized back | Higher — each teammate is a separate session |

### Subagent model

**The orchestrator (main Claude) IS the team lead for all teams.** Subagents cannot spawn other subagents (depth limited to 1), so the orchestrator must spawn experts directly.

**Workflow:**

1. **Consult `project-lead-{project}`** (background) to scope objectives and track progress
2. **Read team context** (`teams/<team>/general.md`) for domain patterns and constraints
3. **Spawn experts directly** in parallel background agents for implementation work
4. **Consult team leads** (foreground, quick) only when you need domain-specific architectural advice
5. **After work completes**, consult project-lead (background) to record outcomes in context.md

**Execution rules:**

- **Always run project-lead and expert agents in the background** (`run_in_background: true`)
- **Maximize parallel agents** — launch as many independent agents as possible in a single message
- **Team leads are advisors**, not delegators — consult them for guidance, don't ask them to spawn experts
- The orchestrator stays conversational with the user while agents work asynchronously
- Only use foreground agents when the result is required before responding

### Agent teams model

Use agent teams when the task benefits from **lateral communication** between workers — not just results flowing back to you.

**When to create an agent team:**

- Work spans multiple hivemind teams or expert domains
- Debugging with competing hypotheses — teammates investigate and challenge each other's theories
- Large features where teammates each own a separate module and need to coordinate interfaces
- Research or review where parallel perspectives add real value (security + performance + testing)

**How to structure teammates using hivemind context:**

Every teammate auto-loads `CLAUDE.md`, which includes all hivemind instructions and active project context. Teammates automatically know about available experts, teams, and project objectives.

- **Assign roles that map to hivemind experts or teams** — e.g., "You own the TUI layer (see the tui-dev team context)" or "You're the Nix infrastructure specialist"
- **Include domain context in spawn prompts** — reference `teams/<team>/general.md` for team-specific patterns and constraints
- **Break project objectives into tasks** — use the shared task list so teammates self-claim work
- **Teammates can spawn hivemind experts as subagents** within their own session for domain-specific knowledge

**Coordination patterns:**

- Consult project-lead (as subagent) to scope work → create agent team → assign tasks from objectives
- Teammates discuss interfaces and dependencies directly via messages
- Require plan approval for risky work — teammates plan in read-only mode until the lead approves
- Team leads can be consulted (as subagents within a teammate) for cross-cutting architectural guidance
- After all tasks complete, consult project-lead to record outcomes

**Team sizing:** Start with 3-5 teammates. Aim for 5-6 tasks per teammate. Three focused teammates outperform five scattered ones.

**Avoid file conflicts:** Break work so each teammate owns different files. Two teammates editing the same file leads to overwrites.

### Metadata update timing

| When | Who | What |
|------|-----|------|
| Before work | Project lead (bg/task) | context.md — scope, decisions |
| Before work | Orchestrator reads | teams/\<team\>/general.md — domain context |
| After work | Project lead (bg/task) | context.md — outcomes, todos checked off |
| After lessons | Orchestrator writes | teams/\<team\>/general.md — new patterns |

## Active Project: hivemind

Project lead: `project-lead-hivemind`

### Current objectives (priority order)

1. **Modern TUI redesign** — remove Header widget, add floating search overlay (`/` opens, `Esc` closes), clean minimal CSS
2. **Full CRUD for experts** — `hivemind expert delete <name>` CLI command + delete action in TUI
3. **Teams/Projects TUI views** — teams screen (list, create, add/remove experts, delete), projects screen (list, set active, create, delete), top-level tab navigation between Experts | Teams | Projects
4. **CLI reorganization** — group expert commands under `hivemind expert` subcommand for consistent command hierarchy (complete)

### Architecture summary

TUI entry point: `hivemind_cli/tui/app.py` → `HivemindApp`
Screens inherit `BaseScreen` (`screens/base_screen.py`)
All tables inherit `VimDataTable` (`widgets/vim_data_table.py`) for consistent vim navigation
Active screens: `MainScreen` (expert list), `VersionDetailScreen` (commit history)

### Key implementation notes

**Objective 1 — TUI redesign:**
- Remove `Header(show_clock=True)` from `MainScreen.compose()` (`screens/main_screen.py` line 43)
- `SearchBar` widget (`widgets/search_bar.py`) becomes a floating CSS-layer overlay (hidden by default, shown on `/`, hidden on `Esc`)
- `BaseScreen.action_focus_search` already handles the `/` binding; add show/hide toggling to it
- Clean up `styles.tcss` to remove any header-related spacing

**Objective 2 — Delete expert:**
- `core.py` needs `delete_expert(name: str) -> dict` — removes from config, deletes agent file, deletes expert dir, removes from hivemind.json repos, regenerates librarian
- CLI: add `hivemind expert delete <name>` command (with confirmation prompt)
- TUI: add `D` binding to `MainScreen` with a confirmation `ModalScreen` before calling `delete_expert_sync(screen, name)` in `operations.py`

**Objective 3 — Teams/Projects TUI:**
- New screens: `screens/teams_screen.py` (TeamsScreen), `screens/projects_screen.py` (ProjectsScreen)
- Both inherit `BaseScreen`, both use `VimDataTable` for their lists
- `HivemindApp` gains `TabbedContent` wrapping all three screens; tab switching via 1/2/3 keys
- `app.py` needs `load_teams()` and `load_projects()` analogous to `load_experts()`
