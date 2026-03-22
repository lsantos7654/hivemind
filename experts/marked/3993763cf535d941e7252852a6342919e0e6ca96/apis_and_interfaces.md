# Marked — APIs and Interfaces

## Public Entry Points

### Primary Import (ESM)
```js
import { marked } from 'marked';
// or
import { Marked, Lexer, Parser, Renderer, Tokenizer, Hooks } from 'marked';
```

### Browser (UMD via CDN)
```html
<script src="https://cdn.jsdelivr.net/npm/marked/lib/marked.umd.js"></script>
<!-- Global: window.marked -->
```

### CLI
```sh
marked -o output.html input.md
echo "# hello" | marked
```

---

## Core Functions

### `marked(src, options?)` / `marked.parse(src, options?)`

Compiles Markdown to HTML. Synchronous by default; returns a Promise when `async: true`.

```ts
// Synchronous
function marked(src: string, options?: MarkedOptions): string;
// Async (when async option is true)
function marked(src: string, options: MarkedOptions & { async: true }): Promise<string>;
```

**Source**: `src/marked.ts:38`

```js
import { marked } from 'marked';

const html = marked('# Hello\n\nworld');
// → '<h1>Hello</h1>\n<p>world</p>\n'

const html = await marked.parse('# Hello', { async: true });
```

### `marked.parseInline(src, options?)`

Parses inline Markdown only (no block-level wrapping — no `<p>` tags).

```js
const html = marked.parseInline('**bold** and _italic_');
// → '<strong>bold</strong> and <em>italic</em>'
```

**Source**: `src/marked.ts:88`

### `marked.use(...extensions)`

Extends the global marked instance. Merges renderer, tokenizer, hooks, walkTokens, and custom extensions.

```js
marked.use({ gfm: true, breaks: false, renderer: { heading({ tokens, depth }) { ... } } });
```

**Source**: `src/marked.ts:66` / `src/Instance.ts:76`

### `marked.setOptions(options)` / `marked.options(options)`

Sets global options. Shallow-merges with current defaults.

```js
marked.setOptions({ gfm: true, breaks: true });
```

**Source**: `src/marked.ts:47`

### `marked.walkTokens(tokens, callback)`

Walks every token in a token tree, calling `callback` for each. Supports async callbacks when used with `async: true`.

```js
marked.walkTokens(tokens, (token) => {
  if (token.type === 'heading') token.depth += 1;
});
```

**Source**: `src/Instance.ts:38`

### `marked.lexer(src, options?)` / `_Lexer.lex(src, options?)`

Tokenizes Markdown into a `TokensList` without rendering.

```js
const tokens = marked.lexer('# Heading\n\n- item');
console.log(tokens[0]); // { type: 'heading', depth: 1, text: 'Heading', ... }
```

**Source**: `src/Lexer.ts:72`

### `marked.parser(tokens, options?)` / `_Parser.parse(tokens, options?)`

Renders a `TokensList` to HTML without re-lexing.

```js
const html = marked.parser(tokens);
```

**Source**: `src/Parser.ts:26`

---

## `Marked` Class (for isolated instances)

Use `new Marked()` to avoid mutating the global singleton:

```js
import { Marked } from 'marked';

const marked = new Marked({ gfm: true });
marked.use(myExtension);

const html = marked.parse('# Hello');
```

**Source**: `src/Instance.ts:17`

```ts
class Marked<ParserOutput = string, RendererOutput = string> {
  defaults: MarkedOptions<ParserOutput, RendererOutput>;
  parse: (src: string, options?: MarkedOptions) => ParserOutput | Promise<ParserOutput>;
  parseInline: (src: string, options?: MarkedOptions) => ParserOutput | Promise<ParserOutput>;
  use(...extensions: MarkedExtension[]): this;
  setOptions(opt: MarkedOptions): this;
  lexer(src: string, options?: MarkedOptions): TokensList;
  parser(tokens: Token[], options?: MarkedOptions): ParserOutput;
  walkTokens(tokens: Token[], callback: (token: Token) => MaybePromise): MaybePromise[];
}
```

---

## Configuration Options (`MarkedOptions`)

