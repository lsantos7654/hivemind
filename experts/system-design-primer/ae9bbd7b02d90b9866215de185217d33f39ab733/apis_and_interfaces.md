# System Design Primer — APIs and Interfaces

## Overview

The System Design Primer is an educational repository, not a software library with a public API. Its "interfaces" are:
1. The knowledge base in `README.md` and its translations
2. Python class interfaces demonstrated in OOD solutions
3. The ePub generation shell script interface
4. The solution templates for system design problems

---

## System Design Methodology Interface

The core reusable framework in this repository is a four-step interview methodology applicable to any system design question.

### The Four-Step Design Process

**Step 1 — Outline use cases, constraints, and assumptions**

Questions to ask:
- Who will use it?
- How will they use it?
- How many users?
- What does the system do?
- What are the inputs and outputs?
- How much data?
- Requests per second?
- Read-to-write ratio?

**Step 2 — Create a high-level design**

- Sketch main components and connections
- Justify architectural choices

**Step 3 — Design core components**

Dive into details for each component. Example for URL shortener:
- Generating and storing a hash (MD5, Base62, hash collision handling)
- SQL vs. NoSQL decision with justification
- Database schema
- API design

**Step 4 — Scale the design**

Identify bottlenecks and address them:
- Load balancer placement
- Horizontal scaling strategy
- Caching layer (what to cache, eviction policy)
- Database sharding strategy

---

## Python Class Interfaces

### LRU Cache (`solutions/object_oriented_design/lru_cache/lru_cache.py`)

```python
class Node(object):
    def __init__(self, results):
        self.results = results  # Cached value
        self.next = next        # Next node in linked list

class LinkedList(object):
    def __init__(self):
        self.head = None
        self.tail = None

    def move_to_front(self, node): ...
    def append_to_front(self, node): ...
    def remove_from_tail(self): ...

class Cache(object):
    def __init__(self, MAX_SIZE):
        self.MAX_SIZE = MAX_SIZE
        self.size = 0
        self.lookup = {}              # dict: query -> node
        self.linked_list = LinkedList()

    def get(self, query) -> results | None:
        """O(1) cache lookup. Moves accessed node to front of LRU list."""

    def set(self, results, query) -> None:
        """O(1) cache update. Evicts LRU entry when at capacity."""
```

**Usage example:**

```python
cache = Cache(MAX_SIZE=100)
cache.set(results={'data': [1, 2, 3]}, query='SELECT * FROM users WHERE id=1')
result = cache.get('SELECT * FROM users WHERE id=1')  # Returns {'data': [1, 2, 3]}
result = cache.get('nonexistent query')               # Returns None
```

**Design pattern:** Combines a hash map (O(1) lookup) with a doubly-linked list (O(1) eviction of LRU entry). This is the canonical O(1) LRU cache implementation.

---

### Call Center (`solutions/object_oriented_design/call_center/call_center.py`)

```python
from enum import Enum
from collections import deque
from abc import ABCMeta, abstractmethod

class Rank(Enum):
    OPERATOR = 0
    SUPERVISOR = 1
    DIRECTOR = 2

class CallState(Enum):
    READY = 0
    IN_PROGRESS = 1
    COMPLETE = 2

class Employee(metaclass=ABCMeta):
    def __init__(self, employee_id, name, rank, call_center): ...
    def take_call(self, call) -> None: ...     # Sets call state to IN_PROGRESS
    def complete_call(self) -> None: ...       # Sets call state to COMPLETE, notifies center
    @abstractmethod
    def escalate_call(self) -> None: ...       # Subclass must implement

class Operator(Employee):
    def escalate_call(self) -> None: ...       # Escalates to SUPERVISOR rank

class Supervisor(Employee):
    def escalate_call(self) -> None: ...       # Escalates to DIRECTOR rank

class Director(Employee):
    def escalate_call(self) -> None: ...       # Raises NotImplementedError

class Call(object):
    def __init__(self, rank: Rank):
        self.state = CallState.READY
        self.rank = rank
        self.employee = None

class CallCenter(object):
    def __init__(self, operators, supervisors, directors):
        self.operators = operators
        self.supervisors = supervisors
        self.directors = directors
        self.queued_calls = deque()

    def dispatch_call(self, call: Call) -> None:
        """Routes call to lowest available employee of appropriate rank.
        Queues call if no employee is available."""

    def notify_call_escalated(self, call: Call) -> None: ...
    def notify_call_completed(self, call: Call) -> None: ...
    def dispatch_queued_call_to_newly_freed_employee(self, call, employee) -> None: ...
```

**Usage example:**

```python
operators = [Operator('op1', 'Alice'), Operator('op2', 'Bob')]
supervisors = [Supervisor('sup1', 'Carol')]
directors = [Director('dir1', 'Dave')]
center = CallCenter(operators, supervisors, directors)

call = Call(rank=Rank.OPERATOR)
center.dispatch_call(call)   # Routes to first available operator
```

---

### MapReduce Analytics (`solutions/system_design/pastebin/pastebin.py`)

