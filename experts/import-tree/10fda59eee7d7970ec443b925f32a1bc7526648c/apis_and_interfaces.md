# import-tree — APIs and Interfaces

## Obtaining the import-tree Object

```nix
# As a flake input (recommended):
inputs.import-tree.url = "github:vic/import-tree";
# inputs.import-tree IS the callable import-tree object

# As a plain Nix import:
let import-tree = import /path/to/import-tree;

# Non-flake, from tarball:
let import-tree = import (builtins.fetchTarball {
  url = "https://github.com/vic/import-tree/archive/main.tar.gz";
});
```

The value obtained is a **callable attrset** — the primary import-tree object. All API methods are attributes on this object, and it can also be called directly as a function.

---

## Core Invocation

### `import-tree <path | [paths] | otherInputs>`

**Signature**: `import-tree :: path | list | attrset -> NixModule`

Calling the import-tree object directly with a path (or list of paths) returns a Nix module whose `imports` list contains all discovered files.

```nix
# Single directory:
import-tree ./modules

# List of directories:
import-tree [ ./modules ./extra ]

# Arbitrarily nested lists (auto-flattened):
import-tree [ ./a [ ./b ./c ] ]

# Other import-tree objects treated as path sources:
import-tree [ (import-tree.addPath ./vendor) ./modules ]

# Attrset with outPath (e.g., flake inputs):
import-tree [ { outPath = ./modules; } ]

# Raw attrsets/modules (passed through filter, included if they pass):
import-tree [
  { options.foo = lib.mkOption { default = "bar"; type = lib.types.str; }; }
]
```

**Special behavior**:
- When the argument is an attrset with `options`, import-tree detects module evaluation context and returns `{ imports = []; }` (empty imports) rather than treating it as a path. This lets a pre-configured tree appear directly in `imports`.
- Paths with `outPath` (like flake inputs) are resolved to `outPath`.
- Other import-tree objects in lists are expanded to their file lists.

**Source**: `default.nix:137` (`functor`) and `default.nix:14` (`perform`).

---

## Filtering API

All filter methods accumulate with logical AND — a file must pass all filters applied.

### `.filter <fn>`

**Signature**: `filter :: (string -> bool) -> import-tree`

Include only files where `fn path` returns `true`. The path is passed as a string.

```nix
# Only files containing ".mod." in path:
import-tree.filter (lib.hasInfix ".mod.") ./modules

# Only files in a desktop/ subdirectory:
import-tree.filter (lib.hasInfix "/desktop/") ./modules

# Composing multiple filters (AND):
(import-tree.filter (lib.hasInfix "/src/")).filter (lib.hasSuffix "_spec.nix") ./modules
```

**Source**: `default.nix:173`

### `.filterNot <fn>`

**Signature**: `filterNot :: (string -> bool) -> import-tree`

Exclude files where `fn path` returns `true` (inverse of `.filter`).

```nix
import-tree.filterNot (lib.hasInfix "experimental") ./modules
import-tree.filterNot (lib.hasInfix "test") ./modules
```

**Source**: `default.nix:174`

### `.match <regex>`

**Signature**: `match :: string -> import-tree`

Include only files whose full path matches the regex. Uses `builtins.match` (tests the **entire** string — the regex must match the complete path).

```nix
# Files named like "word_word.nix":
import-tree.match ".*/[a-z]+_[a-z]+\.nix" ./modules

# Files under a specific directory pattern:
import-tree.match ".*/services/[^/]+\.nix" ./modules
```

Multiple `.match` calls compose with AND.

**Source**: `default.nix:175`

### `.matchNot <regex>`

**Signature**: `matchNot :: string -> import-tree`

Exclude files matching the regex.

```nix
import-tree.matchNot ".*/test_.*\.nix" ./modules
import-tree.matchNot ".*/[0-9]+\.nix" ./modules
```

**Source**: `default.nix:176`

### `.initFilter <fn>`

**Signature**: `initFilter :: (string | any -> bool) -> import-tree`

**Replaces** the default filter entirely (default: `.nix` suffix + no `/_` infix). Also applies to non-path items (attrsets) in import lists.

