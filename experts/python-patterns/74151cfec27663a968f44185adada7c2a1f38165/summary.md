# python-patterns — Repository Summary

## Repository Purpose and Goals

`python-patterns` (maintained by **faif** at https://github.com/faif/python-patterns) is a community-driven reference collection of software design patterns and idioms implemented in idiomatic Python. The core philosophy is that patterns should be understood at the level of *why* to choose them, not just *how* to implement them. The project also explicitly documents several common patterns as **anti-patterns in Python** (Singleton, God Object, excessive inheritance), guiding developers toward Python-native solutions.

The repository serves three purposes:
1. Educational reference — readable, well-commented implementations with docstrings that explain the intent and trade-offs of every pattern.
2. Idiomatic examples — showing how Python's first-class functions, duck typing, descriptors, metaclasses, and protocols make many classical OOP patterns simpler or unnecessary.
3. Practical linking — each pattern file includes references to real-world usage in frameworks (Django, Flask, Grok, Bottle, Werkzeug, etc.).

## Key Features and Capabilities

- **35+ patterns** spanning all four classical categories: Creational, Structural, Behavioral, and Other (non-GoF).
- Each pattern file is self-contained and executable (`if __name__ == "__main__"` → `doctest.testmod()`).
- **Doctests embedded in `main()` functions** serve simultaneously as documentation and automated tests. `pytest --doctest-modules` runs them all.
- Pattern files include sections: *What is this pattern about?*, *What does this example do?*, *Where is it used practically?*, *Examples in Python ecosystem*, and *TL;DR*.
- **Type annotations** throughout (Python 3.10+), using `typing` module constructs (`Protocol`, `Callable`, `TypeVar`, `Dict`, `List`, etc.).
- Visualization diagrams (`viz/` subdirectories) as PNG class-diagram images generated from the code.
- Anti-pattern documentation in the README warns against Singleton, God Object, and deep inheritance hierarchies in Python.

## Primary Use Cases and Target Audience

- **Students and learners** studying software design patterns who want Python-specific implementations.
- **Intermediate Python developers** seeking idiomatic ways to solve recurring design problems.
- **Code reviewers and architects** looking for reference implementations to compare against production code.
- **Interview preparation** — the patterns are exactly the canonical 23 GoF patterns plus several additional idioms.

## High-Level Architecture Overview

The project is a flat collection of Python modules organized into five sub-packages under the top-level `patterns/` package:

```
patterns/
├── creational/    — 7 patterns: abstract_factory, borg, builder, factory, lazy_evaluation, pool, prototype
├── structural/    — 10 patterns: 3-tier, adapter, bridge, composite, decorator, facade, flyweight,
│                                 flyweight_with_metaclass, front_controller, mvc, proxy
├── behavioral/    — 18 patterns: catalog, chain_of_responsibility, chaining_method, command, iterator,
│                                 iterator_alt, mediator, memento, observer, publish_subscribe, registry,
│                                 servant, specification, state, strategy, template, visitor
├── fundamental/   — 1 pattern: delegation_pattern
├── other/         — 3 patterns: blackboard, graph_search, hsm (hierarchical state machine)
└── dependency_injection.py  — 3 DI variants (constructor, parameter, setter injection)
```

Each pattern file follows a consistent structure:
1. Module-level docstring explaining the pattern.
2. Class / function definitions implementing the pattern.
3. A `main()` function containing embedded doctests.
4. A `if __name__ == "__main__": doctest.testmod()` guard.

Tests live in a parallel `tests/` tree that mirrors the `patterns/` hierarchy, using `pytest` with dedicated test files for selected patterns.

## Related Projects and Dependencies

- **Runtime dependencies**: None — `dependencies = []` in `pyproject.toml`. The library is entirely self-contained using only Python standard library modules (`queue`, `weakref`, `copy`, `abc`, `typing`, `functools`, `random`).
- **Dev/test dependencies**: `pytest`, `pytest-cov`, `pytest-randomly`, `black`, `isort`, `flake8`, `mypy`, `tox`, `pyupgrade`, `build`, `pipx`.
- **Build system**: `setuptools` (via `pyproject.toml` with `[build-system]`).
- **CI**: Travis CI (`.travis.yml`) and GitHub Actions (`.github/workflows/lint_python.yml`, `lint_pr.yml`).
- **Python compatibility**: Python 3.10, 3.11, 3.12, 3.13 (per `pyproject.toml` classifiers and `requires-python = ">=3.10"`).
- **Related resources cited in the code**: ActiveState recipes, SourceMaking, Python Cookbook (Beazley & Jones), Grok framework, Django, Flask, Werkzeug, Bottle, Pyramid, and various academic/blog references.
