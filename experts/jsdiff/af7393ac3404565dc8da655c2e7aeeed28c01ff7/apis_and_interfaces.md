# jsdiff — APIs and Interfaces

## Public Entry Point

Everything is exported from the `diff` package root:

```js
// ESM
import { diffChars, diffLines, createPatch, applyPatch } from 'diff';

// CommonJS
const { diffChars, diffLines, createPatch, applyPatch } = require('diff');

// Browser (UMD global)
// <script src="dist/diff.js"></script>
// window.Diff.diffChars(...)
```

---

## Change Objects

All diff functions return arrays of `ChangeObject<ValueT>` (exported as the `Change` alias for `ChangeObject<string>`):

```ts
interface ChangeObject<ValueT> {
  value: ValueT;     // The text/tokens in this segment
  added: boolean;    // true if inserted in new string
  removed: boolean;  // true if deleted from old string
  count: number;     // Number of tokens in this segment
}

type Change = ChangeObject<string>;
type ArrayChange<T> = ChangeObject<T[]>;
```

A change object where both `added` and `removed` are `false` represents content common to both strings.

---

## Diff Functions

### `diffChars(oldStr, newStr[, options])`

Diffs two strings one Unicode code point at a time.

```ts
import { diffChars } from 'diff';

const changes = diffChars('beep boop', 'beep boob blah');
changes.forEach(part => {
  if (part.added) process.stdout.write('\x1b[32m' + part.value + '\x1b[0m');
  else if (part.removed) process.stdout.write('\x1b[31m' + part.value + '\x1b[0m');
  else process.stdout.write(part.value);
});
```

Options: `ignoreCase`, `callback`, `maxEditLength`, `timeout`, `oneChangePerToken`

---

### `diffWords(oldStr, newStr[, options])`

Diffs at word and punctuation token granularity. Whitespace between tokens is preserved but not considered when determining equality.

```ts
import { diffWords } from 'diff';

const changes = diffWords('Hello, World!', 'Hello, brave new World!');
// Produces: [keep 'Hello,', insert ' brave new', keep ' World!']
```

Options: `ignoreCase`, `intlSegmenter` (an `Intl.Segmenter` with `granularity: 'word'`), `callback`, `maxEditLength`, `timeout`, `oneChangePerToken`

**With Intl.Segmenter (for non-Latin text):**

```ts
const segmenter = new Intl.Segmenter('zh', { granularity: 'word' });
const changes = diffWords('你好世界', '你好新世界', { intlSegmenter: segmenter });
```

---

### `diffWordsWithSpace(oldStr, newStr[, options])`

Like `diffWords` but each word, punctuation mark, newline, or run of non-newline whitespace is its own token (whitespace is NOT ignored for equality).

---

### `diffLines(oldStr, newStr[, options])`

Diffs line-by-line.

```ts
import { diffLines } from 'diff';

const changes = diffLines('line1\nline2\nline3\n', 'line1\nline2b\nline3\n');
changes.forEach(part => {
  const prefix = part.added ? '+' : part.removed ? '-' : ' ';
  process.stdout.write(prefix + part.value);
});
```

Options:
- `ignoreWhitespace: boolean` — trim lines before equality check
- `ignoreNewlineAtEof: boolean` — treat `'b\n'` and `'b'` as equal when at EOF
- `stripTrailingCr: boolean` — normalize `\r\n` to `\n` before diffing
- `newlineIsToken: boolean` — give each trailing newline its own token for human-friendly output
- `callback`, `maxEditLength`, `timeout`, `oneChangePerToken`

---

### `diffSentences(oldStr, newStr[, options])`

Diffs at sentence granularity. Sentences are delimited by `.`, `!`, or `?` followed by whitespace. For non-English text, consider tokenizing with `Intl.Segmenter` and passing to `diffArrays` instead.

---

### `diffCss(oldStr, newStr[, options])`

Diffs CSS token by token (identifiers, values, operators, etc.).

---

### `diffJson(oldObj, newObj[, options])`

Serializes both objects to prettily-formatted JSON with alphabetically sorted keys, then diffs line-by-line.

```ts
import { diffJson } from 'diff';

const changes = diffJson({ a: 1, b: 2 }, { a: 1, b: 3, c: 4 });
```

