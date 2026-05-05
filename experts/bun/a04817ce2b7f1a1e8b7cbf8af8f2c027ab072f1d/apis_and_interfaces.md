# Bun — APIs and Interfaces

## Public APIs and Entry Points

Bun exposes its APIs through the global `Bun` object (aliased as `import ... from "bun"`), several built-in modules (`bun:sqlite`, `bun:ffi`, `bun:test`), and Node.js-compatible built-ins (`node:fs`, `node:path`, etc.). TypeScript types are in `packages/bun-types/`.

---

## Key APIs

### HTTP Server — `Bun.serve`

```ts
const server = Bun.serve({
  port: 3000,
  fetch(req: Request): Response | Promise<Response> {
    return new Response("Hello!");
  },
  // WebSocket support
  websocket: {
    open(ws: ServerWebSocket) { ws.send("connected"); },
    message(ws, data) { ws.send(data); },
    close(ws, code, reason) {},
  },
  // Static routes
  routes: {
    "/robots.txt": new Response("User-agent: *\nDisallow: /"),
    "/api/users": async (req) => Response.json(await getUsers()),
  },
  // TLS
  tls: { cert: Bun.file("cert.pem"), key: Bun.file("key.pem") },
  // Error handler
  error(err) { return new Response(err.message, { status: 500 }); },
});
```

Key types: `Server`, `ServerWebSocket<T>`, `ServerWebSocketSendStatus`, `WebSocketHandler`, `ServeOptions`, `TLSServeOptions`, `WebSocketServeOptions`.

`ServerWebSocket` methods: `send(data, compress?)`, `sendText(data, compress?)`, `sendBinary(data, compress?)`, `publish(topic, data)`, `subscribe(topic)`, `unsubscribe(topic)`, `close(code?, reason?)`, `ping()`, `pong()`, `terminate()`.

### File I/O — `Bun.file` / `Bun.write`

```ts
const file = Bun.file("/path/to/file.txt");
const text = await file.text();
const json = await file.json();
const bytes = await file.bytes();
const stream = file.stream();

await Bun.write("/path/to/output.txt", "Hello, world!");
await Bun.write(Bun.file("out.bin"), new Uint8Array([1, 2, 3]));

// FileSink for incremental writes
const sink = Bun.file("out.txt").writer();
sink.write("chunk 1");
sink.write("chunk 2");
await sink.flush();
sink.end();
```

`BunFile` extends `Blob` with `.text()`, `.json()`, `.bytes()`, `.arrayBuffer()`, `.stream()`, `.writer()`, `.exists()`, `.stat()`, `.slice(begin?, end?)`, `.type` (MIME type), `.size`, `.name`, `.lastModified`.

### Child Processes — `Bun.spawn` / `Bun.spawnSync`

```ts
const proc = Bun.spawn(["ls", "-la"], {
  cwd: "/tmp",
  env: { ...process.env, FOO: "bar" },
  stdin: "pipe",
  stdout: "pipe",
  stderr: "inherit",
  onExit(proc, exitCode, signalCode, error) {},
});
const text = await new Response(proc.stdout).text();
await proc.exited;

// Sync variant
const result = Bun.spawnSync(["echo", "hello"]);
console.log(result.stdout.toString()); // "hello\n"
```

`Subprocess` properties: `pid`, `stdin` (WritableStream), `stdout` (ReadableStream), `stderr`, `exited` (Promise<number>), `exitCode`, `signalCode`, `killed`, `resourceUsage()`.

### Shell Scripting — `Bun.$`

```ts
import { $ } from "bun";

const result = await $`ls -la`.text();
const files = await $`find . -name "*.ts"`.lines();
const { stdout, stderr, exitCode } = await $`git status`.quiet();

// Pipe between commands
await $`cat file.txt | grep "error" | wc -l`;

// Custom env/cwd
await $.env({ NODE_ENV: "production" })`npm run build`;
await $.cwd("/tmp")`ls`;

// Nothrow (don't throw on non-zero exit)
const result = await $`false`.nothrow();
```

