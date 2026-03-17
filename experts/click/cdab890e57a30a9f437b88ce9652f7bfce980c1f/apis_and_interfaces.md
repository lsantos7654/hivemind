# Click — APIs and Interfaces

## Public Entry Points

All public names are exported from the top-level `click` package. Import patterns:

```python
import click                          # Recommended: use click.command(), click.echo(), etc.
from click import command, option     # Also valid for selective imports
```

## Core Decorators

### `@click.command(name=None, cls=None, **attrs)`

Converts a Python function into a `Command` object.

```python
@click.command()
@click.option("--count", default=1, help="Number of greetings.")
@click.argument("name")
def hello(count, name):
    """Simple program that greets NAME for a total of COUNT times."""
    for _ in range(count):
        click.echo(f"Hello, {name}!")
```

`cls` allows specifying a custom `Command` subclass. `**attrs` are forwarded to the `Command` constructor.

### `@click.group(name=None, cls=None, **attrs)`

Creates a `Group` (multi-command). Subcommands are registered with `@group.command()`.

```python
@click.group()
def cli():
    """Management tool."""
    pass

@cli.command()
@click.argument("name")
def add(name):
    """Add a resource."""
    click.echo(f"Adding {name}")

if __name__ == "__main__":
    cli()
```

### `@click.option(*param_decls, **attrs)`

Adds an optional parameter to the nearest command. Options use `--name` / `-n` prefixes.

```python
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output.")
@click.option("--output", "-o", type=click.Path(), default="out.txt")
@click.option("--format", type=click.Choice(["json", "yaml", "csv"]), default="json")
@click.option("--count", type=int, default=1, show_default=True)
@click.option("--name", required=True, envvar="APP_NAME")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
```

Key parameters:
- `default` — default value (or callable)
- `required` — raise `MissingParameter` if not provided
- `type` — `ParamType` instance for conversion
- `multiple` — accept multiple values → returns tuple
- `is_flag` — boolean toggle
- `count` — count occurrences (`-vvv` → 3)
- `envvar` — environment variable name(s)
- `prompt` — prompt user if not provided
- `hide_input` — mask input (for passwords)
- `callback` — `fn(ctx, param, value) -> value`
- `is_eager` — process before non-eager params (for `--version`, `--help`)
- `expose_value` — if False, don't pass to callback (for side-effect options)
- `show_default` — include default in help text
- `help` — help string

### `@click.argument(*param_decls, **attrs)`

Adds a positional argument to the command.

```python
@click.argument("filename")                        # Required positional
@click.argument("files", nargs=-1)                 # Variadic (all remaining args)
@click.argument("src", type=click.Path(exists=True))
@click.argument("dst", type=click.Path())
```

Key parameters:
- `nargs` — number of values; `-1` means variadic (returns tuple)
- `type` — `ParamType` for conversion
- `required` — defaults to True for arguments
- `default` — only used when `required=False`

### Context Decorators

```python
@click.pass_context
def cmd(ctx):
    """Receives the click.Context as first argument."""
    click.echo(ctx.obj["verbose"])

@click.pass_obj
def cmd(obj):
    """Receives ctx.obj directly."""
    obj.do_something()

@click.make_pass_decorator(Config, ensure=True)
def pass_config(config):
    """Custom decorator for a specific type stored in ctx.obj."""
    pass

@click.pass_meta_key("key_name")
def cmd(value):
    """Receive ctx.meta["key_name"]."""
    pass
```

### Pre-built Composite Options

```python
@click.version_option("1.0.0", "--version", "-V", prog_name="myapp")
@click.help_option("--help", "-h")
@click.confirmation_option(prompt="Are you sure?")
@click.password_option(envvar="APP_PASSWORD")
```

## Core Classes

### `click.Context`

The execution context. Accessible via `@pass_context` or `click.get_current_context()`.

```python
ctx.params          # dict of resolved parameter values
ctx.obj             # user-defined object passed through group hierarchy
ctx.args            # remaining unprocessed arguments
ctx.info_name       # command name as invoked
ctx.parent          # parent Context (for subcommands)
ctx.meta            # dict for framework extensions
ctx.color           # color mode (True/False/None)
ctx.max_content_width   # help text width
ctx.default_map     # dict of defaults to override

ctx.ensure_object(type)     # initialize ctx.obj if None
ctx.with_resource(cm)       # register context manager for cleanup
ctx.call_on_close(fn)       # register cleanup callback
ctx.close()                 # run cleanup callbacks
ctx.fail(message)           # raise UsageError
ctx.exit(code=0)            # raise Exit
ctx.abort()                 # raise Abort

# Context manager usage (handles cleanup):
with cmd.make_context("prog", args) as ctx:
    cmd.invoke(ctx)
```

