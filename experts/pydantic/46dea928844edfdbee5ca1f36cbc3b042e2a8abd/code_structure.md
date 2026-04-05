# Pydantic — Code Structure

## Annotated Directory Tree

```
pydantic/                          # Root of the repository
├── pyproject.toml                 # Build system config, project metadata, dependencies, tool configs
├── Makefile                       # Developer workflow commands (install, test, lint, docs, etc.)
├── uv.lock                        # Locked dependency manifest for uv package manager
├── mkdocs.yml                     # Documentation site configuration (Material theme)
├── build-docs.sh                  # Script to build documentation
├── update_v1.sh                   # Script to sync/update the pydantic V1 compatibility namespace
├── HISTORY.md                     # Full changelog
├── CITATION.cff                   # Academic citation metadata
├── README.md                      # Project overview and quick-start
│
├── pydantic/                      # Main Python package source
│   ├── __init__.py                # Public API surface; lazy imports via __getattr__; __all__ definition
│   ├── version.py                 # VERSION constant ("2.13.0b3"), version_info(), version checking
│   ├── main.py                    # BaseModel class, create_model() factory function
│   ├── root_model.py              # RootModel — single-root-field model variant
│   ├── type_adapter.py            # TypeAdapter — validate/serialize arbitrary types
│   ├── fields.py                  # Field(), FieldInfo, PrivateAttr, computed_field, FieldInfoInputs
│   ├── config.py                  # ConfigDict TypedDict, with_config decorator, ExtraValues
│   ├── dataclasses.py             # @dataclass decorator with Pydantic validation, rebuild_dataclass
│   ├── validate_call_decorator.py # @validate_call decorator for function argument validation
│   ├── functional_validators.py   # AfterValidator, BeforeValidator, PlainValidator, WrapValidator,
│   │                              #   SkipValidation, ValidateAs, InstanceOf, @field_validator,
│   │                              #   @model_validator
│   ├── functional_serializers.py  # PlainSerializer, WrapSerializer, SerializeAsAny,
│   │                              #   @field_serializer, @model_serializer
│   ├── json_schema.py             # GenerateJsonSchema, model_json_schema(), JsonSchemaValue,
│   │                              #   WithJsonSchema, DEFAULT_REF_TEMPLATE
│   ├── aliases.py                 # AliasPath, AliasChoices, AliasGenerator
│   ├── annotated_handlers.py      # GetCoreSchemaHandler, GetJsonSchemaHandler protocols
│   ├── types.py                   # Built-in constrained/specialized types (Strict*, Secret*,
│   │                              #   UUID*, FilePath, Json, Base64*, PaymentCardNumber, etc.)
│   ├── networks.py                # Network types: AnyUrl, HttpUrl, EmailStr, IPvAny*, DSN types
│   ├── errors.py                  # PydanticUserError, PydanticUndefinedAnnotation, PydanticErrorCodes
│   ├── warnings.py                # PydanticDeprecatedSince* warning classes, PydanticExperimentalWarning
│   ├── mypy.py                    # Full mypy plugin implementation
│   ├── color.py                   # Color type (legacy, kept for compatibility)
│   ├── alias_generators.py        # Alias generation utilities (to_camel, to_snake, etc.)
│   ├── schema.py                  # Deprecated V1 schema() support
│   ├── generics.py                # Deprecated V1 generics support
│   ├── class_validators.py        # Deprecated V1 class validator shims
│   ├── decorator.py               # Deprecated V1 validate_arguments shim
│   ├── datetime_parse.py          # Deprecated V1 datetime parsing
│   ├── env_settings.py            # Deprecated V1 BaseSettings shim (redirects to pydantic-settings)
│   ├── error_wrappers.py          # Deprecated V1 ValidationError wrappers
│   ├── json.py                    # Deprecated V1 json utilities
│   ├── parse.py                   # Deprecated V1 parse utilities
│   ├── tools.py                   # Deprecated V1 tools
│   ├── typing.py                  # Deprecated V1 typing utilities
│   ├── utils.py                   # Deprecated V1 utils
│   ├── validators.py              # Deprecated V1 validators
│   ├── _migration.py              # getattr_migration() — attribute-level migration errors for V1→V2
│   ├── py.typed                   # PEP 561 marker: package ships type stubs/annotations
│   │
│   ├── _internal/                 # Implementation internals (not public API)
│   │   ├── __init__.py
│   │   ├── _generate_schema.py    # Core: Python types → pydantic-core CoreSchema conversion
│   │   │                          #   GenerateSchema class, all type handlers, schema generation logic
│   │   ├── _model_construction.py # ModelMetaclass, model building, _ModelNamespaceDict, mocks
│   │   ├── _config.py             # ConfigWrapper, ConfigWrapperStack — internal config representation
│   │   ├── _fields.py             # Field collection, PydanticExtraInfo, is_valid_field_name
│   │   ├── _decorators.py         # Decorator introspection, PydanticDescriptorProxy, DecoratorInfos
│   │   ├── _decorators_v1.py      # V1 decorator compatibility layer
│   │   ├── _generics.py           # Generic model support, PydanticGenericMetadata, type param mapping
│   │   ├── _discriminated_union.py # Discriminated union handling and tag resolution
│   │   ├── _typing_extra.py       # Extended typing utilities, eval_type_backport, annotation resolution
│   │   ├── _forward_ref.py        # Forward reference handling and deferred annotation support
│   │   ├── _namespace_utils.py    # Namespace resolution, NsResolver, MappingNamespace
│   │   ├── _known_annotated_metadata.py # Processing of annotated type metadata constraints
│   │   ├── _core_metadata.py      # CoreMetadata dataclass, schema metadata management
│   │   ├── _core_utils.py         # Utilities for CoreSchema inspection and manipulation
│   │   ├── _schema_gather.py      # Schema collection during model construction
│   │   ├── _schema_generation_shared.py # Shared schema generation state and helpers
│   │   ├── _mock_val_ser.py       # Mock validators/serializers for deferred model building
│   │   ├── _serializers.py        # Serializer helper implementations
│   │   ├── _validators.py         # Validator helper implementations
│   │   ├── _validate_call.py      # validate_call implementation internals
│   │   ├── _dataclasses.py        # Pydantic dataclass implementation, PydanticDataclass protocol
│   │   ├── _signature.py          # generate_pydantic_signature() for __init__ synthesis
│   │   ├── _repr.py               # __repr__ helpers, ReprArgs
│   │   ├── _docs_extraction.py    # Extract docstrings for field descriptions
│   │   ├── _import_utils.py       # Cached model imports to avoid circular deps
│   │   ├── _internal_dataclass.py # Internal dataclass utilities (slots_true)
│   │   ├── _utils.py              # General utilities: LazyClassAttribute, SafeGetItemProxy, etc.
│   │   └── _git.py                # Git utilities for version_info()
│   │
│   ├── plugin/                    # Plugin system
│   │   ├── __init__.py            # Plugin protocol definitions: PydanticPluginProtocol,
│   │   │                          #   ValidatePythonHandlerProtocol, ValidateJsonHandlerProtocol,
│   │   │                          #   ValidateStringsHandlerProtocol, SchemaTypePath, SchemaKind
│   │   ├── _loader.py             # Plugin discovery and loading via entry points
│   │   └── _schema_validator.py   # PluggableSchemaValidator wrapping pydantic-core SchemaValidator
│   │
│   ├── deprecated/                # V1 backward-compatibility shims
│   │   ├── __init__.py
│   │   ├── class_validators.py    # @validator, @root_validator (V1 decorators)
│   │   ├── config.py              # BaseConfig, Extra enum (V1 config)
│   │   ├── copy_internals.py      # V1 _iter, _copy_and_set_values, _get_value
│   │   ├── decorator.py           # V1 validate_arguments
│   │   ├── json.py                # V1 json utilities
│   │   ├── parse.py               # V1 parse_obj, parse_raw, parse_file
│   │   └── tools.py               # V1 parse_obj_as, schema_json_of, schema_of
│   │
│   ├── experimental/              # Experimental APIs (subject to change)
│   │   ├── __init__.py
│   │   ├── pipeline.py            # Composable validation/transformation pipeline API
│   │   ├── arguments_schema.py    # Experimental arguments schema support
│   │   └── missing_sentinel.py    # Missing sentinel value for experimental features
│   │
│   └── v1/                        # Full Pydantic V1 implementation (for incremental migration)
│       └── ...                    # Complete V1 package (not analyzed in detail)
│
├── pydantic-core/                 # Rust workspace member: the core validation/serialization engine
│   ├── Cargo.toml                 # Rust package config
│   ├── build.rs                   # Rust build script
│   ├── src/                       # Rust source code
│   ├── python/                    # Python bindings (pydantic_core Python package)
│   └── tests/                     # pydantic-core tests (symlinked into tests/pydantic_core)
│
├── tests/                         # Test suite
│   ├── conftest.py                # pytest fixtures and configuration
│   ├── benchmarks/                # Performance benchmarks
│   ├── mypy/                      # Mypy integration tests
│   ├── plugin/                    # Plugin system tests
│   ├── test_main.py               # BaseModel core tests
│   ├── test_types.py              # Type tests
│   ├── test_config.py             # Config tests
│   ├── test_validators.py         # Validator tests
│   ├── test_json_schema.py        # JSON Schema tests
│   ├── test_generics.py           # Generic model tests
│   └── test_*.py                  # Many more test modules
│
└── docs/                          # Documentation source (MkDocs + Material)
    ├── concepts/                  # Core concepts documentation
    ├── api/                       # API reference docs
    ├── examples/                  # Runnable example scripts
    └── ...
```

