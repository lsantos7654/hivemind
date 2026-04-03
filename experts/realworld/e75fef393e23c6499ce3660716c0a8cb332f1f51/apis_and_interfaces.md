# RealWorld — APIs and Interfaces

## Overview

This repository defines three primary API surfaces: the **REST API specification** (what backends must implement), the **E2E test interfaces** (what frontends must expose), and the **test helper API** (TypeScript utilities for writing tests against implementations).

---

## 1. REST API Specification (`specs/api/openapi.yml`)

### Authentication

All protected endpoints require the JWT token in the Authorization header:

```
Authorization: Token <jwt-token>
```

The token is obtained at registration or login and stored in `localStorage.jwtToken` by frontend implementations.

### Endpoints

#### User and Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/users` | None | Register a new user (returns 201 with User) |
| `POST` | `/api/users/login` | None | Login (returns 200 with User) |
| `GET` | `/api/user` | Required | Get current authenticated user |
| `PUT` | `/api/user` | Required | Update current user profile |

**Register request body:**
```json
{
  "user": {
    "username": "jacob",
    "email": "jake@jake.jake",
    "password": "jakejake"
  }
}
```

**Login request body:**
```json
{
  "user": {
    "email": "jake@jake.jake",
    "password": "jakejake"
  }
}
```

**Update user request body (all fields optional):**
```json
{
  "user": {
    "email": "new@email.com",
    "username": "newname",
    "password": "newpass",
    "bio": "I like to skateboard",
    "image": "https://example.com/photo.jpg"
  }
}
```

**User response shape:**
```json
{
  "user": {
    "email": "jake@jake.jake",
    "token": "jwt.token.here",
    "username": "jake",
    "bio": null,
    "image": null
  }
}
```

**Important behavioral rules:**
- `bio` and `image` are nullable — setting to empty string `""` must normalize to `null`
- Setting `bio` or `image` to `null` explicitly must be accepted
- When `username` or `email` changes, a new JWT token should be issued

#### Profiles

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/profiles/:username` | Optional | Get a user profile |
| `POST` | `/api/profiles/:username/follow` | Required | Follow a user |
| `DELETE` | `/api/profiles/:username/follow` | Required | Unfollow a user |

**Profile response shape:**
```json
{
  "profile": {
    "username": "jake",
    "bio": "I work at statefarm",
    "image": "https://api.realworld.io/images/smiley-cyrus.jpg",
    "following": false
  }
}
```

#### Articles

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/articles` | Optional | List articles (paginated, filterable) |
| `GET` | `/api/articles/feed` | Required | Articles from followed users |
| `GET` | `/api/articles/:slug` | None | Get a single article |
| `POST` | `/api/articles` | Required | Create an article |
| `PUT` | `/api/articles/:slug` | Required | Update an article (owner only) |
| `DELETE` | `/api/articles/:slug` | Required | Delete an article (owner only) |

**GET /api/articles query parameters:**
- `?tag=tagname` — filter by tag
- `?author=username` — filter by author
- `?favorited=username` — filter by who favorited
- `?limit=20` — pagination limit (default 20, minimum 1)
- `?offset=0` — pagination offset (default 0, minimum 0)

**Create article request body:**
```json
{
  "article": {
    "title": "How to train your dragon",
    "description": "Ever wonder how?",
    "body": "You have to believe",
    "tagList": ["reactjs", "angularjs", "dragons"]
  }
}
```
Required: `title`, `description`, `body`. Optional: `tagList` (array of strings).

**Update article request body (all optional):**
```json
{
  "article": {
    "title": "Did you train your dragon?",
    "description": "Updated description",
    "body": "Updated body",
    "tagList": ["updated", "tags"]
  }
}
```

**Important behavioral rules:**
- When `title` changes, the `slug` must also be updated
- When `tagList` is omitted from an update, existing tags are preserved
- When `tagList` is sent as `[]`, all tags are removed
- When `tagList` is sent as `null`, the request must be rejected with 422
- Duplicate titles are allowed — each gets a unique slug (e.g., with a suffix)
- The `body` field is NOT included in list responses (only in single article responses)

**Single article response shape:**
```json
{
  "article": {
    "slug": "how-to-train-your-dragon",
    "title": "How to train your dragon",
    "description": "Ever wonder how?",
    "body": "It takes a Jacobian",
    "tagList": ["dragons", "training"],
    "createdAt": "2016-02-18T03:22:56.637Z",
    "updatedAt": "2016-02-18T03:48:35.824Z",
    "favorited": false,
    "favoritesCount": 0,
    "author": {
      "username": "jake",
      "bio": "I work at statefarm",
      "image": "https://i.stack.imgur.com/xHWG8.jpg",
      "following": false
    }
  }
}
```

