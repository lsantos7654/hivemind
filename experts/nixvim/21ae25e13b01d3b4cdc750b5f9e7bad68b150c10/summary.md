# Nixvim — Repository Summary

## Purpose and Goals

Nixvim is a comprehensive Neovim configuration framework built on the Nix language and package manager. Its primary goal is to enable users to declaratively configure Neovim entirely through Nix, eliminating the need to write raw Lua or Vimscript by hand. All editor settings, keymaps, plugins, LSP servers, colorschemes, and autocommands are expressed as structured Nix options that are validated at evaluation time and then compiled into a generated Lua configuration.

The project aims to bring the same reproducibility, type-safety, and composability guarantees that Nix provides for system configuration to the Neovim editor environment. A configuration defined in Nixvim can be reproduced bit-for-bit across machines and shared as a flake.

## Key Features and Capabilities

- **435+ pre-configured plugin modules** covering LSP, completion, fuzzy finding, treesitter, Git integration, file trees, status lines, and more
- **34 colorscheme modules** with typed options for theme-specific settings
- **Declarative LSP configuration** with per-server options for all major language servers via `plugins.lsp.servers.*`
- **nvim-cmp integration** with typed sources, mappings, and formatting options
- **Null-by-default options** — options only emit Lua when explicitly set, keeping configs minimal
- **Raw Lua escape hatch** — any option accepts `{ __raw = "lua_expression"; }` for values that cannot be expressed in Nix
- **Performance features** — optional byte-compilation of Lua and plugin combining to reduce startup time
- **Lazy loading support** — experimental plugin lazy-loading by event, command, or filetype
- **Platform wrappers** for Home Manager, NixOS, and nix-darwin with a shared core
- **Standalone mode** via `makeNixvim` for packaging Neovim as a standalone derivation

## Primary Use Cases and Target Audience

**Target audience**: Nix users (NixOS, Home Manager, nix-darwin) who want to manage their Neovim configuration with the same tools they use for the rest of their system.

**Primary use cases**:
1. **Home Manager users** integrating Neovim into a reproducible user environment via `programs.nixvim`
2. **NixOS users** configuring a system-wide Neovim via the NixOS module
3. **nix-darwin users** doing the same on macOS
4. **Flake authors** packaging a custom Neovim derivation for distribution or personal use
5. **Plugin contributors** who want to add declarative Nix interfaces to Neovim plugins

## High-Level Architecture Overview

Nixvim is structured as a NixOS-style module system layered on top of `pkgs.wrapNeovimUnstable`. The evaluation pipeline is:

```
User Nix configuration
       ↓
NixOS Module System (lib.modules.evalModules)
       ↓
lib.nixvim.modules.evalNixvim
       ↓
Lua code generation (lib.nixvim.toLuaObject)
       ↓
pkgs.neovimUtils.makeNeovimConfig
       ↓
pkgs.wrapNeovimUnstable
       ↓
Final Neovim derivation (with plugins baked in)
```

The project is organized into four main layers:

1. **`lib/`** — Core library: option builders, custom types, Nix-to-Lua serialization, and utilities
2. **`modules/`** — Core configuration modules: keymaps, opts, colorschemes, plugins, autocmds, diagnostics
3. **`plugins/`** — 435+ individual plugin module definitions using `mkNeovimPlugin` / `mkVimPlugin`
4. **`wrappers/`** — Platform-specific integration modules for Home Manager, NixOS, nix-darwin, and nixpkgs

The flake is organized with `flake-parts` and exports:
- `nixosModules.nixvim` / `homeModules.nixvim` / `darwinModules.nixvim` — platform modules
- `legacyPackages.${system}.makeNixvim` — standalone package builder
- `nixvimConfigurations` — flake output helper for full Nixvim configs
- `nixvimModules` — exportable module definitions

## Related Projects and Dependencies

**Hard dependencies**:
- `nixpkgs` — Provides Neovim, all plugin packages, and the `pkgs.wrapNeovimUnstable` infrastructure
- `flake-parts` — Modular flake organization
- `home-manager` — For the Home Manager integration module
- `nix-darwin` — For the macOS integration module

**Ecosystem relationships**:
- Nixvim tracks `nixpkgs-unstable` by default, with stable branches aligned to the nixpkgs release cycle (25.11, 26.05, etc.)
- Plugin packages come from `nixpkgs.vimPlugins`; Nixvim provides the declarative Nix interface on top
- Documentation is built with mdBook and published to GitHub Pages
- CI uses Buildbot-Nix for build checks across all platforms
