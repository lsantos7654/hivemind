# Kröhnkite — APIs and Interfaces

## Public APIs and Entry Points

Kröhnkite is a KWin Script (not a library), so its primary "API" surfaces are:

1. **The `ILayout` interface** — implement to create custom layouts
2. **The `IConfig` interface** — all configuration options
3. **The `Shortcut` enum** — all keyboard shortcuts
4. **The `WindowState` enum** — all window states
5. **The `IDriverContext` / `IDriverWindow` / `ISurface` interfaces** — platform abstraction
6. **The `TilingEngine` methods** — tiling operations
7. **Configuration keys** (`res/config.xml`) — user-facing settings

---

## Key Interfaces

### `ILayout` — Layout Algorithm Interface
**File**: `src/common.ts:356`

```typescript
interface ILayout {
  readonly capacity?: number | null;   // max tiled windows (null = unlimited)
  readonly description: string;        // display name shown in notifications

  // Required: position all tileables within area
  apply(ctx: EngineContext, tileables: WindowClass[], area: Rect, gap: number): void;

  // Optional: adjust layout when user mouse-resizes a tile
  adjust?(area: Rect, tiles: WindowClass[], basis: WindowClass,
          delta: RectDelta, gap: number): void;

  // Optional: handle layout-specific keyboard shortcuts
  handleShortcut?(ctx: EngineContext, input: Shortcut, data?: any): boolean;

  // Optional: handle drag-to-swap operations
  drag?(ctx: EngineContext, draggingRect: Rect, window: WindowClass,
        workingArea: Rect): boolean;

  toString(): string;
}

interface ILayoutClass {
  readonly id: string;               // unique string identifier
  new(capacity?: number | null): ILayout;
}
```

**Usage**: All built-in layouts implement `ILayout`. To add a custom layout, implement this interface and register it in `KWinConfig`'s `layoutsList` array (`src/driver/kwinconfig.ts:174`).

---

### `ILayoutPart` — Composable Layout Primitive
**File**: `src/layouts/layoutpart.ts:8`

```typescript
interface ILayoutPart {
  adjust(area: Rect, tiles: WindowClass[], basis: WindowClass,
         delta: RectDelta, gap: number): RectDelta;
  apply(area: Rect, tiles: WindowClass[], gap: number): Rect[];
}
```

Built-in implementations:
- `FillLayoutPart` — places all tiles at same position (monocle)
- `HalfSplitLayoutPart<L, R>` — splits area into primary/secondary, configurable ratio/angle
- `StackLayoutPart` — equal-split stack (horizontal or vertical)
- `RotateLayoutPart<T>` — wraps another part with 90° rotation steps

---

### `IDriverContext` — Platform Context Interface
**File**: `src/common.ts:319`

```typescript
interface IDriverContext {
  readonly backend: string;
  readonly currentSurfaces: ISurface[];
  readonly cursorPosition: [number, number] | null;

  currentSurface: ISurface;
  currentWindow: WindowClass | null;
  isMetaMode: boolean;

  setTimeout(func: () => void, timeout: number): void;
  showNotification(text: string): void;
  moveWindowsToScreen(windowsToScreen: [Output, WindowClass[]][]): void;
  moveToScreen(window: WindowClass, direction: Direction): boolean;
  moveToVDesktop(window: WindowClass, direction: Direction): boolean;
  focusSpecial(direction: Direction): boolean;
  focusNeighborWindow(direction: Direction, winTypes: WinTypes): Window | null | boolean;
  focusOutput(window: Window | null, direction: Direction, winTypes: WinTypes): boolean;
  focusVDesktop(window: Window | null, direction: Direction, winTypes: WinTypes): boolean;
  metaPushed(): void;
}
```

Implemented by `KWinDriver` (`src/driver/kwindriver.ts`).

---

### `ISurface` — Tiling Surface
**File**: `src/common.ts:305`

```typescript
interface ISurface {
  capacity: number | null;         // max tiled windows on this surface
  output: Output;                  // physical screen
  readonly id: string;
  readonly layoutId: string;       // key for LayoutStore
  readonly ignore: boolean;        // if true, all windows float on this surface
  readonly workingArea: Readonly<Rect>;
  readonly activity: string;
  readonly vDesktop: VirtualDesktop;

  next(): ISurface | null;         // next surface in cycle
  getParams(): [string, string, string]; // [outputName, activity, desktopName]
}
```

---

### `IConfig` — Configuration Interface
**File**: `src/common.ts:166`

All configuration fields accessed at runtime via the global `CONFIG` object. Key groups:

