# Testing & Quality Roadmap

A multi-stage plan to take `hivemind_opencode` from its current state
to production-ready testing, linting, type-checking, and pre-commit.
Local-only (no GitHub CI); `make test` is the single entry point.

## Reading this document

Stages are grouped into four tracks plus a hardening tail. Each stage
names its prerequisites; later stages assume earlier stages landed.
Within a track, stages must be sequenced; across tracks they can be
worked in parallel (subject to track-level prerequisites).

```
                    Stage 0 — Bazel substrate ✅
                    Stage 1 — Stabilize test run ✅
                              │
         ┌────────────────────┼──────────────────────┐
         ▼                    ▼                      ▼
    Track A              Track B                 Track D
    Quality gates        Convention polish       Scenario coverage
    2 → 3                5, 6, 7                 10 → 11 → 12
         │                    │
         │                    ▼
         │              Track C (after B)
         │              Coverage gaps
         │              8, 9
         │
         ▼
    Track E
    Hardening
    13
```

| Track | Stages | Purpose |
|---|---|---|
| **A** | 2, 3 | Instrument coverage, ratchet strict mode (mypy + biome). Depends on Stage 1. |
| **B** | 5, 6, 7 | Bazel test conventions, Pydantic correctness, engine test cleanup. Independent. |
| **C** | 8, 9 | Engine route coverage + Python module coverage expansion. Depends on Track B. |
| **D** | 10, 11, 12 | Per-phase scenario tests from WORKFLOW_SCENARIO.md + E2E harness. Independent. |
| **E** | 13 | Optional hardening (mutation, property, perf regression). |

### Recommended priority order

Local-only — no CI. Build what gives the most signal per effort:

```
Stage 2 (coverage) → Stage 10 (scenario stubs) → Stage 11 (scenario impl)
      → Stage 3 (strict mode) → Stages 5,7 (convention polish)
      → Stages 8,9 (gap filling) → Stage 12 (E2E) → Stage 13 (hardening)
```

Stage 6 (Pydantic testing) can slot in anytime after Stage 3.
Stage 10 only requires Stage 0 (done). Stage 11 lists Stages 5 and 7 as
soft prerequisites for cleaner fixtures — relaxable if needed.

## Ground rules

- **Bazel is the substrate.** Every test, lint, format, and
  type-check runs through a Bazel target. `make test`, `make lint`,
  `make typecheck` etc. wrap `bazelisk` only — no direct `pytest`,
  `bun test`, `ruff`, `mypy`, or `tsgo` invocations from Make.
- **Coverage for both layers.** `pytest-cov` for Python, `bun test
  --coverage` for the engine. Aggregated into a single LCOV → HTML
  report.
- **No BuildBuddy / RBE.** Local sandboxing only.
- **Production-ready means strict.** mypy strict on every Python
  package (including `crawl/` and `tui/` — drop the relaxations).
  `tsgo --noEmit` strict on engine TypeScript.
- **Upstream tests excluded via `_SKIP`** in BUILD.bazel.opencode —
  no tags, no silent failures. The targets simply don't exist.
- **Each stage names experts to consult.**

## Source-of-truth references

- `docs/WORKFLOW_SCENARIO.md` — canonical 12-phase user journey;
  `▶ Test:` callouts define what scenario tests must cover.
- `docs/MEMORY_DAEMON.md` — feature reference for the memory daemon.
- `docs/ARCHITECTURE.md` — layered architecture.
- `AGENTS.md` — project conventions, patched-engine internals.

---

# Stage 0 — Bazel substrate ✅ **DONE**

**Goal:** every test, lint, format, type-check runs through Bazel.
The Makefile becomes a thin alias layer over `bazelisk` invocations.

**Status:** complete. 168/168 tests, all lint + typecheck targets pass.

## Tasks (all complete)

- [x] **`bun_test` Bazel macro** at `tools/bazel/bun_test.bzl`. Tagged `engine`.
- [x] **`tsc_test` Bazel macro** at `tools/bazel/tsc_test.bzl`. Tagged `engine` + `typecheck`.
- [x] **`ruff_check_test` and `ruff_format_test`** at `tools/bazel/ruff_test.bzl`. Tagged `lint`.
- [x] **`mypy_test`** at `tools/bazel/mypy_test.bzl`. Tagged `typecheck`.
  `tests/mypy` intentionally absent — 51 untyped test functions. Stage 3 fixes that.
