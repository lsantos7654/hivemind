# Azure Architecture Center — Code Structure

## Annotated Directory Tree

```
architecture-center/                    # Repository root
├── README.md                           # Project overview and legal notices
├── CONTRIBUTING.md                     # Contribution guidelines
├── SECURITY.md                         # Security disclosure policy
├── LICENSE                             # CC-BY-4.0 for documentation
├── LICENSE-CODE                        # MIT for code samples
├── ThirdPartyNotices                   # Third-party attribution
├── cspell.json                         # Root-level spell check config
├── .acrolinx-config.edn               # Acrolinx content quality config
├── .openpublishing.redirection.json   # 1,643 URL redirect rules
├── azure-update-report/                # Automated update tracking reports
├── includes/                           # Shared markdown includes
│   └── sol-idea-header.md             # Common header for solution idea articles
└── docs/                               # All publishable documentation content
    ├── docfx.json                      # DocFX build configuration (root)
    ├── cspell.json                     # Docs-level spell check config
    ├── cspell-docutune.json            # Docutune-specific spell exclusions
    ├── toc.yml                         # Root table of contents
    ├── _bread/                         # Breadcrumb navigation
    │   └── toc.yml                     # Azure-wide breadcrumb anchor
    ├── _images/                        # Shared images not tied to a section
    ├── icons/                          # Azure service icon downloads/reference
    ├── browse/                         # Architecture browse/catalog pages
    │   └── thumbs/                     # Thumbnail images for browse catalog
    ├── patterns/                       # Cloud Design Patterns (40+ patterns)
    ├── guide/                          # Architecture guides and fundamentals
    ├── best-practices/                 # Cloud application best practices
    ├── antipatterns/                   # Performance antipatterns
    ├── microservices/                  # Microservices architecture guidance
    ├── data-guide/                     # Data architecture guide
    ├── ai-ml/                          # AI and machine learning architectures
    ├── example-scenario/               # Real-world example workloads
    ├── solution-ideas/                 # High-level solution idea articles
    ├── reference-architectures/        # Detailed reference architectures
    ├── databases/                      # Database architecture guidance
    ├── analytics/                      # Analytics architecture guidance
    ├── containers/                     # Container architecture guidance
    ├── networking/                     # Networking architecture guidance
    ├── identity/                       # Identity architecture guidance
    ├── integration/                    # Integration and messaging guidance
    ├── storage/                        # Storage architecture guidance
    ├── serverless/                     # Serverless architecture guidance
    ├── high-availability/              # High availability architectures
    ├── hybrid/                         # Hybrid cloud architectures
    ├── landing-zones/                  # Azure landing zone deployment
    ├── mainframe/                      # Mainframe migration guidance
    ├── industries/                     # Industry-specific architectures
    ├── virtual-desktop/                # Azure Virtual Desktop architectures
    ├── virtual-machines/               # VM-based reference architectures
    ├── web-apps/                       # Web application architectures
    ├── operator-guides/                # Operator runbooks and guides
    ├── pattern-implementations/        # Code-backed pattern implementations
    ├── aws-professional/               # Azure guidance for AWS professionals
    └── gcp-professional/               # Azure guidance for GCP professionals
```

## Key Section Details

### `docs/patterns/` — Cloud Design Patterns
Contains 40+ cloud design patterns. Each pattern uses one of two file formats:

- **Single Markdown** (e.g., `circuit-breaker.md`, `cqrs.md`, `strangler-fig.md`): YAML frontmatter + full body in one file
- **Split YamlMime + content** (e.g., `cache-aside.yml` + `cache-aside-content.md`): The `.yml` uses `YamlMime:Architecture`, holds metadata and an `[!INCLUDE[](cache-aside-content.md)]` directive; the `-content.md` holds the article body

`index.md` provides the master catalog table mapping each pattern to WAF pillars.

### `docs/guide/` — Application Architecture Fundamentals
```
docs/guide/
├── index.md                            # "Azure application architecture fundamentals" landing
├── architecture-styles/                # N-tier, microservices, event-driven, CQRS, big data, etc.
├── design-principles/                  # Build for business, design for self-healing, scale out, etc.
├── technology-choices/                 # Compute decision tree, data stores, messaging, storage options
├── aks/                                # Azure Kubernetes Service specific guidance
├── aws/                                # AWS to Azure migration guides
├── azure-sandbox/                      # Sandbox environment patterns
├── compute/                            # Compute selection guides
├── multitenant/                        # Multitenant application considerations
├── saas/                               # SaaS architecture guidance
├── saas-multitenant-solution-architecture/
├── startups/                           # Startup architecture patterns
├── responsible-innovation/             # Responsible AI and engineering
└── ...
```