**Layouts:**
```typescript
tileLayoutInitialAngle: string;      // "0"|"1"|"2"|"3" → 0/90/180/270°
monocleMaximize: boolean;            // maximize single window in monocle
monocleMinimizeRest: boolean;        // minimize non-active in monocle
quarterLayoutReset: boolean;
columnsLayoutInitialAngle: string;
columnsBalanced: boolean;
columnsLayerConf: string[];
stairReverse: boolean;
layoutOrder: string[];               // ordered list of enabled layout IDs
layoutFactories: { [key: string]: () => ILayout }; // factory per layout ID
```

**Surfaces:**
```typescript
surfacesDefaultConfig: string[];     // per-surface capacity config strings
surfacesIsMoveWindows: boolean;      // auto-move windows to under-capacity screens
surfacesIsMoveOldestWindows: boolean;
```

**Geometry:**
```typescript
screenGapTop: number;
screenGapLeft: number;
screenGapBetween: number;
screenGapRight: number;
screenGapBottom: number;
gapsOverrideConfig: string[];        // per-surface gap override strings
limitTileWidthRatio: number;         // max tile width as ratio of screen height
```

**Behavior:**
```typescript
adjustLayout: boolean;               // resize layout on tile resize
adjustLayoutLive: boolean;           // resize live while dragging
directionalKeyMode: "dwm" | "focus";
focusNormalCfg: WinTypes;            // which window types directional focus considers
focusMetaCfg: WinTypes;
movePointerOnFocus: boolean;
metaConf: string[];                  // custom meta shortcut mappings
metaTimeout: number;                 // meta mode timeout in ms
metaIsToggle: boolean;
newWindowPosition: number;           // 0=end, 1=beginning, 2=beside master
```

**Rules:**
```typescript
ignoreClass: string[];               // window classes to never tile
ignoreTitle: string[];
ignoreRole: string[];
floatingClass: string[];             // window classes to float by default
floatingTitle: string[];
floatDefault: boolean;               // float all new windows by default
floatUtility: boolean;               // float utility-type windows
ignoreActivity: string[];
ignoreScreen: string[];
ignoreVDesktop: string[];
tileNothing: boolean;                // tile no windows (disable tiling)
tilingClass: string[];               // whitelist: only tile these classes
screenDefaultLayout: string[];       // per-screen default layout config strings
```

**Dock:**
```typescript
dockOrder: [number, number, number, number]; // priority order [left,top,right,bottom]
dockHHeight: number;     // horizontal dock height %
dockHWide: number;       // horizontal dock width %
dockHGap: number;
dockHEdgeGap: number;
dockHAlignment: number;
dockVHeight: number;     // vertical dock height %
dockVWide: number;       // vertical dock width %
dockSurfacesConfig: string[];
dockWindowClassConfig: string[];
```

**Options:**
```typescript
tiledWindowsLayer: WindowLayer;
floatedWindowsLayer: WindowLayer;
soleWindowDefaultProps: ISoleWindowProps; // behavior when only one tiled window
soleWindowOutputOverride: { [outputName: string]: ISoleWindowProps };
unfitGreater: boolean;   // float windows too large for their tile
unfitLess: boolean;      // float windows too small for their tile
notificationDuration: number;
layoutPerActivity: boolean;
layoutPerDesktop: boolean;
noTileBorder: boolean;
keepTilingOnDrag: boolean;
preventMinimize: boolean;
preventProtrusion: boolean;
floatSkipPager: boolean;
floatInit: IFloatInit | null; // initial float geometry settings
```

---

## Key Classes

### `TilingEngine` — Core Engine
**File**: `src/engine/engine.ts:22`

```typescript
class TilingEngine {
  public layouts: LayoutStore;
  public windows: WindowStore;
  public docks: DockStore;

  // Window lifecycle
  public manage(window: WindowClass): void;
  public unmanage(window: WindowClass): void;

  // Arrangement
  public arrange(ctx: IDriverContext, reason: string): void;
  public arrangeScreen(ctx: IDriverContext, screenData: ScreenData, reason: string): void;
  public enforceSize(ctx: IDriverContext, window: WindowClass): void;

  // Focus navigation
  public focusOrder(ctx: IDriverContext, step: -1 | 1): void;
  public focusDir(ctx: IDriverContext, dir: Direction): boolean;

  // Window operations
  public swapOrder(window: WindowClass, step: -1 | 1): void;
  public swapDirection(ctx: IDriverContext, direction: Direction, window: WindowClass): boolean;
  public swapDirOrMoveFloat(ctx: IDriverContext, dir: Direction): boolean;
  public moveFloat(window: WindowClass, dir: Direction): void;
  public toggleFloat(window: WindowClass): void;
  public toggleDock(window: WindowClass): void;
  public floatAll(ctx: IDriverContext, srf: ISurface): void;
  public setMaster(window: WindowClass): void;

  // Resize
  public resizeWindow(window: WindowClass, dir: "east"|"west"|"south"|"north", step: -1|1): void;
  public resizeFloat(window: WindowClass, dir: string, step: -1|1): void;
  public resizeTile(window: WindowClass, dir: string, step: -1|1): void;
  public adjustLayout(basis: WindowClass): void;
  public adjustDock(basis: WindowClass): void;

  // Layout management
  public cycleLayout(ctx: IDriverContext, step: 1 | -1): void;
  public setLayout(ctx: IDriverContext, layoutClassID: string): void;
  public handleLayoutShortcut(ctx: IDriverContext, input: Shortcut, data?: any): boolean;
  public handleDockShortcut(ctx: IDriverContext, window: WindowClass, input: Shortcut): boolean;

  // Surface capacity
  public raiseSurfaceCapacity(ctx: IDriverContext): number | null;
  public lowerSurfaceCapacity(ctx: IDriverContext): number | null;
  public ResetSurfaceCapacity(ctx: IDriverContext): number | null;
}
```

