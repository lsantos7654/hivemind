"""Bazel macros wrapping buildifier as `sh_test` and `sh_binary`.

`buildifier_check_test` runs `buildifier --mode=check --lint=warn` over
a list of Starlark sources; fails on style violations or warnings.

The fix-mode counterpart is exposed as `//tools/bazel:buildifier_fix`
(see BUILD.bazel) — invoked via `bazelisk run`.

Example:
    load("//tools/bazel:buildifier_test.bzl", "buildifier_check_test")

    buildifier_check_test(
        name = "buildifier_check",
        srcs = glob(["**/*.bzl", "**/BUILD.bazel"]),
    )
"""

load("@rules_shell//shell:sh_test.bzl", "sh_test")

_BUILDIFIER = "@buildifier_prebuilt//:buildifier"

def buildifier_check_test(name, srcs, tags = []):
    """Run `buildifier --mode=check --lint=warn` over `srcs`."""
    if not srcs:
        fail("buildifier_check_test '%s' has no srcs" % name)
    sh_test(
        name = name,
        srcs = ["//tools/bazel:buildifier_check_runner.sh"],
        data = [_BUILDIFIER] + srcs,
        args = [
            "$(rootpath %s)" % _BUILDIFIER,
        ] + ["$(rootpath %s)" % s for s in srcs],
        tags = ["lint"] + tags,
    )
