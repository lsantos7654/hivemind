# Node.js — APIs and Interfaces

## Public JavaScript APIs (Built-in Modules)

All built-in modules are accessed via `require('node:<name>')` or `require('<name>')`:

### Core Module Reference

| Module | Entry Point | Purpose |
|--------|------------|---------|
| `node:assert` | `lib/assert.js` | Assertion functions for tests |
| `node:async_hooks` | `lib/async_hooks.js` | Async resource lifecycle tracking |
| `node:buffer` | `lib/buffer.js` | Binary data manipulation |
| `node:child_process` | `lib/child_process.js` | Spawn child processes |
| `node:cluster` | `lib/cluster.js` | Multi-process load balancing |
| `node:console` | `lib/console.js` | Console output |
| `node:crypto` | `lib/crypto.js` | Cryptographic functions |
| `node:dgram` | `lib/dgram.js` | UDP sockets |
| `node:diagnostics_channel` | `lib/diagnostics_channel.js` | Publish/subscribe diagnostic info |
| `node:dns` | `lib/dns.js` | DNS lookups |
| `node:domain` | `lib/domain.js` | Error domain handling (legacy) |
| `node:events` | `lib/events.js` | EventEmitter pattern |
| `node:fs` | `lib/fs.js` | File system operations |
| `node:http` | `lib/http.js` | HTTP/1.x client and server |
| `node:http2` | `lib/http2.js` | HTTP/2 client and server |
| `node:https` | `lib/https.js` | HTTPS client and server |
| `node:inspector` | `lib/inspector.js` | V8 Inspector Protocol |
| `node:module` | `lib/module.js` | Module system utilities |
| `node:net` | `lib/net.js` | TCP/IPC sockets |
| `node:os` | `lib/os.js` | OS information |
| `node:path` | `lib/path.js` | File path utilities |
| `node:perf_hooks` | `lib/perf_hooks.js` | Performance measurement |
| `node:process` | `lib/process.js` | Process information (also global) |
| `node:quic` | `lib/quic.js` | QUIC transport (experimental) |
| `node:readline` | `lib/readline.js` | Line-by-line reading from streams |
| `node:repl` | `lib/repl.js` | Read-Eval-Print Loop |
| `node:sea` | `lib/sea.js` | Single Executable Application |
| `node:sqlite` | `lib/sqlite.js` | SQLite database |
| `node:stream` | `lib/stream.js` | Stream abstractions |
| `node:string_decoder` | `lib/string_decoder.js` | Buffer-to-string decoding |
| `node:test` | `lib/test.js` | Built-in test runner |
| `node:timers` | `lib/timers.js` | setTimeout, setInterval, etc. |
| `node:tls` | `lib/tls.js` | TLS/SSL sockets |
| `node:tty` | `lib/tty.js` | TTY streams |
| `node:url` | `lib/url.js` | URL parsing (WHATWG + legacy) |
| `node:util` | `lib/util.js` | Utility functions |
| `node:v8` | `lib/v8.js` | V8 engine internals |
| `node:vm` | `lib/vm.js` | JavaScript sandbox execution |
| `node:wasi` | `lib/wasi.js` | WebAssembly System Interface |
| `node:worker_threads` | `lib/worker_threads.js` | Multi-threading |
| `node:zlib` | `lib/zlib.js` | Compression/decompression |

---

## Key Classes and Functions

### EventEmitter (`node:events`, `lib/events.js:211`)
```js
const { EventEmitter } = require('node:events');
const emitter = new EventEmitter();
emitter.on('data', (chunk) => console.log(chunk));
emitter.once('end', () => console.log('done'));
emitter.emit('data', 'hello');
emitter.removeAllListeners('data');
// Static: EventEmitter.setMaxListeners(n); EventEmitter.on(emitter, 'event')
```

### Streams (`node:stream`, `lib/stream.js`)
```js
const { Readable, Writable, Duplex, Transform, pipeline, compose } = require('node:stream');
// Readable
const r = Readable.from(['a', 'b', 'c']);
// Custom Transform
class MyTransform extends Transform {
  _transform(chunk, enc, cb) { this.push(chunk.toString().toUpperCase()); cb(); }
}
// Pipeline (handles cleanup on error)
await pipeline(readable, new MyTransform(), writable);
// Compose streams
const composed = compose(gzip, encrypt);
```

