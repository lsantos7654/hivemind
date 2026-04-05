# LLM Scraper — Repository Summary

## Purpose and Goals

LLM Scraper (`llm-scraper`) is a TypeScript library that enables extraction of structured, typed data from any webpage by leveraging Large Language Models (LLMs). Rather than writing brittle CSS selectors or XPath queries, developers define a Zod or JSON Schema, point the library at a Playwright `Page`, and receive strongly-typed structured output that matches the schema. The library bridges Playwright-based browser automation with the Vercel AI SDK to turn unstructured web content into machine-readable data.

The project is at version 2.0.0 and was updated to use Vercel AI SDK 6, reflecting a commitment to staying current with the fast-moving AI tooling ecosystem.

## Key Features and Capabilities

- **Multi-provider LLM support**: Works with any provider supported by the Vercel AI SDK — OpenAI (GPT-4o, etc.), Anthropic (Claude Sonnet), Google (Gemini), Groq (Llama), and local models via Ollama. Provider selection is a single constructor argument.
- **Schema-defined extraction**: Schemas are expressed with Zod v4 or raw JSON Schema via AI SDK's `jsonSchema()` helper, giving full type inference in TypeScript.
- **Six content formatting modes**: Controls how webpage content is converted before being sent to the LLM:
  - `html` — pre-processed HTML with noise removed (scripts, styles, forms stripped)
  - `raw_html` — full unprocessed HTML from Playwright's `page.content()`
  - `markdown` — HTML body converted to Markdown via `turndown`
  - `text` — readable text extracted with Mozilla Readability (via CDN import in browser)
  - `image` — base64 screenshot for multimodal models
  - `custom` — caller-supplied function returns any string content
- **Streaming support**: The `stream()` method returns a `partialOutputStream` async iterator for incremental delivery of partial objects as they are generated.
- **Code generation**: The `generate()` method asks the LLM to produce a reusable Playwright IIFE JavaScript snippet that programmatically extracts data matching the schema, bypassing the LLM on subsequent runs.
- **Full TypeScript type safety**: Generic output types flow through all API methods, ensuring the returned `data` field is typed to match the provided schema.
- **AI SDK tool integration**: Can be composed as a tool inside a larger `generateText` agent loop (see `examples/toolUse.ts`).

## Primary Use Cases and Target Audience

**Target audience**: TypeScript developers building data pipelines, research tools, monitoring systems, or any application that needs to reliably extract structured information from websites without maintaining fragile scrapers.

**Use cases**:
- Extracting product data, prices, or reviews from e-commerce pages
- Monitoring news feeds, aggregators, or social platforms for structured content
- Converting arbitrary HTML documentation into structured records
- Building AI agents that browse and collect information from multiple URLs
- One-off research tasks requiring structured output from web pages
- Generating reusable scraping scripts to reduce LLM costs on repeated visits

## High-Level Architecture Overview

The library is composed of three layers:

1. **Entry point / public API** (`src/index.ts`): The `LLMScraper` class holds a reference to a Vercel AI SDK `LanguageModel` instance and exposes three async methods: `run()`, `stream()`, and `generate()`. Each method delegates preprocessing to `src/preprocess.ts` and then calls the appropriate model function from `src/models.ts`.

2. **Preprocessing layer** (`src/preprocess.ts` + `src/cleanup.ts`): Accepts a Playwright `Page` and a format option. Converts the live browser page to the requested text or binary representation. For the `html` format, it first injects and executes a DOM cleanup script (`src/cleanup.ts`) that removes noise elements and attributes directly in the browser context before serializing the HTML.

3. **LLM interaction layer** (`src/models.ts`): Wraps Vercel AI SDK's `generateText` and `streamText` calls. Constructs the prompt (system prompt + page content as user message), selects between structured object/array output and plain-text code generation, and returns typed results.

The library intentionally has no routing, HTTP server, CLI, or persistence layer — it is purely a composable TypeScript module meant to be embedded in larger applications or scripts.

## Related Projects and Dependencies

**Runtime dependencies**:
- `ai` (Vercel AI SDK v6) — core LLM abstraction, `generateText`, `streamText`, `Output`, type definitions
- `@ai-sdk/provider` — provider interface types shared across AI SDK packages
- `turndown` — HTML-to-Markdown conversion for the `markdown` format
- `playwright` (peer/dev) — browser automation; callers are expected to manage browser lifecycle
- `@mozilla/readability` — loaded dynamically from CDN in browser context for `text` format

**Dev/optional provider packages** (not bundled, user installs as needed):
- `@ai-sdk/openai`, `@ai-sdk/anthropic`, `@ai-sdk/google` — official AI SDK providers
- `ollama-ai-provider-v2` — community provider for local Ollama models
- `zod` — schema definition (v4 compatible)

**Related ecosystem projects**:
- [Vercel AI SDK](https://github.com/vercel/ai) — the underlying LLM abstraction this library is built on
- [Playwright](https://playwright.dev) — browser automation used for page navigation and content extraction
- [Turndown](https://github.com/mixmark-io/turndown) — Markdown conversion
- [Mozilla Readability](https://github.com/mozilla/readability) — article text extraction
