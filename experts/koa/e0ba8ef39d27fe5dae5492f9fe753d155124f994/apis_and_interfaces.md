# Koa — APIs and Interfaces

## Entry Point and Exports

**File:** `lib/application.js`

```js
// CommonJS
const Koa = require('koa');

// ESM
import Koa from 'koa';

// Also exported:
const { HttpError } = require('koa');  // re-exported from http-errors
```

---

## Application Class (`lib/application.js`)

`class Application extends EventEmitter`

### Constructor

```js
const app = new Koa(options?)
```

**Options:**

| Option | Type | Default | Description |
|---|---|---|---|
| `env` | `string` | `NODE_ENV` or `'development'` | Environment name |
| `keys` | `string[]` | — | Signed cookie keys (passed to KeyGrip) |
| `proxy` | `boolean` | `false` | Trust proxy headers (X-Forwarded-*) |
| `subdomainOffset` | `number` | `2` | Number of host parts to skip for subdomains |
| `proxyIpHeader` | `string` | `'X-Forwarded-For'` | Header to read client IPs from |
| `maxIpsCount` | `number` | `0` (unlimited) | Max number of IPs to read from proxy header |
| `compose` | `function` | `koa-compose` | Custom middleware composition function |
| `asyncLocalStorage` | `boolean\|AsyncLocalStorage` | `false` | Enable per-request AsyncLocalStorage |

### Instance Methods

**`app.use(fn) → Application`** (`lib/application.js:152`)

Registers middleware. Returns `this` for chaining. `fn` must be a function with signature `(ctx, next) => Promise`.

```js
app.use(async (ctx, next) => {
  console.log(ctx.method, ctx.url);
  await next();
});
app.use(middleware1).use(middleware2);  // chainable
```

**`app.listen(...args) → http.Server`** (`lib/application.js:113`)

Creates an HTTP server and calls `.listen()` on it. Equivalent to:
```js
http.createServer(app.callback()).listen(...args)
```

**`app.callback() → (req, res) => void`** (`lib/application.js:167`)

Returns a Node.js `http` request handler. Use to mount Koa in an existing server or to start HTTP/2:
```js
const server = http.createServer(app.callback());
const server2 = https.createServer(opts, app.callback());
const http2Server = http2.createSecureServer(opts, app.callback());
```

**`app.toJSON() → Object`** (`lib/application.js:127`)

Returns `{ subdomainOffset, proxy, env }`.

**`get app.currentContext → Context|undefined`** (`lib/application.js:188`)

Returns the current request's Context from `AsyncLocalStorage`. Only available when `asyncLocalStorage` option was set.

```js
const app = new Koa({ asyncLocalStorage: true });
// ... in a middleware or function called from middleware:
const ctx = app.currentContext;
```

### Instance Properties

- `app.env` — environment string
- `app.keys` — array of signed cookie keys
- `app.proxy` — boolean proxy trust flag
- `app.subdomainOffset` — number
- `app.proxyIpHeader` — string
- `app.maxIpsCount` — number
- `app.middleware` — the raw array of middleware functions
- `app.context` — prototype object for all Context instances (can be extended)
- `app.request` — prototype object for all Request instances
- `app.response` — prototype object for all Response instances
- `app.silent` — suppress error logging (default: `false`)

### Application Events

```js
app.on('error', (err, ctx) => {
  // Emitted for all errors bubbling out of middleware
  // ctx may be undefined if error occurred during setup
});
```

---

## Context Object (`lib/context.js`)

One Context is created per request. It acts as the unified interface combining request and response.

### Own Methods

**`ctx.throw(status?, message?, properties?)` / `ctx.throw(error)`** (`lib/context.js:95`)

Throws an HTTP error using `http-errors`. The error is caught by Koa's error handler.

```js
ctx.throw(400);                          // 400 Bad Request
ctx.throw(400, 'name required');         // with message
ctx.throw(400, new Error('invalid'));    // with Error instance
ctx.throw(400, new Error('invalid'), { user: 'john' }); // with props
```

**`ctx.assert(test, status?, message?, properties?)`** (`lib/context.js:72`)

Like `ctx.throw` but only throws if `test` is falsy.

```js
ctx.assert(ctx.user, 401, 'Please login!');
```

**`ctx.onerror(err)`** — Internal per-request error handler. Emits `app.emit('error', err, this)`.

### Cookies

**`ctx.cookies`** — Lazy `Cookies` instance (from the `cookies` package).