`$.ShellPromise` methods: `.text()`, `.json()`, `.lines()`, `.bytes()`, `.arrayBuffer()`, `.blob()`, `.quiet()`, `.nothrow()`, `.throws(bool)`, `.env(env)`, `.cwd(dir)`, `.stdin(input)`.

### TCP/TLS Sockets — `Bun.connect` / `Bun.listen`

```ts
// Server
const server = Bun.listen({
  hostname: "localhost",
  port: 8080,
  socket: {
    open(socket) { socket.write("hello"); },
    data(socket, data) { socket.write(data); },
    close(socket) {},
    error(socket, err) {},
    drain(socket) {},
  },
});

// Client
const socket = await Bun.connect({
  hostname: "example.com",
  port: 443,
  tls: true,
  socket: {
    open(socket) {},
    data(socket, data) {},
    handshake(socket, success, authError) {},
  },
});
socket.write("GET / HTTP/1.1\r\n\r\n");
```

`TCPSocket` / `TLSSocket` methods: `write(data)`, `end(data?)`, `terminate()`, `flush()`, `ref()`, `unref()`, `reload(handler)`, `setServername(name)`, `getServername()`, `getPeerCertificate()`, `getAuthorizationError()`.

### UDP Sockets — `Bun.udpSocket`

```ts
const socket = await Bun.udpSocket({
  port: 9000,
  socket: {
    data(socket, buf, port, addr) { socket.send(buf, port, addr); },
    drain(socket) {},
    error(socket, err) {},
  },
});
socket.send(new Uint8Array([1, 2, 3]), 9001, "127.0.0.1");
```

### SQLite — `bun:sqlite`

```ts
import { Database } from "bun:sqlite";

const db = new Database("app.db", { create: true, strict: true });
const stmt = db.prepare("SELECT * FROM users WHERE id = ?");
const user = stmt.get(1);
const users = stmt.all();

// Transactions
const insert = db.transaction((users) => {
  for (const user of users) db.run("INSERT INTO users VALUES (?)", [user.name]);
});
insert(["Alice", "Bob"]);

// Serialization
const bytes = db.serialize();
const db2 = Database.deserialize(bytes);
```

`Database` methods: `prepare(sql)`, `query(sql)`, `run(sql, params?)`, `exec(sql)`, `transaction(fn)`, `serialize()`, `close()`, `loadExtension(path)`.
`Statement` methods: `get(...params)`, `all(...params)`, `run(...params)`, `values(...params)`, `iterate(...params)`, `finalize()`.

### PostgreSQL — `Bun.sql`

```ts
import { sql } from "bun";

const users = await sql`SELECT * FROM users WHERE id = ${userId}`;
const result = await sql`INSERT INTO users (name) VALUES (${name}) RETURNING *`;

// Transactions
await sql.begin(async (sql) => {
  await sql`INSERT INTO accounts VALUES (${id}, ${balance})`;
  await sql`UPDATE totals SET count = count + 1`;
});

// Connection options
const db = new Bun.SQL({ url: "postgres://user:pass@host/db", max: 10 });
```

### Redis/Valkey — `Bun.redis` / `Bun.valkey`

```ts
import { redis } from "bun";

await redis.set("key", "value", { ex: 60 });
const val = await redis.get("key");
await redis.del("key");
await redis.hset("hash", { field: "value" });
const client = new Bun.ValkeyClient({ url: "redis://localhost:6379" });
```

### S3 — `Bun.s3`

```ts
import { s3 } from "bun";

const file = s3.file("my-bucket/path/to/file.txt");
const text = await file.text();
await s3.write("my-bucket/output.txt", "Hello!");
const url = file.presign({ expiresIn: 3600 });

const client = new Bun.S3Client({
  bucket: "my-bucket",
  region: "us-east-1",
  accessKeyId: "...",
  secretAccessKey: "...",
});
```

### FFI — `bun:ffi`

