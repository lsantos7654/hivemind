# Bun — APIs and Interfaces

## Public API Entry Points

Bun exposes APIs through three mechanisms:
1. **The `Bun` global namespace** — available in all JS/TS files running under Bun
2. **Built-in module imports** — `import { ... } from "bun"`, `bun:sqlite`, `bun:ffi`, etc.
3. **Node.js compatibility modules** — `node:fs`, `node:path`, `node:crypto`, etc.

Complete type definitions: `packages/bun-types/` and `src/js/builtins.d.ts`

---

## HTTP Server (`Bun.serve`)

```typescript
// Basic HTTP server
const server = Bun.serve({
  port: 3000,
  fetch(req: Request): Response {
    return new Response("Hello World");
  },
});

// With TLS (HTTPS)
Bun.serve({
  port: 443,
  tls: {
    cert: Bun.file("cert.pem"),
    key: Bun.file("key.pem"),
  },
  fetch(req) { return new Response("Secure"); },
});

// WebSocket upgrade
Bun.serve({
  fetch(req, server) {
    if (server.upgrade(req)) return; // returns undefined if upgraded
    return new Response("HTTP fallback");
  },
  websocket: {
    open(ws) { ws.send("connected"); },
    message(ws, msg) { ws.send(`echo: ${msg}`); },
    close(ws) { },
  },
});

// Stop the server
server.stop();
server.port; // number
server.hostname; // string
server.url;  // URL
```

**Source**: `src/bun.js/api/` + `src/http.zig`

---

## File I/O (`Bun.file`, `Bun.write`)

```typescript
// Read a file
const file = Bun.file("./data.json");
const json = await file.json();
const text = await file.text();
const bytes = await file.bytes(); // Uint8Array
const ab = await file.arrayBuffer();

// File metadata
file.size;      // number (bytes)
file.type;      // MIME type string
file.name;      // file path
file.lastModified; // Unix timestamp

// Write a file
await Bun.write("./output.txt", "Hello");
await Bun.write("./output.txt", new Uint8Array([1, 2, 3]));
await Bun.write("./output.json", JSON.stringify({ key: "value" }));

// Copy a file
await Bun.write(Bun.file("./dest.txt"), Bun.file("./src.txt"));

// Stream a file
const stream = file.stream(); // ReadableStream
```

**Source**: `src/bun.js/` + `src/fs.zig`

---

## Bundler (`Bun.build`)

```typescript
// Basic bundle
const result = await Bun.build({
  entrypoints: ["./src/index.ts"],
  outdir: "./dist",
  minify: true,
  sourcemap: "linked",
  target: "browser", // "browser" | "bun" | "node"
});

if (!result.success) {
  console.error(result.logs);
}

// With plugins
Bun.build({
  entrypoints: ["./src/index.ts"],
  outdir: "./dist",
  plugins: [
    {
      name: "my-plugin",
      setup(build) {
        build.onLoad({ filter: /\.txt$/ }, async (args) => {
          return {
            contents: `export default ${JSON.stringify(await Bun.file(args.path).text())}`,
            loader: "js",
          };
        });
      },
    },
  ],
});

// Code splitting
Bun.build({
  entrypoints: ["./app.ts", "./admin.ts"],
  outdir: "./dist",
  splitting: true,
});

// Output to in-memory (no outdir)
const result = await Bun.build({
  entrypoints: ["./src/index.ts"],
});
for (const artifact of result.outputs) {
  const content = await artifact.text();
}
```

**Source**: `src/bundler/bundle_v2.zig`

---

## Test Runner (`bun:test`)

```typescript
import { test, it, describe, expect, beforeAll, afterEach,
         mock, spyOn, jest } from "bun:test";

describe("math", () => {
  test("addition", () => {
    expect(1 + 2).toBe(3);
    expect([1, 2]).toEqual([1, 2]);
    expect("hello").toContain("ell");
    expect(() => { throw new Error(); }).toThrow();
  });

  it("async", async () => {
    const result = await Promise.resolve(42);
    expect(result).toBe(42);
  });
});

// Mocking
const mockFn = mock((x: number) => x * 2);
mockFn(5);
expect(mockFn).toHaveBeenCalledTimes(1);
expect(mockFn).toHaveBeenCalledWith(5);

// Spying
const obj = { method: (x: number) => x };
const spy = spyOn(obj, "method");
obj.method(42);
expect(spy).toHaveBeenCalledWith(42);

// Snapshots
expect({ a: 1 }).toMatchSnapshot();
expect("hello world").toMatchInlineSnapshot(`"hello world"`);

// Lifecycle hooks
beforeAll(() => { /* setup */ });
afterEach(() => { /* cleanup */ });
```

