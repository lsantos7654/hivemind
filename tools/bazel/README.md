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

Filter from the command line:

```bash
bazelisk test //... --test_tag_filters=lint
bazelisk test //... --test_tag_filters=typecheck
bazelisk test '@opencode_src//...' --test_tag_filters=engine
```

Or via Make (preferred):

```bash
make lint            # ruff + buildifier
make typecheck       # mypy + tsgo
make unit            # Python pytest
make engine-test     # all bun:test targets in @opencode_src
make format          # ruff format + buildifier fix + ruff check --fix
make test            # everything
```

## Skipped upstream tests

Three upstream tests are excluded from `BUILD.bazel.opencode` because
they cannot run under Bazel's `darwin-sandbox`:

| File | Reason |
|---|---|
| `effect/cross-spawn-spawner.test.ts` | Spawns `node -e ...` — sandbox has only `bun` in PATH |
| `lsp/index.test.ts` | Runs `npm install` — sandbox has no network |
| `memory/abort-leak.test.ts` | Fetches `https://example.com` + sandbox memory profile skew |

If the sandbox gains `node` or network access, remove entries from
`_SKIP` in `third_party/opencode/BUILD.bazel.opencode`. No tags,
no silent failures — the targets don't exist.

## Adding a new tool wrapper

1. Add a `py_console_script_binary` / `py_entrypoint_binary` /
   `py_venv_binary` in `BUILD.bazel`.
2. Write a runner shell script next to the others — accept the binary
   path as `$1`, then config + sources as remaining args. cd into
   `$TEST_SRCDIR/_main` so the workspace topology applies.
3. Export the runner via `exports_files([...])` in `BUILD.bazel`.
4. Add the macro in a new `*_test.bzl` file.
5. Document the macro + tag here.
