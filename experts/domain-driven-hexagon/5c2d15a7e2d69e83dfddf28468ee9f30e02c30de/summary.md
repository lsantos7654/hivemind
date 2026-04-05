# Domain-Driven Hexagon — Summary

## Repository Purpose and Goals

Domain-Driven Hexagon (github.com/Sairyss/domain-driven-hexagon) is a reference implementation and comprehensive guide demonstrating how to combine multiple architectural patterns into a cohesive, production-grade application architecture. The repository's stated emphasis is to provide **recommendations** for designing software applications — not prescriptive rules.

The project fuses:
- **Domain-Driven Design (DDD)** — entities, aggregates, value objects, domain events, bounded contexts
- **Hexagonal Architecture (Ports and Adapters)** — infrastructure isolation via ports/interfaces
- **Clean / Onion Architecture** — layered dependency direction pointing inward
- **CQRS (Command Query Responsibility Segregation)** — separate read/write models
- **Secure by Design** — domain invariants enforced at the type/object level
- **SOLID Principles** — single responsibility, open/closed, dependency inversion throughout

The codebase is not a library or framework — it is a **working NestJS application** (version 2.0.0) demonstrating these patterns with TypeScript, primarily serving as a learning resource and architectural blueprint.

## Key Features and Capabilities

1. **Complete DDD building blocks** — abstract base classes for `Entity`, `AggregateRoot`, `ValueObject`, `DomainEvent`, `Command`, and `Query` are provided as reusable lib classes in `src/libs/ddd/`.
2. **Repository pattern with Slonik** — type-safe PostgreSQL queries using the Slonik SQL library, with runtime Zod schema validation of database results.
3. **CQRS via NestJS CQRS module** — commands are handled by command handlers (`@CommandHandler`), queries by query handlers (`@QueryHandler`).
4. **Multi-interface support** — a single use case can be exposed simultaneously through HTTP controllers, GraphQL resolvers, CLI commands, and microservice message controllers.
5. **Domain Event system** — aggregates accumulate domain events, published atomically after persistence via `EventEmitter2`.
6. **Cross-module communication via events** — modules communicate by emitting/subscribing to domain events instead of direct imports (e.g., `CreateWalletWhenUserIsCreatedDomainEventHandler`).
7. **Result type pattern** — uses `oxide.ts` (Rust-inspired `Result<Ok, Err>`) throughout the application layer instead of throwing exceptions for business errors.
8. **Mapper pattern** — explicit `toPersistence`, `toDomain`, `toResponse` mappings prevent data leakage between layers.
9. **Request-scoped context** — `AppRequestContext` and `RequestContextService` propagate correlation IDs and database transaction connections within a request lifecycle.
10. **Dependency graph validation** — `dependency-cruiser` is configured to enforce architectural boundaries at build time.
11. **BDD-style e2e tests** — Gherkin feature files executed via `jest-cucumber` and Supertest.

## Primary Use Cases and Target Audience

**Target audience**: Mid-to-senior software engineers, architects, and teams building enterprise-grade Node.js backends who want a canonical reference for DDD + Hexagonal architecture.

**Primary use cases**:
- Learning DDD, Hexagonal Architecture, and CQRS patterns with a working TypeScript/NestJS example
- Using as a starter template for complex domain-rich applications
- Reference for specific techniques: value object validation, domain event publication, CQRS query/command separation, layered exception handling
- Understanding how to structure feature modules with vertical slices
- Learning how to expose the same use case via multiple transport protocols

## High-Level Architecture Overview

The architecture is organized in concentric layers, each with a strict dependency direction (outer layers depend on inner ones, never the reverse):

```
[ Interface Adapters (Controllers, Resolvers, CLI, Message) ]
                       ↓
         [ Application Layer (Services, Commands, Queries, Ports) ]
                       ↓
                [ Domain Layer (Entities, Aggregates, Value Objects, Domain Events) ]
                       ↑
[ Infrastructure Layer (Repositories, DB Adapters) ] ← implements ports
```

Code is organized **by module** (bounded contexts): `user` and `wallet`. Each module contains its own domain, application commands/queries, database adapters, and DTOs. Modules communicate exclusively through domain events, enforcing loose coupling.

The data flow for a typical command:
1. HTTP request → `CreateUserHttpController` parses DTO → creates `CreateUserCommand`
2. CommandBus dispatches command → `CreateUserService` (application layer)
3. Service creates `UserEntity` aggregate (domain layer), which emits `UserCreatedDomainEvent`
4. Service persists entity via `UserRepositoryPort` (port/interface)
5. `UserRepository` (infrastructure) maps entity to `UserModel` via `UserMapper` and executes Slonik SQL query
6. After persistence, domain events are published via `EventEmitter2`
7. `CreateWalletWhenUserIsCreatedDomainEventHandler` in the `wallet` module responds

## Related Projects and Dependencies

**Runtime dependencies of note**:
- `@nestjs/cqrs` — CQRS pattern implementation (CommandBus, QueryBus)
- `@nestjs/event-emitter` — domain event publication
- `@nestjs/graphql` + `@nestjs/apollo` — GraphQL interface
- `@nestjs/microservices` — message-based controller support
- `slonik` + `nestjs-slonik` — type-safe PostgreSQL client
- `zod` — runtime schema validation for database rows
- `oxide.ts` — Result/Option types (Rust-inspired)
- `nestjs-console` — CLI controller support
- `class-validator` + `class-transformer` — DTO validation
- `nestjs-request-context` — request-scoped AsyncLocalStorage context

**Related repositories by the same author**:
- `Sairyss/backend-best-practices` — backend development best practices guide
- `Sairyss/system-design-patterns` — distributed systems and scalability topics
- `Sairyss/fullstack-starter-template` — full-stack template (TypeScript, React, Vite, tRPC, Fastify, Prisma, Zod)
