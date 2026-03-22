# Chalk — APIs and Interfaces

## Public API Entry Points

Chalk exports from `source/index.js`:

| Export | Kind | Description |
|--------|------|-------------|
| `default` (chalk) | `ChalkInstance` | Pre-built instance with auto-detected stdout color level |
| `Chalk` | class | Constructor for custom chalk instances |
| `chalkStderr` | `ChalkInstance` | Pre-built instance using stderr color detection |
| `supportsColor` | `ColorInfo \| false` | Detected color support for stdout |
| `supportsColorStderr` | `ColorInfo \| false` | Detected color support for stderr |
| `modifierNames` | `string[]` | Array of all modifier style names |
| `foregroundColorNames` | `string[]` | Array of all foreground color names |
| `backgroundColorNames` | `string[]` | Array of all background color names |
| `colorNames` | `string[]` | Combined foreground + background color names |

Deprecated aliases (present until next major): `modifiers`, `foregroundColors`, `backgroundColors`, `colors`.

## Key Interfaces

### `ChalkInstance`

Defined in `source/index.d.ts:32`. A `ChalkInstance` is simultaneously:
- **Callable:** `(...text: unknown[]): string` — joins arguments with spaces and returns a plain string (no styling) when called without a preceding style chain
- **Style-chain object:** exposes all style names as readonly `this`-returning properties

```typescript
export interface ChalkInstance {
  (...text: unknown[]): string;
  level: ColorSupportLevel;           // 0 | 1 | 2 | 3

  // Dynamic color methods (return this for chaining):
  rgb(red: number, green: number, blue: number): this;
  hex(color: string): this;
  ansi256(index: number): this;
  bgRgb(red: number, green: number, blue: number): this;
  bgHex(color: string): this;
  bgAnsi256(index: number): this;

  // Modifiers (all readonly this):
  readonly reset: this;
  readonly bold: this;
  readonly dim: this;
  readonly italic: this;
  readonly underline: this;
  readonly overline: this;
  readonly inverse: this;
  readonly hidden: this;
  readonly strikethrough: this;
  readonly visible: this;

  // 16 foreground colors + bright variants + aliases:
  readonly black: this; readonly red: this; readonly green: this;
  readonly yellow: this; readonly blue: this; readonly magenta: this;
  readonly cyan: this; readonly white: this;
  readonly gray: this; readonly grey: this;        // aliases for blackBright
  readonly blackBright: this; readonly redBright: this;
  readonly greenBright: this; readonly yellowBright: this;
  readonly blueBright: this; readonly magentaBright: this;
  readonly cyanBright: this; readonly whiteBright: this;

  // 16 background colors + bright variants + aliases:
  readonly bgBlack: this; readonly bgRed: this; readonly bgGreen: this;
  readonly bgYellow: this; readonly bgBlue: this; readonly bgMagenta: this;
  readonly bgCyan: this; readonly bgWhite: this;
  readonly bgGray: this; readonly bgGrey: this;    // aliases for bgBlackBright
  readonly bgBlackBright: this; /* ...bgRedBright through bgWhiteBright */
}
```

### `Options`

```typescript
export interface Options {
  readonly level?: ColorSupportLevel;  // 0 | 1 | 2 | 3
}
```

Passed to `new Chalk(options)` to set a fixed color level, bypassing auto-detection.

### `ColorSupportLevel`

```typescript
type ColorSupportLevel = 0 | 1 | 2 | 3;
```

| Value | Meaning |
|-------|---------|
| `0` | All colors disabled |
| `1` | Basic 16-color ANSI support |
| `2` | 256-color (xterm-256) support |
| `3` | Truecolor (16 million colors) support |

### `ColorInfo`

Exported from `source/vendor/supports-color/index.d.ts`:

```typescript
interface ColorInfo {
  level: ColorSupportLevel;
  hasBasic: boolean;
  has256: boolean;
  has16m: boolean;
}
```

`supportsColor` is either `false` (no color support) or a `ColorInfo` object.

## Usage Examples

