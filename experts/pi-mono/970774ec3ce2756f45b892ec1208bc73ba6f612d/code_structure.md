# Pi Monorepo — Code Structure

## Annotated Directory Tree

```
pi-mono/
├── package.json                    # Root workspace config; scripts: build, dev, check, test, release
├── tsconfig.base.json              # Shared TypeScript base config
├── tsconfig.json                   # Root tsconfig for type-checking (uses tsgo)
├── biome.json                      # Lint/format config (Biome)
├── pi-mono.code-workspace          # VS Code workspace file
├── test.sh                         # Run tests skipping API-key-dependent tests
├── pi-test.sh                      # Run pi from sources (use from repo root)
├── scripts/
│   ├── sync-versions.js            # Keep inter-package version refs in sync
│   ├── release.mjs                 # Automated release script (patch/minor/major)
│   ├── build-binaries.sh           # Build standalone binary (Bun compile)
│   ├── cost.ts                     # Token cost calculation utility
│   ├── session-transcripts.ts      # Session transcript export utility
│   ├── check-browser-smoke.mjs     # Verify browser-safe bundle
│   ├── oss-weekend.mjs             # OSS weekend issue tooling
│   └── browser-smoke-entry.ts      # Browser bundle entry for smoke test
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  # CI: install, build, check, test
│   │   ├── pr-gate.yml             # PR gating checks
│   │   ├── build-binaries.yml      # Binary build workflow
│   │   ├── approve-contributor.yml # Contributor approval automation
│   │   └── oss-weekend-issues.yml  # OSS weekend issue creation
│   └── ISSUE_TEMPLATE/             # GitHub issue templates (bug, contribution)
└── packages/
    ├── ai/                         # @mariozechner/pi-ai — LLM provider abstraction
    ├── agent/                      # @mariozechner/pi-agent-core — Agent loop
    ├── coding-agent/               # @mariozechner/pi-coding-agent — CLI + SDK
    ├── tui/                        # @mariozechner/pi-tui — Terminal UI framework
    ├── web-ui/                     # @mariozechner/pi-web-ui — Web components
    ├── mom/                        # @mariozechner/pi-mom — Slack bot
    └── pods/                       # @mariozechner/pi-pods — GPU pod management
```

---

## Package: `packages/ai/` — `@mariozechner/pi-ai`

Core LLM provider abstraction. Only models supporting tool calling are included.

```
packages/ai/
├── src/
│   ├── index.ts                    # Public exports: stream, complete, getModel, getProviders, ...
│   ├── types.ts                    # KnownApi, KnownProvider, Model<A>, Context, Message, Tool,
│   │                               #   AssistantMessage, StreamOptions, SimpleStreamOptions, ...
│   ├── models.ts                   # Model registry helpers: getModel(), getModels(), getProviders()
│   ├── models.generated.ts         # Auto-generated model list from scripts/generate-models.ts
│   ├── stream.ts                   # AssistantMessageEventStream: stream(), complete(),
│   │                               #   streamSimple(), completeSimple(), validateToolCall()
│   ├── api-registry.ts             # registerApiProvider(), getApiProvider() — plugin system for APIs
│   ├── env-api-keys.ts             # getEnvApiKey() — reads API keys from environment variables
│   ├── oauth.ts                    # OAuth token management, refreshOAuthToken, getOAuthApiKey
│   ├── cli.ts                      # npx @mariozechner/pi-ai login/list CLI
│   ├── bedrock-provider.ts         # Amazon Bedrock streaming (Node-only, loaded lazily)
│   ├── providers/
│   │   ├── register-builtins.ts    # Lazy-load and register all built-in API implementations
│   │   ├── anthropic.ts            # Anthropic Messages API (streamAnthropic, AnthropicOptions)
│   │   ├── openai-completions.ts   # OpenAI Chat Completions (streamOpenAICompletions)
│   │   ├── openai-responses.ts     # OpenAI Responses API (streamOpenAIResponses)
│   │   ├── openai-codex-responses.ts # OpenAI Codex / ChatGPT subscription (SSE + WebSocket)
│   │   ├── openai-responses-shared.ts # Shared logic for Responses-compatible APIs
│   │   ├── azure-openai-responses.ts # Azure OpenAI Responses API
│   │   ├── google.ts               # Google Generative AI API (streamGoogle)
│   │   ├── google-vertex.ts        # Google Vertex AI (streamGoogleVertex)
│   │   ├── google-gemini-cli.ts    # Google Cloud Code Assist / Gemini CLI OAuth
│   │   ├── google-shared.ts        # Shared Google message transformation
│   │   ├── mistral.ts              # Mistral Conversations API
│   │   ├── amazon-bedrock.ts       # Bedrock Converse Stream (re-exports bedrock-provider)
│   │   ├── simple-options.ts       # SimpleStreamOptions → provider-specific options mapping
│   │   └── transform-messages.ts   # Cross-provider message normalization (thinking blocks → text)
│   └── utils/
│       ├── event-stream.ts         # SSE parser utilities
│       ├── hash.ts                 # Hash utilities (for cache key generation)
│       ├── json-parse.ts           # Incremental/partial JSON parsing for streaming tool args
│       ├── overflow.ts             # Context overflow detection helpers
│       ├── sanitize-unicode.ts     # Unicode surrogate pair sanitization
│       ├── typebox-helpers.ts      # StringEnum helper (Google-compatible enum schemas)
│       └── validation.ts           # validateToolCall() using AJV + TypeBox schemas
├── scripts/
│   ├── generate-models.ts          # Fetches model lists from providers, writes models.generated.ts
│   └── generate-test-image.ts      # Creates test image for vision tests
├── bedrock-provider.js             # Pre-built Bedrock provider CJS module (lazy-loaded)
├── bedrock-provider.d.ts           # Type declarations for pre-built Bedrock module
├── test/                           # ~35 test files covering all providers and edge cases
└── vitest.config.ts                # Vitest config (provider tests require env vars)
```

