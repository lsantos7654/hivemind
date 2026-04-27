- OpenCode Plugin Development
  - Plugin architecture and lifecycle management
  - Tool creation with `@opencode-ai/plugin` API
  - Hook integration (`experimental.chat.system.transform`, `experimental.session.compacting`, `tool.execute.before`)
  - Event handling for session management
  - Plugin distribution via OCX registry system
  - Zero-build architecture with direct TypeScript execution
  - Plugin context and dependency injection patterns

- Background Delegation System
  - Async task delegation with immediate ID return
  - Session isolation and management for background tasks
  - Agent capability detection and routing logic
  - Delegation lifecycle management (creation, execution, completion, cleanup)
  - Progress tracking and timeout handling (15-minute limits)
  - Batched notification system with parent session updates
  - Context preservation during OpenCode compaction cycles

- Agent Integration and Routing
  - Permission-based agent capability detection
  - Read-only vs write-capable agent classification
  - Tool routing enforcement (`delegate` vs `task`)
  - Agent configuration parsing from OpenCode settings
  - Support for researcher, explore, coder, scribe, and general agents
  - Error handling for invalid agent usage patterns

- Storage and Persistence
  - Project identification using git repository metadata
  - Cross-worktree storage consistency with git commondir resolution
  - Markdown-formatted delegation result storage
  - Metadata generation using small language models
  - File-based delegation history with auto-generated titles
  - Session-scoped storage organization and cleanup

- DelegationManager Class Implementation
  - Core orchestration class for delegation operations
  - Session creation and management for isolated execution
  - Result extraction from OpenCode session messages
  - Delegation state tracking (running, complete, error, timeout, cancelled)
  - Event-driven completion handling via session.idle events
  - Progress monitoring and timeout enforcement

- Tool API Implementation
  - `delegate(prompt, agent)` - Background task creation
  - `delegation_read(id)` - Result retrieval by readable ID
  - `delegation_list()` - Delegation discovery and browsing
  - Parameter validation and error handling
  - Tool context integration with OpenCode sessions
  - Consistent error messaging and user guidance

- OpenCode Integration Patterns
  - System prompt injection for delegation rules
  - Context compaction hook for result preservation
  - Tool execution interception for agent routing
  - Event system integration for lifecycle management
  - Client API usage for session and agent operations
  - Configuration system integration for agent permissions

- TypeScript Architecture and Patterns
  - Modern TypeScript with comprehensive type safety
  - Interface-driven design for extensibility
  - Factory pattern for tool creation
  - Manager pattern for delegation orchestration
  - Observer pattern for event-driven updates
  - Law-based error handling (Early Exit, Fail Fast)

- Cross-Platform Utilities (kdco-primitives)
  - Project identification with git root commit hashing
  - Promise timeout management with custom error types
  - Cross-platform shell command escaping
  - Async mutex implementation for resource coordination
  - Terminal environment detection and handling
  - Unified logging with OpenCode API integration

- Git Repository Integration
  - Git worktree detection and commondir resolution
  - Root commit SHA extraction for project stability
  - Cache management in .git/opencode directory
  - Path-based fallback for non-git projects
  - Cross-platform git command execution with timeouts

- Metadata and Content Generation
  - Small model integration for title/description generation
  - Fallback text truncation when models unavailable
  - Structured markdown format for delegation results
  - JSON parsing and validation for generated metadata
  - Content summarization and tagging systems

- Error Handling and Resilience
  - Comprehensive error categorization and messaging
  - Graceful degradation when components fail
  - Timeout handling with configurable limits
  - Session cleanup and resource management
  - Debug logging with structured output

- OCX Registry and Distribution
  - Registry.json configuration for component distribution
  - File mapping from source to installation targets
  - Component dependency declarations and skill integration
  - Schema validation and registry compatibility
  - Manual vs automated installation workflows

- Performance and Optimization
  - Zero-build architecture for minimal overhead
  - Runtime dependency resolution without bundling
  - Incremental module loading and hot reloading
  - Memory-efficient delegation tracking
  - Batched notifications to reduce context usage

- Security and Isolation
  - Background session isolation for safe execution
  - Agent permission validation before delegation
  - Read-only agent enforcement for data integrity
  - Secure storage with project-scoped directories
  - Input validation and sanitization patterns

- Context Management and Compaction
  - Context preservation strategies during OpenCode compaction
  - Delegation state injection into compacted sessions
  - Running vs completed delegation categorization
  - Historical delegation browsing and retrieval
  - Session tree navigation and root resolution

- Plugin Extension Points
  - Custom metadata generator implementation
  - Storage backend customization options
  - Agent capability detection extensions
  - Tool routing logic modifications
  - Event handler customization patterns

- Integration Testing Patterns
  - Manual integration testing workflows
  - Debug logging and troubleshooting techniques
  - OpenCode log panel integration for monitoring
  - Error reproduction and diagnostic procedures
  - Plugin hot reloading for development iteration
