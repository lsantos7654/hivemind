# Nixpkgs Build System

## Build System Type

Nixpkgs is itself written in the **Nix expression language** and evaluated by the **Nix package manager**. It is not a traditional build system (Make, CMake, Cargo, etc.) — instead, it is a meta-build system: a collection of Nix expressions that describe how to invoke any number of underlying build systems (autotools, CMake, Meson, Cargo, Go modules, Cabal, etc.) in a reproducible, isolated manner.

The core build interface is the Nix **derivation**: a specification of inputs, build commands, outputs, and environment, evaluated by `nix-build` or the Nix daemon.

## Configuration Files

| File | Role |
|---|---|
| `flake.nix` | Modern flakes entry point: declares inputs (none for nixpkgs itself) and outputs |
| `default.nix` | Legacy entry: `import <nixpkgs> { config = {}; overlays = []; }` |
| `shell.nix` | Development environment with review and formatting tools |
| `pkgs/top-level/config.nix` | 200+ global configuration options (allowUnfree, allowBroken, etc.) |
| `pkgs/top-level/impure.nix` | Reads environment variables for config and platform |
| `pkgs/top-level/stage.nix` | Constructs a single consistent package set stage |
| `pkgs/top-level/all-packages.nix` | Master package attribute map |
| `pkgs/top-level/by-name-overlay.nix` | Generates overlay from `pkgs/by-name/` automatically |
| `pkgs/stdenv/default.nix` | Standard build environment with gcc, make, coreutils, etc. |

## External Dependencies and Management

Nixpkgs has **no external dependency manager** (no package.json, Cargo.toml, requirements.txt). All dependencies are:

1. **Other nixpkgs packages** — referenced by attribute name and resolved via the package set.
2. **External sources** — fetched at build time by fetcher functions (`fetchurl`, `fetchgit`, etc.) using content-addressed hashes.
3. **The Nix package manager itself** — the only external tool required to evaluate and build nixpkgs expressions. Minimum version requirements are expressed in `flake.nix` and documentation.

Binary caches (cache.nixos.org) serve pre-built artifacts, making most builds equivalent to downloads.

## Standard Build Environment (stdenv)

Every package builds inside a **stdenv** that provides:
- C/C++ compiler (GCC or Clang)
- GNU Make, coreutils, findutils, grep, sed, awk, tar, gzip
- Standard headers and build tools
- A set of **setup hooks** that implement build phases

The standard build phases executed by `stdenv.mkDerivation`:
1. `unpackPhase` — Unpack source archive
2. `patchPhase` — Apply patches
3. `configurePhase` — Run `./configure` (or CMake, Meson, etc.)
4. `buildPhase` — Run `make` or equivalent
5. `checkPhase` — Run test suite (if `doCheck = true`)
6. `installPhase` — Install to `$out`
7. `fixupPhase` — Patch shebangs, strip binaries, move docs
8. `installCheckPhase` — Post-install tests (if `doInstallCheck = true`)

Any phase can be overridden by setting `preBuild`, `postInstall`, etc.

## Build Commands

### Building a Package

```bash
# Build a single package
nix-build -A hello

# Build with flakes
nix build nixpkgs#hello

# Build a NixOS system
nix-build '<nixpkgs/nixos>' -A system -I nixos-config=./configuration.nix

# Build a package for a different platform
nix-build -A pkgsCross.aarch64-multiplatform.hello
```

### Development Shells

```bash
# Enter the nixpkgs development shell
nix-shell

# Enter a package's build environment for debugging
nix-shell -A curl

# With flakes
nix develop
nix develop .#curl  # for a specific package shell
```

### Evaluating and Querying

```bash
# Query a package attribute
nix eval nixpkgs#hello.version

# Show derivation details
nix show-derivation nixpkgs#hello

# List all packages matching a name
nix search nixpkgs hello
```

## Testing

### Library Tests

```bash
# Run lib/ unit tests
nix-build lib/tests/release.nix
nix-instantiate --eval lib/tests/misc.nix
```

### Package Tests

```bash
# Run a package's own test suite
nix-build -A hello.tests

# Run the testers suite
nix-build -A testers.runTests { ... }
```

### NixOS Integration Tests

NixOS tests use QEMU virtual machines. Each test is a Nix expression:

```bash
# Run a NixOS test
nix-build nixos/tests/nginx.nix

# With flakes
nix build .#nixosTests.nginx
```

Tests are written in Python and run inside the test VM framework:
```python
machine.start()
machine.wait_for_unit("nginx.service")
machine.succeed("curl http://localhost/")
```

### CI Validation

```bash
# Check format compliance
nix fmt --check

# Run Hydra release jobs locally
nix-build pkgs/top-level/release.nix -A unstable
```

## Language-Specific Build Systems

Each language ecosystem has dedicated build support:

### Rust (`rustPlatform`)
```nix
rustPlatform.buildRustPackage {
  pname = "ripgrep";
  version = "14.0.3";
  src = fetchFromGitHub { ... };
  cargoHash = "sha256-...";
}
```

### Go (`buildGoModule`)
```nix
buildGoModule {
  pname = "caddy";
  version = "2.7.6";
  src = fetchFromGitHub { ... };
  vendorHash = "sha256-...";
}
```

### Python (`buildPythonPackage`)
```nix
buildPythonPackage {
  pname = "requests";
  version = "2.31.0";
  pyproject = true;
  build-system = [ setuptools ];
  dependencies = [ certifi urllib3 ];
}
```

### Haskell (`haskell.packages.ghc96x.mkDerivation`)
```nix
mkDerivation {
  pname = "pandoc";
  version = "3.1.11";
  sha256 = "sha256-...";
  isLibrary = true;
  isExecutable = true;
  libraryHaskellDepends = [ ... ];
}
```

### Node.js (`buildNpmPackage`, `mkYarnPackage`)
```nix
buildNpmPackage {
  pname = "node-red";
  version = "3.1.3";
  src = fetchFromGitHub { ... };
  npmDepsHash = "sha256-...";
}
```

## Deployment Workflow

### Package Publication

1. Package is added/updated in `pkgs/by-name/<prefix>/<name>/package.nix` or `all-packages.nix`
2. PR submitted to GitHub
3. GitHub Actions CI runs automated checks (format, eval, basic build)
4. Hydra (hydra.nixos.org) evaluates and builds the package for all platforms
5. Successful builds are cached to cache.nixos.org
6. Package becomes available on `nixpkgs-unstable` channel immediately after merge
7. Stable releases (nixpkgs-25.05, nixpkgs-25.11) are branched and maintained separately

### NixOS System Deployment

```bash
# Apply NixOS configuration
sudo nixos-rebuild switch

# Test in a VM
sudo nixos-rebuild build-vm

# Roll back to previous generation
sudo nixos-rebuild switch --rollback
```

## Cross-Compilation

nixpkgs has first-class cross-compilation via `pkgsCross`:

```nix
# Package set targeting aarch64-linux from x86_64-linux
pkgsCross.aarch64-multiplatform.hello

# Raspberry Pi target
pkgsCross.raspberryPi.gcc

# musl-based static builds
pkgsMusl.curl
pkgsStatic.wget
```

Cross-compilation is managed through `splice.nix`, which maintains separate `buildPackages` (tools that run on the build host) and the main package set (output for the target).
