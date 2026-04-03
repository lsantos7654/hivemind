# OCX - OpenCode Extensions CLI

## Repository Purpose and Goals

OCX (OpenCode Extensions) is a ShadCN-style CLI tool designed to manage OpenCode extensions, configurations, and components across different projects and environments. Following the philosophy of "your AI agent never runs code you haven't reviewed," OCX provides a secure, transparent way to install and manage OpenCode agents, skills, plugins, and MCP servers.

The project's core mission is to solve the problem of OpenCode configuration portability and security. Unlike traditional package managers that hide code in `node_modules`, OCX follows the ShadCN model by copying components directly into your project (`.opencode/` directory), ensuring you own and can review all code before it runs.

## Key Features and Capabilities

### Profile-Based Configuration Management
OCX introduces a powerful profile system that allows users to maintain consistent OpenCode configurations across different repositories. Profiles are isolated environments that contain:
- Registry configurations for component sources
- OpenCode settings and preferences
- Security patterns via include/exclude lists
- Component installations and dependencies

### Multi-Mode Component Installation
The system supports multiple installation paradigms:
- **Local Mode**: Components installed to `.opencode/` directory within projects
- **Global Mode**: System-wide installation for user-level configurations
- **Profile Mode**: Installation within named profile directories for isolated environments

### Registry System with SHA-256 Verification
OCX implements a distributed registry system where:
- Components are fetched from configurable registry URLs
- All content is SHA-256 verified for integrity
- Registries follow a structured schema with component manifests
- Supports both registry components and npm plugins

### Receipt-Based Dependency Tracking
The v2 system introduced atomic receipt-based tracking (`receipt.jsonc`) that maintains:
- Canonical component identifiers with hash-based revisions
- File-level integrity hashes for installed components
- Dependency resolution graphs
- Installation metadata and provenance

### Security-First Architecture
Security is embedded throughout the system:
- Path validation prevents directory traversal attacks
- Blocked paths protect critical system files
- Content verification before installation
- Atomic write transactions with rollback capability

## Primary Use Cases and Target Audience

### Individual Developers
- Maintain consistent OpenCode setups across multiple projects
- Install curated extensions from trusted registries
- Manage different configuration profiles for different types of work

### Teams and Organizations
- Share standardized OpenCode configurations via profiles
- Distribute internal tools and agents through private registries
- Ensure consistent development environments across team members

### Registry Maintainers
- Publish and distribute OpenCode extensions
- Build and validate registry manifests
- Manage component versions and dependencies

### Enterprise Users
- Deploy controlled OpenCode environments with approved extensions
- Maintain security compliance through content verification
- Implement standardized tooling across development teams

## High-Level Architecture Overview

### Monorepo Structure
OCX follows a Turborepo-based monorepo architecture with:
- **packages/cli**: Main CLI implementation in TypeScript
- **workers/**: Cloudflare Workers for registry hosting
- **docs/**: Comprehensive documentation site
- **examples/**: Registry starter templates

### Core CLI Architecture
The CLI is built around several key architectural principles:

**Command Registration Pattern**: All commands follow a consistent registration pattern with shared options and error handling.

**Provider Abstraction**: Configuration providers abstract local vs global vs profile modes, allowing the same core logic to work across different installation targets.

**Schema-Driven Validation**: Extensive use of Zod schemas for type-safe configuration parsing and validation at system boundaries.

**Atomic Transactions**: File operations use atomic write patterns with backup/rollback capabilities to ensure consistency.

**Registry Resolution**: Dependency resolution follows Cargo-style semantics with support for both implicit (same-registry) and explicit (cross-registry) references.

### Data Model
The system maintains several key data structures:
- **Registry Schema**: Defines component manifests, dependencies, and metadata
- **OCX Configuration**: Project and global settings, registry mappings
- **Profile Configuration**: Isolated environment definitions with security patterns
- **Receipt Format**: Installation tracking with integrity verification
- **Component Manifest**: Individual component definitions with files, dependencies, and OpenCode configuration

## Related Projects and Dependencies

### Core Runtime Dependencies
- **Commander**: CLI framework for command structure and argument parsing
- **Zod**: Schema validation and type safety throughout the system
- **Chokidar**: File system watching for development workflows
- **Ora**: Terminal spinners and progress indicators
- **Kleur**: Terminal color output
- **JSONC-Parser**: Support for JSON with comments in configuration files

### Build and Development Tools
- **Bun**: JavaScript runtime and package manager (requires Node 18+)
- **Turborepo**: Monorepo management and build orchestration
- **Biome**: Code formatting and linting
- **TypeScript**: Type checking and compilation

### Integration Ecosystem
- **OpenCode**: The target platform for extension management
- **Registry Ecosystem**: Compatible with any HTTP-served registry following the OCX schema
- **npm Registry**: Supports npm plugins via `npm:package` syntax
- **Cloudflare Workers**: Registry hosting infrastructure

### Documentation and Tooling
- Comprehensive docs site with interactive examples
- CLI help system with detailed command documentation
- JSON Schema definitions for IDE support
- Migration tools for version upgrades

The project emphasizes developer experience through clear error messages, comprehensive help text, and extensive validation that fails fast with actionable feedback. The architecture supports both simple use cases (installing a single component) and complex scenarios (managing enterprise-wide extension ecosystems).
