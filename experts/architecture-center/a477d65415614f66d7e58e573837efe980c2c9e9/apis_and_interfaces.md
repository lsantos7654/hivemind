# Azure Architecture Center — APIs and Interfaces

## Overview

This is a documentation repository with no programmatic APIs, SDKs, or callable interfaces. The "API" of this repository is its **content schema** — the structured frontmatter, file naming conventions, YamlMime types, and TOC format that govern how content is authored, organized, and published.

## Content Authoring Interfaces

### Standard Markdown Article

Every article begins with YAML frontmatter followed by Markdown content. The frontmatter schema:

```yaml
---
title: <string>            # Page title, also used for SEO meta title
description: <string>      # SEO meta description (1-2 sentences)
author: <github-username>  # GitHub username of the author
ms.author: <ms-alias>      # Microsoft employee alias (e.g., "pnp" for team articles)
ms.date: MM/DD/YYYY        # Date of last significant content update
ms.topic: <topic-type>     # See topic types below
ms.subservice: <string>    # Subsection taxonomy (e.g., "cloud-fundamentals", "architecture-guide")
ms.custom: <string>        # Optional custom tags (e.g., "arb-aiml", "arb-web")
ai-usage: <string>         # Optional: "ai-assisted" when AI tools contributed
---
```

**Valid `ms.topic` values** (from `docfx.json` `globalMetadata`):
- `concept-article` — Default for most articles
- `design-pattern` — Used for pattern catalog entries
- `best-practice` — Used for best practice articles

**Valid `ms.subservice` values** (inferred from usage):
- `cloud-fundamentals` — Patterns, core architecture concepts
- `architecture-guide` — Application architecture fundamentals, technology choices
- `best-practice` — Best practices and antipatterns
- `cloud-fundamentals` — Patterns index

### YamlMime:Architecture (Split-File Format)

Used for articles that appear in the browse catalog with thumbnails. The YAML wrapper (`foo.yml`):

```yaml
### YamlMime:Architecture
metadata:
  title: <string>
  description: <string>
  author: <github-username>
  ms.author: <ms-alias>
  ms.date: MM/DD/YYYY
  ms.topic: <topic-type>
  ms.subservice: <string>
  ms.custom: <string>        # Optional: arb-web, arb-aiml, etc.
azureCategories:             # Azure portal category tags
  - web
  - developer-tools
  - integration
  - devops
  - databases
  - ai-machine-learning
  # ... (many others)
products:                    # Azure products featured in the article
  - azure-kubernetes-service
  - azure-api-management
  - azure-service-bus
  # ... (any azure-* product slug)
name: <string>               # Display name in browse catalog
summary: <string>            # Short description for catalog cards
thumbnailUrl: /azure/architecture/browse/thumbs/<image>.png
content: |
  [!INCLUDE[](<article-name>-content.md)]
```

The corresponding `-content.md` file contains only the Markdown body — no frontmatter — and is excluded from direct publishing by `docfx.json`.

### Table of Contents (`toc.yml`)

Every section directory contains a `toc.yml` that defines hierarchical navigation. Structure:

```yaml
items:
- name: Section Title
  href: index.md
  items:
  - name: Subsection
    items:
    - name: Article Title
      href: article.md
      displayName: "keyword1, keyword2"    # Optional: extra search terms
    - name: External Link
      href: https://example.com
```

The root `docs/toc.yml` imports section TOCs and defines the top-level site navigation.

### Breadcrumb (`_bread/toc.yml`)

```yaml
- name: Azure
  tocHref: /azure/
  topicHref: /azure
  items:
  - name: Architecture Center
    tocHref: /azure/architecture/
    topicHref: /azure/architecture
```

### Redirections (`.openpublishing.redirection.json`)

```json
{
  "redirections": [
    {
      "source_path": "docs/old-section/article.md",
      "redirect_url": "/azure/architecture/new-section/article",
      "redirect_document_id": true
    }
  ]
}
```

`redirect_document_id: true` transfers the article's document ID (and associated metrics/ratings) to the new URL.

## Content Pattern Examples

### Pattern Article — Single Markdown (Circuit Breaker)

File: `docs/patterns/circuit-breaker.md`

```markdown
---
title: Circuit Breaker Pattern
description: Handle faults that might take a variable amount of time to fix...
ms.author: pnp
author: claytonsiemens77
ms.date: 02/05/2025
ms.topic: design-pattern
ms.subservice: cloud-fundamentals
---

# Circuit Breaker pattern

## Context and problem
...

## Solution
...

## Issues and considerations
...

## When to use this pattern
...

## Workload design
...

## Example
...

## Related resources
...
```

### Pattern Article — Split Format (Cache-Aside)

File: `docs/patterns/cache-aside.yml`

