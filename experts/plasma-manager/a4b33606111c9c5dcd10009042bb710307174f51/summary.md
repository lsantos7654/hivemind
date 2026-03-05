# plasma-manager: Summary

## Repository Purpose and Goals

plasma-manager is a Nix/Home Manager library that provides declarative configuration for the KDE Plasma desktop environment. Its core goal is to let users express their entire KDE Plasma setup — themes, panels, widgets, shortcuts, window rules, application settings, and more — as Nix code in their Home Manager configuration. This enables reproducible, version-controlled desktop environments that can be deployed across multiple machines identically.

The project was inspired by a long-standing Home Manager feature request and built on the work of several community contributors. It lives under the `nix-community` GitHub organization.

## Key Features and Capabilities

- **Low-level config file access**: The `files`, `configFile`, and `dataFile` options let you write directly to KDE INI config files (`$HOME`, `$XDG_CONFIG_HOME`, `$XDG_DATA_HOME`) with full key-value control, including immutability markers (`[$i]`) and shell expansion markers (`[$e]`).
- **High-level workspace settings**: The `workspace` module covers global themes (Look and Feel, Plasma style, color scheme), cursor themes, icon themes, wallpapers (static, slideshow, picture-of-the-day, plain color, custom plugin), window decorations, splash screens, widget style, and sound theme.
- **Panel management**: Full declarative panel configuration including location, height, alignment, hiding mode (autohide, dodge windows, etc.), floating, opacity, per-screen targeting, and ordered widget lists.
- **Widget configuration**: Both simple string-based widget specification and rich typed widget configuration for 14 named widgets (kickoff, kicker, digital clock, system tray, icon tasks, pager, etc.) plus a generic config-dict escape hatch.
- **KWin settings**: Virtual desktops (count, names, rows), titlebar button layout, night light, tiling, edge/corner barriers, and a large set of compositing effects (blur, wobbly windows, zoom, magnifier, minimize animations, etc.).
- **Shortcuts and hotkeys**: Global keyboard shortcuts via `kglobalshortcutsrc` and custom hotkey commands.
- **KDE application modules**: Application-specific declarative configuration for Kate, Konsole, Okular, Ghostwriter, and Elisa.
- **Input devices**: Keyboard, touchpad, and mouse configuration.
- **KRunner, screen locker, fonts, power management, session management, window rules, spectacle**: Dedicated modules for each.
- **overrideConfig mode**: When enabled, plasma-manager deletes all tracked KDE config files on each Home Manager activation and recreates them from scratch, giving fully declarative behavior.
- **rc2nix tool**: A Python script that reads existing KDE configuration files and outputs equivalent Nix expressions, simplifying migration.
- **Startup script system**: Generates shell scripts and Plasma desktop scripts (JavaScript evaluated via `qdbus`) that run at session start to apply settings that cannot be set via config files alone (theme application, panel layout, wallpaper).

## Primary Use Cases and Target Audience

The primary audience is NixOS or nix-darwin users who use Home Manager and run KDE Plasma as their desktop environment. Typical use cases include:

- Reproducible desktop setups across multiple machines from a single Nix config
- Version-controlling and sharing KDE configurations
- Declarative dotfile management for KDE (analogous to what Home Manager does for other apps)
- Migrating an existing imperative KDE setup to a declarative Nix-managed one using `rc2nix`

## High-Level Architecture Overview

When Home Manager activates, plasma-manager:

1. Collects all option values from the various NixOS/Home Manager module options under `programs.plasma.*`.
2. Merges them into a single JSON structure keyed by absolute config file paths.
3. Passes the JSON to `write_config.py` (a Python script), which reads and patches KDE INI-format config files in-place, respecting immutability flags and the `overrideConfig` deletion list.
4. Generates numbered shell scripts and Plasma desktop scripts (JavaScript), placing them under `$XDG_DATA_HOME/plasma-manager/scripts/` and `data/`.
5. Installs a `.desktop` autostart entry so that `run_all.sh` executes on each login. Scripts track their last-run SHA256 and skip re-execution unless their content changes (unless `runAlways = true`).
6. Theme application, panel layout, wallpaper, and other settings that require Plasma runtime APIs are applied via `plasma-apply-*` CLI tools or `qdbus org.kde.plasmashell evaluateScript`.

## Related Projects and Dependencies

- **Home Manager** (`github:nix-community/home-manager`): The module system plasma-manager plugs into; plasma-manager is imported as a Home Manager module.
- **nixpkgs** (`github:NixOS/nixpkgs/nixos-unstable`): Provides packages like `python3`, `kdePackages.*`, `polonium`, `plasma-panel-colorizer`, `application-title-bar`, etc.
- **KDE Plasma 5 / Plasma 6**: The target desktop environment. The `trunk` branch targets Plasma 6; a `plasma-5` branch targets Plasma 5.
- **rc2nix**: A Python tool bundled in the repo (`script/rc2nix.py`) to convert existing KDE configs to Nix.
- **Third-party widget packages**: `plasma-panel-colorizer`, `application-title-bar`, `plasmusic-toolbar`, `kara`, `plasma-panel-spacer-extended` — auto-installed when the corresponding widget is declared in the config.
