"""opencode_install repository rule.

Fetches a pinned tagged release of sst/opencode, applies our patches, runs
`bun install`, then runs `bun run script/build.ts --single` to produce
the compiled binary IN-PLACE inside the @opencode_src// repo. Doing the
compile in the repo rule (instead of a downstream genrule over a
TreeArtifact bundle) preserves bun's pnpm-style symlink layout in
`node_modules/.bun/`, which the bundler needs to resolve transitive
peer-dep paths like `@babel/preset-typescript` from inside
`@opentui/solid`.

Network access is allowed at fetch time, which `bun install` requires.
The `bun build --compile` step does not need network once node_modules
is populated, but running it here keeps the symlink layout intact.

Why a custom rule and not `http_archive(... patches=[...])`:
  http_archive can extract + patch but cannot run `bun install` or
  `bun build`. Both must happen at fetch time to keep network and
  symlink semantics correct.
"""

_OPENCODE_URL = "https://github.com/sst/opencode/archive/refs/tags/v{version}.tar.gz"

# Per-platform bun file labels (the raw `bun` executable inside each
# bun_<plat> repo, exported via `exports_files(["bun"])`).
_BUN_LABELS = {
    ("mac",   "arm64"):  Label("@bun_macos_arm64//:bun"),
    ("mac",   "x86_64"): Label("@bun_macos_x86_64//:bun"),
    ("linux", "arm64"):  Label("@bun_linux_arm64//:bun"),
    ("linux", "x86_64"): Label("@bun_linux_x86_64//:bun"),
}

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
            step, result.return_code, result.stdout, result.stderr,
        ))

def _opencode_install_impl(ctx):
    repo_root = str(ctx.path("."))

    # 1. Fetch + extract the upstream opencode tarball.
    ctx.download_and_extract(
        url = _OPENCODE_URL.format(version = ctx.attr.version),
        sha256 = ctx.attr.sha256,
        stripPrefix = "opencode-{}".format(ctx.attr.version),
    )

    # 2. Apply patches in declaration order via the SYSTEM `patch` tool.
    #    Bazel's built-in `ctx.patch()` uses a stricter Starlark parser that
    #    chokes on full-context hunks and certain whitespace patterns; the
    #    system `patch -p1` accepts the same diffs `git apply` would.
    for patch in ctx.attr.patches:
        patch_path = ctx.path(patch)
        result = ctx.execute(
            ["patch", "-p1", "--input", str(patch_path)],
            timeout = 60,
            quiet = False,
        )
        if result.return_code != 0:
            fail("opencode_install: failed to apply {}\nstdout:\n{}\nstderr:\n{}".format(
                patch_path, result.stdout, result.stderr,
            ))

    # 3. Resolve a host-matching bun binary; Skyframe waits for the bun_*
    #    repo to be fetched before this rule's body continues.
    bun_label = _host_bun_label(ctx.os.name, ctx.os.arch)
    bun_path = str(ctx.path(bun_label))

    bun_env = {
        # Isolate state so we don't pollute ~/.bun or read host config.
        "HOME": repo_root,
        "BUN_INSTALL_CACHE_DIR": repo_root + "/.bun-cache",
        # opencode's build script reads OPENCODE_VERSION/OPENCODE_CHANNEL,
        # falling back to `git branch --show-current` in the source tree —
        # which fails in a fetched tarball (no .git). Pin both so the
        # fallback doesn't fire.
        "OPENCODE_VERSION": ctx.attr.version,
        "OPENCODE_CHANNEL": "stable",
    }

    # 4. Populate node_modules. NOT --frozen-lockfile — the released
    #    bun.lock needs minor metadata refresh on first install with bun
    #    1.3.11, which --frozen-lockfile rejects.
    _run(ctx, [bun_path, "install"], bun_env, "bun install")

    # 5. Compile the CLI in place. opencode's own build script handles
    #    SQL migration loading, the Solid plugin, web-UI embedding, etc.
    #    --single                : current platform only
    #    --skip-embed-web-ui     : skip the packages/app web-UI bundle
    #    --skip-install          : we already installed above
    _run(
        ctx,
        [bun_path, "run", "script/build.ts", "--single", "--skip-embed-web-ui", "--skip-install"],
        bun_env,
        "bun run script/build.ts",
        working_directory = "packages/opencode",
    )

    # 6. Find the produced binary (platform suffix is computed at runtime
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

    # 7. Drop in the BUILD.bazel that exports the produced binary.
    ctx.symlink(ctx.attr.build_file, "BUILD.bazel")

opencode_install = repository_rule(
    implementation = _opencode_install_impl,
    attrs = {
        "version":    attr.string(mandatory = True),
        "sha256":     attr.string(mandatory = True),
        "patches":    attr.label_list(allow_files = True),
        "build_file": attr.label(allow_single_file = True, mandatory = True),
    },
)
