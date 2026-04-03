# OCX APIs and Interfaces

## Public APIs and Entry Points

### CLI Command Interface
OCX exposes its functionality through a comprehensive command-line interface built on Commander.js. All commands follow a consistent pattern with standardized options and error handling.

#### Core Installation Commands
```bash
# Component installation from registries
ocx add <components...>
ocx add kdco/researcher              # Install from registry with alias
ocx add researcher                   # Install with implicit registry resolution
ocx add npm:@types/node              # Install npm package as plugin

# Installation options
ocx add kdco/workspace --dry-run     # Preview installation without changes
ocx add researcher --from https://registry.example.com  # Ephemeral registry
ocx add workspace --trust            # Skip npm plugin validation
ocx add kdco/researcher --global     # Install globally
ocx add workspace -p my-profile      # Install to specific profile
```

#### Profile Management API
```bash
# Profile lifecycle
ocx profile add <name>               # Create new profile
ocx profile add work --clone personal  # Clone existing profile
ocx profile add kdco --source tweak/p-1vp4xoqv --from https://tweakoc.com/r --global

# Profile operations
ocx profile list                     # List all profiles
ocx profile show <name>              # Inspect profile configuration
ocx profile remove <name>            # Delete profile
ocx profile move <old> <new>         # Rename profile

# Profile-based OpenCode execution
ocx oc -p <profile>                  # Launch OpenCode with profile
ocx opencode --profile work          # Alternative syntax
```

#### Configuration Management
```bash
# Configuration editing
ocx config edit                      # Edit local configuration
ocx config edit --global             # Edit global configuration
ocx config edit --profile work       # Edit profile configuration

# Registry management
ocx registry add https://registry.kdco.dev --name kdco  # Add registry
ocx registry list                    # List configured registries
ocx registry remove kdco             # Remove registry
```

#### Build and Validation Tools
```bash
# Registry development
ocx build                            # Build registry from source
ocx build --dry-run                  # Preview build without output
ocx validate                         # Validate registry structure
ocx verify                           # Verify installation integrity

# Migration and maintenance
ocx migrate                          # Preview v1.4.6 → v2 migration
ocx migrate --apply                  # Apply migration
ocx update <component>               # Update installed components
ocx remove <component>               # Remove components
```

### Programmatic API
OCX exports library functions for programmatic use, enabling integration with other tools and custom workflows.

#### Build Registry Function
```typescript
import { buildRegistry } from 'ocx'

interface BuildRegistryOptions {
  source: string    // Source directory with registry.jsonc
  out: string       // Output directory for built registry
  dryRun?: boolean  // Preview mode without file creation
}

interface BuildRegistryResult {
  componentsCount: number  // Number of components built
  outputPath: string       // Absolute path to output
}

// Build registry from source
const result = await buildRegistry({
  source: './my-registry',
  out: './dist',
  dryRun: false
})

console.log(`Built ${result.componentsCount} components to ${result.outputPath}`)
```

#### Schema Validation
```typescript
import {
  registrySchema,
  componentManifestSchema,
  ocxConfigSchema
} from 'ocx'

// Validate registry manifest
const registry = registrySchema.parse(registryData)

// Validate component manifest
const component = componentManifestSchema.parse(componentData)

// Validate OCX configuration
const config = ocxConfigSchema.parse(configData)
```

## Key Classes, Functions, and Interfaces

### Core Configuration Types

#### Registry Configuration
```typescript
interface Registry {
  name: string                    // Registry display name
  version: string                 // Semver version
  author: string                  // Registry author
  opencode?: string              // Minimum OpenCode version
  ocx?: string                   // Minimum OCX version
  components: ComponentManifest[] // Component definitions
}

interface ComponentManifest {
  name: string                   // Component name (kebab-case)
  type: ComponentType           // 'agent' | 'skill' | 'plugin' | 'command' | 'tool' | 'bundle' | 'profile'
  description: string           // Human-readable description
  files: ComponentFile[]        // Files to install
  dependencies: string[]        // Component dependencies
  npmDependencies?: string[]    // npm dependencies
  npmDevDependencies?: string[] // npm dev dependencies
  opencode?: OpencodeConfig     // OpenCode configuration to merge
}
```

#### Component File Definitions
```typescript
// Cargo-style file specification (string shorthand or full object)
type ComponentFile = string | ComponentFileObject

interface ComponentFileObject {
  path: string    // Source path in registry
  target: string  // Target installation path (root-relative)
}

// Examples:
const files: ComponentFile[] = [
  "agents/researcher.md",                    // String shorthand
  { path: "src/plugin.ts", target: "plugins/my-plugin.ts" }  // Full control
]
```

