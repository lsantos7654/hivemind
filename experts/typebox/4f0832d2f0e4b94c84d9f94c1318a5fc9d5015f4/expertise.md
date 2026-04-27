### Type Construction (src/type/)
- Creating primitive types: Any, Array, BigInt, Boolean, Integer, Literal, Never, Null, Number, Object, String, Symbol, Tuple, Undefined, Union, Unknown, Unsafe, Void
- Creating JavaScript-native types: AsyncIterator, Constructor, Function, Iterator, Promise
- Composite types: Intersect, Record, Enum, TemplateLiteral
- TypeScript utility type equivalents: Partial, Required, Readonly, ReadonlyType, Pick, Omit, KeyOf, Exclude, Extract, NonNullable, ReturnType, Parameters, ConstructorParameters, InstanceType, Awaited
- Mapped types: Mapped, Conditional, Index, Interface, Evaluate
- String intrinsics: Capitalize, Uncapitalize, Uppercase, Lowercase
- Schema options: TSchemaOptions, TStringOptions, TNumberOptions, TArrayOptions, TObjectOptions, TTupleOptions, TIntersectOptions
- Modifiers: Optional, Readonly, Immutable, Options
- Extension types: Codec, Refine, Immutable
- Recursive/self-referential types: Cyclic, Ref, This
- Generic types: Generic, Parameter, Call, Infer
- Module namespacing: Module
- TypeScript DSL: Script() runtime parser, TScript type, TScriptOptions
- Deferred/lazy types: Deferred, TDeferred
- Type instantiation engine: Instantiate, TInstantiate, InstantiateType

### Static Type Inference
- Static<T> — infer TypeScript type from TypeBox schema
- StaticDecode<T> — infer decoded type (Codec decode direction)
- StaticEncode<T> — infer encoded type (Codec encode direction)
- StaticParse<T> — infer parse direction type
- Context-aware type inference via TProperties context parameter
- StaticType<Stack, Direction, Context, This, Type> — the main conditional type dispatcher

### Value Operations (src/value/)
- Value.Check(schema, value) — boolean type guard
- Value.Assert(schema, value) — throws AssertError if invalid
- Value.Parse(schema, value) — validate or throw ParseError
- Value.Errors(schema, value) — lazy error iterator
- Value.Clone(value) — deep clone any JavaScript value
- Value.Equal(a, b) — deep structural equality
- Value.Hash(value) — content-addressable bigint hash
- Value.Create(schema) — generate default value conforming to schema
- Value.Default(schema, value) — apply schema `default` keywords
- Value.Convert(schema, value) — coerce types (string→number, etc.)
- Value.Clean(schema, value) — strip additional properties
- Value.Repair(schema, value) — best-effort correction
- Value.Mutate(value, next) — in-place structural mutation
- Value.Encode(schema, value) — apply Codec encode transforms
- Value.Decode(schema, value) — apply Codec decode transforms
- Value.Diff(a, b) — structural delta/edit list
- Value.Patch(value, edits) — apply edits to a value
- Value.Pointer — JSON Pointer (RFC 6901) get/set/delete operations
- Value.Pipeline(value, [transforms]) — composable transform chain
- HasCodec(context, schema) — detect if schema has Codec
- ParseError class — thrown by Parse on invalid data

### JIT Compilation (src/compile/)
- Compile(type) → Validator — single-schema compile
- Compile(context, type) → Validator — context-aware compile for Ref resolution
- Validator class API: Check, Parse, Errors, Decode, Encode, Convert, Clean, Create, Default, Clone, Code, Type, Context, IsAccelerated
- JIT acceleration detection (Environment.CanAccelerate)
- Generated validation code inspection via Validator.Code()
- Validator as Base<T> — base class shared with Schema-level validators
- Settings.correctiveParse — controls Parse corrective behavior

