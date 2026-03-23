# Sequelize Code Structure

## Complete Annotated Directory Tree

```
sequelize/
├── .editorconfig                    # Editor configuration for consistent formatting
├── .eslintrc.js                     # ESLint configuration for code quality
├── .gitattributes                   # Git attributes configuration
├── .github/                         # GitHub workflow and template files
│   ├── copilot-instructions.md      # Instructions for GitHub Copilot
│   ├── ISSUE_TEMPLATE/              # Issue templates for bug reports and features
│   └── workflows/                   # CI/CD pipeline configurations
├── .gitignore                       # Git ignore patterns
├── .husky/                          # Git hooks for pre-commit checks
├── .markdownlint.json               # Markdown linting configuration
├── .mocharc.jsonc                   # Mocha test configuration
├── .prettierignore                  # Files to exclude from Prettier
├── .prettierrc.json                 # Prettier code formatting configuration
├── .yarn/                           # Yarn package manager cache and config
├── .yarnrc.yml                      # Yarn configuration
├── AUTHORS                          # List of project contributors
├── build-packages.mjs               # ESBuild-based compilation script
├── CHANGELOG.md                     # Version history and release notes
├── CODE-OF-CONDUCT.md               # Community guidelines
├── CONTACT.md                       # Contact information for maintainers
├── CONTRIBUTING.md                  # Contribution guidelines
├── CONTRIBUTING.DOCS.md             # Documentation contribution guidelines
├── dev/                             # Development utilities and database setup
│   ├── delete-changelog.mjs         # Changelog management script
│   ├── sync-exports.mjs             # Export synchronization utility
│   └── [database]/                  # Database-specific dev environments
│       ├── oldest/                  # Oldest supported version configs
│       └── latest/                  # Latest version configs
├── lerna.json                       # Lerna monorepo configuration
├── LICENSE                          # MIT license
├── logo.svg                         # Sequelize logo
├── nx.json                          # Nx workspace configuration
├── package-support.json             # Package support configuration
├── package.json                     # Root package configuration and scripts
├── packages/                        # Core monorepo packages
│   ├── cli/                         # Command-line interface package
│   ├── core/                        # Main Sequelize ORM functionality
│   ├── db2/                         # DB2 database dialect
│   ├── ibmi/                        # IBM i database dialect
│   ├── mariadb/                     # MariaDB database dialect
│   ├── mssql/                       # Microsoft SQL Server dialect
│   ├── mysql/                       # MySQL database dialect
│   ├── oracle/                      # Oracle database dialect
│   ├── postgres/                    # PostgreSQL database dialect
│   ├── snowflake/                   # Snowflake database dialect
│   ├── sqlite3/                     # SQLite3 database dialect
│   ├── utils/                       # Shared utility functions
│   └── validator-js/                # JavaScript validation library
├── README.md                        # Project overview and getting started
├── renovate.json                    # Renovate dependency updates config
├── SECURITY.md                      # Security policy and reporting
├── sscce.ts                         # Short Self-Contained Correct Example template
├── test/                            # Root-level test configuration
│   ├── esm-named-exports.test.js    # ESM export validation tests
│   └── register-esbuild.js          # ESBuild registration for tests
├── tsconfig-preset.json             # Shared TypeScript configuration
├── tsconfig.json                    # Root TypeScript configuration
├── typedoc.base.json                # TypeDoc documentation base config
├── typedoc.js                       # TypeDoc documentation generation
└── yarn.lock                        # Yarn lockfile for dependency versions
```

## Module and Package Organization

**Monorepo Architecture**: Sequelize follows a monorepo pattern managed by Lerna, with each package serving a specific purpose in the ORM ecosystem. The `packages/` directory contains all publishable packages, each with independent versioning and dependency management while sharing common development tooling and configuration.

**Core Package Structure**: The `@sequelize/core` package contains the primary ORM functionality and serves as the main entry point. It provides the foundational classes, interfaces, and utilities that other packages build upon, including the abstract dialect system, model definitions, query builders, and transaction management.

**Database Dialect Packages**: Each supported database has its own package (`@sequelize/postgres`, `@sequelize/mysql`, etc.) that implements the abstract interfaces defined in core. These packages contain database-specific query generators, connection managers, data type mappings, and optimization strategies tailored to each database's unique features and SQL dialect.

**Utility and Support Packages**: Supporting packages include `@sequelize/utils` for shared utility functions, `@sequelize/validator-js` for validation capabilities, and `@sequelize/cli` for command-line tools. These packages are designed to be reusable across the ecosystem and provide common functionality needed by multiple dialect packages.

## Main Source Directories and Their Purposes

### packages/core/src/ - Primary ORM Implementation

**Core Architecture Components**:
- `sequelize.js` - Main Sequelize class and entry point, orchestrates all ORM functionality
- `model.js` - Model class definition with CRUD operations, validations, and associations
- `transaction.js` - Transaction management with isolation levels and nested transactions
- `sequelize-typescript.ts` - TypeScript-specific implementations and type definitions

