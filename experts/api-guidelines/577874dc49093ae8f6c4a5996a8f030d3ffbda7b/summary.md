# Microsoft REST API Guidelines — Summary

## Repository Purpose and Goals

The Microsoft REST API Guidelines repository (`microsoft/api-guidelines`) is a public, open-source collection of prescriptive design guidance for building consistent, developer-friendly REST APIs. Published by Microsoft to foster dialogue and learning in the broader API design community, the repository also serves as the authoritative internal reference for Azure and Microsoft Graph service teams.

The primary goals are to help service teams build APIs that:
- Are developer-friendly via consistent patterns and web standards (HTTP, REST, JSON)
- Are efficient, cost-effective, and work well with multi-language SDKs
- Enable fault-tolerant applications through retries, idempotency, and optimistic concurrency
- Are sustainable and versionable via clear API contracts that never break customer workloads
- Are evolvable — customers can adopt a new version without requiring code changes

## Key Features and Capabilities

The repository is organized around three distinct but related bodies of guidance:

**1. Azure REST API Guidelines** (`azure/Guidelines.md`)
The primary reference for Azure data-plane service teams. Covers URL patterns, HTTP methods, status codes, request/response patterns, JSON conventions, API versioning, deprecation, long-running operations (LROs), collections, pagination, filtering, sorting, conditional requests (ETags), Bring Your Own Storage (BYOS), distributed tracing, and error handling. Guidelines are labeled with prescriptive symbols (✅ DO, ☑ YOU SHOULD, ✔ YOU MAY, ⚠ YOU SHOULD NOT, 🚫 DO NOT).

**2. Azure Versioning Guidelines** (`azure/VersioningGuidelines.md`)
A focused Dos and Don'ts list for complying with the Azure versioning and breaking change policy. Covers GA vs preview API version lifecycle, retirement timelines (90 days), how to handle breaking changes, and coordination with the Azure Breaking Change Review Board.

**3. Considerations for Service Design** (`azure/ConsiderationsForServiceDesign.md`)
Introductory and conceptual guidance covering developer experience, hero scenarios, naming principles, management plane vs data plane distinctions, API-first design, long-running operations design philosophy, extensible enums, and design for change resiliency.

**4. Microsoft Graph REST API Guidelines** (`graph/GuidelinesGraph.md`)
A parallel set of guidelines for Microsoft Graph API teams. Covers OData conventions, naming standards, resource modeling patterns, URL structures, query support (`$filter`, `$select`, `$expand`), error handling, backward compatibility, and the Graph-specific API contract.

**5. Graph Pattern Catalog** (`graph/patterns/`)
A library of named, reusable design patterns for common Graph API problems: change tracking, dictionaries, enums, evolvable enums, facets, flat-bag, long-running operations, namespaces, navigation properties, subsets, subtypes, upsert, and viewpoints.

**6. Graph Articles** (`graph/articles/`)
Deep-dive articles on specific topics: collections, core types, deprecation, error responses, filter-as-segment, naming, and nullable fields.

## Primary Use Cases and Target Audience

- **Azure service teams** building or modifying data-plane APIs that must pass Azure HTTP/REST Stewardship Board review
- **Microsoft Graph service teams** defining OData-based APIs that integrate into the Graph ecosystem
- **API designers and architects** at any organization seeking a comprehensive, battle-tested REST API style guide
- **SDK authors** and tooling developers who need to understand the conventions their code must handle
- **Developers consuming Azure or Graph APIs** who want to understand the design rationale behind the APIs they use

## High-Level Architecture Overview

The repository is a documentation-only project — there is no runnable code. It is organized as a hierarchy of Markdown documents:

```
/                          ← Root: general Microsoft REST API Guidelines (deprecated)
├── azure/                 ← Azure-specific guidance (primary reference)
│   ├── Guidelines.md      ← Main Azure REST API Guidelines
│   ├── ConsiderationsForServiceDesign.md
│   ├── VersioningGuidelines.md
│   └── README.md
├── graph/                 ← Microsoft Graph-specific guidance
│   ├── GuidelinesGraph.md ← Main Graph guidelines
│   ├── articles/          ← Deep-dive topic articles
│   └── patterns/          ← Named design patterns catalog
└── Guidelines.md          ← Deprecated top-level doc (redirects to azure/ and graph/)
```

The Azure guidelines use numbered HTML anchor tags (`<a href="#anchor-name">`) on every guideline rule to enable cross-referencing from associated tooling (e.g., API linters, Stewardship Board review tools).

## Related Projects and Dependencies

- **Azure Resource Manager Resource Provider Contract** — for management-plane (ARM) APIs (separate repo)
- **Azure REST API Specs** (`Azure/azure-rest-api-specs`) — where OpenAPI specifications for Azure services live
- **Azure API Style Guide** (`Azure/azure-api-style-guide`) — OpenAPI-level style linting rules
- **AutoRest** — code generation tool; Azure guidelines reference autorest extensions for OpenAPI
- **OData 4.01** — the protocol standard underlying Microsoft Graph's query conventions
- **RFC 7231, RFC 9110** — HTTP standards that Azure guidelines are built on top of
- **RFC 7396** — JSON Merge Patch, the required PATCH body format
- **RFC 3339** — date/time format required for JSON fields
- **RFC 4122** — UUID format required for identifier fields
- **OASIS Repeatable Requests v1.0** — standard for idempotent POST operations
