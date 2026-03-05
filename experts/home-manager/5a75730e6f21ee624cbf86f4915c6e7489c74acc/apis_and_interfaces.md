# Home Manager — APIs and Interfaces

## Public API Entry Points

### `homeManagerConfiguration` (Primary Function)

Defined in `lib/default.nix`. This is the main function used by end users in their `flake.nix`.

```nix
homeManagerConfiguration {
  pkgs,                  # nixpkgs package set (required)
  modules,               # list of HM modules (required)
  lib ? pkgs.lib,        # override the lib (optional)
  extraSpecialArgs ? {}, # extra arguments passed to all modules (optional)
  check ? true,          # enable option type checking (optional)
  minimal ? false,       # disable expensive outputs like docs (optional)
}
```

**Returns** a module system evaluation result with:
- `config` — Final merged configuration attribute set
- `options` — Declared options with metadata
- `activationPackage` — Derivation: the bash script that applies the config
- `newsDisplay` — String of news entries for display
- `extendModules` — Function to extend with additional modules

**Example** in `flake.nix`:
```nix
{
  inputs.home-manager.url = "github:nix-community/home-manager";
  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs = { nixpkgs, home-manager, ... }: {
    homeConfigurations."alice" = home-manager.lib.homeManagerConfiguration {
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
      modules = [ ./home.nix ];
    };
  };
}
```

---

## Core Module Options

### `home.*` — Core Home Configuration
(`modules/home-environment.nix`)

```nix
home.username = "alice";           # Required: Unix username
home.homeDirectory = "/home/alice"; # Required: Absolute path to home
home.stateVersion = "25.11";       # Required: Compatibility version
home.packages = [ pkgs.ripgrep ];  # Additional packages to install

# Environment variables (written to shell rc and systemd environment)
home.sessionVariables = {
  EDITOR = "nvim";
  PAGER = "less";
};

# Shell path additions
home.sessionPath = [ "$HOME/.local/bin" ];

# Activation scripts (ordered via DAG)
home.activation.myScript = lib.hm.dag.entryAfter ["writeBoundary"] ''
  echo "Activation step runs here"
'';

# Language-specific packages
home.language = {
  base = "en_US.UTF-8";
  time = "de_DE.UTF-8";
};
```

### `home.file.*` — File Management
(`modules/files.nix`)

```nix
# Symlink a file
home.file.".config/myapp/config".source = ./myconfig;

# Write a text file
home.file.".config/myapp/config".text = ''
  setting = value
'';

# Control whether to create parent directories
home.file.".config/myapp/config".force = true;

# Executable file
home.file.".local/bin/myscript" = {
  source = ./myscript.sh;
  executable = true;
};
```

### `xdg.*` — XDG Base Directory Support
(`modules/misc/xdg.nix`, `xdg-mime.nix`, `xdg-user-dirs.nix`, `xdg-portal.nix`)

```nix
# Override XDG directories
xdg.configHome = "${config.home.homeDirectory}/.config";
xdg.dataHome   = "${config.home.homeDirectory}/.local/share";
xdg.cacheHome  = "${config.home.homeDirectory}/.cache";
xdg.stateHome  = "${config.home.homeDirectory}/.local/state";

# xdg.configFile is the recommended way to write to ~/.config/
xdg.configFile."myapp/settings.ini".text = "...";

# Default applications per MIME type
xdg.mimeApps = {
  enable = true;
  defaultApplications = {
    "text/html" = "firefox.desktop";
    "image/png" = "feh.desktop";
  };
};

# XDG user directories
xdg.userDirs = {
  enable = true;
  documents = "${config.home.homeDirectory}/docs";
  download  = "${config.home.homeDirectory}/dl";
};
```

---

## Program Module Interface

All program modules under `modules/programs/` follow this pattern:

### `programs.<name>.enable`
Boolean option to enable the module. Default: `false`.

### `programs.<name>.package`
The package to install. Usually defaults to `pkgs.<name>` via `lib.mkPackageOption`.

### Common Shell Programs

