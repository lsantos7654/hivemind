# plasma-manager: APIs and Interfaces

## Entry Point

All plasma-manager options are under `programs.plasma` in Home Manager configuration. The module must be enabled with:

```nix
programs.plasma.enable = true;
```

Source: `modules/default.nix:25`

---

## Core Options

### `programs.plasma.enable`
Type: `bool` (mkEnableOption)
Enables the plasma-manager module. All other options are no-ops unless this is `true`.

### `programs.plasma.overrideConfig`
Type: `bool`, default: `false`
Source: `modules/files.nix:121`

When `true`, plasma-manager deletes a predefined list of KDE config files on each Home Manager activation and recreates them from scratch. This gives fully declarative behavior but will wipe any settings made outside plasma-manager.

### `programs.plasma.immutableByDefault`
Type: `bool`, default: `false`
Source: `modules/files.nix:146`

When `true`, all keys written by plasma-manager receive the `[$i]` immutable marker, preventing KDE settings UI from overwriting them.

### `programs.plasma.resetFiles`
Type: `list of str`, default: computed from `overrideConfig`
Source: `modules/files.nix:133`

Explicit list of config file names (relative to `$XDG_CONFIG_HOME`) to delete on activation.

### `programs.plasma.resetFilesExclude`
Type: `list of str`, default: `[]`
Files to exclude from deletion even if listed in `resetFiles`.

---

## Low-Level Config File Options

Source: `modules/files.nix:93–148`

These options accept nested attribute sets of the form `file.group.key = value`.

### `programs.plasma.configFile`
Files relative to `$XDG_CONFIG_HOME` (typically `~/.config`).

```nix
programs.plasma.configFile = {
  kwinrc."org.kde.kdecoration2".ButtonsOnLeft = "SF";
  kwinrc.Desktops.Number = {
    value = 8;
    immutable = true;   # adds [$i] marker
  };
  kscreenlockerrc."Greeter/Wallpaper/org.kde.potd/General".Provider = "bing";
};
```

### `programs.plasma.dataFile`
Files relative to `$XDG_DATA_HOME` (typically `~/.local/share`).

### `programs.plasma.file`
Files relative to `$HOME`.

### Setting Value Types
Source: `lib/types.nix`

Each value can be:
- A plain scalar (`bool`, `int`, `float`, `str`)
- An attribute set with advanced options:

```nix
{
  value = "myvalue";       # the actual value (required)
  immutable = true;        # adds [$i] → KDE won't let UI change it
  shellExpand = false;     # adds [$e] → shell-expands the value
  persistent = false;      # when overrideConfig enabled, don't reset this key
  escapeValue = true;      # apply KDE escape encoding (default true)
}
```

---

## Workspace Options

Source: `modules/workspace.nix:132–356`

```nix
programs.plasma.workspace = {
  lookAndFeel = "org.kde.breezedark.desktop";   # Global theme package ID
  theme = "breeze-dark";                          # Plasma style
  colorScheme = "BreezeDark";                     # Color scheme name
  iconTheme = "Papirus-Dark";                     # Icon theme
  widgetStyle = "breeze";                         # Qt widget style
  soundTheme = "freedesktop";

  cursor = {
    theme = "Bibata-Modern-Ice";
    size = 32;
    cursorFeedback = "Bouncing";   # "Bouncing" | "Blinking" | "Static" | "None"
    taskManagerFeedback = true;
    animationTime = 5;
  };

  wallpaper = "${pkgs.kdePackages.plasma-workspace-wallpapers}/share/wallpapers/Kay/.../1080x1920.png";
  # OR:
  wallpaperSlideShow = { path = "/path/to/wallpapers"; interval = 300; };
  # OR:
  wallpaperPictureOfTheDay = { provider = "apod"; updateOverMeteredConnection = false; };
  # OR:
  wallpaperPlainColor = "0,64,174,256";   # R,G,B,A string
  # OR:
  wallpaperCustomPlugin = {
    plugin = "luisbocanegra.smart.video.wallpaper.reborn";
    config.General.VideoUrls = ''[{"filename":"file:///path/to/video.mp4","enabled":true}]'';
  };

  wallpaperFillMode = "stretch";  # "stretch" | "scaled" | "cropped" | "centered" | "tiled" | "keepAspectRatio"
  wallpaperBackground = { blur = true; };  # or { color = "219,99,99"; }

  splashScreen = { theme = "None"; };  # theme = "None" disables splash
  windowDecorations = {
    library = "org.kde.kwin.aurorae";
    theme = "__aurorae__svg__CatppuccinMocha-Modern";
  };

  clickItemTo = "open";   # "open" | "select"
  enableMiddleClickPaste = false;
  tooltipDelay = 5;
};
```

**Constraint**: Only one of `wallpaper`, `wallpaperSlideShow`, `wallpaperPictureOfTheDay`, `wallpaperPlainColor`, `wallpaperCustomPlugin` may be set at a time.

---

## Panel Options