## Module and Package Organization

### Public API Layer (`pydantic/`)

The package uses a **lazy import pattern** in `__init__.py`: all imports are defined under `TYPE_CHECKING` for IDE/type-checker support, with runtime imports resolved via `__getattr__`. This keeps import time fast while providing full IDE completion.

Public modules correspond directly to conceptual areas:
- **Model definition**: `main.py`, `root_model.py`, `fields.py`, `config.py`
- **Validation**: `functional_validators.py`, `type_adapter.py`, `validate_call_decorator.py`, `dataclasses.py`
- **Serialization**: `functional_serializers.py`
- **Types**: `types.py`, `networks.py`, `aliases.py`
- **Schema**: `json_schema.py`, `annotated_handlers.py`
- **Infrastructure**: `errors.py`, `warnings.py`, `version.py`
- **Tooling**: `mypy.py`

### Internal Implementation (`pydantic/_internal/`)

The `_internal/` package is the most complex part of the codebase:

- **`_generate_schema.py`** is the largest file and most important internal module. It contains the `GenerateSchema` class with handlers for every Python type (primitives, collections, generics, TypedDicts, dataclasses, etc.) that converts them into pydantic-core's `CoreSchema` format.
- **`_model_construction.py`** contains `ModelMetaclass` — the metaclass responsible for intercepting class creation, collecting fields and decorators, generating the schema, and setting up the model.
- **`_config.py`** provides `ConfigWrapper`, an internal proxy around `ConfigDict` that exposes configuration as typed attributes.
- **`_generics.py`** handles the complex logic for generic models and type parameter substitution.
- **`_decorators.py`** processes `@field_validator`, `@model_validator`, `@field_serializer`, `@model_serializer` decorated functions and wraps them into `PydanticDescriptorProxy` objects.

