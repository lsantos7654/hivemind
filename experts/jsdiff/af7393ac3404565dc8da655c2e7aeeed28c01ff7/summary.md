# jsdiff — Summary

## Repository Purpose and Goals

jsdiff (npm package: `diff`) is a JavaScript/TypeScript text differencing library implementing the Myers O(ND) difference algorithm. It computes the minimal edit distance (sequence of insertions and deletions) between two inputs and exposes the result as structured data that consumers can render, serialize to unified diff format, or apply as patches.

The library's primary goals are:
- Provide a rich set of built-in tokenization strategies (characters, words, lines, sentences, CSS tokens, JSON, arrays)
- Support unified diff patch creation, parsing, and application compatible with GNU `patch`
- Offer full TypeScript typings with overload-aware async/abortable call signatures (as of v8)
- Work in Node.js, browsers (via a UMD bundle), and any ES5+ environment
- Maintain 100% code coverage and be dependency-free at runtime

## Key Features and Capabilities

- **Multiple diff granularities**: character, word (with optional `Intl.Segmenter` for CJK/multilingual), word-with-space, line, trimmed-line, sentence, CSS token, JSON object, and arbitrary array diffs.
- **Patch workflow**: `structuredPatch` → `formatPatch` → `applyPatch` / `applyPatches`. Patches are compatible with the unified diff format accepted by GNU `patch`.
- **Fuzzy patch application**: `applyPatch` supports a `fuzzFactor` (Levenshtein distance in lines) to tolerate minor context mismatches.
- **Async / non-blocking mode**: All diff functions accept a `callback` option to yield control to the event loop between iterations.
- **Abortable diffs**: `timeout` (milliseconds) and `maxEditLength` options abort expensive diffs early and return `undefined`.
- **Custom diffing**: Extend the `Diff` base class and override `castInput`, `tokenize`, `removeEmpty`, `equals`, `join`, and `postProcess` to implement completely custom diff logic.
- **Format conversions**: `convertChangesToDMP` (Google diff-match-patch format) and `convertChangesToXML`.
- **Configurable patch headers**: `INCLUDE_HEADERS`, `FILE_HEADERS_ONLY`, and `OMIT_HEADERS` constants for controlling unified diff header lines.
- **Dual CJS/ESM builds**: Ships as both CommonJS (`libcjs/`) and ESM (`libesm/`), plus a UMD browser bundle (`dist/diff.js` / `dist/diff.min.js`).

## Primary Use Cases and Target Audience

- **Developer tools and IDEs**: Syntax-highlighted diff views, inline change visualization.
- **Version control and review tools**: Generating unified diff patches, applying patches programmatically.
- **Test frameworks and CI**: Comparing expected vs. actual output at various granularities.
- **Code editors / web apps**: Browser-side diffing without a backend.
- **Content management**: Tracking changes to text content, JSON configuration, CSS files.
- **Migration scripts**: Patching text files at runtime without spawning a child process.

Target audience: JavaScript/TypeScript developers who need programmatic access to textual diffs in Node.js or the browser.

## High-Level Architecture Overview

The library is organized into four subsystems:

1. **`src/diff/`** — Tokenization and core Myers algorithm. The abstract `Diff<TokenT, ValueT, InputValueT>` base class in `base.ts` implements the algorithm. Concrete subclasses (`CharacterDiff`, `WordDiff`, `LineDiff`, etc.) each define how to tokenize input and compare tokens.

2. **`src/patch/`** — Unified diff patch utilities. `create.ts` converts a `diffLines` result into a structured patch object or a formatted string. `parse.ts` parses unified diff strings back to structured objects. `apply.ts` applies structured patches with optional fuzz. `reverse.ts` inverts a patch. `line-endings.ts` handles CRLF/LF normalization.

3. **`src/convert/`** — Output format converters. `dmp.ts` converts change objects to Google's diff-match-patch tuple format. `xml.ts` serializes change objects to XML markup.

4. **`src/util/`** — Shared helpers. `string.ts` provides Unicode-aware string utilities (whitespace segmentation, prefix/suffix operations). `array.ts` has array utilities. `params.ts` merges option objects. `distance-iterator.ts` implements the bidirectional search used by `applyPatch`.

The `src/index.ts` entry point re-exports everything from the four subsystems and all TypeScript types from `src/types.ts`.

## Related Projects and Dependencies

- **Runtime dependencies**: None. The library is zero-dependency at runtime.
- **Related**: Google's [diff-match-patch](https://github.com/google/diff-match-patch) (output conversion supported via `convertChangesToDMP`).
- **Algorithm reference**: Myers, E. W. (1986). "An O(ND) Difference Algorithm and Its Variations."
- **Type definitions**: As of v8, bundled with the package. The `@types/diff` DefinitelyTyped package should no longer be used.
