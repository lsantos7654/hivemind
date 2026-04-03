# Sequelize Code Structure

## Complete Annotated Directory Tree

```
sequelize/
├── .editorconfig                 # Editor configuration for consistent formatting
├── .eslintrc.json               # ESLint configuration for code quality
├── .gitattributes               # Git attributes for line endings and file handling
├── .github/                     # GitHub-specific configuration
│   ├── ISSUE_TEMPLATE/          # Issue templates for bug reports and features
│   │   ├── bug_report.md
│   │   ├── docs_issue.md
│   │   ├── feature_request.md
│   │   └── other_issue.md
│   └── PULL_REQUEST_TEMPLATE.md # PR template for contributions
├── .gitignore                   # Git ignore patterns
├── .husky/                      # Git hooks for pre-commit validation
├── .markdownlint.json           # Markdown linting configuration
├── .mocharc.jsonc               # Mocha test runner configuration
├── .npmrc                       # NPM configuration
├── build.js                     # Custom build script using ESBuild
├── CONTACT.md                   # Contact information for maintainers
├── CONTRIBUTING.DOCS.md         # Documentation contribution guidelines
├── CONTRIBUTING.md              # General contribution guidelines
├── dev/                         # Development database containers
│   ├── db2/11.5/               # IBM DB2 development setup
│   ├── mariadb/10.3/           # MariaDB development setup
│   ├── mssql/2019/             # Microsoft SQL Server setup
│   ├── mysql/                  # MySQL development setups
│   │   ├── 5.7/
│   │   └── 8.0/
│   ├── oracle/                 # Oracle database setups
│   │   ├── 18-slim/
│   │   └── 21-slim/
│   └── postgres/10/            # PostgreSQL development setup
├── docs/                        # Documentation generation
│   ├── css/                    # Documentation styling
│   ├── esdoc-config.js         # ESDoc configuration for API docs
│   ├── favicon.ico             # Documentation favicon
│   ├── images/                 # Documentation images
│   ├── index.md                # Documentation index
│   ├── manual-groups.json      # Manual organization of docs
│   ├── redirects.json          # URL redirects for docs
│   ├── redirects/              # Redirect handling
│   ├── ROUTER.txt              # Documentation routing
│   ├── run-docs-transforms.js  # Documentation transformation scripts
│   ├── scripts/                # Documentation build scripts
│   └── transforms/             # Documentation content transforms
├── docs.sh                      # Documentation build script
├── ENGINE.md                    # Database engine support matrix
├── esdoc-ts.js                  # ESDoc TypeScript configuration
├── index.js                     # Main entry point (delegates to src/index.js)
├── LICENSE                      # MIT license
├── logo.svg                     # Sequelize logo
├── package-support.json         # Package support configuration
├── package.json                 # Package configuration and dependencies
├── README.md                    # Project overview and getting started
├── SECURITY.md                  # Security policy and vulnerability reporting
├── src/                         # Source code (TypeScript/JavaScript)
│   ├── associations/            # Relationship management system
│   │   ├── base.d.ts           # Base association type definitions
│   │   ├── base.js             # Abstract association class
│   │   ├── belongs-to-many.d.ts # Many-to-many association types
│   │   ├── belongs-to-many.js  # Many-to-many association implementation
│   │   ├── belongs-to.d.ts     # Many-to-one association types
│   │   ├── belongs-to.js       # Many-to-one association implementation
│   │   ├── has-many.d.ts       # One-to-many association types
│   │   ├── has-many.js         # One-to-many association implementation
│   │   ├── has-one.d.ts        # One-to-one association types
│   │   ├── has-one.js          # One-to-one association implementation
│   │   ├── helpers.js          # Association utility functions
│   │   ├── index.d.ts          # Association module types
│   │   ├── index.js            # Association module exports
│   │   └── mixin.js            # Association methods mixed into Model class
│   ├── data-types.d.ts         # Data type type definitions
│   ├── data-types.js           # Database data type implementations
│   ├── deferrable.d.ts         # Deferrable constraint type definitions
│   ├── deferrable.js           # Deferrable constraint implementation
│   ├── dialects/               # Database-specific implementations
│   │   ├── abstract/           # Abstract base classes for all dialects
│   │   │   ├── connection-manager.js    # Base connection management
│   │   │   ├── data-types.js           # Base data type mappings
│   │   │   ├── query-generator.js      # Base SQL generation
│   │   │   └── query-interface.js      # Base query interface
│   │   ├── db2/                # IBM DB2 dialect implementation
│   │   ├── mariadb/            # MariaDB dialect implementation
│   │   ├── mssql/              # Microsoft SQL Server dialect
│   │   ├── mysql/              # MySQL dialect implementation
│   │   ├── oracle/             # Oracle database dialect (experimental)
│   │   ├── parserStore.js      # SQL parser store for caching
│   │   ├── postgres/           # PostgreSQL dialect implementation
│   │   ├── snowflake/          # Snowflake dialect implementation
│   │   └── sqlite/             # SQLite dialect implementation
│   ├── errors/                 # Error classes and hierarchy
│   │   ├── base/               # Base error classes
│   │   ├── connection/         # Connection-related errors
│   │   ├── database/           # Database-specific errors
│   │   ├── index.d.ts          # Error type definitions
│   │   ├── index.js            # Error module exports
│   │   ├── instance/           # Instance validation errors
│   │   ├── query/              # Query execution errors
│   │   └── validation/         # Data validation errors
│   ├── generic/                # Generic utility modules
│   ├── hooks.d.ts              # Hook system type definitions
│   ├── hooks.js                # Hook system implementation
│   ├── index-hints.d.ts        # Database index hint type definitions
│   ├── index-hints.js          # Database index hint implementation
│   ├── index.d.ts              # Main module type definitions
│   ├── index.js                # Main module entry point
│   ├── index.mjs               # ESM module entry point
│   ├── instance-validator.d.ts # Instance validation type definitions
│   ├── instance-validator.js   # Instance validation implementation
│   ├── model-manager.d.ts      # Model registry type definitions
│   ├── model-manager.js        # Model registry and factory
│   ├── model.d.ts              # Model class type definitions
│   ├── model.js                # Core Model class implementation
│   ├── operators.ts            # Query operator definitions
│   ├── query-types.d.ts        # Query type enumeration definitions
│   ├── query-types.js          # Query type enumeration implementation
│   ├── query.d.ts              # Query class type definitions
│   ├── sequelize.d.ts          # Main Sequelize class type definitions
│   ├── sequelize.js            # Main Sequelize class implementation
│   ├── sql-string.d.ts         # SQL string utilities type definitions
│   ├── sql-string.js           # SQL string utilities implementation
│   ├── table-hints.d.ts        # Database table hint type definitions
│   ├── table-hints.js          # Database table hint implementation
│   ├── transaction.d.ts        # Transaction type definitions
│   ├── transaction.js          # Transaction implementation
│   ├── utils.d.ts              # Utility functions type definitions
│   ├── utils.js                # Utility functions implementation
│   └── utils/                  # Utility modules
│       ├── class-to-invokable.js    # Class method invocation utilities
│       ├── deprecations.js          # Deprecation warning system
│       ├── join-sql-fragments.js    # SQL fragment joining utilities
│       ├── logger.js                # Logging utilities
│       ├── sql.js                   # SQL manipulation utilities
│       └── validator-extras.js      # Extended validation utilities
├── sscce.js                     # Short Self-Contained Correct Example template
├── test/                        # Test suite
│   ├── .eslintrc.json          # Test-specific ESLint configuration
│   ├── config/                 # Test database configurations
│   ├── integration/            # Integration test suite
│   │   ├── associations/       # Association functionality tests
│   │   ├── data-types/         # Data type tests
│   │   ├── dialects/           # Database dialect tests
│   │   ├── hooks/              # Hook system tests
│   │   ├── model/              # Model functionality tests
│   │   ├── query-interface/    # Query interface tests
│   │   ├── sequelize/          # Main class tests
│   │   └── ... (many more)     # Additional integration test categories
│   ├── registerEsbuild.js      # ESBuild registration for testing
│   ├── support.js              # Test support utilities
│   ├── teaser.js               # Quick validation test
│   ├── tmp/                    # Temporary test files
│   ├── tsconfig.json           # TypeScript configuration for tests
│   ├── types/                  # TypeScript type tests
│   └── unit/                   # Unit test suite
│       ├── data-types/         # Data type unit tests
│       ├── dialects/           # Dialect unit tests
│       ├── model/              # Model unit tests
│       ├── sequelize/          # Main class unit tests
│       └── ... (many more)     # Additional unit test categories
├── tsconfig.json               # TypeScript configuration
└── yarn.lock                   # Yarn dependency lockfile
```

