# Hivemind Expert System

Expert agents are managed centrally via the `hivemind` CLI. Source of truth: `~/projects/hivemind`.

## Managing Experts

```
hivemind list              # See all experts and their status
hivemind add <url>         # Register, clone, AI-analyze, and create expert agent
hivemind enable <name>     # Enable an expert (clones repo + deploys agent)
hivemind disable <name>    # Disable an expert (removes agent)
hivemind update [name]     # Fetch latest commits and re-analyze with AI
hivemind query <question>  # Ask the librarian which expert(s) can help
hivemind status            # Full dashboard
hivemind init              # Set up provider directory structure and enable agents
hivemind redeploy          # Regenerate all agent files for the active provider
hivemind provider list     # List available providers and their status
hivemind provider switch   # Switch active provider
hivemind provider show     # Show detailed provider configuration
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

ALWAYS USE `builtin cd` INSTEAD OF `cd` TO AVOID ZOXIDE INTERFERENCE!!!!
ONLY USE `builtin` FOR `cd` only and no other command

## Active Project: hivemind

Project lead: `project-lead-hivemind`

### Working on hivemind features

Before implementing any feature in this project:

1. **Consult `project-lead-hivemind`** for scope, architecture decisions, and cross-team coordination.
2. **Delegate TUI work to `team-lead-tui-dev`** for all Textual/Python TUI implementation.

The project lead maintains the architecture map and tracks objectives. The tui-dev team lead owns all implementation in `hivemind_cli/tui/`.

### Current objectives (priority order)

1. **Modern TUI redesign** — remove Header widget, add floating search overlay (`/` opens, `Esc` closes), clean minimal CSS
2. **Full CRUD for experts** — `hivemind delete <name>` CLI command + delete action in TUI
3. **Teams/Projects TUI views** — teams screen (list, create, add/remove experts, delete), projects screen (list, set active, create, delete), top-level tab navigation between Experts | Teams | Projects

### Architecture summary

TUI entry point: `hivemind_cli/tui/app.py` → `HivemindApp`
Screens inherit `BaseScreen` (`screens/base_screen.py`)
All tables inherit `VimDataTable` (`widgets/vim_data_table.py`) for consistent vim navigation
Active screens: `MainScreen` (expert list), `VersionDetailScreen` (commit history)
