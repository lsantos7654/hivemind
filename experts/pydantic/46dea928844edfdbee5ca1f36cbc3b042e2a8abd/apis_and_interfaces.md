# Pydantic — APIs and Interfaces

## Public API Entry Points

All public symbols are importable from `pydantic` directly. The package uses lazy `__getattr__` for runtime imports combined with `TYPE_CHECKING` blocks for IDE support.

```python
import pydantic
# or specifically:
from pydantic import BaseModel, Field, ConfigDict, TypeAdapter, validate_call, ...
```

---

## BaseModel — Core Class (`pydantic/main.py`)

The primary way to define validated data models.

### Definition Pattern

```python
from pydantic import BaseModel, Field
from typing import Optional

class User(BaseModel):
    id: int
    name: str = 'John Doe'
    email: Optional[str] = None
    age: int = Field(gt=0, le=150)
```

### Key Class Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `model_validate` | `(obj, *, strict, from_attributes, context, experimental_allow_partial, by_alias, by_name)` | Validate from Python object |
| `model_validate_json` | `(json_data, *, strict, context, experimental_allow_partial, by_alias, by_name)` | Validate from JSON string/bytes |
| `model_validate_strings` | `(obj, *, strict, context)` | Validate from dict of strings |
| `model_construct` | `(_fields_set, **values)` | Build instance without validation |
| `model_rebuild` | `(*, force, raise_errors, _parent_namespace_depth, _types_namespace)` | Rebuild schema (for forward refs) |
| `model_json_schema` | `(*, by_alias, ref_template, schema_generator, mode)` | Generate JSON Schema dict |
| `model_parametrized_name` | `(params)` | Override generic model naming |
| `model_post_init` | `(context)` | Hook called after `__init__` |

### Key Instance Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `model_dump` | `(*, mode, include, exclude, context, by_alias, by_name, exclude_unset, exclude_defaults, exclude_none, round_trip, warnings, serialize_as_any, fallback)` | Serialize to dict |
| `model_dump_json` | `(*, indent, include, exclude, context, by_alias, by_name, exclude_unset, exclude_defaults, exclude_none, round_trip, warnings, serialize_as_any, fallback)` | Serialize to JSON string |
| `model_copy` | `(*, update, deep)` | Copy model, optionally updating fields |

### Key Class Properties

| Property | Description |
|----------|-------------|
| `model_fields` | `dict[str, FieldInfo]` — field metadata |
| `model_computed_fields` | `dict[str, ComputedFieldInfo]` |
| `model_config` | `ConfigDict` for this model |
| `model_extra` | Extra fields dict (if `extra='allow'`) |
| `model_fields_set` | Set of field names provided at init |

---

## Field() and FieldInfo (`pydantic/fields.py`)

Used to add metadata to model fields.

```python
from pydantic import BaseModel, Field

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="Product name")
    price: float = Field(gt=0, alias="unit_price")
    sku: str = Field(pattern=r'^[A-Z]{3}-\d{4}$')
    tags: list[str] = Field(default_factory=list, max_length=10)
```

### Field() Parameters (selected)

| Parameter | Type | Description |
|-----------|------|-------------|
| `default` | `Any` | Default value |
| `default_factory` | `Callable[[], Any] \| Callable[[dict], Any]` | Factory for default |
| `alias` | `str` | Alternative field name for both validation and serialization |
| `validation_alias` | `str \| AliasPath \| AliasChoices` | Alias for validation only |
| `serialization_alias` | `str` | Alias for serialization only |
| `title` | `str` | JSON Schema title |
| `description` | `str` | JSON Schema description |
| `gt`, `ge`, `lt`, `le` | `float` | Numeric constraints |
| `min_length`, `max_length` | `int` | String/collection length constraints |
| `pattern` | `str \| Pattern` | Regex pattern constraint |
| `strict` | `bool` | Strict type checking for this field |
| `frozen` | `bool` | Make field immutable |
| `exclude` | `bool` | Exclude from serialization |
| `deprecated` | `str \| bool` | Mark field as deprecated |
| `discriminator` | `str \| Discriminator` | Union discriminator |
| `json_schema_extra` | `dict \| Callable` | Extra JSON Schema properties |

