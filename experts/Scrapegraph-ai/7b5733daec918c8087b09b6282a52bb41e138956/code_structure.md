# ScrapeGraphAI — Code Structure

## Annotated Directory Tree

```
Scrapegraph-ai/
├── scrapegraphai/                  # Main Python package
│   ├── __init__.py                 # Package root (minimal re-exports)
│   ├── builders/
│   │   ├── __init__.py
│   │   └── graph_builder.py        # GraphBuilder: LLM-powered dynamic graph construction
│   ├── docloaders/
│   │   ├── __init__.py
│   │   ├── browser_base.py         # BrowserBase managed-browser integration
│   │   ├── chromium.py             # ChromiumLoader: Playwright/headless browser loader
│   │   └── scrape_do.py            # Scrape.do API integration
│   ├── graphs/
│   │   ├── __init__.py             # Public graph API (20+ graph classes)
│   │   ├── abstract_graph.py       # AbstractGraph: base class, LLM init, run lifecycle
│   │   ├── base_graph.py           # BaseGraph: DAG execution engine
│   │   ├── code_generator_graph.py # Generates BeautifulSoup extract_data() functions
│   │   ├── csv_scraper_graph.py    # Scrapes a single CSV source
│   │   ├── csv_scraper_multi_graph.py  # Scrapes multiple CSV sources
│   │   ├── depth_search_graph.py   # Multi-level link-following crawl
│   │   ├── document_scraper_graph.py   # Generic document scraper (PDF, HTML, etc.)
│   │   ├── document_scraper_multi_graph.py
│   │   ├── json_scraper_graph.py   # Scrapes a single JSON source
│   │   ├── json_scraper_multi_graph.py
│   │   ├── markdownify_graph.py    # Converts page to Markdown without LLM
│   │   ├── omni_scraper_graph.py   # Multimodal: text + image scraping
│   │   ├── omni_search_graph.py    # Internet search with multimodal scraping
│   │   ├── screenshot_scraper_graph.py  # Screenshot + OCR scraping
│   │   ├── script_creator_graph.py # Generates reusable scraping scripts
│   │   ├── script_creator_multi_graph.py
│   │   ├── search_graph.py         # DuckDuckGo/Serper search → SmartScraper per URL → merge
│   │   ├── search_link_graph.py    # Finds and follows relevant links from a page
│   │   ├── smart_scraper_graph.py  # Core single-URL LLM scraper
│   │   ├── smart_scraper_lite_graph.py  # Lightweight version without chunking
│   │   ├── smart_scraper_multi_concat_graph.py  # Multiple URLs → concat then answer
│   │   ├── smart_scraper_multi_graph.py    # Multiple URLs → per-URL answers → merge
│   │   ├── smart_scraper_multi_lite_graph.py
│   │   ├── speech_graph.py         # Scrape + text-to-speech output
│   │   ├── xml_scraper_graph.py    # Scrapes a single XML source
│   │   └── xml_scraper_multi_graph.py
│   ├── helpers/
│   │   ├── __init__.py
│   │   ├── default_filters.py      # Default HTML tag filters
│   │   ├── models_tokens.py        # Token limit lookup table (all supported models)
│   │   ├── nodes_metadata.py       # Node descriptions for GraphBuilder
│   │   ├── robots.py               # robots.txt parsing helpers
│   │   └── schemas.py              # JSON Schema definitions for graph configs
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── burr_bridge.py          # BurrBridge: Burr framework adapter for graph execution
│   │   └── indexify_node.py        # Indexify integration node
│   ├── models/
│   │   ├── __init__.py
│   │   ├── clod.py                 # CLoD custom LangChain chat model wrapper
│   │   ├── deepseek.py             # DeepSeek custom chat model wrapper
│   │   ├── minimax.py              # MiniMax custom chat model wrapper
│   │   ├── nvidia.py               # Nvidia NIM custom model wrapper
│   │   ├── oneapi.py               # OneAPI custom model wrapper
│   │   ├── openai_itt.py           # OpenAIImageToText: image-to-text model wrapper
│   │   ├── openai_tts.py           # OpenAITextToSpeech: TTS model wrapper
│   │   └── xai.py                  # XAI (Grok) custom model wrapper
│   ├── nodes/
│   │   ├── __init__.py             # Public nodes API (30+ node classes)
│   │   ├── base_node.py            # BaseNode ABC: execute(), input key parsing
│   │   ├── concat_answers_node.py  # Concatenates multiple answers
│   │   ├── conditional_node.py     # Boolean branching in graph
│   │   ├── description_node.py     # Generates natural-language page description
│   │   ├── fetch_node.py           # FetchNode: primary web/file fetcher
│   │   ├── fetch_node_level_k.py   # FetchNodeLevelK: depth-k link following
│   │   ├── fetch_screen_node.py    # FetchScreenNode: screenshot capture
│   │   ├── generate_answer_csv_node.py  # CSV-specific answer generation
│   │   ├── generate_answer_from_image_node.py  # Image-based answer generation
│   │   ├── generate_answer_node.py  # Core LLM answer generation
│   │   ├── generate_answer_node_k_level.py  # Multi-level answer generation
│   │   ├── generate_answer_omni_node.py  # Multimodal answer generation
│   │   ├── generate_code_node.py   # Code generation with iterative correction
│   │   ├── generate_scraper_node.py  # Scraper script generation
│   │   ├── get_probable_tags_node.py  # Identifies relevant HTML tags
│   │   ├── graph_iterator_node.py  # Runs a sub-graph over a list of items
│   │   ├── html_analyzer_node.py   # Analyzes HTML structure
│   │   ├── image_to_text_node.py   # Converts images to text descriptions
│   │   ├── markdownify_node.py     # Converts HTML to Markdown
│   │   ├── merge_answers_node.py   # Merges answers from multiple sources
│   │   ├── merge_generated_scripts_node.py  # Merges generated code scripts
│   │   ├── parse_node.py           # Splits documents into chunks
│   │   ├── parse_node_depth_k_node.py  # Depth-aware parsing
│   │   ├── prompt_refiner_node.py  # Refines user prompt for better extraction
│   │   ├── rag_node.py             # RAG: Qdrant-backed vector retrieval
│   │   ├── reasoning_node.py       # Structured reasoning before answer generation
│   │   ├── robots_node.py          # Checks robots.txt compliance
│   │   ├── search_internet_node.py  # DuckDuckGo/Serper search
│   │   ├── search_link_node.py     # Finds relevant links on a page
│   │   ├── search_node_with_context.py  # Context-aware link search
│   │   └── text_to_speech_node.py  # TTS output generation
│   ├── prompts/
│   │   ├── __init__.py             # Exports all prompt template strings
│   │   ├── description_node_prompts.py
│   │   ├── generate_answer_node_csv_prompts.py
│   │   ├── generate_answer_node_omni_prompts.py
│   │   ├── generate_answer_node_pdf_prompts.py
│   │   ├── generate_answer_node_prompts.py  # Core TEMPLATE_CHUNKS/NO_CHUNKS/MERGE variants
│   │   ├── generate_code_node_prompts.py
│   │   ├── get_probable_tags_node_prompts.py
│   │   ├── html_analyzer_node_prompts.py
│   │   ├── merge_answer_node_prompts.py
│   │   ├── merge_generated_scripts_prompts.py
│   │   ├── prompt_refiner_node_prompts.py
│   │   ├── reasoning_node_prompts.py
│   │   ├── robots_node_prompts.py
│   │   ├── search_internet_node_prompts.py
│   │   ├── search_link_node_prompts.py
│   │   └── search_node_with_context_prompts.py
│   ├── telemetry/
│   │   ├── __init__.py
│   │   └── telemetry.py            # log_graph_execution(): anonymous usage telemetry
│   └── utils/
│       ├── __init__.py             # Public utils API
│       ├── cleanup_code.py         # extract_code(): strips markdown fences from LLM output
│       ├── cleanup_html.py         # cleanup_html(), reduce_html(): strip scripts/styles
│       ├── code_error_analysis.py  # Syntax/semantic/execution/validation error analysis
│       ├── code_error_correction.py  # LLM-based code correction utilities
│       ├── convert_to_md.py        # convert_to_md(): html2text HTML→Markdown
│       ├── copy.py                 # safe_deepcopy(): handles non-copyable LLM instances
│       ├── custom_callback.py      # LangChain callback for token/cost tracking
│       ├── data_export.py          # export_to_csv/json/xml()
│       ├── dict_content_compare.py # are_content_equal(): deep dict comparison
│       ├── llm_callback_manager.py # CustomLLMCallbackManager: per-node cost tracking
│       ├── logging.py              # Centralized logger with verbosity control
│       ├── model_costs.py          # Per-model cost lookup tables
│       ├── output_parser.py        # get_pydantic_output_parser(): Pydantic → LangChain parser
│       ├── parse_state_keys.py     # State key expression parser
│       ├── prettify_exec_info.py   # prettify_exec_info(): formats execution stats table
│       ├── proxy_rotation.py       # Proxy dataclass, search_proxy_servers(), parse_or_search_proxy()
│       ├── research_web.py         # search_on_web(): web search wrapper
│       ├── save_audio_from_bytes.py
│       ├── save_code_to_file.py
│       ├── schema_trasform.py      # transform_schema(): JSON Schema → Pydantic model
│       ├── screenshot_scraping/
│       │   ├── __init__.py
│       │   ├── screenshot_preparation.py  # take_screenshot(), crop_image(), ipywidget select
│       │   └── text_detection.py   # detect_text(): surya-OCR text detection
│       ├── split_text_into_chunks.py  # split_text_into_chunks() with token awareness
│       ├── sys_dynamic_import.py   # dynamic_import(), srcfile_import()
│       ├── tokenizer.py            # num_tokens_calculus(): multi-backend tokenizer
│       └── tokenizers/
│           ├── tokenizer_mistral.py
│           ├── tokenizer_ollama.py
│           └── tokenizer_openai.py
├── tests/
│   ├── conftest.py                 # Pytest fixtures and shared helpers
│   ├── graphs/                     # Graph-level integration tests (per-provider)
│   ├── nodes/                      # Node-level unit tests
│   ├── utils/                      # Utility function tests
│   ├── integration/                # Full integration tests
│   ├── inputs/                     # Test fixture files (CSV, JSON, XML, HTML)
│   └── fixtures/                   # Benchmark and helper fixtures
├── docs/                           # Sphinx documentation source + i18n READMEs
├── examples/                       # Example scripts
├── pyproject.toml                  # Build system, dependencies, tool config
├── Makefile                        # Developer workflow targets
├── Dockerfile / docker-compose.yml # Container deployment
├── pytest.ini                      # Test configuration
└── requirements.txt / requirements-dev.txt
```

