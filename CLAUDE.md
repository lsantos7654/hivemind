# Hivemind Expert System

Expert agents are managed centrally via the `hivemind` CLI. Source of truth: `~/projects/hivemind`.

## Managing Experts

```
hivemind list              # See all experts and their status
hivemind add <url>         # Register, clone, AI-analyze, and create expert agent
hivemind enable <name>     # Enable an expert (clones repo + creates agent symlink)
hivemind disable <name>    # Disable an expert (removes agent symlink)
hivemind update [name]     # Fetch latest commits and re-analyze with AI
hivemind query <question>  # Ask the librarian which expert(s) can help
hivemind status            # Full dashboard
hivemind init              # Set up ~/.claude symlinks and enable agents
```

## Architecture

- Expert definitions: `~/.claude/experts/<name>/HEAD/agent.md` (with knowledge docs alongside)
- Versioned knowledge: `~/.claude/experts/<name>/<commit>/` (HEAD symlink points to active version)
- Agent symlinks: `~/.claude/agents/expert-<name>.md` → `../experts/<name>/HEAD/agent.md`
- Librarian: `~/.claude/agents/librarian.md` — auto-generated catalog of all experts, regenerated on `add`, `update`, and `init`
- Slash commands: `~/.claude/commands/`
- Fetched repos: `~/.cache/hivemind/repos/<name>`

When editing experts, edit `experts/<name>/HEAD/agent.md` — changes are live immediately (agents are symlinks).
