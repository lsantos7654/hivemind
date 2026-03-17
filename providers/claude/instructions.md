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

1. **Consult `project-lead-{project}`** (background) to scope objectives and track progress
2. **Read team context** (`teams/<team>/general.md`) for domain patterns and constraints
3. **Spawn experts directly** in parallel background agents for implementation work
4. **Consult team leads** (foreground, quick) only when you need domain-specific architectural advice
5. **After work completes**, consult project-lead (background) to record outcomes in context.md

**Execution rules:**

- **Always run project-lead and expert agents in the background** (`run_in_background: true`)
- **Maximize parallel agents** — launch as many independent agents as possible in a single message
- **Team leads are advisors**, not delegators — consult them for guidance, don't ask them to spawn experts
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

- Consult project-lead (as subagent) to scope work → create agent team → assign tasks from objectives
- Teammates discuss interfaces and dependencies directly via messages
- Require plan approval for risky work — teammates plan in read-only mode until the lead approves
- Team leads can be consulted (as subagents within a teammate) for cross-cutting architectural guidance
- After all tasks complete, consult project-lead to record outcomes

**Team sizing:** Start with 3-5 teammates. Aim for 5-6 tasks per teammate. Three focused teammates outperform five scattered ones.

**Avoid file conflicts:** Break work so each teammate owns different files. Two teammates editing the same file leads to overwrites.

### Metadata update timing

| When | Who | What |
|------|-----|------|
| Before work | Project lead (bg/task) | context.md — scope, decisions |
| Before work | Orchestrator reads | teams/\<team\>/general.md — domain context |
| After work | Project lead (bg/task) | context.md — outcomes, todos checked off |
| After lessons | Orchestrator writes | teams/\<team\>/general.md — new patterns |
