# import-tree — Code Structure

## Annotated Directory Tree

```
import-tree/
├── default.nix                   # The entire library — single Nix file
├── flake.nix                     # Trivial flake wrapper (outputs = _: import ./.)
├── LICENSE                       # License file
├── README.md                     # Project overview and quick-start examples
│
├── checkmate/                    # Test suite (used by vic/checkmate test runner)
│   ├── modules/
│   │   ├── tests.nix             # All nix-unit test cases
│   │   └── formatter.nix        # treefmt exclusion config for test fixtures
│   └── tree/                    # File fixtures used by tests
│       ├── a/
│       │   ├── a.txt             # Non-nix file (for initFilter tests)
│       │   ├── a_b.nix           # Nix file (name contains underscore)
│       │   └── b/
│       │       ├── b_a.nix       # Nix file
│       │       ├── m.nix         # Nix file
│       │       ├── _n.nix        # Hidden file (underscore prefix, ignored)
│       │       └── _c/           # Hidden directory (underscore prefix)
│       │           └── d/
│       │               ├── e.nix # Accessible (root of _c traversal is allowed)
│       │               └── _f.nix # Double-hidden (ignored)
│       ├── x/
│       │   └── y.nix             # Returns "z" when imported (for map tests)
│       ├── hello/
│       │   └── world             # Non-nix file (not imported)
│       └── modules/
│           ├── hello-world/
│           │   └── mod.nix       # Sets config.hello = "world"
│           └── hello-option/
│               └── mod.nix       # Declares options.hello option
│
├── docs/                         # Documentation site (Astro Starlight)
│   ├── astro.config.mjs          # Astro + Starlight config, sidebar structure
│   ├── package.json              # pnpm dependencies (astro, starlight, catppuccin)
│   ├── pnpm-lock.yaml            # Locked dependency versions
│   ├── tsconfig.json             # TypeScript config for the docs
│   ├── public/
│   │   └── favicon.svg           # Site favicon
│   └── src/
│       ├── content.config.ts     # Astro content collection config
│       ├── assets/
│       │   └── houston.webp      # Image asset
│       ├── components/           # Custom Astro components
│       │   ├── Sidebar.astro     # Custom sidebar component
│       │   ├── Footer.astro      # Footer component
│       │   ├── SocialIcons.astro # Social links component
│       │   ├── PageSidebar.astro # Per-page sidebar
│       │   ├── Ad.astro          # Sponsor/ad component
│       │   └── tabs/             # Tabbed content components
│       │       ├── TabbedContent.astro
│       │       ├── TabListItem.astro
│       │       ├── TabPanel.astro
│       │       └── LICENSE
│       └── content/
│           └── docs/             # Documentation pages
│               ├── motivation.mdx
│               ├── community.md
│               ├── contributing.md
│               ├── getting-started/
│               │   └── quick-start.mdx
│               ├── guides/
│               │   ├── filtering.mdx
│               │   ├── mapping.mdx
│               │   ├── custom-api.mdx
│               │   ├── outside-modules.mdx
│               │   └── dendritic.mdx
│               └── reference/
│                   └── api.mdx
│
├── .github/
│   ├── FUNDING.yml               # GitHub Sponsors config
│   └── workflows/
│       ├── test.yml              # CI: runs checkmate test suite
│       └── gh-pages.yml         # CI: builds and deploys docs to GitHub Pages
│
└── .tangled/
    └── workflows/
        └── mirror.yml            # Tangled (Codeberg mirror) workflow
```

## Module and Package Organization

`import-tree` has no traditional package structure — it is intentionally a **single Nix expression**. The codebase is split into three concerns:

1. **Library core** (`default.nix`): The entire import-tree implementation.
2. **Tests** (`checkmate/`): Test suite and test fixtures, consumed by the external `vic/checkmate` test runner.
3. **Documentation** (`docs/`): Astro Starlight static site.

## Main Source: `default.nix`

The library is structured as a single `let … in` block with named internal helpers and a single exported value (`callable`). Key internal components:

### Top-level `let` bindings

