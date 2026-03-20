# Pi Monorepo — APIs and Interfaces

## `@mariozechner/pi-ai` — LLM Provider API

The primary entry point. Exports from `packages/ai/src/index.ts`.

### Core Streaming Functions

```typescript
import { stream, complete, streamSimple, completeSimple, getModel } from '@mariozechner/pi-ai';

// Get a typed model object
const model = getModel('anthropic', 'claude-sonnet-4-20250514');

// Streaming with full event types
const s = stream(model, context, options?);
for await (const event of s) {
  if (event.type === 'text_delta') process.stdout.write(event.delta);
  if (event.type === 'toolcall_end') await executeToolCall(event.toolCall);
  if (event.type === 'done') console.log(`Stop: ${event.reason}`);
}
const finalMessage = await s.result();

// Non-streaming
const response = await complete(model, context, options?);

// Simplified with reasoning level
const s2 = streamSimple(model, context, { reasoning: 'medium' });
const r2 = await completeSimple(model, context, { reasoning: 'high' });
```

### Streaming Event Types

| Event Type | Key Properties |
|-----------|---------------|
| `start` | `partial`: initial assistant message skeleton |
| `text_start` | `contentIndex` |
| `text_delta` | `delta: string`, `contentIndex` |
| `text_end` | `content: string`, `contentIndex` |
| `thinking_start` | `contentIndex` |
| `thinking_delta` | `delta: string`, `contentIndex` |
| `thinking_end` | `content: string`, `contentIndex` |
| `toolcall_start` | `contentIndex` |
| `toolcall_delta` | `delta: string`, `partial.content[contentIndex].arguments: Partial` |
| `toolcall_end` | `toolCall: { id, name, arguments }` |
| `done` | `reason: 'stop' | 'length' | 'toolUse'`, `message: AssistantMessage` |
| `error` | `reason: 'error' | 'aborted'`, `error: AssistantMessage` |

### Context and Message Types

```typescript
interface Context {
  systemPrompt?: string;
  messages: Message[];
  tools?: Tool[];
}

// Message union type
type Message = UserMessage | AssistantMessage | ToolResultMessage;

interface UserMessage {
  role: 'user';
  content: string | (TextContent | ImageContent)[];
}

interface ToolResultMessage {
  role: 'toolResult';
  toolCallId: string;
  toolName: string;
  content: (TextContent | ImageContent)[];
  isError: boolean;
  timestamp: number;
}

interface TextContent { type: 'text'; text: string; }
interface ImageContent { type: 'image'; data: string; mimeType: string; }
```

### Tool Definition

```typescript
import { Type, Tool, StringEnum } from '@mariozechner/pi-ai';

const myTool: Tool = {
  name: 'get_weather',
  description: 'Get current weather',
  parameters: Type.Object({
    location: Type.String({ description: 'City name' }),
    units: StringEnum(['celsius', 'fahrenheit'])  // Use StringEnum, NOT Type.Enum
  })
};
```

### Tool Validation

```typescript
import { validateToolCall } from '@mariozechner/pi-ai';

// Throws if arguments don't match schema
const validatedArgs = validateToolCall(tools, toolCall);
```

### Model Registry

```typescript
import { getProviders, getModels, getModel } from '@mariozechner/pi-ai';

const providers = getProviders();  // ['openai', 'anthropic', 'google', ...]
const models = getModels('anthropic');  // Model[] for this provider
const model = getModel('openai', 'gpt-4o-mini');  // Typed Model<'openai-responses'>

// Model properties
model.id            // 'gpt-4o-mini'
model.name          // 'GPT-4o mini'
model.api           // 'openai-responses'
model.provider      // 'openai'
model.contextWindow // 128000
model.maxTokens     // 16384
model.reasoning     // false
model.input         // ['text', 'image']
model.cost          // { input: 0.15, output: 0.60, cacheRead: ..., cacheWrite: ... }
```

### Custom Models

