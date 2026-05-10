# Testing & Quality Roadmap

A multi-stage plan to take `hivemind_opencode` from its current state
to production-ready testing, linting, type-checking, pre-commit, and
CI. Designed to be worked through over many sessions.

## Reading this document

Stages are dependency-ordered and grouped into five tracks. Each
stage names its prerequisites; later stages assume earlier stages
landed. Within a track, stages must be sequenced; across tracks,
they can be worked in parallel (subject to track-level prerequisites
shown below).

```
                    Stage 0 — Bazel substrate ✅
                              │
        ┌─────────────────────┼──────────────────────┐
        ▼                     ▼                      ▼
   Track A             Track B (parallel)      Track D (parallel)
   Stabilize → ship CI Convention polish       Scenario coverage
   1 → 2 → 3 → 4       5 6 7                   10 → 11 → 12
                              │
                              ▼
                       Track C (after B)
                       Coverage gaps
                       8 9
                              │
                              ▼
                       Track E (after most)
                       13 Hardening
```

| Track | Stages | Purpose |
|---|---|---|
| **A** | 1, 2, 3, 4 | Stabilize default test run, instrument coverage, ratchet strict mode, ship CI. Each gates the next. |
| **B** | 5, 6, 7 | Bazel test conventions, Pydantic correctness, engine test antipattern cleanup. Depend only on Stage 0; shippable in any order. |
| **C** | 8, 9 | Engine route coverage (Hono) and Python module coverage expansion. Depend on Track B's polish. |
| **D** | 10, 11, 12 | Per-phase scenario tests + E2E harness. Independent of every other track besides Stage 0. |
| **E** | 13 | Optional hardening (mutation, property, perf regression). |

## Ground rules

- **Bazel is the substrate.** Every test, lint, format, and
  type-check runs through a Bazel target. `make test`, `make lint`,
  `make typecheck` etc. wrap `bazelisk` only — no direct `pytest`,
  `bun test`, `ruff`, `mypy`, or `tsgo` invocations from Make.
- **Coverage for both layers.** `pytest-cov` for Python, `bun test
  --coverage` for the engine. Aggregated into a single coverage
  surface in CI (LCOV → Codecov or self-hosted equivalent).
- **No BuildBuddy / RBE.** Local sandboxing + GitHub Actions cache.
- **Production-ready means strict.** mypy strict on every Python
  package (including `crawl/` and `tui/` — drop the relaxations).
  TypeScript `tsgo --noEmit` strict. Tests are themselves
  type-checked and linted.
- **Each stage names experts to consult.** Always go through the
  team lead first if one exists; spawn experts in parallel where
  possible.

## Source-of-truth references

- `docs/WORKFLOW_SCENARIO.md` — canonical 12-phase user journey;
  the `▶ Test:` callouts define what scenario tests must cover.
- `docs/MEMORY_DAEMON.md` — feature reference for the memory
  daemon (Phases 6 + 11 of the scenario doc).
- `docs/ARCHITECTURE.md` — layered architecture.
- `AGENTS.md` — project conventions; in particular the patched-
  engine + native `Bun.serve` notes.

---

# Stage 0 — Bazel as the universal entry point ✅ **DONE** (commit 9e043f8)

**Goal:** every test, lint, format, type-check, and coverage run
goes through Bazel. The Makefile becomes a thin alias layer over
`bazelisk` invocations.

**Status:** complete. Final pass rate at substage exit: 14/14 main
tests + 151/156 engine tests + 5 lint targets + 1 typecheck target.
The 5 engine failures are sandbox-dep environment issues (no `node`
in PATH, no network for `npm install`); they're surfaced — not
introduced — by Stage 0 wiring. **Stage 1 stabilizes them.**

## Prerequisites

None.

## Tasks (all complete)

- [x] **`bun_test` Bazel macro** at `tools/bazel/bun_test.bzl`. Each
  per-file target is an `sh_test` that resolves the engine
  workspace via `realpath(package.json marker)` and execs
  `bun test --timeout 30000 <relative path>`. Engine source is NOT
  copied into runfiles; the runner cds into the absolute external
  repo path so pnpm-style symlinks resolve. Tagged `engine`.
- [x] **`tsc_test` Bazel macro** at `tools/bazel/tsc_test.bzl`.
  Single target per TS package (not per file — tsgo runs at
  project granularity). Invokes `bun --bun node_modules/.bin/tsgo
  --noEmit` (the `--bun` flag overrides tsgo's `#!/usr/bin/env node`
  shebang since the sandbox has no node). Tagged
  `engine` + `typecheck`.
  - **`engine_typecheck` is currently tagged `manual`** — the
    patched engine has pre-existing TS errors (upstream + patch
    drift). Stage 1 removes the `manual` tag.
- [x] **`ruff_check_test` and `ruff_format_test` Bazel macros** at
  `tools/bazel/ruff_test.bzl`. Wrap `ruff check` / `ruff format
  --check`. Runner cds to `$TEST_SRCDIR/_main` so isort first-party
  detection works (fallback config: `[tool.ruff.lint.isort]
  known-first-party = ["hivemind"]`). Tagged `lint`.
- [x] **`mypy_test` Bazel macro** at `tools/bazel/mypy_test.bzl`.
  `mypy_bin` is a `py_venv_binary` (NOT `py_console_script_binary`)
  whose deps include `//src/hivemind:lib` so the venv contains
  every project runtime dep mypy needs to typecheck call sites.
  Runner exports `MYPYPATH=$TEST_SRCDIR/_main/src` and passes
  `--explicit-package-bases`. Tagged `typecheck`.
  - **`tests/mypy` is intentionally absent** — existing tests have
    51 untyped function signatures. Stage 3 fixes that and adds
    the target.
- [x] **`buildifier_check_test` macro** at
  `tools/bazel/buildifier_test.bzl` + `bazel_dep("buildifier_prebuilt"
  8.5.1.2 dev_dependency=True)`. The `--warnings=-canonical-repository`
  flag suppresses the `@@//` warning needed for cross-repo loads
  from BUILD.bazel.opencode. Companion `//tools/bazel:buildifier_fix`
  sh_binary applies fixes via `bazelisk run`. Tagged `lint`.
- [x] **Makefile rewritten** — every target wraps `bazelisk`. Real
  targets:
  ```make
  test:           bazelisk test //... '@opencode_src//...'
  unit:           bazelisk test //... --test_tag_filters=unit
  lint:           bazelisk test //... --test_tag_filters=lint
  typecheck:      bazelisk test //... --test_tag_filters=typecheck
  engine-test:    bazelisk test '@opencode_src//...' --test_tag_filters=engine
  format:         bazelisk run //tools/bazel:format
  coverage:       echo "Stage 2 deliverable"; exit 1
  ```
  `dev*` targets still shell to `scripts/dev-opencode.py`; `make
  dev-save` now also runs `//tools/bazel:buildifier_fix` since
  `_rewrite_patches_list` produces formatting drift.
