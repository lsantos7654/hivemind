# TypeBox — Code Structure

## Annotated Directory Tree

```
typebox/
├── src/                          # All library source code
│   ├── index.ts                  # Root package entry: re-exports type system + default Type namespace
│   ├── typebox.ts                # The `Type.*` namespace object (all builder functions collected)
│   │
│   ├── type/                     # Core type construction subsystem (no runtime validation)
│   │   ├── index.ts              # Barrel: re-exports types/, action/, engine/, script/, extends/
│   │   ├── types/                # Primitive and composite type definitions
│   │   │   ├── schema.ts         # TSchema base interface, TSchemaOptions, IsKind(), IsSchema()
│   │   │   ├── static.ts         # Static<T>, StaticDecode<T>, StaticEncode<T>, StaticParse<T> types
│   │   │   ├── properties.ts     # TProperties, TRequiredArray, StaticProperties helpers
│   │   │   ├── any.ts            # Any() → TAny
│   │   │   ├── array.ts          # Array() → TArray
│   │   │   ├── async-iterator.ts # AsyncIterator() → TAsyncIterator
│   │   │   ├── base.ts           # Base<T> abstract class (shared by Validator)
│   │   │   ├── bigint.ts         # BigInt() → TBigInt
│   │   │   ├── boolean.ts        # Boolean() → TBoolean
│   │   │   ├── call.ts           # Call() → TCall (generic invocation)
│   │   │   ├── constructor.ts    # Constructor() → TConstructor
│   │   │   ├── cyclic.ts         # Cyclic() → TCyclic (recursive/self-referential types)
│   │   │   ├── deferred.ts       # TDeferred, Deferred() — lazy instantiation token
│   │   │   ├── enum.ts           # Enum() → TEnum
│   │   │   ├── function.ts       # Function() → TFunction
│   │   │   ├── generic.ts        # Generic() → TGeneric (parameterized type factories)
│   │   │   ├── identifier.ts     # Identifier() → TIdentifier (type variable)
│   │   │   ├── infer.ts          # Infer() → TInfer (infer keyword equivalent)
│   │   │   ├── integer.ts        # Integer() → TInteger
│   │   │   ├── intersect.ts      # Intersect() → TIntersect
│   │   │   ├── iterator.ts       # Iterator() → TIterator
│   │   │   ├── literal.ts        # Literal() → TLiteral
│   │   │   ├── never.ts          # Never() → TNever
│   │   │   ├── null.ts           # Null() → TNull
│   │   │   ├── number.ts         # Number() → TNumber
│   │   │   ├── object.ts         # Object() → TObject
│   │   │   ├── parameter.ts      # Parameter() → TParameter (generic type parameter)
│   │   │   ├── promise.ts        # Promise() → TPromise
│   │   │   ├── record.ts         # Record() → TRecord
│   │   │   ├── ref.ts            # Ref() → TRef (schema reference by ID)
│   │   │   ├── rest.ts           # Rest() → TRest (rest/spread for tuples)
│   │   │   ├── string.ts         # String() → TString
│   │   │   ├── symbol.ts         # Symbol() → TSymbol
│   │   │   ├── template-literal.ts # TemplateLiteral() → TTemplateLiteral
│   │   │   ├── this.ts           # This() → TThis (recursive self-reference)
│   │   │   ├── tuple.ts          # Tuple() → TTuple
│   │   │   ├── undefined.ts      # Undefined() → TUndefined
│   │   │   ├── union.ts          # Union() → TUnion
│   │   │   ├── unknown.ts        # Unknown() → TUnknown
│   │   │   ├── unsafe.ts         # Unsafe() → TUnsafe (escape hatch)
│   │   │   ├── void.ts           # Void() → TVoid
│   │   │   ├── _codec.ts         # Codec, EncodeBuilder, DecodeBuilder, TCodec
│   │   │   ├── _immutable.ts     # Immutable() → TImmutable (deep readonly)
│   │   │   ├── _optional.ts      # Optional() → TOptional (marks property optional)
│   │   │   ├── _readonly.ts      # Readonly() → TReadonly (marks property readonly)
│   │   │   └── _refine.ts        # Refine(), TRefine, TRefinement (custom predicates)
│   │   │
│   │   ├── action/               # TypeScript utility-type equivalents as runtime actions
│   │   │   ├── index.ts          # Barrel for all action types
│   │   │   ├── awaited.ts        # Awaited<T>
│   │   │   ├── capitalize.ts     # Capitalize<T>
│   │   │   ├── conditional.ts    # Conditional<T, U, True, False> (extends ? :)
│   │   │   ├── constructor-parameters.ts # ConstructorParameters<T>
│   │   │   ├── evaluate.ts       # Evaluate<T> (force type materialization)
│   │   │   ├── exclude.ts        # Exclude<T, U>
│   │   │   ├── extract.ts        # Extract<T, U>
│   │   │   ├── indexed.ts        # Index<T, K> (indexed access types)
│   │   │   ├── instance-type.ts  # InstanceType<T>
│   │   │   ├── interface.ts      # Interface<T> (interface merge semantics)
│   │   │   ├── keyof.ts          # KeyOf<T>
│   │   │   ├── lowercase.ts      # Lowercase<T>
│   │   │   ├── mapped.ts         # Mapped<T, K, U> (mapped types)
│   │   │   ├── module.ts         # Module<Context> (type namespace)
│   │   │   ├── non-nullable.ts   # NonNullable<T>
│   │   │   ├── omit.ts           # Omit<T, K>
│   │   │   ├── options.ts        # Options<T, O> (merge schema options)
│   │   │   ├── parameters.ts     # Parameters<T>
│   │   │   ├── partial.ts        # Partial<T>
│   │   │   ├── pick.ts           # Pick<T, K>
│   │   │   ├── readonly-type.ts  # ReadonlyType<T>
│   │   │   ├── required.ts       # Required<T>
│   │   │   ├── return-type.ts    # ReturnType<T>
│   │   │   ├── uncapitalize.ts   # Uncapitalize<T>
│   │   │   └── uppercase.ts      # Uppercase<T>
│   │   │
│   │   ├── engine/               # Type instantiation engine (handles Deferred/Generic resolution)
│   │   │   ├── index.ts          # Barrel
│   │   │   ├── instantiate.ts    # Instantiate(), TInstantiate, InstantiateType, TInstantiateType
│   │   │   └── [subdirs]/        # Per-type instantiation logic (cyclic, enum, mapped, etc.)
│   │   │
│   │   ├── script/               # Runtime TypeScript DSL parser
│   │   │   ├── index.ts          # Barrel
│   │   │   ├── script.ts         # Script(), TScript — parses TS type strings into schemas
│   │   │   └── parser.ts         # Internal parser implementation (parsebox-based)
│   │   │
│   │   └── extends/              # Structural type assignability / extends checking
│   │       └── index.ts
│   │
│   ├── value/                    # Runtime value operations subsystem
│   │   ├── index.ts              # Barrel + default export
│   │   ├── value.ts              # Named exports: Assert, Check, Clean, Clone, Decode,
│   │   │                         #   Encode, Convert, Create, Default, Equal, Errors,
│   │   │                         #   Hash, Mutate, Parse, Diff, Patch, Pointer, Repair
│   │   ├── assert/               # Assert(schema, value) — throws on invalid
│   │   ├── check/                # Check(schema, value) → boolean
│   │   ├── clean/                # Clean(schema, value) — removes additional properties
│   │   ├── clone/                # Clone(value) — deep clone
│   │   ├── codec/                # Encode(schema, value) / Decode(schema, value) codec transforms
│   │   ├── convert/              # Convert(schema, value) — type coercion (string→number etc.)
│   │   ├── create/               # Create(schema) — generate default value from schema
│   │   ├── default/              # Default(schema, value) — apply schema defaults
│   │   ├── delta/                # Diff(a, b) / Patch(value, edits) — structural delta
│   │   ├── equal/                # Equal(a, b) — deep structural equality
│   │   ├── errors/               # Errors(schema, value) → validation error iterator
│   │   ├── hash/                 # Hash(value) → bigint content hash
│   │   ├── mutate/               # Mutate(value, next) — in-place structural mutation
│   │   ├── parse/                # Parse(schema, value) — validate + return or throw
│   │   ├── pipeline/             # Pipeline(value, [fns]) — composable transform chain
│   │   ├── pointer/              # Pointer — JSON Pointer (RFC 6901) operations
│   │   ├── repair/               # Repair(schema, value) — best-effort value correction
│   │   └── shared/               # Internal helpers
│   │
│   ├── schema/                   # Standalone JSON Schema validator (Draft 3–2020-12)
│   │   ├── index.ts              # Barrel + default export (Schema namespace)
│   │   ├── schema.ts             # Schema.Compile(), Schema.Build(), Schema.Check(), Schema.Parse(), Schema.Errors()
│   │   ├── build.ts              # Build() — constructs compiled schema object
│   │   ├── check.ts              # Check() — validate against compiled schema
│   │   ├── compile.ts            # Compile() — JIT compile JSON Schema to checker function
│   │   ├── parse.ts              # Parse() — validate and return or throw
│   │   ├── errors.ts             # Errors() — enumerate validation errors
│   │   ├── engine/               # Internal compilation engine
│   │   ├── static/               # XStatic type inference for schema-level types
│   │   ├── types/                # Schema-level type definitions
│   │   ├── pointer/              # Internal JSON pointer support
│   │   └── resolve/              # $ref resolution
│   │
│   ├── compile/                  # JIT compilation of TypeBox types
│   │   ├── index.ts              # Barrel: exports Compile(), Validator
│   │   ├── compile.ts            # Compile(type) / Compile(context, type) → Validator
│   │   ├── validator.ts          # Validator<Context, Type> class — full validation API
│   │   └── code.ts               # Code generation utilities
│   │
│   ├── error/                    # Validation error types
│   │   ├── index.ts              # Barrel
│   │   └── errors.ts             # TValidationError union, TLocalizedValidationError, ParseError
│   │
│   ├── format/                   # JSON Schema string format validators
│   │   ├── index.ts              # Barrel + format registry
│   │   ├── _registry.ts          # FormatRegistry — register/lookup custom formats
│   │   ├── date.ts               # date format validator
│   │   ├── date-time.ts          # date-time format validator
│   │   ├── time.ts               # time format validator
│   │   ├── duration.ts           # duration format validator
│   │   ├── email.ts              # email format validator
│   │   ├── idn-email.ts          # idn-email format validator
│   │   ├── hostname.ts           # hostname format validator
│   │   ├── idn-hostname.ts       # idn-hostname format validator
│   │   ├── ipv4.ts               # ipv4 format validator
│   │   ├── ipv6.ts               # ipv6 format validator
│   │   ├── uri.ts                # uri format validator
│   │   ├── uri-reference.ts      # uri-reference format validator
│   │   ├── iri.ts                # iri format validator
│   │   ├── iri-reference.ts      # iri-reference format validator
│   │   ├── uri-template.ts       # uri-template format validator
│   │   ├── url.ts                # url format validator
│   │   ├── uuid.ts               # uuid format validator
│   │   ├── regex.ts              # regex format validator
│   │   ├── json-pointer.ts       # json-pointer format validator
│   │   ├── json-pointer-uri-fragment.ts # json-pointer-uri-fragment format validator
│   │   └── relative-json-pointer.ts     # relative-json-pointer format validator
│   │
│   ├── guard/                    # Type guards for schema value discrimination
│   │   ├── index.ts              # Barrel: Guard, EmitGuard, GlobalsGuard, NativeGuard
│   │   ├── guard.ts              # Guard — IsString, IsNumber, IsObject, IsArray, HasPropertyKey, etc.
│   │   ├── emit.ts               # EmitGuard — code-generation guard helpers
│   │   ├── globals.ts            # GlobalsGuard — runtime globals detection
│   │   └── native.ts             # NativeGuard — JS native type checks
│   │
│   └── system/                   # Cross-cutting system utilities
│       ├── index.ts              # Barrel + System namespace
│       ├── system.ts             # Re-exports all subsystems
│       ├── arguments/            # Arguments.Match() — overload argument pattern matching
│       ├── environment/          # Environment.CanAccelerate() — JIT availability detection
│       ├── hashing/              # Internal hashing utilities
│       ├── locale/               # Error message localization
│       ├── memory/               # Memory.Create/Update/Discard — immutable schema cloning
│       ├── settings/             # Settings.Get/Set — global config (e.g. correctiveParse)
│       └── unreachable/          # Unreachable() — compile-time exhaustiveness checking
│
├── test/                         # Test suite
│   ├── common/                   # Shared test utilities (assert helpers)
│   ├── typebox/                  # TypeBox-specific tests (mirrors src/type structure)
│   └── jsonschema/               # JSON Schema spec compliance tests
│
├── example/                      # Usage examples
│   ├── index.ts                  # Main example entry
│   ├── route/route.ts            # REST route validation example
│   ├── mcp/                      # MCP (Model Context Protocol) integration example
│   ├── standard/                 # Standard usage examples
│   ├── javascript/               # JavaScript date examples
│   ├── prototype/                # Prototype/reverse-static examples
│   └── legacy/                   # Legacy 0.34.x compatibility examples
│
├── task/                         # Build task implementations
│   ├── bench/                    # Benchmark task
│   ├── syntax/                   # Parser code generation task
│   ├── website/                  # Documentation website build
│   ├── turing/                   # Turing completeness test
│   ├── range/                    # TypeScript compiler range tests
│   └── metrics/                  # Bundle size metrics
│
├── changelog/                    # Release notes
│   ├── 1.0.0.md                  # v1.0.0 release notes
│   ├── 1.1.0.md                  # v1.1.x release notes (current)
│   ├── 1.0.0-migration.md        # Migration guide from 0.34.x
│   └── legacy/                   # Historical changelogs (0.x.x)
│
├── docs/                         # Built documentation website (HTML/JS/CSS)
├── design/                       # Design artifacts (website mockup, syntax examples)
├── tasks.ts                      # Task runner entry point (deno task build/test/etc.)
├── deno.jsonc                    # Deno project config: tasks, imports, compiler options
├── tsconfig.json                 # TypeScript compiler config (strict, ES2020, ESNext modules)
├── deno.lock                     # Deno lock file
└── readme.md                     # Project README with usage examples
```

