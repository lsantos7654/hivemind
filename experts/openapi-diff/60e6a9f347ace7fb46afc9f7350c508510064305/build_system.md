# OpenAPI-diff Build System

## Build System Type and Configuration Files

OpenAPI-diff uses **Apache Maven** as its build system, implementing a multi-module Maven project structure. The project requires Java 8 or higher for compilation and runtime.

### Primary Configuration Files

**`pom.xml` (Parent POM)** - Root configuration at repository root
- Coordinates: `org.openapitools.openapidiff:openapi-diff-parent:2.1.8-SNAPSHOT`
- Packaging: `pom` (parent POM)
- Defines 4 child modules: core, cli, maven, maven-example
- Establishes dependency versions via `<dependencyManagement>`
- Configures shared build plugins and properties
- Defines release and docker build profiles
- Sets up Maven Central and Sonatype OSSRH distribution

**Module-Specific POMs:**
- `core/pom.xml` - Core library configuration
- `cli/pom.xml` - CLI application with Maven Shade plugin
- `maven/pom.xml` - Maven plugin configuration
- `maven-example/pom.xml` - Example project demonstrating usage

**Maven Wrapper:**
- `mvnw` / `mvnw.cmd` - Maven wrapper scripts for version consistency
- `.mvn/` - Maven wrapper configuration directory

**Build Properties (from parent POM):**
```xml
<maven.compiler.source>1.8</maven.compiler.source>
<maven.compiler.target>1.8</maven.compiler.target>
<project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
<swagger-parser.version>2.1.31</swagger-parser.version>
<slf4j.version>2.0.17</slf4j.version>
```

## External Dependencies and Management

### Dependency Management Strategy

All dependency versions are centralized in the parent POM's `<dependencyManagement>` section, ensuring consistency across modules. Child modules inherit these versions without specifying version numbers.

### Core Library Dependencies (core module)

**Primary Dependencies:**

1. **Swagger Parser v3 (v2.1.31)**
   ```xml
   <dependency>
       <groupId>io.swagger.parser.v3</groupId>
       <artifactId>swagger-parser-v3</artifactId>
   </dependency>
   ```
   - Purpose: Parsing OpenAPI 3.x specifications from files and URLs
   - Provides OpenAPI object model
   - Includes Jackson for JSON/YAML serialization

2. **Swagger Parser (v2.1.31)**
   ```xml
   <dependency>
       <groupId>io.swagger.parser.v3</groupId>
       <artifactId>swagger-parser</artifactId>
   </dependency>
   ```
   - Core parsing functionality

3. **Swagger Parser v2 Converter (v2.1.31)**
   ```xml
   <dependency>
       <groupId>io.swagger.parser.v3</groupId>
       <artifactId>swagger-parser-v2-converter</artifactId>
   </dependency>
   ```
   - Converts Swagger 2.0 specs to OpenAPI 3.x
   - Excludes commons-logging (replaced with jcl-over-slf4j)

4. **j2html (v1.6.0)**
   ```xml
   <dependency>
       <groupId>com.j2html</groupId>
       <artifactId>j2html</artifactId>
   </dependency>
   ```
   - Type-safe HTML generation for HtmlRender

5. **Apache Commons Collections4 (v4.5.0)**
   ```xml
   <dependency>
       <groupId>org.apache.commons</groupId>
       <artifactId>commons-collections4</artifactId>
   </dependency>
   ```
   - Advanced collection utilities

6. **Apache Commons Configuration2 (v2.13.0)**
   ```xml
   <dependency>
       <groupId>org.apache.commons</groupId>
       <artifactId>commons-configuration2</artifactId>
   </dependency>
   ```
   - YAML and properties configuration file parsing

7. **SLF4J API (v2.0.17)**
   ```xml
   <dependency>
       <groupId>org.slf4j</groupId>
       <artifactId>slf4j-api</artifactId>
   </dependency>
   ```
   - Logging facade

8. **jcl-over-slf4j (v2.0.17)**
   ```xml
   <dependency>
       <groupId>org.slf4j</groupId>
       <artifactId>jcl-over-slf4j</artifactId>
   </dependency>
   ```
   - Redirects Apache Commons Logging to SLF4J

**Test Dependencies:**

1. **JUnit 5 (Jupiter) (v5.14.2)**
   - Managed via junit-bom
   - Scope: test
   - Modern testing framework