- [x] **`buildifier_check_test`** at `tools/bazel/buildifier_test.bzl`. Tagged `lint`.
- [x] **Makefile rewritten** — every target wraps `bazelisk`.
- [x] **Stripped placeholder package.json scripts.**
- [x] **`format` aggregate sh_binary** at `tools/bazel/format.sh`.

## Deviations from the original plan

1. `aspect_bazel_lib` does NOT have a bun toolchain — bun exposed at `//third_party:bun`.
2. `py_console_script_binary` doesn't work for ruff — use `py_entrypoint_binary`.
3. mypy needs runtime deps in its venv — use `py_venv_binary`.
4. Pre-commit Bazel target dropped — needs network for hook repos.
5. `_engine_rlocation.pyi` stub equalizes uv-driven vs Bazel-driven mypy.
6. `scripts/dev-opencode.py` regex tolerant of buildifier kwarg reordering.
7. Pre-commit excludes for `third_party/{patches,dep_patches}/`.
8. No `aspect_rules_js`/`aspect_rules_ts` — custom macros are sufficient.
9. **Selective node_modules symlinking** — `@opencode-ai/plugin` resolves to patched source.

## Files

**Modified:** `Makefile`, `MODULE.bazel`, `BUILD.bazel`, `src/hivemind/BUILD.bazel`,
`tests/BUILD.bazel`, `third_party/BUILD.bazel`, `third_party/dep_patches/BUILD.bazel`,
`tools/BUILD.bazel`, `pyproject.toml`, `src/hivemind/opencode.py`,
`src/hivemind/mcp/tools.py`, `scripts/dev-opencode.py`,
`third_party/extensions.bzl`, `third_party/opencode_install.bzl`,
`third_party/opencode/BUILD.bazel.opencode`, `.pre-commit-config.yaml`.

**Created:** `tools/bazel/{BUILD.bazel, README.md}`;
`tools/bazel/{ruff_test.bzl, mypy_test.bzl, buildifier_test.bzl,
bun_test.bzl, tsc_test.bzl}`; runner scripts for all test types;
`tools/bazel/format.sh`; `src/hivemind/_engine_rlocation.pyi`.

## Verification

```bash
make lint         # ruff + buildifier
make typecheck    # mypy on src/ + engine_typecheck
make unit         # 5 pytest targets
make engine-test  # 154 bun_test targets
make format       # ruff format + buildifier fix + ruff check --fix
make test         # everything — 168/168 pass
```

---

# Stage 1 — Stabilize default test run ✅ **DONE**

**Goal:** `make test` is green. No tagged failures, no silent exceptions.

**Status:** complete. 168/168 pass. `engine_typecheck` passes.
26 consolidated patches (down from 35).

## What changed

### Engine TypeScript fixes (captured as patches)

| File | Fix |
|---|---|
| `agent.ts` | `State = Omit<Interface, "generate" \| "reload">` — reload is service-level |
| `agent.ts` | `Effect.serviceOption(Bus.Service)` + `Option.isSome` — reload works without Bus.Service in scope |
| `agent.ts` | `reloadAll`: typed boundary assertion on `Instance.provide` return |
| `config.ts` | Removed Zod `.default()`; added post-migration `??=` defaults so autoshare→share migration isn't blocked |
| `server.ts` + presence tests | `type BunServer = ReturnType<typeof Bun.serve>` + non-null port assertions |
| `footer.tsx` | Slot handler types from updated `TuiHostSlotMap` |
| `task.ts` | `nextSession!.id` non-null in cancel callback |
| `read-task-result.ts` | Explicit return type including `"running"` variant |
| `plugin/package.json` | Added `types` + exports `types` conditions |
| `plugin/tui.ts` | Added `session_footer` to `TuiHostSlotMap` |
| `test/permission/next.test.ts` | Updated 9 fromConfig assertions for `{bash, "sudo *", deny}` prefix |

### Build system fixes

| File | Fix |
|---|---|
| `third_party/opencode_install.bzl` | Selective node_modules symlinking — substitute `@opencode-ai/plugin` → patched source |
| `third_party/opencode/BUILD.bazel.opencode` | `_SKIP` filter — 3 upstream tests excluded. No tags. |

