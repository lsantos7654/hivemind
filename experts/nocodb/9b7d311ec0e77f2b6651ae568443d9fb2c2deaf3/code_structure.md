# NocoDB Code Structure

## Complete Annotated Directory Tree

```
nocodb/
├── .github/                          # GitHub configuration
│   ├── workflows/                    # CI/CD workflows
│   ├── CONTRIBUTING.md              # Contribution guidelines
│   ├── COMMIT_CONVENTION.md         # Commit message standards
│   └── PULL_REQUEST_TEMPLATE.md     # PR template
├── .do/                             # DigitalOcean deployment configs
├── charts/                          # Kubernetes Helm charts
├── docker-compose/                  # Docker Compose configurations
│   ├── 1_Auto_Upstall/             # Auto-installation scripts
│   ├── 2_pg/                        # PostgreSQL setup
│   ├── 3_traefik/                   # Traefik reverse proxy
│   ├── nginx/                       # Nginx configurations
│   └── nginx-proxy-manager/         # Nginx Proxy Manager setup
├── markdown/                        # Documentation and localized READMEs
│   ├── plugins/                     # Plugin documentation
│   └── readme/languages/            # Multilingual README files
├── packages/                        # Monorepo packages
│   ├── nocodb/                      # Backend application (NestJS)
│   ├── nocodb-sdk/                  # TypeScript SDK
│   ├── nocodb-sdk-v2/              # SDK v2 (next generation)
│   ├── nc-gui/                      # Frontend application (Nuxt 3)
│   ├── nc-lib-gui/                  # Compiled frontend library
│   ├── nc-mail-assets/              # Email template assets
│   ├── nc-integration-scaffolder/   # Integration scaffolding tool
│   ├── nc-secret-mgr/              # Secret management utilities
│   └── noco-integrations/           # Integration framework
├── scripts/                         # Build and utility scripts
├── tests/                           # Test suites
│   ├── playwright/                  # End-to-end Playwright tests
│   └── docker/                      # Docker test environments
├── package.json                     # Root package configuration
├── pnpm-workspace.yaml             # pnpm workspace definition
├── pnpm-lock.yaml                  # Dependency lock file
├── lerna.json                       # Lerna configuration
└── LICENSE.md                       # Sustainable Use License
```

## Main Source Directories and Their Purposes

### 1. packages/nocodb/ - Backend Application

