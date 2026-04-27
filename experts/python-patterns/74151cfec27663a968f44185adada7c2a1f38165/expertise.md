### Creational Patterns
- Abstract Factory pattern — `patterns/creational/abstract_factory.py` — Python idiom: passing the class itself as the factory callable
- Borg / Monostate pattern — `patterns/creational/borg.py` — shared state via `__dict__` assignment, alternative to Singleton
- Builder pattern — `patterns/creational/builder.py` — `Building` base class calling abstract `build_floor()` / `build_size()`, external `construct_building()` director
- Factory Method pattern — `patterns/creational/factory.py` — `get_localizer()` factory function, `Localizer` Protocol for structural subtyping
- Lazy Evaluation pattern — `patterns/creational/lazy_evaluation.py` — `lazy_property` descriptor class and `lazy_property2` function decorator, caching in `__dict__`
- Object Pool pattern — `patterns/creational/pool.py` — `ObjectPool` wrapping `queue.Queue` with context manager (`__enter__`, `__exit__`, `__del__`)
- Prototype pattern — `patterns/creational/prototype.py` — `Prototype.clone()` method, `PrototypeDispatcher` registry for named prototypes

### Structural Patterns
- 3-Tier Architecture — `patterns/structural/3-tier.py` — strict data / business logic / presentation layer separation
- Adapter pattern — `patterns/structural/adapter.py` — `Adapter` class storing adapted methods in `__dict__`, `__getattr__` passthrough to wrapped object
- Bridge pattern — `patterns/structural/bridge.py` — Abstraction / Implementor separation
- Composite pattern — `patterns/structural/composite.py` — `Graphic` ABC, `CompositeGraphic` with children list, `Ellipse` leaf
- Decorator pattern — `patterns/structural/decorator.py` — `TextTag` / `BoldWrapper` / `ItalicWrapper` wrapping chain with `render()`
- Facade pattern — `patterns/structural/facade.py` — `ComputerFacade` orchestrating `CPU`, `Memory`, `SolidStateDrive`
- Flyweight pattern — `patterns/structural/flyweight.py` — `Card.__new__()` using `weakref.WeakValueDictionary` pool
- Flyweight with Metaclass — `patterns/structural/flyweight_with_metaclass.py` — alternative implementation using metaclass
- Front Controller pattern — `patterns/structural/front_controller.py` — single dispatcher for all requests
- MVC pattern — `patterns/structural/mvc.py` — `Model` / `View` / `Controller` ABCs + `Router`, `ProductModel`, `ConsoleView`
- Proxy pattern — `patterns/structural/proxy.py` — `Proxy` + `RealSubject` sharing `Subject` interface, with access control and logging

