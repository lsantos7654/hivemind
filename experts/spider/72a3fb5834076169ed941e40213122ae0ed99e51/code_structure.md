# Spider — Code Structure

## Workspace Root

```
spider/                         # Cargo workspace root
├── Cargo.toml                  # Workspace manifest (8 members)
├── Cargo.lock
├── CLAUDE.md                   # Developer quick reference
├── CHANGELOG.md
├── README.md
├── LICENSE                     # MIT
├── SECURITY.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── default.nix                 # Nix development shell
│
├── spider/                     # Core crawling library (crate: spider)
├── spider_agent/               # AI agent runtime (crate: spider_agent)
├── spider_agent_types/         # Pure data types (crate: spider_agent_types)
├── spider_agent_html/          # HTML cleaning utilities (crate: spider_agent_html)
├── spider_cli/                 # CLI binary (crate: spider_cli)
├── spider_utils/               # CSS/XPath selector utilities (crate: spider_utils)
├── spider_worker/              # Distributed worker (crate: spider_worker)
├── spider_mcp/                 # MCP server (crate: spider_mcp)
├── examples/                   # Core library examples (65+ files)
└── benches/                    # Criterion benchmarks
```

## spider/ — Core Library

The heart of the workspace. Provides the `Website` crawler, `Page` type, and all feature-gated subsystems.

```
spider/src/
├── lib.rs                      # Crate root: re-exports, feature docs, black_list module
├── website.rs                  # Website struct: crawl/scrape/subscribe methods (~3,000 lines)
├── page.rs                     # Page struct: URL, HTML, status, headers, metadata
├── configuration.rs            # Configuration + SpiderCloudConfig + SpiderBrowserConfig
├── client.rs                   # reqwest Client wrapper + redirect policy
├── traits.rs                   # Crawler + PageData trait abstractions
│
├── features/                   # Feature-gated subsystems
│   ├── mod.rs                  # Feature module declarations
│   ├── chrome.rs               # Chrome CDP crawling logic
│   ├── chrome_args.rs          # Chrome launch arguments
│   ├── chrome_common.rs        # Shared Chrome types (Viewport, WaitFor*, AuthChallenge, etc.)
│   ├── chrome_viewport.rs      # Viewport configuration
│   ├── automation.rs           # Web automation script execution
│   ├── disk.rs                 # SQLite hybrid disk storage (DatabaseHandler)
│   ├── gemini.rs               # Gemini AI integration
│   ├── gemini_common.rs        # Shared Gemini types (GeminiConfigs)
│   ├── glob.rs                 # URL glob matching support
│   ├── openai.rs               # OpenAI integration for browser scripts
│   ├── openai_common.rs        # Shared OpenAI types (GPTConfigs)
│   ├── search.rs               # Search feature base types
│   ├── solvers.rs              # Bot challenge solver utilities
│   ├── webdriver.rs            # WebDriver crawling logic
│   ├── webdriver_args.rs       # WebDriver arguments
│   ├── webdriver_common.rs     # Shared WebDriver types (WebDriverBrowser, WebDriverConfig)
│   ├── decentralized_headers.rs # Header handling for distributed mode
│   └── search_providers/       # Search provider implementations
│       ├── mod.rs
│       ├── bing.rs
│       ├── brave.rs
│       ├── serper.rs
│       └── tavily.rs
│
├── packages/
│   └── robotparser/            # Built-in robots.txt parser
│       ├── mod.rs
│       └── parser.rs           # RobotFileParser struct
│
└── utils/                      # Internal utilities
    ├── mod.rs                  # Main utils: URL handling, logging, semaphores
    ├── abs.rs                  # Absolute URL conversion
    ├── adaptive_concurrency.rs # AIMD-based concurrency control
    ├── auto_throttle.rs        # Auto-throttle based on response times
    ├── backoff.rs              # Exponential backoff
    ├── bloom.rs                # mmap bloom filter for URL deduplication
    ├── coalesce.rs             # Request coalescing (dedup in-flight requests)
    ├── connect.rs              # TCP connection utilities
    ├── css_selectors.rs        # CSS selector utilities
    ├── detect_chrome.rs        # Chrome binary detection
    ├── detect_system.rs        # System resource detection
    ├── dns_cache.rs            # DashMap-backed DNS cache
    ├── etag_cache.rs           # ETag-based HTTP cache
    ├── frontier.rs             # Priority URL frontier with scoring
    ├── h2_tracker.rs           # HTTP/2 stream multiplexing tracker
    ├── header_utils.rs         # HTTP header helpers
    ├── hedge.rs                # Hedged/parallel requests for slow crawls
    ├── interner.rs             # String interning (ListBucket)
    ├── numa.rs                 # NUMA thread pinning (Linux)
    ├── parallel_backends.rs    # LightPanda/Servo parallel crawl backends
    ├── rate_limiter.rs         # Per-domain token bucket rate limiter
    ├── robots_cache.rs         # Cross-crawl robots.txt TTL cache
    ├── tab_pool.rs             # Chrome tab pool management
    ├── templates.rs            # URL templating utilities
    ├── trie.rs                 # URL trie for path-based decisions
    ├── uring_fs.rs             # Linux io_uring async file I/O
    ├── validation.rs           # URL validation
    ├── warc.rs                 # WARC archive output (WarcConfig)
    └── zero_copy.rs            # Zero-copy byte parsing utilities
```

