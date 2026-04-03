# TypeScript — APIs and Interfaces

## Public API Entry Point

The TypeScript compiler API is exported through the `typescript` npm package. The main entry point is `lib/typescript.js` (the `main` field in `package.json`) and the types are in `lib/typescript.d.ts`.

```typescript
import ts from "typescript";
// or
import * as ts from "typescript";
// or (CommonJS)
const ts = require("typescript");
```

The source entry point is `src/typescript/typescript.ts`, which re-exports everything from the `ts` namespace.

**Important**: Many symbols inside the source are marked `/** @internal */`. These are stripped from the published `lib/typescript.d.ts` by `scripts/dtsBundler.mjs`. Only symbols without `@internal` are part of the stable public API.

---

## Core Compiler API

### `ts.createProgram()` — `src/compiler/program.ts:1499`

The primary entry point for programmatic compilation.

```typescript
// Overload 1: with options object
function createProgram(createProgramOptions: CreateProgramOptions): Program;

// Overload 2: with root file list
function createProgram(
  rootNames: readonly string[],
  options: CompilerOptions,
  host?: CompilerHost,
  oldProgram?: Program,
  configFileParsingDiagnostics?: readonly Diagnostic[]
): Program;
```

**Usage example:**
```typescript
const program = ts.createProgram({
  rootNames: ["src/index.ts"],
  options: {
    target: ts.ScriptTarget.ES2020,
    module: ts.ModuleKind.CommonJS,
    strict: true,
    outDir: "dist",
  },
});

// Emit JavaScript
const emitResult = program.emit();

// Get diagnostics
const allDiagnostics = ts
  .getPreEmitDiagnostics(program)
  .concat(emitResult.diagnostics);
```

### `ts.Program` interface — `src/compiler/types.ts:4703`

The central object representing a compilation. Key methods:

```typescript
interface Program {
  getSourceFile(fileName: string): SourceFile | undefined;
  getSourceFiles(): readonly SourceFile[];
  getCompilerOptions(): CompilerOptions;
  getTypeChecker(): TypeChecker;
  emit(targetSourceFile?, writeFile?, cancellationToken?, emitOnlyDtsFiles?, customTransformers?): EmitResult;
  getSyntacticDiagnostics(sourceFile?, cancellationToken?): readonly DiagnosticWithLocation[];
  getSemanticDiagnostics(sourceFile?, cancellationToken?): readonly Diagnostic[];
  getDeclarationDiagnostics(sourceFile?, cancellationToken?): readonly DiagnosticWithLocation[];
  getConfigFileParsingDiagnostics(): readonly Diagnostic[];
  getRootFileNames(): readonly string[];
  // ... many more
}
```

### `ts.TypeChecker` interface — `src/compiler/types.ts:5073`

Access via `program.getTypeChecker()`. Used for type analysis and symbol resolution:

```typescript
const checker = program.getTypeChecker();

// Get type of an AST node
const type = checker.getTypeAtLocation(node);
const typeString = checker.typeToString(type);

// Get symbol for an identifier
const symbol = checker.getSymbolAtLocation(node);

// Get all properties of a type
const properties = checker.getPropertiesOfType(type);

// Check assignability
const isAssignable = checker.isTypeAssignableTo(sourceType, targetType);

// Resolve a type to its declaration
const declarations = symbol?.getDeclarations();
```

### `ts.SourceFile` interface — `src/compiler/types.ts:4320`

Represents a parsed TypeScript/JavaScript file:

```typescript
interface SourceFile extends Declaration, LocalsContainer {
  fileName: string;
  statements: NodeArray<Statement>;
  text: string;
  languageVersion: ScriptTarget;
  scriptKind: ScriptKind;
  // ...
}
```

### `ts.createSourceFile()` — `src/compiler/parser.ts`

Parse a single file to an AST without creating a full Program:

```typescript
const sourceFile = ts.createSourceFile(
  "example.ts",
  "const x: number = 42;",
  ts.ScriptTarget.ES2020,
  /*setParentNodes*/ true
);
```

---

## Scanner API

### `ts.createScanner()` — `src/compiler/scanner.ts:1022`

Low-level tokenizer:

```typescript
const scanner = ts.createScanner(
  ts.ScriptTarget.Latest,
  /*skipTrivia*/ false
);
scanner.setText("const x = 1;");
let token = scanner.scan();
while (token !== ts.SyntaxKind.EndOfFileToken) {
  console.log(ts.SyntaxKind[token], scanner.getTokenText());
  token = scanner.scan();
}
```

---

## Configuration Parsing API

### `ts.parseConfigFileTextToJson()` / `ts.parseJsonConfigFileContent()`

Parse `tsconfig.json` files:

```typescript
// Read and parse tsconfig.json
const configPath = ts.findConfigFile("./", ts.sys.fileExists, "tsconfig.json");
const configFile = ts.readConfigFile(configPath!, ts.sys.readFile);
const parsedConfig = ts.parseJsonConfigFileContent(
  configFile.config,
  ts.sys,
  path.dirname(configPath!)
);

const { fileNames, options, errors } = parsedConfig;
```

### Key `CompilerOptions` fields — `src/compiler/types.ts:7403`

```typescript
interface CompilerOptions {
  target?: ScriptTarget;           // ES3, ES5, ES2015, ..., ESNext
  module?: ModuleKind;             // CommonJS, ESNext, NodeNext, etc.
  moduleResolution?: ModuleResolutionKind;
  strict?: boolean;
  outDir?: string;
  rootDir?: string;
  declaration?: boolean;           // Emit .d.ts files
  sourceMap?: boolean;
  jsx?: JsxEmit;                   // None, React, ReactJSX, etc.
  lib?: string[];                  // Library files to include
  paths?: MapLike<string[]>;       // Path aliases
  baseUrl?: string;
  types?: string[];                // @types packages to include
  // ... 100+ options
}
```

---

## Language Service API

### `ts.createLanguageService()` — `src/services/services.ts:1627`

Creates an IDE-facing language service:

```typescript
class MyLanguageServiceHost implements ts.LanguageServiceHost {
  getCompilationSettings(): ts.CompilerOptions {
    return { strict: true };
  }
  getScriptFileNames(): string[] {
    return ["index.ts"];
  }
  getScriptVersion(fileName: string): string {
    return "1";
  }
  getScriptSnapshot(fileName: string): ts.IScriptSnapshot | undefined {
    const content = fs.readFileSync(fileName, "utf-8");
    return ts.ScriptSnapshot.fromString(content);
  }
  getCurrentDirectory(): string {
    return process.cwd();
  }
  getDefaultLibFileName(options: ts.CompilerOptions): string {
    return ts.getDefaultLibFilePath(options);
  }
}

const host = new MyLanguageServiceHost();
const languageService = ts.createLanguageService(host);

// IDE features
const completions = languageService.getCompletionsAtPosition("index.ts", offset, undefined);
const diagnostics = languageService.getSemanticDiagnostics("index.ts");
const definition = languageService.getDefinitionAtPosition("index.ts", offset);
const refs = languageService.getReferencesAtPosition("index.ts", offset);
const renames = languageService.findRenameLocations("index.ts", offset, false, false);
```

### `ts.LanguageService` interface — `src/services/types.ts:460`

Key methods:

```typescript
interface LanguageService {
  // Diagnostics
  getSyntacticDiagnostics(fileName: string): DiagnosticWithLocation[];
  getSemanticDiagnostics(fileName: string): Diagnostic[];
  getSuggestionDiagnostics(fileName: string): DiagnosticWithLocation[];
  getCompilerOptionsDiagnostics(): Diagnostic[];

  // Navigation
  getDefinitionAtPosition(fileName: string, position: number): readonly DefinitionInfo[] | undefined;
  getTypeDefinitionAtPosition(fileName: string, position: number): readonly DefinitionInfo[] | undefined;
  getReferencesAtPosition(fileName: string, position: number): ReferenceEntry[] | undefined;
  findRenameLocations(fileName, position, findInStrings, findInComments, ...): readonly RenameLocation[] | undefined;

  // Completions
  getCompletionsAtPosition(fileName, position, options): WithMetadata<CompletionInfo> | undefined;
  getCompletionEntryDetails(fileName, position, name, ...): CompletionEntryDetails | undefined;

  // Code actions
  getCodeFixesAtPosition(fileName, start, end, errorCodes, formatOptions, preferences): readonly CodeFixAction[];
  getApplicableRefactors(fileName, positionOrRange, preferences, ...): ApplicableRefactorInfo[];
  getEditsForRefactor(fileName, formatOptions, positionOrRange, refactorName, actionName, ...): RefactorEditInfo | undefined;

  // Formatting
  getFormattingEditsForRange(fileName, start, end, options): TextChange[];
  getFormattingEditsForDocument(fileName, options): TextChange[];

  // Inlay hints
  provideInlayHints(fileName, span, preferences): InlayHint[];

  // Quick info / hover
  getQuickInfoAtPosition(fileName: string, position: number): QuickInfo | undefined;

  // Signature help
  getSignatureHelpItems(fileName, position, options): SignatureHelpItems | undefined;

  // Document symbols / outline
  getNavigationBarItems(fileName: string): NavigationBarItem[];
  getNavigateToItems(searchValue, maxResultCount?, ...): NavigateToItem[];

  // Organize imports
  organizeImports(args, formatOptions, preferences): readonly FileTextChanges[];

  // Call hierarchy
  prepareCallHierarchy(fileName: string, position: number): CallHierarchyItem | CallHierarchyItem[] | undefined;
  provideCallHierarchyIncomingCalls(fileName, position): CallHierarchyIncomingCall[];
  provideCallHierarchyOutgoingCalls(fileName, position): CallHierarchyOutgoingCall[];
}
```

---

## Transpile API

### `ts.transpileModule()` — `src/services/transpile.ts:65`

Single-file transpilation without type checking (fast, no cross-file information):

```typescript
const result = ts.transpileModule('const x: number = 1;', {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES5,
  },
  fileName: 'input.ts',
});
console.log(result.outputText);   // "var x = 1;"
console.log(result.sourceMapText); // Source map JSON string
console.log(result.diagnostics);   // Parse-only diagnostics
```

### `ts.transpile()` — `src/services/transpile.ts:226`

Simpler single-string to single-string transpilation (no output metadata).

---

## Emitter / Printer API

### `ts.createPrinter()` — `src/compiler/emitter.ts:1211`

Print an AST node back to source text (useful for code generation/transformation):

```typescript
const printer = ts.createPrinter({ newLine: ts.NewLineKind.LineFeed });
const file = ts.createSourceFile("tmp.ts", "", ts.ScriptTarget.ES2020, false, ts.ScriptKind.TS);

const node = ts.factory.createVariableStatement(
  undefined,
  ts.factory.createVariableDeclarationList([
    ts.factory.createVariableDeclaration("x", undefined, undefined, ts.factory.createNumericLiteral("42")),
  ], ts.NodeFlags.Const)
);

const result = printer.printNode(ts.EmitHint.Unspecified, node, file);
// "const x = 42;"
```

---

## Custom Transformers

Custom AST transformations can be injected into `program.emit()`:

