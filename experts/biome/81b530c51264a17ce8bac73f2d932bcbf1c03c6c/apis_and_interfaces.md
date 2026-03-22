# Biome — APIs and Interfaces

## 1. CLI Interface

The primary user-facing interface. The binary is `biome` (or `npx @biomejs/biome`).

### Commands

| Command | Description |
|---------|-------------|
| `biome check [paths]` | Run formatter, linter, and assist on files |
| `biome format [paths]` | Format files |
| `biome lint [paths]` | Lint files |
| `biome ci [paths]` | CI mode (no writes; exit 1 on issues) |
| `biome start` | Start the background daemon |
| `biome stop` | Stop the background daemon |
| `biome search <pattern> [paths]` | Search code with GritQL patterns |
| `biome migrate` | Migrate `biome.json` to current version |
| `biome migrate eslint` | Convert ESLint config to `biome.json` |
| `biome migrate prettier` | Convert Prettier config to `biome.json` |
| `biome init` | Initialize a new `biome.json` |
| `biome version` | Show version |
| `biome rage` | Diagnostic info for bug reports |
| `biome explain <rule>` | Show documentation for a lint rule |
| `biome clean` | Remove cached data |

### Key CLI Options

```bash
biome check --write          # Apply safe fixes
biome check --fix            # Apply safe fixes (alias for --write)
biome check --unsafe         # Apply unsafe fixes too
biome check --stdin-file-path=foo.js  # Read from stdin
biome format --indent-style=space --indent-width=2 src/
biome lint --rule=noVar src/
biome check --changed        # Only process VCS-changed files
biome check --since=main     # Changed since git ref
```

## 2. Configuration API (`biome.json`)

The `biome.json` file is the primary configuration interface.

### Top-Level Structure

```json
{
  "$schema": "https://biomejs.dev/schemas/2.0.0/schema.json",
  "extends": ["./base.json"],
  "files": {
    "includes": ["**/*.js", "!**/dist"],
    "ignoreUnknownFiles": false,
    "maxSize": 1048576
  },
  "formatter": {
    "enabled": true,
    "indentStyle": "tab",
    "indentWidth": 2,
    "lineWidth": 80,
    "lineEnding": "lf",
    "includes": ["**/*.js"]
  },
  "linter": {
    "enabled": true,
    "rules": {
      "recommended": true,
      "style": {
        "noVar": "error",
        "useConst": "warn"
      },
      "a11y": { "useAltText": "error" }
    }
  },
  "assist": {
    "enabled": true,
    "actions": {
      "source": { "organizeImports": "on" }
    }
  },
  "javascript": {
    "formatter": {
      "quoteStyle": "double",
      "trailingCommas": "all",
      "semicolons": "always",
      "bracketSameLine": false,
      "bracketSpacing": true,
      "arrowParentheses": "always"
    },
    "parser": {
      "unsafeParameterDecoratorsEnabled": true
    },
    "globals": ["myGlobal"]
  },
  "typescript": {
    "formatter": { "quoteStyle": "single" }
  },
  "json": {
    "formatter": { "indentStyle": "space", "indentWidth": 4 },
    "parser": { "allowComments": true, "allowTrailingCommas": true }
  },
  "css": {
    "formatter": { "quoteStyle": "double" },
    "linter": { "enabled": true }
  },
  "vcs": {
    "enabled": true,
    "clientKind": "git",
    "useIgnoreFile": true,
    "defaultBranch": "main"
  },
  "overrides": [
    {
      "includes": ["**/*.test.js"],
      "linter": { "rules": { "suspicious": { "noExplicitAny": "off" } } }
    }
  ],
  "plugins": ["./plugins/my-rule.grit"]
}
```

## 3. Workspace Rust API (`biome_service`)

The `Workspace` trait is the central programmatic API for all tooling (CLI and LSP).

### `Workspace` Trait (simplified)

