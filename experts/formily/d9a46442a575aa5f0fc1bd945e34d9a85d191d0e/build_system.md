# Formily Build System

## Build System Type and Configuration Files

Formily uses a sophisticated multi-stage build system combining TypeScript compilation, Rollup bundling, and Lerna monorepo management. The build infrastructure supports multiple output formats (CommonJS, ES Modules, UMD) and targets various consumption scenarios from npm packages to CDN distribution.

**Primary Build Tools**:
- **Lerna 4.0.0**: Monorepo orchestration and version management
- **TypeScript 4.1.5+**: Source compilation with strict type checking
- **Rollup 2.37.1**: Module bundling for browser distributions
- **Jest 26.0.0**: Test execution and coverage reporting
- **Yarn Workspaces**: Dependency hoisting and link management

**Key Configuration Files**:

**lerna.json**: Defines monorepo structure with unified versioning strategy
```json
{
  "version": "2.3.7",
  "npmClient": "yarn",
  "useWorkspaces": true,
  "command": {
    "version": {
      "forcePublish": true,
      "exact": true,
      "message": "chore(release): 😊 publish %s"
    }
  }
}
```

**package.json** (root): Workspace configuration and global scripts
- Workspaces: `packages/*` and `devtools/*`
- Build script: `rimraf -rf packages/*/{lib,dist,esm} && lerna run build`
- Test script: Jest with coverage across all packages
- Version scripts: Semantic versioning with prerelease support (alpha, beta, rc)

**tsconfig.json** (root): Base TypeScript configuration
- Target: ES5 for maximum compatibility
- Module: CommonJS for Node.js
- JSX: React for React components
- Paths: Aliased imports for `@formily/*` packages
- Experimental decorators enabled for observable models

**tsconfig.build.json** (per package): Production build configuration
- Extends root configuration
- Declaration generation enabled
- Source maps with inline sources
- Strict type checking

**rollup.config.js** (per package): References shared base configuration
- Imports `scripts/rollup.base.js`
- Specifies output filename and global namespace
- Can include package-specific plugins

**scripts/rollup.base.js**: Shared Rollup configuration factory
- Generates UMD development and production bundles
- Configures external dependencies and globals mapping
- Includes TypeScript, CommonJS, and resolution plugins
- Applies Terser minification for production
- Generates `.d.ts` bundles for non-UI packages

## External Dependencies and Management

**Development Dependencies** (root package.json):
- **Build Tools**: Rollup and plugins (typescript2, commonjs, node-resolve, dts, terser)
- **Testing**: Jest, @testing-library/react, @testing-library/vue, jest-dom
- **Code Quality**: ESLint, Prettier, lint-staged, commitlint
- **Documentation**: Dumi 1.1.53 for documentation generation
- **Type Definitions**: @types/react, @types/react-dom, @types/node

**Package Dependencies Pattern**:
Each package declares its own dependencies in its package.json:

**Core Package Dependencies** (@formily/core):
```json
"dependencies": {
  "@formily/reactive": "2.3.7",
  "@formily/shared": "2.3.7",
  "@formily/validator": "2.3.7"
}
```

**React Package Dependencies** (@formily/react):
```json
"dependencies": {
  "@formily/core": "2.3.7",
  "@formily/json-schema": "2.3.7",
  "@formily/reactive": "2.3.7",
  "@formily/reactive-react": "2.3.7",
  "@formily/shared": "2.3.7",
  "@formily/validator": "2.3.7",
  "hoist-non-react-statics": "^3.3.2"
},
"peerDependencies": {
  "react": ">=16.8.0",
  "react-dom": ">=16.8.0",
  "react-is": ">=16.8.0"
}
```

**Ant Design Package Dependencies** (@formily/antd):
```json
"dependencies": {
  "@dnd-kit/core": "^6.0.0",
  "@dnd-kit/sortable": "^7.0.0",
  "@formily/core": "2.3.7",
  "@formily/grid": "2.3.7",
  "@formily/json-schema": "2.3.7",
  "@formily/react": "2.3.7",
  "@formily/reactive": "2.3.7",
  "@formily/reactive-react": "2.3.7",
  "@formily/shared": "2.3.7",
  "classnames": "^2.2.6",
  "react-sticky-box": "^0.9.3"
},
"peerDependencies": {
  "@ant-design/icons": "4.x",
  "antd": "<=4.22.8",
  "react": ">=16.8.0",
  "react-dom": ">=16.8.0"
}
```

