# OpenAPI-diff Code Structure

## Complete Annotated Directory Tree

```
openapi-diff/
├── .circleci/                      # CircleCI configuration (legacy)
├── .github/
│   ├── dependabot.yml             # Automated dependency updates
│   └── workflows/                 # GitHub Actions CI/CD
│       ├── docker-release.yml     # Docker image publishing
│       ├── maven.yml              # Main build workflow
│       ├── maven-release.yml      # Release automation
│       └── pr.yml                 # Pull request validation
├── .mvn/                          # Maven wrapper configuration
├── cli/                           # Command-line interface module
│   ├── pom.xml                    # CLI Maven configuration
│   └── src/
│       └── main/
│           ├── java/
│           │   └── org/openapitools/openapidiff/cli/
│           │       └── Main.java  # CLI entry point
│           └── resources/         # CLI resources
├── core/                          # Core comparison library
│   ├── pom.xml                    # Core Maven configuration
│   └── src/
│       ├── main/
│       │   ├── java/
│       │   │   └── org/openapitools/openapidiff/core/
│       │   │       ├── OpenApiCompare.java        # Public API entry point
│       │   │       ├── compare/                    # Comparison logic
│       │   │       │   ├── OpenApiDiff.java       # Central coordinator
│       │   │       │   ├── OpenApiDiffOptions.java # Configuration
│       │   │       │   ├── PathsDiff.java         # Path comparison
│       │   │       │   ├── PathDiff.java          # Single path comparison
│       │   │       │   ├── OperationDiff.java     # Operation comparison
│       │   │       │   ├── ParametersDiff.java    # Parameters comparison
│       │   │       │   ├── ParameterDiff.java     # Single parameter
│       │   │       │   ├── SchemaDiff.java        # Schema comparison
│       │   │       │   ├── RequestBodyDiff.java   # Request body comparison
│       │   │       │   ├── ResponseDiff.java      # Response comparison
│       │   │       │   ├── ApiResponseDiff.java   # API response comparison
│       │   │       │   ├── ContentDiff.java       # Content comparison
│       │   │       │   ├── MediaTypeDiff.java     # Media type comparison
│       │   │       │   ├── HeadersDiff.java       # Headers comparison
│       │   │       │   ├── HeaderDiff.java        # Single header
│       │   │       │   ├── SecurityRequirementsDiff.java
│       │   │       │   ├── SecurityRequirementDiff.java
│       │   │       │   ├── SecuritySchemeDiff.java
│       │   │       │   ├── OAuthFlowsDiff.java    # OAuth flows
│       │   │       │   ├── OAuthFlowDiff.java     # Single OAuth flow
│       │   │       │   ├── ExtensionsDiff.java    # Extensions comparison
│       │   │       │   ├── ExtensionDiff.java     # SPI interface
│       │   │       │   ├── MetadataDiff.java      # Metadata comparison
│       │   │       │   ├── OperationIdDiff.java   # Operation ID handling
│       │   │       │   ├── ListDiff.java          # List comparison utility
│       │   │       │   ├── MapKeyDiff.java        # Map comparison utility
│       │   │       │   ├── CacheKey.java          # Caching for schemas
│       │   │       │   ├── SecurityDiffInfo.java  # Security context
│       │   │       │   └── matchers/              # Path matching strategies
│       │   │       │       ├── PathMatcher.java   # Interface
│       │   │       │       └── DefaultPathMatcher.java
│       │   │       ├── exception/
│       │   │       │   └── RendererException.java # Rendering errors
│       │   │       ├── model/                     # Data model
│       │   │       │   ├── Changed.java           # Base interface
│       │   │       │   ├── ChangedOpenApi.java    # Root result object
│       │   │       │   ├── ChangedOperation.java  # Operation changes
│       │   │       │   ├── ChangedParameter.java  # Parameter changes
│       │   │       │   ├── ChangedParameters.java # Parameters list
│       │   │       │   ├── ChangedSchema.java     # Schema changes
│       │   │       │   ├── ChangedContent.java    # Content changes
│       │   │       │   ├── ChangedMediaType.java  # Media type changes
│       │   │       │   ├── ChangedResponse.java   # Response changes
│       │   │       │   ├── ChangedApiResponse.java
│       │   │       │   ├── ChangedHeader.java     # Header changes
│       │   │       │   ├── ChangedHeaders.java
│       │   │       │   ├── ChangedExtensions.java # Extensions changes
│       │   │       │   ├── ChangedMetadata.java   # Metadata changes
│       │   │       │   ├── ChangedPaths.java      # Paths changes
│       │   │       │   ├── ChangedPath.java       # Single path
│       │   │       │   ├── ChangedList.java       # Generic list changes
│       │   │       │   ├── ChangedSecurityRequirements.java
│       │   │       │   ├── ChangedSecurityRequirement.java
│       │   │       │   ├── ChangedSecurityScheme.java
│       │   │       │   ├── ChangedSecuritySchemeScopes.java
│       │   │       │   ├── ChangedOAuthFlows.java
│       │   │       │   ├── ChangedExample.java
│       │   │       │   ├── ComposedChanged.java   # Composite changes
│       │   │       │   ├── DiffResult.java        # Result enumeration
│       │   │       │   ├── Endpoint.java          # Endpoint representation
│       │   │       │   ├── BackwardIncompatibleProp.java
│       │   │       │   ├── Change.java            # Generic change
│       │   │       │   ├── DiffContext.java       # Comparison context
│       │   │       │   ├── deferred/              # Deferred processing
│       │   │       │   │   ├── DeferredChanged.java
│       │   │       │   │   ├── RealizedChanged.java
│       │   │       │   │   ├── DeferredSchemaCache.java
│       │   │       │   │   ├── DeferredLogger.java
│       │   │       │   │   └── RecursiveSchemaSet.java
│       │   │       │   └── schema/                # Schema-specific models
│       │   │       │       ├── ChangedMaxLength.java
│       │   │       │       ├── ChangedMinLength.java
│       │   │       │       ├── ChangedMaxProperties.java
│       │   │       │       └── [other schema constraints]
│       │   │       ├── output/                    # Rendering engines
│       │   │       │   ├── Render.java           # Base interface
│       │   │       │   ├── ConsoleRender.java    # Text output
│       │   │       │   ├── HtmlRender.java       # HTML output
│       │   │       │   ├── MarkdownRender.java   # Markdown output
│       │   │       │   ├── AsciidocRender.java   # AsciiDoc output
│       │   │       │   ├── JsonRender.java       # JSON output
│       │   │       │   └── HttpStatus.java       # HTTP status utilities
│       │   │       └── utils/                     # Utility classes
│       │   │           ├── EndpointUtils.java    # Endpoint conversion
│       │   │           ├── ChangedUtils.java     # Change utilities
│       │   │           ├── Copy.java             # Deep copy utilities
│       │   │           ├── FileUtils.java        # File operations
│       │   │           ├── RefPointer.java       # Reference resolution
│       │   │           └── RefType.java          # Reference type enum
│       │   └── resources/
│       │       └── META-INF/services/
│       │           └── org.openapitools.openapidiff.core.compare.ExtensionDiff
│       └── test/
│           ├── java/                              # Unit tests (106 files)
│           └── resources/                         # Test fixtures
│               ├── *.json                        # Test OpenAPI specs
│               ├── *.yaml                        # Test OpenAPI specs
│               ├── parameterDiff/                # Parameter test cases
│               ├── schemaDiff/                   # Schema test cases
│               └── [other test directories]
├── maven/                         # Maven plugin module
│   ├── pom.xml                    # Maven plugin configuration
│   └── src/
│       ├── main/
│       │   └── java/
│       │       └── org/openapitools/openapidiff/maven/
│       │           └── OpenApiDiffMojo.java  # Maven goal implementation
│       └── test/
│           ├── java/                         # Plugin tests
│           └── resources/                    # Test resources
├── maven-example/                 # Example Maven project
│   └── pom.xml                    # Example usage
├── pom.xml                        # Parent POM
├── Dockerfile                     # Docker image definition
├── .dockerignore                  # Docker build exclusions
├── .gitignore                     # Git exclusions
├── .gitpod.yml                    # Gitpod configuration
├── mvnw                           # Maven wrapper script
├── mvnw.cmd                       # Maven wrapper (Windows)
├── README.md                      # Project documentation
├── CONTRIBUTING.md                # Contribution guidelines
├── CODE_OF_CONDUCT.md             # Community standards
└── LICENSE                        # Apache 2.0 license
```

