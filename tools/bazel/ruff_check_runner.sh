#!/usr/bin/env bash
# Run `ruff check` over the source files passed as positional args.
#
# Args:
#   $1     — path to ruff binary (workspace-relative)
#   $2     — path to pyproject.toml (or other ruff config, workspace-relative)
#   $3...  — paths to .py files to check (workspace-relative)
#
# All paths are resolved relative to the runfiles tree's main-workspace
# root ($TEST_SRCDIR/_main) so ruff's first-party detection picks up
# `src/hivemind/` and sorts `from hivemind...` imports correctly.
set -euo pipefail

ruff_bin_rel="$1"
config_rel="$2"
shift 2

workspace_root="${TEST_SRCDIR:-$PWD}/_main"
if [[ ! -d "$workspace_root" ]]; then
    workspace_root="$PWD"
fi

ruff_bin="$workspace_root/$ruff_bin_rel"
# External-repo paths are siblings of `_main/`, not under it.
[[ -x "$ruff_bin" ]] || ruff_bin="${TEST_SRCDIR:-$PWD}/$ruff_bin_rel"

if [[ ! -x "$ruff_bin" ]]; then
    echo "ERROR: ruff is not executable at $ruff_bin" >&2
    exit 1
fi

cd "$workspace_root"
exec "$ruff_bin" check --config "$config_rel" --no-cache "$@"
