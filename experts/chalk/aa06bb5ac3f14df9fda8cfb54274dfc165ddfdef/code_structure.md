# Chalk — Code Structure

## Annotated Directory Tree

```
chalk/                              # Repository root
├── source/                         # All published source code
│   ├── index.js                    # Main entry point — Chalk class, builder, style engine
│   ├── index.d.ts                  # TypeScript type definitions for the public API
│   ├── index.test-d.ts             # tsd type-level tests (excluded from npm publish)
│   ├── utilities.js                # Low-level string helpers (CRLF handling, replace-all)
│   └── vendor/                     # Vendored dependencies (no external runtime deps)
│       ├── ansi-styles/
│       │   ├── index.js            # ANSI escape code table + color conversion utilities
│       │   └── index.d.ts          # TypeScript types for ansi-styles
│       └── supports-color/
│           ├── index.js            # Node.js color-support detection
│           ├── index.d.ts          # TypeScript types for supports-color
│           ├── browser.js          # Browser color-support detection (Chromium)
│           └── browser.d.ts        # TypeScript types for browser variant
├── test/                           # Test suite (AVA)
│   ├── chalk.js                    # Main integration tests
│   ├── instance.js                 # Tests for new Chalk({level}) instances
│   ├── level.js                    # Tests for level detection and clamping
│   ├── visible.js                  # Tests for the `visible` pseudo-style
│   ├── no-color-support.js         # Tests when color is disabled (level 0)
│   └── _fixture.js                 # Shared test fixture (child process helper)
├── examples/
│   ├── rainbow.js                  # Animated rainbow text using chalk.hex()
│   └── screenshot.js               # Generates the readme screenshot
├── benchmark.js                    # matcha benchmarks for style application
├── package.json                    # Package manifest, scripts, xo/c8 config
├── readme.md                       # Primary documentation
├── license                         # MIT license
├── contributing.md                 # Contribution guidelines
├── code-of-conduct.md              # Code of conduct
├── .editorconfig                   # Editor formatting config
├── .gitattributes                  # Git line-ending config
├── .npmrc                          # npm config (save-exact=true)
├── media/                          # Images used in readme
│   ├── logo.svg
│   ├── logo.png
│   └── screenshot.png
└── .github/
    ├── workflows/main.yml          # CI: Node 14/16/18, npm test, codecov upload
    ├── funding.yml                 # GitHub Sponsors config
    └── security.md                 # Security policy
```

## Module and Package Organization

The package uses **ESM-only** (`"type": "module"` in `package.json`). There is no CommonJS build. The package exports a single entry point:

```json
"main": "./source/index.js",
"exports": "./source/index.js",
"types": "./source/index.d.ts"
```

Internal module resolution uses Node.js package imports (`"imports"` field in `package.json`) to alias vendor paths:

```json
"imports": {
  "#ansi-styles": "./source/vendor/ansi-styles/index.js",
  "#supports-color": {
    "node": "./source/vendor/supports-color/index.js",
    "default": "./source/vendor/supports-color/browser.js"
  }
}
```

This means `source/index.js` uses `import ansiStyles from '#ansi-styles'` and `import supportsColor from '#supports-color'`, which resolve to the appropriate platform-specific vendor file. The browser variant of `supports-color` is selected via the `"default"` condition when bundlers process the package.

## Main Source Files and Their Roles

### `source/index.js` (226 lines) — Core Style Engine

This is the entire public API implementation. Key internal components:

**Symbol keys** — Three private symbols used as non-enumerable properties on builder functions:
- `GENERATOR` — points back to the root chalk instance (carries the `level` value)
- `STYLER` — linked-list node of accumulated `{open, close, openAll, closeAll, parent}` style data
- `IS_EMPTY` — boolean flag for the `visible` pseudo-style behavior

**`levelMapping`** — Maps the integer level (0–3) to the string key used to look up the ANSI formatter function in `ansiStyles.color`:
```js
const levelMapping = ['ansi', 'ansi', 'ansi256', 'ansi16m'];
```

**`applyOptions(object, options)`** — Validates the `level` option (must be integer 0–3) and sets `object.level`, defaulting to the auto-detected `stdoutColor.level`.

**`Chalk` class** — Exported named class whose constructor returns `chalkFactory(options)` (uses `no-constructor-return` eslint disable). This enables both `new Chalk(opts)` and internal use.

**`chalkFactory(options)`** — Creates a raw function `chalk` (the no-style passthrough), sets its prototype to `createChalk.prototype`, and returns it.

**`createChalk(options)`** — The function whose `.prototype` all chalk instances inherit from. `Object.setPrototypeOf(createChalk.prototype, Function.prototype)` ensures instances are valid functions.

