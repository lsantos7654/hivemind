# nix.dev — Code Structure

## Annotated Directory Tree

```
repo/
├── .github/                         # GitHub CI/CD configuration
│   ├── ISSUE_TEMPLATE/              # GitHub issue templates
│   └── workflows/                   # GitHub Actions workflows
│       ├── build-and-deploy.yml     # Full site build and Netlify deployment
│       ├── test.yml                 # Code block extraction and syntax tests
│       ├── editorconfig.yml         # EditorConfig format validation
│       ├── vale.yml                 # Vale documentation style linting
│       └── update-nix-releases.yml  # Scheduled Nix version updates
│
├── nix/                             # Nix build configuration
│   ├── default.nix                  # Main Nix build derivation entry
│   ├── inputs.nix                   # Pinned upstream sources (nixpkgs, Nix releases)
│   ├── overlay.nix                  # Custom nixpkgs overlay
│   ├── releases.nix                 # Multi-version release management logic
│   ├── tex-env.nix                  # LaTeX/XeTeX environment for PDF output
│   ├── update-nix-releases.nix      # Script to update Nix version pins
│   ├── update-nixpkgs-releases.nix  # Script to update Nixpkgs version pins
│   ├── nix-versions.json            # Pinned Nix release version list
│   └── sources.json                 # Pinned Nixpkgs release sources (npins format)
│
├── npins/                           # npins lockfiles
│   ├── default.nix                  # npins Nix integration
│   └── sources.json                 # Pinned source versions for npins
│
├── source/                          # All documentation content (MyST Markdown)
│   ├── conf.py                      # Sphinx configuration (central config file)
│   ├── index.md                     # Site homepage (root toctree)
│   ├── install-nix.md               # Nix installation guide
│   ├── recommended-reading.md       # External learning resources
│   ├── robots.txt                   # Search engine instructions
│   ├── favicon.png                  # Site favicon
│   │
│   ├── _ext/                        # Custom Sphinx extensions (Python)
│   │   └── extractable_code_block.py  # Extracts code blocks to files for CI testing
│   │
│   ├── _static/                     # Static assets (not processed by Sphinx)
│   │   ├── css/                     # Custom CSS overrides for the theme
│   │   ├── img/                     # Documentation images (PNG/SVG)
│   │   └── _img/                    # Original/source images
│   │
│   ├── _templates/                  # Jinja2 Sphinx HTML templates
│   │   └── (sidebar, layout overrides)
│   │
│   ├── tutorials/                   # Diataxis: Learning-oriented content
│   │   ├── index.md                 # Tutorials landing page
│   │   ├── nix-language.md          # Comprehensive Nix language tutorial
│   │   ├── packaging-existing-software.md  # How to package software
│   │   ├── callpackage.md           # callPackage pattern tutorial
│   │   ├── working-with-local-files.md     # Local file handling
│   │   ├── cross-compilation.md     # Cross-compilation with Nix
│   │   ├── first-steps/             # Beginner tutorial series
│   │   │   ├── index.md             # First steps landing page
│   │   │   ├── ad-hoc-shell-environments.md   # nix-shell one-liners
│   │   │   ├── declarative-shell.md            # shell.nix basics
│   │   │   ├── reproducible-scripts.md         # Reproducible scripts
│   │   │   └── towards-reproducibility-pinning-nixpkgs.md  # Pinning
│   │   ├── module-system/           # NixOS module system tutorial series
│   │   │   ├── index.md
│   │   │   ├── deep-dive.md         # In-depth module system walkthrough
│   │   │   └── a-basic-module/      # Worked example
│   │   │       ├── index.md
│   │   │       └── default.nix      # Example module source
│   │   └── nixos/                   # NixOS-specific tutorials
│   │       ├── index.md
│   │       ├── integration-testing-using-virtual-machines.md
│   │       ├── installing-nixos-on-a-raspberry-pi.md
│   │       ├── provisioning-remote-machines.md
│   │       └── distributed-builds-setup.md
│   │
│   ├── guides/                      # Diataxis: Task-oriented content
│   │   ├── index.md                 # Guides landing page
│   │   ├── best-practices.md        # Nix ecosystem best practices
│   │   ├── troubleshooting.md       # Common problems and fixes
│   │   ├── faq.md                   # Frequently asked questions
│   │   └── recipes/                 # Practical how-to recipes
│   │       ├── index.md
│   │       ├── direnv.md            # Automatic shell environments with direnv
│   │       ├── dependency-management.md  # Managing dependencies
│   │       ├── sharing-dependencies.md   # Cross-project dependency sharing
│   │       ├── add-binary-cache.md       # Configuring binary caches
│   │       ├── continuous-integration-github-actions.md  # CI setup
│   │       ├── post-build-hook.md        # Post-build hook configuration
│   │       └── python-environment.md     # Python development with Nix
│   │
│   ├── reference/                   # Diataxis: Information-oriented content
│   │   ├── index.md                 # Reference landing page
│   │   ├── glossary.md              # Nix ecosystem terminology
│   │   ├── nix-manual.md            # Links to versioned Nix reference manuals
│   │   └── pinning-nixpkgs.md       # Reference for Nixpkgs pinning strategies
│   │
│   ├── concepts/                    # Diataxis: Explanation-oriented content
│   │   ├── index.md                 # Concepts landing page
│   │   ├── flakes.md                # Explanation of Nix flakes
│   │   └── faq.md                   # Conceptual FAQ
│   │
│   ├── contributing/                # Contributor documentation
│   │   ├── index.md                 # Contributing landing page
│   │   ├── how-to-contribute.md     # Contribution workflow
│   │   ├── how-to-get-help.md       # Getting help as a contributor
│   │   └── documentation/           # Docs-specific contribution guides
│   │       ├── index.md
│   │       ├── diataxis.md          # Diataxis framework explanation
│   │       ├── style-guide.md       # Writing style rules
│   │       ├── writing-a-tutorial.md  # How to write tutorials
│   │       └── resources.md         # Writing resources
│   │
│   └── acknowledgements/
│       └── index.md                 # Project acknowledgements
│
├── vale/                            # Vale style linter configuration
│   ├── Style/                       # Custom Vale style rules
│   └── config/                      # Vale configuration
│
├── maintainers/                     # Maintainer-specific documentation
│   └── this-month-in-nix-docs/      # Monthly docs update log
│
├── Makefile                         # Sphinx build orchestration
├── default.nix                      # Top-level Nix build entry point
├── shell.nix                        # Development shell (wraps default.nix)
├── netlify.toml                     # Netlify deployment + redirect configuration
├── run_code_block_tests.sh          # Shell script: runs extracted code block tests
├── runtime.txt                      # Python version pin (3.7, for Netlify)
├── .editorconfig                    # Editor formatting rules
├── .vale.ini                        # Vale linter configuration
├── .envrc                           # direnv: auto-loads Nix development shell
├── .imgbotconfig                    # Image optimization bot settings
├── .git-blame-ignore-revs           # Git blame ignore list
├── _redirects                       # Cloudflare/Netlify redirect rules
├── CONTRIBUTING.md                  # Contribution guidelines
├── LICENSE.md                       # CC-BY-SA 4.0 license
└── README.md                        # Project overview
```