```nix
# Find .txt files instead of .nix:
import-tree.initFilter (lib.hasSuffix ".txt") ./docs

# Find .nix but use /ignored/ instead of /_ as ignore convention:
import-tree.initFilter (p: lib.hasSuffix ".nix" p && !lib.hasInfix "/ignored/" p)

# Filter out specific attrset-shaped modules:
import-tree.initFilter (x: !(x ? config.boom)) [ module1 module2 ]
```

**Source**: `default.nix:183`

---

## Transformation API

### `.map <fn>`

**Signature**: `map :: (path -> a) -> import-tree`

Transform each discovered path. Applied after filtering. Multiple `.map` calls compose left-to-right (first map runs first).

```nix
# Wrap each path in a module:
import-tree.map (path: { imports = [ path ]; }) ./modules

# Trace discovered paths for debugging:
import-tree.map lib.traceVal ./modules

# Actually import each file:
(import-tree.withLib lib).map import |>.leafs ./modules

# Compose maps:
(import-tree.withLib lib)
  .map import           # first: import each file
  .map builtins.stringLength  # then: get result length
  |>.leafs ./modules
```

**Source**: `default.nix:177`

---

## Path Accumulation API

### `.addPath <path>`

**Signature**: `addPath :: path -> import-tree`

Add a path to the internal path list. Can be called multiple times — paths are appended in order.

```nix
# Discover files in both directories:
(import-tree.addPath ./vendor).addPath ./modules

# Using with .files (no need to call with a path):
(import-tree.withLib lib).addPath ./modules |>.files

# Equivalent to calling with a list:
(import-tree.withLib lib).addPath ./a |>.addPath ./b |>.files
# is the same as:
(import-tree.withLib lib).leafs [ ./a ./b ]
```

**Source**: `default.nix:178`

---

## Extension API

### `.addAPI <attrset>`

**Signature**: `addAPI :: { name: (self -> ...) } -> import-tree`

Extend the import-tree object with new named methods. Each value is a function `self -> result` where `self` is the current import-tree instance. Methods are **late-bound** — they resolve at call time, allowing forward references.

```nix
# Basic extension:
let extended = import-tree.addAPI {
  helloOption = self: self.addPath ./modules/hello-option;
  feature = self: infix: self.filter (lib.hasInfix infix);
  minimal = self: self.feature "minimal";
};
extended.helloOption.files
extended.feature "networking" ./modules
extended.minimal ./src

# Cumulative — previous extensions preserved:
let first = import-tree.addAPI { foo = self: self.addPath ./foo; };
let second = first.addAPI { bar = self: self.addPath ./bar; };
second.foo.files  # still works

# Late binding (forward reference):
let first = import-tree.addAPI { result = self: self.late; };
let extended = first.addAPI { late = _self: "hello"; };
extended.result  # => "hello"

# Real-world: module distribution:
let modules-tree = lib.pipe import-tree [
  (i: i.addPath ./modules)
  (i: i.addAPI { on = self: flag: self.filter (lib.hasInfix "+${flag}"); })
  (i: i.addAPI { off = self: flag: self.filterNot (lib.hasInfix "+${flag}"); })
  (i: i.addAPI { ruby = self: self.on "ruby"; })
  (i: i.addAPI { python = self: self.on "python"; })
];
# Consumer:
{ imports = [ (modules-tree.ruby.python) ]; }
```

**Source**: `default.nix:179`

---

## Output API

### `.withLib <lib>`

**Signature**: `withLib :: lib -> import-tree`

Provides `lib` for use outside module evaluation. Required before calling `.leafs`, `.files`, or `.pipeTo`. Inside the module system, `lib` is obtained automatically from module arguments.

```nix
import-tree.withLib pkgs.lib
import-tree.withLib lib  # inside a module
```

**Source**: `default.nix:182`

### `.leafs`

**Signature**: `leafs :: import-tree` (callable as `leafs <path>`)

Returns a configured import-tree that, when called with a path, produces a flat list of discovered files (instead of a module). Requires `.withLib` to have been called.

```nix
(import-tree.withLib lib).leafs ./modules
# => [ ./modules/a.nix ./modules/b.nix ]

(import-tree.withLib lib).leafs [ ./a ./b ]
# => [ ./a/x.nix ./b/y.nix ]

# Leafs on a file path (not a directory) — returns that file:
(import-tree.withLib lib).leafs ./modules/a.nix
# => [ ./modules/a.nix ]
```

**Source**: `default.nix:185` and inner `leafs` function starting at `default.nix:29`

