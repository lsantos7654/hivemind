# flake-parts APIs and Interfaces

## Public APIs and Entry Points

All public API is exported from the root `flake.nix` under `flake-parts.lib`:

```nix
flake-parts.lib.mkFlake         # Primary entry point
flake-parts.lib.evalFlakeModule # Lower-level evaluation
flake-parts.lib.mkPerSystemOption
flake-parts.lib.mkPerSystemType
flake-parts.lib.mkTransposedPerSystemModule
flake-parts.lib.mkSubmoduleOptions  # Deprecated
flake-parts.lib.mkDeferredModuleType  # Deprecated
flake-parts.lib.mkDeferredModuleOption  # Deprecated
flake-parts.lib.importApply
flake-parts.lib.importAndPublish
flake-parts.lib.memoizeStr
flake-parts.lib.deferredModuleWith   # Deprecated (internal use)
flake-parts.lib.defaultModule
flake-parts.lib.attrsWith            # Polyfill
flake-parts.lib.mkAliasOptionModule
```

Optional extra modules are exported as:
```nix
flake-parts.flakeModules.easyOverlay
flake-parts.flakeModules.flakeModules
flake-parts.flakeModules.modules
flake-parts.flakeModules.partitions
flake-parts.flakeModules.bundlers
```

---

## Core Functions

### `lib.mkFlake` — Primary Entry Point

**File**: `lib.nix:158`

```nix
mkFlake : { inputs, specialArgs?, self? } -> module -> AttrSet
```

The main function users call. Takes flake output arguments and a module, returns the evaluated flake outputs.

```nix
outputs = inputs@{ flake-parts, ... }:
  flake-parts.lib.mkFlake { inherit inputs; } {
    systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" "x86_64-darwin" ];
    perSystem = { pkgs, ... }: {
      packages.default = pkgs.hello;
    };
    flake = {
      nixosModules.my-module = ./module.nix;
    };
  };
```

### `lib.evalFlakeModule` — Lower-level Evaluation

**File**: `lib.nix:92`

```nix
evalFlakeModule : { inputs, specialArgs?, self?, moduleLocation? } -> module -> EvalResult
```

Returns the full `lib.evalModules` result (with `config`, `options`, `extendModules`). Used when you need access to the raw module system evaluation rather than just the flake outputs.

### `lib.importApply` — Import with Static Arguments

**File**: `lib.nix:280`

```nix
importApply : Path -> AttrSet -> Module
```

Imports a Nix module file with static arguments while preserving the module's `_file` location for error messages.

```nix
# In flake.nix or a flake-module.nix:
imports = [
  (flake-parts-lib.importApply ./my-module.nix { inherit someStaticArg; })
];
```

### `lib.importAndPublish` — Import and Publish as Flake Module

**File**: `lib.nix:293`

```nix
importAndPublish : String -> Module -> Module
```

Returns a module that both imports the given module AND exposes it as `flake.modules.flake.<name>`. Requires `flakeModules.modules` to also be imported.

```nix
imports = [
  (flake-parts-lib.importAndPublish "my-module" ./my-module.nix)
];
```

### `lib.mkPerSystemOption` — Extend perSystem Options

**File**: `lib.nix:218`

```nix
mkPerSystemOption : Module -> Option
```

Creates an option declaration that, when assigned to `options.perSystem`, merges the given module into the `perSystem` submodule. Used by library modules to add options to `perSystem`.

```nix
# In a library module:
options = {
  perSystem = flake-parts-lib.mkPerSystemOption {
    options.myTool.enable = lib.mkEnableOption "myTool";
    config = { ... };
  };
};
```

### `lib.mkTransposedPerSystemModule` — Create Transposed Attribute Module

**File**: `lib.nix:228`

```nix
mkTransposedPerSystemModule : { name: String, option: Option, file: Path } -> Module
```

Creates a complete flake-parts module that:
1. Declares `perSystem.<name>` with the given option
2. Declares `flake.<name>` as a lazy attrs-of that type, keyed by system
3. Wires transposition so perSystem values appear in flake outputs

```nix
# Example (from modules/packages.nix):
mkTransposedPerSystemModule {
  name = "packages";
  option = mkOption {
    type = types.lazyAttrsOf types.package;
    default = { };
  };
  file = ./packages.nix;
}
```

### `lib.memoizeStr` — String-keyed Memoization

**File**: `lib/memoize/memoize.nix:47`

```nix
memoizeStr : (String -> a) -> String -> a
```

Creates a memoized version of a string-to-value function using a trie data structure. Important: create the memoized function once (in a `let` binding) and reuse it; creating it multiple times wastes memory.

---

## Core Module Options

### Top-level Options

#### `systems` — List of Systems

**File**: `modules/perSystem.nix:73`

```nix
systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" "x86_64-darwin" ];
```

The list of system strings for which per-system attributes are enumerated. Controls which systems appear in `packages.<system>`, `devShells.<system>`, etc.

