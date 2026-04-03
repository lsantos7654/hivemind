# node.js-clean-architecture — Code Structure

## Annotated Directory Tree

```
node.js-clean-architecture/
│
├── app.js                          # Application entry point. Wires all layers together.
├── package.json                    # NPM manifest: scripts, dependencies, Husky hooks.
├── .babelrc                        # Babel config: @babel/preset-env + transform-runtime.
├── .eslintrc.json                  # ESLint config: airbnb-base + prettier, ecmaVersion 2020.
├── .prettierrc                     # Prettier formatting rules.
├── .gitignore
├── .dockerignore
├── Dockerfile                      # Multi-stage Docker build (builder → production, node:22-alpine).
├── docker-compose.yml              # Compose: mongo, redis, web services on shared network.
│
├── config/
│   └── config.js                   # Central config export: port, host, MongoDB URI, Redis URI, JWT secret.
│                                   # All values come from env vars with sensible defaults.
│
├── src/
│   └── entities/
│       ├── post.js                 # Post entity factory. Returns getter closures for title, description,
│       │                           # createdAt, isPublished, userId. No framework imports.
│       └── user.js                 # User entity factory. Returns getter closures for username, password,
│                                   # email, role, createdAt. No framework imports.
│
├── application/
│   ├── use_cases/
│   │   ├── auth/
│   │   │   └── login.js            # Login use case: validates credentials, compares password hash,
│   │   │                           # generates JWT token via injected authService.
│   │   ├── post/
│   │   │   ├── add.js              # addPost use case: validates fields, creates Post entity,
│   │   │   │                       # delegates to postRepository.add().
│   │   │   ├── findAll.js          # findAll use case: delegates to postRepository.findAll(params).
│   │   │   ├── findById.js         # findById use case: delegates to postRepository.findById(id).
│   │   │   ├── countAll.js         # countAll use case: delegates to postRepository.countAll(params).
│   │   │   ├── updateById.js       # updateById use case: validates fields, fetches post to confirm
│   │   │   │                       # existence, creates updated Post entity, delegates update.
│   │   │   └── deleteΒyId.js      # deleteById use case: delegates to postRepository.deleteById(id).
│   │   │                           # NOTE: filename contains a Unicode beta character (Β vs B).
│   │   └── user/
│   │       ├── add.js              # addUser use case: validates fields, checks for duplicate username
│   │       │                       # and email, hashes password via authService, saves user entity.
│   │       ├── findById.js         # findById use case: delegates to userRepository.findById(id).
│   │       ├── findByProperty.js   # findByProperty use case: delegates to userRepository.findByProperty().
│   │       └── countAll.js         # countAll use case: delegates to userRepository.countAll(params).
│   │
│   ├── repositories/
│   │   ├── postDbRepository.js     # Post DB repository interface (port). Wraps injected impl,
│   │   │                           # exposes: findAll, countAll, findById, add, updateById, deleteById.
│   │   ├── postRedisRepository.js  # Post Redis repository interface (port). Wraps injected impl,
│   │   │                           # exposes: setCache.
│   │   └── userDbRepository.js     # User DB repository interface (port). Wraps injected impl,
│   │                               # exposes: findByProperty, countAll, findById, add, deleteById.
│   │
│   └── services/
│       └── authService.js          # Auth service interface (port). Wraps injected impl,
│                                   # exposes: encryptPassword, compare, verify, generateToken.
│
├── adapters/
│   └── controllers/
│       ├── postController.js       # Post adapter controller. Instantiates repositories from injected
│       │                           # interface+impl pairs. Implements fetchAllPosts (with Redis caching
│       │                           # write), fetchPostById, addNewPost, updatePostById, deletePostById.
│       ├── userController.js       # User adapter controller. Implements fetchUsersByProperty
│       │                           # (paginated), fetchUserById, addNewUser.
│       └── authController.js       # Auth adapter controller. Implements loginUser.
│
├── frameworks/
│   ├── webserver/
│   │   ├── express.js              # Express app configuration: helmet, compression, body-parser,
│   │   │                           # CORS headers (manual), morgan logger.
│   │   ├── server.js               # Server bootstrap with @godaddy/terminus: health check at
│   │   │                           # /healthcheck (checks mongoose readyState), onSignal (disconnect
│   │   │                           # mongoose), beforeShutdown (15s delay), startServer().
│   │   ├── routes/
│   │   │   ├── index.js            # Root router: mounts post, user, auth routers at /api/v1/*.
│   │   │   ├── post.js             # Post routes: injects deps into postController, applies
│   │   │   │                       # authMiddleware + redisCachingMiddleware on GETs.
│   │   │   ├── user.js             # User routes: injects deps into userController, applies
│   │   │   │                       # authMiddleware on GET endpoints.
│   │   │   └── auth.js             # Auth routes: injects deps into authController, POST /api/v1/login.
│   │   └── middlewares/
│   │       ├── authMiddleware.js       # JWT verification middleware. Reads Authorization header,
│   │       │                           # expects "Bearer <token>", verifies via authService, sets req.user.
│   │       ├── redisCachingMiddleware.js # Redis cache-check middleware factory. Takes redisClient and
│   │       │                           # key prefix; returns middleware that calls redisClient.get,
│   │       │                           # short-circuits response if cached.
│   │       └── errorHandlingMiddleware.js # Express 4-arg error handler. Returns JSON { status, message }.
│   │
│   ├── database/
│   │   ├── mongoDB/
│   │   │   ├── connection.js           # MongoDB connection factory. Listens to mongoose events
│   │   │   │                           # (connected, reconnected, error, disconnected) and auto-retries.
│   │   │   ├── models/
│   │   │   │   ├── post.js             # Mongoose Post schema: title (unique), description, createdAt,
│   │   │   │   │                       # isPublished, userId (ObjectId ref User). Compound indexes on userId+*.
│   │   │   │   └── user.js             # Mongoose User schema: username (unique), password, email (unique,
│   │   │   │                           # required, lowercase), role (default: test_user), createdAt.
│   │   │   └── repositories/
│   │   │       ├── postRepositoryMongoDB.js  # Concrete MongoDB post repo: findAll (skip/limit pagination),
│   │   │       │                             # countAll, findById, add (creates PostModel from entity getters),
│   │   │       │                             # updateById (findOneAndUpdate), deleteById (findByIdAndRemove).
│   │   │       └── userRepositoryMongoDB.js  # Concrete MongoDB user repo: findByProperty (skip/limit),
│   │   │                                     # countAll, findById (excludes password field), add.
│   │   └── redis/
│   │       ├── connection.js           # Redis connection factory. Creates client from URI string,
│   │       │                           # logs connect and error events.
│   │       └── postRepositoryRedis.js  # Concrete Redis post repo factory. Returns closure over
│   │                                   # redisClient; setCache calls redisClient.setex(key, ttl, data).
│   │
│   └── services/
│       └── authService.js          # Concrete auth service: bcryptjs for password hashing/comparison,
│                                   # jsonwebtoken for token sign (expiresIn: 360000s) and verify.
│
└── tests/
    └── unit/
        ├── fixtures/
        │   └── posts.js            # Static fixture objects for API stub tests (all, single, add, update
        │                           # success/failure shapes with status codes and JSON bodies).
        └── post/
            ├── api/
            │   └── api.spec.test.js        # API-shape tests using sinon stubs on `request` module.
            │                               # Tests GET /posts, GET /posts/:id, POST /posts, PUT /posts/:id.
            └── use_cases/
                └── use_cases.spec.test.js  # Unit tests for post use cases (findById, findAll, addPost)
                                            # using sinon stubs on the repository interface.
```

