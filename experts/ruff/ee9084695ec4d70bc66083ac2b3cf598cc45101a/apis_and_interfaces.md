# Ruff APIs and Interfaces

## CLI Entry Points

### Primary Commands

```bash
# Lint files (check for violations)
ruff check [OPTIONS] [FILES]...

# Format files (reformat Python code)
ruff format [OPTIONS] [FILES]...

# Show rule documentation
ruff rule <RULE_CODE>

# Start LSP server
ruff server

# Analyze import dependency graph
ruff analyze graph [OPTIONS] [FILES]...

# Show resolved configuration
ruff check --show-settings [FILES]

# Add noqa suppression directives
ruff check --add-noqa [FILES]

# Clean the cache
ruff clean
```

### Key CLI Options

```bash
# Lint with auto-fix
ruff check --fix path/

# Fix only fixable violations (unsafe fixes disabled by default)
ruff check --fix --unsafe-fixes path/

# Select specific rules
ruff check --select E,F,B path/

# Ignore specific rules
ruff check --ignore E501 path/

# Watch mode (re-lint on file changes)
ruff check --watch path/

# Output formats
ruff check --output-format json path/
ruff check --output-format sarif path/
ruff check --output-format github path/
ruff check --output-format junit path/
ruff check --output-format text path/  # default

# Format check without modifying files
ruff format --check path/

# Format with diff output
ruff format --diff path/

# Lint/format from stdin
echo "x = 1" | ruff check --stdin-filename test.py -
echo "x=1" | ruff format --stdin-filename test.py -
```

## Configuration API

### Configuration Files

Ruff discovers config in order: `ruff.toml` > `.ruff.toml` > `pyproject.toml [tool.ruff]`

**pyproject.toml example:**

```toml
[tool.ruff]
# Global settings
line-length = 88
target-version = "py311"
src = ["src", "tests"]
exclude = ["migrations/", "build/"]

[tool.ruff.lint]
# Rule selection
select = ["E", "F", "B", "I"]
ignore = ["E501", "B008"]
fixable = ["ALL"]
unfixable = []

# Per-file overrides
[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S101"]  # Allow assert in tests
"__init__.py" = ["F401"]  # Allow unused imports in __init__

[tool.ruff.lint.isort]
known-first-party = ["mypackage"]
combine-as-imports = true

[tool.ruff.lint.pydocstyle]
convention = "google"  # or "numpy", "pep257"

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

**ruff.toml / .ruff.toml example:**

```toml
line-length = 88
target-version = "py311"

[lint]
select = ["E", "F", "B"]
ignore = ["E501"]

[format]
quote-style = "single"
```

### Configuration Options (Key Settings)

| Option | Type | Description |
|--------|------|-------------|
| `line-length` | int | Max line length (default: 88) |
| `target-version` | string | Min Python version (e.g., "py311") |
| `src` | list[str] | Source directories for import resolution |
| `exclude` | list[str] | Paths to exclude |
| `extend-exclude` | list[str] | Additional exclusions (extends default) |
| `force-exclude` | bool | Apply exclusions even on explicit paths |
| `respect-gitignore` | bool | Honor .gitignore files (default: true) |
| `lint.select` | list[str] | Rule codes/prefixes to enable |
| `lint.ignore` | list[str] | Rule codes to ignore |
| `lint.fixable` | list[str] | Rules allowed to auto-fix |
| `lint.unfixable` | list[str] | Rules not allowed to auto-fix |
| `lint.per-file-ignores` | dict | Per-glob rule overrides |
| `lint.extend-select` | list[str] | Add rules without replacing select |
| `lint.preview` | bool | Enable preview (unstable) rules |
| `format.quote-style` | string | "double" (default) or "single" |
| `format.indent-style` | string | "space" (default) or "tab" |
| `format.magic-trailing-comma` | string | "respect" (default) or "ignore" |

## Python API (via PyPI Package)

The `ruff` PyPI package is primarily a CLI tool, but its WASM build exposes a JavaScript/TypeScript API for the playground.

## Rust Library APIs

### `ruff_python_parser` — Parsing

```rust
use ruff_python_parser::{parse_module, parse_expression, Mode};
use ruff_python_ast::ModModule;

// Parse a complete Python module
let parsed = parse_module("x = 1\nprint(x)\n");
let module: &ModModule = parsed.syntax();
let errors = parsed.errors();

// Parse an expression
let parsed = parse_expression("1 + 2 * 3");

// The returned Parsed<T> contains:
// - .syntax() -> &T  (the AST root)
// - .errors() -> &[ParseError]
// - .tokens() -> &TokenSource  (token stream)
```

### `ruff_linter` — Linting

```rust
use ruff_linter::linter::{lint_only, lint_fix};
use ruff_linter::settings::LinterSettings;
use ruff_source_file::SourceFileBuilder;

