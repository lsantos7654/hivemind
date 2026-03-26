# Sequelize Build System

## Build System Type and Configuration Files

### Primary Build System: Custom ESBuild Configuration
Sequelize uses a custom build system implemented in `build.js` that leverages ESBuild for high-performance JavaScript/TypeScript compilation. This system replaces traditional webpack or rollup configurations with a purpose-built solution optimized for the library's specific requirements.

**Key Configuration Files:**
- **`build.js`** - Main build script (110 lines) using ESBuild API
- **`tsconfig.json`** - TypeScript compilation configuration
- **`package.json`** - NPM scripts and build targets
- **`.mocharc.jsonc`** - Test runner configuration
- **`esdoc-config.js`** - API documentation generation

### TypeScript Configuration (`tsconfig.json`)
```json
{
  "compilerOptions": {
    "target": "esnext",
    "module": "commonjs",
    "moduleResolution": "node",
    "allowJs": true,
    "declaration": true,
    "emitDeclarationOnly": true,
    "outDir": "./types",
    "rootDir": "./src",
    "strict": true,
    "types": ["node"]
  },
  "include": ["./src/**/*.ts"]
}
```

**Configuration Purpose:**
- Generates TypeScript declaration files (`.d.ts`) in `/types` directory
- Enables strict type checking for development
- Supports both JavaScript and TypeScript source files
- Targets modern JavaScript (ESNext) with CommonJS modules

### Build Script Architecture (`build.js`)
The custom build script performs several key operations:

1. **File Discovery**: Uses `fast-glob` to find all source files matching `./src/**/*.{mjs,cjs,js,mts,cts,ts}`
2. **Output Directory Management**: Cleans `/lib` and `/types` directories for full rebuilds
3. **ESBuild Compilation**: Compiles JavaScript/TypeScript with optimized settings
4. **File Copying**: Copies additional assets and maintains directory structure
5. **TypeScript Declaration Generation**: Runs TypeScript compiler for type definitions

**ESBuild Configuration:**
- Platform: Node.js
- Target: ES2018+ for modern JavaScript compatibility
- Format: CommonJS for NPM compatibility
- Source maps: Generated for debugging
- Minification: Disabled for library distribution

## External Dependencies and Management

### Package Management: Yarn with Lock Files
Sequelize uses Yarn as the primary package manager with comprehensive dependency locking:
- **`yarn.lock`** - Exact version locking for reproducible builds
- **`package-support.json`** - Additional package configuration
- **`.npmrc`** - NPM registry configuration

### Core Runtime Dependencies

**Database Abstraction:**
- **`pg-connection-string`** (^2.6.1) - PostgreSQL connection string parsing
- **`sequelize-pool`** (^7.1.0) - Database connection pooling
- **`wkx`** (^0.5.0) - Well-Known Text/Binary geometry parsing

**Data Manipulation:**
- **`lodash`** (^4.17.21) - Utility functions and functional programming
- **`dottie`** (^2.0.6) - Nested object property access
- **`inflection`** (^1.13.4) - String pluralization and singularization
- **`validator`** (^13.9.0) - String validation and sanitization

**Date/Time Handling:**
- **`moment`** (^2.29.4) - Date manipulation library
- **`moment-timezone`** (^0.5.43) - Timezone-aware date operations

**System Utilities:**
- **`debug`** (^4.3.4) - Debugging utility with namespaces
- **`retry-as-promised`** (^7.0.4) - Promise-based retry logic
- **`semver`** (^7.5.4) - Semantic version parsing and comparison
- **`uuid`** (^8.3.2) - UUID generation
- **`toposort-class`** (^1.0.1) - Topological sorting for dependencies

### Database Driver Dependencies (Peer Dependencies)
Sequelize requires database-specific drivers as peer dependencies, allowing users to install only needed drivers:

**Relational Databases:**
- **`pg`** + **`pg-hstore`** - PostgreSQL with JSON/hstore support
- **`mysql2`** - MySQL and MariaDB with prepared statements
- **`sqlite3`** - SQLite embedded database
- **`tedious`** (8.3.0) - Microsoft SQL Server
- **`ibm_db`** - IBM DB2
- **`oracledb`** - Oracle Database (experimental)

**Cloud Databases:**
- **`snowflake-sdk`** - Snowflake Data Cloud

### Development Dependencies

**Build Tools:**
- **`esbuild`** (0.14.3) - Fast JavaScript/TypeScript compiler
- **`typescript`** (^4.5.4) - TypeScript compiler for type checking
- **`copyfiles`** (^2.4.1) - Cross-platform file copying
- **`rimraf`** (^3.0.2) - Cross-platform directory removal

**Testing Framework:**
- **`mocha`** (^7.2.0) - Test framework
- **`chai`** (^4.3.7) - Assertion library
- **`chai-as-promised`** (^7.1.1) - Promise assertion extensions
- **`chai-datetime`** (^1.8.0) - Date/time assertions
- **`sinon`** (^12.0.1) - Test spies, stubs, and mocks
- **`sinon-chai`** (^3.7.0) - Sinon integration with Chai
- **`nyc`** (^15.1.0) - Code coverage reporting

**Code Quality:**
- **`eslint`** (^8.5.0) - JavaScript/TypeScript linting
- **`@typescript-eslint/eslint-plugin`** (^5.8.1) - TypeScript ESLint rules
- **`@typescript-eslint/parser`** (^5.8.1) - TypeScript ESLint parser
- **`markdownlint-cli`** (^0.30.0) - Markdown linting

**Documentation:**
- **`esdoc`** (^1.1.0) - API documentation generation
- **`esdoc-standard-plugin`** (^1.0.0) - Standard ESDoc plugins
- **`cheerio`** (^1.0.0-rc.10) - Server-side HTML manipulation for docs

**Development Utilities:**
- **`husky`** (^7.0.4) - Git hooks for pre-commit validation
- **`lint-staged`** (^12.1.4) - Staged file linting
- **`cross-env`** (^7.0.3) - Cross-platform environment variables
- **`semantic-release`** (^18.0.1) - Automated versioning and publishing

## Build Targets and Commands

### Primary Build Commands

**Main Build Process:**
```bash
npm run build          # Compiles source code using build.js
npm run prepare        # Runs build + husky install (pre-installation hook)
```

**Development and Testing:**
```bash
npm run lint           # ESLint with automatic fixing
npm run lint-docs      # Markdown documentation linting  
npm run test-typings   # TypeScript type checking without compilation
npm run test           # Full test suite (prepare + typings + teaser + unit + integration)
npm run teaser         # Quick validation test
```

### Database-Specific Testing
Sequelize provides comprehensive testing commands for each supported database:

**Unit Tests by Database:**
```bash
npm run test-unit-mariadb     # MariaDB unit tests
npm run test-unit-mysql       # MySQL unit tests  
npm run test-unit-postgres    # PostgreSQL unit tests
npm run test-unit-sqlite      # SQLite unit tests
npm run test-unit-mssql       # SQL Server unit tests
npm run test-unit-db2         # DB2 unit tests
npm run test-unit-snowflake   # Snowflake unit tests
npm run test-unit-oracle      # Oracle unit tests
npm run test-unit-all         # All databases sequentially
```

**Integration Tests by Database:**
```bash
npm run test-integration-mariadb    # MariaDB integration tests
npm run test-integration-postgres   # PostgreSQL integration tests
npm run test-integration-sqlite     # SQLite integration tests
# ... (similar pattern for all databases)
```

**Full Test Suites by Database:**
```bash
npm run test-mariadb    # Complete MariaDB test suite
npm run test-postgres   # Complete PostgreSQL test suite
npm run test-sqlite     # Complete SQLite test suite
# ... (all supported databases)
```