```js
// Read
const name = ctx.cookies.get('name');
const signed = ctx.cookies.get('session', { signed: true });

// Write
ctx.cookies.set('name', 'value');
ctx.cookies.set('session', token, { signed: true, httpOnly: true, maxAge: 86400000 });
```

### Context State

**`ctx.state`** — Plain `{}` object. The recommended namespace for passing data between middleware.

```js
app.use(async (ctx, next) => {
  ctx.state.user = await User.find(ctx.query.id);
  await next();
});
```

### Delegated Response Properties (via `delegates`)

These are shortcuts that proxy to `ctx.response.*`:

| Property/Method | Type | Notes |
|---|---|---|
| `ctx.status` | getter/setter | HTTP status code (number) |
| `ctx.message` | getter/setter | HTTP status message |
| `ctx.body` | getter/setter | Response body |
| `ctx.length` | getter/setter | Content-Length |
| `ctx.type` | getter/setter | Content-Type (auto-resolves via mime-types) |
| `ctx.lastModified` | getter/setter | Last-Modified header |
| `ctx.etag` | getter/setter | ETag header |
| `ctx.headerSent` | getter | Whether headers are sent |
| `ctx.writable` | getter | Whether response is still writable |
| `ctx.set(field, val)` | method | Set response header(s) |
| `ctx.get(field)` | method | Get response header |
| `ctx.has(field)` | method | Check if response header exists |
| `ctx.remove(field)` | method | Remove response header |
| `ctx.append(field, val)` | method | Append to response header |
| `ctx.redirect(url)` | method | 302 redirect |
| `ctx.back(alt?)` | method | Redirect to Referrer (same-origin) or alt |
| `ctx.attachment(filename?)` | method | Content-Disposition: attachment |
| `ctx.vary(field)` | method | Add to Vary header |
| `ctx.flushHeaders()` | method | Flush headers early |

### Delegated Request Properties (via `delegates`)

| Property/Method | Type | Notes |
|---|---|---|
| `ctx.method` | getter/setter | HTTP method |
| `ctx.url` | getter/setter | Request URL |
| `ctx.path` | getter/setter | Pathname (preserves querystring) |
| `ctx.query` | getter/setter | Parsed query object (URLSearchParams-based) |
| `ctx.querystring` | getter/setter | Raw query string (without `?`) |
| `ctx.search` | getter/setter | Query string with leading `?` |
| `ctx.socket` | getter/setter | Request socket |
| `ctx.idempotent` | getter/setter | Whether method is idempotent |
| `ctx.accept` | getter/setter | `accepts` instance |
| `ctx.header` / `ctx.headers` | getter | Request headers object |
| `ctx.host` | getter | Host (proxy-aware) |
| `ctx.hostname` | getter | Hostname without port |
| `ctx.URL` | getter | WHATWG URL object (lazily memoized) |
| `ctx.protocol` | getter | `'http'` or `'https'` |
| `ctx.secure` | getter | `true` if HTTPS |
| `ctx.ip` | getter | Client IP (proxy-aware) |
| `ctx.ips` | getter | Array of IPs from X-Forwarded-For |
| `ctx.subdomains` | getter | Array of subdomain parts |
| `ctx.fresh` | getter | Cache freshness check result |
| `ctx.stale` | getter | Inverse of fresh |
| `ctx.origin` | getter | Origin header value |
| `ctx.href` | getter | Full URL including protocol/host |
| `ctx.accepts(types...)` | method | Content type negotiation |
| `ctx.acceptsEncodings(...)` | method | Encoding negotiation |
| `ctx.acceptsCharsets(...)` | method | Charset negotiation |
| `ctx.acceptsLanguages(...)` | method | Language negotiation |
| `ctx.get(field)` | method | Get request header |
| `ctx.is(type...)` | method | Check Content-Type |

### Raw Node.js Objects

```js
ctx.req   // Node.js IncomingMessage
ctx.res   // Node.js ServerResponse
ctx.app   // Application instance
ctx.request   // Koa Request object
ctx.response  // Koa Response object
ctx.originalUrl  // The original URL before any rewrites
```

---

## Response Object (`lib/response.js`)

### Body Setter

`ctx.response.body = val` (`lib/response.js:135`) accepts:

| Type | Behavior |
|---|---|
| `string` | Sets `Content-Type: text/html` (if starts with `<`) or `text/plain` |
| `Buffer` | Sets `Content-Type: application/octet-stream` |
| Node.js `Stream` | Sets `Content-Type: application/octet-stream`; destroys on finish |
| `ReadableStream` (WHATWG) | Same as stream |
| `Blob` | Sets length from `val.size` |
| `Response` (WHATWG) | Copies status and headers |
| Plain object / Array | JSON-serialized; `Content-Type: application/json` |
| `null` | Sets status 204 (unless already empty-body status) |

