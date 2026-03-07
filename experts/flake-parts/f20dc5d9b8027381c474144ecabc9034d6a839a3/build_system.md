# flake-parts Build System

## Build System Type

`flake-parts` is a **pure Nix project** — the only build system is Nix itself. There are no Makefiles, Cargo.toml, package.json, or other language-specific build files. Everything is managed through Nix flakes.

The project uses a two-flake architecture:
- **Root flake** (`flake.nix`): Production library, minimal inputs
- **Dev flake** (`dev/flake.nix`): Development tooling, CI, heavy inputs — loaded only via the `partitions` module

## Configuration Files

| File | Purpose |
|------|---------|
| `flake.nix` | Root flake — declares `nixpkgs-lib` as sole input, exports lib/templates/flakeModules |
| `flake.lock` | Locks `nixpkgs-lib` (and indirectly nixpkgs for evals) |
| `dev/flake.nix` | Dev flake — depends on `pre-commit-hooks-nix`, `hercules-ci-effects`, `nixpkgs` |
| `dev/flake.lock` | Locks dev-only inputs |
| `shell.nix` | Legacy `nix-shell` entry point for pre-commit hooks |
| `bors.toml` | Bors merge bot configuration (CI gating) |

## External Dependencies

### Production Dependencies

Only one flake input in the root flake:

```nix
inputs = {
  nixpkgs-lib.url = "github:nix-community/nixpkgs.lib";
};
```

- **nixpkgs-lib**: A lightweight flake providing only the `lib` attribute from Nixpkgs. This is used instead of full Nixpkgs to minimize closure size for consumers who only need the library. Minimum supported version: 23.05 (checked at evaluation time in `lib.nix`).

### Vendored Dependency

- **flake-compat** (vendored at `vendor/flake-compat/`): Used internally by the `partitions` extra module to load path-based flakes in pure evaluation mode. Vendoring avoids adding it as a flake input, keeping the root flake minimal.

### Development Dependencies (dev/flake.lock)

- **nixpkgs**: Full Nixpkgs for building checks, dev shells
- **pre-commit-hooks-nix**: Pre-commit hooks (runs `nixpkgs-fmt` on commit)
- **hercules-ci-effects**: Provides `herculesCI` flake attribute, Hercules CI integration, automated flake updates

## Build Targets

### Packages

The root flake does not define any packages — it is a pure library. The dev partition defines:

```
nix build .#checks.x86_64-linux.eval-tests    # Pure evaluation test suite
```

### Checks

Run with `nix flake check` (requires building the dev partition):

```
nix build .#checks.x86_64-linux.eval-tests
```

The `eval-tests` check (`dev/tests/eval-tests.nix`) is a pure Nix evaluation test — it does not invoke any builders. It runs a series of `assert` statements verifying the behavior of `mkFlake`, `perSystem`, overlays, bundlers, `flakeModules`, `partitions`, `nixosModules`, and other features. The test is implemented as a Nix file that, when evaluated, returns a string `"ok"` if all assertions pass.

### Dev Shell

```
nix develop        # or: nix-shell
```

Provides:
- `nixpkgs-fmt` — Nix formatter
- `hci` — Hercules CI CLI
- Pre-commit hooks (`nixpkgs-fmt` on staged Nix files)

### Templates

```
nix flake init -t github:hercules-ci/flake-parts                   # default template
nix flake init -t github:hercules-ci/flake-parts#multi-module       # multi-module
nix flake init -t github:hercules-ci/flake-parts#unfree             # nixpkgs with unfree
nix flake init -t github:hercules-ci/flake-parts#package            # package + test
```

## How to Build, Test, and Deploy

### Testing Locally

The primary test suite is `dev/tests/eval-tests.nix`, which is a pure evaluation test:

```bash
# Run as a Nix build check
nix build .#checks.x86_64-linux.eval-tests

# Or run in nix repl for interactive testing
nix repl
nix-repl> :lf .
nix-repl> checks.x86_64-linux.eval-tests.internals
```

The test file is loaded by `dev/flake-module.nix`:
```nix
checks.eval-tests =
  let tests = import ./tests/eval-tests.nix { flake-parts = self; };
  in tests.runTests pkgs.emptyFile // { internals = tests; };
```

Template smoke tests are at `dev/tests/template.nix` and run as Hercules CI effects (not regular checks).

### Running Pre-commit Hooks

```bash
nix-shell   # installs pre-commit hooks
# or
nix develop
# then commit — nixpkgs-fmt runs automatically
```

### Formatting

`nixpkgs-fmt` is the formatter. Run manually:
```bash
nixpkgs-fmt **/*.nix
```

Or via the pre-commit hook automatically on `git commit`.

### CI (Hercules CI via hercules-ci.com)

The project uses Hercules CI for automated testing. Key CI configuration in `dev/flake-module.nix`:
- `checks.eval-tests`: Primary test suite
- `hercules-ci.flake-update`: Automated monthly flake input updates (1st of month), auto-merged

### Consuming the Library (Consumer Build Pattern)

Consumers add flake-parts as an input and call `mkFlake`:

```nix
# flake.nix
{
  inputs = {
    flake-parts.url = "github:hercules-ci/flake-parts";
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = inputs@{ flake-parts, ... }:
    flake-parts.lib.mkFlake { inherit inputs; } {
      systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" "x86_64-darwin" ];
      perSystem = { pkgs, ... }: {
        packages.default = pkgs.hello;
      };
    };
}
```

### Overriding nixpkgs-lib

If a consumer wants to use a specific nixpkgs-lib version:

```nix
inputs.flake-parts.inputs.nixpkgs-lib.follows = "nixpkgs";
```

This is a common pattern to ensure consistent lib versions across inputs. The minimum supported version is 23.05; using an older version will produce an `abort` message at evaluation time.

## Architecture Note: Partitions and Dev Inputs

The root flake uses the `partitions` extra module to keep dev inputs out of the main evaluation:

```nix
imports = [ flakeModules.partitions ];
partitionedAttrs.checks = "dev";
partitionedAttrs.devShells = "dev";
partitionedAttrs.herculesCI = "dev";
partitions.dev.extraInputsFlake = ./dev;
partitions.dev.module = { imports = [ ./dev/flake-module.nix ]; };
```

This means:
- Evaluating `flake-parts.lib` does **not** require fetching `nixpkgs`, `pre-commit-hooks-nix`, or `hercules-ci-effects`
- Only evaluating `checks`, `devShells`, or `herculesCI` triggers the dev partition and fetches those inputs
- The vendored `flake-compat` is needed to load `./dev` as a flake in pure mode
