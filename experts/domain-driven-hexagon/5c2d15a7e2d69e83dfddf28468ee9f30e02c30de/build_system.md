# Domain-Driven Hexagon — Build System

## Build System Type and Configuration Files

The project uses the **NestJS CLI** as its build system, backed by TypeScript compiler (`tsc`) and configured by NestJS-specific wrappers. The following configuration files govern the build:

| File | Purpose |
|------|---------|
| `package.json` | NPM scripts, dependencies, inline Jest config |
| `tsconfig.json` | Base TypeScript configuration with path aliases |
| `tsconfig.build.json` | Extends `tsconfig.json`; excludes `node_modules`, `tests`, specs |
| `nest-cli.json` | NestJS CLI configuration (entrypoint, compiler settings) |
| `.jestrc.json` | Jest configuration for unit tests |
| `jest-e2e.json` | Jest configuration for end-to-end integration tests |
| `.eslintrc.js` | ESLint rules (TypeScript-aware, Prettier integration) |
| `.prettierrc` | Code formatting configuration |
| `.dependency-cruiser.js` | Architecture boundary enforcement rules |
| `.env.example` | Template for environment variables |
| `.env.test` | Test environment variables |

### TypeScript Path Aliases (`tsconfig.json`)

The `tsconfig.json` defines module path aliases that allow clean imports throughout the codebase:

```json
"paths": {
  "@libs/*":    ["src/libs/*"],
  "@modules/*": ["src/modules/*"],
  "@src/*":     ["src/*"],
  "@config/*":  ["src/configs/*"],
  "@tests/*":   ["tests/*"]
}
```

These are resolved at runtime for `ts-node` via `tsconfig-paths`, and at compile time via `tsc`.

## External Dependencies and Management

Dependencies are managed via **NPM** (Node.js 20.1.0 per Volta pinning in `package.json`).

### Core Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `@nestjs/common`, `@nestjs/core` | ^9.0.0 | NestJS framework core |
| `@nestjs/cqrs` | ^9.0.1 | CQRS (CommandBus, QueryBus, EventBus) |
| `@nestjs/event-emitter` | ^1.3.1 | Domain event publication via EventEmitter2 |
| `@nestjs/graphql` + `@nestjs/apollo` | ^10.x | GraphQL interface with Apollo driver |
| `@nestjs/microservices` | ^9.1.2 | Microservice message controllers |
| `@nestjs/platform-express` | ^9.0.0 | HTTP adapter |
| `@nestjs/swagger` | ^6.1.2 | OpenAPI/Swagger documentation |
| `slonik` | ^31.2.4 | Type-safe PostgreSQL client |
| `nestjs-slonik` | ^9.0.0 | NestJS Slonik integration |
| `@slonik/migrator` | ^0.11.3 | Database migration runner |
| `zod` | ^3.21.4 | Runtime schema validation (database rows) |
| `oxide.ts` | ^1.0.5 | Result/Option types (Rust-inspired) |
| `class-validator` | ^0.13.2 | DTO validation decorators |
| `class-transformer` | ^0.5.1 | Object transformation (used with class-validator) |
| `nestjs-console` | ^8.0.0 | CLI controller support |
| `nestjs-request-context` | ^2.1.0 | AsyncLocalStorage-based request context |
| `nanoid` | ^3.3.4 | Short ID generation |
| `uuid` | ^9.0.0 | UUID v4 generation |
| `dotenv` + `env-var` | ^16.0.2, ^7.3.0 | Environment variable loading and typed access |
| `jest-cucumber` | ^3.0.1 | Gherkin BDD feature file test runner |
| `reflect-metadata` + `rxjs` | ^0.1.13, ^7.2.0 | NestJS decorators + reactive streams |

### Dev-Only Dependencies

