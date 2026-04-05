# Awesome Software Architecture — Code Structure

## Annotated Directory Tree

```
awesome-software-architecture/
├── README.md                          # GitHub landing page; mirrors mkdocs.yml nav with TOC and descriptions
├── mkdocs.yml                         # MkDocs site config: nav tree, theme, markdown extensions, site URL
├── contributing.md                    # Community contribution guidelines and PR workflow
├── banner.png                         # Banner image used in README.md header
├── LICENSE                            # CC0 1.0 Universal public domain dedication
├── Program.cs                         # C# .NET 9 console app: git diff → release notes generator
├── ReleaseNotes.csproj                # .NET 9 project file for the release notes utility
│
├── .github/
│   ├── FUNDING.yml                    # GitHub Sponsors/funding configuration
│   └── workflows/
│       └── ci.yml                     # GitHub Actions: link-check + MkDocs deploy to GitHub Pages
│
├── assets/
│   └── home.png                       # Image used on the MkDocs home page
│
└── docs/                              # ALL content lives here — one .md file per topic
    ├── README.md                      # MkDocs home page content (mirrors repo README)
    ├── abstraction.md                 # Abstraction resources
    ├── algorithm.md                   # Algorithms resources
    ├── architecture-documententation.md  # Architecture documentation (C4, ADRs, etc.)
    ├── back-pressure.md               # Back pressure pattern resources
    ├── caching.md                     # Caching strategies and tools
    ├── clean-architecture.md          # Clean Architecture (Uncle Bob) resources
    ├── clean-code.md                  # Clean Code principles and practices
    ├── cloud-best-practices.md        # Cloud best practices
    ├── cloud-native.md                # Cloud native patterns and tooling
    ├── code-review.md                 # Code review practices
    ├── concurrency.md                 # Concurrency patterns and resources
    ├── cqrs.md                        # CQRS pattern resources
    ├── data-driven-design.md          # Data-driven design resources
    ├── distributed-locking.md         # Distributed locking resources
    ├── distributed-transactions.md    # Distributed transactions and Saga pattern
    ├── event-driven-architecture.md   # Event-driven architecture resources
    ├── event-sourcing.md              # Event sourcing resources
    ├── eventual-consistency.md        # Eventual consistency resources
    ├── functional.md                  # Functional programming resources
    ├── grpc.md                        # gRPC resources
    ├── hexagonal-architecture.md      # Hexagonal / Ports & Adapters architecture
    ├── ids.md                         # Identifier generation (UUIDs, ULIDs, etc.)
    ├── micro-frontend.md              # Micro-frontend architecture resources
    ├── modular-monolith.md            # Modular monolith resources
    ├── object-oriented-design.md      # OOP design resources
    ├── onion-architecture.md          # Onion architecture resources
    ├── open-source.md                 # Open source contribution resources
    ├── others.md                      # Miscellaneous resources
    ├── refactoring.md                 # Refactoring resources
    ├── rest.md                        # RESTful API design resources
    ├── scaling.md                     # Scaling strategies resources
    ├── serverless.md                  # Serverless architecture resources
    ├── service-oriented-architecture.md  # SOA resources
    ├── software-architecture.md       # Core software architecture resources
    ├── type-driven-design.md          # Type-driven design resources
    ├── vertical-slice-architecture.md # Vertical Slice Architecture resources
    │
    ├── actor-model-architecture/      # Actor Model subtopic directory
    │   ├── actor-model-architecture.md
    │   ├── akka-net.md                # Akka.NET framework resources
    │   ├── orleans.md                 # Microsoft Orleans resources
    │   └── protoactor.md              # Proto.Actor resources
    │
    ├── ai/                            # AI/ML topic directory
    │   ├── a2a.md                     # Agent-to-Agent (A2A) protocol resources
    │   ├── agent-framework.md         # Microsoft Agent Framework resources
    │   ├── agent.md                   # AI agents resources
    │   ├── ai.md                      # General AI resources
    │   ├── code-assistants.md         # AI code assistant tools
    │   ├── embedding-vector.md        # Embeddings and vector databases
    │   ├── langchain.md               # LangChain resources
    │   ├── llms.md                    # Large Language Model resources
    │   ├── mcp.md                     # Model Context Protocol resources
    │   ├── ml.net.md                  # ML.NET resources
    │   ├── prompt-engineering.md      # Prompt engineering resources
    │   ├── rag.md                     # Retrieval-Augmented Generation resources
    │   ├── semantic-kernel.md         # Semantic Kernel & .NET AI resources
    │   └── models/                    # AI model subtopics
    │       ├── hugging-face.md
    │       ├── models.md
    │       ├── ollama.md
    │       ├── openai.md
    │       └── phi.md
    │
    ├── anti-patterns/                 # Anti-patterns directory
    │   ├── anti-patterns.md
    │   ├── big-ball-of-mud.md
    │   ├── code-smells.md
    │   ├── god-object.md
    │   ├── leaky-abstractions.md
    │   ├── partial-object.md
    │   └── static-cling.md
    │
    ├── architectural-design-principles/  # Design principles directory
    │   ├── architectural-design-principles.md
    │   ├── cap.md                     # CAP Theorem
    │   ├── cohesion.md
    │   ├── coupling.md
    │   ├── cqs.md                     # Command Query Separation
    │   ├── cross-cutting-concerns.md
    │   ├── dependency-inversion.md
    │   ├── dry.md                     # Don't Repeat Yourself
    │   ├── encapsulation.md
    │   ├── fail-fast.md
    │   ├── favor-composition-over-inheritance.md
    │   ├── grasp.md                   # GRASP patterns
    │   ├── interface-segregation.md
    │   ├── inversion-control.md       # IoC
    │   ├── kiss.md                    # Keep It Simple
    │   ├── open-closed-principles.md
    │   ├── persistence-ignorance.md
    │   ├── single-responsibility.md
    │   ├── solid.md
    │   └── yagni.md
    │
    ├── azure/                         # Microsoft Azure cloud topics
    │   ├── aks.md                     # Azure Kubernetes Service
    │   ├── azure-api-management.md
    │   ├── azure-app-service.md
    │   ├── azure-app-service-plan.md
    │   ├── azure-arc.md
    │   ├── azure-cloud.md
    │   ├── azure-configuration.md
    │   ├── azure-functions.md
    │   ├── azure-load-balancing.md
    │   ├── azure-logic-app.md
    │   ├── messaging/                 # Azure messaging services
    │   ├── nosql/                     # Azure NoSQL (CosmosDB, etc.)
    │   └── storage/                   # Azure storage services
    │
    ├── cloud-design-patterns/         # Cloud design patterns
    │   ├── ambassador-pattern.md
    │   ├── anti-corruption-layer-pattern.md
    │   ├── bff.md                     # Backends for Frontends
    │   ├── bulkhead-pattern.md
    │   ├── circuit-breaker.md
    │   ├── cloud-design-patterns.md
    │   ├── exactly-one-delivery.md
    │   ├── gateway-aggregation.md
    │   ├── gateway-pattern.md
    │   ├── inbox-pattern.md
    │   ├── outbox-pattern.md
    │   ├── sidecar.md
    │   └── strangler-fig-pattern.md
    │
    ├── database/                      # Database topics
    │   ├── nosql/                     # NoSQL databases (CosmosDB, MongoDB, DocumentDB)
    │   ├── relational/                # Relational DB (PostgreSQL, SQL)
    │   ├── replication.md
    │   └── sharding.md
    │
    ├── design-best-practices/         # Best practices directory
    │   ├── 12-factor.md               # 12-Factor App methodology
    │   ├── design-best-practices.md
    │   └── thin-controllers.md
    │
    ├── design-patterns/               # GoF and other design patterns
    │   ├── adapter-pattern.md
    │   ├── builder.md
    │   ├── chain-of-responsibility.md
    │   ├── command-message-pattern.md
    │   ├── command-pattern.md
    │   ├── decorator-pattern.md
    │   ├── design-patterns.md
    │   ├── factory-pattern.md
    │   ├── mediator-pattern.md
    │   ├── observer.md
    │   ├── query-object-pattern.md
    │   ├── repository-pattern.md
    │   ├── repr.md                    # Request-Endpoint-Response pattern
    │   ├── service-locator.md
    │   ├── singleton.md
    │   ├── specification-pattern.md
    │   ├── state-pattern.md
    │   ├── strategy-pattern.md
    │   └── transaction-script-pattern.md
    │
    ├── devops/                        # DevOps tooling
    │   ├── ci-cd/                     # CI/CD (Azure DevOps, GitHub Actions, Jenkins)
    │   ├── containerd.md
    │   ├── docker/                    # Docker and Docker Compose
    │   ├── kubernetes/                # Kubernetes with deployment tools, ingress, etc.
    │   └── terminal/                  # Shell scripting (Bash, PowerShell)
    │
    ├── domain-driven-design/          # DDD topics
    │   ├── aggregation.md
    │   ├── anemic-domain-model.md
    │   ├── application-service.md
    │   ├── bounded-context.md
    │   ├── domain.md
    │   ├── domain-driven-design.md
    │   ├── domain-events.md
    │   ├── domain-primitives.md       # Primitive obsession / value types
    │   ├── domain-service.md
    │   ├── enums.md
    │   ├── event-sourcing.md
    │   ├── exception-and-validation.md
    │   ├── infrastructure.md
    │   ├── integration-event.md
    │   ├── mapping.md
    │   ├── orm/                       # ORM resources (Entity Framework)
    │   ├── rich-domain-model.md
    │   ├── strategic-design-patterns.md
    │   ├── tactical-design-patterns.md
    │   └── value-objects.md
    │
    ├── iaas/                          # Infrastructure as a Service
    │   ├── ansible.md
    │   ├── iaas.md
    │   ├── nomad.md
    │   ├── pulumi.md
    │   └── terraform.md
    │
    ├── messaging/                     # Messaging systems and patterns
    │   ├── async-api-documentation.md
    │   ├── change-data-capture.md     # CDC
    │   ├── kafka.md
    │   ├── messaging.md
    │   ├── messaging-patterns.md
    │   ├── nats.md
    │   ├── rabbitmq.md
    │   └── zeromq.md
    │
    ├── microservices/                 # Microservices topics
    │   ├── api-gateway/
    │   ├── communication.md
    │   ├── composite-ui.md
    │   ├── microservices.md
    │   ├── observability/             # Logging, tracing, monitoring, ELK/EFK, Loki
    │   ├── resiliency/                # High availability, idempotency
    │   ├── security/
    │   ├── services-boundries.md
    │   ├── testing.md
    │   └── tools/                     # CAP, Dapr, Wolverine, MassTransit, Aspire, etc.
    │
    ├── modeling/                      # Software modeling techniques
    │   ├── architecture-diagram.md
    │   ├── class-diagram.md
    │   ├── component-diagram.md
    │   ├── domain-stroytelling.md     # Domain Storytelling
    │   ├── er-diagrams.md
    │   ├── event-modeling.md
    │   ├── event-storming.md
    │   ├── modeling.md
    │   └── tools.md
    │
    ├── paas/                          # Platform as a Service
    │   ├── heroku.md
    │   ├── netlify.md
    │   ├── openshift.md
    │   └── rancher.md
    │
    ├── reverse-proxy-lb/              # Reverse proxy and load balancing
    │   ├── envoy.md
    │   ├── haproxy.md
    │   ├── load-balancing.md
    │   ├── nginx.md
    │   ├── reverse-proxy.md
    │   ├── traefik.md
    │   └── yarp.md                    # YARP (.NET reverse proxy)
    │
    ├── service-discovery/             # Service discovery tools
    │   ├── consul.md
    │   ├── eureka.md
    │   └── service-discovery.md
    │
    ├── service-mesh/                  # Service mesh
    │   ├── istio.md
    │   ├── linkerd.md
    │   ├── maesh.md
    │   └── service-mesh.md
    │
    └── systems-design/                # Systems design
        ├── consistent-hash.md
        └── systems-design.md
```

