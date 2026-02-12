# NocoBase Repository Summary

## Overview

NocoBase is an extensible, AI-powered, open-source no-code development platform designed with a scalability-first philosophy. It enables teams to rapidly build complex business systems without years of development or millions in investment. The platform adopts a data model-driven approach rather than being constrained by traditional form or table-driven paradigms, offering unprecedented flexibility in application development.

## Purpose and Goals

NocoBase aims to provide total control and infinite extensibility for building business applications. The platform separates data structure from user interface, allowing developers and non-technical users to:

- Build complex business systems through a visual, WYSIWYG interface
- Extend functionality through a plugin-based microkernel architecture
- Integrate AI capabilities seamlessly into workflows and interfaces
- Deploy applications in minutes rather than months or years
- Maintain complete control over data and business logic

The dual-licensing model (AGPL-3.0 and NocoBase Commercial License) supports both open-source community development and commercial enterprise deployments.

## Key Features and Capabilities

### 1. Data Model-Driven Architecture
NocoBase decouples UI components from underlying data structures, enabling:
- Multiple views (Grid, Gallery, Kanban, Calendar, Form) for the same data model
- Unlimited blocks and actions for any table or record
- Support for main database, external databases, and third-party APIs as data sources
- Dynamic schema generation and runtime configuration

### 2. AI Employee Integration
Unlike standalone AI tools, NocoBase embeds AI capabilities directly into business systems:
- Define AI employees for specific roles (translator, analyst, researcher, assistant)
- Seamless AI-human collaboration within interfaces and workflows
- Secure, transparent, and customizable AI usage tailored to business needs
- Integration with major AI providers (OpenAI, Anthropic, AWS Bedrock)

### 3. WYSIWYG Interface Builder
The platform provides an intuitive visual development experience:
- One-click switching between usage mode and configuration mode
- Page-based canvas for arranging blocks and actions (similar to Notion)
- Configuration interface designed for ordinary users, not just programmers
- Real-time preview of changes without deployment delays

### 4. Plugin-Based Extensibility
Everything in NocoBase is a plugin, following a WordPress-like architecture:
- All functionality delivered through plugins (83+ official plugins)
- Plugins are immediately usable upon installation
- Custom plugins can extend pages, blocks, actions, APIs, and data sources
- Plugin system supports both client-side and server-side extensions

### 5. Multi-Database Support
The database abstraction layer powered by Sequelize supports:
- PostgreSQL (including TimescaleDB, ClickHouse, Snowflake)
- MySQL
- SQLite
- MariaDB
- Kingbase (Chinese database)
- Multi-tenant and multi-datasource configurations

## Target Audience

NocoBase serves multiple user personas:

1. **No-Code Users**: Business analysts and domain experts who configure applications through the visual interface
2. **Low-Code Developers**: JavaScript/TypeScript developers who extend functionality through custom plugins
3. **Full-Stack Developers**: Engineers who contribute to the core platform or build complex integrations
4. **Enterprise Teams**: Organizations requiring self-hosted, scalable business application platforms
5. **System Integrators**: Consultants building custom solutions for clients

## High-Level Architecture

NocoBase follows a modern monorepo architecture managed by Lerna and Yarn workspaces:

### Core Layers
- **Client Layer** (`@nocobase/client`): React 18-based frontend using Ant Design 5, Formily, and custom schema system
- **Server Layer** (`@nocobase/server`): Koa-based Node.js application with plugin architecture
- **Database Layer** (`@nocobase/database`): Sequelize-based ORM with collection abstraction
- **Build System** (`@nocobase/build`): Custom build tooling for TypeScript compilation and bundling

### Key Architectural Patterns
- **Microkernel Architecture**: Minimal core with all features as plugins
- **Schema-Driven UI**: JSON schema-based component configuration
- **Resource-Action Pattern**: RESTful API design with resourcer abstraction
- **Event-Driven**: Async emitters for lifecycle hooks and cross-plugin communication
- **Repository Pattern**: Data access abstraction layer above Sequelize models

### Technology Stack
- **Frontend**: React 18, Ant Design 5, Formily (form solution), Emotion CSS, G2Plot (charts)
- **Backend**: Node.js 18+, Koa 2, Sequelize 6, WebSocket (real-time features)
- **Build Tools**: TypeScript 5.1, Vite-based bundling, Vitest (testing), Playwright (E2E)
- **Infrastructure**: Docker, PM2, Nginx, Redis (caching and pub/sub)

## Related Projects and Dependencies

### Core Dependencies
- **Formily**: Alibaba's form solution powering dynamic form generation
- **Sequelize**: Multi-dialect ORM for database abstraction
- **Ant Design**: Enterprise UI component library
- **Koa**: Web framework for the server layer

### Integration Ecosystem
- **AI Services**: OpenAI, Anthropic Claude, AWS Bedrock
- **Cloud Storage**: AWS S3, Alibaba Cloud OSS, Tencent COS
- **Authentication**: OAuth, SAML, OIDC, SMS-based auth
- **Workflow Automation**: Built-in workflow engine with multiple triggers
- **Data Visualization**: Chart libraries and custom visualization plugins

### Development Tools
- **CLI**: `create-nocobase-app` for project scaffolding
- **DevTools**: Built-in development mode with hot reload
- **Testing**: Comprehensive test utilities for both client and server
- **Documentation**: Dumi-based documentation system

## Deployment Models

NocoBase supports multiple deployment strategies:

1. **Docker Compose**: Recommended for no-code scenarios (single container deployment)
2. **Create NocoBase App**: For low-code development with custom business logic
3. **Git Source**: For core contributors and bleeding-edge features
4. **Production Docker**: Multi-stage builds with Nginx for enterprise deployments

The platform is designed to scale from single-server deployments to multi-tenant, distributed architectures with horizontal scaling capabilities through Redis-backed session management and pub/sub messaging.

## Community and Ecosystem

- **Version**: Currently at v1.9.46 (rapid release cycle)
- **License**: Dual-licensed (AGPL-3.0 for open source, commercial license available)
- **Repository**: GitHub at `nocobase/nocobase`
- **Documentation**: Comprehensive docs at docs.nocobase.com
- **Support**: Active forum at forum.nocobase.com
- **Use Cases**: Public customer stories and implementation examples available

NocoBase represents a modern approach to no-code platforms, prioritizing extensibility and developer experience while maintaining accessibility for non-technical users. Its architecture supports everything from simple CRUD applications to complex enterprise systems with custom workflows, AI integration, and multi-database orchestration.