## Module and Package Organization

TypeBox uses a **subsystem barrel pattern**: each major subsystem has its own `index.ts` that re-exports from internal files, and the root `src/index.ts` aggregates everything for the main `typebox` package entry point.

The package exposes **eight distinct import paths** (configured in both `deno.jsonc` and `tsconfig.json`):

| Import path | Source | Purpose |
|---|---|---|
| `typebox` | `src/index.ts` | Main entry: all types + `Type` default namespace |
| `typebox/type` | `src/type/index.ts` | Type system only (no Value, no Schema) |
| `typebox/value` | `src/value/index.ts` | All Value operations |
| `typebox/schema` | `src/schema/index.ts` | Standalone JSON Schema validator |
| `typebox/compile` | `src/compile/index.ts` | JIT compilation + Validator class |
| `typebox/format` | `src/format/index.ts` | Format validators + FormatRegistry |
| `typebox/guard` | `src/guard/index.ts` | Type guard utilities |
| `typebox/system` | `src/system/index.ts` | Settings, Memory, Environment utilities |
| `typebox/error` | `src/error/index.ts` | Error type definitions |

## Code Organization Patterns

**Naming conventions**: Every TypeBox type interface is prefixed with `T` (e.g., `TObject`, `TString`, `TUnion`). Every factory function omits the prefix (e.g., `Object()`, `String()`, `Union()`). Type guards follow `Is<Name>` (e.g., `IsObject`, `IsString`).

**Memory system**: All type objects are constructed immutably via `Memory.Create()` and mutated via `Memory.Update()` (which performs a shallow merge clone). `Memory.Discard()` strips internal symbols (prefixed `~`) to produce clean JSON Schema output.

**Deferred/Instantiate pattern**: Generic types and action types (Partial, Omit, etc.) use a two-phase construction — a `Deferred` token is created first, then `Instantiate()` resolves it against a context. This enables lazy evaluation of recursive and context-dependent types.

**Internal symbol keys**: TypeBox uses `~kind`, `~codec`, `~refine`, and similar `~`-prefixed keys to store TypeBox-internal metadata on schema objects. These keys do not appear in serialized JSON Schema output.

**Underscore-renamed exports**: JavaScript reserved words that overlap with TypeScript built-ins (e.g., `Object`, `Array`, `String`) are implemented as `_Object_`, `_Array_`, `_String_` internally and re-exported under the correct name for CommonJS/ESM interop.