| Package | Purpose |
|---------|---------|
| `@nestjs/cli` + `@nestjs/schematics` | NestJS build toolchain |
| `@nestjs/testing` | NestJS test utilities |
| `typescript` | ^4.7.4 |
| `ts-jest`, `ts-node` | TypeScript test runner and direct execution |
| `tsconfig-paths` | Resolves TypeScript path aliases at runtime |
| `jest` | 28.1.3 — test runner |
| `supertest` | HTTP integration test assertions |
| `dependency-cruiser` | Architecture dependency rule enforcement |
| `eslint` + plugins | Linting with Prettier integration |

## Build Targets and Commands

All commands are defined in `package.json`'s `scripts` section:

### Application Lifecycle

```bash
# Development (watch mode with hot reload)
npm run start:dev

# Debug mode with watch
npm run start:debug

# Production build
npm run build        # Runs: rimraf dist && nest build

# Run production bundle
npm run start:prod   # Runs: node dist/main
```

### Testing

```bash
# Unit tests (pattern: *.spec.ts in src/)
npm test             # jest --config .jestrc.json

# Unit tests in watch mode
npm run test:watch

# Unit tests with coverage
npm run test:cov

# End-to-end tests (pattern: *.e2e-spec.ts in tests/)
npm run test:e2e     # jest -i --config jest-e2e.json
```

The e2e tests run with `-i` (in-band/serial) because they share a real PostgreSQL database.

**Jest configuration** (`package.json`):
```json
{
  "rootDir": "src",
  "testRegex": ".*\\.spec\\.ts$",
  "testEnvironment": "node"
}
```

**E2E Jest configuration** (`jest-e2e.json`) targets `tests/` directory with `*.e2e-spec.ts` pattern.

### Code Quality

```bash
# Lint and auto-fix
npm run lint         # eslint "{src,apps,libs,tests}/**/*.ts" --fix

# Format with Prettier
npm run format       # prettier --write "src/**/*.ts" "tests/**/*.ts"

# Validate architectural dependency rules
npm run deps:validate   # depcruise src --config .dependency-cruiser.js

# Generate dependency graph SVG
npm run deps:graph      # depcruise src --output-type dot | dot -T svg > assets/dependency-graph.svg
```

### Database Operations

```bash
# Start PostgreSQL and pgAdmin via Docker
npm run docker:env      # docker-compose --file docker/docker-compose.yml up --build

# Run pending migrations (dev)
npm run migration:up

# Run pending migrations (test environment)
npm run migration:up:tests

# Rollback last migration
npm run migration:down

# Create a new migration
npm run migration:create -- --name my-migration

# Seed database
npm run seed:up
```

Database migration files are SQL files under `database/migrations/`, with down migrations in `database/migrations/down/`.

## How to Build, Test, and Deploy

### Local Development Setup

1. **Start the database**:
   ```bash
   npm run docker:env
   ```

2. **Configure environment** (copy `.env.example` to `.env` and fill values):
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_USER=user
   DB_PASSWORD=password
   DB_NAME=ddh
   ```

3. **Run migrations**:
   ```bash
   npm run migration:up
   ```

4. **Start development server** (port 3000):
   ```bash
   npm run start:dev
   ```

5. **Access Swagger UI**: `http://localhost:3000/docs`

### Running Tests

For e2e tests, the test database must be available and migrated:
```bash
npm run migration:up:tests
npm run test:e2e
```

The test suite uses `jestGlobalSetup.ts` and `jestSetupAfterEnv.ts` to manage a real database connection pool. Tables are truncated between tests (`afterEach`).

### Production Build

```bash
npm run build
# Produces: dist/ directory
npm run start:prod
```

NestJS CLI compiles TypeScript using the `tsconfig.build.json` (which excludes test files). The `prebuild` script runs `rimraf dist` to clean previous builds.

### Architecture Validation

The project uses `dependency-cruiser` to enforce that outer layers do not import from inner layers. Run:
```bash
npm run deps:validate
```

If any forbidden dependency is detected, the command exits with an error — useful as a CI gate.
