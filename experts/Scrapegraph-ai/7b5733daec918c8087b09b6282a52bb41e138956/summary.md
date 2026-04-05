# ScrapeGraphAI — Repository Summary

## Purpose and Goals

ScrapeGraphAI (PyPI: `scrapegraphai`, version 1.75.1) is a Python web scraping library that replaces brittle, selector-based scrapers with LLM-driven scraping pipelines. The core idea is "You Only Scrape Once": instead of writing and maintaining CSS/XPath selectors, the user describes *what* information they want in natural language and ScrapeGraphAI constructs and executes a graph-based pipeline that fetches, parses, and extracts that data using a connected large language model.

The library models each scraping task as a directed acyclic graph (DAG) of nodes: fetching pages, parsing HTML into chunks, optionally applying RAG (Retrieval-Augmented Generation) for large documents, reasoning, and finally generating a structured answer. This approach makes the scraping logic robust to page layout changes and enables complex multi-step pipelines out of the box.

## Key Features and Capabilities

- **Natural-language-driven extraction** — any LLM-compatible prompt replaces rigid selectors.
- **20+ pre-built graph pipelines** — `SmartScraperGraph`, `SearchGraph`, `ScriptCreatorGraph`, `CodeGeneratorGraph`, `DepthSearchGraph`, `OmniScraperGraph`, CSV/JSON/XML/Document scrapers, multi-URL scrapers, speech graph, screenshot scraper, and more.
- **Multi-LLM support** — OpenAI, Anthropic, Google Gemini/Vertex AI, AWS Bedrock, Mistral AI, Ollama (local), Groq, NVIDIA, DeepSeek, xAI (Grok), MiniMax, Fireworks, TogetherAI, Ernie, CLoD, OneAPI, HuggingFace.
- **Structured output via Pydantic schemas** — pass any `BaseModel` subclass to get typed JSON output.
- **Playwright-based browser automation** — handles JavaScript-heavy pages; supports headless/headful mode, proxy rotation, and browser state persistence.
- **BrowserBase and Scrape.do integrations** — plug-in managed browser services via `browser_base` or `scrape_do` config keys.
- **RAG for large pages** — optional Qdrant-backed vector store chunks oversized documents to stay within context limits.
- **Script generation mode** — `ScriptCreatorGraph` and `CodeGeneratorGraph` generate reusable BeautifulSoup/Python scripts rather than returning data directly.
- **Internet search integration** — `SearchGraph` and `OmniSearchGraph` query DuckDuckGo (or Serper) and scrape the top results.
- **Depth-crawl support** — `DepthSearchGraph` and `FetchNodeLevelK` follow links to a configurable depth *k*.
- **Telemetry and cost tracking** — built-in `CustomLLMCallbackManager` records token counts, costs, and per-node execution time.
- **Burr integration** — optional graph execution via the Burr state machine framework for observability and step tracking.
- **OCR/screenshot scraping** — `ScreenshotScraperGraph` captures page screenshots; surya-OCR optional extra for text extraction from images.

## Primary Use Cases and Target Audience

- **Data engineers and analysts** automating web data collection without maintaining fragile selectors.
- **Developers building AI-powered pipelines** that combine web content retrieval with LLM reasoning.
- **Researchers** extracting structured information from multiple web pages or local documents (PDF, CSV, JSON, XML, HTML, Markdown).
- **Teams evaluating scraping code generation** — generating maintainable BeautifulSoup/Playwright scripts via `CodeGeneratorGraph` or `ScriptCreatorGraph`.
- **Applications requiring multi-source aggregation** — `SmartScraperMultiGraph`, `SearchGraph`, and `DepthSearchGraph` handle multiple URLs and merge answers automatically.

## High-Level Architecture Overview

```
User Code
    │
    ▼
AbstractGraph (graphs/abstract_graph.py)
  ├── _create_llm()  — instantiates the LLM from config["llm"]
  ├── _create_graph() — returns a BaseGraph with nodes + edges (implemented per subclass)
  └── run() — calls BaseGraph.execute(initial_state)

BaseGraph (graphs/base_graph.py)
  ├── execute() — traverses DAG from entry_point
  ├── _execute_node() — runs each BaseNode, captures LLM callbacks
  └── _get_next_node() — handles conditional branching

BaseNode (nodes/base_node.py)
  └── execute(state: dict) -> dict  — implemented by each node type

Node types (nodes/):
  FetchNode → ChromiumLoader (docloaders/chromium.py) or HTTP
  ParseNode → html2text / BeautifulSoup chunk splitting
  RAGNode → Qdrant in-memory or persistent
  GenerateAnswerNode → LangChain chain with prompt templates
  SearchInternetNode → DuckDuckGo / Serper search
  GraphIteratorNode → spawns sub-graphs per URL
  MergeAnswersNode → merges multi-source answers
  ConditionalNode → branching logic
  ... (30+ node types total)
```

The library ships pre-wired graph pipelines as concrete `AbstractGraph` subclasses in `scrapegraphai/graphs/`. Users instantiate one of these classes with a prompt, a source (URL or file path), and a config dict, then call `.run()`.

## Related Projects and Dependencies

- **LangChain ecosystem** — `langchain`, `langchain-classic`, `langchain-openai`, `langchain-mistralai`, `langchain-community`, `langchain-aws`, `langchain-ollama` (all pinned in `pyproject.toml`).
- **Playwright** — headless browser automation for JavaScript-heavy pages.
- **html2text / BeautifulSoup4** — HTML to Markdown conversion and DOM parsing.
- **tiktoken / semchunk** — tokenization and semantic text chunking.
- **Pydantic v2** — structured output schemas.
- **DuckDuckGo Search** (`duckduckgo-search`) — default internet search backend.
- **Qdrant** (optional) — vector store for RAG node.
- **Burr** (optional extra) — state machine observability framework.
- **surya-ocr / Pillow / matplotlib** (optional `ocr` extra) — screenshot text extraction.
- **scrapegraph-py** — official API SDK for `scrapegraphai/smart-scraper` cloud model.
- **free-proxy** — automatic proxy pool for rotating scrapers.