---

## Package: `packages/agent/` — `@mariozechner/pi-agent-core`

Stateful agent with event streaming. Built on pi-ai.

```
packages/agent/
├── src/
│   ├── index.ts                    # Public exports: Agent, agentLoop, agentLoopContinue, ...
│   ├── agent.ts                    # Agent class — stateful wrapper around agentLoop
│   ├── agent-loop.ts               # agentLoop() and agentLoopContinue() async generators
│   ├── types.ts                    # AgentContext, AgentLoopConfig, AgentTool, AgentEvent,
│   │                               #   AgentState, AgentMessage, ThinkingLevel, ...
│   └── proxy.ts                    # streamProxy() — for browser apps proxying through backend
└── test/                           # Agent loop tests, E2E tests, Bedrock model tests
```

---

## Package: `packages/coding-agent/` — `@mariozechner/pi-coding-agent`

The `pi` CLI binary and SDK. This is the largest and most complex package.

```
packages/coding-agent/
├── src/
│   ├── cli.ts                      # Node.js CLI entry point (bin: "pi")
│   ├── main.ts                     # Startup: parse args, resolve model, load resources, run mode
│   ├── index.ts                    # Public SDK exports
│   ├── config.ts                   # Config directory resolution (~/.pi/agent/)
│   ├── migrations.ts               # Settings/data migration logic
│   ├── cli/
│   │   ├── args.ts                 # CLI argument parsing (yargs-style, all flags defined here)
│   │   ├── config-selector.ts      # Interactive provider/model setup UI
│   │   ├── file-processor.ts       # @file argument processing (reads files into prompt)
│   │   ├── initial-message.ts      # Build initial prompt from CLI args + stdin
│   │   ├── list-models.ts          # --list-models implementation
│   │   └── session-picker.ts       # --resume: interactive session browser
│   ├── core/
│   │   ├── agent-session.ts        # createAgentSession() — the SDK entry point
│   │   ├── auth-storage.ts         # AuthStorage: read/write OAuth credentials (auth.json)
│   │   ├── bash-executor.ts        # BashExecutor: PTY-based bash execution with streaming output
│   │   ├── defaults.ts             # Default system prompt, tool list, thinking budgets
│   │   ├── diagnostics.ts          # Startup diagnostics (version check, API key status)
│   │   ├── event-bus.ts            # EventBus: type-safe inter-extension communication
│   │   ├── exec.ts                 # exec() utility for spawning child processes
│   │   ├── footer-data-provider.ts # FooterDataProvider: git branch, extension statuses
│   │   ├── keybindings.ts          # KeybindingsManager: load/save ~/.pi/agent/keybindings.json
│   │   ├── messages.ts             # CustomMessage type for extension-defined messages
│   │   ├── model-registry.ts       # ModelRegistry: API key resolution, OAuth token refresh
│   │   ├── model-resolver.ts       # Resolve --provider/--model flags to a Model object
│   │   ├── package-manager.ts      # pi install/remove/update/list/config commands
│   │   ├── prompt-templates.ts     # Load .md prompt templates from ~/.pi/agent/prompts/
│   │   ├── resolve-config-value.ts # Resolve config values (path, env var, literal)
│   │   ├── resource-loader.ts      # Discover extensions, skills, prompts, themes from disk
│   │   ├── sdk.ts                  # createAgentSession() implementation
│   │   ├── session-manager.ts      # SessionManager: JSONL session files with tree structure
│   │   ├── settings-manager.ts     # SettingsManager: load/save settings.json (global + project)
│   │   ├── skills.ts               # Load SKILL.md files (AgentSkills standard)
│   │   ├── slash-commands.ts       # Built-in /commands registry
│   │   ├── system-prompt.ts        # Build system prompt from defaults + context files + skills
│   │   ├── timings.ts              # Turn timing tracking for diagnostics
│   │   ├── compaction/
│   │   │   ├── compaction.ts       # Auto/manual compaction logic (context overflow recovery)
│   │   │   ├── branch-summarization.ts # Summarise session branch for /tree navigation
│   │   │   ├── utils.ts            # Compaction helpers
│   │   │   └── index.ts            # Public exports
│   │   ├── extensions/
│   │   │   ├── types.ts            # All extension types: ExtensionAPI, ExtensionEvent,
│   │   │   │                       #   ExtensionContext, ToolDefinition, ProviderConfig, ...
│   │   │   ├── loader.ts           # Load extension files via jiti (TypeScript at runtime)
│   │   │   ├── runner.ts           # ExtensionRunner: bind actions, dispatch events, call handlers
│   │   │   ├── wrapper.ts          # Wrap agent tools with extension beforeToolCall/afterToolCall
│   │   │   └── index.ts            # Public exports
│   │   ├── tools/
│   │   │   ├── index.ts            # Tool registry + type exports (BashToolInput, ReadToolInput, ...)
│   │   │   ├── bash.ts             # bash tool (PTY execution, streaming output)
│   │   │   ├── read.ts             # read tool (file read with line range support)
│   │   │   ├── write.ts            # write tool (create/overwrite files)
│   │   │   ├── edit.ts             # edit tool (exact string replacement with diff preview)
│   │   │   ├── find.ts             # find tool (glob-based file search)
│   │   │   ├── grep.ts             # grep tool (ripgrep-based content search)
│   │   │   ├── ls.ts               # ls tool (directory listing)
│   │   │   ├── path-utils.ts       # Path security: allowlist enforcement, sandbox checks
│   │   │   ├── edit-diff.ts        # Diff rendering for edit tool results
│   │   │   └── truncate.ts         # Tool output truncation helpers
│   │   └── export-html/
│   │       ├── index.ts            # exportSession() — HTML export
│   │       ├── ansi-to-html.ts     # ANSI escape sequence → HTML converter
│   │       ├── tool-renderer.ts    # Render tool calls/results to HTML
│   │       ├── template.html       # HTML export template
│   │       ├── template.css        # Export styles
│   │       └── template.js         # Export client-side JS
│   ├── modes/
│   │   ├── index.ts                # Mode dispatcher
│   │   ├── print-mode.ts           # Non-interactive print mode (-p flag)
│   │   ├── interactive/
│   │   │   ├── interactive-mode.ts # Full TUI interactive mode (main event loop)
│   │   │   └── theme/              # Built-in themes: dark.json, light.json
│   │   └── rpc/
│   │       ├── rpc-mode.ts         # RPC server mode (--mode rpc)
│   │       ├── rpc-types.ts        # JSONL message types for RPC protocol
│   │       ├── rpc-client.ts       # TypeScript RPC client for process integration
│   │       └── jsonl.ts            # JSONL framing (strict LF-only splitting)
│   ├── utils/
│   │   ├── git.ts                  # Git utilities (current branch, status)
│   │   ├── clipboard.ts            # Clipboard read/write (cross-platform)
│   │   ├── clipboard-image.ts      # Paste image from clipboard
│   │   ├── clipboard-native.ts     # Native clipboard bindings
│   │   ├── image-convert.ts        # Image format conversion
│   │   ├── image-resize.ts         # Image resize (photon-node)
│   │   ├── exif-orientation.ts     # EXIF orientation correction
│   │   ├── child-process.ts        # Spawn child process helpers
│   │   ├── frontmatter.ts          # YAML frontmatter parser (for skills/prompts)
│   │   └── changelog.ts            # CHANGELOG.md parsing for /changelog command
│   └── bun/
│       ├── cli.ts                  # Bun-compiled binary entry point
│       └── register-bedrock.ts     # Register Bedrock provider for Bun binary
├── docs/                           # Comprehensive docs (extensions, sdk, rpc, providers, ...)
├── examples/
│   ├── extensions/                 # 20+ extension examples (hello, commands, custom-footer, ...)
│   └── sdk/                        # SDK usage examples
└── vitest.config.ts
```

