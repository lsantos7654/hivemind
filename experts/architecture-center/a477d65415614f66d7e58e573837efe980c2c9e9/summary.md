# Azure Architecture Center — Repository Summary

## Repository Purpose and Goals

The Azure Architecture Center repository (`MicrosoftDocs/architecture-center`) is the source content for Microsoft's official cloud architecture guidance site at <https://azure.com/architecture>. Maintained by Microsoft's Patterns & Practices (PnP) team, it serves as the authoritative reference for designing, building, and operating workloads on Microsoft Azure.

The repository is a documentation-only project — there is no executable code, libraries, or deployable tooling. Its purpose is to provide cloud architects, developers, and IT professionals with:

- Proven design patterns for distributed, cloud-native systems
- Architecture style guidance for common workload types
- Technology selection frameworks and decision trees
- Reference architectures and example scenarios demonstrating best practices
- Guidance for professionals migrating from AWS or GCP to Azure

## Key Features and Capabilities

**Cloud Design Patterns Catalog** — 40+ named patterns (Ambassador, Circuit Breaker, CQRS, Event Sourcing, Saga, Strangler Fig, etc.) each mapped to one or more Azure Well-Architected Framework (WAF) pillars: Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency.

**Architecture Styles** — Structured guidance for N-tier, Web-Queue-Worker, Microservices, Event-Driven, Big Data, Big Compute, and CQRS architectures, with logical diagrams and Azure service recommendations for each.

**AI Agent Orchestration Patterns** — Dedicated guidance for multi-agent AI architectures including sequential, concurrent, group chat, handoff, and magentic orchestration patterns.

**Performance Antipatterns** — 10 antipatterns (Busy Database, Chatty I/O, Extraneous Fetching, Retry Storm, Synchronous I/O, etc.) with root cause analysis, symptoms, and remediation.

**Best Practices Catalog** — Opinionated guidance for API design, API implementation, autoscaling, background jobs, caching, CDN, data partitioning, message encoding, monitoring, and transient fault handling.

**Microservices Design Series** — End-to-end guidance for designing microservice architectures including compute options, interservice communication, API design, API gateways, data considerations, and container orchestration.

**Data Guide** — Technology selection frameworks for analytical stores, batch/stream processing, relational data, AI services, and disaster recovery.

**Multi-Cloud Mapping** — Service mapping tables for AWS-to-Azure and GCP-to-Azure professionals covering compute, storage, networking, databases, messaging, and security.

**Reference Architectures and Example Scenarios** — Production-quality blueprint architectures covering N-tier, microservices, SAP, mainframe, containers (AKS), networking, identity, and more.

## Target Audience

- **Cloud architects** designing Azure workloads from scratch or migrating from on-premises/other clouds
- **Application developers** adopting distributed systems patterns
- **IT professionals** looking for Azure service selection guidance
- **AWS and GCP professionals** transitioning to Azure

## High-Level Architecture Overview

The repository is a pure documentation system built on Microsoft's Open Publishing Service (OPS). Content lives under `docs/` as a mix of Markdown files and YAML files. Two key file patterns exist:

1. **Single-file articles** — standard Markdown files with YAML frontmatter (`title`, `description`, `ms.author`, `ms.date`, `ms.topic`, etc.)
2. **Split-file articles** — a `foo.yml` stub using `YamlMime:Architecture` that references a `foo-content.md` file via `[!INCLUDE[](foo-content.md)]`. The YAML file holds metadata, Azure service tags, categories, and thumbnail; the `-content.md` file holds the full body. This pattern is used extensively in patterns, microservices, and reference architectures sections. The DocFX build configuration in `docs/docfx.json` explicitly excludes `*-content.md` files from direct publishing — they are only surfaced via their YAML wrapper.

The build system is DocFX with the Markdig rendering engine. Navigation is defined by `toc.yml` files hierarchically throughout the content tree. A breadcrumb `_bread/toc.yml` file anchors the Azure-wide navigation. Over 1,600 URL redirections (`.openpublishing.redirection.json`) accommodate the long history of content reorganization.

## Related Projects and Dependencies

- **Azure Well-Architected Framework** — The five WAF pillars (Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency) are the organizing principle for pattern categorization throughout the repo
- **Cloud Adoption Framework (CAF)** — Referenced for organizational cloud adoption strategy and landing zones
- **Azure landing zones** — Landing zone patterns documented under `docs/landing-zones/`
- **DocFX** — Build tool for generating the documentation site
- **Markdig** — Markdown rendering engine specified in `docfx.json`
- **cspell** — Spell-checking via `cspell.json` config files at root and within `docs/`
- **Acrolinx** — Content quality and style checking (`.acrolinx-config.edn`)
- **GitHub Actions / OPS CI** — Pull request processing and publishing via Microsoft's Open Publishing pipeline