#### Profile Configuration
```typescript
interface ProfileOcxConfig {
  $schema: string                    // Schema URL for IDE support
  registries: Record<string, {       // Registry alias → URL mapping
    url: string
  }>
  renameWindow?: boolean            // Enable terminal window renaming
  exclude: string[]                 // Glob patterns to exclude from OpenCode
  include: string[]                 // Glob patterns to explicitly include
}
```

### Core Business Logic Classes

#### Configuration Providers
```typescript
abstract class ConfigProvider {
  abstract cwd: string
  abstract getRegistries(): Record<string, { url: string }>
  abstract getComponentPath(): string
}

// Local project configuration
const localProvider = await LocalConfigProvider.requireInitialized('./project')

// Global user configuration
const globalProvider = await GlobalConfigProvider.requireInitialized()

// Profile-based configuration
const resolver = await ConfigResolver.create(cwd, { profile: 'work' })
```

#### Registry Resolution System
```typescript
interface ResolvedComponent {
  registryName: string      // Registry alias
  name: string             // Component name
  type: ComponentType      // Component type
  baseUrl: string         // Registry base URL
  files: ComponentFile[]   // Normalized file list
  opencode?: Record<string, unknown>  // OpenCode config to merge
}

interface DependencyResolution {
  components: ResolvedComponent[]  // All resolved components
  installOrder: string[]          // Topologically sorted install order
  opencode?: Record<string, unknown>  // Merged OpenCode configuration
  npmDependencies: string[]       // Collected npm dependencies
  npmDevDependencies: string[]    // Collected npm dev dependencies
}

// Resolve component dependencies across registries
const resolved = await resolveDependencies(registries, ['kdco/researcher'])
```

### Registry and Component Management

#### Registry Fetching
```typescript
// Fetch registry index
const index: RegistryIndex = await fetchRegistryIndex('https://registry.kdco.dev')

// Fetch component packument (npm-style versioned manifest)
const packument: Packument = await fetchRegistryPackument(baseUrl, componentName)

// Fetch component file content
const content: string = await fetchFileContent(baseUrl, componentName, filePath)
```

#### Receipt Management (V2)
```typescript
interface Receipt {
  version: number                           // Receipt format version
  root: string                             // Installation root directory
  installed: Record<string, ReceiptEntry>  // Canonical ID → installation details
}

interface ReceiptEntry {
  registryUrl: string      // Source registry URL
  registryName: string     // Registry alias used
  name: string            // Component name
  revision: string        // Content hash revision (sha256:...)
  hash: string           // Bundle hash for integrity verification
  files: Array<{         // Installed files with individual hashes
    path: string         // Resolved installation path
    hash: string         // File content hash
  }>
  installedAt: string    // ISO timestamp
  opencode?: Record<string, unknown>  // Component's OpenCode config
}
```

## Usage Examples with Code Snippets

### Basic Component Installation
```bash
# Initialize OCX in a project
ocx init

# Add a registry
ocx registry add https://registry.kdco.dev --name kdco

# Install components
ocx add kdco/researcher kdco/workspace

# Verify installation
ocx verify
```

### Profile-Based Workflow
```bash
# Set up global OCX
ocx init --global

# Create development profile
ocx profile add dev --clone default

# Install profile-specific components
ocx add kdco/debugging-tools -p dev

# Launch OpenCode with profile
ocx oc -p dev

# Create project profile from registry
ocx profile add enterprise --source enterprise/baseline --from https://company.com/registry --global
```

### Registry Development Workflow
```bash
# Create new registry
mkdir my-registry
cd my-registry

# Initialize registry structure
ocx init --registry

# Build registry
ocx build --source . --out dist

# Validate before publishing
ocx validate

# Test locally
ocx registry add file://$(pwd)/dist --name test
ocx add test/my-component --dry-run
```

### Programmatic Library Usage
```typescript
import { buildRegistry, registrySchema } from 'ocx'

// Build and validate registry programmatically
async function buildMyRegistry() {
  try {
    // Validate source registry
    const sourceData = await Bun.file('./registry.jsonc').json()
    const registry = registrySchema.parse(sourceData)

    // Build registry
    const result = await buildRegistry({
      source: './src',
      out: './dist',
      dryRun: false
    })

    console.log(`✅ Built ${result.componentsCount} components`)
    return result
  } catch (error) {
    console.error('❌ Build failed:', error.message)
    throw error
  }
}
```

## Integration Patterns and Workflows

### CI/CD Integration
```yaml
# GitHub Actions example
name: Build Registry
on: [push, pull_request]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: oven-sh/setup-bun@v1
      - run: bun install
      - run: bun add -g ocx
      - run: ocx validate              # Validate registry structure
      - run: ocx build --dry-run       # Preview build
      - run: ocx build                 # Build registry
      - run: ocx verify                # Verify integrity
```

