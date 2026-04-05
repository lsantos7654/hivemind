# Spider — APIs and Interfaces

## Core Library: spider

### Website (spider/src/website.rs)

The primary entry point for all crawling. Uses a fluent builder pattern.

```rust
use spider::{tokio, website::Website};

// Simplest usage
let mut website = Website::new("https://example.com");
website.crawl().await;
let links = website.get_links();

// Full builder
let mut website = Website::new("https://example.com")
    .with_limit(50)                   // max concurrent requests
    .with_depth(10)                   // max link traversal depth
    .with_delay(200)                  // ms delay between requests
    .with_respect_robots_txt(true)    // obey robots.txt
    .with_subdomains(true)            // follow subdomains
    .with_user_agent(Some("MyBot/1.0"))
    .with_blacklist_url(Some(vec!["/admin".into()]))
    .with_whitelist_url(Some(vec!["/blog".into()]))
    .with_budget(Some(HashMap::from([("/blog", 50), ("*", 200)])))
    .with_caching(true)
    .with_proxies(Some(vec!["http://proxy:8080".into()]))
    .with_external_domains(Some(vec!["https://cdn.example.com".into()].into_iter()))
    .with_request_timeout(Some(Duration::from_secs(30)))
    .build()
    .unwrap();
```

**Key methods:**
- `website.crawl().await` — crawl, collecting links; pages not stored
- `website.scrape().await` — crawl and store page HTML
- `website.crawl_smart().await` — HTTP first, Chrome on JS-heavy pages (feature: `smart`)
- `website.subscribe(buffer_size) -> Receiver<Page>` — stream pages as they arrive (feature: `sync`)
- `website.unsubscribe()` — close broadcast channel
- `website.get_links() -> &HashSet<CaseInsensitiveString>` — all visited URLs
- `website.get_pages() -> Option<&Vec<Page>>` — all stored pages (after `scrape()`)
- `website.get_all_links_visited() -> HashSet` — async version with full set
- `website.stop()` — stop crawl (feature: `control`)
- `website.pause()` / `website.resume()` — pause/resume (feature: `control`)

### Page (spider/src/page.rs)

Represents a single crawled page.

```rust
// Accessed via subscription or get_pages()
let url: &str = page.get_url();
let html: &str = page.get_html();          // full HTML string
let content: &str = page.get_content();   // cleaned content (markdown if cloud)
let bytes: &[u8] = page.get_html_bytes_u8();
let status: StatusCode = page.status_code;
let headers: &HeaderMap = page.headers;   // feature: headers
```

### Configuration (spider/src/configuration.rs)

```rust
use spider::configuration::Configuration;

// Reusable config for multiple websites
let config = Configuration::new()
    .with_user_agent(Some("MyBot/1.0"))
    .with_respect_robots_txt(true)
    .build();

let mut website = Website::new("https://example.com")
    .with_config(config)
    .build()
    .unwrap();
```

**Chrome-specific configuration:**
```rust
use spider::configuration::{
    RequestInterceptConfiguration, WaitForIdleNetwork, WaitForSelector, WaitForDelay,
    Viewport, ScreenShotConfig, ScreenshotParams, GPTConfigs, GeminiConfigs,
};

let mut website = Website::new("https://spa.example.com")
    .with_chrome_intercept(RequestInterceptConfiguration::new(true)) // block ads
    .with_stealth(true)
    .with_wait_for_idle_network(Some(WaitForIdleNetwork::new(Some(Duration::from_secs(30)))))
    .with_wait_for_selector(Some(WaitForSelector::new(
        Some(Duration::from_secs(10)),
        "div.loaded".into(),
    )))
    .build()
    .unwrap();

website.crawl().await;
```

### Spider Cloud (feature: spider_cloud)

