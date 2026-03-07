# import-tree — Build System

## Build System Type

`import-tree` has a minimal build system reflecting its zero-dependency philosophy:

- **Library**: No build step required. The library is a single Nix file (`default.nix`) imported directly.
- **Tests**: Delegated to the external [vic/checkmate](https://github.com/vic/checkmate) test runner (which uses `nix-unit` internally).
- **Documentation**: Astro static site built with `pnpm`.
- **Flake**: `flake.nix` is a trivial one-liner — no flake-level build configuration beyond re-exporting `default.nix`.

## Configuration Files

| File | Purpose |
|------|---------|
| `default.nix` | The library itself (also the build artifact) |
| `flake.nix` | Flake wrapper (`outputs = _: import ./.`) |
| `checkmate/modules/tests.nix` | Test definitions consumed by checkmate |
| `checkmate/modules/formatter.nix` | treefmt exclusions (`checkmate/tree/*`, `docs/*`) |
| `docs/package.json` | pnpm manifest for the documentation site |
| `docs/pnpm-lock.yaml` | Locked dependency versions |
| `docs/astro.config.mjs` | Astro + Starlight configuration |
| `.github/workflows/test.yml` | CI: run checkmate tests |
| `.github/workflows/gh-pages.yml` | CI: build and deploy docs |

## External Dependencies

### Library Dependencies

The library (`default.nix`) has **zero external dependencies**. It only uses:
- `builtins.*` — Nix built-in functions (`builtins.match`, `builtins.isPath`, `builtins.isAttrs`, `builtins.readFileType`, `builtins.isString`, `builtins.map`, `builtins.filter`, `builtins.toString`, `builtins.mapAttrs`)
- `lib.filesystem.listFilesRecursive` — From nixpkgs lib, accessed lazily (injected via module args or `.withLib`)
- `lib.pipe`, `lib.lists.flatten`, `lib.hasInfix`, `lib.hasSuffix`, `lib.hasPrefix`, `lib.removePrefix` — Accessed lazily from the same lib

The library is intentionally dependency-free at the flake level — `flake.nix` ignores all inputs.

### Test Dependencies

Tests are run via the external `vic/checkmate` flake (not declared as a flake input). The test command provides `checkmate` as the test runner:

```sh
nix flake check github:vic/checkmate --override-input target path:.
```

Checkmate internally uses:
- `nix-unit` — Nix expression unit testing

### Documentation Dependencies (`docs/package.json`)

| Package | Version | Purpose |
|---------|---------|---------|
| `astro` | `^5.17.3` | Static site framework |
| `@astrojs/starlight` | `^0.37.6` | Documentation theme for Astro |
| `@catppuccin/starlight` | `^1.1.1` | Catppuccin color theme plugin |
| `astro-mermaid` | `^1.3.1` | Mermaid diagram support |
| `mermaid` | `^11.12.3` | Diagram rendering library |
| `sharp` | `^0.34.5` | Image processing (Astro optimization) |

Package manager: **pnpm** (version 10, as specified in GitHub Actions workflow).

## Build Targets and Commands

### Library (No Build Step)

The library requires no build. To use it:

```nix
# As a flake input:
inputs.import-tree.url = "github:vic/import-tree";
# => inputs.import-tree is the import-tree callable object

# As a plain import:
let import-tree = import ./path-to/import-tree;

# From tarball (no flakes):
let import-tree = import (builtins.fetchTarball {
  url = "https://github.com/vic/import-tree/archive/main.tar.gz";
});
```

### Running Tests

```sh
# Run full test suite (uses checkmate as external test runner):
nix flake check github:vic/checkmate --override-input target path:.

# Or from CI (using exact commit):
nix flake check -L github:vic/checkmate --override-input target github:vic/import-tree/<SHA>
```

The `--override-input target path:.` flag tells checkmate to test the current directory. The test suite is in `checkmate/modules/tests.nix`.

### Formatting Code

```sh
# Format all Nix files (treefmt via checkmate):
nix run github:vic/checkmate#fmt
```

Treefmt configuration excludes `checkmate/tree/*` and `docs/*` (configured in `checkmate/modules/formatter.nix`).

### Documentation Site

```sh
# Development server (hot reload):
cd docs && pnpm install && pnpm run dev

# Production build:
cd docs && pnpm install && pnpm run build
# Output: docs/dist/

# Preview production build locally:
cd docs && pnpm run preview
```

## CI/CD Pipelines

### Test CI (`.github/workflows/test.yml`)

Triggered on: pull requests and pushes to `main`.

```yaml
jobs:
  flake-check:
    runs-on: ubuntu-latest
    steps:
      - uses: cachix/install-nix-action@v30
      - run: nix flake check -L github:vic/checkmate
               --override-input target github:$GITHUB_REPOSITORY/$GITHUB_SHA
```

Uses `cachix/install-nix-action` (version 30) to install Nix, then runs checkmate against the exact commit SHA.

### Documentation CI (`.github/workflows/gh-pages.yml`)

Triggered on: pushes to `main` that touch `docs/**`, or manual dispatch.

```yaml
jobs:
  deploy:
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4 (version: 10)
      - run: pushd docs && pnpm install && pnpm run build && popd
      # Deploys docs/dist/ to GitHub Pages
```

Deploys to GitHub Pages using the standard `actions/configure-pages` + `actions/upload-pages-artifact` + `actions/deploy-pages` stack. Concurrency group `"pages"` with `cancel-in-progress: true` to avoid conflicting deploys.

### Tangled Mirror (`.tangled/workflows/mirror.yml`)

Mirrors the repository to a Codeberg/Tangled host.

## How to Deploy/Release

There is no formal release process. The library is consumed directly from GitHub:

- **Latest**: `github:vic/import-tree` (follows the `main` branch)
- **Pinned**: `github:vic/import-tree/<commit-sha>` or via flake lock files
- **Tarball** (non-flake): `https://github.com/vic/import-tree/archive/main.tar.gz`

Users relying on the flake input can update with:
```sh
nix flake update import-tree
```
