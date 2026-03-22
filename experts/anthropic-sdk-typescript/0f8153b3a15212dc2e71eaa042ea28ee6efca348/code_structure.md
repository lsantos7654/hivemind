# Code Structure: @anthropic-ai/sdk

## Annotated Directory Tree

```
anthropic-sdk-typescript/
├── src/                              # Main SDK source (TypeScript)
│   ├── index.ts                      # Public entry point — re-exports all public API
│   ├── client.ts                     # BaseAnthropic + Anthropic client classes + ClientOptions
│   ├── version.ts                    # VERSION constant ("0.80.0")
│   ├── error.ts                      # Re-exports from core/error (backwards compat shim)
│   ├── streaming.ts                  # Re-exports from core/streaming (backwards compat shim)
│   ├── pagination.ts                 # Re-exports from core/pagination (backwards compat shim)
│   ├── resource.ts                   # Re-exports from core/resource (backwards compat shim)
│   ├── api-promise.ts                # Re-exports from core/api-promise (backwards compat shim)
│   ├── uploads.ts                    # Re-exports from core/uploads (backwards compat shim)
│   ├── resources.ts                  # Re-exports from resources/index
│   │
│   ├── core/                         # Foundational SDK infrastructure
│   │   ├── api-promise.ts            # APIPromise<T> wrapping fetch + response parsing
│   │   ├── error.ts                  # Full error class hierarchy (AnthropicError → APIError → subclasses)
│   │   ├── pagination.ts             # Page, PageCursor, TokenPage iterables; PagePromise
│   │   ├── resource.ts               # APIResource base class (holds client reference)
│   │   ├── streaming.ts              # Stream<T> async iterable over SSE events
│   │   ├── uploads.ts                # Uploadable type, toFile() helper, multipart form
│   │   └── README.md                 # Notes on shared core layer
│   │
│   ├── internal/                     # Private implementation utilities
│   │   ├── builtin-types.ts          # TypeScript re-exports of platform built-in types
│   │   ├── constants.ts              # MODEL_NONSTREAMING_TOKENS map (model → token limit)
│   │   ├── detect-platform.ts        # Platform detection for User-Agent headers
│   │   ├── errors.ts                 # castToError(), isAbortError() utilities
│   │   ├── headers.ts                # buildHeaders() — merges header sources
│   │   ├── parse.ts                  # Response parsing, APIResponseProps
│   │   ├── request-options.ts        # RequestOptions type, merging utilities
│   │   ├── shim-types.ts             # TypeScript shim types for cross-platform compat
│   │   ├── shims.ts                  # Runtime shims (fetch, FormData, File, etc.)
│   │   ├── stream-utils.ts           # SSE line parsing, ReadableStream utilities
│   │   ├── to-file.ts                # toFile() implementation
│   │   ├── types.ts                  # HTTPMethod, PromiseOrValue, MergedRequestInit, etc.
│   │   ├── uploads.ts                # multipartFormRequestOptions() for file uploads
│   │   ├── utils.ts                  # Barrel re-export for all internal utils
│   │   ├── decoders/
│   │   │   ├── jsonl.ts              # JSONLDecoder — async iterable over JSONL streams
│   │   │   └── line.ts               # LineDecoder — splits byte stream into text lines
│   │   └── utils/
│   │       ├── base64.ts             # toBase64(), fromBase64() helpers
│   │       ├── bytes.ts              # Byte array utilities
│   │       ├── env.ts                # readEnv() — safe process.env accessor
│   │       ├── log.ts                # Logger interface, LogLevel, log utilities
│   │       ├── path.ts               # path`` template tag for URL path construction
│   │       ├── query.ts              # stringifyQuery() — query string serialization
│   │       ├── sleep.ts              # sleep(ms) promise utility
│   │       ├── uuid.ts               # uuid4() generator
│   │       └── values.ts             # validatePositiveInteger, isAbsoluteURL, safeJSON, isObj
│   │
│   ├── resources/                    # API resource classes (one per API endpoint group)
│   │   ├── index.ts                  # Barrel export of all resources
│   │   ├── shared.ts                 # Shared types across resources (ErrorObject, etc.)
│   │   ├── top-level.ts              # Top-level API types
│   │   ├── completions.ts            # Legacy text completions endpoint
│   │   ├── models.ts                 # Models resource + ModelInfo, ModelCapabilities types
│   │   ├── messages.ts               # Re-export shim for messages/
│   │   ├── beta.ts                   # Re-export shim for beta/
│   │   ├── messages/
│   │   │   ├── index.ts              # Barrel export
│   │   │   ├── messages.ts           # Messages resource: create(), stream(), parse(), countTokens()
│   │   │   └── batches.ts            # Batches resource: create(), retrieve(), list(), cancel(), delete(), results()
│   │   └── beta/
│   │       ├── index.ts              # Barrel export
│   │       ├── beta.ts               # Beta resource aggregator + beta error types
│   │       ├── files.ts              # Files resource: upload(), list(), retrieve(), delete()
│   │       ├── messages.ts           # Beta messages + toolRunner() method
│   │       ├── models.ts             # Beta models resource
│   │       ├── messages/
│   │       │   ├── index.ts          # Barrel export
│   │       │   ├── messages.ts       # Beta Messages resource with extended types
│   │       │   └── batches.ts        # Beta message batches
│   │       └── skills/
│   │           ├── index.ts          # Barrel export
│   │           ├── skills.ts         # Skills resource: create(), retrieve(), list(), delete()
│   │           └── versions.ts       # Skill versions resource
│   │
│   ├── lib/                          # High-level SDK helper abstractions
│   │   ├── MessageStream.ts          # MessageStream<ParsedT> — event-emitter + async iter over SSE
│   │   ├── BetaMessageStream.ts      # BetaMessageStream — MessageStream variant for beta API
│   │   ├── parser.ts                 # parseMessage(), AutoParseableOutputFormat, ParsedMessage types
│   │   ├── beta-parser.ts            # Beta variants of parser utilities
│   │   ├── transform-json-schema.ts  # Transforms Zod-generated JSON Schema for Claude compat
│   │   ├── stainless-helper-header.ts# SDK_HELPER_SYMBOL, collectStainlessHelpers() for x-stainless-helper header
│   │   └── tools/
│   │       ├── BetaRunnableTool.ts   # BetaRunnableTool<T> interface + Promisable type
│   │       ├── BetaToolRunner.ts     # BetaToolRunner<Stream> — async iter conversation loop
│   │       ├── CompactionControl.ts  # CompactionControl interface + DEFAULT_TOKEN_THRESHOLD/PROMPT
│   │       └── ToolError.ts          # ToolError class for structured tool error results
│   │
│   ├── helpers/                      # Public user-facing helper utilities
│   │   ├── index.ts                  # Barrel export for main helpers
│   │   ├── zod.ts                    # zodOutputFormat() — Zod → ParseableOutputFormat
│   │   ├── json-schema.ts            # jsonSchemaOutputFormat() — JSON Schema → ParseableOutputFormat
│   │   └── beta/
│   │       ├── zod.ts                # betaZodOutputFormat(), betaZodTool()
│   │       ├── json-schema.ts        # betaTool() — JSON Schema tool with type inference
│   │       ├── mcp.ts                # mcpTool/mcpTools/mcpMessage/mcpMessages/mcpContent/mcpResourceToContent/mcpResourceToFile
│   │       └── memory.ts             # betaMemoryTool() — memory_20250818 tool wrapper
│   │
│   ├── tools/
│   │   └── memory/
│   │       └── node.ts               # Node.js filesystem-backed memory tool implementation
│   │
│   └── _vendor/
│       └── partial-json-parser/
│           ├── parser.ts             # partialParse() — parse incomplete/streaming JSON
│           └── README.md
│
├── packages/                         # Platform-specific SDK sub-packages
│   ├── bedrock-sdk/                  # @anthropic-ai/bedrock-sdk — AWS Bedrock
│   │   └── src/
│   │       ├── client.ts             # AnthropicBedrock extends BaseAnthropic
│   │       ├── AWS_restJson1.ts      # AWS SigV4 signing + REST/JSON protocol
│   │       ├── index.ts
│   │       └── core/                 # Forked core layer for Bedrock-specific behavior
│   ├── vertex-sdk/                   # @anthropic-ai/vertex-sdk — Google Vertex AI
│   │   └── src/
│   │       ├── client.ts             # AnthropicVertex extends BaseAnthropic
│   │       ├── index.ts
│   │       └── core/                 # Forked core layer for Vertex-specific behavior
│   └── foundry-sdk/                  # @anthropic-ai/foundry-sdk — Anthropic Foundry
│       └── src/
│           ├── client.ts             # AnthropicFoundry extends BaseAnthropic
│           ├── index.ts
│           └── core/
│
├── tests/                            # Unit/integration tests
│   ├── index.test.ts                 # Client construction + request behavior tests
│   ├── streaming.test.ts             # Stream parsing tests
│   ├── responses.test.ts             # Response parsing tests
│   ├── uploads.test.ts               # File upload tests
│   ├── form.test.ts                  # Multipart form tests
│   ├── base64.test.ts                # Base64 utility tests
│   ├── buildHeaders.test.ts          # Header building tests
│   ├── path.test.ts                  # Path template tests
│   └── stringifyQuery.test.ts        # Query string tests
│
├── examples/                         # Runnable TypeScript examples
│   ├── demo.ts                       # Basic message creation
│   ├── streaming.ts                  # MessageStream usage
│   ├── raw-streaming.ts              # Low-level Stream<> usage
│   ├── tools.ts                      # Basic tool use
│   ├── tools-streaming.ts            # Streaming tool use
│   ├── tools-helpers-zod.ts          # betaZodTool() with BetaToolRunner
│   ├── tools-helpers-json-schema.ts  # betaTool() with BetaToolRunner
│   ├── tools-helpers-advanced.ts     # BetaToolRunner iteration patterns
│   ├── tools-helpers-advanced-streaming.ts # Streaming BetaToolRunner
│   ├── tools-helpers-memory.ts       # betaMemoryTool() usage
│   ├── structured-outputs-zod.ts     # zodOutputFormat() with parse()
│   ├── structured-outputs-json-schema.ts # jsonSchemaOutputFormat() with parse()
│   ├── structured-outputs-streaming.ts   # Streaming structured outputs
│   ├── structured-outputs-raw.ts     # Manual output parsing
│   ├── thinking.ts                   # Extended thinking
│   ├── thinking-stream.ts            # Streaming extended thinking
│   ├── mcp.ts                        # MCP tool integration
│   ├── web-search.ts                 # Web search tool
│   ├── web-search-stream.ts          # Streaming web search
│   ├── batch-results.ts              # Message batch processing
│   ├── count-tokens.ts               # Token counting
│   ├── cancellation.ts               # AbortController / stream cancellation
│   └── autoCompaction.ts             # CompactionControl in BetaToolRunner
│
├── scripts/                          # Build and tooling scripts (shell + Node)
│   ├── build                         # Main build script (tsc-multi → CJS+ESM)
│   ├── build-all                     # Builds main SDK + all sub-packages
│   ├── test                          # Jest test runner
│   ├── lint                          # ESLint runner
│   ├── format                        # Prettier formatter
│   ├── fast-format                   # Fast Prettier format (changed files only)
│   ├── bootstrap                     # yarn install + setup
│   ├── mock                          # Starts mock server via Prism
│   ├── detect-breaking-changes       # Checks API surface for breaking changes
│   └── publish-packages.ts           # npm publish automation
│
├── bin/
│   ├── cli                           # `anthropic-ai-sdk` CLI entry point
│   ├── migration-config.json         # Migration tool configuration
│   ├── check-release-environment     # Release environment checks
│   ├── publish-npm                   # npm publish wrapper
│   └── replace-internal-symlinks     # Symlink replacement for release
│
├── package.json                      # @anthropic-ai/sdk package manifest v0.80.0
├── tsconfig.json                     # TypeScript config (strict, target es2020, noEmit)
├── tsconfig.build.json               # Build-specific tsconfig (emits to dist/)
├── tsconfig.dist-src.json            # Tsconfig for dist/src (source maps)
├── tsconfig.deno.json                # Deno-specific tsconfig
├── tsc-multi.json                    # tsc-multi config: CJS (.js) + ESM (.mjs) targets
├── jest.config.ts                    # Jest config (ts-jest/esm preset, @swc/jest transform)
├── eslint.config.mjs                 # ESLint flat config
├── README.md                         # Quick start guide
├── helpers.md                        # Detailed helpers documentation (MessageStream, structured outputs, tools)
├── api.md                            # API surface documentation
├── MIGRATION.md                      # Migration guide from older versions
├── CHANGELOG.md                      # Release notes
└── CONTRIBUTING.md                   # Contribution guide (Stainless codegen workflow)
```