Options:
- `stringifyReplacer: (k: string, v: any) => any` — custom JSON.stringify replacer
- `undefinedReplacement: any` — replacement for `undefined` values (ignored if `stringifyReplacer` is set)
- `callback`, `maxEditLength`, `timeout`, `oneChangePerToken`

Also exports `canonicalize(obj, stack?, replacementList?, options?)` — the internal function that produces the sorted-key JSON representation.

---

### `diffArrays(oldArr, newArr[, options])`

Diffs two arrays of any type using `===` equality (or a custom comparator).

```ts
import { diffArrays } from 'diff';

const changes = diffArrays([1, 2, 3, 4], [1, 3, 4, 5]);
// ArrayChange<number>[]

// With custom comparator:
const changes2 = diffArrays(
  ['Foo', 'Bar'],
  ['foo', 'baz'],
  { comparator: (a, b) => a.toLowerCase() === b.toLowerCase() }
);
```

Options: `comparator: (a: T, b: T) => boolean`, `callback`, `maxEditLength`, `timeout`, `oneChangePerToken`

---

## Universal Options

Available on all diff functions:

| Option | Type | Description |
|--------|------|-------------|
| `callback` | `(result) => void` | Async mode — result passed to callback via `setTimeout`, returns `undefined` |
| `maxEditLength` | `number` | Abort if edit distance exceeds this; returns `undefined` |
| `timeout` | `number` | Abort after this many milliseconds; returns `undefined` |
| `oneChangePerToken` | `boolean` | Emit one change object per token instead of merging runs |

---

## Patch Functions

### `structuredPatch(oldFileName, newFileName, oldStr, newStr[, oldHeader[, newHeader[, options]]])`

Returns a `StructuredPatch` object:

```ts
interface StructuredPatch {
  oldFileName: string;
  newFileName: string;
  oldHeader: string | undefined;
  newHeader: string | undefined;
  hunks: StructuredPatchHunk[];
  index?: string;
}

interface StructuredPatchHunk {
  oldStart: number;
  oldLines: number;
  newStart: number;
  newLines: number;
  lines: string[];   // Lines prefixed with ' ', '+', '-', or '\ '
}
```

Options: `context` (default 4), `ignoreWhitespace`, `stripTrailingCr`, `callback`, `maxEditLength`, `timeout`

---

### `createTwoFilesPatch(oldFileName, newFileName, oldStr, newStr[, oldHeader[, newHeader[, options]]])`

Returns a unified diff patch string. Equivalent to `formatPatch(structuredPatch(...))`.

```ts
import { createTwoFilesPatch } from 'diff';

const patch = createTwoFilesPatch('file1.txt', 'file2.txt', oldContent, newContent);
// "Index: file1.txt\n===...===\n--- file1.txt\n+++ file2.txt\n@@ ... @@\n..."
```

Extra option: `headerOptions: HeaderOptions` — controls which header lines to include.

---

### `createPatch(fileName, oldStr, newStr[, oldHeader[, newHeader[, options]]])`

Like `createTwoFilesPatch` but `oldFileName === newFileName`.

---

### `formatPatch(patch[, headerOptions])`

Serializes a `StructuredPatch` or `StructuredPatch[]` to a unified diff string.

```ts
import { structuredPatch, formatPatch, FILE_HEADERS_ONLY } from 'diff';

const sp = structuredPatch('a.txt', 'b.txt', oldStr, newStr);
const patchStr = formatPatch(sp, FILE_HEADERS_ONLY);
```

**Header option constants** (exported from `diff`):
- `INCLUDE_HEADERS` — `{ includeIndex: true, includeUnderline: true, includeFileHeaders: true }` (default)
- `FILE_HEADERS_ONLY` — `{ includeIndex: false, includeUnderline: false, includeFileHeaders: true }`
- `OMIT_HEADERS` — `{ includeIndex: false, includeUnderline: false, includeFileHeaders: false }`

---

### `applyPatch(source, patch[, options])`

Applies a unified diff patch to a source string. Returns patched string or `false` on failure.

```ts
import { applyPatch } from 'diff';

const patched = applyPatch(source, patchString, { fuzzFactor: 2 });
if (patched === false) {
  console.error('Patch failed to apply');
} else {
  console.log(patched);
}
```

`patch` may be a string, a `StructuredPatch` object, or a single-element `[StructuredPatch]` array.

