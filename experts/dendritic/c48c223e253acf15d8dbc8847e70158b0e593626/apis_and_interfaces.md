# The Dendritic Pattern — APIs and Interfaces

## Overview

The Dendritic Pattern is an architectural convention, not a library with a published API. Its "API" consists of:

1. **Conventions** — rules about how files are structured and what they contain
2. **Option schemas** — how top-level options are declared for the communication bus
3. **Integration with external tools** — flake-parts, import-tree, and the Nixpkgs module system

All code snippets below are taken directly from `example/modules/` in the repository.

---

## Entry Point Interface

### `flake.nix` — The Minimal Entry Point

```nix
# example/flake.nix
{
  inputs = {
    flake-parts = {
      url = "github:hercules-ci/flake-parts";
      inputs.nixpkgs-lib.follows = "nixpkgs";
    };
    import-tree.url = "github:vic/import-tree";
    nixpkgs.url = "github:nixos/nixpkgs/25.11";
  };

  outputs =
    inputs:
    inputs.flake-parts.lib.mkFlake { inherit inputs; }
      (inputs.import-tree ./modules);
}
```

**Key interface point**: `inputs.import-tree ./modules` returns a list of all `.nix` files under `./modules` as import paths. This is passed directly to `flake-parts.lib.mkFlake` as the module list. This replaces an explicit `imports = [...]` list.

---

## Top-Level Option Declarations

Top-level options form the inter-module communication bus. Any module can declare new top-level options; any module can read from or write to existing top-level options.

### Declaring a Shared Constant Option

```nix
# example/modules/meta.nix
{ lib, ... }:
{
  options.username = lib.mkOption {
    type = lib.types.singleLineStr;
    readOnly = true;
    default = "iam";
  };
}
```

**Usage from any other module**:
```nix
{ config, ... }:
{
  # Read the username anywhere
  some.option = config.username;
}
```

This is the replacement for `specialArgs` pass-thru. Values are declared as options and read via `config.*`, not threaded through function arguments.

### Enabling the `flake.modules` Option Namespace

```nix
# example/modules/flake-parts.nix
{ inputs, ... }:
{
  imports = [
    # Provides the `flake.modules` option for storing deferredModule values
    inputs.flake-parts.flakeModules.modules
  ];
}
```

After this module is imported, the `flake.modules` option namespace is available to all other modules. See https://flake.parts/options/flake-parts-modules.html for the full option schema.

---

## Declaring Lower-Level Configuration Options

### The `configurations.nixos` Option Pattern

```nix
# example/modules/nixos.nix
{ lib, config, ... }:
{
  options.configurations.nixos = lib.mkOption {
    type = lib.types.lazyAttrsOf (
      lib.types.submodule {
        options.module = lib.mkOption {
          type = lib.types.deferredModule;
        };
      }
    );
  };

  config.flake = {
    nixosConfigurations = lib.flip lib.mapAttrs config.configurations.nixos (
      name: { module }: lib.nixosSystem { modules = [ module ]; }
    );

    checks =
      config.flake.nixosConfigurations
      |> lib.mapAttrsToList (
        name: nixos: {
          ${nixos.config.nixpkgs.hostPlatform.system} = {
            "configurations:nixos:${name}" = nixos.config.system.build.toplevel;
          };
        }
      )
      |> lib.mkMerge;
  };
}
```

**Key types used**:
- `lib.types.lazyAttrsOf` — lazy attribute set; configurations are only evaluated when accessed
- `lib.types.submodule` — each configuration entry is itself a mini-module with a `module` option
- `lib.types.deferredModule` — a module that is not evaluated immediately; its merge semantics allow multiple sources to contribute to the same module value

---

## Feature Module Interface

### Writing Feature Modules (the Core Pattern)

A feature module contributes lower-level module fragments for one feature across all relevant platforms. The `deferredModule` value may be an attrset, a function, or a list.

**Attrset form** (simple, no access to lower-level `config`):
```nix
# example/modules/admin.nix
{ config, ... }:
{
  flake.modules = {
    nixos.pc = {
      users.groups.wheel.members = [ config.username ];
    };

    darwin.pc.system.primaryUser = config.username;
  };
}
```

**Function form** (access to lower-level evaluated `config`):
```nix
# example/modules/shell.nix
{ config, lib, ... }:
{
  flake.modules = {
    # Lambda receives the lower-level NixOS module args
    nixos.pc = nixosArgs: {
      programs.fish.enable = true;
      users.users.${config.username}.shell = nixosArgs.config.programs.fish.package;
    };

    nixOnDroid.base =
      { pkgs, ... }:
      {
        user.shell = lib.getExe pkgs.fish;
      };
  };
}
```