## Module and Package Organization

### Multi-Module Maven Structure

The project uses a parent-child Maven multi-module structure:

**Parent Module (`openapi-diff-parent`):**
- Coordinates all child modules
- Manages dependency versions centrally via `<dependencyManagement>`
- Defines common build plugins and configurations
- Version: 2.1.8-SNAPSHOT
- Group ID: `org.openapitools.openapidiff`

**Child Modules:**

1. **core** - Core library (`openapi-diff-core`)
   - Artifact type: JAR
   - Published to Maven Central
   - No dependencies on other project modules
   - Used by CLI and Maven plugin modules

2. **cli** - Command-line tool (`openapi-diff-cli`)
   - Artifact type: Shaded JAR (uber-JAR)
   - Depends on: core
   - Main class: `org.openapitools.openapidiff.cli.Main`
   - Used for standalone execution and Docker image

3. **maven** - Maven plugin (`openapi-diff-maven`)
   - Artifact type: Maven plugin
   - Depends on: core
   - Goal prefix: `openapi-diff`
   - Integrates into Maven build lifecycle

4. **maven-example** - Example project
   - Demonstrates Maven plugin usage
   - Not published as artifact

## Main Source Directories and Their Purposes

### core/src/main/java

**Package: `org.openapitools.openapidiff.core`**
Root package containing the public API entry point.

