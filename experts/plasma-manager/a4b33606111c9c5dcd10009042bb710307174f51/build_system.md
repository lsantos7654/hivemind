# plasma-manager: Build System

## Build System Type

plasma-manager uses **Nix Flakes** as its build system. The repository is a pure Nix flake with no build tools outside of Nix itself. A legacy `default.nix` is also provided for users who do not use flakes (nix-channels users).

The project has no compiled code. All outputs are either Nix modules (`.nix` files), Python scripts wrapped by Nix, or documentation built via Nix derivations.

## Configuration Files

| File | Purpose |
|------|---------|
| `flake.nix` | Primary build definition: inputs, outputs, packages, apps, checks, devShells |
| `flake.lock` | Locked revisions for all flake inputs |
| `default.nix` | Legacy entry point, imports `./modules` directly |
| `docs/default.nix` | Documentation build derivation (HTML + JSON) |
| `.envrc` | `use flake` for automatic devShell activation via direnv |

## External Dependencies

### Flake Inputs (declared in `flake.nix`)

```nix
inputs = {
  nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  home-manager.url = "github:nix-community/home-manager";
  home-manager.inputs.nixpkgs.follows = "nixpkgs";
};
```

- **nixpkgs (nixos-unstable)**: Provides all packages used at build and runtime.
- **home-manager**: The module framework plasma-manager plugs into. Its input nixpkgs is overridden to follow plasma-manager's nixpkgs to avoid duplicate nixpkgs in the closure.

### Runtime Dependencies (from nixpkgs)

These packages are referenced from the flake's `nixpkgsFor.${system}`:

| Package | Used For |
|---------|---------|
| `python3` | Running `write_config.py` and `rc2nix.py` |
| `kdePackages.plasma-workspace` | Provides `plasma-changeicons` libexec tool |
| `application-title-bar` | Auto-installed when `application-title-bar` widget is used |
| `plasmusic-toolbar` | Auto-installed when `plasmusic-toolbar` widget is used |
| `plasma-panel-colorizer` | Auto-installed when `luisbocanegra.panel.colorizer` widget is used |
| `kdePackages.applet-window-buttons6` | Auto-installed when `org.kde.windowbuttons` widget is used |
| `kara` | Auto-installed when `org.dhruv8sh.kara` widget is used |
| `plasma-panel-spacer-extended` | Auto-installed when `luisbocanegra.panelspacer.extended` widget is used |
| `polonium` | Auto-installed when `programs.plasma.kwin.scripts.polonium.enable = true` |

### Developer Shell Dependencies

The `devShells.default` provides:
- `nixfmt-rfc-style`: Formatter for Nix code (also used as `formatter` output for `nix fmt`)
- `ruby` + `ruby.devdoc`: For documentation tooling
- `python3` with `python-lsp-server`, `black`, `isort`: Python language server and formatters for editing scripts

## Supported Systems

```nix
supportedSystems = [ "aarch64-linux" "i686-linux" "x86_64-linux" ];
```

Packages, checks, apps, devShells, and formatter are generated for all three systems using `lib.genAttrs supportedSystems`. Note: **macOS is not a supported system** since KDE Plasma does not run on macOS.

## Build Targets and Commands

### Using the rc2nix Tool

Run the migration tool without cloning the repo:
```sh
nix run github:nix-community/plasma-manager
# Equivalent to:
nix run github:nix-community/plasma-manager#rc2nix
```

### Running the Demo VM

```sh
nix run github:nix-community/plasma-manager#demo
```

This builds a NixOS VM with a full KDE Plasma session and plasma-manager pre-configured.

### Building Documentation

```sh
nix build github:nix-community/plasma-manager#docs-html
nix build github:nix-community/plasma-manager#docs-json
```

### Running Tests

Tests are NixOS VM integration tests defined in `test/basic.nix`. They run with:

```sh
nix flake check
# Or for a specific system:
nix build .#checks.x86_64-linux.default
```

### Formatting Code

```sh
nix fmt
```

Uses `nixfmt-rfc-style` (RFC 166 style) for all `.nix` files.

### Entering the Dev Shell

```sh
nix develop
# Or with direnv:
direnv allow
```

## How to Use plasma-manager (Integration)

### With Nix Flakes

Add plasma-manager as a flake input and import the Home Manager module:

```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    home-manager.url = "github:nix-community/home-manager";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";
    plasma-manager.url = "github:nix-community/plasma-manager";
    plasma-manager.inputs.nixpkgs.follows = "nixpkgs";
    plasma-manager.inputs.home-manager.follows = "home-manager";
  };

  outputs = { nixpkgs, home-manager, plasma-manager, ... }: {
    homeConfigurations."user" = home-manager.lib.homeManagerConfiguration {
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
      modules = [
        plasma-manager.homeModules.plasma-manager
        ./home.nix
      ];
    };
  };
}
```

### With NixOS System Configuration

```nix
# flake.nix outputs
nixosConfigurations.mymachine = nixpkgs.lib.nixosSystem {
  modules = [
    home-manager.nixosModules.home-manager
    {
      home-manager.users.myuser = {
        imports = [ plasma-manager.homeModules.plasma-manager ];
        # ... plasma config here
      };
    }
  ];
};
```

### With Nix Channels (non-flake)

```nix
# In home.nix
{ config, pkgs, ... }:
let
  plasma-manager = import (fetchTarball "https://github.com/nix-community/plasma-manager/archive/trunk.tar.gz") {};
in {
  imports = [ plasma-manager.homeModules.plasma-manager ];
  # ... plasma config
}
```

## How the Runtime Configuration Works

At Home Manager activation time (`home-manager switch`):

1. **`modules/files.nix`** generates a Nix derivation that invokes `write_config.py` with:
   - A JSON file containing all config key-value pairs keyed by absolute file path
   - A space-separated list of config files to delete (the `resetFiles` list, when `overrideConfig = true`)
   - The `immutableByDefault` flag

2. **`write_config.py`** (Python) is executed as a Home Manager activation script:
   - Deletes listed config files if `overrideConfig` is set
   - For each config file, opens (or creates) the KDE INI file
   - Applies each key, respecting KDE's escape format, immutability markers, and persistence flags

3. **Startup scripts** (`modules/startup.nix`) generate:
   - Numbered shell scripts: `$XDG_DATA_HOME/plasma-manager/scripts/N_name.sh`
   - Desktop JavaScript files: `$XDG_DATA_HOME/plasma-manager/data/desktop_script_name.js`
   - A master `run_all.sh` that iterates scripts in order and restarts required services
   - An XDG autostart `.desktop` file pointing to `run_all.sh`

4. On each **login**, `run_all.sh` is executed. Each sub-script checks its SHA256 against a stored last-run file; if unchanged, it skips execution. If changed (new config generation), it re-applies the changes.

## Python Script Details

### `script/write_config.py`

- Parses KDE INI format including group nesting (`[Group][Subgroup]`)
- Handles KDE's custom escape sequences (`\s`, `\t`, `\n`, `\r`, `\\`, `\x??`, etc.)
- Writes back with proper escaping using the same escape format KDE uses
- Supports three key modifiers: `[$i]` (immutable), `[$e]` (shell-expand), both
- When a key is marked persistent, reads current value from file and preserves it

### `script/rc2nix.py`

- Reads KDE `.rc` INI config files
- Outputs Nix expressions under `programs.plasma.configFile.*`
- Run as: `nix run github:nix-community/plasma-manager [-- file1.rc file2.rc ...]`
- Falls back to reading standard KDE config locations if no files specified
