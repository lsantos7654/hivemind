# Code Structure: Architecture Patterns with Python (cosmicpython/code)

## Annotated Directory Tree

```
cosmicpython/code/
├── README.md                         # Project overview, chapter/branch guide, build/test instructions
├── requirements.txt                  # Python dependencies (Flask, SQLAlchemy, Redis, pytest, etc.)
├── Makefile                          # Build targets: build, up, down, test, unit-tests, integration-tests, e2e-tests
├── Dockerfile                        # Python 3.9-slim image; installs requirements and src package
├── docker-compose.yml                # Multi-service stack: api, redis_pubsub, postgres, redis, mailhog
├── mypy.ini                          # mypy static type checker configuration
├── .travis.yml                       # (Legacy) Travis CI configuration
├── .github/
│   └── workflows/
│       └── run_tests_on_pull_request.yml   # GitHub Actions CI workflow
├── src/
│   ├── setup.py                      # setuptools package definition for the 'allocation' package
│   └── allocation/                   # Main application package
│       ├── __init__.py               # Empty package marker
│       ├── config.py                 # Environment-based configuration (Postgres, Redis, Email, API URLs)
│       ├── bootstrap.py              # Composition root: wires dependencies and returns MessageBus
│       ├── views.py                  # CQRS read side: query functions against the read model
│       ├── domain/                   # Pure domain layer — no framework imports
│       │   ├── __init__.py
│       │   ├── model.py              # Domain aggregates: Product, Batch, OrderLine
│       │   ├── events.py             # Domain events: Allocated, Deallocated, OutOfStock
│       │   └── commands.py           # Application commands: Allocate, CreateBatch, ChangeBatchQuantity
│       ├── adapters/                 # Infrastructure adapters (ports-and-adapters)
│       │   ├── __init__.py
│       │   ├── orm.py                # Classical SQLAlchemy table definitions and mapper setup
│       │   ├── repository.py         # AbstractRepository + SqlAlchemyRepository
│       │   ├── notifications.py      # AbstractNotifications + EmailNotifications (SMTP)
│       │   └── redis_eventpublisher.py  # Publish domain events to Redis pub/sub channels
│       ├── service_layer/            # Orchestration layer: use cases and message handling
│       │   ├── __init__.py
│       │   ├── handlers.py           # Command/event handler functions + handler registries
│       │   ├── messagebus.py         # MessageBus: routes commands/events to handlers
│       │   └── unit_of_work.py       # AbstractUnitOfWork + SqlAlchemyUnitOfWork
│       └── entrypoints/              # External-facing entry points
│           ├── __init__.py
│           ├── flask_app.py          # Flask REST API (POST /add_batch, POST /allocate, GET /allocations/<orderid>)
│           └── redis_eventconsumer.py  # Redis pub/sub consumer for 'change_batch_quantity' channel
└── tests/
    ├── __init__.py
    ├── pytest.ini                    # Pytest configuration
    ├── conftest.py                   # Shared fixtures: DB sessions, ORM mappers, service wait helpers
    ├── random_refs.py                # Test helpers: generate random SKU/orderid/batchref strings
    ├── unit/                         # Unit tests — no I/O, use fakes
    │   ├── test_batches.py           # Tests for Batch domain logic (allocate, can_allocate, etc.)
    │   ├── test_product.py           # Tests for Product aggregate (allocate, change_batch_quantity)
    │   └── test_handlers.py          # Tests for service layer handlers via FakeUoW/FakeRepository
    ├── integration/                  # Integration tests — hit real Postgres (via SQLite in some cases)
    │   ├── __init__.py
    │   ├── test_repository.py        # Tests for SqlAlchemyRepository
    │   ├── test_uow.py               # Tests for SqlAlchemyUnitOfWork
    │   ├── test_views.py             # Tests for CQRS views (allocations_view table)
    │   └── test_email.py             # Tests for EmailNotifications adapter
    └── e2e/                          # End-to-end tests — hit the running Flask API + Redis
        ├── __init__.py
        ├── api_client.py             # HTTP helper functions (post_to_add_batch, post_to_allocate, get_allocation)
        ├── redis_client.py           # Redis helper for publishing test events
        ├── test_api.py               # E2E tests for HTTP API happy/unhappy paths
        └── test_external_events.py   # E2E tests for Redis event consumer
```

## Module and Package Organization

The application follows a strict **layered hexagonal architecture** with dependency rules enforced by convention:

1. **`domain/`** — innermost layer; no imports from any other app layer. Contains pure Python business logic.
2. **`service_layer/`** — imports from `domain/` only (plus abstract adapters via TYPE_CHECKING). Contains orchestration logic.
3. **`adapters/`** — imports from `domain/` and `config`. Provides concrete I/O implementations.
4. **`entrypoints/`** — imports from `service_layer/`, `domain/`, `bootstrap`, and `views`. Entry points for external interaction.
5. **`bootstrap.py`** and **`views.py`** — composition root and read-side query module, respectively.

## Main Source Directories and Their Purposes

### `src/allocation/domain/`

The **domain layer** is the core of the application. It contains:

- **`model.py`**: The domain model with three classes:
  - `Product` — the aggregate root. Owns a list of `Batch` objects, holds a `version_number` for optimistic locking, and accumulates domain `events`.
  - `Batch` — a stock batch with a SKU, quantity, and optional ETA. Tracks allocations as a set of `OrderLine` objects. Provides `allocate()`, `deallocate_one()`, `can_allocate()`, and quantity properties.
  - `OrderLine` — a value object (frozen dataclass) representing a line in a customer order.
