### DDD Building Blocks
- Abstract `Entity<EntityProps>` base class: constructor, `getProps()`, `toObject()`, `equals()`, `validate()` lifecycle, `AggregateID` type
- Abstract `AggregateRoot<EntityProps>` base class: domain event queue, `addEvent()`, `publishEvents()`, `clearEvents()`
- Abstract `ValueObject<T>` base class: structural equality via `equals()`, `unpack()` method, `DomainPrimitive<T>` for single-value VOs, validation lifecycle
- `DomainEvent` base class: auto-generated UUID id, aggregateId, metadata (correlationId, causationId, timestamp, userId)
- `Command` base class: id, metadata, `CommandProps<T>` type helper
- `QueryBase` and `PaginatedQueryBase`: limit/offset/page/orderBy defaults
- `RepositoryPort<Entity>` interface: insert, findOneById, findAll, findAllPaginated, delete, transaction
- `Mapper<DomainEntity, DbRecord, Response>` interface: toPersistence, toDomain, toResponse
- `Paginated<T>` class and `PaginatedQueryParams` type

### Architecture Patterns
- Hexagonal Architecture (Ports and Adapters): inner domain layer, application layer, infrastructure adapters
- CQRS: separate command handlers (`@CommandHandler`) and query handlers (`@QueryHandler`)
- Vertical Slice architecture within modules: each use case has its own folder
- Module isolation: no direct imports between modules, only event-based communication
- Dependency inversion: repositories accessed via port interfaces, injected via DI tokens
- Clean dependency direction: infrastructure depends on domain, never the reverse
- Bounded context organization: user module and wallet module as independent contexts

### NestJS Integration
- `@Module` wiring: how providers, controllers, repositories, mappers are assembled
- DI tokens pattern: `USER_REPOSITORY`, `WALLET_REPOSITORY` string tokens in `*.di-tokens.ts`
- `@CommandHandler(CreateUserCommand)` — NestJS CQRS command handler registration
- `@QueryHandler(FindUsersQuery)` — NestJS CQRS query handler registration
- `@OnEvent(EventName.name)` — NestJS EventEmitter2 domain event subscription
- Global interceptors: `ContextInterceptor` (sets requestId), `ExceptionInterceptor` (formats errors)
- `APP_INTERCEPTOR` global provider pattern in root AppModule
- NestJS ValidationPipe with `transform: true, whitelist: true`
- GraphQL auto-schema generation with `ApolloDriver`

### Request Context and Correlation
- `AppRequestContext` extends `RequestContext` (nestjs-request-context): requestId, transactionConnection
- `RequestContextService`: `getContext()`, `setRequestId()`, `getRequestId()`, `getTransactionConnection()`, `setTransactionConnection()`, `cleanTransactionConnection()`
- `ContextInterceptor`: assigns unique requestId per request
- How correlationId propagates through Command metadata, DomainEvent metadata, ExceptionBase

### Repository and Database
- `SqlRepositoryBase<Aggregate, DbModel>`: abstract tableName, abstract schema (Zod), pool getter (transaction-aware)
- `writeQuery()` utility: validates entity, logs, executes SQL, publishes events
- `generateInsertQuery()`: dynamic INSERT from plain object keys
- Transaction management: `transaction()` wraps in Slonik transaction, stores connection in RequestContext
- `UserRepository`: `updateAddress()`, `findOneByEmail()` custom methods, Zod `userSchema` definition
- Zod runtime validation of database rows for extra safety
- Slonik `sql.type(schema)` for typed query results
- `@InjectPool()` decorator from nestjs-slonik

### Exception Handling
- `ExceptionBase`: abstract class with message, cause, metadata, correlationId, code string, `toJSON()`
- Concrete exception classes: `ArgumentInvalidException`, `ArgumentNotProvidedException`, `ArgumentOutOfRangeException`, `ConflictException`, `NotFoundException`, `InternalServerErrorException`
- Exception codes: `GENERIC.ARGUMENT_INVALID`, `GENERIC.NOT_FOUND`, etc.
- Domain-specific errors extending ExceptionBase: `UserAlreadyExistsError` (code: `USER.ALREADY_EXISTS`)
- `ExceptionInterceptor`: how HTTP errors get correlationId attached, how class-validator errors are reformatted
- `ApiErrorResponse` DTO shape: statusCode, message, error, correlationId, subErrors

