# Home Manager — Repository Summary

## Purpose and Goals

Home Manager is a Nix-based system for declarative, reproducible management of user home directories, dotfiles, environment variables, and application configurations. It extends the NixOS module system to the user level, allowing individuals to describe their entire home environment as code and apply it across multiple machines or operating systems with full rollback support.

The project's core goals are:
- **Reproducibility**: Identical home environments across different machines and systems
- **Declarativity**: All configuration expressed in Nix, eliminating imperative dotfile scripts
- **Composability**: Modular system where configurations can be mixed, extended, and shared
- **Multi-Platform**: First-class support for Linux (standalone, NixOS), macOS (nix-darwin), and other UNIX systems

## Key Features and Capabilities

- **350+ program modules**: Declarative configuration for common tools (bash, zsh, git, neovim, VS Code, tmux, Firefox, SSH, GPG, and hundreds more)
- **160+ service modules**: User-level systemd services and macOS launchd jobs
- **Three integration modes**: Standalone CLI tool, NixOS module, or nix-darwin module
- **Generation management**: Full rollback to previous configurations with `home-manager generations`
- **Activation scripts**: Safe, atomic home directory updates with backup/restore on conflict
- **Account management**: Unified email, calendar, and contacts account configuration
- **XDG compliance**: Automatic XDG base directory specification enforcement
- **GTK/Qt theming**: Declarative desktop theming configuration
- **Font configuration**: fontconfig management including custom fonts
- **dconf/GVariant**: GNOME settings database configuration
- **News system**: In-tool release notes and migration notices
- **State versioning**: Forward-compatible configuration evolution via `home.stateVersion`
- **Extended Nix library**: `lib.hm` with DAG utilities, custom types, generators, and more

## Primary Use Cases

- **Developers** who want consistent shell environments, editor configs, and development tools across workstations
- **System administrators** managing home environments for multiple users or machines
- **NixOS users** who want to manage their home configuration alongside their system configuration
- **macOS users** combining nix-darwin with home-manager for full declarative system+home management
- **Dotfile managers** migrating from imperative tools (chezmoi, stow, etc.) to a fully reproducible Nix approach
- **Sysadmins and DevOps** who need guaranteed identical developer environments across a team

## High-Level Architecture

Home Manager is built on top of the **NixOS module system** (`pkgs.lib.evalModules`). Its architecture has several layers:

### Module System Core
The `modules/` directory contains the entire module library. `modules/default.nix` is the evaluation entry point, which imports `modules/modules.nix`—the master list of all included modules. Modules are standard NixOS-style modules with `options`, `config`, and `imports` attributes.

### Extended Library (`modules/lib/`)
Augments `nixpkgs.lib` with `lib.hm.*` functions: DAG operations for ordered activation steps, custom Nix types (dag, gvariant, selectorFunction), format generators (INI, TOML, JSON, YAML), GVariant encoding for dconf, and shell/string utilities.

### Activation System
When `home-manager switch` is run, the `home.activationPackage` (a bash derivation) executes to symlink managed files, write generated configs, enable systemd services, and run user-defined activation scripts in DAG-defined order.

### Integration Layers
- **Standalone** (`home-manager/`): A bash CLI script that drives Nix evaluation and activation independently
- **NixOS** (`nixos/`): A NixOS module that wires Home Manager activation into the systemd user service infrastructure
- **nix-darwin** (`nix-darwin/`): A nix-darwin module using launchctl for macOS activation

### Program and Service Modules
Each module in `modules/programs/` or `modules/services/` follows a standard pattern:
1. Declare `options.programs.<name>` (or `services.<name>`) with typed options
2. Conditionally generate config files, environment variables, shell aliases, and activation scripts under `config` when `enable = true`

## Related Projects and Dependencies

- **nixpkgs**: Primary dependency; provides the package set, base library, and module system
- **nix-darwin**: macOS system configuration tool; Home Manager provides a module for integration
- **NixOS**: Linux distribution using Nix; Home Manager provides a NixOS module
- **nmt** (Nix Module Tests): Test framework used in the test suite
- **flake-parts**: Flake composition tool; Home Manager provides a `flakeModules.home-manager` output
- **treefmt / nixfmt**: Code formatting used in the repository
- **buildbot-nix**: CI/CD for the project

The canonical repository is `github.com/nix-community/home-manager`. The project follows a release schedule aligned with NixOS (YY.MM versioning, e.g., 25.11). The master branch tracks `nixpkgs-unstable`.
