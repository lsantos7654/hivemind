## Orchestration model

**The primary agent coordinates all work.** Subagents are spawned via the `task` tool and report results back. Subagents cannot communicate with each other — all coordination flows through the primary agent.

**Workflow:**

1. **Consult `project-lead-{project}`** via task to scope objectives and track progress
2. **Read team context** (`teams/<team>/general.md`) for domain patterns and constraints
3. **Spawn experts via `task`** for implementation work — launch multiple tasks in parallel when independent
4. **Consult team leads** via task only when you need domain-specific architectural advice
5. **After work completes**, consult project-lead via task to record outcomes in context.md

**Agent execution rules:**

- **Use the `task` tool** to spawn any hivemind agent (experts, team leads, project leads)
- **Maximize parallel tasks** — spawn independent tasks simultaneously for throughput
- **Team leads are advisors**, not delegators — consult them for guidance, don't ask them to spawn experts
- The primary agent stays conversational with the user while tasks run
- All agents are discovered automatically from the `agents/` directory

**Metadata update timing:**

| When | Who | What |
|------|-----|------|
| Before work | Project lead (task) | context.md — scope, decisions |
| Before work | Primary agent reads | teams/\<team\>/general.md — domain context |
| After work | Project lead (task) | context.md — outcomes, todos checked off |
| After lessons | Primary agent writes | teams/\<team\>/general.md — new patterns |