#### `perSystem` — Per-system Module

**File**: `modules/perSystem.nix:97`

```nix
perSystem = { config, system, pkgs, self', inputs', ... }: {
  packages.default = pkgs.hello;
  devShells.default = pkgs.mkShell { nativeBuildInputs = [ pkgs.git ]; };
  checks.test = pkgs.runCommand "test" {} "echo ok > $out";
};
```

A deferred module evaluated once per system in `systems`. Available module arguments:
- `system`: The current system string (`"x86_64-linux"`, etc.)
- `pkgs`: Nixpkgs package set for this system (auto-provided if `nixpkgs` input exists)
- `config`: The perSystem config for this system
- `self'`: System-specific attributes of the flake's own outputs
- `inputs'`: System-specific attributes of all flake inputs (e.g., `inputs'.nixpkgs.legacyPackages`)
- `lib`: nixpkgs lib

#### `flake` — System-agnostic Flake Outputs

**File**: `modules/flake.nix`

```nix
flake = {
  nixosModules.my-module = ./module.nix;
  nixosConfigurations.my-machine = inputs.nixpkgs.lib.nixosSystem { ... };
  overlays.default = final: prev: { };
  templates.my-template = { path = ./template; description = "..."; };
};
```

Freeform attribute set for system-agnostic flake outputs. Any attribute can be set here; declared options (like `overlays`, `nixosModules`) get proper type checking and merging.

#### `debug` — Debug Mode

**File**: `modules/debug.nix:23`

```nix
debug = true;
```

When true, exposes `debug`, `allSystems`, and `currentSystem` in flake outputs for inspection via `nix repl`.

#### `perInput` — Per-system Input Processing

**File**: `modules/perSystem.nix:83`

```nix
perInput = system: inputFlake: {
  myAttr = inputFlake.myAttr.${system};
};
```

Function to compute system-specific attributes from a flake input. Used to populate `inputs'` entries. Each module's `perInput` definitions are merged.

---

### Standard Flake Output Options

All defined in `modules/` and included by default.

| Option | Type | Description |
|--------|------|-------------|
| `perSystem.packages` | `lazyAttrsOf package` | Packages for `nix build .#<name>` |
| `perSystem.devShells` | `lazyAttrsOf package` | Shells for `nix develop .#<name>` |
| `perSystem.checks` | `lazyAttrsOf package` | Derivations for `nix flake check` |
| `perSystem.apps` | `lazyAttrsOf appType` | Apps for `nix run .#<name>` |
| `perSystem.formatter` | `nullOr package` | Formatter for `nix fmt` |
| `perSystem.legacyPackages` | `lazyAttrsOf raw` | Unmergeable packages (like nixpkgs) |
| `flake.overlays` | `lazyAttrsOf overlay` | Nixpkgs overlays |
| `flake.nixosModules` | `lazyAttrsOf deferredModule` | Reusable NixOS modules |
| `flake.nixosConfigurations` | `lazyAttrsOf raw` | Machine NixOS configurations |

The `apps` type expects:
```nix
apps.default = {
  type = "app";  # default, can be omitted
  program = "${config.packages.hello}/bin/hello";  # path or derivation with meta.mainProgram
  meta = { description = "say hello"; };  # optional
};
```

---

## Module Arguments Reference

### Top-level Module Arguments

Available in any top-level module (the module passed to `mkFlake`):

| Argument | Source | Description |
|----------|--------|-------------|
| `config` | module system | Top-level configuration |
| `options` | module system | Top-level option declarations |
| `lib` | nixpkgs-lib | Nixpkgs library |
| `inputs` | `evalFlakeModule` args | All flake inputs |
| `self` | `evalFlakeModule` args | The flake itself |
| `flake-parts-lib` | `lib.nix` | flake-parts library functions |
| `moduleLocation` | computed | Path to the flake.nix file |
| `withSystem` | `modules/withSystem.nix` | Access perSystem config |
| `moduleWithSystem` | `modules/moduleWithSystem.nix` | Bridge to NixOS modules |
| `getSystem` | `modules/perSystem.nix` | Access perSystem config (raw) |

### perSystem Module Arguments

Available inside `perSystem = { ... }:`:

| Argument | Source | Description |
|----------|--------|-------------|
| `config` | module system | perSystem configuration |
| `options` | module system | perSystem option declarations |
| `lib` | nixpkgs-lib | Nixpkgs library |
| `system` | specialArgs | Current system string |
| `pkgs` | `modules/nixpkgs.nix` | Nixpkgs package set |
| `self'` | `modules/perSystem.nix` | System-specific own outputs |
| `inputs'` | `modules/perSystem.nix` | System-specific input attrs |
| `flake-parts-lib` | top-level specialArg | flake-parts library |

**Note**: `self`, `inputs`, `withSystem`, `moduleWithSystem` are NOT available in perSystem scope (they throw helpful errors). Use `top@{ withSystem, ... }:` to capture them in the top-level, then access via `top.withSystem`.

