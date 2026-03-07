# flake-parts Code Structure

## Annotated Directory Tree

```
flake-parts/
├── flake.nix                   # Root flake: exposes lib, templates, flakeModules
├── flake.lock                  # Locked inputs (only nixpkgs-lib)
├── lib.nix                     # Core library: mkFlake, evalFlakeModule, helpers
├── all-modules.nix             # Lists all core modules to import
│
├── modules/                    # Core built-in flake output modules
│   ├── flake.nix               # The `flake` top-level option (freeform attr set)
│   ├── perSystem.nix           # `systems`, `perSystem`, `allSystems`, `perInput`
│   ├── transposition.nix       # Transposes perSystem attrs to flake-level attrs
│   ├── withSystem.nix          # `withSystem` module argument
│   ├── moduleWithSystem.nix    # `moduleWithSystem` module argument
│   ├── nixpkgs.nix             # Auto-provides `pkgs` in perSystem from nixpkgs input
│   ├── packages.nix            # flake.packages / perSystem.packages
│   ├── devShells.nix           # flake.devShells / perSystem.devShells
│   ├── checks.nix              # flake.checks / perSystem.checks
│   ├── apps.nix                # flake.apps / perSystem.apps
│   ├── formatter.nix           # flake.formatter / perSystem.formatter
│   ├── overlays.nix            # flake.overlays
│   ├── legacyPackages.nix      # flake.legacyPackages / perSystem.legacyPackages
│   ├── nixosModules.nix        # flake.nixosModules
│   ├── nixosConfigurations.nix # flake.nixosConfigurations
│   └── debug.nix               # debug option: expose config/options in flake outputs
│
├── extras/                     # Optional importable extra modules
│   ├── easyOverlay.nix         # Expose perSystem packages as overlays.default
│   ├── flakeModules.nix        # flake.flakeModules / flake.flakeModule (alias)
│   ├── modules.nix             # flake.modules.<class>.<name>
│   ├── partitions.nix          # partitions + partitionedAttrs (lazy input loading)
│   └── bundlers.nix            # flake.bundlers / perSystem.bundlers
│
├── lib/
│   └── memoize/
│       ├── memoize.nix         # memoizeStr: trie-based string memoization
│       ├── bytes.dat           # All non-null byte values for trie keys
│       ├── measure-bytes-per-char.nix  # Utility for measuring memory cost
│       └── test.nix            # Tests for memoize.nix
│
├── template/                   # nix flake init templates
│   ├── default/
│   │   └── flake.nix           # Minimal flake-parts flake template
│   ├── multi-module/
│   │   ├── flake.nix           # Multi-module template (imports a flake-module.nix)
│   │   └── hello/
│   │       └── flake-module.nix  # Example sub-module
│   ├── package/
│   │   ├── flake.nix           # Package template with callPackage + checks
│   │   └── hello/
│   │       ├── package.nix     # Example package definition
│   │       ├── hello.sh        # Example shell script
│   │       └── test.nix        # Example test derivation
│   └── unfree/
│       └── flake.nix           # Template with nixpkgs unfree config
│
├── examples/                   # Full example flakes
│   ├── shell-environments/
│   │   ├── flake.nix           # devShells example
│   │   ├── flake.lock
│   │   └── README.md
│   └── project-commands/
│       ├── flake.nix           # nix run app example
│       ├── flake.lock
│       ├── Hello.avdl
│       └── README.md
│
├── dev/                        # Development flake (separate inputs, CI)
│   ├── flake.nix               # Development flake entry point
│   ├── flake.lock              # Dev-only locked inputs
│   ├── flake-module.nix        # Dev flake-module: devShells, checks, CI
│   └── tests/
│       ├── eval-tests.nix      # Pure evaluation tests (no build needed)
│       ├── template.nix        # Template smoke tests
│       └── README.md
│
├── vendor/
│   └── flake-compat/           # Vendored flake-compat (for partitions pure mode)
│       ├── default.nix
│       ├── README.md
│       └── COPYING
│
├── README.md                   # Project overview and quick start
├── CONTRIBUTING.md             # Coding style guide
├── ChangeLog.md                # Notable changes history
├── LICENSE                     # MIT license
├── bors.toml                   # Bors merge bot config
├── shell.nix                   # Legacy nix-shell (pre-commit hooks)
└── .gitignore
```

## Module and Package Organization

`flake-parts` is a **pure Nix library** — there are no Python, Rust, or other language source files. The entire project is Nix expressions.

The project has two distinct flakes:
1. **Root flake** (`flake.nix`): Minimal, depends only on `nixpkgs-lib`. Exports `lib`, `templates`, and `flakeModules`. Uses `partitions` to keep dev-only checks and devShells out of the main evaluation.
2. **Dev flake** (`dev/flake.nix` + `dev/flake-module.nix`): References `pre-commit-hooks-nix` and `hercules-ci-effects`. Provides the development shell and CI configuration. Loaded only by the `dev` partition.

