# Home Manager — Code Structure

## Annotated Directory Tree

```
repo/
├── flake.nix                     # Flake outputs: lib, packages, nixosModules, darwinModules, templates
├── flake.lock                    # Locked dependency versions (nixpkgs, etc.)
├── flake-module.nix              # flake-parts integration module
├── default.nix                   # Non-flake (legacy) entry point; mirrors flake outputs
├── overlay.nix                   # Nixpkgs overlay (adds home-manager package)
├── release.json                  # { "isReleaseBranch": bool } — controls release vs. dev mode
├── all-maintainers.nix           # Central database of module maintainers
├── Makefile                      # Convenience targets (docs, tests, format checks)
├── Justfile                      # Additional task runner recipes
├── treefmt.toml                  # Multi-formatter config (nixfmt, prettier, etc.)
├── buildbot-nix.toml             # Buildbot CI configuration
│
├── lib/                          # Public library (exported at flake level)
│   ├── default.nix               # Exports: homeManagerConfiguration, hm (extended lib)
│   ├── nix/                      # Nix-based maintainer extraction utilities
│   │   ├── extract-maintainers.nix
│   │   └── extract-maintainers-meta.nix
│   ├── python/                   # Python utility scripts (docs generation helpers)
│   └── bash/                     # Bash utility scripts
│
├── modules/                      # Core module library (~2,900 Nix files)
│   ├── default.nix               # evalModules entry point; returns activationPackage etc.
│   ├── modules.nix               # Master import list of all included modules
│   ├── home-environment.nix      # Core options: username, homeDirectory, stateVersion,
│   │                             #   packages, sessionVariables, activation scripts (30KB)
│   ├── files.nix                 # home.file.*: managed file/symlink system (13KB)
│   ├── systemd.nix               # systemd.user.{services,timers,sockets,...} (17KB)
│   ├── xsession.nix              # X11 session init, window manager hooks (7KB)
│   ├── wayland.nix               # Wayland session variables and hooks
│   ├── xresources.nix            # ~/.Xresources generation
│   ├── dbus.nix                  # D-Bus user session support
│   ├── manual.nix                # In-generation HTML/man documentation integration
│   ├── deprecations.nix          # Renamed/removed option aliases with warnings
│   │
│   ├── lib/                      # Extended standard library (lib.hm.*)
│   │   ├── default.nix           # Merges all lib sub-modules; sets lib.hm
│   │   ├── stdlib-extended.nix   # Augments nixpkgs.lib with all hm.* utilities
│   │   ├── dag.nix               # DAG: mkBefore/mkAfter/mkOrder/topoSort for activation
│   │   ├── types.nix             # Custom module types: dagOf, selectorFunction, etc.
│   │   ├── types-dag.nix         # Type definitions for DAG-ordered values
│   │   ├── generators.nix        # Config format generators: ini, toml, json, yaml, etc.
│   │   ├── file-type.nix         # File type helpers for home.file
│   │   ├── gvariant.nix          # GVariant encoding for dconf values
│   │   ├── deprecations.nix      # mkRenamedOptionModule, mkRemovedOptionModule wrappers
│   │   ├── maintainers.nix       # Maintainer alias database
│   │   ├── assertions.nix        # Extended assertion utilities
│   │   ├── booleans.nix          # Boolean utilities (xor, implies, etc.)
│   │   ├── strings.nix           # String utilities (levenshtein, toShellVar, etc.)
│   │   ├── shell.nix             # POSIX shell utilities (toExportedShellVariables, etc.)
│   │   ├── zsh.nix               # Zsh-specific utilities
│   │   ├── nushell.nix           # Nushell-specific utilities
│   │   └── darwin.nix            # macOS/launchd utilities
│   │
│   ├── config/                   # Core home configuration modules
│   │   ├── home-cursor.nix       # home.pointerCursor: cursor theme management
│   │   └── i18n.nix              # home.language: locale and i18n settings
│   │
│   ├── programs/                 # Application configuration modules (356 files)
│   │   ├── bash.nix              # programs.bash: Bash shell with aliases, initExtra
│   │   ├── zsh/                  # programs.zsh: Zsh with plugins, oh-my-zsh, powerlevel10k
│   │   ├── fish/                 # programs.fish: Fish shell
│   │   ├── nushell/              # programs.nushell: Nu shell config
│   │   ├── git/                  # programs.git: git config, delta, signing, hooks
│   │   ├── vim/                  # programs.vim: vimrc generation
│   │   ├── neovim/               # programs.neovim: init.lua, plugin management
│   │   ├── emacs/                # programs.emacs: init.el, use-package config
│   │   ├── vscode/               # programs.vscode: settings.json, extensions, keybindings
│   │   ├── ssh/                  # programs.ssh: ~/.ssh/config generation
│   │   ├── tmux/                 # programs.tmux: tmux.conf, plugin manager
│   │   ├── gpg.nix               # programs.gpg: gpg.conf, key management
│   │   ├── alacritty/            # programs.alacritty: terminal emulator config
│   │   ├── kitty/                # programs.kitty: terminal config
│   │   ├── wezterm/              # programs.wezterm: Lua-based config
│   │   ├── firefox/              # programs.firefox: profiles, extensions, policies
│   │   ├── chromium.nix          # programs.chromium: extensions, flags
│   │   ├── direnv.nix            # programs.direnv: .envrc, stdlib
│   │   ├── fzf.nix               # programs.fzf: key bindings, theme
│   │   ├── starship.nix          # programs.starship: cross-shell prompt
│   │   ├── htop.nix              # programs.htop: configuration
│   │   ├── mpv/                  # programs.mpv: mpv.conf, scripts
│   │   ├── password-managers/    # programs.{pass,bw,_1password,keepassxc}
│   │   └── ...                   # 300+ more application modules
│   │
│   ├── services/                 # User service modules (162 files)
│   │   ├── gpg-agent.nix         # services.gpg-agent: GPG agent daemon
│   │   ├── ssh-agent.nix         # services.ssh-agent: SSH agent daemon
│   │   ├── syncthing.nix         # services.syncthing: file sync daemon
│   │   ├── emacs.nix             # services.emacs: Emacs server daemon
│   │   ├── dunst.nix             # services.dunst: notification daemon
│   │   ├── polybar/              # services.polybar: status bar service
│   │   ├── sway/                 # services.sway: Wayland compositor
│   │   ├── i3/                   # services.i3: X11 window manager
│   │   ├── hyprland/             # services.hyprland: Wayland compositor
│   │   ├── home-manager-auto-upgrade.nix  # Automatic HM updates via systemd
│   │   ├── home-manager-auto-expire.nix   # Old generation cleanup
│   │   └── ...                   # 155+ more service modules
│   │
│   ├── accounts/                 # Unified account management
│   │   ├── email.nix             # accounts.email.*: multi-account email (mbsync, msmtp, etc.)
│   │   ├── calendar.nix          # accounts.calendar.*: caldav, khal, evolution
│   │   └── contacts.nix         # accounts.contacts.*: carddav, vdirsyncer
│   │
│   ├── misc/                     # Miscellaneous home configuration modules
│   │   ├── dconf.nix             # dconf.settings: GNOME dconf database
│   │   ├── fontconfig.nix        # fonts.fontconfig: fontconfig.conf generation (11KB)
│   │   ├── gtk.nix               # gtk.{theme,iconTheme,font,gtk2,gtk3,gtk4}
│   │   ├── gtk/                  # GTK sub-modules (gtk3 extraConfig, css)
│   │   ├── qt.nix                # qt.{platformTheme,style}
│   │   ├── qt/                   # Qt sub-modules
│   │   ├── nix.nix               # nix.{settings,registry,channels}: user Nix config
│   │   ├── nixpkgs.nix           # nixpkgs.{config,overlays}: per-user nixpkgs settings
│   │   ├── xdg.nix               # xdg.{configHome,dataHome,cacheHome,stateHome}
│   │   ├── xdg-mime.nix          # xdg.mimeApps: default applications per MIME type
│   │   ├── xdg-autostart.nix     # xdg.autostart: autostart .desktop entries
│   │   ├── xdg-user-dirs.nix     # xdg.userDirs: XDG_DOCUMENTS_DIR etc.
│   │   ├── xdg-portal.nix        # xdg.portal: desktop portal configuration
│   │   ├── news.nix              # news.* system for in-tool release notes
│   │   ├── version.nix           # home.stateVersion: compatibility versioning
│   │   ├── pam.nix               # pam.sessionVariables, loginLimits
│   │   ├── tmpfiles.nix          # systemd.user.tmpfiles.rules
│   │   ├── shell.nix             # home.shell: shell selection
│   │   ├── specialisation.nix    # specialisation.*: named config variants
│   │   ├── xfconf.nix            # xfconf.settings: Xfce settings
│   │   └── ...                   # Additional misc modules
│   │
│   ├── targets/                  # Platform-specific target modules
│   │   ├── generic-linux.nix     # targets.genericLinux: non-NixOS Linux support
│   │   └── darwin/               # macOS-specific options and integration
│   │
│   ├── i18n/                     # Internationalization
│   │   └── input-method/         # Input method engine configuration (fcitx5, ibus, etc.)
│   │
│   ├── launchd/                  # macOS launchd integration
│   │   └── default.nix           # launchd.agents.*, launchd.daemons.*
│   │
│   └── lib-bash/                 # Bash library for activation scripts
│       └── ...                   # Utility functions used in activation
│
├── home-manager/                 # CLI tool and package definition
│   ├── home-manager              # Main Bash executable (43KB): switch, build, generations, news
│   ├── default.nix               # Package derivation for home-manager binary + completions
│   ├── home-manager.nix          # Module wrapper (wraps modules/default.nix)
│   ├── formatter.nix             # nix fmt formatter configuration
│   ├── devShell.nix              # nix develop shell with dev tools
│   ├── install.nix               # Standalone installer script
│   ├── build-news.nix            # Release notes HTML builder
│   ├── completion.bash           # Bash tab completions
│   ├── completion.zsh            # Zsh tab completions
│   ├── completion.fish           # Fish tab completions
│   └── po/                       # Translation files (gettext)
│
├── nixos/                        # NixOS system module
│   ├── default.nix               # home-manager NixOS module: wires HM into systemd
│   └── common.nix                # Shared NixOS config used by module
│
├── nix-darwin/                   # macOS (nix-darwin) module
│   └── default.nix               # home-manager nix-darwin module: launchctl activation
│
├── docs/                         # Documentation source
│   ├── manual/                   # Manual (mdBook source)
│   │   ├── manual.md             # Root document
│   │   ├── introduction.md
│   │   ├── installation/         # Per-platform installation guides
│   │   ├── usage/                # Usage guides (switch, build, news, generations)
│   │   ├── nix-flakes/           # Flakes-specific docs
│   │   ├── writing-modules/      # Module development documentation
│   │   ├── contributing/         # Contribution guide
│   │   ├── internals/            # Architecture internals
│   │   └── faq/                  # Frequently asked questions
│   ├── release-notes/            # Per-release changelogs (rl-*.md)
│   └── static/                   # Static documentation assets
│
├── templates/                    # nix flake init templates
│   ├── standalone/               # Standalone home-manager setup
│   ├── nixos/                    # NixOS-integrated setup
│   └── nix-darwin/               # nix-darwin-integrated setup
│
└── tests/                        # Test suite
    ├── default.nix               # Main test runner (uses nmt)
    ├── tests.py                  # Python test utilities
    ├── package.nix               # Test package derivation
    ├── asserts.nix               # Assertion helpers for tests
    ├── stubs.nix                 # Stub module definitions
    ├── darwinScrublist.nix       # Darwin output scrubbing for tests
    ├── modules/                  # Per-module test files
    │   ├── programs/             # 80+ program module tests
    │   ├── services/             # 50+ service module tests
    │   ├── accounts/             # Account module tests
    │   ├── config/               # Core config tests
    │   └── misc/                 # Misc module tests
    ├── integration/              # Integration tests
    │   ├── nixos/                # NixOS system integration tests
    │   └── standalone/           # Standalone CLI integration tests
    └── lib/                      # Library unit tests
        ├── types/                # Custom type tests
        └── generators/           # Generator utility tests
```

