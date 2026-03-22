# TypeBox — APIs and Interfaces

## Main Entry Points

TypeBox exposes distinct API surfaces through separate import paths. Each subsystem is independently importable.

```typescript
import Type from 'typebox'             // Type namespace (default)
import { Type } from 'typebox'         // Named export
import Value from 'typebox/value'      // Value operations
import Schema from 'typebox/schema'    // JSON Schema validator
import { Compile, Validator } from 'typebox/compile'  // JIT compilation
import { Format } from 'typebox/format'               // Format registry
import { Guard } from 'typebox/guard'                 // Type guards
import { Settings } from 'typebox/system'             // Runtime settings
```

---

## 1. Type Namespace (`typebox`)

The `Type` object is the primary API for building schemas. All functions return plain JSON Schema objects augmented with TypeScript type metadata.

### Standard JSON Schema Types

```typescript
// Primitives
Type.String()                     // { type: 'string' }
Type.Number()                     // { type: 'number' }
Type.Integer()                    // { type: 'integer' }
Type.Boolean()                    // { type: 'boolean' }
Type.BigInt()                     // { type: 'bigint' }
Type.Null()                       // { type: 'null' }
Type.Undefined()                  // { type: 'undefined' }
Type.Symbol()                     // { type: 'symbol' }
Type.Any()                        // {}
Type.Unknown()                    // {}
Type.Never()                      // { not: {} }
Type.Void()                       // { type: 'void' }

// With options
Type.String({ minLength: 1, maxLength: 100, format: 'email' })
Type.Number({ minimum: 0, maximum: 100, multipleOf: 5 })
Type.Integer({ minimum: 0 })

// Composites
Type.Object({ x: Type.Number(), y: Type.Number() })
Type.Array(Type.String())
Type.Tuple([Type.Number(), Type.String()])
Type.Union([Type.String(), Type.Number()])
Type.Intersect([TypeA, TypeB])
Type.Record(Type.String(), Type.Number())
Type.Enum({ A: 'a', B: 'b' })
Type.Literal('hello')
Type.TemplateLiteral([Type.Literal('hello-'), Type.String()])
```

### Object options

```typescript
Type.Object({ ... }, {
  additionalProperties: false,
  title: 'MyObject',
  description: 'An object type',
  $id: 'MyObject'
})
```

### Static Type Inference

```typescript
import type { Static, StaticDecode, StaticEncode } from 'typebox'

const T = Type.Object({ x: Type.Number(), y: Type.Number() })

type T         = Static<typeof T>       // { x: number, y: number }
type TDecoded  = StaticDecode<typeof T> // decode direction (with Codec)
type TEncoded  = StaticEncode<typeof T> // encode direction (with Codec)
```

### TypeScript Utility Type Equivalents

```typescript
Type.Partial(T)            // Partial<T>
Type.Required(T)           // Required<T>
Type.Readonly(T)           // Readonly<T> (marks properties readonly)
Type.Pick(T, ['x'])        // Pick<T, 'x'>
Type.Omit(T, ['x'])        // Omit<T, 'x'>
Type.KeyOf(T)              // keyof T
Type.Exclude(Union, T)     // Exclude<Union, T>
Type.Extract(Union, T)     // Extract<Union, T>
Type.NonNullable(T)        // NonNullable<T>
Type.ReturnType(Fn)        // ReturnType<Fn>
Type.Parameters(Fn)        // Parameters<Fn>
Type.InstanceType(Cls)     // InstanceType<Cls>
Type.ConstructorParameters(Cls) // ConstructorParameters<Cls>
Type.Awaited(T)            // Awaited<T>
Type.Capitalize(T)         // Capitalize<T>
Type.Uncapitalize(T)       // Uncapitalize<T>
Type.Uppercase(T)          // Uppercase<T>
Type.Lowercase(T)          // Lowercase<T>
```

### Mapped Types and Index Access

```typescript
// Conditional types
Type.Conditional(T, U, TrueType, FalseType)  // T extends U ? True : False

// Indexed access
Type.Index(T, Type.KeyOf(T))  // T[keyof T]

// Mapped types
Type.Mapped(Type.KeyOf(T), (K) => Type.Index(T, K))  // { [K in keyof T]: T[K] }

// Interface (merge semantics)
Type.Interface({ name: Type.String() })
```

### Modifiers