```typescript
import type { Model } from '@mariozechner/pi-ai';

const ollama: Model<'openai-completions'> = {
  id: 'llama3.1:8b', name: 'Llama 3.1 8B',
  api: 'openai-completions', provider: 'ollama',
  baseUrl: 'http://localhost:11434/v1',
  reasoning: false, input: ['text'],
  cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0 },
  contextWindow: 128000, maxTokens: 32000,
  compat: { supportsDeveloperRole: false, supportsReasoningEffort: false }
};
```

### OAuth

```typescript
import {
  loginAnthropic, loginOpenAICodex, loginGitHubCopilot,
  loginGeminiCli, loginAntigravity,
  refreshOAuthToken, getOAuthApiKey,
  type OAuthProvider, type OAuthCredentials
} from '@mariozechner/pi-ai/oauth';

// Login
const creds = await loginGitHubCopilot({ onAuth, onPrompt, onProgress });

// Get API key (refreshes if expired)
const result = await getOAuthApiKey('github-copilot', storedCredentials);
if (result) {
  // result.apiKey — use for requests
  // result.newCredentials — persist updated credentials
}
```

### Environment Variables

The library auto-reads API keys from env vars. Set these to skip explicit `apiKey` params:
`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`, `XAI_API_KEY`, `MISTRAL_API_KEY`, `CEREBRAS_API_KEY`, `OPENROUTER_API_KEY`, `AI_GATEWAY_API_KEY`, `ZAI_API_KEY`, `MINIMAX_API_KEY`, `OPENCODE_API_KEY`, `KIMI_API_KEY`, `COPILOT_GITHUB_TOKEN`, `AZURE_OPENAI_API_KEY` + `AZURE_OPENAI_BASE_URL`

---

## `@mariozechner/pi-agent-core` — Agent Runtime API

### Agent Class

```typescript
import { Agent } from '@mariozechner/pi-agent-core';
import { getModel } from '@mariozechner/pi-ai';

const agent = new Agent({
  initialState: {
    systemPrompt: 'You are helpful.',
    model: getModel('anthropic', 'claude-sonnet-4-20250514'),
    tools: [],
    thinkingLevel: 'off',  // 'off' | 'minimal' | 'low' | 'medium' | 'high' | 'xhigh'
    messages: [],
  },
  toolExecution: 'parallel',        // or 'sequential'
  beforeToolCall: async ({ toolCall, args, context }) => {
    if (toolCall.name === 'bash') return { block: true, reason: 'not allowed' };
  },
  afterToolCall: async ({ toolCall, result, isError }) => {
    return { details: { ...result.details, logged: true } };
  },
  convertToLlm: (messages) => messages.filter(m =>
    ['user', 'assistant', 'toolResult'].includes(m.role)
  ),
  transformContext: async (messages, signal) => messages,
  steeringMode: 'one-at-a-time',    // or 'all'
  followUpMode: 'one-at-a-time',
  sessionId: 'my-session',
  getApiKey: async (provider) => refreshToken(),
  thinkingBudgets: { minimal: 128, low: 512, medium: 1024, high: 2048 },
});

// Subscribe to events
const unsub = agent.subscribe((event) => {
  if (event.type === 'message_update' && event.assistantMessageEvent.type === 'text_delta') {
    process.stdout.write(event.assistantMessageEvent.delta);
  }
});

// Send prompts
await agent.prompt('Hello!');
await agent.prompt('Show image', [{ type: 'image', data: base64, mimeType: 'image/png' }]);
await agent.continue();  // Resume from current context (last msg must be user/toolResult)

// State management
agent.setModel(getModel('openai', 'gpt-4o'));
agent.setSystemPrompt('New prompt');
agent.setThinkingLevel('medium');
agent.setTools([myTool]);
agent.replaceMessages(messages);
agent.clearMessages();
agent.reset();
agent.abort();
await agent.waitForIdle();

// Steering while agent runs
agent.steer({ role: 'user', content: 'Stop, do this instead', timestamp: Date.now() });
agent.followUp({ role: 'user', content: 'Then do X', timestamp: Date.now() });
```

### Agent Tool Definition