```ts
import { dlopen, FFIType, CString, ptr, toBuffer } from "bun:ffi";

const { symbols } = dlopen("libsqlite3", {
  sqlite3_open: {
    args: [FFIType.cstring, FFIType.ptr],
    returns: FFIType.i32,
  },
});

// Inline C compilation
import { cc } from "bun:ffi";
const { symbols: { add } } = cc({
  source: `int add(int a, int b) { return a + b; }`,
  symbols: { add: { args: [FFIType.i32, FFIType.i32], returns: FFIType.i32 } },
});
console.log(add(1, 2)); // 3
```

`FFIType` enum values: `char`, `int8_t`/`i8`, `uint8_t`/`u8`, `int16_t`/`i16`, `uint16_t`/`u16`, `int32_t`/`i32`, `uint32_t`/`u32`, `int64_t`/`i64`, `uint64_t`/`u64`, `float`/`f32`, `double`/`f64`, `bool`, `ptr`, `cstring`, `void`, `function`.

### Bundler — `Bun.build`

```ts
const result = await Bun.build({
  entrypoints: ["./src/index.ts"],
  outdir: "./dist",
  target: "browser",        // "browser" | "bun" | "node"
  format: "esm",            // "esm" | "cjs" | "iife"
  splitting: true,
  minify: true,
  sourcemap: "external",
  define: { "process.env.NODE_ENV": '"production"' },
  loader: { ".png": "file", ".svg": "text" },
  plugins: [myPlugin],
  external: ["react"],
  // Single-file executable
  compile: true,
});

if (!result.success) {
  for (const msg of result.logs) console.error(msg);
}
```

`BuildConfig` key options: `entrypoints`, `outdir`, `outfile`, `target`, `format`, `splitting`, `minify` (bool or `{whitespace, identifiers, syntax}`), `sourcemap`, `define`, `loader`, `plugins`, `external`, `publicPath`, `naming`, `conditions`, `drop`, `banner`, `footer`, `compile`, `bytecode`.

### Transpiler — `Bun.Transpiler`

```ts
const transpiler = new Bun.Transpiler({
  loader: "tsx",
  define: { "process.env.NODE_ENV": '"production"' },
  target: "browser",
});
const code = transpiler.transformSync(`const x: number = 1;`);
const imports = transpiler.scanImports(code);
```

### Test Runner — `bun:test`

```ts
import { describe, test, expect, mock, spyOn, beforeAll, afterEach } from "bun:test";

describe("math", () => {
  test("adds numbers", () => {
    expect(1 + 1).toBe(2);
  });

  test("async test", async () => {
    const result = await fetch("https://example.com");
    expect(result.ok).toBeTrue();
  });
});

// Mocking
const fn = mock(() => 42);
expect(fn()).toBe(42);
expect(fn).toHaveBeenCalledTimes(1);

// Module mocking
mock.module("fs/promises", () => ({
  readFile: () => Promise.resolve("mocked"),
}));

// Time mocking
import { setSystemTime } from "bun:test";
setSystemTime(new Date("2024-01-01"));
```

`expect` matchers: `.toBe`, `.toEqual`, `.toStrictEqual`, `.toBeNull`, `.toBeUndefined`, `.toBeTruthy`, `.toBeFalsy`, `.toBeTrue`, `.toBeFalse`, `.toBeGreaterThan`, `.toBeLessThan`, `.toContain`, `.toMatch`, `.toThrow`, `.toHaveBeenCalled`, `.toHaveBeenCalledTimes`, `.toHaveBeenCalledWith`, `.toMatchSnapshot`, `.toMatchInlineSnapshot`, `.resolves`, `.rejects`.

### Crypto — `Bun.CryptoHasher` / `Bun.password`

```ts
const hasher = new Bun.CryptoHasher("sha256");
hasher.update("hello");
const digest = hasher.digest("hex");

// Convenience hashes
const hash = Bun.SHA256.hash("hello", "hex");
const md5 = Bun.MD5.hash(data);

// Password hashing
const hashed = await Bun.password.hash("my-password");
const valid = await Bun.password.verify("my-password", hashed);
```

Supported algorithms: `md4`, `md5`, `sha1`, `sha224`, `sha256`, `sha384`, `sha512`, `sha512-256`, `sha3-224`, `sha3-256`, `sha3-384`, `sha3-512`, `blake2b256`, `blake2b512`, `ripemd160`.