**Abstract Dialect System** (`abstract-dialect/`):
- `dialect.ts` - Base dialect class defining common database interface
- `query-generator.js` - Abstract query generation with SQL building logic
- `query-interface.js` - Database schema manipulation and DDL operations
- `connection-manager.ts` - Connection pooling and database connection management
- `query.ts` - Query execution and result processing
- `data-types.ts` - Abstract data type definitions and validation

**Data Types and Validation** (`data-types.ts`, `instance-validator.js`):
- Comprehensive data type system supporting all SQL types
- Custom validation rules and constraint checking
- Type conversion and serialization logic
- Database-specific type mapping and optimization

**Associations** (`associations/`):
- `base.ts` - Abstract association class with common functionality
- `belongs-to.ts` - One-to-one and many-to-one relationship implementation
- `has-one.ts` - One-to-one relationship from the other side
- `has-many.ts` - One-to-many relationship implementation
- `belongs-to-many.ts` - Many-to-many relationship with junction tables

**Expression Builders** (`expression-builders/`):
- SQL expression construction with type safety
- Function calls, literals, column references, and complex expressions
- WHERE clause building with operator support
- JSON path expressions and advanced SQL features

**Utilities** (`utils/`):
- String manipulation and inflection utilities
- Object handling and deep merging functions
- SQL query utilities and parameter binding
- Model utilities and relationship helpers
- Logging and debugging support

### packages/cli/src/ - Command Line Interface

**Command Structure**:
- `commands/` - Individual CLI commands for migrations, seeding, and model generation
- `utils/` - CLI-specific utilities for file handling and user interaction
- `templates/` - Code generation templates for models, migrations, and seeders
- Configuration loading and project structure detection

### Database Dialect Packages

Each dialect package follows a consistent structure:

**Core Implementation Files**:
- `dialect.js` - Dialect-specific configuration and feature flags
- `query-generator.js` - SQL generation tailored to database syntax
- `query-interface.js` - DDL operations and schema management
- `query.js` - Query execution with database-specific optimizations
- `connection-manager.js` - Connection handling and pooling logic

**Data Type Mappings**:
- `data-types.js` - Database-specific type definitions and conversions
- Type validation and serialization logic
- Custom type extensions and database-specific features

## Key Files and Their Roles

### Configuration and Build Files

**package.json** (root): Defines workspace configuration, development scripts, and coordinates monorepo-wide operations. Contains scripts for testing across all database dialects, formatting, and building packages.

**build-packages.mjs**: Custom build script using ESBuild for compiling TypeScript and JavaScript files across packages. Handles both CommonJS and ESM builds, generates declaration files, and manages the compilation pipeline for the entire monorepo.

**lerna.json**: Lerna configuration managing monorepo versioning, publishing, and cross-package dependencies. Coordinates releases and ensures consistent versioning across all packages.

**tsconfig-preset.json**: Shared TypeScript configuration providing consistent compiler options across all packages. Defines strict type checking, module resolution, and output configurations.

### Core Entry Points

**packages/core/src/index.js**: Main CommonJS entry point that exports the Sequelize constructor for backward compatibility. Handles both named and default import patterns.

**packages/core/src/index.d.ts**: Primary TypeScript type definitions and export declarations. Defines the complete public API surface and type relationships for the entire ORM.

**packages/core/src/sequelize.js**: The main Sequelize class implementation that orchestrates all ORM functionality including model registration, connection management, transaction handling, and query execution.

### Model and Data Layer

**packages/core/src/model.js**: Comprehensive Model class implementation providing the primary interface for database entities. Includes CRUD operations, validation logic, association management, hooks, and query building.

**packages/core/src/abstract-dialect/**: Foundation of the multi-database support system containing abstract implementations that each database dialect extends and customizes.

### Testing Infrastructure

**test/register-esbuild.js**: Test registration script that configures ESBuild for on-the-fly TypeScript compilation during test execution.

**packages/core/test/**: Comprehensive test suites including unit tests for individual components, integration tests across database dialects, and performance benchmarks.

## Code Organization Patterns

**Abstract Base Classes**: The codebase extensively uses abstract base classes to define common interfaces while allowing database-specific implementations. This pattern is evident in the dialect system, query generators, and data types.

**Mixin Pattern**: Many components use mixins to compose functionality, particularly in the model system where behaviors can be mixed in without requiring deep inheritance hierarchies.

**Factory Pattern**: Object creation throughout the system uses factory patterns, particularly for creating database connections, query objects, and model instances.

**Strategy Pattern**: Database-specific behaviors are implemented using the strategy pattern, allowing the same high-level API to work across different databases with completely different underlying implementations.

**Composition over Inheritance**: The architecture favors composition, particularly in the model definition system where attributes, associations, and behaviors are composed rather than inherited.

**Module Federation**: The monorepo structure allows for clear separation of concerns while maintaining tight integration between packages. Each package can be developed and tested independently while contributing to the cohesive whole.

The code organization reflects years of evolution and refinement, balancing backward compatibility with modern JavaScript patterns, and providing both simplicity for basic use cases and sophistication for complex enterprise requirements.