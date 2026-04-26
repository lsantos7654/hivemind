#!/usr/bin/env python3
"""Dev workflow for opencode patches.

Subcommands:
  clone   Clone upstream sst/opencode at the pinned version into dev/opencode,
          create branch `hivemind`, then `git am` each third_party/patches/*.patch
          so every patch becomes one commit. Fails if dev/opencode already exists.
  save    `git format-patch v<VERSION>..hivemind` inside dev/opencode, replace
          third_party/patches/*.patch with the result, then rewrite
          _OPENCODE_PATCHES in third_party/extensions.bzl from disk.

Edit-and-save loop:
    make dev                      # one-time clone
    cd dev/opencode && ...        # edit, commit, rebase as needed
    make dev-save                 # regenerate patch files + bazel list
    make update                   # rebuild + refresh launcher

Reads the opencode version from MODULE.bazel so dev/ tracks the bazel pin.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEV_DIR = REPO_ROOT / "dev" / "opencode"
PATCHES_DIR = REPO_ROOT / "third_party" / "patches"
EXTENSIONS_BZL = REPO_ROOT / "third_party" / "extensions.bzl"
MODULE_BAZEL = REPO_ROOT / "MODULE.bazel"
UPSTREAM_URL = "https://github.com/sst/opencode.git"
BRANCH = "hivemind"


def _opencode_version() -> str:
    text = MODULE_BAZEL.read_text()
    m = re.search(r'ext\.opencode\(\s*version\s*=\s*"([^"]+)"', text)
    if not m:
        sys.exit(f"error: could not find ext.opencode(version=...) in {MODULE_BAZEL}")
    return m.group(1)


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    where = f"  (in {cwd.relative_to(REPO_ROOT)})" if cwd else ""
    print(f"$ {' '.join(cmd)}{where}")
    subprocess.run(cmd, cwd=cwd, check=True)


def _patches_sorted(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.patch"))


def cmd_clone() -> None:
    if DEV_DIR.exists():
        sys.exit(f"error: {DEV_DIR.relative_to(REPO_ROOT)} already exists. Use `make dev-reset` to recreate.")
    version = _opencode_version()
    DEV_DIR.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "git",
            "clone",
            "--depth",
            "1",
            "--branch",
            f"v{version}",
            UPSTREAM_URL,
            str(DEV_DIR),
        ]
    )
    _run(["git", "checkout", "-b", BRANCH], cwd=DEV_DIR)
    for patch in _patches_sorted(PATCHES_DIR):
        _run(["git", "am", str(patch)], cwd=DEV_DIR)
    print()
    print(f"✓ Dev tree ready at {DEV_DIR.relative_to(REPO_ROOT)} (branch: {BRANCH})")
    print("  Edit packages/opencode/src/... then commit; run `make dev-save` to write patches.")


def _rewrite_patches_list(filenames: list[str]) -> None:
    """Replace the `_OPENCODE_PATCHES = [...]` literal in extensions.bzl."""
    src = EXTENSIONS_BZL.read_text()
    pattern = re.compile(r"^_OPENCODE_PATCHES\s*=\s*\[[^\]]*\]\s*$", re.MULTILINE)
    if not pattern.search(src):
        sys.exit(f"error: could not find _OPENCODE_PATCHES literal in {EXTENSIONS_BZL.relative_to(REPO_ROOT)}")
    body = "\n".join(f'    "{name}",' for name in filenames)
    new_block = f"_OPENCODE_PATCHES = [\n{body}\n]"
    new_src = pattern.sub(new_block, src, count=1)
    if new_src != src:
        EXTENSIONS_BZL.write_text(new_src)
        print(f"  updated _OPENCODE_PATCHES in {EXTENSIONS_BZL.relative_to(REPO_ROOT)}")


def cmd_save() -> None:
    if not DEV_DIR.exists():
        sys.exit(f"error: {DEV_DIR.relative_to(REPO_ROOT)} not found. Run `make dev` first.")
    version = _opencode_version()
    staging = DEV_DIR / ".save-patches"
    if staging.exists():
        shutil.rmtree(staging)
    _run(
        [
            "git",
            "format-patch",
            f"v{version}..{BRANCH}",
            "--output-directory",
            str(staging),
        ],
        cwd=DEV_DIR,
    )

    new_patches = _patches_sorted(staging)
    if not new_patches:
        sys.exit("error: format-patch produced no files (no commits past the tag?)")

    existing = _patches_sorted(PATCHES_DIR)
    if len(new_patches) != len(existing):
        print(f"warning: patch count changed ({len(existing)} -> {len(new_patches)})", file=sys.stderr)

    # Replace the patches dir contents wholesale. Filenames come from commit
    # subjects, so leftover stale files would become orphans not referenced
    # by _OPENCODE_PATCHES.
    for old in existing:
        old.unlink()
    for new in new_patches:
        dst = PATCHES_DIR / new.name
        shutil.copy2(new, dst)
        print(f"  wrote {dst.relative_to(REPO_ROOT)}")
    shutil.rmtree(staging)

    _rewrite_patches_list([p.name for p in _patches_sorted(PATCHES_DIR)])
    print()
    print("✓ Patches saved. Run `make update` to rebuild with the new patches.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("clone", help="Clone opencode and apply patches as commits.")
    sub.add_parser("save", help="Regenerate patch files from commits.")
    args = parser.parse_args()
    if args.cmd == "clone":
        cmd_clone()
    elif args.cmd == "save":
        cmd_save()


if __name__ == "__main__":
    main()