```typescript
function myTransformerFactory(context: ts.TransformationContext): ts.Transformer<ts.SourceFile> {
  return (sourceFile: ts.SourceFile) => {
    function visitor(node: ts.Node): ts.Node {
      // Transform nodes here
      if (ts.isCallExpression(node)) {
        // ... modify call expression
      }
      return ts.visitEachChild(node, visitor, context);
    }
    return ts.visitNode(sourceFile, visitor) as ts.SourceFile;
  };
}

program.emit(undefined, undefined, undefined, false, {
  before: [myTransformerFactory],
  after: [],
  afterDeclarations: [],
});
```

---

## Solution Builder API (Project References)

### `ts.createSolutionBuilder()` — `src/compiler/tsbuild.ts`

For building `tsc --build` / composite project graphs:

```typescript
const buildHost = ts.createSolutionBuilderHost(ts.sys);
const builder = ts.createSolutionBuilder(buildHost, ["tsconfig.json"], {});
builder.build();
```

---

## Diagnostic Utilities

```typescript
// Format diagnostics for console output
const formatted = ts.formatDiagnosticsWithColorAndContext(diagnostics, {
  getCurrentDirectory: () => process.cwd(),
  getCanonicalFileName: (f) => f,
  getNewLine: () => "\n",
});
console.error(formatted);

// Get pre-emit diagnostics (syntax + semantic + declaration)
const diagnostics = ts.getPreEmitDiagnostics(program);
```

---

## Node Type Guards — `src/compiler/factory/nodeTests.ts`

Comprehensive set of `isXxx(node)` type guard functions:

```typescript
ts.isIdentifier(node)
ts.isFunctionDeclaration(node)
ts.isClassDeclaration(node)
ts.isCallExpression(node)
ts.isStringLiteral(node)
ts.isImportDeclaration(node)
ts.isTypeReferenceNode(node)
ts.isInterfaceDeclaration(node)
// ... one for every SyntaxKind
```

---

## AST Visitor Utilities

```typescript
// Visit each child of a node
ts.forEachChild(node, (child) => {
  // visit child
});

// Visit all children recursively
function visit(node: ts.Node) {
  ts.forEachChild(node, visit);
}

// Transform with visitor context
ts.visitEachChild(node, visitor, transformationContext);
ts.visitNode(node, visitor);
```

---

## Integration Patterns

### Pattern 1: Compile and check diagnostics

```typescript
const program = ts.createProgram(["./src/index.ts"], {
  strict: true, outDir: "./dist"
});
const diagnostics = ts.getPreEmitDiagnostics(program);
if (diagnostics.length > 0) {
  console.error(ts.formatDiagnosticsWithColorAndContext(diagnostics, host));
  process.exit(1);
}
program.emit();
```

### Pattern 2: Walk the AST to find all function declarations

```typescript
function findFunctions(sourceFile: ts.SourceFile): ts.FunctionDeclaration[] {
  const functions: ts.FunctionDeclaration[] = [];
  function visit(node: ts.Node) {
    if (ts.isFunctionDeclaration(node)) functions.push(node);
    ts.forEachChild(node, visit);
  }
  visit(sourceFile);
  return functions;
}
```

### Pattern 3: Incremental compilation (watch mode)

```typescript
const host = ts.createWatchCompilerHost(
  "tsconfig.json",
  {},
  ts.sys,
  ts.createEmitAndSemanticDiagnosticsBuilderProgram,
  reportDiagnostic,
  reportWatchStatusChanged
);
ts.createWatchProgram(host);
```

---

## Extension Points

- **Custom compiler host**: Implement `ts.CompilerHost` to intercept file reads/writes (useful for virtual file systems or in-memory compilation)
- **Custom transformers**: Inject `before`/`after`/`afterDeclarations` transformers into `program.emit()`
- **Custom language service host**: Implement `ts.LanguageServiceHost` to provide file content, versions, and project settings to the language service
- **Document registry**: Share `ts.createDocumentRegistry()` across multiple language service instances to reduce memory usage
- **Plugin API** (tsserver only): tsserver supports `plugins` in `tsconfig.json` that can augment the language service via a plugin factory pattern
