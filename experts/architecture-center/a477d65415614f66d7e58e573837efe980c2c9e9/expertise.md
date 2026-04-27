### Cloud Design Patterns (docs/patterns/)
- Full catalog of 40+ cloud design patterns and their WAF pillar mappings
- Ambassador pattern — helper service for network requests on behalf of consumers
- Anti-Corruption Layer — façade between modern and legacy systems
- Asynchronous Request-Reply — decoupling back-end processing from front-end
- Backends for Frontends — separate backends per frontend interface
- Bulkhead — isolation pools to contain failures
- Cache-Aside — demand-load data from data store into cache
- Choreography — decentralized service coordination without central orchestrator
- Circuit Breaker — fault handling for variable-time recoveries
- Claim Check — split large messages to avoid overwhelming message bus
- Compensating Transaction — undo steps in eventually consistent operations
- Competing Consumers — multiple consumers on single messaging channel
- Compute Resource Consolidation — merge tasks into single computational unit
- CQRS — separate read and write interfaces
- Deployment Stamps — independent copies of application components
- Edge Workload Configuration — configuration for edge deployments
- Event Sourcing — append-only store of full event history
- External Configuration Store — centralized configuration management
- Federated Identity — delegate authentication to external identity providers
- Gateway Aggregation — aggregate multiple requests into one via gateway
- Gateway Offloading — offload shared functionality to gateway proxy
- Gateway Routing — route to multiple services via single endpoint
- Geode — geographically distributed back-end nodes
- Health Endpoint Monitoring — functional checks via exposed endpoints
- Index Table — secondary indexes over data store fields
- Leader Election — elect one instance to coordinate distributed actions
- Materialized View — prepopulated views over poorly formatted data
- Messaging Bridge — intermediary between incompatible messaging systems
- Pipes and Filters — decompose complex processing into reusable elements
- Priority Queue — prioritize requests for faster high-priority processing
- Publisher-Subscriber — announce events to multiple consumers asynchronously
- Quarantine — ensure external assets meet quality standards before consumption
- Queue-Based Load Leveling — queue buffer between task and service
- Rate Limiting — control resource consumption to minimize throttling errors
- Retry — handle temporary failures by retrying failed operations
- Saga — manage data consistency across microservices in distributed transactions
- Scheduler Agent Supervisor — coordinate actions across distributed services
- Sequential Convoy — process related messages in order without blocking other groups
- Sharding — divide data store into horizontal partitions
- Sidecar — deploy components in separate process/container for isolation
- Static Content Hosting — deploy static content to cloud storage for direct delivery
- Strangler Fig — incrementally migrate legacy systems
- Throttling — control consumption of resources across tenants/services
- Valet Key — restricted direct client access to specific resources

### Architecture Styles (docs/guide/architecture-styles/)
- N-tier architecture — layered enterprise applications
- Web-Queue-Worker — web front end + message queue + background worker
- Microservices — autonomous service decomposition
- Event-driven architecture — event producer/consumer decoupling
- Big data / Lambda architecture — batch + speed + serving layers
- Big compute / HPC — massively parallel computational workloads
- CQRS-based architecture styles

### Application Architecture Fundamentals (docs/guide/)
- Design principles: build for business, design for self-healing, scale out, design for evolution, design for operations, use managed services, use the best data store, minimize coordination, partition around limits, redundancy
- Technology choices: compute decision tree, data store models, messaging options, storage options, hybrid considerations
- Architecture patterns for AKS, multi-tenant applications, SaaS, startups, responsible innovation
- Azure landing zones and cloud adoption strategy

### Best Practices (docs/best-practices/)
- API design — platform independence, resource-based REST, partial responses, filtering, pagination
- API implementation — idempotency, content negotiation, HTTP compliance, exception handling, large requests
- Autoscaling — dynamic resource allocation, Azure Monitor autoscale, service-level autoscaling
- Background jobs — batch processing, Azure platform services, event/schedule triggers
- Caching — demand-load patterns, Azure Managed Redis, expiration, concurrency, cache population
- Content Delivery Networks — CDN deployment, versioning, security, resilience
- Data partitioning — horizontal, vertical, functional partitioning; scalability and cost reduction
- Data partitioning by service — Azure SQL Database, Cosmos DB, Blob Storage, Redis, Service Bus
- Host name preservation — reverse proxy to back-end host name preservation
- Message encoding — payload structure, encoding formats, serialization, schema evolution
- Monitoring and diagnostics — telemetry pipeline, alerts, reports, performance SLA compliance
- Transient fault handling — retry strategies, backoff policies, circuit breakers, anti-patterns