### PrivateAttr

```python
from pydantic import BaseModel, PrivateAttr

class MyModel(BaseModel):
    _internal: str = PrivateAttr(default='hidden')
    _cache: dict = PrivateAttr(default_factory=dict)
```

### computed_field

```python
from pydantic import BaseModel, computed_field

class Circle(BaseModel):
    radius: float

    @computed_field
    @property
    def area(self) -> float:
        return 3.14159 * self.radius ** 2
```

---

## ConfigDict (`pydantic/config.py`)

A `TypedDict` for model configuration. Apply via `model_config` class attribute.

```python
from pydantic import BaseModel, ConfigDict

class StrictModel(BaseModel):
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        extra='forbid',
        populate_by_name=True,
        from_attributes=True,
        revalidate_instances='always',
    )
    x: int
```

### Key ConfigDict Options

| Option | Default | Description |
|--------|---------|-------------|
| `strict` | `False` | No coercion — types must match exactly |
| `frozen` | `False` | Instances are immutable |
| `extra` | `'ignore'` | `'ignore'`, `'allow'`, or `'forbid'` extra fields |
| `populate_by_name` | `False` | Allow populating by field name even when alias is set |
| `from_attributes` | `False` | Allow validation from ORM objects |
| `arbitrary_types_allowed` | `False` | Allow non-Pydantic types in fields |
| `validate_assignment` | `False` | Validate on `model.field = value` |
| `validate_default` | `False` | Validate default values |
| `alias_generator` | `None` | Function or AliasGenerator for auto-aliasing |
| `revalidate_instances` | `'never'` | `'always'`, `'never'`, `'subclass-instances'` |
| `defer_build` | `False` | Defer schema building until first use |
| `json_encoders` | `None` | Custom JSON encoders (V1 compat) |
| `json_schema_extra` | `None` | Extra JSON Schema properties |
| `use_enum_values` | `False` | Store enum `.value` instead of enum instance |
| `ser_json_timedelta` | `'iso8601'` | `'iso8601'` or `'float'` for timedelta serialization |
| `hide_input_in_errors` | `False` | Omit input values from ValidationError messages |
| `plugin_settings` | `None` | Dict passed to plugins |

### with_config decorator

```python
from pydantic import with_config
from typing import TypedDict

@with_config({'strict': True})
class MyTypedDict(TypedDict):
    x: int
```

---

## Validators (`pydantic/functional_validators.py`)

### @field_validator

```python
from pydantic import BaseModel, field_validator

class MyModel(BaseModel):
    name: str

    @field_validator('name', mode='before')
    @classmethod
    def name_must_contain_space(cls, v: str) -> str:
        if ' ' not in v:
            raise ValueError('must contain a space')
        return v.title()
```

Modes: `'before'`, `'after'` (default), `'wrap'`, `'plain'`

### @model_validator

```python
from pydantic import BaseModel, model_validator
from typing import Any, Self

class MyModel(BaseModel):
    a: int
    b: int

    @model_validator(mode='after')
    def check_a_less_than_b(self) -> Self:
        if self.a >= self.b:
            raise ValueError('a must be less than b')
        return self
```

Modes: `'before'` (receives raw input dict), `'after'` (receives model instance), `'wrap'`

### Annotated Validators

```python
from typing import Annotated
from pydantic import AfterValidator, BeforeValidator, PlainValidator, WrapValidator

def double(v: int) -> int:
    return v * 2

MyInt = Annotated[int, AfterValidator(double)]

class Model(BaseModel):
    value: MyInt  # Validates as int, then doubles
```

- `AfterValidator(func)` — runs after core validation
- `BeforeValidator(func)` — runs before core validation
- `PlainValidator(func)` — replaces core validation entirely
- `WrapValidator(func)` — wraps around core validation
- `SkipValidation` — skip validation for a type
- `ValidateAs(type)` — validate as a different type
- `InstanceOf(type)` — require an instance of a specific type

---

## Serializers (`pydantic/functional_serializers.py`)

### @field_serializer

```python
from pydantic import BaseModel, field_serializer
from datetime import datetime

class Event(BaseModel):
    dt: datetime

    @field_serializer('dt')
    def serialize_dt(self, v: datetime) -> str:
        return v.strftime('%Y-%m-%d')
```

