# Formily Repository Summary

## Repository Purpose and Goals

Formily is a high-performance, enterprise-grade form solution developed by Alibaba's Digital Supply Chain team. The project addresses the critical challenges of building complex, data-driven forms in modern web applications, particularly focusing on React and Vue ecosystems. Formily's primary goal is to eliminate the performance bottlenecks inherent in traditional controlled form implementations while providing a comprehensive solution for dynamic form rendering, complex field linkage, and backend-driven form scenarios.

The repository represents a complete rewrite (version 2.x) that evolved from UForm through Formily 1.x, incorporating years of production experience from Alibaba's middle and back-office applications. It provides a unified framework that can handle everything from simple forms to complex scenarios involving hundreds of fields with intricate interdependencies.

## Key Features and Capabilities

**Performance Architecture**: Formily implements distributed field state management inspired by MVVM patterns, achieving O(1) rendering complexity for field updates instead of the O(n) full-tree rendering typical in React controlled forms. This is accomplished through a custom reactive system (@formily/reactive) that provides dependency tracking and precise rendering similar to MobX.

**Framework Agnostic Core**: The architecture separates the core form logic (@formily/core) from framework-specific implementations, supporting both React (@formily/react) and Vue (@formily/vue) with identical APIs and capabilities. Vue support extends to both Vue 2 and Vue 3 through vue-demi integration.

**JSON Schema Integration**: Deep integration with JSON Schema protocol enables backend-driven form rendering. The @formily/json-schema package provides schema compilation, transformation, and runtime interpretation, allowing non-technical users to configure complex forms through JSON definitions.

**Component Libraries**: Production-ready component libraries integrate with popular design systems including Ant Design (@formily/antd), Alibaba Fusion Next (@formily/next), and Element UI (@formily/element). Each library provides 30+ specialized form components with built-in validation, layout management, and accessibility features.

**Advanced Validation System**: The @formily/validator package offers extensible validation with built-in rules, custom validators, async validation, format validation, and internationalized error messages. It supports complex validation scenarios including cross-field validation and conditional validation rules.

**Path System**: A sophisticated path resolution system (@formily/path) enables precise field addressing and manipulation using dot notation, bracket notation, wildcards, and destructuring patterns, making field linkage and batch operations intuitive.

**Form Builder Support**: The ecosystem includes a visual form builder (designable-antd.formilyjs.org) enabling low-code form development, allowing designers and product managers to construct complex forms without writing code.

## Primary Use Cases and Target Audience

**Enterprise Applications**: Formily is specifically designed for middle and back-office enterprise applications where forms are complex, dynamic, and data-intensive. Common scenarios include:
- Administration dashboards with hundreds of configuration fields
- Multi-step wizards and workflows
- Dynamic query builders and filter forms
- CRUD interfaces with complex validation rules
- Data entry systems requiring real-time field linkage

**Target Audience**:
- Frontend developers building React or Vue applications with complex form requirements
- Enterprise development teams needing consistent form solutions across multiple projects
- Backend developers implementing form schemas for dynamic rendering
- Low-code platform developers seeking robust form capabilities
- Teams migrating from traditional form libraries like react-hook-form, Formik, or Element UI forms

**Specific Scenarios**:
- Self-incrementing array fields with drag-and-drop reordering
- Complex field dependencies (one-to-many, many-to-one, many-to-many linkage)
- Forms requiring different patterns (editable, disabled, read-only, preview)
- Dialog and drawer-based forms with state isolation
- Tab and step-based multi-page forms
- Grid and flexible layouts with responsive design

## High-Level Architecture Overview

Formily follows a layered architecture with clear separation of concerns:

**Reactive Layer** (@formily/reactive): Custom reactive system providing observable state management, dependency tracking, computed values, and batched updates. This layer is framework-agnostic and forms the foundation for all state management.

**Core Layer** (@formily/core): Framework-independent form logic including Form, Field, ArrayField, ObjectField, and VoidField models. Implements lifecycle management, validation coordination, field graph management, and effect systems.

**Schema Layer** (@formily/json-schema): JSON Schema compiler and transformer that converts schema definitions into runtime field configurations. Supports schema nesting, references, expressions, and dynamic schema manipulation.

**Bridge Layer** (@formily/react, @formily/vue): Framework-specific adapters that bridge core models with UI components. Provides hooks, context providers, and rendering utilities specific to each framework.

**Component Layer** (@formily/antd, @formily/next, @formily/element): Pre-built component libraries implementing common form patterns with design system integration.

**Utility Layers**: Supporting packages including @formily/shared (common utilities), @formily/path (path resolution), @formily/validator (validation engine), and @formily/grid (layout system).

The architecture enables progressive enhancement where developers can start with simple JSX-based forms and gradually adopt JSON Schema, visual builders, and advanced features as needs evolve.

## Related Projects and Dependencies

**Core Dependencies**:
- TypeScript (^4.1.5): Full TypeScript implementation with comprehensive type definitions
- Lerna (^4.0.0): Monorepo management for 15+ packages
- Rollup (^2.37.1): Module bundling for UMD, ESM, and CommonJS outputs
- Jest (^26.0.0): Testing framework with extensive test coverage

**React Ecosystem** (peer dependencies):
- React ^16.8.0 / ^18.0.0: Hooks-based React integration
- React DOM ^16.8.0 / ^18.0.0: DOM rendering support
- React-is ^16.8.0: React element type checking

**Vue Ecosystem** (peer dependencies):
- Vue ^2.6.0 / >=3.0.0: Dual Vue version support
- @vue/composition-api ^1.0.0: Composition API for Vue 2
- vue-demi >=0.13.6: Vue version abstraction layer

**Design System Integration**:
- Ant Design ^4.0.0: Enterprise-class UI design language
- @alifd/next ^1.19.1: Alibaba Fusion design system
- Element UI: Vue-based component library

**Related Projects**:
- Designable (github.com/alibaba/designable): Visual form builder and designer
- FormBuilder: Low-code form construction tool
- IceJS (github.com/alibaba/ice): Application framework integration

**Development Tools**:
- Dumi (^1.1.53): Documentation generation framework
- ESLint, Prettier: Code quality and formatting
- Commitlint: Conventional commit enforcement
- Testing Library: Component testing utilities

The repository maintains version synchronization across all packages (currently 2.3.7) and publishes to npm with public access, ensuring consistent behavior across the entire ecosystem.
