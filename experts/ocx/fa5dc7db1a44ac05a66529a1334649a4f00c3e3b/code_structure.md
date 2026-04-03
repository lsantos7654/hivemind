# OCX Code Structure and Organization

## Complete Annotated Directory Tree

```
ocx/
├── .git/                           # Git repository metadata
├── .github/                        # GitHub workflows and issue templates
│   └── workflows/
│       └── ci.yml                  # Continuous integration pipeline
├── .gitignore                      # Git ignore patterns
├── .husky/                         # Git hooks for pre-commit validation
├── AGENTS.md                       # Agent system documentation
├── assets/                         # Static assets (images, demos)
│   └── profiles-demo.gif          # Profile system demonstration
├── biome.json                      # Biome configuration for linting/formatting
├── bun.lock                        # Bun lockfile for dependency versions
├── cliff.toml                      # Git cliff configuration for changelog generation
├── commitlint.config.ts           # Commit message linting configuration
├── context7.json                   # Context configuration (likely for AI tools)
├── CONTRIBUTING.md                 # Contributor guidelines and development setup
├── docs/                           # Complete documentation site
│   ├── cli/                       # CLI command documentation
│   ├── docs.json                  # Documentation metadata
│   ├── enterprise/                # Enterprise feature documentation
│   ├── favicon.svg                # Site favicon
│   ├── getting-started/           # Onboarding guides
│   ├── guides/                    # Step-by-step tutorials
│   ├── integrations/              # Integration examples and patterns
│   ├── logo/                      # Brand assets and logos
│   ├── maintainers/               # Maintainer documentation
│   ├── MANUAL_TESTING.md          # Manual testing procedures
│   ├── migration/                 # Version migration guides
│   ├── profiles/                  # Profile system documentation
│   ├── reference/                 # API and configuration reference
│   ├── registries/                # Registry creation and management
│   ├── schemas/                   # JSON schema definitions
│   └── security/                  # Security model and best practices
├── examples/                       # Example implementations and templates
│   └── registry-starter/          # Template for creating new registries
├── facades/                        # Facade patterns for API abstraction
├── LICENSE                         # MIT license
├── package.json                    # Root workspace configuration
├── packages/                       # Main source packages
│   └── cli/                       # CLI package (primary implementation)
│       ├── .npmignore             # npm publish ignore patterns
│       ├── .opencode/             # OpenCode configuration for CLI development
│       ├── bunfig.toml           # Bun-specific configuration
│       ├── package.json           # CLI package dependencies and scripts
│       ├── scripts/               # Build and utility scripts
│       │   ├── build.ts          # Main build script
│       │   ├── build-binary.ts   # Binary compilation script
│       │   └── serve-legacy-fixture.ts # Test fixture server
│       ├── src/                   # TypeScript source code
│       │   ├── commands/          # CLI command implementations
│       │   │   ├── add.ts        # Component installation command
│       │   │   ├── build.ts      # Registry build command
│       │   │   ├── config/       # Configuration management commands
│       │   │   ├── init.ts       # Project initialization
│       │   │   ├── migrate/      # Version migration commands
│       │   │   ├── opencode-overlay.ts # OpenCode integration layer
│       │   │   ├── opencode.ts   # OpenCode launcher command
│       │   │   ├── profile/      # Profile management commands
│       │   │   │   ├── add.ts    # Profile creation
│       │   │   │   ├── index.ts  # Profile command registration
│       │   │   │   ├── install-from-registry.ts # Registry-based profile installation
│       │   │   │   ├── list.ts   # Profile listing
│       │   │   │   ├── move.ts   # Profile renaming/moving
│       │   │   │   ├── remove.ts # Profile deletion
│       │   │   │   └── show.ts   # Profile inspection
│       │   │   ├── registry.ts   # Registry management
│       │   │   ├── remove.ts     # Component removal
│       │   │   ├── search.ts     # Component search
│       │   │   ├── self/         # CLI self-management commands
│       │   │   ├── update.ts     # Component updates
│       │   │   ├── validate.ts   # Validation utilities
│       │   │   └── verify.ts     # Integrity verification
│       │   ├── config/           # Configuration system
│       │   │   ├── index.ts      # Configuration exports
│       │   │   ├── provider.ts   # Configuration provider abstraction
│       │   │   └── resolver.ts   # Configuration resolution logic
│       │   ├── constants.ts      # System constants and defaults
│       │   ├── index.ts          # Main CLI entry point
│       │   ├── lib/              # Core library functions
│       │   │   ├── build-registry.ts # Registry compilation
│       │   │   ├── index.ts      # Library exports
│       │   │   ├── validation-runner.ts # Validation orchestration
│       │   │   └── validators.ts # Validation implementations
│       │   ├── profile/          # Profile system implementation
│       │   │   ├── atomic.ts     # Atomic operations for profiles
│       │   │   ├── manager.ts    # Profile lifecycle management
│       │   │   ├── paths.ts      # Profile path resolution
│       │   │   └── schema.ts     # Profile configuration schema
│       │   ├── registry/         # Registry system implementation
│       │   │   ├── fetcher.ts    # Registry content fetching
│       │   │   ├── index.ts      # Registry exports
│       │   │   ├── merge.ts      # Registry merging logic
│       │   │   └── resolver.ts   # Dependency resolution
│       │   ├── schemas/          # Zod schema definitions
│       │   │   ├── common.ts     # Shared schema patterns
│       │   │   ├── config.ts     # Configuration schemas
│       │   │   ├── index.ts      # Schema exports
│       │   │   ├── ocx.ts        # OCX-specific schemas
│       │   │   └── registry.ts   # Registry and component schemas
│       │   ├── self-update/      # CLI self-update system
│       │   │   ├── check.ts      # Update availability checking
│       │   │   ├── detect-method.ts # Installation method detection
│       │   │   ├── download.ts   # Update download logic
│       │   │   ├── index.ts      # Self-update exports
│       │   │   ├── notify.ts     # Update notifications
│       │   │   ├── types.ts      # Self-update type definitions
│       │   │   ├── verify.ts     # Update verification
│       │   │   └── version-provider.ts # Version resolution
│       │   ├── updaters/         # Configuration update utilities
│       │   │   └── update-opencode-config.ts # OpenCode config management
│       │   └── utils/            # Utility functions and helpers
│       │       ├── content.ts    # Content comparison utilities
│       │       ├── dep-invalidation.ts # Dependency cache management
│       │       ├── dry-run.ts    # Dry-run operation support
│       │       ├── errors.ts     # Error type definitions
│       │       ├── git-root.ts   # Git repository detection
│       │       ├── index.ts      # Utility exports
│       │       ├── json-output.ts # JSON output formatting
│       │       ├── logger.ts     # Logging utilities
│       │       ├── npm-registry.ts # npm integration
│       │       ├── path-security.ts # Path validation and security
│       │       ├── paths.ts      # Path resolution utilities
│       │       ├── planned-writes.ts # Write operation planning
│       │       ├── receipt.ts    # Receipt management
│       │       ├── shared-options.ts # CLI option definitions
│       │       ├── terminal-title.ts # Terminal title management
│       │       ├── type-guards.ts # TypeScript type guards
│       │       └── url.ts        # URL utilities
│       ├── tests/                # Comprehensive test suite
│       │   ├── [numerous test files] # Unit and integration tests
│       │   ├── fixture.ts        # Test fixture utilities
│       │   ├── mock-registry.ts  # Registry mocking
│       │   └── preload.ts        # Test environment setup
│       └── tsconfig.json         # TypeScript configuration
├── README.md                       # Project documentation and quick start
├── scripts/                        # Project-level scripts
├── SECURITY.md                     # Security policy and reporting
├── tsconfig.json                   # Root TypeScript configuration
├── turbo.json                      # Turborepo configuration
└── workers/                        # Cloudflare Workers for registry hosting
    ├── kdco-registry/             # KDCO registry implementation
    ├── ocx/                       # Core OCX worker
    │   ├── src/
    │   │   ├── index.ts          # Worker entry point
    │   │   └── index.test.ts     # Worker tests
    │   └── worker-configuration.d.ts # Worker type definitions
    └── ocx-kit/                   # OCX worker utilities
        └── scripts/
            └── build.ts          # Worker build script
```