```rust
use spider::configuration::{SpiderCloudConfig, SpiderCloudMode, SpiderCloudReturnFormat};

// Full config
let config = SpiderCloudConfig::new("YOUR_API_KEY")
    .with_mode(SpiderCloudMode::Smart)                           // recommended
    .with_return_format(SpiderCloudReturnFormat::Markdown);      // LLM-ready

let mut website = Website::new("https://example.com")
    .with_spider_cloud_config(config)
    .with_limit(10)
    .build()
    .unwrap();

// Or shorthand (Proxy mode, raw HTML)
let mut website = Website::new("https://example.com");
website.with_spider_cloud("YOUR_API_KEY");
```

**SpiderCloudMode variants:**
- `Proxy` (default) — transparent proxy
- `Api` — POST /crawl per page
- `Unblocker` — POST /unblocker for heavy bot protection
- `Fallback` — direct fetch first, cloud on 403/429/503
- `Smart` — proxy + auto-fallback to unblocker (production recommended)

**SpiderCloudReturnFormat:** `Raw`, `Markdown`, `CommonMark`, `Text`, `Bytes`

### Browser Cloud (features: spider_cloud + chrome)

```rust
use spider::configuration::SpiderBrowserConfig;

let browser = SpiderBrowserConfig::new("YOUR_API_KEY")
    .with_stealth(true)
    .with_country("us");

let mut website = Website::new("https://example.com")
    .with_spider_browser_config(browser)
    .build()
    .unwrap();
website.crawl().await;
```

### Subscription Pattern (feature: sync)

```rust
let mut website = Website::new("https://example.com");
let mut rx = website.subscribe(16); // buffer 16 pages

tokio::spawn(async move {
    while let Ok(page) = rx.recv().await {
        println!("[{}] {} bytes", page.get_url(), page.get_html_bytes_u8().len());
    }
});

website.crawl().await;
website.unsubscribe();
```

---

## spider_agent — Agent API

### Agent struct (spider_agent/src/agent.rs)

```rust
use spider_agent::{Agent, AgentConfig};
use std::sync::Arc;

// Build agent
let agent = Arc::new(
    Agent::builder()
        .with_openai("sk-...", "gpt-4o-mini")
        .with_search_serper("serper-key")
        .with_max_concurrent_llm_calls(10)
        .build()?
);

// Search
let results: SearchResults = agent.search("rust web frameworks").await?;
let results = agent.search_with_options(
    "query",
    SearchOptions::new().with_limit(5).with_country("us"),
).await?;

// Fetch
let page: FetchResult = agent.fetch("https://example.com").await?;
// page.html, page.status, page.content_type

// Extract with natural language prompt
let data: serde_json::Value = agent.extract(&page.html, "Extract product names").await?;

// Extract with JSON schema
let schema = serde_json::json!({ "type": "object", "properties": { "title": {"type": "string"} }});
let structured = agent.extract_structured(&page.html, &schema).await?;

// Research: search + fetch + extract + synthesize
let research: ResearchResult = agent.research(
    "How does Tokio compare to async-std?",
    ResearchOptions::new()
        .with_max_pages(5)
        .with_synthesize(true),
).await?;
println!("{}", research.summary.unwrap());

// LLM prompt
let response = agent.prompt(vec![Message::user("Hello")]).await?;

// Memory
agent.memory_set("key", "value").await;
let val = agent.memory_get("key").await;
agent.memory_clear().await;

// Custom tools
let tools = agent.list_custom_tools();
let result = agent.execute_custom_tool("spider_cloud_scrape", None, None, Some(&body)).await?;
```

### AgentBuilder

```rust
Agent::builder()
    // LLM provider
    .with_openai(api_key, model)          // OpenAI or compatible
    .with_config(agent_config)
    .with_system_prompt("You are a helpful assistant")
    .with_max_concurrent_llm_calls(10)

    // Search
    .with_search_serper(api_key)          // Serper.dev
    .with_search_brave(api_key)           // Brave Search
    .with_search_bing(api_key)            // Bing Search
    .with_search_tavily(api_key)          // Tavily

    // Spider Cloud tools
    .with_spider_cloud(api_key)           // shorthand
    .with_spider_cloud_config(config)     // full config

    // Spider Browser Cloud tools
    .with_spider_browser(api_key)         // shorthand
    .with_spider_browser_config(config)   // full config

    // Browser
    .with_chrome(browser_context)         // Chrome context (feature: chrome)
    .with_webdriver(wd_context)           // WebDriver context (feature: webdriver)

    // Custom tools
    .with_custom_tool(tool)
    .with_custom_tools(tools)
    .build()?
```