### `click.Command`

```python
cmd = click.Command(
    name="hello",
    callback=hello_fn,
    params=[click.Option(["--name"]), click.Argument(["file"])],
    help="Command help text.",
    epilog="Epilog text.",
    short_help="Short help.",
    add_help_option=True,
    no_args_is_help=False,
    hidden=False,
    deprecated=False,
)

cmd.main(args=None, prog_name=None, complete_var=None, standalone_mode=True, **extra)
cmd.get_help(ctx)          # returns formatted help string
cmd.get_short_help_str(limit=45)
cmd.to_info_dict(ctx)     # introspection dict
```

### `click.Group`

```python
@click.group(invoke_without_command=True, chain=True)
@click.pass_context
def cli(ctx):
    if ctx.invoked_subcommand is None:
        click.echo("No subcommand given")

cli.add_command(cmd, name="alias")
cli.list_commands(ctx)       # sorted list of command names
cli.get_command(ctx, name)   # retrieve Command by name
```

Chain mode (`chain=True`) allows: `tool process --opt1 transform --opt2`.

## Parameter Types

### Built-in Type Instances

```python
click.STRING      # str (default)
click.INT         # int
click.FLOAT       # float
click.BOOL        # bool (yes/no/1/0/true/false/on/off)
click.UUID        # uuid.UUID
click.UNPROCESSED # pass through unchanged
```

### Parameterized Types

```python
click.Choice(["a", "b", "c"], case_sensitive=False)
click.IntRange(min=0, max=100, clamp=False)  # clamp=True clips instead of errors
click.FloatRange(min=0.0, max=1.0)
click.DateTime(formats=["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"])
click.Tuple([click.INT, click.FLOAT, click.STRING])  # heterogeneous nargs=3

click.File("r")          # open file for reading, returns file object
click.File("w", lazy=True)   # lazy open (open on first write)
click.Path(
    exists=True,              # path must exist
    file_okay=True,           # allow files
    dir_okay=False,           # disallow directories
    writable=True,            # must be writable
    readable=True,
    resolve_path=True,        # resolve symlinks
    allow_dash=True,          # allow '-' for stdin
    path_type=pathlib.Path,   # return type (default: str)
    executable=True,          # must be executable
)
```

### Custom Type

```python
class ColorType(click.ParamType):
    name = "color"

    def convert(self, value, param, ctx):
        if isinstance(value, tuple):  # already converted
            return value
        try:
            r, g, b = (int(x) for x in value.split(","))
            return (r, g, b)
        except (ValueError, TypeError):
            self.fail(f"{value!r} is not a valid RGB color", param, ctx)

    def shell_complete(self, ctx, param, incomplete):
        return [
            click.shell_completion.CompletionItem(c)
            for c in ["255,0,0", "0,255,0", "0,0,255"]
            if c.startswith(incomplete)
        ]

COLOR = ColorType()
```

## Terminal Output Functions

```python
click.echo(message=None, file=None, nl=True, err=False, color=None)
# Writes to stdout (or file); handles unicode/bytes; strips ANSI when piped

click.secho("Hello", fg="green", bold=True, err=False)
# = click.echo(click.style("Hello", fg="green", bold=True))

click.style(
    text,
    fg=None,       # "black","red","green","yellow","blue","magenta","cyan","white"
                   # or (r, g, b) tuple for 256-color or RGB
    bg=None,       # same options as fg
    bold=None,
    dim=None,
    underline=None,
    overline=None,
    italic=None,
    blink=None,
    reverse=None,
    strikethrough=None,
    reset=True,    # append reset code at end
)
```

## Interactive Input Functions

```python
value = click.prompt(
    "Enter value",
    default="hello",
    hide_input=False,
    confirmation_prompt=False,
    type=click.INT,
    value_proc=None,         # custom conversion callable
    prompt_suffix=": ",
    show_default=True,
    err=False,
    show_choices=True,
)

confirmed = click.confirm("Are you sure?", default=False, abort=True)
# abort=True raises Abort if user says no

char = click.getchar(echo=False)  # read a single character without Enter

click.pause(info="Press any key to continue...", err=False)
```

## Progress Bar