**Source**: `src/MarkedOptions.ts:117` / `src/defaults.ts`

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `async` | `boolean` | `false` | If `true`, `parse()` returns a Promise; `walkTokens` can be async |
| `breaks` | `boolean` | `false` | Add `<br>` on single line breaks (requires `gfm: true`) |
| `gfm` | `boolean` | `true` | GitHub Flavored Markdown spec |
| `pedantic` | `boolean` | `false` | Strict markdown.pl conformance; overrides `gfm` |
| `silent` | `boolean` | `false` | Return error as HTML string instead of throwing |
| `renderer` | `_Renderer` | `new Renderer()` | Custom renderer instance |
| `tokenizer` | `_Tokenizer` | `new Tokenizer()` | Custom tokenizer instance |
| `hooks` | `_Hooks` | `null` | Lifecycle hooks instance |
| `walkTokens` | `function` | `null` | Per-token callback |
| `extensions` | `object` | `null` | Custom extension registrations (internal format) |

---

## Extension System (`marked.use()`)

### `MarkedExtension` Interface

**Source**: `src/MarkedOptions.ts:52`

```ts
interface MarkedExtension<ParserOutput = string, RendererOutput = string> {
  async?: boolean;
  breaks?: boolean;
  gfm?: boolean;
  pedantic?: boolean;
  silent?: boolean;
  renderer?: RendererObject;     // Override existing renderer methods
  tokenizer?: TokenizerObject;   // Override existing tokenizer methods
  hooks?: HooksObject;           // Override lifecycle hooks
  walkTokens?: (token: Token) => void | Promise<void>;
  extensions?: TokenizerAndRendererExtension[]; // Add new token types
}
```

### Renderer Override Example

```js
// Override heading renderer to add anchor links
marked.use({
  renderer: {
    heading({ tokens, depth }) {
      const text = this.parser.parseInline(tokens);
      const id = text.toLowerCase().replace(/[^\w]+/g, '-');
      return `<h${depth} id="${id}">${text}</h${depth}>\n`;
    }
  }
});
```

Renderer methods can return `false` to fall through to the previously registered renderer.

### Tokenizer Override Example

```js
// Override codespan to handle LaTeX $...$
marked.use({
  tokenizer: {
    codespan(src) {
      const match = src.match(/^\$+([^\$\n]+?)\$+/);
      if (match) return { type: 'codespan', raw: match[0], text: match[1].trim() };
      return false; // fall back to default
    }
  }
});
```

### Custom Extension (new token type)

```js
// Add custom block-level token
marked.use({
  extensions: [{
    name: 'myBlock',
    level: 'block',
    start(src) { return src.indexOf(':::'); },
    tokenizer(src, tokens) {
      const match = /^:::([^\n]*)\n([\s\S]*?):::/.exec(src);
      if (match) {
        return {
          type: 'myBlock',
          raw: match[0],
          label: match[1].trim(),
          tokens: []
        };
      }
    },
    renderer(token) {
      return `<div class="block ${token.label}">${this.parser.parse(token.tokens)}</div>`;
    },
    childTokens: ['tokens']
  }]
});
```

**Source**: `src/MarkedOptions.ts:16-35`

**`TokenizerExtension` fields:**
- `name: string` — identifies the token type
- `level: 'block' | 'inline'` — when in the pipeline to run
- `start?(src): number | void` — hints the lexer where the token might begin
- `tokenizer(src, tokens): Tokens.Generic | undefined` — produces the token
- `childTokens?: string[]` — token properties to walk via `walkTokens`

---

## Hooks API

**Source**: `src/Hooks.ts:7`

Available hooks (override via `marked.use({ hooks: { ... } })`):

| Hook | Signature | Description |
|------|-----------|-------------|
| `preprocess` | `(markdown: string) => string` | Transform raw Markdown before lexing |
| `postprocess` | `(html: ParserOutput) => ParserOutput` | Transform HTML after parsing |
| `processAllTokens` | `(tokens: Token[]) => Token[]` | Modify token list before walkTokens |
| `emStrongMask` | `(src: string) => string` | Mask content so `_` and `*` aren't treated as em/strong |
| `provideLexer` | `() => (src, options?) => TokensList` | Provide a custom lexer function |
| `provideParser` | `() => (tokens, options?) => ParserOutput` | Provide a custom parser function |

```js
// Example: front-matter preprocessing
marked.use({
  hooks: {
    preprocess(markdown) {
      // strip front-matter before parsing
      return markdown.replace(/^---[\s\S]*?---\n/, '');
    },
    postprocess(html) {
      // sanitize output
      return DOMPurify.sanitize(html);
    }
  }
});
```