```yaml
### YamlMime:Architecture
metadata:
  title: Cache-Aside Pattern
  ms.date: 09/11/2025
  ms.topic: design-pattern
  ms.subservice: cloud-fundamentals
  ms.custom: arb-web
azureCategories:
  - web
products:
  - azure-managed-redis
name: Cache-Aside pattern
summary: Load data on demand into a cache...
thumbnailUrl: /azure/architecture/browse/thumbs/cache-aside-diagram.png
content: |
  [!INCLUDE[](cache-aside-content.md)]
```

File: `docs/patterns/cache-aside-content.md` — body only, no YAML frontmatter.

### Microservices Design Article

File: `docs/microservices/design/gateway.yml`

```yaml
### YamlMime:Architecture
metadata:
  title: API gateways
  ms.date: 02/01/2025
  ms.topic: concept-article
  ms.subservice: architecture-guide
  ms.custom: arb-web
azureCategories:
  - web
  - developer-tools
products:
  - azure-application-gateway
  - azure-api-management
name: Use API gateways in microservices
summary: An API gateway sits between clients and services...
thumbnailUrl: /azure/architecture/browse/thumbs/gateway-thumbnail.png
content: |
  [!include[](gateway-content.md)]
```

### AI/ML Guide Article

File: `docs/ai-ml/guide/ai-agent-design-patterns.md`

```markdown
---
title: AI Agent Orchestration Patterns
ms.date: 02/12/2026
ms.topic: concept-article
ms.collection: ce-skilling-ai-copilot
ms.subservice: architecture-guide
ms.custom: arb-aiml
---

# AI agent orchestration patterns
...
```

The `ms.collection: ce-skilling-ai-copilot` tag associates the article with Microsoft's AI skills learning path.

## Cross-Reference Conventions

Internal links use repo-relative paths or absolute `/azure/architecture/` URLs:

```markdown
<!-- Relative links within the same section -->
[Circuit Breaker](./circuit-breaker.md)
[Retry pattern](./retry.yml)

<!-- Absolute links to other Azure docs properties -->
[Azure Well-Architected Framework](/azure/well-architected/)
[Azure Kubernetes Service](/azure/aks/)
```

Cross-references to WAF pillars always use absolute URLs to the Well-Architected Framework site.

## Image and Media Conventions

Images are stored in section-level `images/` or `media/` directories. Browse catalog thumbnails live at `docs/browse/thumbs/` and are referenced via absolute URL: `/azure/architecture/browse/thumbs/<filename>.png`.

Diagram references in articles use DocFX image syntax with alt text and optional lightbox:

```markdown
:::image type="complex" border="false"
         source="./images/diagram.svg"
         alt-text="Descriptive alt text."
         lightbox="./images/diagram.svg":::
   Long description of the diagram for accessibility.
:::image-end:::
```

## Integration Patterns

### Global Metadata Inheritance

All articles inherit `globalMetadata` from `docfx.json`. Section-specific overrides in `fileMetadata` apply additional metadata based on glob patterns:

```json
"fileMetadata": {
  "searchScope": {
    "patterns/**/*.md": ["Azure", "Azure Architecture Center", "Cloud Design Patterns"],
    "data-guide/**/*.md": ["Azure", "Azure Architecture Center", "Data Guide"]
  }
}
```

### Feedback System Integration

All articles display a feedback widget via `"feedback_system": "Standard"` and `"feedback_github_repo": "MicrosoftDocs/architecture-center"`. This allows readers to submit feedback that creates GitHub issues.

### Learn Platform Integration

Articles can include `ms.collection` tags to associate with Microsoft Learn learning paths:
- `ms.collection: ce-skilling-ai-copilot` — AI copilot skills path
- Learning path associations are managed via metadata, not content structure

## Extension Points

### Adding a New Cloud Design Pattern

1. Create `docs/patterns/<pattern-name>.md` (single-file) or `<pattern-name>.yml` + `<pattern-name>-content.md` (split-file)
2. Add required frontmatter with `ms.topic: design-pattern` and `ms.subservice: cloud-fundamentals`
3. For split format: add `thumbnailUrl` referencing a new thumbnail at `docs/browse/thumbs/`
4. Add entry to `docs/patterns/toc.yml` and `docs/patterns/index.md` catalog table
5. Include WAF pillar mapping in the `index.md` table

### Adding a New Example Scenario

1. Create directory under `docs/example-scenario/<category>/`
2. Create `<scenario>.yml` (YamlMime:Architecture) + `<scenario>-content.md`
3. Add `azureCategories` and `products` tags appropriate to the scenario
4. Add entry to the section's `toc.yml`

### Adding URL Redirects

Add entries to `.openpublishing.redirection.json` when moving or renaming articles:
```json
{
  "source_path": "docs/old/path.md",
  "redirect_url": "/azure/architecture/new/path",
  "redirect_document_id": true
}
```