### `docs/microservices/` — Microservices Series
```
docs/microservices/
├── design/                             # Microservice design articles
│   ├── index.md                        # Series landing page
│   ├── compute-options.md              # AKS vs Container Apps vs Functions
│   ├── api-design.md                   # API design for microservices
│   ├── data-considerations.md          # Data consistency across services
│   ├── patterns.md                     # Design patterns for microservices
│   ├── gateway.yml + gateway-content.md       # API gateways
│   ├── interservice-communication.yml + *-content.md
│   └── orchestration.yml + *-content.md
├── model/                              # Domain modeling for microservices
│   ├── domain-analysis.md
│   ├── microservice-boundaries.yml + *-content.md
│   └── tactical-ddd.yml + *-content.md
├── ci-cd.yml + ci-cd-content.md        # CI/CD for microservices
└── ci-cd-kubernetes.yml + *-content.md
```

### `docs/data-guide/` — Data Architecture Guide
```
docs/data-guide/
├── technology-choices/                 # Data store selection, AI services, stream/batch processing
├── scenarios/                          # OLTP, OLAP, lambda architecture, etc.
├── relational-data/                    # Relational data patterns
├── ai-services/                        # AI service selection
└── disaster-recovery/                  # Data DR patterns
```

### `docs/ai-ml/` — AI and Machine Learning
```
docs/ai-ml/
├── index.md                            # AI/ML section landing
├── architecture/                       # AI architecture diagrams
├── guide/                              # AI guides (agent patterns, MLOps, GenAI, RAG)
│   ├── ai-agent-design-patterns.md    # Multi-agent orchestration patterns
│   ├── azure-openai-gateway-*.yml     # Azure OpenAI gateway series
│   ├── genaiops-for-mlops.md          # GenAI operations guidance
│   ├── machine-learning-operations-v2.md
│   ├── mlops-maturity-model.md
│   └── rag/                           # Retrieval-augmented generation patterns
├── idea/                               # AI solution ideas
└── openai/                             # Azure OpenAI specific architectures
```

### `docs/antipatterns/` — Performance Antipatterns
Each antipattern is a self-contained directory:
```
docs/antipatterns/
├── index.md                            # Antipatterns catalog
├── busy-database/                      # Busy Database antipattern
├── busy-front-end/                     # Busy Front End antipattern
├── chatty-io/                          # Chatty I/O antipattern
├── extraneous-fetching/                # Extraneous Fetching antipattern
├── improper-instantiation/             # Improper Instantiation antipattern
├── monolithic-persistence/             # Monolithic Persistence antipattern
├── no-caching/                         # No Caching antipattern
├── noisy-neighbor/                     # Noisy Neighbor antipattern
├── retry-storm/                        # Retry Storm antipattern
└── synchronous-io/                     # Synchronous I/O antipattern
```

### `docs/reference-architectures/` — Reference Architectures
```
docs/reference-architectures/
├── n-tier/                             # N-tier reference architectures (Windows/Linux VMs)
├── microservices/                      # Microservices on AKS
├── containers/                         # Container deployment architectures
├── data/                               # Data pipeline architectures
├── hybrid-networking/                  # Hub-spoke, ExpressRoute, VPN
├── dmz/                                # Network DMZ architectures
├── identity/                           # Identity federation architectures
├── sap/                                # SAP on Azure
├── ibm/                                # IBM workloads on Azure
├── enterprise-integration/             # Logic Apps, Service Bus integration
├── event-hubs/                         # Event Hubs streaming architectures
├── migration/                          # Application migration patterns
└── app-modernization/                  # App modernization scenarios
```

## File Format Patterns

### Standard Markdown Article
```markdown
---
title: Circuit Breaker Pattern
description: Learn how to handle faults...
ms.author: pnp
author: claytonsiemens77
ms.date: 02/05/2025
ms.topic: design-pattern
ms.subservice: cloud-fundamentals
---

# Circuit Breaker pattern
...
```

### YamlMime:Architecture (Split Pattern)
`cache-aside.yml`:
```yaml
### YamlMime:Architecture
metadata:
  title: Cache-Aside Pattern
  description: Learn how to load data...
  ms.author: pnp
  ms.date: 09/11/2025
  ms.topic: design-pattern
  ms.subservice: cloud-fundamentals
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

`cache-aside-content.md` — body only, no frontmatter, excluded from direct publishing by `docfx.json`.

## Code Organization Patterns

1. **Split-file pattern** — Separates machine-readable metadata (YAML) from human-authored content (Markdown). Enables the browse catalog to display thumbnails/summaries without loading full content.

2. **Section-level `toc.yml`** — Each major directory has its own `toc.yml` defining the navigation tree for that section. The root `docs/toc.yml` ties all sections together.

3. **Content includes** — The `includes/` directory at the repo root and section-level includes allow shared boilerplate (e.g., `sol-idea-header.md`) to be injected into many articles.

4. **`-content.md` exclusion** — `docfx.json` explicitly excludes `**/**/*-content.md` from the published content list, ensuring they only appear via their YAML wrappers.

5. **Image co-location** — Each section typically has an `images/` or `media/` subdirectory containing diagrams referenced by articles in that section.

6. **`ms.subservice` taxonomy** — Articles use standardized `ms.subservice` values (`cloud-fundamentals`, `architecture-guide`, `best-practice`) for cross-site filtering and search scoping.