### `TilingController` — Event Handler
**File**: `src/engine/control.ts:15`

```typescript
class TilingController {
  public engine: TilingEngine;

  // Event handlers (called by KWinDriver)
  public onSurfaceUpdate(ctx: IDriverContext): void;
  public onCurrentActivityChanged(ctx: IDriverContext): void;
  public onCurrentSurfaceChanged(ctx: IDriverContext): void;
  public onWindowAdded(ctx: IDriverContext, window: WindowClass): void;
  public onWindowRemoved(ctx: IDriverContext, window: WindowClass): void;
  public onWindowMove(window: WindowClass): void;
  public onWindowDragging(ctx: IDriverContext, window: WindowClass, windowRect: Rect): void;
  public onWindowMoveOver(ctx: IDriverContext, window: WindowClass): void;
  public onWindowResize(ctx: IDriverContext, window: WindowClass): void;
  public onWindowResizeOver(ctx: IDriverContext, window: WindowClass): void;
  public onWindowMaximizeChanged(ctx: IDriverContext, window: WindowClass): void;
  public onWindowGeometryChanged(ctx: IDriverContext, window: WindowClass): void;
  public onWindowChanged(ctx: IDriverContext, window: WindowClass | null, comment?: string): void;
  public onWindowFocused(ctx: IDriverContext, window: WindowClass): void;
  public onDesktopsChanged(ctx: IDriverContext, window: WindowClass): void;
  public onWindowSkipPagerChanged(ctx: IDriverContext, window: WindowClass, skipPager: boolean): void;
  public onShortcut(ctx: IDriverContext, input: Shortcut, data?: any): void;
}
```

### `WindowClass` — Window Abstraction
**File**: `src/engine/window.ts:8`

```typescript
class WindowClass {
  // Static helpers
  static isTileableState(state: WindowState): boolean;
  static isTiledState(state: WindowState): boolean;
  static isFloatingState(state: WindowState): boolean;
  static isDockedState(state: WindowState): boolean;

  // Properties
  readonly id: string;
  readonly window: IDriverWindow;
  get state(): WindowState;       // computed, accounts for fullscreen/maximized override
  set state(value: WindowState);
  get isTileable(): boolean;
  get isTiled(): boolean;
  get isFloating(): boolean;
  get isDocked(): boolean;
  get actualGeometry(): Readonly<Rect>; // current KWin geometry
  get geometryDelta(): RectDelta | null;
  geometry: Rect;                 // desired geometry (set by layout)
  floatGeometry: Rect;            // geometry when floating
  timestamp: number;
  dock: IDock | null;

  // Methods
  commit(noBorder?: boolean): void;  // apply geometry to KWin
  forceSetGeometry(rect: Rect): void;
  moveMouseToFocus(): void;
}
```

### `Rect` — Geometry
**File**: `src/util/rect.ts:8`

```typescript
class Rect {
  constructor(x: number, y: number, width: number, height: number);
  get maxX(): number;
  get maxY(): number;
  get center(): [number, number];
  clone(): Rect;
  equals(other: Rect): boolean;
  gap(left: number, right: number, top: number, bottom: number): Rect;  // inset
  subtract(other: Rect): Rect;
  includesPoint(point: [number, number]): boolean;
}
```

---

## Shortcut Enum
**File**: `src/common.ts:47`

