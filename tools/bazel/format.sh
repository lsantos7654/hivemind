#!/usr/bin/env bash
# Run every formatter (ruff format, buildifier --mode=fix) over the
# workspace's source files in place. Invoked via
# `bazelisk run //tools/bazel:format`.
#
# Args:
#   $1 — path to ruff binary (workspace-relative)
#   $2 — path to buildifier binary (workspace-relative)
set -euo pipefail

ruff_rel="$1"
buildifier_rel="$2"

if [[ -z "${BUILD_WORKSPACE_DIRECTORY:-}" ]]; then
    echo "ERROR: BUILD_WORKSPACE_DIRECTORY not set." \
         "Run via 'bazelisk run //tools/bazel:format'." >&2
    exit 1
fi

ruff="$PWD/$ruff_rel"
[[ -x "$ruff" ]] || ruff="$PWD/_main/$ruff_rel"

buildifier="$PWD/$buildifier_rel"
[[ -x "$buildifier" ]] || buildifier="$PWD/_main/$buildifier_rel"

if [[ ! -x "$ruff" ]]; then
    echo "ERROR: ruff is not executable at $ruff" >&2
    exit 1
fi
if [[ ! -x "$buildifier" ]]; then
    echo "ERROR: buildifier is not executable at $buildifier" >&2
    exit 1
fi

cd "$BUILD_WORKSPACE_DIRECTORY"

# ruff_bin is a py_venv_binary whose launcher needs Bazel's runfiles
# helper (`runfiles.bash`). When called from within another sh_binary
# (us), the inherited RUNFILES_* vars point at OUR tree, which doesn't
# carry the helper. Resolve via the absolute path that points into
# ruff_bin's own runfiles directory — the launcher cd's there itself.
ruff_runfiles_root="$(realpath "$ruff").runfiles"
if [[ -d "$ruff_runfiles_root" ]]; then
    export RUNFILES_DIR="$ruff_runfiles_root"
    unset RUNFILES_MANIFEST_FILE
fi

echo "==> ruff format ."
"$ruff" format --no-cache .

# Buildifier is a single Go binary, no runfiles needed.
unset RUNFILES_DIR

echo "==> buildifier --mode=fix"
find . \
    -path './dev/opencode' -prune -o \
    -path './bazel-*' -prune -o \
    -path './.venv' -prune -o \
    \( -name '*.bzl' -o -name 'BUILD.bazel' -o -name 'MODULE.bazel' \) \
    -type f -print0 \
    | xargs -0 "$buildifier" --mode=fix --lint=fix

if [[ -d "$ruff_runfiles_root" ]]; then
    export RUNFILES_DIR="$ruff_runfiles_root"
fi

echo "==> ruff check --fix ."
"$ruff" check --fix --no-cache .

echo "OK"