---

## Integration Patterns and Workflows

### Pattern 1: Multi-module Flake

Split logic across files using `imports`:

```nix
# flake.nix
outputs = inputs@{ flake-parts, ... }:
  flake-parts.lib.mkFlake { inherit inputs; } {
    imports = [
      ./nix/packages.nix
      ./nix/devshell.nix
      ./nix/ci.nix
    ];
    systems = [ "x86_64-linux" "aarch64-darwin" ];
  };

# nix/packages.nix (a flake-module.nix)
{ pkgs, ... }: {
  perSystem = { pkgs, ... }: {
    packages.my-app = pkgs.callPackage ./my-app.nix {};
  };
}
```

### Pattern 2: withSystem — Access perSystem from Top-level

```nix
{ withSystem, ... }: {
  flake.nixosConfigurations.my-machine = inputs.nixpkgs.lib.nixosSystem {
    modules = [
      ./hardware-configuration.nix
      (withSystem "x86_64-linux" ({ config, pkgs, ... }:
        { environment.systemPackages = [ config.packages.my-app ]; }
      ))
    ];
  };
}
```

### Pattern 3: moduleWithSystem — Bridge to NixOS

```nix
{ moduleWithSystem, ... }: {
  flake.nixosModules.my-module = moduleWithSystem
    ({ config, pkgs, ... }:  # perSystem args
      { config, ... }:       # NixOS module args
      {
        services.my-service.package = config.packages.my-app;
      }
    );
}
```

### Pattern 4: Publishing a Reusable Module

```nix
# In your library flake:
{ flake-parts-lib, ... }: {
  imports = [
    (flake-parts-lib.importAndPublish "my-module" ./my-module.nix)
  ];
}

# Consumers import it as:
inputs = [ some-lib.flakeModules.my-module ]
# Or via the modules attribute:
inputs = [ some-lib.modules.flake.my-module ]
```

### Pattern 5: easyOverlay Extra Module

```nix
{ ... }: {
  imports = [ inputs.flake-parts.flakeModules.easyOverlay ];
  perSystem = { config, pkgs, ... }: {
    packages.my-pkg = pkgs.callPackage ./my-pkg.nix {};
    overlayAttrs = {
      my-pkg = config.packages.my-pkg;
    };
  };
  # consumers get: some-flake.overlays.default
}
```

### Pattern 6: Partitions for Dev/Prod Separation

```nix
{ ... }: {
  imports = [ inputs.flake-parts.flakeModules.partitions ];
  partitionedAttrs.checks = "dev";
  partitionedAttrs.devShells = "dev";
  partitions.dev = {
    extraInputsFlake = ./dev;   # ./dev/flake.nix has extra inputs
    module.imports = [ ./dev/flake-module.nix ];
  };
  # Main flake now doesn't fetch dev inputs when evaluating packages
}
```

### Pattern 7: Importing External Flake Modules

Many ecosystem modules expose a `flakeModule` or `flakeModules.default` attribute:

```nix
outputs = inputs@{ flake-parts, treefmt-nix, devenv, ... }:
  flake-parts.lib.mkFlake { inherit inputs; } {
    imports = [
      treefmt-nix.flakeModule        # uses flakeModules.default
      devenv.flakeModule
    ];
    # ...
  };
```

`flake-parts-lib.defaultModule` handles the `maybeFlake.flakeModules.default or maybeFlake` lookup automatically when a flake is passed.

---

## Configuration Extension Points

### Extending perSystem with Custom Options

Library modules that want to add options to perSystem use `mkPerSystemOption`:

```nix
# In your library's flake-module.nix:
{ flake-parts-lib, lib, ... }: {
  options.perSystem = flake-parts-lib.mkPerSystemOption {
    options.myLib.settings = lib.mkOption {
      type = lib.types.attrsOf lib.types.str;
      default = {};
    };
    config = { ... };
  };
}
```

### Adding New Transposed Output Types

```nix
{ flake-parts-lib, lib, ... }:
flake-parts-lib.mkTransposedPerSystemModule {
  name = "myOutputs";
  option = lib.mkOption {
    type = lib.types.lazyAttrsOf lib.types.raw;
    default = {};
  };
  file = ./my-module.nix;
}
```

### specialArgs for Custom Module Arguments

```nix
flake-parts.lib.mkFlake
  { inherit inputs; specialArgs = { myArg = "value"; }; }
  ({ myArg, ... }: {
    # myArg is available here
  });
```

### flake.modules — Multi-class Module Publishing

```nix
{ ... }: {
  imports = [ inputs.flake-parts.flakeModules.modules ];
  flake.modules = {
    nixos.my-service = ./nixos/my-service.nix;
    flake.my-flake-module = ./flake-module.nix;
    generic.my-util = ./util-module.nix;
  };
}
```
