# Kröhnkite — Code Structure

## Annotated Directory Tree

```
krohnkite/
├── src/                          # TypeScript source (compiled to krohnkite.js)
│   ├── common.ts                 # Shared types, interfaces, enums, globals
│   ├── engine/                   # Core tiling engine (platform-agnostic)
│   │   ├── engine.ts             # TilingEngine: main tiling logic class
│   │   ├── control.ts            # TilingController: event-to-action translator
│   │   ├── enginecontext.ts      # EngineContext: bridge between engine and driver
│   │   ├── gaps.ts               # Gap configuration parsing and management
│   │   ├── layoutstore.ts        # LayoutStore/LayoutStoreEntry: per-surface layout state
│   │   ├── window.ts             # WindowClass: engine-level window abstraction
│   │   └── windowstore.ts        # WindowStore: ordered window list management
│   ├── layouts/                  # Layout algorithm implementations
│   │   ├── tilelayout.ts         # TileLayout: DWM-style master/stack (default)
│   │   ├── monoclelayout.ts      # MonocleLayout: full-screen single window cycle
│   │   ├── threecolumnlayout.ts  # ThreeColumnLayout: three-column tiling
│   │   ├── spirallayout.ts       # SpiralLayout: Fibonacci/spiral tiling
│   │   ├── quarterlayout.ts      # QuarterLayout: 2x2 grid tiling
│   │   ├── stackedlayout.ts      # StackedLayout: horizontal/vertical stacking
│   │   ├── columns.ts            # ColumnsLayout: multi-column with configurable layers
│   │   ├── column.ts             # Column: single column primitive used by ColumnsLayout
│   │   ├── spreadlayout.ts       # SpreadLayout: cascade-like spread
│   │   ├── floatinglayout.ts     # FloatingLayout: disables tiling (all windows float)
│   │   ├── stairlayout.ts        # StairLayout: staircase/waterfall arrangement
│   │   ├── btreelayout.ts        # BinaryTreeLayout: binary space partitioning
│   │   ├── cascadelayout.ts      # CascadeLayout: overlapping cascade
│   │   ├── layoutpart.ts         # ILayoutPart and composable primitives
│   │   └── layoututils.ts        # Utility functions shared by layouts
│   ├── dock/                     # Docked window management
│   │   ├── dock.ts               # Dock: represents a docked window configuration
│   │   ├── dockcommon.ts         # DockPosition enum, IDock/IDockCfg interfaces
│   │   ├── dockdefaultcfg.ts     # DefaultDockCfg: parses default dock config from CONFIG
│   │   ├── dockentry.ts          # DockEntry: maps a window class to dock config
│   │   ├── dockparseusercfg.ts   # Parses user-supplied dock config strings
│   │   ├── dockslot.ts           # DockSlot: represents one edge slot for a docked window
│   │   └── dockstore.ts          # DockStore: manages all docked windows and rendering
│   ├── driver/                   # KWin-specific driver (platform integration)
│   │   ├── kwindriver.ts         # KWinDriver: main IDriverContext implementation
│   │   ├── kwinconfig.ts         # KWinConfig: reads all settings via KWIN.readConfig()
│   │   ├── kwinwindow.ts         # KWinWindow: wraps KWin Window object as IDriverWindow
│   │   ├── kwinsurface.ts        # KWinSurface/KWinSurfaceStore: screen+desktop+activity surface
│   │   ├── kwindbus.ts           # KWinDBus: D-Bus calls for mouse pointer movement
│   │   └── kwinsettimeout.ts     # setTimeout wrapper for KWin scripting environment
│   ├── extern/                   # TypeScript type declarations for KWin/Qt APIs
│   │   ├── kwin.d.ts             # Main KWin scripting API types
│   │   ├── window.kwin.d.ts      # KWin Window interface
│   │   ├── workspace.kwin.d.ts   # KWin Workspace interface
│   │   ├── tile.kwin.d.ts        # KWin Tile interface
│   │   ├── output.kwin.d.ts      # KWin Output (screen) interface
│   │   ├── virtualdesktop.kwin.d.ts # KWin VirtualDesktop interface
│   │   ├── qt.d.ts               # Qt types (QML interop)
│   │   ├── plasma.d.ts           # Plasma-specific types
│   │   ├── global.d.ts           # Global utility function declarations
│   │   └── enums.ts              # Shared enum definitions (e.g. WindowLayer)
│   └── util/                     # Utility classes and helpers
│       ├── rect.ts               # Rect: rectangle with geometric operations
│       ├── rectdelta.ts          # RectDelta: difference between two rectangles
│       ├── func.ts               # Pure utility functions (clip, slide, wrapIndex, etc.)
│       ├── log.ts                # Logging: granular debug logging system
│       ├── validation.ts         # Input validation helpers
│       ├── windrose.ts           # WindRose: directional focus/navigation utilities
│       ├── wrappermap.ts         # WrapperMap: maps KWin objects to engine objects
│       ├── kwinutil.ts           # KWin-specific utilities
│       └── debugwin.ts           # Debug window information helpers
├── res/                          # Runtime resources (QML, UI, config)
│   ├── main.qml                  # QML entry point: loads script, wires signals
│   ├── shortcuts.qml             # QML: registers all keyboard shortcuts with KWin
│   ├── dbus.qml                  # QML: provides D-Bus interface for mouse movement
│   ├── popup.qml                 # QML: notification popup display
│   ├── main.js                   # JavaScript loader that bootstraps the script
│   ├── config.ui                 # Qt Designer UI file for the settings dialog
│   ├── config.xml                # KConfigXT schema defining all config keys/defaults
│   └── metadata.json             # KWin package metadata ($VER, $REV substituted at build)
├── tools/                        # Developer and installer tools
│   ├── autoinstall/              # Python auto-install daemon scripts
│   │   ├── install.py            # Installs the package
│   │   ├── uninstall.py          # Uninstalls the package
│   │   ├── autoinstalld.py       # Daemon that watches for changes and auto-installs
│   │   ├── lib.py                # Shared autoinstall library functions
│   │   └── pyproject.toml        # Python project metadata
│   └── legacy/                   # Legacy scripts (kept for reference)
│       ├── testenv-docker_1.sh   # Old Docker test environment setup
│       ├── shortcut_1.py         # Old shortcut registration script
│       └── load-script_1.sh      # Old script loader
├── translations/                 # Localization files
│   ├── translations.po           # Base/template .po file
│   ├── russian.po                # Russian translation
│   ├── chinese.po                # Chinese translation
│   └── locale/                   # Compiled .mo files
│       ├── ru/LC_MESSAGES/krohnkite.mo
│       └── zh/LC_MESSAGES/krohnkite.mo
├── img/                          # Documentation images
│   ├── screenshot.png            # Main screenshot
│   └── conf.png                  # Configuration screenshot
├── .github/ISSUE_TEMPLATE/       # GitHub issue templates
├── Makefile                      # Legacy Makefile build system
├── taskfile.yaml                 # Primary go-task build system
├── package.json                  # npm package (TypeScript dev dependency)
├── tsconfig.json                 # TypeScript compiler configuration
├── tslint.json                   # TSLint configuration
├── package-lock.json             # npm lockfile
├── LICENSE                       # MIT License
└── README.md                     # Installation, usage, and configuration docs
```

