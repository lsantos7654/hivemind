## Orchestration models

Two orchestration modes are available. Choose based on task complexity:

| | Subagents (default) | Agent Teams |
|---|---|---|
| **How** | Agent tool spawns focused workers | Full Claude Code sessions with shared task list |
| **Communication** | Results return to orchestrator only | Teammates message each other directly |
| **Best for** | Focused tasks, quick lookups, isolated work | Cross-domain work, parallel exploration, debate |
| **Cost** | Lower — results summarized back | Higher — each teammate is a separate session |

### Subagent model

**The orchestrator (main Claude) IS the team lead for all teams.** Subagents cannot spawn other subagents (depth limited to 1), so the orchestrator must spawn experts directly.

**Workflow:**

1. **Read team context** (`teams/<team>/general.md`) for domain patterns and constraints
2. **On plan approval**, simultaneously:
   a. Begin implementation via background agent(s) — delegate ALL code changes
   b. Notify `project-lead-{project}` (background) with scope and decisions → project lead records in context.md and responds with which teams are affected
   c. When project lead responds with affected teams, notify those `team-lead-{team}` agents (background) so they are aware of incoming changes to their domain
3. **Spawn experts directly** — prefer team-scoped variants (`expert-{name}_{team}`) over generic experts when the task falls within a team's domain. Launch parallel background agents for domain questions.
4. **On work completion**, simultaneously:
   a. Report results to user (foreground)
   b. Notify `project-lead-{project}` (background) with outcomes → project lead records in context.md and flags team leads that need context updates
   c. Notify affected `team-lead-{team}` (background) with what changed → team lead reviews against patterns in general.md, updates general.md with new lessons, flags any pattern violations

**Key principles:**

- **Orchestrator is a coordinator, not a worker** — NEVER write code directly. Delegate ALL implementation to background agents and stay free for user conversation.
- **Leads NEVER block implementation** — always notify in background, never wait for a response before starting work
- **Project lead is the context router** — it knows which teams a change touches and tells the orchestrator which team leads need updates
- **The orchestrator CAN update team leads directly**, but the project lead should inform which ones are affected
- **Team leads review completed work** — after implementation agents finish, notify affected team leads (background) so they can review changes against team patterns and update general.md
- **Experts are the core value** — they answer domain questions grounded in real source code. Spawn them freely.

**Execution rules:**

- **Always run ALL agents in the background** (`run_in_background: true`) — implementation agents, project-lead, experts, team leads
- **Maximize parallel agents** — launch as many independent agents as possible in a single message
- The orchestrator stays conversational with the user while agents work asynchronously
- Only use foreground agents when the result is required before responding

### Agent teams model

Use agent teams when the task benefits from **lateral communication** between workers — not just results flowing back to you.

**When to create an agent team:**

- Work spans multiple hivemind teams or expert domains
- Debugging with competing hypotheses — teammates investigate and challenge each other's theories
- Large features where teammates each own a separate module and need to coordinate interfaces
- Research or review where parallel perspectives add real value (security + performance + testing)

**How to structure teammates using hivemind context:**

Every teammate auto-loads `CLAUDE.md`, which includes all hivemind instructions and active project context. Teammates automatically know about available experts, teams, and project objectives.

- **Assign roles that map to hivemind experts or teams** — e.g., "You own the TUI layer (see the tui-dev team context)" or "You're the Nix infrastructure specialist"
- **Include domain context in spawn prompts** — reference `teams/<team>/general.md` for team-specific patterns and constraints
- **Break project objectives into tasks** — use the shared task list so teammates self-claim work
- **Teammates can spawn hivemind experts as subagents** within their own session for domain-specific knowledge

**Coordination patterns:**

- On plan approval, notify project-lead (background) → create agent team → assign tasks from objectives
- Teammates discuss interfaces and dependencies directly via messages
- Require plan approval for risky work — teammates plan in read-only mode until the lead approves
- Team leads can be consulted (as subagents within a teammate) for cross-cutting architectural guidance
- After all tasks complete, notify project-lead (background) to record outcomes

**Team sizing:** Start with 3-5 teammates. Aim for 5-6 tasks per teammate. Three focused teammates outperform five scattered ones.

**Avoid file conflicts:** Break work so each teammate owns different files. Two teammates editing the same file leads to overwrites.

### Metadata update timing

| When | Who | What |
|------|-----|------|
| Plan approved | Project lead (bg) | Notified of scope → responds with affected teams |
| During work | Implementation agent(s) (bg) | Execute code changes delegated by orchestrator |
| During work | Orchestrator reads | teams/\<team\>/general.md — domain context |
| Work complete | Project lead (bg) | Records outcomes in context.md, flags teams to update |
| Work complete | Team lead(s) (bg) | Review changes against patterns in general.md, update with new lessons |

### Orchestrator operational notes

**Subagent permissions and scope:**
- Spawn implementation agents with `mode: "acceptEdits"` — they can read and edit files but NEVER run bash commands
- NEVER use `mode: "bypassPermissions"` — it bypasses all governance
- If an agent's work requires a bash command (e.g., `hivemind redeploy`, import verification), the agent reports back and the orchestrator runs it
- Responsibility split: subagents edit files → orchestrator runs commands → user handles git/deploys
- The session MUST be in `acceptEdits` mode for agents to edit files — set globally via `hivemind.json` → `providers.claude.permissions.defaultMode`, then `hivemind init` to propagate
- Prefer team-scoped expert variants (`expert-{name}_{team}`) over generic experts (`expert-{name}`) when working within a team's domain — team-scoped variants have team patterns from general.md baked in

**Template vs deployed agents:**
- `hivemind_cli/templates.py` templates only affect NEW leads created after changes
- Existing leads deploy from `teams/<team>/lead.md` — update these files directly for current teams
- Always update BOTH the template (future) and existing `lead.md` files (current), then run `hivemind redeploy`

**Orchestrator responsibilities:**
- Run `hivemind redeploy` after agents edit template, lead, or provider instruction files
- Run import verification (`uv run python -c "..."`) after implementation agents complete
- Route team lead notifications based on project lead's affected-teams response — this is not optional
- Never write code directly — delegate ALL file changes to background agents