## spider_agent/ — AI Agent Runtime

Autonomous agent for web research, extraction, and browser automation.

```
spider_agent/src/
├── lib.rs                      # Crate root: re-exports all public types
├── agent.rs                    # Agent struct + AgentBuilder (core entry point)
├── config.rs                   # AgentConfig, UsageLimits, LimitType, UsageStats
├── error.rs                    # AgentError, AgentResult, SearchError
├── memory.rs                   # AgentMemory (DashMap-backed session memory)
├── tools.rs                    # CustomTool, CustomToolRegistry, AuthConfig,
│                               #   SpiderCloudToolConfig, SpiderBrowserToolConfig
│
├── llm/                        # LLM provider layer
│   ├── mod.rs                  # LLMProvider trait, Message, CompletionOptions/Response
│   └── openai.rs               # OpenAIProvider: OpenAI + compatible API calls
│
├── search/                     # Search provider layer
│   ├── mod.rs                  # SearchProvider trait, SearchResult, SearchResults
│   ├── serper.rs               # SerperProvider
│   ├── brave.rs                # BraveProvider
│   ├── bing.rs                 # BingProvider
│   └── tavily.rs               # TavilyProvider
│
├── browser/                    # Chrome browser context (feature: chrome)
│   └── (browser.rs)            # BrowserContext for CDP-based automation
│
├── webdriver/                  # WebDriver context (feature: webdriver)
│   └── (webdriver.rs)          # WebDriverContext
│
├── temp/                       # Temporary filesystem storage (feature: fs)
│   └── (temp.rs)               # TempFile, TempStorage
│
└── automation/                 # Core automation engine
    ├── mod.rs                  # Re-exports from spider_agent_types + local modules
    ├── browser.rs              # Chrome browser automation actions (feature: chrome)
    ├── cache.rs                # SmartCache, CacheValue, CacheStats (TTL cache)
    ├── concurrent_chain.rs     # execute_graph() for dependency-graph parallel execution
    ├── config.rs               # Local automation config (re-exports from types)
    ├── engine.rs               # RemoteMultimodalEngine: LLM-driven extraction
    ├── engine_error.rs         # EngineError, EngineResult
    ├── executor.rs             # ChainExecutor, BatchExecutor, PrefetchManager
    ├── helpers.rs              # Utility functions (JSON parsing, text helpers)
    ├── long_term_memory.rs     # ExperienceMemory via memvid-rs (feature: memvid)
    ├── router.rs               # ModelRouter, ModelSelector, RoutingDecision
    └── skills.rs               # SkillRegistry, Skill, SkillTrigger (feature: skills)

spider_agent/examples/
├── basic_search.rs             # Web search with Serper
├── extract.rs                  # Fetch + LLM extraction
├── research.rs                 # Search + fetch + synthesize pipeline
├── concurrent.rs               # Parallel multi-query execution
├── multimodal.rs               # Vision/screenshot extraction
├── open_page_concurrent.rs     # Concurrent Chrome page opening
├── spider_cloud_end_to_end.rs  # Full Spider Cloud pipeline
├── spider_cloud_prompt_flows.rs # Prompt-driven route orchestration
├── spider_cloud_ecommerce_competitor.rs # Competitor intelligence
├── spider_cloud_jobs_pipeline.rs # Job market intelligence
├── spider_browser_cloud.rs     # Browser Cloud (remote CDP)
├── extraction.rs               # Structured extraction patterns
└── ...

spider_agent/tests/
├── action_feedback_integration.rs
├── thinking_integration.rs
├── live_spider_cloud.rs        # Integration: requires SPIDER_CLOUD_API_KEY
├── live_spider_browser.rs      # Integration: requires SPIDER_CLOUD_API_KEY
└── live_env_smoke.rs           # Smoke tests with real env
```