## Module and Package Organization

The source is written in TypeScript but compiled to a single concatenated JavaScript file (`krohnkite.js`) because KWin scripts must be a single file — there is no module system at runtime. This means:

- All TypeScript classes/interfaces/functions are in **global scope** after compilation.
- `tsconfig.json` is configured for concatenation (`outFile` mode).
- Files must be loaded in dependency order by TypeScript (managed via `/// <reference>` directives or tsconfig `files`/`include` ordering).

## Main Source Directories and Their Purposes

### `src/common.ts` — Shared Foundation
Defines all shared types and interfaces used across the entire codebase:
- `WindowState` constant object (Unmanaged, NativeFullscreen, NativeMaximized, Floating, Maximized, Tiled, TiledAfloat, Undecided, Dragging, Docked)
- `Shortcut` constant object with all shortcut names
- `ILayout`, `ILayoutClass`, `ILayoutPart` interfaces
- `IDriverContext`, `IDriverWindow`, `ISurface`, `ISurfaceStore` interfaces
- `IConfig` interface with all configuration fields
- `IGaps`, `ISize`, `IFloatInit` interfaces
- `LogModules`, `LogPartitions` for the logging system
- Global singletons: `CONFIG`, `LOG`, `DBUS`

### `src/engine/` — Core Tiling Logic
The heart of the script. Platform-agnostic tiling logic:
- **`TilingEngine`**: Maintains `LayoutStore`, `WindowStore`, and `DockStore`. Provides methods for all tiling operations (arrange, manage, unmanage, focusOrder, focusDir, swapOrder, swapDirection, toggleFloat, setMaster, cycleLayout, setLayout, resizeWindow, etc.).
- **`TilingController`**: Handles all event callbacks from the driver (onWindowAdded, onWindowRemoved, onWindowMoveOver, onWindowResize, onShortcut, etc.) and delegates to `TilingEngine`.
- **`LayoutStore`**: Per-surface layout state. Keys layouts by a surface ID composed of output + activity + virtual desktop. Lazily instantiates layout objects via `CONFIG.layoutFactories`.
- **`WindowStore`**: An ordered list of `WindowClass` objects. Operations: push, unshift, beside_first, remove, move, swap, setMaster.
- **`WindowClass`**: Wraps `IDriverWindow`. Tracks state, geometry commitment, float geometry, dock assignment, and timestamps.
- **`EngineContext`**: A thin wrapper combining `IDriverContext` and `TilingEngine` for passing to layout `apply()` and `handleShortcut()` methods.

