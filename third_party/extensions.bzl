"""Module extension `external_engines`: fetches bun + opencode source.

Provides:
  @bun_macos_arm64//:bin, @bun_macos_x86_64//:bin,
  @bun_linux_arm64//:bin,  @bun_linux_x86_64//:bin
  @opencode_src//:hivemind_engine
"""

load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load(":opencode_install.bzl", "opencode_install")

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
        opencode_install(
            name = "opencode_src",
            version = opencode_tag.version,
            sha256 = opencode_tag.sha256,
            patches = ["@//third_party/patches:" + p for p in _OPENCODE_PATCHES],
            build_file = "@//third_party/opencode:BUILD.bazel.opencode",
        )

    return ctx.extension_metadata(reproducible = True)

# Patches applied to the fetched opencode tree, in order. Resolved relative
# to //third_party/patches/.
_OPENCODE_PATCHES = [
    "0001-Rewrite-the-TUI-exit-Continue-suggestion-to-hivemind.patch",
    "0002-Rebrand-the-OPENCODE-wordmark-TUI-logo-to-HIVEMIND.patch",
    "0003-Inline-connection-indicator-into-home-sidebar-footer.patch",
    "0004-Non-destructive-agent-reload-endpoint.patch",
    "0005-Hardened-opencode-config-defaults.patch",
    "0006-Bake-bash.sudo-deny-into-Permission.fromConfig.patch",
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
            "sha256":  attr.string(mandatory = True),
        }),
    },
)
