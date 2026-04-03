# node.js-clean-architecture — Summary

## Repository Purpose and Goals

`node.js-clean-architecture` is a reference implementation of Robert C. Martin's Clean Architecture principles applied to a Node.js REST API. The primary goal is to demonstrate how to separate concerns across distinct, dependency-directed layers so that business logic remains completely independent of infrastructure details (frameworks, databases, caching layers). The application is intentionally simple — a CRUD blog post API with JWT-authenticated users — so the architectural patterns can be studied without domain complexity obscuring the structural choices.

The project shows that by following the Dependency Rule (inner circles never import outer circles), the database, web framework, and caching layer can all be replaced without touching the use cases or entities.

## Key Features and Capabilities

- **RESTful API** for managing blog posts (create, read, update, delete) and users (register, find), plus a login endpoint that issues JWTs.
- **Clean Architecture layering**: four concentric layers (Entities → Use Cases → Interface Adapters → Frameworks & Drivers), each only depending inward.
- **JWT authentication**: all post and user read endpoints require a Bearer token; the auth middleware decodes and attaches the user to the request.
- **Redis response caching**: GET requests for posts check Redis before hitting MongoDB; results are cached with a 30-second TTL.
- **Graceful shutdown**: the `@godaddy/terminus` library provides health check (`/healthcheck`) and SIGINT-handled teardown with MongoDB disconnect.
- **Auto-reconnecting MongoDB**: connection module listens to `connected`, `reconnected`, `error`, and `disconnected` events and retries on failure.
- **Docker / Docker Compose**: multi-stage Dockerfile (builder + production) and a Compose file that wires MongoDB, Redis, and the API together in an isolated network.
- **PM2 process manager**: production start command runs the transpiled build with `pm2 start -i ${NODE_PROCESSES}` for cluster mode.
- **Babel transpilation**: ES module syntax (`import`/`export`) is transpiled with `@babel/preset-env` for Node.js compatibility.
- **Linting and formatting**: ESLint (Airbnb base config) + Prettier enforced via a Husky pre-commit hook.
- **Unit tests**: Mocha + Chai + Sinon for use case tests; Chai-HTTP + stubbed `request` calls for API-shape tests.

## Primary Use Cases and Target Audience

This repository is primarily a **learning resource and architectural template** for:

- Developers learning Clean Architecture who want a concrete, runnable Node.js example.
- Teams evaluating how to structure a new Node.js service so that business logic can be unit-tested without spinning up a database.
- Engineers looking for patterns to make their Express/MongoDB applications more maintainable and testable.
- Developers who want to understand how dependency injection is achieved without a DI container in plain JavaScript.

## High-Level Architecture Overview

The codebase is organized into four layers matching the Clean Architecture diagram:

1. **Entities** (`src/entities/`) — Plain factory functions (`post`, `user`) that encapsulate only business-invariant data via getter closures. No framework or library imports.

2. **Use Cases** (`application/use_cases/`) — Application-specific business rules. Each use case is a single exported function that accepts injected repository/service interfaces. Validates input, creates entities, delegates to repository. No knowledge of Express, MongoDB, or Redis.

3. **Interface Adapters** (`adapters/controllers/` + `application/repositories/` + `application/services/`) — Controllers translate HTTP request data into use-case calls and format responses. Repository interfaces (`postDbRepository`, `userDbRepository`, `postRedisRepository`) are thin wrappers that forward calls to whatever implementation is injected, acting as ports. Service interfaces (`authService`) similarly wrap the concrete auth implementation.

4. **Frameworks & Drivers** (`frameworks/`) — All infrastructure code: Express setup, route definitions, middlewares, MongoDB connection and Mongoose models, MongoDB repository implementations, Redis connection and Redis repository implementation, JWT/bcrypt auth service implementation.

Dependency injection is done manually at the route level: routes import both the interface and the concrete implementation, instantiate them, and pass them to controllers. Controllers instantiate repositories by calling `interface(implementation())`, which returns the interface-wrapped version.

## Related Projects and Dependencies

**Runtime dependencies:**
- `express` ^4.17.1 — HTTP web framework
- `mongoose` ^8.8.3 — MongoDB ODM
- `redis` ^3.0.2 — Redis client (v3 callback-based API)
- `jsonwebtoken` ^9.0.0 — JWT signing and verification
- `bcryptjs` ^2.4.3 — Password hashing
- `@godaddy/terminus` ^4.6.0 — Graceful shutdown and health checks
- `helmet` ^5.0.2 — HTTP security headers
- `compression` ^1.7.4 — gzip compression middleware
- `body-parser` ^1.19.0 — Request body parsing
- `morgan` ^1.10.0 — HTTP request logging
- `pm2` ^6.0.9 — Production process manager

**Dev dependencies:**
- `@babel/core`, `@babel/cli`, `@babel/node`, `@babel/preset-env`, `@babel/plugin-transform-runtime` — Babel toolchain for ES module transpilation
- `mocha` ^9.2.0, `chai` ^4.3.0, `sinon` ^9.2.4 — Test framework and mocking
- `chai-http` ^4.3.0, `request` ^2.88.2 — HTTP test utilities
- `faker` ^5.4.0 — Fake data generation for tests
- `eslint` ^8.8.0 with `eslint-config-airbnb-base` and `eslint-plugin-prettier` — Linting
- `prettier` ^2.2.1 — Code formatting
- `husky` ^4.3.8 — Git hooks for pre-commit lint enforcement
- `nodemon` ^2.0.7 — Auto-restart in development

**External documentation:** API documentation available at the Postman documenter link referenced in the README.
