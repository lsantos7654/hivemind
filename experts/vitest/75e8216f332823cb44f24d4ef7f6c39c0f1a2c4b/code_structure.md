# Vitest Code Structure

## Complete Annotated Directory Tree

```
vitest/
├── .github/                          # GitHub Actions workflows and templates
│   ├── workflows/                    # CI/CD pipelines for testing, building, releasing
│   ├── PULL_REQUEST_TEMPLATE.md      # PR template with contribution guidelines
│   └── commit-convention.md          # Commit message conventions
├── .vscode/                          # VS Code workspace configuration
│   ├── settings.json                 # Editor settings for consistent formatting
│   ├── extensions.json               # Recommended extensions for development
│   └── tasks.json                    # VS Code tasks for building and testing
├── docs/                             # Documentation website (Vite-powered)
│   ├── api/                          # API documentation for public interfaces
│   ├── config/                       # Configuration option documentation
│   ├── guide/                        # User guides and tutorials
│   └── vite.config.ts               # Documentation site build configuration
├── examples/                         # Example projects and integrations
│   ├── basic/                        # Simple Vitest setup examples
│   ├── react/                        # React component testing examples
│   ├── vue/                          # Vue component testing examples
│   └── [various framework examples]  # Additional framework integrations
├── packages/                         # Core monorepo packages
│   ├── vitest/                       # Main testing framework package
│   │   ├── src/                      # Source code for core functionality
│   │   │   ├── api/                  # WebSocket API and RPC interfaces
│   │   │   ├── node/                 # Node.js-specific functionality
│   │   │   │   ├── cli/              # Command-line interface implementation
│   │   │   │   ├── pools/            # Test execution pools (threads, forks, browser)
│   │   │   │   ├── reporters/        # Test result reporting and formatting
│   │   │   │   └── plugins/          # Vite plugin integration
│   │   │   ├── runtime/              # Test runtime and execution environment
│   │   │   │   ├── runners/          # Test and benchmark runners
│   │   │   │   └── moduleRunner/     # Module evaluation and loading
│   │   │   ├── types/                # TypeScript type definitions
│   │   │   ├── integrations/         # Third-party library integrations
│   │   │   └── public/               # Public API exports
│   │   ├── vitest.mjs               # CLI entry point executable
│   │   └── package.json             # Package configuration and dependencies
│   ├── browser/                      # Browser testing capabilities
│   │   ├── src/                      # Browser test implementation
│   │   └── context.js               # Browser context setup
│   ├── browser-playwright/           # Playwright browser automation
│   ├── browser-webdriverio/          # WebDriverIO browser automation
│   ├── coverage-v8/                  # V8 code coverage provider
│   ├── coverage-istanbul/            # Istanbul code coverage provider
│   ├── expect/                       # Assertion library (Chai-based)
│   ├── runner/                       # Core test runner functionality
│   ├── spy/                          # Mocking and spying utilities
│   ├── snapshot/                     # Snapshot testing implementation
│   ├── mocker/                       # Module mocking system
│   ├── utils/                        # Shared utility functions
│   ├── pretty-format/               # Test output formatting
│   ├── ui/                          # Web-based test result viewer
│   └── web-worker/                  # Web Worker test environment
├── test/                            # Comprehensive test suites
│   ├── core/                        # Core functionality tests
│   ├── browser/                     # Browser testing integration tests
│   ├── cli/                         # Command-line interface tests
│   ├── config/                      # Configuration parsing tests
│   ├── coverage-test/               # Code coverage functionality tests
│   ├── reporters/                   # Reporter implementation tests
│   └── workspaces/                  # Workspace configuration tests
├── scripts/                         # Build and development scripts
│   ├── release.ts                   # Automated release process
│   ├── build.ts                     # Package building utilities
│   └── [various utility scripts]   # Development and maintenance tools
├── patches/                         # Package patches for dependencies
├── package.json                     # Root workspace configuration
├── pnpm-workspace.yaml             # pnpm workspace definition
├── pnpm-lock.yaml                  # Dependency lock file
├── tsconfig.base.json              # Base TypeScript configuration
├── tsconfig.build.json             # Build-specific TypeScript settings
└── README.md                       # Project overview and quick start
```

## Module and Package Organization

### Core Framework Architecture

The Vitest monorepo follows a modular architecture where each package serves a specific purpose within the testing ecosystem:

**Primary Package** (`packages/vitest`): The main framework package that orchestrates all testing activities. It depends on other packages in the monorepo and provides the unified CLI interface and API that users interact with.

