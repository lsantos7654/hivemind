"""opencode_node_modules_install + opencode_install repository rules.

Two-repo split for caching. Bazel wipes a repository_rule's output dir on
every re-execution (RepositoryFunction.setupRepoRoot → deleteTree), so
in-rule marker files don't survive. To skip `bun install` on patch-only
edits we instead keep the install state in a separate repo whose inputs
don't include the (frequently-edited) source patches.

Two patch tiers:

  dep_patches   — modify package.json / bun.lock. Applied in BOTH repos
                  (install repo applies them before `bun install`, build
                  repo applies them as part of its patch series). Editing
                  one invalidates BOTH repos and pays the full ~30s
                  install + build cost. Rare.

  code_patches  — modify only source files (no dep manifests). Applied
                  ONLY in the build repo. Editing one invalidates only
                  the build repo, which symlinks node_modules from the
                  install repo and runs `bun build`. ~3s. Common.

Resulting cache behaviour:

  @opencode_node_modules  download + dep_patches + bun install
                          cache key: version + sha256 + bun version +
                          dep_patches contents.
                          Re-runs only when those change.

  @opencode_src           download + dep_patches + code_patches +
                          ctx.symlink node_modules from
                          @opencode_node_modules + bun build.
                          cache key: version + sha256 + ALL patches.
                          Re-runs on any patch edit (~3s when only code
                          patches changed) but always reuses the
                          install repo's node_modules.

Doing the bun build in @opencode_src — instead of in a downstream
genrule over a TreeArtifact bundle — preserves bun's pnpm-style symlink
layout in node_modules/.bun/, which the bundler walks to resolve
transitive peer-dep paths like @babel/preset-typescript from inside
@opentui/solid. The ctx.symlink that links our node_modules into the
install repo's tree preserves all the relative .bun/ symlinks because
the entire tree is reached through one extra outer symlink — bun
resolves through it normally.

Diff guard (in opencode_install): even with the dep_patches tier, the
build rule diffs package.json files between the two repos. If a
code_patch accidentally modifies a dep manifest, the install repo's
node_modules will be stale; the diff guard fails fast with a clear
"move this to dep_patches/" message instead of letting `bun build`
fail later with confusing module-not-found errors.
"""

_OPENCODE_URL = "https://github.com/sst/opencode/archive/refs/tags/v{version}.tar.gz"

_BUN_LABELS = {
    ("mac", "arm64"): Label("@bun_macos_arm64//:bun"),
    ("mac", "x86_64"): Label("@bun_macos_x86_64//:bun"),
    ("linux", "arm64"): Label("@bun_linux_arm64//:bun"),
    ("linux", "x86_64"): Label("@bun_linux_x86_64//:bun"),
}

# Manifests that must match between @opencode_node_modules and the
# post-patch @opencode_src tree. If they diverge, the install repo's
# node_modules is stale for what the build rule will compile.
#
# Notably absent: bun.lock. Bun 1.3.11 refreshes lockfile metadata on the
# first install (the released lockfile is not bit-identical to what bun
# produces), so @opencode_node_modules's post-install bun.lock will always
# differ from the freshly-extracted tarball's bun.lock. We rely on the
# package.json checks to catch real dep changes — a patch can't add a
# dep without first adding it to a package.json.
_DEP_MANIFESTS = [
    "package.json",
    "packages/opencode/package.json",
]

def _normalize_arch(arch):
    if arch in ("amd64", "x86_64", "x64"):
        return "x86_64"
    if arch in ("arm64", "aarch64"):
        return "arm64"
    return arch

def _host_bun_label(os_name, arch):
    name = os_name.lower()
    family = "mac" if "mac" in name or "darwin" in name else "linux"
    arch = _normalize_arch(arch)
    label = _BUN_LABELS.get((family, arch))
    if label == None:
        fail("opencode_install: unsupported host platform: {} {}".format(os_name, arch))
    return label

def _run(ctx, args, env, step, working_directory = ""):
    result = ctx.execute(
        args,
        environment = env,
        timeout = 1800,
        quiet = False,
        working_directory = working_directory,
    )
    if result.return_code != 0:
        fail("opencode_install: {} failed (exit {}):\nstdout:\n{}\nstderr:\n{}".format(
            step,
            result.return_code,
            result.stdout,
            result.stderr,
        ))