```rust
// crates/biome_service/src/workspace.rs
pub trait Workspace: Send + Sync {
    // Project management
    fn open_project(&self, params: OpenProjectParams) -> Result<OpenProjectResult, WorkspaceError>;
    fn scan_project(&self, params: ScanProjectParams) -> Result<ScanProjectResult, WorkspaceError>;
    fn update_settings(&self, params: UpdateSettingsParams) -> Result<(), WorkspaceError>;

    // File lifecycle
    fn open_file(&self, params: OpenFileParams) -> Result<OpenFileResult, WorkspaceError>;
    fn close_file(&self, params: CloseFileParams) -> Result<(), WorkspaceError>;
    fn change_file(&self, params: ChangeFileParams) -> Result<(), WorkspaceError>;
    fn get_file_content(&self, params: GetFileContentParams) -> Result<String, WorkspaceError>;

    // Formatting
    fn format_file(&self, params: FormatFileParams) -> Result<Printed, WorkspaceError>;
    fn format_range(&self, params: FormatRangeParams) -> Result<Printed, WorkspaceError>;
    fn format_on_type(&self, params: FormatOnTypeParams) -> Result<Printed, WorkspaceError>;

    // Analysis
    fn pull_diagnostics(&self, params: PullDiagnosticsParams) -> Result<PullDiagnosticsResult, WorkspaceError>;
    fn pull_actions(&self, params: PullActionsParams) -> Result<PullActionsResult, WorkspaceError>;
    fn fix_file(&self, params: FixFileParams) -> Result<FixFileResult, WorkspaceError>;
    fn rename(&self, params: RenameParams) -> Result<RenameResult, WorkspaceError>;

    // Introspection
    fn get_syntax_tree(&self, params: GetSyntaxTreeParams) -> Result<GetSyntaxTreeResult, WorkspaceError>;
    fn get_control_flow_graph(&self, params: GetControlFlowGraphParams) -> Result<String, WorkspaceError>;
    fn get_formatter_ir(&self, params: GetFormatterIRParams) -> Result<String, WorkspaceError>;
    fn get_type_info(&self, params: GetTypeInfoParams) -> Result<String, WorkspaceError>;

    // GritQL search
    fn parse_pattern(&self, params: ParsePatternParams) -> Result<ParsePatternResult, WorkspaceError>;
    fn search_pattern(&self, params: SearchPatternParams) -> Result<SearchPatternResult, WorkspaceError>;

    // Capability check
    fn file_features(&self, params: SupportsFeatureParams) -> Result<FileFeaturesResult, WorkspaceError>;
    fn is_path_ignored(&self, params: PathIsIgnoredParams) -> Result<bool, WorkspaceError>;
}
```

### Creating a Workspace Server

```rust
use biome_service::{App, workspace};
use biome_console::EnvConsole;
use biome_fs::OsFileSystem;
use std::sync::Arc;

let fs = Arc::new(OsFileSystem::default());
let mut console = EnvConsole::default();
let app = App::with_filesystem_and_console(fs, &mut console);
// app.workspace is a WorkspaceRef (Owned or Borrowed)
```

## 4. Analyzer / Lint Rule API

### Implementing a Lint Rule

```rust
use biome_analyze::{context::RuleContext, declare_lint_rule, Rule, RuleDiagnostic};
use biome_js_syntax::JsVariableDeclaration;

declare_lint_rule! {
    /// Use `const` instead of `let` when the variable is never reassigned.
    pub NoVar {
        version: "1.0.0",
        name: "noVar",
        language: "js",
        recommended: true,
    }
}

impl Rule for NoVar {
    type Query = Ast<JsVariableDeclaration>;
    type State = ();
    type Signals = Option<Self::State>;
    type Options = ();

    fn run(ctx: &RuleContext<Self>) -> Self::Signals {
        let node = ctx.query();
        if node.kind_token()?.text_trimmed() == "var" {
            Some(())
        } else {
            None
        }
    }

    fn diagnostic(ctx: &RuleContext<Self>, _state: &Self::State) -> Option<RuleDiagnostic> {
        Some(RuleDiagnostic::new(
            rule_category!(),
            ctx.query().range(),
            "Use of `var` is discouraged.",
        ))
    }
}
```

### Rule Queries

The `type Query` associated type can be:
- `Ast<N>` — matches any AST node of type `N`
- `Semantic<N>` — matches AST node with semantic model available
- `Semantic<N>` with binding information
- `ControlFlowGraph` — for control flow analysis
- `CstNode<N>` — concrete syntax tree node

### Code Actions (Fix)

```rust
use biome_analyze::FixKind;

impl Rule for NoVar {
    // ...
    fn action(ctx: &RuleContext<Self>, _state: &Self::State) -> Option<JsRuleAction> {
        let mut mutation = ctx.root().begin();
        // Replace 'var' keyword with 'let' or 'const'
        Some(JsRuleAction::new(
            ActionCategory::QuickFix,
            ctx.metadata().applicability(),
            markup! { "Replace `var` with `let`" },
            mutation,
        ))
    }
}
```

