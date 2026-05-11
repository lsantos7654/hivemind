---
name: list_sessions
description: List all live sessions on this machine as a tree, with each root session and its spawned subagents. Use when you want a quick visual of who's running what.
---

# List sessions

Call the `list_sessions` MCP tool with `live_only=true` and `tree=true`.
The tool returns JSON with `index`, `id`, `title`, `branch`, `dir`, and
nested `children`. Build plain-text blocks from it. Wrap in a code block:

```
[1] Title of root
    id:      ses_1e82a3b26ffe9NOAlpDbuQCtlm
    branch:  main
    dir:     ~/projects/hivemind

[2] Another root
    id:      ses_1eb59b8f8ffeOX2WFUFHzr2WTW
    branch:  feat/existing-impl
    dir:     ~/projects/hivemind
    ├ [3] Subagent title
    │   id:      ses_1ea851de3ffeQ57P7qqP9QNfud
    └ [4] Another subagent
        id:      ses_1eb4fe767ffeu7vTY11FeEV9Nh
```

Rules:
- Roots (depth 0) show: `[index] title`, then `id`, `branch`, `dir` lines
- Subagents (nested in children) show only `[index] title` and `id`
- Omit branch/dir completely when null (no `—` placeholder)
- 4-space indent for meta lines, tree glyphs `├ ` / `└ ` for titles
- For non-last children, continuation lines use `│   `; last uses `    `
- Full ses_* ID, no truncation
- Blank line between root blocks only

If the result is empty, say "No live sessions."

After rendering, do NOT take further action.