---

## Package: `packages/tui/` — `@mariozechner/pi-tui`

Minimal TUI framework used by pi-coding-agent.

```
packages/tui/
├── src/
│   ├── index.ts                    # Public exports: TUI, Component, all built-in components
│   ├── tui.ts                      # TUI class: differential render loop, focus management
│   ├── terminal.ts                 # Terminal interface, ProcessTerminal, VirtualTerminal
│   ├── components/
│   │   ├── text.ts                 # Text: word-wrapped multi-line text
│   │   ├── truncated-text.ts       # TruncatedText: single-line status text
│   │   ├── input.ts                # Input: single-line text input + Focusable
│   │   ├── editor.ts               # Editor: multi-line editor, autocomplete, paste handling
│   │   ├── markdown.ts             # Markdown: rendered markdown with syntax highlighting
│   │   ├── loader.ts               # Loader / CancellableLoader: animated spinner
│   │   ├── select-list.ts          # SelectList: keyboard-navigable selection list
│   │   ├── settings-list.ts        # SettingsList: settings panel with value cycling
│   │   ├── spacer.ts               # Spacer: empty vertical space
│   │   ├── image.ts                # Image: Kitty/iTerm2 inline image rendering
│   │   ├── box.ts                  # Box: container with padding and background
│   │   └── container.ts            # Container: group of child components
│   ├── autocomplete.ts             # CombinedAutocompleteProvider (slash commands + file paths)
│   ├── keys.ts                     # matchesKey(), Key helper, Kitty keyboard protocol support
│   ├── ansi.ts                     # ANSI utilities: visibleWidth, truncateToWidth, wrapTextWithAnsi
│   └── cursor.ts                   # CURSOR_MARKER constant for IME cursor positioning
└── test/
    └── chat-simple.ts              # Example chat interface (runnable demo)
```