**Core Structure:**
```
packages/nocodb/
├── src/
│   ├── Noco.ts                      # Main application entry point
│   ├── app.module.ts                # NestJS root module
│   ├── app.config.ts                # Application configuration
│   ├── instrument.ts                # Monitoring and instrumentation
│   │
│   ├── controllers/                 # API request handlers
│   │   ├── v3/                     # API v3 controllers
│   │   ├── api-docs/               # API documentation controllers
│   │   ├── users/                  # User management controllers
│   │   ├── internal/               # Internal API controllers
│   │   └── old-datas/              # Legacy data controllers
│   │
│   ├── services/                    # Business logic layer
│   │   ├── v3/                     # API v3 services
│   │   ├── api-docs/               # API documentation generation
│   │   ├── base-users/             # Base user management
│   │   ├── app-hooks/              # Application lifecycle hooks
│   │   ├── mail/                   # Email services
│   │   ├── notifications/          # Notification services
│   │   ├── users/                  # User services
│   │   ├── emit-handler/           # Event emission handling
│   │   ├── formula-column-type-changer/  # Formula column operations
│   │   └── meta-dependency/        # Metadata dependency tracking
│   │
│   ├── models/                      # Data models and ORM
│   │   ├── Base.ts                 # Base (project) model
│   │   ├── BaseUser.ts             # Base user associations
│   │   ├── Column.ts               # Table column model
│   │   ├── Table.ts                # Table model
│   │   ├── View.ts                 # View model
│   │   ├── Filter.ts               # Filter model
│   │   ├── Sort.ts                 # Sort model
│   │   ├── Hook.ts                 # Webhook model
│   │   ├── User.ts                 # User model
│   │   ├── ApiToken.ts             # API token model
│   │   ├── Audit.ts                # Audit log model
│   │   ├── Extension.ts            # Extension model
│   │   ├── Integration.ts          # Integration model
│   │   └── [40+ model files]      # Specialized models
│   │
│   ├── db/                          # Database layer
│   │   ├── BaseModelSqlv2/         # SQL model implementation
│   │   ├── BaseModelSqlv2.ts       # Base SQL model class
│   │   ├── sql-client/             # Database client adapters
│   │   ├── sql-data-mapper/        # Data mapping utilities
│   │   ├── sql-mgr/                # SQL manager
│   │   ├── sql-migrator/           # Database migrations
│   │   ├── formulav2/              # Formula engine v2
│   │   ├── functionMappings/       # Database function mappings
│   │   ├── aggregations/           # Aggregation query builders
│   │   ├── cte-generator/          # Common Table Expression generator
│   │   ├── field-handler/          # Field type handlers
│   │   ├── links/                  # Link/relationship handling
│   │   ├── widgets/                # Widget data handlers
│   │   ├── util/                   # Database utilities
│   │   ├── CustomKnex.ts           # Custom Knex instance
│   │   ├── conditionV2.ts          # Query condition builder
│   │   └── sortV2.ts               # Query sorting logic
│   │
│   ├── modules/                     # NestJS feature modules
│   │   ├── auth/                   # Authentication module
│   │   ├── oauth/                  # OAuth integration
│   │   ├── jobs/                   # Background job processing
│   │   ├── event-emitter/          # Event system
│   │   └── noco.module.ts          # Main NocoDB module
│   │
│   ├── meta/                        # Metadata management
│   │   ├── meta.service.ts         # Core metadata service
│   │   ├── audit.service.ts        # Audit service
│   │   └── migrations/             # Metadata schema migrations
│   │
│   ├── plugins/                     # Plugin system
│   │   ├── s3/                     # AWS S3 plugin
│   │   ├── gcs/                    # Google Cloud Storage plugin
│   │   ├── minio/                  # MinIO plugin
│   │   ├── smtp/                   # SMTP email plugin
│   │   ├── ses/                    # AWS SES plugin
│   │   ├── slack/                  # Slack integration
│   │   ├── discord/                # Discord integration
│   │   ├── teams/                  # Microsoft Teams integration
│   │   ├── mattermost/             # Mattermost integration
│   │   ├── twilio/                 # Twilio SMS plugin
│   │   ├── storage/                # Storage abstraction
│   │   └── [15+ storage plugins]  # Various storage providers
│   │
│   ├── strategies/                  # Passport authentication strategies
│   │   ├── authtoken.strategy/     # Token-based auth
│   │   ├── google.strategy/        # Google OAuth
│   │   ├── basic.strategy/         # Basic auth
│   │   └── base-view.strategy/     # View-based auth
│   │
│   ├── guards/                      # Route guards
│   │   └── global/                 # Global authentication guards
│   │
│   ├── middlewares/                 # Express/NestJS middlewares
│   │   ├── extract-ids/            # ID extraction middleware
│   │   ├── gui/                    # GUI serving middleware
│   │   ├── global/                 # Global middleware
│   │   ├── raw-body.middleware.ts  # Raw body parser
│   │   ├── json-body.middleware.ts # JSON body parser
│   │   └── url-encode.middleware.ts # URL encoding middleware
│   │
│   ├── interceptors/                # NestJS interceptors
│   │   └── is-upload-allowed/      # Upload permission interceptor
│   │
│   ├── filters/                     # Exception filters
│   │   └── global-exception/       # Global exception handler
│   │
│   ├── decorators/                  # Custom decorators
│   ├── gateways/                    # WebSocket gateways
│   │   └── RedisIoAdapter.ts       # Redis adapter for Socket.io
│   │
│   ├── helpers/                     # Helper functions
│   │   └── db-error/               # Database error helpers
│   │
│   ├── integrations/                # Integration implementations
│   ├── interface/                   # TypeScript interfaces
│   ├── mcp/                         # Model Context Protocol
│   ├── providers/                   # Dependency injection providers
│   ├── cache/                       # Caching layer
│   ├── redis/                       # Redis utilities
│   ├── socket/                      # WebSocket handling
│   ├── constants/                   # Application constants
│   ├── schema/                      # JSON schemas
│   ├── types/                       # TypeScript types
│   │   ├── nc-plugin/              # Plugin type definitions
│   │   ├── data-columns/           # Column type definitions
│   │   └── metaProps/              # Metadata property types
│   │
│   ├── utils/                       # Utility functions
│   │   ├── builders/               # Query builders
│   │   ├── cloud/                  # Cloud-specific utilities
│   │   ├── common/                 # Common utilities
│   │   └── nc-config/              # Configuration utilities
│   │
│   ├── version-upgrader/            # Version migration system
│   │   └── upgraders/              # Version-specific upgraders
│   │
│   ├── run/                         # Application entry points
│   │   ├── docker.ts               # Docker entry point
│   │   ├── dockerRunMysql.ts       # MySQL dev entry
│   │   ├── dockerRunPG.ts          # PostgreSQL dev entry
│   │   └── testDocker.ts           # Test environment entry
│   │
│   ├── public/                      # Static assets
│   │   ├── css/                    # Stylesheets
│   │   └── js/                     # JavaScript files
│   │
│   └── dbQueryClient/              # Database query client
│
├── docker/                          # Docker build files
│   ├── main.js                     # Docker entry script
│   ├── start-litestream.sh         # Litestream backup script
│   └── rspack.config.js            # Docker build configuration
│
├── tests/                           # Backend tests
│   ├── unit/                       # Unit tests
│   │   ├── formula/                # Formula tests
│   │   └── rest/                   # REST API tests
│   └── export-import/              # Export/import tests
│
├── Dockerfile                       # Production Docker image
├── package.json                     # Package definition
├── rspack.config.js                # Production build config
├── rspack.dev.config.js            # Development build config
├── rspack.cli.config.js            # CLI build config
└── tsconfig.json                   # TypeScript configuration
```

