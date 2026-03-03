# Joi Code Structure

## Directory Tree

```
joi/
├── .github/
│   └── workflows/
│       └── ci-module.yml          # CI/CD configuration
├── benchmarks/                     # Performance regression testing
│   ├── bench.js                   # Benchmark runner
│   ├── suite.js                   # Test suite definitions
│   ├── package.json               # Benchmark dependencies
│   └── README.md                  # Benchmark documentation
├── browser/                        # Browser build configuration
│   ├── lib/                       # Browser-specific adaptations
│   ├── tests/                     # Browser test suite
│   ├── karma.conf.js              # Karma test runner config
│   ├── webpack.config.js          # Production webpack config
│   ├── webpack.mocha.js           # Test webpack config
│   └── package.json               # Browser build dependencies
├── dist/                          # Generated browser bundle (git-ignored)
│   └── joi-browser.min.js         # Minified browser build
├── lib/                           # Main source directory
│   ├── types/                     # Type implementations
│   │   ├── alternatives.js        # Alternatives type (387 lines)
│   │   ├── any.js                 # Base any type (174 lines)
│   │   ├── array.js               # Array type (831 lines)
│   │   ├── binary.js              # Binary/Buffer type (100 lines)
│   │   ├── boolean.js             # Boolean type (151 lines)
│   │   ├── date.js                # Date type (233 lines)
│   │   ├── function.js            # Function type (93 lines)
│   │   ├── keys.js                # Object keys type (1090 lines)
│   │   ├── link.js                # Recursive link type (168 lines)
│   │   ├── number.js              # Number type (363 lines)
│   │   ├── object.js              # Object type (22 lines, extends keys)
│   │   ├── string.js              # String type (882 lines)
│   │   └── symbol.js              # Symbol type (102 lines)
│   ├── annotate.js                # Error annotation for display
│   ├── base.js                    # Base schema class
│   ├── cache.js                   # LRU caching system
│   ├── common.js                  # Shared utilities and constants
│   ├── compile.js                 # Schema compilation from plain objects
│   ├── errors.js                  # Error handling and ValidationError
│   ├── extend.js                  # Type extension system
│   ├── index.js                   # Main entry point (282 lines)
│   ├── index.d.ts                 # TypeScript definitions (2659 lines)
│   ├── manifest.js                # Schema serialization/deserialization
│   ├── messages.js                # Error message management
│   ├── modify.js                  # Schema modification utilities
│   ├── ref.js                     # Reference system
│   ├── schemas.js                 # Internal validation schemas
│   ├── state.js                   # Validation state management
│   ├── template.js                # Template engine for messages
│   ├── trace.js                   # Debug tracing support
│   ├── validator.js               # Core validation engine
│   └── values.js                  # Valid/invalid value sets
├── test/                          # Test suite
│   ├── types/                     # Type-specific tests
│   │   ├── alternatives.js
│   │   ├── any.js
│   │   ├── array.js
│   │   ├── binary.js
│   │   ├── boolean.js
│   │   ├── date.js
│   │   ├── function.js
│   │   ├── link.js
│   │   ├── number.js
│   │   ├── object.js
│   │   ├── string.js
│   │   └── symbol.js
│   ├── base.js                    # Base functionality tests
│   ├── cache.js                   # Cache tests
│   ├── helper.js                  # Test utilities
│   ├── isAsync.js                 # Async validation tests
│   ├── manifest.js                # Manifest tests
│   ├── modify.js                  # Modification tests
│   ├── template.js                # Template tests
│   └── validator.js               # Validator tests
├── .gitignore                     # Git ignore rules
├── .npmrc                         # npm configuration
├── API.md                         # Complete API documentation (154KB)
├── eslint.config.js               # ESLint configuration
├── LICENSE.md                     # BSD-3-Clause license
├── package.json                   # Project metadata and dependencies
└── README.md                      # Quick start guide
```

## Module Organization

### Source Directory (`lib/`)

The library is organized into a modular structure with clear separation of concerns:

**Core Entry Point**: `lib/index.js` serves as the main export, creating the root Joi object with all type constructors, utility methods, and aliases. It assembles the complete API surface from component modules.

**Type System**: The `lib/types/` directory contains all built-in type implementations. Each type is a self-contained module that extends a base type using the extension system. The hierarchy is: `any` (base) → `keys` → `object`, while other types extend `any` directly.

**Infrastructure Modules**: Core functionality is split across specialized modules:
- Validation orchestration (`validator.js`)
- Error handling (`errors.js`)
- Schema compilation (`compile.js`)
- Reference system (`ref.js`)
- Template engine (`template.js`)
- Extension mechanism (`extend.js`)

### Type System Architecture

**Base Type (`lib/types/any.js`)**: Defines the foundational schema type that all others inherit from. Implements core rules like `custom()`, `messages()`, `warning()`, and `shared()`. Provides the blueprint for flags, terms, rules, and modifiers.

