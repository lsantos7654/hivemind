# Awesome Design Patterns — Build System

## Build System Type

This repository has **no conventional build system**. There are no Makefiles, Gruntfiles, Webpack configs, CMakeLists, or similar build tooling. The "build" is entirely handled by **GitHub Pages' automatic Jekyll pipeline**, triggered on every push to the `master` branch.

The only build configuration file is:

```
_config.yml
```

Content: `theme: jekyll-theme-architect`

This single line tells GitHub Pages which Jekyll theme to apply when rendering the repository's `README.md` as a static website.

## External Dependencies

### Runtime / Rendering Dependencies

| Dependency | Version / Pin | Purpose |
|---|---|---|
| Jekyll | GitHub Pages-managed | Static site generator |
| `jekyll-theme-architect` | GitHub Pages-managed | Site visual theme |

GitHub Pages automatically manages Jekyll versioning; the repository does not pin a specific Jekyll version. No `Gemfile` or `Gemfile.lock` exists, so dependency management is entirely delegated to the GitHub Pages platform.

### Development Dependencies

**None.** There are no Node.js packages, Python packages, Ruby gems (beyond what GitHub Pages provides), or any other dependency manifests in the repository.

### Link/Resource Dependencies

The repository's content depends on a large number of external URLs. These are not managed as versioned dependencies — they are static hyperlinks that may drift over time. Notable linked repositories include (see `README.md` for full list):

- `github.com/donnemartin/system-design-primer`
- `github.com/iluwatar/java-design-patterns`
- `github.com/kamranahmedse/design-patterns-for-humans`
- `github.com/faif/python-patterns`
- `github.com/tmrts/go-patterns`
- `github.com/ochococo/Design-Patterns-In-Swift`
- `github.com/dbacinski/Design-Patterns-In-Kotlin`
- `github.com/terrytangyuan/distributed-ml-patterns`
- `github.com/jarulraj/sqlcheck`
- Various AWS, Azure, GCP, and O'Reilly documentation URLs

## Build Targets and Commands

### Publishing (GitHub Pages)

The only "build" step is GitHub Pages rendering. It runs automatically when changes are pushed to `master`. No manual command is required.

If you need to preview locally using Jekyll:

```bash
# Prerequisites: Ruby + Bundler installed
# Create a minimal Gemfile (not present in repo):
echo 'source "https://rubygems.org"
gem "github-pages", group: :jekyll_plugins' > Gemfile

bundle install
bundle exec jekyll serve
# Site available at http://localhost:4000
```

This is not documented in the repository itself; it is the standard GitHub Pages local preview workflow.

### Linting / Validation

The repository has **no automated CI/CD, no linting pipeline, and no link-checker**. There are no GitHub Actions workflows (no `.github/workflows/` directory). Validation is entirely manual via the PR review process described in `contributing.md`.

Common community tools that could be applied (but are not configured here):

```bash
# Check for broken links (not configured in repo):
npx markdown-link-check README.md

# Lint markdown formatting:
npx markdownlint README.md

# Validate awesome-list conventions:
npx awesome-lint
```

## How to Build, Test, and Deploy

### To Contribute / "Build"

Since this is a curated list, "building" means editing `README.md` and submitting a PR:

```bash
# 1. Fork the repository on GitHub

# 2. Clone your fork
git clone https://github.com/<your-username>/awesome-design-patterns
cd awesome-design-patterns

# 3. Create a branch
git checkout -b add-my-pattern-resource

# 4. Edit README.md — add your link in the appropriate section
# Format: - [name](URL) - Description.

# 5. Commit and push
git commit -am 'add <resource-name> to <section>'
git push origin add-my-pattern-resource

# 6. Open a pull request on GitHub
```

### To Preview Locally

```bash
# Requires Ruby and Bundler
gem install bundler jekyll

# Since there is no Gemfile in the repo, create one temporarily:
cat > Gemfile <<'EOF'
source "https://rubygems.org"
gem "github-pages", group: :jekyll_plugins
EOF

bundle install
bundle exec jekyll serve --watch
# Open http://localhost:4000 in browser
```

### Deployment

Deployment is fully automated via GitHub Pages:
- Any push to `master` triggers a GitHub Pages build.
- The site is published at `https://dovAmir.github.io/awesome-design-patterns` (or the custom domain if configured).
- No manual deployment step exists.

## Configuration Details

### `_config.yml`

```yaml
theme: jekyll-theme-architect
```

The `jekyll-theme-architect` theme provides:
- Responsive layout with a dark header and light content area.
- Navigation links to the repository on GitHub.
- Automatic rendering of `README.md` as `index.html`.

No other Jekyll configuration (baseurl, title, description, plugins, collections, etc.) is set — all defaults apply.

### GitHub Pages Settings

Not visible in the repository files, but inferred from `_config.yml`:
- **Source:** `master` branch, root directory.
- **Theme:** `jekyll-theme-architect`.
- **Jekyll build:** enabled (not a plain HTML site).

## Summary

| Aspect | Detail |
|---|---|
| Build system | GitHub Pages (Jekyll, automated) |
| Build config | `_config.yml` (1 line) |
| Package manifests | None |
| CI/CD | None |
| Test suite | None |
| Local preview | Manual `bundle exec jekyll serve` |
| Deployment | Automatic on push to `master` |
| License | CC0 (Public Domain) |