## Module and Package Organization

The SDK uses a **layered architecture** with clear separation between:

1. **`src/core/`** — shared infrastructure used by both the main SDK and sub-packages. Contains the HTTP client machinery, error hierarchy, pagination, and streaming primitives.
2. **`src/internal/`** — private utilities not intended for direct consumer use. Everything here is implementation detail.
3. **`src/resources/`** — API resource classes generated from the OpenAPI spec. Each maps to a URL namespace in the API (`/v1/messages`, `/v1/files`, etc.).
4. **`src/lib/`** — higher-level abstractions built on top of the resources layer: streaming event emitters, tool runner loop, parser utilities.
5. **`src/helpers/`** — optional user-facing utilities (Zod integration, JSON Schema, MCP). These import from `lib/` and `resources/` but are not generated — they are hand-authored.

## Code Organization Patterns

- **Stainless codegen**: All files with `// File generated from our OpenAPI spec by Stainless.` at the top are auto-generated. **Do not edit them directly** — changes must go through the OpenAPI spec.
- **Backwards compat shims**: Top-level files like `src/error.ts`, `src/streaming.ts`, `src/pagination.ts` simply re-export from `src/core/` to preserve import paths used in older SDK versions.
- **Dual package exports**: `package.json` `exports` map resolves `.mjs` for ESM consumers and `.js` for CJS consumers; both are emitted by `tsc-multi` from the same TypeScript source.
- **Private fields**: The codebase consistently uses ECMAScript private fields (`#field`) for internal state in classes like `MessageStream` and `BetaToolRunner`.
- **Index barrel files**: Each directory under `resources/` has an `index.ts` that re-exports everything for clean import paths.
