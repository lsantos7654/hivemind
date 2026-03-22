# APIs and Interfaces: @anthropic-ai/sdk

## Public APIs and Entry Points

The SDK is imported as `@anthropic-ai/sdk` and sub-paths follow the pattern `@anthropic-ai/sdk/helpers/zod`, `@anthropic-ai/sdk/helpers/beta/mcp`, etc.

```ts
import Anthropic from '@anthropic-ai/sdk';
// or:
import { Anthropic, BaseAnthropic, type ClientOptions } from '@anthropic-ai/sdk';
```

## Key Classes, Functions, and Types

### `Anthropic` / `BaseAnthropic` — Client (`src/client.ts`)

The main entry point. `Anthropic` extends `BaseAnthropic` and wires up all resources.

```ts
const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,      // Default: process.env.ANTHROPIC_API_KEY
  authToken: '...',                           // Bearer token auth (alternative to apiKey)
  baseURL: 'https://api.anthropic.com',       // Default base URL
  maxRetries: 2,                              // Default: 2
  timeout: 60_000,                            // Default: 10 minutes (ms)
  defaultHeaders: { 'X-Custom': 'value' },   // Headers added to every request
  defaultQuery: { version: '...' },          // Query params added to every request
});

// Resource namespaces:
client.messages          // Messages + Batches
client.models            // Model listing
client.completions       // Legacy text completions
client.beta.messages     // Beta messages + toolRunner
client.beta.files        // Files API (beta)
client.beta.models       // Beta models
client.beta.skills       // Skills API (beta)
```

**`ClientOptions`** type (from `src/client.ts`):
- `apiKey?: string` — API key (reads `ANTHROPIC_API_KEY` env var by default)
- `authToken?: string` — Bearer token alternative
- `baseURL?: string` — API base URL override
- `maxRetries?: number` — Retry count for 429/5xx errors
- `timeout?: number` — Request timeout in milliseconds
- `defaultHeaders?: HeadersLike` — Headers merged into every request
- `defaultQuery?: Record<string, unknown>` — Query params merged into every request
- `fetch?: Function` — Custom fetch implementation

---

### `client.messages` — Messages API (`src/resources/messages/messages.ts`)

#### `client.messages.create(body, options?)`
Send a message to Claude. Overloaded: returns `Message` (non-streaming) or `Stream<RawMessageStreamEvent>` (streaming).

```ts
// Non-streaming
const message = await client.messages.create({
  model: 'claude-opus-4-6',
  max_tokens: 1024,
  messages: [{ role: 'user', content: 'Hello, Claude' }],
});
console.log(message.content[0].text); // TextBlock

// Streaming (returns Stream<RawMessageStreamEvent>)
const stream = await client.messages.create({
  model: 'claude-opus-4-6',
  max_tokens: 1024,
  messages: [{ role: 'user', content: 'Tell me a story' }],
  stream: true,
});
for await (const event of stream) { console.log(event); }
```

#### `client.messages.stream(body, options?)` → `MessageStream`
Higher-level streaming that returns a `MessageStream` (event emitter + async iterable):

```ts
const stream = client.messages.stream({
  model: 'claude-opus-4-6',
  max_tokens: 1024,
  messages: [{ role: 'user', content: 'Write a poem' }],
});

stream.on('text', (delta, snapshot) => process.stdout.write(delta));
const finalMessage = await stream.finalMessage();
// or: for await (const event of stream) { ... }
```

#### `client.messages.parse(body, options?)` → `Promise<ParsedMessage>`
Structured output parsing — returns `ParsedMessage` with `.parsed_output` if `output_config.format` is provided:

```ts
import { zodOutputFormat } from '@anthropic-ai/sdk/helpers/zod';
import { z } from 'zod';

const Result = z.object({ answer: z.string(), confidence: z.number() });

const msg = await client.messages.parse({
  model: 'claude-sonnet-4-6',
  max_tokens: 1024,
  messages: [{ role: 'user', content: 'What is 2+2?' }],
  output_config: { format: zodOutputFormat(Result) },
});
console.log(msg.parsed_output?.answer); // "4"
```

#### `client.messages.countTokens(body, options?)` → `Promise<MessageTokensCount>`
Count tokens for a message before sending it.

---

### `client.messages.batches` — Message Batches (`src/resources/messages/batches.ts`)

```ts
// Create a batch
const batch = await client.messages.batches.create({
  requests: [
    { custom_id: 'req-1', params: { model: '...', max_tokens: 1024, messages: [...] } },
  ],
});

// Poll for completion
const status = await client.messages.batches.retrieve(batch.id);

// List batches
for await (const b of await client.messages.batches.list()) { ... }

// Stream results (JSONL)
const batchWithResults = await client.messages.batches.retrieve(batch.id);
const stream = await client.messages.batches.results(batch.id);
for await (const result of stream) {
  console.log(result.custom_id, result.result);
}

// Cancel a batch
await client.messages.batches.cancel(batch.id);
await client.messages.batches.delete(batch.id);
```

---