### Three upstream tests excluded

| File | Reason |
|---|---|
| `effect/cross-spawn-spawner.test.ts` | Spawns `node -e` — sandbox has only `bun` in PATH |
| `lsp/index.test.ts` | Runs `npm install` — network needed |
| `memory/abort-leak.test.ts` | Fetches `https://example.com` + sandbox memory profile skew |

### Patch consolidation: 35 → 26

- Dropped 3 dead-end tsconfig experiment patches
- Merged reload type fixes into reload endpoint patch (2 saved)
- Merged permission test fixes into sudo deny patch (1 saved)
- Merged TuiHostSlotMap into session_footer slot patch (1 saved)
- Combined dep types patches into one (1 saved)
- Combined remaining tsgo fixes into one (1 saved)

## Verification

```bash
make test    # 168/168 pass
```

---

# Stage 2 — Coverage instrumentation

**Goal:** generate coverage reports for both layers (Python via
`pytest-cov`, engine via `bun test --coverage`), merge into a
single HTML report via `make coverage`.

## Prerequisites

Stages 0, 1 (Bazel substrate + green baseline).

## Tasks

- [ ] **Add `pytest-cov`** to `pyproject.toml` + pin in `uv.lock`.
- [ ] **`py_test` targets emit LCOV** via `--cov=src/hivemind --cov-report=lcov`.
- [ ] **`bun_test` targets emit LCOV** via `bun test --coverage --coverage-reporter=lcov`.
  Plumb through `bun_test.bzl`.
- [ ] **`//tools/coverage:report`** aggregating LCOV from both layers → HTML.
- [ ] **`make coverage`** — replace the current stub.
- [ ] **`.coveragerc`** with per-package thresholds.

## Files

**Modify:** `pyproject.toml`, `uv.lock`, `Makefile`, `tools/bazel/bun_test.bzl`.
**Create:** `.coveragerc`, `tools/coverage/aggregate.py`, `tools/coverage/BUILD.bazel`.

## Experts

- **`expert-rules_python`** — coverage collection vs pytest-cov direct emission
- **`expert-bun`** — `bun test --coverage --coverage-reporter=lcov`
- **`expert-bazel`** — LCOV aggregation

## Verification

```bash
make coverage
open bazel-bin/tools/coverage/report/index.html
```

---

# Stage 3 — Quality gates: strict mode + biome

**Goal:** mypy strict on every Python package. Engine TS lint via biome.
Pre-commit wired with buildifier + biome hooks.

## Prerequisites

Stages 0, 1, 2.

## Tasks

### Pre-commit polish

- [ ] **Add `keith/pre-commit-buildifier`** to `.pre-commit-config.yaml`.
- [ ] **Add `biome check` as a local hook.**
- [ ] **Document pre-commit workflow.**

### Python — strict mypy

- [ ] **Drop mypy relaxations** for `crawl/` and `tui/`. Install `types-*` stubs.
- [ ] **Annotate ~51 test functions** with `-> None` and add `tests/mypy` target.

### Engine — TypeScript strict + biome

- [ ] **Flip `noUncheckedIndexedAccess: true`** in engine tsconfig (dep patch).
- [ ] **Adopt biome** — create `biome.json`, `biome_check_test` target, wire into `make format`.

## Files

**Modify:** `pyproject.toml`, `uv.lock`, `tests/BUILD.bazel`, `tests/test_*.py`,
`.pre-commit-config.yaml`.
**Create:** `dev/opencode/biome.json` (via patches), `tools/bazel/biome_test.bzl`.

## Experts

- **`expert-mypy`** — strict-mode, `types-*` selection
- **`expert-pre-commit`** — config shape
- **`expert-biome`** — schema, rule selection
- **`expert-pydantic`** — mypy plugin

## Verification

```bash
make lint      # Bazel-driven (now with biome)
make typecheck # mypy on src/ AND tests/
```

---

# Stage 5 — Bazel test conventions polish

**Goal:** tests use canonical `aspect_rules_py` patterns; hermeticity is
env-driven, not import-order-dependent.

## Prerequisites

Stage 0. (Independent — parallel track.)

## Tasks

