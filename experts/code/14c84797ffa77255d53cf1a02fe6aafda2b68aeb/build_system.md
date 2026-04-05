# Build System: Architecture Patterns with Python (cosmicpython/code)

## Build System Type and Configuration Files

The project uses a **Make + Docker Compose** build system. There is no complex build tool (no setuptools build, no Bazel, no Gradle) — Python packaging is minimal. The key configuration files are:

| File | Purpose |
|------|---------|
| `Makefile` | Top-level build targets for building containers, running tests |
| `Dockerfile` | Image definition for both `api` and `redis_pubsub` services |
| `docker-compose.yml` | Multi-service stack definition (api, redis_pubsub, postgres, redis, mailhog) |
| `requirements.txt` | Python package dependencies |
| `src/setup.py` | Minimal setuptools package definition for `pip install -e src/` |
| `mypy.ini` | Static type checker configuration |
| `tests/pytest.ini` | Pytest configuration |
| `.travis.yml` | Legacy Travis CI config |
| `.github/workflows/run_tests_on_pull_request.yml` | GitHub Actions CI |

## External Dependencies

### Application Dependencies (`requirements.txt`)

```
# app
sqlalchemy<2          # ORM and SQL toolkit (classical mapper); pinned below v2 due to mapper() API removal
flask                 # HTTP web framework for the REST API entrypoint
psycopg2-binary       # PostgreSQL adapter for Python (binary distribution, no build deps needed)
redis                 # Redis client for pub/sub publishing and consuming

# dev/tests
pytest                # Test runner
pytest-icdiff         # Improved diff output in pytest failures
mypy                  # Static type checker
pylint                # Linter
requests              # HTTP client used in e2e tests
tenacity              # Retry library used in test fixtures to wait for services
```

**Notable constraint**: `sqlalchemy<2` — the code uses the classical `mapper()` API which was removed in SQLAlchemy 2.0.

### Infrastructure Services (via Docker Compose)

| Service | Image | Purpose |
|---------|-------|---------|
| `postgres` | `postgres:9.6` | Primary relational database (PostgreSQL 9.6) |
| `redis` | `redis:alpine` | Message broker for pub/sub (events consumer + publisher) |
| `mailhog` | `mailhog/mailhog` | SMTP mock server for email notifications in development/testing |

### Python Package

The `allocation` package is installed as an editable package (`pip install -e /src`). The `src/setup.py` defines:

```python
setup(
    name="allocation",
    version="0.1",
    packages=["allocation"],
)
```

This allows `import allocation` to work from any directory within the Docker container.

## Build Targets and Commands

### Makefile Targets

```makefile
all: down build up test       # Full cycle: tear down, build, start, test

build:                         # Build Docker images
    docker-compose build

up:                            # Start all services in detached mode
    docker-compose up -d

down:                          # Stop and remove all containers (including orphans)
    docker-compose down --remove-orphans

test: up                       # Run all tests (unit + integration + e2e) inside the api container
    docker-compose run --rm --no-deps --entrypoint=pytest api /tests/unit /tests/integration /tests/e2e

unit-tests:                    # Run only unit tests (no services needed)
    docker-compose run --rm --no-deps --entrypoint=pytest api /tests/unit

integration-tests: up          # Run integration tests (requires postgres, redis)
    docker-compose run --rm --no-deps --entrypoint=pytest api /tests/integration

e2e-tests: up                  # Run e2e tests (requires full stack including api)
    docker-compose run --rm --no-deps --entrypoint=pytest api /tests/e2e

logs:                          # Tail recent logs from api and redis_pubsub services
    docker-compose logs --tail=25 api redis_pubsub

black:                         # Format all Python files with black (line length 86)
    black -l 86 $$(find * -name '*.py')
```

The `COMPOSE_DOCKER_CLI_BUILD=1` and `DOCKER_BUILDKIT=1` environment variables at the top of the Makefile enable BuildKit for faster Docker builds.

## How to Build

### Using Docker (Recommended, Required from Chapter 3+)

