# openai-node — Code Structure

## Annotated Directory Tree

```
openai-node/
├── src/                          # All TypeScript source code
│   ├── index.ts                  # Public package entry point; re-exports OpenAI, AzureOpenAI, error types, APIPromise
│   ├── client.ts                 # Core OpenAI class, ClientOptions interface, HTTP engine
│   ├── azure.ts                  # AzureOpenAI subclass; Azure-specific auth and URL construction
│   ├── version.ts                # Exports VERSION constant ("6.32.0")
│   ├── error.ts                  # Re-exports error classes (thin shim to core/error.ts)
│   ├── api-promise.ts            # Re-export of core/api-promise (shim for compatibility)
│   ├── streaming.ts              # Re-export of core/streaming (shim)
│   ├── pagination.ts             # Re-export of core/pagination (shim)
│   ├── uploads.ts                # Re-export of core/uploads (shim)
│   ├── resource.ts               # Re-export of core/resource (shim)
│   ├── resources.ts              # Re-exports all resource classes
│   │
│   ├── core/                     # Core SDK machinery
│   │   ├── api-promise.ts        # APIPromise<T>: wraps fetch Promise with .withResponse(), .asResponse(), streaming
│   │   ├── error.ts              # All error classes: APIError, BadRequestError, RateLimitError, etc.
│   │   ├── pagination.ts         # AbstractPage, CursorPage, ConversationCursorPage (async iterable pagination)
│   │   ├── resource.ts           # APIResource base class (holds _client reference)
│   │   ├── streaming.ts          # Stream<T>: SSE/NDJSON async iterable wrapper
│   │   ├── uploads.ts            # Uploadable type, toFile() helper, multipart form building
│   │   └── README.md             # Notes on core module design
│   │
│   ├── internal/                 # Private implementation details (not part of public API)
│   │   ├── builtin-types.ts      # Type aliases for global Web API types (RequestInit, fetch, etc.)
│   │   ├── detect-platform.ts    # isRunningInBrowser(), getPlatformHeaders() for User-Agent
│   │   ├── errors.ts             # castToError(), isAbortError() utilities
│   │   ├── headers.ts            # HeadersLike type, buildHeaders(), NullableHeaders merging
│   │   ├── parse.ts              # HTTP response parsing: defaultParseResponse, WithRequestID
│   │   ├── request-options.ts    # RequestOptions, FinalRequestOptions types
│   │   ├── shim-types.ts         # ReadableStream type shim for cross-runtime compat
│   │   ├── shims.ts              # Runtime shims (FormData, File, Blob detection)
│   │   ├── stream-utils.ts       # lineDecoder, SSE chunking utilities
│   │   ├── to-file.ts            # toFile() implementation internals
│   │   ├── types.ts              # HTTPMethod, PromiseOrValue, MergedRequestInit, etc.
│   │   ├── uploads.ts            # Upload helpers, checkFileSupport()
│   │   ├── utils.ts              # Re-exports from utils/* submodules
│   │   ├── decoders/
│   │   │   └── line.ts           # Line-by-line stream decoder for SSE parsing
│   │   ├── qs/                   # Vendored query-string serializer (qs fork)
│   │   │   ├── index.ts
│   │   │   ├── stringify.ts
│   │   │   ├── formats.ts
│   │   │   ├── types.ts
│   │   │   └── utils.ts
│   │   └── utils/
│   │       ├── base64.ts         # base64 encode/decode utilities
│   │       ├── bytes.ts          # Byte array utilities
│   │       ├── env.ts            # readEnv() — reads environment variables safely
│   │       ├── log.ts            # Logger, LogLevel, loggerFor(), formatRequestDetails()
│   │       ├── path.ts           # URL path joining utility
│   │       ├── query.ts          # stringifyQuery() for query parameter serialization
│   │       ├── sleep.ts          # sleep() Promise utility
│   │       ├── uuid.ts           # uuid4() UUID generator
│   │       └── values.ts         # validatePositiveInteger, isAbsoluteURL, safeJSON, isEmptyObj, maybeObj
│   │
│   ├── lib/                      # High-level helpers and streaming abstractions
│   │   ├── AbstractChatCompletionRunner.ts   # Base class for tool-call loop runners
│   │   ├── ChatCompletionRunner.ts           # Non-streaming tool call runner (.runTools())
│   │   ├── ChatCompletionStream.ts           # Streaming chat completion with events
│   │   ├── ChatCompletionStreamingRunner.ts  # Streaming runner with tool call loop
│   │   ├── AssistantStream.ts               # Streaming runner for Assistants API
│   │   ├── EventEmitter.ts                   # Typed EventEmitter base class
│   │   ├── EventStream.ts                    # Async event stream abstraction
│   │   ├── RunnableFunction.ts               # RunnableFunctionWithParse / WithoutParse types
│   │   ├── ResponsesParser.ts                # Structured output parsing for Responses API
│   │   ├── parser.ts                         # AutoParseableResponseFormat, makeParseableTool, makeParseableResponseFormat
│   │   ├── jsonschema.ts                     # JSONSchema type definitions
│   │   ├── transform.ts                      # toStrictJsonSchema() — enforces OpenAI strict mode constraints
│   │   ├── Util.ts                           # Utility functions for lib
│   │   ├── chatCompletionUtils.ts            # Chat completion message/content utilities
│   │   └── responses/
│   │       ├── ResponseStream.ts             # ResponseStream class for Responses API streaming
│   │       └── EventTypes.ts                 # Typed event interfaces for Response streams
│   │
│   ├── helpers/                  # End-user utility helpers
│   │   ├── audio.ts              # playAudio(), recordAudio() — Node.js ffplay/ffmpeg wrappers
│   │   └── zod.ts                # zodResponseFormat(), zodTextFormat(), zodFunction() — Zod → OpenAI schema
│   │
│   ├── realtime/                 # Realtime WebSocket API client
│   │   ├── index.ts              # Re-exports
│   │   ├── internal-base.ts      # OpenAIRealtimeEmitter base, buildRealtimeURL(), isAzure()
│   │   ├── websocket.ts          # OpenAIRealtimeWebSocket — browser WebSocket transport
│   │   └── ws.ts                 # OpenAIRealtimeWS — Node.js `ws` package transport
│   │
│   ├── beta/                     # Beta realtime path aliases (points to realtime/)
│   │   └── realtime/
│   │       ├── index.ts
│   │       ├── internal-base.ts
│   │       ├── websocket.ts
│   │       └── ws.ts
│   │
│   ├── _vendor/                  # Vendored third-party code
│   │   ├── partial-json-parser/  # Partial JSON parser for streaming structured outputs
│   │   │   ├── parser.ts
│   │   │   └── README.md
│   │   └── zod-to-json-schema/   # Zod v3 → JSON Schema converter (vendored for customization)
│   │       ├── index.ts
│   │       ├── zodToJsonSchema.ts
│   │       ├── Refs.ts
│   │       ├── Options.ts
│   │       ├── parseDef.ts
│   │       └── parsers/          # One file per Zod type (string, number, array, object, etc.)
│   │
│   └── resources/                # One file/directory per API resource (auto-generated)
│       ├── index.ts              # Re-exports all resource classes and types
│       ├── shared.ts             # Shared types: AllModels, ChatModel, FunctionDefinition, etc.
│       ├── audio/                # Audio API: speech, transcriptions, translations
│       ├── batches.ts            # Batch processing
│       ├── chat/
│       │   ├── chat.ts           # Chat resource namespace
│       │   ├── index.ts
│       │   └── completions/      # ChatCompletions, ChatCompletionChunk, all ChatCompletion* types
│       │       ├── completions.ts
│       │       ├── messages.ts
│       │       └── index.ts
│       ├── completions.ts        # Legacy text completions (GPT-3 style)
│       ├── containers/           # Container management
│       ├── conversations/        # Conversation items
│       ├── embeddings.ts         # Embeddings
│       ├── evals/                # Model evaluations and runs
│       ├── files.ts              # File upload/retrieval/deletion
│       ├── fine-tuning/          # Fine-tuning jobs, checkpoints, methods, alpha graders
│       ├── graders/              # Grader models for evals
│       ├── images.ts             # Image generation and editing (DALL-E)
│       ├── models.ts             # Model listing and retrieval
│       ├── moderations.ts        # Content moderation
│       ├── realtime/             # Realtime sessions, calls, client-secrets
│       ├── responses/            # Responses API — primary generation endpoint
│       │   ├── responses.ts      # Responses class, ParsedResponse types
│       │   ├── input-items.ts    # InputItems sub-resource
│       │   ├── input-tokens.ts   # InputTokens sub-resource
│       │   ├── internal-base.ts  # Shared Responses streaming infrastructure
│       │   ├── ws.ts             # WebSocket transport for Responses streaming
│       │   └── index.ts
│       ├── skills/               # Skills management (versions, content)
│       ├── uploads/              # Multipart upload sessions and parts
│       ├── vector-stores/        # Vector store CRUD, file batches
│       ├── videos.ts             # Video generation and editing
│       ├── webhooks/             # Webhook signature verification
│       └── beta/                 # Beta APIs
│           ├── assistants.ts     # Assistants
│           ├── threads/          # Threads, Messages, Runs, Run Steps
│           ├── realtime/         # Beta Realtime sessions and transcription
│           └── chatkit/          # Beta ChatKit sessions and threads
│
├── tests/                        # Jest test suite
├── examples/                     # Usage examples
├── ecosystem-tests/              # Integration tests for various runtimes
├── scripts/                      # Build, test, lint, format shell scripts
│   ├── build                     # Main build script (calls tsc-multi)
│   ├── test                      # Test runner
│   ├── lint                      # ESLint runner
│   ├── format                    # Prettier runner
│   └── utils/                    # Helper scripts (git swap, check-is-in-git-install)
├── api.md                        # Full API reference (methods + types, auto-generated)
├── azure.md                      # Azure OpenAI usage guide
├── helpers.md                    # Helpers API documentation
├── realtime.md                   # Realtime API guide
├── package.json                  # Package manifest (name: "openai", version: "6.32.0")
├── tsconfig.json                 # Development TypeScript config (strict mode, noEmit)
├── tsconfig.build.json           # Build TypeScript config
├── tsconfig.deno.json            # Deno-specific TypeScript config
├── tsconfig.dist-src.json        # dist-src TypeScript config
├── tsc-multi.json                # tsc-multi config: builds CJS (.js) and ESM (.mjs) targets
├── jest.config.ts                # Jest config with @swc/jest transform
├── eslint.config.mjs             # ESLint flat config
└── yarn.lock                     # Yarn 1.x lockfile
```

