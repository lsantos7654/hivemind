# node.js-clean-architecture — APIs and Interfaces

## Public REST API Endpoints

All endpoints are prefixed with `/api/v1`. The server listens on port `1234` by default.

### Authentication

#### `POST /api/v1/login`
Log in and receive a JWT token.

**Request body:**
```json
{ "email": "user@example.com", "password": "secret" }
```

**Response (200):**
```json
"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Error (401):** `{ "status": 401, "message": "Invalid email or password" }`

The returned token must be sent as `Authorization: Bearer <token>` on all protected endpoints.

---

### Posts

All post endpoints require `Authorization: Bearer <token>`.

#### `GET /api/v1/posts`
Fetch paginated posts for the authenticated user. Supports Redis caching (key: `posts_`, TTL: 30s).

**Query parameters:**
- `page` (integer, default: 1)
- `perPage` (integer, default: 10)
- Any additional query params are passed as filters to MongoDB `find()`

**Response (200):**
```json
{
  "posts": [...],
  "totalItems": 42,
  "totalPages": 5,
  "itemsPerPage": 10
}
```

#### `GET /api/v1/posts/:id`
Fetch a single post by MongoDB ObjectId. Redis cache key: `post_<id>`, TTL: 30s.

**Response (200):** The post object, or `{ "status": 404, "message": "No post found with id: <id>" }`.

#### `POST /api/v1/posts`
Create a new post.

**Request body:**
```json
{ "title": "My Post", "description": "Post content" }
```
`userId` is extracted from the JWT token (`req.user.id`). `title` and `description` are required.

**Response (200):** `"post added"`

#### `PUT /api/v1/posts/:id`
Update an existing post by ID.

**Request body:**
```json
{ "title": "Updated Title", "description": "Updated content", "isPublished": true }
```
`title` and `description` are required. `isPublished` is optional (boolean).

**Response (200):** The updated post object from MongoDB.

#### `DELETE /api/v1/posts/:id`
Delete a post by ID.

**Response (200):** `"post sucessfully deleted!"` (note: typo in original code)

---

### Users

#### `POST /api/v1/users`
Register a new user. Public endpoint (no auth required).

**Request body:**
```json
{ "username": "alice", "password": "secret", "email": "alice@example.com", "role": "admin", "createdAt": "2024-01-01" }
```
`username`, `password`, and `email` are required. Checks for duplicate username and email.

**Response (200):** The created user document from MongoDB.

#### `GET /api/v1/users`
Fetch paginated users (auth required). Accepts the same query param pattern as posts.

**Query parameters:** `page`, `perPage`, plus any MongoDB filter properties (e.g., `role=admin`).

**Response (200):**
```json
{
  "users": [...],
  "totalItems": 10,
  "totalPages": 1,
  "itemsPerPage": 10
}
```

#### `GET /api/v1/users/:id`
Fetch a single user by ID (auth required). Password field is excluded from the response.

**Response (200):** User document without the `password` field.

---

### Health Check

#### `GET /healthcheck`
Returns HTTP 200 if MongoDB is connected, or 503 if disconnected/connecting. Provided by `@godaddy/terminus`.

---

## Key Functions and Their Signatures

### Entity Factories (`src/entities/`)

```js
// src/entities/post.js
function post({ title, description, createdAt, isPublished = false, userId })
// Returns: { getTitle, getDescription, getCreatedAt, isPublished, getUserId }

// src/entities/user.js
function user(username, password, email, role, createdAt)
// Returns: { getUserName, getPassword, getEmail, getRole, getCreatedAt }
```

Entities are plain objects with getter closures. They carry no framework code and can be constructed and tested in isolation.

### Repository Interface Factories (`application/repositories/`)

```js
// application/repositories/postDbRepository.js
function postRepository(repository)
// Returns: { findAll(params), countAll(params), findById(id), add(post), updateById(id, post), deleteById(id) }

// application/repositories/userDbRepository.js
function userRepository(repository)
// Returns: { findByProperty(params), countAll(params), findById(id), add(user), deleteById(id) }

// application/repositories/postRedisRepository.js
function redisPostRepository(repository)
// Returns: { setCache({ key, expireTimeSec, data }) }
```

Each interface function wraps an injected concrete implementation, forwarding calls. This is the port side of the ports-and-adapters pattern.

### Service Interface Factory (`application/services/`)

```js
// application/services/authService.js
function authService(service)
// Returns: { encryptPassword(password), compare(password, hashedPassword), verify(token), generateToken(payload) }
```

### Use Case Functions (`application/use_cases/`)

All use cases are exported as named default functions that accept data and injected repositories/services:

```js
// auth
function login(email, password, userRepository, authService) => Promise<string> // JWT token

// post use cases
function addPost({ title, description, createdAt, isPublished, userId, postRepository }) => Promise<PostDocument>
function findAll(params, postRepository) => Promise<PostDocument[]>
function findById(id, postRepository) => Promise<PostDocument>
function countAll(params, postRepository) => Promise<number>
function updateById({ id, title, description, createdAt, isPublished, userId, postRepository }) => Promise<PostDocument>
function deleteById(id, postRepository) => Promise<void>  // file: deleteΒyId.js (Unicode B)

// user use cases
function addUser(username, password, email, role, createdAt, userRepository, authService) => Promise<UserDocument>
function findById(id, userRepository) => Promise<UserDocument>
function findByProperty(params, userRepository) => Promise<UserDocument[]>
function countAll(params, userRepository) => Promise<number>
```

### Controller Factories (`adapters/controllers/`)

```js
// adapters/controllers/postController.js
function postController(postDbRepository, postDbRepositoryImpl, cachingClient, postCachingRepository, postCachingRepositoryImpl)
// Returns: { fetchAllPosts, fetchPostById, addNewPost, updatePostById, deletePostById }
// Each method is an Express handler: (req, res, next) => void

