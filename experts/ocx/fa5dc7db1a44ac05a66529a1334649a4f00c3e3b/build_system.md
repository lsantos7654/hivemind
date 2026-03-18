# OCX Build System and Configuration

## Build System Type and Configuration Files

### Turborepo Monorepo Architecture
OCX uses Turborepo as its primary build orchestration system, configured via `turbo.json`:

```json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**"]
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "check": {},
    "test": {
      "dependsOn": ["^build"]
    }
  }
}
```

**Key Build Features:**
- **Dependency-aware builds**: `^build` ensures dependencies build before dependents
- **Output caching**: `dist/**` outputs are cached for faster subsequent builds
- **Development mode**: Persistent dev servers with cache disabled
- **Test orchestration**: Tests run after build completion

### Package Manager: Bun
OCX leverages Bun as both runtime and package manager (specified in `package.json`):
- **Version**: `bun@1.3.5` via `packageManager` field
- **Runtime requirements**: Node.js 18+ for compatibility
- **Lockfile**: `bun.lock` ensures reproducible installs
- **Performance**: Significantly faster than npm/yarn for most operations

### TypeScript Configuration
Multi-level TypeScript configuration with inheritance:

**Root `tsconfig.json`:**
- Base configuration for the entire monorepo
- Shared compiler options and path mappings

**Package-level `tsconfig.json` (packages/cli/):**
- Inherits from root configuration
- Package-specific compilation settings
- Module resolution for CLI-specific imports

### Code Quality Tools

#### Biome (Linting and Formatting)
Configured via `biome.json` for ultra-fast code quality:
- **Linting**: ESLint-compatible rules with better performance
- **Formatting**: Prettier-compatible with faster execution
- **Integration**: Works with editors and CI/CD pipelines
- **Script**: `bun run format` applies formatting automatically

#### Commit Quality
- **Commitlint**: Enforces conventional commit format via `commitlint.config.ts`
- **Husky**: Git hooks in `.husky/` directory for pre-commit validation
- **Cliff**: Changelog generation configured in `cliff.toml`

## External Dependencies and Management

### Runtime Dependencies (CLI Package)
**Core Framework Dependencies:**
```json
{
  "commander": "^14.0.0",        // CLI framework and argument parsing
  "zod": "^3.24.0",              // Schema validation and type safety
  "jsonc-parser": "3.3.1",      // JSON with comments support
  "kleur": "^4.1.5",            // Terminal colors and styling
  "ora": "^8.2.0"               // Spinner and progress indicators
}
```

**File System and Utility Dependencies:**
```json
{
  "chokidar": "^5.0.0",         // File system watching
  "ignore": "^7.0.5",           // .gitignore-style pattern matching
  "diff": "^8.0.0",             // Text diffing utilities
  "fuzzysort": "^3.1.0",        // Fuzzy search implementation
  "remeda": "^2.33.0"           // Functional utility library
}
```

**Key Dependency Choices:**
- **Commander**: Industry-standard CLI framework with excellent TypeScript support
- **Zod**: Runtime validation that generates TypeScript types automatically
- **JSONC-Parser**: Enables user-friendly configuration files with comments
- **Ora**: Professional terminal UI with spinner animations

### Development Dependencies
```json
{
  "@biomejs/biome": "^2.3.15",        // Fast linting and formatting
  "@commitlint/cli": "^19.8.1",       // Commit message validation
  "husky": "^9.1.7",                  // Git hooks management
  "turbo": "^2.8.7",                  // Monorepo build orchestration
  "typescript": "^5.9.3",             // TypeScript compiler
  "wrangler": "^4.65.0",              // Cloudflare Workers deployment
  "pkg-pr-new": "0.0.65"              // PR-based package publishing
}
```

### Dependency Management Strategy

#### Version Pinning Policy
- **Exact versions** for critical dependencies (jsonc-parser: `3.3.1`)
- **Caret ranges** for most dependencies (`^major.minor.patch`)
- **Careful major version management** to avoid breaking changes

#### Security and Supply Chain
- **Minimal dependency surface**: Only essential packages included
- **Regular updates**: Automated dependency updates via bots
- **Vulnerability scanning**: Integrated into CI/CD pipeline
- **License compliance**: MIT-compatible dependencies only

## Build Targets and Commands

### Primary Build Commands