### File System (`node:fs`, `lib/fs.js`)
```js
const fs = require('node:fs');
const { promises: fsPromises } = require('node:fs');
// Callback-based
fs.readFile('/path/to/file', 'utf8', (err, data) => { ... });
// Promise-based
const data = await fsPromises.readFile('/path/to/file', 'utf8');
// Sync
const data = fs.readFileSync('/path/to/file', 'utf8');
// Glob
for await (const file of fsPromises.glob('**/*.js')) { ... }
// Watch (recursive)
const watcher = fsPromises.watch('.', { recursive: true });
for await (const event of watcher) { console.log(event.filename); }
```

### HTTP Server (`node:http`, `lib/http.js`)
```js
const http = require('node:http');
const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Hello World');
});
server.listen(3000);
// HTTP Client
const response = await fetch('http://example.com'); // global fetch (undici)
```

### Crypto (`node:crypto`, `lib/crypto.js`)
```js
const crypto = require('node:crypto');
// Hashing
const hash = crypto.createHash('sha256').update('data').digest('hex');
// HMAC
const hmac = crypto.createHmac('sha256', 'secret').update('data').digest('hex');
// Key generation
const { privateKey, publicKey } = crypto.generateKeyPairSync('rsa', { modulusLength: 2048 });
// Random bytes
const bytes = crypto.randomBytes(32);
// UUID
const uuid = crypto.randomUUID();
// Web Crypto API
const key = await globalThis.crypto.subtle.generateKey(...);
// Argon2 (new in v26)
const hash = await crypto.hash('argon2id', password, options);
```

### Worker Threads (`node:worker_threads`, `lib/worker_threads.js`)
```js
const { Worker, isMainThread, parentPort, workerData } = require('node:worker_threads');
if (isMainThread) {
  const worker = new Worker(__filename, { workerData: { n: 40 } });
  worker.on('message', (result) => console.log(result));
} else {
  parentPort.postMessage(fibonacci(workerData.n));
}
```

### Test Runner (`node:test`, `lib/test.js`)
```js
const { test, describe, it, mock, beforeEach, afterEach } = require('node:test');
const assert = require('node:assert/strict');

describe('MyModule', () => {
  it('does something', async (t) => {
    const mockFn = t.mock.fn(() => 42);
    assert.strictEqual(mockFn(), 42);
    assert.strictEqual(mockFn.mock.callCount(), 1);
  });
  it('snapshot', async (t) => {
    t.assert.snapshot({ key: 'value' });  // snapshot testing
  });
});
// Run via: node --test [--test-reporter=spec] [--experimental-test-coverage]
```

### SQLite (`node:sqlite`, `lib/sqlite.js`)
```js
const { DatabaseSync } = require('node:sqlite');
const db = new DatabaseSync(':memory:');
db.exec('CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT)');
const insert = db.prepare('INSERT INTO t (name) VALUES (?)');
insert.run('Alice');
const row = db.prepare('SELECT * FROM t WHERE id = ?').get(1);
console.log(row.name); // 'Alice'
db.close();
```

### AsyncLocalStorage (`node:async_hooks`, `lib/async_hooks.js`)
```js
const { AsyncLocalStorage, AsyncResource } = require('node:async_hooks');
const store = new AsyncLocalStorage();
store.run({ userId: 123 }, () => {
  setTimeout(() => {
    console.log(store.getStore()); // { userId: 123 }
  }, 100);
});
```

### Single Executable Applications (`node:sea`, `lib/sea.js`)
```js
const { isSea, getAsset, getAssetAsBlob, getRawAsset } = require('node:sea');
if (isSea()) {
  const config = getAsset('config.json', 'utf8');
  const logo = getAssetAsBlob('logo.png');
}
```

### QUIC (experimental, `node:quic`, `lib/quic.js`)
```js
const { connect, listen, QuicEndpoint, QuicSession, QuicStream } = require('node:quic');
// Server
const endpoint = listen({ alpn: 'myproto', key, cert });
for await (const session of endpoint) {
  for await (const stream of session) { ... }
}
// Client
const session = connect({ address: 'localhost', port: 4433, alpn: 'myproto' });
const stream = await session.open();
```

---

