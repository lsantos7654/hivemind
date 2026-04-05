# python-patterns — APIs and Interfaces

This repository is a **reference library**, not a framework with a public API. Each pattern file is a self-contained, importable module. The "API" consists of the classes and functions defined in each module, intended to be read, understood, and adapted rather than used as library dependencies.

---

## Creational Patterns

### `patterns/creational/factory.py`

**Key interface:**
```python
class Localizer(Protocol):
    def localize(self, msg: str) -> str: ...

def get_localizer(language: str = "English") -> Localizer
```

**Usage:**
```python
from patterns.creational.factory import get_localizer
e = get_localizer("English")
g = get_localizer("Greek")
print(g.localize("dog"))  # → "σκύλος"
```

Pattern: factory function returns instances matching a `Protocol` without the caller knowing the concrete class.

---

### `patterns/creational/abstract_factory.py`

**Key interface:**
```python
class PetShop:
    def __init__(self, animal_factory: Type[Pet]) -> None
    def buy_pet(self, name: str) -> Pet
```

**Usage:**
```python
from patterns.creational.abstract_factory import PetShop, Cat, Dog
cat_shop = PetShop(Cat)
pet = cat_shop.buy_pet("Lucy")  # → Cat<Lucy>
pet.speak()  # → "meow"
```

Python idiom: passes the *class itself* as the factory (classes are first-class callables).

---

### `patterns/creational/borg.py`

**Key interface:**
```python
class Borg:
    _shared_state: Dict[str, str] = {}
    def __init__(self) -> None  # assigns self.__dict__ = self._shared_state

class YourBorg(Borg):
    def __init__(self, state: str = None) -> None
    def __str__(self) -> str
```

**Usage:**
```python
from patterns.creational.borg import YourBorg
rm1 = YourBorg()
rm2 = YourBorg("Running")
print(rm1)  # → "Running"  (shared state)
print(rm1 is rm2)  # → False (different instances, same state)
```

---

### `patterns/creational/builder.py`

**Key interface:**
```python
class Building:
    def build_floor(self): ...  # abstract
    def build_size(self): ...   # abstract

class House(Building): ...
class Flat(Building): ...
def construct_building(cls) -> Building  # external director function
```

**Usage:**
```python
from patterns.creational.builder import House, construct_building, ComplexHouse
house = House()               # Floor: One | Size: Big
ch = construct_building(ComplexHouse)  # Floor: One | Size: Big and fancy
```

---

### `patterns/creational/lazy_evaluation.py`

**Key interface:**
```python
class lazy_property:
    """Descriptor: computes value once, then caches in instance __dict__."""
    def __init__(self, function: Callable) -> None
    def __get__(self, obj, type_) -> str

def lazy_property2(fn: Callable) -> property  # alternative using @property + hasattr
```

**Usage:**
```python
from patterns.creational.lazy_evaluation import lazy_property, Person

class MyObj:
    @lazy_property
    def expensive(self) -> str:
        return "computed once"

obj = MyObj()
_ = obj.expensive  # computed now, cached in obj.__dict__["expensive"]
```

---

### `patterns/creational/pool.py`

**Key interface:**
```python
class ObjectPool:
    def __init__(self, queue: Queue, auto_get: bool = False) -> None
    def __enter__(self) -> str
    def __exit__(self, Type, value, traceback) -> None
    def __del__(self) -> None
```

**Usage:**
```python
import queue
from patterns.creational.pool import ObjectPool

q = queue.Queue()
q.put("resource")
with ObjectPool(q) as obj:
    print(obj)  # → "resource"
# resource returned to pool after with-block
```

---

### `patterns/creational/prototype.py`

**Key interface:**
```python
class Prototype:
    def __init__(self, value: str = "default", **attrs: Any) -> None
    def clone(self, **attrs: Any) -> "Prototype"  # shallow copy + override

class PrototypeDispatcher:
    def register_object(self, name: str, obj: Prototype) -> None
    def unregister_object(self, name: str) -> None
    def get_objects(self) -> dict[str, Prototype]
```