### @model_serializer

```python
from pydantic import BaseModel, model_serializer

class MyModel(BaseModel):
    x: int
    y: int

    @model_serializer
    def serialize_model(self) -> dict:
        return {'sum': self.x + self.y}
```

### Annotated Serializers

```python
from typing import Annotated
from pydantic import PlainSerializer, SerializeAsAny

CustomList = Annotated[list, PlainSerializer(lambda v: ','.join(v), return_type=str)]
```

- `PlainSerializer(func, return_type, when_used)` — replace default serialization
- `WrapSerializer(func, return_type, when_used)` — wrap default serialization
- `SerializeAsAny` — serialize using the actual runtime type, not the declared type

---

## TypeAdapter (`pydantic/type_adapter.py`)

Validate and serialize types that aren't BaseModel subclasses.

```python
from pydantic import TypeAdapter
from typing import List

ta = TypeAdapter(List[int])
result = ta.validate_python(['1', '2', '3'])  # [1, 2, 3]
json_result = ta.validate_json('[1, 2, 3]')

schema = ta.json_schema()
json_str = ta.dump_json([1, 2, 3])
```

### TypeAdapter Methods

| Method | Description |
|--------|-------------|
| `validate_python(obj, ...)` | Validate Python object |
| `validate_json(data, ...)` | Validate JSON string/bytes |
| `validate_strings(obj, ...)` | Validate string dict |
| `dump_python(instance, ...)` | Serialize to Python object |
| `dump_json(instance, ...)` | Serialize to JSON bytes |
| `json_schema(...)` | Generate JSON Schema |
| `json_schemas(inputs, ...)` | Generate multiple JSON Schemas |
| `get_default_value()` | Get default value for type |

---

## create_model() (`pydantic/main.py`)

Dynamically create a model class at runtime.

```python
from pydantic import create_model

DynamicModel = create_model(
    'DynamicModel',
    name=(str, ...),           # (type, default) tuple
    age=(int, 18),
    __config__=ConfigDict(strict=True),
)
instance = DynamicModel(name='Alice', age=25)
```

---

## RootModel (`pydantic/root_model.py`)

Model with a single `root` field of arbitrary type.

```python
from pydantic import RootModel
from typing import List

IntList = RootModel[List[int]]
model = IntList.model_validate([1, 2, 3])
print(model.root)  # [1, 2, 3]
print(model.model_dump())  # [1, 2, 3]
```

---

## Pydantic Dataclasses (`pydantic/dataclasses.py`)

```python
from pydantic.dataclasses import dataclass
from pydantic import Field

@dataclass
class Point:
    x: float
    y: float = Field(default=0.0, ge=0.0)

p = Point(x=1.0)  # Validated
```

Compatible with `dataclasses.asdict()`, `dataclasses.fields()`, etc.

---

## @validate_call (`pydantic/validate_call_decorator.py`)

```python
from pydantic import validate_call

@validate_call
def process(x: int, y: float = 1.0) -> str:
    return f'{x * y}'

process('3', '2.5')  # Arguments validated and coerced
```

Supports `config: ConfigDict` parameter and `validate_return=True` for return value validation.

---

## Alias System (`pydantic/aliases.py`)

```python
from pydantic import BaseModel, Field, AliasPath, AliasChoices, AliasGenerator

class UserProfile(BaseModel):
    # Deep path alias
    city: str = Field(validation_alias=AliasPath('address', 'city'))

    # Multiple alias choices
    username: str = Field(validation_alias=AliasChoices('user_name', 'username', 'login'))

class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(
        validation_alias=lambda s: ''.join(w.capitalize() if i else w for i, w in enumerate(s.split('_'))),
        serialization_alias=lambda s: s.upper()
    ))
    first_name: str  # validates from 'firstName', serializes as 'FIRST_NAME'
```

---

## JSON Schema (`pydantic/json_schema.py`)

```python
from pydantic import BaseModel
from pydantic.json_schema import GenerateJsonSchema

class MyModel(BaseModel):
    x: int

# Simple usage
schema = MyModel.model_json_schema()

# Custom schema generator
class MyGenerator(GenerateJsonSchema):
    def int_schema(self, schema):
        result = super().int_schema(schema)
        result['myCustomKey'] = 'value'
        return result

schema = MyModel.model_json_schema(schema_generator=MyGenerator)
```