// Lint without fixing
let source = "import os\nx = 1\n";
let path = Path::new("example.py");
let settings = LinterSettings::default();

let result = lint_only(source, path, &settings);
for message in &result.messages {
    println!("{}: {}", message.rule(), message.message());
}

// Lint with fix application
let result = lint_fix(source, path, flags, &settings);
if let Some(fixed_source) = result.output {
    // Write fixed_source back to the file
}
```

### `ruff_python_formatter` — Formatting

```rust
use ruff_python_formatter::{format_module_source, PyFormatOptions};

let source = "x=1\ny  =  2\n";
let options = PyFormatOptions::default();
let formatted = format_module_source(source, options)?;
println!("{}", formatted.as_code());
```

### `ruff_python_ast` — AST Visitor

```rust
use ruff_python_ast::{visitor::Visitor, Expr, Stmt};

struct MyVisitor;

impl Visitor<'_> for MyVisitor {
    fn visit_expr(&mut self, expr: &Expr) {
        match expr {
            Expr::Call(call) => {
                // Handle function calls
            }
            _ => {}
        }
        // Continue traversal
        self.generic_visit_expr(expr);
    }
}
```

## Rule Authoring API

Rules are implemented in `ruff_linter/src/rules/<category>/`. Each rule is a struct that implements a violation:

```rust
use ruff_diagnostics::{Diagnostic, Violation, ViolationMetadata};
use ruff_macros::{ViolationMetadata, derive_message_formats};
use ruff_python_ast::ExprCall;
use ruff_text_size::Ranged;

/// ## What it does
/// Detects use of `print()`.
///
/// ## Why is this bad?
/// Print statements are often debugging artifacts.
///
/// ## Fix safety
/// This fix is always safe.
///
/// ## Example
/// ```python
/// print("hello")
/// ```
///
/// Use instead:
/// ```python
/// logger.info("hello")
/// ```
#[derive(ViolationMetadata)]
pub(crate) struct PrintFound;

impl Violation for PrintFound {
    #[derive_message_formats]
    fn message(&self) -> String {
        format!("`print` found")
    }
}

// In the checker:
pub(crate) fn print_found(checker: &mut Checker, call: &ExprCall) {
    if is_print_call(call, checker.semantic()) {
        checker.report_diagnostic(Diagnostic::new(PrintFound, call.range()));
    }
}
```

### Diagnostic with Fix

```rust
use ruff_diagnostics::{Diagnostic, Fix, FixAvailability, Violation};

impl Violation for MyRule {
    const FIX_AVAILABILITY: FixAvailability = FixAvailability::Always;

    fn message(&self) -> String { ... }
}

// Attach a fix to a diagnostic:
let mut diagnostic = Diagnostic::new(MyRule, expr.range());
diagnostic.set_fix(Fix::safe_edit(Edit::range_replacement(
    "new_text".to_string(),
    expr.range(),
)));
checker.report_diagnostic(diagnostic);
```

## LSP Server API

The LSP server (`ruff server`) implements the Language Server Protocol:

- **textDocument/didOpen** — lint and publish diagnostics
- **textDocument/didChange** — re-lint on change
- **textDocument/formatting** — format document
- **textDocument/codeAction** — provide fix actions
- **workspace/executeCommand** — apply fixes

**VS Code settings integration:**

```json
{
  "ruff.lint.enable": true,
  "ruff.format.enable": true,
  "ruff.organizeImports": true,
  "ruff.fixAll": true,
  "ruff.server.extraArgs": ["--preview"]
}
```

## `noqa` Suppression Directives

```python
import os  # noqa: F401       # Suppress specific rule
import sys  # noqa            # Suppress all rules on this line
x = 1  # type: ignore        # Also respected (for some rules)
```

## Integration Patterns

### Pre-commit Integration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.15.9
    hooks:
      - id: ruff          # Run linter
        args: [--fix]
      - id: ruff-format   # Run formatter
```

### GitHub Actions

```yaml
- uses: astral-sh/ruff-action@v1
  with:
    args: "check --output-format github"
```

### Programmatic invocation from Python

```python
import subprocess

result = subprocess.run(
    ["ruff", "check", "--output-format", "json", "--stdin-filename", "test.py", "-"],
    input=python_source.encode(),
    capture_output=True,
)
violations = json.loads(result.stdout)
```

## Extension Points

- **Custom rule stubs**: Not supported; all rules are compiled into the binary
- **Plugin architecture**: No external plugin system; contribute rules upstream
- **Configuration extends**: `extend` key allows inheriting from another config file
- **Per-file overrides**: `[lint.per-file-ignores]` and `[lint.extend-per-file-ignores]`
- **Preview rules**: Opt-in unstable rules via `lint.preview = true`
