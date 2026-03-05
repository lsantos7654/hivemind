# nix.dev — APIs and Interfaces

## Overview

nix.dev is primarily a documentation project rather than a software library, so its "APIs" are the authoring interfaces and conventions that contributors use to create and extend documentation. The key interfaces are:

1. The **MyST Markdown authoring interface** for content
2. The **custom Sphinx extension API** for extractable code blocks
3. The **Nix build interface** for the build system
4. The **Sphinx configuration interface** (`conf.py`)
5. The **Diataxis content organization structure**

---

## 1. MyST Markdown Authoring Interface

All content in `source/` is written in MyST (Markedly Structured Text), a Sphinx-compatible superset of CommonMark Markdown.

### Basic Document Structure

Every MyST file begins with a heading (used as the page title) and contains prose, code blocks, and MyST directives:

```markdown
# Page Title

Introductory paragraph.

## Section Heading

Content here.
```

### MyST Directives

Directives are the primary extension mechanism in MyST. They use the colon-fence (` ::: `) or code-fence (` ``` `) syntax:

**Admonitions (notes, warnings, etc.):**
```markdown
:::{note}
This is a note admonition.
:::

:::{warning}
This is a warning.
:::

:::{important}
This is important information.
:::
```

**Tabs (using sphinx-design):**
```markdown
::::{tab-set}
:::{tab-item} Linux
Instructions for Linux.
:::
:::{tab-item} macOS
Instructions for macOS.
:::
::::
```

**Grid cards:**
```markdown
::::{grid} 1 1 2 3
:::{grid-item-card} Card Title
Card content here.
:::
::::
```

**Code blocks with syntax highlighting:**
```markdown
```nix
{ pkgs ? import <nixpkgs> {} }:
pkgs.mkShell {
  packages = [ pkgs.hello ];
}
```
```

**Cross-references:**
```markdown
{ref}`label-name`           # Reference a labeled section
{doc}`relative/path`        # Reference another document
{term}`glossary-term`       # Reference a glossary term
```

**Labels (for cross-referencing):**
```markdown
(my-label)=
## Section That Can Be Referenced
```

### Enabled MyST Extensions (conf.py)

The following MyST features are enabled in `source/conf.py`:

| Feature | What it enables |
|---------|----------------|
| `colon_fence` | `:::` syntax for directives |
| `linkify` | Auto-converts bare URLs to links |
| `tasklist` | GitHub-style `- [x]` task lists |
| `attrs_block` | Block attribute syntax `{.class key="val"}` |
| `header-anchors` | Auto-anchors on headings (3 levels deep) |

---

## 2. Extractable Code Block Extension

### Source: `source/_ext/extractable_code_block.py`

This custom Sphinx extension allows code blocks to be automatically extracted into files and tested in CI.

### Directive Syntax

Use the `extractable-code-block` directive (or the standard code-fence with a filename):

```markdown
```{extractable-code-block} python
:filename: test_example.py

import subprocess
result = subprocess.run(["hello"], capture_output=True)
assert result.returncode == 0
```
```

The filename argument determines the output file. Files prefixed with `test_` are automatically run by `run_code_block_tests.sh`.

### Output Location

Extracted files are written to:
```
<builddir>/extracted/<docname>/<filename>
```

For example, a code block in `source/tutorials/first-steps/ad-hoc-shell-environments.md` with filename `test_hello.sh` would be extracted to:
```
_build/extracted/tutorials/first-steps/ad-hoc-shell-environments/test_hello.sh
```

### Shell Script Handling

Files with `.sh` extensions are automatically made executable (`chmod +x`) after extraction.

### Python Extension API

```python
class ExtractableCodeBlock(CodeBlock):
    """
    A Sphinx CodeBlock subclass that additionally writes the code
    content to a file in the build directory.

    Arguments: (first positional) language
    Options: filename (str) — name of the file to write
    """
    option_spec = {
        'filename': directives.unchanged,
        **CodeBlock.option_spec
    }

    def run(self):
        # Call parent to render the code block normally
        nodes = super().run()
        # Extract file if :filename: option is set
        if 'filename' in self.options:
            self._extract_to_file(self.options['filename'])
        return nodes

def setup(app):
    app.add_directive('extractable-code-block', ExtractableCodeBlock)
    return {'version': '0.1', 'parallel_read_safe': True}
```

---

## 3. Nix Build Interface

### `default.nix` — Primary Build Entry Point

The top-level `default.nix` exposes the following attributes:

```nix
# Build the documentation HTML
nix-build                            # → result/ (HTML site)
nix-build --arg withManuals true     # → result/ (HTML + Nix manuals)

# Development shell
nix-shell                            # → shell with devmode, sphinx, etc.

# Development server
nix-shell --run devmode              # → live-reload at :8080
```

**Arguments:**

| Argument | Default | Description |
|----------|---------|-------------|
| `withManuals` | `false` | Include pre-built Nix reference manuals |
| `nixpkgs` | pinned nixpkgs-rolling | Override the nixpkgs source |

### `nix/inputs.nix` — Source Inputs Interface

```nix
# Returns attrset of all pinned inputs:
{
  nixpkgs-rolling = <nixpkgs-rolling-src>;
  nix-2-18 = <nix-2.18-src>;
  nix-2-19 = <nix-2.19-src>;
  # ... more versions
  nixpkgs-23-05 = <nixpkgs-23.05-src>;
  # ... more versions
}
```

### Development Shell Tools

When inside `nix-shell`, the following tools are available:

| Command | Description |
|---------|-------------|
| `devmode` | Start live-reload Sphinx server at :8080 |
| `sphinx-build` | Run Sphinx directly |
| `make html` | Build HTML via Makefile |
| `make dummy` | Syntax check (fast) |
| `make linkcheck` | Validate external links |
| `vale` | Run style linter |
| `netlify` | Test Netlify redirects locally |

---

## 4. Sphinx Configuration Interface (conf.py)

### Key Configuration Sections

**Project metadata:**
```python
project = "nix.dev"
copyright = "2019-2024, Nix documentation team"
author = "Nix documentation team"
```

**Extensions list:**
```python
extensions = [
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx.ext.intersphinx",
    "sphinx_notfound_page",
    "sphinx_sitemap",
    "extractable_code_block",  # local custom extension
]
```

**MyST configuration:**
```python
myst_enable_extensions = [
    "colon_fence",
    "linkify",
    "tasklist",
    "attrs_block",
]
myst_heading_anchors = 3
```

**Copy button configuration:**
```python
copybutton_prompt_text = r"^\$ |^# |^nix-repl> "
copybutton_prompt_is_regexp = True
```

**HTML theme (sphinx-book-theme):**
```python
html_theme = "sphinx_book_theme"
html_theme_options = {
    "repository_url": "https://github.com/NixOS/nix.dev",
    "use_repository_button": True,
    "use_edit_page_button": True,
    "use_issues_button": True,
    # ... additional options
}
```

**Intersphinx mappings (cross-project references):**
```python
intersphinx_mapping = {
    "nix": ("https://nix.dev/manual/nix/stable", None),
    "nixpkgs": ("https://nixos.org/manual/nixpkgs/stable", None),
    "nixos": ("https://nixos.org/manual/nixos/stable", None),
}
```

---

## 5. Diataxis Content Organization

### Content Type Interface

Each content type has defined conventions for when to use it and how to structure it:

**Tutorials** (`source/tutorials/`)
- Learning-oriented, step-by-step lessons
- Reader follows along and does something
- Success metric: reader completes all steps
- Example file pattern: `tutorials/<topic>.md` or `tutorials/<topic>/index.md`

**Guides/Recipes** (`source/guides/recipes/`)
- Task-oriented, problem-solving how-tos
- Reader achieves a specific goal
- Assumes prerequisite knowledge
- Example file pattern: `guides/recipes/<task>.md`

**Reference** (`source/reference/`)
- Information-oriented technical facts
- Dry, precise, complete
- Suitable for lookup while working
- Example file pattern: `reference/<topic>.md`

**Concepts** (`source/concepts/`)
- Explanation-oriented background knowledge
- Provides context and understanding
- Not task-focused
- Example file pattern: `concepts/<topic>.md`

### Table of Contents (toctree) Pattern

Each section index file defines a toctree:

```markdown
# Section Title

Brief description.

```{toctree}
:hidden:

page-one
page-two
subsection/index
```
```

The `:hidden:` option keeps the toctree from appearing inline while still adding entries to the sidebar navigation.

---

## 6. Configuration Options and Extension Points

### Adding New Documentation Pages

1. Create a new `.md` file in the appropriate Diataxis directory
2. Add the filename (without extension) to the nearest `index.md` toctree
3. Use MyST formatting and directives as needed
4. Add extractable code blocks with `test_` prefix for CI testing

### Adding Extractable Code Tests

In any documentation file:
```markdown
```{extractable-code-block} bash
:filename: test_my_example.sh

#!/usr/bin/env nix-shell
#!nix-shell -i bash -p hello

hello
```
```

The test file will be automatically run by `./run_code_block_tests.sh` in CI.

### Redirects

Add permanent redirects to `_redirects` (Cloudflare format) or `netlify.toml`:

```toml
# netlify.toml
[[redirects]]
  from = "/old-path"
  to = "/new-path"
  status = 301
```

Test redirects locally with:
```bash
nix-shell --run "netlify dev"
```

### Style Checking

Vale rules are configured in `.vale.ini` and `vale/Style/`. To add a new rule:
1. Create a YAML rule file in `vale/Style/nix.dev/`
2. Reference it in `.vale.ini` under `[*.md]`

### Adding New Nix/Nixpkgs Release Versions

Run the update scripts to fetch new version metadata:
```bash
nix-build nix/update-nix-releases.nix && ./result
nix-build nix/update-nixpkgs-releases.nix && ./result
```

This updates `nix/nix-versions.json` and `nix/sources.json` with new release data.