```typescript
const Shortcut = {
  FocusNext, FocusPrev,
  DWMLeft, DWMRight,
  FocusUp, FocusDown, FocusLeft, FocusRight,
  ShiftLeft, ShiftRight, ShiftUp, ShiftDown,
  SwapUp, SwapDown, SwapLeft, SwapRight,
  GrowWidth, GrowHeight, ShrinkWidth, ShrinkHeight,
  Increase, Decrease,
  ToggleFloat, ToggleFloatAll,
  SetMaster,
  NextLayout, PreviousLayout, SetLayout,
  Rotate, RotatePart,
  ToggleDock,
  RaiseSurfaceCapacity, LowerSurfaceCapacity,
  KrohnkiteMeta,
  MetaResetSurfaceCapacity,
  MetaFocusLeft, MetaFocusRight, MetaFocusUp, MetaFocusDown,
} as const;
```

---

## Configuration Options and Extension Points

### Screen Default Layout Format
**Config key**: `screenDefaultLayout` (comma-separated entries in config)
```
OutputName:ActivityId:VirtualDesktopName:layoutName
```
Examples:
- `HDMI-A-1:99a12h44-e9a6-1142-55eedaa7-3a922a15ab08::columns` — columns on HDMI-A-1, specific activity, all desktops
- `DP-2:spread` — spread on DP-2, all activities/desktops
- `:threecolumn` — threecolumn on all monitors (catch-all)

Layout names (case-insensitive, `layout` suffix optional): `tile`, `monocle`, `threecolumn`, `spread`, `stair`, `spiral`, `stacked`, `floating`, `btree`, `cascade`, `columns`, `quarter`

### Window Filter Format
**Config keys**: `ignoreClass`, `floatingClass` (comma-separated)
- Exact match: `firefox`
- Substring match with brackets: `[fire]` matches any class containing "fire" (case-insensitive)
- Default ignored classes: `krunner,yakuake,spectacle,kded5,xwaylandvideobridge,plasmashell,ksplashqml,org.kde.plasmashell,org.kde.polkit-kde-authentication-agent-1`

### Gaps Override Format
**Config key**: `gapsOverrideConfig` (newline-separated entries)
```
outputName:activity:desktopName:left:right:top:bottom:between
```

### Surface Capacity Format
**Config key**: `surfacesDefaultConfig` (newline-separated)
```
outputName:activity:desktopName:capacity
```

### Dock Window Class Config Format
**Config key**: `dockWindowClassConfig` (newline-separated)
```
windowClassName:position:priority
```
Where `position` is `left`, `right`, `top`, or `bottom`.

### Sole Window Output Override Format
**Config key**: `soleWindowOutputOverride` (comma-separated)
```
outputName:width:height:noBorders:noGaps
```
Example: `HDMI-A-1:80:90:1:0` — on HDMI-A-1, sole window is 80% wide, 90% tall, no borders, with gaps.

### Meta Shortcut Config Format
**Config key**: `metaConf` (newline-separated)
```
PushedShortcut = RunShortcut
```
Example: `FocusUp = SwapUp` — when in meta mode, FocusUp triggers SwapUp.

---

## Integration Patterns and Workflows

### KWin Script Loading
1. KWin loads `contents/ui/main.qml` (the `X-Plasma-MainScript`).
2. `main.qml` uses a `Loader` component to include `shortcuts.qml` and `dbus.qml`.
3. `main.js` bootstraps the TypeScript-compiled `script.js` into the KWin JavaScript engine.
4. The script creates a `KWinConfig`, initializes `TilingEngine` and `TilingController`, and wires up all KWin workspace signals.

### Adding a New Layout
1. Create a new file `src/layouts/mylayout.ts` implementing `ILayout`.
2. Add the class to `layoutsList` in `KWinConfig` constructor (`src/driver/kwinconfig.ts:174`):
   ```typescript
   [MyLayout, true],  // true = supports capacity configuration
   ```
3. Add a shortcut entry in `src/common.ts` `IShortcuts` interface and register it in `res/shortcuts.qml`.
4. Rebuild: `go-task install`.

### Window State Lifecycle
```
new window appears
    → KWinDriver.onWindowAdded()
    → TilingController.onWindowAdded()
    → TilingEngine.manage()
        → if shouldIgnore: skip
        → if dock config matches: WindowState.Docked
        → else: WindowState.Undecided
    → TilingEngine.arrange()
        → getTileables(): Undecided → Tiled or Floating based on shouldFloat/floatDefault
        → layout.apply(): sets window.geometry
        → window.commit(): applies geometry to KWin
```

### Per-Surface Layout Persistence
Each unique (output × activity × virtualDesktop) combination has its own `LayoutStoreEntry`. The `layoutId` key format is generated by `KWinSurface.generateId()`. Layout state (current layout, layout instances) persists for the lifetime of the KWin script session. `layoutPerActivity` and `layoutPerDesktop` config flags control whether the surface ID includes activity/desktop components.