## Module and Package Organization

### Core Module Structure
The Sequelize codebase follows a modular architecture with clear separation of concerns:

**Primary Modules:**
- `src/sequelize.js` - Main Sequelize class providing database connection management
- `src/model.js` - Base Model class with ORM functionality and lifecycle management
- `src/model-manager.js` - Model registry and factory for instance management
- `src/transaction.js` - Transaction management with ACID support
- `src/data-types.js` - Database-agnostic data type system

**Supporting Modules:**
- `src/hooks.js` - Extensible lifecycle event system
- `src/utils.js` - Core utility functions and helpers
- `src/operators.ts` - Query operator definitions and symbols
- `src/query-types.js` - Query type enumerations
- `src/sql-string.js` - SQL string manipulation and escaping

### Association System
The association system (`src/associations/`) implements all SQL relationship patterns:
- `base.js` - Abstract association class with common functionality
- `belongs-to.js` - Many-to-one relationships
- `has-one.js` - One-to-one relationships
- `has-many.js` - One-to-many relationships
- `belongs-to-many.js` - Many-to-many relationships with junction tables
- `mixin.js` - Association methods mixed into Model prototype

### Dialect Architecture
Database-specific implementations are organized under `src/dialects/`:
- `abstract/` - Base classes with common database functionality
- Individual dialect folders (postgres/, mysql/, sqlite/, etc.) containing:
  - Connection management
  - SQL query generation
  - Data type mappings
  - Database-specific optimizations

