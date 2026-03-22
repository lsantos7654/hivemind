# openai-node — APIs and Interfaces

## Public Entry Points

The package exports from `src/index.ts`:

```ts
import OpenAI from 'openai';                     // Default export: OpenAI client
import { AzureOpenAI } from 'openai';            // Azure variant
import { APIPromise } from 'openai';             // Promise type
import { toFile } from 'openai';                 // File upload helper
import { APIError, RateLimitError, ... } from 'openai';  // Error classes
```

Sub-path imports:
```ts
import { OpenAIRealtimeWebSocket } from 'openai/realtime/websocket';
import { OpenAIRealtimeWS } from 'openai/realtime/ws';
import { zodResponseFormat, zodFunction } from 'openai/helpers/zod';
import { playAudio, recordAudio } from 'openai/helpers/audio';
```

## Main Client: `OpenAI` class (`src/client.ts`)

### Constructor and `ClientOptions`

```ts
const client = new OpenAI({
  apiKey?: string | (() => Promise<string>),  // Defaults to OPENAI_API_KEY env var; accepts async factory
  organization?: string,                       // Defaults to OPENAI_ORG_ID
  project?: string,                            // Defaults to OPENAI_PROJECT_ID
  webhookSecret?: string,                      // Defaults to OPENAI_WEBHOOK_SECRET
  baseURL?: string,                            // Override API base; defaults to OPENAI_BASE_URL
  timeout?: number,                            // ms; default 600_000 (10 minutes)
  maxRetries?: number,                         // Default 2; set 0 to disable
  fetch?: Fetch,                               // Custom fetch implementation
  fetchOptions?: RequestInit,                  // Additional options passed to all fetch calls
  defaultHeaders?: Record<string, string>,     // Headers added to every request
  defaultQuery?: Record<string, string>,       // Query params added to every request
  logLevel?: 'debug'|'info'|'warn'|'error'|'off',  // Controlled by OPENAI_LOG env var
  logger?: Logger,                             // Custom logger (pino, winston, bunyan, etc.)
  dangerouslyAllowBrowser?: boolean,           // Required to use from browser environments
});
```

### Resource Properties

After construction, `client` exposes all resources:

```ts
client.responses        // Responses API (primary text/multimodal generation)
client.chat.completions // Chat Completions
client.audio.speech     // Text-to-speech
client.audio.transcriptions  // Whisper transcription
client.audio.translations    // Whisper translation
client.embeddings       // Embeddings
client.images           // DALL-E image generation/editing
client.files            // File management
client.models           // Model listing
client.moderations      // Content moderation
client.fineTuning.jobs  // Fine-tuning jobs
client.fineTuning.checkpoints // Fine-tuning checkpoints
client.vectorStores     // Vector store CRUD
client.batches          // Batch API
client.evals            // Evaluation runs
client.containers       // Container management
client.conversations    // Conversation threads
client.realtime         // Realtime sessions/calls
client.graders          // Grader models
client.skills           // Skills management
client.uploads          // Multipart upload sessions
client.webhooks         // Webhook verification
client.beta.assistants  // Assistants API
client.beta.threads     // Thread/Message/Run management
client.beta.realtime    // Beta Realtime sessions
```

### Low-Level HTTP Methods

```ts
// Generic HTTP verbs for undocumented endpoints
await client.get('/some/path', { query: { foo: 'bar' } });
await client.post('/some/path', { body: { key: 'value' } });
await client.put('/some/path', { body: { ... } });
await client.delete('/some/path');
await client.patch('/some/path', { body: { ... } });
```

## `APIPromise<T>` (`src/core/api-promise.ts`)

All resource methods return `APIPromise<T>` which extends `Promise<T>` and adds:

```ts
// Access parsed response and raw HTTP response simultaneously
const { data, response } = await client.responses.create(...).withResponse();
// response: Response (raw fetch response)
// data: T (parsed body)

// Access raw Response before body is consumed (for custom streaming/parsing)
const httpResponse = await client.responses.create(...).asResponse();
httpResponse.headers.get('x-request-id');
```

## Responses API (`src/resources/responses/responses.ts`)

The primary API for model interaction:

```ts
// Basic text generation
const response = await client.responses.create({
  model: 'gpt-4o',
  input: 'What is 2+2?',
  instructions: 'Be brief.',  // system-level instructions
});
console.log(response.output_text);  // Convenience accessor

// With streaming
const stream = await client.responses.create({
  model: 'gpt-4o',
  input: 'Tell me a story',
  stream: true,
});
for await (const event of stream) {
  if (event.type === 'response.output_text.delta') {
    process.stdout.write(event.delta);
  }
}

// Structured output with Zod
import { zodResponseFormat } from 'openai/helpers/zod';
import { z } from 'zod';

const MathAnswer = z.object({ result: z.number(), steps: z.array(z.string()) });
const parsed = await client.responses.parse({
  model: 'gpt-4o-2024-08-06',
  input: 'Solve: 2x + 4 = 10',
  text: { format: zodResponseFormat(MathAnswer, 'math_answer') },
});
// parsed.output_parsed is typed as { result: number; steps: string[] }

// Stream with high-level helper
const stream2 = client.responses.stream({
  model: 'gpt-4o',
  input: 'Hello',
});
stream2.on('response.output_text.delta', (e) => process.stdout.write(e.delta));
const finalResponse = await stream2.finalResponse();
```

