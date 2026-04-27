This expert specializes in:

### Core Architecture
- **Monorepo Structure**: Lerna + Yarn workspaces organization, 22 core packages + 83+ plugins
- **Microkernel Design**: Plugin-based architecture where all features are plugins
- **Data Model-Driven**: Decoupling of data structure from UI, schema-driven components
- **Dual Package Pattern**: Client/server separation in packages (src/client, src/server)

### Database Layer (`@nocobase/database`)
- **Collection API**: Table abstraction with field definitions and options
- **Repository Pattern**: Data access layer above Sequelize models
- **Field Types**: 30+ field types including relations, formulas, sequences, rich text
- **Query Operators**: NocoBase-specific operators ($gt, $like, $anyOf, etc.)
- **Multi-Database Support**: PostgreSQL, MySQL, SQLite, MariaDB, Kingbase
- **Migrations**: Umzug-based migration system with version tracking
- **Interface Manager**: Field interface definitions and UI bindings

### Server Framework (`@nocobase/server`)
- **Application Class**: Main Koa-based application (packages/core/server/src/application.ts:222)
- **Plugin System**: Plugin base class with lifecycle hooks (load, install, upgrade, enable, disable)
- **Resource-Action Pattern**: RESTful API abstraction via Resourcer
- **Middleware Stack**: Koa middleware for auth, ACL, logging, error handling
- **Event System**: AsyncEmitter for database hooks and application events
- **Cron Jobs**: Scheduled task management
- **WebSocket Gateway**: Real-time communication layer
- **Pub/Sub Manager**: Redis-backed message passing for distributed systems

### Client Framework (`@nocobase/client`)
- **React Application**: React 18 + Ant Design 5 component library
- **Schema System**: JSON schema-driven UI with x-component, x-decorator patterns
- **Formily Integration**: Form solution with validators, effects, and reactive state
- **Schema Initializers**: UI builders for adding blocks, fields, actions
- **Schema Settings**: Configuration panels for UI customization
- **Block System**: Reusable UI blocks (table, form, calendar, kanban, charts)
- **API Client**: Hook-based data fetching (useRequest, useAPIClient)
- **Plugin Manager**: Client-side plugin loading and registration
- **Variable System**: Dynamic value resolution in schemas
- **ACL Provider**: Client-side permission checking

### Plugin Development
- **Plugin Structure**: Standardized src/client, src/server, src/locale organization
- **Lifecycle Hooks**: afterAdd, beforeLoad, load, install, upgrade, beforeEnable, afterEnable, beforeDisable, afterDisable, beforeRemove, afterRemove
- **Collection Definition**: Database schema in server/collections/
- **Resource Definition**: REST API endpoints with custom actions
- **UI Components**: Schema components registration and block initializers
- **Migrations**: Database migrations in server/migrations/
- **i18n**: Locale files with multi-language support
- **Plugin Examples**: 83+ official plugins as reference implementations

### Build System
- **TypeScript Compilation**: Dual output (CommonJS lib/, ESM es/)
- **Lerna Publishing**: Monorepo version management (current: 1.9.46)
- **CLI Commands**: nocobase build, dev, start, test, clean, pm
- **Docker Support**: Multi-stage Dockerfile, docker-compose setup
- **Testing**: Vitest (unit), Playwright (E2E)
- **Development Mode**: Hot reload for client, auto-restart for server

### Advanced Features
- **Workflow Engine**: Visual workflow builder with triggers, nodes, conditions
- **AI Integration**: AI employee system with OpenAI, Anthropic, Bedrock support
- **Multi-Tenancy**: Multi-app manager plugin for SaaS deployments
- **Authentication**: OAuth, SAML, OIDC, SMS auth providers
- **File Management**: Multi-storage support (local, S3, OSS, COS)
- **Data Visualization**: Chart blocks with G2Plot integration
- **Audit Logging**: Comprehensive change tracking
- **Backup/Restore**: Database and configuration backup system

### API Patterns
- **RESTful Resources**: `/api/{resource}:{action}` pattern
- **Association Resources**: `/api/{resource}/{id}/{association}` pattern
- **Action Middleware**: Composable action handlers
- **Filter Syntax**: Complex query filters with nested operators
- **Pagination**: Cursor-based and offset-based pagination
- **Eager Loading**: Association preloading with appends parameter
- **Batch Operations**: Bulk create, update, destroy actions

### Configuration
- **Environment Variables**: APP_ENV, DB_DIALECT, REDIS_HOST, etc.
- **Application Options**: Database, resourcer, plugins, logger, cache, ACL config
- **Plugin Options**: Per-plugin configuration in plugin array
- **Collection Options**: Table settings (sortable, timestamps, paranoid, etc.)
- **Field Options**: Validation, UI props, default values, unique constraints

### Deployment
- **Docker Compose**: Recommended for no-code scenarios
- **create-nocobase-app**: CLI tool for project scaffolding
- **Git Clone**: For core development and contributions
- **Production Build**: Multi-stage Docker with Nginx
- **Environment Setup**: PostgreSQL/MySQL + Redis + Node.js 18+
- **PM2 Integration**: Process management for production

### Common Patterns
- **Collection-to-Resource**: Automatic REST API generation from collections
- **Schema Initialization**: Programmatic UI construction via JSON schemas
- **Repository Actions**: Standard CRUD (list, get, create, update, destroy)
- **Custom Actions**: Extending resources with business logic
- **Event Handlers**: Database hooks (afterCreate, beforeDestroy, etc.)
- **ACL Rules**: Role-based permission definitions
- **i18n Implementation**: Translation keys in locale files

### File Locations (Key Implementations)
- Application: `packages/core/server/src/application.ts:222`
- Database: `packages/core/database/src/database.ts`
- Collection: `packages/core/database/src/collection.ts:145`
- Plugin Base: `packages/core/server/src/plugin.ts`
- Resource: `packages/core/resourcer/src/resource.ts`
- Client App: `packages/core/client/src/application/Application.tsx`
- Schema Component: `packages/core/client/src/schema-component/`
- Build System: `packages/core/build/src/`
- CLI: `packages/core/cli/src/cli.js`
