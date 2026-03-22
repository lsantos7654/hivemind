# jsdiff — Code Structure

## Annotated Directory Tree

```
jsdiff/
├── src/                          # TypeScript source (compiled to libcjs/, libesm/, dist/)
│   ├── index.ts                  # Public entry point — re-exports all APIs and types
│   ├── types.ts                  # All shared TypeScript interfaces and type aliases
│   ├── diff/                     # Core diffing algorithm implementations
│   │   ├── base.ts               # Abstract Diff<TokenT, ValueT, InputValueT> class; Myers algorithm
│   │   ├── character.ts          # CharacterDiff — one Unicode code point per token
│   │   ├── word.ts               # WordDiff and WordsWithSpaceDiff; Intl.Segmenter support
│   │   ├── line.ts               # LineDiff; tokenize() also used by jsonDiff
│   │   ├── sentence.ts           # SentenceDiff — sentence-boundary tokenization
│   │   ├── css.ts                # CssDiff — CSS token tokenization
│   │   ├── json.ts               # JsonDiff — JSON serialization + line-level diff
│   │   └── array.ts              # ArrayDiff — arbitrary typed arrays, no removeEmpty
│   ├── patch/                    # Unified diff patch creation, parsing, application
│   │   ├── create.ts             # structuredPatch, createTwoFilesPatch, createPatch, formatPatch
│   │   ├── parse.ts              # parsePatch — unified diff string → StructuredPatch[]
│   │   ├── apply.ts              # applyPatch, applyPatches with fuzz support
│   │   ├── reverse.ts            # reversePatch — invert a structured patch
│   │   └── line-endings.ts       # isWin/isUnix/unixToWin/winToUnix helpers
│   ├── convert/                  # Output format converters
│   │   ├── dmp.ts                # convertChangesToDMP — Google diff-match-patch tuples
│   │   └── xml.ts                # convertChangesToXML — XML markup
│   └── util/                     # Internal helper utilities
│       ├── string.ts             # Unicode-aware whitespace, prefix/suffix, overlap utilities
│       ├── array.ts              # Array utility helpers
│       ├── params.ts             # generateOptions — merge options objects
│       └── distance-iterator.ts  # Bidirectional scan iterator used by applyPatch
│
├── test/                         # Mocha test suite (JavaScript, run against compiled output)
│   ├── index.js                  # Aggregates all test files
│   ├── diff/                     # Tests for each diff/* module
│   │   ├── character.js
│   │   ├── word.js
│   │   ├── line.js
│   │   ├── sentence.js
│   │   ├── css.js
│   │   ├── json.js
│   │   └── array.js
│   ├── patch/                    # Tests for patch/* modules
│   │   ├── create.js
│   │   ├── parse.js
│   │   ├── apply.js
│   │   ├── reverse.js
│   │   └── line-endings.js
│   ├── convert/                  # Tests for convert/* modules
│   │   └── dmp.js
│   └── util/
│       └── string.js
│
├── test-d/                       # tsd type-level tests
│   ├── diffCharsOverloads.test-d.ts   # Overload resolution tests for diffChars
│   └── originalDefinitelyTypedTests.test-d.ts  # Migrated @types/diff tests
│
├── examples/                     # Usage examples
│   ├── node_example.js           # Node.js colored diff example
│   └── web_example.html          # Browser-side diff example
│
├── images/                       # README screenshots
│
├── package.json                  # Build scripts, exports map, devDependencies
├── tsconfig.json                 # TypeScript compiler configuration
├── rollup.config.mjs             # Rollup: bundles libesm/index.js → dist/diff.js (UMD)
├── karma.conf.js                 # Karma browser test runner configuration
├── eslint.config.mjs             # ESLint flat config
├── runtime.js                    # @babel/register hook for running tests on compiled output
├── .babelrc                      # Babel preset-env + istanbul plugin for coverage
└── .yarnrc.yml                   # Yarn 4 configuration
```

## Module and Package Organization

### Source (`src/`)

The source is written in TypeScript (strict mode, ES module format). Three generic type parameters on the base `Diff` class capture token type, value type, and input value type, enabling type-safe subclassing for custom diffing scenarios.

Each diff variant is a concrete class plus one or more standalone factory functions. Both are exported from `src/index.ts` — the class instances (e.g. `wordDiff`, `lineDiff`) are exported for callers who want to call `.diff()` directly or subclass the pre-configured instance; the functions (e.g. `diffWords`, `diffLines`) are the primary convenience API.

### Compiled outputs

- `libcjs/` — CommonJS output from `tsc --module commonjs`. Includes a `package.json` with `{ "type": "commonjs" }`.
- `libesm/` — ESM output from `tsc --module nodenext --target es6`. Includes a `package.json` with `{ "type": "module" }`.
- `dist/diff.js` — UMD bundle built by Rollup from `libesm/index.js`, exposes global `Diff`.
- `dist/diff.min.js` — Minified UMD bundle from uglify-js.