### `.files`

**Signature**: `files :: [path]`

Shorthand for `.leafs.result` — evaluates the configured paths and returns a flat list. Requires `.addPath` to have been called and `.withLib` to be set.

```nix
lib.pipe import-tree [
  (i: i.addPath ./modules)
  (i: i.withLib lib)
  (i: i.files)
]
# => [ ./modules/a.nix ./modules/b.nix ]
```

**Source**: `default.nix:191`

### `.pipeTo <fn>`

**Signature**: `pipeTo :: (list -> a) -> import-tree`

Like `.leafs` but pipes the discovered file list through `fn`. Useful for counting, folding, or other list operations.

```nix
(import-tree.withLib lib).pipeTo builtins.length ./modules
# => 5

(import-tree.withLib lib).map lib.pathType |>.pipeTo lib.length ./modules
# => count of files
```

**Source**: `default.nix:184`

### `.result`

**Signature**: `result :: NixModule | [path]`

Evaluates the import-tree with an empty path list (i.e., `current []`). Equivalent to calling with `[]`. Useful when paths have been pre-configured via `.addPath`.

```nix
(import-tree.addPath ./modules).result
# equivalent to: (import-tree.addPath ./modules) []
```

**Source**: `default.nix:188`

### `.new`

**Signature**: `new :: import-tree`

Returns a fresh import-tree object with empty state — no paths, no filters, no maps, no API extensions.

```nix
let configured = import-tree.addPath ./modules;
let fresh = configured.new;  # back to a clean slate
```

**Source**: `default.nix:194`

---

## Default Filter Behavior

The built-in default filter (`nixFilter`) at `default.nix:45`:

```nix
nixFilter = andNot (lib.hasInfix "/_") (lib.hasSuffix ".nix");
```

- **Includes**: files ending in `.nix`
- **Excludes**: any file whose path contains `/_` (underscore-prefixed directory segment)

**Exception**: When explicitly starting traversal from a `/_` directory, files at that root level are included (only sub-`/_` paths are excluded). Example from tests: `lit.leafs ../tree/a/b/_c` returns `[ ../tree/a/b/_c/d/e.nix ]` but not `../tree/a/b/_c/d/_f.nix`.

---

## Integration Patterns

### With flake-parts

```nix
# flake.nix
{
  inputs.import-tree.url = "github:vic/import-tree";
  inputs.flake-parts.url = "github:hercules-ci/flake-parts";

  outputs = inputs: inputs.flake-parts.lib.mkFlake { inherit inputs; }
    (inputs.import-tree ./modules);
}
```

### With NixOS / home-manager

```nix
{ config, ... }: {
  imports = [ (import-tree ./modules) ];
}
```

### Non-flake (with npins + with-inputs)

```nix
let
  sources = import ./npins;
  with-inputs = import sources.with-inputs sources { };
  outputs = inputs:
    (inputs.nixpkgs.lib.evalModules {
      specialArgs.inputs = inputs;
      modules = [ (inputs.import-tree ./modules) ];
    }).config;
in
with-inputs outputs
```

### Module distribution (library pattern)

```nix
# Library flake module:
{ inputs, lib, ... }:
let
  on = self: flag: self.filter (lib.hasInfix "+${flag}");
  off = self: flag: self.filterNot (lib.hasInfix "+${flag}");
in {
  flake.lib.modules-tree = lib.pipe inputs.import-tree [
    (i: i.addPath ./modules)
    (i: i.addAPI { inherit on off; })
    (i: i.addAPI { ruby = self: self.on "ruby"; })
  ];
}

# Consumer:
{ inputs, ... }: {
  imports = [ (inputs.my-lib.lib.modules-tree.ruby) ];
}
```

---

## Configuration Options

There are no runtime configuration files. All configuration is done through the builder API. The key configurable behaviors:

| Behavior | Default | How to change |
|----------|---------|--------------|
| File suffix filter | `.nix` | `.initFilter` |
| Ignored path pattern | `/_` | `.initFilter` |
| Additional include predicate | accept all | `.filter` / `.match` |
| Additional exclude predicate | none | `.filterNot` / `.matchNot` |
| Path transformation | identity | `.map` |
| Output format | NixModule | `.leafs` / `.pipeTo` |
| Custom methods | none | `.addAPI` |