2. **AssertJ (v3.27.7)**
   - Fluent assertion library
   - Scope: test

3. **SLF4J Simple (v2.0.17)**
   - Simple logging implementation for tests
   - Scope: test

### CLI Module Dependencies

Inherits all core dependencies plus:

1. **Apache Commons CLI (v1.11.0)**
   ```xml
   <dependency>
       <groupId>commons-cli</groupId>
       <artifactId>commons-cli</artifactId>
   </dependency>
   ```
   - Command-line argument parsing

2. **Apache Commons Lang3 (v3.20.0)**
   ```xml
   <dependency>
       <groupId>org.apache.commons</groupId>
       <artifactId>commons-lang3</artifactId>
   </dependency>
   ```
   - String utilities, exception utilities

3. **Logback Classic (v1.3.14)**
   ```xml
   <dependency>
       <groupId>ch.qos.logback</groupId>
       <artifactId>logback-classic</artifactId>
   </dependency>
   ```
   - SLF4J implementation with configurable log levels

### Maven Plugin Dependencies

1. **Maven Plugin API (v3.6.0)**
   - Scope: provided
   - Required for plugin development

2. **Maven Core (v3.6.0)**
   - Scope: provided
   - Maven runtime integration

3. **Maven Plugin Annotations (v3.4)**
   - Scope: provided
   - Annotation-based plugin configuration

## Build Targets and Commands

### Standard Maven Lifecycle Commands

**Clean build:**
```bash
./mvnw clean install
```
Removes all generated files and rebuilds all modules, installing to local Maven repository.

**Quick build (skip tests):**
```bash
./mvnw clean install -DskipTests
```
Useful for rapid iteration during development.

**Run tests only:**
```bash
./mvnw test
```
Executes all unit tests across all modules.

**Generate site documentation:**
```bash
./mvnw site
```
Generates project website with reports, javadocs, etc.

### Profile-Specific Builds

**Docker build profile:**
```bash
./mvnw -P docker package
```
Optimized build for Docker image creation:
- Skips tests (`maven.test.skip=true`)
- Skips javadoc generation
- Skips source JAR generation
- Skips install phase
- Skips deploy phase
- Skips fmt (formatting) checks

**Release profile:**
```bash
./mvnw -P release deploy
```
Production release build that:
- Signs artifacts with GPG
- Generates source JARs
- Generates javadoc JARs
- Publishes to Maven Central via central-publishing-maven-plugin

### Module-Specific Commands

**Build core library only:**
```bash
./mvnw -pl core clean install
```

**Build CLI with all dependencies:**
```bash
./mvnw -pl cli clean package
```
Generates shaded JAR at `cli/target/openapi-diff-cli-2.1.8-SNAPSHOT-all.jar`

**Build Maven plugin:**
```bash
./mvnw -pl maven clean install
```

### Code Quality Commands

**Format code:**
```bash
./mvnw com.coveo:fmt-maven-plugin:format
```
Automatically formats all Java code according to Google Java Format.

**Run code coverage:**
```bash
./mvnw clean verify
```
Generates JaCoCo coverage reports.

**SonarCloud analysis:**
```bash
./mvnw clean verify sonar:sonar \
  -Dsonar.projectKey=OpenAPITools_openapi-diff \
  -Dsonar.organization=openapitools \
  -Dsonar.host.url=https://sonarcloud.io
```

## How to Build, Test, and Deploy

### Prerequisites

1. **Java Development Kit (JDK) 8 or higher**
   ```bash
   java -version  # Should show 1.8 or higher
   ```

2. **Maven 3.6+** (or use included Maven wrapper)
   ```bash
   ./mvnw --version
   ```

3. **Git** (for cloning repository)

### Building from Source

**Step 1: Clone the repository**
```bash
git clone https://github.com/OpenAPITools/openapi-diff.git
cd openapi-diff
```

**Step 2: Full build with tests**
```bash
./mvnw clean install
```

This command:
1. Cleans all modules
2. Compiles source code (Java 8 target)
3. Runs all unit tests (106 test classes in core module)
4. Packages JARs for each module
5. Installs artifacts to local Maven repository (~/.m2/repository)

**Build artifacts produced:**
- `core/target/openapi-diff-core-2.1.8-SNAPSHOT.jar` - Core library
- `cli/target/openapi-diff-cli-2.1.8-SNAPSHOT.jar` - Thin JAR
- `cli/target/openapi-diff-cli-2.1.8-SNAPSHOT-all.jar` - Shaded JAR (uber-JAR)
- `maven/target/openapi-diff-maven-2.1.8-SNAPSHOT.jar` - Maven plugin

