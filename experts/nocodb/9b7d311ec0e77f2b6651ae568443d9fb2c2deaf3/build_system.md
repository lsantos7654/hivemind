# NocoDB Build System

## Build System Type and Configuration Files

NocoDB uses a sophisticated monorepo build system combining multiple modern tools:

**Primary Build Tools:**
- **pnpm Workspaces**: Monorepo package management
- **Rspack**: High-performance bundler for backend (webpack successor)
- **Nuxt 3/Vite**: Frontend build system with Vite under the hood
- **TypeScript**: Type-safe compilation across all packages
- **Lerna**: Additional monorepo coordination (v8.2.2)

**Key Configuration Files:**

Root Level:
- `pnpm-workspace.yaml` - Workspace package definitions
- `pnpm-lock.yaml` - Dependency lock file
- `lerna.json` - Lerna monorepo configuration
- `package.json` - Root package scripts and dev dependencies

Backend (packages/nocodb/):
- `rspack.config.js` - Production build configuration
- `rspack.dev.config.js` - Development build with watch mode
- `rspack.cli.config.js` - CLI module build configuration
- `docker/rspack.config.js` - Docker-specific build
- `tsconfig.json` - TypeScript compiler options
- `Dockerfile` - Multi-stage Docker build

Frontend (packages/nc-gui/):
- `nuxt.config.ts` - Nuxt 3 configuration with Vite
- `tsconfig.json` - TypeScript configuration
- `windi.config.ts` - WindiCSS configuration
- `vite.config.ts` - Vite-specific settings (if overrides needed)

SDK (packages/nocodb-sdk/):
- `tsconfig.json` - Main TypeScript config
- `tsconfig.module.json` - ES module build config
- `build-script/mergeAndGenerateSwaggerCE` - Swagger generation script

## External Dependencies and Management

**Dependency Management Strategy:**

1. **Workspace Protocol**: Internal packages reference each other via `workspace:^`
2. **Version Pinning**: Critical dependencies pinned to specific versions
3. **Security Overrides**: pnpm overrides for vulnerability patches
4. **Hoisted Dependencies**: Strategic hoisting for shared dependencies

**Major External Dependencies:**

Backend Core:
```json
{
  "@nestjs/core": "^10.4.19",
  "@nestjs/common": "^10.4.19",
  "@nestjs/platform-express": "^10.4.19",
  "express": "^4.21.2",
  "knex": "3.1.0",
  "mysql2": "^3.14.1",
  "pg": "^8.13.1",
  "sqlite3": "^5.1.7"
}
```

Database Clients:
```json
{
  "@clickhouse/client": "^1.11.1",
  "@databricks/sql": "^1.11.0",
  "snowflake-sdk": "^2.1.0"
}
```

AI Services:
```json
{
  "@ai-sdk/openai": "^3.0.1",
  "@ai-sdk/anthropic": "^3.0.1",
  "@ai-sdk/google": "^3.0.1",
  "@ai-sdk/amazon-bedrock": "^4.0.3",
  "openai": "^5.8.2",
  "ai": "^6.0.3"
}
```

Cloud Services:
```json
{
  "@aws-sdk/client-s3": "^3.743.0",
  "@aws-sdk/client-ses": "^3.743.0",
  "@google-cloud/storage": "^7.15.0",
  "minio": "^8.0.4"
}
```

Job Processing:
```json
{
  "bull": "^4.16.5",
  "@nestjs/bull": "^10.2.3",
  "ioredis": "5.6.1"
}
```

Frontend Core:
```json
{
  "vue": "3.5.14",
  "nuxt": "3.17.4",
  "@pinia/nuxt": "^0.5.5",
  "ant-design-vue": "^3.2.20"
}
```

Rich Text & Editors:
```json
{
  "@tiptap/vue-3": "^2.11.5",
  "monaco-editor": "^0.52.2",
  "markdown-it": "^14.1.0"
}
```

Visualization:
```json
{
  "echarts": "^5.6.0",
  "@vue-flow/core": "^1.47.0",
  "leaflet": "^1.9.4"
}
```

**pnpm Override Strategy:**
The root package.json includes extensive security overrides to patch vulnerabilities:
```json
{
  "pnpm": {
    "overrides": {
      "axios@>=0.8.1 <0.28.0": ">=0.28.0",
      "vue@*": "3.5.14",
      "typescript": "5.8.3",
      "ws@<8.17.1": ">=8.17.1",
      "knex@<3.1.0": ">=3.1.0"
    }
  }
}
```