### Performance Antipatterns (docs/antipatterns/)
- Busy Database — offloading too much processing to the data store
- Busy Front End — resource-intensive tasks blocking the front-end thread
- Chatty I/O — many small network requests instead of batched requests
- Extraneous Fetching — retrieving more data than needed
- Improper Instantiation — repeatedly creating shared/reusable objects
- Monolithic Persistence — using one data store for all data regardless of access patterns
- No Caching — failure to cache frequently accessed, rarely changing data
- Noisy Neighbor — single tenant consuming disproportionate shared resources
- Retry Storm — excessive retries overwhelming a recovering service
- Synchronous I/O — blocking calling thread during I/O completion

### Microservices Design (docs/microservices/)
- Compute options — AKS vs Azure Container Apps vs Azure Functions trade-offs
- Interservice communication — synchronous REST vs asynchronous messaging, service mesh
- API design for microservices — versioning, loose coupling, independent evolution
- API gateways — Azure API Management, Application Gateway, cross-cutting concerns
- Data considerations — distributed data consistency, distributed transactions, polyglot persistence
- Container orchestration — Kubernetes fundamentals, AKS deployment, health management
- CI/CD for microservices — pipeline design, independent service deployment
- Domain modeling — domain-driven design, bounded contexts, microservice boundary identification
- Design patterns for microservices — Saga, Bulkhead, Strangler Fig in microservice context

### Data Architecture Guide (docs/data-guide/)
- Relational data patterns — OLTP, OLAP, data warehousing
- Analytical data stores — selection criteria, trade-offs
- Batch processing architectures — Azure Data Factory, Databricks, Synapse
- Stream processing architectures — Event Hubs, Stream Analytics, real-time processing
- Lambda and Kappa architecture patterns
- AI services technology selection — cognitive services, custom ML, Azure AI
- Natural language processing architectures
- Disaster recovery for data platforms

### AI and Machine Learning Architecture (docs/ai-ml/)
- Multi-agent orchestration patterns — sequential, concurrent, group chat, handoff, magentic
- Complexity levels — direct model call vs single agent with tools vs multi-agent orchestration
- RAG (Retrieval-Augmented Generation) architectures
- Azure OpenAI gateway patterns — custom authentication, monitoring, multi-backend routing
- MLOps and GenAIOps — maturity models, operations pipelines
- Foundation model lifecycle management
- Machine learning operations (MLOps v2)
- AI/ML workload architectures on Azure

### Reference Architectures (docs/reference-architectures/)
- N-tier VM architectures — Linux and Windows VMs with load balancing
- Microservices on AKS — production-grade Kubernetes deployments
- Hub-spoke networking — Virtual WAN, ExpressRoute, VPN topologies
- Network DMZ architectures — perimeter network security
- Identity architectures — federation, Azure AD B2C, hybrid identity
- SAP on Azure — HANA, S/4HANA, NetWeaver deployments
- IBM workloads on Azure — mainframe migration
- Enterprise integration — Logic Apps, Service Bus, API Management patterns
- Event Hubs streaming — high-throughput event ingestion architectures
- Data pipeline reference architectures

### Example Scenarios and Solution Ideas (docs/example-scenario/, docs/solution-ideas/)
- AI-powered scenarios — AI search, conversational data insights
- Analytics scenarios — Databricks, modern analytics platform
- AKS scenarios — AGIC ingress, Front Door, GitOps
- DevOps and DevSecOps scenarios
- Hybrid and mainframe migration scenarios
- IoT and manufacturing scenarios
- Security and identity scenarios
- Serverless and quantum computing scenarios

### Multi-Cloud Guidance
- Azure for AWS professionals (docs/aws-professional/) — compute, storage, networking, databases, messaging, security, identity mapping tables; EKS to AKS migration
- Azure for GCP professionals (docs/gcp-professional/) — service-to-service mapping

### Content Authoring Schema
- Standard Markdown article format with required YAML frontmatter fields
- YamlMime:Architecture split-file format (`.yml` wrapper + `-content.md` body)
- DocFX `docfx.json` configuration — content sources, exclusions, global metadata, file metadata overrides
- `ms.topic` values: `concept-article`, `design-pattern`, `best-practice`
- `ms.subservice` taxonomy: `cloud-fundamentals`, `architecture-guide`, `best-practice`
- `azureCategories` and `products` tags for browse catalog filtering
- `toc.yml` navigation structure and hierarchical TOC composition
- URL redirect management via `.openpublishing.redirection.json`
- cspell spell-checking configuration
- `ms.update-cycle` metadata values — 180-days (AI), 365-days (default), 1095-days (stable content)
- Browse catalog thumbnail conventions (`docs/browse/thumbs/`)
- Internal cross-reference URL patterns (relative vs absolute)
- DocFX image syntax with accessibility alt text and lightbox support