Source: `modules/panels.nix:55–208`

```nix
programs.plasma.panels = [
  {
    location = "bottom";           # "top" | "bottom" | "left" | "right" | "floating"
    height = 44;
    alignment = "center";          # "left" | "center" | "right"
    hiding = "autohide";           # "none" | "autohide" | "dodgewindows" | "windowsgobelow" | ...
    floating = true;               # floating panel style
    opacity = "adaptive";          # "adaptive" | "opaque" | "translucent"
    lengthMode = "fill";           # "fit" | "fill" | "custom"
    minLength = 1000;
    maxLength = 1600;
    offset = 0;
    screen = 0;                    # int, list of ints, or "all"
    extraSettings = "panel.writeConfig(\"SomeKey\", \"value\");";

    widgets = [
      # Plain string: widget with default config
      "org.kde.plasma.marginsseparator"

      # Generic: name + raw config attrset
      {
        name = "org.kde.plasma.kickoff";
        config.General.icon = "nix-snowflake-white";
        extraConfig = "(w) => { w.currentConfigGroup = [\"General\"]; }";
      }

      # High-level typed widget config (preferred):
      { kickoff = { sortAlphabetically = true; icon = "nix-snowflake-white"; }; }
      { digitalClock = { calendar.firstDayOfWeek = "sunday"; time.format = "12h"; }; }
      { systemTray.items = { shown = ["org.kde.plasma.battery"]; hidden = ["org.kde.plasma.volume"]; }; }
      { iconTasks.launchers = ["applications:org.kde.dolphin.desktop"]; }
    ];
  }
];
```

---

## KWin Options

Source: `modules/kwin.nix:137–701`

```nix
programs.plasma.kwin = {
  titlebarButtons.left = [ "on-all-desktops" "keep-above-windows" ];
  titlebarButtons.right = [ "minimize" "maximize" "close" ];

  virtualDesktops = {
    number = 4;
    names = [ "Work" "Chat" "Media" "Games" ];
    rows = 2;
  };

  borderlessMaximizedWindows = true;
  edgeBarrier = 0;       # 0 disables edge barriers
  cornerBarrier = false;

  nightLight = {
    enable = true;
    mode = "times";      # "automatic" | "constant" | "location" | "times"
    temperature = { day = 6500; night = 4000; };
    time = { morning = "06:30"; evening = "20:00"; };
    transitionTime = 30;
  };

  tiling = {
    padding = 4;
    layout = {
      id = "cf5c25c2-4217-4193-add6-b5971cb543f2";
      tiles = { layoutDirection = "horizontal"; tiles = [ { width = 0.5; } { width = 0.5; } ]; };
    };
  };

  effects = {
    blur = { enable = true; strength = 5; noiseStrength = 8; };
    wobblyWindows.enable = true;
    minimization.animation = "magiclamp";  # "squash" | "magiclamp" | "off"
    desktopSwitching.animation = "slide";  # "fade" | "slide" | "off"
    windowOpenClose.animation = "glide";   # "fade" | "glide" | "scale" | "off"
    dimInactive.enable = false;
    translucency.enable = false;
  };

  scripts.polonium = {
    enable = true;
    settings = {
      layout.engine = "binaryTree";
      borderVisibility = "noBorderAll";
      maximizeSingleWindow = true;
    };
  };
};
```

---

## Shortcuts and Hotkeys

Source: `modules/shortcuts.nix`, `modules/hotkeys.nix`

```nix
programs.plasma.shortcuts = {
  ksmserver."Lock Session" = [ "Screensaver" "Meta+Ctrl+Alt+L" ];
  kwin."Switch Window Down" = "Meta+J";
  kwin."Expose" = "Meta+,";
  "services/org.kde.konsole.desktop"."_launch" = "Ctrl+Alt+T";
};

programs.plasma.hotkeys.commands."launch-konsole" = {
  name = "Launch Konsole";
  key = "Meta+Alt+K";
  command = "konsole";
};
```

---

## Fonts

Source: `modules/fonts.nix`

```nix
programs.plasma.fonts = {
  general = { family = "JetBrains Mono"; pointSize = 12; };
  fixedWidth = { family = "JetBrains Mono"; pointSize = 11; };
  small = { family = "Noto Sans"; pointSize = 9; };
  toolbar = { family = "Noto Sans"; pointSize = 10; };
  menu = { family = "Noto Sans"; pointSize = 10; };
  windowTitle = { family = "Noto Sans"; pointSize = 10; bold = true; };
};
```

---

## Window Rules

Source: `modules/window-rules.nix`

```nix
programs.plasma.window-rules = [
  {
    description = "Force Dolphin borderless and maximized";
    match = {
      window-class = { value = "dolphin"; type = "substring"; };
      window-types = [ "normal" ];
    };
    apply = {
      noborder = { value = true; apply = "force"; };
      maximizehoriz = true;   # apply defaults to "apply-initially"
      maximizevert = true;
    };
  }
];
```

---