### SpiderCloudToolConfig

```rust
use spider_agent::SpiderCloudToolConfig;

let config = SpiderCloudToolConfig::new("api-key")
    .with_api_url("https://api.spider.cloud")
    .with_tool_name_prefix("spider_cloud")   // tools: spider_cloud_crawl, etc.
    .with_enable_ai_routes(true);            // requires paid plan

// Default tools: crawl, scrape, search, links, transform, unblocker
// AI tools (paid): ai_crawl, ai_scrape, ai_search, ai_browser, ai_links
```

### SpiderBrowserToolConfig

```rust
use spider_agent::SpiderBrowserToolConfig;

let config = SpiderBrowserToolConfig::new("api-key")
    .with_stealth(true)
    .with_country("us");

// Tools: spider_browser_navigate, spider_browser_html,
//        spider_browser_screenshot, spider_browser_evaluate,
//        spider_browser_click, spider_browser_fill, spider_browser_wait
```

---

## Remote Multimodal Engine (spider_agent/src/automation/engine.rs)

LLM-driven extraction using any OpenAI-compatible endpoint.

```rust
use spider_agent::automation::{RemoteMultimodalEngine, RemoteMultimodalConfig};

let engine = RemoteMultimodalEngine::new(
    "https://openrouter.ai/api/v1/chat/completions",
    "qwen/qwen-2-vl-72b-instruct",
    None,
).with_api_key(Some("your-api-key"));

let result = engine.extract_from_html(
    "<html>...</html>",
    "https://example.com",
    Some("Page Title"),
).await?;

println!("{:?}", result.extracted);
```

**RemoteMultimodalConfig presets:**
```rust
// Fast: tool calling + HTML diff + confidence retries + concurrent execution
let config = RemoteMultimodalConfig::fast();

// Fast with planning + self-healing
let config = RemoteMultimodalConfig::fast_with_planning();

// Manual configuration
let config = RemoteMultimodalConfig::default()
    .with_tool_calling_mode(ToolCallingMode::Auto)
    .with_html_diff_mode(HtmlDiffMode::Auto)       // 50-70% token reduction
    .with_reasoning_effort(Some(ReasoningEffort::Medium))
    .with_planning_mode(PlanningModeConfig::default())
    .with_self_healing(SelfHealingConfig::default())
    .with_confidence_strategy(ConfidenceRetryStrategy::default())
    .with_concurrent_execution(true);
```

---

## Automation Action Types (spider_agent_types/src/actions.rs)

Over 30 `ActionType` variants for browser automation:

```rust
ActionType::Navigate          // navigate to URL
ActionType::Click             // click element by selector
ActionType::ClickAll(String)  // click all matching elements
ActionType::ClickPoint { x, y }
ActionType::Fill { selector, value }  // clear + type
ActionType::Type              // type text
ActionType::Select            // dropdown select
ActionType::Check             // checkbox
ActionType::Scroll
ActionType::ScrollX(i32)      // scroll horizontally px
ActionType::ScrollY(i32)      // scroll vertically px
ActionType::InfiniteScroll(u32)
ActionType::WaitFor(String)   // wait for selector
ActionType::WaitForNavigation
ActionType::KeyPress
ActionType::Hover
ActionType::Submit
ActionType::Back / Forward / Refresh
ActionType::Screenshot
ActionType::Script            // execute JavaScript
ActionType::Extract           // extract data from page
ActionType::DragDrop
ActionType::ClickDrag { from, to, modifier }
ActionType::ValidateChain     // chain control
ActionType::Custom(String)
```