**When to use the function form**: when the feature needs to read values from the lower-level configuration's own `config` (e.g. a package resolved inside NixOS's evaluation). The lambda receives the standard NixOS/home-manager/nix-darwin module arguments (`config`, `pkgs`, `lib`, `options`, etc.).

---

## Configuration Declaration Interface

### Assembling Configurations from Named Modules

```nix
# example/modules/desktop.nix
{ config, ... }:
let
  inherit (config.flake.modules) nixos;
in
{
  configurations.nixos.desktop.module = {
    imports = [
      nixos.admin   # references the deferredModule value set in admin.nix
      nixos.shell   # references the deferredModule value set in shell.nix
      # ...other `nixos` modules
    ];
    nixpkgs.hostPlatform = "x86_64-linux";
  };
}
```

**Key**: `config.flake.modules.nixos.<name>` resolves to the `deferredModule` value contributed by the feature module with that name. This allows the configuration assembly module to refer to features by name rather than by file path.

---

## Integration Patterns

### Pattern 1: Cross-Platform Feature

A single file sets a feature for all platforms where it applies:

```nix
{ config, lib, ... }:
{
  flake.modules = {
    nixos.myFeature = { pkgs, ... }: {
      # NixOS-specific config
      environment.systemPackages = [ pkgs.git ];
    };

    homeManager.myFeature = { pkgs, ... }: {
      # home-manager-specific config
      programs.git.enable = true;
    };

    darwin.myFeature = { pkgs, ... }: {
      # nix-darwin-specific config
      homebrew.casks = [ "some-app" ];
    };
  };
}
```

### Pattern 2: Cross-Cutting Constant

```nix
# In meta.nix or a similar file:
{ lib, ... }:
{
  options.myProject.domain = lib.mkOption {
    type = lib.types.str;
    default = "example.com";
  };
}

# Consumed by any feature module:
{ config, ... }:
{
  flake.modules.nixos.webServer = {
    services.nginx.virtualHosts.${config.myProject.domain} = { ... };
  };
}
```

### Pattern 3: Home-Manager Within NixOS

```nix
# A feature module contributes to both NixOS and home-manager:
{ config, ... }:
{
  flake.modules = {
    nixos.myUser = { config, ... }: {
      # Enable home-manager as a NixOS module
      home-manager.users.${config.username} = {
        imports = [ config.flake.modules.homeManager.myFeature ];
      };
    };

    homeManager.myFeature = {
      programs.tmux.enable = true;
    };
  };
}
```

---

## Configuration Options Reference

### System Declaration

```nix
# systems.nix
{
  systems = [
    "x86_64-linux"
    "aarch64-linux"
    "x86_64-darwin"
    "aarch64-darwin"
  ];
}
```

### NixOS Configuration Registration

```nix
configurations.nixos.<name>.module = <deferredModule>;
# Results in: flake.nixosConfigurations.<name> = lib.nixosSystem { modules = [module]; }
# Results in: flake.checks.<system>."configurations:nixos:<name>" = toplevel derivation
```

### Module Store Namespaces (via flake-parts.flakeModules.modules)

```nix
flake.modules.nixos.<featureName>        # NixOS deferredModule fragments
flake.modules.homeManager.<featureName>  # home-manager deferredModule fragments
flake.modules.darwin.<featureName>       # nix-darwin deferredModule fragments
flake.modules.nixOnDroid.<featureName>   # nix-on-droid deferredModule fragments
```

See https://flake.parts/options/flake-parts-modules.html for the complete `flake.modules` option schema.

---

## Extension Points

### Adding New Lower-Level Configuration Classes

The pattern extends to any Nixpkgs-module-system-based configuration system. To add support for a new system (e.g. `nixOnDroid`), follow the same pattern as `nixos.nix`:

```nix
{ lib, config, inputs, ... }:
{
  options.configurations.nixOnDroid = lib.mkOption {
    type = lib.types.lazyAttrsOf (
      lib.types.submodule {
        options.module = lib.mkOption {
          type = lib.types.deferredModule;
        };
      }
    );
  };

  config.flake.nixOnDroidConfigurations = lib.flip lib.mapAttrs config.configurations.nixOnDroid (
    name: { module }:
    inputs.nix-on-droid.lib.nixOnDroidConfiguration { modules = [ module ]; }
  );
}
```

### Adding New Top-Level Options

Any module can add new top-level options to the communication bus:

```nix
{ lib, ... }:
{
  options.myNamespace.someValue = lib.mkOption {
    type = lib.types.str;
    description = "A value shared across all feature modules";
  };
}
```

### Using `lib.evalModules` Directly (Without flake-parts)

The pattern does not require flake-parts. If using `lib.evalModules` directly:

```nix
# default.nix
{ pkgs ? import <nixpkgs> {} }:
let
  topLevel = pkgs.lib.evalModules {
    modules = import-tree ./modules;  # or explicit list
  };
in
topLevel.config.output
```
