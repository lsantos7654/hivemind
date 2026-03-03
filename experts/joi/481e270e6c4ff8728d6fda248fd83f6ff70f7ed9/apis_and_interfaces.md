# Joi APIs and Interfaces

## Public API Overview

Joi exposes a rich API through its main export (`lib/index.js`). The API consists of type constructors, validation methods, utility functions, and configuration options. All methods return immutable schema objects, enabling safe composition and reuse.

## Entry Points

### Main Module Import

```javascript
const Joi = require('joi');
// or ES6:
import Joi from 'joi';
```

The default export provides:
- Type constructors (e.g., `Joi.string()`, `Joi.number()`)
- Validation methods (`assert()`, `attempt()`, `compile()`)
- Utility functions (`ref()`, `isRef()`, `isSchema()`, `expression()`)
- Configuration (`defaults()`, `extend()`)
- Error classes (`ValidationError`)

## Type Constructors

### Available Types

```javascript
Joi.any()           // Base type, matches any value
Joi.alternatives()  // Match against multiple schemas (alias: alt)
Joi.array()         // Array of items
Joi.binary()        // Buffer/binary data
Joi.boolean()       // Boolean values (alias: bool)
Joi.date()          // Date objects
Joi.function()      // Functions (alias: func)
Joi.link()          // Recursive schema references
Joi.number()        // Numbers
Joi.object()        // Objects with key validation
Joi.string()        // Strings
Joi.symbol()        // JavaScript symbols
```

**Constructor Patterns**:

```javascript
// Most types take no arguments
const schema = Joi.string();

// Some types accept configuration
const schema = Joi.object({
  name: Joi.string(),
  age: Joi.number()
});

const schema = Joi.alternatives().try(
  Joi.string(),
  Joi.number()
);

const schema = Joi.link('#person');  // Recursive reference
```

### Type-Specific Arguments

Only three types accept constructor arguments:
- `object(schema)` - Define keys inline
- `alternatives()` - Can use `.try()` method instead
- `link(ref)` - Specify recursive reference

All other types must be configured via chained methods.

## Core Validation Methods

### `schema.validate(value, [options])`

Synchronous validation with detailed results:

```javascript
const schema = Joi.object({
  username: Joi.string().alphanum().min(3).max(30).required(),
  password: Joi.string().pattern(/^[a-zA-Z0-9]{3,30}$/),
  birth_year: Joi.number().integer().min(1900).max(2013)
});

const { value, error } = schema.validate({
  username: 'abc',
  birth_year: 1994
});

if (error) {
  console.log(error.details); // Array of error objects
} else {
  console.log(value); // Validated and coerced value
}
```

**Return Value**:
```typescript
{
  value: any,              // Validated/coerced value
  error?: ValidationError, // Error if validation failed
  warning?: WarningObject, // Warnings if any
  artifacts?: Object,      // Generated artifacts if enabled
  debug?: Array           // Debug info if enabled
}
```

### `schema.validateAsync(value, [options])`

Asynchronous validation supporting external rules:

```javascript
const schema = Joi.string().external(async (value) => {
  const exists = await checkDatabase(value);
  if (exists) {
    throw new Error('Username already taken');
  }
});

try {
  const value = await schema.validateAsync('newuser');
  console.log('Valid:', value);
} catch (err) {
  console.log('Error:', err.message);
}
```

**Throws** `ValidationError` on failure instead of returning it.

### Validation Options

```javascript
const options = {
  abortEarly: false,      // Return all errors (default: true)
  allowUnknown: true,     // Allow unknown object keys (default: false)
  convert: true,          // Type coercion (default: true)
  presence: 'required',   // Default presence (optional|required|forbidden)
  stripUnknown: true,     // Remove unknown keys (default: false)
  context: { user: {} },  // External context for references
  messages: { ... },      // Custom error messages
  errors: {
    escapeHtml: false,    // HTML escape error messages
    label: 'path',        // Label format (path|key|false)
    stack: false          // Include stack traces
  }
};

schema.validate(value, options);
```

## Global Validation Functions

### `Joi.assert(value, schema, [message], [options])`

Throws error if validation fails:

```javascript
Joi.assert('x', Joi.number()); // Throws ValidationError

// With custom message
Joi.assert('x', Joi.number(), 'Expected a number');

// With custom error
Joi.assert('x', Joi.number(), new TypeError('Invalid type'));
```

### `Joi.attempt(value, schema, [message], [options])`

Returns validated value or throws:

```javascript
const num = Joi.attempt('4', Joi.number());
console.log(num); // 4 (converted to number)

Joi.attempt('x', Joi.number()); // Throws ValidationError
```

### `Joi.compile(schema, [options])`

Converts shorthand notation to Joi schema:

```javascript
// Array as alternatives
const schema = Joi.compile(['key', 5, { a: true }]);
// Equivalent to:
// Joi.alternatives().try(
//   Joi.string().valid('key'),
//   Joi.number().valid(5),
//   Joi.object({ a: Joi.boolean().valid(true) })
// )

// RegExp as string pattern
const schema = Joi.compile(/^[a-z]+$/);
// Equivalent to: Joi.string().pattern(/^[a-z]+$/)

// Plain object as Joi.object()
const schema = Joi.compile({ name: Joi.string() });
// Equivalent to: Joi.object({ name: Joi.string() })
```

**Options**:
- `legacy: true` - Compile using older Joi version compatibility

## Common Schema Methods

### Value Constraints

```javascript
schema.allow(value1, value2, ...)    // Allow specific values
schema.valid(value1, value2, ...)    // Only allow these values (alias: equal, only)
schema.invalid(value1, value2, ...)  // Disallow values (alias: disallow, not)

// Examples
Joi.string().allow('', null)         // Allow empty string and null
Joi.number().valid(1, 2, 3)         // Only 1, 2, or 3
Joi.string().invalid('admin')        // Cannot be 'admin'
```

### Presence

```javascript
schema.required()    // Must be present
schema.optional()    // May be absent (default)
schema.forbidden()   // Must not be present

// Example
Joi.object({
  username: Joi.string().required(),
  nickname: Joi.string().optional(),
  password_hash: Joi.string().forbidden()  // Strip from output
});
```

### Default Values

```javascript
schema.default(value, [description])

// Examples
Joi.string().default('guest')
Joi.number().default(() => Date.now(), 'current timestamp')
Joi.array().default([])
```

### Conditional Validation

```javascript
schema.when(condition, options)

// Based on another field
Joi.object({
  type: Joi.string().valid('personal', 'business'),
  taxId: Joi.string().when('type', {
    is: 'business',
    then: Joi.required(),
    otherwise: Joi.forbidden()
  })
});

// Based on value itself
Joi.string().when(Joi.string().min(5), {
  then: Joi.string().max(10),
  otherwise: Joi.string().max(20)
});

// Switch statement pattern
Joi.object({
  type: Joi.string(),
  value: Joi.when('type', {
    switch: [
      { is: 'number', then: Joi.number() },
      { is: 'string', then: Joi.string() },
      { is: 'boolean', then: Joi.boolean() }
    ],
    otherwise: Joi.any()
  })
});
```

## String Type API

### Format Validation

```javascript
Joi.string().alphanum()              // Only alphanumeric
Joi.string().email([options])        // Valid email
Joi.string().uri([options])          // Valid URI
Joi.string().domain([options])       // Valid domain
Joi.string().ip([options])           // IP address (v4/v6)
Joi.string().guid([options])         // GUID/UUID
Joi.string().base64([options])       // Base64 encoded
Joi.string().dataUri([options])      // Data URI
Joi.string().hex([options])          // Hexadecimal
Joi.string().hostname()              // Valid hostname
Joi.string().isoDate()               // ISO 8601 date
Joi.string().isoDuration()           // ISO 8601 duration
Joi.string().creditCard()            // Credit card number

// Examples
Joi.string().email({
  minDomainSegments: 2,
  tlds: { allow: ['com', 'net'] }
})

Joi.string().uri({
  scheme: ['http', 'https']
})

Joi.string().guid({
  version: ['uuidv4', 'uuidv5']
})
```

### Length and Pattern

```javascript
Joi.string().length(limit, [encoding])
Joi.string().min(limit, [encoding])
Joi.string().max(limit, [encoding])
Joi.string().pattern(regex, [options])
Joi.string().regex(regex, [options])  // Alias for pattern

// Examples
Joi.string().min(3).max(30)
Joi.string().length(10)
Joi.string().pattern(/^[A-Z]+$/, { name: 'uppercase' })
Joi.string().pattern(/^\d{3}-\d{4}$/)
```

### Case and Trimming

```javascript
Joi.string().lowercase()
Joi.string().uppercase()
Joi.string().trim()
Joi.string().case('upper')  // or 'lower'
Joi.string().normalize([form])  // Unicode normalization (NFC, NFD, NFKC, NFKD)

// Examples
Joi.string().lowercase().trim()
Joi.string().case('upper')
```

### String Replacement

```javascript
Joi.string().replace(pattern, replacement)

// Example
Joi.string().replace(/-/g, '')  // Remove dashes
```

## Number Type API