**Usage:**
```python
from patterns.creational.prototype import Prototype, PrototypeDispatcher
proto = Prototype()
a = proto.clone(value="a-value", category="a")
b = a.clone(value="b-value", is_checked=True)
```

---

## Structural Patterns

### `patterns/structural/adapter.py`

**Key interface:**
```python
class Adapter:
    def __init__(self, obj: T, **adapted_methods: Callable[..., Any]) -> None
    def __getattr__(self, attr: str) -> Any  # passthrough to wrapped obj
    def original_dict(self) -> Dict[str, Any]
```

**Usage:**
```python
from patterns.structural.adapter import Adapter, Dog, Cat
dog = Dog()
adapted = Adapter(dog, make_noise=dog.bark)
print(adapted.make_noise())  # → "woof!"
print(adapted.name)          # → "Dog" (via __getattr__ passthrough)
```

---

### `patterns/structural/facade.py`

**Key interface:**
```python
class ComputerFacade:
    def __init__(self)  # creates CPU, Memory, SolidStateDrive internally
    def start(self)     # orchestrates boot sequence
```

**Usage:**
```python
from patterns.structural.facade import ComputerFacade
computer = ComputerFacade()
computer.start()
# Freezing processor.
# Loading from 0x00 data: '...'
# Jumping to: 0x00
# Executing.
```

---

### `patterns/structural/decorator.py`

**Key interface:**
```python
class TextTag:
    def render(self) -> str

class BoldWrapper(TextTag):
    def __init__(self, wrapped: TextTag) -> None
    def render(self) -> str  # → "<b>{wrapped.render()}</b>"

class ItalicWrapper(TextTag):
    def __init__(self, wrapped: TextTag) -> None
    def render(self) -> str  # → "<i>{wrapped.render()}</i>"
```

**Usage:**
```python
from patterns.structural.decorator import TextTag, BoldWrapper, ItalicWrapper
tag = ItalicWrapper(BoldWrapper(TextTag("hello")))
print(tag.render())  # → "<i><b>hello</b></i>"
```

---

### `patterns/structural/flyweight.py`

**Key interface:**
```python
class Card:
    _pool: weakref.WeakValueDictionary  # shared pool
    def __new__(cls, value: str, suit: str)  # returns cached or new instance
    def __repr__(self) -> str
```

**Usage:**
```python
from patterns.structural.flyweight import Card
c1 = Card("9", "h")
c2 = Card("9", "h")
assert c1 is c2  # same object returned from pool
```

---

### `patterns/structural/proxy.py`

**Key interface:**
```python
class Subject:
    def do_the_job(self, user: str) -> None

class RealSubject(Subject):
    def do_the_job(self, user: str) -> None

class Proxy(Subject):
    def do_the_job(self, user: str) -> None  # adds logging + access control

def client(job_doer: Union[RealSubject, Proxy], user: str) -> None
```

---

### `patterns/structural/composite.py`

**Key interface:**
```python
class Graphic(ABC):
    @abstractmethod
    def render(self) -> None

class CompositeGraphic(Graphic):
    def add(self, graphic: Graphic) -> None
    def remove(self, graphic: Graphic) -> None
    def render(self) -> None  # delegates to children

class Ellipse(Graphic):
    def render(self) -> None  # leaf node
```

---

### `patterns/structural/mvc.py`

**Key interface:**
```python
class Model(ABC):
    def __iter__(self) -> Any
    def get(self, item: str) -> dict
    @property
    def item_type(self) -> str

class View(ABC):
    def show_item_list(self, item_type: str, item_list: list) -> None
    def show_item_information(self, item_type: str, item_name: str, item_info: dict) -> None
    def item_not_found(self, item_type: str, item_name: str) -> None

class Controller:
    def __init__(self, model_class: Model, view_class: View) -> None
    def show_items(self) -> None
    def show_item_information(self, item_name: str) -> None

class Router:
    def register(self, path: str, controller_class, model_class, view_class) -> None
    def resolve(self, path: str) -> Controller
```

