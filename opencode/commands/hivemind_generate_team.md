---
name: hivemind_generate_team
description: Scope the current worktree, find tech dependencies, ensure relevant hivemind experts exist and are enabled at the project's pinned versions, and create a project-scoped team that bundles them.
---

# Hivemind: generate a team for this project

Scope the current worktree, identify the technologies it depends on,
ensure hivemind has experts for each (creating missing ones from
upstream), and bundle the result into a team. The deliverable is
**one new team** the orchestrator can spawn for this project.

If you are uncertain about any step, prefer asking a clarifying
question over guessing. Otherwise execute the procedure end-to-end.

## Step 1 — Scope the worktree

Read whichever of these manifest files exist in the current working
directory. Stop at the first level — don't recurse into nested
projects.

| File | What to extract |
|---|---|
| `package.json` | `dependencies` + `devDependencies` keys + their versions |
| `pyproject.toml` | `[project.dependencies]`, `[tool.poetry.dependencies]`, `[tool.uv.dependencies]` |
| `uv.lock` / `poetry.lock` / `requirements.txt` | Resolved versions (preferred over loose pyproject ranges) |
| `MODULE.bazel` | `bazel_dep(name = "...", version = "...")` entries |
| `WORKSPACE` / `WORKSPACE.bazel` | Older Bazel — extract repo references |
| `Cargo.toml` / `Cargo.lock` | `[dependencies]` table; lock for resolved versions |
| `go.mod` | `require` directives |
| `Gemfile.lock` | Resolved gem versions |
| `composer.json` | PHP packages |
| `.tool-versions` (asdf) | Tool versions across ecosystems |
| `flake.nix` / `default.nix` | Nix-derived dependencies |

Build a list of `(tech_name, version, source_file)` tuples. Prefer
**lockfile** versions over loose dep ranges — `pyproject.toml` may
say `pydantic >= 2.0` while `uv.lock` says `2.10.4`. Pin to 2.10.4.

Focus on **direct, top-level** dependencies. Skip transitive deps
the user didn't pick. Skip experts for runtime libraries with no
meaningful upstream knowledge surface (one-line utility packages,
internal forks, etc.).

## Step 2 — Map each tech to a hivemind expert

For each `(tech, version)`:

1. Read `hivemind.json` (or use `list_agents` if available) and look
   for an entry whose name matches `expert-<tech>` or a close
   variant. Common naming:
   - `expert-bun`, `expert-bazel`, `expert-vitest`, `expert-pydantic`
   - `expert-<org>-<tech>` for ambiguous names
2. Classify each tech as:
   - **enabled** — already in catalog and deployed → ready
   - **unlisted / disabled** — in catalog but not deployed →
     `enable_agent(name)` queue
   - **missing** — not in catalog → needs a `hivemind-expert-curator`
     subagent spawn (which clones the upstream repo, performs the
     analysis in its own session, and registers the catalog entry as
     *unlisted*)
   - **version mismatch** — catalog version differs by a major
     release from project's pin → consider `switch_version`

For missing experts, determine the upstream repository URL. There
is **no curated mapping table** — figure it out per call. Sources:

- npm packages → check `package.json`'s `repository` field; failing
  that, the registry homepage at
  `https://registry.npmjs.org/<package>` returns metadata with
  repository links
- PyPI packages → `https://pypi.org/pypi/<package>/json` exposes
  `info.project_urls`
- Bazel modules → check the Bazel Central Registry's metadata at
  `https://registry.bazel.build/modules/<name>/<version>` — the
  `metadata.json` has `repository`
- Go modules → the module path itself is usually the repo URL
- Rust crates → `https://crates.io/api/v1/crates/<name>` exposes
  `repository`

If the project's tooling tells you (a `repository` field in
`package.json`, etc.) prefer that over registry lookups.

When in doubt, surface the URL to the user and let them confirm
before spawning the curator.

## Step 3 — Execute the queue

Spawn all curator subagents and run all fast direct-MCP calls **in
parallel** (single message, multiple tool calls). The curator handles
the slow operations (add + switch); fast direct-MCP handles
`enable_agent` for in-catalog matches.

```
# All in one message — opencode runs them concurrently:

# Missing — curator clones + analyzes in-session, registers as unlisted:
Task(
  subagent_type="hivemind-expert-curator",
  background=true,
  description="add <name>",
  prompt="Add expert from <url> with ref v<version>"
)

# Major version mismatch — curator handles cached vs fresh-analysis paths
# transparently (cached is sub-second; fresh runs in-session):
Task(
  subagent_type="hivemind-expert-curator",
  background=true,
  description="switch <name> to v<version>",
  prompt="Switch <name> to v<version>"
)

# Fast direct-MCP for in-catalog matches that just need deployment:
enable_agent(name=...)
```

Curator spawns return `task_id` immediately. Collect each via
`read_task_result(task_id=...)` once opencode reports the task ready
in a `<system-reminder>`. Newly-created experts land as *unlisted*,
so queue an `enable_agent(name=...)` after each successful add.

## Step 4 — Create the project team

Once all needed experts are enabled (or queued for enable), spawn the
curator with the create-team intent. The curator generates one
`## expert-<name>` section per roster member in-session — a multi-minute
operation that would time out as a direct MCP call.

```
Task(
  subagent_type="hivemind-expert-curator",
  background=true,
  description="create team <team-name>",
  prompt="Create team <team-name> with experts <comma-separated names> and description '<one-sentence project summary>'"
)
# → returns task_id; collect with read_task_result(task_id=...).

# After read_task_result reports success:
enable_agent(name="<team-name>")
```

**Team name:** pick something that identifies this project. The
worktree directory name is a sensible default but use your judgment
— a more meaningful name (the project's actual identity, not its
filesystem location) is fine if obvious. Don't ask the user unless
genuinely ambiguous.

If a team with this name already exists, reconcile via
`add_expert_to_team` / `remove_expert_from_team` instead of
recreating — those are fast direct-MCP tools (no curator needed).

## Step 5 — Report

Summarize for the user, organized by status:

```
✓ Already enabled: expert-bun, expert-vitest
✓ Newly enabled:   expert-pydantic
… Newly created:   expert-foo (curator spawned: ses_xxx — collect
                     with read_task_result, then enable_agent)
⚠ Version drift:   expert-bar (catalog: v3, project: v4)
✗ No upstream:     <tech>  (couldn't find a repo URL — please provide)

… Team `<name>`:   curator spawned: ses_yyy — collect with
                     read_task_result, then enable_agent.
Once enabled, spawn it with: Task(subagent_type="<name>", ...)
```

## When NOT to run this command

- The user has explicitly said "use existing experts" or "no setup".
- The worktree has no recognizable manifest files (likely not a
  software project).
- The user is mid-debugging an unrelated issue and you're being
  asked to "set up experts" as a tangent — confirm intent first.
