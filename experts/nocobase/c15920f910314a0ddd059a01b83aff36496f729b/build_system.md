# NocoBase Build System

## Build System Overview

NocoBase uses a custom build system based on TypeScript compilation, managed through the `@nocobase/build` package. The monorepo is orchestrated by Lerna and Yarn workspaces, with scripts coordinated through the `nocobase` CLI.

## Build System Type

### Primary Tools
- **Lerna**: Monorepo version management and publishing (v1.9.46)
- **Yarn Workspaces**: Package linking and dependency management
- **TypeScript**: Source compilation (TypeScript 5.1.3)
- **Custom Build Scripts**: `@nocobase/build` package with CLI
- **Vitest**: Testing framework (v1.5.0)
- **Playwright**: E2E testing

### Build Architecture
NocoBase employs a multi-stage build process:
1. TypeScript compilation to CommonJS (`lib/`) and ESM (`es/`)
2. Client bundling for browser distribution
3. Plugin bundling for dynamic loading
4. Asset processing and optimization

## Configuration Files

### Root Configuration

**package.json** - Root workspace configuration
```json
{
  "name": "nocobase",
  "private": true,
  "workspaces": [
    "packages/*/*",
    "packages/*/*/*"
  ],
  "engines": {
    "node": ">=18"
  },
  "scripts": {
    "nocobase": "nocobase",
    "build": "nocobase build",
    "dev": "nocobase dev",
    "start": "nocobase start",
    "test": "nocobase test",
    "clean": "nocobase clean"
  }
}
```

**lerna.json** - Version and publishing configuration
```json
{
  "version": "1.9.46",
  "npmClient": "yarn",
  "useWorkspaces": true,
  "command": {
    "version": {
      "forcePublish": true,
      "exact": true
    }
  }
}
```

**tsconfig.json** - TypeScript compilation settings
```json
{
  "compilerOptions": {
    "target": "esnext",
    "module": "esnext",
    "jsx": "react",
    "esModuleInterop": true,
    "moduleResolution": "node",
    "declaration": true,
    "experimentalDecorators": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "sourceMap": true,
    "baseUrl": "."
  },
  "include": ["packages/**/*"],
  "exclude": [
    "packages/**/node_modules",
    "packages/**/dist",
    "packages/**/lib",
    "packages/**/es"
  ]
}
```

**vitest.config.mts** - Test configuration
```javascript
import { defineConfig } from '@nocobase/test/vitest.mjs';
export default defineConfig();
```

**playwright.config.ts** - E2E test configuration
Located at root for end-to-end testing setup.

## External Dependencies

### Core Runtime Dependencies

**Backend Stack:**
- `koa` (^2.15.4): Web framework
- `sequelize` (^6.26.0): ORM and database abstraction
- `ioredis` (^5.7.0): Redis client for caching and pub/sub
- `i18next` (^22.4.9): Internationalization
- `commander` (^9.2.0): CLI framework
- `ws` (^8.13.0): WebSocket support
- `dayjs` (^1.11.8): Date/time utilities
- `lodash` (^4.17.21): Utility functions
- `nanoid` (^3.3.11): ID generation
- `axios` (^1.7.0): HTTP client

**Frontend Stack:**
- `react` (^18.0.0): UI framework
- `react-dom` (^18.0.0): DOM rendering
- `antd` (5.24.2): UI component library
- `@ant-design/icons` (^5.6.1): Icon library
- `@formily/core`, `@formily/react`, `@formily/antd-v5` (^2.2.27, 1.2.3): Form solution
- `@emotion/css` (^11.7.1): CSS-in-JS styling
- `react-router-dom` (6.28.1): Client-side routing
- `@dnd-kit/core`, `@dnd-kit/sortable` (^6.0.0, ^7.0.0): Drag and drop
- `ahooks` (^3.7.2): React hooks library
- `i18next`, `react-i18next` (^22.4.9, ^11.15.1): i18n

**Database Drivers** (peer dependencies):
- `mysql2`: MySQL/MariaDB support
- `pg`: PostgreSQL support
- `sqlite3`: SQLite support

### Development Dependencies

- `typescript` (5.1.3): TypeScript compiler
- `vitest` (^1.5.0): Unit testing
- `@playwright/test`: E2E testing
- `eslint`: Code linting
- `prettier`: Code formatting
- `@commitlint/cli`, `@commitlint/config-conventional`: Commit linting
- `lerna`: Monorepo management
- `patch-package` (^8.0.0): Dependency patching
- `pm2` (^6.0.5): Process management
- `ghooks` (^2.0.4): Git hooks
- `lint-staged` (^13.2.3): Staged file linting

### Version Pinning (Resolutions)
Key dependencies pinned for compatibility:
```json
{
  "react": "^18.0.0",
  "react-dom": "^18.0.0",
  "antd": "5.24.2",
  "@formily/antd-v5": "1.2.3",
  "dayjs": "1.11.13",
  "typescript": "5.1.3"
}
```

## Build Commands and Targets

### Main Build Commands

**Development Build:**
```bash
yarn dev                  # Start development server with hot reload
yarn dev-server           # Start only backend server in dev mode
```

**Production Build:**
```bash
yarn build                # Build all packages (TypeScript + client bundles)
yarn build --no-dts       # Build without generating .d.ts files
```

**Testing:**
```bash
yarn test                 # Run all tests
yarn test:server          # Run server-side tests
yarn test:client          # Run client-side tests
yarn test:server-coverage # Server tests with coverage
yarn test:client-coverage # Client tests with coverage
yarn e2e                  # Run Playwright E2E tests
```