- [x] **Stripped placeholder package.json scripts** —
  `random`/`lint`/`format`/`docs`/`deploy`/`clean` plus
  `randomField` removed. Captured as
  `third_party/dep_patches/0022-Strip-placeholder-package.json-scripts.patch`.
- [x] **Tag conventions documented** in `tools/bazel/README.md`
  with the canonical set: `unit`, `engine`, `lint`, `typecheck`,
  `scenario`, `e2e`, `manual`, `requires-network`.
- [x] **`format` aggregate sh_binary** at
  `tools/bazel/format.sh` — runs ruff format, buildifier --mode=fix,
  ruff check --fix in sequence. Bypasses RUNFILES_DIR contamination
  by computing the inner binary's runfiles root from
  `realpath("$ruff").runfiles`.

## Deviations from the original plan

These came up during implementation and are worth preserving for
future sessions:

1. **`aspect_bazel_lib` does NOT have a "bun toolchain"** — bun is
   exposed at `//third_party:bun` (a `select()` over four
   `@bun_*//:bin` filegroups). We reuse that label.
2. **`py_console_script_binary` doesn't work for ruff** — ruff's
   wheel uses the legacy `data/scripts/` mechanism, not
   `entry_points.txt`. Use `py_entrypoint_binary` with explicit
   `entrypoint = "ruff.__main__:_run"`.
3. **mypy needs hivemind's runtime deps in its venv** —
   `py_entrypoint_binary` only takes one `pkg`. Use
   `py_venv_binary` instead with `deps = [
     "//src/hivemind:lib", "@pypi//mypy"]` so mypy can resolve
   `import typer`, `import rich`, `import textual`, etc.
4. **The pre-commit Bazel target was dropped** — pre-commit needs
   network to fetch hook repos; not hermetic. Pre-commit stays as
   the existing git hook (which already runs ruff + ruff-format +
   mypy via `uv run`).
5. **`_engine_rlocation.pyi` stub added** — uv-driven mypy doesn't
   see the build-generated `_engine_rlocation.py` (lives in
   `bazel-bin/`); Bazel-driven mypy does. The stub equalizes both
   so `# type: ignore[import-untyped]` becomes unnecessary.
6. **`scripts/dev-opencode.py` regex tolerance** — buildifier
   reformats `ext.opencode(version=..., sha256=...)` to alphabetical
   kwargs. The version-extraction regex now matches the multi-line
   call body and pulls `version=` from anywhere within.
7. **Pre-commit excludes** — `third_party/{patches,dep_patches}/`
   added to `trailing-whitespace`, `end-of-file-fixer`, and
   `mixed-line-ending` hooks. `git format-patch` output is
   regenerated by `make dev-save` and would otherwise oscillate
   between hook-cleaned and dev-save-canonical states.
8. **No `aspect_rules_js`/`aspect_rules_ts` added** — confirmed
   neither is needed; custom `bun_test` + `tsc_test` macros over
   `sh_test` + `//third_party:bun` are sufficient.

## Files

**Modified:** `Makefile`, `MODULE.bazel`, `BUILD.bazel`,
`src/hivemind/BUILD.bazel`, `tests/BUILD.bazel`,
`third_party/BUILD.bazel`, `third_party/dep_patches/BUILD.bazel`,
`tools/BUILD.bazel`, `pyproject.toml`, `src/hivemind/opencode.py`,
`src/hivemind/mcp/tools.py`, `scripts/dev-opencode.py`,
`third_party/extensions.bzl`, `third_party/opencode_install.bzl`,
`third_party/opencode/BUILD.bazel.opencode`, `.pre-commit-config.yaml`.

**Created:** `tools/bazel/{BUILD.bazel, README.md}`;
`tools/bazel/{ruff_test.bzl, mypy_test.bzl, buildifier_test.bzl,
bun_test.bzl, tsc_test.bzl}`; `tools/bazel/{ruff_check_runner.sh,
ruff_format_runner.sh, mypy_main.py, mypy_runner.sh,
buildifier_check_runner.sh, buildifier_fix_runner.sh,
bun_test_runner.sh, tsc_runner.sh, format.sh}`;
`src/hivemind/_engine_rlocation.pyi`;
`third_party/dep_patches/0022-Strip-placeholder-package.json-scripts.patch`.

## Experts (consulted)

- **`expert-rules_python`** — `py_console_script_binary` /
  `py_entrypoint_binary` semantics, MYPYPATH from sh_test
  (notes file at `/Users/santos/.claude/teams/bazel/expert-rules_python/notes.md`)

## Verification

```bash
make lint         # ruff + buildifier on all Starlark + Python
make typecheck    # mypy on src/ (engine_typecheck is `manual`-tagged for now)
make unit         # 5 pytest targets
make engine-test  # 156 bun_test targets (151 pass)
make format       # ruff format + buildifier fix + ruff check --fix
make test         # everything
```

---

# Stage 1 — Stabilize default test run

**Goal:** every test in `bazelisk test //... '@opencode_src//...'`
is either green or correctly tagged. CI cannot ship in good faith
until this lands — otherwise day-one CI is red. Stage 0 left two
classes of known failures: 5–6 sandbox-sensitive engine tests, and
`engine_typecheck` (tagged `manual`) blocked by patched-engine TS
errors.

## Prerequisites

Stage 0.

## Tasks

### Tag the 5–6 sandbox-failing engine tests

These tests fail under `darwin-sandbox` for environment reasons,
not test bugs. Prefer per-test `requires-network` / `no-sandbox`
tags over `manual` so they still run under permissive CI configs:

- [ ] **`config_config_test`** — depends on real config dir paths.
  Add `requires-network` or `no-sandbox`, OR refactor to use
  `Instance.provide({directory})`.
- [ ] **`provider_provider_test`** — long-running (~66s); likely
  hits real provider URLs. Tag `requires-network` or mock the
  HTTP layer.
- [ ] **`effect_cross-spawn-spawner_test`** — calls `node -e ...`;
  the sandbox doesn't have `node` in PATH. Tag `requires-node`
  (new tag) or mock the spawner.
- [ ] **`lsp_index_test`** — calls `npm install
  typescript-language-server` (network required). Tag
  `requires-network` and mock the install in the test.
- [ ] **`memory_abort-leak_test`** — sandbox-sensitive process
  spawn. Tag `no-sandbox` or refactor.
- [ ] **`permission_next_test`** — sandbox-sensitive process
  spawn. Tag `no-sandbox` or refactor.

Tags are applied via the `bun_test` macro's `tags = [...]` arg. The
glob in `BUILD.bazel.opencode` needs an exception list so these
tests pick up the per-target tag.

### Fix `engine_typecheck` TS errors (drop the `manual` tag)

`engine_typecheck` was tagged `manual` in Stage 0 because the
patched engine has pre-existing TS errors. Categories observed:

