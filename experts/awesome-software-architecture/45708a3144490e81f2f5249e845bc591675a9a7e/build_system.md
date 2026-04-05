# Awesome Software Architecture — Build System

## Build System Type and Configuration Files

This repository uses **two independent build systems** for its two distinct components:

### 1. MkDocs (Python-based documentation site)

- **Configuration**: `mkdocs.yml` in the repository root
- **Tool**: [MkDocs](https://www.mkdocs.org/) with the [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) theme
- **Deployment**: GitHub Actions via `mhausenblas/mkdocs-deploy-gh-pages` to GitHub Pages, serving at `https://awesome-architecture.com`
- **No local `requirements.txt` or `pyproject.toml`** is present in the repository; all Python dependencies are managed by the GitHub Actions deployment action

### 2. .NET 9 Console App (Release Notes Generator)

- **Configuration**: `ReleaseNotes.csproj`
- **Tool**: .NET 9 SDK (`dotnet` CLI)
- **Source**: `Program.cs` (single-file C# program, no namespaces)

## External Dependencies and Management

### MkDocs Dependencies (managed by GitHub Actions action)

The `mhausenblas/mkdocs-deploy-gh-pages` action installs MkDocs and required plugins automatically. The following extensions are configured in `mkdocs.yml`:

| Extension | Purpose |
|-----------|---------|
| `smarty` | Smart quotes and typography |
| `sane_lists` | Better list handling |
| `fenced_code` | Fenced code blocks |
| `meta` | Page metadata |
| `admonition` | Note/warning boxes |
| `attr_list` | HTML attributes on elements |
| `pymdownx.arithmatex` | Math rendering |
| `pymdownx.betterem` | Better emphasis |
| `pymdownx.caret` | Superscript |
| `pymdownx.critic` | CriticMarkup |
| `pymdownx.details` | Collapsible sections |
| `pymdownx.inlinehilite` | Inline code highlighting |
| `pymdownx.magiclink` | Auto-link URLs |
| `pymdownx.mark` | Highlighting |
| `pymdownx.smartsymbols` | Symbol substitution |
| `pymdownx.superfences` | Advanced code blocks |
| `pymdownx.tasklist` | Checkboxes |
| `pymdownx.tabbed` | Tabbed content |
| `pymdownx.tilde` | Subscript |
| `codehilite` | Syntax highlighting |
| `footnotes` | Footnote support |
| `toc` | Table of contents with permalink anchors |

### .NET Dependencies

The `ReleaseNotes.csproj` has no external NuGet packages — it relies only on the .NET 9 base class library:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
```

Standard library classes used: `System.Diagnostics.Process` (to run `git diff`), `System.Text.RegularExpressions.Regex`, `System.Collections.Generic`, `System.IO.Path`.

### CI Dependencies (GitHub Actions)

| Action | Version | Purpose |
|--------|---------|---------|
| `actions/checkout` | `master` / `v2` | Repository checkout |
| `gaurav-nelson/github-action-markdown-link-check` | `v1` | Validate all markdown links |
| `mhausenblas/mkdocs-deploy-gh-pages` | `master` | Install MkDocs + deploy to GitHub Pages |

## Build Targets and Commands

### MkDocs — Local Development

To build and preview the documentation site locally:

```bash
# Install MkDocs and Material theme
pip install mkdocs mkdocs-material

# Install PyMdown extensions (required for pymdownx.* extensions)
pip install pymdown-extensions

# Serve locally with live reload (default: http://127.0.0.1:8000)
mkdocs serve

# Build static site into site/ directory
mkdocs build

# Deploy to GitHub Pages manually (requires GITHUB_TOKEN)
mkdocs gh-deploy
```

**Important**: `mkdocs.yml` sets `docs_dir:` to empty (blank value), which means MkDocs looks for docs in the default `docs/` directory.

### .NET Release Notes Generator

```bash
# Build the release notes tool
dotnet build ReleaseNotes.csproj

# Run with default (last commit diff)
dotnet run --project ReleaseNotes.csproj

# Run with custom commit range
dotnet run --project ReleaseNotes.csproj -- HEAD~5..HEAD

# Publish as self-contained executable
dotnet publish ReleaseNotes.csproj -c Release
```

The tool outputs formatted markdown release notes to stdout. Example output:

```
## Clean architecture

### Resources
**Added**
- [New Clean Architecture article](https://example.com) - Description

**Removed**
- [Old link](https://example.com)
```

## How to Build, Test, and Deploy

### Adding New Content (Primary Workflow)

1. Create or edit a `.md` file in `docs/<category>/` with the new resource link.
2. If creating a new topic file, register it in `mkdocs.yml` under the `nav:` section.
3. Follow the link format from `contributing.md`: `**(LINK) | (LIBRARY) | (GitHub-UserName/GitHub-RepositoryName) - DESCRIPTION**`
4. Submit a pull request — CI will run link checking automatically.

### CI Pipeline (`.github/workflows/ci.yml`)

On push to `main`, two jobs run in parallel:

**Job 1: `link-check`**
```yaml
- uses: gaurav-nelson/github-action-markdown-link-check@v1
```
Crawls all `.md` files and validates every HTTP/HTTPS link. Fails the build on broken links.

**Job 2: `build` (Deploy docs)**
```yaml
- uses: mhausenblas/mkdocs-deploy-gh-pages@master
  env:
    GITHUB_TOKEN: ${{ secrets.PERSONAL_TOKEN }}
    CUSTOM_DOMAIN: awesome-architecture.com
```
Installs MkDocs + Material theme, builds the site, and pushes to the `gh-pages` branch. `PERSONAL_TOKEN` is a repository secret; `CUSTOM_DOMAIN` maps the GitHub Pages deployment to `awesome-architecture.com`.

### Testing

There is no automated unit test suite for the content. Quality is enforced by:
- **CI link checker**: validates all URLs in markdown files on every push to `main`.
- **Manual PR review**: maintainers review formatting and relevance of contributed links.
- **MkDocs build**: a failed MkDocs build (e.g., due to missing files referenced in `mkdocs.yml`) will fail the deployment job.

### Local Link Validation

To run link checking locally before submitting a PR:
```bash
# Using the same action's underlying tool (markdown-link-check npm package)
npm install -g markdown-link-check
find docs -name "*.md" | xargs -I {} markdown-link-check {}
```
