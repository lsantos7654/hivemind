# Distroless APIs and Interfaces

## Public APIs and Entry Points

The distroless project provides two primary API surfaces: pre-built container images available from Google Container Registry, and Bazel rules for custom image creation.

### Pre-Built Container Images (Primary API)

**Registry**: `gcr.io/distroless/`

All images are published as OCI-compliant container images with multi-architecture support. Images are consumed via standard container tooling (Docker, Kubernetes, Podman, etc.).

**Image Naming Convention**:
```
gcr.io/distroless/<image-type>-<distro>:<tag>-<arch>
```

Where:
- `<image-type>`: static, base, base-nossl, cc, python3, java17/21/25, nodejs20/22/24
- `<distro>`: debian12 (bookworm), debian13 (trixie)
- `<tag>`: latest, nonroot, debug, debug-nonroot
- `<arch>`: amd64, arm64, arm, s390x, ppc64le (optional, defaults to manifest list)

**Distro-Agnostic Tags**: Images without `-debian12` or `-debian13` suffix currently resolve to Debian 13 images (as of the DEFAULT_DISTRO setting). This will change as new Debian versions are released.

### Image Categories

#### Static Binary Images

**`gcr.io/distroless/static-debian12`**

Minimal base for statically-linked binaries (Go, Rust) containing:
- `/etc/passwd`, `/etc/group` (root, nobody, nonroot users)
- CA certificates in `/etc/ssl/certs/`
- Timezone data
- Base filesystem structure

No glibc or dynamic linkers. Size: ~2 MiB.

```dockerfile
FROM gcr.io/distroless/static-debian12
COPY --from=build /app/myapp /myapp
CMD ["/myapp"]
```

#### Base Images

**`gcr.io/distroless/base-debian12`**

Adds dynamic library support for non-specialized applications:
- glibc (libc6)
- OpenSSL (libssl3)
- Zlib, bzip2, xz libraries
- Everything from static image

Use for dynamically-linked applications without language runtimes.

**`gcr.io/distroless/base-nossl-debian12`**

Base image without OpenSSL, for applications providing their own TLS implementation.

#### C/C++ Runtime Images

**`gcr.io/distroless/cc-debian12`**

Extends base with C++ standard library:
- libstdc++
- libgcc
- All base image contents

```dockerfile
FROM gcc:12 as build
WORKDIR /app
COPY . .
RUN g++ -o myapp main.cpp

FROM gcr.io/distroless/cc-debian12
COPY --from=build /app/myapp /
CMD ["/myapp"]
```

#### Java Runtime Images

**`gcr.io/distroless/java-base-debian12`**

Minimal Java base with OpenJDK libraries but no specific JDK version. Rarely used directly.

**`gcr.io/distroless/java17-debian12`**
**`gcr.io/distroless/java21-debian12`**
**`gcr.io/distroless/java25-debian13`**

Complete Java runtime environments with Eclipse Adoptium (Temurin) JDK:

```dockerfile
FROM eclipse-temurin:21-jdk AS build
WORKDIR /app
COPY . .
RUN javac Main.java && jar cfe app.jar Main *.class

FROM gcr.io/distroless/java21-debian12
COPY --from=build /app/app.jar /app.jar
CMD ["/app.jar"]
```

Default entrypoint: `["/usr/bin/java", "-jar"]`

#### Python Runtime Images

**`gcr.io/distroless/python3-debian12`**

Python 3 interpreter and standard library:

```dockerfile
FROM python:3.11 as build
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt
COPY . .

FROM gcr.io/distroless/python3-debian12
COPY --from=build /root/.local /root/.local
COPY --from=build /app /app
WORKDIR /app
ENV PATH=/root/.local/bin:$PATH
CMD ["app.py"]
```

Default entrypoint: `["/usr/bin/python3"]`

#### Node.js Runtime Images

**`gcr.io/distroless/nodejs20-debian12`**
**`gcr.io/distroless/nodejs22-debian12`**
**`gcr.io/distroless/nodejs24-debian13`**

Node.js runtime with npm:

```dockerfile
FROM node:22 as build
WORKDIR /app
COPY package*.json .
RUN npm ci --omit=dev
COPY . .

FROM gcr.io/distroless/nodejs22-debian12
COPY --from=build /app /app
WORKDIR /app
CMD ["server.js"]
```

