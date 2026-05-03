---
name: hivemind-expert-management
description: How to manage hivemind experts and teams via the MCP tools — adding, enabling, disabling, updating, switching versions, deleting. Covers the three catalog states (unlisted / enabled / disabled), the per-machine vs catalog-wide split, common workflows, and hand-editing the AI-generated knowledge docs. Load when the user wants to add or remove experts, when about to call any catalog mutation tool, when debugging an "Unknown agent type" error, or when reasoning about lifecycle transitions.
---

# Hivemind expert management

## Catalog state model

Every agent (expert or team-lead) is in one of three states:

- **unlisted** — entry exists in `hivemind.json` (committed catalog)
  but no agent file deployed on this machine. Opencode won't show it
  in the subagent picker. `Task(subagent_type=...)` returns
  *"Unknown agent type"*.
- **enabled** — deployed; `Task(subagent_type=...)` works. For
  git-analyzed experts the cloned source repo lives at
  `~/.cache/hivemind/repos/<name>/`.
- **disabled** — catalog entry preserved, deployed file removed.
  Memory tree retained.

The catalog (`hivemind.json`) is committed; the per-machine state
(`config.json`, gitignored) decides which entries are enabled here.
That split is intentional — collaborators share a catalog but each
machine picks its own active set.

If `Task` reports an unknown agent, **it's almost certainly unlisted
or disabled, not missing.** Read `hivemind.json` to confirm the
entry exists, then `enable_agent(name)`. This is the expected next
step, not a failure.

## All catalog mutation tools

All hot-reload automatically — opencode re-reads `agents/*.md`
without disposing in-flight sessions. **No need to warn the user, no
`continue` needed.** Just call the tool and proceed.

| Tool | Purpose |
|---|---|
| `create_git_expert(url, ref?)` | Clone repo, run AI analysis, register as new expert. Lands **unlisted** — call `enable_agent` after. |
| `create_team(name, description, experts)` | Register a new team-lead agent with member roster. Lands **unlisted** — call `enable_agent` after. |
| `enable_agent(name)` | Deploy an unlisted/disabled agent. Symlinks the cached repo (for git_analyzed) and writes the agent file. |
| `disable_agent(name)` | Remove deployed file, keep catalog entry + memory. |
| `update_agent(name, skip_analysis?)` | For git-analyzed experts: fetch latest commits and re-run AI analysis. Hand-edited `description.md` and `expertise.md` are preserved. |
| `switch_version(name, commit)` | Switch a git-analyzed expert to a specific commit's stored analysis. Useful for pinning to an upstream version that matches your project. |
| `delete_agent(name, purge_memory?)` | Remove catalog entry and deployed file. Memory tree at `~/.config/opencode/hivemind/memory/<name>/` is preserved unless `purge_memory=true`. |
| `add_expert_to_team(team, expert)` | Add a roster member. Team must be enabled. |
| `remove_expert_from_team(team, expert)` | Remove a roster member. Team must be enabled. |
| `redeploy` | Regenerate every enabled agent's deployed file from the catalog. Also re-syncs `opencode/agents/*.md` user-supplied entries. |

Roster mutations require the team itself to be enabled. If you need
to modify a disabled team's roster, enable it first.

## Common workflows

### Add a new expert from upstream

```
create_git_expert(url="https://github.com/owner/repo", ref="v2.1.0")
enable_agent(name="<auto-derived-name>")
```

`create_git_expert` derives the expert name from the repo. If the
project pins a specific version, pass `ref=<tag-or-sha>` so the
analysis is grounded in that exact tree.

### "Task says expert-X doesn't exist"

Most likely it's in the catalog but not enabled here:

```
enable_agent(name="expert-x")
```

If it's not in `hivemind.json` at all, `create_git_expert` first.

### Refresh an expert to latest

```
update_agent(name="expert-x")
```

Fetches the latest upstream commits, re-runs AI analysis, redeploys
if currently enabled. The `description.md` and `expertise.md` files
(hand-editable AI output) survive the update.

### Pin an expert to a specific historical version

```
switch_version(name="expert-x", commit="abc1234")
```

Useful when the project pins a specific upstream version and you
want the expert grounded in that exact commit.

### Take an expert out of rotation temporarily

```
disable_agent(name="expert-x")
```

Catalog stays intact, memory tree preserved. Re-enable to restore.

### Remove an expert permanently

```
delete_agent(name="expert-x", purge_memory=true)
```

Without `purge_memory=true`, memory at
`~/.config/opencode/hivemind/memory/<name>/` is preserved (so the
expert can be re-created later without losing accumulated context).

### Edit AI-generated docs by hand

Each enabled git-analyzed expert has its analysis docs at
`~/.config/opencode/experts/<name>/HEAD/`. The two files that survive
`update_agent` are:

- `description.md` — single hand-editable paragraph used as the
  agent's description in the subagent picker.
- `expertise.md` — longer hand-editable expertise blurb baked into
  the deployed prompt.

Edit either, then `redeploy` to regenerate the deployed `agent.md`.
Edits survive subsequent `update_agent` runs.

## Team interactions

- Roster mutations require the team to be enabled. Disabled teams
  must be re-enabled before adding/removing members.
- Removing the last expert from a team doesn't disable the team
  itself — `disable_agent` or `delete_agent` it explicitly if no
  longer needed.
- Disabling a member expert leaves the team's roster intact (the
  catalog entry stays). The team-lead's deployed prompt may still
  reference disabled members; if you care, run `redeploy` after
  disabling.