## Main Source Directories and Their Purposes

### `modules/` — Core Built-in Modules

All files in `modules/` are imported by `all-modules.nix` and therefore always active when using `mkFlake`. These implement the standard flake output attributes.

The pattern used throughout is either:
- **`mkTransposedPerSystemModule`** — for per-system attributes that get transposed (packages, devShells, checks, apps, legacyPackages, bundlers). These define both `perSystem.<name>` and `flake.<name>` options linked by transposition.
- **Direct option declaration** — for non-per-system flake attributes (overlays, nixosModules, nixosConfigurations) or special options (debug, perSystem itself).

### `extras/` — Optional Extra Modules

These must be explicitly imported. They are exposed as `flake-parts.flakeModules.<name>`:
- `easyOverlay` → `flake-parts.flakeModules.easyOverlay`
- `flakeModules` → `flake-parts.flakeModules.flakeModules`
- `modules` → `flake-parts.flakeModules.modules`
- `partitions` → `flake-parts.flakeModules.partitions`
- `bundlers` → `flake-parts.flakeModules.bundlers`

### `lib/memoize/` — String Memoization

Implements a trie-based memoization for string inputs. Used by `perSystem.nix` to memoize the per-system module evaluation for systems not in the configured `systems` list (accessed via `withSystem` for arbitrary system strings). The trie uses `bytes.dat` (all 255 non-null byte values) as the character key set.

## Key Files and Their Roles

### `lib.nix` (Root library entry point)
The central file. Returns the `flake-parts-lib` attribute set after checking the nixpkgs-lib minimum version. Contains:
- `evalFlakeModule`: Core function that calls `lib.evalModules` with `all-modules.nix` and the user module
- `mkFlake`: Thin wrapper — evaluates and returns `eval.config.flake`
- `deferredModuleWith`: Legacy type for perSystem type-merging (deprecated in favor of nixpkgs `types.deferredModuleWith`)
- `mkPerSystemType` / `mkPerSystemOption`: Build option declarations for extending perSystem
- `mkTransposedPerSystemModule`: Build a complete module with both `perSystem.<name>` and `flake.<name>` options
- `importApply`: Import preserving module location info
- `importAndPublish`: Import and also publish as `flake.modules.flake.<name>`
- `memoizeStr`: Re-exported from `lib/memoize/memoize.nix`
- `mkAliasOptionModule`: Local implementation of an alias module helper
- `attrsWith`: Polyfill for `types.attrsWith` (available in Nixpkgs 25.05+)
- `defaultModule`: Extract `flakeModules.default` from a flake if it's a flake, otherwise return as-is

### `all-modules.nix`
Simple import list — includes all 16 core modules from `modules/`. This is passed as the second element in the `modules` list to `lib.evalModules` in `evalFlakeModule`.

### `modules/perSystem.nix`
The most important module. Defines:
- `systems`: List of system strings to enumerate
- `perSystem`: A deferred module option; each module defined here is evaluated per-system
- `allSystems`: Internal — `genAttrs config.systems config.perSystem`
- `perInput`: Function for system-specific input access (used by `inputs'` and `self'`)
- `getSystem` / `getSystemIgnoreWarning`: Module args for accessing per-system config
- Helpful error messages when `self`, `inputs`, `withSystem`, `moduleWithSystem` are accidentally used in perSystem scope

### `modules/transposition.nix`
Implements the `transposition` option that drives most of the automatic system-dimension handling. When `transposition.foo = {}` is defined, it wires:
- `flake.foo.${system} = (perSystem system).foo`
- `perInput = system: flake: flake.foo.${system}`

### `modules/nixpkgs.nix`
Special exception module that auto-provides `pkgs` in perSystem. Sets `_module.args.pkgs` to `inputs'.nixpkgs.legacyPackages` as a default-priority value (overridable by users).

## Code Organization Patterns

1. **Module arguments via `_module.args`**: Used to inject `withSystem`, `moduleWithSystem`, `getSystem`, `pkgs` into the module scope without declaring them as options.

2. **`mkTransposedPerSystemModule` pattern**: Standard approach for adding new transposed attributes. Used for packages, devShells, checks, apps, legacyPackages, bundlers.

3. **`mkPerSystemOption` for extending perSystem**: Used by withSystem.nix, formatter.nix, debug.nix to add options to the `perSystem` submodule.

4. **Deferred module types**: `perSystem` uses a deferred module type so that module definitions accumulate and are evaluated lazily per-system.

5. **`_file` annotations**: Every module that creates sub-modules sets `_file` to the declaring file path for accurate error messages.

6. **Error context via `builtins.addErrorContext`**: Wraps key evaluations (especially `inputs'`, `self'`) to give users helpful messages when an attribute is missing.

7. **Partitioned dev flake**: Dev-only attributes (`checks`, `devShells`, `herculesCI`) are in the `dev` partition, keeping the main flake evaluation light.