Default entrypoint: `["/nodejs/bin/node"]`

### Image Variants (Tags)

Every image type supports four tag variants:

**`latest`**: Root user (UID 0), production image
```dockerfile
FROM gcr.io/distroless/static-debian12:latest
```

**`nonroot`**: Non-root user (UID 65532, username "nonroot")
```dockerfile
FROM gcr.io/distroless/static-debian12:nonroot
USER nonroot
```

**`debug`**: Root user with busybox shell
```dockerfile
FROM gcr.io/distroless/static-debian12:debug
# Entrypoint: ["/busybox/sh"]
# PATH includes /busybox
```

**`debug-nonroot`**: Non-root user with busybox shell
```dockerfile
FROM gcr.io/distroless/static-debian12:debug-nonroot
```

Debug images include `/busybox/sh` and set `PATH=$PATH:/busybox`, providing basic shell utilities for debugging.

### Architecture-Specific Tags

Access specific architectures directly:

```dockerfile
# Explicitly use amd64 variant
FROM gcr.io/distroless/static-debian12:latest-amd64

# Explicitly use arm64 variant
FROM gcr.io/distroless/static-debian12:latest-arm64
```

Available suffixes: `-amd64`, `-arm64`, `-arm`, `-s390x`, `-ppc64le`

## Key Classes, Functions, and Macros

### Bazel API (for Custom Images)

#### Image Construction Macros

**`static_image(distro, arch)`** (from `static/static.bzl`)

Constructs minimal static images for a given distribution and architecture.

```starlark
load("//static:static.bzl", "static_image")

static_image(
    distro = "debian12",
    arch = "amd64",
)
```

Creates targets: `static_root_amd64_debian12`, `static_nonroot_amd64_debian12`, `static_debug_root_amd64_debian12`, `static_debug_nonroot_amd64_debian12`

**`base_image(distro, arch, packages)`** (from `base/base.bzl`)

Creates base images with specified Debian packages:

```starlark
load("//base:base.bzl", "base_image")

base_image(
    distro = "debian12",
    arch = "amd64",
    packages = ["netbase", "tzdata", "ca-certificates", "libssl3"],
)
```

**`cc_image(distro, arch, packages)`** (from `cc/cc.bzl`)

C++ runtime images with libstdc++.

**`java_image_index(distro, java_version, architectures)`** (from `java/java.bzl`)

Multi-architecture Java runtime image indexes.

**`python3_image(distro, arch, packages)`** (from `python3/python.bzl`)

Python runtime images.

**`nodejs_image(distro, arch, major_version)`** (from `nodejs/nodejs.bzl`)

Node.js runtime images for specific versions.

#### OCI Image Convenience Wrappers

**`java_image(name, base, layers, ...)`** (from `private/oci/java_image.bzl`)

Simplified Java application containerization:

```starlark
load("//private/oci:defs.bzl", "java_image")

java_image(
    name = "my_java_app",
    base = "//java:java21_root_amd64_debian12",
    layers = [":app_jar_layer"],
    entrypoint = ["/usr/bin/java", "-jar", "/app/app.jar"],
)
```

**`go_image(name, base, binary, ...)`** (from `private/oci/go_image.bzl`)

Go application containerization:

```starlark
load("//private/oci:defs.bzl", "go_image")
load("@rules_go//go:def.bzl", "go_binary")

go_binary(
    name = "app",
    srcs = ["main.go"],
)

go_image(
    name = "app_image",
    base = "//static:static_root_amd64_debian12",
    binary = ":app",
)
```

**`cc_image(name, base, binary, ...)`** (from `private/oci/cc_image.bzl`)

C++ application containerization.

**`rust_image(name, base, binary, ...)`** (from `private/oci/rust_image.bzl`)

Rust application containerization.

#### Utility Functions

**`deb.package(arch, distro, package_name)`** (from `private/util/deb.bzl`)

Constructs Bazel label for a Debian package:

```starlark
load("//private/util:deb.bzl", "deb")

oci_image(
    name = "my_image",
    tars = [
        deb.package("amd64", "debian12", "curl"),
        deb.package("amd64", "debian12", "ca-certificates"),
    ],
)
```

**`deb.version(arch, distro, package_name)`**

