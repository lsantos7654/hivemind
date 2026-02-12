# NocoDB Repository Summary

## Repository Purpose and Goals

NocoDB is an open-source platform that provides a no-code database interface, transforming any database into a smart spreadsheet. The primary mission is to democratize access to powerful database computing tools by providing the most powerful no-code interface for databases, accessible to every internet business across the world. NocoDB aims to bridge the gap between spreadsheets (used by billions) and databases (far more powerful but less accessible), making database functionality as easy to use as spreadsheet software.

The project addresses a fundamental problem: while spreadsheets are collaboratively used by over a billion people, databases—which are significantly more powerful tools—remain difficult to work with at comparable speeds. NocoDB eliminates vendor lock-in, data lock-in, and the limitations of SaaS offerings by providing a self-hostable, extensible platform.

## Key Features and Capabilities

**Rich Spreadsheet Interface:**
- Complete CRUD operations (Create, Read, Update, Delete) for tables, columns, and rows
- Advanced field operations including sort, filter, group, hide/unhide columns
- Multiple view types: Grid (default), Gallery, Form, Kanban, and Calendar views
- View permission types: Collaborative views and locked views
- Public and private sharing capabilities with password protection
- Extensive cell types: ID, Links, Lookup, Rollup, SingleLineText, Attachment, Currency, Formula, User, and more
- Fine-grained access control with role-based permissions

**App Store for Workflow Automations:**
The platform provides extensive integrations across three main categories:
- Chat integrations: Slack, Discord, Mattermost
- Email services: AWS SES, SMTP, MailerSend
- Storage providers: AWS S3, Google Cloud Storage, Minio, and various cloud storage services

**Programmatic Access:**
- Complete REST API for all database operations
- Official NocoDB SDK for programmatic interactions
- Token-based authentication (JWT or Social Auth)
- WebSocket support for real-time collaboration

**AI Integration:**
The platform includes AI capabilities with support for multiple providers including OpenAI, Anthropic, AWS Bedrock, Google AI, Groq, and DeepSeek, enabling AI-powered features within the database interface.

## Primary Use Cases and Target Audience

**Target Audience:**
- Internet businesses of all sizes needing database management
- Teams seeking alternatives to Airtable or Google Sheets with more power
- Developers building internal tools and admin panels
- Organizations requiring self-hosted database solutions
- Teams needing collaborative database interfaces without vendor lock-in

**Use Cases:**
- Rapid prototyping and MVP development
- Internal tool creation and admin dashboards
- Customer relationship management (CRM) systems
- Project management and task tracking
- Content management systems
- Data collection and form management
- API generation for existing databases
- Multi-user collaborative data management

## High-Level Architecture Overview

NocoDB follows a modern monorepo architecture with clear separation of concerns:

**Frontend (nc-gui):**
- Built with Nuxt 3 (Vue 3 framework) using TypeScript
- Component-based architecture with over 30 major component categories
- State management using Pinia
- Rich UI components from Ant Design Vue
- WindiCSS for styling
- Monaco Editor for code editing
- Real-time collaboration via Socket.io
- Responsive design with mobile support

**Backend (nocodb):**
- NestJS framework providing modular, scalable architecture
- TypeScript-based with comprehensive type safety
- Multi-database support: PostgreSQL, MySQL, SQLite, SQL Server, ClickHouse, Snowflake, Databricks
- Knex.js for database abstraction and query building
- RESTful API with comprehensive endpoints (v1 and v2 APIs)
- WebSocket gateway for real-time updates
- Plugin architecture for extensibility
- Job queue system using Bull for background tasks
- Redis support for caching and session management
- Passport-based authentication with multiple strategies

**SDK (nocodb-sdk):**
- Standalone TypeScript SDK for API consumers
- Auto-generated from OpenAPI/Swagger specifications
- Type-safe interfaces for all API operations
- Shared utilities and helper functions

**Integrations Framework (noco-integrations):**
- Modular integration system for third-party services
- Support for authentication, AI, sync, and storage integrations
- Extensible architecture for custom integrations

**Build System:**
- Rspack for backend bundling (webpack successor)
- Vite/Nuxt for frontend development and building
- pnpm workspace for monorepo management
- Docker-based deployment with multi-stage builds

## Related Projects and Dependencies

**Major Dependencies:**

Backend:
- NestJS: Core framework for backend architecture
- Knex.js: SQL query builder and database abstraction
- Passport: Authentication middleware
- Bull: Redis-based queue for background jobs
- Socket.io: Real-time bidirectional communication
- Sharp: Image processing
- Handlebars/EJS: Template engines
- Various cloud SDKs: AWS, Google Cloud, Azure
- AI SDKs: OpenAI, Anthropic, Google AI, AWS Bedrock

Frontend:
- Vue 3: Progressive JavaScript framework
- Nuxt 3: Meta-framework for Vue
- Pinia: State management
- Ant Design Vue: UI component library
- TipTap: Rich text editor
- Monaco Editor: Code editor
- Leaflet: Map visualization
- Chart.js/Echarts: Data visualization
- VueFlow: Node-based workflow visualization

**Related Ecosystem:**
- Official documentation at docs.nocodb.com
- Community forum at community.nocodb.com
- Discord community for support
- Docker Hub for container images
- Kubernetes Helm charts for deployment

**Database Support:**
NocoDB doesn't replace databases but sits on top of them, supporting PostgreSQL, MySQL, SQLite, Microsoft SQL Server, ClickHouse, Snowflake, and Databricks. It can connect to existing databases or create new ones.

**License:**
The project is licensed under the Sustainable Use License, requiring a Contributor License Agreement (CLA) for contributions. The project welcomes contributions following Gitflow workflow with all development happening in the `develop` branch.