```typescript
// Optional property (use inside Object properties)
Type.Optional(Type.String())     // marks property as optional in TObject

// Readonly property
Type.Readonly(Type.String())

// Immutable (deep readonly)
Type.Immutable(T)

// Evaluate (force type materialization)
Type.Evaluate(T)
```

### JavaScript-Native Types (non-JSON-Schema)

```typescript
Type.Promise(Type.String())
Type.Function([Type.String()], Type.Number())
Type.Constructor([Type.String()], Type.Object({ ... }))
Type.AsyncIterator(Type.String())
Type.Iterator(Type.String())
Type.Symbol()
Type.BigInt()
Type.Undefined()
Type.Void()
```

### References and Recursion

```typescript
// By $id reference
const Node = Type.Object({ value: Type.Number(), children: Type.Array(Type.Ref('Node')) }, { $id: 'Node' })

// Recursive self-reference
const T = Type.Cyclic({ Node: Type.Object({ value: Type.Number(), children: Type.Array(Type.Ref('Node')) }) }, 'Node')

// This() for recursive types
const T = Type.Recursive(Self => Type.Object({ value: Type.Number(), children: Type.Array(Self) }))
```

### Generics

```typescript
// Define a generic type
const Box = Type.Generic([Type.Parameter('T')], Type.Object({ value: Type.Infer('T') }))

// Call/instantiate with a concrete type
const NumberBox = Type.Call(Box, [Type.Number()])
// → { type: 'object', properties: { value: { type: 'number' } } }
```

### Module (Type Namespacing)

```typescript
const M = Type.Module({
  Vec2: Type.Object({ x: Type.Number(), y: Type.Number() }),
  Vec3: Type.Object({ x: Type.Number(), y: Type.Number(), z: Type.Number() })
})
const Vec2 = Type.Index(M, Type.Literal('Vec2'))
```

### Script (TypeScript DSL)

```typescript
// Parse a TypeScript type expression string at runtime
const T = Type.Script(`{ x: number, y: number, z: number }`)

// With context types
const S = Type.Script({ T }, `{ [K in keyof T]: T[K] | null }`)

// Both are fully type-inferred
type T = Static<typeof T>   // { x: number; y: number; z: number }
type S = Static<typeof S>   // { x: number | null; y: number | null; z: number | null }
```

### Options

```typescript
// Merge extra JSON Schema options onto any type
Type.Options(T, { $id: 'MyType', title: 'My Type', description: 'A type' })
```

### Codec (Bidirectional Transform)

```typescript
const DateType = Type.Codec(Type.String({ format: 'date-time' }))
  .Decode((str) => new Date(str))           // string → Date
  .Encode((date) => date.toISOString())     // Date → string

type Decoded = StaticDecode<typeof DateType>  // Date
type Encoded = StaticEncode<typeof DateType>  // string
```

### Refine (Custom Predicates)

```typescript
const Positive = Type.Refine(Type.Number(), (n) => n > 0, { message: 'Must be positive' })
```

### Unsafe (Escape Hatch)

```typescript
// Provide an arbitrary TypeScript type with no schema validation
const T = Type.Unsafe<{ custom: unknown }>({ type: 'object' })
```

---

## 2. Value Module (`typebox/value`)

All functions accept `(schema, value)` or just `(value)` where schema is not needed.

```typescript
import Value from 'typebox/value'
```

| Function | Signature | Purpose |
|---|---|---|
| `Value.Check` | `(schema, value) → boolean` | Type guard validation |
| `Value.Assert` | `(schema, value) → void` | Throws `AssertError` if invalid |
| `Value.Parse` | `(schema, value) → T` | Validate and return, or throw `ParseError` |
| `Value.Errors` | `(schema, value) → Iterator<ValueErrorType>` | Enumerate all validation errors |
| `Value.Clone` | `(value) → T` | Deep clone any value |
| `Value.Equal` | `(a, b) → boolean` | Deep structural equality |
| `Value.Hash` | `(value) → bigint` | Content-addressable hash |
| `Value.Create` | `(schema) → T` | Generate a default value from schema |
| `Value.Default` | `(schema, value) → T` | Apply `default` keywords from schema |
| `Value.Convert` | `(schema, value) → T` | Coerce types (e.g., `"42"` → `42`) |
| `Value.Clean` | `(schema, value) → T` | Remove additional properties |
| `Value.Repair` | `(schema, value) → T` | Best-effort correction (Clean + Convert + Default) |
| `Value.Mutate` | `(value, next) → void` | In-place structural mutation |
| `Value.Encode` | `(schema, value) → T` | Apply Codec encode transforms |
| `Value.Decode` | `(schema, value) → T` | Apply Codec decode transforms |
| `Value.Diff` | `(a, b) → Edit[]` | Structural diff between two values |
| `Value.Patch` | `(value, edits) → T` | Apply diff edits to a value |
| `Value.Pointer` | — | JSON Pointer (RFC 6901) operations |
| `Value.Pipeline` | `(value, [fn, fn, ...]) → T` | Composable transform pipeline |

