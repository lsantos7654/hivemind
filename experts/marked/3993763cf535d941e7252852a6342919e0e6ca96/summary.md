# Marked — Repository Summary

## Repository Purpose and Goals

Marked is a fast, low-level Markdown compiler for JavaScript. Its primary goal is to convert Markdown source text into HTML as quickly as possible, without caching or blocking for long periods of time. The project strives to be lightweight while fully implementing all Markdown features from supported flavors and specifications (CommonMark, GitHub Flavored Markdown).

The library targets three runtime environments equally:
- **Browser** (via UMD and ESM bundles)
- **Node.js server** (ESM module, requires Node >= 20)
- **Command Line Interface** (the `marked` binary)

## Key Features and Capabilities

- **Speed-focused design**: Non-blocking, no caching, designed for throughput
- **GFM support**: GitHub Flavored Markdown enabled by default (`gfm: true`)
- **Async mode**: Optional Promise-based parsing for asynchronous `walkTokens` callbacks
- **Extensibility**: Four primary extension points — custom tokenizers, renderers, hooks, and `walkTokens`
- **Multiple output formats**: ESM (`lib/marked.esm.js`) and UMD (`lib/marked.umd.js`) bundles, plus TypeScript type declarations
- **Inline-only parsing**: `marked.parseInline()` skips block-level parsing for fragments
- **Pedantic mode**: Optional strict conformance to the original `markdown.pl` behavior
- **Worker-safe**: Can safely run in Node.js Worker Threads or browser Web Workers to avoid ReDoS
- **No built-in sanitization**: HTML output is unsanitized by design; users are expected to pipe through DOMPurify or similar

## Primary Use Cases and Target Audience

**Target audience**: JavaScript/TypeScript developers who need to render Markdown to HTML in web apps, Node.js servers, static site generators, or CLI tools.

**Common use cases**:
- Rendering user-submitted Markdown content in web applications
- Building documentation sites and static site generators
- CLI tools for converting `.md` files to HTML
- Embedding Markdown preview in text editors or IDEs
- Extending with syntax highlighting (`marked-highlight`), LaTeX math (`marked-katex-extension`), custom heading IDs (`marked-gfm-heading-id`), footnotes (`marked-footnote`), and many other community extensions

## High-Level Architecture Overview

Marked's architecture follows a classic compiler pipeline:

```
Input Markdown string
        │
   [Hooks.preprocess]
        │
    [Lexer / Tokenizer]
        │  produces TokensList (Token[])
   [Hooks.processAllTokens]
        │
    [walkTokens callbacks]
        │
    [Parser / Renderer]
        │  produces HTML string (or custom ParserOutput)
   [Hooks.postprocess]
        │
   Output HTML string
```

**Core classes:**

| Class | File | Role |
|-------|------|------|
| `Marked` | `src/Instance.ts` | Main class; holds options/extensions, orchestrates the pipeline |
| `_Lexer` | `src/Lexer.ts` | Block-level tokenization; drives `_Tokenizer` |
| `_Tokenizer` | `src/Tokenizer.ts` | Individual token-matching methods (fences, heading, list, etc.) |
| `_Parser` | `src/Parser.ts` | Token-tree traversal; dispatches to `_Renderer` |
| `_Renderer` | `src/Renderer.ts` | HTML generation for each token type |
| `_TextRenderer` | `src/TextRenderer.ts` | Plain-text fallback renderer (strips HTML) |
| `_Hooks` | `src/Hooks.ts` | Lifecycle hooks (preprocess, postprocess, etc.) |

**Top-level `marked` export** (`src/marked.ts`) is a singleton `Marked` instance with convenience function wrappers, making it usable as both `marked(src)` and `marked.parse(src)`.

**Extension system** (`marked.use()`): Extensions are merged non-destructively. Each new extension wraps the previous handler and can return `false` to fall back, enabling layered override chains. This design implements a middleware/chain-of-responsibility pattern.

## Related Projects and Dependencies

**Runtime dependencies**: None — Marked ships with zero production dependencies.

**Dev dependencies** (build/test only):
- `typescript` + `dts-bundle-generator` — TypeScript compilation and type bundling
- `esbuild` + `esbuild-plugin-umd-wrapper` — Fast bundling to ESM and UMD
- `semantic-release` — Automated versioned releases via conventional commits
- `commonmark` — Used to run the CommonMark specification test suite
- `marked-highlight` — Used in tests/benchmarks for code highlighting
- `recheck` — ReDoS vulnerability detection on regex patterns

**Ecosystem extensions** (official and community):
- `marked-highlight` — Syntax highlighting via highlight.js / Shiki / etc.
- `marked-gfm-heading-id` — GitHub-style `id` attributes on headings
- `marked-mangle` — Obfuscate email addresses
- `marked-footnote` — GFM footnote syntax
- `marked-base-url` — Prefix relative URLs
- `marked-katex-extension` — LaTeX math rendering
- `marked-emoji` — GitHub-style emoji support
- `marked-smartypants` — Typographic punctuation
- `marked-xhtml` — XHTML-compliant void element tags
- Many more listed at `docs/USING_ADVANCED.md`
