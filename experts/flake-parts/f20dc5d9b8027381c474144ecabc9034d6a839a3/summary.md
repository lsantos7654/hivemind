# flake-parts Summary

## Repository Purpose and Goals

`flake-parts` is the core of a distributed framework for writing Nix Flakes using the NixOS module system. Its primary goal is to bring the benefits of the NixOS module system — declarative configuration, composability, option merging, and modular decomposition — to Nix flakes.

The project aims to be a **minimal mirror of the Nix flake schema**: it provides options that represent standard flake attributes and establishes a principled, ergonomic way of handling per-system attributes (the `system` dimension in flake outputs like `packages.<system>.hello`). Used by itself without extra modules, it is very lightweight.

Unlike NixOS, but following Flakes' spirit, `flake-parts` is explicitly **not** a monorepo that absorbs all packages and configurations. Instead, it is a single composable module that other repositories can build upon, while ensuring a baseline level of compatibility with the core flake schema.

## Key Features and Capabilities

- **Module-based flake decomposition**: Split `flake.nix` into focused, reusable `flake-module.nix` files using Nix's module system.
- **Automatic system transposition**: Define packages, devShells, checks, apps, etc. once in `perSystem` and automatically get them transposed to `packages.<system>`, `devShells.<system>`, etc.
- **perSystem evaluation**: System-specific logic is defined in a `perSystem` option, which receives `system`, `pkgs`, `config`, `self'`, and `inputs'` as arguments.
- **withSystem**: Access per-system configuration from top-level (system-agnostic) modules.
- **moduleWithSystem**: Bridge NixOS/other module system modules to per-system flake-parts context.
- **Auto-provided `pkgs`**: When a `nixpkgs` input is present, `pkgs` is automatically available in `perSystem`.
- **Partitioned evaluations**: The `partitions` extra module allows partitioning flake attributes so that development-only inputs are not fetched when only production attributes are needed.
- **easyOverlay**: Expose `perSystem`-defined packages as a Nixpkgs overlay with minimal boilerplate.
- **flakeModules publishing**: Export reusable flake-parts modules via `flake.flakeModules`.
- **Module publishing**: Publish NixOS, generic, or other modules via `flake.modules.<class>.<name>`.
- **Debug mode**: Expose internal config, options, and `extendModules` in the flake output for interactive inspection.
- **String memoization**: Internal `memoizeStr` function avoids redundant per-system evaluations.

## Primary Use Cases and Target Audience

**Target audience**: Nix/NixOS practitioners who write or maintain Nix flakes, ranging from individual developers to large open-source projects (nixd, hyperswitch, argo-workflows, emanote, etc.).

**Primary use cases**:
1. Organizing a complex `flake.nix` into multiple focused files without custom glue code.
2. Cleanly handling the `system` dimension when defining per-architecture packages, shells, and checks.
3. Creating reusable flake modules that other projects can import.
4. Defining NixOS configurations alongside project packages in a single coherent flake.
5. Building library flakes whose outputs users can integrate into their own flakes.
6. Separating development dependencies from production dependencies via partitions.

## High-Level Architecture Overview

The core of `flake-parts` is a call to `lib.evalModules` (from nixpkgs-lib) that evaluates a user-supplied Nix module using `all-modules.nix` — the list of all built-in flake-parts modules — as the base configuration.

```
flake-parts.lib.mkFlake { inherit inputs; } { /* user module */ }
    → evalFlakeModule → lib.evalModules
        → [all-modules.nix] + [user module]
            → eval.config.flake  (the actual flake outputs)
```

The **transposition** mechanism is the core innovation: `perSystem` is evaluated once per system, and the resulting attributes are transposed (swapped indices) to produce `packages.<system>`, `devShells.<system>`, etc. This is implemented via `transposition.nix` and the `mkTransposedPerSystemModule` helper.

The `lib.nix` file is the primary entry point, exporting `flake-parts-lib` with:
- `mkFlake` / `evalFlakeModule`: Top-level evaluation functions
- `mkPerSystemOption` / `mkPerSystemType`: Helpers for extending `perSystem`
- `mkTransposedPerSystemModule`: Helper for adding new transposed output types
- `importApply` / `importAndPublish`: Module import helpers
- `memoizeStr`: String-keyed memoization for system lookups

## Related Projects and Dependencies

- **nixpkgs-lib** (`github:nix-community/nixpkgs.lib`): The only direct flake input. Provides the module system (`lib.evalModules`), option types, and all lib functions. Minimum supported version: 23.05.
- **flake-compat** (vendored in `vendor/`): Used by the `partitions` extra to load path-based flakes in pure mode.
- **flake.parts website** (`github:hercules-ci/flake.parts-website`): Official documentation site for flake-parts and the broader ecosystem of compatible modules.
- **hercules-ci-effects** (dev input): Used for CI automation (`herculesCI` flake attribute).
- **pre-commit-hooks-nix** (dev input): Used for development pre-commit hooks.
- **Ecosystem modules**: The broader flake-parts ecosystem includes many external modules (treefmt-nix, devenv, dream2nix, home-manager integration, etc.) that consumers can import alongside flake-parts.