```typescript
import type { AgentTool } from '@mariozechner/pi-agent-core';
import { Type } from '@sinclair/typebox';

const readFileTool: AgentTool = {
  name: 'read_file',
  label: 'Read File',        // UI display label
  description: 'Read a file',
  parameters: Type.Object({
    path: Type.String({ description: 'File path' }),
  }),
  execute: async (toolCallId, params, signal, onUpdate) => {
    onUpdate?.({ content: [{ type: 'text', text: 'Reading...' }], details: {} });
    const text = await fs.readFile(params.path, 'utf-8');
    return {
      content: [{ type: 'text', text }],
      details: { path: params.path }
    };
  },
};
```

### Low-Level API

```typescript
import { agentLoop, agentLoopContinue } from '@mariozechner/pi-agent-core';

for await (const event of agentLoop([userMessage], context, config)) {
  // Events: agent_start, agent_end, turn_start, turn_end, message_start,
  //         message_update, message_end, tool_execution_start,
  //         tool_execution_update, tool_execution_end
}

// Continue from existing context
for await (const event of agentLoopContinue(context, config)) { ... }
```

### Proxy Usage (Browser)

```typescript
import { streamProxy } from '@mariozechner/pi-agent-core';

const agent = new Agent({
  streamFn: (model, context, options) =>
    streamProxy(model, context, {
      ...options,
      proxyUrl: 'https://your-backend.com',
      authToken: 'bearer-token',
    }),
});
```

---

## `@mariozechner/pi-coding-agent` — SDK and Extension API

### SDK Entry Point

```typescript
import {
  createAgentSession, AuthStorage, ModelRegistry, SessionManager
} from '@mariozechner/pi-coding-agent';

const { session } = await createAgentSession({
  sessionManager: SessionManager.inMemory(),
  authStorage: AuthStorage.create(),
  modelRegistry: new ModelRegistry(authStorage),
});

await session.prompt('What files are in the current directory?');
```

### Extension API (`ExtensionAPI`)

Extensions are TypeScript modules loaded at runtime via jiti. Export a default function:

```typescript
// ~/.pi/agent/extensions/my-ext.ts
export default function (pi: ExtensionAPI) {
  // Subscribe to events
  pi.on('tool_call', async (event, ctx) => {
    if (event.toolName === 'bash' && event.input.command.includes('rm -rf')) {
      const ok = await ctx.ui.confirm('Dangerous command', event.input.command);
      if (!ok) return { block: true, reason: 'User cancelled' };
    }
  });

  pi.on('agent_end', async (event, ctx) => {
    console.log(`Agent finished. Messages: ${event.messages.length}`);
  });

  // Register a custom tool
  pi.registerTool({
    name: 'deploy',
    label: 'Deploy',
    description: 'Deploy the application',
    parameters: Type.Object({ env: StringEnum(['staging', 'prod']) }),
    execute: async (id, params, signal, onUpdate, ctx) => {
      return { content: [{ type: 'text', text: 'Deployed!' }] };
    },
  });

  // Register a command
  pi.registerCommand('stats', {
    description: 'Show session stats',
    handler: async (args, ctx) => {
      const usage = ctx.getContextUsage();
      ctx.ui.notify(`${usage?.tokens} tokens used`);
    },
  });

  // Register a keyboard shortcut
  pi.registerShortcut('ctrl+shift+d', {
    description: 'Deploy',
    handler: async (ctx) => { /* ... */ },
  });

  // Register a CLI flag
  pi.registerFlag('no-deploy', { type: 'boolean', default: false });
  const disabled = pi.getFlag('no-deploy');

  // UI methods
  pi.on('session_start', async (event, ctx) => {
    ctx.ui.setStatus('my-ext', 'Ready');
    ctx.ui.setWidget('my-widget', ['Line 1', 'Line 2']);
    ctx.ui.notify('Extension loaded', 'info');
  });

  // Register provider
  pi.registerProvider('my-proxy', {
    baseUrl: 'https://proxy.example.com',
    api: 'anthropic-messages',
    models: [{ id: 'claude-sonnet-4', name: 'Claude Sonnet 4', ... }],
  });

  // Send messages to the agent
  pi.sendUserMessage('Please summarize the last change');
  pi.sendMessage({ customType: 'notification', content: [], display: 'Info: done' });

  // Extension event bus (inter-extension communication)
  pi.events.emit('my-ext:action', { data: 42 });
  pi.events.on('other-ext:event', (data) => { ... });
}
```