**Source**: `src/test/runner.zig`; `src/bun.js/api/jest.classes.ts`

---

## SQLite (`bun:sqlite`)

```typescript
import { Database } from "bun:sqlite";

const db = new Database("./mydb.sqlite");
// In-memory: new Database(":memory:")

// Execute statements
db.exec("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)");

// Prepared statements (preferred for performance)
const insert = db.prepare("INSERT INTO users (name) VALUES (?)");
insert.run("Alice");
insert.run("Bob");

// Query
const users = db.query("SELECT * FROM users").all();
// => [{ id: 1, name: "Alice" }, { id: 2, name: "Bob" }]

const first = db.query("SELECT * FROM users WHERE id = ?").get(1);

// Transactions
const insertMany = db.transaction((names: string[]) => {
  for (const name of names) insert.run(name);
});
insertMany(["Carol", "Dave"]);

db.close();
```

**Source**: `src/sql/sqlite.zig`

---

## Process Spawning (`Bun.spawn`, `Bun.spawnSync`)

```typescript
// Async spawn
const proc = Bun.spawn({
  cmd: ["ls", "-la"],
  cwd: "/tmp",
  env: { ...Bun.env, CUSTOM_VAR: "value" },
  stdout: "pipe",
  stderr: "pipe",
  stdin: "pipe",
});

const stdout = await new Response(proc.stdout).text();
const exitCode = await proc.exited;

// Sync spawn
const result = Bun.spawnSync({ cmd: ["echo", "hello"] });
result.stdout.toString(); // "hello\n"
result.exitCode;          // 0

// Write to stdin
proc.stdin.write("input data");
proc.stdin.end();
```

**Source**: `src/bun.js/api/` + `src/cli/exec.zig`

---

## Shell (`Bun.$`)

```typescript
import { $ } from "bun";

// Execute shell command
const { stdout, stderr, exitCode } = await $`ls -la`;
console.log(stdout.text());

// Variable interpolation (safe, no injection)
const filename = "my file.txt";
await $`cat ${filename}`;

// Piping
await $`cat file.txt | grep "pattern" | wc -l`;

// Redirect output to a file
await $`echo "hello" > output.txt`;

// Quiet mode (no stdout to terminal)
await $`npm install`.quiet();

// Custom env/cwd
await $`git status`.cwd("/path/to/repo").env({ GIT_DIR: "/custom" });

// Stream output
for await (const line of $`tail -f logfile.txt`.lines()) {
  console.log(line);
}
```

**Source**: `src/shell/interpreter.zig`

---

## FFI (`bun:ffi`)

```typescript
import { dlopen, FFIType, suffix } from "bun:ffi";

const lib = dlopen(`libm.${suffix}`, {
  cos: {
    args: [FFIType.double],
    returns: FFIType.double,
  },
  sin: {
    args: [FFIType.double],
    returns: FFIType.double,
  },
});

const { cos, sin } = lib.symbols;
console.log(cos(Math.PI)); // -1
console.log(sin(Math.PI / 2)); // 1

// With CString and pointers
import { CString, ptr, read } from "bun:ffi";
const cstr = new CString(rawPointer);
```

**Source**: `src/bun.js/bindings/` — FFI implementation

---

## Hashing and Crypto (`Bun.hash`, `Bun.CryptoHasher`)

