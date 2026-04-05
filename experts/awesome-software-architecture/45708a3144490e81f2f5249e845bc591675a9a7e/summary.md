# Awesome Software Architecture — Repository Summary

## Repository Purpose and Goals

**Awesome Software Architecture** (by Mehdi Hadeli, GitHub: `mehdihadeli/awesome-software-architecture`) is a continuously-updated, community-driven curated list of articles, books, videos, GitHub repositories, and tools covering the full spectrum of software architecture, design patterns, and engineering principles. The project's mission is to be the single canonical reference point for software architects and engineers seeking high-quality learning resources.

The official companion website is published at **https://awesome-architecture.com** using MkDocs with the Material theme, and the source of truth lives in the GitHub repository. The list is licensed under CC0 1.0 (public domain), meaning anyone can freely use and redistribute its contents.

## Key Features and Capabilities

- **Breadth of coverage**: Over 80 distinct topic areas spanning architectural styles (Clean, Onion, Hexagonal, Vertical Slice, Microservices, SOA, Modular Monolith, Actor Model), design principles (SOLID, DRY, KISS, YAGNI, GRASP, CAP Theorem), design patterns (GoF patterns, Cloud Design Patterns, messaging patterns), cloud platforms (Azure), DevOps tooling, databases, messaging systems, and AI/ML architecture.
- **MkDocs website**: All markdown content in `docs/` is rendered as a full-featured documentation site at awesome-architecture.com, using the MkDocs Material theme with dark/light mode, instant navigation, and integrated table of contents.
- **Release notes tooling**: A C# (.NET 9) program (`Program.cs`, `ReleaseNotes.csproj`) that parses `git diff` output to automatically extract and format added/removed resources from markdown files — useful for generating changelogs when new links are contributed.
- **CI/CD pipeline**: GitHub Actions (`.github/workflows/ci.yml`) runs two jobs on push to `main`: (1) Markdown link checking via `gaurav-nelson/github-action-markdown-link-check` to enforce link quality, and (2) MkDocs deployment to GitHub Pages with a custom domain.
- **Contribution-friendly structure**: Each topic has its own dedicated markdown file in `docs/`, and the contribution guide (`contributing.md`) provides clear formatting standards and pull request workflow.

## Primary Use Cases and Target Audience

- **Software architects** seeking curated reading lists on architectural styles and patterns.
- **Senior engineers** wanting to learn or deepen knowledge of DDD, CQRS, Event Sourcing, microservices, Clean Architecture, etc.
- **Students and learners** looking for structured learning paths and resource collections.
- **Tech leads** researching patterns such as Circuit Breaker, Outbox/Inbox, Saga, CQRS, or service mesh.
- **DevOps engineers** looking for Kubernetes, Docker, CI/CD, IaC, and observability resources.
- **AI/ML engineers** looking for resources on LLMs, RAG, embeddings, MCP, Semantic Kernel, agent frameworks, and prompt engineering.

## High-Level Architecture Overview

The repository is a **static content repository** — there is no runnable application beyond the release notes tool. Its architecture consists of:

1. **`docs/`** — the primary content directory, organized hierarchically by topic into subdirectories. Each topic area has one or more `.md` files containing categorized lists of links (articles, videos, books, repos).
2. **`mkdocs.yml`** — the MkDocs configuration defining site metadata, theme settings (Material), markdown extensions, and the full navigation tree mapping every doc file to its menu location.
3. **`README.md`** — a GitHub-facing index mirroring the mkdocs nav structure with table-of-contents links and brief descriptions of each topic area.
4. **`Program.cs` / `ReleaseNotes.csproj`** — a standalone C# .NET 9 console application for release note generation from git diffs.
5. **`.github/workflows/ci.yml`** — GitHub Actions pipeline for link validation and site deployment.
6. **`contributing.md`** — community contribution guidelines.
7. **`assets/`** — images (home.png, banner.png).

## Related Projects and Dependencies

- **MkDocs** (Python) with **mkdocs-material** theme — used to build and serve the documentation site.
- **GitHub Actions**: `gaurav-nelson/github-action-markdown-link-check` for CI link validation; `mhausenblas/mkdocs-deploy-gh-pages` for deployment.
- **Custom domain**: `awesome-architecture.com` served via GitHub Pages.
- Related "awesome" lists referenced in the repo include: `simskij/awesome-software-architecture`, `binhnguyennus/awesome-scalability`, `Developer-Y/Scalable-Software-Architecture`, `mhadidg/software-architecture-books`.
- **.NET 9 SDK** — required only to build/run the `ReleaseNotes.csproj` changelog utility.