- [ ] **`agent.ts` — missing `reload` method on `Agent.State`** —
  patches reference it but the type definition doesn't expose it.
  Add `reload: () => Effect<void, never, never>` to the State
  interface.
- [ ] **`agent.ts:472` — `result is of type 'unknown'`** —
  effect-ts type narrowing missing. Add explicit type or use
  `Effect.cast<>`.
- [ ] **`tui/feature-plugins/home/footer.tsx` — implicit `any`
  parameters** — patches added handlers without explicit types.
  Annotate `_ctx` and `props`.
- [ ] **`config.ts:111` — `{} not assignable to type 'Info'`** —
  patch type drift. Update the patch hunk to construct a proper
  `Info` value.
- [ ] **`test/server/presence-client.test.ts`,
  `test/server/presence.test.ts` —
  `Server<WebSocketData>` requires 1 type argument** — tighten
  the generic in patch 0015.
- [ ] **Drop `tags = ["manual"]`** from the `engine_typecheck`
  target in `BUILD.bazel.opencode`. Verify
  `bazelisk test '@opencode_src//:engine_typecheck'` passes.

### Update tag conventions

If `requires-node` is a new tag, document it in
`tools/bazel/README.md` alongside `requires-network`.

## Files

**Modify (via patches workflow — `make dev` then `make dev-save`):**
- `dev/opencode/packages/opencode/src/agent/agent.ts`
- `dev/opencode/packages/opencode/src/cli/cmd/tui/feature-plugins/home/footer.tsx`
- `dev/opencode/packages/opencode/src/config/config.ts`
- `dev/opencode/packages/opencode/test/server/presence.test.ts`
- `dev/opencode/packages/opencode/test/server/presence-client.test.ts`

**Modify (workspace):**
- `third_party/opencode/BUILD.bazel.opencode` — drop `manual` tag
  from `engine_typecheck`; add per-target tag overrides for the
  sandbox-failing tests
- `tools/bazel/README.md` — document any new tags

## Experts

- **`expert-bun`** — sandbox-runtime quirks (node-shebang, child
  process spawning under darwin-sandbox)
- **`expert-hono`** — `Server<WebSocketData>` typing in patches
- **`team-lead-bazel`** — `requires-network` / `no-sandbox` tag
  semantics on macOS

## Verification

```bash
make test               # 170/170 pass (or all "expected" fails tagged)
bazelisk test '@opencode_src//:engine_typecheck'  # passes
bazelisk test '@opencode_src//...' --test_tag_filters=engine,-requires-network,-no-sandbox
# → confirms tagged tests are excluded by tag filters
```

After this stage lands, `make test` is green by default. CI (Stage
4) can be added without inheriting red noise.

---

# Stage 2 — Coverage instrumentation

**Goal:** generate coverage reports for both layers, surface them
in CI, fail builds when coverage drops below a threshold.

## Prerequisites

Stages 0, 1 (so coverage runs are themselves Bazel targets and
default-green).

## Tasks

- [ ] **Add `pytest-cov`** as a `pyproject.toml` dev dep + pin in
  `uv.lock`.
- [ ] **`py_test` targets emit LCOV** via `--cov=src/hivemind
  --cov-report=lcov:coverage.lcov`. Use Bazel's
  `--instrumentation_filter` + `--collect_code_coverage` if the
  rules_py support is mature; otherwise emit LCOV from pytest
  directly and collect via `data` attribute.
- [ ] **`bun_test` targets emit LCOV** via `bun test --coverage
  --coverage-reporter=lcov`. Plumb through the `bun_test` macro.
- [ ] **`//tools/coverage:report` Bazel target** that aggregates LCOV
  from both layers and produces a single HTML report.
- [ ] **`make coverage` Makefile target** — replace the
  Stage-2-deliverable stub with the real implementation.
- [ ] **Per-package coverage thresholds** in `.coveragerc` so
  Stage 9 modules can have rising floors as their tests land.
- [ ] **Coverage gate** — fail PR if total drops below current
  baseline. Set initial baseline once Stage 9 lands.

## Files

**Modify:**
- `pyproject.toml` — `pytest-cov` dep + `[tool.coverage]` config
- `uv.lock` — regenerate
- `Makefile` — `make coverage` real implementation
- `tools/bazel/bun_test.bzl` — `--coverage` plumbing

**Create:**
- `.coveragerc`
- `tools/coverage/aggregate.py` — merge Python LCOV + bun LCOV
- `tools/coverage/BUILD.bazel`

## Experts

- **`expert-rules_python`** — Bazel-native coverage collection vs
  pytest-cov direct emission
- **`expert-bun`** — `bun test --coverage --coverage-reporter=lcov`
- **`expert-bazel`** — `--collect_code_coverage` mechanics

## Verification

```bash
make coverage
open bazel-bin/tools/coverage/report/index.html
```

---

# Stage 3 — Quality gates: strict mode + biome

**Goal:** every gate runs in strict mode. mypy strict on every
Python package (drop the relaxations). Engine TS lint via biome.
Pre-commit fully wired with buildifier + tsgo + biome hooks.

## Prerequisites

Stages 0, 1, 2 (gates exist, coverage measures impact of changes).

## Tasks

### Pre-commit polish

The existing `.pre-commit-config.yaml` already covers ruff,
ruff-format, mypy (local hook via `uv run`), and the
`pre-commit-hooks` essentials. Stage 0 added the
`third_party/{patches,dep_patches}/` exclusion. What's left:

- [ ] **Add `keith/pre-commit-buildifier`** to the existing config.
- [ ] **Add `tsgo --noEmit` as `stages: [pre-push]` local hook** —
  too slow for every commit, but caught before push.
- [ ] **Add `biome check` as `stages: [pre-push]` local hook** —
  same rationale (depends on biome adoption below).
- [ ] **Document pre-commit workflow** in `CONTRIBUTING.md` —
  install, autoupdate cadence, manual stages, the
  `git add -u` workflow to avoid stash-conflicts.

### Python — strict mypy across the board

- [ ] **Drop the mypy relaxations** in `pyproject.toml` for
  `src/hivemind/crawl/` and `src/hivemind/tui/`. They were added
  because of missing stubs; either install stubs (`types-requests`,
  etc.) or write inline type ignores at narrow points.
- [ ] **Add `types-*` packages** for any third-party deps still
  causing strict-mode failures.
- [ ] **Make tests themselves type-check.** Stage 0 left
  `tests/mypy` unwired because the existing tests have ~51 untyped
  function signatures (`def test_x():` instead of `def test_x() ->
  None:`). Annotate them and add the target:
  ```starlark
  load("//tools/bazel:mypy_test.bzl", "mypy_test")
  mypy_test(name = "mypy", srcs = _PY_SRCS)
  ```

### Engine — TypeScript strict