**Node.js Version Requirements:**
- Backend (nocodb): Node.js >= 22
- Frontend (nc-gui): Node.js >= 18
- SDK (nocodb-sdk): Node.js >= 18

## Build Targets and Commands

### Root Level Commands

**Bootstrap/Setup:**
```bash
pnpm bootstrap
# Installs and builds SDK, then installs all packages and builds integrations
```

**Package Management:**
```bash
pnpm install              # Install all workspace dependencies
pnpm preinstall           # Enforces pnpm usage (runs automatically)
```

**Development:**
```bash
pnpm start:frontend       # Start frontend dev server
pnpm start:backend        # Start backend dev server
```

**Database Testing:**
```bash
pnpm start:mysql          # Start MySQL test container
pnpm stop:mysql           # Stop MySQL test container
pnpm start:pg             # Start PostgreSQL test container
pnpm stop:pg              # Stop PostgreSQL test container
```

**Integration Management:**
```bash
pnpm integrations:build   # Build integration packages
pnpm registerIntegrations # Register integrations with backend
```

### Backend (nocodb) Commands

**Development:**
```bash
pnpm start                # Start dev server with watch mode
pnpm watch:run            # Start with hot reload (SQLite)
pnpm watch:run:mysql      # Start with hot reload (MySQL)
pnpm watch:run:pg         # Start with hot reload (PostgreSQL)
pnpm watch:run:playwright # Start for Playwright testing
```

**Production Build:**
```bash
pnpm build                # Production build (calls docker:build)
pnpm docker:build         # Build with rspack for Docker
pnpm build:obfuscate      # Build with code obfuscation (EE)
pnpm build:cli:module     # Build CLI module separately
```

**Testing:**
```bash
pnpm test                 # Run Jest tests
pnpm test:unit            # Run unit tests with Mocha
pnpm test:unit:pg         # Run unit tests with PostgreSQL
pnpm test:watch           # Watch mode testing
pnpm test:cov             # Generate coverage report
pnpm test:e2e             # Run end-to-end tests
```

**Code Quality:**
```bash
pnpm lint                 # Run ESLint with auto-fix
pnpm format               # Format code with Prettier
```

**Integration Registration:**
```bash
pnpm registerIntegrations # Register integrations from noco-integrations
```

### Frontend (nc-gui) Commands

**Development:**
```bash
pnpm dev                  # Start Nuxt dev server with HMR
```

**Production Build:**
```bash
pnpm build                # Build for production (SSR)
pnpm generate             # Generate static site (SSG)
pnpm start                # Start production server
```

**Library Build:**
```bash
pnpm build:copy           # Build and copy to nc-lib-gui
pnpm build:copy:publish   # Build, copy, and publish nc-lib-gui
```

**Testing:**
```bash
pnpm test                 # Run Vitest tests
pnpm test:ui              # Run tests with UI
pnpm coverage             # Generate coverage report
```

**Code Quality:**
```bash
pnpm lint                 # Run ESLint with auto-fix
```

**CI/CD:**
```bash
pnpm ci:run               # Install, build, and start for CI
pnpm ci:start             # Start production server for CI
```

### SDK (nocodb-sdk) Commands

**Build:**
```bash
pnpm build                # Clean, generate SDK, and build
pnpm build:main           # Build CommonJS output
pnpm build:module         # Build ES module output
pnpm generate:sdk         # Generate from Swagger and build
```

**Development:**
```bash
pnpm watch:build          # Watch mode compilation
```

**Testing:**
```bash
pnpm test                 # Run all tests
pnpm test:unit            # Run unit tests
pnpm test:lint            # Check code style
pnpm test:prettier        # Check formatting
pnpm test:spelling        # Check spelling
```

**Code Quality:**
```bash
pnpm fix                  # Fix all issues
pnpm fix:prettier         # Format with Prettier
pnpm fix:lint             # Fix ESLint issues
```

### Integration Framework (noco-integrations) Commands

**Build:**
```bash
pnpm build                # Build all integration packages
pnpm test                 # Run tests for all integrations
pnpm test:coverage        # Generate test coverage
```

### Playwright Tests Commands

**Test Execution:**
```bash
pnpm test                 # Run all Playwright tests
pnpm test:debug           # Run tests in debug mode
```

**Linting:**
```bash
pnpm lint:staged:playwright # Lint staged files
```

## How to Build, Test, and Deploy

### Initial Setup

1. **Prerequisites:**
   ```bash
   # Install Node.js 22+ and pnpm
   npm install -g pnpm@9.15.4
   ```

