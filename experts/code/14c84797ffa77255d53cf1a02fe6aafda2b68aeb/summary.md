# Summary: Architecture Patterns with Python (cosmicpython/code)

## Repository Purpose and Goals

This repository contains the **example application code** for the book *"Architecture Patterns with Python"* (also known as "Cosmic Python") by Harry Percival and Bob Gregory. The project demonstrates how to apply enterprise-grade software architecture patterns to a Python web application — specifically a **stock allocation service** for a fictional retail business.

The central goal is to show readers how patterns from domain-driven design (DDD) and enterprise architecture — Repository, Unit of Work, Service Layer, Message Bus, CQRS, and Event Sourcing — can be applied idiomatically in Python. Each chapter of the book has a corresponding branch in the repository, so the codebase evolves chapter by chapter. The commit at `14c84797ffa77255d53cf1a02fe6aafda2b68aeb` represents the state at a late chapter, where the full architecture (including event-driven messaging via Redis pub/sub) is in place.

## Key Features and Capabilities

- **Domain Model**: Pure Python domain entities (`Product`, `Batch`, `OrderLine`) with no framework dependencies. Business logic lives entirely in the domain layer.
- **Repository Pattern**: An abstract `AbstractRepository` decouples the domain from the database, with a concrete `SqlAlchemyRepository` for production and `FakeRepository` for testing.
- **Unit of Work Pattern**: `AbstractUnitOfWork` wraps database sessions, collects domain events from aggregates, and ensures commit/rollback semantics. `SqlAlchemyUnitOfWork` is the production implementation.
- **Service Layer with Command/Event Handlers**: `handlers.py` contains pure functions (`add_batch`, `allocate`, `change_batch_quantity`, etc.) that process commands and react to events. Commands and events are simple dataclasses.
- **Message Bus**: A `MessageBus` class dispatches `Command` and `Event` messages to registered handlers. Events emitted by the domain during command handling are automatically collected and processed.
- **Dependency Injection via Bootstrap**: The `bootstrap()` function wires up all dependencies (UoW, notifications, publish) using Python's `inspect` module, injecting them into handlers by parameter name. No DI container framework required.
- **CQRS Read Model**: A denormalized `allocations_view` table is maintained by event handlers, and queries against it via `views.py` avoid loading full domain aggregates.
- **Redis Pub/Sub Integration**: External events are consumed from a Redis channel (`change_batch_quantity`) by a dedicated `redis_eventconsumer` entrypoint. Allocated events are published to the `line_allocated` channel.
- **Email Notifications**: An `AbstractNotifications` interface with an SMTP-based `EmailNotifications` implementation sends out-of-stock alerts.
- **Classical SQLAlchemy ORM Mapping**: Domain classes are mapped to database tables using SQLAlchemy's classical mapper (`mapper()`) rather than declarative base, keeping domain objects free of framework imports.

## Primary Use Cases and Target Audience

This codebase is primarily an **educational reference** for Python developers and architects who want to:

- Learn DDD patterns (Aggregates, Domain Events, Commands) in Python
- Understand how to structure a Flask/SQLAlchemy application with clean architecture
- See how to implement the Repository and Unit of Work patterns
- Understand event-driven architecture using Redis pub/sub in Python
- Learn how to write highly testable code with dependency injection and abstract base classes
- Study CQRS with a separate read model alongside a write model

The secondary use case is as a **working reference implementation** of a stock allocation system — a domain used consistently throughout the book to demonstrate each pattern in context.

## High-Level Architecture Overview

The application follows a layered, ports-and-adapters (hexagonal) architecture:

```
┌─────────────────────────────────────────────────────┐
│  Entrypoints (Flask HTTP API, Redis Consumer)        │
├─────────────────────────────────────────────────────┤
│  Service Layer (MessageBus, Handlers, Commands)      │
├─────────────────────────────────────────────────────┤
│  Domain Layer (Model, Events, Commands)              │
├─────────────────────────────────────────────────────┤
│  Adapters (ORM, Repository, Notifications, Redis)    │
└─────────────────────────────────────────────────────┘
```

- **Entrypoints** (`flask_app.py`, `redis_eventconsumer.py`) receive external input, convert it to Command objects, and dispatch via `MessageBus.handle()`.
- **Service Layer** (`handlers.py`, `messagebus.py`, `unit_of_work.py`) orchestrates use cases. Handlers receive commands/events plus injected dependencies.
- **Domain Layer** (`model.py`, `events.py`, `commands.py`) contains pure business logic. Aggregates (`Product`) raise domain events appended to `self.events`.
- **Adapters** (`orm.py`, `repository.py`, `notifications.py`, `redis_eventpublisher.py`) provide concrete implementations of infrastructure concerns.
- **Bootstrap** (`bootstrap.py`) is the composition root: it wires everything together for production or test use.

## Related Projects and Dependencies

- **Book**: *Architecture Patterns with Python* by Harry Percival and Bob Gregory (O'Reilly) — the book for which this code is the companion example
- **Flask**: HTTP web framework for the REST API entrypoint
- **SQLAlchemy (<2)**: ORM and SQL toolkit; classical mapper style is used
- **psycopg2-binary**: PostgreSQL driver
- **Redis**: Message broker for pub/sub between services
- **pytest**: Test runner with unit, integration, and e2e test suites
- **tenacity**: Retry library used in test fixtures to wait for services to come up
- **mypy**: Static type checking
- **mailhog**: SMTP mock server used in development/testing for email notifications
- **Docker / docker-compose**: Container orchestration for the full stack (postgres, redis, mailhog, api, redis_pubsub)
