# Awesome Software Architecture — APIs and Interfaces

## Overview

This repository is a **curated content repository**, not a software library with a programmatic API. Its primary "interfaces" are:

1. **The MkDocs documentation site** at `https://awesome-architecture.com` — the navigable web interface
2. **The Markdown content files** in `docs/` — the human and machine-readable resource lists
3. **The `mkdocs.yml` navigation schema** — the structural contract for the site
4. **The `Program.cs` release notes CLI** — a developer tool with a simple command-line interface
5. **The GitHub repository** — the collaboration and contribution interface

---

## Public Interfaces

### 1. Content Files Interface (Markdown)

Each file in `docs/` follows a consistent structure. Reading and navigating these files is the primary use pattern.

**Standard file format:**

```markdown
# Topic Name

## 📘 Resources
- [Link Title](URL)
- [Another Resource](URL) - Brief description

## 📕 Articles
- [Article Title](URL) - Description

## 📺 Videos
- [Video Title](URL)

## 📦 Libraries / Tools
- [Tool Name](GitHub-URL) - Description
```

**Section headers vary by topic** but typically include one or more of:
- `## 📘 Resources` — general resource collections
- `## 📕 Articles` — blog posts and written guides
- `## 📺 Videos` — video content and conference talks
- `## 🎬 Youtube Channels` — YouTube channel recommendations
- `## 📦 Libraries` — open source libraries and tools
- `## 🔖 Books` — recommended books

**Contribution format** (from `contributing.md`):
```
**(LINK) | (LIBRARY) | (GitHub-UserName/GitHub-RepositoryName) - DESCRIPTION**
```

---

### 2. MkDocs Navigation Schema (`mkdocs.yml`)

The `nav:` section of `mkdocs.yml` is the **authoritative mapping** of all content to the site menu. Every new doc file must be registered here.

**Nav entry patterns:**

```yaml
# Flat topic entry
- Topic Name: topic-file.md

# Nested category entry
- Category Name:
  - Subtopic: category/subtopic.md
  - Another: category/another.md

# Deeply nested entry
- Parent:
  - Child:
    - Grandchild: parent/child/grandchild.md
```

**Site configuration contract:**

```yaml
site_name: Awesome Software Architecture
site_url: https://awesome-architecture.com
docs_dir:                              # blank = defaults to docs/
repo_url: https://github.com/mehdihadeli/awesome-software-architecture
edit_uri: edit/main/docs/              # "Edit on GitHub" links
```

---

### 3. Release Notes CLI (`Program.cs`)

A single-binary C# .NET 9 console application with the following interface:

**Usage:**
```bash
dotnet run --project ReleaseNotes.csproj [<commit-range>]
```

**Arguments:**

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `commit-range` | `string` | `HEAD~1..HEAD` | Git commit range to diff (e.g., `v1.0..v1.1`, `HEAD~5..HEAD`) |

**Output:** Markdown-formatted release notes to stdout, grouped by file and section.

**Example invocations:**
```bash
# Show changes from last commit (default)
dotnet run --project ReleaseNotes.csproj

# Show changes across last 5 commits
dotnet run --project ReleaseNotes.csproj -- HEAD~5..HEAD

# Show changes between two tags
dotnet run --project ReleaseNotes.csproj -- v1.0..v2.0
```

**Example output:**
```markdown
## Clean architecture

### Resources
**Added**
- [Clean Architecture with .NET](https://example.com) - Guide for applying Clean Architecture in .NET

**Removed**
- [Outdated resource](https://example.com)

## Microservices

### Tools
**Added**
- [Dapr 1.14 Release](https://docs.dapr.io) - New distributed application runtime features
```

**Internal parsing logic** (`Program.cs`):
- `SectionRegex`: `^\+\s*##\s+(.*)` — matches added `##` section headers in the diff
- `ItemRegex`: `^[+-]\s*-\s*(.*)` — matches added (`+`) or removed (`-`) list items in the diff
- Lines starting with `+++ b/` ending in `.md` identify which markdown file is being changed
- Changes are grouped by: `file → section → changeType (Added|Removed) → items[]`

