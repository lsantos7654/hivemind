# Design Patterns For Humans — Build System

## Overview

**design-patterns-for-humans has no build system.** This is a pure documentation repository consisting of a single Markdown file (`readme.md`). There are no compilation steps, no package manifests, no test runners, no CI configuration files, and no deployment pipelines tracked in the repository.

This is an intentional architectural choice: the project is a human-readable reference document, not software to be installed or executed.

## What Exists (and What Does Not)

### Files present at commit `7023f30d183b6502fe8945d705f2eafdd07dcf4a`

| File | Purpose |
|---|---|
| `readme.md` | The entire project — all content, all examples |

### Files that do NOT exist

| File | Why it's absent |
|---|---|
| `composer.json` | No PHP package to install; examples are embedded in Markdown |
| `package.json` | No Node.js tooling |
| `Makefile` | No build targets |
| `.travis.yml` / `.github/workflows/` | No CI pipeline |
| `phpunit.xml` | No test suite |
| `Dockerfile` | Not a deployable application |
| `LICENSE` | License is declared inline in `readme.md` via a CC BY 4.0 badge |
| `.gitignore` | Nothing to ignore |

## PHP Code Examples — Runtime Context

The PHP 7 code samples embedded in `readme.md` are illustrative, not runnable scripts. However, for readers who want to execute them:

### PHP Version Requirement
- **PHP 7+** is required (uses PHP 7 type declarations: `string`, `float`, `int`, `array`, `bool` in function signatures)
- PHP 7.1+ recommended (uses nullable return types implicitly in some examples)

### PHP Extensions / Standard Library Used
The Iterator pattern example uses PHP's Standard PHP Library (SPL) interfaces directly:
```php
use Countable;
use Iterator;

class StationList implements Countable, Iterator { ... }
```
Both `Countable` and `Iterator` are built into PHP core — no extension installation needed.

No third-party Composer packages are used anywhere in the examples.

### Running an Example
To run any example locally, copy the relevant PHP code block(s) from `readme.md` into a `.php` file and run with the PHP CLI:

```bash
# Example: running the Simple Factory example
php simple_factory.php

# Requires PHP 7+
php --version
```

No `composer install`, no autoloading, no framework bootstrap — the examples are self-contained.

## Viewing the Documentation

### GitHub (primary)
The `readme.md` renders automatically as the repository's front page on GitHub with full Markdown formatting including syntax-highlighted PHP code blocks.

### Local Markdown Rendering
Any Markdown viewer can render the file:

```bash
# Using a terminal Markdown renderer (e.g., glow)
glow readme.md

# Using VS Code
code readme.md  # then toggle preview with Ctrl+Shift+V / Cmd+Shift+V

# Using Python's built-in HTTP server + a browser
python3 -m markdown readme.md > index.html && open index.html
```

### Pandoc — Converting to Other Formats
The file can be converted to PDF, HTML, DOCX, or EPUB using Pandoc:

```bash
# HTML
pandoc readme.md -o design-patterns.html

# PDF (requires LaTeX)
pandoc readme.md -o design-patterns.pdf

# EPUB
pandoc readme.md -o design-patterns.epub
```

Note: PHP syntax highlighting in converted outputs depends on Pandoc's syntax highlighting engine (Skylighting). PHP is fully supported.

## Contributing — What "Building" Means for This Project

Since the project is documentation, "building" means:

1. **Editing `readme.md`** — all content changes happen here
2. **Verifying Markdown renders correctly** — check in a Markdown previewer
3. **Verifying PHP examples are syntactically valid** — manually or with `php -l` (lint check):

```bash
# PHP syntax check (lint only, no execution)
# Extract a code block to a file, then:
php -l example.php
```

4. **Opening a Pull Request on GitHub** — the contribution workflow is: fork → edit → PR

## External Dependencies Summary

| Dependency | Version | Required For |
|---|---|---|
| PHP CLI | 7.0+ | Running code examples locally |
| PHP SPL | Built-in | Iterator pattern example (`Countable`, `Iterator`) |
| Markdown renderer | Any | Reading/rendering the documentation |
| Pandoc | Any (optional) | Converting to PDF/HTML/EPUB |

All of these are optional for the primary use case of reading the documentation on GitHub. None are installed or managed by the repository itself.

## License

The content is licensed under [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). This is declared via a badge in the readme's closing section. No `LICENSE` file exists in the repository — the badge and inline declaration serve as the license notice.