### Basic Usage

```js
import chalk from 'chalk';

console.log(chalk.blue('Hello world!'));
// => '\u001B[34mHello world!\u001B[39m'

console.log(chalk.red.bold('Error!'));
// => '\u001B[31m\u001B[1mError!\u001B[22m\u001B[39m'

console.log(chalk.blue.bgRed.bold('Hello world!'));
// Stacks three styles: blue text, red background, bold
```

### Chaining and Nesting

```js
import chalk from 'chalk';

// Multiple arguments joined with space
chalk.red('foo', 'bar');  // => '\u001B[31mfoo bar\u001B[39m'

// Nested styles — outer color is correctly restored
chalk.red('Hello', chalk.underline.bgBlue('world') + '!');

// Styles of the same type can be nested
chalk.red('a' + chalk.yellow('b' + chalk.green('c') + 'b') + 'c');
// Correctly re-opens 'yellow' and 'red' after inner 'green' closes
```

### Custom Color Models

```js
import chalk from 'chalk';

// RGB (Truecolor — requires level 3)
chalk.rgb(123, 45, 67).underline('Underlined reddish color');

// Hex
chalk.hex('#DEADED').bold('Bold gray!');
chalk.hex('#FF8800').bold('Orange!');

// 256-color index
chalk.ansi256(201)('Bright violet');

// Background variants
chalk.bgRgb(15, 100, 204).inverse('Hello!');
chalk.bgHex('#DEADED').underline('Hello, world!');
chalk.bgAnsi256(194)('Honeydew, more or less');
```

### Creating a Custom Instance

```js
import {Chalk} from 'chalk';

// Force a specific color level (overrides auto-detection)
const chalk256 = new Chalk({level: 2});
chalk256.hex('#FF0000')('hello');
// At level 2, hex is downsampled to 256-color:
// => '\u001B[38;5;196mhello\u001B[39m'

// Disable all colors
const noColor = new Chalk({level: 0});
noColor.red('plain text');  // => 'plain text'
```

### Defining Themes

```js
import chalk from 'chalk';

const error   = chalk.bold.red;
const warning = chalk.hex('#FFA500');  // Orange
const success = chalk.green;
const info    = chalk.blue;

console.log(error('Error!'));
console.log(warning('Warning!'));
console.log(success('Done.'));
```

### Template Literals

```js
import chalk from 'chalk';

const name = 'World';
console.log(`Hello ${chalk.red(name)}!`);

// Multi-line template
console.log(`
CPU:  ${chalk.red('90%')}
RAM:  ${chalk.green('40%')}
DISK: ${chalk.yellow('70%')}
`);
```

### `visible` Style

```js
import chalk from 'chalk';

// Only outputs when chalk.level > 0 (i.e., color is supported)
chalk.visible('Decorative text');
// At level 0: '' (empty string)
// At level >= 1: 'Decorative text' (no ANSI codes, just the text)
```

### `chalkStderr`

```js
import {chalkStderr} from 'chalk';

process.stderr.write(chalkStderr.red('Error logged to stderr\n'));
// Uses stderr color-detection level independently from stdout
```

### Validating Style Names

```js
import {modifierNames, foregroundColorNames, colorNames} from 'chalk';

modifierNames.includes('bold');          // => true
foregroundColorNames.includes('pink');   // => false
colorNames.includes('bgRed');            // => true
```

### Accessing `supportsColor`

```js
import {supportsColor, supportsColorStderr} from 'chalk';

if (supportsColor) {
  console.log('Level:', supportsColor.level);
  console.log('Has 256 colors:', supportsColor.has256);
  console.log('Has Truecolor:', supportsColor.has16m);
}
```

## Configuration Options and Environment Variables

### Color Level Override — Code

```js
import chalk from 'chalk';

// Override globally (affects all chalk consumers!)
chalk.level = 1;

// Preferred: create a new instance for reusable modules
import {Chalk} from 'chalk';
const myChalk = new Chalk({level: 1});
```

### Color Level Override — Environment Variables

