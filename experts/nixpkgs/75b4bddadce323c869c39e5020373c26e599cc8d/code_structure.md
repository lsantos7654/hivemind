# Nixpkgs Code Structure

## Annotated Top-Level Directory Tree

```
nixpkgs/
├── flake.nix                    # Flakes interface: outputs lib, legacyPackages, devShells
├── default.nix                  # Entry point for `import <nixpkgs>` (calls impure.nix)
├── shell.nix                    # Developer shell with nixpkgs-review, gh, treefmt
├── README.md                    # Project overview and quick-start
├── CONTRIBUTING.md              # Contribution guidelines
├── COPYING                      # MIT license
│
├── pkgs/                        # All package definitions (~38,099 Nix files)
│   ├── top-level/               # Package composition and aggregation layer
│   ├── by-name/                 # Modern alphabetical package layout (751 subdirs)
│   ├── build-support/           # Build infrastructure: fetchers, builders, hooks
│   ├── stdenv/                  # Standard build environments per platform
│   ├── applications/            # User-facing applications (traditional categories)
│   ├── development/             # Development tools and libraries
│   ├── tools/                   # System tools
│   ├── servers/                 # Server software
│   ├── games/                   # Games
│   ├── desktops/                # Desktop environments (GNOME, KDE, XFCE, etc.)
│   ├── kde/                     # KDE-specific packages
│   ├── data/                    # Data files and databases
│   ├── shells/                  # Shell implementations (bash, zsh, fish, etc.)
│   ├── misc/                    # Miscellaneous packages
│   ├── os-specific/             # OS-specific packages (linux/, darwin/)
│   └── test/                    # Package test definitions
│
├── lib/                         # Nix standard library (~600+ exported functions)
│   ├── default.nix              # Library entrypoint; imports and exposes all sub-libs
│   ├── trivial.nix              # id, const, pipe, flip, basic operators
│   ├── attrsets.nix             # Attribute set operations (53k lines)
│   ├── lists.nix                # List manipulation (40k lines)
│   ├── strings.nix              # String operations (66k lines)
│   ├── fixedPoints.nix          # Fixed-point combinators (fix, extends, composeExtensions)
│   ├── customisation.nix        # callPackageWith, makeOverridable, makeScope
│   ├── derivations.nix          # Derivation utilities and helpers
│   ├── modules.nix              # Module system: imports, options, config merging (75k)
│   ├── options.nix              # mkOption, mkEnableOption, showOption (25k lines)
│   ├── types.nix                # Module system types: str, int, bool, listOf, etc. (56k)
│   ├── generators.nix           # Config format generators: toJSON, toYAML, toINI, etc.
│   ├── licenses.nix             # License definitions (MIT, GPL, Apache, etc.) (40k)
│   ├── meta.nix                 # Package meta attribute helpers
│   ├── debug.nix                # traceVal, traceSeq, debugging tools
│   ├── versions.nix             # Version comparison and parsing
│   ├── asserts.nix              # assertMsg, assertOneOf, assertion helpers
│   ├── fetchers.nix             # Source fetching utilities
│   ├── sources.nix              # Source filtering, cleanSource
│   ├── cli.nix                  # CLI argument builder toGNUCommandLine
│   ├── kernel.nix               # Linux kernel configuration helpers
│   ├── gvariant.nix             # GVariant format generation for GNOME
│   ├── network/                 # Network utilities (CIDR, IP, etc.)
│   ├── filesystem.nix           # File system utilities
│   ├── fileset/                 # Advanced file set operations (separate module)
│   │   ├── default.nix
│   │   └── ...
│   ├── path/                    # Path type checking and manipulation
│   │   ├── default.nix
│   │   └── ...
│   ├── systems/                 # System/platform type definitions
│   │   ├── default.nix
│   │   ├── parse.nix            # System string parsing (x86_64-linux, aarch64-darwin)
│   │   └── ...
│   └── tests/                   # Library unit tests
│
├── nixos/                       # NixOS Linux distribution (~3,893 module files)
│   ├── default.nix              # NixOS system builder entry point
│   ├── lib/                     # NixOS-specific library extensions
│   │   └── make-disk-image.nix  # Disk image creation
│   ├── modules/                 # All NixOS module definitions
│   │   ├── config/              # Base system configuration
│   │   ├── hardware/            # Hardware detection and drivers
│   │   ├── i18n/                # Internationalization and locale
│   │   ├── image/               # System image generation (ISO, SD card, etc.)
│   │   ├── installer/           # NixOS installer
│   │   ├── misc/                # Miscellaneous OS options
│   │   ├── profiles/            # Pre-configured system profiles
│   │   ├── programs/            # Individual program configuration modules
│   │   ├── security/            # Security, PAM, AppArmor, audit
│   │   ├── services/            # System services (nginx, postgres, docker, etc.)
│   │   ├── system/              # Low-level system options
│   │   ├── tasks/               # System initialization tasks
│   │   ├── testing/             # NixOS test infrastructure
│   │   └── virtualisation/      # VMs, containers (Docker, QEMU, etc.)
│   ├── tests/                   # NixOS integration tests
│   └── doc/                     # NixOS manual source
│       └── manual/
│
├── doc/                         # Combined Nixpkgs+NixOS documentation
│   ├── README.md                # How to build the manual
│   └── manual/                  # Manual source files (Markdown + Nix)
│
├── maintainers/                 # Maintainer information and tooling
│   ├── maintainer-list.nix      # Maintainer records (GitHub handle, email, keys)
│   └── scripts/                 # Maintenance scripts (fetch-kde-source, etc.)
│
├── ci/                          # CI configuration for GitHub Actions
│
└── .github/                     # GitHub workflows, PR templates, issue templates
```