---

## Token Types (`Tokens` Namespace)

**Source**: `src/Tokens.ts`

All token types share `type: string` and `raw: string`. Key types:

| Token | Key fields |
|-------|-----------|
| `Tokens.Heading` | `depth: number`, `text: string`, `tokens: Token[]` |
| `Tokens.Code` | `lang?: string`, `text: string`, `codeBlockStyle?: 'indented'` |
| `Tokens.List` | `ordered: boolean`, `start: number | ''`, `items: ListItem[]` |
| `Tokens.ListItem` | `task: boolean`, `checked?: boolean`, `tokens: Token[]` |
| `Tokens.Table` | `align: Array<'left' | 'center' | 'right' | null>`, `header: TableCell[]`, `rows: TableCell[][]` |
| `Tokens.Link` | `href: string`, `title?: string | null`, `tokens: Token[]` |
| `Tokens.Image` | `href: string`, `title: string | null`, `text: string`, `tokens: Token[]` |
| `Tokens.Blockquote` | `text: string`, `tokens: Token[]` |
| `Tokens.Strong` | `text: string`, `tokens: Token[]` |
| `Tokens.Em` | `text: string`, `tokens: Token[]` |
| `Tokens.Codespan` | `text: string` |
| `Tokens.HTML` | `pre: boolean`, `text: string`, `block: boolean` |
| `Tokens.Generic` | `[index: string]: any`, `type: string`, `tokens?: Token[]` |
| `TokensList` | `Token[] & { links: Links }` |

---

## `_Renderer` Methods

**Source**: `src/Renderer.ts`

**Block-level** (called by `_Parser.parse()`):
- `space(token)` → `''`
- `code({ text, lang, escaped })` → `<pre><code>...</code></pre>`
- `blockquote({ tokens })` → `<blockquote>...</blockquote>`
- `html({ text })` → raw HTML passthrough
- `heading({ tokens, depth })` → `<h1>...<h6>`
- `hr(token)` → `<hr>`
- `list(token)` → `<ul>` or `<ol>`
- `listitem(item)` → `<li>`
- `checkbox({ checked })` → `<input type="checkbox">`
- `paragraph({ tokens })` → `<p>`
- `table(token)` → `<table>`
- `tablerow({ text })` → `<tr>`
- `tablecell(token)` → `<td>` or `<th>`

**Inline-level** (called by `_Parser.parseInline()`):
- `strong({ tokens })` → `<strong>`
- `em({ tokens })` → `<em>`
- `codespan({ text })` → `<code>`
- `br(token)` → `<br>`
- `del({ tokens })` → `<del>`
- `link({ href, title, tokens })` → `<a>`
- `image({ href, title, text })` → `<img>`
- `text(token)` → escaped text or inline tokens

---

## `walkTokens` Pattern

```js
// Async walkTokens example: validate links
marked.use({
  async: true,
  async walkTokens(token) {
    if (token.type === 'link') {
      try {
        const res = await fetch(token.href, { method: 'HEAD' });
        if (!res.ok) token.title = 'broken link';
      } catch {
        token.title = 'unreachable';
      }
    }
  }
});

const html = await marked.parse(markdownString);
```

**Source**: `src/MarkedOptions.ts:114`, `src/Instance.ts:38`

---

## Integration Patterns

### Multiple Extensions
```js
import { marked } from 'marked';
import markedHighlight from 'marked-highlight';
import hljs from 'highlight.js';

marked.use(markedHighlight({
  langPrefix: 'hljs language-',
  highlight(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext';
    return hljs.highlight(code, { language }).value;
  }
}));
```

### Isolated Instance (avoids global mutation)
```js
import { Marked } from 'marked';

const customMarked = new Marked(
  { gfm: true },
  myExtension1,
  myExtension2
);

// customMarked is completely isolated from the global `marked` singleton
const html = customMarked.parse('# hello');
```

### Direct Lexer/Parser Access
```js
import { Lexer, Parser } from 'marked';

const lexer = new Lexer({ gfm: true });
const tokens = lexer.lex('# Heading\n\nParagraph');
console.log(tokens);

const html = Parser.parse(tokens);
```

### Worker Thread Usage (ReDoS mitigation)
```js
// markedWorker.js
import { marked } from 'marked';
import { parentPort } from 'worker_threads';
parentPort.on('message', (md) => parentPort.postMessage(marked.parse(md)));
```