- [ ] **Audit `dev/opencode/.../tsconfig.json`** for `strict: true`
  + `noUncheckedIndexedAccess` + `exactOptionalPropertyTypes`. Add
  what's missing. (The `packages/opencode/tsconfig.json` currently
  sets `noUncheckedIndexedAccess: false` — flip it.) Captured as
  a new patch under `third_party/dep_patches/`.

### Engine — lint + format (biome)

- [ ] **Adopt `biome` for engine TS lint + format.** No linter
  configured today; prettier was referenced in the placeholder
  `format` script that Stage 0 deleted.
- [ ] **Create `dev/opencode/biome.json`** at the patched repo
  root scoped to `packages/opencode/src/**` and
  `packages/opencode/test/**`. Captured as a new entry in
  `third_party/dep_patches/` so the install repo also gets the
  config.
- [ ] **Bazel `biome_check_test` target** — runs `biome check`
  in CI mode (no fixes). Same shell-runner pattern as `bun_test`.
  Tagged `engine` + `lint`.
- [ ] **`biome format --write` Bazel runfile target** for local
  format runs. Wire into `//tools/bazel:format` so `make format`
  also formats engine TS.

## Files

**Modify:**
- `pyproject.toml` — drop mypy relaxations, add `types-*` deps
- `uv.lock` — regenerate
- `tests/BUILD.bazel` — add `mypy_test`
- `tests/test_*.py` — annotate function signatures with `-> None`
- `.pre-commit-config.yaml` — buildifier + tsgo + biome hooks

**Create:**
- `CONTRIBUTING.md` (or extend existing)
- `dev/opencode/biome.json` (via patches workflow)
- `tools/bazel/biome_test.bzl`
- `tools/bazel/biome_check_runner.sh`

## Experts

- **`team-lead-python-quality`** — routing
- **`expert-pre-commit`** — config shape, stash-conflict workflow,
  rev pinning
- **`expert-mypy`** — strict-mode escape valves, `types-*` package
  selection, Pydantic plugin coordination
- **`expert-pydantic`** — Pydantic mypy plugin setup
- **`expert-biome`** — `biome.json` schema, rule selection

## Verification

```bash
pre-commit run --all-files          # local
make lint                           # Bazel-driven (now with biome)
make typecheck                      # mypy on src/ AND tests/
```

---

# Stage 4 — CI infrastructure

**Goal:** every push to a branch and every PR runs the full Bazel
test suite, lint, type-check, and coverage. Status checks
configured on the default branch.

## Prerequisites

Stages 0, 1, 2, 3 — every gate must be green and coverage measured
before CI can enforce them.

## Tasks

- [ ] **Create `.github/workflows/test.yml`** at repo root:
  - `bazel-contrib/setup-bazel@0.9.0` with `bazelisk-cache`,
    `disk-cache`, `repository-cache` enabled
  - `bazelisk test //... '@opencode_src//...' --config=ci`
  - Upload `bazel-testlogs/**/*.xml` as a JUnit artifact
  - Upload `bazel-bin/tools/coverage/report/**` as the coverage
    artifact
  - Codecov upload step
- [ ] **Add `.bazelrc :ci` config:**
  ```
  test:ci --test_summary=detailed
  test:ci --keep_going
  test:ci --build_event_json_file=bep.json
  test:ci --verbose_failures
  test:ci --test_arg=-v --test_arg=--tb=short
  common:ci --show_timestamps
  build:ci --announce_rc
  ```
- [ ] **Multi-OS matrix** — Ubuntu (default) + macOS for engine
  tests (`darwin-sandbox` differences).
- [ ] **Branch protection rules** — require all checks to pass on
  `main`. Configure once via GitHub UI (out of repo).
- [ ] **Dependabot** for `pyproject.toml`, `uv.lock`, `package.json`,
  `MODULE.bazel`, GitHub Actions versions.
- [ ] **Concurrency cancel** for outdated CI runs on the same PR.
- [ ] **CI runs `pre-commit run --all-files`** as a separate job
  (not via Bazel — pre-commit needs network for hook fetching).

## Files

**Modify:**
- `.bazelrc` — add `:ci` config

**Create:**
- `.github/workflows/test.yml`
- `.github/workflows/coverage.yml` (or merge into test.yml)
- `.github/workflows/precommit.yml`
- `.github/dependabot.yml`

## Experts

- **`team-lead-bazel`** — routing
- **`expert-bazel`** — CI config, BEP, sandbox flags

## Verification

```bash
git push         # CI runs end-to-end
gh run watch     # observe
```

---

# Stage 5 — Bazel test conventions polish

**Goal:** the per-test boilerplate matches the canonical
`aspect_rules_py` pattern; hermeticity is env-driven, not
import-order-dependent.

## Prerequisites

Stage 0. (Independent of Track A — can run in parallel.)

## Tasks

- [ ] **Refactor `tests/BUILD.bazel` to use `py_pytest_main`:**
  ```starlark
  load("@aspect_rules_py//py:defs.bzl", "py_pytest_main", "py_test")
  py_pytest_main(name = "__test__", deps = ["@pypi//pytest"])
  py_test(
      name = "test_core",
      srcs = ["test_core.py", "conftest.py", ":__test__"],
      main = ":__test__.py",
      deps = ["//src/hivemind:lib", "@pypi//pytest"],
  )
  ```
  Stage 0 added the `unit` tag via a `_PYTEST_TAGS` constant —
  the refactor should preserve it.
- [ ] **Move `imports = [".."]` to `//src/hivemind:lib`** as
  `py_library(imports = ["."])` so it propagates via
  `PyInfo.imports` and tests don't need to redeclare.
- [ ] **Refactor `core_paths` fixture from monkeypatch → env-driven
  config.** Read paths from `os.environ.get("HIVEMIND_HOME",
  default)` at call time in `src/hivemind/config.py` (and any
  module-level constants that are paths). In `tests/conftest.py`:
  ```python
  @pytest.fixture(autouse=True)
  def core_paths(tmp_path, monkeypatch):
      monkeypatch.setenv("HIVEMIND_HOME", str(tmp_path / "hivemind"))
      monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
  ```
- [ ] **Audit any remaining `tests/` imports for hard-coded paths**
  and route them through env vars.
- [ ] **Tags audit** — every `py_test` and `bun_test` carries
  appropriate Bazel tags. Stage 0 locked the canonical set
  (`unit`, `engine`, `lint`, `typecheck`, `scenario`, `e2e`,
  `manual`, `requires-network`); Stage 1 may add `requires-node`
  / `no-sandbox`. Stage 5 verifies coverage.

## Files

**Modify:**
- `tests/BUILD.bazel` — `py_pytest_main` adoption, no per-file
  `imports`
- `src/hivemind/BUILD.bazel` — `py_library(imports = ["."])`
- `src/hivemind/config.py` — env-driven path resolution at call
  time
- `tests/conftest.py` — `monkeypatch.setenv()` based fixture

## Experts

