#!/usr/bin/env bash
# Run `mypy` over the source files passed as positional args.
#
# Args:
#   $1     — path to mypy binary (workspace-relative)
#   $2     — path to pyproject.toml (or other mypy config, workspace-relative)
#   $3...  — paths to .py files to check (workspace-relative)
#
# MYPYPATH and --explicit-package-bases are required so imports inside
# `src/hivemind/` resolve when invoked against runfiles-tree paths. The
# runfiles tree mirrors the workspace at $TEST_SRCDIR/_main/.
set -euo pipefail

mypy_bin_rel="$1"
config_rel="$2"
shift 2

workspace_root="${TEST_SRCDIR:-$PWD}/_main"
if [[ ! -d "$workspace_root" ]]; then
    workspace_root="$PWD"
fi

mypy_bin="$workspace_root/$mypy_bin_rel"
# External-repo binaries (e.g., from py_entrypoint_binary) live as
# siblings of `_main/`, not under it.
[[ -x "$mypy_bin" ]] || mypy_bin="${TEST_SRCDIR:-$PWD}/$mypy_bin_rel"

if [[ ! -x "$mypy_bin" ]]; then
    echo "ERROR: mypy is not executable at $mypy_bin" >&2
    exit 1
fi

export MYPYPATH="$workspace_root/src"

cd "$workspace_root"
exec "$mypy_bin" \
    --config-file "$config_rel" \
    --explicit-package-bases \
    --cache-dir "${TEST_TMPDIR:-/tmp}/mypy_cache" \
    "$@"