## Module and Package Organization

The package uses a flat module layout with clear subpackage responsibilities:

| Subpackage | Responsibility |
|---|---|
| `graphs/` | Pre-built scraping pipelines (AbstractGraph subclasses) |
| `nodes/` | Atomic pipeline steps (BaseNode subclasses) |
| `prompts/` | LangChain prompt template strings |
| `models/` | Custom LangChain chat model wrappers |
| `docloaders/` | Web content fetching backends |
| `helpers/` | Configuration lookup tables and metadata |
| `utils/` | Cross-cutting utilities (HTML processing, proxies, logging, tokenization) |
| `integrations/` | Third-party framework bridges (Burr, Indexify) |
| `telemetry/` | Anonymous usage telemetry |
| `builders/` | Dynamic graph construction from NL prompts |

## Key Files and Their Roles

- **`graphs/abstract_graph.py`** — The `AbstractGraph` base class every pipeline inherits from. Defines `_create_llm()` (resolves model provider from config), `_create_graph()` (abstract, returns `BaseGraph`), `run()` (abstract, executes graph), `set_common_params()` (propagates shared config to all nodes), and `run_safe_async()`.

- **`graphs/base_graph.py`** — `BaseGraph` is the runtime DAG executor. It holds `nodes` and `edges`, traverses from `entry_point`, tracks execution time and LLM costs via `CustomLLMCallbackManager`, handles `ConditionalNode` branching, and optionally delegates to `BurrBridge`.

