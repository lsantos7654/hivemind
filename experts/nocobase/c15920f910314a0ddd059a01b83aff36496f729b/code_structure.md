# NocoBase Code Structure

## Repository Organization

NocoBase follows a Lerna-managed monorepo structure with Yarn workspaces, organizing code into three main categories: core packages, plugins, and presets.

## Complete Directory Tree

```
nocobase/
├── .github/                     # GitHub Actions workflows and CI/CD
├── .vscode/                     # VS Code workspace settings
├── benchmark/                   # Performance benchmarking suite
├── docker/                      # Docker configuration files
│   └── nocobase/               # Docker entrypoint and Nginx config
├── examples/                    # Example applications and usage patterns
│   ├── api-client/             # API client usage examples
│   ├── app/                    # Application setup examples
│   └── database/               # Database collection examples
├── locales/                     # Internationalization files
├── packages/                    # Main source code (see detailed structure below)
│   ├── core/                   # Core framework packages
│   ├── plugins/                # Official plugin packages
│   └── presets/                # Application presets
├── patches/                     # Patch files for node_modules (patch-package)
├── scripts/                     # Build and development scripts
├── storage/                     # Runtime storage (uploads, databases)
├── package.json                 # Root package configuration
├── lerna.json                   # Lerna monorepo configuration
├── tsconfig.json                # TypeScript configuration
├── vitest.config.mts           # Vitest test configuration
├── playwright.config.ts        # Playwright E2E test configuration
├── docker-compose.yml          # Development environment services
├── Dockerfile                   # Development Docker image
├── Dockerfile.pro              # Production Docker image
└── yarn.lock                    # Dependency lock file
```

## Packages Structure

### Core Packages (`packages/core/`)

The core packages provide the fundamental building blocks of NocoBase:

```
packages/core/
├── acl/                        # Access Control Layer
│   └── src/                    # ACL logic and role-based permissions
├── actions/                    # Standard CRUD action handlers
│   └── src/                    # Action implementations (list, get, create, update, delete)
├── app/                        # Main application package
│   ├── client/                 # Client-side app entry
│   └── server/                 # Server-side app entry
├── auth/                       # Authentication framework
│   └── src/                    # Auth providers and JWT management
├── build/                      # Build system and tooling
│   ├── bin/                    # Build CLI executables
│   └── src/                    # Build scripts and webpack/vite config
├── cache/                      # Caching abstraction layer
│   └── src/                    # Redis and in-memory cache implementations
├── cli/                        # Command-line interface
│   └── src/
│       ├── commands/           # CLI command implementations
│       │   ├── dev.js          # Development server
│       │   ├── start.js        # Production server
│       │   ├── build.js        # Build command
│       │   ├── test.js         # Test runner
│       │   └── pm2.js          # Plugin manager commands
│       └── cli.js              # CLI entry point
├── client/                     # Frontend framework (React + Ant Design)
│   ├── src/
│   │   ├── acl/                # Client-side ACL
│   │   ├── api-client/         # API communication layer
│   │   ├── application/        # Application context and lifecycle
│   │   ├── block-provider/     # Block rendering system
│   │   ├── collection-manager/ # Collection metadata management
│   │   ├── data-source/        # Data source abstraction
│   │   ├── filter-provider/    # Filter UI components
│   │   ├── hooks/              # React hooks library
│   │   ├── i18n/               # Internationalization
│   │   ├── plugin-manager/     # Client-side plugin loading
│   │   ├── schema-component/   # Schema-driven UI components
│   │   ├── schema-initializer/ # UI schema initialization
│   │   ├── schema-settings/    # Schema configuration UI
│   │   ├── variables/          # Variable system for dynamic values
│   │   ├── modules/            # Feature modules
│   │   │   ├── actions/        # Action components
│   │   │   ├── blocks/         # Block components (table, form, etc.)
│   │   │   ├── fields/         # Field components
│   │   │   ├── menu/           # Menu components
│   │   │   └── popup/          # Popup/modal system
│   │   └── index.ts            # Main export file
│   └── package.json
├── create-nocobase-app/        # Project scaffolding tool
│   ├── templates/              # Project templates
│   └── src/                    # Scaffolding logic
├── data-source-manager/        # Multi-datasource management
│   └── src/                    # Data source registry and abstraction
├── database/                   # Database abstraction layer
│   └── src/
│       ├── collection.ts       # Collection (table) abstraction
│       ├── database.ts         # Main Database class
│       ├── fields/             # Field type definitions
│       ├── dialects/           # Database-specific implementations
│       ├── interfaces/         # Field interface definitions
│       ├── migrations/         # Migration system
│       ├── operators/          # Query operators
│       ├── repository/         # Repository pattern implementation
│       └── query-interface/    # Query interface abstraction
├── devtools/                   # Development tools and utilities
├── evaluators/                 # Expression evaluation (formulas, conditions)
│   └── src/                    # Math.js and custom evaluators
├── lock-manager/               # Distributed locking
│   └── src/                    # Redis-based lock implementation
├── logger/                     # Logging infrastructure
│   └── src/                    # Winston-based logging
├── resourcer/                  # RESTful resource routing
│   └── src/
│       ├── resource.ts         # Resource abstraction
│       ├── resourcer.ts        # Resource manager
│       ├── action.ts           # Action handlers
│       └── middleware.ts       # Middleware system
├── sdk/                        # JavaScript/TypeScript SDK
│   └── src/                    # API client and types
├── server/                     # Backend application framework
│   └── src/
│       ├── application.ts      # Main Application class
│       ├── plugin.ts           # Plugin base class
│       ├── plugin-manager/     # Plugin loading and lifecycle
│       ├── commands/           # Built-in CLI commands
│       ├── gateway/            # WebSocket gateway
│       ├── middlewares/        # Koa middleware
│       ├── cron/               # Cron job management
│       ├── helpers/            # Helper utilities
│       ├── locale/             # Server i18n
│       └── errors/             # Error classes
├── snowflake-id/               # Distributed ID generation
├── telemetry/                  # Telemetry and monitoring
├── test/                       # Testing utilities
│   └── src/                    # Test helpers and mocks
└── utils/                      # Shared utilities
    └── src/                    # Common functions and helpers
```