---

## Concurrent Chain Execution

```rust
use spider_agent::{DependentStep, DependencyGraph, ConcurrentChainConfig, execute_graph, StepResult};
use serde_json::json;

let steps = vec![
    DependentStep::new("fetch", json!({"Navigate": "https://example.com"})),
    DependentStep::new("click_a", json!({"Click": "#btn-a"})).depends_on("fetch"),
    DependentStep::new("click_b", json!({"Click": "#btn-b"})).depends_on("fetch"),
    DependentStep::new("submit", json!({"Click": "#submit"}))
        .depends_on("click_a").depends_on("click_b"),
];

let mut graph = DependencyGraph::new(steps)?;
let config = ConcurrentChainConfig::default();
let result = execute_graph(&mut graph, &config, |step| async move {
    // execution logic
    StepResult::success()
}).await;
```

---

## HTML Cleaning (spider_agent_html)

```rust
use spider_agent_html::{
    clean_html,          // default cleaning
    clean_html_base,     // minimal cleaning
    clean_html_full,     // aggressive cleaning
    clean_html_raw,      // raw passthrough
    clean_html_slim,     // slim profile
    clean_html_with_profile,              // HtmlCleaningProfile
    clean_html_with_profile_and_intent,   // with CleaningIntent hint
    smart_clean_html,    // auto-select profile
};
```

---

## Schema Generation

```rust
use spider_agent::{generate_schema, SchemaGenerationRequest};
use serde_json::json;

let request = SchemaGenerationRequest {
    examples: vec![
        json!({"name": "Product A", "price": 19.99}),
        json!({"name": "Product B", "price": 29.99}),
    ],
    description: Some("Product data".to_string()),
    strict: false,
    name: Some("products".to_string()),
};

let schema: GeneratedSchema = generate_schema(&request);
// schema.to_extraction_schema() for use with extract_structured()
```

---

## MCP Server (spider_mcp)

The MCP server exposes Spider tools to any MCP-compatible LLM client.

```bash
# Run MCP server
cargo run -p spider_mcp

# With Chrome + Spider Cloud
cargo run -p spider_mcp --features "chrome spider_cloud"
```

Tools exposed: `crawl`, `scrape`, `links`, `transform`, `search` (with Serper feature).

---

## CLI (spider_cli)

```bash
cargo install spider_cli

# Authenticate with Spider Cloud
spider authenticate sk-...

# Crawl
spider crawl --url https://example.com
spider crawl --url https://example.com --spider-cloud-mode smart
spider crawl --url https://example.com --spider-cloud-browser

# Scrape (store HTML)
spider scrape --url https://example.com

# Download resources
spider download --url https://example.com
```

API key resolution order: `--spider-cloud-key` flag > `SPIDER_CLOUD_API_KEY` env > `~/.spider/credentials`

---

## Configuration Extension Points

### Custom HTTP headers
```rust
use spider::reqwest::header::{HeaderMap, HeaderValue};
let mut headers = HeaderMap::new();
headers.insert("Authorization", HeaderValue::from_static("Bearer token"));
website.with_headers(Some(headers));
```

### Custom request timeout
```rust
website.with_request_timeout(Some(Duration::from_secs(60)));
```

### Crawl budget per path
```rust
website.with_budget(Some(HashMap::from([
    ("/products", 1000),
    ("/blog", 200),
    ("*", 5000),  // global cap
])));
```

### Custom user-agent rotation (feature: ua_generator)
```rust
website.with_user_agent(None); // uses ua_generator to pick random real UA
```

### Cron scheduling (feature: cron)
```rust
config.cron_str = "0 */6 * * *".into(); // every 6 hours
```

### WARC output (feature: warc)
```rust
use spider::utils::warc::WarcConfig;
config.warc = Some(WarcConfig { path: "output.warc.gz".into(), ..Default::default() });
```