Options (`ApplyPatchOptions`):
- `fuzzFactor: number` (default 0) — max context line mismatches tolerated
- `autoConvertLineEndings: boolean` (default true) — auto-normalize CRLF↔LF mismatches
- `compareLine(lineNumber, line, operation, patchContent): boolean` — custom line equality

---

### `applyPatches(patch, options)`

Applies one or more patches via async callbacks. `patch` is a string or `StructuredPatch[]`.

```ts
import { applyPatches } from 'diff';

applyPatches(patchStr, {
  loadFile: (patch, callback) => {
    fs.readFile(patch.oldFileName, 'utf8', (err, data) => callback(err, data));
  },
  patched: (patch, content, callback) => {
    if (content === false) return callback(`Failed: ${patch.oldFileName}`);
    fs.writeFile(patch.newFileName, content, callback);
  },
  complete: (err) => {
    if (err) console.error(err);
  }
});
```

---

### `parsePatch(diffStr)`

Parses a unified diff string into a `StructuredPatch[]`:

```ts
import { parsePatch } from 'diff';
const patches = parsePatch(fs.readFileSync('changes.patch', 'utf8'));
```

---

### `reversePatch(patch)`

Returns a new patch that undoes the original:

```ts
import { reversePatch, parsePatch } from 'diff';
const reversed = reversePatch(parsePatch(patchStr));
```

---

## Conversion Functions

### `convertChangesToDMP(changes)`

Converts change objects to Google diff-match-patch tuple format `[op, value][]` where `op` is `1` (insert), `-1` (delete), or `0` (equal).

### `convertChangesToXML(changes)`

Converts change objects to XML with `<ins>` and `<del>` tags.

---

## Custom Diffing via the `Diff` Base Class

For custom token types, extend the exported `Diff` class:

```ts
import Diff from 'diff';

class MyDiff extends Diff<string, string> {
  tokenize(value: string) {
    return value.split(/([,;]+)/);  // Split on punctuation
  }
  equals(left: string, right: string) {
    return left.trim() === right.trim();
  }
}

const myDiff = new MyDiff();
const changes = myDiff.diff('a, b; c', 'a, b; d');
```

Overridable methods on `Diff<TokenT, ValueT, InputValueT>`:

| Method | Signature | Description |
|--------|-----------|-------------|
| `castInput` | `(value: InputValueT, options) => ValueT` | Transform raw input before tokenizing |
| `tokenize` | `(value: ValueT, options) => TokenT[]` | Split value into tokens |
| `removeEmpty` | `(array: TokenT[]) => TokenT[]` | Filter token array (default: remove falsy) |
| `equals` | `(left: TokenT, right: TokenT, options) => boolean` | Token equality (default: `===` or `ignoreCase`) |
| `join` | `(tokens: TokenT[]) => ValueT` | Join tokens into a value (default: `tokens.join('')`) |
| `postProcess` | `(changes: ChangeObject<ValueT>[], options) => ChangeObject<ValueT>[]` | Post-process result |

---

## TypeScript Type Exports

All option types use the `Abortable` / `Nonabortable` naming convention. Abortable option objects contain either `timeout` or `maxEditLength` (or both), causing the function return type to become `T | undefined` instead of `T`.

Key exported types:
- `ChangeObject<V>`, `Change`, `ArrayChange<T>`
- `StructuredPatch`, `StructuredPatchHunk`
- `DiffCharsOptionsAbortable`, `DiffCharsOptionsNonabortable`
- `DiffLinesOptionsAbortable`, `DiffLinesOptionsNonabortable`
- `DiffWordsOptionsAbortable`, `DiffWordsOptionsNonabortable`
- `DiffJsonOptionsAbortable`, `DiffJsonOptionsNonabortable`
- `DiffCssOptionsAbortable`, `DiffCssOptionsNonabortable`
- `DiffSentencesOptionsAbortable`, `DiffSentencesOptionsNonabortable`
- `DiffArraysOptionsAbortable<T>`, `DiffArraysOptionsNonabortable<T>`
- `StructuredPatchOptionsAbortable`, `StructuredPatchOptionsNonabortable`
- `CreatePatchOptionsAbortable`, `CreatePatchOptionsNonabortable`
- `ApplyPatchOptions`, `ApplyPatchesOptions`
- `HeaderOptions`
