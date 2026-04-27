This expert has deep knowledge of the OpenAPI-diff project, covering:

### Core Functionality
- **OpenAPI 3.x Specification Comparison**: Deep comparison algorithm that analyzes paths, operations, parameters, request bodies, responses, schemas, security requirements, OAuth flows, headers, and extensions
- **Backward Compatibility Analysis**: Configurable detection of breaking changes vs. compatible changes with customizable incompatibility rules
- **Schema Comparison**: Advanced schema diff including composed schemas (allOf, oneOf, anyOf), circular reference handling, property changes, type changes, and constraint validation
- **Deferred Processing**: Two-pass comparison algorithm to handle complex schema relationships and circular dependencies
- **Change Detection**: Categorization of changes as new additions, deletions, deprecations, or modifications

### APIs and Integration
- **OpenApiCompare Public API**: Static factory methods for comparing specs from files, URLs, strings, or parsed objects
- **OpenApiDiffOptions Configuration**: Builder pattern for YAML configuration files, property overrides, and custom path matchers
- **ChangedOpenApi Result Model**: Comprehensive result object with lists of new/missing/deprecated endpoints, changed operations, compatibility status
- **Maven Plugin**: Integration into Maven build lifecycle with configuration for spec locations, output files, and fail-on conditions
- **Command-Line Interface**: Full-featured CLI with multiple output formats, authorization support, and CI/CD exit codes
- **Docker Container**: Containerized deployment with AppCDS optimization for fast startup

### Output Formats and Rendering
- **HTML Rendering**: Styled HTML output with j2html, visual change highlighting, detailed and summary modes
- **Markdown Export**: GitHub-flavored Markdown suitable for documentation and release notes
- **AsciiDoc Format**: Technical documentation format support
- **JSON Output**: Machine-readable JSON for programmatic processing and integration
- **Console Rendering**: ASCII art formatted text for terminal display

### Extension and Customization
- **PathMatcher Interface**: Customizable path matching strategies (default treats `/users/{id}` as matching `/users/{userId}`)
- **ExtensionDiff SPI**: Service Provider Interface for adding custom comparison logic for OpenAPI extensions
- **Configuration System**: YAML-based configuration for controlling incompatibility detection rules
- **Property-Level Control**: Fine-grained configuration of what constitutes breaking changes (enum expansion, required fields, schema changes, etc.)

### Build System and Development
- **Multi-Module Maven Project**: Parent POM coordinating core, cli, maven, and maven-example modules
- **Dependency Management**: Swagger Parser v3, Apache Commons (Collections, Configuration, CLI, Lang3), j2html, SLF4J/Logback, JUnit 5, AssertJ
- **Maven Build Lifecycle**: Standard lifecycle commands, profile-based builds (docker, release), shaded JAR generation for CLI
- **CI/CD Integration**: GitHub Actions workflows for builds, releases, Docker publishing, PR validation
- **Docker Multi-Stage Build**: Optimized container image with AppCDS for improved performance
- **Maven Central Publishing**: Release process with GPG signing, source/javadoc JARs, and automated publishing

### Code Architecture
- **Diff Component Pattern**: Specialized classes for each OpenAPI element type (PathsDiff, SchemaDiff, ParametersDiff, etc.)
- **Changed Model Hierarchy**: Immutable result objects implementing Changed interface with compatibility analysis
- **Central Coordinator**: OpenApiDiff class orchestrating all comparison operations
- **Renderer Pattern**: Pluggable output renderers implementing Render interface
- **Deferred Schema Cache**: Handles circular references and complex schema relationships via two-pass processing

### Use Cases and Integration Patterns
- **CI/CD Pipeline Integration**: Gradle tasks, GitHub Actions workflows, fail-on-incompatible modes
- **API Version Management**: Comparing production vs. development specs before deployment
- **Change Documentation**: Generating release notes and API changelogs from spec differences
- **Contract Testing**: Verifying API implementations remain compatible with published specs
- **API Governance**: Enforcing organizational policies about API evolution
- **Maven Build Integration**: Automatic comparison during Maven verify phase with configurable failure conditions

### Testing and Quality
- **Comprehensive Test Suite**: 106+ test files in core module with extensive test resources
- **Test Organization**: Feature-based test directories (schemaDiff, parameterDiff, etc.)
- **JUnit 5 and AssertJ**: Modern testing framework with fluent assertions
- **Code Coverage**: JaCoCo integration for coverage reporting
- **Code Quality**: SonarCloud analysis, Google Java Format via fmt-maven-plugin
- **Git Hooks**: Automatic code formatting via pre-commit hooks

### Advanced Topics
- **Authorization Support**: HTTP headers and query parameters for accessing protected specs
- **Remote Spec Fetching**: Compare specs from HTTP URLs with authorization
- **Circular Reference Handling**: Advanced schema graph traversal and deferred resolution
- **Configuration Inheritance**: Multiple YAML config files with override precedence
- **Path Parameter Normalization**: Configurable handling of parameterized path matching
- **Extension Processing**: Automatic discovery and invocation of custom ExtensionDiff implementations
