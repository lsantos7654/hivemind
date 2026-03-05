# Nixvim — Code Structure

## Annotated Directory Tree

```
/repo
├── flake.nix                        # Minimal flake entry point using flake-parts
├── flake.lock                       # Locked dependency graph
├── default.nix                      # flake-compat shim for non-flake Nix users
├── version-info.toml                # Auto-generated version/release tracking
├── README.md                        # Project overview and quick-start guide
├── CONTRIBUTING.md                  # ~30KB contributor guide: architecture, plugin creation, testing
├── MAINTAINING.md                   # Deprecation policy and release management reference
├── buildbot-nix.toml                # CI/CD build bot configuration
├── typos.toml                       # Typo checker configuration
│
├── lib/                             # Core Nixvim library — pure Nix functions
│   ├── top-level.nix                # Constructs the lib.nixvim namespace by importing sub-libs
│   ├── overlay.nix                  # Extends nixpkgs lib with lib.nixvim namespace
│   ├── options.nix                  # Option builder functions (mkNullable, defaultNullOpts.*, etc.)
│   ├── types.nix                    # Custom Nix types (rawLua, maybeRaw, highlight, border, etc.)
│   ├── to-lua.nix                   # Nix-to-Lua serialization (toLuaObject, mkRaw, literalLua)
│   ├── builders.nix                 # Lua file generation (writeLua, byteCompileLua*, etc.)
│   ├── lua-types.nix                # Lua type descriptors
│   ├── keymaps-helpers.nix          # Keymap construction utilities
│   ├── autocmd-helpers.nix          # Autocommand construction utilities
│   ├── deprecation.nix              # Deprecation warning helpers and mkRenamedOption wrappers
│   ├── modules.nix                  # Module evaluation (evalNixvim, mkNixvimModule)
│   ├── utils.nix                    # General utility functions
│   ├── utils.internal.nix           # Internal utilities (not part of public API)
│   ├── maintainers.nix              # Maintainer contact definitions
│   ├── tests.nix                    # Test infrastructure helpers
│   └── plugins/                     # Plugin builder infrastructure
│       ├── default.nix              # Exports mkNeovimPlugin, mkVimPlugin
│       ├── mk-neovim-plugin.nix     # Builder for Lua plugins (with .setup())
│       └── mk-vim-plugin.nix        # Builder for traditional Vim plugins
│
├── modules/                         # NixOS-style module definitions
│   ├── default.nix                  # Imports all core modules (always evaluated)
│   │
│   ├── top-level/                   # Modules only present at the top evaluation level
│   │   ├── default.nix              # Top-level module aggregator
│   │   ├── nixpkgs.nix              # nixpkgs pinning and overlay configuration
│   │   ├── output.nix               # Flake output definition and package building
│   │   ├── readonly-renames.nix     # Renamed/deprecated option passthrough
│   │   ├── test.nix                 # Test framework integration
│   │   ├── files/                   # File output modules (init.lua, extra files)
│   │   └── plugins/                 # Top-level plugin option aggregation
│   │
│   ├── lsp/                         # LSP core configuration modules
│   │   └── [server-specific modules]
│   │
│   ├── misc/                        # Miscellaneous core modules
│   │   ├── assertions.nix           # Configuration-level assertions and warnings
│   │   ├── context.nix              # Context/metadata propagation
│   │   ├── meta.nix                 # Module metadata
│   │   ├── nixvim-info.nix          # Nixvim version info injection
│   │   └── version.nix              # Version handling utilities
│   │
│   ├── autocmd.nix                  # Autocommand configuration (vim.api.nvim_create_autocmd)
│   ├── clipboard.nix                # Clipboard provider configuration
│   ├── colorscheme.nix              # Active colorscheme selection
│   ├── commands.nix                 # Custom Vim command definitions
│   ├── dependencies.nix             # External tool dependency declarations
│   ├── diagnostic.nix               # Diagnostic display (signs, virtual text, float)
│   ├── editorconfig.nix             # EditorConfig integration
│   ├── filetype.nix                 # Filetype detection patterns
│   ├── highlights.nix               # Highlight group definitions
│   ├── keymaps.nix                  # Keymap configuration (vim.keymap.set)
│   ├── lazyload.nix                 # Lazy-loading plugin configuration (experimental)
│   ├── lua-loader.nix               # Lua bytecode loader configuration
│   ├── opts.nix                     # vim.opt / vim.opt_global / vim.opt_local settings
│   ├── output.nix                   # Assembles final init.lua from all module contributions
│   ├── performance.nix              # Startup optimization (byte-compile, combine plugins)
│   ├── plugins.nix                  # Plugin list aggregation and wrapping
│   └── wrappers.nix                 # Platform wrapper integration points
│
├── plugins/                         # Individual plugin module definitions
│   ├── default.nix                  # Import orchestrator for all plugin modules
│   ├── deprecation.nix              # Plugin-level deprecation helpers
│   ├── TEMPLATE.nix                 # Reference template for new plugin modules
│   │
│   ├── by-name/                     # Auto-imported plugin modules (one dir per plugin)
│   │   ├── abolish/default.nix      # vim-abolish
│   │   ├── aerial/default.nix       # aerial.nvim (code outline)
│   │   ├── alpha/default.nix        # alpha.nvim (startup screen)
│   │   ├── bufferline/default.nix   # bufferline.nvim
│   │   ├── conform-nvim/default.nix # conform.nvim (formatter)
│   │   ├── dap/default.nix          # nvim-dap (debugger)
│   │   ├── flash/default.nix        # flash.nvim (motion)
│   │   ├── gitsigns/default.nix     # gitsigns.nvim
│   │   ├── harpoon/default.nix      # harpoon
│   │   ├── indent-blankline/        # indent-blankline.nvim
│   │   ├── lualine/default.nix      # lualine.nvim (statusline)
│   │   ├── mini/default.nix         # mini.nvim (collection)
│   │   ├── neo-tree/default.nix     # neo-tree.nvim (file explorer)
│   │   ├── noice/default.nix        # noice.nvim (UI replacement)
│   │   ├── notify/default.nix       # nvim-notify
│   │   ├── oil/default.nix          # oil.nvim (file manager)
│   │   ├── render-markdown/         # render-markdown.nvim
│   │   ├── snacks/default.nix       # snacks.nvim
│   │   ├── telescope/default.nix    # telescope.nvim
│   │   ├── todo-comments/           # todo-comments.nvim
│   │   ├── treesitter/default.nix   # nvim-treesitter
│   │   ├── trouble/default.nix      # trouble.nvim
│   │   ├── which-key/default.nix    # which-key.nvim
│   │   └── [420+ additional plugins alphabetically]
│   │
│   ├── cmp/                         # nvim-cmp completion engine
│   │   ├── default.nix              # Main cmp module
│   │   ├── auto-enable.nix          # Auto-enable cmp sources
│   │   ├── options/                 # Sub-option modules (mapping, formatting, etc.)
│   │   └── sources/                 # Individual source integrations (lsp, luasnip, path, etc.)
│   │
│   ├── lsp/                         # LSP plugin modules
│   │   ├── default.nix              # Main LSP configuration aggregator
│   │   └── language-servers/        # Per-server configuration (rust-analyzer, lua-ls, gopls, etc.)
│   │
│   └── pluginmanagers/              # Plugin manager integrations
│       ├── lazy.nix                 # lazy.nvim integration
│       └── packer.nix               # packer.nvim integration (legacy)
│
├── colorschemes/                    # Colorscheme modules (34 total)
│   ├── ayu/default.nix
│   ├── catppuccin/default.nix
│   ├── dracula/default.nix
│   ├── everforest/default.nix
│   ├── gruvbox/default.nix
│   ├── kanagawa/default.nix
│   ├── melange/default.nix
│   ├── nord/default.nix
│   ├── one/default.nix
│   ├── onedark/default.nix
│   ├── oxocarbon/default.nix
│   ├── rose-pine/default.nix
│   ├── solarized/default.nix
│   ├── tokyonight/default.nix
│   └── [20+ more colorschemes]
│
├── wrappers/                        # Platform integration wrappers
│   └── modules/
│       ├── shared.nix               # Shared wrapper logic (common to all platforms)
│       ├── hm.nix                   # Home Manager wrapper (programs.nixvim)
│       ├── nixos.nix                # NixOS module wrapper (programs.nixvim system-wide)
│       ├── darwin.nix               # nix-darwin wrapper
│       └── nixpkgs.nix              # nixpkgs-based standalone wrapper (makeNixvim)
│
├── flake/                           # Flake organization (flake-parts modules)
│   ├── flake-modules/
│   │   ├── default.nix              # Imports all flake modules
│   │   ├── auto.nix                 # Automatic derivation detection and handling
│   │   ├── nixvimConfigurations.nix # nixvimConfigurations flake output builder
│   │   └── nixvimModules.nix        # nixvimModules flake output builder
│   └── dev/                         # Development environment configuration
│       └── flake.lock
│
├── tests/                           # Test suite
│   ├── default.nix                  # Test runner/orchestrator
│   ├── platforms/                   # Platform integration tests
│   │   ├── home-manager.nix
│   │   ├── nixos.nix
│   │   └── darwin.nix
│   ├── test-sources/                # Test fixture configurations
│   ├── utils/                       # Test utility functions
│   ├── lib-tests.nix                # Library function unit tests
│   ├── lsp-servers.nix              # LSP server configuration tests
│   ├── plugins-by-name.nix          # Plugin module validation tests
│   └── failing-tests.nix            # Known-failing tests (tracked issues)
│
├── docs/                            # Documentation source
│   ├── user-guide/                  # Tutorials and guides
│   ├── platforms/                   # Platform-specific docs
│   ├── modules/                     # Auto-generated module option docs
│   ├── lib/                         # Library function documentation
│   ├── user-configs/                # Example user configurations
│   ├── mdbook/                      # mdBook configuration (book.toml)
│   ├── man/                         # Man page generation
│   └── server/                      # Documentation dev server
│
├── templates/                       # Flake templates for new users
│   ├── simple/flake.nix             # Basic Nixvim flake template
│   └── experimental-flake-parts/   # Advanced flake-parts template
│
├── generated/                       # Auto-generated files (do not edit manually)
├── ci/                              # CI scripts and configuration
│   ├── nvim-lspconfig/              # LSP config auto-update scripts
│   ├── tag-maintainers/             # Maintainer tagging automation
│   └── version-info/                # Version info generation
│
└── assets/                          # Logo and graphic assets
```