**Runtime Packages**: Core testing functionality is split into specialized packages:
- `@vitest/runner` - Test execution engine and task management
- `@vitest/expect` - Assertion library with Jest-compatible API
- `@vitest/spy` - Mocking, stubbing, and spying capabilities
- `@vitest/snapshot` - Snapshot testing implementation
- `@vitest/mocker` - Advanced module mocking system

**Browser Testing Ecosystem**: Browser testing capabilities are provided through multiple packages:
- `@vitest/browser` - Core browser testing functionality
- `@vitest/browser-playwright` - Playwright automation driver
- `@vitest/browser-webdriverio` - WebDriverIO automation driver
- `@vitest/browser-preview` - Browser preview functionality

**Coverage and Reporting**: Test result analysis and coverage collection:
- `@vitest/coverage-v8` - Native V8 coverage collection
- `@vitest/coverage-istanbul` - Istanbul coverage instrumentation
- `@vitest/ui` - Web-based test result visualization

## Main Source Directories and Their Purposes

### packages/vitest/src/ - Core Framework

**api/**: WebSocket-based communication between test processes and the main thread. Includes RPC interfaces for real-time test result streaming and remote test execution control.

**node/**: Node.js-specific functionality including the CLI implementation, configuration parsing, and test orchestration. Contains the main entry points for running tests in Node.js environments.

**runtime/**: Test execution environment and runtime utilities. Handles test module loading, evaluation, and execution within isolated contexts.

**types/**: Comprehensive TypeScript type definitions for all public and internal APIs. Ensures type safety across the entire framework.

**integrations/**: Third-party library integrations including Chai assertion library setup, Vi mocking utilities, and environment-specific adapters.

### packages/vitest/src/node/ - Node.js Implementation

**cli/**: Complete command-line interface implementation with CAC (Command And Conquer) integration. Handles argument parsing, command routing, and help text generation.

**pools/**: Test execution strategies including thread pools, child process pools, and browser pools. Each pool manages test isolation and parallel execution differently.

**reporters/**: Test result formatting and output generation. Includes built-in reporters (default, verbose, JSON) and interfaces for custom reporter development.

**plugins/**: Vite plugin integration that allows Vitest to leverage Vite's transformation pipeline, module resolution, and development server capabilities.

## Key Files and Their Roles

### Entry Points and CLI

- `packages/vitest/vitest.mjs` - Main CLI executable that bootstraps the framework
- `packages/vitest/src/node/cli.ts` - CLI implementation entry point
- `packages/vitest/src/node/cli/cac.ts` - Command-line argument parsing and command setup
- `packages/vitest/src/public/index.ts` - Primary public API exports

### Core Configuration

- `package.json` - Root workspace configuration with scripts and dependencies
- `pnpm-workspace.yaml` - Monorepo workspace definition and dependency management
- `tsconfig.base.json` - Base TypeScript configuration shared across packages
- `eslint.config.js` - Code quality and formatting rules

### Framework Core

- `packages/vitest/src/node/core.ts` - Main framework orchestration and lifecycle management
- `packages/vitest/src/runtime/runners/test.ts` - Test execution engine
- `packages/vitest/src/node/project.ts` - Project configuration and management
- `packages/vitest/src/node/pools/pool.ts` - Test execution pool abstraction

### API and Integration

- `packages/vitest/src/api/types.ts` - WebSocket API type definitions
- `packages/vitest/src/integrations/chai/index.ts` - Chai assertion library setup
- `packages/vitest/src/integrations/vi/index.ts` - Vi utility functions and mocking APIs

## Code Organization Patterns

### Monorepo Structure

The project uses a well-organized monorepo structure with clear separation of concerns. Each package has a specific responsibility and communicates through well-defined interfaces. Dependencies between packages are managed through workspace references, ensuring version consistency.

### TypeScript Organization

TypeScript types are organized hierarchically with shared base types in `types/` directories and package-specific types co-located with implementations. The build system uses rollup for bundling with TypeScript declaration generation.

### Plugin Architecture

The framework extensively uses a plugin architecture inherited from Vite. This allows for modular functionality where features can be added or removed through plugin configuration. The plugin system enables transformation pipelines, custom environments, and reporter extensions.

### Test Organization

Tests are organized by feature area and integration type. Core functionality tests are separated from integration tests, and browser-specific tests have their own dedicated directories. This organization allows for targeted test execution and easier maintenance.

### Configuration Patterns

Configuration follows a cascading pattern where base configurations are extended by more specific configurations. This enables shared settings across packages while allowing package-specific customizations for building, testing, and linting.
