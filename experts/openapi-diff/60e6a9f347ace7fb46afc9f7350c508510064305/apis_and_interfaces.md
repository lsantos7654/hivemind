# OpenAPI-diff APIs and Interfaces

## Public APIs and Entry Points

### Primary Entry Point: OpenApiCompare

The `OpenApiCompare` class provides the main public API for comparing OpenAPI specifications. Located at `org.openapitools.openapidiff.core.OpenApiCompare`.

**Static Factory Methods:**

All comparison methods return a `ChangedOpenApi` object containing the comparison results.

#### 1. Compare from File Paths (Locations)

```java
// Simple comparison (local files or HTTP URLs)
ChangedOpenApi result = OpenApiCompare.fromLocations(
    "path/to/old-spec.yaml",
    "path/to/new-spec.yaml"
);

// With authorization
List<AuthorizationValue> auths = Collections.singletonList(
    new AuthorizationValue("api-key", "your-key", "header")
);
ChangedOpenApi result = OpenApiCompare.fromLocations(
    "https://api.example.com/openapi.json",
    "https://api-staging.example.com/openapi.json",
    auths
);

// With options
OpenApiDiffOptions options = OpenApiDiffOptions.builder()
    .configYaml(new File("config.yaml"))
    .build();
ChangedOpenApi result = OpenApiCompare.fromLocations(
    oldPath, newPath, auths, options
);
```

**Parameters:**
- `oldLocation` (String): Path to old spec (file path or HTTP URL)
- `newLocation` (String): Path to new spec (file path or HTTP URL)
- `auths` (List<AuthorizationValue>): Optional authorization for HTTP requests
- `options` (OpenApiDiffOptions): Optional configuration options

#### 2. Compare from File Objects

```java
File oldFile = new File("specs/v1.0.0.yaml");
File newFile = new File("specs/v2.0.0.yaml");

ChangedOpenApi result = OpenApiCompare.fromFiles(oldFile, newFile);

// With authorization and options
ChangedOpenApi result = OpenApiCompare.fromFiles(
    oldFile, newFile, auths, options
);
```

#### 3. Compare from String Content

```java
String oldContent = Files.readString(Paths.get("old.yaml"));
String newContent = Files.readString(Paths.get("new.yaml"));

ChangedOpenApi result = OpenApiCompare.fromContents(oldContent, newContent);

// With authorization and options
ChangedOpenApi result = OpenApiCompare.fromContents(
    oldContent, newContent, auths, options
);
```

#### 4. Compare from Parsed OpenAPI Objects

```java
// If you already have parsed OpenAPI objects
OpenAPI oldSpec = parseSpecification("old.yaml");
OpenAPI newSpec = parseSpecification("new.yaml");

ChangedOpenApi result = OpenApiCompare.fromSpecifications(oldSpec, newSpec);

// With options
ChangedOpenApi result = OpenApiCompare.fromSpecifications(
    oldSpec, newSpec, options
);
```

### Configuration: OpenApiDiffOptions

The `OpenApiDiffOptions` class provides configuration for comparison behavior.

**Builder Pattern:**

```java
OpenApiDiffOptions options = OpenApiDiffOptions.builder()
    .configYaml(new File("config.yaml"))
    .configProperty("incompatible.response.enum.increased", "false")
    .configProperty("incompatible.request.parameter.required.increased", "false")
    .pathMatcher(new CustomPathMatcher())
    .build();
```

**Configuration Methods:**

1. **`configYaml(File file)`** - Load YAML configuration file
   - Supports Apache Commons Configuration2 YAML format
   - Multiple files can be loaded (later files override earlier)
   - Properties control what changes are considered incompatible

2. **`configProperty(String key, String value)`** - Set individual property
   - Overrides YAML configuration
   - Key-value format
   - Example keys:
     - `incompatible.response.enum.increased`
     - `incompatible.request.parameter.required.increased`
     - `incompatible.response.schema.changed`