// adapters/controllers/userController.js
function userController(userDbRepository, userDbRepositoryImpl, authServiceInterface, authServiceImpl)
// Returns: { fetchUsersByProperty, fetchUserById, addNewUser }

// adapters/controllers/authController.js
function authController(userDbRepository, userDbRepositoryImpl, authServiceInterface, authServiceImpl)
// Returns: { loginUser }
```

### Concrete Repository Implementations (`frameworks/database/`)

```js
// frameworks/database/mongoDB/repositories/postRepositoryMongoDB.js
function postRepositoryMongoDB()
// Returns: { findAll(params), countAll(params), findById(id), add(postEntity), updateById(id, postEntity), deleteById(id) }
// - findAll: PostModel.find(filters).skip(offset).limit(perPage)
// - add: reads entity via getTitle(), getDescription(), etc., then newPost.save()
// - updateById: PostModel.findOneAndUpdate({ _id: id }, { $set: updatedPost }, { new: true })
// - deleteById: PostModel.findByIdAndRemove(id)

// frameworks/database/mongoDB/repositories/userRepositoryMongoDB.js
function userRepositoryMongoDB()
// Returns: { findByProperty(params), countAll(params), findById(id), add(userEntity) }
// - findById: UserModel.findById(id).select('-password')  // excludes password

// frameworks/database/redis/postRepositoryRedis.js
function PostRepositoryRedis()
// Returns: function(redisClient) { setCache({ key, expireTimeSec, data }) }
// - setCache: redisClient.setex(key, expireTimeSec, data)
```

### Concrete Auth Service (`frameworks/services/authService.js`)

```js
function authService()
// Returns: { encryptPassword(password), compare(password, hashedPassword), verify(token), generateToken(payload) }
// - encryptPassword: bcrypt.hashSync(password, bcrypt.genSaltSync(10))
// - compare: bcrypt.compareSync(password, hashedPassword)
// - verify: jwt.verify(token, config.jwtSecret)
// - generateToken: jwt.sign(payload, config.jwtSecret, { expiresIn: 360000 })
```

Note: `expiresIn: 360000` is interpreted as 360000 **seconds** (~4.16 days) by jsonwebtoken when a number is passed.

---

## Configuration Options

All configuration is in `config/config.js` and read from environment variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `PORT` | `1234` | HTTP server port |
| `HOST` | `0.0.0.0` | HTTP server bind address |
| `MONGO_URL` | `mongodb://localhost:27017/post-clean-code` | MongoDB connection URI |
| `REDIS_URL` | `redis://localhost:6379` | Redis connection URI |
| `JWT_SECRET` | `jkl!±@£!@ghj1237` | Secret for JWT signing/verification |
| `NODE_PROCESSES` | (none) | pm2 cluster worker count (production) |

---

## Integration Patterns and Workflows

### Adding a New Use Case (Clean Architecture Pattern)

1. **Entity**: If new business data is needed, add a factory in `src/entities/`.
2. **Use case**: Create `application/use_cases/<domain>/<action>.js` exporting a single function. Accept repository and service interfaces as parameters — never import concrete implementations.
3. **Repository interface**: If the use case needs new repository methods, add them to the relevant `application/repositories/*.js` interface wrapper.
4. **Controller**: Add a handler in `adapters/controllers/` that calls the use case with data from `req`.
5. **Route**: Register the route in `frameworks/webserver/routes/` and inject the concrete implementation alongside the interface.
6. **Concrete implementation**: Add the method to the MongoDB/Redis repository in `frameworks/database/`.

### Dependency Injection Pattern

The project uses manual constructor injection via function factories:

```js
// In a route file (frameworks layer — allowed to import everything):
import postDbRepository from '../../../application/repositories/postDbRepository';       // interface
import postDbRepositoryMongoDB from '../../database/mongoDB/repositories/postRepositoryMongoDB'; // impl

const controller = postController(
  postDbRepository,             // interface factory
  postDbRepositoryMongoDB,      // impl factory
  redisClient,
  postRedisRepository,
  postRedisRepositoryImpl
);

// In the controller (adapters layer):
const dbRepository = postDbRepository(postDbRepositoryImpl()); // interface wraps impl instance

// dbRepository now exposes the interface methods but delegates to MongoDB
```

### Redis Caching Pattern

Read (GET) requests go through `redisCachingMiddleware` before the controller. If a cache hit occurs, the response is returned immediately. On a cache miss, the controller fetches from MongoDB and then calls `cachingRepository.setCache()` to populate the cache:

```js
// Cache key format: "<prefix>_<id>" or "<prefix>_" for collections
// TTL: 30 seconds (hardcoded in postController.js)
const cachingOptions = {
  key: 'posts_',
  expireTimeSec: 30,
  data: JSON.stringify(posts)
};
cachingRepository.setCache(cachingOptions);
```

### Error Handling Pattern

Errors from use cases or infrastructure bubble up via Promise `.catch((error) => next(error))` in controllers. The global `errorHandlingMiddleware` (4-argument Express handler) catches all errors and returns:

```json
{ "status": <statusCode>, "message": "<error message>" }
```

Custom status codes can be set by attaching `error.statusCode` before throwing. Default status code is 404.

### Mongoose Data Model Notes

**Post schema indexes** (compound on userId):
- `{ userId: 1, title: 1 }`
- `{ userId: 1, description: 1 }`
- `{ userId: 1, createdAt: 1 }`
- `{ userId: 1, isPublished: 1 }`

**User schema indexes:**
- `{ role: 1 }` (single field)
- `username` and `email` are unique fields (implicit indexes)

`ensureIndexes()` is called on both models at module load time.
