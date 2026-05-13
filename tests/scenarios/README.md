# Scenario Tests

Scenario integration tests derived from `docs/WORKFLOW_SCENARIO.md`.

## Layout

| Phase | File | Kind | Exercised primitives |
|-------|------|------|---------------------|
| 1 | `test_phase01_generate_team.py` | pytest | `prep_create_team`, `finalize_create_team`, `Task(ephemeral=true)`, `/global/reload-agents` |
| 2 | `phase02-presence.test.ts` | engine (bun) | WebSocket presence channel (patch 0015), `list_sessions` MCP |
| 3 | `phase03-cross-session-messaging.test.ts` | engine (bun) | `send_message` MCP, per-session inbox (patch 0007) |
| 4 | `phase04-background-spawn.test.ts` | engine (bun) | `Task(background=true)`, `SessionBackground.complete`, `read_task_result` |
| 5 | `phase05-resume-memory.test.ts` | engine (bun) | `Task(task_id=...)`, `memory: true`, system prompt assembly |
| 6 | `phase06-per-expert-daemon.test.ts` | engine (bun) | `file.write` hook (patch 0019), `HivemindMemoryPlugin`, ephemeral cleanup (patch 0021) |
| 7 | `phase07-source-fork-ephemeral.test.ts` | engine (bun) | `Task(source_session_id=..., ephemeral=true)`, `Session.fork`, ephemeral cleanup |
| 8 | `phase08-bidirectional-messaging.test.ts` | engine (bun) | `send_message` round-trip, inbox wake-up |
| 9 | `test_phase09_orchestrator_memory.py` | pytest | Orchestrator's `_orchestrator/short_memory.md` grows on cue |
| 10 | `test_phase10_hivemind_sync.py` | pytest | Worktree scoping, `switch_version` curator path, atomic HEAD rotation |
| 11 | `phase11-daemon-orchestrator.test.ts` | engine (bun) | `mainID = writer.parent_id ?? writer.id` resolves to orchestrator when writer is orchestrator |
| 12 | `phase12-long-arc-session.test.ts` | engine (bun) | Session resumes after engine restart; `task_id` works across restarts; long-term expert memory carries across spawns |

## Running

```bash
# All scenario stubs (pytest layer)
bazelisk test //tests/scenarios:all

# All scenario stubs (engine layer)
bazelisk test '@opencode_src//...' --test_tag_filters=scenario

# Combined (both layers)
bazelisk test //... '@opencode_src//...' --test_tag_filters=scenario
```

## Status

All tests are stubs (`test.skip("TODO: Stage 11")`) — they establish a
coverage tracking surface before implementation. See
`docs/TESTING_ROADMAP.md` Stage 10.