#### Development Workflow
```bash
# Start development mode (file watching, hot reload)
bun run dev           # Turborepo orchestrates dev servers

# Code quality checks
bun run check         # Biome linting + TypeScript checking
bun run format        # Auto-format code with Biome

# Testing
bun run test          # Run test suite across all packages
```

#### Production Builds
```bash
# Build all packages
bun run build         # Turborepo builds with dependency resolution

# CLI-specific builds
cd packages/cli
bun run build         # Compile TypeScript to dist/
bun run build:binary  # Create standalone binary executable
```

### CLI Package Build Process

#### Standard Build (`packages/cli/scripts/build.ts`)
1. **TypeScript Compilation**: Source code compiled to JavaScript
2. **Bundle Optimization**: Tree-shaking and dead code elimination
3. **Version Injection**: `__VERSION__` constant injected at build time
4. **Output Generation**: Single `dist/index.js` with source maps

#### Binary Build (`packages/cli/scripts/build-binary.ts`)
1. **Bun Compilation**: Creates native executable with embedded runtime
2. **Cross-platform Support**: Generates binaries for macOS, Linux, Windows
3. **Distribution Packaging**: Prepares for GitHub releases and npm publishing

### Workers Build System
Cloudflare Workers have specialized build requirements:

```bash
# Worker development
cd workers/ocx
wrangler dev          # Local development server

# Worker deployment
wrangler deploy       # Deploy to Cloudflare edge
```

## How to Build, Test, and Deploy

### Initial Setup
```bash
# Clone repository
git clone https://github.com/kdcokenny/ocx.git
cd ocx

# Install dependencies (uses Bun)
bun install

# Verify setup
bun run check
```

### Development Workflow
```bash
# Start development environment
bun run dev                    # All packages in watch mode

# Make changes to CLI
cd packages/cli
bun run dev                    # CLI-specific development

# Run tests during development
bun run test                   # Full test suite
bun test packages/cli          # Package-specific tests
```

### Quality Assurance
```bash
# Code quality checks
bun run format                 # Auto-format all code
bun run check                  # Lint and type check

# Pre-commit validation (automatic via Husky)
git commit -m "feat: new feature"  # Triggers commitlint + quality checks
```

### Testing Strategy
```bash
# Unit tests
bun test packages/cli/tests/   # Individual function tests

# Integration tests  
bun test packages/cli/tests/   # Command workflow tests

# Registry tests
bun test packages/cli/tests/registry*.test.ts  # Registry interaction tests

# Manual testing
# See docs/MANUAL_TESTING.md for comprehensive test procedures
```

### Production Deployment

#### CLI Package Release
```bash
# Prepare release
bun run build                  # Build all packages
cd packages/cli
bun run prepublishOnly        # Pre-publish validation

# Publish to npm (automated via GitHub Actions)
npm publish                   # Requires appropriate permissions

# Create GitHub release with binaries
bun run build:binary          # Generate platform binaries
# Upload binaries to GitHub releases
```

#### Worker Deployment
```bash
# Deploy registry workers
cd workers/kdco-registry
wrangler deploy               # Deploy to Cloudflare

cd workers/ocx
wrangler deploy               # Deploy core worker
```

### CI/CD Pipeline
The GitHub Actions workflow (`.github/workflows/ci.yml`) handles:

1. **Quality Gates**:
   - Code formatting validation
   - TypeScript type checking  
   - Comprehensive test suite execution
   - Dependency vulnerability scanning

2. **Build Verification**:
   - Multi-platform build testing
   - Binary compilation validation
   - Package integrity verification

3. **Automated Publishing**:
   - npm package publishing on releases
   - GitHub release creation with binaries
   - Documentation site deployment

### Local Binary Testing
```bash
# Build local binary for testing
cd packages/cli
bun run build:binary

# Test binary directly
./dist/ocx --version
./dist/ocx --help

# Install locally for testing
npm install -g ./dist/ocx-*.tgz
```

### Performance Optimization
- **Bun Runtime**: 2-10x faster than Node.js for most operations
- **Turborepo Caching**: Build artifacts cached across runs
- **Incremental Compilation**: TypeScript incremental mode enabled
- **Bundle Analysis**: Regular analysis of bundle size and dependencies

The build system emphasizes developer productivity through fast feedback loops, comprehensive automation, and reliable deployment processes. The combination of Bun, Turborepo, and modern tooling creates an efficient development experience while maintaining high code quality standards.