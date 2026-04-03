# Microsoft REST API Guidelines — Code Structure

## Annotated Directory Tree

```
microsoft/api-guidelines (root)
│
├── README.md
│   Entry point. Explains the repository's purpose, links to Azure and Graph
│   sub-guidelines, and includes the CC BY 4.0 license badge.
│
├── Guidelines.md
│   DEPRECATED top-level guidelines document. Now contains only a notice
│   redirecting readers to azure/Guidelines.md and graph/GuidelinesGraph.md.
│   Retained for backward-compatibility of existing links.
│   The original content was moved to graph/Guidelines-deprecated.md.
│
├── CONTRIBUTING.md
│   Contributor guide: how to open issues, documentation styleguide
│   (GitHub-flavored Markdown, JSON formatting conventions), commit message
│   format, and pull request process (target branch: vNext).
│
├── SECURITY.md
│   Microsoft security disclosure policy for the repository.
│
├── license.txt
│   Creative Commons Attribution 4.0 International (CC BY 4.0) license.
│
├── azure/                        ← Azure-specific REST API guidance
│   ├── README.md
│   │   Overview of Azure REST API resources: links to Guidelines.md,
│   │   ConsiderationsForServiceDesign.md, Azure API Style Guide, versioning
│   │   policy, and breaking changes documentation. Contact info for the
│   │   REST API Stewardship Board.
│   │
│   ├── Guidelines.md             ← PRIMARY Azure reference document
│   │   The main prescriptive guidelines for Azure data-plane API teams.
│   │   ~1,300 lines. Sections:
│   │     - History (change log table)
│   │     - Introduction (goals, guidance notation)
│   │     - Building Blocks: HTTP, REST, & JSON
│   │       - Uniform Resource Locators (URLs)
│   │       - HTTP Request/Response Pattern (idempotency, status codes)
│   │       - HTTP Query Parameters and Header Values
│   │       - REST principles (resource schema, field mutability, error handling)
│   │       - JSON (casing, null values, enums, polymorphic types)
│   │     - Common API Patterns
│   │       - Performing an Action (action URL pattern)
│   │       - Collections (pagination, query options: filter/orderby/skip/top/maxpagesize)
│   │       - API Versioning (api-version query param, date-based versioning)
│   │       - Deprecating Behavior Notification (azure-deprecating header)
│   │       - Repeatability of Requests (Repeatability-Request-ID headers)
│   │       - Long-Running Operations & Jobs (LRO patterns: PUT/DELETE/POST/batch)
│   │       - Bring Your Own Storage (BYOS)
│   │       - Conditional Requests (ETags, If-Match, If-None-Match)
│   │       - Returning String Offsets & Lengths (UTF-8/UTF-16/CodePoint)
│   │       - Distributed Tracing & Telemetry
│   │     - Final thoughts
│   │   Every guideline has an HTML anchor tag for cross-referencing by tooling.
│   │
│   ├── ConsiderationsForServiceDesign.md   ← Conceptual companion to Guidelines.md
│   │   Introduction to API design philosophy for Azure teams. Sections:
│   │     - History (change log)
│   │     - Introduction (principles: versioning, compatibility, backward compat)
│   │     - Azure Management Plane vs Data Plane
│   │     - Start with the Developer Experience
│   │     - Focus on Hero Scenarios
│   │     - Start with your API Definition (OpenAPI)
│   │     - Design for Change Resiliency
│   │     - Use Good Names (naming principles, common names table)
│   │     - Avoid Surprises (polymorphism, surprises section)
│   │     - Long-Running Operations (conceptual introduction)
│   │     - Returning String Offsets & Lengths (detailed example)
│   │
│   ├── VersioningGuidelines.md   ← Azure versioning and breaking change rules
│   │   Focused "Dos and Don'ts" list for the Azure versioning policy. Covers:
│   │     - Testing API contracts before merging to production
│   │     - Retiring preview API versions (90-day rule)
│   │     - Coordinating with the Azure Breaking Change Review Board
│   │     - Date-ordering for preview vs GA API versions
│   │     - Deprovisioning retired API versions
│   │     - Behavior changes requiring review (rate limits, permissions)
│   │
│   └── .markdownlint.json
│       Markdownlint configuration file for the azure/ directory.
│       Disables specific markdown lint rules to accommodate the formatting
│       used in Guidelines.md (e.g., inline HTML, table syntax).
│
└── graph/                        ← Microsoft Graph-specific guidance
    │
    ├── GuidelinesGraph.md        ← PRIMARY Graph reference document
    │   Comprehensive guidelines for Microsoft Graph API teams.
    │   Sections:
    │     - Introduction (goals, legend/notation)
    │     - Design approach
    │       - Naming (lowerCamelCase, no redundant words, no brand names)
    │       - Uniform Resource Locators (URLs)
    │       - Resource modeling patterns (pros/cons, nullable properties)
    │       - Query support
    │       - Behavior modeling
    │       - Error handling
    │       - Limitations on core types
    │     - External standards (OData, HTTP, JSON)
    │     - API contract and nonbackward compatible changes
    │       - Versioning and deprecation
    │     - Recommended API design patterns (links to patterns catalog)
    │     - References
    │
    ├── Guidelines-deprecated.md
    │   The original top-level Guidelines.md content, preserved here after
    │   it was superseded by the azure/ and graph/ sub-guidelines.
    │
    ├── ModelExample.png
    │   Diagram illustrating a sample resource model (used in GuidelinesGraph.md).
    │
    ├── articles/                 ← Deep-dive topic articles for Graph APIs
    │   ├── collections.md        URL patterns, item keys, serialization, nested
    │   │                         collections, delta query support, pagination
    │   ├── coreTypes.md          Primitive types allowed in Graph APIs
    │   ├── deprecation.md        How to deprecate Graph API elements
    │   ├── errorResponses.md     Graph error response structure and conventions
    │   ├── filter-as-segment.md  Using $filter as a URL path segment
    │   ├── naming.md             Detailed naming conventions (casing, compound
    │   │                         names, identity props, date/time props, common
    │   │                         property names table)
    │   └── nullable.md           Graph nullable property conventions
    │
    └── patterns/                 ← Named design pattern catalog for Graph APIs
        ├── PatternDescriptionTemplate.md   Template for new pattern docs
        ├── antiPatternTemplate.md          Template for anti-pattern docs
        ├── alternate-key.md        Alternate key (non-id) addressing
        ├── change-tracking.md      Delta query / change tracking pattern
        ├── default-properties.md   Default vs non-default property projection
        ├── dictionary.md           Dictionary (open type / dynamic properties) — service guidance
        ├── dictionary-client-guidance.md   Dictionary pattern — client guidance
        ├── enums.md                Closed enum usage
        ├── evolvable-enums.md      Open/extensible enum pattern
        ├── facets.md               Facet (type extension) pattern
        ├── flat-bag.md             Flat-bag resource modeling
        ├── long-running-operations.md  LRO pattern for Graph
        ├── namespace.md            Namespace conventions
        ├── navigation-property.md  Navigation property modeling
        ├── operations.md           Function and action (behavior) modeling
        ├── subsets.md              Subset resource pattern
        ├── subtypes.md             Inheritance / subtype modeling
        ├── upsert.md               Upsert (create-or-update) pattern
        ├── viewpoint.md            Viewpoint (caller-relative resource) pattern
        ├── LRO.gif                 Animated diagram for LRO flow
        └── RELO.gif                Animated diagram for RELO (related LRO) flow
```

