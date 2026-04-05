# ScrapeGraphAI — APIs and Interfaces

## Public API Entry Points

All public classes are importable from their respective submodules. The most common import paths:

```python
from scrapegraphai.graphs import SmartScraperGraph, SearchGraph, ScriptCreatorGraph
from scrapegraphai.graphs import SmartScraperMultiGraph, CodeGeneratorGraph
from scrapegraphai.nodes import FetchNode, ParseNode, GenerateAnswerNode, RAGNode
from scrapegraphai.utils import prettify_exec_info, export_to_json
```

---

## Core Graph Classes

### `AbstractGraph` (graphs/abstract_graph.py)

Base class for all scraping pipelines.

```python
class AbstractGraph(ABC):
    def __init__(
        self,
        prompt: str,
        config: dict,
        source: Optional[str] = None,
        schema: Optional[Type[BaseModel]] = None,
    ): ...

    @abstractmethod
    def _create_graph(self) -> BaseGraph: ...

    @abstractmethod
    def run(self) -> str: ...

    def get_state(self, key=None) -> dict: ...
    def get_execution_info(self) -> list: ...
    def append_node(self, node: BaseNode): ...
    async def run_safe_async(self) -> str: ...
    def set_common_params(self, params: dict, overwrite: bool = False): ...
```

**Config dict keys** (passed to all graph constructors as `config`):

| Key | Type | Default | Description |
|---|---|---|---|
| `llm` | dict | required | LLM configuration (see below) |
| `verbose` | bool | `False` | Print execution details |
| `headless` | bool | `True` | Run browser in headless mode |
| `timeout` | int | `480` | Seconds before LLM/fetch timeout |
| `loader_kwargs` | dict | `{}` | Extra kwargs for ChromiumLoader |
| `browser_base` | dict | `None` | BrowserBase integration config |
| `scrape_do` | dict | `None` | Scrape.do API config |
| `storage_state` | str | `None` | Path to Playwright browser state file |
| `cache_path` | str/bool | `False` | Path for caching fetched pages |
| `burr_kwargs` | dict | `None` | Burr framework config |
| `additional_info` | str | `None` | Extra instructions appended to prompt |
| `html_mode` | bool | `False` | Skip Markdown conversion, pass raw HTML |
| `reasoning` | bool | `False` | Add ReasoningNode before answer generation |
| `reattempt` | bool | `False` | Retry if answer is empty/NA |
| `force` | bool | `False` | Force re-fetch even if cached |
| `cut` | bool | `True` | Truncate content to model token limit |
| `max_results` | int | `3` | Max search results (SearchGraph) |
| `search_engine` | str | `None` | `"duckduckgo"` or `"serper"` |
| `serper_api_key` | str | `None` | Serper API key |
| `library` | str | required | Library for ScriptCreatorGraph (`"beautifulsoup"`) |

**LLM config sub-dict** (`config["llm"]`):

```python
# With provider/model string
{"model": "openai/gpt-4o", "temperature": 0, "api_key": "..."}

# With Ollama
{"model": "ollama/llama3.2", "model_tokens": 8192, "format": "json"}

# With explicit model instance
{"model_instance": my_chat_model, "model_tokens": 128000}

# With rate limiting
{"model": "openai/gpt-4o", "rate_limit": {"requests_per_second": 1, "max_retries": 3}}
```

Supported provider prefixes: `openai`, `azure_openai`, `google_genai`, `google_vertexai`, `ollama`, `oneapi`, `nvidia`, `groq`, `anthropic`, `bedrock`, `mistralai`, `hugging_face`, `deepseek`, `ernie`, `fireworks`, `clod`, `togetherai`, `xai`, `minimax`.

---

### `SmartScraperGraph` (graphs/smart_scraper_graph.py)

Single-URL LLM-driven scraper. The flagship graph.

```python
class SmartScraperGraph(AbstractGraph):
    def __init__(
        self,
        prompt: str,
        source: str,        # URL (http/https) or local file path
        config: dict,
        schema: Optional[Type[BaseModel]] = None,
    ): ...

    def run(self) -> str: ...  # returns extracted data as JSON string or dict
```

**Example:**
```python
from scrapegraphai.graphs import SmartScraperGraph
from pydantic import BaseModel

class ProductInfo(BaseModel):
    name: str
    price: str
    description: str

graph = SmartScraperGraph(
    prompt="Extract product name, price, and description",
    source="https://example.com/product",
    config={
        "llm": {"model": "openai/gpt-4o-mini", "api_key": "sk-..."},
        "verbose": True,
        "headless": True,
    },
    schema=ProductInfo,
)
result = graph.run()
print(graph.get_execution_info())  # token counts, costs, timing
```

---

### `SmartScraperMultiGraph` (graphs/smart_scraper_multi_graph.py)

Scrapes multiple URLs in parallel, merges answers via LLM.