## Module and Package Organization

### The `pkgs/top-level/` Composition Layer

This directory is the nerve center of the package set:

| File | Role |
|---|---|
| `default.nix` | Main composition function; applies overlays, stages, config |
| `impure.nix` | Entry point that reads env vars (`NIXPKGS_CONFIG`, `NIXPKGS_ALLOW_UNFREE`) |
| `stage.nix` | Single bootstrap stage that constructs one consistent package set |
| `all-packages.nix` | 12,522-line master list mapping attribute names to `callPackage` calls |
| `aliases.nix` | Maps deprecated/renamed package names to their new names |
| `by-name-overlay.nix` | Generates overlay for packages in `pkgs/by-name/` |
| `config.nix` | Defines 200+ global configuration options |
| `splice.nix` | Cross-compilation: maps packages between build/host/target contexts |
| `variants.nix` | Variant package set combinations |
| `linux-kernels.nix` | Linux kernel package tree |
| `release.nix` | Hydra CI job definitions |
| `python-packages.nix` | Python ecosystem (782k lines) |
| `perl-packages.nix` | Perl ecosystem (1.1M lines) |
| `haskell-packages.nix` | Haskell ecosystem (14k lines) |
| `ruby-packages.nix` | Ruby ecosystem (124k lines) |
| `ocaml-packages.nix` | OCaml ecosystem (91k lines) |

### The `pkgs/by-name/` Modern Layout

The preferred location for new packages. Organized as:
```
pkgs/by-name/
├── ab/
│   ├── ab-av1/
│   │   └── package.nix     # Self-contained package definition
│   └── abcde/
│       └── package.nix
├── ac/
│   └── acl/
│       └── package.nix
...
```

Each `package.nix` is auto-discovered via `by-name-overlay.nix` — no entry in `all-packages.nix` is needed.

### The `pkgs/build-support/` Infrastructure

Organized by function:

**Fetchers** (70+ source fetchers):
- `fetchurl/` — HTTP/HTTPS downloads with hash verification
- `fetchgit/` — Git repositories
- `fetchgithub/`, `fetchgitlab/`, `fetchgitea/` — Hosted Git services
- `fetchpypi/` — Python Package Index
- `fetchcrate/` — Rust crates.io
- `fetchzip/`, `fetchpatch/` — Archive handling
- `fetchmavenartifact/` — Java Maven artifacts
- `fetchdocker/` — Docker image layers