- [ ] **Refactor `tests/BUILD.bazel` to use `py_pytest_main`.**
- [ ] **Move `imports` to `//src/hivemind:lib`** for `PyInfo` propagation.
- [ ] **Refactor `core_paths` fixture** from monkeypatch → env-driven (`HIVEMIND_HOME`).
- [ ] **Audit remaining hard-coded paths.**
- [ ] **Tags audit** — verify every target carries the right tag.

## Experts

- **`expert-rules_python`** — `py_pytest_main`, `PyInfo.imports`
- **`expert-bazel`** — `TEST_TMPDIR`, sandbox env vars

---

# Stage 6 — Pydantic correctness + discriminator migration

**Goal:** every Pydantic model has negative-path coverage; discriminator
uses the canonical native pattern.

## Prerequisites

Stages 3, 5.

## Tasks

- [ ] **`tests/test_models.py`** — `pytest.raises(ValidationError)` for every model.
- [ ] **Migrate `models.py`** from `mode="before"` to
  `Annotated[..., Field(discriminator="kind")]`.
- [ ] **Replace `save_json(model.model_dump())`** with `model_dump_json()`.

## Experts

- **`expert-pydantic`** — discriminator migration, error type contract

---

# Stage 7 — Engine test antipattern cleanup

**Goal:** engine tests stop using flaky-sleep, process-global mutations,
and dead assertions.

## Prerequisites

Stage 0. (Independent — parallel track.)

## Tasks

- [ ] **`presence.test.ts`** — replace `Bun.sleep` + poll with `awaitContains`.
- [ ] **`hivemind-memory.test.ts`** — drop `process.chdir`; pass directory via plugin input.
- [ ] **`file-write-hook.test.ts`** — fix `expect(true).toBe(true)`; use `expect.assertions(N)`.
- [ ] **Create `test/setup.ts`** with shared setup; wire via `bunfig.toml`.

## Experts

- **`expert-bun`** — `bun:test` lifecycle, `--preload`/bunfig

---

# Stage 8 — Engine test gaps (Hono routes)

**Goal:** every Hono route has happy-path + validation-rejection +
(auth middleware) test coverage.

## Prerequisites

Stages 0, 7.

## Tasks

- [ ] **Export `AppType`** from `server.ts` for typed testClient.
- [ ] **Validation-rejection test** for a `validator()`-gated route.
- [ ] **Auth middleware test** — `OPENCODE_SERVER_PASSWORD` → 401.
- [ ] **SSE test** for `/event` — exercise stream lifecycle.
- [ ] **Audit remaining routes** for missing tests.

## Experts

- **`expert-bun`** — Hono test patterns with bun:test

---

# Stage 9 — Python coverage expansion

**Goal:** every production Python module has basic test coverage.
TUI gets behavioral testing via Textual `Pilot`.

## Prerequisites

Stage 5.

## Tasks

- [ ] **`tests/test_lifecycle.py`** — enable/disable/delete, bootstrap, redeploy.
- [ ] **`tests/test_deployment.py`** — librarian, hivemind.md rendering.
- [ ] **`tests/test_cli.py`** — Typer `CliRunner`: list, status, redeploy, errors.
- [ ] **`tests/test_crawl_*.py`** — URL normalize, probe (in-process HTTP), extractor (fixture HTML).
- [ ] **`tests/test_tui_*.py`** — Textual `Pilot`: tabs, vim nav, mutations.
- [ ] **`tests/test_mcp_*.py`** — every MCP tool happy path, notification.

## Experts

- **`expert-typer`** — `CliRunner`
- **`expert-textual`** — `Pilot` API
- **`expert-trafilatura`** — fixture HTML
- **`expert-python-sdk`** — MCP testing

---

# Stage 10 — Scenario test scaffolding

**Goal:** every `▶ Test:` callout in `WORKFLOW_SCENARIO.md` has a
named test stub — a coverage tracking surface before implementation.

## Prerequisites

Stage 0. (Can start anytime.)

## Tasks

- [ ] **Create `tests/scenarios/README.md`.**
- [ ] **Pytest stubs** for Phases 1, 9, 10:
  `test_phase01_generate_team.py`, `test_phase09_orchestrator_memory.py`,
  `test_phase10_hivemind_sync.py`.
- [ ] **Engine stubs** for Phases 2-8, 11, 12:
  one per phase, named `phase##-<slug>.test.ts`.