**Package: `org.openapitools.openapidiff.core.compare`**
The comparison engine - contains all "Diff" classes responsible for comparing specific OpenAPI elements. Each Diff class follows a consistent pattern: it has access to the central `OpenApiDiff` coordinator and compares old vs. new versions of a specific element type.

**Package: `org.openapitools.openapidiff.core.compare.matchers`**
Path matching strategies. The `PathMatcher` interface allows customization of how paths are matched during comparison (e.g., treating `/users/{id}` as equivalent to `/users/{userId}`).

**Package: `org.openapitools.openapidiff.core.model`**
Data transfer objects representing detected changes. All "Changed*" classes implement the `Changed` interface and track what was added, removed, or modified.

**Package: `org.openapitools.openapidiff.core.model.deferred`**
Handles deferred schema processing to resolve circular references and complex schema relationships. The `DeferredSchemaCache` accumulates schemas during the first comparison pass and resolves them in the second pass.

**Package: `org.openapitools.openapidiff.core.model.schema`**
Schema-specific change models for tracking changes to schema constraints like maxLength, minLength, maxProperties, etc.

**Package: `org.openapitools.openapidiff.core.output`**
Rendering engines that transform `ChangedOpenApi` objects into various output formats (HTML, Markdown, AsciiDoc, JSON, console text).

**Package: `org.openapitools.openapidiff.core.utils`**
Utility classes for endpoint conversion, reference resolution, deep copying, and file operations.

**Package: `org.openapitools.openapidiff.core.exception`**
Custom exceptions for rendering and comparison errors.

### cli/src/main/java

**Package: `org.openapitools.openapidiff.cli`**
Contains only the `Main` class, which implements the command-line interface using Apache Commons CLI. Parses arguments, configures logging, invokes the core comparison, and writes output to specified files or console.

### maven/src/main/java

**Package: `org.openapitools.openapidiff.maven`**
Contains the `OpenApiDiffMojo` class, which implements the Maven plugin goal. Annotated with Maven plugin annotations to integrate into the Maven lifecycle.

## Key Files and Their Roles

### Core Library

