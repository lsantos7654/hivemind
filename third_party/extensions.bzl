"""Module extension `external_engines`: fetches bun + opencode source.

Provides:
  @bun_macos_arm64//:bin, @bun_macos_x86_64//:bin,
  @bun_linux_arm64//:bin,  @bun_linux_x86_64//:bin
  @opencode_src//:hivemind_engine
"""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load(":opencode_install.bzl", "opencode_install", "opencode_node_modules_install")

# Bun 1.3.11 release sha256 sums (from SHASUMS256.txt at oven-sh/bun release).
_BUN_VARIANTS = {
    "macos_arm64": struct(
        url_template = "https://github.com/oven-sh/bun/releases/download/bun-v{v}/bun-darwin-aarch64.zip",
        sha256 = "6f5a3467ed9caec4795bf78cd476507d9f870c7d57b86c945fcb338126772ffc",
        strip_prefix = "bun-darwin-aarch64",
    ),
    "macos_x86_64": struct(
        url_template = "https://github.com/oven-sh/bun/releases/download/bun-v{v}/bun-darwin-x64.zip",
        sha256 = "c4fe2b9247218b0295f24e895aaec8fee62e74452679a9026b67eacbd611a286",
        strip_prefix = "bun-darwin-x64",
    ),
    "linux_arm64": struct(
        url_template = "https://github.com/oven-sh/bun/releases/download/bun-v{v}/bun-linux-aarch64.zip",
        sha256 = "d13944da12a53ecc74bf6a720bd1d04c4555c038dfe422365356a7be47691fdf",
        strip_prefix = "bun-linux-aarch64",
    ),
    "linux_x86_64": struct(
        url_template = "https://github.com/oven-sh/bun/releases/download/bun-v{v}/bun-linux-x64.zip",
        sha256 = "8611ba935af886f05a6f38740a15160326c15e5d5d07adef966130b4493607ed",
        strip_prefix = "bun-linux-x64",
    ),
}

_BUN_BUILD_FILE = """\
package(default_visibility = ["//visibility:public"])

# Filegroup target for use as a `data` dep / select() branch. Avoid naming
# this "bun" — Bazel would see a self-edge against the embedded `bun` file.
filegroup(
    name = "bin",
    srcs = ["bun"],
)

# Export the raw file so repository rules can resolve it via
# ctx.path(Label("@bun_macos_arm64//:bun_file")) without going through
# the filegroup (which ctx.path doesn't understand cleanly).
exports_files(["bun"])
"""

def _ext_impl(ctx):
    bun_version = None
    opencode_tag = None
    for mod in ctx.modules:
        for tag in mod.tags.bun:
            bun_version = tag.version
        for tag in mod.tags.opencode:
            opencode_tag = tag

    if not bun_version:
        fail("external_engines: at least one ext.bun(version=...) tag is required")

    for plat, variant in _BUN_VARIANTS.items():
        http_archive(
            name = "bun_" + plat,
            urls = [variant.url_template.format(v = bun_version)],
            sha256 = variant.sha256,
            strip_prefix = variant.strip_prefix,
            build_file_content = _BUN_BUILD_FILE,
        )

    if opencode_tag:
        dep_patches = ["@//third_party/dep_patches:" + p for p in _OPENCODE_DEP_PATCHES]
        code_patches = ["@//third_party/patches:" + p for p in _OPENCODE_CODE_PATCHES]

        # Install repo: download + dep_patches + bun install. Cached by
        # version + sha256 + bun version + dep_patches contents. Survives
        # code_patch edits so the build repo can ctx.symlink its
        # node_modules instead of running `bun install` itself.
        opencode_node_modules_install(
            name = "opencode_node_modules",
            version = opencode_tag.version,
            sha256 = opencode_tag.sha256,
            dep_patches = dep_patches,
        )

        # Build repo: download + dep_patches + code_patches + symlink
        # node_modules + bun build. Patches concatenated in that order so
        # the post-patch state matches what the install repo saw.
        opencode_install(
            name = "opencode_src",
            version = opencode_tag.version,
            sha256 = opencode_tag.sha256,
            patches = dep_patches + code_patches,
            build_file = "@//third_party/opencode:BUILD.bazel.opencode",
            node_modules_anchor = "@opencode_node_modules//:BUILD.bazel",
        )

    return ctx.extension_metadata(reproducible = True)

# Patches that modify dep manifests (package.json / bun.lock). Applied in
# BOTH @opencode_node_modules and @opencode_src, before bun install. Editing
# one invalidates the install repo (~30s rebuild). Resolved relative to
# //third_party/dep_patches/. Empty by default — most patches should be
# code patches.
_OPENCODE_DEP_PATCHES = [
    "0001-SDK-gen-backgroundTasks-endpoint-SessionBackgroundCh.patch",
    "0002-SDK-gen-liveSessions-endpoint-LiveSessionsChanged-ev.patch",
    "0003-SDK-gen-ephemeral-on-Session-create-fork-inputs.patch",
    "0004-Strip-placeholder-package.json-scripts.patch",
    "0005-fix-add-types-field-to-plugin-package.json-for-tsgo-.patch",
]

# Patches that modify only source files (no dep manifest changes). Applied
# only in @opencode_src, after dep_patches, after install. Editing one
# invalidates only the build repo (~3s rebuild). Resolved relative to
# //third_party/patches/.
_OPENCODE_CODE_PATCHES = [
    "0006-TUI-wordmark-and-exit-message.patch",
    "0007-Inline-connection-indicator-into-home-sidebar-footers.patch",
    "0008-Non-destructive-agent-reload-endpoint.patch",
    "0009-Hardened-opencode-config-defaults.patch",
    "0010-Bake-bash.sudo-deny-into-Permission.fromConfig.patch",
    "0011-cross-session-primitives-per-session-inbox-and-fork.patch",
    "0012-Task-tool-accepts-source_session_id.patch",
    "0013-TUI-session_footer-slot-dual-slot-home-footer-plugin.patch",
    "0014-Switch-HTTP-listener-to-native-Bun.serve.patch",
    "0015-Per-client-WebSocket-presence-and-focus-tracking.patch",
    "0016-Extend-reload-agents-to-invalidate-Skill-and-Command.patch",
    "0017-TUI-SSE-loop-catch-transient-errors-and-reconnect.patch",
    "0018-Session-metadata-column.patch",
    "0019-Broadcast-reload-agents-notification-over-presence-W.patch",
    "0020-fix-stabilize-engine-typecheck-autoshare-migration-f.patch",
    "0021-Capture-git-branch-and-remote-URL-in-session-metadat.patch",
    "0022-fix-inline-git-info-read-into-createNext-drop-broken.patch",
    "0023-fix-rerender-subagent-count-pill-on-session-focus-ch.patch",
    "0024-test-add-scenario-test-stubs-Stage-10-Stage-11-TODO.patch",
]
external_engines = module_extension(
    implementation = _ext_impl,
    tag_classes = {
        "bun": tag_class(attrs = {
            "version": attr.string(mandatory = True),
        }),
        # Opencode tag added in Phase 2b.
        "opencode": tag_class(attrs = {
            "version": attr.string(mandatory = True),
            "sha256": attr.string(mandatory = True),
        }),
    },
)
