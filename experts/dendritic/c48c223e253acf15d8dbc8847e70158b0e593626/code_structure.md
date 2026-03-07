# The Dendritic Pattern — Code Structure

## Directory Tree

```
dendritic/                        # Repository root
├── README.md                     # Primary documentation — the pattern specification
├── LICENSE                       # License file
├── logo.jpg                      # Project logo
└── example/                      # Annotated example implementation
    ├── README.md                 # Example disclaimer ("this example is incomplete")
    ├── flake.nix                 # Entry point — the only non-module file in example/
    └── modules/                  # All non-entry-point files; every file is a flake-parts module
        ├── meta.nix              # Declares shared top-level options (e.g. `username`)
        ├── flake-parts.nix       # Imports the flake-parts `modules` flake module
        ├── systems.nix           # Declares supported systems for flake-parts
        ├── nixos.nix             # Provides the `configurations.nixos` option and wires flake outputs
        ├── admin.nix             # Feature: admin/wheel permissions across NixOS and nix-darwin
        ├── shell.nix             # Feature: default shell across NixOS and nix-on-droid
        └── desktop.nix           # Declares a concrete NixOS configuration named "desktop"
```

This is a small repository. It is **not** a library package — it is documentation of a pattern plus an annotated illustrative example.

## Module and Package Organization

The repository has no build artifacts, no packages, and no library code to install. Its value is entirely in:

1. **`README.md`** — the canonical description of the pattern.
2. **`example/`** — a working (though deliberately incomplete) demonstration.

Within `example/`, the organization follows the pattern's own rules:

- `flake.nix` is the sole entry point. It is **not** a module.
- Every `.nix` file under `modules/` is a flake-parts module. None of them call `lib.evalModules` or define a flake directly — they only contribute options and config values to the top-level flake-parts evaluation.

## Main Source Directories and Their Purposes

### `example/modules/` — Feature module directory

This is the only source directory in the repository. Each file demonstrates a distinct aspect of the Dendritic Pattern:

| File | Role in the pattern |
|---|---|
| `meta.nix` | Shared top-level option declaration (`username`). Shows how cross-cutting data is stored in the top-level config rather than passed via `specialArgs`. |
| `flake-parts.nix` | Infrastructure module that enables `flake-parts.flakeModules.modules`, which provides the `flake.modules` option namespace for storing lower-level `deferredModule` values. |
| `systems.nix` | Minimal flake-parts config setting `systems = ["x86_64-linux" "aarch64-linux"]`. Shows that even trivial configuration is its own module. |
| `nixos.nix` | Provides the `configurations.nixos` option (of type `lazyAttrsOf (submodule { options.module = deferredModule; })`). Wires `configurations.nixos` into `flake.nixosConfigurations` and `flake.checks`. |
| `admin.nix` | Feature module: sets `users.groups.wheel.members` on NixOS and `system.primaryUser` on nix-darwin using `config.username`. Demonstrates cross-platform feature implementation in a single file. |
| `shell.nix` | Feature module: enables fish shell on NixOS (accessing the evaluated `programs.fish.package`) and on nix-on-droid. Demonstrates using lower-level evaluated `config` values within a `deferredModule`. |
| `desktop.nix` | Configuration declaration module: uses `configurations.nixos.desktop.module` to assemble a NixOS configuration by importing named `deferredModule` values from `config.flake.modules.nixos`. |

## Key Files and Their Roles

### `README.md`

The central document. Contains:
- The problem statement (motivation for the pattern)
- The pattern definition (every file is a top-level module; single feature per file; file path = feature name)
- Benefits enumeration (known file type, automatic importing, file-path independence)
- Required skills (Nix language, Nixpkgs module system, `deferredModule` type)
- Anti-patterns section (specifically `specialArgs` pass-thru as the primary anti-pattern)
- Real-world examples (links to public infrastructure repos that have adopted the pattern)
- Community links (GitHub Discussions, Matrix room)

### `example/flake.nix`

The minimal entry point. Key properties:
- Declares three inputs: `flake-parts`, `import-tree`, `nixpkgs`
- The entire `outputs` is a single call: `inputs.flake-parts.lib.mkFlake { inherit inputs; } (inputs.import-tree ./modules)`
- No explicit imports list — `import-tree` collects all `.nix` files under `./modules` automatically
- Demonstrates that the entry point can be extremely terse under this pattern

### `example/modules/nixos.nix`

The most architecturally instructive module. Demonstrates:
- Defining a custom top-level option (`configurations.nixos`) typed as `lazyAttrsOf (submodule { options.module = deferredModule; })`
- Using the Nix pipe operator (`|>`) for list-to-attrset transformations
- Producing both `flake.nixosConfigurations` and `flake.checks` from a single option
- How lower-level configurations (`lib.nixosSystem`) are assembled from `deferredModule` values

### `example/modules/admin.nix` and `example/modules/shell.nix`

Feature modules. Demonstrate:
- Writing to `flake.modules.nixos.<name>` and `flake.modules.darwin.<name>` / `flake.modules.nixOnDroid.<name>` within a single file
- Accessing the top-level `config.username` option (defined in `meta.nix`) from within a feature module — no `specialArgs` needed
- Passing a lambda as a `deferredModule` value to access the lower-level evaluated config (e.g. `nixosArgs.config.programs.fish.package` in `shell.nix`)

### `example/modules/desktop.nix`

Configuration assembly module. Demonstrates:
- Referencing named `deferredModule` values via `config.flake.modules.nixos.*`
- Using `let inherit (config.flake.modules) nixos; in ...` to destructure for readability
- The pattern of a configuration declaration module being just another top-level module, indistinguishable in type from feature modules

## Code Organization Patterns

### The Core Rule

Every `.nix` file that is not an entry point follows exactly one template:

```nix
{ lib, config, inputs, ... }:
{
  # optional: options declarations
  options.<something> = lib.mkOption { ... };

  # optional: config contributions
  config.<something> = ...;

  # shorthand (no options declared):
  <something> = ...;
}
```

All files are syntactically Nixpkgs module system modules of the **same class** (the top-level flake-parts class). There is no ambiguity about what a file contains.

### The `deferredModule` Storage Pattern

Lower-level (NixOS, home-manager, nix-darwin) configuration fragments are stored as values of type `lib.types.deferredModule` under a shared namespace such as `flake.modules.nixos.<featureName>`. This is the key mechanism that allows:
- Feature modules to contribute to multiple lower-level configurations without knowing which configurations exist
- Configuration assembly modules to reference feature modules by name
- Merge semantics: multiple modules can contribute to `flake.modules.nixos.shell` and they merge correctly

### Automatic Importing

```nix
inputs.import-tree ./modules
```

This single expression replaces an explicit `imports = [ ./modules/meta.nix ./modules/shell.nix ... ]` list. As the codebase grows, no imports list needs updating. New files are automatically incorporated.

### Top-Level Option Namespace Design

Top-level options serve as a communication bus between modules. Examples from the repository:
- `username` (in `meta.nix`) — a shared constant readable by any module
- `configurations.nixos` (in `nixos.nix`) — the registry of NixOS configurations to build
- `flake.modules.nixos.*` (via `flake-parts.flakeModules.modules`) — the `deferredModule` store
