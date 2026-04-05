# Firecrawl — Build System

## Build System Overview

Firecrawl is a **polyglot monorepo** using different build tools for each component:

| Component | Language | Build Tool | Package Manager |
|-----------|----------|------------|-----------------|
| `apps/api` | TypeScript/Node.js | `tsc` (TypeScript compiler) | npm |
| `apps/python-sdk` | Python | setuptools / pyproject.toml | pip |
| `apps/js-sdk` | TypeScript | tsup | pnpm |
| `apps/playwright-service-ts` | TypeScript | tsc (implicit via tsx) | pnpm |
| `apps/rust-sdk` | Rust | Cargo | cargo |
| `apps/java-sdk` | Java | Gradle | gradle |
| `apps/elixir-sdk` | Elixir | Mix | mix |
| `apps/ui/ingestion-ui` | TypeScript/React | Vite | pnpm |
| `apps/go-html-to-md-service` | Go | go build | go |
| Full deployment | All | Docker Compose | — |

## API Server (`apps/api`)

### Configuration Files
- `apps/api/package.json` — npm scripts, dependencies, version
- `apps/api/tsconfig.json` — TypeScript compiler options
- `apps/api/.husky/` — Git hooks (pre-commit linting)

### Build Commands
```bash
# Development (watch mode, hot reload via tsx)
npm run dev

# TypeScript compile to dist/
npm run build

# Production start (compile then run)
npm start

# Production without recompile
npm run server:production:nobuild
```

### Worker Commands
Workers are separate processes that consume from the job queues:
```bash
# Main scrape queue worker
npm run workers                        # dev (watch)
npm run worker:production              # production

# NuQ worker (RabbitMQ-backed)
npm run nuq-worker:production

# NuQ prefetch worker
npm run nuq-prefetch-worker:production

# NuQ reconciler worker
npm run nuq-reconciler-worker:production

# Extract worker
npm run extract-worker:production

# Index worker
npm run index-worker:production
```

### Test Commands
```bash
# Unit tests (excludes e2e no-auth tests)
npm test

# Snapshot tests only (v1 + v2)
npm run test:snips

# Full e2e with auth
npm run test:full

# Production test suite
npm run test:prod
```

Tests use **Jest** and are organized under `src/__tests__/`:
- `snips/v1/` and `snips/v2/` — API snapshot/unit tests (fast, no real network)
- `e2e_withAuth/`, `e2e_noAuth/` — End-to-end tests against a running server

### Key Dependencies (API)
- **Express** — HTTP server framework
- **express-ws** — WebSocket support for crawl status streaming
- **BullMQ** — Redis-backed job queue
- **Zod** — Schema validation for all request/response types
- **uuid (v7)** — Time-ordered job IDs
- **pino** — Structured JSON logging
- **Supabase** (`@supabase/supabase-js`) — Optional auth/database backend
- **OpenAI** (`openai`) — LLM integration for extraction features
- **@sentry/node** — Error monitoring
- **opentelemetry** — Distributed tracing
- **pg** — PostgreSQL client for NuQ
- **amqplib** — RabbitMQ client for NuQ
- **culori** — Color science library (brand extraction)
- **jest** + **supertest** — Testing framework

## Python SDK (`apps/python-sdk`)

### Configuration Files
- `apps/python-sdk/pyproject.toml` — Build config, metadata, dependencies
- `apps/python-sdk/setup.py` — Setuptools entry (delegates to pyproject.toml)

### Build and Install
```bash
cd apps/python-sdk

# Install in development mode
pip install -e .

# Build distribution packages
python -m build

# Install from PyPI
pip install firecrawl-py
```

### Key Dependencies (Python SDK)
```
requests       # Synchronous HTTP
httpx          # HTTP client used by v2 client internals
python-dotenv  # .env file loading
websockets     # WebSocket support (crawl status streaming)
nest-asyncio   # Nested event loop support for async
pydantic>=2.0  # Data validation and serialization
aiohttp        # Async HTTP client
```

### Testing (Python SDK)
```bash
cd apps/python-sdk
# Tests are in tests/ directory
pytest tests/
```

Test files:
- `tests/test_timeout_conversion.py` — Timeout parameter handling
- `tests/test_change_tracking.py` — Change tracking/diff features
- `tests/test_agent_integration.py` — Agent API integration
- `tests/test_api_key_handling.py` — API key validation

## JavaScript SDK (`apps/js-sdk`)

