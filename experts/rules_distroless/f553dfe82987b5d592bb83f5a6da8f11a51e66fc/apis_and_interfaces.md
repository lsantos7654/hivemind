# rules_distroless APIs and Interfaces

## Public APIs and Entry Points

`rules_distroless` provides two main API surfaces: the **APT package management API** and the **distroless system file rules API**.

### APT Package Management API

#### Bzlmod Extension (Recommended)

**Entry Point:** `@rules_distroless//apt:extensions.bzl`

```starlark
# MODULE.bazel
bazel_dep(name = "rules_distroless", version = "0.5.1")

apt = use_extension("@rules_distroless//apt:extensions.bzl", "apt")
apt.install(
    name = "debian_packages",
    manifest = "//:packages.yaml",
    lock = "//:packages.lock.json",  # Optional but recommended
)
use_repo(apt, "debian_packages")
```

**Tag Class: `install`**

Attributes:
- `name` (string, required): Name of the generated repository
- `manifest` (label, required): YAML file defining packages to install
- `lock` (label, optional): JSON lockfile for reproducible builds
- `nolock` (bool, default=False): Set to True to suppress lockfile warnings
- `package_template` (label, optional): EXPERIMENTAL - custom BUILD template
- `resolve_transitive` (bool, default=True): Include transitive dependencies
- `mergedusr` (bool, default=False): Normalize packages following mergedusr conventions

#### WORKSPACE Macro (Legacy)

**Entry Point:** `@rules_distroless//apt:apt.bzl`

```starlark
# WORKSPACE
load("@rules_distroless//apt:apt.bzl", "apt")

apt.install(
    name = "debian",
    manifest = "//path/to:packages.yaml",
    lock = "//path/to:packages.lock.json",
)

load("@debian//:packages.bzl", "debian_packages")
debian_packages()
```

Parameters are identical to the Bzlmod extension.

### Distroless System File Rules API

**Entry Point:** `@rules_distroless//distroless:defs.bzl`

```starlark
load("@rules_distroless//distroless:defs.bzl",
    "passwd", "group", "home", "cacerts", "java_keystore",
    "locale", "os_release", "flatten"
)
```

### APT Status Database Rules API

**Entry Point:** `@rules_distroless//apt:defs.bzl`

```starlark
load("@rules_distroless//apt:defs.bzl", "dpkg_status", "dpkg_statusd")
```

## Key Classes, Functions, and Macros

### 1. passwd - Create /etc/passwd File

Creates a passwd file from user definitions.

**Function Signature:**
```starlark
passwd(name, entries, mode = "0644", time = "0.0", **kwargs)
```

**Parameters:**
- `name` (string): Target name
- `entries` (list[dict]): Array of user dictionaries
- `mode` (string): File permissions (default: "0644")
- `time` (string): Timestamp for reproducibility (default: "0.0")

**Entry Dictionary Fields:**
- `username` (string, required): User login name
- `uid` (int, required): User ID
- `gid` (int, required): Primary group ID
- `home` (string, required): Home directory path
- `shell` (string, required): Login shell path
- `password` (string, optional): Password field (default: "!")
- `gecos` (list[string], optional): GECOS fields

**Output:** A `.tar.gz` archive containing `/etc/passwd`

**Example:**
```starlark
passwd(
    name = "passwd",
    entries = [
        dict(
            username = "root",
            uid = 0,
            gid = 0,
            home = "/root",
            shell = "/bin/bash",
        ),
        dict(
            username = "nobody",
            uid = 65534,
            gid = 65534,
            home = "/nonexistent",
            shell = "/usr/sbin/nologin",
        ),
    ],
)
```

### 2. group - Create /etc/group File

Creates a group file from group definitions.

**Function Signature:**
```starlark
group(name, entries, time = "0.0", mode = "0644", **kwargs)
```

**Parameters:**
- `name` (string): Target name
- `entries` (list[dict]): Array of group dictionaries
- `mode` (string): File permissions (default: "0644")
- `time` (string): Timestamp (default: "0.0")

**Entry Dictionary Fields:**
- `name` (string, required): Group name
- `gid` (int, required): Group ID
- `password` (string, optional): Group password field (default: "!")
- `users` (list[string], optional): List of member usernames (default: [])

**Output:** A `.tar.gz` archive containing `/etc/group`

**Example:**
```starlark
group(
    name = "group",
    entries = [
        dict(name = "root", gid = 0),
        dict(name = "www-data", gid = 33, users = ["www-data"]),
        dict(name = "nogroup", gid = 65534),
    ],
)
```

### 3. home - Create Home Directories

Creates home directories with specific ownership and permissions.

**Function Signature:**
```starlark
home(name, dirs, **kwargs)
```

**Parameters:**
- `name` (string): Target name
- `dirs` (list[dict]): Array of home directory specifications