## Module and Package Organization

### Module Loading Chain
1. **Entry**: `lib/default.nix` exports `homeManagerConfiguration`
2. **Evaluation**: calls `modules/default.nix` via `pkgs.lib.evalModules`
3. **Module list**: `modules/modules.nix` provides the master import list
4. **Per-domain modules**: imported from `programs/`, `services/`, `misc/`, etc.

### Standard Module Pattern
Every program and service module follows this idiomatic structure:
```nix
{ config, lib, pkgs, ... }:
let
  cfg = config.programs.<name>;
in {
  options.programs.<name> = {
    enable = lib.mkEnableOption "...";
    package = lib.mkPackageOption pkgs "<name>" {};
    # ... additional typed options
  };

  config = lib.mkIf cfg.enable {
    home.packages = [ cfg.package ];
    xdg.configFile."<name>/config" = { ... };
    programs.bash.initExtra = "...";
    # etc.
  };
}
```

### Key Architectural Boundaries
- `lib/` — Public API surface (imported by end users in flakes)
- `modules/lib/` — Internal library used within module evaluation
- `modules/` — Module definitions (not imported directly by users)
- `home-manager/` — CLI tooling and package derivations
- `nixos/` and `nix-darwin/` — System-level integration wrappers

## Code Organization Patterns

- **Domain namespacing**: `programs.*`, `services.*`, `accounts.*`, `misc.*`, `targets.*`
- **Conditional config blocks**: All module config wrapped in `lib.mkIf cfg.enable`
- **DAG-ordered activation**: Activation steps ordered via `lib.hm.dag.mkBefore/mkAfter`
- **Generator functions**: `lib.hm.generators.*` used consistently for config file output
- **Deprecation modules**: Old options mapped via `lib.mkRenamedOptionModule` in `deprecations.nix`
- **State version guards**: Breaking changes gated behind `home.stateVersion` comparisons
- **News entries**: Each breaking change accompanied by a news entry in `misc/news.nix`