### Plugin Packages (`packages/plugins/@nocobase/`)

NocoBase includes 83+ official plugins organized by functionality:

```
packages/plugins/@nocobase/
├── plugin-acl/                 # Access control plugin
├── plugin-action-*/            # Action plugins (bulk-edit, bulk-update, export, import, etc.)
├── plugin-ai/                  # AI employee integration
├── plugin-api-doc/             # API documentation generator
├── plugin-api-keys/            # API key management
├── plugin-audit-logs/          # Audit logging
├── plugin-auth/                # Main auth plugin
├── plugin-auth-sms/            # SMS authentication
├── plugin-backup-restore/      # Backup and restore functionality
├── plugin-block-*/             # Block plugins (iframe, template, workbench)
├── plugin-calendar/            # Calendar view
├── plugin-charts/              # Charting plugin
├── plugin-client/              # Client-side plugin utilities
├── plugin-collection-*/        # Collection type plugins (SQL, tree)
├── plugin-data-source-*/       # Data source plugins (main, manager)
├── plugin-data-visualization/  # Data visualization
├── plugin-departments/         # Department management
├── plugin-environment-variables/ # Environment variable management
├── plugin-error-handler/       # Error handling
├── plugin-field-*/             # Field type plugins
│   ├── plugin-field-attachment-url/
│   ├── plugin-field-china-region/
│   ├── plugin-field-formula/
│   ├── plugin-field-markdown-vditor/
│   ├── plugin-field-sequence/
│   ├── plugin-field-sort/
│   └── ...
├── plugin-file-manager/        # File management
├── plugin-file-previewer-*/    # File preview plugins
├── plugin-gantt/               # Gantt chart view
├── plugin-graph-collection-manager/ # Visual collection designer
├── plugin-iframe-block/        # Iframe embedding
├── plugin-import-export/       # Import/export functionality
├── plugin-kanban/              # Kanban board view
├── plugin-localization/        # Localization management
├── plugin-map/                 # Map integration
├── plugin-mobile-client/       # Mobile app support
├── plugin-multi-app-manager/   # Multi-tenant management
├── plugin-notification-*/      # Notification plugins (email, SMS, in-app)
├── plugin-oidc/                # OIDC authentication
├── plugin-public-forms/        # Public form sharing
├── plugin-saml/                # SAML authentication
├── plugin-sequence-field/      # Auto-increment sequences
├── plugin-snapshot-field/      # Snapshot/versioning
├── plugin-system-settings/     # System configuration
├── plugin-theme-editor/        # Theme customization
├── plugin-ui-schema-storage/   # UI schema persistence
├── plugin-users/               # User management
├── plugin-verification/        # Verification codes
├── plugin-workflow/            # Workflow engine
├── plugin-workflow-*/          # Workflow extension plugins
│   ├── plugin-workflow-action-trigger/
│   ├── plugin-workflow-aggregate/
│   ├── plugin-workflow-delay/
│   ├── plugin-workflow-dynamic-calculation/
│   ├── plugin-workflow-json-query/
│   ├── plugin-workflow-manual/
│   ├── plugin-workflow-parallel/
│   ├── plugin-workflow-request/
│   ├── plugin-workflow-sql/
│   └── ...
└── ...
```