**Directory Dictionary Fields:**
- `home` (string, required): Directory path
- `uid` (int, required): Owner user ID
- `gid` (int, required): Owner group ID
- `mode` (string, optional): Directory permissions (default: "700")
- `time` (string, optional): Timestamp (default: "0")

**Output:** A `.tar.gz` archive containing the directory structure

**Example:**
```starlark
home(
    name = "homes",
    dirs = [
        dict(home = "/root", uid = 0, gid = 0, mode = "700"),
        dict(home = "/home/appuser", uid = 1000, gid = 1000),
    ],
)
```

### 4. cacerts - Bundle CA Certificates

Creates a CA certificate bundle from the ca-certificates Debian package.

**Function Signature:**
```starlark
cacerts(name, package, mode = "0555", time = "0.0", **kwargs)
```

**Parameters:**
- `name` (string): Target name
- `package` (label): The ca-certificates package data.tar (required)
- `mode` (string): File permissions (default: "0555")
- `time` (string): Timestamp (default: "0.0")

**Output:** A `.tar.gz` archive with:
- `/etc/ssl/certs/ca-certificates.crt` - The certificate bundle
- `/usr/share/doc/ca-certificates/copyright` - License file

**Example:**
```starlark
# MODULE.bazel
http_archive = use_repo_rule("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "ca-certificates",
    urls = ["https://snapshot.debian.org/.../ca-certificates_20210119_all.deb"],
    sha256 = "b2d488ad4d8d8adb3ba319fc9cb2cf9909fc42cb82ad239a26c570a2e749c389",
    build_file_content = 'exports_files(["data.tar.xz"])',
)

# BUILD.bazel
load("@rules_distroless//distroless:defs.bzl", "cacerts")

cacerts(
    name = "cacerts",
    package = "@ca-certificates//:data.tar.xz",
)

# Important: Set SSL_CERT_FILE environment variable in your image:
# SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
```

### 5. java_keystore - Create Java Keystore

Generates a Java keystore from CA certificates.

**Function Signature:**
```starlark
java_keystore(name, cacerts, time = "0.0", **kwargs)
```

**Parameters:**
- `name` (string): Target name
- `cacerts` (label): Output from the `cacerts` rule (required)
- `time` (string): Timestamp (default: "0.0")

**Output:** A `.tar.gz` archive containing Java keystore files

**Example:**
```starlark
load("@rules_distroless//distroless:defs.bzl", "cacerts", "java_keystore")

cacerts(
    name = "cacerts",
    package = "@ca-certificates//:data.tar.xz",
)

java_keystore(
    name = "keystore",
    cacerts = ":cacerts",
)
```

### 6. locale - Extract and Strip Locale Data

Extracts locale data from libc-bin package, stripping unnecessary charsets.

**Function Signature:**
```starlark
locale(name, package, charset = "C.utf8", time = "0.0", **kwargs)
```

**Parameters:**
- `name` (string): Target name
- `package` (label): libc-bin package data.tar (required)
- `charset` (string): Locale charset to keep (default: "C.utf8")
- `time` (string): Timestamp (default: "0.0")

**Output:** A `.tar.gz` archive with stripped `/usr/lib/locale/`

**Example:**
```starlark
http_archive(
    name = "libc-bin",
    urls = ["https://snapshot.debian.org/.../libc-bin_2.31-13+deb11u7_amd64.deb"],
    sha256 = "8b048ab5c7e9f5b7444655541230e689631fd9855c384e8c4a802586d9bbc65a",
    build_file_content = 'exports_files(["data.tar.xz"])',
)

locale(
    name = "locale",
    package = "@libc-bin//:data.tar.xz",
    charset = "C.utf8",
)
```

### 7. os_release - Create /etc/os-release File

Creates an operating system identification file.

**Function Signature:**
```starlark
os_release(name, content, path = "/usr/lib/os-release", mode = "0555", time = "0", **kwargs)
```

**Parameters:**
- `name` (string): Target name
- `content` (dict): Key-value pairs for os-release fields (required)
- `path` (string): File path in archive (default: "/usr/lib/os-release")
- `mode` (string): File permissions (default: "0555")
- `time` (string): Timestamp (default: "0")

**Output:** A `.tar.gz` archive with the os-release file

**Common Content Fields:**
- `NAME`: Operating system name
- `VERSION`: Version string
- `ID`: Lowercase OS identifier
- `VERSION_ID`: Version number
- `PRETTY_NAME`: User-friendly name
- `HOME_URL`: Homepage URL
- `SUPPORT_URL`: Support page URL

**Example:**
```starlark
os_release(
    name = "os_release",
    content = {
        "NAME": "Distroless",
        "ID": "distroless",
        "VERSION_ID": "11",
        "PRETTY_NAME": "Distroless (Debian 11)",
    },
)
```

