# MiroFish — APIs and Interfaces

## Backend REST API

The Flask backend exposes three groups of REST endpoints, all under the `/api/` prefix. All responses follow this envelope format:

```json
{
  "success": true,
  "data": { ... },
  "error": "error message if success=false"
}
```

---

### Graph API — `/api/graph`

Handles project lifecycle, ontology generation, and Zep knowledge graph construction.

#### Project Management

| Method | Path | Description |
|---|---|---|
| GET | `/api/graph/project/<project_id>` | Retrieve a project by ID |
| GET | `/api/graph/project/list` | List all projects (query: `?limit=50`) |
| DELETE | `/api/graph/project/<project_id>` | Delete a project |
| POST | `/api/graph/project/<project_id>/reset` | Reset project status to allow re-building |

#### Ontology Generation (Step 1)

```
POST /api/graph/ontology/generate
Content-Type: multipart/form-data

Fields:
  files                  (required) One or more files (PDF/MD/TXT/Markdown)
  simulation_requirement (required) Natural language description of what to predict
  project_name           (optional) Human-readable project name
  additional_context     (optional) Extra context for ontology generation

Response:
  {
    "project_id": "proj_xxxx",
    "project_name": "...",
    "ontology": {
      "entity_types": ["Person", "Organization", ...],
      "edge_types": ["KNOWS", "WORKS_AT", ...]
    },
    "analysis_summary": "...",
    "files": [{"filename": "...", "size": 12345}],
    "total_text_length": 45678
  }
```

#### Graph Building (Step 2)

```
POST /api/graph/build
Content-Type: application/json

{
  "project_id": "proj_xxxx",   (required)
  "graph_name": "My Graph",    (optional)
  "chunk_size": 500,           (optional, default 500)
  "chunk_overlap": 50,         (optional, default 50)
  "force": false               (optional, force rebuild)
}

Response:
  {
    "project_id": "proj_xxxx",
    "task_id": "task_xxxx",
    "message": "..."
  }
```

#### Task / Graph Status Queries

| Method | Path | Description |
|---|---|---|
| GET | `/api/graph/task/<task_id>` | Get async task status and progress (0–100) |
| GET | `/api/graph/tasks` | List all tasks |
| GET | `/api/graph/data/<graph_id>` | Get Zep graph nodes and edges |
| DELETE | `/api/graph/delete/<graph_id>` | Delete a Zep graph |

Task response shape:
```json
{
  "task_id": "task_xxxx",
  "status": "processing|completed|failed",
  "progress": 55,
  "message": "...",
  "result": { ... },
  "error": "..."
}
```

---

### Simulation API — `/api/simulation`

Handles entity reading, agent profile generation, simulation preparation, control, and agent interviewing.

#### Entity Access

| Method | Path | Description |
|---|---|---|
| GET | `/api/simulation/entities/<graph_id>` | Get filtered entities from Zep graph |
| GET | `/api/simulation/entities/<graph_id>/<entity_uuid>` | Get a single entity's details |

Query parameters for entity listing:
- `entity_types` — comma-separated type filter
- `enrich=true|false` — include related edge information (default: true)

#### Profile Generation (Step 2)

```
POST /api/simulation/profiles/generate
Content-Type: application/json

{
  "simulation_id": "sim_xxxx",     (required if simulation exists)
  "project_id": "proj_xxxx",       (required for new simulation)
  "graph_id": "graph_xxxx",        (required)
  "entity_uuids": ["uuid1", ...],  (optional, defaults to all entities)
  "platform": "twitter|reddit|both"
}
```

#### Simulation Lifecycle

| Method | Path | Description |
|---|---|---|
| POST | `/api/simulation/prepare` | Prepare simulation (entities + profiles + config) |
| POST | `/api/simulation/start` | Start the simulation subprocess |
| POST | `/api/simulation/pause` | Pause the running simulation |
| POST | `/api/simulation/resume` | Resume a paused simulation |
| POST | `/api/simulation/stop` | Stop the simulation |
| GET | `/api/simulation/status/<simulation_id>` | Get simulation status |
| GET | `/api/simulation/list` | List all simulations |
| GET | `/api/simulation/actions/<simulation_id>` | Get recorded agent actions |

