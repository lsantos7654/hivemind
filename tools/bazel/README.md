# `tools/bazel/` — Quality-gate macros

Bazel-native wrappers for the project's lint, format, and type-check
tools so every gate runs through `bazelisk test //...`.

## Macros

| Macro | Tool | Tags emitted |
|---|---|---|
| `ruff_check_test` | `ruff check` | `lint` |
| `ruff_format_test` | `ruff format --check` | `lint` |
| `mypy_test` | `mypy` | `typecheck` |
| `bun_test` | `bun test` over a single `.test.ts` | `engine` |
| `tsc_test` | `tsgo --noEmit` over a TS package | `engine`, `typecheck` |
| `buildifier_check_test` | `buildifier --mode=check` | `lint` |

Each macro produces a single `sh_test`. The underlying binary is a
`py_console_script_binary`/`py_entrypoint_binary`/`py_venv_binary` (Python
tools), `@buildifier_prebuilt//:buildifier` (Go binary from BCR), or
`//third_party:bun` (the engine's pinned bun toolchain).

## Usage

```starlark
load("//tools/bazel:ruff_test.bzl", "ruff_check_test", "ruff_format_test")
load("//tools/bazel:mypy_test.bzl", "mypy_test")

ruff_check_test(name = "ruff_check", srcs = glob(["**/*.py"]))
ruff_format_test(name = "ruff_format", srcs = glob(["**/*.py"]))
mypy_test(name = "mypy", srcs = glob(["**/*.py"]))
```

## Tag conventions

| Tag | Meaning |
|---|---|
| `unit` | Python pytest (default for `py_test`) |
| `engine` | bun test on `@opencode_src` |
| `lint` | ruff, buildifier |
| `typecheck` | mypy, tsgo |
| `scenario` | reserved for Stage 9+ |
| `e2e` | reserved for Stage 11+ |
| `manual` | excluded from `bazelisk test //...` |
| `requires-network` | reserved for Stage 4 |

Filter from the command line:

```bash
bazelisk test //... --test_tag_filters=lint
bazelisk test //... --test_tag_filters=typecheck
bazelisk test '@opencode_src//...' --test_tag_filters=engine
```

Or via Make (preferred):

```bash
make lint            # ruff + buildifier
make typecheck       # mypy + (tsgo, when un-deferred)
make unit            # Python pytest
make engine-test     # all bun:test targets in @opencode_src
make format          # ruff format + buildifier fix + ruff check --fix
make test            # everything
```

## Known engine test failures (Stage 6 cleanup pending)

The following ~5 engine tests fail under Bazel's `darwin-sandbox` due
to pre-existing environment dependencies. They are NOT Stage 0
regressions — they are surfaced by Stage 0's wiring:

- `config_config_test`, `provider_provider_test` — depend on real
  network or system config
- `effect_cross-spawn-spawner_test` — needs `node` in PATH (sandbox
  doesn't include it)
- `lsp_index_test` — calls `npm install` to fetch
  `typescript-language-server` (network required)
- `memory_abort-leak_test`, `permission_next_test` — sandbox-sensitive
  process spawn

Stage 6 of `docs/TESTING_ROADMAP.md` ("engine test cleanup") fixes
these. Until then, these targets are visible failures — `make test`
exits non-zero. To run only the green subset:

```bash
make engine-test --keep_going    # see all results, exits non-zero
bazelisk test '@opencode_src//...' --test_tag_filters=engine \
  -- -@opencode_src//:config_config_test \
     -@opencode_src//:provider_provider_test \
     -@opencode_src//:lsp_index_test \
     -@opencode_src//:effect_cross-spawn-spawner_test \
     -@opencode_src//:memory_abort-leak_test \
     -@opencode_src//:permission_next_test
```

## Pending sub-stages

| Sub-stage | Status |
|---|---|
| 0.1 — Python lint/typecheck wrapper macros | done |
| 0.2 — buildifier integration | done |
| 0.3 — `bun_test` macro for engine `*.test.ts` | done (96% pass) |
| 0.4 — `tsc_test`, format binary, Makefile rewrite | done |
| 0.5 — strip placeholder engine package.json scripts | done (patch 0022) |

`tests/mypy` is intentionally absent — Stage 2 of the roadmap fixes
the test suite's untyped functions before adding strict mypy there.
`engine_typecheck` is tagged `manual` because the patched engine has
pre-existing TS errors that Stage 6 addresses.

## Adding a new tool wrapper

1. Add a `py_console_script_binary` / `py_entrypoint_binary` /
   `py_venv_binary` in `BUILD.bazel`.
2. Write a runner shell script next to the others — accept the binary
   path as `$1`, then config + sources as remaining args. cd into
   `$TEST_SRCDIR/_main` so the workspace topology applies.
3. Export the runner via `exports_files([...])` in `BUILD.bazel`.
4. Add the macro in a new `*_test.bzl` file.
5. Document the macro + tag here.