3. **`pathMatcher(PathMatcher matcher)`** - Custom path matching strategy
   - Default: `DefaultPathMatcher` (treats `/users/{id}` as matching `/users/{userId}`)
   - Implement `PathMatcher` interface for custom logic

**Example YAML Configuration:**

```yaml
# config.yaml
incompatible:
  response:
    enum:
      increased: false  # Don't treat enum expansion as breaking
  request:
    parameter:
      required:
        increased: true  # Treat new required params as breaking
```

## Key Classes and Functions

### Result Object: ChangedOpenApi

The main result object returned by all comparison operations.

**Key Methods:**

```java
ChangedOpenApi result = OpenApiCompare.fromLocations(old, new);

// Access comparison results
List<Endpoint> newEndpoints = result.getNewEndpoints();
List<Endpoint> missingEndpoints = result.getMissingEndpoints();
List<Endpoint> deprecatedEndpoints = result.getDeprecatedEndpoints();
List<ChangedOperation> changedOps = result.getChangedOperations();
List<ChangedSchema> changedSchemas = result.getChangedSchemas();
ChangedExtensions extensions = result.getChangedExtensions();

// Compatibility analysis
DiffResult diffResult = result.isChanged();  // NO_CHANGES, COMPATIBLE, INCOMPATIBLE
boolean hasChanges = result.isDifferent();
boolean isCompatible = result.isCompatible();
boolean isIncompatible = result.isIncompatible();
boolean noChanges = result.isUnchanged();

// Access original specs
OpenAPI oldSpec = result.getOldSpecOpenApi();
OpenAPI newSpec = result.getNewSpecOpenApi();
```

**DiffResult Enumeration:**
- `NO_CHANGES` - Specifications are identical
- `COMPATIBLE` - Changes exist but are backward compatible
- `INCOMPATIBLE` - Breaking changes detected

### Endpoint Model

Represents an API endpoint (path + HTTP method).

```java
public class Endpoint {
    private String pathUrl;      // e.g., "/users/{id}"
    private HttpMethod method;   // GET, POST, PUT, DELETE, etc.
    private String summary;      // Operation summary
    private Operation operation; // Full OpenAPI Operation object
}
```

### ChangedOperation Model

Represents changes to a specific operation.

```java
public class ChangedOperation {
    private String pathUrl;
    private HttpMethod httpMethod;
    private String summary;

    // Changes detected
    private ChangedParameters parameters;
    private ChangedRequestBody requestBody;
    private ChangedApiResponse apiResponses;
    private ChangedSecurityRequirements securityRequirements;
    private ChangedExtensions extensions;

    // Compatibility
    DiffResult isChanged();
    boolean isDeprecated();
}
```

## Usage Examples with Code Snippets

### Example 1: Basic Comparison

```java
import org.openapitools.openapidiff.core.OpenApiCompare;
import org.openapitools.openapidiff.core.model.ChangedOpenApi;
import org.openapitools.openapidiff.core.model.DiffResult;

public class BasicComparison {
    public static void main(String[] args) {
        // Compare two specifications
        ChangedOpenApi diff = OpenApiCompare.fromLocations(
            "specs/v1.0.0.yaml",
            "specs/v2.0.0.yaml"
        );

        // Check if there are breaking changes
        if (diff.isIncompatible()) {
            System.err.println("ERROR: Breaking changes detected!");
            System.exit(1);
        }

        // Print summary
        System.out.println("New endpoints: " + diff.getNewEndpoints().size());
        System.out.println("Removed endpoints: " + diff.getMissingEndpoints().size());
        System.out.println("Changed operations: " + diff.getChangedOperations().size());
        System.out.println("Status: " + diff.isChanged().getValue());
    }
}
```

### Example 2: Generate HTML Report