Returns package version string from lockfiles:

```starlark
version = deb.version("amd64", "debian12", "libc6")
# Returns: "2.36-9+deb12u4" (or current locked version)
```

**`deb.data(arch, distro, package_name)`**

Returns label to package data files (extracted package contents without metadata).

## Usage Examples with Code Snippets

### Example 1: Simple Go Application

**Multi-stage Dockerfile**:

```dockerfile
# Build stage
FROM golang:1.22 as build
WORKDIR /go/src/app
COPY . .
RUN go mod download
RUN CGO_ENABLED=0 go build -o /go/bin/app

# Runtime stage
FROM gcr.io/distroless/static-debian12
COPY --from=build /go/bin/app /
CMD ["/app"]
```

Build and run:
```bash
docker build -t myapp .
docker run myapp
```

### Example 2: Java Application with Non-Root User

```dockerfile
FROM eclipse-temurin:21-jdk AS build
COPY . /workspace
WORKDIR /workspace
RUN javac Main.java && jar cfe app.jar Main *.class

FROM gcr.io/distroless/java21-debian12:nonroot
COPY --from=build /workspace/app.jar /app/app.jar
WORKDIR /app
CMD ["app.jar"]
```

The `:nonroot` variant runs as UID 65532, improving security.

### Example 3: Python Application with Dependencies

```dockerfile
FROM python:3.11-slim as build
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt
COPY . .

FROM gcr.io/distroless/python3-debian12
COPY --from=build /root/.local /home/nonroot/.local
COPY --from=build /app /app
WORKDIR /app
ENV PATH=/home/nonroot/.local/bin:$PATH
ENV PYTHONPATH=/home/nonroot/.local/lib/python3.11/site-packages
CMD ["server.py"]
```

### Example 4: Node.js Express Application

```dockerfile
FROM node:22 as build
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev
COPY . .

FROM gcr.io/distroless/nodejs22-debian12:nonroot
COPY --from=build /app /app
WORKDIR /app
EXPOSE 3000
CMD ["server.js"]
```

### Example 5: C++ Application

```dockerfile
FROM gcc:12 as build
WORKDIR /src
COPY . .
RUN g++ -o myapp main.cpp -static-libstdc++ -static-libgcc

FROM gcr.io/distroless/cc-debian12
COPY --from=build /src/myapp /
CMD ["/myapp"]
```

### Example 6: Debugging with Debug Images

Build with debug image:

```dockerfile
FROM gcr.io/distroless/python3-debian12:debug
COPY app/ /app/
WORKDIR /app
CMD ["server.py"]
```

Enter container with shell:

```bash
docker build -t myapp:debug .
docker run -it --entrypoint=/busybox/sh myapp:debug

# Inside container
/app # ls
/app # cat /etc/passwd
/app # env
```

Debug images include busybox with utilities: sh, ls, cat, ps, wget, nc, ping, grep, find, etc.

### Example 7: Bazel Custom Image

**BUILD.bazel**:

```starlark
load("@rules_oci//oci:defs.bzl", "oci_image", "oci_tarball")
load("@rules_pkg//:pkg.bzl", "pkg_tar")
load("//private/util:deb.bzl", "deb")

pkg_tar(
    name = "app_layer",
    srcs = ["myapp"],
    package_dir = "/app",
)

oci_image(
    name = "myapp_image",
    base = "//static:static_root_amd64_debian12",
    tars = [
        ":app_layer",
        deb.package("amd64", "debian12", "ca-certificates"),
    ],
    entrypoint = ["/app/myapp"],
)

oci_tarball(
    name = "myapp_tarball",
    image = ":myapp_image",
    repo_tags = ["myapp:latest"],
)
```

Build and load:

```bash
bazel run //:myapp_tarball
docker run myapp:latest
```

## Integration Patterns and Workflows

### Docker Multi-Stage Build Pattern

**Standard workflow**:

1. **Build stage**: Use full SDK image (golang, python, node, maven, etc.)
2. **Compile/package**: Build application binary or package
3. **Runtime stage**: Use minimal distroless image
4. **Copy artifacts**: Transfer only application and runtime dependencies
5. **Set entrypoint**: Configure execution command

