"""Bazel macro wrapping `bun test` over a single `.test.ts` file.

The engine source lives in the fetched `@opencode_src` external repo
along with a populated `node_modules/` symlinked from
`@opencode_node_modules`. Wrapping `bun test` requires bun to run with
its cwd at the engine workspace root so its module resolver picks up
that node_modules tree.

To avoid copying the engine into Bazel's runfiles tree (huge, breaks
pnpm symlink topology), the runner script `realpath`s the package.json
marker passed via `data` to compute the engine workspace root, `cd`s
there, and execs bun with the test file's path *relative to the engine
root*. node_modules and src/ resolve through the original external-repo
filesystem layout.

Trade-off: tests are not fully sandboxed — they touch the external
repo's tree directly. Acceptable for Stage 0; revisit in Stage 4.

Example (typical usage from BUILD.bazel.opencode):
    load("@@//tools/bazel:bun_test.bzl", "bun_test")

    [
        bun_test(
            name = f.replace("/", "_").replace(".test.ts", "_test"),
            src = f,
        )
        for f in glob(["packages/opencode/test/**/*.test.ts"])
    ]
"""

load("@rules_shell//shell:sh_test.bzl", "sh_test")

_BUN = "@@//third_party:bun"
_DEFAULT_ENGINE_ROOT = "@opencode_src//:packages/opencode/package.json"

def bun_test(name, src, engine_root = None, timeout = "long", tags = [], env = None):
    """Run `bun test` against `src` inside the engine workspace.

    Args:
      name: target name (typically derived from the test file path)
      src: label of the .test.ts file (string or Label)
      engine_root: label of a marker file whose dirname is the engine
        workspace root. Defaults to packages/opencode/package.json in
        @opencode_src.
      timeout: Bazel test timeout (default "long" — bun tests can be slow)
      tags: extra tags to add (`engine` is always added)
      env: optional dict of custom env vars to pass through alongside
        Bazel-inherited vars (e.g. COVERAGE_DIR from `bazel coverage`).
    """
    if engine_root == None:
        engine_root = _DEFAULT_ENGINE_ROOT
    kwargs = dict(
        name = name,
        srcs = ["@@//tools/bazel:bun_test_runner.sh"],
        data = [
            _BUN,
            engine_root,
            src,
        ],
        args = [
            "$(rootpath %s)" % _BUN,
            "$(rootpath %s)" % engine_root,
            "$(rootpath %s)" % src,
        ],
        timeout = timeout,
        tags = ["engine"] + tags,
    )
    if env:
        kwargs["env"] = env
    sh_test(**kwargs)
