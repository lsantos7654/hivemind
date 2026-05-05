---
name: hivemind-expert-management
description: How to manage hivemind experts and teams via the MCP tools — adding, enabling, disabling, updating, switching versions, deleting. Covers the three catalog states (unlisted / enabled / disabled), the per-machine vs catalog-wide split, the curator-subagent path for the three slow operations (add / update / switch_version), the fast direct-MCP path for everything else, and hand-editing the AI-generated knowledge docs. Load when the user wants to add or remove experts, when about to call any catalog mutation tool, when debugging an "Unknown agent type" error, or when reasoning about lifecycle transitions.
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

## Two MCP surfaces

### Fast direct-MCP tools (sub-second, no AI)

Call these directly. All hot-reload automatically — opencode re-reads
`agents/*.md` without disposing in-flight sessions.

| Tool | Purpose |
|---|---|
| `list_agents(state?, kind?)` | List catalog entries with state and kind. Filter by either. |
| `show_agent(name)` | Per-agent detail including kind-specific body params. |
| `status` | Catalog summary — totals + per-kind breakdown. |
| `enable_agent(name)` | Deploy an unlisted/disabled agent. Symlinks the cached repo (for git_analyzed) and writes the agent file. |
| `disable_agent(name)` | Remove deployed file, keep catalog entry + memory. |
| `delete_agent(name, purge_memory?)` | Remove catalog entry and deployed file. Memory tree is preserved unless `purge_memory=true`. |
| `add_expert_to_team(team, expert)` | Add a roster member. Team must be enabled. |
| `remove_expert_from_team(team, expert)` | Remove a roster member. Team must be enabled. |
| `redeploy` | Regenerate every enabled agent's deployed file from the catalog. |

Roster mutations require the team itself to be enabled. If you need
to modify a disabled team's roster, enable it first.

### The slow operations — add, update, switch_version, create_team

These four operations need multi-minute AI work that doesn't fit
MCP's request/response model. They're handled by spawning the
**`hivemind-expert-curator`** subagent in background mode — the
curator does the work in its own session and reports back via
`task_id`.

There are no `update_agent` / `switch_version` / `create_git_expert` /
`create_team` MCP tools for you to call directly. The underlying
prep/finalize MCP tools (four pairs, one per operation) are scoped
to the curator's permission allowlist; you don't call them yourself.

## Common workflows

### Add a new expert from upstream

```
Task(
  subagent_type="hivemind-expert-curator",
  background=true,
  description="add <name>",
  prompt="Add expert from https://github.com/owner/repo with ref v2.1.0"
)
# → returns task_id immediately

# Later, once opencode reports the task ready:
read_task_result(task_id="ses_xxx")
# → "Added expert <name> at <commit[:12]>. Run enable_agent to deploy."

enable_agent(name="<name>")
```

The curator clones the repo, performs the AI analysis in its own
session (Read/Grep/Glob/Write), and registers the catalog entry as
*unlisted*. Pass the optional `with ref <ref>` clause to pin to a
specific tag/branch/commit at creation time.

### Refresh an expert to the latest upstream commit

```
Task(
  subagent_type="hivemind-expert-curator",
  background=true,
  description="update expert-x",
  prompt="Update expert-x"
)
# → task_id; collect with read_task_result later

# Result is one of:
#   "Updated expert-x from <old[:12]> to <new[:12]>."
#   "Agent expert-x is already up to date at <new[:12]>. No work needed."
```

The curator fetches origin, resolves the latest commit, re-runs AI
analysis (preserving hand-edited `description.md` + `expertise.md`),
and rotates HEAD. If currently enabled, the agent is auto-redeployed.

### Pin an expert to a specific commit / tag / branch

```
Task(
  subagent_type="hivemind-expert-curator",
  background=true,
  description="switch expert-bazel to 8.5.1",
  prompt="Switch expert-bazel to 8.5.1"
)
# → task_id

read_task_result(task_id="ses_xxx")
# → "Switched expert-bazel from <old[:12]> to <new[:12]>."
```

Refs (tags, branches, full or short SHAs) are auto-resolved against
the local clone, fetching tags first so freshly-pushed releases work.
If the target commit's analysis docs are already cached locally
(typically because the agent was switched to it before), the curator
finishes in seconds — no AI analysis needed. Otherwise the curator
runs a fresh in-session analysis.

### Crawl external docs for an expert

```
Task(
  subagent_type="hivemind-crawler",
  background=true,
  description="crawl docs for expert-foo",
  prompt="Crawl https://docs.foo.com for expert-foo with max 100 pages"
)
# → task_id

read_task_result(task_id="ses_xxx")
# → "Crawled 87/100 pages for expert-foo from https://docs.foo.com.
#     Output: ~/.cache/hivemind/external_docs/expert-foo/"
```

The crawler probes the site and picks the right strategy
(sitemap-driven / breadth-first spider / Playwright-rendered),
writes clean markdown to
`~/.cache/hivemind/external_docs/<agent>/`, and that path is in
the expert agent's `external_directory` allowlist — the new docs
are immediately readable by the expert, no separate enable /
redeploy needed. Drop the `with max <N> pages` clause for an
uncapped crawl. Use this when an expert needs supplemental
content that isn't in the upstream repo (vendor docs, tutorial
sites, hosted API references, etc.).

If the response says `requires browser rendering, but Chromium
isn't installed`, the user must run `playwright install chromium`
once (it's a one-time host setup step) before retrying.

### Create a new team-lead agent

```
Task(
  subagent_type="hivemind-expert-curator",
  background=true,
  description="create team <name>",
  prompt="Create team <name> with experts <comma-separated names> and description '<one-sentence summary>'"
)
# → task_id

read_task_result(task_id="ses_xxx")
# → "Created team <name> with experts: <names>. Run enable_agent to deploy."

enable_agent(name="<name>")
```

The curator reads each roster member's `summary.md` from
`~/.config/opencode/experts/<expert>/HEAD/` and writes one
`## expert-<name>` section per member into the team's directory. The
team-lead agent's deployed prompt assembles those sections plus the
description into a routing reference the orchestrator uses to pick
the right expert for a given question.

For roster mutations on an existing team, use the fast direct-MCP
tools `add_expert_to_team` / `remove_expert_from_team` — those just
generate a single section (or none) and don't need the curator.

### "Task says expert-X doesn't exist"

Most likely it's in the catalog but not enabled here:

```
list_agents(state="unlisted")    # confirm presence
enable_agent(name="expert-x")
```

If it's not in `hivemind.json` at all, spawn the curator subagent to
add it (see "Add a new expert from upstream" above).

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
the update workflow are:

- `description.md` — single hand-editable paragraph used as the
  agent's description in the subagent picker.
- `expertise.md` — longer hand-editable expertise blurb baked into
  the deployed prompt.

Edit either, then `redeploy` to regenerate the deployed `agent.md`.
Edits survive subsequent updates because `prep_update_agent` copies
both files forward into the new commit's staging dir before the
analyzer runs.

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
