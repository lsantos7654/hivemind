#!/usr/bin/env bash
# Run `bun test` against a single .test.ts file in the engine workspace.
#
# Args:
#   $1 — path to bun binary (workspace-relative)
#   $2 — path to the engine workspace marker (package.json)
#   $3 — path to the .test.ts file
#
# Resolution: $TEST_SRCDIR is the runfiles tree root. The engine source
# lives under $TEST_SRCDIR/<external-repo>/, where node_modules is a
# symlink that ultimately resolves into @opencode_node_modules. We
# `realpath` the marker to get an absolute path that survives the
# symlink chain, then `cd` to its dirname so bun's resolver picks up
# the in-tree node_modules.
set -euo pipefail

bun_rel="$1"
marker_rel="$2"
test_rel="$3"

runfiles_root="${TEST_SRCDIR:-$PWD}"

# bun and engine source files are external-repo data, so they live
# directly under the runfiles root (NOT under _main/).
bun_path="$runfiles_root/$bun_rel"
[[ -x "$bun_path" ]] || bun_path="$runfiles_root/_main/$bun_rel"

marker_path="$runfiles_root/$marker_rel"
[[ -e "$marker_path" ]] || marker_path="$runfiles_root/_main/$marker_rel"

test_path="$runfiles_root/$test_rel"
[[ -e "$test_path" ]] || test_path="$runfiles_root/_main/$test_rel"

if [[ ! -x "$bun_path" ]]; then
    echo "ERROR: bun is not executable at $bun_path" >&2
    exit 1
fi
if [[ ! -e "$marker_path" ]]; then
    echo "ERROR: engine workspace marker missing at $marker_path" >&2
    exit 1
fi
if [[ ! -e "$test_path" ]]; then
    echo "ERROR: test file missing at $test_path" >&2
    exit 1
fi

# realpath through any symlinks (Bazel runfile symlinks AND the
# node_modules cross-repo symlink) so the resolved engine_root is the
# absolute path inside @opencode_src that contains node_modules.
engine_root="$(dirname "$(realpath "$marker_path")")"
test_abs="$(realpath "$test_path")"
relative="${test_abs#$engine_root/}"

if [[ "$relative" == "$test_abs" ]]; then
    echo "ERROR: $test_abs is not under engine_root $engine_root" >&2
    exit 1
fi

# Sandbox the engine's local state so parallel tests don't collide on
# .opencode/, .cache/, etc.
export HOME="${TEST_TMPDIR:-/tmp}"
export XDG_CONFIG_HOME="${TEST_TMPDIR:-/tmp}/xdg-config"
export XDG_DATA_HOME="${TEST_TMPDIR:-/tmp}/xdg-data"
export XDG_CACHE_HOME="${TEST_TMPDIR:-/tmp}/xdg-cache"

cd "$engine_root"
exec "$bun_path" test --timeout 30000 "$relative"