- **`team-lead-bazel`** — routing
- **`expert-rules_python`** — `py_pytest_main` exit-code semantics,
  `imports` propagation via `PyInfo`
- **`expert-bazel`** — `TEST_TMPDIR`, sandbox env vars, tag conventions

## Verification

```bash
bazelisk test //...                           # everything still passes
bazelisk query 'kind(py_test, //tests:*)'     # target list unchanged
bazelisk test //tests:test_core --sandbox_debug   # confirm hermetic
```

---

# Stage 6 — Pydantic correctness + discriminator migration

**Goal:** every Pydantic model has negative-path test coverage; the
discriminated-union dispatch is the canonical native pattern.

## Prerequisites

Stage 5 (test infra polished). Stage 3 (mypy + Pydantic plugin
configured).

## Tasks

### Negative-path coverage

- [ ] **Create `tests/test_models.py`** with `pytest.raises(ValidationError)`
  tests for every model:
  - `extra="forbid"` rejection (every body class)
  - `kind` / `body` mismatch in `CatalogEntry` (every kind branch)
  - missing required fields per body
  - non-dict input to `CatalogEntry.body`
  - unknown `kind` falls through cleanly
  - `OperationResult` invariant at `models.py:248-256`
  - `RedeployResult.derive_success` validator at `models.py:390-402`
- [ ] **Assert on `error["type"]`** (stable contract from
  `pydantic-core`), not on human-readable `msg`.

### `validate_assignment` coverage

- [ ] **One sanity test per body class** that mutating a field
  after construction raises `ValidationError`.

### Round-trip coverage

- [ ] **`model_dump()` → `model_validate()` round-trips** for every
  body class + `HivemindConfig` with populated `agents`.
- [ ] **JSON round-trip** — `model_dump_json()` →
  `model_validate_json()` — to catch `Path`/`datetime`/`StrEnum`
  serialization asymmetries.

### Refactor: native discriminator

- [ ] **Migrate `models.py:170-191` from `mode="before"` to
  `Annotated[..., Field(discriminator="kind")]`.**
- [ ] **Verify on disk:** read every existing `hivemind.json` on
  the dev machine + any test fixtures and confirm the new
  validator parses them identically.
- [ ] **Delete the manual `_dispatch_body` validator.**

### Refactor: `model_dump_json` over generic `save_json`

- [ ] **Replace `save_json(model.model_dump())` call sites in
  `config.py` with `model.model_dump_json(indent=2)`.**