## Module and Package Organization

This is a documentation-only repository with no runnable source code. The organizational units are:

- **Root level** — top-level README, license, contribution guide, security policy, and the deprecated original guidelines
- **`azure/`** — self-contained body of Azure REST API guidance with its own README, main guidelines, companion design document, and versioning rules
- **`graph/`** — self-contained body of Microsoft Graph API guidance, split into:
  - **Main guidelines document** — overview and core principles
  - **`articles/`** — focused deep-dives on specific technical topics
  - **`patterns/`** — a named, cross-referenceable catalog of design patterns

## Key Files and Their Roles

| File | Role |
|------|------|
| `azure/Guidelines.md` | The authoritative, prescriptive set of rules for Azure data-plane REST APIs; every guideline has an HTML anchor for tooling |
| `azure/ConsiderationsForServiceDesign.md` | Conceptual companion — the "why" behind the guidelines, plus hero scenario methodology |
| `azure/VersioningGuidelines.md` | Versioning and breaking change Dos/Don'ts |
| `graph/GuidelinesGraph.md` | Authoritative rules for Microsoft Graph API teams |
| `graph/articles/naming.md` | Detailed naming conventions (casing, property naming, common property names table) |
| `graph/articles/collections.md` | Collection URL patterns, pagination, delta queries |
| `graph/articles/errorResponses.md` | Graph error response structure |
| `graph/patterns/long-running-operations.md` | Graph LRO pattern details |
| `graph/patterns/evolvable-enums.md` | Extensible enum pattern |
| `graph/patterns/change-tracking.md` | Delta query / change tracking |

## Code Organization Patterns

**Prescriptive notation system** — Azure guidelines use emoji-based labels (✅ DO, ☑ YOU SHOULD, ✔ YOU MAY, ⚠ YOU SHOULD NOT, 🚫 DO NOT) to indicate the strength of each guideline. Graph guidelines use (✔ MUST, 🚫 MUST NOT, ☑ SHOULD, ⚠ SHOULD NOT).

**HTML anchor cross-referencing** — Every guideline in `azure/Guidelines.md` has a named HTML anchor tag (e.g., `<a href="#http-url-pattern" name="http-url-pattern">`), allowing external tooling such as API linters and the Stewardship Board review system to reference specific rules by ID.

**Pattern catalog structure** — Graph patterns follow a template (`PatternDescriptionTemplate.md`) that describes the problem, solution, tradeoffs, and examples in a consistent format.

**Living document approach** — Both main guideline files include a change history table at the top, tracking which sections were added or updated and when. Issues and pull requests are the primary mechanisms for proposing changes.

**Branch convention** — Active development happens on the `vNext` branch; contributors are instructed to submit PRs targeting `vNext`.