## Desktop Widgets

Source: `modules/desktop.nix`

```nix
programs.plasma.desktop.widgets = [
  {
    plasmusicToolbar = {
      position = { horizontal = 51; vertical = 100; };
      size = { width = 250; height = 250; };
    };
  }
];

programs.plasma.desktop.icons = {
  arrangement = "leftToRight";   # "leftToRight" | "topToBottom"
  sortingMethod = "name";        # "manual" | "name" | "size" | "date" | "type"
  size = 2;
  spacing = "medium";
};

programs.plasma.desktop.mouseActions = {
  leftButton = "applicationLauncher";
  rightButton = "contextMenu";
  middleButton = "paste";
};
```

---

## Power Management

Source: `modules/powerdevil.nix`

```nix
programs.plasma.powerdevil = {
  AC = {
    powerButtonAction = "lockScreen";
    autoSuspend = { action = "shutDown"; idleTimeout = 1000; };
    turnOffDisplay = { idleTimeout = 1000; idleTimeoutWhenLocked = "immediately"; };
  };
  battery = {
    powerButtonAction = "sleep";
    whenSleepingEnter = "standbyThenHibernate";
  };
  lowBattery = {
    whenLaptopLidClosed = "hibernate";
  };
};
```

---

## Screen Locker

Source: `modules/kscreenlocker.nix`

```nix
programs.plasma.kscreenlocker = {
  lockOnResume = true;
  timeout = 10;   # minutes
  appearance = {
    wallpaper = "/path/to/wallpaper.png";
    wallpaperSlideShow = { path = "/path/to/dir"; interval = 600; };
  };
};
```

---

## Startup Scripts (Advanced)

Source: `modules/startup.nix:105–135`

Users can inject custom scripts:

```nix
programs.plasma.startup.startupScript."my-custom-script" = {
  text = ''
    qdbus org.kde.KWin /KWin reconfigure
  '';
  priority = 4;          # 0–8, lower runs earlier
  restartServices = [ "plasma-plasmashell" ];
  runAlways = false;     # default: skip if unchanged
};

# Plasma desktop scripts (JavaScript, evaluated via qdbus PlasmaShell.evaluateScript)
programs.plasma.startup.desktopScript."my-widget-config" = {
  text = ''
    let allDesktops = desktops();
    for (const desktop of allDesktops) {
      desktop.wallpaperPlugin = "org.kde.image";
    }
  '';
  priority = 5;
  preCommands = "echo 'before'";
  postCommands = "echo 'after'";
};
```

---

## KDE Application Options

### Konsole

```nix
programs.plasma.konsole = {
  defaultProfile = "MyProfile";
  profiles.MyProfile = {
    name = "MyProfile";
    colorScheme = "Breeze";
    font = { family = "JetBrains Mono"; pointSize = 12; };
    command = "/run/current-system/sw/bin/fish";
  };
};
```

### Kate

```nix
programs.plasma.kate = {
  sessions.mySession = {
    documents = [ "/path/to/file.txt" ];
  };
  plugins.lsp.enable = true;
};
```

### Okular

```nix
programs.plasma.okular = {
  general.smoothScrolling = true;
};
```

### Ghostwriter

```nix
programs.plasma.ghostwriter = {
  general.autoSave = true;
};
```

---

## Integration Patterns

### Combining High-Level and Low-Level Options

High-level options (like `programs.plasma.workspace.colorScheme`) internally set `programs.plasma.configFile` entries. You can use both in the same config; `lib.mkMerge` handles merging:

```nix
programs.plasma = {
  workspace.colorScheme = "BreezeDark";  # high-level

  # Also directly write to config files for options not yet in plasma-manager:
  configFile.kdeglobals.General.AccentColor = "61,174,233";
};
```

### Third-Party Widget Auto-Packaging

Some widgets automatically add their packages to `home.packages` when declared. For example, using `{ kickerdash = {}; }` in a panel's widgets list does NOT auto-install; but using `{ name = "luisbocanegra.panel.colorizer"; }` will add `plasma-panel-colorizer` to `home.packages`.

Widgets with auto-packaging (source: `modules/panels.nix:17–24`):
- `com.github.antroids.application-title-bar` → `application-title-bar`
- `plasmusic-toolbar` → `plasmusic-toolbar`
- `luisbocanegra.panel.colorizer` → `plasma-panel-colorizer`
- `org.kde.windowbuttons` → `kdePackages.applet-window-buttons6`
- `org.dhruv8sh.kara` → `kara`
- `luisbocanegra.panelspacer.extended` → `plasma-panel-spacer-extended`

### Nested Config Group Separator

For deeply nested KDE config groups, use `/` as a separator in the key name:

```nix
programs.plasma.configFile.kscreenlockerrc = {
  "Greeter/Wallpaper/org.kde.potd/General".Provider = "bing";
  # Writes to [Greeter][Wallpaper][org.kde.potd][General] → Provider=bing
};
```

Source: `examples/home.nix:296–299`
