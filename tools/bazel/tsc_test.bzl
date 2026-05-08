"""Bazel macro wrapping `tsgo --noEmit` (TypeScript type-check) for the engine.

Unlike `bun_test`, tsgo runs against the entire TypeScript project at
once — per-file checking is meaningless because a single file's
referenced types might span many other files. So this is a single
target per package.

Tagged `engine` and `typecheck` so both
`--test_tag_filters=engine` and `--test_tag_filters=typecheck` pick it up.

Example (from BUILD.bazel.opencode):
    load("@@//tools/bazel:tsc_test.bzl", "tsc_test")
    tsc_test(
        name = "engine_typecheck",
        package_dir = "packages/opencode",
    )
"""

load("@rules_shell//shell:sh_test.bzl", "sh_test")

_BUN = "@@//third_party:bun"

def tsc_test(name, package_marker, timeout = "long", tags = []):
    """Run `bun run typecheck` (tsgo --noEmit) over a TS package.

    Args:
      name: target name
      package_marker: label of the package's package.json. The runner
        cd's to this file's dirname before invoking `bun run typecheck`,
        so the dir's tsconfig.json + node_modules + src/ all apply.
      timeout: Bazel test timeout (default "long")
      tags: extra tags (`engine` and `typecheck` are always added)
    """
    sh_test(
        name = name,
        srcs = ["@@//tools/bazel:tsc_runner.sh"],
        data = [
            _BUN,
            package_marker,
        ],
        args = [
            "$(rootpath %s)" % _BUN,
            "$(rootpath %s)" % package_marker,
        ],
        timeout = timeout,
        tags = ["engine", "typecheck"] + tags,
    )