---

### 4. GitHub Contribution Interface

**Pull Request Workflow:**

1. Fork the repository
2. Create a new branch
3. Add links to the appropriate `docs/<topic>.md` file
4. If creating a new topic, add entry to `mkdocs.yml` nav
5. Open a PR — CI link check runs automatically

**Naming conventions for PRs:** Create separate PRs per category; do not batch multiple categories into one PR.

**Research project tag:** Academic or research papers should be tagged with `**[Research]**`.

---

## Key Topic Areas and Their Files

The following table maps the most commonly referenced architecture topics to their files in `docs/`:

| Topic | File Path |
|-------|-----------|
| Software Architecture | `docs/software-architecture.md` |
| Clean Architecture | `docs/clean-architecture.md` |
| Domain-Driven Design | `docs/domain-driven-design/domain-driven-design.md` |
| CQRS | `docs/cqrs.md` |
| Event Sourcing | `docs/event-sourcing.md` |
| Event-Driven Architecture | `docs/event-driven-architecture.md` |
| Microservices | `docs/microservices/microservices.md` |
| Hexagonal Architecture | `docs/hexagonal-architecture.md` |
| Onion Architecture | `docs/onion-architecture.md` |
| Vertical Slice Architecture | `docs/vertical-slice-architecture.md` |
| Modular Monolith | `docs/modular-monolith.md` |
| SOLID Principles | `docs/architectural-design-principles/solid.md` |
| Design Patterns (GoF) | `docs/design-patterns/design-patterns.md` |
| Cloud Design Patterns | `docs/cloud-design-patterns/cloud-design-patterns.md` |
| Outbox Pattern | `docs/cloud-design-patterns/outbox-pattern.md` |
| Circuit Breaker | `docs/cloud-design-patterns/circuit-breaker.md` |
| Saga / Distributed Transactions | `docs/distributed-transactions.md` |
| Messaging / Message Queues | `docs/messaging/messaging.md` |
| Kafka | `docs/messaging/kafka.md` |
| RabbitMQ | `docs/messaging/rabbitmq.md` |
| AI / LLMs | `docs/ai/ai.md`, `docs/ai/llms.md` |
| RAG | `docs/ai/rag.md` |
| MCP | `docs/ai/mcp.md` |
| Semantic Kernel | `docs/ai/semantic-kernel.md` |
| Kubernetes | `docs/devops/kubernetes/kubernetes.md` |
| Docker | `docs/devops/docker/docker.md` |
| Terraform | `docs/iaas/terraform.md` |
| Observability | `docs/microservices/observability/observibility.md` |
| Repository Pattern | `docs/design-patterns/repository-pattern.md` |
| Actor Model | `docs/actor-model-architecture/actor-model-architecture.md` |

---

## Integration Patterns and Extension Points

### Adding a New Topic

```bash
# 1. Create the markdown file
touch docs/my-new-topic.md

# 2. Add content following the standard format
cat >> docs/my-new-topic.md << 'EOF'
# My New Topic

## 📘 Resources
- [Resource Title](https://example.com) - Description

## 📕 Articles
- [Article](https://example.com) - Description
EOF

# 3. Register in mkdocs.yml nav section
# Add: - My New Topic: my-new-topic.md
```

### Querying the Content Programmatically

Since all content is markdown files, standard tools work:

```bash
# Find all topics mentioning a pattern
grep -r "Circuit Breaker" docs/

# List all resource files in a category
ls docs/domain-driven-design/

# Count resources in a file
grep -c "^-" docs/microservices/microservices.md

# Extract all external URLs from a file
grep -oE 'https?://[^)]+' docs/clean-architecture.md
```

### MkDocs API for Extensions

The `mkdocs.yml` config exposes extension hooks; the `plugins:` section (currently empty/absent) could be populated with MkDocs plugins like `search`, `minify`, or `git-revision-date` without breaking existing content.
