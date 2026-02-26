# Formily Code Structure

## Repository Organization

Formily is organized as a Lerna-managed monorepo with a clear separation between core packages, framework bindings, component libraries, and development tools. The repository structure follows a modular architecture where each package can be independently versioned and consumed, though they maintain synchronized versions in practice.

## Complete Annotated Directory Tree

```
formily/
├── packages/                    # Core monorepo packages (published to npm)
│   ├── core/                   # Framework-agnostic form core (@formily/core)
│   │   ├── src/
│   │   │   ├── models/         # Form state models
│   │   │   │   ├── Form.ts     # Main Form class with lifecycle management
│   │   │   │   ├── Field.ts    # Input field model with validation
│   │   │   │   ├── ArrayField.ts  # Array/list field model
│   │   │   │   ├── ObjectField.ts # Object/nested field model
│   │   │   │   ├── VoidField.ts   # Layout-only field (no value)
│   │   │   │   ├── Query.ts    # Field query and search utilities
│   │   │   │   ├── Graph.ts    # Field dependency graph management
│   │   │   │   └── Heart.ts    # Lifecycle event scheduler
│   │   │   ├── effects/        # Form effect hooks and lifecycle
│   │   │   │   ├── onFormEffects.ts   # Form-level lifecycle hooks
│   │   │   │   └── onFieldEffects.ts  # Field-level lifecycle hooks
│   │   │   ├── shared/         # Internal utilities and helpers
│   │   │   │   ├── internals.ts   # State getters/setters
│   │   │   │   ├── checkers.ts    # Type checking utilities
│   │   │   │   ├── effective.ts   # Effect system implementation
│   │   │   │   ├── externals.ts   # Public API exports
│   │   │   │   └── constants.ts   # Constants and enums
│   │   │   └── types.ts        # TypeScript type definitions
│   │   ├── docs/               # Package documentation
│   │   └── package.json        # Dependencies: @formily/reactive, validator, shared
│   │
│   ├── reactive/               # Reactive state management (@formily/reactive)
│   │   ├── src/
│   │   │   ├── observable.ts   # Core observable creation
│   │   │   ├── autorun.ts      # Auto-tracking reactive functions
│   │   │   ├── reaction.ts     # Reactive side effects
│   │   │   ├── batch.ts        # Batched updates
│   │   │   ├── tracker.ts      # Dependency tracking system
│   │   │   ├── handlers.ts     # Proxy handlers for observables
│   │   │   ├── model.ts        # Observable model decorator
│   │   │   ├── action.ts       # Action wrapper for mutations
│   │   │   ├── annotations/    # Observable type annotations
│   │   │   │   ├── observable.ts  # Deep observable
│   │   │   │   ├── shallow.ts     # Shallow observable
│   │   │   │   ├── computed.ts    # Computed values
│   │   │   │   ├── ref.ts         # Reference wrapper
│   │   │   │   └── box.ts         # Boxed primitive values
│   │   │   ├── observe.ts      # Observation utilities
│   │   │   ├── untracked.ts    # Untracked execution context
│   │   │   ├── checkers.ts     # Type checking for observables
│   │   │   ├── array.ts        # Observable array utilities
│   │   │   ├── tree.ts         # Tree structure utilities
│   │   │   └── types.ts        # TypeScript definitions
│   │   └── benchmark.ts        # Performance benchmarks
│   │
│   ├── react/                  # React framework bindings (@formily/react)
│   │   ├── src/
│   │   │   ├── components/     # React form components
│   │   │   │   ├── FormProvider.tsx    # Form context provider
│   │   │   │   ├── Field.tsx           # Field component wrapper
│   │   │   │   ├── ArrayField.tsx      # Array field component
│   │   │   │   ├── ObjectField.tsx     # Object field component
│   │   │   │   ├── VoidField.tsx       # Void/layout field
│   │   │   │   ├── SchemaField.tsx     # JSON Schema renderer
│   │   │   │   ├── RecursionField.tsx  # Recursive field renderer
│   │   │   │   ├── FormConsumer.tsx    # Form state consumer
│   │   │   │   ├── ReactiveField.tsx   # Reactive field wrapper
│   │   │   │   ├── ExpressionScope.tsx # Expression scope provider
│   │   │   │   ├── RecordScope.tsx     # Record data scope
│   │   │   │   └── RecordsScope.tsx    # Multiple records scope
│   │   │   ├── hooks/          # React hooks for forms
│   │   │   │   ├── useForm.ts          # Form instance hook
│   │   │   │   ├── useField.ts         # Field instance hook
│   │   │   │   ├── useParentForm.ts    # Parent form access
│   │   │   │   ├── useFieldSchema.ts   # Field schema access
│   │   │   │   ├── useFormEffects.ts   # Effect registration
│   │   │   │   └── useExpressionScope.ts # Expression scope access
│   │   │   ├── shared/         # Shared React utilities
│   │   │   │   ├── connect.ts      # Component connection HOC
│   │   │   │   ├── context.ts      # React contexts
│   │   │   │   └── render.ts       # Rendering utilities
│   │   │   └── types.ts        # React-specific types
│   │   └── docs/               # React-specific documentation
│   │
│   ├── vue/                    # Vue framework bindings (@formily/vue)
│   │   ├── src/
│   │   │   ├── components/     # Vue form components (similar to React)
│   │   │   ├── hooks/          # Vue composition API hooks
│   │   │   ├── shared/         # Vue-specific utilities
│   │   │   ├── utils/          # Helper functions
│   │   │   ├── types/          # Vue type definitions
│   │   │   └── vue2-components.ts  # Vue 2 compatibility layer
│   │   ├── bin/                # CLI tools
│   │   │   ├── formily-vue-switch.js  # Vue version switcher
│   │   │   └── formily-vue-fix.js     # Migration helper
│   │   └── scripts/            # Build and setup scripts
│   │       └── postinstall.js  # Post-install Vue version detection
│   │
│   ├── reactive-react/         # React reactive integration (@formily/reactive-react)
│   │   ├── src/
│   │   │   ├── observer.ts     # React component observer HOC
│   │   │   ├── hooks/          # Reactive hooks for React
│   │   │   └── shared/         # Shared reactive-react utilities
│   │
│   ├── reactive-vue/           # Vue reactive integration (@formily/reactive-vue)
│   │   ├── src/
│   │   │   ├── observer/       # Vue component observer
│   │   │   └── hooks/          # Reactive hooks for Vue
│   │
│   ├── json-schema/            # JSON Schema engine (@formily/json-schema)
│   │   ├── src/
│   │   │   ├── schema.ts       # Schema class and API
│   │   │   ├── compiler.ts     # Expression compiler for schemas
│   │   │   ├── transformer.ts  # Schema to field props transformer
│   │   │   ├── patches.ts      # Schema patches and extensions
│   │   │   ├── polyfills/      # Polyfills for schema features
│   │   │   ├── shared.ts       # Shared schema utilities
│   │   │   └── types.ts        # Schema type definitions
│   │
│   ├── validator/              # Validation engine (@formily/validator)
│   │   ├── src/
│   │   │   ├── validator.ts    # Main validation function
│   │   │   ├── rules.ts        # Built-in validation rules
│   │   │   ├── formats.ts      # Format validators (email, url, etc.)
│   │   │   ├── registry.ts     # Rule and format registration
│   │   │   ├── parser.ts       # Validator parsing logic
│   │   │   ├── template.ts     # Error message templates
│   │   │   ├── locale.ts       # Internationalization support
│   │   │   └── types.ts        # Validator type definitions
│   │
│   ├── shared/                 # Shared utilities (@formily/shared)
│   │   ├── src/
│   │   │   ├── array.ts        # Array manipulation utilities
│   │   │   ├── checkers.ts     # Type checking functions
│   │   │   ├── clone.ts        # Deep cloning utilities
│   │   │   ├── compare.ts      # Value comparison utilities
│   │   │   ├── merge.ts        # Object merging utilities
│   │   │   ├── isEmpty.ts      # Empty value checking
│   │   │   ├── case.ts         # String case conversion
│   │   │   ├── string.ts       # String utilities
│   │   │   ├── path.ts         # Path manipulation (FormPath)
│   │   │   ├── uid.ts          # Unique ID generation
│   │   │   ├── global.ts       # Global object polyfill
│   │   │   ├── deprecate.ts    # Deprecation warnings
│   │   │   ├── subscribable.ts # Event subscription pattern
│   │   │   ├── middleware.ts   # Middleware pattern utilities
│   │   │   ├── defaults.ts     # Default value utilities
│   │   │   └── instanceof.ts   # instanceof checks across realms
│   │
│   ├── path/                   # Path resolution system (@formily/path)
│   │   ├── src/
│   │   │   ├── index.ts        # Main FormPath class
│   │   │   ├── parser.ts       # Path string parser
│   │   │   ├── tokenizer.ts    # Path tokenization
│   │   │   ├── matcher.ts      # Path pattern matching
│   │   │   ├── destructor.ts   # Path destructuring
│   │   │   ├── tokens.ts       # Token definitions
│   │   │   ├── contexts.ts     # Parsing contexts
│   │   │   ├── shared.ts       # Path utilities
│   │   │   └── types.ts        # Path type definitions
│   │
│   ├── grid/                   # Grid layout system (@formily/grid)
│   │   ├── src/
│   │   │   ├── index.ts        # Grid container component
│   │   │   └── observer.ts     # Grid responsive observer
│   │
│   ├── antd/                   # Ant Design component library (@formily/antd)
│   │   ├── src/
│   │   │   ├── form/           # Form wrapper component
│   │   │   ├── form-item/      # FormItem field wrapper
│   │   │   ├── form-layout/    # Layout configuration
│   │   │   ├── form-grid/      # Grid layout integration
│   │   │   ├── form-dialog/    # Dialog-based forms
│   │   │   ├── form-drawer/    # Drawer-based forms
│   │   │   ├── form-tab/       # Tab-based forms
│   │   │   ├── form-step/      # Step/wizard forms
│   │   │   ├── form-collapse/  # Collapsible form sections
│   │   │   ├── form-button-group/  # Form action buttons
│   │   │   ├── array-base/     # Array field utilities
│   │   │   ├── array-table/    # Table-based array fields
│   │   │   ├── array-cards/    # Card-based array fields
│   │   │   ├── array-tabs/     # Tab-based array fields
│   │   │   ├── array-collapse/ # Collapsible array fields
│   │   │   ├── array-items/    # Custom array item renderer
│   │   │   ├── input/          # Text input wrapper
│   │   │   ├── password/       # Password input wrapper
│   │   │   ├── number-picker/  # Number input wrapper
│   │   │   ├── select/         # Select dropdown wrapper
│   │   │   ├── select-table/   # Table-based select
│   │   │   ├── tree-select/    # Tree select wrapper
│   │   │   ├── cascader/       # Cascading select wrapper
│   │   │   ├── transfer/       # Transfer list wrapper
│   │   │   ├── checkbox/       # Checkbox wrapper
│   │   │   ├── radio/          # Radio button wrapper
│   │   │   ├── switch/         # Switch toggle wrapper
│   │   │   ├── date-picker/    # Date picker wrapper
│   │   │   ├── time-picker/    # Time picker wrapper
│   │   │   ├── upload/         # File upload wrapper
│   │   │   ├── editable/       # Inline editable component
│   │   │   ├── preview-text/   # Read-only text preview
│   │   │   ├── space/          # Spacing component
│   │   │   ├── submit/         # Submit button
│   │   │   ├── reset/          # Reset button
│   │   │   ├── __builtins__/   # Internal utilities
│   │   │   └── style.less      # Component styles
│   │   ├── create-style.ts     # Style generation script
│   │   └── build-style.ts      # Style build script
│   │
│   ├── next/                   # Alibaba Fusion component library (@formily/next)
│   │   └── src/                # (Similar structure to antd package)
│   │
│   ├── element/                # Element UI component library (@formily/element)
│   │   └── src/                # (Similar structure to antd package)
│   │
│   ├── benchmark/              # Performance benchmarking tools
│   │   └── src/
│   │       └── index.tsx       # Benchmark test cases
│   │
│   └── reactive-test-cases-for-react18/  # React 18 compatibility tests
│       └── src/
│           └── MySlowList.js   # Concurrent rendering tests
│
├── devtools/                   # Development and debugging tools
│   └── (Internal development utilities)
│
├── docs/                       # Documentation source
│   ├── guide/                  # User guides and tutorials
│   │   ├── index.md           # Introduction
│   │   ├── quick-start.zh-CN.md   # Quick start guide
│   │   ├── form-builder.zh-CN.md  # Form builder guide
│   │   ├── contribution.md     # Contribution guidelines
│   │   └── upgrade.md          # Migration guide
│   ├── functions/              # API function documentation
│   └── site/                   # Website configuration
│
├── scripts/                    # Build and automation scripts
│   └── rollup.base.js         # Shared Rollup configuration
│
├── .github/                    # GitHub workflows and templates
│   └── workflows/              # CI/CD pipelines
│
├── lerna.json                  # Lerna monorepo configuration
├── package.json                # Root package.json with workspace config
├── tsconfig.json               # Root TypeScript configuration
├── tsconfig.build.json         # Build-specific TypeScript config
├── tsconfig.jest.json          # Test-specific TypeScript config
├── jest.config.js              # Jest testing configuration
├── .umirc.js                   # Dumi documentation config
├── rollup.config.js            # Rollup bundling configuration
├── .eslintrc                   # ESLint configuration
├── .prettierrc.js              # Prettier configuration
├── commitlint.config.js        # Commit message linting
├── CHANGELOG.md                # Version changelog
└── README.md                   # Repository documentation
```