## spider_agent_types/ — Pure Data Types

Minimal-dependency crate containing all automation type definitions.

```
spider_agent_types/src/
├── lib.rs                      # Crate root and re-exports
├── actions.rs                  # ActionType (30+ variants), ActionResult, ActionRecord
├── chain.rs                    # ChainStep, ChainResult, ChainCondition, ChainContext
├── concurrent_chain.rs         # DependentStep, DependencyGraph, ConcurrentChainConfig
├── confidence.rs               # ConfidenceTracker, ConfidenceSummary, Alternative, Verification
├── config.rs                   # RetryPolicy, RecoveryStrategy, CostTier, ModelPolicy,
│                               #   RemoteMultimodalConfig, AutomationConfig
├── content.rs                  # ContentAnalysis (aho-corasick pattern matching)
├── helpers.rs                  # JSON/text utilities (extract_*, parse_tool_calls, etc.)
├── html_diff.rs                # HtmlDiffResult, PageStateDiff, ElementChange, DiffStats
├── map_result.rs               # MapResult, DiscoveredUrl, categories()
├── memory_ops.rs               # AutomationMemory, MemoryOperation
├── observation.rs              # PageObservation, InteractiveElement, FormField, FormInfo
├── planning.rs                 # ExecutionPlan, PlannedStep, Checkpoint, PlanningModeConfig
├── prompts.rs                  # System prompt constants (DEFAULT, ACT, OBSERVE, etc.)
├── schema_gen.rs               # GeneratedSchema, SchemaCache, SchemaGenerationRequest,
│                               #   generate_schema(), infer_schema(), refine_schema()
├── selector_cache.rs           # SelectorCache, SelectorCacheEntry
├── self_healing.rs             # SelfHealingConfig, HealingRequest, HealingResult,
│                               #   HealingDiagnosis, HealedSelectorCache
├── synthesis.rs                # SynthesisConfig, SynthesisResult, MultiPageContext
└── tool_calling.rs             # ToolDefinition, FunctionDefinition, ToolCall, ToolCallingMode
```

## spider_agent_html/ — HTML Cleaning

```
spider_agent_html/src/
├── lib.rs                      # Re-exports from cleaning module
└── cleaning.rs                 # clean_html*() variants (lol_html-based streaming rewriter)
                                #   clean_html, clean_html_base, clean_html_full,
                                #   clean_html_raw, clean_html_slim,
                                #   clean_html_with_profile, smart_clean_html
```

## spider_cli/ — CLI Binary

```
spider_cli/src/
└── main.rs                     # CLI entry point (clap-based), subcommands:
                                #   crawl, scrape, download, authenticate
```

## spider_utils/ — Selector Utilities

```
spider_utils/src/
└── lib.rs                      # DocumentSelectors<K>, css_query_select_map_streamed(),
                                #   XPath evaluation via sxd_xpath
```

## spider_worker/ — Distributed Worker

```
spider_worker/src/              # warp-based HTTP server for decentralized IO processing
                                # Receives page tasks from spider core via flexbuffers
```

## spider_mcp/ — MCP Server

```
spider_mcp/src/
└── main.rs                     # rmcp-based MCP server exposing Spider as tools:
                                #   crawl, scrape, links, transform, search
```

## Code Organization Patterns

1. **Feature-gated modules**: Almost all optional functionality lives behind `#[cfg(feature = "...")]`. Zero cost when not enabled.

2. **Builder pattern**: Both `Website` and `Agent` use builder structs (`Configuration`, `AgentBuilder`) with chained `.with_*()` methods.

3. **Re-export strategy**: `spider_agent` re-exports everything from `spider_agent_types` and `spider_agent_html`. The top-level `spider` crate re-exports `spider_agent` types under `spider::agent::*`.

4. **Crate dependency order**: `spider_agent_types` → `spider_agent_html` → `spider_agent` → `spider` → frontends (CLI/worker/MCP). This ensures clean separation: types are dependency-free, HTML processing is light, the agent is self-contained, and the core library integrates them all.

5. **Separation of runtime vs types**: `spider_agent_types` has no tokio/reqwest/dashmap dependencies, making it usable in constrained environments. Runtime components (engine, browser, executor) stay in `spider_agent`.

6. **examples/ directory**: 65+ standalone example files demonstrating every feature combination. Named clearly by feature (e.g., `chrome.rs`, `openai.rs`, `spider_cloud_markdown.rs`).