**Deployment:**
```bash
yarn start                # Start production server
yarn tar                  # Create deployment tarball
```

**Maintenance:**
```bash
yarn clean                # Clean build artifacts
yarn postinstall          # Post-install hooks
```

**Plugin Management:**
```bash
yarn pm add <plugin>      # Add plugin
yarn pm remove <plugin>   # Remove plugin
yarn pm enable <plugin>   # Enable plugin
yarn pm disable <plugin>  # Disable plugin
```

**Versioning and Publishing:**
```bash
yarn version:alpha        # Create alpha pre-release version
yarn release              # Publish packages to npm
yarn release:force        # Force publish from package versions
```

### Custom NocoBase CLI Commands

The `@nocobase/cli` package provides additional commands:

```bash
nocobase build            # Build packages
nocobase dev              # Development mode
nocobase start            # Production mode
nocobase test             # Run tests
nocobase clean            # Clean build outputs
nocobase pm               # Plugin manager
nocobase pm2              # PM2 operations
nocobase db:sync          # Sync database schema
nocobase install          # Install application
nocobase upgrade          # Upgrade application
nocobase doc              # Generate documentation
nocobase benchmark        # Run benchmarks
nocobase perf             # Performance testing
```

## How to Build, Test, and Deploy

### Initial Setup

1. **Clone and Install:**
```bash
git clone https://github.com/nocobase/nocobase.git
cd nocobase
yarn install
```

2. **Environment Configuration:**
```bash
cp .env.example .env
# Edit .env with database credentials and settings
```

### Development Workflow

**Start Development Server:**
```bash
# Full stack development (client + server)
yarn dev

# Server only (for API development)
yarn dev-server
```

The development server provides:
- Hot module replacement for client code
- Auto-restart on server code changes
- TypeScript compilation on the fly
- Live database schema synchronization

**Running Tests:**
```bash
# Run all tests
yarn test

# Run specific test suites
yarn test:server          # Backend unit tests
yarn test:client          # Frontend unit tests
yarn e2e                  # E2E tests with Playwright

# With coverage
yarn test:server-coverage
yarn test:client-coverage
```

### Production Build Process

**1. Build All Packages:**
```bash
yarn build
```

This command:
- Compiles TypeScript for all packages
- Generates CommonJS output in `lib/`
- Generates ESM output in `es/`
- Creates type definition files (.d.ts)
- Bundles client-side code for browser

**2. Create Deployment Package:**
```bash
yarn tar
```

Creates `nocobase.tar.gz` containing:
- Compiled server code
- Bundled client assets
- Node modules for production
- Configuration templates

**3. Build Docker Image:**
```bash
# Development image
docker build -t nocobase:dev -f Dockerfile .

# Production image
docker build -t nocobase:latest -f Dockerfile.pro .
```

### Docker Deployment

**Using Docker Compose (Recommended):**
```bash
# Copy environment file
cp .env.example .env

# Edit .env with production settings
# Start services
docker-compose up -d
```

Docker Compose includes:
- NocoBase application
- PostgreSQL/MySQL database
- Redis for caching
- Adminer for database management (dev only)

**Using create-nocobase-app:**
```bash
npx create-nocobase-app my-app
cd my-app
yarn install
yarn nocobase install
yarn start
```

### Database Setup

**Initial Installation:**
```bash
# Sync database schema
yarn nocobase db:sync

# Install with initial data
yarn nocobase install
```

**Migrations:**
```bash
# Run migrations
yarn nocobase upgrade
```

### Plugin Development Build

**Create New Plugin:**
```bash
yarn nocobase create-plugin my-plugin
```

**Build Plugin:**
```bash
cd packages/plugins/@nocobase/plugin-my-plugin
yarn build
```

**Install Plugin in Development:**
```bash
yarn pm add @nocobase/plugin-my-plugin
yarn pm enable @nocobase/plugin-my-plugin
```

### CI/CD Integration

**GitHub Actions Workflow:**
The repository includes workflows for:
- Automated testing on PR
- Docker image building
- NPM package publishing
- Documentation deployment

**Pre-commit Hooks:**
```json
{
  "ghooks": {
    "pre-commit": "yarn lint-staged",
    "commit-msg": "commitlint --edit"
  }
}
```

### Environment Variables

Key environment variables for build/deployment:

```bash
# Application
APP_ENV=production
APP_PORT=13000
APP_KEY=your-secret-key

# Database
DB_DIALECT=postgres|mysql|sqlite
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=nocobase
DB_USER=nocobase
DB_PASSWORD=password

# Redis (optional)
REDIS_HOST=localhost
REDIS_PORT=6379

# Build Options
BUILD_NO_DTS=1              # Skip .d.ts generation
BUILD_CLEAN=1               # Clean before build
```

### Performance Optimization

**Production Optimizations:**
- Minification and tree-shaking for client bundles
- Gzip compression via Nginx
- Redis caching for frequently accessed data
- Connection pooling for databases
- Static asset CDN integration

**Build Optimization:**
```bash
# Parallel builds
yarn build --parallel

# Skip type checking (faster, less safe)
yarn build --no-dts

# Clean build
yarn clean && yarn build
```

### Troubleshooting

**Clear Build Cache:**
```bash
yarn clean
rm -rf node_modules
yarn install
yarn build
```

**Fix Lock File:**
```bash
yarn install --frozen-lockfile
```

**Rebuild Single Package:**
```bash
cd packages/core/server
yarn build
```

This build system is designed for both monorepo-wide operations and individual package development, supporting the plugin architecture while maintaining build performance and developer experience.
