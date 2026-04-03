# Jinja2 — APIs and Interfaces

## Core Entry Points

### Creating an Environment

`Environment` (`src/jinja2/environment.py:145`) is the primary entry point for all Jinja2 usage.

```python
from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader("templates/"),
    autoescape=True,           # Enable HTML autoescaping
    trim_blocks=True,          # Strip newline after block tags
    lstrip_blocks=True,        # Strip leading whitespace before block tags
    undefined=StrictUndefined, # Raise on undefined variables
)
```

**Full constructor signature** (`environment.py:295`):
```python
Environment(
    block_start_string="{%",     block_end_string="%}",
    variable_start_string="{{",  variable_end_string="}}",
    comment_start_string="{#",   comment_end_string="#}",
    line_statement_prefix=None,  line_comment_prefix=None,
    trim_blocks=False,           lstrip_blocks=False,
    newline_sequence="\n",       keep_trailing_newline=False,
    extensions=(),
    optimized=True,
    undefined=Undefined,         # or StrictUndefined, DebugUndefined, ChainableUndefined
    finalize=None,               # Callable applied to every output value
    autoescape=False,            # bool or callable(template_name) -> bool
    loader=None,
    cache_size=400,
    auto_reload=True,
    bytecode_cache=None,
    enable_async=False,
)
```

### Loading and Rendering Templates

```python
# Load a named template
tmpl = env.get_template("index.html")

# Load the first template found from a list
tmpl = env.select_template(["custom.html", "default.html"])

# Render to a string
result = tmpl.render(name="World", items=[1, 2, 3])

# Render from a string (no loader needed)
tmpl = env.from_string("Hello {{ name }}!")
result = tmpl.render(name="Alice")

# Render asynchronously (requires enable_async=True)
result = await tmpl.render_async(name="World")

# Stream output (memory-efficient for large templates)
stream = tmpl.stream(name="World")
stream.enable_buffering(5)   # Buffer 5 items before yielding
for chunk in stream:
    response.write(chunk)
```

### Compile Expression

`Environment.compile_expression` (`environment.py:772`) evaluates a single Jinja expression:

```python
env = Environment()
expr = env.compile_expression("foo == 42")
expr(foo=42)   # True
expr(foo=0)    # False

# Undefined resolves to None by default
env.compile_expression("missing_var")()  # None
# Set undefined_to_none=False to get the Undefined object
env.compile_expression("missing_var", undefined_to_none=False)()  # Undefined
```

### Ahead-of-Time Compilation

`Environment.compile_templates` pre-compiles all templates to a target directory for use with `ModuleLoader`:

```python
env.compile_templates("/path/to/output/", zip=None, ignore_errors=True)
```

## Template Loaders

All loaders are in `src/jinja2/loaders.py`. Every loader is a subclass of `BaseLoader`.

### FileSystemLoader
```python
from jinja2 import FileSystemLoader
# Single directory
loader = FileSystemLoader("/path/to/templates")
# Multiple directories (searched in order)
loader = FileSystemLoader(["/path/a", "/path/b"])
# Control encoding
loader = FileSystemLoader("/path/to/templates", encoding="utf-8", followlinks=True)
```

### PackageLoader
```python
from jinja2 import PackageLoader
# Load from mypackage/templates/
loader = PackageLoader("mypackage", "templates")
```

### DictLoader
```python
from jinja2 import DictLoader
loader = DictLoader({"index.html": "Hello {{ name }}", "base.html": "{% block body %}{% endblock %}"})
```

### FunctionLoader
```python
from jinja2 import FunctionLoader
def load_template(name):
    # Return source string, or (source, filename, uptodate_callable), or None
    return open(f"templates/{name}").read()
loader = FunctionLoader(load_template)
```

### PrefixLoader
```python
from jinja2 import PrefixLoader, FileSystemLoader
loader = PrefixLoader({
    "admin": FileSystemLoader("/admin/templates"),
    "user":  FileSystemLoader("/user/templates"),
})
# Usage in templates: {% include "admin/dashboard.html" %}
```

### ChoiceLoader
```python
from jinja2 import ChoiceLoader, FileSystemLoader, PackageLoader
loader = ChoiceLoader([FileSystemLoader("/override"), PackageLoader("myapp")])
```