### 2. packages/nc-gui/ - Frontend Application

**Core Structure:**
```
packages/nc-gui/
├── components/                      # Vue components
│   ├── dashboard/                  # Dashboard components
│   ├── smartsheet/                 # Spreadsheet grid components
│   │   ├── grid/                  # Grid view
│   │   ├── gallery/               # Gallery view
│   │   ├── kanban/                # Kanban view
│   │   ├── calendar/              # Calendar view
│   │   ├── toolbar/               # View toolbars
│   │   └── column/                # Column components
│   ├── cell/                       # Cell type components
│   ├── virtual-cell/               # Virtual cell components
│   ├── project/                    # Project/base components
│   ├── workspace/                  # Workspace components
│   ├── account/                    # Account management
│   ├── auth/                       # Authentication components
│   ├── webhook/                    # Webhook configuration
│   ├── api-client/                 # API client interface
│   ├── erd/                        # Entity relationship diagram
│   ├── extensions/                 # Extension components
│   ├── general/                    # General-purpose components
│   ├── nc/                         # NocoDB-specific components
│   ├── dlg/                        # Dialog components
│   ├── tabs/                       # Tab components
│   ├── cmd-j/                      # Command palette (Cmd+J)
│   ├── cmd-k/                      # Search palette (Cmd+K)
│   ├── cmd-l/                      # Quick actions (Cmd+L)
│   ├── cmd-footer/                 # Command footer
│   ├── ai/                         # AI integration components
│   ├── monaco/                     # Monaco editor components
│   ├── template/                   # Template components
│   ├── notification/               # Notification system
│   ├── permissions/                # Permission management
│   ├── roles/                      # Role management
│   ├── actions/                    # Action components
│   ├── feed/                       # Activity feed
│   └── payment/                    # Payment integration
│
├── composables/                     # Vue composition functions
│   ├── useApi/                     # API client composable
│   ├── useGlobal/                  # Global state composable
│   ├── useMultiSelect/             # Multi-select functionality
│   ├── usePlugin/                  # Plugin system composable
│   ├── useRoles/                   # Role management composable
│   ├── useSidebar/                 # Sidebar state
│   ├── useDialog/                  # Dialog management
│   ├── useCommandPalette/          # Command palette
│   ├── useFormBuilder/             # Form builder
│   ├── useExpandedFormDetached/    # Detached form view
│   ├── useInjectionState/          # State injection
│   ├── useSelectedCellKeyupListener/ # Keyboard navigation
│   ├── useMenuCloseOnEsc/          # Menu handling
│   └── viewRowColor/               # Row color logic
│
├── pages/                           # Nuxt pages (routes)
│   ├── index/                      # Home page
│   ├── projects/                   # Project routes
│   ├── account/                    # Account pages
│   ├── signup/                     # Registration
│   ├── reset/                      # Password reset
│   ├── oauth/                      # OAuth callback
│   ├── error/                      # Error pages
│   ├── playground/                 # Development playground
│   └── leaving/                    # Exit pages
│
├── layouts/                         # Nuxt layouts
├── middleware/                      # Nuxt middleware
├── plugins/                         # Nuxt plugins
├── store/                           # Pinia stores
│   └── ui/                         # UI state stores
│
├── utils/                           # Utility functions
│   └── search/                     # Search utilities
│
├── helpers/                         # Helper functions
│   ├── parsers/                    # Data parsers
│   ├── tiptap/                     # TipTap helpers
│   └── tiptap-markdown/            # Markdown integration
│
├── extensions/                      # Extension implementations
│   ├── data-exporter/              # Data export extension
│   └── json-exporter/              # JSON export extension
│
├── workers/                         # Web workers
├── lang/                            # i18n translations
├── assets/                          # Static assets
│   ├── css/                        # Global styles
│   ├── icons/                      # Icon sets
│   ├── img/                        # Images
│   ├── nc-icons/                   # NocoDB custom icons
│   ├── nc-icons-v2/                # NocoDB icons v2
│   └── style/                      # Style definitions
│
├── public/                          # Public static files
│   ├── js/                         # JavaScript libraries
│   └── plugins/                    # Plugin assets
│
├── lib/                             # Library code
├── context/                         # Context providers
├── error/                           # Error handling
├── test/                            # Frontend tests
├── nuxt.config.ts                  # Nuxt configuration
├── package.json                    # Package definition
├── tsconfig.json                   # TypeScript configuration
└── windi.config.ts                 # WindiCSS configuration
```

