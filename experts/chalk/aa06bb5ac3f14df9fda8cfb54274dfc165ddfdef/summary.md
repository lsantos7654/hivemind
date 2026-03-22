# Chalk — Repository Summary

## Repository Purpose and Goals

Chalk is a Node.js library for terminal string styling, described in its own words as "Terminal string styling done right." Published under the `chalk` npm organization and maintained by Sindre Sorhus and Josh Junon, it provides a fluent, chainable API for wrapping strings with ANSI escape codes that produce colored and formatted output in terminal environments.

The project's core goals are:
- Expressive, composable API for combining text styles without boilerplate
- High performance with lazy property caching and minimal overhead
- Zero runtime dependencies — all dependencies are vendored into `source/vendor/`
- Correct behavior for edge cases: nested styles, multi-line strings, and terminals with varying color support
- Full TypeScript type definitions for IDE tooling
- ESM-only distribution (Chalk 5+)

## Key Features and Capabilities

**Chainable style API** — Styles are accessed as getter properties on the chalk object. Each getter returns a new builder function that accumulates the style chain. The final invocation applies the accumulated ANSI codes around the provided string(s).

**256 and Truecolor support** — Beyond the standard 16 ANSI colors, Chalk supports 256-color (ansi256) and 24-bit Truecolor (RGB/hex) modes. When the terminal reports a lower color level, colors are automatically downsampled to the nearest supported representation.

**Automatic color-level detection** — The bundled `supports-color` vendor module inspects environment variables (`TERM`, `COLORTERM`, `FORCE_COLOR`), command-line flags (`--color`, `--no-color`), CI environment variables (GitHub Actions, CircleCI, Travis, etc.), platform heuristics (Windows 10 build numbers), and TTY status to determine the appropriate color level (0–3) at startup.

**Style nesting** — When a styled string contains existing ANSI escape codes (e.g., from nested chalk calls), Chalk replaces any matching close codes with re-open codes so the outer style is correctly restored after each inner-styled segment.

**Multi-line fix** — Chalk wraps each line individually (splitting on `\n`/`\r\n`) to prevent color bleed across line boundaries, which causes visual artifacts in some macOS terminal emulators.

**`visible` pseudo-style** — A special style that causes the string to be printed only when color is enabled (level > 0), useful for purely decorative output.

**`chalkStderr` instance** — A separate default chalk instance whose color level is detected from `stderr` rather than `stdout`, for logging pipelines that separate stdout/stderr.

**Browser support** — The vendor `supports-color/browser.js` detects Chromium ≥ 94 via `navigator.userAgentData` and falls back to a user-agent string check, enabling use in browser developer consoles.

## Primary Use Cases and Target Audience

- **CLI tool authors** styling help text, progress indicators, error messages, and status output
- **Logger/reporter libraries** (test frameworks, build tools) adding color-coded severity levels
- **Interactive terminal applications** using color to structure output
- **Developers** embedding Chalk in ~115,000 downstream npm packages (as of 2024)

## High-Level Architecture Overview

The library is structured around a prototype-manipulation pattern that makes chalk instances behave simultaneously as callable functions and as objects with style-getter properties:

1. `createChalk()` produces a function (the chalk instance) whose prototype is set to `createChalk.prototype`.
2. `createChalk.prototype` has all style names defined as lazy getters via `Object.defineProperties`.
3. When a style getter is accessed, it calls `createBuilder()`, which returns a new function whose prototype is set to `proto` — another object with all style getters and a `level` accessor.
4. `createBuilder()` caches the built function on the calling object via `Object.defineProperty`, so subsequent accesses are O(1) property lookups (no getter re-execution).
5. When the builder function is finally called with string arguments, `applyStyle()` assembles the ANSI open/close sequences from the accumulated styler chain and wraps the string.

Style metadata (ANSI escape codes for each named style, plus color-conversion utilities) comes from the vendored `ansi-styles` module. Color-support detection comes from the vendored `supports-color` module.

## Related Projects and Dependencies

**Vendored (zero external runtime deps):**
- `source/vendor/ansi-styles/` — ANSI escape code definitions and color-conversion utilities (RGB↔256↔16)
- `source/vendor/supports-color/` — terminal color-support detection for Node.js and browsers

**Chalk ecosystem (related separate packages):**
- `chalk-template` — tagged template literal support
- `chalk-cli` — CLI wrapper
- `ansi-styles`, `supports-color`, `strip-ansi`, `wrap-ansi`, `slice-ansi` — lower-level ANSI utilities
- `yoctocolors` — minimal alternative by the same author for size-critical contexts

**Dev dependencies:** `ava` (test runner), `c8` (coverage), `tsd` (TypeScript definition testing), `xo` (linter), `matcha` (benchmarking), `color-convert` and `log-update` (used only in examples).