### Example: Validate and Parse

```typescript
const T = Type.Object({ x: Type.Number(), y: Type.Number() })

if (Value.Check(T, data)) {
  // data is typed as { x: number, y: number }
}

const result = Value.Parse(T, data)  // throws ParseError if invalid

for (const error of Value.Errors(T, data)) {
  console.log(error.path, error.message)
}
```

### Example: Codec Round-Trip

```typescript
const T = Type.Codec(Type.String({ format: 'date-time' }))
  .Decode(s => new Date(s))
  .Encode(d => d.toISOString())

const decoded = Value.Decode(T, '2024-01-01T00:00:00.000Z')  // Date object
const encoded = Value.Encode(T, new Date())                    // ISO string
```

---

## 3. Compile Module (`typebox/compile`)

JIT-compiles a schema into a high-performance `Validator` object.

```typescript
import { Compile, Validator } from 'typebox/compile'

const V = Compile(Type.Object({ x: Type.Number() }))

// With context (for Ref resolution)
const V = Compile({ Node }, Type.Array(Type.Ref('Node')))
```

### `Validator<Context, Type>` Class

| Method | Return type | Purpose |
|---|---|---|
| `.Check(value)` | `value is T` | Type-guard validation |
| `.Parse(value)` | `T` | Validate and return, or throw |
| `.Errors(value)` | `TLocalizedValidationError[]` | Return all validation errors |
| `.Decode(value)` | `Decoded` | Validate + apply Codec decode |
| `.Encode(value)` | `Encoded` | Apply Codec encode |
| `.Convert(value)` | `unknown` | Type coercion |
| `.Clean(value)` | `unknown` | Remove additional properties |
| `.Create()` | `T` | Generate default value |
| `.Default(value)` | `unknown` | Apply schema defaults |
| `.Clone()` | `Validator<C, T>` | Clone the validator instance |
| `.Code()` | `string` | Return generated validation code |
| `.Type()` | `Type` | Return the original schema |
| `.Context()` | `Context` | Return the context |
| `.IsAccelerated()` | `boolean` | True if using JIT acceleration |

---

## 4. Schema Module (`typebox/schema`)

Standalone JSON Schema validator supporting Drafts 3 through 2020-12.

```typescript
import Schema from 'typebox/schema'

const C = Schema.Compile({
  type: 'object',
  required: ['x', 'y'],
  properties: {
    x: { type: 'number' },
    y: { type: 'number' }
  }
})

C.Check({ x: 1, y: 2 })  // true
const R = C.Parse({ x: 1, y: 2 })  // typed result

// Direct functions
Schema.Check(schema, value)   // → boolean
Schema.Parse(schema, value)   // → T or throw
Schema.Errors(schema, value)  // → error iterator
Schema.Build(schema)          // → compiled schema object
```

---

## 5. Format Module (`typebox/format`)

Register and use JSON Schema string format validators.

```typescript
import { Format } from 'typebox/format'

// Built-in formats: date, date-time, time, duration, email, idn-email,
// hostname, idn-hostname, ipv4, ipv6, uri, uri-reference, iri,
// iri-reference, uri-template, url, uuid, regex, json-pointer,
// json-pointer-uri-fragment, relative-json-pointer

// Register a custom format
Format.Set('my-format', (value: string) => /^custom-.+$/.test(value))

// Use in a type
const T = Type.String({ format: 'my-format' })
```

---

## 6. System Module (`typebox/system`)

Runtime configuration and utilities.

```typescript
import { Settings } from 'typebox/system'

// Get current settings
const config = Settings.Get()
// { correctiveParse: false }

// Enable corrective parsing (Convert + Default + Clean on invalid values)
Settings.Set({ correctiveParse: true })
```

---

## 7. Guard Module (`typebox/guard`)

