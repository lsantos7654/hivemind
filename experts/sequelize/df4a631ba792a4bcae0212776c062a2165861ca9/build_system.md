# Sequelize Build System

## Build System Type and Configuration Files

**ESBuild-Based Compilation**: Sequelize uses a custom build system based on ESBuild for fast TypeScript and JavaScript compilation. The build process is orchestrated by `build-packages.mjs`, a Node.js script that handles the complex compilation requirements of the monorepo structure.

**Monorepo Build Coordination**: The build system uses Lerna for coordinating builds across multiple packages, with each package having its own build configuration while sharing common compilation settings. The root `package.json` defines workspace-wide build scripts that can compile individual packages or the entire monorepo.

**TypeScript Configuration**: The build system relies on a hierarchical TypeScript configuration with `tsconfig-preset.json` providing shared compiler options and individual packages having their own `tsconfig.json` files that extend the preset. This ensures consistency across packages while allowing package-specific customizations.

### Primary Configuration Files

**build-packages.mjs**: The main build script that orchestrates compilation for individual packages. It uses ESBuild for JavaScript/TypeScript compilation and the TypeScript compiler for declaration file generation. Key features include:

- Fast compilation using ESBuild with source map generation
- Separate handling of `.mjs` files that are copied without compilation
- TypeScript declaration file generation using `tsc --emitDeclarationOnly`
- Dual module support generating both CommonJS and ESM declaration files
- Target specification for Node.js 18+ compatibility

**tsconfig-preset.json**: Shared TypeScript configuration providing:
```json
{
  "compilerOptions": {
    "target": "esnext",
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "strict": true,
    "declaration": true,
    "exactOptionalPropertyTypes": true,
    "stripInternal": true
  }
}
```

**lerna.json**: Monorepo configuration managing package versioning and coordinating cross-package builds:
```json
{
  "$schema": "node_modules/lerna/schemas/lerna-schema.json",
  "version": "7.0.0-alpha.48"
}
```

**nx.json**: Nx workspace configuration for build caching and dependency graph management, optimizing build performance across the monorepo.

## External Dependencies and Management

### Core Runtime Dependencies

**Utility Libraries**:
- `lodash` (^4.17.23) - Comprehensive utility functions for object manipulation, array operations, and functional programming patterns
- `debug` (^4.4.3) - Lightweight debugging utility with namespace support for logging
- `inflection` (^3.0.2) - String inflection library for pluralization, singularization, and case transformations
- `validator` (^13.15.26) - String validation and sanitization functions

**Database and Query Processing**:
- `sequelize-pool` (^8.0.1) - Connection pooling implementation optimized for database connections
- `retry-as-promised` (^7.1.1) - Promise-based retry logic with exponential backoff
- `bnf-parser` (^3.1.6) - BNF grammar parser for SQL parsing and analysis

**Type System and Validation**:
- `type-fest` (^4.41.0) - Advanced TypeScript utility types for enhanced type safety
- `uuid` (^11.1.0) - UUID generation for primary keys and unique identifiers
- `semver` (^7.7.4) - Semantic versioning utilities for dependency and compatibility checks

**Date and Time Handling**:
- `dayjs` (^1.11.20) - Lightweight date manipulation library with timezone support

**Utility and Infrastructure**:
- `toposort-class` (^1.0.1) - Topological sorting for dependency resolution
- `ansis` (^3.17.0) - ANSI color and styling for terminal output
- `fast-glob` (^3.3.3) - Fast file system globbing for file discovery

### Database Driver Dependencies

Each dialect package includes database-specific drivers:

**PostgreSQL**:
- `pg` (latest) - Native PostgreSQL client for Node.js
- `pg-native` (optional) - Native C++ bindings for enhanced performance

**MySQL/MariaDB**:
- `mysql2` (latest) - MySQL client with prepared statement support and connection pooling

**SQL Server**:
- `tedious` (latest) - TDS protocol implementation for SQL Server connectivity

**SQLite**:
- `sqlite3` (latest) - Native SQLite3 bindings with async support

**DB2**:
- `ibm_db` (latest) - IBM DB2 driver with native bindings

**Oracle**:
- `oracledb` (latest) - Oracle Database driver with connection pooling

**Snowflake**:
- `snowflake-sdk` (latest) - Snowflake Data Cloud connectivity

### Development Dependencies

**Build and Compilation Tools**:
- `esbuild` (0.27.4) - Fast JavaScript bundler and minifier used for compilation
- `typescript` (5.8.3) - TypeScript compiler for type checking and declaration generation
- `ts-node` (10.9.2) - TypeScript execution environment for development scripts

**Testing Framework**:
- `mocha` (11.7.5) - Test framework with comprehensive assertion and mocking support
- `chai` (4.5.0) - BDD/TDD assertion library with fluent interface
- `sinon` (18.0.1) - Standalone test spies, stubs, and mocks
- `nyc` (17.1.0) - Command line interface for Istanbul code coverage