**`OpenApiCompare.java`** (183 lines)
Public API facade providing static factory methods for comparing OpenAPI specs. Offers multiple overloaded methods accepting specifications as:
- File paths
- File objects
- HTTP URLs
- String content
- Parsed OpenAPI objects

Handles parsing via Swagger Parser and delegates to `OpenApiDiff` for comparison.

**`OpenApiDiff.java`** (303 lines)
Central coordinator orchestrating all comparison operations. Initializes specialized Diff components, manages two-pass comparison algorithm, handles deferred schema processing, and constructs the final `ChangedOpenApi` result. All Diff components reference this coordinator to access other Diff components when needed.

**`OpenApiDiffOptions.java`** (62 lines)
Configuration object built via Builder pattern. Supports:
- YAML configuration files
- Individual property overrides
- Custom PathMatcher implementation
Uses Apache Commons Configuration2 for flexible configuration merging.

**`ChangedOpenApi.java`** (163 lines)
Root result object returned by comparison. Contains:
- Lists of new, missing, and deprecated endpoints
- List of changed operations
- Changed extensions
- Changed schemas
- References to old and new OpenAPI specifications
Implements `ComposedChanged` for compatibility analysis.

**`SchemaDiff.java`**
Complex comparison logic for JSON schemas. Handles:
- Composed schemas (allOf, oneOf, anyOf)
- Schema properties and required fields
- Type changes and format changes
- Constraint changes (min/max, pattern, etc.)
- Circular reference detection
- Deferred processing for complex schema graphs

**Main.java** (304 lines)
CLI entry point. Implements comprehensive command-line argument parsing with support for:
- Multiple output formats (HTML, Markdown, AsciiDoc, JSON, text)
- Log level control
- Authorization headers/query parameters
- Configuration files and properties
- Fail-on conditions for CI/CD
- State-only output mode

### Output Renderers

**`HtmlRender.java`** (~22KB)
Generates styled HTML using j2html library. Supports detailed and summary modes. Highlights incompatible changes with visual indicators.

**`MarkdownRender.java`** (~23KB)
Generates GitHub-flavored Markdown suitable for documentation and release notes.

**`ConsoleRender.java`** (~14KB)
Generates ASCII art formatted text output for terminal display.

**`JsonRender.java`** (~1.1KB)
Simple JSON serialization of the ChangedOpenApi object using Jackson (via Swagger Parser dependency).

## Code Organization Patterns

### Diff Component Pattern

Each OpenAPI element has a corresponding Diff class following this pattern:

```java
public class ElementDiff {
    private final OpenApiDiff openApiDiff;  // Coordinator reference

    public ElementDiff(OpenApiDiff openApiDiff) {
        this.openApiDiff = openApiDiff;
    }

    public Optional<ChangedElement> diff(Element oldElement, Element newElement) {
        // Comparison logic
        // Can access other Diff components via openApiDiff
        return Optional.of(changedElement);
    }
}
```

### Changed Model Pattern

All change models implement the `Changed` interface:

```java
public interface Changed {
    DiffResult isChanged();
    boolean isDifferent();
    // Other methods
}
```

### Two-Pass Comparison Algorithm

1. **First Pass:** PathsDiff traverses all paths and operations, collecting schemas into DeferredSchemaCache without fully resolving them
2. **Second Pass:** DeferredSchemaCache.process() resolves all collected schemas, handling circular references
3. **Result Assembly:** ChangedOpenApi aggregates all detected changes

### Extension Point via SPI

Custom comparison logic can be added by:
1. Implementing `ExtensionDiff` interface
2. Registering implementation in `META-INF/services/org.openapitools.openapidiff.core.compare.ExtensionDiff`

### Builder Pattern for Configuration

`OpenApiDiffOptions.Builder` allows fluent configuration construction:

```java
OpenApiDiffOptions options = OpenApiDiffOptions.builder()
    .configYaml(new File("config.yaml"))
    .configProperty("incompatible.response.enum.increased", "false")
    .pathMatcher(new CustomPathMatcher())
    .build();
```

### Immutable Result Objects

All Changed* model objects are immutable after construction, using builder-style setters that return `this` for chaining during initial construction only.
