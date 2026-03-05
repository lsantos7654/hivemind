# Nixvim — Build System

## Build System Type

Nixvim uses the **Nix Flakes** build system with **flake-parts** for modular flake organization. There is no Makefile, CMake, or traditional build system — all build logic is expressed in Nix.

**Key build files**:
- `flake.nix` — Flake entry point; imports flake-parts and delegates to `flake/flake-modules/`
- `flake.lock` — Locked dependency snapshot (reproducible builds)
- `default.nix` — flake-compat shim for non-flake Nix users (e.g., `nix-env`, `nix-build`)
- `flake/flake-modules/default.nix` — Core flake module orchestration
- `flake/flake-modules/nixvimConfigurations.nix` — `nixvimConfigurations` output builder
- `flake/flake-modules/nixvimModules.nix` — `nixvimModules` output builder

## Flake Inputs (External Dependencies)

All dependencies are declared in `flake.nix` and locked in `flake.lock`:

| Input | Purpose |
|---|---|
| `nixpkgs` | Neovim binary, all `vimPlugins.*`, standard lib |
| `flake-parts` | Modular flake output organization |
| `home-manager` | Home Manager module system integration |
| `nix-darwin` | macOS (nix-darwin) module system integration |

`nixpkgs` defaults to `nixpkgs-unstable`. Stable branches (e.g., `25.11`) track the corresponding `nixpkgs` release.

## Flake Outputs

Nixvim exports these flake outputs:

```
nixosModules.nixvim          # NixOS module (programs.nixvim)
homeModules.nixvim           # Home Manager module (programs.nixvim)
darwinModules.nixvim         # nix-darwin module (programs.nixvim)
nixvimModules.<name>         # Exportable sub-modules for composing configs
nixvimConfigurations.<name>  # Full evaluated Nixvim configs (for flake consumers)
legacyPackages.<system>.makeNixvim      # Standalone Neovim package builder
legacyPackages.<system>.makeNixvimWithModule  # Builder accepting a module argument
packages.<system>.docs       # Documentation (mdBook)
packages.<system>.man        # Man pages
devShells.<system>.default   # Development shell for contributors
checks.<system>.*            # Test derivations
```

## How Configuration Evaluation Works

### Module Evaluation Pipeline

```
User config (Nix attrset or module)
         ↓
lib.nixvim.modules.evalNixvim (modules.nix)
         ↓ (runs NixOS module system)
Merged configuration attrset
         ↓
modules/output.nix
         ↓ (serializes options → Lua)
lib.nixvim.toLuaObject (lib/to-lua.nix)
         ↓
Generated init.lua string
         ↓
pkgs.neovimUtils.makeNeovimConfig
         ↓
pkgs.wrapNeovimUnstable
         ↓
Final Neovim derivation
```

### `makeNixvim` — Standalone Package Builder

`legacyPackages.${system}.makeNixvim` accepts a configuration attrset and returns a Neovim derivation:

```nix
packages.nvim = inputs.nixvim.legacyPackages.${system}.makeNixvim {
  plugins.telescope.enable = true;
  opts.number = true;
};
```

### `makeNixvimWithModule`

Accepts a full NixOS-style module (with `imports`, `config`, etc.):

```nix
packages.nvim = inputs.nixvim.legacyPackages.${system}.makeNixvimWithModule {
  imports = [ ./my-neovim-module.nix ];
};
```

## Build Targets and Commands

### Common Developer Commands

```bash
# Enter development shell (provides Nix, nil, statix, etc.)
nix develop

# Build and run the documentation server
nix run .#docs

# Build man pages
nix build .#man

# Run the full test suite (all platforms)
nix flake check --all-systems

# Run tests for a specific platform
nix build .#checks.x86_64-linux.home-manager-tests

# Build a specific plugin test
nix build .#checks.x86_64-linux.plugins-telescope

# Build the standalone Neovim package (from flake templates)
nix build .#packages.x86_64-linux.default
```

### Testing a Configuration During Development

```bash
# Directly run a Nixvim configuration without installing
nix run github:nix-community/nixvim -- --config my-config.nix

# Build and test a flake-based config
nix build .#packages.x86_64-linux.nvim
result/bin/nvim
```

## Plugin Package Resolution

Plugin packages are sourced from `nixpkgs.vimPlugins`. Each plugin module specifies its default package:

```nix
# In plugins/by-name/telescope/default.nix
{
  name = "telescope";
  package = pkgs.vimPlugins.telescope-nvim;
  # ...
}
```

Users can override the package:
```nix
plugins.telescope.package = pkgs.vimPlugins.telescope-nvim.overrideAttrs { /* ... */ };
```

## Performance Build Options

Nixvim includes build-time performance optimizations in `modules/performance.nix`:

### Byte-Compile Lua (`performance.byteCompileLua`)

Compiles Lua files to bytecode at build time using `luajit -b`:
```nix
performance.byteCompileLua = {
  enable = true;
  configs = true;       # Byte-compile init.lua and plugin configs
  nvimRuntime = true;   # Byte-compile Neovim runtime Lua files
  plugins = true;       # Byte-compile plugin Lua files
  initLua = true;       # Byte-compile the main init.lua
};
```

### Combine Plugins (`performance.combinePlugins`)

Merges all plugin directories into a single `pack/` entry, reducing startup file-system operations:
```nix
performance.combinePlugins = {
  enable = true;
  standalonePlugins = [ "nvim-treesitter" ]; # Exclude specific plugins
};
```

## Dependency Management

External tool dependencies (ripgrep, fd, tree-sitter CLI, etc.) are declared via `extraPackages`:

```nix
extraPackages = with pkgs; [
  ripgrep    # Required by telescope live_grep
  fd         # Required by telescope find_files
  tree-sitter # Required by nvim-treesitter
];
```

The `modules/dependencies.nix` module aggregates all plugin-declared dependencies and adds them to the Neovim wrapper's `PATH`.

## Release and Versioning

- Version information is stored in `version-info.toml`
- Release branches align with nixpkgs (`25.11`, `26.05`, etc.)
- Releases happen approximately every 6 months (May and November)
- The `main` branch tracks `nixpkgs-unstable` and is the development branch
- CI is managed via `buildbot-nix.toml` with builds triggered on pull requests

## Flake Templates

Two templates are available for bootstrapping new Nixvim projects:

**Simple template** (`templates/simple/`):
```bash
nix flake init -t github:nix-community/nixvim#simple
```

**Flake-parts template** (`templates/experimental-flake-parts/`):
```bash
nix flake init -t github:nix-community/nixvim#experimental-flake-parts
```
