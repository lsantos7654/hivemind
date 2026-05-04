---
name: hivemind-expert-management
description: How to manage hivemind experts and teams via the MCP tools — adding, enabling, disabling, updating, switching versions, deleting. Covers the three catalog states (unlisted / enabled / disabled), the per-machine vs catalog-wide split, common workflows, the curator-subagent path for adding new experts, and hand-editing the AI-generated knowledge docs. Load when the user wants to add or remove experts, when about to call any catalog mutation tool, when debugging an "Unknown agent type" error, or when reasoning about lifecycle transitions.
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
or disabled, not missing.** Use `list_agents` or `show_agent(name=...)`
to check the catalog, then `enable_agent(name)`. This is the expected
next step, not a failure.

## All catalog mutation tools

All hot-reload automatically — opencode re-reads `agents/*.md`
without disposing in-flight sessions. **No need to warn the user, no
`continue` needed.** Just call the tool and proceed.

| Tool | Purpose |
|---|---|
| `list_agents(state?, kind?)` | List catalog entries with state (enabled / disabled / unlisted) and kind. Filter by either. |
| `show_agent(name)` | Per-agent detail including kind-specific body params (remote, commit, ref_name, experts, …). |
| `status` | Catalog summary — totals + per-kind breakdown. |
| `create_team(name, description, experts)` | Register a new team-lead agent with member roster. Lands **unlisted** — call `enable_agent` after. |
| `enable_agent(name)` | Deploy an unlisted/disabled agent. Symlinks the cached repo (for git_analyzed) and writes the agent file. |
| `disable_agent(name)` | Remove deployed file, keep catalog entry + memory. |
| `update_agent(name, skip_analysis?)` | For git-analyzed experts: fetch latest commits and re-run AI analysis. **Blocks on AI analysis** — will time out from the chat-TUI MCP path; prefer running it from a terminal via `hivemind expert update <name>`. Hand-edited `description.md` and `expertise.md` are preserved. |
| `switch_version(name, commit)` | Switch a git-analyzed expert to a specific commit (or tag/branch ref — auto-resolved). **Blocks on AI analysis** if the target commit isn't already analyzed locally; same MCP-timeout caveat as `update_agent`. |
| `delete_agent(name, purge_memory?)` | Remove catalog entry and deployed file. Memory tree at `~/.config/opencode/hivemind/memory/<name>/` is preserved unless `purge_memory=true`. |
| `add_expert_to_team(team, expert)` | Add a roster member. Team must be enabled. |
| `remove_expert_from_team(team, expert)` | Remove a roster member. Team must be enabled. |
| `redeploy` | Regenerate every enabled agent's deployed file from the catalog. Also re-syncs `opencode/agents/*.md` user-supplied entries. |

Note: there is **no** `create_git_expert` MCP tool — adding a new
git-analyzed expert from the chat TUI goes through the
`hivemind-expert-curator` subagent (see "Add a new expert from upstream"
below). The MCP-only primitives `prep_create_expert` and
`finalize_create_expert` are scoped to the curator's permission
allowlist; they're not for orchestrator-direct use.

Roster mutations require the team itself to be enabled. If you need
to modify a disabled team's roster, enable it first.

## Common workflows

### Add a new expert from upstream

From a chat-TUI session, spawn the curator subagent in the background:

```
Task(
  subagent_type="hivemind-expert-curator",
  background=true,
  description="add <repo-name> expert",
  prompt="Add expert from https://github.com/owner/repo (ref v2.1.0 if relevant)"
)
```

Returns a `task_id` immediately. The curator clones the repo, performs
the analysis **in its own session** (Read/Grep/Glob/Write — no nested
subprocess, no MCP timeout), and registers the catalog entry as
*unlisted*. Pick up the result later:

```
read_task_result(task_id="ses_xxx")
# → "Added expert <name> at <commit[:12]>. Run enable_agent to deploy."

enable_agent(name="<name>")
```

If you're working from a real terminal (not a chat-TUI session), use
the one-shot CLI instead — it's faster because it doesn't pay the
in-session-LLM cost:

```bash
hivemind expert add https://github.com/owner/repo --ref v2.1.0
```

Either path lands the same `git_analyzed` catalog entry; they differ
only in **who** runs the analysis stage.

### "Task says expert-X doesn't exist"

Most likely it's in the catalog but not enabled here:

```
list_agents(state="unlisted")    # confirm presence
enable_agent(name="expert-x")
```

If it's not in `hivemind.json` at all, spawn the curator subagent to
add it (see "Add a new expert from upstream" above).

### Refresh an expert to latest

From a real terminal (not the chat TUI — analysis takes minutes and
will time out the MCP call):

```bash
hivemind expert update expert-x
```

Fetches the latest upstream commits, re-runs AI analysis, redeploys
if currently enabled. The `description.md` and `expertise.md` files
(hand-editable AI output) survive the update.

### Pin an expert to a specific historical version

`switch_version` accepts a commit SHA (full or short), tag, or branch
name — refs are auto-resolved against the local clone, fetching tags
if needed:

```
switch_version(name="expert-x", commit="v8.5.1")
```

If the target commit's analysis docs are already cached locally, this
is fast (just a HEAD repoint + body params update). If a fresh AI
analysis is needed, **the MCP call will time out** — run from a
terminal instead:

```bash
hivemind expert switch-version expert-x v8.5.1
```

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
