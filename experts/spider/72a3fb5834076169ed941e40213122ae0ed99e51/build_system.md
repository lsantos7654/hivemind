# Spider — Build System

## Build System Type

Spider uses **Cargo** (Rust's standard build tool) with a Cargo workspace at the repository root. The workspace resolver is version `2`. All eight crates share a common `Cargo.lock`.

There is also an optional **Nix** development shell (`default.nix`) for reproducible toolchain setup.

## Workspace Configuration

**`Cargo.toml` (root):**
```toml
[workspace]
members = [
    "spider",
    "spider_worker",
    "spider_cli",
    "spider_utils",
    "spider_agent",
    "spider_agent_types",
    "spider_agent_html",
    "spider_mcp",
    # internal
    "examples",
    "benches",
]
resolver = "2"
```

## Package Versions

All crates share version `2.48.35` and are published to crates.io under the `spider-rs` organization.

## Key Dependencies by Crate

### spider (core)
- `reqwest` 0.13 — HTTP client (default)
- `wreq` 5 — alternative HTTP client with browser impersonation (feature: `wreq`)
- `tokio` 1 — async runtime (re-exported)
- `chromey` 2 — Chrome CDP library (feature: `chrome`)
- `thirtyfour` 0.36 — WebDriver (feature: `webdriver`)
- `lol_html` 2 — streaming HTML rewriter
- `spider_fingerprint` 2 — browser fingerprinting
- `spider_agent_types` (workspace path)
- `spider_agent` (workspace path, feature: `agent`)
- `async-openai` 0.33 (feature: `openai`)
- `gemini-rust` 1.7 (feature: `gemini`)
- `hashbrown` 0.16 — fast hash maps
- `dashmap` 6 — concurrent hash map (various features)
- `aho-corasick` 1, `memchr` 2 — fast pattern matching
- `quick-xml` 0.39 — XML/sitemap parsing
- `regex` 1 (feature: `regex`)
- `h2` 0.4, `tower` 0.5 — HTTP/2 support
- `sqlx` 0.8 with SQLite (feature: `disk`)
- `sonic-rs` 0.5 — SIMD JSON (feature: `simd`)
- `io-uring` 0.7 (Linux only, feature: `io_uring`)
- `zerocopy` 0.8 (feature: `zero_copy`)
- `statrs` 0.18, `rand` 0.9 (feature: `real_browser`)
- `sysinfo` 0.38 (feature: `balance`)
- `http-global-cache`, `http-cache-reqwest` (feature: `cache`)

### spider_agent
- `tokio` 1 (sync, rt features)
- `reqwest` 0.13 (json, query)
- `dashmap` 6, `parking_lot` 0.12
- `serde`, `serde_json` 1
- `thiserror` 2
- `base64` 0.22
- `spider_agent_types`, `spider_agent_html` (workspace paths)
- `lol_html` 2, `aho-corasick` 1
- `llm_models_spider` 0.1 — model capabilities/pricing
- `async-openai` 0.33 (feature: `openai`)
- `chromey` 2 (feature: `chrome`)
- `thirtyfour` 0.36 (feature: `webdriver`)
- `tempfile` 3 (feature: `fs`)
- `spider_skills` 0.1.7 (feature: `skills`)
- `memvid-rs` 1.2 (feature: `memvid`)
- `aws-sdk-s3` 1, `aws-config` 1 (feature: `skills_s3`)

### spider_agent_types
- `serde`, `serde_json` 1
- `aho-corasick` 1
- `llm_models_spider` 0.1

### spider_cli
- `clap` 4 (derive feature)
- `spider` (workspace path, features: `tokio_io_std`, `sync`, `serde`, `cookies`)
- `spider_transformations` 2

### spider_mcp
- `rmcp` 1 (server + transport-async-rw)
- `uuid` 1 (v4)
- `spider`, `spider_transformations`

### spider_worker
- `warp` 0.4
- `hyper` 1, `hyper-util` 0.1
- `spider` (serde + flexbuffers)

## Feature Flags System

Spider uses a highly granular feature flag system. The `spider` crate alone has 100+ features. Key groupings:

### Default Features
```
default = ["basic", "io_uring", "tcp_fastopen", "splice", "numa", "zero_copy"]
```

The `basic` feature is a meta-feature that pulls in:
- `sync`, `cookies`, `ua_generator`, `encoding`, `string_interner_buffer_backend`
- `balance`, `real_browser`, `disk_native_tls`, `time`, `adaptive_concurrency`
- `priority_frontier`, `dns_cache`, `rate_limit`, `request_coalesce`
- `auto_throttle`, `etag_cache`, `warc`

### Important Feature Groups

| Group | Examples |
|-------|----------|
| Chrome | `chrome`, `chrome_headed`, `chrome_stealth`, `chrome_screenshot`, `chrome_intercept`, `chrome_headless_new`, `smart` |
| WebDriver | `webdriver`, `webdriver_headed`, `webdriver_chrome`, `webdriver_firefox`, `webdriver_edge` |
| Caching | `cache`, `cache_mem`, `cache_chrome_hybrid`, `cache_openai`, `etag_cache` |
| AI | `openai`, `gemini`, `agent`, `agent_chrome`, `agent_openai`, `agent_skills`, `agent_full` |
| Search | `search`, `search_serper`, `search_brave`, `search_bing`, `search_tavily` |
| Networking | `socks`, `wreq`, `h2_multiplex`, `robots_cache` |
| Storage | `disk`, `disk_native_tls`, `disk_aws` |
| Performance | `io_uring`, `simd`, `zero_copy`, `numa`, `bloom`, `inline-more` |
| Cloud | `spider_cloud` |
| Distributed | `decentralized`, `decentralized_headers`, `firewall` |

## Build Commands

### Standard builds
```bash
# Debug build (all crates)
cargo build --workspace

# Release build
cargo build --workspace --release

# Build specific crate
cargo build -p spider
cargo build -p spider_agent --features "openai search_serper"
cargo build -p spider_cli
```

### Running examples
```bash
# Basic crawl
cargo run --example example

# Chrome rendering
cargo run --example chrome --features chrome

# Smart mode (HTTP + Chrome hybrid)
cargo run --example smart --features smart

# Spider Cloud markdown output
SPIDER_CLOUD_API_KEY=sk-... cargo run --example spider_cloud_markdown --features spider_cloud

# OpenAI vision automation
OPENAI_API_KEY=sk-... cargo run --example openai --features "chrome openai"

# Remote multimodal LLM
cargo run --example remote_multimodal --features "chrome openai"

# Agent search
SERPER_API_KEY=xxx cargo run -p spider_agent --example basic_search --features search_serper

# Agent research
OPENAI_API_KEY=xxx SERPER_API_KEY=xxx cargo run -p spider_agent --example research \
  --features "openai search_serper"
```

### Testing
```bash
# Unit tests (no network)
cargo test -p spider
cargo test -p spider_agent
cargo test -p spider_agent_types
cargo test -p spider_agent_html

# Live integration tests (require network)
RUN_LIVE_TESTS=1 cargo test -p spider --test crawler_test_com

# Spider Cloud integration
SPIDER_CLOUD_API_KEY=sk-... RUN_LIVE_TESTS=1 \
  cargo test -p spider_agent --test live_spider_cloud

# Agent smoke tests with real env
RUN_LIVE_TESTS=1 cargo test -p spider_agent --test live_env_smoke \
  --features "openai search_serper" -- --nocapture

# Feature-specific tests
cargo test -p spider --test smart_vs_chrome --features "smart chrome"
cargo test -p spider uring_fs --features io_uring
```

### Documentation
```bash
# Generate docs (avoids agent_full which needs ObjC compiler)
cargo doc -p spider --features "basic chrome openai serde search agent"
```

### Benchmarks
```bash
cargo bench -p spider
```

### Workspace checks
```bash
cargo check --workspace
cargo clippy --workspace
```

## Publishing / Release

The project uses a `release.sh` script that publishes crates in dependency order:
```
spider_agent_types → spider_agent_html → spider_agent → spider → spider_cli / spider_utils / spider_worker / spider_mcp
```

CLI and utils crates use `--no-verify` during publish.

## Environment Variables for Build/Runtime

| Variable | Purpose |
|----------|---------|
| `CHROME_URL` | Connect to remote Chrome instance |
| `OPENAI_API_KEY` | OpenAI API key |
| `GEMINI_API_KEY` | Gemini API key |
| `SPIDER_CLOUD_API_KEY` | Spider Cloud API key |
| `SPIDER_CLOUD_API_URL` | Custom API URL (default: `https://api.spider.cloud`) |
| `SPIDER_CLOUD_RETURN_FORMAT` | `raw\|markdown\|commonmark\|text\|bytes` |
| `SPIDER_BROWSER_STEALTH` | Enable browser stealth (`1`/`true`) |
| `SPIDER_BROWSER_COUNTRY` | Geo-targeting country code |
| `SCREENSHOT_DIRECTORY` | Screenshot output directory |
| `SERPER_API_KEY` | Serper search API key |
| `RUN_LIVE_TESTS` | Enable live network integration tests (`1`) |
| `SPIDER_CLOUD_ENABLE_AI_ROUTES` | Enable `/ai/*` routes in agent (`1`) |