def _apply_patches(ctx, patches):
    """Apply each patch in declaration order via the SYSTEM `patch` tool.

    Bazel's built-in `ctx.patch()` uses a stricter Starlark parser that
    chokes on full-context hunks and certain whitespace patterns; the
    system `patch -p1` accepts the same diffs `git apply` would.

    Each patch path is registered with ctx.watch so edits invalidate the
    rule. Bazel 8's `--incompatible_no_implicit_watch_label` default is
    true, so `ctx.path(label)` does NOT add the file's content to
    recordedInputs; the explicit watch is load-bearing.
    """
    for patch in patches:
        patch_path = ctx.path(patch)
        ctx.watch(patch_path)
        result = ctx.execute(
            ["patch", "-p1", "--input", str(patch_path)],
            timeout = 60,
            quiet = False,
        )
        if result.return_code != 0:
            fail("opencode_install: failed to apply {}\nstdout:\n{}\nstderr:\n{}".format(
                patch_path,
                result.stdout,
                result.stderr,
            ))

def _bun_env(repo_root, version):
    return {
        # Isolate state so we don't pollute ~/.bun or read host config.
        "HOME": repo_root,
        "BUN_INSTALL_CACHE_DIR": repo_root + "/.bun-cache",
        # opencode's build script reads OPENCODE_VERSION/OPENCODE_CHANNEL,
        # falling back to `git branch --show-current` in the source tree —
        # which fails in a fetched tarball (no .git). Pin both so the
        # fallback doesn't fire.
        "OPENCODE_VERSION": version,
        "OPENCODE_CHANNEL": "stable",
    }

def _download_opencode(ctx):
    ctx.download_and_extract(
        url = _OPENCODE_URL.format(version = ctx.attr.version),
        sha256 = ctx.attr.sha256,
        stripPrefix = "opencode-{}".format(ctx.attr.version),
    )

# ----------------------------------------------------------------------
# @opencode_node_modules: download + bun install. No patches.
# ----------------------------------------------------------------------

# BUILD file dropped into @opencode_node_modules. Exposes BUILD.bazel as a
# label so the @opencode_src rule can ctx.path() it, walk to its parent
# (the install repo's root), and locate node_modules + dep manifests.
_NODE_MODULES_BUILD = """\
package(default_visibility = ["//visibility:public"])

# BUILD.bazel is exported as a label so opencode_install can resolve a
# stable filesystem path into this repo. The actual node_modules tree
# lives next to it as a sibling directory.
exports_files(["BUILD.bazel"])
"""

def _opencode_node_modules_install_impl(ctx):
    repo_root = str(ctx.path("."))

    # 1. Fetch + extract upstream tarball.
    _download_opencode(ctx)

    # 2. Apply dep_patches BEFORE install so bun install sees the
    #    post-patch package.json / bun.lock. Empty list is fine.
    _apply_patches(ctx, ctx.attr.dep_patches)

    # 3. Resolve a host-matching bun binary.
    bun_label = _host_bun_label(ctx.os.name, ctx.os.arch)
    bun_path = str(ctx.path(bun_label))

    # 4. Run bun install. NOT --frozen-lockfile — the released bun.lock
    #    needs minor metadata refresh on first install with bun 1.3.11,
    #    which --frozen-lockfile rejects.
    _run(ctx, [bun_path, "install", "--ignore-scripts"], _bun_env(repo_root, ctx.attr.version), "bun install")

    # 5. Drop in the BUILD file that exposes BUILD.bazel as a label.
    ctx.file("BUILD.bazel", _NODE_MODULES_BUILD)

