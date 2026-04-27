**CLI Framework and Architecture:**
- Commander.js-based CLI with systematic command registration patterns
- Provider abstraction for local, global, and profile configuration modes
- Atomic transaction system with rollback capabilities for file operations
- Error handling with structured error types and actionable user feedback
- Turborepo monorepo architecture with TypeScript and Bun runtime
- Comprehensive test suite with unit, integration, and fixture-based testing

**Profile and Configuration Management:**
- Profile system for isolated OpenCode environment configurations
- Multi-level configuration inheritance (global → profile → local)
- JSONC configuration files with schema validation and IDE support
- Registry alias mapping and ephemeral registry support
- Include/exclude pattern matching for security and content control
- Terminal window renaming and workspace integration features

**Component Registry System:**
- ShadCN-style component copying (not node_modules hiding)
- Distributed registry architecture with HTTP-based component serving
- SHA-256 content verification for security and integrity
- Cargo-style dependency references (implicit and explicit cross-registry)
- Component manifest schema with Zod validation
- Registry index generation and discovery (.well-known/ocx.json)

**Installation and Dependency Management:**
- Receipt-based tracking with canonical component identifiers
- Hash-based revision system for content verification
- Topological dependency resolution across multiple registries
- Atomic installation transactions with conflict detection and resolution
- npm plugin integration via npm: protocol syntax
- File-level integrity tracking with individual content hashes

**Component Types and Schemas:**
- Agent, skill, plugin, command, tool, bundle, and profile component types
- Zod-based schema validation at all system boundaries
- OpenCode configuration merging and plugin management
- MCP server configuration with OAuth and environment support
- Component file targeting with security validation
- Cargo-style union types (string shortcuts or full objects)

**Security and Path Validation:**
- Comprehensive path validation preventing directory traversal attacks
- Blocked path protection for critical system files
- Content verification before installation with integrity checking
- Runtime path containment validation using battle-tested algorithms
- Security-first architecture with defense in depth
- Reserved target protection for OCX-managed files

**Build and Development Tools:**
- Registry compilation from source with validation
- Dry-run capabilities across all operations for preview
- Binary compilation for standalone executable distribution
- Cloudflare Workers deployment for registry hosting
- Migration tooling for version upgrades
- Comprehensive validation and verification tooling

**Error Handling and User Experience:**
- Structured error types with context and remediation suggestions
- Fail-fast validation with detailed error messages
- Terminal UI with spinners, progress indicators, and colored output
- JSON output mode for programmatic integration
- Comprehensive help system with examples and usage patterns
- Human-readable diff output for migration previews

**TypeScript and Type Safety:**
- Extensive use of discriminated unions for type safety
- Zod schema integration generating TypeScript types
- Provider pattern abstractions with type-safe implementations
- Parse-don't-validate architecture following functional principles
- Comprehensive type guards and validation at boundaries
- Modern TypeScript features with strict type checking

**Registry Development and Publishing:**
- Registry scaffold generation with example templates
- Component manifest authoring with schema validation
- Registry build pipeline with integrity verification
- Component versioning following npm-style packument format
- Registry deployment to Cloudflare Workers or static hosting
- Discovery and indexing systems for registry ecosystems

**Integration Patterns:**
- OpenCode configuration merging with component-specified settings
- CI/CD integration patterns for registry validation and deployment
- Programmatic API for custom tooling integration
- Extension points for custom validation and component types
- Template and example systems for common use cases
- Documentation generation and schema-driven IDE support

**Migration and Version Management:**
- Version detection and compatibility checking
- Automated migration between OCX versions
- Receipt format evolution with backward compatibility
- Registry schema versioning and upgrade paths
- Component dependency upgrade workflows
- Installation verification and repair tooling

**Performance and Optimization:**
- Bun runtime for 2-10x performance improvements over Node.js
- Turborepo caching for fast incremental builds
- Parallel dependency resolution and installation
- Efficient file operations with atomic writes
- Registry caching and content deduplication
- Bundle size optimization and tree-shaking

**Developer Experience:**
- Comprehensive documentation with interactive examples
- Clear error messages with suggested resolutions
- Extensive help system with contextual guidance
- Development workflow integration with file watching
- Testing utilities and mock registry support
- Debugging tools and verbose operation modes