| Variable | Effect |
|----------|--------|
| `FORCE_COLOR=0` or `FORCE_COLOR=false` | Disable all colors (level 0) |
| `FORCE_COLOR=1` or `FORCE_COLOR=true` | Force basic colors (level 1) |
| `FORCE_COLOR=2` | Force 256 colors (level 2) |
| `FORCE_COLOR=3` | Force Truecolor (level 3) |

### Color Level Override — CLI Flags

| Flag | Effect |
|------|--------|
| `--no-color`, `--no-colors`, `--color=false`, `--color=never` | Level 0 |
| `--color`, `--colors`, `--color=true`, `--color=always` | Level 1 |
| `--color=256` | Level 2 |
| `--color=16m`, `--color=full`, `--color=truecolor` | Level 3 |

### Auto-Detection Heuristics (in `source/vendor/supports-color/index.js`)

The color level is determined by inspecting (in precedence order):
1. `FORCE_COLOR` env var / `--color` flags
2. Azure DevOps (`TF_BUILD` + `AGENT_NAME` → level 1)
3. TTY check (non-TTY stream → level 0 unless forced)
4. `TERM=dumb` → level 0
5. Windows 10 build number → level 2 or 3
6. CI environments: GitHub Actions/Gitea/CircleCI → level 3; Travis/AppVeyor/GitLab/Buildkite/Drone → level 1
7. TeamCity version regex
8. `COLORTERM=truecolor` → level 3
9. Specific `TERM` values: `xterm-kitty`, `xterm-ghostty`, `wezterm` → level 3
10. `TERM_PROGRAM`: iTerm3+ → level 3, iTerm2 → level 2, Apple_Terminal → level 2
11. `TERM` regex: `-256color` suffix → level 2; `xterm`, `screen`, `vt100`, `ansi`, etc. → level 1
12. `COLORTERM` present (any value) → level 1

## Integration Patterns

### With `chalk-template` (Tagged Template Literals)

```js
import chalkTemplate from 'chalk-template';

chalkTemplate`{bold.red Error:} something went wrong`;
// Equivalent to: chalk.bold.red('Error:') + ' something went wrong'
```

### Browser / Bundler Usage

When bundling for browsers, the package import condition `"default"` in the `#supports-color` import map selects `source/vendor/supports-color/browser.js`, which uses `navigator.userAgentData` (Chromium 94+) or user-agent sniffing.

Bundlers that support package `"imports"` (e.g., webpack 5, Rollup with `@rollup/plugin-node-resolve`) will resolve the browser variant automatically when `browser: true` is set in bundler config.

### Caching Style Builders for Performance

```js
import chalk from 'chalk';

// Pre-build and cache style chains — subsequent accesses are O(1) property reads
const errorStyle  = chalk.bold.red;
const warnStyle   = chalk.yellow;
const debugStyle  = chalk.dim.gray;

// In hot logging paths, use the cached builders
errorStyle('Something failed');
warnStyle('Watch out');
debugStyle('Debug info');
```

### Downsampling Across Color Levels

```js
import {Chalk} from 'chalk';

// At level 1 (16 colors): RGB is downsampled to nearest ANSI 16-color
new Chalk({level: 1}).hex('#FF0000')('hello');
// => '\u001B[91mhello\u001B[39m'  (bright red ANSI)

// At level 2 (256 colors): RGB is downsampled to nearest 256-color index
new Chalk({level: 2}).hex('#FF0000')('hello');
// => '\u001B[38;5;196mhello\u001B[39m'

// At level 3 (Truecolor): RGB passes through directly
new Chalk({level: 3}).hex('#FF0000')('hello');
// => '\u001B[38;2;255;0;0mhello\u001B[39m'
```

### Extension Points

Chalk does not have a plugin or extension API. Customization is achieved by:
- Creating new `Chalk` instances with specific `level` values
- Composing and naming style chains as constants (themes)
- Using `chalk-template` for tagged template literal syntax
- Directly using the vendored `ansi-styles` exports for raw ANSI code manipulation