This pattern reduces final image size by 90%+ compared to full SDK images.

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: myapp
  template:
    metadata:
      labels:
        app: myapp
    spec:
      containers:
      - name: app
        image: gcr.io/distroless/python3-debian12:nonroot
        # Non-root security context already set by image
        securityContext:
          runAsNonRoot: true
          readOnlyRootFilesystem: true
        ports:
        - containerPort: 8080
```

### Google Jib Integration

[Jib](https://github.com/GoogleContainerTools/jib) has native distroless support:

**Maven** (`pom.xml`):

```xml
<plugin>
  <groupId>com.google.cloud.tools</groupId>
  <artifactId>jib-maven-plugin</artifactId>
  <version>3.3.1</version>
  <configuration>
    <from>
      <image>gcr.io/distroless/java21-debian12:nonroot</image>
    </from>
    <to>
      <image>myregistry/myapp</image>
    </to>
  </configuration>
</plugin>
```

Build without Docker daemon:

```bash
mvn compile jib:build
```

### Bazel Custom Distroless Images with rules_distroless

For users needing custom packages beyond pre-built images:

```starlark
load("@rules_oci//oci:defs.bzl", "oci_image")
load("@rules_distroless//distroless:defs.bzl", "apt")

# Define custom package set
apt.install(
    name = "custom_packages",
    packages = ["curl", "ca-certificates", "libpq5"],
    distro = "debian12",
    arch = "amd64",
)

oci_image(
    name = "custom_base",
    base = "//static:static_root_amd64_debian12",
    tars = [":custom_packages"],
)
```

## Configuration Options and Extension Points

### Environment Variables

**Common across all images**:
- `PATH`: Set to `/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin`
- `SSL_CERT_FILE`: Set to `/etc/ssl/certs/ca-certificates.crt` (enables TLS)

**Debug images**:
- `PATH`: Appends `:/busybox` to include busybox utilities

**Language-specific**:
- Java: `JAVA_HOME`, `JAVA_VERSION` (set by runtime)
- Python: Default `PYTHONPATH` includes standard library
- Node.js: `NODE_VERSION`, `PATH` includes `/nodejs/bin`

### User Configuration

**User Definitions** (`/etc/passwd`):

```
root:x:0:0:root:/root:/sbin/nologin
nobody:x:65534:65534:nobody:/nonexistent:/sbin/nologin
nonroot:x:65532:65532:nonroot:/home/nonroot:/sbin/nologin
```

**Group Definitions** (`/etc/group`):

```
root:x:0:
nobody:x:65534:
nonroot:x:65532:
```

Use `:nonroot` tags or set `USER nonroot` in Dockerfile for non-root execution.

### Entrypoint Customization

**Critical**: Distroless images have no shell. Always use **vector form** for entrypoints and commands:

✅ Correct:
```dockerfile
ENTRYPOINT ["/app/server"]
CMD ["--port", "8080"]
```

❌ Incorrect (tries to invoke shell):
```dockerfile
ENTRYPOINT "/app/server --port 8080"
```

### Package Metadata Location

Distroless uses non-standard dpkg metadata structure:

**Standard location** (not present): `/var/lib/dpkg/status`, `/var/lib/dpkg/info/`

**Distroless location**: `/var/lib/dpkg/status.d/`

Structure:
```
/var/lib/dpkg/status.d/
  ├── libc6              # Package metadata
  ├── libc6.md5sums      # File checksums
  ├── libssl3
  ├── libssl3.md5sums
  └── ...
```

This structure supports CVE scanning while avoiding conflicts with dpkg if installed later.

### Verification and Security

**Verify image signature**:

```bash
cosign verify gcr.io/distroless/static-debian12:latest \
  --certificate-oidc-issuer https://accounts.google.com \
  --certificate-identity keyless@distroless.iam.gserviceaccount.com
```

**Inspect image SBOM** (if available):

```bash
cosign download sbom gcr.io/distroless/static-debian12:latest
```

### Support Policy

Images follow Debian support timelines:

- **Debian 12**: Supported until September 2026
- **Debian 13**: Supported until ~1 year after Debian 14 release

Language runtime images have shorter support:
- Java/Node: Until 3 months after next Debian release
- Python: Until 3 months after next Debian release

Always pin specific Debian versions in production (`-debian12`, `-debian13`) rather than relying on unpinned tags.
