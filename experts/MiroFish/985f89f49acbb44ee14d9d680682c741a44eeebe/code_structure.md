# MiroFish — Code Structure

## Annotated Directory Tree

```
MiroFish/                          # Project root
├── .env.example                   # Template for required environment variables
├── .gitignore
├── .dockerignore
├── docker-compose.yml             # Single-service Docker Compose deployment
├── Dockerfile                     # Container image definition
├── LICENSE                        # AGPL-3.0
├── package.json                   # Root-level npm scripts (orchestrates both stacks)
├── package-lock.json
├── README.md                      # Chinese documentation
├── README-EN.md                   # English documentation
├── static/                        # Static assets (logos, screenshots, demo covers)
│   └── image/
│
├── backend/                       # Python Flask backend
│   ├── pyproject.toml             # Python project metadata and dependency declarations (hatchling build)
│   ├── requirements.txt           # Legacy pip requirements (mirrors pyproject.toml deps)
│   ├── uv.lock                    # Locked dependency tree for uv package manager
│   ├── run.py                     # Backend entry point; validates config, creates Flask app, starts server
│   ├── app/                       # Main application package
│   │   ├── __init__.py            # Flask app factory (create_app); registers blueprints, CORS, logging
│   │   ├── config.py              # Config class; loads .env, exposes all config constants
│   │   ├── api/                   # HTTP route handlers (Flask Blueprints)
│   │   │   ├── __init__.py        # Blueprint declarations: graph_bp, simulation_bp, report_bp
│   │   │   ├── graph.py           # /api/graph routes: project management, ontology generation, graph building
│   │   │   ├── simulation.py      # /api/simulation routes: entities, profile generation, simulation control
│   │   │   └── report.py          # /api/report routes: report generation, retrieval, chat
│   │   ├── services/              # Business logic layer
│   │   │   ├── __init__.py        # Re-exports all service classes
│   │   │   ├── ontology_generator.py      # LLM-driven ontology (entity/edge type) generation from docs
│   │   │   ├── graph_builder.py           # Zep Cloud graph CRUD, text chunking upload, episode wait
│   │   │   ├── text_processor.py          # Text preprocessing and chunking utilities
│   │   │   ├── zep_entity_reader.py       # Read and filter entities from Zep graph
│   │   │   ├── oasis_profile_generator.py # Convert Zep entities → OASIS agent profiles (Twitter/Reddit)
│   │   │   ├── simulation_config_generator.py  # LLM-driven simulation parameter generation
│   │   │   ├── simulation_manager.py      # Orchestrate simulation lifecycle and state persistence
│   │   │   ├── simulation_runner.py       # Launch/monitor simulation subprocesses; IPC; memory updates
│   │   │   ├── simulation_ipc.py          # File-based IPC between Flask and simulation subprocesses
│   │   │   ├── report_agent.py            # ReACT-style report generation agent; report state management
│   │   │   ├── zep_tools.py               # Zep retrieval tool wrappers (InsightForge, PanoramaSearch, etc.)
│   │   │   └── zep_graph_memory_updater.py  # Write simulation agent activities back to Zep as episodes
│   │   ├── models/                # Data model layer (filesystem-persisted JSON)
│   │   │   ├── __init__.py
│   │   │   ├── project.py         # Project dataclass + ProjectManager (CRUD, file storage)
│   │   │   └── task.py            # Task dataclass + TaskManager (async task status tracking)
│   │   └── utils/                 # Shared utility modules
│   │       ├── __init__.py
│   │       ├── file_parser.py     # Extract text from PDF (PyMuPDF), Markdown, TXT files
│   │       ├── llm_client.py      # Thin OpenAI SDK wrapper (LLMClient)
│   │       ├── logger.py          # Logging setup (setup_logger, get_logger)
│   │       ├── retry.py           # Retry decorators and helpers
│   │       └── zep_paging.py      # Zep pagination helpers (fetch_all_nodes, fetch_all_edges)
│   └── scripts/                   # Standalone simulation scripts (run directly by SimulationRunner)
│       ├── run_parallel_simulation.py   # Dual-platform (Twitter + Reddit) simulation runner script
│       ├── run_twitter_simulation.py    # Twitter-only simulation runner script
│       ├── run_reddit_simulation.py     # Reddit-only simulation runner script
│       ├── action_logger.py             # Shared action logging for simulation scripts
│       └── test_profile_format.py       # Test/validation for agent profile format
│
└── frontend/                      # Vue 3 frontend
    ├── index.html                 # SPA entry HTML
    ├── package.json               # Frontend npm dependencies
    ├── package-lock.json
    ├── vite.config.js             # Vite build config; dev server port 3000, proxies /api to :5001
    ├── public/                    # Static public assets
    └── src/                       # Vue application source
        ├── main.js                # App bootstrap (createApp, use router, mount)
        ├── App.vue                # Root component with router-view
        ├── router/
        │   └── index.js           # Vue Router route definitions
        ├── store/
        │   ├── pendingUpload.js   # Upload state store
        │   └── index.js           # Global store index
        ├── api/
        │   ├── index.js           # Axios instance with interceptors and retry logic
        │   ├── graph.js           # Graph API call wrappers
        │   ├── simulation.js      # Simulation API call wrappers
        │   └── report.js          # Report API call wrappers
        ├── assets/                # Frontend assets (CSS, images)
        ├── views/                 # Page-level views
        │   ├── Home.vue           # Landing/home page
        │   ├── MainView.vue       # Main workflow container view
        │   ├── Process.vue        # Step-by-step workflow process view (wraps step components)
        │   ├── SimulationView.vue # Simulation configuration view
        │   ├── SimulationRunView.vue  # Live simulation monitoring view
        │   ├── ReportView.vue     # Report display view
        │   └── InteractionView.vue    # Agent/report chat interaction view
        └── components/            # Reusable and step-specific components
            ├── Step1GraphBuild.vue    # Step 1: Upload docs and generate ontology
            ├── Step2EnvSetup.vue      # Step 2: Entity review and agent profile generation
            ├── Step3Simulation.vue    # Step 3: Simulation configuration and launch
            ├── Step4Report.vue        # Step 4: Report generation and display
            ├── Step5Interaction.vue   # Step 5: Deep chat interaction with agents
            ├── GraphPanel.vue         # D3.js-powered knowledge graph visualization panel
            └── HistoryDatabase.vue    # Saved project/simulation history browser
```