## Module and Package Organization

The repository has no runtime modules or packages in the traditional sense. Its organization follows a **topic-per-file, category-per-directory** convention:

- **Flat files** for top-level topics (e.g., `docs/cqrs.md`, `docs/refactoring.md`).
- **Subdirectories** for multi-document topic areas (e.g., `docs/domain-driven-design/`, `docs/microservices/`, `docs/ai/`).
- **Nested subdirectories** for second-level groupings within a topic (e.g., `docs/microservices/tools/`, `docs/ai/models/`, `docs/azure/messaging/`).

## Key Files and Their Roles

| File | Role |
|------|------|
| `mkdocs.yml` | Authoritative navigation tree; every docs file must be registered here |
| `README.md` | GitHub-facing version of the index, with the same structure as mkdocs nav |
| `contributing.md` | Formatting rules and PR workflow for contributors |
| `Program.cs` | Release notes generator; parses git diff to extract added/removed markdown list items |
| `ReleaseNotes.csproj` | .NET 9 project configuration for the release notes tool |
| `.github/workflows/ci.yml` | Two-job CI: link validation + MkDocs deployment |
| `docs/README.md` | The MkDocs home page content |

## Code Organization Patterns

1. **One topic = one markdown file**: Every concept (e.g., CQRS, Circuit Breaker, Kafka) gets its own `.md` file. This keeps content isolated and makes contributions via PR straightforward.
2. **Sections within each file**: Each topic file uses consistent section headers: `## 📘 Resources`, `## 📕 Articles`, `## 📺 Videos`, `## 📦 Libraries` (varies by topic).
3. **mkdocs.yml as registry**: `mkdocs.yml` is the canonical registry. Adding a new topic requires both creating `docs/<topic>.md` and adding it to `mkdocs.yml`'s `nav` section.
4. **Hyphenated filenames**: All doc files use lowercase kebab-case filenames mirroring the topic name (e.g., `clean-architecture.md`, `event-driven-architecture.md`).
5. **Self-contained directories for complex topics**: Topics with 5+ subtopics get a dedicated subdirectory (e.g., `docs/microservices/`, `docs/devops/`, `docs/domain-driven-design/`).
