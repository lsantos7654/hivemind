---
name: hivemind_sync
description: Scope the current worktree, identify tech dependencies and pinned versions, and propose which hivemind experts to enable, create, or switch_version so the catalog matches what this project actually uses (e.g. .bazelversion 8.5.1 → expert-bazel @ 8.5.1). Proposes first; executes only on confirmation. No team is created — for that, use /hivemind_generate_team instead.
---

# Hivemind: sync experts for this project

Scope the current worktree, identify the technologies and pinned
versions it depends on, and produce a **proposal** of which hivemind
experts to enable (unlisted/disabled but in catalog), create from
upstream (missing), or `switch_version` (catalog HEAD doesn't match
project pin). **Do not execute the proposal until the user confirms.**

If you are uncertain about any step, ask a clarifying question rather
than guessing.

## Step 1 — Scope the worktree

Read whichever of these files exist in the cwd. Stop at the first
level — don't recurse into nested projects. Two file categories:

**Dependency manifests** (multi-package; produces `(tech, version)`
tuples):

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
| `flake.nix` / `default.nix` | Nix-derived dependencies |

**Single-tool version pins** (one tool → one version, no dep tree):

| File | Tech |
|---|---|
| `.bazelversion` | bazel |
| `.python-version` (pyenv) | python |
| `.nvmrc` | node |
| `.ruby-version` | ruby |
| `.go-version` | go |
| `.tool-versions` (asdf) | multiple — format `<tool> <version>` per line |

Build a list of `(tech_name, pinned_version, source_file)` tuples.
Prefer **lockfile** versions over loose dep ranges — `pyproject.toml`
may say `pydantic >= 2.0` while `uv.lock` says `2.10.4`. Pin to
2.10.4. Focus on **direct, top-level** dependencies — skip transitive
deps and runtime utilities with no meaningful upstream knowledge
surface (one-line packages, internal forks, etc.).

## Step 2 — Map each tech to a hivemind expert

For each `(tech, pinned_version)`:

1. Call `list_agents()` to find an entry matching `expert-<tech>` or
   a close variant (`expert-<org>-<tech>` for ambiguous names).
2. For experts in catalog, call `show_agent(name)` to read the
   current pin. Returned body has `ref_name` (e.g. `"8.5.0"`) and
   `commit` (resolved SHA). Use `ref_name` for comparison when
   present; fall back to `commit` for raw-SHA pins.
3. Classify each tech:
   - **enabled + version match** — `ref_name` (or `commit`) equals
     the project pin → done
   - **enabled + version mismatch** — `switch_version` candidate.
     Compare exact strings: catalog `ref_name` `8.5.0` vs project
     pin `8.5.1` → mismatch. Patch-level drift counts; the goal is
     exact alignment with the project's pin.
   - **unlisted / disabled** (in catalog) — `enable_agent` candidate.
     If `ref_name` also drifts from pin, queue `switch_version` first.
   - **missing** — `hivemind-expert-curator` spawn candidate. The
     curator clones the upstream repo, performs the analysis in its
     own session, and registers the catalog entry as *unlisted*. The
     `ref` you pass through the curator's prompt pins the new expert
     at analysis time so it lands at the right version, not `main`.

For missing experts, determine the upstream repo URL — you'll pass
it (and the ref) into the curator's prompt in Step 4. There is no
curated mapping table — figure it out per call:

- npm packages → `package.json`'s `repository` field, or
  `https://registry.npmjs.org/<package>` returns metadata with
  repository links
- PyPI packages → `https://pypi.org/pypi/<package>/json` exposes
  `info.project_urls`
- Bazel modules → `https://registry.bazel.build/modules/<name>/<version>`
  has `metadata.json.repository`
- Go modules → the module path itself is usually the repo URL
- Rust crates → `https://crates.io/api/v1/crates/<name>` exposes
  `repository`

When in doubt, surface the URL in the proposal and let the user
confirm before spawning the curator.