### Error Hierarchy
Comprehensive error system in `src/errors/`:
- `base/` - Base error classes
- `connection/` - Connection and network errors
- `database/` - Database-specific errors
- `validation/` - Data validation errors
- `instance/` - Model instance errors
- `query/` - Query execution errors

## Main Source Directories and Their Purposes

### `/src/` - Core Implementation
Contains all production source code written in JavaScript with TypeScript definitions.

**Key Characteristics:**
- Dual file system: `.js` implementation files with corresponding `.d.ts` type definitions
- Modern JavaScript (ES2018+) with CommonJS modules
- Extensive JSDoc documentation for API generation
- Strict separation between public and internal APIs

### `/src/dialects/` - Database Abstraction Layer
Implements the adapter pattern for multi-database support.

**Architecture:**
- Abstract base classes define common interface
- Concrete implementations extend base classes with database-specific logic
- Query generation is completely database-specific
- Connection management handles database-specific connection pooling

### `/src/associations/` - Relationship Management
Implements object-relational mapping for SQL relationships.

**Features:**
- Association metadata management
- Lazy and eager loading strategies
- Cascading operations (save, delete)
- Junction table management for many-to-many relationships

### `/src/utils/` - Utility Layer
Provides common functionality used throughout the codebase.

**Components:**
- String manipulation and SQL escaping
- Data type conversion and validation
- Logging and debugging utilities
- Deprecation warning system
- Class method invocation helpers

### `/test/` - Comprehensive Test Suite
Extensive testing infrastructure covering all functionality.

**Organization:**
- `unit/` - Isolated unit tests for individual components
- `integration/` - End-to-end tests with real database connections
- `config/` - Test database configuration for all supported databases
- `types/` - TypeScript type checking tests

## Key Files and Their Roles

### Entry Points
- **`index.js`** - Main package entry point, delegates to `src/index.js`
- **`src/index.js`** - Exports the main Sequelize class
- **`src/index.mjs`** - ESM module entry point for modern JavaScript
- **`src/sequelize.js`** - Main Sequelize class implementation (1486 lines)

### Core Classes
- **`src/model.js`** - Base Model class (4754 lines) - The heart of the ORM
- **`src/model-manager.js`** - Model registry and lifecycle management
- **`src/transaction.js`** - ACID transaction implementation
- **`src/data-types.js`** - Database data type system (1082 lines)

### Configuration Files
- **`package.json`** - NPM package configuration with comprehensive script collection
- **`tsconfig.json`** - TypeScript compilation configuration
- **`build.js`** - Custom build system using ESBuild
- **`.mocharc.jsonc`** - Mocha test framework configuration

### Development Infrastructure
- **`sscce.js`** - Template for creating minimal reproduction cases
- **`docs.sh`** - Documentation generation script
- **`dev/`** - Docker containers for all supported databases

## Code Organization Patterns

### Separation of Interface and Implementation
Sequelize maintains strict separation between TypeScript type definitions and JavaScript implementations:
- `.d.ts` files contain comprehensive type information
- `.js` files contain runtime implementation
- This pattern allows for precise type checking while maintaining runtime flexibility

### Dialect Pattern Implementation
Database-specific functionality follows a consistent pattern:
```
dialects/
  abstract/
    ├── connection-manager.js    # Base connection handling
    ├── query-generator.js       # Base SQL generation
    ├── query-interface.js       # Base query interface
    └── data-types.js           # Base type mappings
  postgres/
    ├── connection-manager.js    # PostgreSQL-specific connections
    ├── query-generator.js       # PostgreSQL SQL generation
    ├── query-interface.js       # PostgreSQL query interface
    └── data-types.js           # PostgreSQL type mappings
```

### Mixin Pattern for Associations
Association functionality is mixed into the Model class rather than using inheritance:
- `associations/mixin.js` adds association methods to Model.prototype
- This allows models to gain association capabilities without complex inheritance hierarchies
- Association instances manage relationship metadata and operations

### Hook System Architecture
The hook system provides extension points throughout the ORM lifecycle:
- Hooks are defined as string constants in `hooks.js`
- Hook execution is managed through the `Hooks` class
- Both instance and model-level hooks are supported
- Hooks enable plugins and custom behavior injection

### Utility Module Organization
Utilities are organized by functionality:
- Core utilities in `utils.js`
- Specialized utilities in `utils/` subdirectory
- Each utility module has a single responsibility
- Utilities are imported selectively to minimize bundle size

This modular architecture enables Sequelize to support multiple databases while maintaining a consistent API and allowing for extensive customization and extension.
