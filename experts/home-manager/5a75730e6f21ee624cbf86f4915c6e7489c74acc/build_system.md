# Home Manager — Build System

## Build System Type

Home Manager uses **Nix** as its primary build system. The repository supports both legacy (non-flake) and modern flake-based Nix workflows.

### Primary Build Files

| File | Role |
|------|------|
| `flake.nix` | Primary entry point; all flake outputs (packages, modules, lib, templates) |
| `flake.lock` | Locked dependency versions for reproducible builds |
| `default.nix` | Non-flake entry point; mirrors flake outputs for legacy `nix-build` usage |
| `overlay.nix` | Nixpkgs overlay that adds `home-manager` to the package set |
| `Makefile` | Convenience wrapper for common development commands |
| `Justfile` | Additional task runner recipes |
| `treefmt.toml` | Multi-formatter configuration |
| `buildbot-nix.toml` | CI/CD pipeline configuration |

---

## External Dependencies

### Nix Flake Inputs (`flake.nix`)

```nix
inputs = {
  nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";  # Primary package set
  # (on release branches, this points to nixos-YY.MM)
};
```

Home Manager's only declared flake input is **nixpkgs**. All other dependencies are sourced from nixpkgs. The `flake.lock` file pins the exact commit of nixpkgs used.

### Runtime Dependencies (from nixpkgs)
The `home-manager` CLI script depends on:
- `bash` — Shell runtime for activation scripts
- `coreutils` — Standard Unix utilities used in activation
- `curl` / `wget` — For installer script
- `nix` — Nix package manager (the core engine)
- Various Nix utilities (`nix-env`, `nix build`, `nix profile`, etc.)

### Development/Documentation Dependencies (from nixpkgs)
- `mdbook` — Documentation builder
- `nixfmt-rfc-style` — Nix code formatter
- `prettier` — Markdown/JSON formatter
- `python3` — Used in test infrastructure and doc generation
- `gettext` — Internationalization (po/pot files)

---

## Build Targets and Commands

### Nix Flake Commands

```bash
# Build the home-manager CLI package
nix build github:nix-community/home-manager#home-manager

# Build for a specific system
nix build .#packages.x86_64-linux.home-manager
nix build .#packages.aarch64-darwin.home-manager

# Build the documentation
nix build .#packages.x86_64-linux.docs

# Open a development shell
nix develop

# Run a specific test
nix build .#legacyPackages.x86_64-linux.tests.programs.git

# Run all tests (as derivations)
nix build .#legacyPackages.x86_64-linux.tests
```

### Legacy Non-Flake Commands

```bash
# Build home-manager package
nix-build -A packages.x86_64-linux.home-manager

# Build docs
nix-build -A packages.x86_64-linux.docs

# Run tests
nix-build -A legacyPackages.x86_64-linux.tests
```

### Makefile Targets

```bash
make docs          # Build documentation
make fmt           # Format all Nix files
make fmt-check     # Check formatting without modifying
make tests         # Run module tests
```

### Formatting

The repository uses `treefmt` (configured in `treefmt.toml`) to run multiple formatters:
- **nixfmt-rfc-style**: All `.nix` files
- **prettier**: Markdown (`.md`) and JSON files

```bash
# Format all files
nix fmt

# Or via treefmt directly
treefmt
```

---

## How to Build

### Standalone Installation

```bash
# Using Nix flakes (recommended)
nix run home-manager/master -- init
nix run home-manager/master -- switch

# Or install the CLI
nix profile install github:nix-community/home-manager
home-manager init
home-manager switch
```

### NixOS Integration

Add to your NixOS `flake.nix`:
```nix
{
  inputs.home-manager.url = "github:nix-community/home-manager";

  outputs = { nixpkgs, home-manager, ... }: {
    nixosConfigurations.myhost = nixpkgs.lib.nixosSystem {
      modules = [
        home-manager.nixosModules.home-manager
        # your config...
      ];
    };
  };
}
```

Then build: `sudo nixos-rebuild switch`

### nix-darwin Integration

```nix
{
  inputs.home-manager.url = "github:nix-community/home-manager";
  inputs.nix-darwin.url = "github:LnL7/nix-darwin";

  outputs = { nix-darwin, home-manager, ... }: {
    darwinConfigurations.mymac = nix-darwin.lib.darwinSystem {
      modules = [
        home-manager.darwinModules.home-manager
        # your config...
      ];
    };
  };
}
```

Then build: `darwin-rebuild switch`

---

## Testing

### Test Framework

Tests use the **nmt** (Nix Module Tests) framework, which evaluates Home Manager modules and compares generated outputs against expected values.

### Running Tests

```bash
# Run all tests for a platform
nix build .#legacyPackages.x86_64-linux.tests

# Run specific test suite
nix build .#legacyPackages.x86_64-linux.tests.programs.git
nix build .#legacyPackages.x86_64-linux.tests.services.gpg-agent

# Integration tests
nix build .#legacyPackages.x86_64-linux.tests.integration
```

### Test Structure

Each test module in `tests/modules/` follows this pattern:
```nix
{ ... }:
{
  testScript = ''
    # Python test script assertions
  '';

  config = {
    programs.git = {
      enable = true;
      userName = "test";
      # ...
    };
  };

  # Expected file contents
  expected."home-files/.config/git/config".text = ''
    [user]
      name = test
  '';
}
```

### CI/CD

The repository uses **buildbot-nix** (configured in `buildbot-nix.toml`) for continuous integration. GitHub Actions workflows in `.github/workflows/` handle:
- PR checks (formatting, test runs)
- Automatic updates via Dependabot (`.github/dependabot.yml`)
- Documentation deployment

---

## Deployment

### Home Manager Switch (apply configuration)

```bash
# Apply current configuration
home-manager switch

# Build without applying
home-manager build

# Build and show what would change
home-manager build --dry-run
```

### Generation Management

```bash
# List generations
home-manager generations

# Roll back to previous generation
home-manager rollback

# Remove old generations
home-manager expire-generations "-30 days"
home-manager remove-generations <id>
```

### Development Workflow

```bash
# Enter development shell with all tools
nix develop

# Run formatter
nix fmt

# Build docs locally
nix build .#packages.x86_64-linux.docs
open result/share/doc/home-manager/index.html
```

---

## Flake Outputs Summary

```nix
outputs = {
  # User-facing API
  lib.<system>.homeManagerConfiguration = ...;  # Main configuration function

  # System integration modules
  nixosModules.home-manager = ...;
  darwinModules.home-manager = ...;
  flakeModules.home-manager = ...;  # flake-parts integration

  # Packages
  packages.<system>.home-manager = ...;  # CLI binary
  packages.<system>.docs = ...;          # HTML documentation

  # Flake templates
  templates.standalone = ...;
  templates.nixos = ...;
  templates."nix-darwin" = ...;

  # Tests (accessed via legacyPackages)
  legacyPackages.<system>.tests = ...;
};
```