---

## Behavioral Patterns

### `patterns/behavioral/observer.py`

**Key interface:**
```python
class Observer:
    def update(self, subject: "Subject") -> None

class Subject:
    def attach(self, observer: Observer) -> None
    def detach(self, observer: Observer) -> None
    def notify(self) -> None

class Data(Subject):
    @property
    def data(self) -> int
    @data.setter
    def data(self, value: int) -> None  # calls self.notify() on set
```

**Usage:**
```python
from patterns.behavioral.observer import Data, DecimalViewer, HexViewer
d = Data("sensor")
d.attach(DecimalViewer())
d.data = 42  # → "DecimalViewer: Subject sensor has data 42"
```

---

### `patterns/behavioral/strategy.py`

**Key interface:**
```python
class DiscountStrategyValidator:  # descriptor
    def __set_name__(self, owner, name: str) -> None
    def __set__(self, obj: "Order", value: Callable) -> None
    def __get__(self, obj, objtype) -> Callable

class Order:
    discount_strategy = DiscountStrategyValidator()
    def __init__(self, price: float, discount_strategy: Callable = None) -> None
    def apply_discount(self) -> float

def ten_percent_discount(order: Order) -> float
def on_sale_discount(order: Order) -> float
```

**Usage:**
```python
from patterns.behavioral.strategy import Order, ten_percent_discount
order = Order(100, discount_strategy=ten_percent_discount)
print(order.apply_discount())  # → 90.0
```

---

### `patterns/behavioral/command.py`

**Key interface:**
```python
class HideFileCommand:
    def execute(self, filename: str) -> None
    def undo(self) -> None

class DeleteFileCommand:
    def execute(self, filename: str) -> None
    def undo(self) -> None

class MenuItem:
    def __init__(self, command: Union[HideFileCommand, DeleteFileCommand]) -> None
    def on_do_press(self, filename: str) -> None
    def on_undo_press(self) -> None
```

---

### `patterns/behavioral/chain_of_responsibility.py`

**Key interface:**
```python
class Handler(ABC):
    def __init__(self, successor: Optional["Handler"] = None)
    def handle(self, request: int) -> None  # delegates to successor if can't handle
    @abstractmethod
    def check_range(self, request: int) -> Optional[bool]
```

**Usage:**
```python
from patterns.behavioral.chain_of_responsibility import (
    ConcreteHandler0, ConcreteHandler1, ConcreteHandler2, FallbackHandler
)
h0 = ConcreteHandler0()
h1 = ConcreteHandler1()
h2 = ConcreteHandler2(FallbackHandler())
h0.successor = h1
h1.successor = h2
h0.handle(5)   # → "request 5 handled in handler 0"
h0.handle(15)  # → "request 15 handled in handler 1"
```

---

### `patterns/behavioral/publish_subscribe.py`

**Key interface:**
```python
class Provider:
    def notify(self, msg: str) -> None
    def subscribe(self, msg: str, subscriber: "Subscriber") -> None
    def unsubscribe(self, msg: str, subscriber: "Subscriber") -> None
    def update(self) -> None  # dispatches queued messages to subscribers

class Publisher:
    def publish(self, msg: str) -> None

class Subscriber:
    def subscribe(self, msg: str) -> None
    def unsubscribe(self, msg: str) -> None
    def run(self, msg: str) -> None  # called when a subscribed message is dispatched
```

---

### `patterns/behavioral/memento.py`

**Key interface:**
```python
def memento(obj: Any, deep: bool = False) -> Callable  # returns restore() closure

class Transaction:
    def __init__(self, deep: bool, *targets: Any) -> None
    def commit(self) -> None
    def rollback(self) -> None

def Transactional(method)  # decorator: rolls back on exception
```

---

### `patterns/behavioral/registry.py`