- **`events.py`**: Dataclass event types inheriting from `Event` base class: `Allocated`, `Deallocated`, `OutOfStock`.
- **`commands.py`**: Dataclass command types inheriting from `Command` base class: `Allocate`, `CreateBatch`, `ChangeBatchQuantity`.

### `src/allocation/service_layer/`

The **service/application layer** orchestrates use cases:

- **`handlers.py`**: Pure functions that implement use cases. Each handler takes a command/event and injected dependencies (UoW, notifications, publish). Contains `EVENT_HANDLERS` and `COMMAND_HANDLERS` dictionaries mapping message types to handler functions.
- **`messagebus.py`**: The `MessageBus` class. Its `handle()` method processes a queue of `Message` objects, dispatching events to multiple handlers and commands to a single handler. Newly emitted domain events are collected from the UoW after each handler and appended to the queue.
- **`unit_of_work.py`**: `AbstractUnitOfWork` (ABC) defines the context manager interface and `collect_new_events()` to harvest events from seen aggregates. `SqlAlchemyUnitOfWork` provides the production SQLAlchemy-backed implementation.

### `src/allocation/adapters/`

The **adapters layer** bridges the application to infrastructure:

- **`orm.py`**: SQLAlchemy `Table` objects (classical mapping). Defines `order_lines`, `products`, `batches`, `allocations`, and `allocations_view` tables. `start_mappers()` registers the classical mapper. An SQLAlchemy `load` event listener resets `product.events = []` on load.
- **`repository.py`**: `AbstractRepository` (ABC) tracks `seen` products and delegates `_add`, `_get`, `_get_by_batchref` to subclasses. `SqlAlchemyRepository` implements these with SQLAlchemy session queries.
- **`notifications.py`**: `AbstractNotifications` (ABC) with `send(destination, message)`. `EmailNotifications` sends via SMTP using Python's `smtplib`.
- **`redis_eventpublisher.py`**: `publish(channel, event)` serializes events to JSON and publishes to Redis.

### `src/allocation/entrypoints/`

The **entrypoints** are the boundary between the application and the outside world:

- **`flask_app.py`**: Flask app with three routes. Bootstraps the `MessageBus` at module load time and uses it to handle commands.
- **`redis_eventconsumer.py`**: Subscribes to the `change_batch_quantity` Redis channel. In a loop, receives messages and dispatches `ChangeBatchQuantity` commands to the bus.

### `src/allocation/bootstrap.py`

The **composition root**. The `bootstrap()` function:
1. Optionally calls `orm.start_mappers()` (skipped in tests to avoid duplicate mapper registration)
2. Injects dependencies into handler functions using Python `inspect` (parameter-name matching)
3. Returns a fully wired `MessageBus`

### `src/allocation/views.py`

The **CQRS read side**. `allocations(orderid, uow)` queries the `allocations_view` table directly via raw SQL, bypassing the domain model entirely for read performance.

## Key Files and Their Roles

| File | Role |
|------|------|
| `domain/model.py` | Domain aggregates, entities, value objects; core business rules |
| `domain/events.py` | Domain event dataclasses raised by aggregates |
| `domain/commands.py` | Command dataclasses representing user intentions |
| `service_layer/handlers.py` | Use case functions + handler registries |
| `service_layer/messagebus.py` | Message dispatcher: routes commands/events to handlers |
| `service_layer/unit_of_work.py` | Transaction boundary and event harvesting |
| `adapters/orm.py` | DB schema + classical mapper; keeps domain model clean |
| `adapters/repository.py` | Data access abstraction over SQLAlchemy |
| `bootstrap.py` | Composition root: wires all dependencies for production or test |
| `views.py` | Read-model queries (CQRS read side) |
| `entrypoints/flask_app.py` | HTTP REST API (write side) |
| `entrypoints/redis_eventconsumer.py` | External event ingestion from Redis |
| `tests/unit/test_handlers.py` | Demonstrates testing service layer with Fake adapters |
| `tests/conftest.py` | DB/ORM/session fixtures for integration/e2e tests |

## Code Organization Patterns

1. **Ports and Adapters (Hexagonal Architecture)**: Abstract base classes (`AbstractRepository`, `AbstractUnitOfWork`, `AbstractNotifications`) are the "ports." Concrete implementations (`SqlAlchemyRepository`, `SqlAlchemyUnitOfWork`, `EmailNotifications`) are the "adapters."

2. **Classical SQLAlchemy Mapping**: Domain classes are plain Python with no SQLAlchemy imports. `orm.py` maps them externally, preserving domain purity.

3. **Dependency Injection by Inspection**: `bootstrap.py:inject_dependencies()` uses `inspect.signature()` to match handler parameter names against available dependencies, wrapping each handler in a lambda closure.

4. **Event Sourcing via Aggregate Events**: `Product.events` is a list that accumulates domain events during command processing. `UnitOfWork.collect_new_events()` drains this list, feeding the `MessageBus` queue.

5. **Fake Adapters for Testing**: `tests/unit/test_handlers.py` defines `FakeRepository`, `FakeUnitOfWork`, and `FakeNotifications` as test doubles, allowing the service layer to be tested without any I/O.

6. **Three-Tier Test Strategy**: Unit tests (no I/O, fakes), integration tests (real database via SQLite or Postgres), and e2e tests (running Docker stack). Separate `make` targets for each.
