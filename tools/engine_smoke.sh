#!/usr/bin/env bash
# Smoke test for the bun-compiled hivemind-engine binary.
set -euo pipefail

engine="$1"
echo "Resolved engine: $engine"

if [[ ! -x "$engine" ]]; then
    echo "ERROR: engine is not executable at $engine" >&2
    exit 1
fi

version_output=$("$engine" --version)
echo "engine --version: $version_output"

# Pinned upstream opencode version; bump in lockstep with MODULE.bazel
# `ext.opencode(version=...)`.
expected="1.4.3"
if [[ "$version_output" != "$expected" ]]; then
    echo "ERROR: expected engine version $expected, got $version_output" >&2
    exit 1
fi

echo "OK"
