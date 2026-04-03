# Azure Architecture Center — Build System

## Build System Type

This is a **documentation-only repository** with no application code, binaries, or deployable services. The build system is Microsoft's **Open Publishing Service (OPS)** with **DocFX** as the documentation generation tool and **Markdig** as the Markdown rendering engine.

There are no `package.json`, `requirements.txt`, `Makefile`, `Cargo.toml`, or similar application build files. The "build" in this context means converting Markdown and YAML source files into a published documentation website hosted at <https://azure.com/architecture>.

## Configuration Files

### `docs/docfx.json` — Primary Build Configuration
The central build configuration at `docs/docfx.json` controls:

**Content sources** — Which files are processed:
```json
{
  "build": {
    "content": [{
      "src": ".",
      "dest": ".",
      "files": ["**/*.md", "**/toc.yml", "**/*.yml"],
      "exclude": [
        "**/obj/**",
        "**/*.liquid.md",
        "**/_css/**",
        "**/includes/**",
        "**/_bread/**",
        "**/_themes/**",
        "**/**/*-content.md"   // Split-file bodies excluded from direct publishing
      ]
    }]
  }
}
```

**Resource files** — Images, CSS, JS, JSON, DOCX, and other static assets:
```json
"resource": [{
  "files": ["**/*.css", "**/*.png", "**/*.jpg", "**/*.svg", "**/*.js",
            "**/*.json", "**/*.docx", "feed.atom"],
  "exclude": ["**/obj/**", "**/_themes/**"]
}]
```

**Global metadata** — Applied to all articles:
```json
"globalMetadata": {
  "feedback_system": "Standard",
  "feedback_github_repo": "MicrosoftDocs/architecture-center",
  "breadcrumb_path": "/azure/architecture/bread/toc.json",
  "brand": "azure",
  "uhfHeaderId": "azure",
  "titleSuffix": "Azure Architecture Center",
  "ms.author": "pnp",
  "ms.service": "azure-architecture-center",
  "ms.update-cycle": "365-days",
  "manager": "lnyswonger",
  "ms.topic": "concept-article",
  "searchScope": ["Azure", "Azure Architecture Center"]
}
```

**File-level metadata overrides** — Applied per glob pattern:
- `open_to_public_contributors` — All `.md` and `.yml` files are open for contributions
- `searchScope` — Different sections get additional search scopes (e.g., `"Cloud Design Patterns"` for `patterns/**`, `"Data Guide"` for `data-guide/**`)
- `ms.update-cycle` — Some sections (e.g., `guide/multitenant/`, `patterns/`, `antipatterns/`) override to `1095-days` (3-year cycle); `ai-ml/**` uses `180-days` (6-month cycle)

**Rendering configuration**:
```json
"template": ["docs.html"],
"dest": "azure",
"markdownEngineName": "markdig"
```

### `cspell.json` (Root and `docs/`)
Spell-checking configuration used during content validation. The root `cspell.json` and `docs/cspell.json` define custom word lists and exclusion patterns. `docs/cspell-docutune.json` provides additional docutune-specific exclusions. These are enforced in the pull request pipeline.

### `.acrolinx-config.edn`
Acrolinx content quality configuration — enforces Microsoft writing style guidelines, terminology standards, and readability targets on submitted content.

### `.openpublishing.redirection.json`
Defines 1,643 URL redirect rules mapping old article paths to current paths. This file is critical to maintaining SEO and link integrity as content is reorganized. Format:
```json
{
  "redirections": [
    {
      "source_path": "docs/old/path/article.md",
      "redirect_url": "/azure/architecture/new/path/article",
      "redirect_document_id": true
    }
  ]
}
```

### `docs/_bread/toc.yml`
Breadcrumb navigation for the Azure portal header. Built separately (`src: "_bread"`, `dest: "bread"`) and deployed as `bread/toc.json`.

## Build Targets and Publishing Pipeline

The repository uses Microsoft's **Open Publishing System (OPS)** GitHub integration. There is no local build script or CI YAML file exposed in the repository. The publishing pipeline:

1. **PR validation** — When a pull request is opened, OPS triggers a build that validates:
   - Markdown/YAML syntax
   - Internal link integrity
   - Spell checking via `cspell`
   - Acrolinx style scoring
   - Metadata completeness (required frontmatter fields)

2. **Preview build** — OPS generates a preview URL for reviewing rendered output before merge.

3. **Merge and publish** — On merge to the main branch, OPS builds and publishes to the live site at `https://learn.microsoft.com/azure/architecture/` (canonical URL mirrors `https://azure.com/architecture`).

4. **Redirection processing** — `.openpublishing.redirection.json` is processed to set up HTTP 301 redirects on the CDN.

## Document Format Requirements

All articles must include YAML frontmatter with required metadata fields:

| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Page title for SEO and browser tab |
| `description` | Yes | Meta description (SEO) |
| `author` | Yes | GitHub username of primary author |
| `ms.author` | Yes | Microsoft alias (typically `pnp` for team articles) |
| `ms.date` | Yes | Last significant content update date (MM/DD/YYYY) |
| `ms.topic` | Yes | Content type (`concept-article`, `design-pattern`, `best-practice`, etc.) |
| `ms.subservice` | Recommended | Subsection taxonomy for filtering |

`YamlMime:Architecture` files additionally require:
- `name` — Display name for browse catalog
- `summary` — Short description for cards/tiles
- `thumbnailUrl` — Path to browse catalog thumbnail image
- `content` — The `[!INCLUDE[](foo-content.md)]` directive

## How to Contribute

Per `CONTRIBUTING.md` and the Microsoft contributor guide:

1. **Minor edits** — Use the "Edit in GitHub" button on any published article. This creates a fork and PR automatically.

2. **Larger contributions** — Fork the repository, create a branch, make changes, open a PR against the main branch.

3. **New articles** — Must follow the file format patterns (standard Markdown or split YamlMime + content), include all required frontmatter, and be added to the appropriate `toc.yml`.

4. **Validation** — The OPS PR validation must pass. Spell check failures, broken links, and missing metadata will block merge.

## External Dependencies

| Tool / Service | Purpose |
|---------------|---------|
| DocFX | Documentation site generator |
| Markdig | Markdown rendering engine (supports extended syntax for Azure docs) |
| cspell | Spell checking during CI |
| Acrolinx | Writing style and terminology compliance |
| Microsoft OPS | Build, preview, and publish pipeline (managed by Microsoft) |
| GitHub | Version control and PR workflow |
| Azure CDN | Content delivery for the published site |

There are no npm packages, Python dependencies, or other package managers involved — the repository is purely content files processed by Microsoft's managed publishing infrastructure.