### Glob — `Bun.Glob`

```ts
const glob = new Bun.Glob("**/*.ts");
for await (const file of glob.scan({ cwd: "./src" })) {
  console.log(file);
}
const matches = glob.match("src/index.ts"); // true
```

### Semver — `Bun.semver`

```ts
Bun.semver.satisfies("1.2.3", "^1.0.0"); // true
Bun.semver.order("1.2.3", "1.3.0");       // -1
```

### HTMLRewriter

```ts
const rewriter = new HTMLRewriter()
  .on("a[href]", {
    element(el) {
      el.setAttribute("href", el.getAttribute("href")!.replace("http:", "https:"));
    },
  })
  .on("p", {
    text(text) { console.log(text.text); },
  });

const response = rewriter.transform(new Response("<a href='http://example.com'>link</a>"));
```

### FileSystemRouter

```ts
const router = new Bun.FileSystemRouter({
  style: "nextjs",
  dir: "./pages",
});
const match = router.match("/blog/hello-world");
// match.filePath, match.params, match.name, match.query
```

### Terminal (PTY) — `Bun.Terminal`

```ts
const terminal = new Bun.Terminal({
  cols: 80,
  rows: 24,
  onData(data) { process.stdout.write(data); },
  onExit(exitCode) {},
});
terminal.write("ls -la\n");
terminal.resize(120, 40);
```

### Bake (Full-Stack Dev Server)

```ts
import { Bake } from "bun";

Bun.serve({
  ...await Bake.serve({
    framework: "react",
    // or custom framework:
    framework: {
      serverEntrypoint: "./src/server.tsx",
      clientEntrypoint: "./src/client.tsx",
      router: { style: "nextjs", dir: "./pages" },
    },
  }),
});
```

## Configuration Options

### `bunfig.toml`

```toml
[install]
registry = "https://registry.npmjs.org"
cache = "~/.bun/install/cache"
frozen = false

[install.scopes]
"@myorg" = { registry = "https://npm.myorg.com", token = "$NPM_TOKEN" }

[test]
preload = ["./test-setup.ts"]
timeout = 5000
coverage = true

[run]
bun = true  # prefer bun over node for scripts
```

### Plugin API

```ts
import type { BunPlugin } from "bun";

const myPlugin: BunPlugin = {
  name: "my-plugin",
  setup(build) {
    build.onLoad({ filter: /\.txt$/ }, async ({ path }) => ({
      contents: await Bun.file(path).text(),
      loader: "text",
    }));
    build.onResolve({ filter: /^virtual:/ }, ({ path }) => ({
      path: path.replace("virtual:", ""),
      namespace: "virtual",
    }));
  },
};

await Bun.build({ entrypoints: ["./src/index.ts"], plugins: [myPlugin] });
// Also usable at runtime:
import { plugin } from "bun";
plugin(myPlugin);
```

## Integration Patterns

### Node.js compatibility

Bun supports most Node.js built-ins natively: `fs`, `path`, `os`, `crypto`, `http`, `https`, `net`, `stream`, `buffer`, `events`, `util`, `url`, `querystring`, `zlib`, `child_process`, `worker_threads`, `cluster`, `assert`, `tty`, `readline`, `dns`, `dgram`, `vm`, `module`, `perf_hooks`, `timers`, `string_decoder`, `punycode`, `domain`, `constants`.

### TypeScript / JSX

No configuration needed — Bun transpiles `.ts`, `.tsx`, `.jsx` natively. `tsconfig.json` paths are respected for module resolution.

### Environment variables

`.env`, `.env.local`, `.env.production`, `.env.development` are loaded automatically. Access via `process.env` or `Bun.env`.

### Single-file executables

```bash
bun build ./cli.ts --compile --outfile my-cli
./my-cli  # standalone binary, no bun required
```

### Macros

```ts
// macro.ts
export function getVersion() {
  return process.env.npm_package_version;
}

// usage.ts
import { getVersion } from "./macro.ts" with { type: "macro" };
console.log(getVersion()); // inlined at bundle time
```