## Module and Package Organization

### Primary Package: packages/cli
The CLI package contains the entire OCX implementation, organized into clear functional modules:

**Command Layer (`src/commands/`)**
- Each command follows a consistent registration pattern
- Commands are grouped by functionality (profile, config, self-management)
- Shared options and error handling across all commands
- Clear separation between CLI concerns and business logic

**Configuration System (`src/config/`)**
- Provider abstraction enables local, global, and profile modes
- Resolver handles complex configuration inheritance and merging
- Type-safe configuration parsing with Zod schemas

**Registry System (`src/registry/`)**
- Fetcher handles HTTP communication with registries
- Resolver implements Cargo-style dependency resolution
- Merge utilities handle configuration composition

**Profile Management (`src/profile/`)**
- Atomic operations ensure consistency during profile modifications
- Path resolution abstracts profile directory structures
- Manager handles full profile lifecycle

**Schema Definitions (`src/schemas/`)**
- Comprehensive Zod schemas for all data structures
- Cargo-style union types (string shortcuts or full objects)
- Runtime validation at system boundaries

### Secondary Packages: workers/
Cloudflare Workers provide registry hosting infrastructure:

**Core Worker (`workers/ocx/`)**
- Handles registry index serving
- Component manifest delivery
- Discovery endpoint implementation