### ExtensionContext (`ctx` in event handlers)

```typescript
interface ExtensionContext {
  ui: ExtensionUIContext;      // UI methods
  hasUI: boolean;              // false in print/RPC mode
  cwd: string;                 // current working directory
  sessionManager: ReadonlySessionManager;
  modelRegistry: ModelRegistry;
  model: Model<any> | undefined;
  isIdle(): boolean;
  abort(): void;
  hasPendingMessages(): boolean;
  shutdown(): void;
  getContextUsage(): ContextUsage | undefined;
  compact(options?: CompactOptions): void;
  getSystemPrompt(): string;
}
```

### ExtensionUIContext (UI methods available to extensions)

```typescript
ctx.ui.select(title, options, opts?)          // → Promise<string | undefined>
ctx.ui.confirm(title, message, opts?)         // → Promise<boolean>
ctx.ui.input(title, placeholder?, opts?)      // → Promise<string | undefined>
ctx.ui.notify(message, type?)                 // type: 'info' | 'warning' | 'error'
ctx.ui.setStatus(key, text?)                  // Set footer status text
ctx.ui.setWorkingMessage(message?)            // Override streaming indicator
ctx.ui.setWidget(key, content, options?)      // Set widget above/below editor
ctx.ui.setFooter(factory)                     // Custom footer component
ctx.ui.setHeader(factory)                     // Custom header component
ctx.ui.setTitle(title)                        // Terminal window title
ctx.ui.custom(factory, options?)              // Show custom component with focus
ctx.ui.pasteToEditor(text)                    // Paste text into editor
ctx.ui.setEditorText(text)                    // Set editor content
ctx.ui.getEditorText()                        // Get editor content
ctx.ui.setEditorComponent(factory)            // Replace editor component
ctx.ui.setTheme(theme)                        // Set active theme
ctx.ui.getToolsExpanded()                     // Get tool output expansion state
ctx.ui.setToolsExpanded(expanded)             // Set tool output expansion state
```

### Full Event List

All events on `pi.on(...)`:

| Event | Handler Return | Description |
|-------|---------------|-------------|
| `resources_discover` | `ResourcesDiscoverResult?` | Add skill/prompt/theme paths |
| `session_directory` | `SessionDirectoryResult?` | Override session storage dir |
| `session_start` | void | Session loaded |
| `session_before_switch` | `{ cancel? }` | Before switching sessions |
| `session_switch` | void | After switching sessions |
| `session_before_fork` | `{ cancel?, skipConversationRestore? }` | Before fork |
| `session_fork` | void | After fork |
| `session_before_compact` | `{ cancel?, compaction? }` | Before compaction |
| `session_compact` | void | After compaction |
| `session_shutdown` | void | Process exit |
| `session_before_tree` | `{ cancel?, summary?, customInstructions? }` | Before tree nav |
| `session_tree` | void | After tree nav |
| `context` | `{ messages? }` | Before LLM call, can modify messages |
| `before_provider_request` | payload replacement | Before HTTP request to provider |
| `before_agent_start` | `{ message?, systemPrompt? }` | Before agent loop starts |
| `agent_start` | void | Agent loop starts |
| `agent_end` | void | Agent loop ends |
| `turn_start` | void | LLM call begins |
| `turn_end` | void | LLM call + tools complete |
| `message_start` | void | Any message starts |
| `message_update` | void | Assistant streaming delta |
| `message_end` | void | Any message ends |
| `tool_execution_start` | void | Tool begins |
| `tool_execution_update` | void | Tool streams progress |
| `tool_execution_end` | void | Tool completes |
| `model_select` | void | Model changed |
| `tool_call` | `{ block?, reason? }` | Before tool executes |
| `tool_result` | `{ content?, details?, isError? }` | After tool executes |
| `user_bash` | `{ operations?, result? }` | User runs `!command` |
| `input` | `{ action, text?, images? }` | User submits input |