```python
class SmartScraperMultiGraph(AbstractGraph):
    def __init__(
        self,
        prompt: str,
        source: List[str],   # list of URLs
        config: dict,
        schema: Optional[Type[BaseModel]] = None,
    ): ...
```

---

### `SearchGraph` (graphs/search_graph.py)

Searches the internet via DuckDuckGo/Serper, scrapes top results, merges answers.

```python
class SearchGraph(AbstractGraph):
    def __init__(
        self, prompt: str, config: dict, schema: Optional[Type[BaseModel]] = None
    ): ...

    def run(self) -> str: ...
    def get_considered_urls(self) -> List[str]: ...
```

**Example:**
```python
from scrapegraphai.graphs import SearchGraph

graph = SearchGraph(
    prompt="What are the latest advances in quantum computing?",
    config={"llm": {"model": "openai/gpt-4o"}, "max_results": 5},
)
result = graph.run()
urls_used = graph.get_considered_urls()
```

---

### `CodeGeneratorGraph` (graphs/code_generator_graph.py)

Generates a Python `extract_data(html: str) -> dict` function using BeautifulSoup.

```python
class CodeGeneratorGraph(AbstractGraph):
    def __init__(self, prompt: str, source: str, config: dict,
                 schema: Optional[Type[BaseModel]] = None): ...
```

Requires `schema` parameter. Returns Python code as a string.

---

### `ScriptCreatorGraph` (graphs/script_creator_graph.py)

Generates a reusable scraping script. Requires `config["library"]`.

```python
class ScriptCreatorGraph(AbstractGraph):
    def __init__(self, prompt: str, source: str, config: dict,
                 schema: Optional[Type[BaseModel]] = None): ...
```

---

### `DepthSearchGraph` (graphs/depth_search_graph.py)

Crawls a URL to depth *k*, following links, and aggregates answers.

```python
class DepthSearchGraph(AbstractGraph):
    def __init__(self, prompt: str, source: str, config: dict,
                 schema: Optional[Type[BaseModel]] = None): ...
```

Config key `depth` (int) controls how many link levels to follow.

---

### Other Graph Classes

| Class | Source file | Key behavior |
|---|---|---|
| `SmartScraperLiteGraph` | `smart_scraper_lite_graph.py` | No chunking; faster for small pages |
| `SmartScraperMultiConcatGraph` | `smart_scraper_multi_concat_graph.py` | Concatenates multi-URL content before LLM |
| `SmartScraperMultiLiteGraph` | `smart_scraper_multi_lite_graph.py` | Lite variant of multi-graph |
| `JSONScraperGraph` | `json_scraper_graph.py` | Extracts from a JSON source |
| `CSVScraperGraph` | `csv_scraper_graph.py` | Extracts from a CSV source |
| `XMLScraperGraph` | `xml_scraper_graph.py` | Extracts from an XML source |
| `DocumentScraperGraph` | `document_scraper_graph.py` | Generic document (PDF, HTML) |
| `OmniScraperGraph` | `omni_scraper_graph.py` | Text + image multimodal scraping |
| `OmniSearchGraph` | `omni_search_graph.py` | Search + multimodal scraping |
| `ScreenshotScraperGraph` | `screenshot_scraper_graph.py` | Screenshot capture + OCR |
| `SpeechGraph` | `speech_graph.py` | Scrape → text-to-speech audio output |
| `SearchLinkGraph` | `search_link_graph.py` | Find and follow relevant links on page |
| `MarkdownifyGraph` | `markdownify_graph.py` | Convert page to Markdown (no LLM) |

---

## Core Node Classes

### `BaseNode` (nodes/base_node.py)

```python
class BaseNode(ABC):
    def __init__(self, node_name: str, node_type: str,  # "node" or "conditional_node"
                 input: str, output: List[str],
                 min_input_len: int = 1,
                 node_config: Optional[dict] = None): ...

    @abstractmethod
    def execute(self, state: dict) -> dict: ...
    def update_config(self, params: dict, overwrite: bool = False): ...
    def get_input_keys(self, state: dict) -> List[str]: ...
```

Input expressions use `&` (AND) and `|` (OR): `"user_prompt & (relevant_chunks | parsed_doc | doc)"`.

### `FetchNode` (nodes/fetch_node.py)

Fetches URL or local file content. Supports HTTP, Playwright browser, BrowserBase, Scrape.do, and PyPDF.

```python
FetchNode(
    input="url | local_dir",
    output=["doc"],
    node_config={
        "llm_model": llm,
        "headless": True,
        "timeout": 30,
        "force": False,
        "cut": True,
        "loader_kwargs": {},
        "browser_base": None,
        "scrape_do": None,
        "storage_state": None,
    }
)
```

### `ParseNode` (nodes/parse_node.py)

Splits documents into token-aware chunks. `chunk_size` controls chunking threshold.