**Tag format:** the `ref` passed to `switch_version` (or to the
curator via its prompt) accepts any ref that resolves in the cloned
repo — tags are fetched first so freshly-pushed releases work. For
Bazel (tags as `8.5.1`) pass the bare version. For repos that prefix
with `v` (e.g. `v0.7.3`) pass the prefixed form. Try the literal
version first; if `switch_version` rejects it as not-found, retry
with the `v` prefix.

## Step 3 — Propose

Render the result as a single grouped report and **stop**. Do not
spawn the curator and do not call `enable_agent` / `switch_version`
yet.

Format:

```
For repo `<cwd-basename>` (<short project summary>):

✓ Already enabled at correct version (no action):
  - expert-bun (HEAD: 1.3.11, project: 1.3.11)

↻ Switch version (catalog HEAD ≠ project pin):
  - expert-bazel (HEAD: 8.5.0, project: 8.5.1) — .bazelversion
  - expert-pydantic (HEAD: 2.9.0, project: 2.10.4) — uv.lock

+ Enable (in catalog, currently unlisted/disabled):
  - expert-rich (catalog HEAD: 13.7.1, project: 13.7.1)
  - expert-pytest (catalog HEAD: 8.0, project: 8.2) — also needs
    switch_version

+ Create + enable (missing from catalog):
  - expert-foo → https://github.com/foo/foo (ref: v2.1.0)
  - expert-bar → https://github.com/bar/bar (ref: 0.7.3)

✗ No upstream URL found (please confirm or provide):
  - <tech-name> — couldn't resolve repo URL

Proceed? (yes / pick a subset / no)
```

After printing this, **stop**. Wait for the user. If they say "yes",
move to Step 4 with the full set. If they pick a subset, execute
that subset. If they say "no", do nothing.

## Step 4 — Execute on confirmation

Spawn all curator subagents and run all fast direct-MCP calls **in
parallel** (single message, multiple tool calls). The curator handles
the slow operations (switch + create) — each runs in its own session,
returns a `task_id` immediately, and you collect the results as they
finish. The fast operations (`enable_agent` for in-catalog matches)
run alongside.

```
# All in one message — opencode runs them concurrently:

# Switch existing experts to project pin (curator handles cached vs
# fresh-analysis paths transparently — cached is sub-second, fresh
# runs in-session):
Task(
  subagent_type="hivemind-expert-curator",
  background=true,
  description="switch <name> to <ref>",
  prompt="Switch <name> to <ref>"
)

# Add missing experts (curator clones + analyzes in-session, registers
# the catalog entry as unlisted):
Task(
  subagent_type="hivemind-expert-curator",
  background=true,
  description="add <name>",
  prompt="Add expert from <url> with ref <pinned_version>"
)

# Fast direct-MCP for in-catalog matches that just need deployment:
enable_agent(name=...)
```

Curator spawns return `task_id` immediately. As each finishes opencode
shows the ready ID in a `<system-reminder>`; collect each via
`read_task_result(task_id=...)`. Newly-created experts land as
*unlisted*, so queue an `enable_agent(name=...)` after each successful
add.

Order within a single expert: switch first, then enable. The deployed
file should reflect the pinned version, not the prior HEAD.

## Step 5 — Report

Compact summary, organized by what changed:

```
✓ Already correct:                 expert-bun, expert-vitest
✓ Switched (cached, instant):      expert-bazel-lib, expert-jinja
✓ Switched (analyzed in-session):  expert-pydantic (8.5.0 → 8.5.1)
✓ Newly enabled:                   expert-rich
… Newly created:                   expert-foo (curator spawned: ses_xxx —
                                      collect with read_task_result, then enable_agent)
✗ Skipped:                         <tech> (no upstream URL provided)
```

(No team is created. Use `/hivemind_generate_team` if you also want
a project-scoped team bundling these experts.)

## When NOT to run this command

- The project has no recognizable manifest or version-pin files.
- The user asked to "use existing experts" or "skip setup".
- The user wants a team bundle — point them at
  `/hivemind_generate_team`.
- The user is mid-debugging an unrelated issue and "set up experts"
  is a tangent — confirm intent first.