- [ ] **Each stub** quotes the `▶ Test:` callout; body is `test.skip("TODO: Stage 11")`.
- [ ] **Tagged `["scenario", "skipped"]`.**

## Verification

```bash
bazelisk test //tests/scenarios:all   # all PASS via skip
```

---

# Stage 11 — Implement scenario tests (12 sub-stages)

**Goal:** convert each stub to a real test exercising the load-bearing
primitive. One sub-stage per WORKFLOW phase.

## Prerequisites

Stages 0, 10. (Stages 5 and 7 are soft — can build against Stage 1
layout if cleaner fixtures haven't landed yet.)

## Sub-stages

**11.1 — Phase 1: `/hivemind_generate_team`** — test full slash-command
flow against tmpdir worktree. Assert experts created, team deployed,
curator sessions auto-delete.

**11.2 — Phase 2: presence + `list_sessions`** — N TUIs converge to N;
kill one, count drops within a beat.

**11.3 — Phase 3: cross-session messaging** — `send_message` delivery
during idle and mid-turn; multi-message order preserved.

**11.4 — Phase 4: background spawn** — `Task(background=true)` returns
immediately; `read_task_result` consumes output.

**11.5 — Phase 5: resume + memory** — `Task(task_id=...)` resumes
verbatim; memory injected on every spawn.

**11.6 — Phase 6: per-expert daemon** — over-threshold write spawns
daemon; concurrent writes de-duped; no accumulation.

**11.7 — Phase 7: source-fork + ephemeral** — `Task(source_session_id=B,
ephemeral=true)` forks then auto-deletes.

**11.8 — Phase 8: bidirectional messaging** — two idle sessions exchange
messages; both advance independently.

**11.9 — Phase 9: orchestrator memory** — `short_memory.md` grows;
injected into subagent system prompt.

**11.10 — Phase 10: `/hivemind_sync`** — proposal reflects drift;
does not execute without confirmation; HEAD rotates atomically.

**11.11 — Phase 11: daemon at orchestrator depth** — daemon spawns under
orchestrator; memory survives compaction; cross-project recall works.

**11.12 — Phase 12: long-arc session** — session survives week-long idle
and engine restarts; week-1 memory still in week-4 prompt.

## Verification

```bash
bazelisk test //... --test_tag_filters=scenario   # all scenarios pass
```

---

# Stage 12 — End-to-end harness

**Goal:** a single test boots opencode against a tmpdir worktree and
runs the full WORKFLOW scenario in sequence.

## Prerequisites

Stage 11.

## Tasks

- [ ] **Build prism fixture** — `tests/e2e/fixtures/prism/` with
  minimal `package.json`, `MODULE.bazel`.
- [ ] **Write `tests/e2e/scenario.py`** — boots opencode, runs Phases
  1→12, asserts cumulative state at each beat.
- [ ] **Tag `["e2e", "manual"]`.** Add `make e2e` target.

---

# Stage 13 — Hardening (optional)

**Goal:** catch mutations, property violations, and regressions.

## Prerequisites

Stages 0–12.

## Tasks

- [ ] **Mutation testing** — `mutmut` for Python.
- [ ] **Property-based testing** — `hypothesis` (Python), `fast-check` (TS).
- [ ] **Patch regression tests** — `make dev-save` byte-stable; every
  patch applies cleanly in order.
- [ ] **Perf benchmarks** — engine boot time, MCP tool latency.

---

# Cross-cutting: experts to consult

**Team leads:**
- **`team-lead-hivemind`** — Stages 10, 11, 12

**Standalone:**
- **`expert-bun`** — Stages 0, 1, 2, 7, 8, 11, 12
- **`expert-bazel`** — Stages 0, 1, 2, 5, 11
- **`expert-rules_python`** — Stages 0, 2, 5, 12
- **`expert-pydantic`** — Stages 3, 6, 11, 13
- **`expert-mypy`** — Stage 3
- **`expert-pre-commit`** — Stage 3
- **`expert-biome`** — Stage 3
- **`expert-typer`**, **`expert-textual`**, **`expert-trafilatura`** — Stage 9
- **`expert-python-sdk`** — Stages 9, 11

---

# Out of scope

- GitHub CI / Actions.
- BuildBuddy / remote build executor.
- BCR mirroring.
- Cross-machine session discovery.
- Multi-engine support.
- Project-scoped orchestrator.