## Module and Package Organization

The project is organized by **architectural layer** rather than by feature. Each directory maps directly to one of the four Clean Architecture layers:

| Directory | Layer | Allowed Imports |
|-----------|-------|-----------------|
| `src/entities/` | Entities (innermost) | None |
| `application/use_cases/` | Use Cases | Entities only |
| `application/repositories/`, `application/services/` | Interface ports | None (pass-through wrappers) |
| `adapters/controllers/` | Interface Adapters | Use Cases + application ports |
| `frameworks/` | Frameworks & Drivers (outermost) | Everything |

## Key Files and Their Roles

### `app.js`
The composition root. Creates the Express app, calls `expressConfig` (middleware setup), `serverConfig` (terminus/graceful shutdown), `mongoDbConnection`, `redisConnection`, and `routes`. This is the only file that directly imports from multiple layers simultaneously — it is the wiring layer.

### `config/config.js`
Single source of truth for all environment-dependent values. Reads from `process.env` with defaults. Used by `app.js`, `frameworks/database/*/connection.js`, and `frameworks/services/authService.js`.

### Entity factories (`src/entities/`)
Each entity is a pure factory function returning an object of getter closures. They contain no validation logic (noted as a TODO) and no imports from any other layer. This makes entities independently unit-testable as plain functions.

### Repository interfaces (`application/repositories/`)
Each interface is a function that accepts a concrete implementation object and returns a new object with the same method signatures. This is the repository pattern implemented via manual dependency injection — no DI container required. The interface is what use cases import and call.

### Controller factories (`adapters/controllers/`)
Each controller is a factory function that receives the repository interface, the concrete implementation, and any other needed service interfaces/implementations. It calls `interface(implementation())` to create the wrapped repository, then returns an object of Express handler functions. Handlers call use cases with plain data extracted from `req`.

### Route files (`frameworks/webserver/routes/`)
Routes are the composition boundary where interfaces are paired with implementations. They import both the abstract port (from `application/`) and the concrete implementation (from `frameworks/`), then pass both to the controller factory.

## Code Organization Patterns

**Dependency Injection via factory functions:** No DI container or class-based injection. Dependencies are passed as function arguments. The factory pattern lets each layer define what it needs via its parameter list.

**Repository pattern as interface ports:** `application/repositories/*.js` files are 5-10 line wrappers that define the interface surface use cases depend on. Concrete implementations in `frameworks/database/` fulfill the same method names.

**Single-responsibility use cases:** Each file in `application/use_cases/` exports exactly one function representing one action. Files are short (5–30 lines) and highly focused.

**Unicode filename quirk:** `application/use_cases/post/deleteΒyId.js` uses a Unicode Greek capital beta (Β, U+0392) instead of the ASCII letter B in "By". This is the actual filename in the repository and must be imported exactly.

**Pagination via omit helper:** Both MongoDB repository implementations include a local `omit()` utility that strips `page` and `perPage` from query params before passing to Mongoose `find()`, then uses those values for `skip`/`limit`. This helper is duplicated across the two files (noted in a comment as needing a better location).
