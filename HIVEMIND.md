# Hivemind Expert System

Expert agents are managed centrally via the `hivemind` CLI. Source of truth: `~/projects/hivemind`.

## Commands

```
hivemind expert list              # See all experts and their status
hivemind expert show <name>       # Show expert details
hivemind expert add <url>         # Register, clone, AI-analyze, and create expert agent
hivemind expert enable <name>     # Enable an expert (clones repo + deploys agent)
hivemind expert disable <name>    # Disable an expert (removes agent)
hivemind expert delete <name>     # Delete an expert entirely
hivemind expert update [name]     # Fetch latest commits and re-analyze with AI
hivemind expert query <question>  # Ask the librarian which expert(s) can help
hivemind team list                # List all teams
hivemind team create <name>       # Create a team with AI-generated lead
hivemind team show <name>         # Show team details and roster
hivemind team add-expert <t> <e>  # Add an expert to a team
hivemind team remove-expert <t> <e> # Remove an expert from a team
hivemind team delete <name>       # Delete a team
hivemind status                   # Full dashboard
hivemind redeploy                 # Regenerate all agent files
hivemind init                     # Set up provider directory structure
```

## Architecture

- Expert definitions: `experts/<name>/HEAD/agent.md` (platform-neutral, no frontmatter)
- Versioned knowledge: `experts/<name>/<commit>/` (HEAD symlink → active version)
- Deployed agents: `agents/` — generated at deploy time with provider-specific frontmatter
- Librarian: `agents/librarian.md` — auto-generated catalog of all experts and teams
- Team leads: `teams/<team>/lead.md` → deployed as `agents/team-lead-<team>.md`
- Expert notes: `teams/<team>/expert-<name>/notes.md` — per-expert consultation journal
- Fetched repos: `~/.cache/hivemind/repos/<name>`

## Workflow

You (main) handle all implementation directly. Subagents are for domain research only — they cannot spawn other agents.

### When you need domain expertise:

1. **Consult the team lead** — spawn `team-lead-{team}` to get routing advice. The team lead knows each expert's strengths and recent consultation history (via notes.md files). It will recommend which expert(s) to call and what to ask.

2. **Spawn experts in parallel** — call the recommended experts with specific questions. Include which team they're part of so they can update their notes. Experts read their knowledge docs and source code, then report findings.

3. **Experts update their notes** — each expert writes to `teams/{team}/expert-{name}/notes.md` with what was asked and what they found. This builds institutional memory across sessions.

### When you don't know which team or expert to use:

Spawn the **librarian** (`librarian`) — it knows every expert and team and will recommend who to consult.

### Key principles:

- **You do the implementation** — read code, write code, run commands. Subagents research and advise.
- **Subagents cannot spawn other agents** — only you can. Depth is limited to 1.
- **Maximize parallel expert calls** — if you need input from multiple experts, spawn them all at once.
- **Experts are grounded in source code** — they have access to cloned repos and structured knowledge docs. Trust their findings over general knowledge.