**Specialized Types**: Each type in `lib/types/` implements domain-specific validation:
- **`string.js`** (882 lines): Most feature-rich with email, URI, GUID, base64, domain, IP, regex, length, case normalization
- **`array.js`** (831 lines): Item validation, length constraints, ordering, uniqueness, sparse arrays
- **`keys.js`** (1090 lines): Object key validation, patterns, dependencies, renaming, unknown keys - serves as base for `object.js`
- **`number.js`** (363 lines): Integer, precision, range, sign, multiple, port validation
- **`alternatives.js`** (387 lines): Conditional schemas, type matching, try-catch patterns

**Lightweight Types**: Some types are minimal wrappers:
- **`object.js`** (22 lines): Extends `keys.js` with Map casting
- **`binary.js`** (100 lines): Buffer validation with encoding and length
- **`function.js`** (93 lines): Function validation with arity and class checks

### Key Files and Their Roles

**`lib/base.js`**: Implements the `Base` class that serves as the prototype for all schemas. Contains methods for:
- Schema cloning and mutation (`clone()`, `_assign()`)
- Rule management (`$_addRule()`, `$_getRule()`)
- Validation entry points (`validate()`, `validateAsync()`)
- Schema composition (`concat()`, `when()`, `alter()`)
- Common rules (`allow()`, `valid()`, `required()`, `optional()`, `forbidden()`)
- Metadata (`description()`, `example()`, `meta()`, `tag()`, `note()`)

**`lib/validator.js`**: Core validation engine implementing:
- Entry points for sync (`entry()`) and async (`entryAsync()`) validation
- State management during validation traversal
- External rule execution for async validators
- Error collection and aggregation
- Artifact and warning management

**`lib/compile.js`**: Handles schema compilation from various input formats:
- Converts plain objects to `Joi.object().keys()` schemas
- Handles arrays as `alternatives().try()`
- Supports RegExp as string patterns
- Enables shorthand notations for common patterns
- Validates and compiles references

**`lib/errors.js`**: Error system with two main classes:
- **`ValidationError`**: Final error thrown/returned with details array, annotate method
- **`Report`**: Individual error instance with code, path, message, template rendering

**`lib/ref.js`**: Reference implementation for cross-field validation:
- Path-based references (e.g., `Joi.ref('a.b.c')`)
- Context references (e.g., `Joi.ref('$global.value')`)
- Ancestor references (e.g., `Joi.ref('....parent')`)
- Reference manager for tracking dependencies

**`lib/extend.js`**: Extension system that enables custom types:
- Merges parent and child definitions
- Handles flags, terms, rules, messages
- Manages coerce, prepare, and validate hooks
- Prototypal inheritance for methods

### Code Organization Patterns

**Immutable Schema Pattern**: Every schema method returns a new instance via `clone()`. Internal state is never mutated directly. This pattern enables safe schema reuse and composition.

**Internal Namespace Convention**: The codebase uses a consistent naming convention:
- `internals`: Private module-level utilities and constants
- `$_property`: Internal schema methods (extension points)
- `$_terms`: Schema terms (arrays of configuration objects)
- `_property`: Private instance properties
- `property`: Public API

**Definition-Driven Types**: Types are defined declaratively using definition objects with:
- `type`: Type name string
- `flags`: Configurable boolean/value flags with defaults
- `terms`: Arrays of internal data (e.g., `keys`, `patterns`, `whens`)
- `rules`: Validation rules with method, validate, args
- `modifiers`: Rule modifiers (e.g., `keep`, `message`, `warn`)
- `coerce`: Type coercion hooks
- `validate`: Core validation logic
- `messages`: Default error messages

**Validation Pipeline**: The validation flow follows a clear pipeline:
1. **Prepare**: Pre-processing hook for value transformation
2. **Coerce**: Type coercion based on input type
3. **Validate**: Core type validation
4. **Rules**: Sequential rule evaluation
5. **Finalize**: Post-processing and artifact generation

### Module Size Metrics

Total lines in `lib/` (excluding types): ~6,450 lines
- Largest core modules: `base.js`, `validator.js`, `errors.js`
- Type modules total: ~4,600 lines
- TypeScript definitions: 2,659 lines (comprehensive)
- API documentation: ~154KB (detailed reference)

The codebase demonstrates excellent modularity with clear separation between type implementations, core infrastructure, and utilities. Each module has a single, well-defined responsibility with minimal coupling.

### Test Organization

The `test/` directory mirrors the `lib/` structure:
- 28 test files total
- Each type has dedicated test coverage
- Core modules tested separately (`base.js`, `cache.js`, `validator.js`)
- Target: 100% code coverage (enforced via `lab -t 100`)

### Browser Build Structure

The `browser/` directory contains:
- Webpack configuration for bundling
- Karma test runner for browser testing
- Browser-specific test adaptations
- Independent package with dev dependencies

This structure keeps browser build concerns isolated from the main library while sharing the core source code.