## Module and Package Organization

### The `lib.nixvim` Namespace

All Nixvim library functions live under `lib.nixvim`, constructed in `lib/top-level.nix` and injected into the nixpkgs lib via `lib/overlay.nix`. The namespace is divided into sub-namespaces:

- `lib.nixvim.options` — Option builder functions
- `lib.nixvim.types` — Custom Nix types
- `lib.nixvim.plugins` — Plugin builder functions (`mkNeovimPlugin`, `mkVimPlugin`)
- `lib.nixvim.keymaps` — Keymap helpers
- `lib.nixvim.autocmd` — Autocommand helpers
- `lib.nixvim.deprecation` — Deprecation utilities
- `lib.nixvim.modules` — Module evaluation functions

### Plugin Modules Pattern

Every plugin in `plugins/by-name/` follows the same pattern:
1. A directory named after the plugin (kebab-case)
2. A `default.nix` file using `lib.nixvim.plugins.mkNeovimPlugin` or `mkVimPlugin`
3. Defines: `name`, `package`, `maintainers`, `description`, `settingsOptions`, `settingsExample`

### Core Modules vs. Plugin Modules

- **Core modules** (`modules/`) are always evaluated and define the fundamental configuration surface: opts, keymaps, autocmds, highlights, colorscheme, diagnostics
- **Plugin modules** (`plugins/`) are opt-in; each plugin is inactive unless `plugins.<name>.enable = true` is set

## Code Organization Patterns

### Null-by-Default Options

The defining pattern throughout the codebase is that almost all options default to `null`. The `defaultNullOpts.*` family of functions in `lib/options.nix` creates options that emit nothing to the Lua output unless explicitly set. This keeps generated configurations minimal and avoids Neovim loading unnecessary defaults.

### Settings Options

Plugin settings use a special `settings` attrset option created by `mkSettingsOption`. Values in `settings` are passed through `toLuaObject` and fed directly to `require('plugin').setup(settings)`. This allows the full plugin API surface to be exposed without needing to enumerate every option individually.

### Raw Lua Escape Hatch

The `{ __raw = "lua_expression"; }` pattern (implemented via `lib.nixvim.mkRaw` and `types.rawLua`) allows injecting arbitrary Lua anywhere a typed option is expected. This is essential for callbacks, function references, and expressions that cannot be expressed as Nix values.

### Platform Abstraction

The `wrappers/modules/shared.nix` contains all logic common to every platform. Platform-specific wrappers (`hm.nix`, `nixos.nix`, `darwin.nix`) only add the platform-specific module system integration (e.g., mapping `config.programs.nixvim` to the shared configuration surface).