The `package.json` exports map routes `import` → `libesm/`, `require` → `libcjs/`, and `browser` → `dist/diff.js`.

## Main Source Directories and Their Purposes

### `src/diff/` — Core Algorithm

All concrete differ classes extend `Diff` from `base.ts`. The Myers algorithm runs in `base.ts:diffWithOptionsObj`. The `execEditLength` inner function performs one iteration of the BFS over the edit graph diagonals; it is called in a tight loop (sync mode) or via `setTimeout` (async/callback mode). The `buildValues` function converts the internal linked-list path representation into the array of `ChangeObject`s returned to callers.

Key overridable methods in subclasses:
- `castInput` — transforms the raw input before tokenization (used by `JsonDiff` to `JSON.stringify`)
- `tokenize` — splits a value into an array of tokens
- `removeEmpty` — filters out falsy tokens (overridden to a no-op in `ArrayDiff`)
- `equals` — token equality predicate
- `join` — combines tokens back into a value string (overridden in `WordDiff` for whitespace deduplication and in `ArrayDiff` to return the array)
- `postProcess` — post-processes the change objects (used by `WordDiff` for whitespace normalization)

### `src/patch/` — Unified Diff Patch Utilities

`create.ts` calls `diffLines` internally, then transforms the resulting change objects into hunks (groups of consecutive changed lines with context). The `formatPatch` function serializes a `StructuredPatch` object to the standard unified diff text format (`@@ -M,N +P,Q @@`).

`apply.ts` implements a sophisticated hunk application loop: it tries each hunk at its specified position first, then scans bidirectionally (via `distanceIterator`) for a matching location, and optionally allows up to `fuzzFactor` context mismatches.

### `src/util/` — Utilities

`string.ts` is the most complex utility file. It provides Unicode-aware operations used by `WordDiff.postProcess` to eliminate duplicated whitespace at the boundaries between keep/insert/delete change objects. Functions like `leadingAndTrailingWs`, `longestCommonPrefix`, `longestCommonSuffix`, `maximumOverlap`, `replacePrefix`, `replaceSuffix`, `removePrefix`, `removeSuffix`, and the `segment` function (which normalizes `Intl.Segmenter` output) all live here.

`distance-iterator.ts` exports a generator that yields positions around a starting point in expanding radius: `start`, `start-1`, `start+1`, `start-2`, `start+2`, …, bounded by `min` and `max`. This is used by `applyPatch` to search for a hunk match near the expected position.

## Key Files and Their Roles

| File | Role |
|------|------|
| `src/index.ts` | Single public entry point; re-exports all functions, classes, constants, and types |
| `src/types.ts` | All TypeScript interfaces: `ChangeObject<V>`, `Change`, `ArrayChange<T>`, `StructuredPatch`, `StructuredPatchHunk`, all `DiffXxxOptions{Abortable,Nonabortable}` types |
| `src/diff/base.ts` | Myers O(ND) algorithm implementation; `Diff<TokenT,ValueT,InputValueT>` class |
| `src/diff/word.ts` | `WordDiff` with `Intl.Segmenter` support and whitespace deduplication post-processing |
| `src/diff/line.ts` | `LineDiff` + exported `tokenize()` function (also used by `JsonDiff`) |
| `src/diff/json.ts` | `JsonDiff` — serializes objects to sorted-key JSON, diffs line-by-line, exports `canonicalize` |
| `src/patch/create.ts` | `structuredPatch`, `createTwoFilesPatch`, `createPatch`, `formatPatch`; `INCLUDE_HEADERS`, `FILE_HEADERS_ONLY`, `OMIT_HEADERS` constants |
| `src/patch/apply.ts` | `applyPatch`, `applyPatches`, `ApplyPatchOptions`, `ApplyPatchesOptions` |
| `src/patch/parse.ts` | `parsePatch` — unified diff string parser |
| `src/util/string.ts` | Unicode-aware whitespace utilities for word diff post-processing |
| `src/util/distance-iterator.ts` | Bidirectional position scanner for fuzzy patch application |

## Code Organization Patterns

- **Overload-based TypeScript API**: Each public diff function has 5 overload signatures to capture the cross-product of async/sync × abortable/non-abortable call modes. The implementation signature uses `any` for internal flexibility, with the exported overloads providing correct narrowing.
- **Singleton class instances**: Each diff variant instantiates a singleton (e.g. `export const wordDiff = new WordDiff()`) which the convenience functions delegate to. This allows callers to use the class directly if needed.
- **Linked-list change tracking**: Internally, the algorithm builds a singly-linked list of `DraftChangeObject` nodes (via `previousComponent`), which is converted to a final array in `buildValues`. This avoids O(n²) array copies during the BFS.
- **Test files are JavaScript**: Tests run against the compiled output, not the TypeScript source. The `runtime.js` file registers Babel with Istanbul instrumentation for coverage.