### `client.beta.messages.toolRunner()` — Tool Loop (`src/resources/beta/messages/messages.ts`)

Returns a `BetaToolRunner<Stream>` that orchestrates the tool use conversation loop automatically.

```ts
import { betaZodTool } from '@anthropic-ai/sdk/helpers/beta/zod';
import { z } from 'zod';

const weatherTool = betaZodTool({
  name: 'get_weather',
  description: 'Get weather for a city',
  inputSchema: z.object({ city: z.string() }),
  run: async ({ city }) => `It is 72°F and sunny in ${city}.`,
});

// Await directly for final message
const finalMsg = await client.beta.messages.toolRunner({
  model: 'claude-sonnet-4-6',
  max_tokens: 1024,
  messages: [{ role: 'user', content: 'What's the weather in Paris?' }],
  tools: [weatherTool],
});

// Iterate for intermediate messages
const runner = client.beta.messages.toolRunner({ ... });
for await (const message of runner) {
  console.log('intermediate:', message);
}
const result = await runner.done();
```

**`BetaToolRunner` API** (`src/lib/tools/BetaToolRunner.ts`):
- `await runner` — equivalent to `runner.runUntilDone()`, returns final `BetaMessage`
- `runner.done()` — returns Promise<BetaMessage> after iteration completes
- `runner.runUntilDone()` — eagerly reads stream and returns final message
- `runner.setMessagesParams(params | mutatorFn)` — update conversation params mid-loop
- `runner.pushMessages(...messages)` — add messages to conversation history
- `runner.generateToolResponse()` — get tool execution results for the last assistant message
- `runner.params` — read-only current parameters

**CompactionControl** (auto-context compression):
```ts
const runner = client.beta.messages.toolRunner({
  model: 'claude-sonnet-4-6',
  max_tokens: 1024,
  messages: [...],
  tools: [...],
  compaction: {
    enabled: true,
    contextTokenThreshold: 50_000, // default: 100_000
    model: 'claude-haiku-4-5',     // model used for summarization
    summaryPrompt: '...',          // custom compaction prompt
  },
});
```

---

### `MessageStream` Events and Methods (`src/lib/MessageStream.ts`)

**Events** (via `.on(event, handler)`):
- `connect` — connection established
- `streamEvent(event, snapshot)` — every SSE event with accumulated message snapshot
- `text(delta, snapshot)` — text content delta
- `citation(citation, snapshot)` — citation delta
- `inputJson(partial, snapshot)` — tool input JSON delta
- `thinking(delta, snapshot)` — extended thinking delta
- `signature(sig)` — thinking block signature
- `message(msg)` — complete message received
- `contentBlock(block)` — complete content block
- `finalMessage(msg)` — final message (fired after `message`)
- `error(err)` — error occurred
- `abort(err)` — aborted
- `end()` — stream complete

**Methods**:
- `stream.abort()` — cancel the stream
- `await stream.done()` — wait for completion
- `stream.currentMessage` — current accumulated message (may be undefined)
- `await stream.finalMessage()` — Promise resolving to final message
- `await stream.finalText()` — Promise resolving to final text content

---

### Error Classes (`src/core/error.ts`)

```ts
import {
  AnthropicError,           // Base error
  APIError,                 // HTTP API errors (has .status, .headers, .error, .requestID)
  APIConnectionError,       // Network failures
  APIConnectionTimeoutError,// Timeout
  APIUserAbortError,        // AbortController abort
  BadRequestError,          // 400
  AuthenticationError,      // 401
  PermissionDeniedError,    // 403
  NotFoundError,            // 404
  ConflictError,            // 409
  UnprocessableEntityError, // 422
  RateLimitError,           // 429
  InternalServerError,      // 5xx
} from '@anthropic-ai/sdk';
```

---

### Helper Functions

#### `zodOutputFormat(schema)` — `src/helpers/zod.ts`
Converts a Zod schema to a `ParseableOutputFormat` for use with `messages.parse()` or `output_config.format`.

```ts
import { zodOutputFormat } from '@anthropic-ai/sdk/helpers/zod';
const format = zodOutputFormat(z.object({ name: z.string() }));
```

#### `jsonSchemaOutputFormat(schema, options?)` — `src/helpers/json-schema.ts`
Creates output format from raw JSON Schema.

```ts
import { jsonSchemaOutputFormat } from '@anthropic-ai/sdk/helpers/json-schema';
const format = jsonSchemaOutputFormat({ type: 'object', properties: { name: { type: 'string' } } });
```

#### `betaZodTool(options)` — `src/helpers/beta/zod.ts`
Creates a `BetaRunnableTool` from a Zod schema. Input validation is automatic.

```ts
import { betaZodTool } from '@anthropic-ai/sdk/helpers/beta/zod';
const tool = betaZodTool({
  name: 'calculator',
  description: 'Arithmetic',
  inputSchema: z.object({ a: z.number(), b: z.number(), op: z.enum(['+','-','*','/']) }),
  run: ({ a, b, op }) => String(eval(`${a}${op}${b}`)),
});
```