## Module and Package Organization

**Core Packages** (framework-agnostic):
- `@formily/reactive`: Reactive state management foundation
- `@formily/core`: Form logic and field models
- `@formily/shared`: Common utilities shared across packages
- `@formily/path`: Path resolution and manipulation
- `@formily/validator`: Validation engine
- `@formily/json-schema`: Schema interpretation and compilation

**Framework Bindings**:
- `@formily/react`: React integration with hooks and components
- `@formily/vue`: Vue integration for Vue 2 and Vue 3
- `@formily/reactive-react`: Reactive system for React components
- `@formily/reactive-vue`: Reactive system for Vue components

**Component Libraries**:
- `@formily/antd`: Ant Design component wrappers
- `@formily/next`: Alibaba Fusion component wrappers
- `@formily/element`: Element UI component wrappers
- `@formily/grid`: Responsive grid layout system

## Main Source Directories and Their Purposes

**packages/core/src/models/**: Contains the core domain models implementing form state management. The Form class orchestrates overall form behavior, while Field, ArrayField, ObjectField, and VoidField represent different field types with specific value semantics. The Graph manages field dependencies, and Heart schedules lifecycle events.

**packages/reactive/src/**: Implements the reactive programming foundation. The observable.ts creates reactive proxies, tracker.ts manages dependency collection, and handlers.ts defines proxy trap behaviors. The annotations directory provides decorators for different observable types (deep, shallow, computed, ref).

**packages/react/src/components/**: React components that bridge Formily core with React's rendering system. SchemaField renders forms from JSON Schema, RecursionField handles nested schemas recursively, and various Field components provide typed wrappers around core field models.

**packages/json-schema/src/**: Schema compilation and transformation layer. The Schema class represents parsed schemas, compiler.ts evaluates expressions in schemas, and transformer.ts converts schemas to field configuration objects.

**packages/validator/src/**: Validation system with built-in rules, custom validator support, and internationalized messages. The validator.ts coordinates validation execution, while rules.ts and formats.ts provide standard validation functions.

**packages/antd/src/**: Ant Design component wrappers organized by component type. Each subdirectory contains a component wrapper, its styles, and TypeScript definitions. The __builtins__ directory provides shared component utilities.

## Key Files and Their Roles

**packages/core/src/models/Form.ts**: The central Form class managing form lifecycle, field registration, validation coordination, and submission handling. Contains approximately 1000+ lines implementing the complete form state machine.

**packages/reactive/src/observable.ts**: Entry point for creating reactive state. Exports the observable function and its variants (box, ref, shallow, deep, computed) that underpin all state management.

**packages/react/src/components/SchemaField.tsx**: Critical component for JSON Schema-driven rendering. Creates the SchemaField factory function that consumers use to build schema-driven forms.

**packages/shared/src/path.ts**: Exports FormPath class for field path manipulation. Supports destructuring, wildcards, and complex path operations essential for field queries and batch updates.

**packages/core/src/shared/externals.ts**: Public API surface for @formily/core. Exports the createForm factory function and all public utilities, serving as the main entry point.

**scripts/rollup.base.js**: Shared Rollup configuration generator creating UMD, development, and production builds for all packages with consistent external mappings and plugin configurations.

**lerna.json**: Monorepo configuration defining workspace structure, version management strategy (exact versions), and npm client settings.

## Code Organization Patterns

**Separation of Concerns**: Each package has a single, well-defined responsibility. Core packages are framework-agnostic, bindings adapt to frameworks, and component libraries provide concrete implementations.

**Reactive Architecture**: All state mutations flow through the reactive system. Components observe reactive state and automatically re-render on changes, achieving O(1) update complexity.

**Plugin Architecture**: Effects system allows hooking into lifecycle events. Validators, formats, and rules are registered via plugin APIs, enabling extensibility without modifying core code.

**TypeScript-First**: Comprehensive type definitions in dedicated types.ts files. Generic types allow type-safe form models with custom value types.

**Monorepo Structure**: Lerna manages interdependencies with yarn workspaces. All packages share build configuration but maintain independent entry points for tree-shaking.

**Documentation Co-location**: Each package includes its own docs/ directory with API documentation, guides, and examples specific to that package's functionality.

**Test Organization**: Tests live in __tests__ directories adjacent to source code, using Jest with @testing-library for component testing.