### Result and Option Types
- `oxide.ts` library usage: `Ok(value)`, `Err(error)`, `Result<T, E>`, `Option<T>`, `Some(value)`, `None`
- `match(result, { Ok: ..., Err: ... })` pattern in controllers
- `result.unwrap()` for extracting value (used when error is not expected)
- How `RepositoryPort.findOneById()` returns `Option<Entity>`
- Pattern for application services returning `Result<AggregateID, DomainError>`

### Value Objects
- `Address` value object: country, postalCode, street — multi-property VO with `Guard` validation
- How VOs enforce domain invariants at construction time
- `Guard.isEmpty()` and `Guard.lengthIsBetween()` for invariant checks
- Converting VOs back to raw values via `unpack()`

### Domain Events and Cross-Module Communication
- `UserCreatedDomainEvent`, `UserDeletedDomainEvent`, `UserRoleChangedDomainEvent`, `UserAddressUpdatedDomainEvent`
- `WalletCreatedDomainEvent`
- `CreateWalletWhenUserIsCreatedDomainEventHandler`: cross-module event handler pattern
- How events are published: `entity.publishEvents(logger, eventEmitter)` called after DB write
- Why events are published after transaction commit (atomicity)

### HTTP Controllers and DTOs
- `CreateUserHttpController`: CommandBus injection, Result matching, Swagger annotations
- `CreateUserRequestDto`: class-validator decorators (IsEmail, IsAlphanumeric, Matches, MaxLength, MinLength)
- `UserResponseDto` extending `ResponseBase` (id, createdAt, updatedAt)
- `IdResponse` DTO for mutation responses
- `PaginatedResponseDto<T>` base for paginated responses
- `ApiErrorResponse` DTO structure

### Multiple Transport Controllers
- HTTP: `@Controller`, `@Post`, `@Get`, `@Delete`, `@Body`, `@Query`, `@Param`
- GraphQL: `@Resolver`, `@Mutation`, `@Query`, `@Args`
- CLI: `@Console`, `@Command` decorators from nestjs-console
- Microservice: `@MessagePattern('user.create')` from @nestjs/microservices
- Pattern: one service/command handler, multiple controllers all using the same CommandBus

### CQRS Query Side
- `FindUsersQuery` extends `PaginatedQueryBase` with optional filter properties
- `FindUsersQueryHandler`: bypasses domain/repository layers, queries directly via DatabasePool
- Read model uses raw DB model types (`UserModel`) not domain entities
- Composable SQL with Slonik conditional clauses

### Decorators
- `@frozen` decorator: `Object.freeze(constructor)` and `Object.freeze(constructor.prototype)`
- `@final` decorator: runtime check prevents subclassing

### TypeScript Utility Types
- `DeepPartial<T>`, `Mutable<T>`, `NonFunctionProperties<T>`, `ObjectLiteral`, `RequireOne<T, K>`
- `AggregateID` type alias for string IDs
- `CommandProps<T>` and `DomainEventProps<T>` type helpers that strip id and metadata

### Testing
- BDD/Gherkin e2e tests with `jest-cucumber` and `.feature` files
- `ApiClient` test utility class for HTTP requests
- `TestContext<T>` for sharing state between Gherkin steps
- `jestGlobalSetup.ts` and `jestSetupAfterEnv.ts` for database setup
- Truncating tables between tests with real Slonik connection pool
- Artillery load test YAML configuration for performance testing

### Build and Tooling
- `nest build` with `rimraf dist` prebuild
- TypeScript path alias resolution at runtime via `tsconfig-paths`
- `dependency-cruiser` for enforcing architectural dependency rules
- Environment variable management with `dotenv` and `env-var`
- Database migrations with `@slonik/migrator`
- Docker Compose for PostgreSQL + pgAdmin
- Volta for Node.js version pinning (20.1.0)
