# OpenCode Background Agents - Build System and Dependencies

## Build System Type and Configuration

### No Traditional Build System
The OpenCode Background Agents plugin uses a **zero-build architecture** that leverages modern JavaScript runtime capabilities rather than traditional build tooling. This approach aligns with OpenCode's plugin philosophy of minimal friction and direct TypeScript execution.

**Key characteristics:**
- **Runtime TypeScript**: Direct .ts file execution via Bun runtime
- **No compilation step**: TypeScript files are consumed directly by the OpenCode plugin system
- **No bundling**: Individual module files loaded as needed
- **Registry-based distribution**: Files copied directly to target locations without transformation

### Configuration Files

#### `registry.json` - Distribution Configuration
**Purpose**: OCX registry metadata defining plugin structure and distribution
**Key sections:**
- `components`: Defines plugin and skill components with file mappings
- `files`: Source-to-target path mappings for installation
- `dependencies`: No explicit dependencies due to runtime resolution

```json
{
  "$schema": "https://ocx.kdco.dev/schema/registry.json",
  "name": "kdco-background-agents",
  "description": "Async background agents for OpenCode - lightweight delegation system",
  "components": [
    {
      "name": "kdco-background-agents",
      "type": "ocx:plugin",
      "files": [
        {
          "path": "src/plugin/kdco-background-agents.ts",
          "target": "plugin/kdco-background-agents.ts"
        }
      ]
    }
  ]
}
```

## External Dependencies and Management

### Runtime Dependencies
The plugin has minimal runtime dependencies that are resolved at execution time:

#### **@opencode-ai/plugin** - Core Plugin API
- **Purpose**: OpenCode plugin system integration
- **Usage**: Tool creation, hook registration, and plugin lifecycle management
- **Resolution**: Provided by OpenCode runtime environment
- **Key imports**: `Plugin`, `ToolContext`, `tool`

#### **@opencode-ai/sdk** - OpenCode Client SDK
- **Purpose**: OpenCode API client and type definitions
- **Usage**: Session management, agent queries, and system integration
- **Resolution**: Available in OpenCode plugin context
- **Key imports**: `Event`, `Message`, `Part`, `TextPart`, client types

#### **unique-names-generator** - Human-Readable ID Generation
- **Purpose**: Generate memorable delegation IDs (e.g., "swift-amber-falcon")
- **Usage**: Delegation ID creation with configurable dictionaries
- **Resolution**: Must be manually installed if not using OCX
- **Key imports**: `uniqueNamesGenerator`, `adjectives`, `animals`, `colors`

### Dependency Management Strategy

#### **OCX Package Manager Integration**
When installed via OCX, dependencies are automatically managed:
```bash
ocx add kdco/background-agents --from https://registry.kdco.dev
```
- **Automatic resolution**: OCX handles dependency installation
- **Version management**: Registry-backed versioning and updates
- **Isolation**: Plugin-scoped dependency resolution

#### **Manual Installation Requirements**
For manual installation, dependencies must be handled manually:
- Copy `src/plugin/background-agents.ts` to `.opencode/plugin/background-agents.ts`
- Manually install `unique-names-generator` via npm/yarn/pnpm/bun
- Handle updates by re-copying source files

#### **No Package Lock Files**
The repository contains no traditional package management files:
- No `package.json` - dependencies resolved by OpenCode runtime
- No lock files (`package-lock.json`, `yarn.lock`, etc.)
- No `node_modules` - runtime dependency resolution

## Build Targets and Commands

### No Traditional Build Targets
Due to the zero-build architecture, traditional build commands are not applicable:
- **No compilation target**: TypeScript consumed directly
- **No bundling target**: Individual modules loaded as needed
- **No test runner**: No test suite configured
- **No linting setup**: No explicit linting configuration

### Runtime Execution Model

#### **Plugin Loading Process**
1. **Discovery**: OpenCode scans `.opencode/plugin/` directory
2. **Loading**: Direct TypeScript file execution via Bun runtime
3. **Registration**: Plugin exports processed for tool and hook registration
4. **Activation**: Plugin initialized with OpenCode context

