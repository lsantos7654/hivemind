# Pydantic — Summary

## Repository Purpose and Goals

Pydantic is the most widely used Python data validation library, providing fast and extensible data validation and serialization using Python type hints. The project's core mission is to allow developers to define how data should be structured using pure, canonical Python 3.9+ type annotations, and then validate, parse, and serialize that data with high performance and clear error reporting.

The current version in this commit is **2.13.0b3** (Pydantic V2), which is a ground-up rewrite from V1. V2 delivers dramatically better performance through its Rust-powered core (`pydantic-core`), a cleaner API, improved type-checker integration, and a richer feature set.

## Key Features and Capabilities

- **Type-hint-driven validation**: Define models with standard Python type annotations; Pydantic infers validation rules automatically.
- **BaseModel**: The central class for defining data models with automatic `__init__`, validation, serialization, and JSON schema generation.
- **RootModel**: Models whose root value is a single type rather than a set of named fields.
- **Pydantic Dataclasses**: Drop-in replacement for standard `dataclasses.dataclass` with added validation.
- **TypeAdapter**: Validate and serialize arbitrary types (not just BaseModel subclasses) — useful for primitive types, TypedDicts, dataclasses, and more.
- **validate_call decorator**: Validates function arguments and return values at call time using type annotations.
- **ConfigDict**: Fine-grained model configuration including strict mode, frozen models, extra field handling, alias generation, JSON schema customization, and more.
- **Field / FieldInfo**: Rich field metadata (default values, aliases, constraints, descriptions, examples, deprecation).
- **Functional validators**: `@field_validator`, `@model_validator`, `AfterValidator`, `BeforeValidator`, `PlainValidator`, `WrapValidator`, `InstanceOf`, `SkipValidation`, `ValidateAs` for flexible validation logic.
- **Functional serializers**: `@field_serializer`, `@model_serializer`, `PlainSerializer`, `WrapSerializer`, `SerializeAsAny` for custom serialization behavior.
- **JSON Schema generation**: `model_json_schema()`, `TypeAdapter.json_schema()`, and the `GenerateJsonSchema` class for customizing JSON Schema output.
- **Alias support**: `AliasPath`, `AliasChoices`, `AliasGenerator` for mapping between Python field names and external data keys.
- **Rich built-in types**: `types.py` provides `Strict*` types, constrained numeric/string types, `SecretStr`/`SecretBytes`, `Json`, `UUID*`, `FilePath`, `DirectoryPath`, `Base64*`, `PaymentCardNumber`, `ByteSize`, datetime variants, and more.
- **Network types**: `HttpUrl`, `AnyUrl`, `EmailStr`, `NameEmail`, `IPvAnyAddress`, DSN types (PostgresDsn, RedisDsn, etc.) in `networks.py`.
- **Mypy plugin**: Full mypy plugin support for accurate type inference on Pydantic models.
- **Plugin system**: A protocol-based plugin API allowing observability tools (e.g., Pydantic Logfire) to hook into validation lifecycle events.
- **Experimental pipeline API**: Composable, chainable validation/transformation pipelines via `pydantic.experimental.pipeline`.
- **V1 backward compatibility**: `pydantic.v1` namespace ships the previous V1 implementation for incremental migration.

## Primary Use Cases and Target Audience

- **API development** (FastAPI, Django Ninja, etc.): Define request/response schemas with automatic validation and OpenAPI/JSON Schema export.
- **Settings management**: Used as the backbone of `pydantic-settings` for environment variable and config file parsing.
- **Data ingestion pipelines**: Parse and validate data from external sources (databases, APIs, files) with detailed error reporting.
- **CLI tool input validation**: Validate arguments and configuration structures.
- **ORM integration**: Use `from_attributes=True` to validate ORM objects directly into Pydantic models.
- **LLM/AI structured output**: Enforce structured output schemas for AI models via JSON Schema generation.

Target audience: Python developers (3.9+) who need robust, performant, and maintainable data validation integrated naturally with Python's type system.

## High-Level Architecture Overview

Pydantic V2 is split into two layers:

1. **Python layer** (`pydantic/`): Provides the user-facing API — `BaseModel`, `Field`, `TypeAdapter`, validators, serializers, JSON schema, config, types, aliases, and more. This layer generates **core schemas** (a Rust-compatible JSON-like schema IR) and delegates actual validation/serialization work to `pydantic-core`.

2. **Rust core** (`pydantic-core/`): A Rust extension (`pydantic_core`) compiled via PyO3. It implements the actual validation and serialization engines (`SchemaValidator`, `SchemaSerializer`) operating on core schema objects. This is the performance-critical layer.

The internal `_internal/` sub-package contains the implementation machinery: `_generate_schema.py` (Python type → core schema), `_model_construction.py` (metaclass and model building), `_fields.py`, `_decorators.py`, `_generics.py`, and more.

## Related Projects and Dependencies

- **pydantic-core** (workspace member, Rust): The validation/serialization engine.
- **typing-extensions** (≥4.14.1): Extended type hint support.
- **annotated-types** (≥0.6.0): Standardized annotated type metadata.
- **typing-inspection** (≥0.4.2): Runtime type introspection utilities.
- **pydantic-settings**: Environment variable / config file settings management built on Pydantic.
- **pydantic-extra-types**: Additional type definitions (color, phone numbers, country codes, etc.).
- **FastAPI**: Web framework that uses Pydantic as its data layer.
- **Pydantic Logfire**: Observability platform with native Pydantic plugin integration.