```java
import org.openapitools.openapidiff.core.OpenApiCompare;
import org.openapitools.openapidiff.core.model.ChangedOpenApi;
import org.openapitools.openapidiff.core.output.HtmlRender;

import java.io.FileOutputStream;
import java.io.OutputStreamWriter;

public class HtmlReportGenerator {
    public static void main(String[] args) throws Exception {
        // Compare specs
        ChangedOpenApi diff = OpenApiCompare.fromLocations(
            "old-spec.yaml",
            "new-spec.yaml"
        );

        // Generate HTML report
        HtmlRender htmlRender = new HtmlRender(
            "API Changelog",
            "https://example.com/styles.css"  // Optional custom CSS
        );

        try (FileOutputStream fos = new FileOutputStream("api-diff.html");
             OutputStreamWriter writer = new OutputStreamWriter(fos)) {
            htmlRender.render(diff, writer);
        }

        System.out.println("Report generated: api-diff.html");
    }
}
```

### Example 3: Custom Configuration

```java
import org.openapitools.openapidiff.core.OpenApiCompare;
import org.openapitools.openapidiff.core.compare.OpenApiDiffOptions;
import org.openapitools.openapidiff.core.model.ChangedOpenApi;

import java.io.File;

public class CustomConfiguration {
    public static void main(String[] args) {
        // Build custom options
        OpenApiDiffOptions options = OpenApiDiffOptions.builder()
            .configYaml(new File("diff-config.yaml"))
            .configProperty("incompatible.response.enum.increased", "false")
            .configProperty("incompatible.request.required.increased", "true")
            .build();

        // Compare with options
        ChangedOpenApi diff = OpenApiCompare.fromLocations(
            "old-spec.yaml",
            "new-spec.yaml",
            null,  // No authorization
            options
        );

        // Process results
        processChanges(diff);
    }

    private static void processChanges(ChangedOpenApi diff) {
        // Custom processing logic
        diff.getChangedOperations().forEach(op -> {
            System.out.println("Changed: " + op.getHttpMethod() + " " + op.getPathUrl());
            if (op.isDeprecated()) {
                System.out.println("  - Operation is now deprecated");
            }
        });
    }
}
```

### Example 4: Multiple Output Formats

```java
import org.openapitools.openapidiff.core.OpenApiCompare;
import org.openapitools.openapidiff.core.model.ChangedOpenApi;
import org.openapitools.openapidiff.core.output.*;

import java.io.FileOutputStream;
import java.io.OutputStreamWriter;

public class MultiFormatOutput {
    public static void main(String[] args) throws Exception {
        ChangedOpenApi diff = OpenApiCompare.fromLocations(
            "old-spec.yaml", "new-spec.yaml"
        );

        // Generate HTML
        HtmlRender htmlRender = new HtmlRender();
        writeOutput(diff, htmlRender, "diff.html");

        // Generate Markdown
        MarkdownRender mdRender = new MarkdownRender();
        writeOutput(diff, mdRender, "diff.md");

        // Generate JSON
        JsonRender jsonRender = new JsonRender();
        writeOutput(diff, jsonRender, "diff.json");

        // Generate AsciiDoc
        AsciidocRender adocRender = new AsciidocRender();
        writeOutput(diff, adocRender, "diff.adoc");

        System.out.println("All formats generated successfully!");
    }

    private static void writeOutput(ChangedOpenApi diff, Render render,
                                     String filename) throws Exception {
        try (FileOutputStream fos = new FileOutputStream(filename);
             OutputStreamWriter writer = new OutputStreamWriter(fos)) {
            render.render(diff, writer);
        }
    }
}
```

### Example 5: Authorization for Remote Specs

```java
import io.swagger.v3.parser.core.models.AuthorizationValue;
import org.openapitools.openapidiff.core.OpenApiCompare;
import org.openapitools.openapidiff.core.model.ChangedOpenApi;

import java.util.Collections;
import java.util.List;

public class RemoteSpecComparison {
    public static void main(String[] args) {
        // Set up authorization
        List<AuthorizationValue> auths = Collections.singletonList(
            new AuthorizationValue(
                "Authorization",           // Header name
                "Bearer eyJhbGc...",       // Token value
                "header"                   // Type: header or query
            )
        );

        // Compare remote specs
        ChangedOpenApi diff = OpenApiCompare.fromLocations(
            "https://api.prod.example.com/openapi.json",
            "https://api.staging.example.com/openapi.json",
            auths
        );

        // Process results
        if (diff.isDifferent()) {
            System.out.println("APIs differ!");
            diff.getNewEndpoints().forEach(endpoint ->
                System.out.println("New: " + endpoint.getMethod() + " " +
                                   endpoint.getPathUrl())
            );
        }
    }
}
```