**Key interface:**
```python
class RegistryHolder(type):  # metaclass
    REGISTRY: Dict[str, "RegistryHolder"] = {}
    @classmethod
    def get_registry(cls) -> dict

class BaseRegisteredClass(metaclass=RegistryHolder):
    """Inherit from this to auto-register in RegistryHolder.REGISTRY."""
```

---

### `patterns/behavioral/specification.py`

**Key interface:**
```python
class CompositeSpecification(Specification):
    @abstractmethod
    def is_satisfied_by(self, candidate) -> bool
    def and_specification(self, candidate) -> "AndSpecification"
    def or_specification(self, candidate) -> "OrSpecification"
    def not_specification(self) -> "NotSpecification"
```

**Usage:**
```python
from patterns.behavioral.specification import UserSpecification, SuperUserSpecification, User
spec = UserSpecification().and_specification(SuperUserSpecification())
spec.is_satisfied_by(User(super_user=True))  # → True
```

---

### `patterns/behavioral/visitor.py`

**Key interface:**
```python
class Visitor:
    def visit(self, node: Union[A, C, B], *args, **kwargs) -> None
    # Dispatches to visit_ClassName() via MRO walk, falls back to generic_visit()
    def generic_visit(self, node, *args, **kwargs) -> None
    def visit_B(self, node, *args, **kwargs) -> None
```

---

## Design for Testability

### `patterns/dependency_injection.py`

**Three DI variants:**
```python
class ConstructorInjection:
    def __init__(self, time_provider: Callable) -> None  # inject at construction
    def get_current_time_as_html_fragment(self) -> str

class ParameterInjection:
    def get_current_time_as_html_fragment(self, time_provider: Callable) -> str  # inject per call

class SetterInjection:
    def set_time_provider(self, time_provider: Callable)  # inject via setter
    def get_current_time_as_html_fragment(self) -> str
```

**Usage:**
```python
from patterns.dependency_injection import ConstructorInjection, midnight_time_provider
ti = ConstructorInjection(midnight_time_provider)
ti.get_current_time_as_html_fragment()  # → '<span class="tinyBoldText">24:01</span>'
```

---

## Other / Non-GoF Patterns

### `patterns/other/blackboard.py`

```python
class AbstractExpert(ABC):
    @property
    @abstractmethod
    def is_eager_to_contribute(self) -> int: ...
    @abstractmethod
    def contribute(self) -> None: ...

class Blackboard:
    def add_expert(self, expert: AbstractExpert) -> None

class Controller:
    def run_loop(self)  # runs until common_state["progress"] >= 100
```

### `patterns/other/hsm/hsm.py`

```python
class HierachicalStateMachine:
    def on_message(self, message_type: str) -> None
    # Dispatches to current state's handler

class Unit:  # base state
class Inservice(Unit):
class OutOfService(Unit):
class Active(Inservice):
class Standby(Inservice):
class Suspect(OutOfService):
class Failed(OutOfService):
```

---

## Integration Patterns and Workflows

### Running a Pattern as a Script
```bash
python patterns/creational/factory.py
# Runs doctest.testmod() — equivalent to pytest --doctest-modules on that file
```

### Importing into Your Own Code
```python
# Since the package has no runtime deps, patterns are directly importable
from patterns.behavioral.observer import Subject, Observer
from patterns.creational.pool import ObjectPool
from patterns.structural.flyweight import Card
```

### Extending a Pattern
The standard extension point is subclassing:
```python
# Extend Chain of Responsibility
from patterns.behavioral.chain_of_responsibility import Handler
class MyHandler(Handler):
    def check_range(self, request: int) -> Optional[bool]:
        if request == 42:
            print("handled!")
            return True
```

### Adding New Patterns
Per the contributing guidelines:
1. Create `patterns/<category>/<pattern_name>.py` with the standard docstring structure.
2. Implement classes/functions with type annotations.
3. Add a `main()` function with embedded doctests.
4. Add `if __name__ == "__main__": import doctest; doctest.testmod()`.
5. Add corresponding `tests/<category>/test_<pattern_name>.py` if needed.
6. Update `README.md` with a row in the appropriate table.