Key methods: `create()`, `retrieve()`, `update()`, `list()`, `delete()`, `cancel()`, `parse()`, `stream()`

## Chat Completions API (`src/resources/chat/completions/completions.ts`)

```ts
// Basic completion
const completion = await client.chat.completions.create({
  model: 'gpt-4o',
  messages: [
    { role: 'system', content: 'You are helpful.' },
    { role: 'user', content: 'What is TypeScript?' },
  ],
});
console.log(completion.choices[0].message.content);

// Streaming
const stream = await client.chat.completions.create({
  model: 'gpt-4o',
  messages: [{ role: 'user', content: 'Hello' }],
  stream: true,
});
for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content ?? '');
}

// Structured output (parse helper)
import { zodResponseFormat } from 'openai/helpers/zod';
const result = await client.chat.completions.parse({
  model: 'gpt-4o-2024-08-06',
  messages: [{ role: 'user', content: 'What is 10 + 5?' }],
  response_format: zodResponseFormat(z.object({ answer: z.number() }), 'result'),
});
// result.choices[0].message.parsed is typed as { answer: number }
```

### Tool-Call Runner (Chat Completions)

```ts
import { zodFunction } from 'openai/helpers/zod';

const runner = client.chat.completions.runTools({
  model: 'gpt-4o',
  messages: [{ role: 'user', content: 'What is the weather in Paris?' }],
  tools: [
    zodFunction({
      name: 'getWeather',
      parameters: z.object({ city: z.string() }),
      function: async ({ city }) => ({ temperature: 22, city }),
    }),
  ],
});
const finalMessage = await runner.finalMessage();
// runner.on('message', ...) for streaming events
```

### Streaming Helper (`ChatCompletionStream`)

```ts
const stream = client.chat.completions.stream({
  model: 'gpt-4o',
  messages: [{ role: 'user', content: 'Hello' }],
});
stream.on('content', (delta, snapshot) => process.stdout.write(delta));
const finalCompletion = await stream.finalChatCompletion();
```

## Pagination (`src/core/pagination.ts`)

All list methods return paginated results:

```ts
// Auto-paginate with async iteration
for await (const job of client.fineTuning.jobs.list({ limit: 20 })) {
  console.log(job.id);
}

// Manual pagination
let page = await client.fineTuning.jobs.list({ limit: 20 });
for (const job of page.data) { ... }
while (page.hasNextPage()) {
  page = await page.getNextPage();
}
```

`AbstractPage<T>` implements `AsyncIterable<T>` with `iterPages()`, `hasNextPage()`, and `getNextPage()`. Cursor-based pagination uses `CursorPage<T>` and `ConversationCursorPage<T>`.

## File Uploads (`src/core/uploads.ts`)

```ts
import { toFile } from 'openai';
import fs from 'fs';

// fs.ReadStream (recommended in Node.js)
await client.files.create({ file: fs.createReadStream('data.jsonl'), purpose: 'fine-tune' });

// Web File API
await client.files.create({ file: new File(['content'], 'data.jsonl'), purpose: 'fine-tune' });

// fetch Response
await client.files.create({ file: await fetch('https://example.com/data.jsonl'), purpose: 'fine-tune' });

// toFile helper for Buffer/Uint8Array/etc.
await client.files.create({
  file: await toFile(Buffer.from('...'), 'data.jsonl', { type: 'application/jsonl' }),
  purpose: 'fine-tune',
});
```

## Error Handling (`src/core/error.ts`)

```ts
import OpenAI, { APIError, RateLimitError, AuthenticationError } from 'openai';

try {
  await client.chat.completions.create({ ... });
} catch (err) {
  if (err instanceof APIError) {
    console.log(err.status);      // HTTP status code (number)
    console.log(err.message);     // Human-readable message
    console.log(err.code);        // OpenAI error code (string | null)
    console.log(err.type);        // OpenAI error type (string | undefined)
    console.log(err.headers);     // Response headers
    console.log(err.requestID);   // x-request-id header value
  }
  if (err instanceof RateLimitError) { /* 429 */ }
  if (err instanceof AuthenticationError) { /* 401 */ }
}
```

Error class hierarchy:
- `OpenAIError` (base)
  - `APIError` (HTTP errors with status)
    - `BadRequestError` (400)
    - `AuthenticationError` (401)
    - `PermissionDeniedError` (403)
    - `NotFoundError` (404)
    - `ConflictError` (409)
    - `UnprocessableEntityError` (422)
    - `RateLimitError` (429)
    - `InternalServerError` (500+)
    - `APIConnectionError` (network failure)
    - `APIConnectionTimeoutError` (timeout)
    - `APIUserAbortError` (user abort)
  - `LengthFinishReasonError` (structured output length limit)
  - `ContentFilterFinishReasonError` (content filter)
  - `InvalidWebhookSignatureError` (webhook verification failure)

