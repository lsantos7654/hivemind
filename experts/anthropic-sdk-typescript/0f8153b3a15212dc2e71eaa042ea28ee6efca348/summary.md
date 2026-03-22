# Summary: @anthropic-ai/sdk (Claude SDK for TypeScript)

## Repository Purpose and Goals

`@anthropic-ai/sdk` is the official TypeScript/JavaScript SDK for the Anthropic API, providing access to Claude AI models from server-side Node.js applications. Version **0.80.0**, the SDK is generated from Anthropic's OpenAPI specification using the [Stainless](https://stainlessapi.com/) code generator and published as the `@anthropic-ai/sdk` package on npm. Its goals are to provide a type-safe, ergonomic, and feature-complete interface to every capability of the Claude API, including messages, streaming, tool use, structured outputs, batch processing, file uploads, and beta features.

## Key Features and Capabilities

- **Messages API** — Send single-turn or multi-turn conversations to Claude; supports text, images, PDFs, and document inputs. Overloaded `create()` method returns either a `Message` or a `Stream` depending on the `stream` parameter.
- **Streaming** — `MessageStream` class provides an event-emitter + async-iterator interface over SSE streams. Events: `connect`, `streamEvent`, `text`, `citation`, `inputJson`, `thinking`, `message`, `contentBlock`, `finalMessage`, `error`, `abort`, `end`.
- **Tool Use (Function Calling)** — Define custom tools; the `BetaToolRunner` (accessed via `client.beta.messages.toolRunner()`) orchestrates the automatic conversation loop between assistant and tool execution, with optional streaming.
- **Structured Outputs** — Parse JSON responses using Zod schemas (`zodOutputFormat`) or raw JSON Schema (`jsonSchemaOutputFormat`). Use `client.messages.parse()` to get a `ParsedMessage` with `.parsed_output`.
- **Extended Thinking** — Support for `ThinkingBlock`, `ThinkingBlockParam`, `ThinkingConfigEnabled/Disabled/Adaptive` types; configurable via the `thinking` parameter on message creation.
- **Prompt Caching** — `CacheControlEphemeral` type on content blocks enables cache control at the API level.
- **Message Batches** — `client.messages.batches.create()` submits async batch jobs (up to 24-hour processing); results streamed via JSONL via `results()` method.
- **Files API (Beta)** — `client.beta.files` supports `upload()`, `list()`, `retrieve()`, `delete()` for persistent file management.
- **MCP Integration** — `mcpTool`, `mcpTools`, `mcpMessage`, `mcpMessages`, `mcpContent`, `mcpResourceToContent`, `mcpResourceToFile` helpers in `helpers/beta/mcp` bridge the Model Context Protocol SDK to Anthropic's API.
- **Memory Tool** — `betaMemoryTool()` helper in `helpers/beta/memory` wraps the built-in memory tool with typed handlers per command.
- **Context Compaction** — `CompactionControl` in `BetaToolRunner` auto-summarizes long conversation histories when token count exceeds a threshold.
- **Auto-pagination** — `Page` and `PageCursor` iterables for list endpoints (files, models, message batches, skills).
- **Platform Support** — CJS and ESM dual build; compatible with Node.js 18+, Deno (separate build target), and edge runtimes.
- **Skills API (Beta)** — `client.beta.skills` for creating, retrieving, listing, deleting, and versioning reusable skill definitions.

## Primary Use Cases and Target Audience

The SDK targets server-side TypeScript and JavaScript developers building:
- Conversational AI applications and chatbots
- Agentic systems using tool use and multi-step reasoning
- Batch content processing pipelines
- Applications integrating MCP (Model Context Protocol) tools
- Data extraction and structured-output workflows
- Applications deployed on AWS Bedrock, Google Cloud Vertex AI, or Anthropic Foundry (via sub-packages)

## High-Level Architecture Overview

The codebase follows a layered architecture:

1. **Entry point** — `src/index.ts` re-exports everything public; `src/client.ts` contains `BaseAnthropic` and `Anthropic` classes.
2. **Resources layer** — `src/resources/` mirrors the API surface: `messages/`, `beta/` (messages, files, skills, models), `completions`, `models`, `shared`. Each resource extends `APIResource` from `src/core/resource.ts`.
3. **Core layer** — `src/core/` provides `APIPromise`, `APIResource`, error classes, streaming, pagination, and upload utilities. These are shared across the main SDK and sub-packages.
4. **Internal layer** — `src/internal/` contains infrastructure: HTTP request building, response parsing, header management, platform detection, utilities (base64, env, path, query, sleep, uuid).
5. **Library helpers** — `src/lib/` contains `MessageStream`, `BetaMessageStream`, `parser`, `beta-parser`, tool runner infrastructure (`BetaToolRunner`, `BetaRunnableTool`, `CompactionControl`, `ToolError`).
6. **Public helpers** — `src/helpers/` provides high-level conveniences: `zod.ts`, `json-schema.ts`, and `beta/` variants for Zod, JSON Schema, MCP, and memory tool integration.
7. **Sub-packages** — `packages/bedrock-sdk`, `packages/vertex-sdk`, `packages/foundry-sdk` each extend `BaseAnthropic` with platform-specific auth and API routing.

## Related Projects and Dependencies

- **Runtime dependencies**: `json-schema-to-ts` (JSON Schema type inference)
- **Optional peer dependency**: `zod` ^3.25 or ^4.0 (for structured output helpers)
- **Sub-packages**: `@anthropic-ai/bedrock-sdk` (AWS Bedrock), `@anthropic-ai/vertex-sdk` (Google Vertex AI), `@anthropic-ai/foundry-sdk` (Anthropic Foundry)
- **Dev tooling**: TypeScript 5.8, tsc-multi (dual CJS/ESM builds), Jest + @swc/jest, ESLint, Prettier, nock (HTTP mocking), publint
- **Stainless**: Code generation from OpenAPI spec (see `CONTRIBUTING.md`)
- **MCP SDK**: `@modelcontextprotocol/sdk` is a dev dependency; helpers use duck-typed interfaces to avoid a hard runtime dependency