## Module and Package Organization

### Backend

The backend follows a classic layered Flask architecture:

- **Entry point** (`run.py`): Validates environment, invokes the app factory, starts the WSGI server.
- **App factory** (`app/__init__.py`): Creates the Flask instance, applies CORS, registers cleanup hooks and blueprints.
- **API layer** (`app/api/`): Three Flask Blueprints, each handling one domain. Routes are defined as functions decorated with `@<blueprint>.route(...)`. All handlers return JSON with a consistent `{"success": bool, "data": ..., "error": ...}` shape.
- **Services layer** (`app/services/`): Stateless (or internally stateful) classes and functions that implement the actual business logic. Services call external APIs (Zep, LLM) and interact with the models layer.
- **Models layer** (`app/models/`): `Project` and `Task` dataclasses, each with a corresponding `Manager` class that handles JSON serialization to/from the filesystem (`backend/uploads/` directory).
- **Utils layer** (`app/utils/`): Shared infrastructure — logging, LLM client, file parsing, retry logic, Zep pagination.
- **Scripts** (`scripts/`): Standalone Python scripts that are launched as subprocesses by `SimulationRunner`. They run the actual OASIS simulation loop and communicate back to Flask via the IPC protocol.

### Frontend

The frontend follows a standard Vue 3 SPA structure:

- **Router**: Defines page-level navigation between home, workflow steps, and interaction views.
- **Store**: Minimal reactive state shared across components (pending upload data).
- **API module**: Axios-based wrappers grouped by domain, with retry logic and centralized error handling.
- **Views**: Page containers that orchestrate layouts and contain the major workflow steps.
- **Components**: Large step-specific Vue SFCs (Single File Components) that contain the UI logic for each of the five workflow phases. `GraphPanel.vue` is a self-contained D3.js graph renderer.

## Code Organization Patterns

- **Async operations via background threads**: Graph building and report generation are dispatched via `threading.Thread` in route handlers, allowing the HTTP response to return immediately with a `task_id`.
- **Filesystem as state store**: Project and task state is serialized as JSON files under `backend/uploads/`. This avoids the need for a database.
- **Subprocess-based simulation isolation**: OASIS simulations run as separate Python subprocesses launched via `subprocess` to avoid blocking the Flask server and to allow platform-level process isolation.
- **File-based IPC**: The Flask backend and simulation subprocesses exchange commands and responses through a structured directory of JSON files, implementing a polling-based command/response protocol.
- **Zep as primary memory backend**: All long-term knowledge — both the initial document knowledge graph and the evolving simulation episode memory — is stored in Zep Cloud.
- **OpenAI SDK compatibility layer**: The LLM client is designed to work with any provider that implements the OpenAI REST API, enabling easy model swapping via environment variables.
