# Nixvim — APIs and Interfaces

## Public Entry Points

### 1. Home Manager Integration (most common)

```nix
# In your Home Manager configuration
{ inputs, pkgs, ... }: {
  imports = [ inputs.nixvim.homeModules.nixvim ];

  programs.nixvim = {
    enable = true;
    # ... configuration
  };
}
```

### 2. NixOS Module

```nix
# In configuration.nix or a module
{ inputs, ... }: {
  imports = [ inputs.nixvim.nixosModules.nixvim ];

  programs.nixvim = {
    enable = true;
    # ... configuration
  };
}
```

### 3. nix-darwin Module

```nix
{ inputs, ... }: {
  imports = [ inputs.nixvim.darwinModules.nixvim ];
  programs.nixvim.enable = true;
}
```

### 4. Standalone Package (`makeNixvim`)

```nix
# flake.nix
{
  inputs.nixvim.url = "github:nix-community/nixvim";

  outputs = { nixvim, nixpkgs, ... }: let
    system = "x86_64-linux";
    pkgs = nixpkgs.legacyPackages.${system};
  in {
    packages.${system}.nvim = nixvim.legacyPackages.${system}.makeNixvim {
      plugins.telescope.enable = true;
      opts.number = true;
    };
  };
}
```

### 5. Standalone Package with Module (`makeNixvimWithModule`)

```nix
packages.${system}.nvim = nixvim.legacyPackages.${system}.makeNixvimWithModule {
  imports = [ ./neovim-config.nix ];
  config = {
    plugins.lsp.enable = true;
  };
};
```

---

## Core Configuration Options (`programs.nixvim`)

### Editor Options

```nix
programs.nixvim = {
  # Vim options (vim.opt.*)
  opts = {
    number = true;
    relativenumber = true;
    tabstop = 2;
    shiftwidth = 2;
    expandtab = true;
    wrap = false;
    colorcolumn = "80";
    signcolumn = "yes";
    updatetime = 250;
    termguicolors = true;
  };

  # Global variables (vim.g.*)
  globals = {
    mapleader = " ";
    maplocalleader = " ";
  };

  # Colorscheme
  colorscheme = "tokyonight";
};
```

### Keymaps

```nix
programs.nixvim.keymaps = [
  {
    mode = "n";                    # Normal mode (default)
    key = "<leader>ff";
    action = "<cmd>Telescope find_files<cr>";
    options = {
      desc = "Find files";
      silent = true;
      noremap = true;
    };
  }
  {
    mode = [ "n" "v" ];           # Multiple modes
    key = "<leader>y";
    action.__raw = ''              # Raw Lua action
      function()
        vim.fn.setreg("+", vim.fn.getreg('"'))
      end
    '';
  }
];
```

### Autocommands

```nix
programs.nixvim.autoCmd = [
  {
    event = [ "BufWritePre" ];
    pattern = [ "*.nix" ];
    command = "retab";
  }
  {
    event = "BufEnter";
    pattern = "*";
    callback.__raw = ''
      function()
        vim.opt.formatoptions:remove({ "c", "r", "o" })
      end
    '';
  }
];
```

### Highlights

```nix
programs.nixvim.highlight = {
  Comment = { fg = "#888888"; italic = true; };
  NonText = { link = "Comment"; };
};
```

### Diagnostics

```nix
programs.nixvim.diagnostic = {
  settings = {
    virtual_text = true;
    signs = true;
    update_in_insert = false;
    underline = true;
    severity_sort = true;
    float = {
      border = "rounded";
      source = "always";
    };
  };
};
```

---

## Plugin Configuration API

### The `plugins.<name>` Namespace

Every plugin module exposes a consistent interface:

```nix
plugins.<plugin-name> = {
  enable = true;           # Required to activate the plugin
  package = pkgs.vimPlugins.<pkg>;  # Override default package

  # Plugin-specific settings (passed to require('plugin').setup(settings))
  settings = {
    option1 = "value";
    nested.option = 42;
    callback.__raw = "function() end";  # Raw Lua in settings
  };

  # Lua code hooks
  luaConfig = {
    pre = "-- Lua before require('plugin').setup()";
    post = "-- Lua after require('plugin').setup()";
  };

  # Plugin-provided keymaps (if the module defines them)
  keymaps = [
    { key = "<leader>x"; action = "<cmd>Command<cr>"; }
  ];
};
```