## Module and Package Organization

### Python Source (source/_ext/)

The only Python source code in the repository is the custom Sphinx extension:

**`source/_ext/extractable_code_block.py`**
- Defines `ExtractableCodeBlock`, a subclass of Sphinx's built-in `CodeBlock` directive
- Intercepts code blocks with a filename argument (e.g., ` ```python test_example.py`)
- Writes the code to `<builddir>/extracted/<docname>/<filename>` during the build
- Makes `.sh` files executable (chmod +x)
- Registered with Sphinx as `extractable-code-block` directive
- Enables CI testing of documentation examples

### Nix Build Modules (nix/)

**`nix/inputs.nix`** — Source pinning
- Fetches the main `nixpkgs-rolling` tarball
- Imports all pinned Nix release versions from `nix-versions.json`
- Imports all pinned Nixpkgs releases from `sources.json`
- Returns an attrset of all available inputs

**`nix/releases.nix`** — Multi-version release logic
- Accepts inputs and generates derivations for each Nix/Nixpkgs version
- Handles symlink creation for `/latest` and `/stable` aliases
- Integrates with Netlify redirect generation

**`nix/overlay.nix`** — Custom nixpkgs overlay
- Overrides or adds packages needed for the build
- Ensures consistent Python package versions

**`nix/tex-env.nix`** — LaTeX environment
- Assembles a minimal TeXLive environment with required packages for PDF generation
- Uses `xelatex` and `latexmk`

### Sphinx Configuration (source/conf.py)

The 462-line Sphinx configuration is the central control file for the documentation build:

- **Extensions loaded**: `myst_parser`, `sphinx_copybutton`, `sphinx_design`, `sphinx_book_theme`, `sphinx_sitemap`, `sphinx_notfound_page`, and local `extractable_code_block`
- **MyST features**: Colon fencing, linkify, task lists, `attrs_block`, `header-anchors` (3 levels)
- **Code block settings**: Copy button configured to strip shell prompts (`$`, `#`, `nix-repl>`)
- **HTML theme**: `sphinx_book_theme` with custom sidebar, repository links, and icon buttons
- **Linkcheck**: Skip patterns for GitHub anchors, SPA sites, and dynamically generated content
- **Sitemap**: Auto-generated at build time

## Code Organization Patterns

1. **Content-as-code**: All documentation is version-controlled Markdown, treated the same as source code
2. **Diataxis quadrants**: Strict organizational hierarchy — tutorials, guides, reference, concepts — prevents content sprawl
3. **Reproducible builds**: No implicit dependencies; everything pinned via Nix or npins
4. **Test-driven docs**: Code examples are extracted and tested in CI, treating documentation correctness as a first-class concern
5. **Separation of concerns**: Content (`source/`), build logic (`nix/`, `Makefile`), deployment (`netlify.toml`, `.github/workflows/`), and tooling (`vale/`, `.editorconfig`) are clearly separated
6. **Minimal custom code**: Only one custom Python module; the rest is configuration and content