Start simulation request:
```json
{
  "simulation_id": "sim_xxxx",
  "max_rounds": 20,
  "enable_twitter": true,
  "enable_reddit": true
}
```

#### Agent Interview (Deep Interaction)

```
POST /api/simulation/interview
Content-Type: application/json

{
  "simulation_id": "sim_xxxx",
  "agent_id": 3,
  "prompt": "What do you think about the policy?"
}
```

The system automatically prepends a prefix to prevent tool calls and ensures the agent responds as a character in-world.

---

### Report API — `/api/report`

Handles prediction report generation and conversational follow-up.

#### Report Generation (Step 4)

```
POST /api/report/generate
Content-Type: application/json

{
  "simulation_id": "sim_xxxx",
  "force_regenerate": false
}

Response:
  {
    "simulation_id": "sim_xxxx",
    "task_id": "task_xxxx",
    "status": "generating",
    "message": "..."
  }
```

#### Report Access

| Method | Path | Description |
|---|---|---|
| GET | `/api/report/status/<simulation_id>` | Check report generation status |
| GET | `/api/report/<report_id>` | Get full report content |
| GET | `/api/report/simulation/<simulation_id>` | Get report by simulation ID |
| GET | `/api/report/list` | List all reports |
| GET | `/api/report/<report_id>/download` | Download report as file |

#### Report Chat (Step 5)

```
POST /api/report/chat
Content-Type: application/json

{
  "report_id": "report_xxxx",
  "message": "What caused the spike in agent activity?"
}
```

---

## Key Backend Classes and Data Models

### `Project` (`app/models/project.py`)

```python
@dataclass
class Project:
    project_id: str
    name: str
    status: ProjectStatus           # CREATED | ONTOLOGY_GENERATED | GRAPH_BUILDING | GRAPH_COMPLETED | FAILED
    files: list[dict]               # [{filename, size}]
    ontology: dict | None           # {entity_types: [...], edge_types: [...]}
    graph_id: str | None            # Zep graph UUID
    simulation_requirement: str | None
    chunk_size: int                 # default 500
    chunk_overlap: int              # default 50
```

### `SimulationState` (`app/services/simulation_manager.py`)

```python
@dataclass
class SimulationState:
    simulation_id: str
    project_id: str
    graph_id: str
    enable_twitter: bool
    enable_reddit: bool
    status: SimulationStatus        # CREATED | PREPARING | READY | RUNNING | PAUSED | STOPPED | COMPLETED | FAILED
    current_round: int
    twitter_status: str
    reddit_status: str
```

### `OasisAgentProfile` (`app/services/oasis_profile_generator.py`)

```python
@dataclass
class OasisAgentProfile:
    user_id: int
    user_name: str
    name: str
    bio: str
    persona: str                    # Rich character description
    karma: int                      # Reddit style
    friend_count: int               # Twitter style
    follower_count: int
    age: int | None
    gender: str | None
    mbti: str | None
    country: str | None
    profession: str | None
    interested_topics: list[str]
    source_entity_uuid: str | None
    source_entity_type: str | None
```

Methods:
- `to_reddit_format() -> dict`
- `to_twitter_format() -> dict`

### `AgentAction` (`app/services/simulation_runner.py`)

```python
@dataclass
class AgentAction:
    round_num: int
    timestamp: str
    platform: str                   # "twitter" | "reddit"
    agent_id: int
    agent_name: str
    action_type: str                # CREATE_POST | LIKE_POST | REPOST | FOLLOW | DO_NOTHING | etc.
    action_args: dict
    result: str | None
    success: bool
```

### `GraphBuilderService` (`app/services/graph_builder.py`)

