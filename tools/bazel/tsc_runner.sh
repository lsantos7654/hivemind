#!/usr/bin/env bash
# Run `bun run typecheck` (tsgo --noEmit) over a TS package.
#
# Args:
#   $1 — path to bun binary (workspace-relative)
#   $2 — path to the TS package's package.json (the typecheck root)
#
# tsgo runs at project granularity, not per-file, so this is one target
# per package. We cd into the package directory so tsgo picks up the
# package's tsconfig.json + node_modules + src/.
set -euo pipefail

bun_rel="$1"
marker_rel="$2"

runfiles_root="${TEST_SRCDIR:-$PWD}"

bun_path="$runfiles_root/$bun_rel"
[[ -x "$bun_path" ]] || bun_path="$runfiles_root/_main/$bun_rel"

marker_path="$runfiles_root/$marker_rel"
[[ -e "$marker_path" ]] || marker_path="$runfiles_root/_main/$marker_rel"

if [[ ! -x "$bun_path" ]]; then
    echo "ERROR: bun is not executable at $bun_path" >&2
    exit 1
fi
if [[ ! -e "$marker_path" ]]; then
    echo "ERROR: package marker missing at $marker_path" >&2
    exit 1
fi

# Resolve through symlinks (Bazel runfiles + cross-repo node_modules)
# so we're cd'd into the actual package source dir, not a runfiles
# alias that lacks node_modules.
package_root="$(dirname "$(realpath "$marker_path")")"

# Sandbox local state.
export HOME="${TEST_TMPDIR:-/tmp}"
export XDG_CONFIG_HOME="${TEST_TMPDIR:-/tmp}/xdg-config"
export XDG_DATA_HOME="${TEST_TMPDIR:-/tmp}/xdg-data"
export XDG_CACHE_HOME="${TEST_TMPDIR:-/tmp}/xdg-cache"

cd "$package_root"

# tsgo's shebang is `#!/usr/bin/env node`; the Bazel sandbox doesn't
# have node. `bun --bun` overrides the shebang and runs the .js file
# under bun's runtime instead.
exec "$bun_path" --bun "$package_root/node_modules/.bin/tsgo" --noEmit