**Code Quality Tools**:
- `eslint` (8.57.1) - JavaScript and TypeScript linting with extensive rule configuration
- `prettier` (3.5.3) - Code formatting with consistent style enforcement
- `husky` (9.1.7) - Git hooks for running quality checks before commits
- `lint-staged` (16.4.0) - Run linters on staged files in git

**Documentation**:
- `typedoc` (0.27.9) - TypeScript documentation generator
- `markdownlint-cli` (0.48.0) - Markdown linting for documentation consistency

## Build Targets and Commands

### Root Level Build Commands

**Package Compilation**:
```bash
# Build individual package
node build-packages.mjs <package-name>

# Build all packages using Lerna
lerna run build

# Generate TypeScript documentation
npm run docs
```

**Quality Assurance**:
```bash
# Format code using ESLint and Prettier
npm run format

# Run format validation
npm run test:format

# Test TypeScript types across packages
npm run test-typings

# Validate package exports
npm run test-exports
```

**Testing Commands**:
```bash
# Run unit tests across all packages
npm run test-unit

# Database-specific integration tests
npm run test-integration-postgres
npm run test-integration-mysql
npm run test-integration-sqlite3
# ... (similar commands for each database)
```

**Development Database Management**:
```bash
# Start database containers for development
npm run start-postgres-latest
npm run start-mysql-latest
# ... (commands for each database)

# Reset development databases
npm run reset-postgres
npm run reset-mysql
# ... (reset commands for each database)

# Stop all database containers
npm run stop-all
```

### Package-Specific Build Targets

**Core Package** (`packages/core`):
```bash
# Compile TypeScript to JavaScript with declarations
yarn build

# Run comprehensive test suite
yarn test

# Type checking without emission
yarn test-typings

# Unit tests for specific database dialect
yarn test-unit-postgres
yarn test-unit-mysql
# ... (dialect-specific unit tests)

# Integration tests for specific database
yarn test-integration-postgres
yarn test-integration-mysql
# ... (dialect-specific integration tests)

# Generate code coverage reports
yarn cover
```

**CLI Package** (`packages/cli`):
```bash
# Build CLI with oclif manifest generation
yarn build

# Generate oclif manifest and README
yarn prepack

# Test CLI commands
yarn test-unit
```

## How to Build, Test, and Deploy

### Initial Setup

1. **Environment Preparation**:
   ```bash
   # Ensure Node.js 18.20.8+ is installed
   node --version

   # Install dependencies using Yarn
   yarn install

   # Prepare Git hooks
   npm run prepare
   ```

2. **Database Setup** (for testing):
   ```bash
   # Start development databases
   npm run start-latest

   # Reset databases to clean state
   npm run reset-all
   ```

### Build Process

1. **Full Monorepo Build**:
   ```bash
   # Build all packages in dependency order
   lerna run build

   # Alternative: build specific package
   node build-packages.mjs core
   ```

2. **Development Build Process**:
   The build process follows these steps:
   - Clean previous build artifacts (`lib/` directories)
   - Compile TypeScript/JavaScript files using ESBuild
   - Generate TypeScript declaration files using `tsc`
   - Copy non-compiled files (`.mjs`, `.d.ts`)
   - Create dual module declarations (`.d.ts` and `.d.mts`)

### Testing Strategy

1. **Unit Testing**:
   ```bash
   # Test individual components in isolation
   npm run test-unit

   # Test specific database dialect
   yarn test-unit-postgres
   ```

2. **Integration Testing**:
   ```bash
   # Test complete ORM functionality
   npm run test-integration-postgres

   # Test across all supported databases
   lerna run test-integration
   ```

3. **Type Safety Validation**:
   ```bash
   # Validate TypeScript types
   npm run test-typings

   # Check export integrity
   npm run test-exports
   ```

### Deployment and Publishing

1. **Pre-release Validation**:
   ```bash
   # Comprehensive format checking
   npm run test:format

   # Full test suite across all databases
   lerna run test

   # Documentation generation
   npm run docs
   ```

2. **Publishing Process**:
   ```bash
   # Automated publishing with Lerna
   npm run publish-all

   # Manual package publishing
   lerna publish --conventional-commits
   ```

### Continuous Integration

The build system integrates with GitHub Actions for automated testing across multiple Node.js versions and database configurations. The CI pipeline includes:

- Lint and format validation
- TypeScript type checking
- Unit test execution across all packages
- Integration tests for each database dialect
- Documentation generation and validation
- Security vulnerability scanning
- Performance regression testing

The build system is designed for both development efficiency and production reliability, with comprehensive testing ensuring compatibility across Node.js versions and database systems while maintaining the high performance standards expected from a production ORM.