## Public C++ Embedding API (`src/node.h`)

The embedding API allows external programs to host a Node.js environment.

### Initialization and Startup
```cpp
#include "node.h"
// Simple: run Node.js as a subprocess equivalent
int main(int argc, char* argv[]) {
  return node::Start(argc, argv);  // src/node.h:296
}
```

### CommonEnvironmentSetup (recommended embedder pattern)
```cpp
// src/node.h:939 — class CommonEnvironmentSetup
auto setup = node::CommonEnvironmentSetup::Create(
    platform, &errors, argc, argv, exec_argc, exec_argv);
v8::Isolate* isolate = setup->isolate();
node::Environment* env = setup->env();
{
  v8::HandleScope scope(isolate);
  v8::Context::Scope ctx(setup->context());
  // Load and run a script
  auto result = node::LoadEnvironment(env, "process.mainModule.require('./app')");
  if (result.IsEmpty()) { /* error */ }
  node::SpinEventLoop(env).FromJust();  // src/node.h:935
}
node::Stop(env);
```

### Environment Lifecycle
```cpp
// src/node.h:679, 688 — CreateEnvironment
node::Environment* env = node::CreateEnvironment(
    isolate_data, context, argc, argv, exec_argc, exec_argv);

// src/node.h:789–830 — LoadEnvironment (multiple overloads)
node::LoadEnvironment(env, "require('http').createServer(...).listen(8080)");
node::LoadEnvironment(env, node::StartExecutionCallback{...});

// src/node.h:835 — FreeEnvironment
node::FreeEnvironment(env);

// src/node.h:911, 914, 918
node::EmitProcessBeforeExit(env);
auto exit_code = node::EmitProcessExit(env);
node::RunAtExit(env);
```

### Key Embedding Types
- `node::Environment` — per-isolate runtime state; never share across threads
- `node::IsolateData` — V8 isolate metadata shared across Environments on same isolate
- `node::MultiIsolatePlatform` — V8 platform supporting multiple isolates; get via `node::GetMultiIsolatePlatform(env)`
- `node::CommonEnvironmentSetup` — RAII wrapper managing isolate + environment lifecycle
- `node::ThreadId` — Opaque thread identifier for worker threads

---

## Node-API (N-API) — `src/node_api.h`, `src/js_native_api.h`

N-API provides an ABI-stable interface for writing native add-ons. Supported versions: 1–10.

### Add-on Registration
```c
// Using macro (preferred)
NAPI_MODULE_INIT() {
  napi_value fn;
  napi_create_function(env, NULL, 0, MyFunction, NULL, &fn);
  napi_set_named_property(env, exports, "myFunction", fn);
  return exports;
}

// Legacy registration (deprecated)
NAPI_MODULE(addon, Init)
```

### Core N-API Patterns
```c
#include <node_api.h>

// Create values
napi_value str, num, obj, arr;
napi_create_string_utf8(env, "hello", NAPI_AUTO_LENGTH, &str);
napi_create_double(env, 3.14, &num);
napi_create_object(env, &obj);
napi_create_array(env, &arr);

// Set properties
napi_set_named_property(env, obj, "key", str);

// Create functions
napi_create_function(env, "fn", NAPI_AUTO_LENGTH, cb, nullptr, &fn);

// Error handling
napi_status status = napi_get_value_double(env, val, &result);
if (status != napi_ok) {
  napi_throw_error(env, NULL, "Expected a number");
  return nullptr;
}

// Async work
napi_async_work work;
napi_create_async_work(env, nullptr, resource_name, execute_cb, complete_cb, data, &work);
napi_queue_async_work(env, work);

// References (prevent GC)
napi_ref ref;
napi_create_reference(env, val, 1, &ref);
napi_value derefed;
napi_get_reference_value(env, ref, &derefed);
napi_delete_reference(env, ref);
```

---

## Module Customization Hooks (`module.register()`)

```js
// register() in ESM — hooks run in a separate worker thread
import { register } from 'node:module';
register('./my-hooks.mjs', import.meta.url);

// hooks file (my-hooks.mjs)
export async function resolve(specifier, context, nextResolve) {
  // intercept module resolution
  return nextResolve(specifier, context);
}
export async function load(url, context, nextLoad) {
  // intercept module loading / transform source
  const result = await nextLoad(url, context);
  return { ...result, source: transform(result.source) };
}
export function initialize(data) {
  // receive data passed to register()
}
```

