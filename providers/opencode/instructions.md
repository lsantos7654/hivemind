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
