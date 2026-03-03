# Joi - JavaScript Object Schema Validation

## Overview

Joi is the most powerful schema description language and data validator for JavaScript. Developed as part of the hapi.js ecosystem, it provides a simple, intuitive, and readable API for describing and validating data structures. The library enables developers to define complex validation rules using a fluent, chainable interface that emphasizes clarity and maintainability.

## Purpose and Goals

The primary purpose of Joi is to provide robust data validation for JavaScript applications. It allows developers to:

- Define schemas that describe the shape and constraints of data structures
- Validate incoming data against these schemas with detailed error reporting
- Transform and coerce data types during validation
- Create reusable validation schemas that can be composed and extended
- Support both synchronous and asynchronous validation workflows
- Provide clear, customizable error messages for validation failures

Joi is designed to be the definitive solution for data validation in JavaScript, prioritizing developer experience, performance, and flexibility.

## Key Features and Capabilities

### Rich Type System

Joi provides comprehensive built-in types including `string`, `number`, `boolean`, `date`, `array`, `object`, `binary`, `function`, `alternatives`, `link`, and `symbol`. Each type comes with specialized validation rules tailored to its domain (e.g., email validation for strings, min/max for numbers, pattern matching for arrays).

### Fluent API Design

The library uses immutable schema objects with a chainable API. Every method call returns a new schema instance, enabling clean, readable validation rules like `Joi.string().alphanum().min(3).max(30).required()`.

### Advanced Validation Features

- **References and Dependencies**: Define relationships between fields using `Joi.ref()` and conditional validation with `.when()`
- **Custom Validation**: Extend schemas with custom validation functions via `.custom()` method
- **Schema Composition**: Combine schemas using `.concat()`, `.alternatives()`, and `.link()` for recursive structures
- **Type Coercion**: Automatic type conversion (e.g., string to number) with configurable strictness
- **Contextual Validation**: Access external context data during validation for dynamic rules

### Extensibility

Joi supports creating custom types through its extension system. Developers can define new types with custom validation logic, coercion rules, and error messages, fully integrated with the core type system.

### Browser Support

The library includes a browser build generated via webpack, making it usable in both Node.js and browser environments. The browser bundle is optimized for size and includes polyfills for Node.js-specific features.

### TypeScript Support

Joi ships with comprehensive TypeScript definitions (2,659 lines), providing full type safety and IntelliSense support for TypeScript users.

## Primary Use Cases and Target Audience

### Use Cases

1. **API Request Validation**: Validate incoming HTTP request payloads, query parameters, and headers in web applications
2. **Configuration Validation**: Ensure application configuration files and environment variables meet expected schemas
3. **Form Validation**: Validate user input from web forms with complex interdependencies
4. **Data Transformation**: Parse and coerce incoming data into the correct types with validation
5. **Schema-Driven Development**: Use schemas as a source of truth for data structures across application layers
6. **Testing**: Define expected data shapes in test assertions

### Target Audience

- **Backend Developers**: Building REST APIs, GraphQL servers, or microservices that need robust input validation
- **Full-Stack Developers**: Implementing end-to-end validation for web applications
- **Library Authors**: Creating reusable components with validated configuration options
- **Enterprise Teams**: Requiring standardized, maintainable validation across large codebases

## High-Level Architecture

### Core Components

**Base Schema System** (`lib/base.js`): Implements the foundational `Base` class that all schema types extend. Provides core functionality for cloning, validation orchestration, rules management, and schema composition.

**Type System** (`lib/types/`): Contains implementations for all built-in types. Each type extends the base `any` type and adds type-specific validation rules and coercion logic.

**Validation Engine** (`lib/validator.js`): Coordinates the validation process, managing state, errors, external validations, and async operations. Handles both `validate()` and `validateAsync()` entry points.

**Error System** (`lib/errors.js`): Manages error reporting with the `ValidationError` class and `Report` class for individual validation failures. Supports customizable error messages via templates.

**Reference System** (`lib/ref.js`): Implements references to other parts of the data being validated, enabling field dependencies and contextual validation.

**Template Engine** (`lib/template.js`): Provides string templating for dynamic error messages and value transformation using a mathematical expression syntax.

**Compilation** (`lib/compile.js`): Converts plain JavaScript objects and shorthand notations into full Joi schema objects.

**Extension System** (`lib/extend.js`): Allows creation of custom types by extending existing ones with new rules, flags, and validation logic.

### Architecture Patterns

Joi uses an **immutable schema** pattern where every method returns a new schema instance, preventing unintended mutations. The validation process follows a **pipeline architecture** with stages for coercion, value validation, rule evaluation, and error collection. The **extension pattern** allows types to build on each other hierarchically (e.g., `keys` extends `any`, `object` extends `keys`).

## Related Projects and Dependencies

### Core Dependencies

- **@hapi/hoek**: Utility functions for object manipulation, deep cloning, and assertions
- **@hapi/address**: Email and domain validation with URI/IP regex support
- **@hapi/tlds**: Top-level domain list for email validation
- **@hapi/topo**: Topological sorting for dependency management
- **@hapi/formula**: Mathematical formula parsing for template expressions
- **@hapi/pinpoint**: Error location tracking in validation
- **@standard-schema/spec**: Standard schema specification compliance

### Development Tools

- **@hapi/lab**: Testing framework (100% code coverage requirement)
- **@hapi/code**: Assertion library for tests
- **@hapi/eslint-plugin**: Code quality enforcement
- **TypeScript**: Type definition generation and validation

### Related Projects

- **hapi.js**: Web framework that originally drove Joi's development
- **joi.dev**: Official documentation portal and developer resources
- Part of the broader **hapi.js ecosystem** including modules for server-side validation, configuration, and utilities

### Version and Compatibility

Current version: 18.0.2, requiring Node.js >= 20. The library maintains backward compatibility through semantic versioning and supports legacy schema compilation for older Joi versions.