### Development Database Management
Sequelize includes Docker-based development database setups:

**Database Container Management:**
```bash
npm run start-mariadb     # Start MariaDB 10.3 container
npm run start-mysql       # Start MySQL 5.7 container
npm run start-mysql-8     # Start MySQL 8.0 container
npm run start-postgres    # Start PostgreSQL 10 container
npm run start-mssql       # Start SQL Server 2019 container
npm run start-db2         # Start DB2 11.5 container
npm run start-oracle-*    # Start Oracle containers (18-slim, 21-slim)

npm run stop-*           # Stop corresponding database containers
npm run restart-*        # Restart corresponding database containers
```

### Development Tools
```bash
npm run sscce           # Run Short Self-Contained Correct Example template
npm run sscce-postgres  # SSCCE with PostgreSQL
npm run sscce-mysql     # SSCCE with MySQL
# ... (SSCCE for all databases)

npm run docs           # Generate API documentation
```

## How to Build, Test, and Deploy

### Initial Setup
1. **Clone Repository**: `git clone https://github.com/sequelize/sequelize.git`
2. **Install Dependencies**: `yarn install` (installs all development dependencies)
3. **Install Database Drivers**: Install peer dependencies for databases you'll use
4. **Setup Pre-commit Hooks**: `npm run prepare` (runs build + husky install)

### Building the Library
```bash
# Clean build (recommended)
npm run build

# What this does:
# 1. Removes existing /lib and /types directories
# 2. Compiles all source files using ESBuild
# 3. Generates TypeScript declarations
# 4. Copies additional assets
```

### Testing Strategy

**Quick Validation:**
```bash
npm run teaser          # Fast smoke test
npm run test-typings    # TypeScript compilation check
```

**Unit Testing:**
```bash
npm run test-unit       # All unit tests with default database (SQLite)
npm run test-unit-postgres  # Unit tests with PostgreSQL
```

**Integration Testing:**
```bash
npm run test-integration    # Integration tests with default database
npm run test-integration-mysql  # Integration tests with MySQL
```

**Full Test Suite:**
```bash
npm test                # Complete test suite (all tests + type checking)
npm run test-postgres   # Complete suite with PostgreSQL
```

### Code Quality and Linting
```bash
npm run lint           # ESLint with automatic fixing
npm run lint-docs      # Markdown linting for documentation
```

### Coverage Analysis
```bash
npm run cover          # Generate code coverage reports
npm run cover-integration  # Integration test coverage
npm run cover-unit     # Unit test coverage  
npm run merge-coverage # Merge coverage reports
```

### Documentation Generation
```bash
npm run docs           # Generate API documentation using ESDoc
./docs.sh             # Alternative documentation build script
```

### Development Workflow
1. **Setup Development Database**: `npm run start-postgres` (or preferred database)
2. **Run Tests**: `npm run test-unit-postgres` and `npm run test-integration-postgres`
3. **Code Quality Check**: `npm run lint` and `npm run test-typings`
4. **Create SSCCE**: `npm run sscce-postgres` for reproducing issues
5. **Generate Documentation**: `npm run docs` for API documentation updates

### Release and Deployment
Sequelize uses automated semantic release:
- **Semantic Release**: Automated versioning based on commit messages
- **GitHub Actions**: CI/CD pipeline for testing and publishing
- **NPM Publishing**: Automatic package publishing on version bumps
- **Changelog Generation**: Automated changelog from commit messages

**Release Configuration** (in `package.json`):
```json
{
  "release": {
    "plugins": [
      "@semantic-release/commit-analyzer",
      "semantic-release-fail-on-major-bump",
      "@semantic-release/release-notes-generator",
      "@semantic-release/npm",
      "@semantic-release/github"
    ],
    "branches": ["v6", {"name": "v6-beta", "prerelease": "beta"}]
  }
}
```

The build system is designed for maintainability, comprehensive testing, and reliable releases while supporting the complexity of multi-database compatibility testing.