### Testing

**Run all tests:**
```bash
./mvnw test
```

**Run specific test class:**
```bash
./mvnw -Dtest=OpenApiCompareTest test
```

**Run tests with coverage report:**
```bash
./mvnw clean verify
# Coverage report: target/site/jacoco/index.html
```

**Test structure:**
- Core module: ~106 Java test files
- Extensive test resources with sample OpenAPI specs
- Organized by feature area (schemaDiff, parameterDiff, etc.)
- Uses JUnit 5 with AssertJ assertions

### Running the CLI

**After building, run the CLI:**
```bash
java -jar cli/target/openapi-diff-cli-2.1.8-SNAPSHOT-all.jar \
  path/to/old-spec.yaml \
  path/to/new-spec.yaml
```

**With output options:**
```bash
java -jar cli/target/openapi-diff-cli-2.1.8-SNAPSHOT-all.jar \
  old-spec.yaml new-spec.yaml \
  --markdown diff.md \
  --html diff.html \
  --json diff.json
```

### Docker Build

**Build Docker image:**
```bash
docker build -t openapi-diff:local .
```

The Dockerfile uses multi-stage build:
1. **Build stage:** Compiles project using Maven with docker profile
2. **Runtime stage:** Creates minimal JRE-based image
3. **AppCDS optimization:** Pre-generates class data sharing archive for faster startup

**Run Docker container:**
```bash
docker run --rm -v $(pwd):/specs openapi-diff:local \
  /specs/old-spec.yaml /specs/new-spec.yaml
```

### Deploying to Maven Central

**Prerequisites:**
- GPG key configured
- Maven Central credentials in `~/.m2/settings.xml`
- Release permissions for org.openapitools.openapidiff

**Release process:**
```bash
# 1. Prepare release (updates versions, creates tag)
./mvnw release:prepare

# 2. Perform release (builds, signs, deploys)
./mvnw release:perform
```

Or using the release profile directly:
```bash
./mvnw -P release clean deploy
```

This process:
1. Compiles all modules
2. Runs all tests
3. Generates source JARs
4. Generates javadoc JARs
5. Signs all artifacts with GPG
6. Deploys to Maven Central via central-publishing-maven-plugin
7. Automatically publishes (autoPublish=true)

### CI/CD Pipeline (GitHub Actions)

**Main build workflow** (`.github/workflows/maven.yml`):
- Triggered on: push to main/master, pull requests
- Runs on: Ubuntu latest with Java 8, 11, 17, 21
- Steps:
  1. Checkout code
  2. Set up JDK
  3. Cache Maven dependencies
  4. Run `./mvnw verify`
  5. Run SonarCloud analysis (on Java 21 only)

**Release workflow** (`.github/workflows/maven-release.yml`):
- Triggered on: Manual workflow dispatch
- Creates GitHub release
- Publishes to Maven Central

**Docker release workflow** (`.github/workflows/docker-release.yml`):
- Triggered on: GitHub releases
- Builds multi-platform Docker images (amd64, arm64)
- Pushes to Docker Hub as `openapitools/openapi-diff:latest` and versioned tags

**PR workflow** (`.github/workflows/pr.yml`):
- Validates pull requests
- Ensures code formatting
- Runs tests
- Checks for merge conflicts

### IDE Setup

**IntelliJ IDEA:**
1. Import as Maven project
2. Maven will auto-download dependencies
3. Enable annotation processing for Maven plugin module
4. Use Google Java Format plugin (configured via fmt-maven-plugin)

**Eclipse:**
1. Import as Existing Maven Project
2. Install Maven integration (m2e)
3. Configure Java 8 compiler

**VS Code:**
1. Install "Java Extension Pack"
2. Install "Maven for Java"
3. Open project folder
4. VSCode auto-detects Maven structure

### Git Hooks

The project uses `githook-maven-plugin` to install pre-commit hooks:

**Pre-commit hook:**
```bash
./mvnw com.coveo:fmt-maven-plugin:format
```

Automatically formats code before each commit to ensure consistent style.

**Hook installation:**
Hooks are automatically installed when running Maven builds via the githook-maven-plugin configuration in parent POM.