### `src/layouts/` — Layout Algorithms
Each layout implements `ILayout`:
- `apply(ctx, tileables, area, gap)`: Positions all tileable windows within the given area.
- `adjust?(area, tiles, basis, delta, gap)`: Handles mouse-resize adjustments.
- `handleShortcut?(ctx, input, data)`: Handles layout-specific keyboard shortcuts (e.g., increase/decrease master count, rotate).
- `drag?(ctx, draggingRect, window, workingArea)`: Optional drag-to-swap support.

Layouts are composed from `ILayoutPart` primitives in `layoutpart.ts`:
- `FillLayoutPart`: Places all tiles in the same area (monocle-like).
- `HalfSplitLayoutPart<L, R>`: Splits area into primary/secondary halves with configurable ratio, rotation angle, and primary size.
- `StackLayoutPart`: Divides area among multiple tiles with equal splits (with gap).
- `RotateLayoutPart`: Wraps another part and applies 90/180/270-degree rotations.

### `src/dock/` — Docked Window System
Windows can be "docked" to screen edges. The dock system:
- Maintains a priority-ordered list of docked windows per screen edge.
- Reduces the tiling area (`workingArea`) around docked windows.
- Supports horizontal and vertical docking with configurable width/height percentages, gaps, and alignment.
- Config parsed from `CONFIG.dockWindowClassConfig` and `CONFIG.dockSurfacesConfig`.

### `src/driver/` — KWin Integration
- **`KWinDriver`**: Implements `IDriverContext`. Connects KWin workspace signals to `TilingController`. Manages window tracking via `WrapperMap`. Handles surface creation and lifecycle.
- **`KWinConfig`**: Reads all settings at startup via `KWIN.readConfig()`. Constructs layout factories with capacity parameters.
- **`KWinWindow`**: Wraps `Window` (KWin type). Computes `shouldIgnore`/`shouldFloat` based on class, title, role rules. Commits geometry to KWin.
- **`KWinSurface`**: Represents a unique (output × activity × virtualDesktop) combination. Manages `capacity` overrides and `ignore` flag.

### `src/util/` — Utilities
- **`Rect`**: Core geometry class (x, y, width, height) with `gap()`, `equals()`, `clone()`, `subtract()`, `includesPoint()`.
- **`RectDelta`**: Represents change in rectangle edges (east, west, north, south deltas). Used for mouse-resize layout adjustment.
- **`func.ts`**: `clip()`, `slide()`, `wrapIndex()`, `overlap()`, `toRect()`, `separate()`, `getMethodName()`, `getTime()`.
- **`log.ts`**: `Logging` class with per-module enable/disable and window-class filtering.
- **`wrappermap.ts`**: `WrapperMap<K, V>` — maps KWin Window objects to `WindowClass` instances.

## Key Files and Their Roles

| File | Role |
|------|------|
| `src/common.ts` | All shared types, interfaces, global declarations |
| `src/engine/engine.ts` | Core tiling logic, `TilingEngine` class |
| `src/engine/control.ts` | Event handler, `TilingController` class |
| `src/driver/kwindriver.ts` | KWin integration, signal wiring, `IDriverContext` |
| `src/driver/kwinconfig.ts` | Configuration reader, `KWinConfig` class |
| `src/driver/kwinwindow.ts` | Window wrapper, filter logic |
| `src/layouts/tilelayout.ts` | Default DWM-style master/stack layout |
| `src/layouts/layoutpart.ts` | Composable layout building blocks |
| `res/main.qml` | QML entry point, signal connections |
| `res/shortcuts.qml` | Keyboard shortcut registration |
| `res/config.xml` | All configuration keys and defaults |
| `taskfile.yaml` | Primary build system |
