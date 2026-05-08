"""Bazel macros wrapping `ruff check` and `ruff format --check` as `sh_test`.

Each macro materializes the source files into runfiles, invokes the
ruff binary (a `py_console_script_binary` defined at
`//tools/bazel:ruff_bin`), and propagates the exit code.

Example:
    load("//tools/bazel:ruff_test.bzl", "ruff_check_test", "ruff_format_test")

    ruff_check_test(
        name = "ruff_check",
        srcs = glob(["**/*.py"]),
    )
    ruff_format_test(
        name = "ruff_format",
        srcs = glob(["**/*.py"]),
    )
"""

load("@rules_shell//shell:sh_test.bzl", "sh_test")

_RUFF_BIN = "//tools/bazel:ruff_bin"
_DEFAULT_CONFIG = "//:pyproject.toml"

def _ruff_test(name, runner, srcs, config, tags):
    if not srcs:
        fail("ruff test '%s' has no srcs" % name)
    sh_test(
        name = name,
        srcs = [runner],
        data = [_RUFF_BIN, config] + srcs,
        args = [
            "$(rootpath %s)" % _RUFF_BIN,
            "$(rootpath %s)" % config,
        ] + ["$(rootpath %s)" % s for s in srcs],
        tags = ["lint"] + tags,
    )

def ruff_check_test(name, srcs, config = _DEFAULT_CONFIG, tags = []):
    """Run `ruff check` over `srcs`. Fails on lint violations."""
    _ruff_test(
        name = name,
        runner = "//tools/bazel:ruff_check_runner.sh",
        srcs = srcs,
        config = config,
        tags = tags,
    )

def ruff_format_test(name, srcs, config = _DEFAULT_CONFIG, tags = []):
    """Run `ruff format --check` over `srcs`. Fails on unformatted code."""
    _ruff_test(
        name = name,
        runner = "//tools/bazel:ruff_format_runner.sh",
        srcs = srcs,
        config = config,
        tags = tags,
    )