---

## CLI Flags and Configuration

Key Node.js CLI flags (defined in `src/node_options.cc`):

```sh
node [options] [script.js | -e code] [args]

# Module system
--input-type=module|commonjs   # Treat stdin/eval as ESM or CJS
--experimental-default-type    # Default module type for ambiguous files
--import=<module>              # Preload ESM module before main
--require=<module>             # Preload CJS module before main (-r)

# TypeScript
--experimental-strip-types     # Enable TypeScript type stripping
--experimental-transform-types # Enable full TypeScript transforms

# Testing
--test                         # Run test runner mode
--test-reporter=<name>         # tap | spec | junit | dot | lcov
--test-reporter-destination    # Where to write reporter output
--experimental-test-coverage   # Enable code coverage

# Debugging
--inspect[=host:port]          # Enable V8 Inspector
--inspect-brk                  # Pause before first line

# Security
--permission                   # Enable permission model
--allow-fs-read=<path>         # Allow file system read for path
--allow-fs-write=<path>        # Allow file system write for path
--allow-net[=<host:port>]      # Allow network access
--allow-child-process          # Allow spawning child processes
--allow-addons                 # Allow native add-ons
--allow-worker                 # Allow worker threads
--allow-wasi                   # Allow WASI

# Performance
--compile-cache[=<dir>]        # Enable/specify compile cache directory
--max-old-space-size=<mb>      # V8 heap limit

# Watch mode
--watch                        # Restart on file changes
--watch-path=<dir>             # Specific paths to watch
--watch-preserve-output        # Don't clear terminal on restart
--watch-kill-signal=<signal>   # Signal to send before restart

# Environment
--env-file=<path>              # Load .env file
--env-file-if-exists=<path>    # Load .env file if it exists

# Misc
--run <script>                 # Run package.json script (like npm run)
--entry-url                    # Treat main argument as a URL (experimental)
--no-deprecation               # Silence deprecation warnings
--experimental-sea-config=<f>  # SEA configuration file
```

---

## Web-Compatible Globals

Globals available without require in both main thread and workers (`lib/internal/bootstrap/web/`):

- **`fetch(input, init?)`** — WHATWG Fetch (via undici)
- **`WebSocket`**, **`EventSource`** — WebSocket and SSE clients
- **`URL`**, **`URLSearchParams`** — WHATWG URL parsing
- **`TextEncoder`**, **`TextDecoder`** — String encoding
- **`AbortController`**, **`AbortSignal`** — Cancellation API
- **`ReadableStream`**, **`WritableStream`**, **`TransformStream`** — WHATWG Streams
- **`Blob`**, **`File`** — Binary data objects
- **`FormData`**, **`Headers`**, **`Request`**, **`Response`** — Fetch API types
- **`crypto`** — Web Crypto API (`crypto.subtle`, `crypto.getRandomValues()`)
- **`structuredClone(value)`** — Deep clone with transfer support
- **`queueMicrotask(fn)`** — Schedule microtask
- **`setTimeout`**, **`setInterval`**, **`clearTimeout`**, **`clearInterval`** — Timers
- **`setImmediate`**, **`clearImmediate`** — Node.js immediate timers
- **`process`** — Node.js process object
- **`console`** — Console output
- **`Buffer`** — Node.js binary data class
- **`__filename`**, **`__dirname`** — CJS module file paths (not in ESM by default)
- **`module`**, **`exports`**, **`require`** — CJS module system

---

## Integration Patterns

### TypeScript Support (v26+)
```sh
# Direct execution — strips types, no compilation needed
node --experimental-strip-types app.ts
# Full TypeScript transforms (decorators, enums, etc.)
node --experimental-transform-types app.ts
```

### ESM with import hooks
```js
// register a hook to handle .svelte, .vue, or custom files
import { register } from 'node:module';
register(new URL('./loader.mjs', import.meta.url));
```

### Compile cache for faster startup
```sh
node --compile-cache=./cache app.js
# Subsequent runs will be faster as compiled code is cached
```

### Permission model enforcement
```sh
node --permission --allow-fs-read=/app --allow-net=api.example.com app.js
```