**Dependency Management Strategy**:
- **Exact Version Pinning**: All internal dependencies use exact versions (2.3.7) to ensure consistency
- **Peer Dependencies**: Framework and UI library dependencies are declared as peers to avoid duplication
- **Hoisting**: Yarn workspaces hoist common dependencies to root node_modules
- **Version Locking**: yarn.lock (949KB) ensures reproducible builds
- **Optional Peers**: Type definitions marked as optional in peerDependenciesMeta

**Version Resolution Overrides** (package.json resolutions):
```json
"resolutions": {
  "@types/react": "^18.0.0",
  "@types/react-dom": "^18.0.0",
  "yargs": "^16.x",
  "commander": "^6.x"
}
```

## Build Targets and Commands

**Global Build Commands** (from root package.json):

**Primary Build Pipeline**:
```bash
yarn build
# Executes: rimraf -rf packages/*/{lib,dist,esm} && lerna run build
# 1. Cleans all output directories (lib, dist, esm) across packages
# 2. Runs individual package build scripts via Lerna
```

**Per-Package Build Scripts** (example from @formily/core):
```bash
# Full build (all formats)
npm run build
# Executes: rimraf -rf lib esm dist &&
#           npm run build:cjs &&
#           npm run build:esm &&
#           npm run build:umd

# CommonJS build
npm run build:cjs
# Executes: tsc --project tsconfig.build.json
# Output: lib/ directory with .js and .d.ts files

# ES Modules build
npm run build:esm
# Executes: tsc --project tsconfig.build.json --module es2015 --outDir esm
# Output: esm/ directory with ES module syntax

# UMD bundle build
npm run build:umd
# Executes: rollup --config
# Output: dist/ directory with development and production UMD bundles
```

**Build Output Structure** (per package):
```
package/
├── lib/               # CommonJS modules (main entry point)
│   ├── index.js
│   ├── index.d.ts
│   └── (mirror of src structure)
├── esm/               # ES Modules (module entry point)
│   ├── index.js
│   ├── index.d.ts
│   └── (mirror of src structure)
└── dist/              # UMD bundles (unpkg/jsdelivr entry)
    ├── formily.core.umd.development.js
    ├── formily.core.umd.development.js.map
    ├── formily.core.umd.production.js
    ├── formily.core.umd.production.js.map
    ├── formily.core.d.ts           # Single-file types
    └── formily.core.all.d.ts       # Bundled types with deps
```

**Component Library Build Extensions** (e.g., @formily/antd):
```bash
# Additional style processing
npm run create:style  # Generates style entry points
npm run build:style   # Compiles Less to CSS

# Build sequence for component libraries:
# 1. rimraf -rf lib esm dist
# 2. create:style (generates style.js files)
# 3. build:cjs, build:esm, build:umd
# 4. build:style (compiles stylesheets)
```

**Testing Commands**:
```bash
# Full test suite with coverage
yarn test
# Executes: jest --coverage

# Package-specific tests
yarn test:core         # Test @formily/core
yarn test:react        # Test @formily/react
yarn test:reactive     # Test @formily/reactive
yarn test:validator    # Test @formily/validator

# Watch mode for development
yarn test:core:watch   # Continuous testing during development
```

**Documentation Commands**:
```bash
# Development server
yarn start
# Executes: dumi dev
# Starts documentation site at http://localhost:8000

# Production documentation build
yarn build:docs
# Executes: dumi build
# Output: dist/ directory with static site
```

**Version Management Commands**:
```bash
# Prerelease versions
yarn version:alpha     # Bump to next alpha version
yarn version:beta      # Bump to next beta version
yarn version:rc        # Bump to next release candidate

# Release versions
yarn version:patch     # Bump patch version (2.3.7 -> 2.3.8)
yarn version:minor     # Bump minor version (2.3.7 -> 2.4.0)
yarn version:major     # Bump major version (2.3.7 -> 3.0.0)

# Force publish (recovery from failed publish)
yarn release:force
# Executes: lerna publish from-package --yes
```

