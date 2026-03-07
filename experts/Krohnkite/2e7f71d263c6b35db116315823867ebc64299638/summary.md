# Kröhnkite — Summary

## Repository Purpose and Goals

Kröhnkite is a dynamic tiling window manager extension (KWin Script) for KDE Plasma 6 / KWin 6. It is inspired by [dwm](https://dwm.suckless.org/) from the suckless project and aims to bring automatic, dynamic window tiling to KDE's window manager while remaining fully integrated into KWin's existing feature set.

The core goal is to automatically arrange open windows into non-overlapping tile configurations ("tiling layouts") so users never have to manually position or resize windows. Users can switch layouts, cycle through windows with keyboard shortcuts, and configure per-screen or per-desktop default layouts.

## Key Features and Capabilities

- **Dynamic tiling**: Windows are automatically arranged when created, destroyed, or moved. No manual placement required.
- **Multiple layout algorithms**: 12 layouts are bundled — Tile (DWM-style master/stack), Monocle (full-screen cycle), ThreeColumn, Spiral, Quarter, Stacked, Columns, Spread, Floating, Stair, BinaryTree, and Cascade.
- **Floating windows**: Individual windows can be toggled between tiled and floating mode.
- **Docked windows**: A unique "Dock" feature allows pinning windows to screen edges (top/bottom/left/right), similar to a taskbar or side panel, shrinking the tiling area around them.
- **Multi-screen support**: Full multi-monitor support with per-screen layout assignment.
- **Activities and Virtual Desktops**: Layouts can be maintained independently per activity and/or per virtual desktop (controlled by `layoutPerActivity` and `layoutPerDesktop` config options).
- **Screen capacity management**: Limit how many tiled windows appear on a surface; excess windows float or move to another screen.
- **Gap configuration**: Configurable screen edge gaps (top, left, right, bottom) and between-tile gaps, with per-surface override.
- **Window filtering/rules**: Ignore or float windows by class name, title, or role. Windows that don't fit their minimum/maximum size constraints can be automatically floated.
- **Mouse dragging**: Dragging a tiled window swaps it with the target window, or converts it to floating.
- **Keyboard shortcuts**: Full keyboard control including focus navigation (directional and cyclic), swap/move, grow/shrink, layout cycling and direct selection, master promotion, and surface capacity adjustment.
- **KrohnkiteMeta mode**: A "meta key" modifier system allowing users to remap shortcuts into a secondary mode triggered by a special hotkey.
- **D-Bus integration**: Optional mouse-pointer-follows-focus via D-Bus calls.
- **Localization**: Russian and Chinese translations bundled.
- **Debug logging**: Granular logging system for diagnosing window management behavior.

## Primary Use Cases and Target Audience

Kröhnkite targets KDE Plasma 6 power users who want efficient keyboard-driven window management without leaving the KDE ecosystem. It is particularly useful for:

- Developers, sysadmins, and power users who prefer tiling WM workflows but want to stay on KDE Plasma.
- Multi-monitor setups requiring per-screen layout management.
- Users who want to mix tiling and floating windows on the same desktop.
- Users migrating from tiling WMs like i3, dwm, or bspwm who want KDE features (notifications, system tray, Activities, etc.).

## High-Level Architecture Overview

Kröhnkite follows a clean **Model-View-Controller** / **layered** architecture:

1. **Driver Layer** (`src/driver/`): KWin-specific implementation. `KWinDriver` (implements `IDriverContext`) connects Qt/KWin signals to the engine, reads configuration via `KWinConfig`, manages surfaces (`KWinSurface`/`KWinSurfaceStore`), wraps KWin windows (`KWinWindow`), and handles D-Bus (`KWinDBus`).

2. **Engine Layer** (`src/engine/`): Platform-agnostic tiling logic. `TilingEngine` maintains state (`LayoutStore`, `WindowStore`, `DockStore`) and executes tiling operations (arrange, focus, swap, resize, manage/unmanage). `TilingController` translates events to engine calls.

3. **Layout Layer** (`src/layouts/`): Individual layout algorithms, all implementing `ILayout`. Composable via `ILayoutPart` primitives (`HalfSplitLayoutPart`, `StackLayoutPart`, `RotateLayoutPart`, `FillLayoutPart`).

4. **Dock Layer** (`src/dock/`): Manages "docked" windows pinned to screen edges, adjusting the working area available to the tiling engine.

5. **Utilities** (`src/util/`): `Rect`, `RectDelta`, geometric helpers, logging, validation, and `WrapperMap`.

6. **Extern Declarations** (`src/extern/`): TypeScript type definitions for KWin, Qt, and Plasma APIs (`kwin.d.ts`, `qt.d.ts`, `plasma.d.ts`, etc.).

7. **Resources** (`res/`): QML entry points (`main.qml`, `shortcuts.qml`, `dbus.qml`, `popup.qml`), configuration UI (`config.ui`, `config.xml`), and the JS loader (`main.js`).

The entire TypeScript source is compiled to a single `krohnkite.js` file, which is bundled into a `.kwinscript` zip package installable via KDE's `kpackagetool6`.

## Related Projects and Dependencies

- **KWin 6 / KDE Plasma 6**: Runtime environment. Kröhnkite is a KWin Script and requires KWin 6 (`X-Plasma-API-Minimum-Version: 6.0`).
- **Original Krohnkite**: The upstream project by Eon S. Jeon. This fork is maintained by Vjatcheslav V. Kolchkov at `https://codeberg.org/anametologin/Krohnkite`.
- **dwm**: Design inspiration for the master/stack tiling paradigm.
- **TypeScript**: All source code is TypeScript 5.x, compiled to JavaScript.
- **go-task**: Task runner used to orchestrate the build pipeline (`taskfile.yaml`).
- **7-zip (p7zip)**: Used to package the `.kwinscript` zip archive.
- **npm**: Node package manager for TypeScript compiler installation.
- **kpackagetool6**: KDE utility for installing/upgrading/removing KWin scripts.
