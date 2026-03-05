# nix.dev — Build System

## Build System Type

nix.dev uses a **Nix-native build system** as its primary build mechanism, with a **Makefile** as a convenience wrapper for Sphinx commands. The Nix build is the source of truth for reproducible builds and CI/CD; the Makefile is used for local development iteration.

### Configuration Files

| File | Role |
|------|------|
| `default.nix` | Top-level Nix build entry — defines all derivations |
| `shell.nix` | Development shell — thin wrapper around `default.nix` |
| `nix/default.nix` | Inner Nix build logic |
| `nix/inputs.nix` | Pinned source inputs (nixpkgs, Nix releases, Nixpkgs releases) |
| `nix/releases.nix` | Multi-version release derivation builder |
| `nix/overlay.nix` | Custom nixpkgs package overrides |
| `nix/tex-env.nix` | LaTeX environment for PDF output |
| `nix/nix-versions.json` | Pinned Nix release versions |
| `nix/sources.json` | Pinned Nixpkgs release sources (npins format) |
| `npins/sources.json` | npins lockfile for top-level dependencies |
| `Makefile` | Sphinx build commands (convenience wrapper) |
| `netlify.toml` | Netlify deployment and redirect configuration |
| `runtime.txt` | Python version pin (`3.7`) for Netlify |

## External Dependencies and Management

### Nix Dependencies (Pinned via npins/nix/)

All build dependencies are pinned for reproducibility:

```
nixpkgs-rolling          # Current unstable Nixpkgs (main build environment)
nix-2.18, nix-2.19, ... # Multiple Nix release versions (for manuals)
nixpkgs-23.05, ...       # Multiple Nixpkgs releases (for version-specific docs)
```

Pins are managed with **npins** and updated via:
```bash
nix-build nix/update-nix-releases.nix
nix-build nix/update-nixpkgs-releases.nix
```

### Python Dependencies (from default.nix)

Resolved through nixpkgs, all version-pinned by the Nix derivation:

| Package | Purpose |
|---------|---------|
| `sphinx` | Core documentation builder |
| `sphinx-book-theme` | Visual theme (book-style layout) |
| `myst-parser` | MyST Markdown parser for Sphinx |
| `sphinx-copybutton` | Adds copy button to code blocks |
| `sphinx-design` | Tabs, grids, cards, badges |
| `sphinx-notfound-page` | Custom 404 page |
| `sphinx-sitemap` | Automatic sitemap.xml generation |
| `linkify-it-py` | Auto-linkify URLs in MyST content |

### LaTeX Dependencies (for PDF output)

Assembled in `nix/tex-env.nix`:
- `texlive` (custom subset: base, xetex, xelatex, latexmk, fancyhdr, etc.)
- `gnu-freefont` (fonts for PDF rendering)
- `latexmk` (LaTeX build automation)
- `perl` (required by latexmk)

### Infrastructure Dependencies

| Service | Purpose |
|---------|---------|
| Netlify | Site hosting, PR previews, redirect proxy |
| Cachix (`nix-dev` cache) | Binary cache for Nix build outputs |
| GitHub Actions | CI/CD pipeline |
| Vale | Documentation style linter |

## Build Targets and Commands

### Nix Build (Primary — Reproducible)

**Build the HTML documentation:**
```bash
nix-build
# Output: ./result/  (symlink to Nix store path)
# Produces: HTML site ready for deployment
```

**Build with Nix manuals included:**
```bash
nix-build --arg withManuals true
# Downloads and integrates upstream Nix reference manuals
# Used in production CI/CD
```

**Access the development shell:**
```bash
nix-shell
# or with direnv:
direnv allow  # auto-loads on cd if .envrc present
```

**Start the live-reload development server:**
```bash
nix-shell --run devmode
# or inside nix-shell:
devmode
# Serves at http://localhost:8080 with auto-rebuild on changes
```

**Update version pins:**
```bash
nix-build nix/update-nix-releases.nix -A update && ./result/bin/update-nix-releases
nix-build nix/update-nixpkgs-releases.nix -A update && ./result/bin/update-nixpkgs-releases
```

### Makefile Targets (Sphinx Convenience Wrappers)

All Makefile targets must be run inside `nix-shell`:

```bash
# Build HTML documentation (primary target)
make html

# Check documentation syntax without full build (fast)
make dummy

# Validate all external hyperlinks
make linkcheck

# Build PDF via LaTeX (requires LaTeX environment)
make latexpdf
make latex  # intermediate step

# Build EPUB
make epub
make epub3

# Build man pages
make man

# Build JSON output
make json

# Clean build artifacts
make clean
```

The Makefile sets `-W` (warnings as errors) for the `html` target, ensuring documentation quality is enforced at build time.

### Test Commands

**Run extracted code block tests:**
```bash
./run_code_block_tests.sh
# Finds all test_* files in build/extracted/*/
# Executes each as a shell script
# Requires: nix-shell environment
```

**Syntax-only build (CI fast path):**
```bash
make dummy
# Runs Sphinx in "dummy" builder mode
# Fast syntax/reference check without generating output files
```

**Style linting:**
```bash
vale source/
# Requires Vale installed (available in nix-shell)
```

## How to Build

### First-Time Setup

1. Install Nix: follow the guide at https://nix.dev/install-nix
2. Clone the repository:
   ```bash
   git clone https://github.com/NixOS/nix.dev
   cd nix.dev
   ```
3. (Optional) Enable direnv for automatic shell loading:
   ```bash
   direnv allow
   ```

### Local Development Build

```bash
# Enter development environment
nix-shell

# Start live-reload preview server
devmode
# Open http://localhost:8080 in browser

# Or build static HTML
make html
# Open _build/html/index.html
```

### Production Build

```bash
# Full build with Nix manuals (as used in CI)
nix-build --arg withManuals true

# Inspect output
ls result/
```

## CI/CD Pipeline

### GitHub Actions Workflows

**`.github/workflows/test.yml`** — Code block tests (runs on every PR and push to master):
1. Install Nix (using `cachix/install-nix-action`)
2. Configure Cachix binary cache (`nix-dev`)
3. Run `make dummy` (syntax check)
4. Run `./run_code_block_tests.sh` (code example tests)

**`.github/workflows/build-and-deploy.yml`** — Full build and deployment:
1. Install Nix + configure Cachix
2. Run `nix-build --arg withManuals true`
3. On `master` push: deploy to Netlify production
4. On PR: deploy to Netlify preview URL

**`.github/workflows/vale.yml`** — Documentation style:
1. Run Vale against `source/` directory
2. Report style violations as PR annotations

**`.github/workflows/editorconfig.yml`** — Format validation:
1. Run `editorconfig-checker` against all files

**`.github/workflows/update-nix-releases.yml`** — Scheduled maintenance:
1. Runs on a schedule
2. Updates `nix/nix-versions.json` with new Nix releases
3. Opens a PR with the changes

### Deployment (Netlify)

Production deployments go to `https://nix.dev`. The `netlify.toml` configures:

- **Proxy redirects**: `/manual/nix/unstable/*` → upstream Hydra HTML builds
- **Proxy redirects**: `/manual/nix/stable/*` → version-pinned Hydra builds
- **Custom headers**: tracking/analytics injection
- **PR previews**: automatically generated for every pull request

The site is served as a static HTML site with Netlify handling all redirects and proxying.