```nix
# Bash (modules/programs/bash.nix)
programs.bash = {
  enable = true;
  shellAliases = { ll = "ls -la"; };
  initExtra = "source ~/.secrets";
  bashrcExtra = "export FOO=bar";
  historySize = 10000;
  historyControl = [ "ignoredups" "erasedups" ];
};

# Zsh (modules/programs/zsh/)
programs.zsh = {
  enable = true;
  oh-my-zsh = {
    enable = true;
    plugins = [ "git" "docker" ];
    theme = "robbyrussell";
  };
  plugins = [{
    name = "zsh-autosuggestions";
    src = pkgs.zsh-autosuggestions;
  }];
  initContent = "...";
};

# Fish (modules/programs/fish/)
programs.fish = {
  enable = true;
  shellAliases = { g = "git"; };
  functions = {
    mkcd = "mkdir -p $argv && cd $argv";
  };
};
```

### Git (`modules/programs/git/`)

```nix
programs.git = {
  enable = true;
  userName  = "Alice";
  userEmail = "alice@example.com";
  signing = {
    key = "ABCDEF01";
    signByDefault = true;
  };
  delta = {
    enable = true;
    options = { navigate = true; };
  };
  extraConfig = {
    pull.rebase = true;
    init.defaultBranch = "main";
  };
  aliases = {
    co = "checkout";
    lg = "log --oneline --graph";
  };
  ignores = [ "*.swp" ".DS_Store" ];
};
```

### SSH (`modules/programs/ssh/`)

```nix
programs.ssh = {
  enable = true;
  matchBlocks = {
    "myserver" = {
      hostname = "192.168.1.1";
      user = "admin";
      identityFile = "~/.ssh/id_ed25519";
      forwardAgent = true;
    };
  };
  serverAliveInterval = 60;
  addKeysToAgent = "yes";
};
```

### Editors

```nix
# Neovim (modules/programs/neovim/)
programs.neovim = {
  enable = true;
  viAlias  = true;
  vimAlias = true;
  defaultEditor = true;
  extraConfig = ''
    set number
    set tabstop=2
  '';
  plugins = with pkgs.vimPlugins; [
    nvim-treesitter
    telescope-nvim
  ];
};

# VS Code (modules/programs/vscode/)
programs.vscode = {
  enable = true;
  extensions = with pkgs.vscode-extensions; [
    vscodevim.vim
    ms-python.python
  ];
  userSettings = {
    "editor.fontSize" = 14;
    "editor.tabSize" = 2;
  };
};
```

---

## Service Module Interface

All service modules under `modules/services/` expose:

```nix
# GPG Agent (modules/services/gpg-agent.nix)
services.gpg-agent = {
  enable = true;
  defaultCacheTtl = 1800;
  enableSshSupport = true;
  pinentryPackage = pkgs.pinentry-curses;
};

# Syncthing (modules/services/syncthing.nix)
services.syncthing = {
  enable = true;
  tray.enable = true;
};

# Emacs server (modules/services/emacs.nix)
services.emacs = {
  enable = true;
  startWithUserSession = true;
};

# Auto-upgrade (modules/services/home-manager-auto-upgrade.nix)
services.home-manager.autoUpgrade = {
  enable = true;
  frequency = "weekly";
};
```

---

## Systemd User Services Interface
(`modules/systemd.nix`)

```nix
# Define a user service
systemd.user.services.myservice = {
  Unit = {
    Description = "My Service";
    After = [ "graphical-session.target" ];
  };
  Service = {
    ExecStart = "${pkgs.myapp}/bin/myapp";
    Restart = "on-failure";
  };
  Install = {
    WantedBy = [ "graphical-session.target" ];
  };
};

# Define a user timer
systemd.user.timers.mytimer = {
  Unit.Description = "My Timer";
  Timer = {
    OnCalendar = "daily";
    Persistent = true;
  };
  Install.WantedBy = [ "timers.target" ];
};
```

---

## `lib.hm` — Extended Standard Library

Available inside all Home Manager modules as `lib.hm.*` (or via the `hm` argument).

### DAG Utilities (`modules/lib/dag.nix`)

Used to define ordered activation scripts and configuration merging:

```nix
# Entry that runs after writeBoundary
home.activation.step1 = lib.hm.dag.entryAfter ["writeBoundary"] ''
  echo "runs after files are written"
'';

# Entry that runs before writeBoundary
home.activation.step2 = lib.hm.dag.entryBefore ["writeBoundary"] ''
  echo "runs before files are written"
'';

# Entry between two others
home.activation.step3 = lib.hm.dag.entryBetween ["after-this"] ["before-this"] ''
  echo "runs between"
'';
```