### Example 6: Custom Path Matcher

```java
import org.openapitools.openapidiff.core.OpenApiCompare;
import org.openapitools.openapidiff.core.compare.OpenApiDiffOptions;
import org.openapitools.openapidiff.core.compare.matchers.PathMatcher;
import org.openapitools.openapidiff.core.model.ChangedOpenApi;

import java.util.*;

public class CustomPathMatchingExample {

    // Custom matcher that requires exact path parameter names
    static class StrictPathMatcher implements PathMatcher {
        @Override
        public Map<String, String> match(Set<String> oldPaths, Set<String> newPaths) {
            Map<String, String> matches = new HashMap<>();
            for (String oldPath : oldPaths) {
                if (newPaths.contains(oldPath)) {
                    matches.put(oldPath, oldPath);
                }
            }
            return matches;
        }
    }

    public static void main(String[] args) {
        OpenApiDiffOptions options = OpenApiDiffOptions.builder()
            .pathMatcher(new StrictPathMatcher())
            .build();

        ChangedOpenApi diff = OpenApiCompare.fromLocations(
            "old-spec.yaml",
            "new-spec.yaml",
            null,
            options
        );

        // With strict matching, /users/{id} != /users/{userId}
        // They would be treated as different endpoints
        System.out.println("New endpoints: " + diff.getNewEndpoints().size());
        System.out.println("Missing endpoints: " + diff.getMissingEndpoints().size());
    }
}
```

## Integration Patterns and Workflows

### Pattern 1: CI/CD Pipeline Integration

**Gradle Task Example:**

```groovy
task compareOpenApi(type: JavaExec) {
    classpath = configurations.openApiDiff
    main = 'org.openapitools.openapidiff.cli.Main'
    args = [
        'src/main/resources/openapi-prod.yaml',
        'build/generated/openapi.yaml',
        '--fail-on-incompatible',
        '--markdown', 'build/reports/api-diff.md'
    ]
}

dependencies {
    openApiDiff 'org.openapitools.openapidiff:openapi-diff-cli:2.1.8:all'
}
```

**GitHub Actions Workflow:**

```yaml
name: API Compatibility Check
on: [pull_request]

jobs:
  check-api:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Java
        uses: actions/setup-java@v3
        with:
          java-version: '11'

      - name: Download openapi-diff
        run: |
          wget https://github.com/OpenAPITools/openapi-diff/releases/download/2.1.7/openapi-diff-cli-2.1.7-all.jar

      - name: Compare APIs
        run: |
          java -jar openapi-diff-cli-2.1.7-all.jar \
            main-branch-spec.yaml \
            pr-branch-spec.yaml \
            --fail-on-incompatible \
            --markdown api-diff.md

      - name: Comment PR
        uses: actions/github-script@v6
        if: failure()
        with:
          script: |
            const fs = require('fs');
            const diff = fs.readFileSync('api-diff.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '## ⚠️ API Breaking Changes Detected\n\n' + diff
            });
```

### Pattern 2: Maven Plugin Integration

**POM Configuration:**

