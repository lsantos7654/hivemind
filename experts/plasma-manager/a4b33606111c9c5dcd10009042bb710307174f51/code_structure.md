# plasma-manager: Code Structure

## Annotated Directory Tree

```
plasma-manager/
├── flake.nix                    # Nix flake entry point: exports homeModules, packages, apps, checks, devShells
├── flake.lock                   # Locked dependency versions (nixpkgs, home-manager)
├── default.nix                  # Legacy (non-flake) entry point for nix-channels usage
├── .envrc                       # direnv integration for development shell
├── .gitignore
├── LICENSE
├── README.md                    # Project documentation and getting-started guide
│
├── modules/                     # Core Home Manager modules (the main library)
│   ├── default.nix              # Root module: imports all sub-modules, defines programs.plasma.enable
│   ├── files.nix                # Low-level config file writer: file/configFile/dataFile options, overrideConfig
│   ├── startup.nix              # Startup script system: shell + desktop scripts, autostart entry
│   ├── workspace.nix            # Workspace appearance: theme, colorScheme, cursor, wallpaper, icons, etc.
│   ├── panels.nix               # Panel layout: panelType submodule, widget lists, panel desktop script
│   ├── desktop.nix              # Desktop widgets, icons arrangement, mouse actions
│   ├── kwin.nix                 # KWin compositor: effects, virtual desktops, night light, tiling, Polonium
│   ├── fonts.nix                # System-wide font settings (general, fixed-width, etc.)
│   ├── hotkeys.nix              # KDE global hotkey commands (khotkeysrc)
│   ├── shortcuts.nix            # Global keyboard shortcuts (kglobalshortcutsrc)
│   ├── input.nix                # Input device configuration (keyboard, touchpad, mouse)
│   ├── krunner.nix              # KRunner (application launcher) settings
│   ├── kscreenlocker.nix        # Screen locker settings
│   ├── powerdevil.nix           # Power management (AC, battery, low battery profiles)
│   ├── session.nix              # Session restore settings
│   ├── spectacle.nix            # Spectacle screenshot tool shortcuts
│   ├── window-rules.nix         # KWin window rules (kwinrulesrc)
│   ├── windows.nix              # Window behavior settings
│   │
│   ├── apps/                    # KDE application-specific modules
│   │   ├── default.nix          # Imports all app modules
│   │   ├── elisa.nix            # Elisa music player settings
│   │   ├── ghostwriter.nix      # Ghostwriter markdown editor settings
│   │   ├── konsole.nix          # Konsole terminal: profiles, color schemes
│   │   ├── okular.nix           # Okular PDF viewer settings
│   │   └── kate/
│   │       ├── default.nix      # Kate text editor: sessions, plugins, color themes
│   │       └── check-theme-name-free.sh  # Helper script for Kate theme validation
│   │
│   └── widgets/                 # Widget type definitions and converters
│       ├── default.nix          # Widget type system: compositeWidgetType, simpleWidgetType, desktopSimpleWidgetType
│       ├── lib.nix              # Widget helper functions: addWidgetStmts, configValueType, JS generation
│       ├── app-menu.nix         # org.kde.plasma.appmenu widget
│       ├── application-title-bar.nix  # com.github.antroids.application-title-bar widget
│       ├── battery.nix          # org.kde.plasma.battery widget
│       ├── digital-clock.nix    # org.kde.plasma.digitalclock widget
│       ├── icon-tasks.nix       # org.kde.plasma.icontasks widget
│       ├── keyboard-layout.nix  # org.kde.plasma.keyboardlayout widget
│       ├── kicker.nix           # org.kde.kicker widget
│       ├── kickerdash.nix       # org.kde.kickerdash widget
│       ├── kickoff.nix          # org.kde.plasma.kickoff widget
│       ├── pager.nix            # org.kde.plasma.pager widget
│       ├── panel-spacer.nix     # org.kde.plasma.panelspacer widget
│       ├── plasma-panel-colorizer.nix  # luisbocanegra.panel.colorizer widget
│       ├── plasmusic-toolbar.nix      # plasmusic-toolbar widget
│       ├── system-monitor.nix   # org.kde.plasma.systemmonitor widget
│       └── system-tray.nix      # org.kde.plasma.systemtray widget
│
├── lib/                         # Shared Nix library functions
│   ├── writeconfig.nix          # writeConfig function: generates write_config.py invocation
│   ├── types.nix                # Nix types: basicSettingsType, advancedSettingsType, coercedSettingsType
│   ├── panel.nix                # panelToLayout: generates Plasma desktop script JS for panels
│   ├── colorscheme.nix          # Color scheme persistence keys for overrideConfig
│   ├── wallpapers.nix           # Wallpaper type definitions (slideshow, POTD, fill modes)
│   └── qfont.nix                # QFont string serialization helpers
│
├── script/                      # Python utility scripts
│   ├── write_config.py          # Runtime config writer: reads JSON, patches KDE INI files
│   └── rc2nix.py                # Migration tool: reads KDE config files, outputs Nix expressions
│
├── docs/                        # Documentation sources
│   ├── default.nix              # Builds HTML + JSON option docs
│   ├── plasma-manager-options.nix  # Option set evaluation for doc generation
│   ├── static/style.css
│   └── manual/
│       ├── manual.md
│       ├── introduction.md
│       ├── preface.md
│       ├── options.md
│       └── manpage-urls.json
│
├── examples/                    # Usage examples
│   ├── home.nix                 # Comprehensive example showing most plasma-manager features
│   ├── homeManager/
│   │   ├── home.nix             # Minimal Home Manager example
│   │   └── README.md
│   ├── homeManagerFlake/
│   │   └── flake.nix            # Flake example with home-manager only
│   └── systemFlake/
│       └── flake.nix            # Flake example using system-level NixOS config
│
├── test/                        # NixOS VM tests
│   ├── basic.nix                # Main test suite (NixOS VM)
│   ├── demo.nix                 # Demo VM configuration
│   └── rc2nix/
│       └── test_rc2nix.py       # Python unit tests for rc2nix
│
└── .github/
    └── workflows/
        ├── ci.yml               # CI pipeline (runs nix flake check)
        ├── backport.yml         # Backport PRs to plasma-5 branch
        └── github_pages.yml     # Deploys docs to GitHub Pages
```

