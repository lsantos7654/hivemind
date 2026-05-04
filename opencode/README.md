# opencode user content

Three slots for user-authored opencode content. Drop a file in the
right subdirectory and run `hivemind redeploy` — the wiring is
idempotent, so additions and removals go live without `hivemind init`.

| Subdirectory | Invocation | Body shape | Loaded by opencode from |
|---|---|---|---|
| `commands/` | User types `/<name>` | Prompt template with `$ARGUMENTS` / `$1` / `$2` | `~/.config/opencode/commands/` (symlink) |
| `skills/` | LLM picks autonomously | Reference material (instructions, doc links) | `~/.config/opencode/skills/` (symlink) |
| `agents/` | `Task(subagent_type=...)` after `enable_agent` | Whole agent prompt with frontmatter, verbatim | catalog → `~/.config/opencode/agents/` |

## `commands/<name>.md`

```markdown
---
description: Short blurb shown in the command picker.
agent: optional-agent-name
model: optional-model-id
subtask: false
---

Prompt template body. The user's typed arguments substitute into
`$ARGUMENTS`, `$1`, `$2`, … at invocation time.
```

Frontmatter fields are all optional. The command name is derived from
the filename (`commit.md` → `/commit`).

## `skills/<name>/SKILL.md`

```markdown
---
name: my-skill
description: One-paragraph hook the LLM uses to decide when to load this skill. Be concrete about what scenarios should trigger it.
---

# Skill body

Reference material — instructions, code patterns, doc links — that
gets injected when the LLM autonomously decides this skill is
relevant. Subdirectories under the skill (e.g. `references/`,
`examples/`) are free-form and readable like any other file.
```

Skills are auto-promoted to `/<name>` commands by opencode, so a
well-written skill is invokable both ways.

## `agents/<name>.md`

```markdown
---
description: One-paragraph hook used by the librarian and by anyone routing tasks. Be specific about what scenarios should invoke this agent.
mode: subagent
memory: false        # optional; default false for user-supplied agents
---

# Agent body

Whatever you write becomes the agent's system prompt verbatim — no AI
analysis, no Jinja templating.
```

Lifecycle:

- Drop a file → `hivemind redeploy` → catalog entry as **unlisted**.
- `hivemind expert enable <name>` → file deployed verbatim to
  `~/.config/opencode/agents/<name>.md`.
- Edit source → `hivemind redeploy` → re-deployed.
- Remove source → `hivemind redeploy` → catalog entry swept.

### Memory opt-in

By default, user-supplied agents have **no memory tree scaffolded** and
**no memory section appended** to their prompt — your file is the entire
deployment, and hivemind's memory contract (which adds a `## Memory`
section pointing at `~/.config/opencode/hivemind/memory/<name>/`) would
clobber a hand-authored prompt. Set `memory: true` in the frontmatter to
opt in: hivemind will scaffold the memory directory on enable AND append
the memory section to the deployed agent file. `memory: false` is the
default; it's accepted explicitly for clarity (e.g. on stateless tool
agents like `hivemind-expert-curator`).

Different from `git_analyzed` and `roster_templated`: no git clone,
no AI analysis, memory is opt-in (vs always-on), no `expert-` /
`team-lead-` prefix in the deployed filename.

## When to choose which

- **Command** — you want a named, user-invokable workflow with
  arguments. "Run my commit message generator on the staged changes."
- **Skill** — you want the LLM to know how to do something and pick
  it up when context matches. "Here's how Cloudflare Workers agents
  are built; load this when the user asks about them."
- **Agent** — you want a hand-authored full agent prompt that the
  orchestrator can spawn as a subagent via `Task`. Goes through the
  hivemind catalog so it shows up in the librarian alongside
  AI-analyzed experts and team leads.
