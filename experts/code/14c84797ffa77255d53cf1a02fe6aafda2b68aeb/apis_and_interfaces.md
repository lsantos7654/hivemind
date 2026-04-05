# APIs and Interfaces: Architecture Patterns with Python (cosmicpython/code)

## Public APIs and Entry Points

### HTTP REST API (`src/allocation/entrypoints/flask_app.py`)

Three HTTP endpoints are exposed by the Flask application:

#### `POST /add_batch`
Creates a new stock batch for a product SKU.

**Request body** (JSON):
```json
{
  "ref": "batch-001",
  "sku": "SMALL-TABLE",
  "qty": 100,
  "eta": "2023-06-15"   // or null for in-stock batches
}
```

**Response**: `"OK"` with HTTP 201 Created.

**Internal flow**: Builds a `CreateBatch` command → `bus.handle(cmd)`

#### `POST /allocate`
Allocates a quantity of a SKU to an order.

**Request body** (JSON):
```json
{
  "orderid": "order-001",
  "sku": "SMALL-TABLE",
  "qty": 3
}
```

**Responses**:
- `"OK"` with HTTP 202 Accepted (success)
- `{"message": "Invalid sku SMALL-TABLE"}` with HTTP 400 (invalid SKU)

**Internal flow**: Builds an `Allocate` command → `bus.handle(cmd)` → raises `InvalidSku` on bad SKU.

#### `GET /allocations/<orderid>`
Fetches all current allocations for an order (CQRS read model).

**Response** (JSON array):
```json
[
  {"sku": "SMALL-TABLE", "batchref": "batch-001"},
  {"sku": "BLUE-CHAIR", "batchref": "batch-005"}
]
```

- Returns HTTP 404 if no allocations found.
- Queries the `allocations_view` denormalized table via `views.allocations()`.

---

### Redis Event Consumer (`src/allocation/entrypoints/redis_eventconsumer.py`)

Subscribes to the `change_batch_quantity` Redis pub/sub channel. Messages must be JSON with:

```json
{
  "batchref": "batch-001",
  "qty": 50
}
```

Internally dispatches a `ChangeBatchQuantity` command to the message bus.

---

## Key Classes and Functions

### Domain Layer

#### `Product` (`src/allocation/domain/model.py:8`)

The aggregate root. Groups a set of `Batch` objects for a given SKU.

```python
class Product:
    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0):
        ...
    
    def allocate(self, line: OrderLine) -> str:
        """
        Allocates an OrderLine to the earliest available Batch.
        Appends Allocated or OutOfStock event to self.events.
        Returns the batch reference string, or None if out of stock.
        """
    
    def change_batch_quantity(self, ref: str, qty: int):
        """
        Updates a batch's purchased quantity.
        If the batch is over-allocated, deallocates lines and appends
        Deallocated events to self.events for each line removed.
        """
```

#### `Batch` (`src/allocation/domain/model.py:48`)

A stock batch with a reference, SKU, purchased quantity, and optional ETA.

```python
class Batch:
    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date]):
        ...
    
    @property
    def available_quantity(self) -> int:
        """purchased_quantity minus sum of allocated line quantities"""
    
    @property
    def allocated_quantity(self) -> int:
        """sum of allocated line quantities"""
    
    def can_allocate(self, line: OrderLine) -> bool:
        """True if SKU matches and available_quantity >= line.qty"""
    
    def allocate(self, line: OrderLine):
        """Adds line to _allocations if can_allocate"""
    
    def deallocate_one(self) -> OrderLine:
        """Pops and returns one allocation (used during batch qty reduction)"""
```

Batches are sorted by ETA: `None` (in-stock) sorts before dated batches.

#### `OrderLine` (`src/allocation/domain/model.py:41`)

Immutable value object:
```python
@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int
```

---

### Commands (`src/allocation/domain/commands.py`)

All commands are frozen dataclasses inheriting from `Command`:

```python
@dataclass
class Allocate(Command):
    orderid: str
    sku: str
    qty: int

@dataclass
class CreateBatch(Command):
    ref: str
    sku: str
    qty: int
    eta: Optional[date] = None

@dataclass
class ChangeBatchQuantity(Command):
    ref: str
    qty: int
```

---

### Events (`src/allocation/domain/events.py`)

All events are dataclasses inheriting from `Event`:

```python
@dataclass
class Allocated(Event):
    orderid: str
    sku: str
    qty: int
    batchref: str

@dataclass
class Deallocated(Event):
    orderid: str
    sku: str
    qty: int

@dataclass
class OutOfStock(Event):
    sku: str
```