| Name | Type | Purpose |
|------|------|---------|
| `perform` | function | Core execution: given a config + path, produces module or file list |
| `compose` | function | Function composition: `g ∘ f` |
| `and` | function | Logical AND for predicates (note: second arg applied first) |
| `andNot` | function | `and` with negation |
| `matchesRegex` | function | Wraps `builtins.match` for predicate use |
| `mapAttr` | function | Update a single attr in an attrset |
| `isDirectory` | function | Predicate: path is a directory |
| `isPathLike` | function | Predicate: path, string, or has `outPath` |
| `hasOutPath` | function | Predicate: attrset with `outPath` field |
| `isImportTree` | function | Predicate: attrset with `__config.__functor` |
| `inModuleEval` | function | Predicate: attrset with `options` (module system context) |
| `functor` | function | User-facing `__functor`: delegates to `perform` |
| `callable` | attrset | Root import-tree value — the library export |

### Inside `perform`

`perform` takes a config record and a path argument, then:
1. Determines result type: if `pipef != null`, computes file list via `pipef`; otherwise returns a module attrset (`{ imports = [ module ]; }`).
2. The inner `module` is a function `{ lib, ... }: { imports = leafs lib path; }` — this defers `lib` access to module evaluation time.
3. `leafs` is a curried function `lib -> root -> [paths]` that:
   - Recursively lists files via `lib.filesystem.listFilesRecursive`
   - Handles import-tree objects, `outPath` containers, directories, and plain files
   - Computes `nixFilter` (default: `.nix` suffix + no `/_` infix)
   - Applies `initialFilter` (default or custom `initf`)
   - Composes `filterf` on top
   - Applies `mapf` to each result
   - Makes paths relative to roots for filter string matching

### Inside `callable`

`callable` is built from an `initial` config record via `initial (config: config)`. The config record holds:

| Field | Initial value | Purpose |
|-------|--------------|---------|
| `api` | `{}` | Accumulated custom API methods |
| `mapf` | `i: i` (identity) | Accumulated path transformation |
| `filterf` | `_: true` (allow all) | Accumulated additional filter predicate |
| `paths` | `[]` | Accumulated list of pre-configured paths |
| `lib` | not set | Nix lib (set by `.withLib`) |
| `pipef` | not set | Output pipe function (set by `.leafs`/`.pipeTo`) |
| `initf` | not set | Initial filter replacement (set by `.initFilter`) |
| `__functor` | internal | The config update mechanism |

The `__functor` on the config accepts an update function, applies it, and returns a new import-tree with:
- All accumulated API methods bound to the new instance (late binding)
- Builder methods: `.filter`, `.filterNot`, `.match`, `.matchNot`, `.map`, `.addPath`, `.addAPI`
- Output methods: `.withLib`, `.initFilter`, `.pipeTo`, `.leafs`, `.files`, `.result`, `.new`

## Key Files and Their Roles

### `default.nix` (the entire library, ~200 lines)
The library. Contains all logic: the builder pattern, recursive file traversal, filtering, mapping, and module generation. No imports, no dependencies.

### `flake.nix` (3 lines)
```nix
{ outputs = _: import ./.; }
```
Makes the library usable as a flake input. Ignores all flake inputs and re-exports the default.nix value as flake outputs.

### `checkmate/modules/tests.nix`
Comprehensive test suite covering: `leafs`, `filter`, `filterNot`, `match`, `matchNot`, `map`, `addPath`, `addAPI`, `pipeTo`, `initFilter`, `new`, and general import-tree invocation patterns. Tests are structured as `nix-unit` test cases grouped by feature.

### `checkmate/tree/`
Fixture directory tree used by tests. Demonstrates the `/_` ignore convention, non-nix files, nested directories, and various module shapes.

## Code Organization Patterns

1. **Single-file functional design**: All logic in one file, relying on Nix's lazy evaluation and let-binding for encapsulation.
2. **Builder/fluent pattern**: Each method returns a new import-tree instance, enabling method chaining.
3. **Functor pattern**: The `__functor` field on attrsets makes them callable in Nix (`obj arg` desugars to `obj.__functor obj arg`).
4. **Accumulator pattern**: `filterf` and `mapf` are accumulated with composition; `paths` and `api` are accumulated with list/attrset merge.
5. **Late binding**: API methods receive `self` (the current import-tree) at call time, enabling forward references.
6. **Lazy lib injection**: `lib` is accessed lazily inside a module argument when used within the module system, avoiding the need for `.withLib` in the common case.