**Linting and Code Quality**:
```bash
# ESLint check
yarn lint
# Executes: eslint .

# Pre-commit hooks (configured via ghooks)
# Automatically runs on git commit:
# 1. lint-staged (eslint + prettier on staged files)
# 2. commitlint (validate commit message format)
```

## How to Build, Test, and Deploy

**Initial Setup**:
```bash
# Clone repository
git clone https://github.com/alibaba/formily.git
cd formily

# Install dependencies (respects yarn.lock)
yarn install --ignore-engines

# The --ignore-engines flag is required due to:
# "devEngines": { "node": "8.x || 9.x || 10.x || 11.x" }
# Modern Node.js versions (14+) work fine with this flag
```

**Development Workflow**:
```bash
# 1. Start documentation site for development
yarn start

# 2. Make changes to source code in packages/*/src/

# 3. Run tests in watch mode for affected package
cd packages/core
yarn test:watch

# 4. Lint and format code
yarn lint
```

**Building for Production**:
```bash
# Full build of all packages
yarn build

# This executes for each package:
# - TypeScript compilation to lib/ (CommonJS)
# - TypeScript compilation to esm/ (ES Modules)
# - Rollup bundling to dist/ (UMD development + production)
# - Type declaration bundling (.d.ts files)
# - Style compilation for component libraries

# Build time: ~5-10 minutes for full monorepo build
```

**Testing Strategy**:
```bash
# Run full test suite with coverage
yarn test

# Coverage reports generated in:
# - coverage/ directory (HTML report)
# - Console output with coverage percentages
# - Uploaded to Codecov in CI pipeline

# Test configuration (jest.config.js):
# - TypeScript tests with ts-jest
# - React testing with @testing-library/react
# - Vue testing with @testing-library/vue
# - Coverage thresholds enforced
```

**Publishing Workflow** (maintainers only):
```bash
# 1. Ensure all changes are committed
git add -A
git commit -m "feat: new feature"

# 2. Run preversion checks (automatic)
# - yarn install --ignore-engines
# - yarn build (full build)
# - yarn lint (code quality)
# - yarn test (full test suite)

# 3. Version bump (interactive)
yarn version:minor
# Prompts for version confirmation
# Updates all package.json files
# Creates git tag
# Generates CHANGELOG.md entry

# 4. Publish to npm (automatic via Lerna)
# Lerna publishes all changed packages
# Packages are scoped to @formily/*
# PublishConfig: { "access": "public" }

# 5. Push changes and tags
git push origin formily_next
git push origin --tags
```

**CI/CD Pipeline** (GitHub Actions):
- **Build**: Runs on all pull requests and commits
- **Test**: Executes full test suite with coverage reporting
- **Lint**: Checks code quality and commit message format
- **Documentation Deployment**: Auto-deploys to Netlify on merge to main
- **NPM Publishing**: Manual trigger or automatic on version tags

**Package Entry Points**:
Each package exports multiple entry points for different consumers:
```json
{
  "main": "lib",              // CommonJS (Node.js, webpack)
  "module": "esm",            // ES Modules (modern bundlers)
  "unpkg": "dist/formily.core.umd.production.js",  // CDN
  "jsdelivr": "dist/formily.core.umd.production.js", // CDN
  "types": "esm/index.d.ts"   // TypeScript definitions
}
```

**Development Tools Integration**:
- **VS Code**: Workspace settings in .vscode/ for consistent formatting
- **EditorConfig**: .editorconfig defines cross-editor standards
- **Git Hooks**: ghooks runs lint-staged and commitlint pre-commit
- **Conventional Commits**: commitlint enforces Angular commit format

**Build Performance Optimization**:
- **Incremental Builds**: TypeScript's incremental flag speeds up rebuilds
- **Parallel Execution**: Lerna runs package builds in parallel where possible
- **Tree Shaking**: ES module builds enable dead code elimination
- **Code Splitting**: Rollup external configuration prevents dependency bundling
- **Caching**: Jest caches test results; TypeScript caches type checking
