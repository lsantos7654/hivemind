#!/usr/bin/env bash
# Run `buildifier --mode=fix` over every Starlark file in the workspace.
#
# Args:
#   $1 — path to buildifier binary (workspace-relative)
#
# Invoked via `bazelisk run //tools/bazel:buildifier_fix`.
# Uses BUILD_WORKSPACE_DIRECTORY (set by `bazel run`) to find files in
# the live source tree, not the runfiles snapshot.
set -euo pipefail

buildifier_rel="$1"
shift

if [[ -z "${BUILD_WORKSPACE_DIRECTORY:-}" ]]; then
    echo "ERROR: BUILD_WORKSPACE_DIRECTORY not set." \
         "Run via 'bazelisk run //tools/bazel:buildifier_fix', not 'bazelisk test'." >&2
    exit 1
fi

# Resolve buildifier path. When run via `bazelisk run`, the cwd is the
# runfiles tree root.
buildifier="$PWD/$buildifier_rel"
[[ -x "$buildifier" ]] || buildifier="$PWD/_main/$buildifier_rel"

if [[ ! -x "$buildifier" ]]; then
    echo "ERROR: buildifier is not executable at $buildifier" >&2
    exit 1
fi

cd "$BUILD_WORKSPACE_DIRECTORY"

# Find every Starlark source. Exclude dev/opencode (transient + upstream)
# and any vendored bazel-* output dirs.
find . \
    -path './dev/opencode' -prune -o \
    -path './bazel-*' -prune -o \
    -path './.venv' -prune -o \
    \( -name '*.bzl' -o -name 'BUILD.bazel' -o -name 'MODULE.bazel' \) \
    -type f -print0 \
    | xargs -0 "$buildifier" --mode=fix --lint=fix
