# The Dendritic Pattern — Summary

## Repository Purpose and Goals

The Dendritic Pattern is an architectural pattern for structuring Nix-based infrastructure codebases. It was created by Shahar "Dawn" Or (@mightyiam) and published at `github.com/mightyiam/dendritic`. The repository does **not** ship an installable library; it documents a design pattern and provides an annotated example. Its goal is to solve a recurring pain point in the Nix community: how to architect a codebase that manages multiple NixOS, home-manager, and nix-darwin configurations in a way that is maintainable, readable, and scalable.

The project acknowledges that many Nix users have re-architected their configuration codebases multiple times trying to solve problems such as sharing modules across multiple machines, managing cross-cutting concerns (e.g. a feature that applies to both NixOS and home-manager), and passing values between files without resorting to hacks like `specialArgs` pass-thru.

## Key Features and Capabilities

- **Universal module type**: Every Nix file that is not an entry point (`flake.nix`, `default.nix`) is a module of the top-level configuration (typically a flake-parts module). This eliminates the need to ask "what kind of file is this?"
- **Automatic importing**: Because all non-entry-point files share the same module type, they can be automatically imported with a trivial expression or the `import-tree` library, removing the need to maintain an explicit import list.
- **File path independence**: A file's path represents a *feature name*, not a configuration type or host assignment. Files can be freely renamed, moved, or split without breaking the architecture.
- **Single-feature files**: Each module implements exactly one feature across all configurations to which that feature applies. For example, a `shell.nix` module sets the default shell on NixOS, nix-darwin, and nix-on-droid simultaneously.
- **`deferredModule` for lower-level configs**: NixOS, home-manager, and nix-darwin modules are stored as `deferredModule`-typed option values in the top-level configuration, allowing them to be composed and referenced by name (e.g. `config.flake.modules.nixos.shell`) instead of via file imports.
- **Eliminates `specialArgs` pass-thru**: Since every file is a top-level module, any file can read from and write to the top-level `config`, making cross-file value sharing trivial.

## Primary Use Cases and Target Audience

**Target audience**: Nix power users and infrastructure engineers managing multi-machine, multi-platform configurations (NixOS, home-manager, nix-darwin, nix-on-droid) who have grown frustrated with file-organization complexity.

**Use cases**:
- Structuring a personal or team Nix infrastructure repository with multiple hosts and users
- Managing cross-platform feature modules (same feature defined for Linux, macOS, and Android)
- Avoiding repeated imports and `specialArgs`/`extraSpecialArgs` threading
- Adopting a convention where file renaming/reorganization carries zero risk of breaking configuration wiring

## High-Level Architecture Overview

The Dendritic Pattern layers three levels of the Nixpkgs module system:

1. **Top-level configuration** — typically a `flake-parts` evaluation. All non-entry-point `.nix` files are imported here, usually via `import-tree`. This level owns cross-cutting options such as `username`, `configurations.nixos`, and `flake.modules.*`.

2. **Feature modules** — each file implements one feature across all applicable platforms. A file declares lower-level modules (NixOS, home-manager, etc.) as values of `deferredModule`-typed options under `flake.modules.nixos.<name>`, `flake.modules.homeManager.<name>`, etc.

3. **Lower-level configurations** — NixOS (`nixosConfigurations`), home-manager, nix-darwin, etc. are declared as option values (e.g. `configurations.nixos.<hostname>.module`) and evaluated at flake output time. They import the relevant feature modules by referencing `config.flake.modules.*` names.

The entry point `flake.nix` is minimal: it declares inputs and calls `flake-parts.lib.mkFlake`, passing `import-tree ./modules` to import all feature files in bulk.

## Related Projects and Dependencies

- **[flake-parts](https://flake.parts)** — The most common top-level evaluation framework used with this pattern. Provides the `flake.modules` option via `flakeModules.modules`.
- **[import-tree](https://github.com/vic/import-tree)** (`github:vic/import-tree`) — A small Nix library that recursively collects all `.nix` files in a directory and returns them as a list of imports, enabling the automatic importing central to the pattern.
- **[vic/den](https://github.com/vic/den)** — An aspect-oriented dendritic framework building on this pattern.
- **[vic/dendritic-unflake](https://github.com/vic/dendritic-unflake)** — Non-flake, non-flake-parts examples of the pattern.
- **[vic/dendrix/Dendritic](https://vic.github.io/dendrix/Dendritic.html)** — Extended essay on the benefits of the pattern.
- **[Doc-Steve/dendritic-design-with-flake-parts](https://github.com/Doc-Steve/dendritic-design-with-flake-parts/wiki/Dendritic_Aspects)** — Module design guide.
- **Nixpkgs module system** — Core infrastructure; the `deferredModule` type is part of Nixpkgs itself.
- **NixOS, home-manager, nix-darwin** — The primary lower-level configuration systems the pattern organizes.