#### `betaTool(options)` — `src/helpers/beta/json-schema.ts`
Creates a `BetaRunnableTool` from JSON Schema with TypeScript type inference.

```ts
import { betaTool } from '@anthropic-ai/sdk/helpers/beta/json-schema';
```

#### MCP Helpers — `src/helpers/beta/mcp.ts`

```ts
import { mcpTool, mcpTools, mcpMessage, mcpMessages, mcpContent, mcpResourceToContent, mcpResourceToFile } from '@anthropic-ai/sdk/helpers/beta/mcp';

// Wrap MCP tool for BetaToolRunner
const { tools } = await mcpClient.listTools();
const runner = await client.beta.messages.toolRunner({
  model: 'claude-sonnet-4-6',
  max_tokens: 1024,
  tools: mcpTools(tools, mcpClient),
  messages: [{ role: 'user', content: 'Use the tools' }],
});

// Convert MCP prompt messages to Anthropic messages
const { messages } = await mcpClient.getPrompt({ name: 'my-prompt' });
await client.beta.messages.create({
  model: 'claude-sonnet-4-6',
  max_tokens: 1024,
  messages: mcpMessages(messages),
});

// Read an MCP resource into a message content block
const resource = await mcpClient.readResource({ uri: 'file:///doc.pdf' });
const block = mcpResourceToContent(resource);

// Upload an MCP resource as a file
const file = mcpResourceToFile(resource);
const uploaded = await client.beta.files.upload({ file });
```

#### `betaMemoryTool(handlers)` — `src/helpers/beta/memory.ts`
Wraps the built-in memory tool with typed per-command handlers:

```ts
import { betaMemoryTool } from '@anthropic-ai/sdk/helpers/beta/memory';
const memTool = betaMemoryTool({
  save: async ({ key, value }) => { /* save to store */ return 'ok'; },
  load: async ({ key }) => { /* load from store */ return storedValue; },
  delete: async ({ key }) => 'deleted',
  list: async () => JSON.stringify(Object.keys(store)),
});
```

#### `ToolError` — `src/lib/tools/ToolError.ts`
Throw from a tool `run()` function to return structured error content to the model:

```ts
import { ToolError } from '@anthropic-ai/sdk/resources/beta/messages';
throw new ToolError('Something went wrong');
throw new ToolError([{ type: 'text', text: 'Error detail' }]);
```

---

### Files API (`src/resources/beta/files.ts`)

```ts
// Upload
const uploaded = await client.beta.files.upload({ file: someFile });

// List (auto-paginated)
for await (const file of await client.beta.files.list()) {
  console.log(file.id, file.filename);
}

// Retrieve metadata
const meta = await client.beta.files.retrieve('file_id');

// Delete
await client.beta.files.delete('file_id');
```

Files require the `files-api-2025-04-14` beta header (automatically added by the SDK).

---

### `toFile(value, name?, options?)` — `src/core/uploads.ts`

Converts various inputs (Buffer, Blob, ReadableStream, string path) into an `Uploadable` for file upload endpoints:

```ts
import { toFile } from '@anthropic-ai/sdk';
const file = await toFile(fs.createReadStream('./doc.pdf'), 'document.pdf', { type: 'application/pdf' });
await client.beta.files.upload({ file });
```

---

### Platform-Specific Clients (Sub-Packages)

#### AWS Bedrock (`@anthropic-ai/bedrock-sdk`)
```ts
import AnthropicBedrock from '@anthropic-ai/bedrock-sdk';
const client = new AnthropicBedrock({ awsRegion: 'us-east-1' });
const message = await client.messages.create({ model: 'anthropic.claude-opus-4-20250514-v1:0', ... });
```

#### Google Vertex AI (`@anthropic-ai/vertex-sdk`)
```ts
import AnthropicVertex from '@anthropic-ai/vertex-sdk';
const client = new AnthropicVertex({ region: 'us-east5', projectId: 'my-project' });
const message = await client.messages.create({ model: 'claude-opus-4@20250514', ... });
```

---

## Configuration Options and Extension Points

- **Custom fetch**: Pass a `fetch` option to `new Anthropic({ fetch: myFetch })` to replace the built-in HTTP implementation (useful for edge runtimes or custom proxies).
- **Request options**: Every resource method accepts an optional `RequestOptions` object as the last argument: `{ headers, query, signal, timeout, stream, idempotencyKey, maxRetries }`.
- **AbortController**: Pass `{ signal: controller.signal }` in request options to cancel requests. `MessageStream.abort()` triggers the stream's internal `AbortController`.
- **Auto-pagination**: List responses implement `AsyncIterable` and expose `.hasNextPage()`, `.nextPage()`, and `.getPaginatedItems()` for manual pagination control.
- **Retry behavior**: Automatically retried with exponential backoff on 429 and 500+ errors. Configurable via `maxRetries` in `ClientOptions` or per-request `RequestOptions`.
- **Beta headers**: Beta API features require `anthropic-beta` headers. Resource classes in `src/resources/beta/` add these automatically. You can also pass them manually via `betas` in the params object.
