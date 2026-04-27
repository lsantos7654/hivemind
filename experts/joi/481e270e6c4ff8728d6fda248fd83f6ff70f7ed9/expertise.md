This expert provides comprehensive knowledge on:

### Core Validation Concepts
- Schema definition and composition using fluent API
- Synchronous validation with `validate()` method
- Asynchronous validation with `validateAsync()` and external rules
- Type coercion and conversion (strings to numbers, etc.)
- Validation options (abortEarly, allowUnknown, convert, stripUnknown, presence)
- Error handling with ValidationError and error details
- Custom error messages and message templating

### Type System
- **any type**: Base type with allow(), valid(), required(), optional(), forbidden()
- **string type**: email, uri, domain, IP, GUID, base64, hex, pattern, length, case, trim
- **number type**: min, max, integer, precision, multiple, positive, negative, port
- **array type**: items, ordered, length, unique, sparse, single, has
- **object type**: keys, pattern, unknown, dependencies (and, or, xor, with, without)
- **boolean type**: truthy, falsy value handling
- **date type**: min, max, timestamp, ISO dates
- **binary type**: Buffer validation, encoding, length
- **alternatives type**: conditional schemas, try-catch patterns, switch statements
- **function type**: arity, class validation, async function detection
- **link type**: recursive schema references
- **symbol type**: JavaScript symbol validation

### Advanced Features
- References with `Joi.ref()` for field dependencies
- Contextual validation with external context
- Conditional validation with `.when()` method
- Schema composition with `.concat()`, `.keys()`, `.append()`
- Template expressions with mathematical operators
- Custom validation with `.custom()` method
- External async validation with `.external()` method
- Schema extension with `Joi.extend()` for custom types
- Schema defaults with `Joi.defaults()` modifier
- Schema compilation from plain objects with `Joi.compile()`

### Implementation Details
- Immutable schema pattern (every method returns new instance)
- Validation pipeline architecture (prepare → coerce → validate → rules)
- Base class hierarchy (Base → Any → specific types)
- Extension system for custom types
- Reference system for cross-field validation (lib/ref.js)
- Template engine for dynamic messages (lib/template.js)
- Error reporting system (lib/errors.js)
- Cache system for performance (lib/cache.js)

### Integration Patterns
- Express middleware for request validation
- Configuration file validation
- Form validation with error display
- API request/response validation
- Environment variable validation
- Testing with Joi schemas
- TypeScript integration with .d.ts definitions

### Tooling and Development
- Testing with @hapi/lab (100% coverage requirement)
- Browser builds with webpack and babel
- ESLint configuration with @hapi/eslint-plugin
- TypeScript definitions (lib/index.d.ts, 2659 lines)
- Benchmark suite for performance regression testing
- CI/CD with GitHub Actions

### Common Patterns and Best Practices
- Reusable schema definitions
- Schema composition vs extension
- Error message customization
- Performance optimization (caching, schema reuse)
- Validation option configuration
- Handling nested objects and arrays
- Field interdependencies and conditional validation
- Migration between Joi versions

### Troubleshooting
- ValidationError debugging and error details interpretation
- Understanding validation options behavior
- Debugging type coercion issues
- Resolving reference resolution errors
- Performance bottleneck identification
- Browser vs Node.js compatibility issues
- TypeScript type definition issues

### Dependencies and Ecosystem
- @hapi/hoek for utilities (clone, merge, assert, reach)
- @hapi/address for email/domain/URI/IP validation
- @hapi/tlds for top-level domain validation
- @hapi/topo for topological sorting (dependency management)
- @hapi/formula for template expression parsing
- @hapi/pinpoint for error location tracking
- @standard-schema/spec for schema specification compliance
- hapi.js framework integration
- joi.dev documentation portal
