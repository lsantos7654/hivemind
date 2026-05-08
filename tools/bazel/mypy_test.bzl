"""Bazel macro wrapping `mypy` as an `sh_test`.

mypy needs `MYPYPATH=src` and `--explicit-package-bases` so imports
inside `src/hivemind/` resolve when invoked against runfiles paths.
The runner sets these from the runfiles tree topology
(`$TEST_SRCDIR/_main/src`).

Example:
    load("//tools/bazel:mypy_test.bzl", "mypy_test")

    mypy_test(
        name = "mypy",
        srcs = glob(["**/*.py"]),
    )
"""

load("@rules_shell//shell:sh_test.bzl", "sh_test")

_MYPY_BIN = "//tools/bazel:mypy_bin"
_DEFAULT_CONFIG = "//:pyproject.toml"

def mypy_test(name, srcs, config = _DEFAULT_CONFIG, tags = []):
    """Run `mypy` over `srcs`. Fails on type errors per the project config."""
    if not srcs:
        fail("mypy_test '%s' has no srcs" % name)
    sh_test(
        name = name,
        srcs = ["//tools/bazel:mypy_runner.sh"],
        data = [_MYPY_BIN, config] + srcs,
        args = [
            "$(rootpath %s)" % _MYPY_BIN,
            "$(rootpath %s)" % config,
        ] + ["$(rootpath %s)" % s for s in srcs],
        tags = ["typecheck"] + tags,
    )
