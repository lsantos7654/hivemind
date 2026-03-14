# MiroFish — Build System

## Build System Overview

MiroFish uses a hybrid build system that coordinates two independent stacks:

- **Frontend**: Node.js / npm + Vite
- **Backend**: Python / uv (Python package manager) + hatchling

A root-level `package.json` ties both stacks together through npm scripts, making it possible to install all dependencies and start both services with a single command.

## Configuration Files

| File | Stack | Purpose |
|---|---|---|
| `package.json` (root) | Both | Orchestration scripts using `concurrently` |
| `frontend/package.json` | Frontend | Frontend npm dependencies and Vite scripts |
| `frontend/vite.config.js` | Frontend | Vite build and dev server configuration |
| `backend/pyproject.toml` | Backend | Python project metadata, dependencies, build backend |
| `backend/requirements.txt` | Backend | Alternative pip-compatible dependency list |
| `backend/uv.lock` | Backend | Locked dependency tree managed by `uv` |
| `docker-compose.yml` | Deployment | Single-container Docker deployment |
| `Dockerfile` | Deployment | Container image build instructions |
| `.env.example` | Both | Template for required environment variables |

## External Dependencies

### Backend Python Dependencies

| Package | Version | Purpose |
|---|---|---|
| flask | >=3.0.0 | Web framework |
| flask-cors | >=6.0.0 | Cross-origin resource sharing |
| openai | >=1.0.0 | LLM API client (OpenAI SDK format) |
| zep-cloud | ==3.13.0 | Knowledge graph and memory store |
| camel-oasis | ==0.2.5 | Multi-agent social simulation (Twitter/Reddit) |
| camel-ai | ==0.2.78 | CAMEL agent framework underlying OASIS |
| PyMuPDF | >=1.24.0 | PDF text extraction |
| charset-normalizer | >=3.0.0 | Encoding detection for non-UTF-8 files |
| chardet | >=5.0.0 | Character encoding detection |
| python-dotenv | >=1.0.0 | Load environment variables from .env |
| pydantic | >=2.0.0 | Data validation |

Optional dev dependencies:
- `pytest>=8.0.0`
- `pytest-asyncio>=0.23.0`
- `pipreqs>=0.5.0`

### Frontend JavaScript Dependencies

| Package | Version | Purpose |
|---|---|---|
| vue | ^3.5.24 | Reactive UI framework |
| vue-router | ^4.6.3 | Client-side routing |
| axios | ^1.13.2 | HTTP client |
| d3 | ^7.9.0 | Graph/data visualization |

Dev dependencies:
- `vite ^7.2.4` — frontend build tool and dev server
- `@vitejs/plugin-vue ^6.0.1` — Vue SFC support for Vite

Root-level dev dependencies:
- `concurrently ^9.1.2` — run multiple npm scripts in parallel

## Build Targets and Commands

### Root-Level npm Scripts

All commands are run from the project root directory.

```bash
# Install ALL dependencies (root + frontend npm + backend Python)
npm run setup:all

# Install only npm dependencies (root + frontend)
npm run setup

# Install only backend Python dependencies (creates .venv via uv)
npm run setup:backend

# Start BOTH frontend and backend in development mode (parallel)
npm run dev

# Start backend only
npm run backend

# Start frontend only
npm run frontend

# Build frontend for production (outputs to frontend/dist/)
npm run build
```

### Frontend-Specific Commands

Run from `frontend/` directory:

```bash
npm run dev       # Start Vite dev server on port 3000
npm run build     # Production build
npm run preview   # Preview production build locally
```

### Backend-Specific Commands

Run from `backend/` directory:

```bash
uv sync           # Install dependencies from uv.lock (creates .venv)
uv run python run.py  # Run the Flask backend server
```

Or using pip:

```bash
pip install -r requirements.txt
python run.py
```

## How to Build

### Development Setup (Recommended)

**Prerequisites:**
- Node.js >= 18.0.0 (includes npm)
- Python >= 3.11, <= 3.12
- `uv` (Python package manager) — install via `pip install uv` or `curl -Ls https://astral.sh/uv/install.sh | sh`

**Steps:**

```bash
# 1. Clone the repository
git clone https://github.com/666ghj/MiroFish.git
cd MiroFish

# 2. Copy and fill in environment variables
cp .env.example .env
# Edit .env: set LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_NAME, ZEP_API_KEY

# 3. Install all dependencies
npm run setup:all

# 4. Start both services
npm run dev
```

Frontend: `http://localhost:3000`
Backend API: `http://localhost:5001`

### Production Build (Frontend)

```bash
npm run build
# Built files in frontend/dist/
```

The Vite dev server proxies `/api` requests to `http://localhost:5001` during development. In production, the backend must be configured to serve or be separately accessible.

## How to Deploy

### Docker (Simplest)

```bash
cp .env.example .env
# Edit .env with real API keys

docker compose up -d
```

The `docker-compose.yml` pulls the pre-built image `ghcr.io/666ghj/mirofish:latest`, reads `.env` from the project root, maps ports `3000` (frontend) and `5001` (backend), and mounts `./backend/uploads` for persistent data.

An alternative mirror address (`ghcr.nju.edu.cn/666ghj/mirofish:latest`) is provided in the compose file for faster pulls.

### Source Deployment

Run `npm run dev` for development. For production, run the frontend build (`npm run build`) and serve `frontend/dist/` with a static server (e.g., Nginx), then run the Flask backend separately with a production WSGI server (e.g., Gunicorn):

```bash
# Frontend static files
cd frontend && npm run build

# Backend production
cd backend && uv run gunicorn -w 4 -b 0.0.0.0:5001 "app:create_app()"
```

## Environment Variables

All required configuration is loaded from the `.env` file at the project root.

| Variable | Required | Default | Description |
|---|---|---|---|
| `LLM_API_KEY` | Yes | — | API key for LLM provider |
| `LLM_BASE_URL` | No | `https://api.openai.com/v1` | LLM API base URL |
| `LLM_MODEL_NAME` | No | `gpt-4o-mini` | LLM model name |
| `ZEP_API_KEY` | Yes | — | Zep Cloud API key |
| `LLM_BOOST_API_KEY` | No | — | Optional faster/cheaper LLM for profile gen |
| `LLM_BOOST_BASE_URL` | No | — | Optional boost LLM base URL |
| `LLM_BOOST_MODEL_NAME` | No | — | Optional boost LLM model name |
| `FLASK_HOST` | No | `0.0.0.0` | Flask bind host |
| `FLASK_PORT` | No | `5001` | Flask bind port |
| `FLASK_DEBUG` | No | `True` | Flask debug mode |
| `OASIS_DEFAULT_MAX_ROUNDS` | No | `10` | Default simulation rounds |
| `REPORT_AGENT_MAX_TOOL_CALLS` | No | `5` | Max tool calls per report section |
| `REPORT_AGENT_MAX_REFLECTION_ROUNDS` | No | `2` | Max reflection rounds in report |
| `REPORT_AGENT_TEMPERATURE` | No | `0.5` | LLM temperature for report generation |

## Testing

Backend tests use pytest:

```bash
cd backend
uv run pytest
# or
uv run pytest --asyncio-mode=auto  # for async tests
```

The `backend/scripts/test_profile_format.py` is a standalone validation script for agent profile format testing.
