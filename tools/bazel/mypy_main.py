"""Entry-point shim for mypy invoked via Bazel's py_venv_binary.

Bazel needs mypy's venv to also contain hivemind's runtime deps so
that imports like `import typer`, `import rich`, `import textual` etc.
resolve during type analysis. We achieve this by declaring those deps
on the `mypy_bin` py_venv_binary (see tools/bazel/BUILD.bazel) and
calling mypy's CLI entry from a thin Python shim.
"""

from __future__ import annotations

from mypy.__main__ import console_entry

if __name__ == "__main__":
    console_entry()
