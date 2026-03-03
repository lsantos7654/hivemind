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

## Architecture

Hivemind supports multiple AI coding platforms via a provider abstraction. The active
provider determines where agents are deployed and how analysis commands are built.

- Provider config: `config.json` → `active_provider` + `providers.<name>.settings`
- Expert definitions: `experts/<name>/HEAD/agent.md` (platform-neutral body, no frontmatter)
- Versioned knowledge: `experts/<name>/<commit>/` (HEAD symlink points to active version)
- Agent files: Generated at deploy time with provider-specific frontmatter
- Librarian: `agents/librarian.md` — auto-generated catalog of all experts
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