**Language builders**:
- `rust/` — `rustPlatform.buildRustPackage`
- `go/` — `buildGoModule`
- `node/` — `buildNpmPackage`, `mkYarnPackage`
- `python/` — `python3.pkgs.buildPythonPackage`
- `ocaml/` — `ocamlPackages.buildDunePackage`
- `dotnet/` — `dotnetCorePackages.buildDotnetPackage`
- `haskell/` — Cabal-based builds

**Container builders**:
- `docker/` — `dockerTools.buildImage`
- `oci-tools/` — OCI image format
- `singularity-tools/` — Singularity/Apptainer

**Utilities**:
- `trivial-builders/` — `runCommand`, `writeScript`, `writeText`, `symlinkJoin`
- `setup-hooks/` — `makeWrapper`, `autoreconfHook`, `pkg-config`, etc.
- `testers/` — `runTests`, `testVersion`, `hasPkgConfigModules`
- `mkshell/` — `mkShell` for development environments
- `cc-wrapper/` — GCC/Clang/LLVM compiler wrapper with proper flags

### The `pkgs/stdenv/` Platform Environments

Provides the base standard build environment per platform:
- `linux/` — GNU/Linux stages (bootstrap → stdenv)
- `darwin/` — macOS with Apple SDK
- `freebsd/` — FreeBSD support
- `cross/` — Cross-compilation scaffolding
- `generic/` — Generic setup hooks and phases (unpackPhase, buildPhase, installPhase, etc.)

### The `nixos/modules/` Module Categories

NixOS modules follow a consistent pattern: `options` (declarations) + `config` (implementation):

| Category | Purpose |
|---|---|
| `config/` | Core system config: fonts, users, groups, environment variables |
| `hardware/` | CPU microcode, GPU drivers, sound, bluetooth, storage |
| `services/` | Daemon configuration (nginx, postgresql, openssh, etc.) — largest category |
| `programs/` | Individual program options (bash, zsh, vim, git, etc.) |
| `security/` | PAM, sudo, AppArmor, audit, firewall, TPM |
| `virtualisation/` | Docker, containerd, QEMU, libvirt, LXC, microVMs |
| `image/` | System image builders: ISO, SD card, disk image |
| `profiles/` | Curated option sets: minimal, graphical, hardened |
| `installer/` | NixOS installer configuration |
| `tasks/` | Boot-time tasks: filesystem mounts, network setup |

## Key Files and Their Roles

| File | Importance |
|---|---|
| `flake.nix` | Primary entry for modern Nix users; exports `legacyPackages`, `lib`, `nixosModules` |
| `default.nix` | Legacy entry point; calls `impure.nix` |
| `pkgs/top-level/all-packages.nix` | Master package index (12,522 lines, ~3,500 entries) |
| `pkgs/top-level/stage.nix` | Core composition function; wires overlays and package sets |
| `lib/modules.nix` | Module system; evaluateModules, mergeModules, fixupOptionType |
| `lib/types.nix` | Type system for NixOS options |
| `lib/customisation.nix` | callPackage, makeScope, makeOverridable |
| `lib/fixedPoints.nix` | `fix`, `extends`, `composeExtensions` for overlay composition |
| `nixos/default.nix` | nixosSystem builder and NixOS lib exports |
| `maintainers/maintainer-list.nix` | Record of all package maintainers |

## Code Organization Patterns

**callPackage pattern**: All packages use dependency injection — arguments to a `package.nix` function are automatically matched to attributes in the package set:
```nix
# pkgs/top-level/all-packages.nix
hello = callPackage ../applications/misc/hello { };
curl = callPackage ../tools/networking/curl { };
```

**Override pattern**: Any package can be customized without touching upstream:
```nix
curl.override { openssl = libressl; }
hello.overrideAttrs (old: { version = "2.12"; })
```

**Fixed-point composition**: The entire package set is a fixed point — packages can reference each other via lazy evaluation, and overlays can override attributes while still referencing the original:
```nix
final: prev: {
  myPackage = prev.myPackage.override { ... };
}
```

**Module system pattern**: NixOS modules declare options and provide configuration conditionally:
```nix
{ config, lib, pkgs, ... }:
{
  options.services.myService.enable = lib.mkEnableOption "my service";
  config = lib.mkIf config.services.myService.enable {
    systemd.services.myService = { ... };
  };
}
```