`WithJsonSchema` annotation forces a specific JSON Schema:

```python
from typing import Annotated
from pydantic.json_schema import WithJsonSchema

MyType = Annotated[int, WithJsonSchema({'type': 'number', 'format': 'my-format'})]
```

---

## Plugin System (`pydantic/plugin/__init__.py`)

Plugins implement `PydanticPluginProtocol` and are registered via Python entry points (`pydantic` group).

```python
# In plugin package's pyproject.toml:
# [project.entry-points.pydantic]
# my_plugin = "my_package:MyPlugin"

from pydantic.plugin import PydanticPluginProtocol, ValidatePythonHandlerProtocol

class MyPlugin:
    def new_schema_validator(self, schema, schema_type, schema_type_path, schema_kind, config, plugin_settings):
        return MyPythonHandler(), None, None

class MyPythonHandler:
    def on_enter(self, input, **kwargs): ...
    def on_success(self, result): ...
    def on_error(self, error): ...
    def on_exception(self, exception): ...
```

---

## Custom Types via `__get_pydantic_core_schema__`

Any class can be used as a Pydantic field type by implementing the protocol:

```python
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

class MyCustomType:
    def __init__(self, value: str):
        self.value = value

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
        return core_schema.no_info_plain_validator_function(
            lambda v: cls(v) if isinstance(v, str) else v,
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda v: v.value
            )
        )
```

---

## Experimental Pipeline API (`pydantic/experimental/pipeline.py`)

```python
from pydantic.experimental.pipeline import validate_as, transform
from typing import Annotated

# Composable validation/transformation
MyStr = Annotated[str, validate_as(str).strip().lower().min_len(1)]
```

Provides chainable methods: `.str()`, `.int()`, `.float()`, `.transform(func)`, `.validate_as(type)`, `.constrain(constraint)`, `.gt()`, `.ge()`, `.lt()`, `.le()`, `.len()`, `.pattern()`, `.is_instance()`, `.not_()`, `.__or__()` (union), `.__and__()` (intersection).

---

## Built-in Types Quick Reference (`pydantic/types.py`, `pydantic/networks.py`)

```python
from pydantic.types import (
    StrictStr, StrictInt, StrictFloat, StrictBool, StrictBytes,
    PositiveInt, NegativeInt, NonNegativeInt, NonPositiveInt,
    PositiveFloat, NegativeFloat, NonNegativeFloat, FiniteFloat,
    SecretStr, SecretBytes,
    Json,                          # Parses JSON string into Python object
    Base64Bytes, Base64Str,
    Base64UrlBytes, Base64UrlStr,
    UUID1, UUID3, UUID4, UUID5, UUID6, UUID7, UUID8,
    FilePath, DirectoryPath, NewPath,
    PaymentCardNumber, ByteSize,
    PastDate, FutureDate, PastDatetime, FutureDatetime,
    AwareDatetime, NaiveDatetime,
    ImportString,                  # Validates as importable Python dotted path
    SocketPath,
)
from pydantic.networks import (
    AnyUrl, AnyHttpUrl, HttpUrl, FileUrl, FtpUrl, WebsocketUrl,
    EmailStr, NameEmail,
    IPvAnyAddress, IPvAnyInterface, IPvAnyNetwork,
    PostgresDsn, CockroachDsn, AmqpDsn, RedisDsn, MongoDsn, KafkaDsn,
)
```

---

## Error Handling

```python
from pydantic import ValidationError

try:
    User(id='not-an-int')
except ValidationError as e:
    print(e.error_count())    # Number of errors
    print(e.errors())          # List of error dicts with type, loc, msg, input, url
    print(e.json(indent=2))    # JSON representation
```

Each error dict contains:
- `type`: Error type identifier string (e.g., `'int_parsing'`, `'missing'`, `'value_error'`)
- `loc`: Tuple of field path segments
- `msg`: Human-readable message
- `input`: The invalid input value
- `url`: Link to error documentation
- `ctx`: Optional context with constraint values