### 8. flatten - Merge Multiple Tar Archives

Flattens multiple tar archives into a single archive.

**Function Signature:**
```starlark
flatten(name, tars, deduplicate = False, compress = None, **kwargs)
```

**Parameters:**
- `name` (string): Target name
- `tars` (list[label]): List of tar archives to flatten (required, non-empty)
- `deduplicate` (bool): Remove duplicate directory entries (default: False, EXPERIMENTAL)
- `compress` (string): Compression type: "gzip", "bzip2", "xz", "zstd", or None

**Output:** A tar archive (with optional compression)

**Example:**
```starlark
load("@rules_distroless//distroless:defs.bzl", "flatten")

flatten(
    name = "base",
    tars = [
        ":passwd",
        ":group",
        ":homes",
        "@debian_packages//coreutils/amd64:data",
        "@debian_packages//bash/amd64:data",
    ],
    compress = "gzip",
)
```

### 9. dpkg_status - Create /var/lib/dpkg/status

Creates a dpkg status file for vulnerability scanners.

**Function Signature:**
```starlark
dpkg_status(name, controls, **kwargs)
```

**Parameters:**
- `name` (string): Target name
- `controls` (list[label]): List of package control.tar files (required)

**Output:** A `.tar` archive containing `/var/lib/dpkg/status`

**Example:**
```starlark
load("@rules_distroless//apt:defs.bzl", "dpkg_status")

dpkg_status(
    name = "dpkg_status",
    controls = [
        "@debian_packages//bash/amd64:control",
        "@debian_packages//coreutils/amd64:control",
    ],
)
```

### 10. dpkg_statusd - Create /var/lib/dpkg/status.d/

Creates individual package status files in status.d directory.

**Function Signature:**
```starlark
dpkg_statusd(name, package_name, control, compression = None, **kwargs)
```

**Parameters:**
- `name` (string): Target name
- `package_name` (string): Package name (required)
- `control` (label): Package control.tar file (required)
- `compression` (string): Compression type (optional)

**Output:** Compressed tar with `/var/lib/dpkg/status.d/<package_name>`

**Example:**
```starlark
load("@rules_distroless//apt:defs.bzl", "dpkg_statusd")

dpkg_statusd(
    name = "bash_statusd",
    package_name = "bash",
    control = "@debian_packages//bash/amd64:control",
    compression = "gzip",
)
```

## Usage Examples with Code Snippets

### Complete Distroless Base Image Example

```starlark
# MODULE.bazel
bazel_dep(name = "rules_distroless", version = "0.5.1")
bazel_dep(name = "rules_oci", version = "2.0.0")

apt = use_extension("@rules_distroless//apt:extensions.bzl", "apt")
apt.install(
    name = "debian",
    manifest = "//:packages.yaml",
    lock = "//:packages.lock.json",
)
use_repo(apt, "debian")

http_archive = use_repo_rule("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

http_archive(
    name = "ca-certificates",
    urls = ["https://snapshot.debian.org/.../ca-certificates_20210119_all.deb"],
    sha256 = "...",
    build_file_content = 'exports_files(["data.tar.xz"])',
)
```

```yaml
# packages.yaml
version: 1

sources:
  - channel: bullseye main
    url: https://snapshot.debian.org/archive/debian/20240210T223313Z

archs:
  - amd64

packages:
  - bash
  - coreutils
  - ca-certificates
```

```starlark
# BUILD.bazel
load("@rules_distroless//distroless:defs.bzl",
    "passwd", "group", "home", "cacerts", "flatten")
load("@rules_oci//oci:defs.bzl", "oci_image")

# Create user management files
passwd(
    name = "passwd",
    entries = [
        dict(username = "root", uid = 0, gid = 0, home = "/root", shell = "/bin/bash"),
        dict(username = "nonroot", uid = 1000, gid = 1000, home = "/home/nonroot", shell = "/bin/bash"),
    ],
)

group(
    name = "group",
    entries = [
        dict(name = "root", gid = 0),
        dict(name = "nonroot", gid = 1000),
    ],
)

home(
    name = "homes",
    dirs = [
        dict(home = "/root", uid = 0, gid = 0),
        dict(home = "/home/nonroot", uid = 1000, gid = 1000),
    ],
)

# Bundle CA certificates
cacerts(
    name = "cacerts",
    package = "@ca-certificates//:data.tar.xz",
)

# Flatten everything into base layer
flatten(
    name = "base_layer",
    tars = [
        ":passwd",
        ":group",
        ":homes",
        ":cacerts",
        "@debian//bash/amd64:data",
        "@debian//coreutils/amd64:data",
    ],
    compress = "gzip",
)

# Build OCI image
oci_image(
    name = "distroless_base",
    base = "@distroless_base_image",
    tars = [":base_layer"],
    entrypoint = ["/bin/bash"],
    env = {
        "SSL_CERT_FILE": "/etc/ssl/certs/ca-certificates.crt",
    },
    user = "1000",
)
```

