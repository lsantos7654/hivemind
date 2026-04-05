# python-patterns — Code Structure

## Annotated Directory Tree

```
python-patterns/
├── README.md                          # Full pattern index with Mermaid diagrams and anti-pattern section
├── pyproject.toml                     # PEP 517 build config, dev dependencies, pytest/coverage/tox/mypy/flake8 settings
├── Makefile                           # Convenience targets: pylinter (black+isort+flake8), pyupgrade (pip-sync)
├── pytest_local.ini                   # Alternate pytest config for local runs (non-doctest-module mode)
├── requirements-dev.txt               # Flat dev requirements (flake8, black, isort, pytest, pytest-randomly, mypy, pyupgrade, tox)
├── lint.sh                            # Shell script running full lint suite
├── .travis.yml                        # Travis CI configuration
├── .codespellignore                   # Words excluded from codespell checks (e.g. Greek translations)
├── .gitignore
│
├── .github/
│   └── workflows/
│       ├── lint_pr.yml                # PR title linting workflow
│       └── lint_python.yml            # Python lint + test workflow
│
├── config_backup/                     # Legacy config files (kept as reference)
│   ├── .coveragerc                    # Old coverage config (superseded by pyproject.toml [tool.coverage])
│   ├── setup.cfg                      # Old setup config (superseded by pyproject.toml)
│   └── tox.ini                        # Old tox config (superseded by pyproject.toml [tool.tox])
│
├── patterns/                          # Main source package
│   ├── __init__.py                    # Empty package marker
│   ├── dependency_injection.py        # DI pattern (3 variants) — lives at package root, not in a sub-package
│   │
│   ├── creational/                    # Object-creation patterns
│   │   ├── __init__.py
│   │   ├── abstract_factory.py        # PetShop using callable factories (Dog, Cat, random_animal)
│   │   ├── borg.py                    # Monostate via __dict__ sharing; YourBorg demo
│   │   ├── builder.py                 # Building/Flat/ComplexBuilding + construct_building() helper
│   │   ├── factory.py                 # get_localizer() factory; Localizer Protocol; EnglishLocalizer/GreekLocalizer
│   │   ├── lazy_evaluation.py         # lazy_property descriptor + lazy_property2 decorator
│   │   ├── pool.py                    # ObjectPool via queue.Queue with context manager (__enter__/__exit__/__del__)
│   │   ├── prototype.py               # Prototype.clone() + PrototypeDispatcher registry
│   │   └── viz/                       # PNG class diagrams (builder, factory_method, pool, prototype, abstract_factory, etc.)
│   │
│   ├── structural/                    # Class/object composition patterns
│   │   ├── __init__.py
│   │   ├── 3-tier.py                  # Data / BusinessLogic / Presentation layer separation
│   │   ├── adapter.py                 # Adapter class with **adapted_methods in __init__; __getattr__ passthrough
│   │   ├── bridge.py                  # Abstraction / Implementor separation
│   │   ├── composite.py               # Graphic ABC + CompositeGraphic + Ellipse leaf
│   │   ├── decorator.py               # TextTag / BoldWrapper / ItalicWrapper chained render()
│   │   ├── facade.py                  # ComputerFacade wrapping CPU / Memory / SolidStateDrive
│   │   ├── flyweight.py               # Card with WeakValueDictionary pool, __new__ override
│   │   ├── flyweight_with_metaclass.py# Alternative flyweight using metaclass
│   │   ├── front_controller.py        # Single dispatcher for all HTTP-style requests
│   │   ├── mvc.py                     # Model / View / Controller + Router; ProductModel / ConsoleView
│   │   ├── proxy.py                   # Proxy / RealSubject with access control and logging
│   │   └── viz/                       # PNG class diagrams (composite, proxy, flyweight, adapter, 3-tier, bridge, etc.)
│   │
│   ├── behavioral/                    # Object interaction and responsibility patterns
│   │   ├── __init__.py
│   │   ├── catalog.py                 # Catalog with construction-time dispatch to specialized methods
│   │   ├── chain_of_responsibility.py # Handler ABC + ConcreteHandler0/1/2 + FallbackHandler linked chain
│   │   ├── chaining_method.py         # Method chaining / fluent interface pattern
│   │   ├── command.py                 # HideFileCommand / DeleteFileCommand / MenuItem invoker with undo
│   │   ├── iterator.py                # Custom iterator with __iter__ / __next__
│   │   ├── iterator_alt.py            # Alternative iterator implementation
│   │   ├── mediator.py                # Mediator coordinating colleagues without direct coupling
│   │   ├── memento.py                 # memento() closure + Transaction guard + @Transactional descriptor
│   │   ├── observer.py                # Observer / Subject / Data / HexViewer / DecimalViewer
│   │   ├── publish_subscribe.py       # Provider / Publisher / Subscriber with message queue
│   │   ├── registry.py                # RegistryHolder metaclass auto-registering all subclasses
│   │   ├── servant.py                 # Servant providing common behavior to unrelated classes
│   │   ├── specification.py           # CompositeSpecification + AndSpecification / OrSpecification / NotSpecification
│   │   ├── state.py                   # Radio with AmState / FmState + toggle_amfm / scan
│   │   ├── strategy.py                # Order + DiscountStrategyValidator descriptor + callable strategies
│   │   ├── template.py                # template_function() with pluggable getter/converter/saver callables
│   │   ├── visitor.py                 # Visitor.visit() using MRO lookup (visit_ClassName methods)
│   │   └── viz/                       # PNG class diagrams (all behavioral patterns)
│   │
│   ├── fundamental/                   # Core OOP idiom patterns
│   │   ├── __init__.py
│   │   ├── delegation_pattern.py      # Delegator.__getattr__ transparently forwarding to Delegate
│   │   └── viz/                       # PNG diagram
│   │
│   └── other/                         # Non-GoF / architectural patterns
│       ├── __init__.py
│       ├── blackboard.py              # Blackboard + AbstractExpert + Controller + Student/Scientist/Professor
│       ├── graph_search.py            # BFS / DFS graph traversal algorithms
│       └── hsm/
│           ├── __init__.py
│           ├── hsm.py                 # HierachicalStateMachine + Unit/Inservice/Active/Standby/OutOfService/Suspect/Failed
│           ├── classes_hsm.png
│           └── classes_test_hsm.png
│
└── tests/                             # pytest test suite (mirrors patterns/ structure)
    ├── __init__.py
    ├── test_hsm.py                    # HSM integration tests
    │
    ├── creational/
    │   ├── test_abstract_factory.py
    │   ├── test_borg.py
    │   ├── test_builder.py
    │   ├── test_factory.py
    │   ├── test_lazy.py
    │   ├── test_pool.py
    │   └── test_prototype.py
    │
    ├── behavioral/
    │   ├── test_catalog.py
    │   ├── test_mediator.py
    │   ├── test_memento.py
    │   ├── test_observer.py
    │   ├── test_publish_subscribe.py
    │   ├── test_servant.py
    │   ├── test_state.py
    │   ├── test_strategy.py
    │   └── test_visitor.py
    │
    ├── structural/
    │   ├── test_adapter.py
    │   ├── test_bridge.py
    │   ├── test_decorator.py
    │   ├── test_facade.py
    │   ├── test_flyweight.py
    │   ├── test_mvc.py
    │   └── test_proxy.py
    │
    └── fundamental/
        └── test_delegation.py
```