opencode_node_modules_install = repository_rule(
    implementation = _opencode_node_modules_install_impl,
    attrs = {
        "version": attr.string(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "dep_patches": attr.label_list(allow_files = True),
    },
)

# ----------------------------------------------------------------------
# @opencode_src: download + patch + symlink node_modules + bun build.
# ----------------------------------------------------------------------

def _opencode_install_impl(ctx):
    repo_root = str(ctx.path("."))

    # 1. Fetch + extract the upstream opencode tarball.
    _download_opencode(ctx)

    # 2. Apply ALL patches (caller passes dep_patches + code_patches in that
    #    order — dep_patches must precede code_patches because code patches
    #    may add hunks that depend on dep-patch-introduced lines).
    _apply_patches(ctx, ctx.attr.patches)

    # 3. Resolve a host-matching bun binary; Skyframe waits for the bun_*
    #    repo to be fetched before this rule's body continues.
    bun_label = _host_bun_label(ctx.os.name, ctx.os.arch)
    bun_path = str(ctx.path(bun_label))
    bun_env = _bun_env(repo_root, ctx.attr.version)

    # 4. Locate the @opencode_node_modules repo via ctx.path on its
    #    BUILD.bazel anchor. Skyframe restarts this rule until the install
    #    repo is fetched (NeedsSkyframeRestartException at
    #    RepositoryFunction.getRootedPathFromLabel:248).
    nm_anchor = ctx.path(ctx.attr.node_modules_anchor)
    nm_repo_root = nm_anchor.dirname

    # 5. Hard guard: patches must NOT touch package.json / bun.lock /
    #    packages/opencode/package.json, because the install repo ran
    #    `bun install` against the unpatched versions. If a patch added a
    #    dep, the install repo's node_modules would be missing it and
    #    `bun build` would fail with a confusing module-not-found error.
    #    Fail fast here with a clear message instead.
    for fname in _DEP_MANIFESTS:
        ours = ctx.read(ctx.path(fname), watch = "no")
        theirs_path = nm_repo_root.get_child(*fname.split("/"))
        if not theirs_path.exists:
            fail((
                "opencode_install: @opencode_node_modules is missing {} — " +
                "the install repo failed to populate or the path layout " +
                "drifted upstream."
            ).format(fname))
        theirs = ctx.read(theirs_path, watch = "no")
        if ours != theirs:
            fail((
                "opencode_install: a patch modified {} relative to what " +
                "@opencode_node_modules saw at install time. Dep manifest " +
                "edits must live in third_party/dep_patches/ (applied in " +
                "BOTH repos before bun install) — not in third_party/" +
                "patches/ (applied only in the build repo, AFTER install). " +
                "Move the offending patch from patches/ to dep_patches/ " +
                "and add its filename to _OPENCODE_DEP_PATCHES in " +
                "third_party/extensions.bzl. Editing a dep_patch costs " +
                "the full ~30s install + build, but a code_patch edit " +
                "stays at ~3s."
            ).format(fname))

    # 6. Symlink ALL node_modules trees from the install repo. Bun
    #    workspaces produce a node_modules at the workspace root AND a
    #    node_modules in each `packages/*` workspace package. Both must
    #    be present for `bun build` to resolve direct + workspace deps.
    #    The pnpm-style relative symlinks inside node_modules/.bun/ resolve
    #    correctly through these outer symlinks because they're walked by
    #    bun relative to their containing dir (which after following the
    #    outer symlink is the install repo's dir, where the original
    #    relative paths still work).
    ctx.symlink(nm_repo_root.get_child("node_modules"), "node_modules")
    packages_dir = ctx.path("packages")
    if packages_dir.exists:
        for pkg_entry in packages_dir.readdir():
            install_nm = nm_repo_root.get_child("packages", pkg_entry.basename, "node_modules")
            if install_nm.exists:
                ctx.symlink(install_nm, "packages/" + pkg_entry.basename + "/node_modules")

    # 7. Compile the CLI in place. opencode's own build script handles
    #    SQL migration loading, the Solid plugin, web-UI embedding, etc.
    #    --single                : current platform only
    #    --skip-embed-web-ui     : skip the packages/app web-UI bundle
    #    --skip-install          : we already installed in @opencode_node_modules
    _run(
        ctx,
        [bun_path, "run", "script/build.ts", "--single", "--skip-embed-web-ui", "--skip-install"],
        bun_env,
        "bun run script/build.ts",
        working_directory = "packages/opencode",
    )

    # 8. Find the produced binary (platform suffix is computed at runtime
    #    by build.ts) and symlink it to a stable name at the repo root so
    #    BUILD.bazel.opencode can reference it as a single file.
    dist = ctx.path("packages/opencode/dist")
    found = None
    for entry in dist.readdir():
        candidate = entry.get_child("bin").get_child("opencode")
        if candidate.exists:
            found = candidate
            break
    if not found:
        fail("opencode_install: produced no binary under packages/opencode/dist/*/bin/opencode")
    ctx.symlink(found, "hivemind-engine")

    # 9. Drop in the BUILD.bazel that exports the produced binary.
    ctx.symlink(ctx.attr.build_file, "BUILD.bazel")

opencode_install = repository_rule(
    implementation = _opencode_install_impl,
    attrs = {
        "version": attr.string(mandatory = True),
        "sha256": attr.string(mandatory = True),
        "patches": attr.label_list(allow_files = True),
        "build_file": attr.label(allow_single_file = True, mandatory = True),
        "node_modules_anchor": attr.label(allow_single_file = True, mandatory = True),
    },
)