---

### MessageBus (`src/allocation/service_layer/messagebus.py:15`)

```python
class MessageBus:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        event_handlers: Dict[Type[Event], List[Callable]],
        command_handlers: Dict[Type[Command], Callable],
    ): ...

    def handle(self, message: Message):
        """
        Dispatches a Message (Command or Event). Internally maintains a queue.
        After each handler, collects new events from the UoW and enqueues them.
        Events: each handler runs independently (exceptions are caught and logged).
        Commands: single handler; exceptions propagate.
        """
```

---

### Service Layer Handlers (`src/allocation/service_layer/handlers.py`)

Pure functions, all taking a command/event plus injected dependencies:

```python
def add_batch(cmd: commands.CreateBatch, uow: AbstractUnitOfWork): ...
def allocate(cmd: commands.Allocate, uow: AbstractUnitOfWork): ...
def reallocate(event: events.Deallocated, uow: AbstractUnitOfWork): ...
def change_batch_quantity(cmd: commands.ChangeBatchQuantity, uow: AbstractUnitOfWork): ...
def send_out_of_stock_notification(event: events.OutOfStock, notifications: AbstractNotifications): ...
def publish_allocated_event(event: events.Allocated, publish: Callable): ...
def add_allocation_to_read_model(event: events.Allocated, uow: SqlAlchemyUnitOfWork): ...
def remove_allocation_from_read_model(event: events.Deallocated, uow: SqlAlchemyUnitOfWork): ...
```

Handler registries (used by `bootstrap()` to wire the `MessageBus`):

```python
EVENT_HANDLERS = {
    events.Allocated: [publish_allocated_event, add_allocation_to_read_model],
    events.Deallocated: [remove_allocation_from_read_model, reallocate],
    events.OutOfStock: [send_out_of_stock_notification],
}

COMMAND_HANDLERS = {
    commands.Allocate: allocate,
    commands.CreateBatch: add_batch,
    commands.ChangeBatchQuantity: change_batch_quantity,
}
```

---

### Unit of Work (`src/allocation/service_layer/unit_of_work.py`)

```python
class AbstractUnitOfWork(abc.ABC):
    products: AbstractRepository   # Set by subclass in __enter__

    def __enter__(self) -> AbstractUnitOfWork: ...
    def __exit__(self, *args): ...    # calls rollback()
    def commit(self): ...             # calls _commit()
    def collect_new_events(self):     # yields events from seen products

    @abc.abstractmethod
    def _commit(self): ...
    @abc.abstractmethod
    def rollback(self): ...

class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY): ...
    # DEFAULT_SESSION_FACTORY connects to Postgres with REPEATABLE READ isolation
```

Usage pattern:
```python
with uow:
    product = uow.products.get(sku=cmd.sku)
    product.allocate(line)
    uow.commit()
```

---

### Repository (`src/allocation/adapters/repository.py`)

```python
class AbstractRepository(abc.ABC):
    seen: Set[Product]   # Tracks all products touched in this session

    def add(self, product: Product): ...
    def get(self, sku) -> Product: ...
    def get_by_batchref(self, batchref) -> Product: ...

    # Abstract methods for subclasses:
    def _add(self, product): ...
    def _get(self, sku) -> Product: ...
    def _get_by_batchref(self, batchref) -> Product: ...

class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session): ...
```

---

### Bootstrap (`src/allocation/bootstrap.py`)

```python
def bootstrap(
    start_orm: bool = True,
    uow: AbstractUnitOfWork = SqlAlchemyUnitOfWork(),
    notifications: AbstractNotifications = None,
    publish: Callable = redis_eventpublisher.publish,
) -> MessageBus:
    """
    Composition root. Call once at application startup.
    Returns a fully wired MessageBus with all handlers injected.
    
    For tests: pass start_orm=False, uow=FakeUnitOfWork(), 
               notifications=FakeNotifications(), publish=lambda *args: None
    """
```

---

### Views (`src/allocation/views.py`)

```python
def allocations(orderid: str, uow: SqlAlchemyUnitOfWork) -> List[dict]:
    """
    Returns a list of dicts with 'sku' and 'batchref' for the given order.
    Queries the read-model table 'allocations_view' directly (CQRS read side).
    Returns [] if no allocations found.
    """
```

---

## Usage Examples with Code Snippets

### Bootstrapping the Application