**Utility Kit (`workers/ocx-kit/`)**
- Shared utilities across workers
- Build tooling for worker deployment

## Main Source Directories and Their Purposes

### `/src/commands/` - CLI Command Implementation
Contains all user-facing command implementations following a consistent pattern:
- Command registration with Commander.js
- Option parsing and validation
- Business logic delegation to core modules
- Error handling and user feedback

Key commands include:
- `add`: Component installation with conflict resolution
- `profile`: Complete profile management suite
- `build`: Registry compilation and validation
- `migrate`: Version upgrade automation

### `/src/lib/` - Core Business Logic
Pure functions implementing OCX's core functionality:
- `build-registry.ts`: Registry compilation from source
- `validation-runner.ts`: Orchestrates validation across the system
- `validators.ts`: Specific validation implementations

### `/src/utils/` - Shared Utilities
Cross-cutting concerns used throughout the system:
- Security: Path validation, content verification
- File operations: Atomic writes, dry-run support
- Error handling: Structured error types with context
- Output formatting: Human-readable and JSON modes

### `/src/schemas/` - Type System Foundation
Zod-based schemas that define the entire OCX data model:
- Registry schemas with component manifests
- Configuration schemas for all modes
- Validation schemas with detailed error messages

## Key Files and Their Roles

### Core Entry Points
- **`src/index.ts`**: Main CLI entry point with command registration
- **`src/constants.ts`**: System-wide constants and configuration values
- **Package.json files**: Dependency management and build scripts

### Critical Implementation Files
- **`src/commands/add.ts`**: Complex component installation with atomic transactions
- **`src/registry/resolver.ts`**: Dependency resolution algorithm
- **`src/profile/manager.ts`**: Profile lifecycle management with atomic operations
- **`src/schemas/registry.ts`**: Complete registry and component schema definitions
- **`src/utils/path-security.ts`**: Security validation preventing directory traversal

### Configuration and Build
- **`turbo.json`**: Monorepo task orchestration
- **`biome.json`**: Code quality and formatting rules
- **`tsconfig.json`**: TypeScript compilation settings
- **CLI `scripts/`**: Build automation and binary compilation

## Code Organization Patterns

### Architectural Principles
1. **Schema-Driven Development**: Zod schemas define boundaries and contracts
2. **Provider Pattern**: Abstract different configuration sources uniformly
3. **Atomic Operations**: File operations support rollback for consistency
4. **Command Registration**: Consistent pattern for CLI command structure
5. **Error-First Design**: Comprehensive error types with actionable messages

### Dependency Flow
```
CLI Commands → Core Libraries → Utilities ← Schemas
     ↓              ↓              ↓         ↑
Configuration → Registry → File System ← Validation
```

### Module Boundaries
- Commands handle user interaction and orchestration
- Libraries implement pure business logic
- Utilities provide cross-cutting concerns
- Schemas enforce contracts at boundaries

### Testing Strategy
Comprehensive test coverage with:
- Unit tests for individual functions
- Integration tests for command workflows
- Mock registries for testing registry interactions
- Fixture-based testing for file operations

The codebase emphasizes maintainability through clear separation of concerns, comprehensive type safety, and extensive documentation. Each module has a focused responsibility with well-defined interfaces to other modules.