### Custom Loader
```python
from jinja2 import BaseLoader, TemplateNotFound
import os

class MyLoader(BaseLoader):
    def __init__(self, path):
        self.path = path

    def get_source(self, environment, template):
        path = os.path.join(self.path, template)
        if not os.path.exists(path):
            raise TemplateNotFound(template)
        mtime = os.path.getmtime(path)
        with open(path) as f:
            source = f.read()
        return source, path, lambda: mtime == os.path.getmtime(path)
```

## Undefined Types

All undefined types are in `src/jinja2/runtime.py`.

| Class | Behavior |
|---|---|
| `Undefined` (default) | Silent — renders as empty string, raises `UndefinedError` on iteration/call/attribute access |
| `DebugUndefined` | Renders as `{{ varname }}` (the original expression), useful for debugging |
| `StrictUndefined` | Raises `UndefinedError` immediately on any access including string conversion |
| `ChainableUndefined` | Like `Undefined` but attribute/item access returns another `ChainableUndefined` |

```python
from jinja2 import Environment, StrictUndefined, make_logging_undefined
import logging

# Strict undefined
env = Environment(undefined=StrictUndefined)

# Logging undefined — logs a warning and falls back to another Undefined class
LoggingUndefined = make_logging_undefined(logger=logging.getLogger(__name__), base=Undefined)
env = Environment(undefined=LoggingUndefined)
```

## Autoescaping

```python
from jinja2 import Environment, select_autoescape

# Enable for .html and .xml, disable for .txt
env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html", "xml"])
)

# Custom function
env = Environment(autoescape=lambda name: name is not None and name.endswith(".html"))
```

`select_autoescape` (`utils.py`) takes `enabled_extensions` and `disabled_extensions` lists and returns a callable.

## Filters

### Adding Custom Filters

```python
def my_filter(value, multiplier=2):
    return value * multiplier

env.filters["multiply"] = my_filter
# Usage: {{ 5 | multiply(3) }}  → 15
```

### Filters Needing Context/Environment

```python
from jinja2 import pass_context, pass_environment, pass_eval_context

@pass_context
def context_filter(ctx, value):
    return f"{value} (user={ctx['user']})"

@pass_environment
def env_filter(env, value):
    return env.getattr(value, "name")

env.filters["ctx_filter"] = context_filter
env.filters["env_filter"] = env_filter
```

### Async Filters

```python
from jinja2.async_utils import async_variant

@pass_eval_context
def sync_filter(eval_ctx, value):
    return str(value)

@async_variant(sync_filter)
@pass_eval_context
async def async_filter(eval_ctx, value):
    result = await some_async_op(value)
    return str(result)

env.filters["my_filter"] = async_filter
```

## Tests (is Operator)

```python
def is_prime(value):
    if value < 2:
        return False
    for i in range(2, int(value**0.5) + 1):
        if value % i == 0:
            return False
    return True

env.tests["prime"] = is_prime
# Usage: {% if n is prime %}...{% endif %}
```

## Global Functions

```python
env.globals["current_user"] = lambda: get_current_user()
env.globals["url_for"] = url_for_function
# Usage: {{ current_user().name }}, {{ url_for('index') }}
```

## Bytecode Cache

```python
from jinja2 import FileSystemBytecodeCache, MemcachedBytecodeCache, Environment

# Filesystem cache
env = Environment(
    loader=FileSystemLoader("templates"),
    bytecode_cache=FileSystemBytecodeCache("/tmp/jinja_cache", "%s.cache"),
)

# Memcached cache
import pylibmc
client = pylibmc.Client(["127.0.0.1"])
env = Environment(
    loader=FileSystemLoader("templates"),
    bytecode_cache=MemcachedBytecodeCache(client, timeout=600),
)

# Custom bytecode cache
from jinja2 import BytecodeCache
class MyCache(BytecodeCache):
    def load_bytecode(self, bucket):
        data = db.get(bucket.key)
        if data:
            bucket.bytecode_from_string(data)

    def dump_bytecode(self, bucket):
        db.set(bucket.key, bucket.bytecode_to_string())
```

## Extensions

### Writing a Custom Extension (`ext.py:55`)

```python
from jinja2 import nodes
from jinja2.ext import Extension

class FragmentCacheExtension(Extension):
    tags = {"cache"}  # Tags this extension handles

    def parse(self, parser):
        lineno = next(parser.stream).lineno
        # Parse the cache key expression
        args = [parser.parse_expression()]
        body = parser.parse_statements(["name:endcache"], drop_needle=True)
        return nodes.CallBlock(
            self.call_method("_cache_support", args),
            [], [], body, lineno=lineno
        )

    def _cache_support(self, name, caller):
        key = f"fragment_{name}"
        cached = self.environment.fragment_cache.get(key)
        if cached is not None:
            return cached
        rv = caller()
        self.environment.fragment_cache.set(key, rv, 300)
        return rv

# Usage:
env = Environment(extensions=[FragmentCacheExtension])
env.fragment_cache = my_cache_backend
```

