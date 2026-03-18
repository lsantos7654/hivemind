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
- Team-scoped experts: `agents/expert-{name}_{team}.md` — when experts join a team, hivemind deploys a variant with team context (general.md, per-expert notes) baked in. Prefer `expert-{name}_{team}` over `expert-{name}` when working within a team's scope.
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

## Orchestration model

**The primary agent coordinates all work.** Subagents are spawned via the `task` tool and report results back. Subagents cannot communicate with each other — all coordination flows through the primary agent.

**Workflow:**

1. **Consult `project-lead-{project}`** via task to scope objectives and track progress
2. **Read team context** (`teams/<team>/general.md`) for domain patterns and constraints
3. **Spawn experts via `task`** for implementation work — prefer team-scoped variants (`expert-{name}_{team}`) over generic experts when the task falls within a team's domain. Launch multiple tasks in parallel when independent.
4. **Consult team leads** via task only when you need domain-specific architectural advice
5. **After work completes**, consult project-lead via task to record outcomes in context.md

**Agent execution rules:**

- **Use the `task` tool** to spawn any hivemind agent (experts, team leads, project leads)
- **Maximize parallel tasks** — spawn independent tasks simultaneously for throughput
- **Team leads are advisors**, not delegators — consult them for guidance, don't ask them to spawn experts
- The primary agent stays conversational with the user while tasks run
- All agents are discovered automatically from the `agents/` directory

**Metadata update timing:**

| When | Who | What |
|------|-----|------|
| Before work | Project lead (task) | context.md — scope, decisions |
| Before work | Primary agent reads | teams/\<team\>/general.md — domain context |
| After work | Project lead (task) | context.md — outcomes, todos checked off |
| After lessons | Primary agent writes | teams/\<team\>/general.md — new patterns |