- **`nodes/base_node.py`** — `BaseNode` ABC defines the `execute(state: dict) -> dict` contract and `_parse_input_keys()` — a small expression evaluator that supports `&` (AND) and `|` (OR) logic to select which state keys to pass to a node.

- **`graphs/smart_scraper_graph.py`** — The flagship pipeline. Composes `FetchNode → ParseNode → GenerateAnswerNode` with optional `ReasoningNode` and `ConditionalNode` reattempt logic. Also supports direct API delegation via `scrapegraph-py` client when `model == "scrapegraphai/smart-scraper"`.

- **`helpers/models_tokens.py`** — Large dictionary mapping provider → model → max token count, used by `AbstractGraph._create_llm()` to auto-set `model_token` for chunk sizing.

- **`utils/cleanup_html.py`** — `cleanup_html()` uses BeautifulSoup to strip `<script>`, `<style>`, and other non-content tags; `reduce_html()` further compresses the document.

- **`utils/convert_to_md.py`** — `convert_to_md()` calls `html2text` to convert cleaned HTML into Markdown, which is the primary representation passed to LLMs.

## Code Organization Patterns

1. **State-passing DAG** — all nodes share a mutable `state: dict` that is threaded through the graph. Node inputs/outputs are declared as string expressions (e.g., `"user_prompt & (relevant_chunks | parsed_doc | doc)"`) and resolved at runtime by `BaseNode._parse_input_keys()`.

2. **Config dict pattern** — all configuration (LLM, headless, timeout, loader options, schema) flows as a plain Python `dict` from the user through `AbstractGraph.__init__` down to individual nodes via `set_common_params()`.

3. **Provider abstraction** — `_create_llm()` in `AbstractGraph` uses LangChain's `init_chat_model()` for standard providers, and falls back to custom wrappers in `models/` for providers not covered by LangChain (DeepSeek, MiniMax, CLoD, XAI, Nvidia, OneAPI, Ernie).

4. **Graph variation configs** — `SmartScraperGraph._create_graph()` uses a dict keyed by `(html_mode, reasoning, reattempt)` tuples to select the correct node/edge configuration, avoiding repetitive if/else chains.

5. **Prompt-per-node-type** — every node type has its own prompt module in `prompts/`, with variants for chunked vs. non-chunked input and Markdown vs. raw HTML mode.