2. **Clone and Bootstrap:**
   ```bash
   git clone https://github.com/nocodb/nocodb.git
   cd nocodb
   pnpm bootstrap
   ```

### Development Workflow

**Full Stack Development:**
```bash
# Terminal 1: Backend
cd packages/nocodb
pnpm watch:run

# Terminal 2: Frontend
cd packages/nc-gui
pnpm dev

# Access at: http://localhost:3000
# Backend API at: http://localhost:8080
```

**Backend-Only Development:**
```bash
cd packages/nocodb
pnpm watch:run              # SQLite
# or
pnpm watch:run:mysql        # MySQL
# or
pnpm watch:run:pg           # PostgreSQL
```

**Frontend-Only Development:**
```bash
cd packages/nc-gui
pnpm dev
# Set NUXT_PUBLIC_NC_BACKEND_URL to point to existing backend
```

**SDK Development:**
```bash
cd packages/nocodb-sdk
pnpm watch:build
```

### Testing

**Backend Tests:**
```bash
cd packages/nocodb
pnpm test:unit              # Unit tests
pnpm test                   # Integration tests
```

**Frontend Tests:**
```bash
cd packages/nc-gui
pnpm test                   # Component tests
pnpm coverage               # With coverage
```

**End-to-End Tests:**
```bash
cd tests/playwright

# Setup test databases
cd ../.. && pnpm start:mysql && cd tests/playwright
# or
cd ../.. && pnpm start:pg && cd tests/playwright

# Run tests
pnpm test
```

### Production Build

**Complete Production Build:**
```bash
# From root
pnpm bootstrap              # Ensure all packages built
cd packages/nocodb
pnpm docker:build           # Build backend
cd ../nc-gui
pnpm generate               # Build frontend static files
```

**Docker Build:**
```bash
# From root directory
docker build -f packages/nocodb/Dockerfile -t nocodb/nocodb:custom .
```

The Dockerfile uses multi-stage builds:
1. **Litestream Builder**: Compiles Litestream for SQLite replication
2. **Node Builder**: Installs dependencies and builds application
3. **Runner**: Final slim image with runtime only

**Environment Configuration:**
Key environment variables:
- `NC_DB`: Database connection string
- `NC_AUTH_JWT_SECRET`: JWT secret for authentication
- `NC_PUBLIC_URL`: Public URL for the application
- `NC_DISABLE_TELE`: Disable telemetry
- `PORT`: Server port (default: 8080)

### Deployment Options

**1. Docker (Recommended):**
```bash
docker run -d \
  --name nocodb \
  -v "$(pwd)"/nocodb:/usr/app/data/ \
  -p 8080:8080 \
  nocodb/nocodb:latest
```

**2. Docker Compose:**
```bash
cd docker-compose/2_pg
docker-compose up -d
```

**3. Auto-Upstall (Production):**
```bash
bash <(curl -sSL http://install.nocodb.com/noco.sh) <(mktemp)
# Includes: PostgreSQL, Redis, MinIO, Traefik, SSL
```

**4. Kubernetes:**
```bash
helm install nocodb ./charts/nocodb
```

**5. Native Binary:**
```bash
# Download platform-specific binary
curl http://get.nocodb.com/linux-x64 -o nocodb -L
chmod +x nocodb
./nocodb
```

### Build Optimization

**Backend Optimizations:**
- Rspack for fast bundling (faster than webpack)
- Code splitting for better loading
- Tree shaking to remove unused code
- Optional code obfuscation for EE builds
- Modclean to reduce node_modules size in Docker

**Frontend Optimizations:**
- Vite for fast development and HMR
- Static site generation for faster loading
- Component lazy loading
- Icon purging to reduce bundle size
- CDN support for assets
- Bundle size optimization with tree shaking

**Docker Optimizations:**
- Multi-stage builds reduce final image size
- Node modules cleaned with modclean
- SQLite deps removed (unnecessary in production)
- Hoisted node_modules for better layer caching
- Slim base images (node:22-slim)

### CI/CD Integration

The project uses GitHub Actions for CI/CD with workflows in `.github/workflows/`. Key workflows:
- Pull request validation
- Unit and integration testing
- Docker image building and publishing
- Release automation
- Security scanning

**Git Workflow:**
- Development branch: `develop`
- Feature branches: `feat/*`, `fix/*`, `enhancement/*`
- All PRs merge to `develop`
- `master` contains stable releases only
- Follows Gitflow design pattern