### Generators (`modules/lib/generators.nix`)

Used by module authors to produce config file content:

```nix
# Generate INI format
lib.generators.toINI {} {
  section1 = { key = "value"; };
}
# Output: [section1]\nkey = value

# Generate TOML
lib.generators.toTOML {} { key = "value"; list = [1 2 3]; }

# Generate key=value format
lib.generators.toKeyValue {} { FOO = "bar"; BAZ = "qux"; }
```

### GVariant Encoding (`modules/lib/gvariant.nix`)

Used with `dconf.settings`:

```nix
dconf.settings = {
  "org/gnome/desktop/interface" = {
    color-scheme = "prefer-dark";
    clock-show-seconds = lib.hm.gvariant.mkBoolean true;
    text-scaling-factor = lib.hm.gvariant.mkDouble 1.25;
    font-name = lib.hm.gvariant.mkString "Noto Sans 11";
  };
};
```

### Custom Types (`modules/lib/types.nix`)

```nix
# DAG type (used for ordered options)
options.myOption = lib.mkOption {
  type = lib.types.dagOf lib.types.str;
};

# selectorFunction: select from an attrset
options.theme = lib.mkOption {
  type = lib.hm.types.selectorFunction;
};
```

---

## Account Management Interface

### Email Accounts (`modules/accounts/email.nix`)

```nix
accounts.email = {
  maildirBasePath = "${config.home.homeDirectory}/mail";
  accounts.personal = {
    primary = true;
    address = "alice@example.com";
    realName = "Alice";
    passwordCommand = "pass show email/personal";
    imap = {
      host = "imap.example.com";
      port = 993;
    };
    smtp = {
      host = "smtp.example.com";
      port = 587;
    };
    mbsync = {
      enable = true;
      create = "maildir";
    };
    msmtp.enable = true;
    notmuch.enable = true;
  };
};
```

---

## Integration Patterns

### Flake-based Setup (Recommended)

```nix
# flake.nix
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    home-manager = {
      url = "github:nix-community/home-manager";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { nixpkgs, home-manager, ... }: {
    homeConfigurations."alice@workstation" = home-manager.lib.homeManagerConfiguration {
      pkgs = nixpkgs.legacyPackages.x86_64-linux;
      modules = [
        ./home.nix
        {
          home.username = "alice";
          home.homeDirectory = "/home/alice";
        }
      ];
      extraSpecialArgs = { inherit inputs; };
    };
  };
}
```

### NixOS Module Integration

```nix
# nixos/configuration.nix or flake.nix
{
  imports = [ inputs.home-manager.nixosModules.home-manager ];

  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    users.alice = import ./home.nix;
    extraSpecialArgs = { inherit inputs; };
  };
}
```

### nix-darwin Integration

```nix
{
  imports = [ inputs.home-manager.darwinModules.home-manager ];

  home-manager = {
    useGlobalPkgs = true;
    useUserPackages = true;
    users.alice = import ./home.nix;
  };
}
```

### Writing Reusable Modules

```nix
# mymodule.nix — a reusable HM module
{ config, lib, pkgs, ... }:
{
  options.mymodule = {
    enable = lib.mkEnableOption "my module";
    fontSize = lib.mkOption {
      type = lib.types.int;
      default = 12;
      description = "Font size for terminal emulators";
    };
  };

  config = lib.mkIf config.mymodule.enable {
    programs.alacritty.settings.font.size = config.mymodule.fontSize;
    programs.kitty.settings.font_size = toString config.mymodule.fontSize;
  };
}
```

---

## Configuration Extension Points

### `specialisation` — Named Config Variants
(`modules/misc/specialisation.nix`)

```nix
specialisation.gaming = {
  configuration = {
    services.picom.enable = false;
    home.packages = [ pkgs.steam ];
  };
};
```

Switch with: `home-manager switch --specialisation gaming`

### `targets.genericLinux` — Non-NixOS Linux

```nix
targets.genericLinux.enable = true;
# Enables XDG_DATA_DIRS, profile.d hooks for non-NixOS distros
```

### `nixpkgs` Configuration

```nix
nixpkgs.config.allowUnfree = true;
nixpkgs.overlays = [ (final: prev: { ... }) ];
```