**Style getter loop** (lines 56–64) — Iterates `Object.entries(ansiStyles)` to define lazy getters on the `styles` object. Each getter calls `createBuilder()` with a new styler node and caches the result on the current object with `Object.defineProperty`.

**`getModelAnsi(model, level, type, ...args)`** (lines 74–92) — Dispatches to the correct ANSI formatter based on color model (`rgb`, `hex`) and current level. Handles downsampling: RGB→ansi256 at level 2, RGB→ansi16 at level 1.

**Color model getter loop** (lines 96–117) — Defines `rgb`, `hex`, `ansi256` getters (and their `bg` counterparts) that return functions accepting color arguments and producing a new builder.

**`proto`** (lines 119–130) — The shared prototype for all builder functions. Defined via `Object.defineProperties` on an arrow function to combine all style getters plus a `level` getter/setter that delegates to `this[GENERATOR].level`.

**`createStyler(open, close, parent)`** (lines 132–150) — Constructs a styler node. Accumulates `openAll` and `closeAll` by prepending/appending to the parent's accumulated sequences.

**`createBuilder(self, _styler, _isEmpty)`** (lines 152–166) — Creates the chainable builder function. Sets its prototype to `proto`, attaches the three Symbol properties.

**`applyStyle(self, string)`** (lines 168–200) — The hot path. Applies ANSI codes to a string:
1. Returns early if `level <= 0` or string is empty (respects `IS_EMPTY` for `visible`)
2. If the string already contains `\u001B` (existing ANSI codes), walks the styler chain replacing each close code with the corresponding open code (nested style correction)
3. Splits on newline characters using `stringEncaseCRLFWithFirstIndex` to prevent color bleed
4. Wraps with `openAll + string + closeAll`

**Default export** — `chalk` (a `createChalk()` instance with auto-detected stdout level)
**Named exports** — `Chalk`, `chalkStderr`, `supportsColor`, `supportsColorStderr`, and the color/modifier name arrays from ansi-styles

### `source/utilities.js` (33 lines) — String Helpers

**`stringReplaceAll(string, substring, replacer)`** — Manual implementation of `String.prototype.replaceAll` optimized for the specific chalk use case (replacing ANSI close codes with open codes). Uses `indexOf` in a loop rather than regex for performance.

**`stringEncaseCRLFWithFirstIndex(string, prefix, postfix, index)`** — Wraps each newline (including CRLF) with `prefix` before and `postfix` after, preserving the `\r` in CRLF sequences. Called once per styled string that contains a newline.

### `source/vendor/ansi-styles/index.js` (223 lines) — ANSI Style Table

Defines raw ANSI code pairs for modifiers, 16 foreground colors, and 16 background colors. The `assembleStyles()` function:
- Converts `[open, close]` pairs to `{open: '\u001B[Xm', close: '\u001B[Ym'}` objects
- Builds a `Map` of open→close codes for quick lookup
- Attaches `ansi`, `ansi256`, `ansi16m` formatter functions for dynamic color models
- Provides color-conversion utilities: `rgbToAnsi256`, `hexToRgb`, `hexToAnsi256`, `ansi256ToAnsi`, `rgbToAnsi`, `hexToAnsi`

### `source/vendor/supports-color/index.js` (191 lines) — Node.js Color Detection

Detects color support by checking (in order of priority): `FORCE_COLOR` env var, `--color`/`--no-color` CLI flags, `--color=256`/`--color=16m` flags, Azure DevOps env, TTY status, `TERM=dumb`, Windows version, CI environment variables, TeamCity, `COLORTERM`, specific `TERM` values (kitty, ghostty, wezterm), `TERM_PROGRAM` (iTerm, Apple Terminal), `TERM` regex patterns.

### `source/vendor/supports-color/browser.js` (34 lines) — Browser Color Detection

Detects Chromium ≥ 94 via `navigator.userAgentData.brands` (returning level 3), or falls back to user-agent regex (level 1). Returns level 0 for non-Chromium browsers.

## Code Organization Patterns

**Lazy caching via `Object.defineProperty`** — Style getters install themselves as value properties on first access, converting O(getter) future accesses to O(property lookup). This is a key performance optimization.

**Prototype chain as shared state** — Rather than creating new objects for each chained style, chalk reuses the `proto` object as the shared prototype for all builder functions. Only the three Symbol-keyed properties differ between builders.

**Linked-list styler chain** — Each call to `createStyler` produces a node with a `parent` pointer. `applyStyle` walks this list when handling nested ANSI codes. The `openAll`/`closeAll` fields are pre-computed concatenations to avoid re-walking for the common (no-existing-codes) case.

**Package imports aliasing** — The `#ansi-styles` and `#supports-color` import aliases allow the vendor files to be swapped per environment (Node vs. browser) without changing the import statement in `index.js`.
