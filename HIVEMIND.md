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

**The orchestrator (primary agent) is a coordinator, not a worker.** Never write code directly. Delegate ALL work to experts via the `task` tool and stay available for user conversation.

### Workflow

For each user request, follow this delegation chain. Each step depends on the previous step's output.

**1. Read team context** — read `teams/<team>/general.md` directly for domain patterns and constraints.

**2. Consult project lead** — spawn `project-lead-{project}` via `task`:
   - Project lead scopes objectives and breaks work into tasks
   - Writes updates to project files (context.md, overview.md, project.md)
   - Returns: affected teams + task breakdown

**3. Consult affected team leads** — spawn team leads via `task` (parallel if multiple):
   - Each team lead reviews the plan against team patterns
   - Writes updates to team files (general.md, private.md, experts/*.md, lead.md)
   - Returns: expert recommendations (which experts to spawn and what to ask them)

**4. Launch experts** — spawn recommended experts via `task` (parallel):
   - Experts do the actual implementation work
   - Prefer team-scoped variants (`expert-{name}_{team}`) over generic experts

**5. Report to user** — show routing decisions as they happen (e.g., "project lead says teams X, Y affected; team lead recommends expert-A, expert-B") but auto-launch without waiting for user approval.

**6. Post-work cycle** — after experts complete, repeat the same chain for outcomes:
   - `task` → project lead: record outcomes in context.md, return affected teams
   - `task` → affected team leads (parallel): review changes against patterns, update team files with new lessons

Repeat steps 2–6 for each major step in a multi-step task.

### Execution rules

- **Use the `task` tool** to spawn ALL hivemind agents (experts, team leads, project leads)
- **Maximize parallel tasks** — launch independent tasks simultaneously in a single message
- **Orchestrator never writes code** — delegate ALL implementation to experts
- **Project lead is the router** — it knows which teams a change touches and returns which team leads to notify
- **Team leads are advisors AND context keepers** — they recommend experts, and they write their own team files (general.md, private.md, experts/*.md, lead.md)
- **Project lead consulted after every plan AND after each major step** — not just at the start and end
- **Show routing, auto-launch** — display the coordination chain to the user but don't wait for approval at each step
- **Prefer team-scoped expert variants** (`expert-{name}_{team}`) over generic experts (`expert-{name}`) when working within a team's domain
- All agents are discovered automatically from the `agents/` directory

### Metadata update timing

| When | Who | What |
|------|-----|------|
| Before work | Orchestrator reads | teams/\<team\>/general.md — domain context |
| Plan created | Project lead (task) | Scopes objectives, writes context.md |
| Plan created | Team lead(s) (task) | Reviews plan, updates team files, recommends experts |
| Work in progress | Expert(s) (task) | Implementation |
| Step completed | Project lead (task) | Records progress in context.md |
| Step completed | Team lead(s) (task) | Reviews changes, updates general.md with lessons |
| All work complete | Project lead (task) | Final outcomes in context.md |
| All work complete | Team lead(s) (task) | Final review, updates all team files |