### Redirect

**`ctx.redirect(url)`** (`lib/response.js:302`)

Performs a 302 redirect. Sanitizes `http(s)://` URLs through `new URL()`. Responds with HTML for browsers or plain text for non-HTML clients.

**`ctx.back(alt?)`** (`lib/response.js:338`)

Redirects to `Referrer` header if same-origin; falls back to `alt` or `'/'`.

### Header Management

```js
ctx.set('Content-Type', 'application/json');
ctx.set({ 'X-Custom': '1', 'X-Other': '2' });
ctx.append('Set-Cookie', 'foo=bar');
ctx.remove('X-Powered-By');
ctx.has('Content-Type');  // → boolean
ctx.get('Content-Type');  // → string
```

---

## Request Object (`lib/request.js`)

### Content Negotiation

```js
// Returns best match or false
ctx.accepts('html', 'json');        // → 'json' (if client prefers JSON)
ctx.acceptsEncodings('gzip');       // → 'gzip'
ctx.acceptsCharsets('utf-8');       // → 'utf-8'
ctx.acceptsLanguages('en', 'es');   // → 'en'
```

### Content-Type Check

```js
ctx.is('json');              // → 'json' or false
ctx.is('text/*', 'json');    // → best match or false
```

### Query Parsing

```js
// GET /search?q=koa&tags=middleware&tags=router
ctx.query;          // → { q: 'koa', tags: ['middleware', 'router'] }
ctx.querystring;    // → 'q=koa&tags=middleware&tags=router'
ctx.search;         // → '?q=koa&tags=middleware&tags=router'

// Setting query
ctx.query = { page: '2' };  // serialized via URLSearchParams
```

### WHATWG URL

```js
ctx.URL;          // → WHATWG URL object, lazily memoized
ctx.URL.hostname; // → 'example.com'
ctx.URL.searchParams.get('q'); // → 'koa'
```

---

## Middleware Composition Pattern

Koa uses **`koa-compose`** to build the middleware chain. The composed function follows the "onion" model:

```js
app.use(async (ctx, next) => {
  // runs first (before downstream)
  await next();
  // runs last (after downstream)
});

app.use(async (ctx, next) => {
  // runs second
  await next();
});

app.use(async ctx => {
  // innermost — no next() call needed
  ctx.body = 'Hello World';
});
```

**Composing sub-stacks with `koa-compose`:**

```js
const compose = require('koa-compose');
const substack = compose([middleware1, middleware2, middleware3]);
app.use(substack);
```

---

## Error Handling Patterns

### Middleware-level error handler

```js
app.use(async (ctx, next) => {
  try {
    await next();
  } catch (err) {
    ctx.status = err.status || 500;
    ctx.body = { error: err.expose ? err.message : 'Internal Server Error' };
    ctx.app.emit('error', err, ctx);
  }
});
```

### App-level error listener

```js
app.on('error', (err, ctx) => {
  logger.error({ err, ctx }, 'server error');
});
```

### Bypass Koa's response handling

```js
app.use(async ctx => {
  ctx.respond = false;  // Koa will not finalize the response
  ctx.res.end('manual response');
});
```

---

## Configuration and Extension Points

### Extending Context

```js
app.context.db = db();             // available as ctx.db in all middleware
app.context.config = config;       // available as ctx.config
```

### Custom Middleware Composition

```js
const app = new Koa({ compose: myCustomCompose });
```

### AsyncLocalStorage Integration

```js
// Option 1: let Koa create its own
const app = new Koa({ asyncLocalStorage: true });
const ctx = app.currentContext;  // access from anywhere

// Option 2: bring your own
const { AsyncLocalStorage } = require('async_hooks');
const als = new AsyncLocalStorage();
const app = new Koa({ asyncLocalStorage: als });
// Then use als.getStore() anywhere in the same async context
```

### Mounting Koa in Express/Connect

```js
const express = require('express');
const expressApp = express();
expressApp.use('/api', koaApp.callback());
```

### HTTP/2 Integration

```js
import Koa from 'koa';
import http2 from 'node:http2';
import fs from 'node:fs';

const app = new Koa();
const server = http2.createSecureServer(
  { key: fs.readFileSync('key.pem'), cert: fs.readFileSync('cert.pem') },
  app.callback()
);
server.listen(3000);
```
