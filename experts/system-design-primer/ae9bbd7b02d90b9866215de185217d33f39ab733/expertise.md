### System Design Fundamentals
- Performance vs. scalability — definition, distinction, diagnostic questions
- Latency vs. throughput — maximizing throughput with acceptable latency
- Availability vs. consistency — fundamental tension in distributed systems
- CAP theorem — CP vs. AP trade-offs, examples of each (HBase, Cassandra, etc.)
- PACELC theorem context — extensions to CAP for latency considerations
- Consistency patterns — weak consistency, eventual consistency, strong consistency with real-world examples
- Availability patterns — fail-over (active-passive, active-active), replication
- Availability in numbers — 99.9% (three nines), 99.99% (four nines) downtime calculations
- Sequential vs. parallel availability math — `Availability(Total) = A * B` vs. `1 - (1-A)*(1-B)`

### Networking and Infrastructure
- DNS architecture — NS records, MX records, A records, CNAME, TTL, latency implications
- DNS routing policies — weighted round robin, latency-based, geolocation-based
- Content delivery networks — push CDN vs. pull CDN, when to use each
- Load balancers — Layer 4 vs. Layer 7, active-passive vs. active-active, horizontal scaling
- Load balancing algorithms — random, least loaded, round robin, weighted round robin, session/cookies
- Reverse proxies — distinction from load balancers, NGINX/HAProxy usage
- SSL termination — offloading from backend servers

### Application Architecture
- Application layer separation from web layer
- Microservices — characteristics, trade-offs, scalability benefits
- Service discovery — Consul, Etcd, Zookeeper patterns and health checks
- Single responsibility principle in service design
- Asynchronism — message queues vs. task queues, back pressure mechanisms

### Database Design
- RDBMS fundamentals — ACID properties (Atomicity, Consistency, Isolation, Durability)
- Master-slave replication — read scaling, failover procedure, replication lag
- Master-master replication — write scaling, conflict resolution, consistency trade-offs
- Database federation — functional partitioning, cross-database join limitations
- Database sharding — horizontal partitioning strategies, hotspot risk, re-sharding complexity
- Denormalization — write complexity vs. read performance trade-off
- SQL tuning — indexing strategies, query optimization

### NoSQL Databases
- Key-value stores — Redis, Memcached use cases and limitations
- Document stores — MongoDB, CouchDB, DynamoDB patterns
- Wide column stores — Cassandra, HBase, BigTable architecture
- Graph databases — use cases for highly connected data
- SQL vs. NoSQL decision framework — when each is appropriate

### Caching
- Cache placement strategies — client caching, CDN caching, web server caching, database caching, application caching
- Query-level vs. object-level caching approaches
- Cache-aside (lazy loading) — read pattern, cache invalidation on write
- Write-through — synchronous cache+DB write, no stale data risk
- Write-behind (write-back) — async DB write, data loss risk, high write performance
- Refresh-ahead — proactive refresh before TTL expiry
- Cache eviction policies — LRU (Least Recently Used), LFU, FIFO
- LRU cache implementation — hash map + doubly linked list, O(1) get/set

### Communication Protocols
- TCP — connection-oriented, reliable delivery, flow control, use cases
- UDP — connectionless, fast but unreliable, use cases (video streaming, VoIP, DNS)
- RPC (Remote Procedure Call) — Protobuf, Thrift, stub generation
- REST — stateless, HTTP verbs, resource-based, cacheable
- REST vs. RPC — comparison and appropriate use cases

### Security Basics
- Encryption in transit and at rest
- Principle of least privilege
- SQL injection, XSS, CSRF awareness
- HTTPS, SSL/TLS termination

### Worked System Design Solutions
- **Pastebin.com / Bit.ly** (`solutions/system_design/pastebin/README.md`) — URL shortening, hash generation, read-heavy optimization, analytics with MapReduce
- **Twitter timeline and search** (`solutions/system_design/twitter/README.md`) — fan-out, timeline generation, search indexing, celebrity user problem
- **Web crawler** (`solutions/system_design/web_crawler/README.md`) — BFS/DFS strategies, deduplication, politeness, distributed crawling
- **Mint.com** (`solutions/system_design/mint/README.md`) — financial aggregation, bank API integration, transaction categorization
- **Social graph** (`solutions/system_design/social_graph/README.md`) — graph data structures, BFS for degree-of-separation, sharding by user ID
- **Query cache / Key-value store** (`solutions/system_design/query_cache/README.md`) — search engine caching, consistent hashing, cache eviction
- **Amazon sales ranking** (`solutions/system_design/sales_rank/README.md`) — time-series data, MapReduce, category hierarchies
- **Scaling on AWS** (`solutions/system_design/scaling_aws/README.md`) — single-server to millions of users progression, AWS-specific services

### Object-Oriented Design Solutions
- **LRU Cache** (`solutions/object_oriented_design/lru_cache/`) — Node, LinkedList, Cache classes; O(1) get/set implementation
- **Call Center** (`solutions/object_oriented_design/call_center/`) — Employee (abstract), Operator, Supervisor, Director, Call, CallCenter; escalation pattern
- **Hash Map** (`solutions/object_oriented_design/hash_table/`) — hash function design, collision resolution (chaining vs. open addressing)
- **Deck of Cards** (`solutions/object_oriented_design/deck_of_cards/`) — Suit, Rank, Card, Deck, Hand class hierarchy
- **Parking Lot** (`solutions/object_oriented_design/parking_lot/`) — VehicleSize, Vehicle, ParkingLot, ParkingSpot hierarchy
- **Online Chat** (`solutions/object_oriented_design/online_chat/`) — User, PrivateChat, GroupChat, Message, UserManager

### Interview Preparation
- Four-step interview methodology — use cases, high-level design, core components, scale
- Study guide by timeline — short (breadth), medium (breadth + some depth), long (breadth + more depth)
- Back-of-envelope calculations — storage estimates, QPS estimates, bandwidth estimates
- Powers of two table — data size reference for capacity planning
- Latency numbers every programmer should know — L1 cache through cross-continent round trip
- How to approach an open-ended system design interview

### Reference Material
- Real-world architectures — MapReduce, Spark, Storm, Bigtable, HBase, Cassandra, DynamoDB, MongoDB, Spanner, Memcached, Redis, GFS, HDFS, Chubby, Dapper, Kafka, Zookeeper
- Company architecture case studies — Amazon, Facebook, Google, Netflix, Twitter, Uber, Instagram, Pinterest, YouTube, WhatsApp, Dropbox, Stack Overflow
- Company engineering blog directory — 30+ major tech company engineering blogs

### Repository Mechanics
- ePub generation via `generate-epub.sh` and pandoc
- Translation workflow and `TRANSLATIONS.md` structure
- Contribution guidelines from `CONTRIBUTING.md`
- Anki flashcard deck structure (`.apkg` files)
- mrjob MapReduce framework usage in `pastebin.py`
- Jupyter Notebook vs. `.py` dual artifact pattern in OOD solutions
- OmniGraffle `.graffle` source files for architecture diagrams
