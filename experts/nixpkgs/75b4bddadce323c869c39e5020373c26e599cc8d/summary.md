# Nixpkgs Repository Summary

## Repository Purpose and Goals

Nixpkgs is the official package collection and library for the Nix package manager and NixOS Linux distribution. It is one of the largest and most active software repositories in existence, containing over 120,000 package definitions, a comprehensive functional programming library for Nix, and the full configuration system for NixOS — a Linux distribution built entirely on reproducible, declarative configuration.

The repository serves three primary purposes:
1. **Package definitions** — Nix expressions that describe how to build software from source or binary, covering virtually every common open-source application, library, and tool.
2. **NixOS modules** — A declarative system configuration framework that describes OS-level services, programs, hardware configuration, and system options.
3. **Nix library (`lib`)** — A comprehensive set of reusable Nix functions for package building, module composition, type checking, string manipulation, and more.

## Key Features and Capabilities

- **Reproducible builds**: Every package is described as a pure, functional derivation — given the same inputs, you always get the same output.
- **Multiple language ecosystems**: Dedicated package sets and build infrastructure for Python, Perl, Haskell, Ruby, OCaml, Rust, Go, Node.js, Java, PHP, Lua, .NET, Coq/Rocq, Agda, D, Dart, and many more.
- **Cross-compilation**: First-class support for cross-compiling packages between architectures and platforms, including specialized `stdenv` stages.
- **NixOS integration**: Packages integrate with NixOS modules for full-system configuration, enabling declarative system management.
- **Overlay system**: Users and organizations can extend or override any part of the package set using composable overlays.
- **Flakes support**: Modern `flake.nix` interface for hermetic, reproducible builds and integration with other flake-based projects.
- **Extensive testing**: Package-level tests, NixOS module integration tests, library unit tests, and CI via Hydra at hydra.nixos.org.
- **Binary caches**: Build results from the official Hydra CI are published to cache.nixos.org for fast, transparent binary distribution.

## Primary Use Cases and Target Audience

**End users** use nixpkgs to:
- Install software with `nix-env -iA nixpkgs.<package>` or `nix profile install`
- Build NixOS system configurations via `nixosSystem`
- Manage development environments with `nix-shell` or `nix develop`
- Create reproducible build environments for projects

**Package maintainers** use nixpkgs to:
- Add and update package definitions in `pkgs/by-name/` or the traditional category structure
- Maintain language-specific package sets (Python, Haskell, Perl, etc.)
- Write and test NixOS modules for system services and programs

**NixOS system administrators** use nixpkgs to:
- Configure an entire Linux operating system declaratively
- Enable system services, programs, hardware support, and security options
- Produce reproducible, rollback-capable OS configurations

**Library users** use the `lib` module to:
- Build package composition and module systems
- Utilize type checking, option declarations, and merge strategies
- Manipulate attribute sets, lists, strings, and paths using battle-tested utilities

## High-Level Architecture Overview

Nixpkgs is organized into four major layers:

1. **`pkgs/`** — All package definitions, split between the traditional category-based layout (`pkgs/applications/`, `pkgs/development/`, `pkgs/tools/`, etc.) and the modern `pkgs/by-name/` structure. The `pkgs/top-level/` directory contains the composition layer that wires packages together through `all-packages.nix`, language-specific package sets, and the overlay system.

2. **`lib/`** — The Nix standard library. Contains utility functions for attribute sets, lists, strings, paths, file sets, options, types, module composition, license definitions, and more. The module system (`lib/modules.nix`) is particularly central to NixOS configuration.

3. **`nixos/`** — The NixOS Linux distribution module system. Contains ~3,900 module files organized by category (hardware, services, programs, security, virtualisation, etc.) and the NixOS documentation.

4. **`pkgs/build-support/`** — Build infrastructure including 70+ source fetchers, language-specific builders (Rust, Go, Node.js, etc.), container image builders (Docker, OCI), and setup hooks.

Packages are composed through `callPackage`, which performs dependency injection by matching function argument names to package set attributes. Users can customize any package with `overrideAttrs` or `override`, and extend the whole package set using overlays.

## Related Projects and Dependencies

- **Nix** — The package manager that evaluates nixpkgs expressions; nixpkgs requires a compatible Nix version.
- **Hydra** — The CI system at hydra.nixos.org that builds and caches nixpkgs packages.
- **NixOS** — The Linux distribution defined by `nixos/` modules; uses nixpkgs as its package source.
- **Home Manager** — A third-party project for user-level NixOS-style configuration, depends on nixpkgs.
- **nix-darwin** — macOS system configuration in NixOS style, imports nixpkgs packages.
- **Flake inputs** — Many flake-based projects use `nixpkgs` as an input for their package sets.
- **treefmt** — The code formatter used for nixpkgs formatting, configured via `flake.nix`.
