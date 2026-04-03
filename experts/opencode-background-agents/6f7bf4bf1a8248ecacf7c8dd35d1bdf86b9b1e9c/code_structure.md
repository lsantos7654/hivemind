# OpenCode Background Agents - Code Structure Analysis

## Complete Annotated Directory Tree

```
/
├── LICENSE                           # MIT license (2026 Kenny)
├── README.md                         # Project documentation and usage guide
├── registry.json                     # OCX registry configuration for plugin distribution
└── src/                             # Source code directory
    └── plugin/                      # OpenCode plugin implementation
        ├── background-agents.ts     # Main plugin implementation (1,345 lines)
        └── kdco-primitives/         # Shared utility modules
            ├── index.ts             # Module exports aggregator
            ├── types.ts             # TypeScript type definitions
            ├── get-project-id.ts    # Git-based project identification
            ├── log-warn.ts          # Unified warning logging
            ├── with-timeout.ts      # Promise timeout utilities
            ├── mutex.ts             # Async mutex implementation
            ├── shell.ts             # Cross-platform shell escaping
            ├── temp.ts              # Temporary directory management
            └── terminal-detect.ts   # Terminal environment detection
```

## Module and Package Organization

### Primary Plugin Module (`background-agents.ts`)
The main plugin file contains the complete background delegation system implemented as a single, comprehensive module. This architectural choice prioritizes:
- **Self-containment**: All core logic in one file for easier reasoning and debugging
- **Atomic functionality**: Single source of truth for delegation behavior and state management
- **Plugin simplicity**: OpenCode plugins benefit from minimal file distribution

**Key organizational patterns within the main module:**
- **Type definitions** (lines 150-207): Interfaces for delegations, progress tracking, and input/output contracts
- **Utility functions** (lines 25-147): ID generation, metadata creation, and helper utilities
- **Core class** (lines 315-969): DelegationManager containing all business logic
- **Tool creators** (lines 980-1078): Factory functions for OpenCode tool integration
- **Hook handlers** (lines 1281-1342): Integration with OpenCode's plugin system
- **Plugin export** (lines 1218-1343): Main plugin factory and configuration

### Shared Primitives Library (`kdco-primitives/`)
The kdco-primitives directory contains extracted, reusable utilities designed for sharing across multiple plugins in the KDCO ecosystem. This follows a microservice-style architecture where common concerns are factored into focused modules.

**Architectural principles:**
- **Single responsibility**: Each module handles exactly one concern
- **Framework agnostic**: Utilities work independently of OpenCode specifics
- **Type safety**: Comprehensive TypeScript coverage with proper exports
- **Error handling**: Consistent error patterns and logging across modules

## Main Source Directories and Their Purposes

### `/src/plugin/` - Plugin Implementation Layer
**Purpose**: Contains the complete OpenCode plugin implementation
**Structure**: Single main file plus shared utilities
**Responsibilities**:
- OpenCode API integration and tool registration
- Delegation lifecycle management from creation to completion
- Session management and event handling
- Storage persistence and retrieval operations

### `/src/plugin/kdco-primitives/` - Utility Layer
**Purpose**: Shared primitives for cross-plugin consistency
**Structure**: Focused single-purpose modules with unified exports
**Responsibilities**:
- Project identification using git repository metadata
- Cross-platform system integration (shell, terminal, filesystem)
- Common patterns (timeouts, mutexes, logging)
- Type definitions and contracts

## Key Files and Their Roles

### Core Implementation Files

#### `background-agents.ts` (1,345 lines) - Main Plugin
**Role**: Complete background delegation system implementation
**Key components**:
- **DelegationManager class** (lines 315-969): Core orchestration logic
  - Session creation and management
  - Agent capability detection and routing
  - Progress tracking and timeout handling
  - Storage persistence and metadata generation
- **Tool implementations** (lines 980-1078): OpenCode tool interfaces
  - `delegate()`: Task creation with immediate ID return
  - `delegation_read()`: Result retrieval by ID
  - `delegation_list()`: Delegation browsing and discovery
- **Hook integrations** (lines 1281-1342): OpenCode plugin system integration
  - System prompt injection for delegation rules
  - Context compaction handling for result preservation
  - Tool execution interception for agent routing

#### `registry.json` (30 lines) - Distribution Configuration
**Role**: OCX registry metadata for plugin distribution
**Key elements**:
- Plugin component definition with TypeScript source mapping
- Skill component definition for delegation protocol guidelines
- Schema validation and component dependency declarations

### Utility Implementation Files

#### `get-project-id.ts` (172 lines) - Project Identity System
**Role**: Stable project identification across git repository operations
**Key features**:
- Git root commit SHA extraction for stable identity
- Worktree support with commondir resolution
- Path-based fallback for non-git projects
- Caching system with .git/opencode storage

#### `types.ts` (13 lines) - Type Definitions
**Role**: Centralized TypeScript type exports
**Key exports**:
- `OpencodeClient`: Derived from SDK factory function for type safety
- Shared interfaces for cross-module consistency

#### `log-warn.ts` (51 lines) - Unified Logging
**Role**: Consistent warning output across all plugin components
**Key features**:
- OpenCode API integration when client available
- Console fallback for CLI contexts
- Service-scoped categorization for log organization

#### `with-timeout.ts` (84 lines) - Promise Timeout Management
**Role**: Clean timeout handling patterns for async operations
**Key features**:
- Custom TimeoutError class with metadata
- Promise.race wrapper with automatic cleanup
- Configurable timeout messages and duration

## Code Organization Patterns

### Architectural Patterns

#### **Law-Based Error Handling**
All utility modules follow consistent error handling laws:
- **Law 1 (Early Exit)**: Guard clauses for invalid inputs
- **Law 4 (Fail Fast)**: Immediate errors for malformed data
- **Silent Degradation**: Logging failures don't disrupt callers

#### **Boundary Pattern Implementation**
The plugin uses explicit boundary parsing for external system integration:
- **Agent capability detection**: Parses OpenCode agent configurations at plugin boundaries
- **Permission validation**: Reads permission settings from configuration with fallback defaults
- **Git system integration**: Safely handles git command execution with timeout and error recovery

#### **Hook-Driven Architecture**
OpenCode integration uses multiple hook points:
- `tool.execute.before`: Intercepts tool calls for agent routing validation
- `experimental.chat.system.transform`: Injects delegation rules into system prompts
- `experimental.session.compacting`: Preserves delegation context during compaction
- `event`: Handles session lifecycle for delegation state management

### Design Patterns

#### **Manager Pattern**
`DelegationManager` acts as a central coordinator:
- **State management**: Maintains in-memory delegation tracking with persistence
- **Lifecycle coordination**: Handles creation, execution, completion, and cleanup
- **Event orchestration**: Coordinates between OpenCode sessions and delegation processes

#### **Factory Pattern**
Tool creation uses factory functions:
- Dependency injection for manager instances
- Consistent parameter validation and error handling
- Unified tool metadata and schema definitions

#### **Observer Pattern**
Event-driven delegation updates:
- Session idle events trigger completion processing
- Message events update progress tracking
- Parent session notifications provide status updates

### File Naming and Organization Standards

- **Kebab-case**: All files use kebab-case naming (background-agents.ts, get-project-id.ts)
- **Descriptive names**: Names clearly indicate module purpose and scope
- **Extension clarity**: .ts extensions for TypeScript, .json for configuration data
- **Hierarchical organization**: Utilities grouped under kdco-primitives/ namespace

The code structure demonstrates enterprise-level organization with clear separation of concerns, comprehensive error handling, and extensible architecture suitable for complex plugin ecosystems.