- [ ] **Keep `save_json` for non-Pydantic `dict[str, Any]` writes**
  (opencode's own JSON files).

## Files

**Modify:**
- `src/hivemind/models.py` — `Field(discriminator="kind")` migration
- `src/hivemind/config.py` — `model_dump_json` for typed writes

**Create:**
- `tests/test_models.py`

## Experts

- **`team-lead-python-quality`** — routing
- **`expert-pydantic`** — `Field(discriminator)` migration, error
  type contract, JSON serialization

## Verification

```bash
bazelisk test //tests:test_models
# Manually verify: load every existing hivemind.json on the system
python -c "import json, pathlib; from hivemind.models import HivemindConfig; \
  [HivemindConfig.model_validate(json.loads(p.read_text())) \
   for p in pathlib.Path.home().glob('.config/opencode/hivemind.json')]"
```

---

# Stage 7 — Engine test antipattern cleanup

**Goal:** existing engine tests stop using flaky-sleep antipatterns,
process-global mutations, and dead assertions. Reduces CI flakes
and per-file boilerplate.

(Stage 1 already addressed the sandbox-failing tests + engine_typecheck
TS errors. Stage 7 is the cosmetic/correctness cleanup that's
parallel-shippable.)

## Prerequisites

Stage 0. (Independent of Track A — can run in parallel.)

## Tasks

### `presence.test.ts` — drop `Bun.sleep` waits

- [ ] **Replace `Bun.sleep(N)` + poll patterns** at lines 125, 130,
  152, 156, 176, 180, 185, 205, 209, 230, 235, 258, 264, 269, 324,
  390, 394 with the existing `awaitContains` / `awaitExcludes`
  helpers (lines 70-114).
- [ ] **Hoist server start to `describe.beforeAll`** if
  `Instance.provide` semantics permit — collapses 10× server boots
  per file run.

### `hivemind-memory.test.ts` — drop `process.chdir`

- [ ] **Plugin reads `cwd` from a config arg or
  `Instance.provide({directory})`** instead of `process.cwd()`.
- [ ] **Update `process.chdir(cfg.path)` call sites** at lines 43,
  72, 113 to pass the directory through the plugin's input
  instead.
- [ ] **Replace `new Promise((r) => setTimeout(r, 200))`** at
  lines 58, 89, 128 with a `Bus.subscribe(session.created)` await.

### `file-write-hook.test.ts`

- [ ] **Fix `expect(true).toBe(true)`** at lines 132, 162. Use
  `expect.assertions(N)` to assert handler invocation count.
- [ ] **Move `process.env.OPENCODE_DISABLE_DEFAULT_PLUGINS` mutation
  into `beforeAll`** rather than module-load time (lines 6-7).

### Cross-cutting

- [ ] **Create `dev/opencode/packages/opencode/test/setup.ts`**
  containing `Log.init({print: false})` and any other shared
  setup. Wire via `bunfig.toml [test] preload = ["./test/setup.ts"]`
  (the `bun_test` Bazel macro doesn't pass per-target preload args,
  so use bunfig). Remove duplicates from `presence.test.ts:9`,
  `metadata.test.ts:8`, `hivemind-memory.test.ts:10`.

## Files

**Modify (via patches workflow):**
- `dev/opencode/packages/opencode/test/server/presence.test.ts`
- `dev/opencode/packages/opencode/test/plugin/hivemind-memory.test.ts`
- `dev/opencode/packages/opencode/test/plugin/file-write-hook.test.ts`
- `dev/opencode/packages/opencode/src/plugin/hivemind-memory.ts` —
  accept `cwd` arg
- `dev/opencode/bunfig.toml` — `[test] preload`

**Create (via patches workflow):**
- `dev/opencode/packages/opencode/test/setup.ts`

## Experts

- **`expert-bun`** — `bun:test` lifecycle hooks, `--preload` /
  bunfig semantics
- **`expert-hono`** — confirm middleware/upgrade behavior is
  unchanged after the test refactor

## Verification

```bash
make dev-save                                     # regenerate patches
make engine                                       # rebuild
bazelisk test '@opencode_src//...' --test_tag_filters=engine
```

---

# Stage 8 — Engine test gaps (Hono routes)

**Goal:** every Hono route has at minimum one happy-path test, one
validation-rejection test, and (for middleware) one auth path test.

## Prerequisites

Stage 0 + Stage 7 (clean test fixtures available).

## Tasks

- [ ] **Export `AppType` from `packages/opencode/src/server/server.ts`**
  so `testClient(Server.createApp({}) as AppType)` typechecks.
- [ ] **Add a `testClient()` smoke test** demonstrating typed-route
  access (`InferRequestType`, `InferResponseType`).
- [ ] **Validation-rejection test** for at least one
  `validator()`-gated route. Recommended target:
  `PUT /auth/:providerID` at `server.ts:129-140` — send a malformed
  body, assert 400 + error shape.
- [ ] **Auth middleware test** — `OPENCODE_SERVER_PASSWORD` set,
  request without credentials → 401. Test at `server.ts:51-62`.
- [ ] **SSE test for `/event`** at `routes/event.ts:34`:
  ```ts
  const res = await app.request("/event")
  const reader = res.body!.getReader()
  const { value } = await reader.read()
  // assert first event payload
  reader.cancel()  // exercise stream.onAbort(stop)
  ```
- [ ] **Audit all routes for missing happy-path tests.** Use
  `bazelisk query` (or grep) to enumerate routes; cross-reference
  with `test/server/`.

## Files

**Modify (via patches workflow):**
- `dev/opencode/packages/opencode/src/server/server.ts` — export
  `AppType`

**Create (via patches workflow):**
- `dev/opencode/packages/opencode/test/server/testclient.test.ts`
- `dev/opencode/packages/opencode/test/server/auth-middleware.test.ts`
- `dev/opencode/packages/opencode/test/server/event-sse.test.ts`
- (Per-route tests as the audit reveals gaps.)

## Experts

- **`expert-hono`** — `testClient`, `validator`, SSE testing
  patterns, middleware isolation
- **`expert-bun`** — bun:test integration with Hono's testing
  helpers

## Verification

```bash
bazelisk test '@opencode_src//...' --test_tag_filters=engine
```

---

# Stage 9 — Python coverage expansion

**Goal:** every production Python module has at least basic test
coverage. The TUI gets behavioral testing via Textual's `Pilot`.

## Prerequisites

Stage 5.

## Tasks

### Core lifecycle modules

- [ ] **`tests/test_lifecycle.py`** —
  - `enable_agent` / `disable_agent` / `delete_agent` happy paths
  - `_seed_system_templated` idempotence (re-seeding is a no-op)
  - `bootstrap_workspace` end-to-end against a tmpdir
  - `redeploy_all_agents` reconciliation
  - kind-migration (e.g., a name was previously `git_analyzed`,
    re-seeded as `system_templated`)

- [ ] **`tests/test_deployment.py`** —
  - `regenerate_librarian()` output shape (pulls every enabled
    agent's `librarian_entry()`)
  - `regenerate_hivemind_md()` template rendering against a
    representative catalog

- [ ] **`tests/test_cli.py`** — Typer's `CliRunner`:
  - `hivemind expert list`, `hivemind status`, `hivemind redeploy`
  - Error paths: invalid expert name, missing `hivemind.json`
  - Exit codes match Typer conventions

### Crawl pipeline

- [ ] **`tests/test_crawl_urls.py`** — `urls.normalize`,
  `urls.is_same_domain`, `urls.absolute`. Pure-function coverage.
- [ ] **`tests/test_crawl_probe.py`** — `probe.is_reachable`
  against an in-process HTTP server (no network).
- [ ] **`tests/test_crawl_extractor.py`** — trafilatura wrappers
  against fixture HTML (recorded once).

### TUI

- [ ] **`tests/test_tui_app.py`** — Textual's `App.run_test()` →
  `Pilot` API:
  - Tab switching (Experts / Teams)
  - Vim navigation (`j`, `k`, `gg`, `G`)
  - Enable / disable / delete keystroke flows
  - Post-mutation reload listener fires
- [ ] **`tests/test_vim_data_table.py`** — `VimDataTable`
  navigation in isolation.

### MCP

- [ ] **`tests/test_mcp_tools.py`** — every MCP tool's happy path:
  `list_agents`, `show_agent`, `enable_agent`, `disable_agent`,
  `create_git_expert`, `create_team`, `get_knowledge`,
  `search_knowledge`, etc. Mock the underlying ops; assert tool-
  result shape.
- [ ] **`tests/test_mcp_notify.py`** — `notify_tools_changed`
  emits `ToolListChangedNotification` to the MCP stdio.

## Files

**Create:**
- `tests/test_lifecycle.py`, `tests/test_deployment.py`,
  `tests/test_cli.py`
- `tests/test_crawl_urls.py`, `tests/test_crawl_probe.py`,
  `tests/test_crawl_extractor.py`
- `tests/test_tui_app.py`, `tests/test_vim_data_table.py`
- `tests/test_mcp_tools.py`, `tests/test_mcp_notify.py`
- `tests/data/` — fixture HTML for crawl tests
- `tests/BUILD.bazel` — wire the new targets

## Experts

- **`team-lead-python-quality`** — routing
- **`expert-typer`** — `CliRunner` patterns, exit codes
- **`expert-trafilatura`** — fixture HTML strategy
- **`expert-textual`** — `App.run_test()`, `Pilot` API
- **`expert-claude-agent-sdk-python`** — MCP tool testing patterns
- **`expert-pydantic`** — verifying tool-result shapes

## Verification

```bash
bazelisk test //tests:test_lifecycle //tests:test_deployment //tests:test_cli
bazelisk test //tests:test_crawl_urls //tests:test_crawl_probe //tests:test_crawl_extractor
bazelisk test //tests:test_tui_app //tests:test_vim_data_table
bazelisk test //tests:test_mcp_tools //tests:test_mcp_notify
make coverage    # confirm expanded module coverage
```

---

# Stage 10 — Scenario test scaffolding

**Goal:** every `▶ Test:` callout in `WORKFLOW_SCENARIO.md` has a
named test stub. Skipped tests show in CI as a coverage tracking
surface.

## Prerequisites

Stage 0. (Independent track — can start anytime after Stage 0.)

## Tasks

- [ ] **Create `tests/scenarios/README.md`** explaining the layout,
  pointing at `docs/WORKFLOW_SCENARIO.md` as the source of truth.
- [ ] **Create stub files** for the pytest layer (Phases 1, 9, 10):
  - `tests/scenarios/test_phase01_generate_team.py`
  - `tests/scenarios/test_phase09_orchestrator_memory.py`
  - `tests/scenarios/test_phase10_hivemind_sync.py`
- [ ] **Create `dev/opencode/.../test/scenarios/README.md`** with
  the same pointer.
- [ ] **Create stub files** for the engine layer (Phases 2-8, 11,
  12):
  - `phase02-presence.test.ts`
  - `phase03-fanout.test.ts`
  - `phase04-background-spawn.test.ts`
  - `phase05-resume.test.ts`
  - `phase06-daemon-expert.test.ts`
  - `phase07-source-fork.test.ts`
  - `phase08-bidirectional.test.ts`
  - `phase11-daemon-orchestrator.test.ts`
  - `phase12-long-arc.test.ts`
- [ ] **Each stub:**
  - Quotes the corresponding `▶ Test:` callout text verbatim as a
    docstring / comment
  - Body is `pytest.skip("not yet implemented", allow_module_level=False)`
    or `test.skip(...)` with a clear "TODO: Stage 11 sub-stage"
    marker
  - Tagged `tags = ["scenario", "skipped"]` in BUILD
- [ ] **Add a coverage-tracking task** that lists which scenario
  tests are still skipped — surfaced as a CI summary comment.

## Files

**Create:**
- `tests/scenarios/__init__.py`
- `tests/scenarios/test_phase01_generate_team.py`
- `tests/scenarios/test_phase09_orchestrator_memory.py`
- `tests/scenarios/test_phase10_hivemind_sync.py`
- `tests/scenarios/README.md`
- `tests/scenarios/BUILD.bazel`
- `dev/opencode/packages/opencode/test/scenarios/README.md`
- `dev/opencode/.../test/scenarios/phase02-presence.test.ts`
- ...one per remaining phase
- `tools/coverage/scenario_summary.py` — emits a markdown table of
  which scenario tests are still skipped

## Experts

None — mechanical. (Spawn `team-lead-hivemind` if the test layer
choice for any phase is ambiguous.)

## Verification

```bash
bazelisk test //tests/scenarios:all                      # all PASS via skip
bazelisk run //tools/coverage:scenario_summary
# → markdown table: 30 scenario callouts; 30 skipped; 0 implemented
```

---

# Stage 11 — Implement scenario tests (12 sub-stages)

**Goal:** convert each scenario test stub to a real test exercising
the load-bearing primitive. One sub-stage per WORKFLOW phase.

## Prerequisites

Stages 0, 5, 7, 10.

## Sub-stages

### 11.1 — Phase 1: `/hivemind_generate_team` end-to-end

- [ ] Test the full slash-command flow against a tmpdir worktree
  (`package.json`, `Cargo.toml`, `MODULE.bazel`).
- [ ] Assert: missing experts created, existing experts left
  untouched, team-lead deployed and enabled, every curator session
  auto-deletes.
- [ ] Test: two parallel curators do not race the catalog.
- [ ] Test: `/global/reload-agents` is non-destructive (MCP
  subprocess survives).
- **Experts:** `expert-claude-agent-sdk-python` (MCP testing),
  `team-lead-hivemind` (workflow correctness)

### 11.2 — Phase 2: presence + `list_sessions`

- [ ] Boot N TUIs in N tmpdir directories; presence count
  converges to N within 100 ms.
- [ ] Kill any single TUI; count drops by 1 within a beat.
- [ ] Regression: `_clients` keyed by `ServerWebSocket`, focus
  updates on `WSContext` wrapper don't look like new connections.
- **Experts:** `expert-bun`, `expert-hono`

### 11.3 — Phase 3: cross-session messaging fan-out

- [ ] `send_message` from A → B causes B's inbox to fire whether
  B is idle or mid-turn; multi-message arrival order preserved.
- [ ] Persistence across TUI reconnect.
- [ ] Truly-parallel fan-out: N receiving sessions enter busy
  state within tens of ms of each other.
- **Experts:** `expert-bun`, `expert-claude-agent-sdk-python`

### 11.4 — Phase 4: background spawn + `read_task_result`

- [ ] `Task(background=true)` registers in `SessionBackground` and
  returns immediately.
- [ ] Buffered result consumable via `read_task_result`.
- [ ] Multi-turn extension via `send_message` into the subagent ID.
- [ ] Closing the parent TUI doesn't dispose the subagent.
- **Experts:** `expert-bun`

### 11.5 — Phase 5: resume + memory injection

- [ ] `Task(task_id=...)` resumes verbatim; parentID unchanged;
  message history intact.
- [ ] `Task(task_id=..., ephemeral=true)` rejected at schema layer.
- [ ] Expert memory tree (`long_memory.md` + topic files) injected
  on every spawn (including resume) when `memory: true`.
- **Experts:** `expert-bun`, `expert-pydantic` (schema rejection)

### 11.6 — Phase 6: per-expert daemon spawn

- [ ] 9 KB write spawns one daemon under main with correct metadata.
- [ ] Concurrent over-threshold writes: implement de-dup if not
  already (this was a TODO in the doc).
- [ ] Daemon `ephemeral === true`; killing mid-pass auto-deletes.
- [ ] Repeat 5×: no daemon accumulation.
- **Experts:** `expert-bun`, `expert-hono`

### 11.7 — Phase 7: source-fork + ephemeral cleanup

- [ ] `Task(source_session_id=B, ephemeral=true)` from A creates
  depth-1 fork F under A with B's history copied.
- [ ] After F reaches idle, F is deleted; B is unmodified.
- [ ] F can read files / call MCP tools normally.
- [ ] Task return value (summary) appears in A's history after F
  is deleted.
- **Experts:** `expert-bun`

### 11.8 — Phase 8: bidirectional `send_message`

- [ ] Two idle sessions: each delivery wakes the recipient and
  queues into its inbox.
- [ ] Both independently advance turns; per-session message order
  preserved.
- [ ] Mid-turn delivery doesn't interrupt the in-flight turn.
- **Experts:** `expert-bun`

### 11.9 — Phase 9: orchestrator memory write

- [ ] Orchestrator's `_orchestrator/short_memory.md` grows on cue
  with appended pinned conventions.
- [ ] Orchestrator memory loads as part of subagent system prompt
  on every spawn under the orchestrator.
- **Experts:** `team-lead-hivemind`

### 11.10 — Phase 10: `/hivemind_sync` proposal-then-confirm

- [ ] Worktree where exactly one expert has drifted produces an
  accurate proposal.
- [ ] Proposal does not execute without confirmation.
- [ ] `switch_version` rotates HEAD symlink atomically; concurrent
  spawn never sees a half-rotated state.
- **Experts:** `expert-claude-agent-sdk-python`, `expert-bazel`
  (atomic-rename semantics on macOS)

### 11.11 — Phase 11: daemon at orchestrator depth

- [ ] When writer's `parent_id` is null (writer is orchestrator),
  daemon spawns under writer.id, not under a phantom parent.
  (Regression test from the doc.)
- [ ] Orchestrator's `_orchestrator` memory tree survives daemon
  compaction (file rewritten in place, never moved).
- [ ] Cross-project: after compaction in project A, switch to
  project B; orchestrator can recall A's pinned conventions.
- **Experts:** `expert-bun`

### 11.12 — Phase 12: long-arc session + memory survival

- [ ] Session idle >7 days, survived multiple engine restarts,
  resumes via `hivemind -- -s ses_xxx` with full history.
- [ ] `Task(task_id=...)` against an old session still works after
  engine restart; token-by-token continuity.
- [ ] Long-arc memory: spawn expert-X in week 1, do work, daemon
  compacts. Week 4: spawn expert-X again; system prompt includes
  topic files from week 1.
- **Experts:** `expert-bun`

## Files

For each sub-stage: convert the stub from Stage 10 into a real
test; remove the `skip` marker; tag `["scenario"]` (not
`["skipped"]`).

## Verification

```bash
bazelisk test //tests/scenarios:test_phase01_generate_team   # one at a time
bazelisk test //... --test_tag_filters=scenario              # all scenarios
bazelisk run //tools/coverage:scenario_summary               # 0 skipped
```

---

# Stage 12 — End-to-end harness

**Goal:** a single test that boots opencode against a tmpdir
"prism-like" worktree and runs the full WORKFLOW scenario in
sequence, asserting cumulative state at each beat.

## Prerequisites

Stage 11 (per-phase scenario tests must work in isolation first).

## Tasks

- [ ] **Build a tmpdir prism fixture** — `tests/e2e/fixtures/prism/`
  with minimal `package.json`, `Cargo.toml`, `MODULE.bazel`,
  `docker-compose.yml`.
- [ ] **Write `tests/e2e/scenario.py`** that:
  - Boots opencode against the tmpdir
  - Runs Phases 1 → 12 in sequence
  - Asserts cumulative state at each beat (subagent tree, memory
    files, session tree, presence count, etc.)
- [ ] **Tag `["e2e", "manual"]`** so `bazelisk test //...` excludes
  it by default.
- [ ] **Add `make e2e` target** that runs only the e2e harness.
- [ ] **CI: nightly job** that runs `bazelisk test //... --
  test_tag_filters=e2e`.
- [ ] **Wall-clock budget: under 5 minutes.** If it grows beyond,
  break into per-phase E2E tests.

## Files

**Create:**
- `tests/e2e/__init__.py`
- `tests/e2e/scenario.py`
- `tests/e2e/fixtures/prism/{package.json, Cargo.toml, MODULE.bazel, docker-compose.yml}`
- `tests/e2e/BUILD.bazel`
- `.github/workflows/nightly-e2e.yml`

**Modify:**
- `Makefile` — add `e2e` target

## Experts

- **`team-lead-hivemind`** — workflow-correctness routing
- **`expert-bun`** — engine boot lifecycle
- **`expert-rules_python`** — Bazel test fixtures via runfiles

## Verification

```bash
make e2e
bazelisk test //tests/e2e:scenario --test_tag_filters=e2e
```

---

# Stage 13 — Hardening (optional but recommended)

**Goal:** the test suite catches mutations, surfaces regressions
loudly, and shapes future-proof against subtle bugs.

## Prerequisites

Stages 0–12.

## Tasks

### Mutation testing (optional)

- [ ] **`mutmut` Bazel target** for the Python codebase. Acts as a
  "coverage of test quality" — does the test suite kill every
  surviving mutant?
- [ ] **Score baseline** — mark current mutation-survival rate;
  set threshold for future PRs.

### Property-based testing (where appropriate)

- [ ] **`hypothesis` for Pydantic models** — generate arbitrary
  inputs, assert round-trip + invariants.
- [ ] **`fast-check` for engine code** — same for TypeScript.

### Integration with patches workflow

- [ ] **Patch regeneration test** — `make dev-save && git diff
  --exit-code third_party/patches/` ensures patches stay
  byte-stable through the build.
- [ ] **Patch application order test** — confirm every patch in
  `third_party/patches/` applies cleanly in order.

### Performance regression

- [ ] **Engine boot benchmark** — `bun:test` benchmark for
  `Bun.serve` startup time; fail PR if regression > X%.
- [ ] **MCP tool latency benchmark** — same for the hivemind MCP
  layer.

## Files

**Create:**
- `tools/mutation/BUILD.bazel`
- `tests/property/test_models_property.py`
- `dev/opencode/.../test/property/`
- `tests/regression/test_patches.py`
- `dev/opencode/.../test/benchmark/`

## Experts

- Spawn the relevant testing-tool experts as the work begins.

## Verification

```bash
bazelisk run //tools/mutation:mutmut         # mutation suite
bazelisk test //... --test_tag_filters=property
bazelisk test //tests/regression:test_patches
```

---

# Cross-cutting: experts and teams to consult

**Teams:**
- **`team-lead-bazel`** — Stages 0, 1, 2, 4, 5, 12
- **`team-lead-python-quality`** — Stages 2, 3, 6, 9
- **`team-lead-hivemind`** — Stages 10, 11 (workflow correctness),
  12
- **`team-lead-architecture`** — Stage 6 (discriminator migration
  trade-offs), Stage 13 (mutation/property testing strategy)

**Standalone experts:**
- **`expert-bun`** — Stages 0, 1, 2, 7, 8, 11.2–11.8, 11.11, 11.12, 12
- **`expert-hono`** — Stages 1, 7, 8, 11.2, 11.6
- **`expert-pydantic`** — Stages 3, 6, 11.5, 13
- **`expert-mypy`** — Stage 3
- **`expert-ruff`** — Stage 3
- **`expert-pre-commit`** — Stage 3
- **`expert-biome`** — Stage 3
- **`expert-rules_python`** — Stages 0, 2, 5, 12
- **`expert-bazel`** — Stages 0, 1, 4, 5, 11.10
- **`expert-bazel-lib`** — Stage 0 (bun toolchain)
- **`expert-rules_js`** — Stage 0 (`js_test` patterns; ultimately
  not used)
- **`expert-typer`** — Stage 9 (`CliRunner`)
- **`expert-trafilatura`** — Stage 9 (crawl extractor fixtures)
- **`expert-textual`** — Stage 9 (TUI `Pilot` testing)
- **`expert-claude-agent-sdk-python`** — Stages 9, 11.1, 11.3,
  11.10

---

# Tracking conventions

- **One PR per stage** when possible. Sub-stages of Stage 11 each
  warrant their own PR.
- **Each PR's description references this doc** by stage number.
- **Coverage threshold rises monotonically.** Don't lower it
  except when a stage explicitly resets the baseline (Stage 2
  initial baseline, Stage 9 expansion).
- **Skip markers carry context.** Every `pytest.skip` /
  `test.skip` includes the stage that will land it.
- **The `tags` attribute matters.** `unit`, `scenario`, `e2e`,
  `manual`, `lint`, `typecheck`, `engine`, `requires-network`,
  `requires-node`, `no-sandbox`, `skipped`. CI filters on these.
- **Update this doc as stages land.** Check off tasks; if a stage
  splits or merges with another, fix the dependency graph.

---

# Out of scope

- **BuildBuddy / remote build executor.**
- **BCR mirroring config.**
- **Cross-machine session discovery / multi-host workflows.**
- **Multi-engine support (the provider abstraction was removed and
  must not be reintroduced).**
- **Project-scoped orchestrator** — orchestrator stays
  user-scoped, cross-project.