```python
with click.progressbar(
    items,                    # iterable or None (use length)
    length=100,               # total length if iterable has no len()
    label="Processing",
    width=0,                  # 0 = auto-detect terminal width
    fill_char="=",
    empty_char="-",
    bar_template="%(label)s [%(bar)s] %(info)s",
    info_sep="  ",
    show_eta=True,
    show_percent=True,
    show_pos=False,
    item_show_func=None,      # callable(item) -> str for current item display
    file=None,
    color=None,
    update_min_steps=1,
) as bar:
    for item in bar:
        process(item)
    # or manual update:
    bar.update(n)
```

## Testing API

```python
from click.testing import CliRunner

runner = CliRunner(
    charset="utf-8",
    env={"MY_VAR": "value"},
    echo_input=False,
    mix_stderr=True,
)

result = runner.invoke(
    cli,
    args=["--option", "value", "arg"],
    input="user input\n",       # simulated stdin
    env={"EXTRA": "var"},
    catch_exceptions=True,
    color=False,
)

result.output          # str: captured stdout (+ stderr if mix_stderr=True)
result.exit_code       # int: 0 on success
result.exception       # Exception or None
result.exc_info        # sys.exc_info() tuple or None
result.return_value    # value returned by the command callback

# Isolated filesystem for tests that write files:
with runner.isolated_filesystem(temp_dir="/tmp"):
    result = runner.invoke(cli, ["--output", "file.txt"])
```

## Exception Handling

```python
# In callbacks, raise Click exceptions for user-facing errors:
raise click.BadParameter("Must be positive", param=param, param_hint="--count")
raise click.UsageError("Conflicting options")
raise click.ClickException("Something went wrong")  # exit code 1
raise click.Abort()     # silent exit with code 1 (Ctrl-C)
raise click.Exit(code=2)  # clean exit with specific code

# ctx.fail() is shorthand for UsageError:
ctx.fail("Invalid state")

# In standalone_mode=True (default), exceptions are caught and formatted.
# In standalone_mode=False, exceptions propagate to the caller.
```

## Shell Completion

```python
# Enable completion in shell profile:
# Bash: eval "$(_MYAPP_COMPLETE=bash_source myapp)"
# Zsh:  eval "$(_MYAPP_COMPLETE=zsh_source myapp)"
# Fish: myapp --_complete=fish_source | source
# PowerShell: (& myapp --_complete=powershell_source) | Invoke-Expression

# Custom completion for a type:
class MyType(click.ParamType):
    def shell_complete(self, ctx, param, incomplete):
        items = get_available_items()
        return [
            click.shell_completion.CompletionItem(item, help=f"Item {item}")
            for item in items
            if item.startswith(incomplete)
        ]

# Completion for an option callback:
@click.option("--name", shell_complete=lambda ctx, param, incomplete: [
    click.shell_completion.CompletionItem(n) for n in names if n.startswith(incomplete)
])
```

## Context Object Pattern (Group Hierarchy)

A common pattern for passing shared state through a group hierarchy:

```python
@click.group()
@click.option("--config", default="config.yaml", type=click.Path())
@click.pass_context
def cli(ctx, config):
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config)

@cli.command()
@click.pass_obj
def status(obj):
    config = obj["config"]
    click.echo(f"Config: {config}")
```

## Lazy Command Loading

For CLIs with many subcommands, use lazy loading to avoid importing all modules at startup:

```python
class LazyCLI(click.Group):
    def get_command(self, ctx, cmd_name):
        # Only import when the command is actually invoked
        import importlib
        try:
            mod = importlib.import_module(f"myapp.commands.{cmd_name}")
            return mod.cli
        except ImportError:
            return None

    def list_commands(self, ctx):
        return ["init", "run", "build", "deploy"]

@click.command(cls=LazyCLI)
def cli():
    pass
```

## Configuration Options Summary

| Feature | Where | Key Parameters |
|---|---|---|
| Auto env prefix | `Command` | `auto_envvar_prefix="MYAPP"` in `main()` |
| Default map | `Context` | `default_map={"opt": "val"}` |
| Help width | `Context` | `max_content_width=120` |
| Color control | `Context` | `color=True/False/None` |
| Token normalization | `Context` | `token_normalize_func=str.lower` |
| Resilient parsing | `Context` | `resilient_parsing=True` (for completion) |
| Allow extra args | `Context` | `allow_extra_args=True` |
| Allow interspersed | `Context` | `allow_interspersed_args=False` |