```python
ParseNode(input="doc", output=["parsed_doc"],
          node_config={"llm_model": llm, "chunk_size": 8192})
```

### `GenerateAnswerNode` (nodes/generate_answer_node.py)

Core LLM answer generation. Handles chunked/non-chunked and Markdown/HTML modes via template selection.

```python
GenerateAnswerNode(
    input="user_prompt & (relevant_chunks | parsed_doc | doc)",
    output=["answer"],
    node_config={
        "llm_model": llm,
        "schema": MyPydanticModel,  # optional structured output
        "additional_info": "Focus on price data only",
        "timeout": 480,
    }
)
```

### `RAGNode` (nodes/rag_node.py)

Stores document chunks in Qdrant, retrieves relevant ones.

```python
RAGNode(
    input="user_prompt & doc",
    output=["relevant_chunks"],
    node_config={
        "llm_model": llm,
        "embedder_model": embedder,
        "client_type": "memory",  # or "local_db" or "image"
    }
)
```

### `GraphIteratorNode` (nodes/graph_iterator_node.py)

Runs a sub-graph (e.g., `SmartScraperGraph`) over each item in a list.

```python
GraphIteratorNode(
    input="user_prompt & urls",
    output=["results"],
    node_config={
        "graph_instance": SmartScraperGraph,
        "scraper_config": config,
    },
    schema=MySchema,
)
```

---

## `BaseGraph` (graphs/base_graph.py)

Low-level graph for custom pipelines:

```python
from scrapegraphai.graphs import BaseGraph

graph = BaseGraph(
    nodes=[fetch_node, parse_node, generate_answer_node],
    edges=[
        (fetch_node, parse_node),
        (parse_node, generate_answer_node),
    ],
    entry_point=fetch_node,
    graph_name="MyCustomGraph",
    use_burr=False,
)
state, exec_info = graph.execute({"user_prompt": "...", "url": "..."})
```

---

## Utility Functions

### `prettify_exec_info` (utils/prettify_exec_info.py)

```python
from scrapegraphai.utils import prettify_exec_info
print(prettify_exec_info(graph.get_execution_info()))
# Prints a formatted table of node names, token counts, costs, timing
```

### `export_to_json / export_to_csv / export_to_xml` (utils/data_export.py)

```python
from scrapegraphai.utils import export_to_json, export_to_csv
export_to_json(result, "output.json")
export_to_csv(result, "output.csv")
```

### `transform_schema` (utils/schema_trasform.py)

```python
from scrapegraphai.utils import transform_schema
pydantic_model = transform_schema(json_schema_dict)
```

---

## Integration Patterns

### Custom pipeline with Pydantic schema

```python
from pydantic import BaseModel
from typing import List
from scrapegraphai.graphs import SmartScraperGraph

class Article(BaseModel):
    title: str
    author: str
    tags: List[str]

graph = SmartScraperGraph(
    prompt="Extract the article title, author, and tags",
    source="https://blog.example.com/post",
    config={"llm": {"model": "openai/gpt-4o-mini"}},
    schema=Article,
)
result = graph.run()  # returns validated Article-shaped dict
```

### Async execution

```python
import asyncio

async def scrape():
    result = await graph.run_safe_async()
    return result

asyncio.run(scrape())
```

### Custom graph with conditional branching

```python
from scrapegraphai.nodes import ConditionalNode
from scrapegraphai.graphs import BaseGraph

cond = ConditionalNode(
    input="answer",
    output=["answer"],
    node_name="CheckAnswer",
    node_config={"key_name": "answer", "condition": 'not answer or answer=="NA"'},
)
# ConditionalNode requires exactly 2 outgoing edges: true branch and false branch
```

### Adding a node dynamically

```python
graph_instance.append_node(my_new_node)
# Appended node connects to the previously last node
```

### Burr integration for observability

```python
config = {
    "llm": {"model": "openai/gpt-4o"},
    "burr_kwargs": {
        "project_name": "my_scraper",
        "app_instance_id": "session-001",
    }
}
graph = SmartScraperGraph(prompt, source, config)
graph.run()  # execution tracked by Burr
```

## Extension Points

1. **Custom LLM** — pass `{"model_instance": my_langchain_chat_model, "model_tokens": N}` in `config["llm"]` to use any LangChain-compatible model.
2. **Custom node** — subclass `BaseNode`, implement `execute(state: dict) -> dict`, use `BaseGraph` directly.
3. **Custom graph** — subclass `AbstractGraph`, implement `_create_graph()` returning a `BaseGraph`, implement `run()`.
4. **Custom prompt templates** — swap prompt strings in `scrapegraphai/prompts/` modules.
5. **Loader kwargs** — pass `loader_kwargs` in config to customize Playwright (viewport, user-agent, cookies, etc.).
6. **Proxy rotation** — set `loader_kwargs={"proxy": {"server": "http://..."}}` or use `free-proxy` auto-rotation via `config["proxy"]`.
