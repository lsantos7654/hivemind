# Vitest Build System

## Build System Type and Configuration Files

Vitest uses a sophisticated multi-tool build system designed to handle the complexity of a modern JavaScript testing framework monorepo:

### Primary Build Tools

**Rollup**: The main bundling tool used for building the core packages. Each package uses Rollup for creating optimized ESM bundles with proper tree-shaking and code splitting. The configuration is defined in `packages/vitest/rollup.config.js`.

**pnpm Workspaces**: The monorepo is managed using pnpm workspaces defined in `pnpm-workspace.yaml`. This provides efficient dependency management with shared node_modules and cross-package linking through workspace references.

**TypeScript**: All source code is written in TypeScript with strict type checking enabled. Multiple TypeScript configurations handle different build scenarios:
- `tsconfig.base.json` - Base configuration shared across packages
- `tsconfig.build.json` - Build-specific settings for compilation
- `tsconfig.check.json` - Type checking configuration for CI

**Vite**: Used for the documentation website and development server functionality. The docs are built using Vite with special configuration in `docs/vite.config.ts`.

### Key Configuration Files

- `package.json` - Root workspace configuration with build scripts and dependency management
- `pnpm-workspace.yaml` - Workspace definition and package inclusion patterns
- `rollup.config.js` - Bundle configuration for the main vitest package with multiple entry points
- `eslint.config.js` - Code quality enforcement and formatting rules
- Various `tsconfig.*.json` files for TypeScript compilation in different contexts

## External Dependencies and Management

### Dependency Categories

**Core Runtime Dependencies**: Essential libraries required for framework functionality:
- `vite` (^6.0.0 || ^7.0.0 || ^8.0.0) - Primary build tool and transformation pipeline
- `@vitest/expect` - Assertion library with Jest-compatible API
- `@vitest/runner` - Test execution engine and task management
- `@vitest/spy` - Mocking and spying functionality
- `tinybench` - Benchmarking capabilities
- `magic-string` - Source code transformation utilities
- `pathe` - Cross-platform path utilities

**Development and Build Dependencies**:
- `rollup` and related plugins for bundling
- `typescript` for type checking and compilation
- `eslint` with `@antfu/eslint-config` for code quality
- `@playwright/test` for browser automation testing
- Various `@types/*` packages for TypeScript definitions

**Peer Dependencies**: Optional dependencies that users may provide:
- Browser automation tools (`@vitest/browser-playwright`, `@vitest/browser-webdriverio`)
- DOM environments (`jsdom`, `happy-dom`)
- Testing UI (`@vitest/ui`)
- Node.js types (`@types/node`)

### Dependency Management Strategy

**Workspace References**: Internal packages are linked using `workspace:*` references, ensuring version consistency and enabling local development without publishing.

**Version Constraints**: Strict version ranges are used for critical dependencies like Vite and Node.js to ensure compatibility and stability.

**Catalog System**: The `pnpm-workspace.yaml` includes a catalog system for managing shared dependency versions across packages, reducing duplication and ensuring consistency.

**Patches**: The `patches/` directory contains package patches for dependencies that need modifications, managed through pnpm's patching system.

## Build Targets and Commands

### Primary Build Scripts

**`pnpm build`**: Builds all packages in the correct dependency order using `pnpm -r --filter`. This command:
- Compiles TypeScript source to JavaScript
- Generates type declaration files
- Creates optimized bundles with Rollup
- Copies necessary assets and configurations

**`pnpm dev`**: Development mode with watch capability:
- Starts Rollup in watch mode for live rebuilding
- Enables source maps for debugging
- Uses parallel execution across packages
- Allocates increased memory (`--max-old-space-size=8192`)

**`pnpm typecheck`**: Comprehensive TypeScript type checking across the entire monorepo using the check configuration.

**`pnpm lint`**: Code quality enforcement using ESLint with automatic fixing capabilities via `pnpm lint:fix`.

### Specialized Build Commands

**Documentation**:
- `pnpm docs` - Development server for documentation
- `pnpm docs:build` - Static documentation site generation
- `pnpm docs:serve` - Serve built documentation locally

**UI Package**:
- `pnpm ui:build` - Build the web-based test result viewer
- `pnpm ui:dev` - Development mode for UI components

**Testing Infrastructure**:
- `pnpm test:ci` - Run all tests in CI environment
- `pnpm test:browser:playwright` - Browser-specific test execution
- `pnpm test:examples` - Validate example projects

### Package-Specific Build Configuration

Each package has its own build configuration tailored to its purpose:

**Main Vitest Package**: Uses a complex Rollup configuration with multiple entry points for different use cases (CLI, node, browser, workers). The build creates:
- ESM bundles for modern environments
- CommonJS bundles for compatibility
- TypeScript declaration files
- Separate worker bundles for performance

**Browser Packages**: Specialized builds for browser environments with different bundling strategies for Playwright and WebDriverIO integrations.

**Utility Packages**: Lightweight builds focused on tree-shaking and minimal bundle sizes.

## How to Build, Test, and Deploy

### Development Setup

1. **Initial Setup**:
   ```bash
   pnpm install          # Install all dependencies
   pnpm build            # Build all packages
   ```

2. **Playwright Setup** (for browser testing):
   ```bash
   npx playwright install --with-deps
   ```

### Development Workflow

1. **Development Mode**:
   ```bash
   pnpm dev              # Watch mode for all packages
   ```

2. **Testing**:
   ```bash
   CI=true pnpm test:ci  # Run full test suite
   pnpm test basic.test.ts -t 'specific test'  # Run specific tests
   ```

3. **Code Quality**:
   ```bash
   pnpm lint:fix         # Fix linting issues automatically
   pnpm typecheck       # Verify TypeScript types
   ```

### Build Verification

**Complete Build**: The full build process includes:
- TypeScript compilation with strict type checking
- ESLint validation and automatic fixing
- Rollup bundling with tree-shaking optimization
- License generation and third-party attribution
- Type declaration file generation

**Build Artifacts**: Successful builds produce:
- `dist/` directories in each package with compiled JavaScript
- `.d.ts` files for TypeScript consumers
- Source maps for debugging
- License files with dependency attribution

### Deployment Process

**Release Preparation**:
- Version bumping with `bumpp`
- Changelog generation with `changelogithub`
- Comprehensive testing across all environments
- Documentation updates and verification

**Publishing**: The release process uses automated scripts in `scripts/release.ts` that handle:
- Package building and verification
- NPM publishing with proper tagging
- GitHub release creation
- Documentation deployment

The build system is designed for reliability and performance, supporting both local development and automated CI/CD pipelines with extensive validation and error handling.