### 3. packages/nocodb-sdk/ - TypeScript SDK

```
packages/nocodb-sdk/
├── src/
│   └── lib/                        # SDK source
│       ├── Api.ts                  # Auto-generated API client
│       ├── UITypes.ts              # UI type definitions
│       ├── CustomAPI.ts            # Custom API utilities
│       ├── TemplateGenerator.ts    # Template generation
│       ├── helperFunctions.ts      # Helper utilities
│       ├── formulaHelpers.ts       # Formula utilities
│       ├── enums.ts                # Enumerations
│       ├── globals.ts              # Global constants
│       ├── columnRules.ts          # Column validation rules
│       ├── sqlUi.ts                # SQL UI helpers
│       ├── timezoneUtils.ts        # Timezone utilities
│       ├── passwordHelpers.ts      # Password utilities
│       ├── dateTimeHelper.ts       # DateTime helpers
│       ├── filterHelpers.ts        # Filter utilities
│       ├── aggregationHelper.ts    # Aggregation helpers
│       ├── errorUtils.ts           # Error handling
│       ├── is.ts                   # Type checking utilities
│       └── [30+ utility modules]  # Various helpers
│
├── build-script/                    # Build automation
│   └── mergeAndGenerateSwaggerCE   # Swagger generation
│
├── build/                           # Compiled output
│   ├── main/                       # CommonJS build
│   └── module/                     # ES module build
│
├── package.json                     # Package definition
└── tsconfig.json                   # TypeScript configuration
```

### 4. packages/noco-integrations/ - Integration Framework

```
packages/noco-integrations/
├── core/                            # Core integration framework
│   └── src/                        # Framework source
│       ├── types.ts                # Type definitions
│       ├── base-integration.ts     # Base integration class
│       └── helpers.ts              # Helper functions
│
└── packages/                        # Integration packages
    ├── auth-github/                # GitHub authentication
    ├── auth-google/                # Google authentication
    ├── ai-openai/                  # OpenAI integration
    ├── sync-github/                # GitHub sync
    ├── sync-jira/                  # Jira sync
    ├── sync-linear/                # Linear sync
    └── [additional integrations]   # Other integrations
```

### 5. tests/playwright/ - End-to-End Tests

```
tests/playwright/
├── tests/                           # Test suites
│   ├── db/                         # Database tests
│   ├── ui/                         # UI tests
│   └── api/                        # API tests
│
├── pages/                           # Page object models
├── fixtures/                        # Test fixtures
├── setup/                           # Test setup
├── scripts/                         # Test scripts
├── constants/                       # Test constants
├── playwright.config.ts            # Playwright configuration
└── package.json                    # Test dependencies
```

## Code Organization Patterns

**Backend Patterns:**
- **NestJS Module Pattern**: Features organized into self-contained modules
- **Service Layer Pattern**: Business logic separated from controllers
- **Repository Pattern**: Data access abstracted through models
- **Strategy Pattern**: Multiple authentication strategies
- **Plugin Architecture**: Extensible plugin system for integrations
- **Event-Driven**: Event emitter for cross-module communication
- **Dependency Injection**: Full DI container via NestJS

**Frontend Patterns:**
- **Composition API**: Vue 3 composables for reusable logic
- **Component-Based**: Modular, reusable components
- **File-Based Routing**: Nuxt automatic routing from pages
- **State Management**: Pinia stores for global state
- **Utility-First CSS**: WindiCSS for styling
- **Server-Side Generation**: Nuxt SSG capabilities

**Monorepo Patterns:**
- **Workspace Structure**: pnpm workspaces for package management
- **Shared Dependencies**: Common packages across workspace
- **Independent Versioning**: Packages can version independently
- **Build Orchestration**: Coordinated builds across packages