### Multi-Architecture Build Example

```starlark
# MODULE.bazel
apt = use_extension("@rules_distroless//apt:extensions.bzl", "apt")
apt.install(
    name = "multiarch",
    manifest = "//:multiarch.yaml",
    lock = "//:multiarch.lock.json",
)
use_repo(apt, "multiarch")
```

```yaml
# multiarch.yaml
version: 1

sources:
  - channel: bullseye main
    url: https://snapshot.debian.org/archive/debian/20240210T223313Z

archs:
  - amd64
  - arm64

packages:
  - bash
  - coreutils
```

```starlark
# BUILD.bazel
load("@rules_distroless//distroless:defs.bzl", "flatten")

[flatten(
    name = "base_" + arch,
    tars = [
        ":passwd",
        ":group",
        "@multiarch//bash/" + arch + ":data",
        "@multiarch//coreutils/" + arch + ":data",
    ],
) for arch in ["amd64", "arm64"]]
```

## Integration Patterns and Workflows

### Workflow 1: Package Resolution and Lockfile Generation

1. **Create manifest** describing desired packages
2. **Run resolution** to generate lockfile
3. **Commit lockfile** to version control
4. **Use locked packages** in builds

```bash
# Define packages in packages.yaml
cat > packages.yaml <<EOF
version: 1
sources:
  - channel: bullseye main
    url: https://snapshot.debian.org/archive/debian/20240210T223313Z
archs:
  - amd64
packages:
  - bash
EOF

# Generate lockfile
bazel run @debian//:lock

# Lockfile created: packages.lock.json
# Commit to VCS for reproducibility
git add packages.yaml packages.lock.json
git commit -m "Add Debian packages"
```

### Workflow 2: Building Container Images

Integration with rules_oci:

```starlark
load("@rules_oci//oci:defs.bzl", "oci_image", "oci_tarball")
load("@rules_distroless//distroless:defs.bzl", "flatten")

flatten(
    name = "rootfs",
    tars = [
        # System files
        ":passwd",
        ":group",
        # Packages
        "@debian//ca-certificates/amd64:data",
        "@debian//openssl/amd64:data",
        # Application
        "//app:layer",
    ],
)

oci_image(
    name = "image",
    base = "@distroless_static",
    tars = [":rootfs"],
    entrypoint = ["/app/main"],
)

oci_tarball(
    name = "tarball",
    image = ":image",
    repo_tags = ["myapp:latest"],
)
```

### Workflow 3: Security Scanning with Package Database

```starlark
load("@rules_distroless//apt:defs.bzl", "dpkg_status")
load("@rules_distroless//distroless:defs.bzl", "flatten")

dpkg_status(
    name = "package_db",
    controls = [
        "@debian//bash/amd64:control",
        "@debian//openssl/amd64:control",
    ],
)

flatten(
    name = "image_with_db",
    tars = [
        ":rootfs",
        ":package_db",
    ],
)
```

Now scanners can detect installed packages and vulnerabilities.

## Configuration Options and Extension Points

### Manifest Configuration

```yaml
version: 1  # Required, must be 1

sources:
  - channel: <distribution> <components>
    url: <repository_url>
    # OR
    urls: [<mirror1>, <mirror2>]  # Multiple mirrors

archs:
  - amd64
  - arm64
  # Supported: amd64, arm64, armhf, i386, ppc64el, s390x

packages:
  - package-name
  - package-name=<version>  # Pin specific version
  - package-name (>= 1.0)   # Version constraints
```

### Package Template Customization (EXPERIMENTAL)

Custom BUILD file template for packages:

```starlark
apt.install(
    name = "custom",
    manifest = "//:manifest.yaml",
    package_template = "//:package.BUILD.tmpl",
)
```

Template variables:
- `{target_name}`: Package target name
- `{deps}`: Package dependencies
- `{urls}`: Download URLs
- `{name}`: Package name
- `{arch}`: Architecture
- `{sha256}`: Checksum
- `{repo_name}`: Repository name

### MergedUSR Support

For compatibility with merged `/usr` filesystems:

```starlark
apt.install(
    name = "merged",
    manifest = "//:manifest.yaml",
    mergedusr = True,  # Normalizes /bin -> /usr/bin, etc.
)
```

This prevents Docker errors about duplicate paths.

### Time and Permissions Control

All rules support reproducible builds:

```starlark
passwd(
    name = "passwd",
    entries = [...],
    mode = "0644",  # Permissions
    time = "0.0",   # Unix epoch for reproducibility
)
```

Use consistent timestamps across all rules for deterministic output.

The APIs are designed for composability, allowing users to mix and match rules to create custom Linux environments tailored to their needs.