### Plugin System (`pydantic/plugin/`)

Plugins implement `PydanticPluginProtocol` and are discovered via Python entry points (`pydantic` group). The `PluggableSchemaValidator` wraps `pydantic_core.SchemaValidator` and dispatches lifecycle callbacks.

## Code Organization Patterns

1. **Schema-driven architecture**: All validation and serialization goes through pydantic-core schema objects. Python type information is first translated to `CoreSchema` by `_generate_schema.py`, then passed to Rust for efficient processing.

2. **`__get_pydantic_core_schema__` protocol**: Custom types and validators implement this method to participate in schema generation, enabling extensibility without modifying internal code.

3. **`__get_pydantic_json_schema__` protocol**: Custom types implement this to control their JSON Schema representation.

4. **Metaclass-based model construction**: `ModelMetaclass` in `_model_construction.py` intercepts `__new__` to inspect the class body, build field info, apply decorators, and generate/cache the core schema and serializer.

5. **V1 compatibility via `deprecated/` and `v1/`**: The `_migration.py` module uses `__getattr__` to raise informative errors when V1 APIs are accessed, guiding migration. The full `v1/` sub-package provides an escape hatch.

6. **Deferred building**: Models can use `defer_build=True` in config, causing schema generation to be deferred until first use, which is important for handling forward references and circular type dependencies.