```xml
<plugin>
    <groupId>org.openapitools.openapidiff</groupId>
    <artifactId>openapi-diff-maven</artifactId>
    <version>2.1.8</version>
    <executions>
        <execution>
            <phase>verify</phase>
            <goals>
                <goal>diff</goal>
            </goals>
            <configuration>
                <!-- Production spec -->
                <oldSpec>https://api.example.com/openapi.json</oldSpec>
                <!-- Generated spec from build -->
                <newSpec>${project.build.directory}/generated-spec.yaml</newSpec>

                <!-- Fail build on incompatible changes -->
                <failOnIncompatible>true</failOnIncompatible>

                <!-- Generate reports -->
                <markdownOutputFileName>target/api-diff.md</markdownOutputFileName>
                <htmlOutputFileName>target/api-diff.html</htmlOutputFileName>
                <jsonOutputFileName>target/api-diff.json</jsonOutputFileName>

                <!-- Configuration -->
                <configFiles>
                    <configFile>src/test/resources/api-diff-config.yaml</configFile>
                </configFiles>
            </configuration>
        </execution>
    </executions>
</plugin>
```

### Pattern 3: Spring Boot Integration

```java
import org.openapitools.openapidiff.core.OpenApiCompare;
import org.openapitools.openapidiff.core.model.ChangedOpenApi;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

@Component
public class ApiCompatibilityChecker {

    @EventListener(ApplicationReadyEvent.class)
    public void checkApiCompatibility() {
        try {
            ChangedOpenApi diff = OpenApiCompare.fromLocations(
                "classpath:openapi-v1.yaml",
                "http://localhost:8080/v3/api-docs"  // Current running API
            );

            if (diff.isIncompatible()) {
                throw new IllegalStateException(
                    "API implementation breaks backward compatibility!"
                );
            }
        } catch (Exception e) {
            // Handle comparison failure
            e.printStackTrace();
        }
    }
}
```

## Configuration Options and Extension Points

### Configuration Properties

Properties can be set via YAML files or programmatically to control incompatibility detection:

**Common Configuration Keys:**

```yaml
incompatible:
  # Response changes
  response:
    schema:
      changed: true              # Any schema change is breaking
    enum:
      increased: false           # Adding enum values is NOT breaking
      decreased: true            # Removing enum values IS breaking
    required:
      increased: true            # New required response fields IS breaking

  # Request changes
  request:
    parameter:
      required:
        increased: true          # New required params IS breaking
        decreased: false         # Removing required params is NOT breaking
    schema:
      changed: true              # Request schema changes are breaking

  # Endpoint changes
  openapi:
    endpoints:
      decreased: true            # Removing endpoints IS breaking
```

### Extension Point: ExtensionDiff Interface

Custom comparison logic can be added via the SPI mechanism:

**1. Implement the interface:**

```java
package com.example;

import org.openapitools.openapidiff.core.compare.ExtensionDiff;
import org.openapitools.openapidiff.core.compare.OpenApiDiff;
import org.openapitools.openapidiff.core.model.Change;
import org.openapitools.openapidiff.core.model.Changed;
import org.openapitools.openapidiff.core.model.DiffContext;

public class CustomExtensionDiff implements ExtensionDiff {
    private OpenApiDiff openApiDiff;

    @Override
    public ExtensionDiff setOpenApiDiff(OpenApiDiff openApiDiff) {
        this.openApiDiff = openApiDiff;
        return this;
    }

    @Override
    public String getName() {
        return "x-custom-extension";  // Extension name to handle
    }

    @Override
    public Changed diff(Change<?> extension, DiffContext context) {
        // Custom comparison logic for your extension
        Object oldValue = extension.getOldValue();
        Object newValue = extension.getNewValue();

        // Return Changed object with your comparison results
        return new CustomChangedExtension(oldValue, newValue);
    }

    @Override
    public boolean isParentApplicable(Change.Type type, Object object,
                                       Object extension, DiffContext context) {
        // Optional: filter when this extension applies
        return true;
    }
}
```

**2. Register via SPI:**

Create file: `src/main/resources/META-INF/services/org.openapitools.openapidiff.core.compare.ExtensionDiff`

```
com.example.CustomExtensionDiff
```

**3. Include in classpath:**

Your custom extension will be automatically discovered and invoked when the specified extension is encountered in OpenAPI specs.