### LSP Configuration

```nix
plugins.lsp = {
  enable = true;

  servers = {
    # Rust
    rust_analyzer = {
      enable = true;
      settings = {
        cargo.allFeatures = true;
        checkOnSave.command = "clippy";
      };
    };

    # Lua
    lua_ls = {
      enable = true;
      settings = {
        Lua.diagnostics.globals = [ "vim" ];
      };
    };

    # TypeScript
    ts_ls.enable = true;

    # Python
    pyright.enable = true;

    # Go
    gopls.enable = true;

    # Nix
    nil_ls.enable = true;
    nixd.enable = true;
  };

  # LSP keymaps
  keymaps = {
    lspBuf = {
      "<leader>ca" = "code_action";
      "K"          = "hover";
      "gd"         = "definition";
      "gD"         = "declaration";
      "gi"         = "implementation";
      "gr"         = "references";
      "<leader>rn" = "rename";
    };
    diagnostic = {
      "<leader>e" = "open_float";
      "[d"        = "goto_prev";
      "]d"        = "goto_next";
    };
  };
};
```

### Completion (nvim-cmp)

```nix
plugins.cmp = {
  enable = true;
  settings = {
    sources = [
      { name = "nvim_lsp"; }
      { name = "luasnip"; }
      { name = "buffer"; }
      { name = "path"; }
    ];
    mapping = {
      "<C-n>".__raw = "cmp.mapping.select_next_item()";
      "<C-p>".__raw = "cmp.mapping.select_prev_item()";
      "<C-y>".__raw = "cmp.mapping.confirm({ select = true })";
      "<C-Space>".__raw = "cmp.mapping.complete()";
    };
    snippet.expand.__raw = ''
      function(args)
        require('luasnip').lsp_expand(args.body)
      end
    '';
  };
};

# Enable cmp sources as separate plugins
plugins.cmp-nvim-lsp.enable = true;
plugins.cmp-buffer.enable = true;
plugins.cmp-path.enable = true;
plugins.luasnip.enable = true;
plugins.cmp_luasnip.enable = true;
```

### Telescope

```nix
plugins.telescope = {
  enable = true;
  settings = {
    defaults = {
      layout_strategy = "horizontal";
      file_ignore_patterns = [ "node_modules" ".git" ];
    };
    pickers = {
      find_files = { hidden = true; };
    };
  };
  keymaps = {
    "<leader>ff" = "find_files";
    "<leader>fg" = "live_grep";
    "<leader>fb" = "buffers";
    "<leader>fh" = "help_tags";
  };
  extensions.fzf-native.enable = true;
};
```

### Treesitter

```nix
plugins.treesitter = {
  enable = true;
  settings = {
    highlight.enable = true;
    indent.enable = true;
    ensure_installed = [
      "nix" "lua" "rust" "python" "typescript" "tsx" "json" "yaml" "toml"
    ];
  };
};
```

### Colorschemes

```nix
# Method 1: Set colorscheme name only (plugin must be installed separately)
colorscheme = "tokyonight";

# Method 2: Use a Nixvim colorscheme module
colorschemes.tokyonight = {
  enable = true;
  settings = {
    style = "night";
    transparent = false;
    terminal_colors = true;
  };
};

# Available colorschemes (34 total):
# ayu, catppuccin, dracula, everforest, gruvbox, kanagawa,
# melange, modus, monochrome, moonfly, nightfox, nightfly,
# nord, nordic, one, onedark, oxocarbon, palenight,
# papercolor, rose-pine, solarized, tokyonight, vscode, ...
```

---

## Library API (`lib.nixvim`)

### Raw Lua Injection (`mkRaw`)

The most important escape hatch — wraps a string as raw Lua:

```nix
# In any option that accepts Nix values:
{ __raw = "vim.fn.getcwd()"; }

# Using the helper (equivalent):
lib.nixvim.mkRaw "vim.fn.getcwd()"
```

### Option Builders (`lib.nixvim.defaultNullOpts`)

Used by plugin authors to define typed options:

```nix
lib.nixvim.defaultNullOpts.mkStr "default_value" "Description of option."
lib.nixvim.defaultNullOpts.mkInt 42 "An integer option."
lib.nixvim.defaultNullOpts.mkBool false "A boolean option."
lib.nixvim.defaultNullOpts.mkEnum [ "a" "b" "c" ] "a" "An enum option."
lib.nixvim.defaultNullOpts.mkListOf types.str [ ] "A list option."
lib.nixvim.defaultNullOpts.mkAttrsOf types.int { } "An attrset option."
lib.nixvim.defaultNullOpts.mkNullable types.str null "Nullable string."
lib.nixvim.defaultNullOpts.mkBorder "rounded" "Border style option."
lib.nixvim.defaultNullOpts.mkHighlight { } "Highlight group option."
lib.nixvim.defaultNullOpts.mkLogLevel "warn" "Log level option."
```

### Plugin Builder (`mkNeovimPlugin`)

Used to define plugin modules for `plugins/by-name/`:

```nix
# plugins/by-name/my-plugin/default.nix
{ lib, ... }:
lib.nixvim.plugins.mkNeovimPlugin {
  name = "my-plugin";
  package = "my-plugin-nvim";     # vimPlugins attribute name
  maintainers = [ lib.maintainers.your_name ];
  description = "My plugin for Nixvim.";

  settingsOptions = {
    option1 = lib.nixvim.defaultNullOpts.mkStr null "Description.";
    option2 = lib.nixvim.defaultNullOpts.mkBool false "Another option.";
  };

  settingsExample = {
    option1 = "value";
    option2 = true;
  };
}
```

### `mkVimPlugin` — For Traditional Vim Plugins

```nix
lib.nixvim.plugins.mkVimPlugin {
  name = "vim-surround";
  package = "vim-surround";
  globalPrefix = "surround_";      # Sets vim.g.surround_* variables
  maintainers = [ lib.maintainers.your_name ];
}
```

### Lua Serialization (`toLuaObject`)

Converts Nix values to Lua table syntax:

```nix
lib.nixvim.toLuaObject {
  key = "value";        # → key = "value"
  num = 42;             # → num = 42
  flag = true;          # → flag = true
  list = [ 1 2 3 ];    # → { 1, 2, 3 }
  nested = { a = 1; }; # → { a = 1 }
  raw.__raw = "fn()";  # → fn()  (raw Lua, not a string)
}
# Result: { key = "value", num = 42, flag = true, list = { 1, 2, 3 }, ... }
```

---

## Extra Configuration Escape Hatches

For configuration that isn't covered by a module option:

```nix
programs.nixvim = {
  # Arbitrary Lua appended to init.lua
  extraConfigLua = ''
    vim.api.nvim_create_user_command("Format", function()
      vim.lsp.buf.format({ async = true })
    end, {})
  '';

  # Lua prepended to init.lua (runs before plugins load)
  extraConfigLuaPre = ''
    vim.loader.enable()  -- Enable the Lua loader
  '';

  # Lua appended after everything else
  extraConfigLuaPost = ''
    -- Runs last
  '';

  # Vimscript
  extraConfigVim = ''
    set noerrorbells
  '';

  # Extra plugins not covered by Nixvim modules
  extraPlugins = with pkgs.vimPlugins; [
    vim-nix
    my-custom-plugin
  ];

  # Extra PATH tools available to Neovim
  extraPackages = with pkgs; [
    ripgrep fd nodejs
  ];
};
```

---

## Integration Patterns and Workflows

### Modular Configuration with Imports

```nix
# home.nix
programs.nixvim = {
  enable = true;
  imports = [
    ./neovim/lsp.nix
    ./neovim/completion.nix
    ./neovim/ui.nix
    ./neovim/git.nix
  ];
};

# neovim/lsp.nix
{ ... }: {
  plugins.lsp.enable = true;
  plugins.lsp.servers.rust_analyzer.enable = true;
}
```

### Sharing a Nixvim Configuration as a Flake Module

```nix
# In your personal config flake:
outputs = { nixvim, ... }: {
  nixvimModules.default = { pkgs, ... }: {
    plugins.treesitter.enable = true;
    opts.number = true;
  };
};

# In another flake consuming it:
programs.nixvim.imports = [ other-flake.nixvimModules.default ];
```

### Overlaying Packages

```nix
programs.nixvim = {
  nixpkgs.overlays = [
    (final: prev: {
      vimPlugins = prev.vimPlugins // {
        my-plugin = prev.vimPlugins.my-plugin.override { /* ... */ };
      };
    })
  ];
};
```