---

## Package: `packages/mom/` — `@mariozechner/pi-mom`

```
packages/mom/
├── src/
│   ├── main.ts                     # Entry: CLI arg parsing, Slack/agent wiring
│   ├── agent.ts                    # Agent runner, event handling, session management
│   ├── slack.ts                    # Slack Socket Mode integration, backfill, message logging
│   ├── context.ts                  # SessionManager (context.jsonl), log→context sync
│   ├── store.ts                    # Channel data persistence, attachment downloads
│   ├── log.ts                      # Centralized logging
│   ├── sandbox.ts                  # Docker / host sandbox execution
│   └── tools/                      # Tool implementations (bash, read, write, edit, attach)
└── docs/                           # Slack setup, Docker sandbox, events, artifacts server docs
```

---

## Package: `packages/pods/` — `@mariozechner/pi-pods`

```
packages/pods/
├── src/
│   ├── index.ts                    # CLI entry (commands: pods, start, stop, list, logs, agent, ...)
│   ├── config.ts                   # ~/.pi config loading and saving
│   ├── ssh.ts                      # SSH command execution utilities
│   ├── setup.ts                    # Pod setup automation (install vLLM, configure)
│   ├── models.ts                   # Predefined model configs (Qwen, GLM, GPT-OSS, ...)
│   ├── agent.ts                    # Standalone pi-agent CLI
│   └── api.ts                      # OpenAI-compatible API client for deployed models
```

---

## Code Organisation Patterns

1. **Layered architecture**: Each package only imports from packages below it in the dependency chain. pi-tui has no pi-ai dependency; pi-agent-core imports pi-ai but not pi-tui.

2. **Lazy provider loading**: `packages/ai/src/providers/register-builtins.ts` registers all providers via lazy wrappers to avoid loading heavy SDKs until needed. Amazon Bedrock is a pre-compiled CJS module to avoid Node.js-only AWS SDK in browser builds.

3. **TypeBox everywhere**: Tool parameters, provider option validation, and agent tool schemas all use `@sinclair/typebox` for JSON Schema generation, serialisation, and AJV-based validation.

4. **Event-based extension API**: All extension hooks are typed events defined in `extensions/types.ts`. The runner (`extensions/runner.ts`) dispatches events and collects results, enabling multiple extensions to compose on the same event.

5. **JSONL sessions**: Session storage uses append-only JSONL files with `id`/`parentId` fields for in-place branching. The session manager in `core/session-manager.ts` builds the branch tree from these flat files.

6. **Mode isolation**: `modes/interactive/`, `modes/print-mode.ts`, and `modes/rpc/` are the three runtime execution contexts. Each implements the `ExtensionUIContext` interface to provide UI primitives to extensions in a mode-appropriate way.