```typescript
// Fast non-cryptographic hashes
Bun.hash("hello");              // default (Wyhash)
Bun.hash.wyhash("hello");       // Wyhash
Bun.hash.adler32("hello");      // Adler-32
Bun.hash.crc32("hello");        // CRC-32
Bun.hash.xxHash32("hello");     // xxHash 32-bit
Bun.hash.xxHash64("hello");     // xxHash 64-bit
Bun.hash.xxHash3("hello");      // xxHash 3

// Cryptographic hasher
const hasher = new Bun.CryptoHasher("sha256");
hasher.update("hello");
hasher.update(" world");
const hash = hasher.digest("hex"); // "b94d27b9..."

// Password hashing
const hashed = await Bun.password.hash("my-password");
const valid = await Bun.password.verify("my-password", hashed);

// Argon2 (default) or bcrypt
const argon = await Bun.password.hash("pw", { algorithm: "argon2id" });
const bcrypt = await Bun.password.hash("pw", { algorithm: "bcrypt", cost: 10 });
```

---

## Glob Matching (`Bun.Glob`)

```typescript
const glob = new Bun.Glob("**/*.ts");

// Scan directory
for await (const file of glob.scan({ cwd: "./src" })) {
  console.log(file); // relative paths
}

// Test a path
glob.match("src/index.ts"); // true
glob.match("README.md");    // false
```

---

## Workers (Multi-threading)

```typescript
// Main thread
const worker = new Worker("./worker.ts");
worker.postMessage({ data: [1, 2, 3] });
worker.onmessage = (e) => console.log(e.data);

// worker.ts
self.onmessage = (e) => {
  const result = e.data.data.reduce((a: number, b: number) => a + b, 0);
  self.postMessage(result);
};
```

---

## FileSystemRouter (`Bun.FileSystemRouter`)

```typescript
const router = new Bun.FileSystemRouter({
  style: "nextjs",
  dir: "./pages",
  origin: "https://example.com",
});

const match = router.match("/blog/post/hello");
if (match) {
  match.filePath;   // "/pages/blog/[slug].tsx"
  match.pathname;   // "/blog/post/hello"
  match.params;     // { slug: "hello" }
  match.query;      // URLSearchParams
}
```

**Source**: `src/router.zig`

---

## Key Environment and Metadata APIs

```typescript
// Bun version
Bun.version;           // "1.3.11"
Bun.revision;          // git commit hash

// Environment variables
Bun.env.NODE_ENV;      // Same as process.env
Bun.env.MY_VAR = "x"; // Set env var

// Entry point detection
import.meta.main;       // true if this file was run directly
import.meta.path;       // absolute path of this file
import.meta.dir;        // directory of this file
import.meta.url;        // file:// URL of this file

// Semver utilities
Bun.semver.satisfies("1.2.3", "^1.0.0"); // true
Bun.semver.order("1.2.3", "1.2.4");      // -1

// Main process info
process.pid;
process.argv;
process.exit(0);
```

---

## Configuration and Extension Points

### Plugin API (Bundler)

```typescript
import type { BunPlugin } from "bun";

const myPlugin: BunPlugin = {
  name: "my-loader",
  setup(build) {
    // Transform files at load time
    build.onLoad({ filter: /\.yaml$/ }, async (args) => ({
      contents: `export default ${JSON.stringify(parseYaml(await Bun.file(args.path).text()))}`,
      loader: "js",
    }));

    // Resolve custom specifiers
    build.onResolve({ filter: /^virtual:/ }, (args) => ({
      path: args.path,
      namespace: "virtual",
    }));
  },
};

// Register globally for all `bun run` invocations
// In bunfig.toml:
// preload = ["./my-plugin.ts"]
```

### bunfig.toml Configuration

```toml
[install]
registry = "https://registry.npmjs.org"
exact = false

[run]
preload = ["./setup.ts"]

[test]
preload = ["./test-setup.ts"]
coverage = true
coverageDir = "./coverage"

[bundle]
entrypoints = ["./src/index.ts"]
outdir = "./dist"
```

---

## Integration Patterns

### Drop-in Node.js Replacement

```bash
# Run a Node.js script with Bun
bun node-script.js

# Use bun as the node binary
ln -s $(which bun) /usr/local/bin/node
```

### TypeScript Without Compilation

```bash
# Run TypeScript directly — no tsc needed
bun ./src/server.ts
```

### Bun as a Script Runner

```bash
# Run package.json scripts (faster than npm run)
bun run dev
bun run build
bun run test
```