---

## `@mariozechner/pi-tui` — Terminal UI API

### TUI + Component Interface

```typescript
import { TUI, Text, Editor, Markdown, SelectList, Loader,
         Container, Box, Spacer, Image,
         ProcessTerminal, matchesKey, Key,
         visibleWidth, truncateToWidth, wrapTextWithAnsi,
         CombinedAutocompleteProvider } from '@mariozechner/pi-tui';

const tui = new TUI(new ProcessTerminal());
tui.addChild(new Text('Hello World', 1, 1));
tui.start();

// Component interface
interface Component {
  render(width: number): string[];   // MUST NOT return lines wider than width
  handleInput?(data: string): void;
  invalidate?(): void;
}
```

### Overlay System

```typescript
const handle = tui.showOverlay(component, {
  width: '80%', maxHeight: 20, anchor: 'center', margin: 2,
  visible: (w, h) => w >= 80,
});
handle.hide();           // Remove overlay
handle.setHidden(true);  // Temporarily hide
handle.focus();
handle.isFocused();
tui.hideOverlay();       // Hide topmost
tui.hasOverlay();        // Any overlay active?
```

### Key Detection

```typescript
import { matchesKey, Key } from '@mariozechner/pi-tui';

// In handleInput(data)
if (matchesKey(data, Key.ctrl('c'))) process.exit();
if (matchesKey(data, Key.enter)) submit();
if (matchesKey(data, Key.ctrlShift('p'))) cyclePrev();
if (matchesKey(data, 'ctrl+shift+p')) cyclePrev();  // string form also works
```

### ANSI Utilities

```typescript
visibleWidth('\x1b[31mHello\x1b[0m')  // → 5 (ignores ANSI codes)
truncateToWidth('Hello World', 8)      // → 'Hello...' (preserves ANSI)
truncateToWidth('Hello World', 8, '')  // → 'Hello Wo' (no ellipsis)
wrapTextWithAnsi('long line...', 20)   // → string[] (preserves ANSI across breaks)
```

---

## `@mariozechner/pi-coding-agent` CLI Reference

```bash
pi [options] [@files...] [messages...]

# Package management
pi install npm:@foo/pi-tools [-l]
pi install git:github.com/user/repo[@tag]
pi remove npm:@foo/pi-tools
pi update [source]
pi list
pi config

# Session
pi -c                         # Continue last session
pi -r                         # Browse sessions
pi --session <path|id>        # Specific session
pi --fork <path|id>           # Fork session
pi --no-session               # Ephemeral

# Mode
pi -p "message"               # Print (non-interactive)
pi --mode json "message"      # JSON event stream
pi --mode rpc                 # RPC mode

# Model
pi --provider anthropic --model claude-sonnet-4-20250514
pi --model openai/gpt-4o      # provider/id shorthand
pi --model sonnet:high         # with thinking level
pi --thinking medium           # off | minimal | low | medium | high | xhigh
pi --list-models [search]

# Tools
pi --tools read,bash,edit,write    # enable specific tools
pi --no-tools                       # disable all built-in tools

# Extensions/resources
pi -e ./my-ext.ts              # Load specific extension
pi --no-extensions             # Disable discovery
pi --skill ./my-skill          # Load specific skill
```

### RPC Mode Protocol

For non-Node.js process integration (`pi --mode rpc`):
- Communication over stdin/stdout using **strict LF-delimited JSONL** (do NOT split on CR or Unicode separators)
- See `packages/coding-agent/docs/rpc.md` for message types
- TypeScript client: `packages/coding-agent/src/modes/rpc/rpc-client.ts`

### Session File Format

Sessions stored as JSONL in `~/.pi/agent/sessions/` organized by working directory:
```jsonl
{"id":"uuid","parentId":null,"type":"user","content":"Hello","timestamp":1234567890}
{"id":"uuid2","parentId":"uuid","type":"assistant","content":"...","timestamp":...}
```

Each entry has `id` and `parentId` enabling in-place branching without new files.