```python
class GraphBuilderService:
    def __init__(self, api_key: str | None = None)
    def create_graph(self, name: str) -> str           # Returns graph_id
    def set_ontology(self, graph_id: str, ontology: dict)
    def add_text_batches(self, graph_id, chunks, batch_size=3, progress_callback=None) -> list[str]
    def get_graph_data(self, graph_id: str) -> dict    # {node_count, edge_count, nodes, edges}
    def delete_graph(self, graph_id: str)
```

### `ZepToolsService` (`app/services/zep_tools.py`)

Used by the Report Agent for knowledge retrieval:

```python
class ZepToolsService:
    # Primary retrieval tools
    def insight_forge(self, query: str, graph_id: str) -> InsightForgeResult
    def panorama_search(self, query: str, graph_id: str) -> PanoramaResult
    def quick_search(self, query: str, graph_id: str) -> SearchResult
    def interview_agent(self, agent_name: str, prompt: str, graph_id: str) -> InterviewResult
```

### IPC — `SimulationIPCClient` / `SimulationIPCServer`

The Flask backend uses `SimulationIPCClient` to write command JSON files; simulation scripts use `SimulationIPCServer` to poll and respond.

```python
# Command types
class CommandType(str, Enum):
    INTERVIEW = "interview"
    BATCH_INTERVIEW = "batch_interview"
    CLOSE_ENV = "close_env"
```

---

## Frontend API Module

Located in `frontend/src/api/`. All functions use an Axios instance with a 5-minute timeout and automatic retry (up to 3 times with exponential backoff).

```javascript
// frontend/src/api/graph.js — example calls
import { generateOntology, buildGraph, getProject } from './graph'

// frontend/src/api/simulation.js
import { startSimulation, getSimulationStatus, interviewAgent } from './simulation'

// frontend/src/api/report.js
import { generateReport, chatWithReport } from './report'
```

The Axios instance (`frontend/src/api/index.js`) targets `http://localhost:5001` by default (overridable via `VITE_API_BASE_URL` env var). During development, Vite proxies `/api` to the same backend URL.

---

## Configuration Extension Points

### LLM Provider

MiroFish supports any OpenAI SDK-compatible LLM. Set these environment variables:

```env
LLM_API_KEY=...
LLM_BASE_URL=https://your-provider.com/v1
LLM_MODEL_NAME=your-model
```

An optional "boost" LLM can be configured for high-throughput operations:

```env
LLM_BOOST_API_KEY=...
LLM_BOOST_BASE_URL=...
LLM_BOOST_MODEL_NAME=...
```

### OASIS Platform Actions

Available actions per platform are defined in `app/config.py`:

```python
OASIS_TWITTER_ACTIONS = [
    'CREATE_POST', 'LIKE_POST', 'REPOST', 'FOLLOW', 'DO_NOTHING', 'QUOTE_POST'
]
OASIS_REDDIT_ACTIONS = [
    'LIKE_POST', 'DISLIKE_POST', 'CREATE_POST', 'CREATE_COMMENT',
    'LIKE_COMMENT', 'DISLIKE_COMMENT', 'SEARCH_POSTS', 'SEARCH_USER',
    'TREND', 'REFRESH', 'DO_NOTHING', 'FOLLOW', 'MUTE'
]
```

### Supported Upload File Types

Configured in `Config.ALLOWED_EXTENSIONS`:
```python
ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt', 'markdown'}
```

Maximum upload size: 50 MB (`MAX_CONTENT_LENGTH`).

### Simulation Parameters

The `SimulationConfigGenerator` service auto-generates simulation parameters using LLM, including:
- `AgentActivityConfig` — per-agent activity level and behavior weights
- `TimeSimulationConfig` — time zone and hourly activity multipliers (defaults to Chinese timezone schedule)
- `EventConfig` — simulated events injected into the world during simulation
- `PlatformConfig` — platform-specific tuning

These can also be manually reviewed and adjusted via the Step 3 UI before starting the simulation.