### Behavioral Patterns
- Catalog pattern — `patterns/behavioral/catalog.py` — construction-time dispatch to specialized handler methods
- Chain of Responsibility — `patterns/behavioral/chain_of_responsibility.py` — `Handler` ABC with successor chaining, `ConcreteHandler0/1/2`, `FallbackHandler`
- Chaining Method (Fluent Interface) — `patterns/behavioral/chaining_method.py` — method chaining returning `self`
- Command pattern — `patterns/behavioral/command.py` — `HideFileCommand` / `DeleteFileCommand` with `execute()` + `undo()`, `MenuItem` invoker
- Iterator pattern — `patterns/behavioral/iterator.py` — custom `__iter__` / `__next__` implementation
- Iterator (alternative) — `patterns/behavioral/iterator_alt.py` — alternative iterator approach
- Mediator pattern — `patterns/behavioral/mediator.py` — mediator coordinating colleague objects without direct coupling
- Memento pattern — `patterns/behavioral/memento.py` — `memento()` closure capturing `__dict__`, `Transaction` guard, `@Transactional` decorator rolling back on exception
- Observer pattern — `patterns/behavioral/observer.py` — `Observer` / `Subject` with `attach()`, `detach()`, `notify()`, `Data` subclass with property setter triggering notify
- Publish-Subscribe pattern — `patterns/behavioral/publish_subscribe.py` — `Provider` message queue, `Publisher`, `Subscriber` with topic-based subscription
- Registry pattern — `patterns/behavioral/registry.py` — `RegistryHolder` metaclass auto-registering all subclasses in `REGISTRY` dict
- Servant pattern — `patterns/behavioral/servant.py` — providing common functionality to unrelated classes without inheritance
- Specification pattern — `patterns/behavioral/specification.py` — `CompositeSpecification` with `and_specification()`, `or_specification()`, `not_specification()` boolean chaining
- State pattern — `patterns/behavioral/state.py` — `Radio` with `AmState` / `FmState` states, `toggle_amfm()` / `scan()` delegating to current state
- Strategy pattern — `patterns/behavioral/strategy.py` — `Order` with `DiscountStrategyValidator` descriptor, callable strategies (`ten_percent_discount`, `on_sale_discount`)
- Template Method pattern — `patterns/behavioral/template.py` — `template_function()` with pluggable getter/converter/saver callables (functional style, not subclass-based)
- Visitor pattern — `patterns/behavioral/visitor.py` — `Visitor.visit()` dispatching via MRO walk to `visit_ClassName()` methods, `generic_visit()` fallback

### Fundamental / Other Patterns
- Delegation pattern — `patterns/fundamental/delegation_pattern.py` — `Delegator.__getattr__` transparently forwarding attribute access and calls to `Delegate`
- Blackboard pattern — `patterns/other/blackboard.py` — `Blackboard` shared state, `AbstractExpert` with `is_eager_to_contribute` / `contribute()`, `Controller.run_loop()`
- Graph Search — `patterns/other/graph_search.py` — BFS / DFS graph traversal algorithms
- Hierarchical State Machine (HSM) — `patterns/other/hsm/hsm.py` — `HierachicalStateMachine`, `Unit`/`Inservice`/`OutOfService` hierarchy, `Active`/`Standby`/`Suspect`/`Failed` states

### Design for Testability
- Dependency Injection (3 variants) — `patterns/dependency_injection.py` — `ConstructorInjection`, `ParameterInjection`, `SetterInjection`

### Python-Specific Idioms
- Using `Protocol` for structural subtyping (duck typing) instead of abstract base classes
- Passing classes as callables for Abstract Factory (no factory-class boilerplate)
- `__dict__` manipulation for Borg / Monostate pattern
- `__new__` override for Flyweight / Singleton-like caching
- Metaclass `__new__` for automatic Registry pattern
- Python descriptor protocol (`__set_name__`, `__set__`, `__get__`) for Strategy validation
- `functools.update_wrapper` for preserving wrapped function metadata in descriptors
- `weakref.WeakValueDictionary` for memory-safe object pools
- `from __future__ import annotations` for forward references in type hints
- Context manager protocol (`__enter__`, `__exit__`) for resource lifecycle (Object Pool)
- MRO (`__mro__`) traversal for visitor dispatch
- `copy.deepcopy` / `copy.copy` for Memento and Prototype cloning
- Closures as mementos (restore function capturing `__dict__` snapshot)

### Anti-Patterns in Python (explicitly documented in README)
- Why Singleton is an anti-pattern in Python (use module-level variables instead)
- Why God Object is harmful (split into cohesive classes)
- Why deep inheritance is problematic (prefer composition and delegation)

### Build and Testing
- `pytest --doctest-modules` — running embedded doctests in pattern files
- `pyproject.toml` configuration for pytest, coverage, mypy, flake8, tox
- Coverage with `pytest-cov`, branch coverage, dynamic context per test function
- `black` + `isort` + `flake8` linting pipeline
- Makefile targets: `pylinter`, `pyupgrade`
- Python 3.10–3.13 compatibility