Type guard utilities for discriminating TypeBox schemas at runtime.

```typescript
import { Guard } from 'typebox/guard'

Guard.IsString(value)     // value is string
Guard.IsNumber(value)     // value is number
Guard.IsObject(value)     // value is object
Guard.IsArray(value)      // value is array
Guard.IsBoolean(value)    // value is boolean
Guard.IsFunction(value)   // value is Function
Guard.HasPropertyKey(obj, key)  // obj has own property key
Guard.IsEqual(a, b)       // strict deep equality
```

TypeBox-specific schema guards are exported from `typebox` directly:

```typescript
import { IsObject, IsString, IsArray, IsUnion, IsSchema, IsKind } from 'typebox'

IsObject(schema)   // schema is TObject
IsString(schema)   // schema is TString
IsSchema(schema)   // schema is TSchema
IsKind(schema, 'Object')  // low-level kind check
```

---

## Configuration Options

### Schema Options (`TSchemaOptions`)

All type builder functions accept an options object as the last argument:

```typescript
{
  $schema?: string        // JSON Schema dialect URI
  $id?: string            // Unique schema identifier
  title?: string          // Human-readable title
  description?: string    // Human-readable description
  default?: unknown       // Default value
  examples?: unknown[]    // Example values
  deprecated?: boolean    // Mark as deprecated
  readOnly?: boolean      // Hint for read-only property
  writeOnly?: boolean     // Hint for write-only property
  [key: PropertyKey]: unknown  // Any additional JSON Schema keywords
}
```

### String Options

```typescript
Type.String({
  minLength?: number
  maxLength?: number
  pattern?: string       // RegExp pattern string
  format?: string        // JSON Schema format name
  contentEncoding?: string
  contentMediaType?: string
})
```

### Number/Integer Options

```typescript
Type.Number({
  minimum?: number
  maximum?: number
  exclusiveMinimum?: number
  exclusiveMaximum?: number
  multipleOf?: number
})
```

### Array Options

```typescript
Type.Array(Items, {
  minItems?: number
  maxItems?: number
  uniqueItems?: boolean
  contains?: TSchema
  minContains?: number
  maxContains?: number
})
```

### Object Options

```typescript
Type.Object(Properties, {
  additionalProperties?: boolean | TSchema
  minProperties?: number
  maxProperties?: number
  patternProperties?: Record<string, TSchema>
})
```

---

## Integration Patterns

### REST Route Validation

```typescript
import Type, { type Static } from 'typebox'
import { Compile } from 'typebox/compile'

const RequestSchema = Type.Object({ name: Type.String(), age: Type.Integer({ minimum: 0 }) })
const ResponseSchema = Type.Object({ id: Type.String(), name: Type.String() })

const requestValidator = Compile(RequestSchema)
const responseValidator = Compile(ResponseSchema)

// In request handler:
if (!requestValidator.Check(body)) {
  return { error: 400, details: requestValidator.Errors(body) }
}
const result = handler(body)  // body is typed
```

### Fastify Integration

```typescript
import fastify from 'fastify'
import Type from 'typebox'

const app = fastify()
app.post('/users', {
  schema: {
    body: Type.Object({ name: Type.String() }),
    response: { 200: Type.Object({ id: Type.String() }) }
  }
}, (req) => {
  // req.body is typed as { name: string }
  return { id: 'abc' }
})
```

### Corrective Parse Pipeline

```typescript
import Value from 'typebox/value'
import { Settings } from 'typebox/system'

Settings.Set({ correctiveParse: true })

// With correctiveParse enabled, Parse attempts Convert + Default + Clean before throwing
const T = Type.Object({ count: Type.Number() })
const result = Value.Parse(T, { count: '42' })  // → { count: 42 } (coerced)
```

### Generic Types

```typescript
const Box = Type.Generic([Type.Parameter('T')], Type.Object({ value: Type.Infer('T') }))
const NumberBox = Type.Call(Box, [Type.Number()])
type NumberBox = Static<typeof NumberBox>  // { value: number }
```

### Schema-level Validation (Ajv-alternative)

```typescript
import Schema from 'typebox/schema'

const validator = Schema.Compile({
  $schema: 'https://json-schema.org/draft/2020-12/schema',
  type: 'object',
  properties: { name: { type: 'string' } },
  required: ['name']
})

const ok = validator.Check({ name: 'Alice' })  // true
```
