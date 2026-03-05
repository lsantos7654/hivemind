# nix.dev — Repository Summary

## Purpose and Goals

**nix.dev** is the official documentation hub for the Nix ecosystem, maintained by the NixOS Foundation's documentation team. Its primary goal is to provide high-quality, structured, and reproducible documentation that helps users "get things done with Nix." The project covers everything from beginner onboarding to advanced system administration topics using Nix, Nixpkgs, and NixOS.

The documentation aims to be the canonical learning resource for the entire Nix ecosystem, replacing fragmented community wikis and scattered guides with authoritative, well-organized, and peer-reviewed content.

## Key Features and Capabilities

- **Diataxis-structured content**: Documentation is organized into four quadrants — Tutorials (learning-oriented), Guides (task-oriented), Reference (information-oriented), and Concepts (explanation-oriented) — following the Diataxis documentation framework.
- **MyST Markdown**: Content is written in MyST (Markedly Structured Text), a superset of CommonMark that enables rich semantic markup including tabs, grids, admonitions, cross-references, and code block extraction.
- **Extractable and testable code blocks**: A custom Sphinx extension (`extractable_code_block.py`) extracts code examples into files that are run as CI tests, ensuring documentation examples remain correct.
- **Multi-version Nix manual**: The site integrates and proxies multiple versions of the upstream Nix reference manual via Netlify redirects, making versioned documentation available at a single URL.
- **Reproducible builds**: All build dependencies are pinned using Nix and npins, ensuring identical builds across machines and time.
- **PR preview deployments**: Every pull request gets a live Netlify preview URL for reviewing changes before merge.
- **Style linting**: Vale is used to enforce consistent writing quality and documentation standards.

## Primary Use Cases and Target Audience

The site serves a broad audience within the Nix community:

- **Beginners** learning Nix for the first time via First Steps tutorials
- **Developers** setting up reproducible development environments with `nix-shell` and flakes
- **DevOps/SRE engineers** integrating Nix into CI/CD pipelines (GitHub Actions, Cachix)
- **System administrators** managing NixOS systems, distributed builds, and remote provisioning
- **Package maintainers** learning to package existing software and manage dependencies
- **Researchers and scientists** seeking reproducible computational environments
- **Documentation contributors** who need guidelines for writing and maintaining content

## High-Level Architecture Overview

The repository is a Sphinx documentation project with a Nix-native build system:

```
Content Layer (source/)
  └── MyST Markdown files organized by Diataxis quadrant

Build Layer
  ├── Sphinx + sphinx-book-theme (HTML generation)
  ├── Makefile (build orchestration)
  └── default.nix (reproducible Nix build with all Python dependencies)

Extension Layer (source/_ext/)
  └── extractable_code_block.py (custom Sphinx extension for testable code)

Release Management (nix/)
  ├── inputs.nix (pinned Nix/Nixpkgs versions)
  ├── releases.nix (multi-version release logic)
  └── nix-versions.json / sources.json (version pins)

Deployment Layer
  ├── Netlify (hosting with redirects and PR previews)
  └── GitHub Actions (CI: build, test, style check, deploy)
```

The build produces a static HTML site (and optionally PDF/EPUB) deployable to Netlify. When `withManuals = true`, it also incorporates pre-built Nix reference manuals fetched from Hydra.

## Related Projects and Dependencies

**Upstream Nix ecosystem:**
- [NixOS/nix](https://github.com/NixOS/nix) — The Nix package manager (reference manual sourced from here)
- [NixOS/nixpkgs](https://github.com/NixOS/nixpkgs) — The Nix packages collection
- [NixOS/nixos-homepage](https://github.com/NixOS/nixos-homepage) — The main NixOS website

**Build and documentation tools:**
- [Sphinx](https://www.sphinx-doc.org/) — Documentation builder
- [sphinx-book-theme](https://sphinx-book-theme.readthedocs.io/) — The site's visual theme
- [myst-parser](https://myst-parser.readthedocs.io/) — MyST Markdown parser for Sphinx
- [sphinx-copybutton](https://sphinx-copybutton.readthedocs.io/) — Copy button for code blocks
- [sphinx-design](https://sphinx-design.readthedocs.io/) — Grid/card/tab layout components
- [sphinx-notfound-page](https://sphinx-notfound-page.readthedocs.io/) — Custom 404 page
- [sphinx-sitemap](https://sphinx-sitemap.readthedocs.io/) — Sitemap generation
- [Vale](https://vale.sh/) — Documentation style linter

**Infrastructure:**
- [Netlify](https://netlify.com/) — Hosting and PR preview deployments
- [Cachix](https://cachix.org/) — Nix binary cache (`nix-dev` cache)
- [GitHub Actions](https://github.com/features/actions) — CI/CD pipeline
- [npins](https://github.com/andir/npins) — Nix dependency pinning