```javascript
Joi.number().min(limit)
Joi.number().max(limit)
Joi.number().greater(limit)      // Exclusive minimum
Joi.number().less(limit)         // Exclusive maximum
Joi.number().integer()
Joi.number().precision(limit)    // Decimal precision
Joi.number().multiple(base)      // Must be multiple of
Joi.number().positive()          // > 0
Joi.number().negative()          // < 0
Joi.number().port()              // Valid port number (0-65535)
Joi.number().sign('positive')    // or 'negative'
Joi.number().unsafe()            // Allow unsafe integers

// Examples
Joi.number().integer().min(0).max(100)
Joi.number().precision(2)        // 2 decimal places
Joi.number().multiple(5)         // 0, 5, 10, 15, ...
Joi.number().port()              // 0-65535
```

## Array Type API

```javascript
Joi.array().items(schema1, schema2, ...)     // Item schemas
Joi.array().ordered(schema1, schema2, ...)   // Ordered item schemas
Joi.array().length(limit)
Joi.array().min(limit)
Joi.array().max(limit)
Joi.array().unique([comparator], [options])
Joi.array().sparse([enabled])                // Allow undefined/null items
Joi.array().single([enabled])                // Convert single value to array
Joi.array().has(schema)                      // Must contain matching item

// Examples
Joi.array().items(Joi.string(), Joi.number())
Joi.array().unique()
Joi.array().min(1).max(10)
Joi.array().ordered(Joi.string(), Joi.number(), Joi.boolean())
Joi.array().has(Joi.string().valid('admin'))
```

## Object Type API

### Key Validation

```javascript
Joi.object().keys(schema)          // Define keys
Joi.object().pattern(pattern, schema)  // Pattern-based keys
Joi.object().unknown([allow])      // Allow unknown keys
Joi.object().min(limit)            // Minimum key count
Joi.object().max(limit)            // Maximum key count
Joi.object().length(limit)         // Exact key count

// Examples
Joi.object({
  name: Joi.string().required(),
  age: Joi.number()
})

Joi.object().pattern(/^[a-z]+$/, Joi.string())  // All keys match pattern
Joi.object().unknown(false)        // Strict mode
```

### Dependencies

```javascript
Joi.object().and(peer1, peer2, ...)        // All or none
Joi.object().or(peer1, peer2, ...)         // At least one
Joi.object().xor(peer1, peer2, ...)        // Exactly one
Joi.object().oxor(peer1, peer2, ...)       // Only one or none
Joi.object().with(key, peers)              // If key, then peers
Joi.object().without(key, peers)           // If key, not peers
Joi.object().nand(peer1, peer2, ...)       // Not all together

// Examples
Joi.object({
  username: Joi.string(),
  password: Joi.string(),
  access_token: Joi.string()
})
.xor('password', 'access_token')           // One authentication method
.with('password', 'username')              // Password requires username
```

### Key Renaming

```javascript
Joi.object().rename(from, to, [options])

// Example
Joi.object({
  user_name: Joi.string()
})
.rename('username', 'user_name', { alias: true })
```

## Reference System

### Creating References

```javascript
Joi.ref(key, [options])           // Reference to another field
Joi.in(key, [options])            // In-reference (for rules)

// Examples
Joi.object({
  password: Joi.string(),
  confirm_password: Joi.ref('password')  // Must match password
})

Joi.object({
  min: Joi.number(),
  max: Joi.number().greater(Joi.ref('min'))
})
```

### Reference Paths

```javascript
// Sibling reference
Joi.ref('fieldName')

// Nested reference
Joi.ref('parent.child.field')

// Ancestor reference
Joi.ref('....grandparent')  // Up 4 levels

// Root reference
Joi.ref('/rootField', { prefix: { root: '/' } })

// Context reference
Joi.ref('$global.config', { prefix: { global: '$' } })
```

### Reference Options

```javascript
{
  separator: '.',          // Path separator (default: '.')
  ancestor: 2,             // Levels up
  prefix: { ... },         // Custom prefixes
  adjust: (value) => ...,  // Transform referenced value
  render: true,            // Enable in templates
  in: true,               // In-reference mode
  iterables: true,        // Iterate arrays/sets
  map: [...]              // Map transformations
}
```

## Custom Validation

### `.custom(method, [description])`

```javascript
const schema = Joi.string().custom((value, helpers) => {
  if (value.includes('forbidden')) {
    throw new Error('Contains forbidden word');
    // or: return helpers.error('any.invalid');
  }
  return value;  // Return value or modified value
}, 'custom validation');

// With transformation
const schema = Joi.string().custom((value, helpers) => {
  return value.toUpperCase();
});
```

**Helper Methods**:
- `helpers.error(code, [local])` - Create error
- `helpers.message(messages)` - Override messages
- `helpers.state` - Current validation state
- `helpers.prefs` - Validation preferences
- `helpers.schema` - Current schema
- `helpers.original` - Original input value

### `.external(method, [description])`

Async validation (only works with `validateAsync`):