Each plugin follows a standard structure:
```
plugin-*/
├── src/
│   ├── client/                 # Client-side plugin code
│   │   ├── index.tsx
│   │   └── components/
│   ├── server/                 # Server-side plugin code
│   │   ├── index.ts
│   │   ├── collections/        # Database collections
│   │   ├── actions/            # Custom actions
│   │   └── migrations/         # Database migrations
│   ├── locale/                 # Plugin translations
│   └── swagger/                # API documentation
├── package.json
└── README.md
```

### Preset Packages (`packages/presets/`)

```
packages/presets/
└── nocobase/                   # Default NocoBase preset
    ├── src/
    │   ├── server/             # Server-side preset configuration
    │   └── client/             # Client-side preset configuration
    └── package.json
```

## Code Organization Patterns

### 1. Dual Package Architecture
Most packages provide both client and server exports:
- Client code in `src/client/` (React components, hooks, providers)
- Server code in `src/server/` (Koa middleware, database logic, actions)
- Shared code in `src/` root (types, utilities, constants)

### 2. Plugin Structure Convention
All plugins follow a consistent pattern:
- Main exports: `src/client/index.tsx` and `src/server/index.ts`
- Collections: Database schema in `src/server/collections/`
- Migrations: Database migrations in `src/server/migrations/`
- Locales: i18n files in `src/locale/`
- Tests: Vitest tests colocated with source (`.test.ts` files)

### 3. Schema-Driven Components
Client-side components are often schema-driven:
- Schema initializers in `schema-initializer/`
- Schema settings in `schema-settings/`
- Schema components in `schema-component/`

### 4. Repository Pattern
Data access follows repository pattern:
- Collection definitions separate from models
- Repository classes extend base Repository
- Custom repositories for special field types (ArrayFieldRepository, RelationRepository)

### 5. Middleware Stack
Koa middleware organized by concern:
- Authentication middleware
- ACL middleware
- Data wrapping middleware
- Error handling middleware
- Request logging middleware

## Key Files and Their Roles

### Root Configuration Files
- `package.json`: Root package with workspace configuration and dev scripts
- `lerna.json`: Version management (current: 1.9.46)
- `tsconfig.json`: TypeScript compilation settings
- `vitest.config.mts`: Test configuration
- `docker-compose.yml`: Development environment setup

### Core Entry Points
- `packages/core/server/src/application.ts`: Main Application class (800+ lines)
- `packages/core/client/src/application/Application.tsx`: Client Application class
- `packages/core/database/src/database.ts`: Database abstraction layer
- `packages/core/resourcer/src/resourcer.ts`: RESTful resource manager
- `packages/core/cli/src/cli.js`: CLI entry point

### Build System
- `packages/core/build/src/buildClient.ts`: Client build logic
- `packages/core/build/src/buildPlugin.ts`: Plugin build logic
- `packages/core/build/bin/nocobase.js`: Build CLI

### Plugin Base Classes
- `packages/core/server/src/plugin.ts`: Server-side Plugin base class
- `packages/core/client/src/application/Plugin.ts`: Client-side Plugin base class

## Module and Package Organization

### Core Dependencies Management
Each package declares dependencies in its own `package.json`:
- `peerDependencies`: Framework dependencies (e.g., `@nocobase/server`)
- `dependencies`: Package-specific dependencies
- `devDependencies`: Development and testing tools

### Workspace Resolution
Yarn workspaces enable cross-package imports:
- Pattern: `packages/*/*` and `packages/*/*/*`
- Internal packages use `@nocobase/*` scope
- Version managed centrally via Lerna

### Build Output
- TypeScript compiled to `lib/` (CommonJS) and `es/` (ESM)
- Client bundles include both formats for tree-shaking
- Type definitions (.d.ts) generated alongside JavaScript

### Test Organization
- Unit tests: Colocated `.test.ts` files
- E2E tests: Playwright tests in `__e2e__/` directories
- Test utilities: `@nocobase/test` package

## Special Directories

- `storage/`: Runtime data (file uploads, SQLite databases, logs)
- `patches/`: Modified node_modules via patch-package
- `locales/`: Application-level translations (separate from plugin locales)
- `examples/`: Runnable example applications demonstrating API usage
- `benchmark/`: Performance testing suite
- `.github/workflows/`: CI/CD pipeline definitions

This structure supports NocoBase's microkernel philosophy where the core provides minimal functionality, and everything else is delivered through composable, independently deployable plugins.