### Custom Integration Patterns
```typescript
// Custom OCX integration example
import { ConfigResolver } from 'ocx'

class CustomOpenCodeManager {
  async setupEnvironment(profileName: string, projectPath: string) {
    // Resolve configuration with profile
    const resolver = await ConfigResolver.create(projectPath, {
      profile: profileName
    })

    // Get merged configuration
    const registries = resolver.getRegistries()
    const componentPath = resolver.getComponentPath()

    // Custom logic using resolved configuration
    return this.deployConfiguration(registries, componentPath)
  }
}
```

### Error Handling Patterns
```typescript
import {
  ConflictError,
  ValidationError,
  IntegrityError,
  ProfileNotFoundError
} from 'ocx'

try {
  await runAddCore(['kdco/researcher'], options, provider)
} catch (error) {
  if (error instanceof ConflictError) {
    // Handle file conflicts with specific resolution steps
    console.error('Conflict:', error.message)
    // Suggest resolution: ocx update or manual conflict resolution
  } else if (error instanceof ValidationError) {
    // Handle validation errors with actionable feedback
    console.error('Validation:', error.message)
    // Suggest fixes based on error context
  } else if (error instanceof IntegrityError) {
    // Handle integrity verification failures
    console.error('Integrity check failed:', error.message)
    // Suggest re-installation or registry verification
  }
}
```

## Configuration Options and Extension Points

### Global Configuration
OCX supports comprehensive configuration at multiple levels:

**Global OCX Config (`~/.config/ocx/ocx.jsonc`)**
```jsonc
{
  "$schema": "https://ocx.kdco.dev/schemas/ocx.json",
  "registries": {
    "kdco": { "url": "https://registry.kdco.dev" },
    "company": { "url": "https://internal.company.com/registry" }
  },
  "componentPath": ".opencode"  // Local installation directory
}
```

**Profile Configuration (`~/.config/ocx/profiles/<name>/ocx.jsonc`)**
```jsonc
{
  "$schema": "https://ocx.kdco.dev/schemas/profile.json",
  "registries": {
    "work": { "url": "https://work-registry.company.com" }
  },
  "renameWindow": true,
  "exclude": [
    "**/AGENTS.md",      // Exclude instruction files
    "**/.opencode/**",   // Exclude OCX management files
    "**/secrets/**"      // Exclude sensitive directories
  ],
  "include": [
    "docs/**/*.md"       // Explicitly include documentation
  ]
}
```

### OpenCode Integration Configuration
Components can specify OpenCode configuration that gets merged into `opencode.json`:

```typescript
// Component manifest with OpenCode config
const component: ComponentManifest = {
  name: "researcher",
  type: "agent",
  description: "Research and analysis agent",
  files: ["agents/researcher.md"],
  opencode: {
    // MCP servers (Cargo-style: string URL or full config)
    mcp: {
      "web-search": "https://mcp.example.com/search",
      "database": {
        type: "remote",
        url: "https://db-mcp.example.com",
        headers: { "Authorization": "Bearer ${DB_TOKEN}" },
        oauth: { scopes: ["read", "write"] }
      }
    },
    // Agent configuration
    agent: {
      "researcher": {
        model: "claude-3-5-sonnet",
        steps: 50,
        tools: { "web": true, "search": true },
        permission: {
          bash: { "*": "deny" },  // Read-only agent
          edit: "ask"
        }
      }
    },
    // Global instructions
    instructions: [
      "Always cite sources when providing information",
      "Use structured output for research findings"
    ]
  }
}
```

### Extension Points for Custom Functionality

#### Custom Validation
```typescript
// Custom validator implementation
export async function validateCustomRegistry(registryPath: string): Promise<ValidationResult> {
  // Custom validation logic
  const customRules = await loadCustomRules()
  return validateWithRules(registryPath, customRules)
}
```

#### Custom Component Types
```typescript
// Extend component types for custom use cases
const customComponentTypes = [
  "agent", "skill", "plugin", "command", "tool", "bundle", "profile",
  "workflow", "template", "config"  // Custom types
] as const

type CustomComponentType = typeof customComponentTypes[number]
```

#### Registry Discovery Integration
OCX supports `.well-known/ocx.json` for automatic registry discovery:
```json
{
  "registry": "/index.json",
  "documentation": "/docs",
  "contact": "admin@registry.example.com"
}
```

The API design emphasizes type safety, clear error messages, and consistent patterns across all interfaces. The combination of CLI commands, programmatic APIs, and extensive configuration options enables OCX to integrate into diverse workflows while maintaining security and reliability.