### JSON Schema Validator (src/schema/)
- Schema.Compile(jsonSchema) — compile any JSON Schema object
- Schema.Build(context, jsonSchema) — build with reference context
- Schema.Check(schema, value) — boolean validation
- Schema.Parse(schema, value) — validate or throw
- Schema.Errors(schema, value) — error enumeration
- JSON Schema Draft 3, 4, 6, 7, 2019-09, 2020-12 support
- $ref resolution and deduplication
- allOf, anyOf, oneOf, not, if/then/else, contains, unevaluatedItems, unevaluatedProperties

### Error Handling (src/error/)
- TValidationError union type — all possible JSON Schema error types
- TLocalizedValidationError — localized error messages with path and details
- TAdditionalPropertiesError, TAnyOfError, TBooleanError, TConstError, TContainsError, TDependenciesError, TDependentRequiredError, TEnumError, TExclusiveMaximumError, TExclusiveMinimumError, TFormatError, TGuardError, TIfError, TMaximumError, TMaxItemsError, TMaxLengthError, TMaxPropertiesError, TMinimumError, TMinItemsError, TMinLengthError, TMinPropertiesError, TMultipleOfError, TNotError, TOneOfError, TPatternError, TPropertyNamesError, TRefineError, TRequiredError, TTypeError, TUnevaluatedItemsError, TUnevaluatedPropertiesError, TUniqueItemsError
- ParseError class — thrown when Parse fails validation
- IsValidationError guard

### Format Validators (src/format/)
- FormatRegistry / Format.Set / Format.Get — custom format registration
- Built-in: date, date-time, time, duration, email, idn-email, hostname, idn-hostname, ipv4, ipv6, uri, uri-reference, iri, iri-reference, uri-template, url, uuid, regex, json-pointer, json-pointer-uri-fragment, relative-json-pointer
- Using formats: Type.String({ format: 'email' })
- Format validation via Value.Check when formats are registered

### Guard Utilities (src/guard/)
- Guard.IsString, IsNumber, IsBoolean, IsObject, IsArray, IsFunction, IsSymbol, IsBigInt, IsUndefined, IsNull
- Guard.HasPropertyKey — own property check
- Guard.IsEqual — strict deep equality
- Per-type schema guards: IsObject, IsString, IsArray, IsUnion, IsIntersect, IsLiteral, IsEnum, IsTuple, IsRecord, IsRef, IsNever, IsAny, IsUnknown, IsOptional, IsReadonly, IsCodec, IsRefine, IsImmutable, IsGeneric, IsSchema, IsKind
- EmitGuard — code generation helpers
- GlobalsGuard — runtime environment detection
- NativeGuard — JS native type checks

### System Utilities (src/system/)
- Settings.Get() / Settings.Set() — runtime configuration
- correctiveParse setting — enable/disable corrective parsing
- Memory.Create / Memory.Update / Memory.Discard — immutable schema object management
- Arguments.Match — overloaded function argument dispatch
- Environment.CanAccelerate — JIT availability detection
- Locale — error message localization

### Build and Tooling
- Deno-based development (deno.jsonc, tasks.ts, deno.lock)
- tasksmith task runner library
- parsebox parser combinator library (used in syntax/Script DSL)
- npm package output at target/build/ with TypeScript 5.9.3
- Multiple entry points: typebox, typebox/value, typebox/schema, typebox/compile, typebox/format, typebox/guard, typebox/system, typebox/error
- tsconfig.json path aliases for IDE support
- Test suite in test/typebox/ and test/jsonschema/

### Migration and Compatibility
- Migration from @sinclair/typebox 0.34.x to typebox 1.x
- Changelog 1.0.0-migration.md — breaking changes
- Changelog 1.1.0 — correctiveParse behavior change
- Side-by-side usage of @sinclair/typebox 0.34.x and typebox 1.x
- Static inference compatibility across versions

### Integration Patterns
- REST API validation (request/response schema validation)
- Fastify integration via JSON Schema body/response schemas
- TypeBox Compile() for high-performance repeated validation
- Route-level validation patterns (example/route/route.ts)
- Codec pattern for DTO transformations
- Corrective parse pipeline for user-facing APIs
- Generic type factories for reusable schema patterns
- MCP (Model Context Protocol) schema generation (example/mcp/)