```python
from allocation import bootstrap

# Production (called at module level in flask_app.py)
bus = bootstrap.bootstrap()

# In tests
bus = bootstrap.bootstrap(
    start_orm=False,
    uow=FakeUnitOfWork(),
    notifications=FakeNotifications(),
    publish=lambda *args: None,
)
```

### Sending Commands via the Message Bus

```python
from allocation.domain import commands

# Create a new batch
bus.handle(commands.CreateBatch(ref="batch-001", sku="SMALL-TABLE", qty=100, eta=None))

# Allocate an order line
bus.handle(commands.Allocate(orderid="order-001", sku="SMALL-TABLE", qty=3))

# Change a batch's quantity (triggers reallocation if needed)
bus.handle(commands.ChangeBatchQuantity(ref="batch-001", qty=50))
```

### Reading Allocations (CQRS Read Side)

```python
from allocation import views

result = views.allocations("order-001", bus.uow)
# Returns: [{"sku": "SMALL-TABLE", "batchref": "batch-001"}]
```

### Using the Unit of Work Directly

```python
with uow:
    product = uow.products.get(sku="SMALL-TABLE")
    if product is None:
        product = model.Product("SMALL-TABLE", batches=[])
        uow.products.add(product)
    product.batches.append(model.Batch("batch-001", "SMALL-TABLE", 100, None))
    uow.commit()
```

### Implementing a Fake Adapter for Testing

```python
class FakeRepository(repository.AbstractRepository):
    def __init__(self, products):
        super().__init__()
        self._products = set(products)

    def _add(self, product):
        self._products.add(product)

    def _get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)

    def _get_by_batchref(self, batchref):
        return next(
            (p for p in self._products for b in p.batches if b.reference == batchref),
            None,
        )

class FakeUnitOfWork(unit_of_work.AbstractUnitOfWork):
    def __init__(self):
        self.products = FakeRepository([])
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass
```

---

## Integration Patterns and Workflows

### Full Allocation Flow

1. HTTP `POST /allocate` → Flask creates `Allocate` command → `bus.handle(cmd)`
2. `MessageBus.handle_command` → calls `allocate(cmd, uow=...)`
3. `allocate()` opens UoW, loads `Product`, calls `product.allocate(line)`
4. `Product.allocate()` appends `Allocated` or `OutOfStock` to `product.events`
5. `uow.commit()` persists the allocation
6. `bus.collect_new_events()` harvests `Allocated` event from the UoW
7. `MessageBus` processes `Allocated`: calls `publish_allocated_event` and `add_allocation_to_read_model`
8. `publish_allocated_event` publishes JSON to Redis `line_allocated` channel
9. `add_allocation_to_read_model` inserts row into `allocations_view` table

### Batch Quantity Change and Reallocation

1. External system publishes to Redis `change_batch_quantity` channel
2. `redis_eventconsumer` receives message, dispatches `ChangeBatchQuantity` command
3. Handler reduces batch quantity; if over-allocated, emits `Deallocated` events
4. `MessageBus` processes `Deallocated`: calls `remove_allocation_from_read_model` then `reallocate`
5. `reallocate` converts the `Deallocated` event back into an `Allocate` command
6. `MessageBus` processes the new `Allocate` command, finding the next available batch

---

## Configuration Options and Extension Points

### Environment-Based Configuration (`src/allocation/config.py`)

All infrastructure addresses are read from environment variables with sensible local defaults:
- `DB_HOST`, `DB_PASSWORD` → PostgreSQL connection
- `REDIS_HOST` → Redis connection
- `EMAIL_HOST` → SMTP server
- `API_HOST` → API URL (used by e2e tests)

### Extending the Message Bus

To add a new event or command:

1. Add a dataclass to `domain/events.py` or `domain/commands.py`
2. Write a handler function in `service_layer/handlers.py`
3. Register it in `EVENT_HANDLERS` or `COMMAND_HANDLERS`
4. No changes needed to `MessageBus` or `bootstrap()` — they pick up the registry automatically

### Custom Notifications

Implement `AbstractNotifications.send(destination, message)`:
```python
class SlackNotifications(AbstractNotifications):
    def send(self, destination, message):
        ...  # post to Slack channel

bus = bootstrap.bootstrap(notifications=SlackNotifications())
```

### Custom Repository

Implement `AbstractRepository._add`, `_get`, `_get_by_batchref`:
```python
class InMemoryRepository(AbstractRepository):
    ...
```

### Custom Unit of Work

Implement `AbstractUnitOfWork._commit` and `rollback`:
```python
class MongoUnitOfWork(AbstractUnitOfWork):
    ...
```
