This expert specializes in:

### Core Form Architecture
- **Distributed State Management**: Field-level state isolation for O(1) rendering complexity (`packages/core/src/models/`)
- **Reactive System**: Custom reactive implementation with dependency tracking (`packages/reactive/src/observable.ts`, `packages/reactive/src/tracker.ts`)
- **Form Lifecycle Management**: Form initialization, mounting, validation, submission workflows (`packages/core/src/models/Form.ts`)
- **Field Models**: Field, ArrayField, ObjectField, VoidField implementations with distinct value semantics
- **Effect System**: Lifecycle hooks and event-driven form behavior (`packages/core/src/effects/`)
- **Field Graph**: Dependency graph management for complex field relationships (`packages/core/src/models/Graph.ts`)

### React Integration
- **React Bindings**: FormProvider, Field, ArrayField, ObjectField, VoidField components (`packages/react/src/components/`)
- **React Hooks**: useForm, useField, useFieldSchema, useFormEffects, useParentForm (`packages/react/src/hooks/`)
- **Component Connection**: connect, mapProps, mapReadPretty HOCs for custom components (`packages/react/src/shared/connect.ts`)
- **Schema Rendering**: SchemaField, RecursionField for JSON Schema-driven forms (`packages/react/src/components/SchemaField.tsx`)
- **Reactive React**: Observer pattern integration for React components (`packages/reactive-react/src/`)

### Vue Integration
- **Vue Bindings**: Vue 2 and Vue 3 dual support via vue-demi (`packages/vue/src/`)
- **Composition API**: Vue composition functions and reactive hooks (`packages/vue/src/hooks/`)
- **Vue Observer**: Reactive component wrapper for Vue (`packages/reactive-vue/src/observer/`)
- **Version Switching**: CLI tools for Vue version migration (`packages/vue/bin/`)

### JSON Schema System
- **Schema Class**: Schema parsing, navigation, and manipulation (`packages/json-schema/src/schema.ts`)
- **Expression Compiler**: Dynamic expression evaluation in schemas (`packages/json-schema/src/compiler.ts`)
- **Schema Transformer**: Schema-to-field-props conversion (`packages/json-schema/src/transformer.ts`)
- **Schema Markup**: JSX-based schema definition components (`packages/react/src/components/SchemaField.tsx`)
- **Schema Reactions**: Declarative field dependencies and effects in schemas

### Validation System
- **Validation Engine**: Async validation coordination and execution (`packages/validator/src/validator.ts`)
- **Built-in Rules**: required, max, min, pattern, format validators (`packages/validator/src/rules.ts`)
- **Format Validators**: email, url, date, phone validation (`packages/validator/src/formats.ts`)
- **Custom Validators**: Registration and extension APIs (`packages/validator/src/registry.ts`)
- **Internationalization**: Multi-language error messages (`packages/validator/src/locale.ts`)
- **Validation Strategies**: validateFirst, cross-field validation, async validation

### Component Libraries
- **Ant Design Components**: 30+ form components for Ant Design 4.x (`packages/antd/src/`)
- **Fusion Components**: Alibaba Fusion Next component wrappers (`packages/next/src/`)
- **Element UI Components**: Element UI form component integration (`packages/element/src/`)
- **Form Layouts**: FormLayout, FormGrid, FormStep, FormTab, FormCollapse patterns
- **Array Components**: ArrayTable, ArrayCards, ArrayTabs, ArrayCollapse, ArrayItems
- **Form Dialogs**: FormDialog, FormDrawer for modal form scenarios
- **Editable Components**: Inline editing with read-only/read-pretty modes

### Path System
- **FormPath Class**: Path parsing, manipulation, and pattern matching (`packages/path/src/`)
- **Path Patterns**: Wildcards, destructuring, bracket notation support
- **Path Operations**: getIn, setIn, deleteIn, existIn for nested data access
- **Path Matching**: Pattern matching for field queries and batch operations

### Advanced Features
- **Field Query System**: Complex field selection with pattern matching (`packages/core/src/models/Query.ts`)
- **Batch Operations**: Batch updates and validation across multiple fields
- **Field Dependencies**: One-to-many, many-to-one, many-to-many field linkage
- **Dynamic Forms**: Runtime field creation and removal
- **Form Patterns**: editable, disabled, readOnly, readPretty modes
- **Display States**: visible, hidden, none display control
- **Value Transformations**: Input/output value conversion and normalization

### Build and Development
- **Monorepo Structure**: Lerna + Yarn workspaces management (`lerna.json`, root `package.json`)
- **TypeScript Configuration**: Multi-target compilation (ES5, ESNext) (`tsconfig.*.json`)
- **Rollup Bundling**: UMD, ESM, CommonJS output formats (`scripts/rollup.base.js`)
- **Testing Infrastructure**: Jest with React Testing Library and Vue Test Utils (`jest.config.js`)
- **Documentation System**: Dumi-based documentation generation (`.umirc.js`)

### Performance Optimization
- **Precise Rendering**: Reactive dependency tracking for minimal re-renders
- **Field Isolation**: Independent field state updates without form-wide renders
- **Computed Values**: Memoized computed properties with automatic invalidation
- **Batch Updates**: Transaction-style batched state mutations
- **Tree Shaking**: ES module builds for optimal bundle sizes

### Form Patterns
- **Multi-Step Forms**: Wizard and stepper patterns with validation per step
- **Dialog Forms**: Modal and drawer-based forms with isolated state
- **Tab Forms**: Tab-based form organization with lazy loading
- **List Management**: Self-incrementing arrays with drag-and-drop reordering
- **Inline Editing**: Grid and table inline editing patterns
- **Query Forms**: Search and filter form patterns
- **Preview Mode**: Read-only form display with formatted values

### Integration Patterns
- **Backend-Driven Forms**: JSON Schema from API endpoints
- **Form Builders**: Visual form designer integration (Designable)
- **State Management**: Integration with Redux, MobX, Zustand
- **Routing**: Form state persistence across navigation
- **Validation Libraries**: Integration with Yup, Joi, custom validators
- **Data Fetching**: Async data loading for field options and validation