## Module and Package Organization

The codebase uses a layered architecture:

1. **Public surface** (`src/index.ts`, `src/resources/`): All exported types and resource classes. Generated by Stainless; do not edit manually.
2. **Core SDK** (`src/core/`): `APIPromise`, `Stream`, `AbstractPage`, and error hierarchy. Runtime behavior.
3. **Internal utilities** (`src/internal/`): Not part of the public API. Platform shims, header handling, logging, query serialization.
4. **High-level helpers** (`src/lib/`): `ChatCompletionRunner`, `ResponseStream`, `parser.ts` — built on top of core for ergonomic streaming and tool calling.
5. **User-facing helpers** (`src/helpers/`): `audio.ts` (play/record), `zod.ts` (Zod schema conversion).
6. **Realtime** (`src/realtime/`): WebSocket clients distinct from HTTP resources.
7. **Vendored code** (`src/_vendor/`): Modified third-party libraries bundled for stability.

## Code Organization Patterns

- **Stainless-generated files** begin with `// File generated from our OpenAPI spec by Stainless.` — do not edit directly.
- **Each API resource** lives in `src/resources/<name>.ts` or `src/resources/<name>/` (when it has sub-resources). The directory form includes `index.ts` + `<name>.ts` + sub-resource files.
- **Shim pattern**: Root-level files like `src/streaming.ts`, `src/pagination.ts`, etc. are thin re-exports of their `src/core/` counterparts, preserving backward-compatible import paths (`import { Stream } from 'openai/streaming'`).
- **Index barrel pattern**: Each `src/resources/*/index.ts` re-exports everything from sibling files, enabling tree-shaking.
- **Dual CJS/ESM build**: `tsc-multi.json` compiles to both `dist/*.js` (CommonJS) and `dist/*.mjs` (ESM), allowing `require()` and `import` from the same package. The `exports` field in `package.json` maps both.
- **Strict TypeScript**: All compiler strict flags are enabled. `exactOptionalPropertyTypes` and `noUncheckedIndexedAccess` are on.