```python
from mrjob.job import MRJob

class HitCounts(MRJob):
    def extract_url(self, line) -> str:
        """Extract generated URL from log line."""

    def extract_year_month(self, line) -> str:
        """Return 'YYYY-MM' portion of timestamp."""

    def mapper(self, _, line):
        """Emits: ((year_month, url), 1) for each log line."""
        url = self.extract_url(line)
        period = self.extract_year_month(line)
        yield (period, url), 1

    def reducer(self, key, values):
        """Sums counts: ((year_month, url), total_count)"""
        yield key, sum(values)

    def steps(self):
        return [self.mr(mapper=self.mapper, reducer=self.reducer)]

if __name__ == '__main__':
    HitCounts.run()
```

**Usage:**
```bash
python pastebin.py < access_logs.txt
# Output: ("2016-01", "url0"), 142
#         ("2016-01", "url1"), 89
```

---

## System Design Knowledge Interfaces

### CAP Theorem Trade-off Interface

For any distributed system design, choose two of three guarantees:

| Choose | Sacrifice | Example Systems |
|--------|-----------|-----------------|
| CP (Consistency + Partition Tolerance) | Availability | HBase, MongoDB, Redis, ZooKeeper |
| AP (Availability + Partition Tolerance) | Consistency | Cassandra, CouchDB, DynamoDB |
| CA (Consistency + Availability) | Partition Tolerance | Traditional RDBMS (single node) |

### Caching Pattern Interface

Four cache update strategies with distinct trade-offs:

**Cache-aside (lazy loading):**
```
read: check cache → if miss, read DB → populate cache → return
write: write DB → invalidate/update cache
```

**Write-through:**
```
write: write cache → write DB (synchronous)
read: check cache → if hit, return; if miss, read DB → return
```

**Write-behind (write-back):**
```
write: write cache → return (async write to DB later)
risk: data loss if cache fails before DB write
```

**Refresh-ahead:**
```
proactively refresh cache before expiration based on access patterns
```

### Database Scaling Decision Interface

| Problem | Solution | Trade-off |
|---------|----------|-----------|
| Read-heavy load | Master-slave replication | Replication lag; complexity |
| Write-heavy load | Master-master replication | Conflict resolution; eventual consistency |
| Large table, too big for one DB | Sharding | Complex queries across shards; hotspot risk |
| Multiple DB functions | Federation | Cannot join across databases |
| Write performance | Denormalization | Read simplicity at cost of write complexity |
| Flexible schema, massive scale | NoSQL (key-value/document/wide-column/graph) | Eventual consistency; limited query flexibility |

### Availability Calculation Interface

```
# Sequential components (both must work):
Availability(Total) = Availability(A) * Availability(B)
# Example: 99.9% * 99.9% = 99.8%

# Parallel components (either must work):
Availability(Total) = 1 - (1 - Availability(A)) * (1 - Availability(B))
# Example: 1 - (0.001 * 0.001) = 99.9999%
```

### Latency Reference Interface

Key latency numbers for back-of-envelope calculations:

```
L1 cache reference:            0.5 ns
L2 cache reference:            7   ns
Main memory reference:         100 ns
SSD random read (4KB):         150 μs
Sequential SSD read (1MB):     1   ms
Datacenter round trip:         500 μs
Cross-continent round trip:    150 ms
```

---

## Solution Template Interface

New system design solutions follow the template in `solutions/system_design/template/`:

```markdown
# Design [System Name]

## Step 1: Outline use cases and constraints

### Use cases
### Constraints and assumptions
#### State assumptions
#### Calculate usage

## Step 2: Create a high level design

## Step 3: Design core components

## Step 4: Scale the design

## Additional talking points
```

---

## Integration Patterns

### Interview Preparation Workflow

1. Read `README.md` sections on relevant topics
2. Review the study guide matrix to prioritize based on timeline
3. Work through system design solutions in `solutions/system_design/`
4. Practice OOD problems via Jupyter notebooks in `solutions/object_oriented_design/`
5. Reinforce with Anki flashcard decks from `resources/flash_cards/`
6. Study real-world architectures from the curated reference list in README

### ePub Generation Workflow

```bash
# Generate all ePub books
bash generate-epub.sh

# Output files created at repo root:
# README.epub          (English, includes all system_design solutions)
# README-ja.epub       (Japanese)
# README-zh-Hans.epub  (Simplified Chinese)
# README-zh-TW.epub    (Traditional Chinese)
```

### Extension Points

To add a new system design solution:
1. Create `solutions/system_design/<problem_name>/`
2. Add `README.md` following the four-step template
3. Optionally add Python implementation files and architecture diagrams
4. Add a row to the solutions table in the main `README.md`
5. The `generate-epub.sh` will automatically include it (directories are iterated dynamically)

To add a new OOD solution:
1. Create `solutions/object_oriented_design/<problem_name>/`
2. Add `<problem_name>.py` with class implementations
3. Add `<problem_name>.ipynb` Jupyter Notebook
4. Add `__init__.py`
5. Add a row to the OOD solutions table in `README.md`
