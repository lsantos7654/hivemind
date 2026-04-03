# Microsoft REST API Guidelines — Build System

## Build System Type

This repository contains **documentation only** — there is no application code, compiled artifacts, or deployable software. There is no build system in the traditional sense (no `Makefile`, `package.json`, `pyproject.toml`, `CMakeLists.txt`, etc.).

The "build" of this project is the authoring and rendering of Markdown documents, which GitHub renders natively in the browser. The only tooling-related configuration present is a Markdown linting rule file.

## Configuration Files

### `.markdownlint.json` (`azure/.markdownlint.json`)

The only tooling configuration file in the repository. It configures the `markdownlint` linter for the `azure/` directory, disabling specific rules that conflict with the formatting conventions used in `Guidelines.md`.

Typical disabled rules include:
- **MD033** — no inline HTML (disabled because Guidelines.md uses `<a>` anchor tags on every rule)
- **MD049** — emphasis style (disabled to allow mixed emphasis)
- **MD055** — table pipe style (disabled for complex table formatting)

There is no equivalent `.markdownlint.json` in the `graph/` directory.

## External Dependencies

Since there is no runnable code, there are no package manager dependencies (no `npm`, `pip`, `cargo`, `go.sum`, etc.). The repository depends only on the following external references:

**Standards documents (referenced, not installed):**
- RFC 7231 — HTTP/1.1 Semantics and Content
- RFC 9110 — HTTP Semantics (updated HTTP standard)
- RFC 7396 — JSON Merge Patch
- RFC 3339 — Date and Time on the Internet
- RFC 4122 — UUID format
- RFC 5789 — PATCH Method for HTTP
- RFC 6648 — Deprecating the "X-" Prefix for Application-Specific MIME Types
- RFC 2557 — MIME Encapsulation of Aggregate Documents
- OASIS Repeatable Requests Version 1.0
- OData Version 4.01 specification

**External tooling (referenced, not bundled):**
- `markdownlint` — Markdown linting (rule config present in `azure/.markdownlint.json`)
- `cspell` — Spell checker (referenced via comment directives in Guidelines.md header)
- GitHub-Flavored Markdown rendering (GitHub's native renderer)

## Build Targets and Commands

There are no build commands. The repository is consumed by reading the Markdown files directly on GitHub or locally.

**For contributors, the recommended local setup** (from `CONTRIBUTING.md`):

```bash
# Clone the repository
git clone https://github.com/microsoft/api-guidelines.git
cd api-guidelines

# Install a Markdown editor (VS Code recommended)
# Install a markdown-toc package for table of contents management

# Create a topic branch for your changes
git checkout -b my-feature-branch vNext

# Edit the relevant .md file(s)
# Submit PR targeting the vNext branch
```

**Spell check annotations** — `Guidelines.md` uses `cspell` ignore comment directives at the top of the file to suppress false positives for domain-specific terms:

```markdown
<!-- cspell:ignore autorest, BYOS, etag, idempotency, maxpagesize, innererror, ... -->
```

**Markdownlint disable annotations** — `Guidelines.md` uses inline disable comments:

```markdown
<!-- markdownlint-disable MD033 MD049 MD055 -->
```

## How to Read and Navigate the Documentation

The documentation is organized for direct reading; there is no compilation step. To use it:

1. **Start with `azure/README.md`** for an overview of Azure-specific resources and contact information
2. **Read `azure/ConsiderationsForServiceDesign.md`** for conceptual introduction to API design
3. **Reference `azure/Guidelines.md`** for the prescriptive rules
4. **Reference `azure/VersioningGuidelines.md`** for versioning and breaking change rules
5. **For Graph teams**, read `graph/GuidelinesGraph.md` then use `graph/articles/` and `graph/patterns/` as needed

## Contribution Workflow

From `CONTRIBUTING.md`, the documentation authoring workflow is:

1. **Open an issue** — describe the proposed change or question before making changes
2. **Fork** the repository on GitHub
3. **Create a topic branch** off the `vNext` branch
4. **Edit** the relevant Markdown files following the documentation style guide:
   - Use GitHub-Flavored Markdown
   - Use syntax-highlighted code examples
   - Use valid, pretty-printed JSON with 2-space indent
   - Write one sentence per line
   - Trim trailing empty lines from HTTP request examples
5. **Submit a pull request** targeting the `vNext` branch
6. **Address review feedback** from Microsoft API guidelines maintainers

## Documentation Style Conventions

From `CONTRIBUTING.md`:

```markdown
# Example HTTP request/response style:

#### Request
GET http://services.odata.org/V4/TripPinServiceRW/People HTTP/1.1
Accept: application/json

#### Response
HTTP/1.1 200 OK
Content-Type: application/json

{
  "@nextLink": "...",
  "value": [
    {
      "userName": "russellwhyte",
      ...
    }
  ]
}
```

**Commit message conventions:**
- Use present tense: "Change ...", not "Changed ..."
- Use imperative mood: "Change ...", not "Changes ..."
- Limit first line to 72 characters
- Reference issues and PRs

## Deployment

The documentation is deployed automatically by GitHub Pages or rendered natively on `github.com/microsoft/api-guidelines`. No CI/CD pipeline files (`.github/workflows/`) are present in this commit. The CODEOWNERS file at `.github/CODEOWNERS` defines the required reviewers for pull requests.