### Configuration Files
- `apps/js-sdk/firecrawl/package.json` — Package metadata and scripts
- `apps/js-sdk/firecrawl/tsup.config.ts` — tsup bundler configuration (CJS + ESM)
- `apps/js-sdk/firecrawl/tsconfig.json` — TypeScript config
- `apps/js-sdk/firecrawl/jest.config.js` — Jest test config
- `apps/js-sdk/audit-ci.jsonc` — CI security audit config

### Build Commands
```bash
cd apps/js-sdk/firecrawl

# Install with pnpm
pnpm install

# Build (outputs CJS + ESM to dist/)
pnpm build

# Watch mode
pnpm dev

# Run tests
pnpm test
```

### Key Dependencies (JS SDK)
- **tsup** — ESM/CJS bundler
- **TypeScript** — Type system
- **jest** + **ts-jest** — Test framework

## Rust SDK (`apps/rust-sdk`)

### Configuration Files
- `apps/rust-sdk/Cargo.toml` — Package metadata, dependencies
- `apps/rust-sdk/Cargo.lock` — Locked dependency versions

### Build Commands
```bash
cd apps/rust-sdk

# Build the library
cargo build

# Run tests (unit)
cargo test

# Run e2e tests (requires API running)
cargo test --test e2e_with_auth
cargo test --test v2_e2e

# Run examples
cargo run --example v2_example
cargo run --example extract_example
cargo run --example search_example
```

### Key Dependencies (Rust SDK)
```toml
reqwest = { version = "0.12", features = ["json", "blocking"] }
serde = { version = "^1.0", features = ["derive"] }
serde_json = "^1.0"
serde_with = "^3.9"
tokio = { version = "^1", features = ["full"] }
thiserror = "^1.0"
uuid = { version = "^1.10", features = ["v4"] }
schemars = "0.8.22"
```

## Docker Compose Deployment

### Configuration
- `docker-compose.yaml` — Full service orchestration at repo root
- `.env` file — Environment variables (copy from `.env.example`)

### Services
| Service | Image/Build | Port | Purpose |
|---------|-------------|------|---------|
| `api` | `apps/api` (build) | 3002 | Main REST API + workers |
| `playwright-service` | `apps/playwright-service-ts` (build) | 3000 | Playwright browser |
| `redis` | `redis:alpine` | 6379 | Job queue state, caching |
| `rabbitmq` | `rabbitmq:3-management` | 5672 | NuQ job queue |
| `nuq-postgres` | `apps/nuq-postgres` (build) | 5432 | Job persistence |

### Deploy Commands
```bash
# Start all services
docker compose up

# Start in background
docker compose up -d

# Rebuild and start
docker compose up --build

# Stop
docker compose down
```

### Resource Configuration
- API: 4 CPUs, 8GB RAM (configurable)
- Playwright: 2 CPUs, 4GB RAM
- Workers: `NUM_WORKERS_PER_QUEUE` (default: 8)
- Concurrent pages: `CRAWL_CONCURRENT_REQUESTS` (default: 10)
- Browser pool: `BROWSER_POOL_SIZE` (default: 5)

## Environment Variables

Required for self-hosting (from `SELF_HOST.md`):
```bash
PORT=3002
HOST=0.0.0.0
USE_DB_AUTHENTICATION=false    # Set true to enable Supabase auth

# Optional: AI features (JSON format, extract API)
OPENAI_API_KEY=sk-...
# Or Ollama: OLLAMA_BASE_URL=http://localhost:11434/api

# Optional: Proxy for scraping
PROXY_SERVER=http://proxy:port
PROXY_USERNAME=user
PROXY_PASSWORD=pass

# Optional: Search backend
SEARXNG_ENDPOINT=http://searxng:8080

# Optional: Webhooks
SELF_HOSTED_WEBHOOK_URL=http://your-webhook

# Optional: Authentication
SUPABASE_URL=https://...
SUPABASE_SERVICE_TOKEN=...

# Worker config
NUM_WORKERS_PER_QUEUE=8
CRAWL_CONCURRENT_REQUESTS=10
MAX_CONCURRENT_JOBS=5
```

## CI/CD

- `audit-ci.jsonc` files in JS packages enforce npm audit security thresholds
- `.husky/` git hooks run linting on pre-commit
- Tests are run via Jest for Node.js, pytest for Python, cargo test for Rust
- The `test:snips` script provides fast, mock-based validation of API behavior without a live server