## Module and Package Organization

### Top-Level Entry Point

`flake.nix` is the primary entry point for flake users. It exports:
- `homeModules.plasma-manager`: The Home Manager module (imports `./modules`)
- `homeManagerModules` (deprecated alias with warning)
- `packages.{system}.rc2nix`: The rc2nix tool as a shell application wrapping `script/rc2nix.py`
- `packages.{system}.demo`: A NixOS VM for demonstration
- `packages.{system}.docs-html` and `docs-json`: Generated documentation
- `apps.{system}.{default,rc2nix,demo}`: Runnable app definitions
- `checks.{system}.default`: NixOS VM test
- `devShells.{system}.default`: Dev shell with nixfmt, ruby, python-lsp

### Module Organization Pattern

Every module follows the same Nix Home Manager module pattern:
1. Receives `{ config, lib, pkgs, ... }` as arguments
2. Reads `cfg = config.programs.plasma` for the full config
3. Declares `options.programs.plasma.<module-name>.*` using `lib.mkOption`
4. Declares `config = lib.mkIf cfg.enable { ... }` for the implementation
5. Uses `programs.plasma.configFile.*` or `programs.plasma.startup.*` to write output

Modules are composed via `imports` lists; `modules/default.nix` imports all of them and defines the top-level `programs.plasma.enable` option.

### Widget System Organization

Widgets are defined in `modules/widgets/`. Each widget file exports a Nix attribute set with:
- `opts`: The NixOS module options for the widget's configuration
- `convert`: A function converting the widget's options to `{ name, config, extraConfig }`
- `description`: Used for NixOS module option documentation

`modules/widgets/default.nix` aggregates all widget sources into a `compositeWidgetType` (a `lib.types.attrTag`) so each widget is an exclusive tag. The widget system supports three representations:
1. A plain string (widget name with default config)
2. A `{ name, config, extraConfig }` attrset (generic)
3. A `{ widgetName = { ... }; }` attrset (high-level, type-checked)

### Key Files and Their Roles

| File | Role |
|------|------|
| `modules/default.nix` | Root module, `programs.plasma.enable` option |
| `modules/files.nix` | Core config writer, `overrideConfig`, `resetFiles`, `immutableByDefault` |
| `modules/startup.nix` | Script generation, autostart `.desktop` file, script priority ordering |
| `modules/panels.nix` | `programs.plasma.panels` list, panel script generation |
| `modules/workspace.nix` | Appearance options + startup scripts for theme application |
| `modules/kwin.nix` | KWin options → `kwinrc` config entries |
| `lib/writeconfig.nix` | `writeConfig` function: JSON → `write_config.py` invocation |
| `lib/types.nix` | `coercedSettingsType`: allows `value` or `{ value, immutable, shellExpand, persistent, escapeValue }` |
| `lib/panel.nix` | Generates the Plasma desktop JavaScript for panel layout |
| `script/write_config.py` | Python: reads JSON, opens KDE INI files, patches keys with proper escaping |
| `script/rc2nix.py` | Python: reads `~/.config/*.rc` files, outputs Nix config expressions |

## Code Organization Patterns

- **All null by default**: Every option defaults to `null`; a `null` value means "don't touch this setting." This is the mechanism for the opt-in, additive (non-`overrideConfig`) behavior.
- **lib.mkIf patterns**: Each `config` block wraps changes in `lib.mkIf (cfg.option != null)` guards so only set options affect output.
- **Startup script priority system**: Scripts are numbered 0–8 (lower = earlier). Internal scripts use reserved priorities (1 = theme apply, 2 = panels, 3 = wallpaper). Users can use 0 or 4–8 for custom scripts.
- **Renamed option modules**: `lib.mkRenamedOptionModule` is used throughout to provide backwards-compatible option paths when options are renamed.
- **Python scripting for runtime ops**: Operations that need the KDE runtime (qdbus, plasma-apply-*) are done in generated shell/JS scripts rather than at build time.
