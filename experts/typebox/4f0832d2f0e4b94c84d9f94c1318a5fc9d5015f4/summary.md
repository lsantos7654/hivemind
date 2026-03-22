# TypeBox — Summary

## Repository Purpose and Goals

TypeBox is a **JSON Schema type builder with static TypeScript type resolution**. It creates in-memory JSON Schema objects that simultaneously infer as TypeScript types, enabling a single unified type definition to serve both compile-time type checking and runtime validation.

The core goal is to bridge the gap between TypeScript's structural type system and the JSON Schema ecosystem. Rather than maintaining separate type definitions and validators, TypeBox lets developers define one schema that TypeScript can introspect statically (`Type.Static<typeof T>`) and that standard JSON Schema validators can consume at runtime.

The library is developed by Haydn Paterson (sinclairzx81) under the MIT license. Current version at this commit is **1.1.6**. The package is published to npm as `typebox` (the modern v1 release; legacy `@sinclair/typebox` 0.34.x is maintained separately at `sinclairzx81/typebox-legacy`).

## Key Features and Capabilities

- **Type namespace** (`Type.*`): Comprehensive set of builder functions covering all standard JSON Schema constructs plus JavaScript-native types. Every function returns a plain JSON object (a schema fragment) that is directly JSON Schema compliant.
- **`Static<T>` type inference**: A TypeScript conditional type that resolves the TypeScript type corresponding to any TypeBox schema, enabling deep generic and recursive type inference.
- **Value submodule** (`typebox/value`): Runtime operations on JavaScript values — `Check`, `Parse`, `Clone`, `Convert`, `Create`, `Default`, `Encode`, `Decode`, `Diff`, `Patch`, `Hash`, `Equal`, `Repair`, `Clean`, `Assert`, and `Pointer`.
- **Schema submodule** (`typebox/schema`): A standalone JSON Schema validator supporting Drafts 3 through 2020-12. Decoupled from TypeBox types, intended as a high-performance Ajv alternative.
- **Compile submodule** (`typebox/compile`): JIT-compiles a TypeBox type into a `Validator` object with accelerated `Check`, `Parse`, `Errors`, `Decode`, `Encode`, `Convert`, `Create`, `Default`, `Clean`, and `Clone` methods.
- **Script()**: Runtime TypeScript DSL engine — parses TypeScript type expression strings (e.g., `"{ x: number, y: string }"`) into TypeBox schemas, including computed mapped types using context types.
- **Codec system**: Bidirectional encode/decode transforms attached to any type via `Codec(type).Decode(fn).Encode(fn)`, surfaced through `Value.Decode` and `Value.Encode`.
- **Refine**: Custom refinement predicates attached to any type for validation beyond JSON Schema constraints.
- **Generic types**: Parameterized type factories via `Generic([param], expression)` allowing reusable higher-kinded schemas.
- **Module**: Namespace/module construct for organizing interrelated types with cross-references.
- **Format validators** (`typebox/format`): Built-in validators for common JSON Schema string formats — email, date, date-time, time, duration, hostname, ipv4, ipv6, uuid, uri, iri, url, regex, json-pointer, and more.
- **Settings system**: Global runtime configuration (`typebox/system`) including the `correctiveParse` flag.

## Primary Use Cases and Target Audience

TypeBox targets **TypeScript developers** who need validated APIs, REST/RPC endpoints, configuration parsing, and any scenario where data crosses a trust boundary. Primary use cases include:

- **API validation**: Define request/response schemas once, get both TypeScript types and runtime validation from the same source of truth.
- **Configuration parsing**: Parse and validate user configuration with full type inference.
- **Data transformation pipelines**: Use `Value.Pipeline`, `Codec`, and `Value.Convert` for typed ETL operations.
- **Code generation and tooling**: Since TypeBox schemas are plain JSON objects they can be serialized, transmitted, and used with any JSON Schema toolchain (documentation generators, OpenAPI tools, etc.).
- **High-performance servers**: JIT-compile validators with `Compile()` for repeated validation paths.

## High-Level Architecture Overview

TypeBox is organized around four primary subsystems:

1. **Type system** (`src/type/`): Pure type construction. No runtime validation happens here — functions build JSON Schema objects that carry TypeScript type metadata. The engine handles generic instantiation; actions mirror TypeScript utility types (Partial, Omit, Pick, KeyOf, Mapped, etc.); the script module parses TypeScript DSL strings.

2. **Value system** (`src/value/`): All runtime operations on JavaScript values against TypeBox schemas. Handles validation, coercion, structural diffing, codec transforms, and JSON pointer operations.

3. **Schema system** (`src/schema/`): A self-contained, draft-agnostic JSON Schema validator. Used internally by the Value module and exportable as a standalone engine.

4. **Compile system** (`src/compile/`): JIT code generation. Emits inline JavaScript validation functions from TypeBox schemas, wrapping them in a `Validator` class that exposes the full Value API with JIT acceleration.

Supporting subsystems (`src/system/`, `src/guard/`, `src/error/`, `src/format/`) provide utilities, type guards, error types, and format registries shared across all subsystems.

## Related Projects and Dependencies

- **`parsebox`** (external): Used in the build pipeline for parser generator utilities (imported in `deno.jsonc` as a Deno URL dependency).
- **`tasksmith`** (external): Custom Deno task runner used for all build, test, and publish tasks.
- **`@sinclair/typebox` 0.34.x** (legacy): Older semver line maintained at `sinclairzx81/typebox-legacy`; the v1 API is compatible for most types.
- **Ajv**: TypeBox's Schema submodule is positioned as a lightweight alternative. TypeBox schemas are fully compatible with Ajv.
- **Fastify, tRPC, Elysia**: Common integration targets; these frameworks accept JSON Schema and can consume TypeBox schemas directly.
- **React/Three.js/React Router**: Listed as npm dependencies in `deno.jsonc` exclusively for the documentation website build.