#### **Hot Reloading Support**
OpenCode supports plugin hot reloading during development:
- File changes trigger automatic plugin reload
- No build step required for development iterations
- Direct source file editing and testing

## How to Build, Test, and Deploy

### Development Workflow

#### **Local Development Setup**
1. **Clone repository**: `git clone <repository-url>`
2. **Install via OCX** (recommended):
   ```bash
   ocx add kdco/background-agents --from https://registry.kdco.dev
   ```
3. **Manual installation** (alternative):
   - Copy `src/plugin/background-agents.ts` to `.opencode/plugin/`
   - Install `unique-names-generator`: `bun add unique-names-generator`

#### **Development Iteration**
1. **Edit source files**: Modify `.ts` files directly
2. **Reload OpenCode**: Plugin changes automatically detected
3. **Test functionality**: Use delegation tools in OpenCode interface
4. **Check logs**: Monitor OpenCode log panel for debug output

### Testing Strategy

#### **Integration Testing**
No automated test suite exists; testing relies on integration testing:
- **Manual delegation testing**: Create delegations and verify completion
- **Agent routing validation**: Test read-only vs write-capable agent handling
- **Storage verification**: Confirm delegation persistence across sessions
- **Error condition testing**: Validate timeout and error handling

#### **Debug Logging**
Comprehensive debug logging system for troubleshooting:
- **Debug log location**: `~/.local/share/opencode/delegations/<project-id>/background-agents-debug.log`
- **Structured logging**: Timestamps and detailed operation tracing
- **OpenCode log integration**: Warnings appear in OpenCode log panel

### Deployment Methods

#### **OCX Registry Distribution** (Recommended)
**Publisher workflow:**
1. **Update registry.json**: Modify version and component definitions
2. **Submit to KDCO Registry**: Submit changes to registry maintainers
3. **Registry propagation**: Changes distributed to all OCX installations

**User installation:**
```bash
ocx add kdco/background-agents --from https://registry.kdco.dev
```

#### **Manual Distribution**
**File copying approach:**
1. **Prepare source**: Ensure `src/plugin/background-agents.ts` is ready
2. **User installation**: Copy file to `.opencode/plugin/background-agents.ts`
3. **Dependency management**: User must manually install `unique-names-generator`
4. **Updates**: Manual re-copying required for updates

#### **Workspace Bundle Integration**
**Part of larger ecosystem:**
- **kdco-workspace**: Comprehensive bundle including background agents
- **Bundled installation**: Single command installs multiple productivity tools
- **Coordinated updates**: Updates handled at bundle level

### Configuration and Customization

#### **No Build Configuration Required**
The zero-build architecture eliminates traditional configuration needs:
- **No webpack.config.js**: No bundling configuration
- **No tsconfig.json**: TypeScript handled by runtime
- **No babel configuration**: No transpilation setup

#### **Runtime Configuration**
Plugin configuration handled through OpenCode's system:
- **Agent permissions**: Configured via OpenCode agent settings
- **Storage locations**: Automatically determined via project identification
- **Logging levels**: Controlled via OpenCode configuration

#### **Extension Points**
The plugin provides several extension points for customization:
- **Metadata generation**: Uses configurable small_model for delegation titles
- **Storage backends**: Project ID system supports different storage strategies
- **Agent routing**: Permission-based routing can be extended for new agent types

### Performance Considerations

#### **Runtime Performance**
- **Zero startup cost**: No build artifacts to load
- **Incremental loading**: Modules loaded on demand
- **Memory efficiency**: No bundled code duplication

#### **Development Performance**
- **Instant reload**: Changes reflected immediately without build time
- **Direct debugging**: Source maps not needed for debugging TypeScript
- **Minimal toolchain**: Fewer tools in development environment

The build system architecture prioritizes simplicity, fast iteration, and minimal setup complexity while maintaining the full functionality needed for a sophisticated background delegation system.
