# Awesome Design Patterns — Code Structure

## Complete Annotated Directory Tree

```
awesome-design-patterns/          # Root of repository
├── README.md                     # PRIMARY CONTENT FILE — the entire curated list
├── contributing.md               # Contribution guidelines for PRs
├── _config.yml                   # Jekyll/GitHub Pages configuration
└── .git/                         # Git repository metadata (not content)
```

This repository is intentionally minimal. There are **no source code directories**, no `src/`, no `lib/`, no tests, no package manager manifests (`package.json`, `requirements.txt`, `Gemfile`, etc.). The entire knowledge surface is `README.md`.

## Module and Package Organisation

Because this is a documentation-only repository, "module" here means the logical sections within `README.md`. The file is structured as a single-level hierarchy of markdown sections, each representing a domain of design-pattern resources.

### Top-Level Sections in README.md

| Section Heading | Anchor | Line Range (approx.) | Description |
|---|---|---|---|
| Contents (TOC) | — | 16–30 | Clickable anchor-link table of contents |
| Programming Language Design Patterns | `#programming-language-design-patterns` | 33–100 | Language-specific GoF/idiom pattern resources |
| General Architecture | `#general-architecture` | 102–110 | Broad architectural patterns and catalogs |
| Cloud Architecture | `#cloud-architecture` | 112–120 | AWS, Azure, GCP cloud design patterns |
| Serverless Architecture | `#serverless-architecture` | 122–129 | Serverless patterns and reference architectures |
| Micro services & Distributed Systems | `#micro-services--distributed-systems` | 131–139 | Microservices patterns, 12-Factor, messaging |
| Internet of things | `#internet-of-things` | 140–143 | IoT communication and architecture patterns |
| Big Data | `#big-data` | 144–147 | MapReduce, stream processing patterns |
| Machine Learning | `#machine-learning` | 148–150 | Distributed ML system patterns |
| Databases and Storage | `#databases` | 151–170 | SQL, NoSQL, and cloud storage patterns |
| DevOps & containers | `#devops--containers` | 171–180 | Kubernetes, containers, CDK patterns |
| Mobile | `#mobile` | 182–188 | iOS and Android architecture patterns |
| Front-End Development | `#front-end-development` | 190–198 | UI patterns, CSS, MV* architectures |
| Security | `#security` | 199–205 | Security architecture and OWASP |
| Books | `#books` | 206–216 | Recommended reading list |
| Other Awesome Lists | `#other-awesome-lists` | 218–219 | Pointer to the sindresorhus/awesome registry |
| Contributing | `#contributing` | 221–222 | Link to contributing.md |
| License | `#license` | 224–229 | CC0 public domain declaration |

## Main Source Directories and Their Purposes

There are no source directories. The repository's content is entirely flat:

### `README.md` (primary file)
The complete curated list. Every link entry follows the format:
```
- [name](URL) - Description.
```
or for sub-items under a language:
```
- Language
    - [resource-name](URL) - Description.
```

This file is the published website content and the sole reference artifact.

### `contributing.md`
Documents the quality bar for contributions:
- Resources must cover multiple patterns (not a single pattern).
- No duplicate submissions.
- Format: `[name](link) - Description.` with trailing period.
- New categories are welcome.
- PRs must explain why a resource should be included.
- Only software-related patterns.

### `_config.yml`
Single-line Jekyll configuration:
```yaml
theme: jekyll-theme-architect
```
Instructs GitHub Pages to render the repository using the [`jekyll-theme-architect`](https://github.com/pages-themes/architect) theme, providing the public website at `https://github.com/DovAmir/awesome-design-patterns` (or the associated GitHub Pages URL).

## Key Files and Their Roles

### `README.md` — The Entire Knowledge Surface

This is the only file a user of this list needs to interact with. It covers:

**Language-specific resources (lines 33–100):**
- 18 languages covered: AngularJS, C#, C++, Clojure, Go, Java, JavaScript, Kotlin, Node.js, Object Oriented (general), PHP, Python, React, Ruby, Rust, Scala, Swift, TypeScript, UML, Vue.js, Elixir.
- Notable inclusions:
  - `java-design-patterns` (iluwatar) — 480+ patterns implemented in Java
  - `design-patterns-for-humans` (kamranahmedse) — PHP ultra-simplified GoF
  - `python-patterns` (faif) — Python GoF + idiomatic patterns
  - `go-patterns` (tmrts) — Go-specific concurrency and structural patterns
  - `rust-unofficial/patterns` — Rust idioms and patterns

**Architecture resources (lines 102–110):**
- Martin Fowler's enterprise application catalog (eaaCatalog)
- system-design-primer (Donne Martin)
- Reactive Design Patterns (Roland Kuhn)
- InnerSource Patterns (innersourcecommons.org)

**Cloud (lines 112–120):**
- AWS CDP (clouddesignpattern.org)
- Azure Architecture Center
- GCP Solutions
- SaaS multi-tenancy patterns

**Microservices (lines 131–139):**
- microservices.io (Chris Richardson's pattern language)
- 12factor.net
- Enterprise Integration Patterns (Hohpe & Woolf)
- Martin Fowler's distributed systems patterns

**Database patterns (lines 151–170):**
- SQL: Azure SaaS tenancy, databaseanswers.org, sqlcheck anti-patterns, AWS Redshift ETL/ELT
- NoSQL: eBay NoSQL resilience, MongoDB patterns, DynamoDB labs, Redis best practices
- Storage: AWS S3 best practices, on-premises vs. AWS storage comparison

**DevOps & Containers (lines 171–180):**
- Kubernetes production patterns (gravitational workshop)
- Container design patterns for Kubernetes pods
- CDK patterns (cdkpatterns.com, awscdk.io)

**Security (lines 199–205):**
- OpenSecurityArchitecture pattern landscape
- Martin Fowler web security basics
- OWASP Security by Design Principles
- Azure security best practices

## Code Organisation Patterns

Since this is a documentation repository, the "patterns" are editorial conventions:

1. **Hierarchical categorisation** — top-level categories are broad domains; sub-items within language sections use indented lists.
2. **Consistent link format** — `[display-name](URL) - Short description ending with period.`
3. **Anchor-linked TOC** — the Contents section at the top links to every major section, supporting both web and raw markdown navigation.
4. **CC0 license** — explicitly public domain, enabling unrestricted reuse.
5. **Awesome-list badge compliance** — includes the official awesome badge, PRs welcome badge, and Gitter community badge.
6. **No versioning of content** — the list is maintained as a living document on the `master` branch; individual resource links may become stale over time.
7. **Flat books section** — notable books are also listed in the domain sections and consolidated in a dedicated `## Books` section for discoverability.
