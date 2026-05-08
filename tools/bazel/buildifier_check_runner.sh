#!/usr/bin/env bash
# Run `buildifier --mode=check --lint=warn` over Starlark sources.
#
# Args:
#   $1     — path to buildifier binary (workspace-relative)
#   $2...  — paths to .bzl/BUILD.bazel/MODULE.bazel files (workspace-relative)
set -euo pipefail

buildifier_rel="$1"
shift

workspace_root="${TEST_SRCDIR:-$PWD}/_main"
if [[ ! -d "$workspace_root" ]]; then
    workspace_root="$PWD"
fi

buildifier="$workspace_root/$buildifier_rel"
[[ -x "$buildifier" ]] || buildifier="${TEST_SRCDIR:-$PWD}/$buildifier_rel"

if [[ ! -x "$buildifier" ]]; then
    echo "ERROR: buildifier is not executable at $buildifier" >&2
    exit 1
fi

cd "$workspace_root"
# `canonical-repository` is suppressed: bun_test.bzl / tsc_test.bzl are
# loaded from inside @opencode_src (BUILD.bazel.opencode is symlinked
# in by the repository rule), so `@@//` is the correct way to reference
# the root module. There's no apparent-name alternative reachable from
# an external repo.
exec "$buildifier" --mode=check --lint=warn \
    --warnings=-canonical-repository "$@"
