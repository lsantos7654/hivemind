# OpenAPI-diff Repository Summary

## Purpose and Goals

OpenAPI-diff is a Java-based tool designed to compare two OpenAPI 3.x specifications and identify differences between them. The primary goal is to help API developers and maintainers understand how their API has changed over time, particularly focusing on backward compatibility concerns. The tool analyzes API specifications comprehensively, comparing endpoints, parameters, responses, schemas, security requirements, and other OpenAPI elements to generate detailed change reports.

The project aims to provide actionable insights into API evolution by categorizing changes as new additions, deletions, deprecations, or modifications, and critically distinguishing between backward-compatible and breaking changes. This enables teams to make informed decisions about API versioning and helps prevent unintended breaking changes from reaching production.

## Key Features and Capabilities

OpenAPI-diff offers comprehensive comparison capabilities across all aspects of OpenAPI specifications:

**Core Comparison Features:**
- Deep comparison of API endpoints (paths), HTTP methods, parameters, request bodies, and responses
- Schema-level analysis with support for complex schema structures including composed schemas (allOf, oneOf, anyOf)
- Detection of new, missing, and changed endpoints
- Identification of deprecated endpoints and operations
- Backward compatibility analysis with configurable incompatibility rules
- Extension point system via Java SPI for custom comparison logic

**Output Formats:**
- HTML rendering with visual highlighting of changes
- Markdown export for documentation purposes
- AsciiDoc format support
- JSON output for programmatic processing
- Plain text console output
- Detailed and summary views available

**Integration Options:**
- Command-line interface (CLI) for standalone usage
- Maven plugin for integration into build pipelines
- Java library (core API) for programmatic integration
- Docker container for containerized deployments
- Homebrew formula for Mac users

**Advanced Capabilities:**
- Support for OpenAPI authorization (headers, query parameters) when fetching remote specs
- Configurable path matching strategies for handling parameterized paths
- YAML-based configuration system to customize comparison behavior
- Fail-on-incompatible and fail-on-changed options for CI/CD integration
- Deferred schema processing to handle circular references and complex schema relationships

## Primary Use Cases and Target Audience

**Target Audience:**
- API developers maintaining versioned APIs
- DevOps engineers integrating API change detection into CI/CD pipelines
- Technical writers documenting API changes
- API governance teams enforcing compatibility standards
- QA teams validating API contracts

**Use Cases:**

1. **API Version Management:** Compare production API specifications against development versions to understand what changes are being introduced before deployment.

2. **CI/CD Integration:** Automatically fail builds when breaking changes are detected, or when any changes occur that haven't been explicitly approved.

3. **Change Documentation:** Generate human-readable change logs (Markdown, HTML) from spec differences to include in release notes or API documentation.

4. **Migration Analysis:** Assess the impact of migrating from one API version to another by identifying all breaking and compatible changes.

5. **Contract Testing:** Verify that API implementations remain compatible with published specifications over time.

6. **API Governance:** Enforce organizational policies about API evolution, such as prohibiting removal of endpoints or requiring deprecation periods.

## High-Level Architecture Overview

OpenAPI-diff follows a modular, multi-module Maven architecture:

**Core Module (`openapi-diff-core`):**
The foundation library containing all comparison logic. Built around a central `OpenApiDiff` class that coordinates specialized "Diff" components for different OpenAPI elements (PathsDiff, SchemaDiff, ParametersDiff, etc.). Uses the Swagger Parser library to parse OpenAPI specifications from files or URLs. Implements a two-pass comparison algorithm: first pass collects all schemas and deferred changes, second pass resolves circular references and computes final differences.

**CLI Module (`openapi-diff-cli`):**
Command-line interface built with Apache Commons CLI. Creates a shaded JAR (uber-JAR) containing all dependencies for standalone execution. Provides options for output format selection, log level control, authorization, and exit codes for CI/CD integration.

**Maven Plugin Module (`openapi-diff-maven`):**
Maven plugin wrapping the core functionality for integration into Maven build lifecycles. Allows specification of old and new spec locations, output file paths, and failure conditions directly in POM configuration.

**Key Design Patterns:**
- **Diff Components:** Specialized classes for comparing each OpenAPI element type
- **Changed Model:** Immutable model objects representing detected changes
- **Deferred Processing:** Two-pass algorithm to handle schema circularity
- **Renderer Pattern:** Pluggable output renderers for different formats
- **Builder Pattern:** Configuration via `OpenApiDiffOptions.Builder`
- **Service Provider Interface:** ExtensionDiff interface for custom comparison logic

## Related Projects and Dependencies

**Core Dependencies:**

1. **Swagger Parser v3 (v2.1.31):** The foundation for parsing OpenAPI specifications. Provides the OpenAPI object model and parsing capabilities for both local files and remote HTTP endpoints.

2. **Apache Commons:**
   - `commons-collections4` - Collection utilities
   - `commons-configuration2` - YAML configuration parsing
   - `commons-cli` - Command-line parsing
   - `commons-lang3` - String and object utilities

3. **j2html (v1.6.0):** Java-to-HTML library for generating HTML output with type-safe HTML construction.

4. **SLF4J/Logback:** Logging framework with configurable log levels.

5. **JUnit 5 & AssertJ:** Testing framework and fluent assertions for comprehensive test coverage.

**Related Projects:**

- **OpenAPI Generator:** Sister project in the OpenAPITools organization focused on code generation from OpenAPI specs
- **Swagger-diff (by Sayi):** Original inspiration for this project, focused on Swagger 2.0 specs
- **OpenAPI Initiative:** Governance organization maintaining the OpenAPI specification standard

**Ecosystem Position:**

OpenAPI-diff is part of the OpenAPITools organization, a community-driven collection of tools for working with OpenAPI specifications. It complements other tools like OpenAPI Generator by focusing specifically on API evolution and change detection rather than code generation. The tool is published to Maven Central (`org.openapitools.openapidiff`) and Docker Hub (`openapitools/openapi-diff`), making it accessible across different deployment environments.

**Build and Release Infrastructure:**
- GitHub Actions for CI/CD (Maven builds, Docker releases, PRs)
- SonarCloud for code quality analysis
- Maven Central and Central Repository OSSRH for artifact distribution
- Gitpod for cloud-based development environments
- Slack community for collaboration (shared with OpenAPI Generator)