**Multiple articles response shape (note: no `body` field):**
```json
{
  "articles": [{
    "slug": "how-to-train-your-dragon",
    "title": "How to train your dragon",
    "description": "Ever wonder how?",
    "tagList": ["dragons", "training"],
    "createdAt": "2016-02-18T03:22:56.637Z",
    "updatedAt": "2016-02-18T03:48:35.824Z",
    "favorited": false,
    "favoritesCount": 0,
    "author": { "username": "jake", "bio": "...", "image": "...", "following": false }
  }],
  "articlesCount": 1
}
```

#### Comments

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/articles/:slug/comments` | Optional | List comments for an article |
| `POST` | `/api/articles/:slug/comments` | Required | Create a comment |
| `DELETE` | `/api/articles/:slug/comments/:id` | Required | Delete a comment (owner only) |

Comment `id` is an integer. **Create comment body:**
```json
{ "comment": { "body": "His name was my name too." } }
```

#### Favorites and Tags

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/articles/:slug/favorite` | Required | Favorite an article |
| `DELETE` | `/api/articles/:slug/favorite` | Required | Unfavorite an article |
| `GET` | `/api/tags` | None | Get list of all tags |

**Tags response:**
```json
{ "tags": ["reactjs", "angularjs"] }
```

### Error Response Format

```json
{
  "errors": {
    "body": ["can't be empty"],
    "username": ["has already been taken"]
  }
}
```

#### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content (DELETE success) |
| 401 | Unauthorized (missing or invalid token) |
| 403 | Forbidden (authenticated but not allowed — e.g., editing another user's article) |
| 404 | Not Found (resource doesn't exist) |
| 409 | Conflict (duplicate username/email) |
| 422 | Unprocessable Entity (validation error) |

Frontends must handle any 2XX status as success (not just 204) for DELETE operations.

---

## 2. Frontend Interface Requirements

### Required Routes (`specs/e2e/SELECTORS.md`)

| Route | Page |
|-------|------|
| `/` | Home / Global Feed |
| `/?feed=following` | Your Feed (authenticated) |
| `/?page=N` | Paginated feed |
| `/tag/:tag` | Articles filtered by tag |
| `/login` | Login page |
| `/register` | Register page |
| `/editor` | New article editor |
| `/editor/:slug` | Edit existing article |
| `/settings` | User settings |
| `/profile/:username` | User profile (own articles) |
| `/profile/:username/favorites` | User's favorited articles |
| `/article/:slug` | Article detail page |

### Required CSS Selectors

Key CSS classes that E2E tests depend on (all must be present in the rendered HTML):

**Layout:**
- `.navbar` — main navigation bar
- `.navbar-brand` — logo/site name link
- `.nav-link` — navigation links
- `.banner` — home page hero banner
- `.container` — page width container

**Feed and Articles:**
- `.feed-toggle` — Global Feed / Your Feed tab bar
- `.article-preview` — article card in feed
- `.article-meta` — author avatar + name + date section
- `.article-content` — rendered article body (detail page)
- `.article-page` — article detail page wrapper
- `.preview-link` — link wrapping the article preview card
- `.author` — author name link
- `.empty-feed-message` — "No articles here" placeholder

**Tags:**
- `.sidebar` — home page sidebar
- `.tag-list` — tag pills container
- `.tag-default` — base tag class
- `.tag-pill` — pill-shaped tag variant

**Comments:**
- `.card` — comment card wrapper
- `.card-block` — comment text body
- `.comment-form` — comment input form (also uses `.card`)
- `.comment-author-img` — commenter's avatar image
- `.mod-options` — delete button container (for comment's own author)
- `.ion-trash-a` — delete icon

**Profile:**
- `.profile-page` — profile page wrapper
- `.user-info` — username, bio, avatar section
- `.user-img` — large avatar on profile page
- `.user-pic` — small avatar in navbar

**Pagination:**
- `.pagination` — pagination container
- `.page-item` — individual page button; active page has class `active`

**Buttons:**
- `.btn-outline-primary` — Favorite button (not yet favorited)
- `.btn-primary` — Unfavorite button (already favorited)
- `.btn-outline-danger` — destructive action (logout)

**Errors:**
- `.error-messages` — validation/API error list (`<ul>`)

### Required Input `name` Attributes

| Selector | Page |
|----------|------|
| `input[name="username"]` | Register, Settings |
| `input[name="email"]` | Login, Register, Settings |
| `input[name="password"]` | Login, Register, Settings |
| `input[name="title"]` | Editor |
| `input[name="description"]` | Editor |
| `textarea[name="body"]` | Editor |
| `input[name="image"]` | Settings |
| `textarea[name="bio"]` | Settings |
| `input[placeholder="Enter tags"]` | Editor |
| `textarea[placeholder="Write a comment..."]` | Article detail |

### LocalStorage

| Key | Value | Purpose |
|-----|-------|---------|
| `jwtToken` | JWT string | Stores authentication token across page reloads |

### `window.__conduit_debug__` Interface

Frontend implementations **must** expose this interface on the global window object for E2E tests:

```typescript
interface ConduitDebug {
  getToken(): string | null;
  getAuthState(): 'authenticated' | 'unauthenticated' | 'unavailable' | 'loading';
  getCurrentUser(): {
    username: string;
    email: string;
    bio: string | null;
    image: string | null;
    token: string;
  } | null;
}

declare global {
  interface Window {
    __conduit_debug__: ConduitDebug;
  }
}
```

### Default Avatar

When `user.image` is `null` or empty, avatar `src` attributes in `.user-img`, `.user-pic`, `.comment-author-img`, and `.article-meta img` must contain `default-avatar.svg`.

---

## 3. E2E Test Helper API (`specs/e2e/helpers/`)

### `helpers/api.ts` — Direct API Calls

```typescript
// Register via API, returns JWT token
registerUserViaAPI(request: APIRequestContext, user: UserCredentials): Promise<string>

// Login via API, returns JWT token
loginUserViaAPI(request: APIRequestContext, email: string, password: string): Promise<string>

// Create article via API, returns slug
createArticleViaAPI(
  request: APIRequestContext,
  token: string,
  article: { title: string; description: string; body: string; tagList?: string[] }
): Promise<string>

// Update user profile via API
updateUserViaAPI(
  request: APIRequestContext,
  token: string,
  updates: { image?: string; bio?: string; username?: string; email?: string }
): Promise<void>

// Create multiple articles for pagination testing, returns slugs array
createManyArticles(
  request: APIRequestContext,
  token: string,
  count: number,
  tag?: string
): Promise<string[]>
```

### `helpers/auth.ts` — Browser UI Auth

```typescript
// Register via UI form
register(page: Page, username: string, email: string, password: string): Promise<void>

// Login via UI form
login(page: Page, email: string, password: string): Promise<void>

// Logout via Settings page button
logout(page: Page): Promise<void>

// Generate a unique user object for test isolation
generateUniqueUser(): { username: string; email: string; password: string }
```

### `helpers/debug.ts` — Debug Interface

```typescript
// Get JWT token from window.__conduit_debug__
getToken(page: Page): Promise<string | null>

// Get auth state from window.__conduit_debug__
getAuthState(page: Page): Promise<AuthState | undefined>

// Get current user object from window.__conduit_debug__
getCurrentUser(page: Page): Promise<User | null>

// Wait for auth state to reach expected value
waitForAuthState(page: Page, expectedState: AuthState, options?: { timeout?: number }): Promise<void>

// Check if debug interface is available
isDebugInterfaceAvailable(page: Page): Promise<boolean>
```

### `helpers/config.ts` — Test Configuration

```typescript
// True unless API_MODE env var is explicitly 'false'
export const API_MODE: boolean

// Backend API base URL, default: 'https://api.realworld.show/api'
export const API_BASE: string
```

---

## 4. Playwright Base Configuration

```typescript
// specs/e2e/playwright.base.ts
export const baseConfig: PlaywrightTestConfig = {
  testDir: './e2e',
  fullyParallel: false,   // Tests run sequentially (shared backend state)
  retries: process.env.CI ? 2 : 1,
  workers: 1,
  reporter: 'html',
  timeout: 15_000,
  use: {
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    actionTimeout: 5_000,
    navigationTimeout: 10_000,
  },
  expect: { timeout: 5_000 },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
};
```

Implementations extend this by spreading `baseConfig` and providing `use.baseURL` and `webServer`.

---

## 5. Integration Patterns

### Testing a Backend

```bash
# Full suite
HOST=http://localhost:3000/api ./specs/api/run-api-tests-hurl.sh

# Single test file
HOST=http://localhost:3000/api ./specs/api/run-api-tests-hurl.sh specs/api/hurl/auth.hurl

# With a custom unique ID for isolation
HOST=http://localhost:3000/api UID_VAL=mytest123 ./specs/api/run-api-tests-hurl.sh
```

### Testing a Frontend (API Mode)

```bash
# Uses demo backend at api.realworld.show
API_MODE=true npx playwright test

# Skip specific API-only tests
API_MODE=false npx playwright test
```

### XSS Testing Pattern

The XSS tests inject malicious payloads directly via API (bypassing UI sanitization) and then check that rendering the data doesn't execute JavaScript:

```typescript
// Inject malicious payload via API
await updateUserViaAPI(request, token, { image: 'javascript:alert(1)' });

// Visit page and check no dialog triggered
const wasXssTriggered = setupXssDetector(page);
await page.goto(`/profile/${user.username}`);
expect(wasXssTriggered()).toBe(false);

// Verify no event handler attributes
const hasOnerror = await imgElement.evaluate(el => el.hasAttribute('onerror'));
expect(hasOnerror).toBe(false);
```