```sh
# Build Docker images
make build

# Start all services
make up

# Run all tests
make test

# Full cycle
make all
```

### Using a Local Virtualenv (Optional, Chapters 1-2 or as supplement)

```sh
# Create and activate a virtualenv
python3.8 -m venv .venv && source .venv/bin/activate

# Install dependencies for chapters 1-2
pip install pytest

# For chapter 2
pip install pytest sqlalchemy

# For chapter 4+
pip install -r requirements.txt

# For chapter 6+ (installs the allocation package in editable mode)
pip install -r requirements.txt
pip install -e src/
```

## How to Test

### All Tests (via Docker)

```sh
make test
# equivalent to:
docker-compose run --rm --no-deps --entrypoint=pytest api /tests/unit /tests/integration /tests/e2e
```

### Individual Test Suites

```sh
# Unit tests only (fast, no services needed)
make unit-tests
# or locally:
pytest tests/unit

# Integration tests (requires postgres and redis)
make integration-tests
# or locally (with services up):
make up && pytest tests/integration

# End-to-end tests (requires full stack)
make e2e-tests
# or locally (with services up):
make up && pytest tests/e2e
```

### Test Fixtures and Infrastructure

- **`tests/conftest.py`** provides shared fixtures:
  - `in_memory_sqlite_db` / `sqlite_session_factory` — for integration tests without Postgres
  - `postgres_db` / `postgres_session_factory` / `postgres_session` — for full integration tests
  - `mappers` — calls `start_mappers()` and `clear_mappers()` around each test
  - `restart_api` — touches `flask_app.py` to trigger Flask debug reload
  - `restart_redis_pubsub` — restarts the redis_pubsub container via `docker-compose`
  - `wait_for_postgres_to_come_up`, `wait_for_webapp_to_come_up`, `wait_for_redis_to_come_up` — retry helpers using `tenacity`

- **`tests/random_refs.py`** provides `random_sku()`, `random_orderid()`, `random_batchref()` for generating unique test identifiers.

## How to Deploy / Run

### Running Services

The Docker Compose stack defines two application services:

**`api` service** — Flask REST API:
```sh
flask run --host=0.0.0.0 --port=80
# Exposed on host port 5005
# Environment: FLASK_APP=allocation/entrypoints/flask_app.py, FLASK_DEBUG=1
```

**`redis_pubsub` service** — Redis event consumer:
```sh
python /src/allocation/entrypoints/redis_eventconsumer.py
# Subscribes to 'change_batch_quantity' Redis channel
```

### Environment Variables

| Variable | Default (local) | Default (container) | Purpose |
|----------|----------------|---------------------|---------|
| `DB_HOST` | `localhost` | `postgres` | PostgreSQL hostname |
| `DB_PASSWORD` | `abc123` | `abc123` | PostgreSQL password |
| `REDIS_HOST` | `localhost` | `redis` | Redis hostname |
| `EMAIL_HOST` | `localhost` | `mailhog` | SMTP server hostname |
| `API_HOST` | `localhost` | `api` | Flask API hostname (used in e2e tests) |
| `FLASK_APP` | — | `allocation/entrypoints/flask_app.py` | Flask app module |
| `FLASK_DEBUG` | — | `1` | Enable Flask debug/reload |

### Port Mappings (Host → Container)

| Host Port | Container Port | Service |
|-----------|---------------|---------|
| `5005` | `80` | Flask API |
| `54321` | `5432` | PostgreSQL |
| `63791` | `6379` | Redis |
| `11025` | `1025` | Mailhog SMTP |
| `18025` | `8025` | Mailhog Web UI |

The config module (`src/allocation/config.py`) uses these non-standard local ports to detect whether it is running locally or in a container and adjusts connection strings accordingly.

## Static Analysis

```sh
# Type checking
mypy src/

# Linting (pylint)
pylint src/allocation/

# Code formatting
make black
```

The `mypy.ini` configures `mypy_path = ./src`, enables `check_untyped_defs`, and suppresses missing import errors for `pytest`, `sqlalchemy`, and `redis` stubs.