## 5. Formatter API

### Core Traits

```rust
// biome_formatter/src/lib.rs

pub trait Format<Context> {
    fn fmt(&self, f: &mut Formatter<Context>) -> FormatResult<()>;
}

pub trait FormatRule<T>: Default {
    type Context;
    fn fmt(&self, item: &T, f: &mut Formatter<Self::Context>) -> FormatResult<()>;
}
```

### Format IR Builders (Macros)

```rust
use biome_formatter::prelude::*;

// In a FormatRule::fmt implementation:
write!(f, [
    text("function"),
    space(),
    format_element!(name),
    text("("),
    group(&format_args![
        soft_line_break(),
        params,
        soft_line_break_or_space(),
    ]),
    text(")"),
    space(),
    body,
])?;

// Key IR builders:
// text("literal")          — literal text
// space()                  — a single space
// hard_line_break()        — forced newline
// soft_line_break()        — newline in expanded groups, nothing in flat
// soft_line_break_or_space() — space in flat, newline in expanded
// group(&content)          — try flat, expand if too long
// indent(&content)         — increase indentation level
// join_with(sep, items)    — join items with separator
// if_group_breaks(...)     — content only when group is expanded
// if_group_fits_on_line(...) — content only in flat mode
```

## 6. JavaScript / TypeScript API (`@biomejs/js-api`)

### Installation

```bash
npm install @biomejs/js-api @biomejs/wasm-nodejs
```

### Usage

```typescript
import { Biome } from "@biomejs/js-api/nodejs";

const biome = new Biome();
const { projectKey } = biome.openProject("path/to/project");

// Optional: apply configuration
biome.applyConfiguration(projectKey, {
  formatter: { indentStyle: "space", indentWidth: 2 },
  linter: { rules: { recommended: true } }
});

// Format code
const formatted = biome.formatContent(projectKey, "function f   (a,b){}", {
  filePath: "example.js",
});
console.log(formatted.content); // "function f(a, b) {}"

// Lint code
const result = biome.lintContent(projectKey, formatted.content, {
  filePath: "example.js",
});

// Print diagnostics as HTML
const html = biome.printDiagnostics(result.diagnostics, {
  filePath: "example.js",
  fileSource: formatted.content,
});
```

### `BiomeCommon` Class Methods

| Method | Description |
|--------|-------------|
| `openProject(path)` | Open a project at the given path; returns `{ projectKey }` |
| `applyConfiguration(projectKey, config)` | Apply configuration to a project |
| `formatContent(projectKey, content, options)` | Format code content |
| `formatContentDebug(projectKey, content, options)` | Format with IR output |
| `lintContent(projectKey, content, options)` | Lint code content |
| `printDiagnostics(diagnostics, options)` | Render diagnostics to HTML string |
| `destroy()` | Free WASM memory |

## 7. LSP Interface

Biome implements the Language Server Protocol. Start the LSP server with:
```bash
biome lsp-proxy   # Used by editor extensions
```

Supported LSP capabilities:
- `textDocument/formatting` — format document
- `textDocument/rangeFormatting` — format selection
- `textDocument/onTypeFormatting` — format on type
- `textDocument/publishDiagnostics` — lint diagnostics
- `textDocument/codeAction` — quick fixes and assist actions
- `textDocument/rename` — symbol rename
- `textDocument/completion` — basic completions (suppressions)
- `workspace/didChangeConfiguration` — config reload

## 8. Suppression Comments

In-source suppression of rules:

```javascript
// biome-ignore lint/suspicious/noVar: legacy code
var x = 1;

// biome-ignore lint: suppress all lint rules on next line
var y = 2;

// biome-ignore format: preserve manual alignment
const a =  1;
const ab = 2;
```

## 9. Plugin API (GritQL)

Plugins are `.grit` files that define custom lint patterns:

```grit
// plugins/no-object-assign.grit
`Object.assign($target, $source)` where {
    $target <: not `{}`
} => `{ ...$target, ...$source }`
```

Register in `biome.json`:
```json
{ "plugins": ["./plugins/no-object-assign.grit"] }
```

## 10. VCS / Changed Files Integration

```bash
# Only check files changed vs main branch
biome check --changed --since=main

# Only check files staged for commit
biome check --staged
```

Requires `vcs.enabled = true` and `vcs.clientKind = "git"` in `biome.json`.
