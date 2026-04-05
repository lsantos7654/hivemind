# Awesome Design Patterns — APIs and Interfaces

## Overview

This repository is a curated documentation list, not a software library. It has no public API, no importable modules, no CLI, and no programmatic interface. Its "API" is the **content structure of `README.md`**: a set of categorised, anchor-linked sections that users navigate to discover design-pattern resources.

This document describes the content interface — how to navigate, use, and contribute to the list — as well as the interfaces of the most significant linked external resources.

---

## Content Interface: README.md Structure

### Table of Contents Anchors

The README provides a clickable TOC. Each anchor maps to a section:

| Anchor | Section |
|---|---|
| `#programming-language-design-patterns` | Language-specific GoF/idiomatic patterns |
| `#general-architecture` | Broad architectural pattern resources |
| `#cloud-architecture` | AWS, Azure, GCP cloud patterns |
| `#serverless-architecture` | Serverless design patterns |
| `#micro-services--distributed-systems` | Microservices and distributed systems |
| `#internet-of-things` | IoT patterns |
| `#big-data` | MapReduce and streaming patterns |
| `#machine-learning` | ML system design patterns |
| `#databases` | SQL, NoSQL, and storage patterns |
| `#devops--containers` | Kubernetes, containers, CDK |
| `#mobile` | iOS and Android patterns |
| `#front-end-development` | UI, CSS, MV* architectures |
| `#security` | Security architecture patterns |
| `#books` | Recommended books |
| `#other-awesome-lists` | Links to the broader awesome ecosystem |
| `#contributing` | How to contribute |

### Entry Format

Every resource entry in the list uses one of these two formats:

**Simple entry:**
```markdown
- [Resource Name](https://url.example.com) - Brief description ending in period.
```

**Language sub-entry (indented under language heading):**
```markdown
- LanguageName
    - [resource-name](https://url.example.com) - Description.
    - [resource-name-2](https://url.example.com) - Another description.
```

---

## Key External Resources and Their Interfaces

Because the repository aggregates links, the most useful "API" knowledge concerns how the linked resources work. The most significant ones are documented below.

### 1. java-design-patterns (iluwatar)

**URL:** https://java-design-patterns.com/patterns/  
**GitHub:** https://github.com/iluwatar/java-design-patterns

Provides 480+ patterns implemented in Java with:
- Searchable web catalog at java-design-patterns.com
- Each pattern has: intent, explanation, UML diagram, code example, applicability
- Maven-based build; each pattern is a Maven module

### 2. design-patterns-for-humans (kamranahmedse) — PHP

**GitHub:** https://github.com/kamranahmedse/design-patterns-for-humans

Ultra-simplified PHP 7 GoF pattern explanations covering all 23 patterns:
- Creational: Simple Factory, Factory Method, Abstract Factory, Builder, Prototype, Singleton
- Structural: Adapter, Bridge, Composite, Decorator, Facade, Flyweight, Proxy
- Behavioral: Chain of Responsibility, Command, Iterator, Mediator, Memento, Observer, Visitor, Strategy, State, Template Method

### 3. python-patterns (faif)

**GitHub:** https://github.com/faif/python-patterns

Python implementations of GoF and idiomatic patterns:
- Each pattern is a standalone `.py` file with a `__main__` block demonstrating usage
- Categories: Creational, Structural, Behavioral, Fundamental, Other

**Example usage pattern:**
```python
# python-patterns uses standalone scripts; run directly:
python creational/singleton.py
python behavioral/observer.py
```

### 4. go-patterns (tmrts)

**GitHub:** https://github.com/tmrts/go-patterns

Go-idiomatic pattern implementations:
- Creational, structural, behavioral GoF patterns
- Concurrency patterns (fan-in, fan-out, pipeline, etc.)
- Stability patterns (circuit breaker, etc.)

### 5. microservices.io (Chris Richardson)

**URL:** http://microservices.io/patterns

A structured pattern language for microservices:
- Application patterns (Database per service, Saga, CQRS, Event Sourcing, API Gateway, etc.)
- Infrastructure patterns (Service registry, Circuit Breaker, etc.)
- Each pattern: context, forces, solution, resulting context, related patterns

