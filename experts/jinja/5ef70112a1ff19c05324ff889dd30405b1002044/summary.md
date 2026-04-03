# Jinja2 — Summary

## Repository Purpose and Goals

Jinja2 (package name `Jinja2`, import name `jinja2`) is a fast, expressive, and extensible Python templating engine maintained by the Pallets organization. Its primary goal is to provide a full-featured template language that keeps application logic in Python while giving template designers a powerful, safe, and readable syntax. Version 3.2.0.dev (commit 5ef70112) requires Python ≥ 3.10 and has a single runtime dependency: `MarkupSafe >= 3.0`.

The project is hosted at https://github.com/pallets/jinja and documented at https://jinja.palletsprojects.com/.

## Key Features and Capabilities

- **Template inheritance and block overriding** — templates can `{% extends %}` a parent and override named `{% block %}` sections.
- **Template inclusion and import** — `{% include %}` embeds another template inline; `{% import %}` / `{% from ... import %}` brings macros into scope.
- **Macros** — reusable template functions defined with `{% macro %}`.
- **Autoescaping** — configurable per-environment or per-extension to prevent XSS when rendering HTML/XML.
- **Sandboxed execution** — `SandboxedEnvironment` restricts attribute access, method calls, and mutable operations to safely evaluate untrusted templates.
- **Async support** — full AsyncIO support via `enable_async=True`; filters, tests, and globals can be async-aware through the `async_variant` decorator pattern.
- **Bytecode cache** — compiled template bytecode can be persisted to the filesystem (`FileSystemBytecodeCache`) or Memcached (`MemcachedBytecodeCache`) to skip recompilation on subsequent requests.
- **Native types** — `NativeEnvironment` / `NativeTemplate` renders templates to native Python types (int, list, dict, etc.) instead of strings, using `ast.literal_eval`.
- **I18N support** — optional `i18n` extra (`Babel >= 2.17`) provides the `InternationalizationExtension` with `{% trans %}` blocks, `gettext`, `ngettext`, `pgettext`, and `npgettext`.
- **Extensible syntax** — custom `Extension` subclasses can add new tags, preprocess source, and filter the token stream.
- **Configurable delimiters** — block, variable, and comment markers are all overridable strings; line-statement and line-comment prefixes are also supported.
- **Template meta-analysis** — the `meta` module exposes `find_undeclared_variables` and `find_referenced_templates` for static analysis of template ASTs.
- **Full type annotations** — the package ships a `py.typed` marker; all public APIs carry precise type hints checked by mypy (strict) and pyright.

## Primary Use Cases and Target Audience

Jinja2 is primarily used by Python web developers as the default template engine in Flask and is widely adopted in:

- **Web applications** — generating HTML responses with variable substitution, loops, conditionals, and inheritance-based layouts.
- **Static site generators** — rendering pages from data files and reusable layout templates.
- **Configuration and code generation** — generating YAML, TOML, JSON, Dockerfile, Kubernetes manifests, Ansible playbooks, or source code files from templates.
- **Email and document rendering** — producing rendered text or HTML for transactional emails.
- **DevOps tooling** — Ansible and SaltStack use Jinja2 internally for templating configuration files.

Target audience: Python developers ranging from beginners building simple Flask apps to advanced users writing custom extensions, bytecode caches, or sandboxed evaluation environments.

## High-Level Architecture Overview

The compilation pipeline flows through five stages:

1. **Lexer** (`lexer.py`) — tokenizes the raw template source string into a `TokenStream`, respecting the configured delimiters and any extension `filter_stream` hooks.
2. **Parser** (`parser.py`) — converts the token stream into an Abstract Syntax Tree (AST) of `nodes.Node` subclasses (defined in `nodes.py`), processing extension `parse` hooks for custom tags.
3. **Optimizer** (`optimizer.py`) — performs constant folding and other compile-time simplifications on the AST.
4. **Code Generator** (`compiler.py`) — walks the AST via `NodeVisitor` (`visitor.py`) and emits Python source code (a module with a `root` function and per-block functions). `NativeCodeGenerator` (`nativetypes.py`) is a subclass that skips the `str()` wrapping.
5. **Runtime** (`runtime.py`) — the generated code executes inside this module's `Context`, `LoopContext`, `Macro`, and `Undefined` classes. The environment's compiled code objects are cached in an LRU cache.

The `Environment` class (`environment.py`) is the central hub: it holds all configuration (delimiters, filters, tests, globals, policies, extensions, loader, cache, bytecode cache) and drives the entire pipeline via `parse`, `compile`, `get_template`, and `from_string` methods. Multiple overlaid environments can share state via `Environment.overlay()`.

## Related Projects and Dependencies

- **MarkupSafe** — required runtime dependency; provides `Markup` (a safe HTML string type) and `escape()` used throughout for autoescaping.
- **Babel** — optional dependency (`i18n` extra) for internationalization support.
- **Flask** — Jinja2 is Flask's default template engine.
- **Ansible / SaltStack** — use Jinja2 as their configuration template language.
- **Sphinx** — uses Jinja2 for HTML theme templates.
- **Cookiecutter / Copier** — project scaffolding tools built on Jinja2.
- **Pallets ecosystem** — Jinja2 is part of the Pallets organization alongside Werkzeug, Click, Flask, ItsDangerous, and MarkupSafe.
