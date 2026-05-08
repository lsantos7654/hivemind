#!/usr/bin/env bash
# Run `ruff format --check` over the source files passed as positional args.
#
# Args:
#   $1     — path to ruff binary (workspace-relative)
#   $2     — path to pyproject.toml (or other ruff config, workspace-relative)
#   $3...  — paths to .py files to check (workspace-relative)
#
# Resolves paths relative to the runfiles tree's main-workspace root.
set -euo pipefail

ruff_bin_rel="$1"
config_rel="$2"
shift 2

workspace_root="${TEST_SRCDIR:-$PWD}/_main"
if [[ ! -d "$workspace_root" ]]; then
    workspace_root="$PWD"
fi

ruff_bin="$workspace_root/$ruff_bin_rel"
[[ -x "$ruff_bin" ]] || ruff_bin="${TEST_SRCDIR:-$PWD}/$ruff_bin_rel"

if [[ ! -x "$ruff_bin" ]]; then
    echo "ERROR: ruff is not executable at $ruff_bin" >&2
    exit 1
fi

cd "$workspace_root"
exec "$ruff_bin" format --check --config "$config_rel" --no-cache "$@"
