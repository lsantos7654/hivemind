#!/usr/bin/env python3
"""Dev workflow for opencode patches.

Subcommands:
  clone   Clone upstream sst/opencode at the pinned version into dev/opencode,
          create branch `hivemind`, then `git am` each patch so every patch
          becomes one commit. Dep patches (third_party/dep_patches/*.patch)
          are applied FIRST, then code patches (third_party/patches/*.patch).
          Fails if dev/opencode already exists.
  save    `git format-patch v<VERSION>..hivemind` inside dev/opencode, then
          route each output patch by what it touches:
            * touches package.json or bun.lock  -> third_party/dep_patches/
            * touches only source files         -> third_party/patches/
          Wholesale-replaces the destination dirs and rewrites both
          _OPENCODE_DEP_PATCHES + _OPENCODE_CODE_PATCHES in extensions.bzl.
          Fails if a single commit touches BOTH dep manifests AND source
          files (split the commit with `git rebase -i` before saving).

Edit-and-save loop:
    make dev                      # one-time clone (applies dep+code patches)
    cd dev/opencode && ...        # edit, commit, rebase as needed
    make dev-save                 # regenerate patch files + bazel lists
    make update                   # rebuild + refresh launcher

Two patch tiers:
    dep_patches  Modify package.json / bun.lock. Editing one invalidates
                 @opencode_node_modules and @opencode_src (~30s rebuild).
                 Rare.
    code_patches Modify only source files. Editing one invalidates only
                 @opencode_src (~3s rebuild). Common.

Ordering: dep patches must precede code patches in the commit history,
because clone replays them in `dep_patches/` then `patches/` order. If
you commit them out of order, save will still classify correctly, but
the next `make dev-reset && make dev` will replay in the canonical
order — which may fail to apply if a code patch context-depends on a
later dep change.

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
DEP_PATCHES_DIR = REPO_ROOT / "third_party" / "dep_patches"
CODE_PATCHES_DIR = REPO_ROOT / "third_party" / "patches"
EXTENSIONS_BZL = REPO_ROOT / "third_party" / "extensions.bzl"
MODULE_BAZEL = REPO_ROOT / "MODULE.bazel"
UPSTREAM_URL = "https://github.com/sst/opencode.git"
BRANCH = "hivemind"

# A patch is a "dep patch" if its diff touches any path matching one of these
# basenames OR any file under one of these path prefixes. Rest go to
# code_patches/.
#
# `packages/sdk/js/` is here because the bun bundler reads the SDK at
# runtime through a node_modules symlink that resolves into the
# `opencode_node_modules` external repo, NOT `opencode_src`. The two repos
# get different patch sets — only dep_patches reach node_modules. SDK
# changes that land only as code_patches are silently ignored at bundle
# time even though they show up correctly in the source tree.
_DEP_MANIFEST_BASENAMES = {"package.json", "bun.lock"}
_DEP_PATH_PREFIXES = ("packages/sdk/js/",)


def _opencode_version() -> str:
    """Extract `version` from the `ext.opencode(...)` call.

    Buildifier reformats kwargs alphabetically, so `version` may come
    after `sha256`. Match the call body as a non-greedy block, then
    pick out the `version` kwarg from anywhere inside.
    """
    text = MODULE_BAZEL.read_text()
    # The call spans multiple lines after buildifier formatting. Anchor
    # on the exact start (`ext.opencode(\n`) to avoid matching comments
    # like `# lockstep with ext.opencode(version=...)` that contain a
    # bare `ext.opencode(...)` token. Body ends at the first
    # `^)` line (Starlark formats closing parens at column 0).
    call = re.search(r"ext\.opencode\(\n(.*?)\n\)", text, re.DOTALL)
    if not call:
        sys.exit(f"error: could not find ext.opencode(...) in {MODULE_BAZEL}")
    m = re.search(r'version\s*=\s*"([^"]+)"', call.group(1))
    if not m:
        sys.exit(f"error: ext.opencode(...) lacks version= in {MODULE_BAZEL}")
    return m.group(1)


def _run(cmd: list[str], cwd: Path | None = None) -> None:
    where = f"  (in {cwd.relative_to(REPO_ROOT)})" if cwd else ""
    print(f"$ {' '.join(cmd)}{where}")
    subprocess.run(cmd, cwd=cwd, check=True)


def _patches_sorted(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob("*.patch"))


def _patch_touched_files(patch_path: Path) -> set[str]:
    """Files touched by the diffs in a `git format-patch` output."""
    files: set[str] = set()
    for line in patch_path.read_text(errors="replace").splitlines():
        m = re.match(r"^diff --git a/(\S+) b/(\S+)", line)
        if m:
            files.add(m.group(1))
            files.add(m.group(2))
    return files


def _is_dep_path(p: str) -> bool:
    return Path(p).name in _DEP_MANIFEST_BASENAMES or any(p.startswith(prefix) for prefix in _DEP_PATH_PREFIXES)


def _classify_patch(patch_path: Path) -> str:
    """Returns 'dep' or 'code'. Fails if the patch touches both."""
    files = _patch_touched_files(patch_path)
    dep_files = {f for f in files if _is_dep_path(f)}
    code_files = files - dep_files
    if dep_files and code_files:
        sys.exit(
            f"error: {patch_path.name} touches both dep-tier paths "
            f"({sorted(dep_files)}) and code-tier paths ({sorted(code_files)}).\n"
            f"  Split the commit so dep changes and code changes live in "
            f"separate commits (use `git rebase -i` in dev/opencode), then "
            f"re-run `make dev-save`."
        )
    return "dep" if dep_files else "code"


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
    # Order matters: dep patches first (so subsequent code patches see the
    # post-dep state), then code patches. Same order opencode_install
    # applies them at build time.
    for patch in _patches_sorted(DEP_PATCHES_DIR):
        _run(["git", "am", str(patch)], cwd=DEV_DIR)
    for patch in _patches_sorted(CODE_PATCHES_DIR):
        _run(["git", "am", str(patch)], cwd=DEV_DIR)
    print()
    print(f"✓ Dev tree ready at {DEV_DIR.relative_to(REPO_ROOT)} (branch: {BRANCH})")
    print("  Edit packages/opencode/src/... then commit; run `make dev-save` to write patches.")


def _rewrite_patches_list(name: str, filenames: list[str]) -> None:
    """Replace a `<name> = [...]` literal in extensions.bzl."""
    src = EXTENSIONS_BZL.read_text()
    pattern = re.compile(rf"^{re.escape(name)}\s*=\s*\[[^\]]*\]\s*$", re.MULTILINE)
    if not pattern.search(src):
        sys.exit(f"error: could not find {name} literal in {EXTENSIONS_BZL.relative_to(REPO_ROOT)}")
    if filenames:
        body = "\n".join(f'    "{fname}",' for fname in filenames)
        new_block = f"{name} = [\n{body}\n]"
    else:
        new_block = f"{name} = [\n]"
    new_src = pattern.sub(new_block, src, count=1)
    if new_src != src:
        EXTENSIONS_BZL.write_text(new_src)
        print(f"  updated {name} in {EXTENSIONS_BZL.relative_to(REPO_ROOT)}")


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

    # Classify each patch. _classify_patch() exits with a clear message if a
    # single commit mixes dep + code changes.
    dep_patches: list[Path] = []
    code_patches: list[Path] = []
    for patch in new_patches:
        kind = _classify_patch(patch)
        (dep_patches if kind == "dep" else code_patches).append(patch)

    # Wipe and replace BOTH destination dirs. Filenames come from commit
    # subjects; leftover stale patches would become orphans not referenced
    # by either _OPENCODE_*_PATCHES list.
    DEP_PATCHES_DIR.mkdir(parents=True, exist_ok=True)
    CODE_PATCHES_DIR.mkdir(parents=True, exist_ok=True)
    for old in _patches_sorted(DEP_PATCHES_DIR):
        old.unlink()
    for old in _patches_sorted(CODE_PATCHES_DIR):
        old.unlink()
    for src_path in dep_patches:
        dst = DEP_PATCHES_DIR / src_path.name
        shutil.copy2(src_path, dst)
        print(f"  wrote {dst.relative_to(REPO_ROOT)} (dep)")
    for src_path in code_patches:
        dst = CODE_PATCHES_DIR / src_path.name
        shutil.copy2(src_path, dst)
        print(f"  wrote {dst.relative_to(REPO_ROOT)} (code)")
    shutil.rmtree(staging)

    _rewrite_patches_list("_OPENCODE_DEP_PATCHES", [p.name for p in _patches_sorted(DEP_PATCHES_DIR)])
    _rewrite_patches_list("_OPENCODE_CODE_PATCHES", [p.name for p in _patches_sorted(CODE_PATCHES_DIR)])
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