## Module and Package Organization

### Pattern File Convention

Every pattern module follows a strict, consistent layout:

1. **Module docstring** — Explains the pattern in 2–5 paragraphs:
   - `*What is this pattern about?` — conceptual description
   - `*What does this example do?` — concrete example walkthrough
   - `*Where is the pattern used practically?` — real-world references
   - `*Examples in Python ecosystem:` — links to Django/Flask/stdlib usage
   - `*TL;DR` — one-line summary
   - `*References:` — URLs to further reading

2. **Implementation classes/functions** — with type annotations using `typing` module.

3. **`main()` function** — contains embedded `doctest` examples as docstring. These are the primary test vectors.

4. **`if __name__ == "__main__": import doctest; doctest.testmod()`** — making each file directly executable.

### Type Annotation Patterns

The codebase uses Python 3.10+ type syntax throughout:
- `Protocol` for structural subtyping (e.g., `Localizer` protocol in `factory.py`)
- `ABC` + `@abstractmethod` for abstract base classes (e.g., `Handler` in `chain_of_responsibility.py`, `Graphic` in `composite.py`)
- `from __future__ import annotations` for forward references (e.g., `observer.py`, `state.py`)
- `TypeVar` for generic adapter patterns (e.g., `T = TypeVar("T")` in `adapter.py`)
- `weakref.WeakValueDictionary` typed pool in `flyweight.py`

### Key Python Idioms Used

- **`__dict__` sharing** — Borg pattern (creational/borg.py:43) shares state between instances by pointing all `__dict__` references to the same dict.
- **`__new__` override** — Flyweight pattern (structural/flyweight.py:39) intercepts object creation to return cached instances.
- **Metaclass** — Registry pattern (behavioral/registry.py:4) uses `RegistryHolder(type)` to auto-register subclasses in `REGISTRY`.
- **Descriptor protocol** — Strategy pattern uses `DiscountStrategyValidator` (behavioral/strategy.py:15) as a descriptor with `__set_name__`, `__set__`, `__get__`.
- **Context manager** — Pool pattern (creational/pool.py:35) implements `__enter__`/`__exit__`/`__del__` for lifecycle management.
- **MRO dispatch** — Visitor pattern (behavioral/visitor.py:36) walks `node.__class__.__mro__` to find `visit_ClassName` methods.
- **Callable factories** — Abstract Factory uses plain callables instead of factory classes (creational/abstract_factory.py).
- **`functools.update_wrapper`** — lazy_property descriptor (creational/lazy_evaluation.py:29) preserves wrapped function metadata.

### Naming Conventions

- Pattern files use `snake_case` module names matching the canonical pattern name.
- Classes use `PascalCase`.
- Tests use `test_<pattern_name>.py`.
- Visualization diagrams use `<module_name>.py.png` under `viz/` subdirectories.
- The `main()` function is the doctest entry point in every pattern file.
