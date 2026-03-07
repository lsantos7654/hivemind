# The Dendritic Pattern — Build System

## Overview

The Dendritic Pattern repository itself has **no build system** in the traditional sense. There is no `Makefile`, `package.json`, `Cargo.toml`, `pyproject.toml`, or CI pipeline in the repository. The repository is documentation plus an annotated Nix example.

The `example/` subdirectory is a Nix flake and can be evaluated with standard Nix tooling, but it is deliberately incomplete (no hardware configurations, no real packages) and is not intended to be built as-is.

## Build System Type: Nix Flakes

The example uses the **Nix flake** system as its build/evaluation framework, layered with **flake-parts** as a module-system wrapper.

### Configuration Files

| File | Role |
|---|---|
| `example/flake.nix` | Flake entry point — declares inputs and wires outputs via flake-parts |
| `example/modules/*.nix` | All module files — evaluated as part of the flake-parts configuration |

There is no `flake.lock` file in the repository, meaning pinned dependency versions are not committed. Users adopting the pattern would generate their own lockfile.

## External Dependencies

### Flake Inputs (declared in `example/flake.nix`)

```nix
inputs = {
  flake-parts = {
    url = "github:hercules-ci/flake-parts";
    inputs.nixpkgs-lib.follows = "nixpkgs";
  };
  import-tree.url = "github:vic/import-tree";
  nixpkgs.url = "github:nixos/nixpkgs/25.11";
};
```

| Input | Source | Purpose |
|---|---|---|
| `flake-parts` | `github:hercules-ci/flake-parts` | Top-level module system evaluation framework; provides `lib.mkFlake`, `flake.modules`, per-system output helpers |
| `import-tree` | `github:vic/import-tree` | Recursively collects all `.nix` files in a directory into a list of imports — enables automatic module importing |
| `nixpkgs` | `github:nixos/nixpkgs/25.11` | Standard Nixpkgs — provides `lib`, package sets, and is the foundation for NixOS evaluations |

### Dependency Pinning

`nixpkgs-lib` (a lighter nixpkgs variant used by flake-parts itself) is made to follow the main `nixpkgs` input via `inputs.nixpkgs-lib.follows = "nixpkgs"`. This is a standard best practice to avoid evaluating two versions of nixpkgs in the same flake.

### Runtime Dependencies (for actual adoption)

When users adopt the Dendritic Pattern for their own infrastructure, they will typically also add:

- `home-manager` (`github:nix-community/home-manager`) — if managing user configurations
- `nix-darwin` (`github:nix-darwin/nix-darwin`) — if managing macOS systems
- `nix-on-droid` — if managing Android systems
- Any other flake-parts modules relevant to their setup

These are **not** in the example's `flake.nix` since the example is intentionally minimal.

## Build Commands

### Evaluating the Example Flake

Because the example has no `flake.lock` and no real hardware configurations, these are illustrative commands:

```bash
# Enter the example directory
cd example/

# Generate a lockfile (required before any evaluation)
nix flake lock

# Show all flake outputs
nix flake show

# Check all derivations under flake.checks
nix flake check

# Evaluate a specific NixOS configuration (if fully defined)
nix build .#nixosConfigurations.desktop.config.system.build.toplevel
```

### For an Adopter's Real Infrastructure Repo

```bash
# Initial setup
nix flake lock

# Build a NixOS system
nix build .#nixosConfigurations.<hostname>.config.system.build.toplevel

# Apply NixOS configuration on the target machine
sudo nixos-rebuild switch --flake .#<hostname>

# Apply home-manager configuration
home-manager switch --flake .#<username>@<hostname>

# Apply nix-darwin configuration
darwin-rebuild switch --flake .#<hostname>

# Run all checks
nix flake check

# Update all inputs
nix flake update

# Update a specific input
nix flake update nixpkgs
```

## How the Flake Evaluation Works

The evaluation pipeline is:

1. **`nix flake` reads `flake.nix`** — collects inputs, calls `flake-parts.lib.mkFlake`.
2. **`import-tree ./modules` runs** — produces a list of all `.nix` paths under `./modules/`, equivalent to `[ ./modules/meta.nix ./modules/flake-parts.nix ./modules/systems.nix ... ]`.
3. **flake-parts evaluates** — runs `lib.evalModules` on the collected modules, building the top-level configuration. All option declarations from all files are merged; all config values are merged.
4. **Option resolution** — after all modules are processed, `configurations.nixos.*` values are resolved to produce `flake.nixosConfigurations.*`. `flake.checks` is similarly populated.
5. **Flake outputs** — the resulting attrset (`nixosConfigurations`, `checks`, `packages`, etc.) is returned as the flake's `outputs`.

## Testing

The pattern wires up `flake.checks` automatically in `example/modules/nixos.nix`:

```nix
config.flake.checks =
  config.flake.nixosConfigurations
  |> lib.mapAttrsToList (
    name: nixos: {
      ${nixos.config.nixpkgs.hostPlatform.system} = {
        "configurations:nixos:${name}" = nixos.config.system.build.toplevel;
      };
    }
  )
  |> lib.mkMerge;
```

This means `nix flake check` will attempt to build every declared NixOS configuration's `system.build.toplevel`, providing a simple CI-friendly test command for the entire infrastructure.

## Adoption Guide

To adopt the Dendritic Pattern in a new repository:

1. Create `flake.nix` with `flake-parts` and `import-tree` as inputs.
2. Set `outputs = inputs: inputs.flake-parts.lib.mkFlake { inherit inputs; } (inputs.import-tree ./modules);`
3. Create a `modules/` directory.
4. Add a `modules/flake-parts.nix` that imports `inputs.flake-parts.flakeModules.modules` (to get the `flake.modules` option).
5. Add a `modules/systems.nix` setting `systems = [...]`.
6. Create one file per feature in `modules/`, each contributing to `flake.modules.nixos.<name>`, `flake.modules.homeManager.<name>`, etc.
7. Add configuration declaration modules (e.g. `modules/my-desktop.nix`) that reference feature modules and call `configurations.nixos.<name>.module = { imports = [...]; }`.
8. Run `nix flake lock` to generate the lockfile.

## No CI Configuration

The repository has no `.github/workflows/`, no `ci.yml`, and no external CI integration. Community members who have adopted the pattern in their own repos run `nix flake check` in their own CI pipelines.