Built-in extensions activated by name:
- `"jinja2.ext.i18n"` — `{% trans %}` internationalization
- `"jinja2.ext.debug"` — `{% debug %}` tag
- `"jinja2.ext.loopcontrols"` — `{% break %}` / `{% continue %}`
- `"jinja2.ext.do"` — `{% do expression %}` statement
- `"jinja2.ext.profiler"` — performance profiling

## I18N Extension

```python
from jinja2 import Environment
import gettext

env = Environment(extensions=["jinja2.ext.i18n"])
translations = gettext.translation("messages", localedir="locale", languages=["de"])
env.install_gettext_translations(translations)
# Template: {% trans count=items|count %}{{ count }} item{% pluralize %}{{ count }} items{% endtrans %}
```

Methods on `Environment` added by `InternationalizationExtension`:
- `env.install_gettext_translations(translations, newstyle=False)`
- `env.install_null_translations(newstyle=False)`
- `env.install_gettext_callables(gettext, ngettext, newstyle=False)`
- `env.uninstall_gettext_translations()`
- `env.extract_translations(source, gettext_functions=GETTEXT_FUNCTIONS)`

## NativeEnvironment

`NativeEnvironment` (`nativetypes.py:88`) and `NativeTemplate` return Python native types instead of strings:

```python
from jinja2.nativetypes import NativeEnvironment

env = NativeEnvironment()
tmpl = env.from_string("{{ value }}")
result = tmpl.render(value=42)     # int: 42
result = tmpl.render(value=[1,2])  # list: [1, 2]

tmpl = env.from_string("[1, 2, {{ x }}]")
result = tmpl.render(x=3)          # list: [1, 2, 3]
```

## Sandboxed Environment

```python
from jinja2.sandbox import SandboxedEnvironment

env = SandboxedEnvironment()
# Safely renders untrusted templates
tmpl = env.from_string("{{ obj.__class__.__name__ }}")  # SecurityError
```

## Template Overlays

```python
base_env = Environment(loader=FileSystemLoader("templates"))
# Create an overlay with different settings but shared loader/cache/extensions
overlay = base_env.overlay(autoescape=True, trim_blocks=False)
```

## Meta API (Introspection)

```python
from jinja2 import Environment, meta

env = Environment()
ast = env.parse("{% set x = 1 %}{{ x + y }}")

# Find variables that must come from context
meta.find_undeclared_variables(ast)  # {'y'}

# Find referenced templates
ast2 = env.parse('{% extends "base.html" %}{% include helper %}')
list(meta.find_referenced_templates(ast2))  # ['base.html', None]
```

## Policies Configuration

The `environment.policies` dict controls runtime behavior:

```python
env.policies["truncate.leeway"] = 5          # Characters of leeway for truncate filter
env.policies["urlize.rel"] = "noopener"      # rel= attribute for urlize
env.policies["urlize.target"] = "_blank"     # target= attribute for urlize
env.policies["urlize.extra_schemes"] = None  # Additional URL schemes
env.policies["json.dumps_function"] = None   # Custom JSON dumps function
env.policies["json.dumps_kwargs"] = {"sort_keys": True}
env.policies["compiler.ascii_str"] = True    # Compile time ascii optimization
env.policies["ext.i18n.trimmed"] = False     # Trim whitespace in trans blocks
```

## Exception Hierarchy

All exceptions are in `src/jinja2/exceptions.py`:

```
TemplateError(Exception)
├── TemplateNotFound(IOError, LookupError, TemplateError)
│   └── TemplatesNotFound
├── TemplateSyntaxError
│   └── TemplateAssertionError
└── TemplateRuntimeError
    ├── UndefinedError
    ├── SecurityError
    └── FilterArgumentError
```

## Utility Functions

```python
from jinja2 import is_undefined, clear_caches, select_autoescape

# Check if a value is Undefined
is_undefined(some_value)  # bool

# Clear the LRU template caches
clear_caches()

# Smart autoescape selector
autoescape = select_autoescape(
    enabled_extensions=("html", "xml"),
    disabled_extensions=("txt",),
    default_for_string=True,  # Default when template name is unknown
    default=False,
)
```