## Realtime API (`src/realtime/`)

```ts
import { OpenAIRealtimeWebSocket } from 'openai/realtime/websocket';
import { OpenAIRealtimeWS } from 'openai/realtime/ws'; // Node.js ws package

// Browser WebSocket transport
const rt = new OpenAIRealtimeWebSocket({ model: 'gpt-4o-realtime-preview' });

rt.on('session.created', (event) => { /* server confirmed session */ });
rt.on('response.text.delta', (event) => process.stdout.write(event.delta));
rt.on('error', (event) => console.error(event));

// Send events to server
rt.send({ type: 'response.create', response: { modalities: ['text'] } });

// Node.js ws transport (requires ws peer dep)
const rtWs = new OpenAIRealtimeWS({ model: 'gpt-4o-realtime-preview' });
```

`OpenAIRealtimeEmitter` (base class in `src/realtime/internal-base.ts`) provides typed event emission for all `RealtimeServerEvent` types.

## Webhook Verification (`src/resources/webhooks/webhooks.ts`)

```ts
// Parse + verify in one step
const event = await client.webhooks.unwrap(
  rawBody,   // string: raw JSON payload from webhook request
  headers,   // HeadersLike: request headers object
  secret,    // optional: override client.webhookSecret
  tolerance, // optional: max age in seconds (default: 300)
);

// Verify-only (returns void, throws InvalidWebhookSignatureError on failure)
await client.webhooks.verifySignature(rawBody, headers);
```

## Zod Helpers (`src/helpers/zod.ts`)

Supports both Zod v3 and Zod v4:

```ts
import { zodResponseFormat, zodTextFormat, zodFunction } from 'openai/helpers/zod';
import { z } from 'zod'; // v3 or v4

// For Chat Completions structured outputs
const format = zodResponseFormat(z.object({ name: z.string() }), 'schema_name');

// For Responses API text format
const textFormat = zodTextFormat(z.object({ result: z.number() }), 'result');

// Tool with auto-parsed arguments
const tool = zodFunction({
  name: 'search',
  parameters: z.object({ query: z.string(), limit: z.number() }),
  description: 'Search for items',
  function: async ({ query, limit }) => { /* implementation */ },
});
```

## Azure OpenAI (`src/azure.ts`)

```ts
import { AzureOpenAI } from 'openai';

// API key auth
const client = new AzureOpenAI({
  apiKey: process.env.AZURE_OPENAI_API_KEY,
  endpoint: 'https://my-resource.openai.azure.com/',
  apiVersion: '2024-10-01-preview',
  deployment: 'my-gpt4-deployment',  // optional: set per-deployment base URL
});

// Microsoft Entra (Azure AD) token auth
import { getBearerTokenProvider, DefaultAzureCredential } from '@azure/identity';
const credential = new DefaultAzureCredential();
const tokenProvider = getBearerTokenProvider(credential, 'https://cognitiveservices.azure.com/.default');
const azureClient = new AzureOpenAI({ azureADTokenProvider: tokenProvider });
```

## Audio Helpers (`src/helpers/audio.ts`)

Node.js-only utilities using ffplay/ffmpeg:

```ts
import { playAudio, recordAudio } from 'openai/helpers/audio';

// Play audio from TTS response
const speech = await client.audio.speech.create({ model: 'tts-1', voice: 'alloy', input: 'Hello' });
await playAudio(speech.body); // Plays via ffplay

// Record audio from microphone
const audioFile = await recordAudio({
  timeout: 5000,   // Stop after 5s
  signal: abortController.signal,  // Cancel recording
  device: 0,       // Input device index
});
await client.audio.transcriptions.create({ file: audioFile, model: 'whisper-1' });
```

## Configuration Options and Extension Points

### Per-Request Options
Every resource method accepts an optional second argument `RequestOptions`:
```ts
await client.chat.completions.create({ ... }, {
  timeout: 5000,       // Override client-level timeout
  maxRetries: 0,       // Override client-level retries
  headers: { 'X-Custom': 'value' },  // Additional headers for this request
  query: { extra: 'param' },          // Additional query params
});
```

### Custom Fetch
```ts
const client = new OpenAI({ fetch: myCustomFetch });
```

### Proxy Configuration (Node.js via undici)
```ts
import * as undici from 'undici';
const client = new OpenAI({
  fetchOptions: { dispatcher: new undici.ProxyAgent('http://proxy:8888') },
});
```

### Aborting Requests
```ts
const controller = new AbortController();
const response = await client.responses.create({ ... }, { signal: controller.signal });
controller.abort(); // Cancel in-flight request (throws APIUserAbortError)
```
