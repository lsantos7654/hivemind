#!/usr/bin/env bash
# Smoke test for the hermetic bun toolchain.
set -euo pipefail

bun_path="$1"
echo "Resolved bun: $bun_path"

if [[ ! -x "$bun_path" ]]; then
    echo "ERROR: bun is not executable at $bun_path" >&2
    exit 1
fi

version_output=$("$bun_path" --version)
echo "bun --version: $version_output"

# Exact version match — fails loudly when MODULE.bazel and SHASUMS drift.
expected="1.3.11"
if [[ "$version_output" != "$expected" ]]; then
    echo "ERROR: expected bun version $expected, got $version_output" >&2
    exit 1
fi

echo "OK"