### 6. system-design-primer (donnemartin)

**GitHub:** https://github.com/donnemartin/system-design-primer

Comprehensive system design guide:
- How to approach system design interview questions
- Scalability, performance, latency, throughput concepts
- Specific components: DNS, CDN, Load Balancers, Reverse Proxies, Databases, Caches, Asynchronism, Communication (REST, RPC)
- Real-world architectures

### 7. 12factor.net

**URL:** https://12factor.net

The Twelve-Factor App methodology — a set of 12 principles for building cloud-native applications:
1. Codebase, 2. Dependencies, 3. Config, 4. Backing Services, 5. Build/Release/Run, 6. Processes, 7. Port Binding, 8. Concurrency, 9. Disposability, 10. Dev/Prod Parity, 11. Logs, 12. Admin Processes

### 8. Enterprise Integration Patterns (Hohpe & Woolf)

**URL:** http://www.enterpriseintegrationpatterns.com/patterns/messaging/toc.html

Canonical messaging patterns catalog:
- Message Channel, Message, Pipes and Filters, Message Router, Message Translator, Message Endpoint
- 65 patterns for enterprise messaging systems

### 9. Martin Fowler's Catalogs

- **eaaCatalog:** https://martinfowler.com/eaaCatalog — Enterprise Application Architecture patterns
- **GUI Architectures:** https://martinfowler.com/eaaDev/uiArchs.html — MVC, MVP, MVVM history
- **Distributed Systems Patterns:** https://martinfowler.com/articles/patterns-of-distributed-systems/

### 10. Azure Architecture Center

**URL:** https://docs.microsoft.com/en-us/azure/architecture/patterns

Cloud design patterns categorised by:
- Availability (Health Endpoint Monitoring, Queue-Based Load Leveling, etc.)
- Data Management (Cache-Aside, CQRS, Event Sourcing, Sharding, etc.)
- Design and Implementation (Ambassador, Anti-Corruption Layer, Strangler Fig, etc.)
- Messaging (Choreography, Competing Consumers, Pipes and Filters, etc.)
- Performance (Bulkhead, Circuit Breaker, Retry, Throttling, etc.)

---

## Integration Patterns and Workflows

### Using the List as a Reference

1. **Navigate by domain** — use the TOC anchors to jump to the relevant category.
2. **Navigate by language** — scroll to "Programming Language Design Patterns" and find your language.
3. **Find books** — the `#books` section consolidates recommended reading.

### Contributing a New Resource

Per `contributing.md`:

```markdown
1. Fork the repository
2. Create a branch: git checkout -b my-new-branch
3. Add your link in the correct section using the format:
   - [name](link) - Description.
4. Ensure the resource covers multiple patterns (not a single pattern)
5. Check for duplicates before adding
6. Commit: git commit -am 'add <resource> to <section>'
7. Push and open a pull request
8. PR description must explain why the resource should be included
```

Quality criteria from `contributing.md`:
- Must cover **multiple** patterns (not a single pattern guide)
- Must be **software-related**
- Descriptions must be **short, simple, and end with a period**
- No duplicates

### Adding a New Category

New top-level categories are explicitly welcome per `contributing.md`. The convention is:
1. Add the `## New Category` heading in `README.md`.
2. Add a TOC entry in the Contents section linking to the new anchor.
3. Include at least one high-quality resource in the new category.

---

## Configuration Options and Extension Points

### Jekyll Theme Change

The only configurable aspect of the site rendering is `_config.yml`:

```yaml
# Current:
theme: jekyll-theme-architect

# Could be changed to any GitHub Pages-supported theme:
# theme: minima
# theme: jekyll-theme-cayman
# theme: jekyll-theme-slate
```

### GitHub Pages Configuration (via repository settings)

Not in files but configurable via GitHub UI:
- Custom domain
- HTTPS enforcement
- Branch selection (currently `master` root)

No other extension points exist — the repository is intentionally minimal.
