# import-tree — Summary

## Repository Purpose and Goals

`import-tree` is a minimal, zero-dependency Nix library that recursively discovers and imports Nix modules from a directory tree. Its primary goal is to eliminate the maintenance burden of manually maintaining `imports` lists in Nix configurations. Rather than listing every `.nix` file by hand, users simply point `import-tree` at a directory and all qualifying files are automatically included.

The project was created by [vic](https://bsky.app/profile/oeiuwq.bsky.social) and is part of the [Dendritic Nix](https://dendritic.oeiuwq.com) ecosystem. It is designed to enable the **Dendritic Pattern** — a convention where every file is a self-contained Nix module, and configuration is organized as a tree of small, focused files.

## Key Features and Capabilities

- **Recursive module discovery**: Scans a directory (or list of directories) and returns a Nix module whose `imports` list contains all discovered `.nix` files.
- **Default ignore convention**: Paths containing `/_` (underscore-prefixed directories) are excluded by default, providing a clean convention for private/helper files.
- **Chainable builder API**: Methods like `.filter`, `.filterNot`, `.match`, `.matchNot`, `.map`, `.addPath`, `.initFilter`, `.pipeTo`, `.withLib`, `.leafs`, `.files`, `.result`, and `.new` compose into precise file selection pipelines.
- **Custom API extension**: `.addAPI` enables library authors to ship pre-configured, domain-specific import-tree instances with their own named methods. API methods are late-bound, supporting incremental composition.
- **Path flexibility**: Accepts plain paths, lists of paths (arbitrarily nested), attrsets with `outPath` (like flake inputs), other import-tree objects, or raw attrsets/modules.
- **Zero dependencies**: The entire implementation is a single `default.nix` with no external inputs.
- **Works everywhere**: Compatible with flakes, non-flakes, NixOS, nix-darwin, home-manager, flake-parts, NixVim, and any other Nix module system.

## Primary Use Cases and Target Audience

**Target audience**: Nix users managing configurations with the Nix module system — particularly NixOS, nix-darwin, home-manager, flake-parts, and NixVim configurations.

**Primary use cases**:
1. **Dendritic configurations**: Organize NixOS/home-manager/flake-parts configs as a tree of one-concern-per-file modules without manual import lists.
2. **Flake-parts module loading**: Use `(inputs.import-tree ./modules)` directly as the flake-parts module function.
3. **Selective module loading**: Use filters and regex matching to include only specific subsets of modules (e.g., only files with a `+feature` flag in their name).
4. **Module distributions**: Library authors ship pre-configured import-tree objects with domain-specific API methods (e.g., `modules-tree.gaming.minimal`).
5. **File listing outside module eval**: Use `.withLib`/`.leafs`/`.files`/`.pipeTo` to get plain file lists for non-module use cases (e.g., reading `.md` files, counting files).

## High-Level Architecture Overview

The entire library is a **single Nix expression** (`default.nix`). The architecture is a self-referential callable attrset implementing a builder pattern:

- **`callable`**: The root import-tree value. It is an attrset with a `__functor` that makes it callable as a function. Calling it with a path returns a Nix module.
- **`__config`**: Internal state record accumulating `filterf`, `mapf`, `paths`, `lib`, `pipef`, `initf`, and `api`. Each builder method returns a new import-tree with updated state.
- **`perform`**: Core function that, given a config and a path, executes the pipeline: list files recursively, apply filters, apply maps, and return a module or list.
- **`leafs`**: The inner function that resolves a directory to a filtered, mapped list of files using `lib.filesystem.listFilesRecursive`.
- **Lazy lib access**: When used inside a module system (the common case), `lib` is obtained from the module arguments, avoiding the need to call `.withLib` explicitly. Outside module evaluation, `.withLib` must be called explicitly.

The `flake.nix` is a trivial one-liner that re-exports `default.nix` as flake outputs.

## Related Projects and Dependencies

- **[vic/flake-file](https://github.com/vic/flake-file)**: Related project for organizing flake outputs.
- **[vic/with-inputs](https://github.com/vic/with-inputs)**: Provides flake-like inputs from npins sources (for non-flake use with import-tree).
- **[Dendritic pattern](https://github.com/mightyiam/dendritic)**: The file-per-module convention that import-tree is designed to enable.
- **[vic/checkmate](https://github.com/vic/checkmate)**: The test framework used to test import-tree (via `nix-unit`).
- **[flake-parts](https://github.com/hercules-ci/flake-parts)**: Commonly used alongside import-tree for structured flake outputs.
- **[Dendrix](https://dendrix.oeiuwq.com/)**: Index of Dendritic-style community projects.
- **Documentation**: Built with [Astro Starlight](https://starlight.astro.build/) and deployed to GitHub Pages. Available at `https://import-tree.oeiuwq.com`.