```javascript
const schema = Joi.string().external(async (value, helpers) => {
  const available = await checkAvailability(value);
  if (!available) {
    throw new Error('Already taken');
  }
});

await schema.validateAsync('username');
```

## Extension System

### `Joi.extend(...extensions)`

Create custom types:

```javascript
const customJoi = Joi.extend((joi) => ({
  type: 'creditCard',
  base: joi.string(),
  messages: {
    'creditCard.invalid': '{{#label}} must be a valid credit card'
  },
  validate(value, helpers) {
    if (!isValidCreditCard(value)) {
      return { value, errors: helpers.error('creditCard.invalid') };
    }
  }
}));

const schema = customJoi.creditCard();
```

**Extension Definition**:
```javascript
{
  type: 'typeName',           // Type name
  base: Joi.any(),            // Base type to extend
  messages: { ... },          // Error messages
  coerce(value, helpers) {},  // Type coercion
  validate(value, helpers) {}, // Core validation
  rules: { ... },             // Custom rules
  flags: { ... },             // Custom flags
  terms: { ... }              // Internal state
}
```

## Template System

### `Joi.expression(template, [options])`

Create dynamic expressions:

```javascript
const schema = Joi.object({
  min: Joi.number(),
  max: Joi.number(),
  value: Joi.number()
    .min(Joi.ref('min'))
    .max(Joi.ref('max'))
    .messages({
      'number.min': Joi.expression('{{#label}} must be >= {#min}'),
      'number.max': Joi.expression('{{#label}} must be <= {#max}')
    })
});
```

**Template Syntax**:
- `{path}` - Insert value without escaping
- `{{path}}` - Insert value with HTML escaping
- `{#label}` - Current field label
- `{#value}` - Current field value
- `{path.to.ref}` - Reference to other fields

**Operators**: `+`, `-`, `*`, `/`, `%`, `^`, `<`, `<=`, `>`, `>=`, `==`, `!=`, `&&`, `||`, `??`

## Error Handling

### ValidationError

```javascript
try {
  Joi.assert(value, schema);
} catch (err) {
  console.log(err.name);       // 'ValidationError'
  console.log(err.message);    // Error message
  console.log(err.details);    // Array of error details
  console.log(err.annotate()); // Annotated error display
}
```

**Error Details Structure**:
```javascript
[{
  message: 'Error message',
  path: ['field', 'path'],
  type: 'error.code',
  context: {
    label: 'field',
    value: 'invalid value',
    key: 'field'
  }
}]
```

## Configuration

### `Joi.defaults(modifier)`

Customize default schemas:

```javascript
const customJoi = Joi.defaults((schema) => {
  return schema.options({ abortEarly: false });
});

// All schemas from customJoi have abortEarly: false
const schema = customJoi.string();
```

### Schema Options

```javascript
schema.options(options)
schema.prefs(options)        // Alias for options
schema.preferences(options)  // Alias for options

// Example
const schema = Joi.object().options({
  abortEarly: false,
  stripUnknown: true
});
```

## Utility Functions

```javascript
Joi.isRef(value)              // Check if value is reference
Joi.isSchema(value)           // Check if value is Joi schema
Joi.isError(err)              // Check if error is ValidationError
Joi.isExpression(value)       // Check if value is expression
Joi.checkPreferences(prefs)   // Validate preferences object
Joi.cache.provision([options]) // Create LRU cache

// Examples
if (Joi.isSchema(value)) { ... }
if (Joi.isError(err)) { ... }
```

## Integration Patterns

### Express Middleware

```javascript
function validate(schema) {
  return (req, res, next) => {
    const { error, value } = schema.validate(req.body);
    if (error) {
      return res.status(400).json({ error: error.details });
    }
    req.validatedBody = value;
    next();
  };
}

app.post('/users', validate(userSchema), (req, res) => {
  // req.validatedBody contains validated data
});
```

### Configuration Files

```javascript
const configSchema = Joi.object({
  port: Joi.number().port().default(3000),
  host: Joi.string().hostname().default('localhost'),
  database: Joi.object({
    url: Joi.string().uri().required(),
    pool: Joi.number().integer().min(1).max(100).default(10)
  }).required()
}).required();

const config = Joi.attempt(rawConfig, configSchema);
```

### Form Validation

```javascript
const registrationSchema = Joi.object({
  email: Joi.string().email().required(),
  password: Joi.string().min(8).pattern(/[A-Z]/).pattern(/[0-9]/).required(),
  confirmPassword: Joi.ref('password'),
  terms: Joi.boolean().valid(true).required()
}).with('password', 'confirmPassword');

const { error, value } = registrationSchema.validate(formData, {
  abortEarly: false
});
```

This comprehensive API enables developers to build robust validation logic with minimal code while maintaining readability and maintainability.
