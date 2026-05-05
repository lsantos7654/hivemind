### Core Runtime Architecture
- `VirtualMachine.zig` — one VM per thread, wraps JSC `JSGlobalObject`; manages event loop, module loader, transpiler cache, source maps, hot reloader, plugin runner
- `ModuleLoader.zig` — ES module and CommonJS loader; handles `.ts`, `.tsx`, `.jsx`, `.json`, `.toml`, `.txt`, `.wasm` natively
- `HardcodedModule.zig` — registry of built-in modules (`bun:sqlite`, `bun:ffi`, `bun:test`, `node:fs`, etc.)
- `RuntimeTranspilerCache.zig` — caches transpiler results to avoid re-parsing unchanged files
- `SavedSourceMap.zig` — stores source maps for stack trace remapping
- `event_loop.zig` — event loop implementation; integrates with uSockets/libuv on Windows
- `hot_reloader.zig` — `ImportWatcher` union (`none`, `hot`, `watch`); drives `--hot` and `--watch` modes
- `web_worker.zig` — Web Worker support; each worker gets its own `VirtualMachine`
- `ipc.zig` — IPC channel for `Bun.spawn` with `ipc` option; Node.js-compatible `process.send`/`process.on("message")`
- `Debugger.zig` — V8 inspector protocol adapter for Chrome DevTools / VS Code debugger
- `ConsoleObject.zig` — `console.log`, `console.error`, `console.table`, `console.time`, etc.
- `crash_handler.zig` — crash reporting with stack traces and GitHub issue links

### JavaScript Engine (JSC)
- JavaScriptCore (JSC) is the JS engine; Bun uses a custom fork of WebKit (`oven-sh/WebKit`)
- `jsc.zig` — root JSC bindings module
- `jsc/` — C++ ↔ Zig bridge wrappers for JSC types (`JSValue`, `JSGlobalObject`, `JSObject`, `CallFrame`, etc.)
- `bindings/` — C++ binding implementations for JSC classes
- Codegen pipeline: `*.classes.ts` → `generate-classes.ts` → `ZigGeneratedClasses*` (C++ + Zig boilerplate)
- `*.bind.ts` / `*.bindv2.ts` — bindgen specs for type-safe JS↔Zig conversion
- `Strong.zig`, `Weak.zig`, `DeprecatedStrong.zig` — JSC GC root management

### HTTP Server (`Bun.serve`)
- `src/bun.js/api/server.zig` — main HTTP server implementation; `AnyServer` union dispatches to SSL/non-SSL variants
- Powered by uWebSockets (uWS) via `packages/bun-uws/` and `packages/bun-usockets/`
- `StaticRoute.zig` — serves static `Response` objects for fixed paths
- `FileRoute.zig` — serves files from disk with range request support
- `HTMLBundle.zig` / `HTMLBundle.Route` — serves bundled HTML imports
- `WebSocketServerContext.zig` — WebSocket upgrade and message dispatch
- `server/SSLConfig.bindv2.ts` — TLS configuration schema
- `AnyRoute` union: `.static`, `.file`, `.html`, `.framework_router`
- `Bun.serve` options: `port`, `hostname`, `fetch`, `websocket`, `routes`, `tls`, `error`, `development`, `maxRequestBodySize`, `id`
- `ServerWebSocket<T>` methods: `send`, `sendText`, `sendBinary`, `publish`, `subscribe`, `unsubscribe`, `close`, `ping`, `pong`, `terminate`, `cork`
- `Server` methods: `stop()`, `reload(options)`, `upgrade(req, options?)`, `publish(topic, data)`, `requestIP(req)`, `pendingRequests`, `pendingWebSockets`, `url`, `port`, `hostname`, `id`

### Bundler (`Bun.build`)
- `src/bundler/bundle_v2.zig` — `BundleV2`: main bundler orchestrator; multi-threaded with mimalloc thread-local heaps
- `LinkerContext.zig` — tree-shaking, code splitting, chunk assignment
- `LinkerGraph.zig` — dependency graph for linking
- `ParseTask.zig` — per-file parse task (runs on worker threads)
- `BundleThread.zig` — worker thread pool management
- `Graph.zig` — module graph
- `Chunk.zig` — output chunk representation
- `barrel_imports.zig` — barrel import optimization (re-export collapsing)
- `ServerComponentParseTask.zig` — React Server Component parse task
- `HTMLImportManifest.zig` — HTML import manifest for full-stack builds
- `JSBundler.zig` — `Bun.build()` JS API; `FileMap` for virtual files
- `BuildConfig` options: `entrypoints`, `outdir`, `outfile`, `target` (`browser`/`bun`/`node`), `format` (`esm`/`cjs`/`iife`), `splitting`, `minify`, `sourcemap`, `define`, `loader`, `plugins`, `external`, `publicPath`, `naming`, `conditions`, `drop`, `banner`, `footer`, `compile`, `bytecode`
- Plugin API: `build.onLoad({ filter })`, `build.onResolve({ filter })`, `build.onStart()`, `build.onEnd()`
- Macros: `import { fn } from "./macro.ts" with { type: "macro" }` — inlined at bundle time
- Single-file executables: `--compile` flag embeds JS + runtime into a standalone binary (`StandaloneModuleGraph.zig`)
- CSS bundler: `src/css/` — native CSS parsing and bundling
- HTML imports: `import html from "./index.html"` — full-stack bundling with Bake

### Package Manager (`bun install`)
- `src/install/PackageManager.zig` — main package manager; drives resolution, download, installation
- `lockfile.zig` — `Lockfile` struct; binary format (`bun.lockb`) and text format (`bun.lock`); `FormatVersion`, `TextLockfile.Version`
- `dependency.zig` — dependency resolution; semver, git, tarball, workspace, catalog dependencies
- `resolution.zig` — version resolution strategies
- `npm.zig` — npm registry client; manifest fetching, tarball downloading
- `PackageInstall.zig` — package installation (copy, hardlink, symlink strategies)
- `PackageInstaller.zig` — orchestrates parallel installation
- `lifecycle_script_runner.zig` — runs `preinstall`, `install`, `postinstall`, `prepare` scripts
- `hoisted_install.zig` — flat/hoisted install mode (default)
- `isolated_install.zig` — isolated install mode (pnpm-style)
- `extract_tarball.zig` — tarball extraction
- `patch_install.zig` — `bun patch` / `bun patch-commit` support
- `migration.zig` — lockfile migration from npm/yarn/pnpm
- `bin.zig` — binary linking into `node_modules/.bin/`
- `integrity.zig` — SHA-512 integrity verification
- `repository.zig` — git repository dependencies
- `pnpm.zig` — pnpm lockfile compatibility
- `yarn.zig` — yarn lockfile compatibility
- `windows-shim/` — Windows `.cmd` shims for binaries
- Commands: `bun install`, `bun add`, `bun remove`, `bun update`, `bun link`, `bun unlink`, `bun pm`, `bun outdated`, `bun audit`, `bun publish`, `bun pack`, `bun patch`, `bun patch-commit`, `bun why`, `bunx`
- Workspace support: `workspaces` in `package.json`; `--filter` flag for workspace scripts
- Registry configuration: `bunfig.toml [install]`, `.npmrc`, scoped registries, auth tokens

### Test Runner (`bun test`)
- `src/cli/test_command.zig` — test runner entry point
- `bun:test` module — Jest-compatible API
- `describe`, `test`, `it`, `expect`, `beforeAll`, `beforeEach`, `afterAll`, `afterEach`
- `mock(fn)` — function mocking; `mock.module(id, factory)` — module mocking; `mock.restore()`, `mock.clearAllMocks()`
- `spyOn(obj, method)` — spy on object methods
- `setSystemTime(date)` — mock `Date.now()` and `new Date()`
- `expect` matchers: `.toBe`, `.toEqual`, `.toStrictEqual`, `.toBeNull`, `.toBeUndefined`, `.toBeTruthy`, `.toBeFalsy`, `.toBeTrue`, `.toBeFalse`, `.toBeGreaterThan`, `.toBeLessThan`, `.toContain`, `.toMatch`, `.toThrow`, `.toHaveBeenCalled`, `.toHaveBeenCalledTimes`, `.toHaveBeenCalledWith`, `.toMatchSnapshot`, `.toMatchInlineSnapshot`, `.resolves`, `.rejects`, `.toSatisfy`
- Test configuration: `bunfig.toml [test]` — `preload`, `timeout`, `coverage`, `coverageThreshold`, `coverageReporter`, `bail`, `testNamePattern`
- Code coverage: `bun test --coverage`; LCOV and text reporters
- DOM testing: `happy-dom` integration via `@happy-dom/global-registrator`
- Watch mode: `bun test --watch`
- Snapshot testing: `expect(x).toMatchSnapshot()`, `bun test --update-snapshots`

### Shell Scripting (`Bun.$`)
- `src/shell/shell.zig` — shell entry point
- `src/shell/interpreter.zig` — shell interpreter; state machine
- `src/shell/Builtin.zig` — built-in commands: `cd`, `echo`, `ls`, `rm`, `mkdir`, `mv`, `cp`, `cat`, `pwd`, `which`, `export`, `unset`, `exit`, `true`, `false`, `printf`, `touch`, `head`, `tail`, `grep`, `wc`, `xargs`, `dirname`, `basename`, `env`
- `src/shell/ParsedShellScript.zig` — parsed shell AST
- `src/shell/braces.zig` — brace expansion (`{a,b,c}`, `{1..5}`)
- `$.ShellPromise` methods: `.text()`, `.json()`, `.lines()`, `.bytes()`, `.arrayBuffer()`, `.blob()`, `.quiet()`, `.nothrow()`, `.throws(bool)`, `.env(env)`, `.cwd(dir)`, `.stdin(input)`, `.pipe()`
- `$.escape(str)` — shell-escape a string
- `$.braces(pattern)` — brace expansion
- `$.env(env)` — set default environment
- `$.cwd(dir)` — set default working directory
- Cross-platform: works on Windows, macOS, Linux

### TCP/TLS Sockets
- `src/bun.js/api/bun/socket.zig` — `NewSocket(ssl)` generic; `TCPSocket`, `TLSSocket`
- `Listener.zig` — `Bun.listen()` return value; `ListenerType` union (uWS, Windows named pipe)
- `Handlers.zig` — socket event handlers: `onOpen`, `onClose`, `onData`, `onWritable`, `onTimeout`, `onConnectError`, `onEnd`, `onError`, `onHandshake`
- `SocketAddress.zig` — IP socket address with `address`, `port`, `family`, `flowlabel`
- `tls_socket_functions.zig` — TLS-specific: `getServername`, `setServername`, `getPeerCertificate`, `getAuthorizationError`, `authorized`
- `WindowsNamedPipeContext.zig` — Windows named pipe support
- `SSLWrapper.zig` — BoringSSL wrapper for TLS over arbitrary transports
- `SocketConfig.bindv2.ts` — socket configuration schema: `socket` (handlers), `data`, `allowHalfOpen`, `hostname`/`host`, `port`, `unix`, `tls`, `binaryType`
- `binaryType` options: `"arraybuffer"`, `"buffer"`, `"uint8array"`

### UDP Sockets
- `src/bun.js/api/bun/udp_socket.zig` — `UDPSocket`; `Bun.udpSocket(options)`
- Handlers: `data(socket, buf, port, addr)`, `drain(socket)`, `error(socket, err)`, `close(socket)`
- Methods: `send(data, port, addr)`, `sendMany(packets)`, `close()`, `ref()`, `unref()`

### Child Processes
- `src/bun.js/api/bun/subprocess.zig` — `Subprocess`; `Bun.spawn` / `Bun.spawnSync`
- `src/bun.js/api/bun/spawn.zig` — `BunSpawn.Actions` — low-level posix_spawn actions
- `src/bun.js/api/bun/js_bun_spawn_bindings.zig` — JS binding for spawn; PATH resolution
- `Subprocess` fields: `pid`, `stdin` (Writable), `stdout` (Readable), `stderr`, `exited` (Promise), `exitCode`, `signalCode`, `killed`, `resourceUsage()`
- `Readable.zig` — subprocess stdout/stderr as ReadableStream or Buffer
- `Writable.zig` — subprocess stdin as WritableStream
- `ResourceUsage.zig` — CPU/memory usage via `getrusage`
- Stdio options: `"pipe"`, `"inherit"`, `"ignore"`, `"ipc"`, `Bun.file(path)`, `ReadableStream`, `number` (fd)
- `onExit(proc, exitCode, signalCode, error)` callback

### HTTP/2
- `src/bun.js/api/bun/h2_frame_parser.zig` — HTTP/2 frame parser; HPACK header compression
- `src/bun.js/api/bun/lshpack.zig` — HPACK encoder/decoder wrapper (lshpack library)
- `h2.classes.ts` — HTTP/2 class definitions for JS bindings
- Supports HTTP/2 client and server via `node:http2` compatibility

### SQLite (`bun:sqlite`)
- `Database` class: `new Database(path, options?)`, `.prepare(sql)`, `.query(sql)`, `.run(sql, params?)`, `.exec(sql)`, `.transaction(fn)`, `.serialize()`, `.close()`, `.loadExtension(path)`, `.fileControl(cmd, value)`
- `Statement` class: `.get(...params)`, `.all(...params)`, `.run(...params)`, `.values(...params)`, `.iterate(...params)`, `.finalize()`, `.toString()`
- `DatabaseOptions`: `readonly`, `create`, `readwrite`, `safeIntegers`, `strict`
- Transactions: `db.transaction(fn)` returns a function; supports nested transactions via savepoints
- In-memory databases: `new Database(":memory:")`
- Serialization: `db.serialize()` → `Uint8Array`; `Database.deserialize(bytes)`

### PostgreSQL (`Bun.sql`)
- `src/sql/` — PostgreSQL client implementation
- `sql.d.ts` — TypeScript types: `SQL`, `ReservedSQL`, `TransactionSQL`, `SQLArrayParameter`
- Tagged template literal API: `` sql`SELECT * FROM users WHERE id = ${id}` ``
- `sql.begin(fn)` — transactions
- `sql.reserve()` — reserve a connection from the pool
- `Bun.SQL` constructor options: `url`, `hostname`, `port`, `database`, `username`, `password`, `max` (pool size), `idleTimeout`, `connectionTimeout`, `tls`

### Redis/Valkey (`Bun.redis` / `Bun.valkey`)
- `src/valkey/` — Valkey/Redis client implementation
- `valkey.classes.ts` — class definitions
- `redis.d.ts` — TypeScript types
- `Bun.ValkeyClient` constructor; `Bun.valkey` default client
- Commands: `get`, `set`, `del`, `exists`, `expire`, `ttl`, `hget`, `hset`, `hgetall`, `lpush`, `rpush`, `lpop`, `rpop`, `lrange`, `sadd`, `smembers`, `zadd`, `zrange`, `publish`, `subscribe`
- `set` options: `ex` (seconds), `px` (milliseconds), `nx`, `xx`, `get`

### S3 (`Bun.s3`)
- `src/bun.js/webcore/S3Client.zig`, `S3File.zig`, `S3Stat.zig` — S3 client implementation
- `s3.d.ts` — TypeScript types: `S3Client`, `S3File`, `S3Options`, `S3PresignOptions`
- `Bun.S3Client` constructor: `bucket`, `region`, `endpoint`, `accessKeyId`, `secretAccessKey`, `sessionToken`, `acl`
- `S3File` (extends `Blob`): `.text()`, `.json()`, `.bytes()`, `.stream()`, `.exists()`, `.stat()`, `.presign(options)`, `.delete()`, `.write(data)`, `.writer()`
- `presign` options: `expiresIn`, `method`, `acl`, `contentType`

### FFI (`bun:ffi`)
- `src/bun.js/api/ffi.zig` — FFI implementation using TinyCC for JIT C wrappers
- `dlopen(lib, symbols)` — load a shared library
- `FFIType` enum: `char`, `i8`/`int8_t`, `u8`/`uint8_t`, `i16`/`int16_t`, `u16`/`uint16_t`, `i32`/`int32_t`, `u32`/`uint32_t`, `i64`/`int64_t`, `u64`/`uint64_t`, `f32`/`float`, `f64`/`double`, `bool`, `ptr`, `cstring`, `void`, `function`
- `CString` — null-terminated C string wrapper
- `ptr(typedArray)` — get pointer to TypedArray data
- `toBuffer(ptr, byteOffset?, byteLength?)` — wrap pointer as Buffer
- `toArrayBuffer(ptr, byteOffset?, byteLength?)` — wrap pointer as ArrayBuffer
- `cc({ source, symbols })` — inline C compilation via TinyCC
- `JSCallback` — wrap a JS function as a C function pointer

### Crypto
- `src/bun.js/api/crypto.zig` — `Bun.CryptoHasher`, `Bun.SHA*`, `Bun.MD*`
- `Bun.CryptoHasher(algorithm)` — streaming hasher; `.update(data)`, `.digest(encoding?)`, `.copy()`
- Algorithms: `md4`, `md5`, `sha1`, `sha224`, `sha256`, `sha384`, `sha512`, `sha512-256`, `sha3-224`, `sha3-256`, `sha3-384`, `sha3-512`, `blake2b256`, `blake2b512`, `ripemd160`
- `Bun.SHA256.hash(data, encoding?)` — one-shot hash
- `Bun.password.hash(password, algorithm?)` — bcrypt/argon2 password hashing
- `Bun.password.verify(password, hash)` — password verification
- `Bun.hash(data)` — fast non-cryptographic hash (Wyhash)
- `Bun.hash.wyhash(data, seed?)`, `.adler32(data)`, `.crc32(data)`, `.cityHash32(data)`, `.cityHash64(data)`, `.murmur32v3(data)`, `.murmur64v2(data)`
- `Bun.CSRF` — CSRF token generation and verification
- Web Crypto API: `crypto.subtle`, `crypto.getRandomValues`, `crypto.randomUUID`

### Glob (`Bun.Glob`)
- `src/bun.js/api/glob.zig` — glob pattern matching
- `new Bun.Glob(pattern)` — create a glob matcher
- `.scan(options?)` — async iterator over matching files; options: `cwd`, `dot`, `absolute`, `followSymlinks`, `onlyFiles`
- `.scanSync(options?)` — sync variant
- `.match(path)` — test if a path matches the pattern

### Semver (`Bun.semver`)
- `src/semver.zig` — semver parsing and comparison
- `Bun.semver.satisfies(version, range)` — check if version satisfies range
- `Bun.semver.order(a, b)` — compare two versions (-1, 0, 1)

### HTMLRewriter
- `src/bun.js/api/html_rewriter.zig` — HTMLRewriter implementation (lol_html)
- `new HTMLRewriter()` — create a rewriter
- `.on(selector, handlers)` — element handler; `.onDocument(handlers)` — document handler
- Element handlers: `element(el)`, `comments(comment)`, `text(text)`
- Document handlers: `doctype(doctype)`, `comments(comment)`, `text(text)`, `end(end)`
- `Element` methods: `getAttribute(name)`, `setAttribute(name, value)`, `removeAttribute(name)`, `hasAttribute(name)`, `before(content, options?)`, `after(content, options?)`, `prepend(content, options?)`, `append(content, options?)`, `replace(content, options?)`, `remove()`, `removeAndKeepContent()`, `setInnerContent(content, options?)`
- `.transform(response)` — transform a Response

### FileSystemRouter
- `src/bun.js/api/filesystem_router.zig` — file system router
- `new Bun.FileSystemRouter({ style, dir, origin?, assetPrefix? })`
- `style` options: `"nextjs"` (pages router), `"nextjs-app"` (app router)
- `.match(request | string)` — returns `MatchedRoute | null`
- `MatchedRoute`: `filePath`, `params`, `name`, `pathname`, `query`, `kind`

### Terminal (PTY)
- `src/bun.js/api/bun/Terminal.zig` — PTY (pseudo-terminal) implementation
- `new Bun.Terminal({ cols, rows, onData, onExit, term? })`
- `.write(data)` — write to terminal stdin
- `.resize(cols, rows)` — resize the terminal
- `.close()` — close the terminal
- Creates master/slave PTY pair; `master_fd`, `slave_fd`, `read_fd`, `write_fd`

### Transpiler (`Bun.Transpiler`)
- `src/bun.js/api/JSTranspiler.zig` — transpiler JS API
- `new Bun.Transpiler({ loader, define, target, tsconfig?, macro?, autoImportJSX?, jsxOptimizationInline? })`
- `.transform(code)` — async transpile
- `.transformSync(code)` — sync transpile
- `.scan(code)` — scan imports/exports
- `.scanImports(code)` — scan only imports
- Loaders: `"js"`, `"jsx"`, `"ts"`, `"tsx"`, `"json"`, `"toml"`, `"text"`, `"base64"`, `"dataurl"`, `"file"`, `"wasm"`, `"napi"`

### Node.js Compatibility
- `src/bun.js/node/` — Zig implementations of Node.js built-ins
- `node_fs.zig` — `fs` module: `readFile`, `writeFile`, `readdir`, `stat`, `mkdir`, `rm`, `rename`, `copyFile`, `watch`, `watchFile`, `createReadStream`, `createWriteStream`, etc.
- `node_fs_watcher.zig` — `fs.watch` implementation
- `node_fs_stat_watcher.zig` — `fs.watchFile` implementation
- `node_process.zig` — `process` object: `env`, `argv`, `cwd()`, `chdir()`, `exit()`, `nextTick()`, `hrtime()`, `memoryUsage()`, `cpuUsage()`, `uptime()`, `pid`, `ppid`, `platform`, `arch`, `version`, `versions`
- `node_crypto_binding.zig` — `crypto` module bindings
- `node_net_binding.zig` — `net` module bindings
- `node_http_binding.zig` — `http`/`https` module bindings
- `node_os.zig` — `os` module: `hostname()`, `platform()`, `arch()`, `cpus()`, `freemem()`, `totalmem()`, `homedir()`, `tmpdir()`, `networkInterfaces()`
- `buffer.zig` — `Buffer` class; Node.js-compatible
- `path.zig` — `path` module: `join`, `resolve`, `dirname`, `basename`, `extname`, `parse`, `format`, `relative`, `normalize`, `isAbsolute`
- `node_zlib_binding.zig` — `zlib` module: `gzip`, `gunzip`, `deflate`, `inflate`, `brotliCompress`, `brotliDecompress`
- `node_assert.zig` — `assert` module
- `node_cluster_binding.zig` — `cluster` module

### Bake (Full-Stack Dev Server)
- `src/bake/DevServer.zig` — development server with HMR
- `src/bake/FrameworkRouter.zig` — framework-based file system routing
- `src/bake/production.zig` — production build
- `src/bake/bun-framework-react/` — built-in React framework integration
- `src/bake/hmr-module.ts` — HMR module runtime
- `src/bake/hmr-runtime-client.ts` — client-side HMR runtime
- `src/bake/hmr-runtime-server.ts` — server-side HMR runtime
- `bake.d.ts` — TypeScript types: `Bake.Options`, `Bake.Framework`, `Bake.BundlerOptions`
- `Bake.Framework` options: `bundlerOptions`, `router`, `serverEntrypoint`, `clientEntrypoint`, `serverComponents`, `reactFastRefresh`
- `Bun.serve({ ...await Bake.serve({ framework: "react" }) })` — start full-stack dev server

### Build System
- CMake ≥ 3.24 + Ninja — primary build orchestrator
- LLVM 21.1.8 (Clang) — C++ compiler (enforced version)
- Zig — auto-downloaded by `SetupZig.cmake`; primary implementation language
- Rust — for native plugin components (`rust-toolchain.toml`)
- `cmake/targets/BuildBun.cmake` — main build target; defines `bun-debug`, `bun-profile`, `bun`, `bun-asan`, `bun-valgrind`, `bun-assertions` variants
- C/C++ dependencies built from source: BoringSSL, Brotli, c-ares, Highway, libdeflate, lol_html, lshpack, mimalloc, zlib, libarchive, HdrHistogram, zstd, TinyCC, SQLite, libuv
- Codegen scripts: `generate-classes.ts`, `generate-jssink.ts`, `cppbind.ts`, `bundle-modules.ts`, `bundle-functions.ts`
- `CODEGEN_EMBED` — embeds codegen files in binary for release builds
- `BUN_DEBUG_<scope>=1` — enable scoped debug logging
- `bun run build` — debug build; `bun run build:release` — release build; `bun bd <args>` — build + run
- AddressSanitizer enabled by default in debug builds on Linux/macOS
- Nix flake (`flake.nix`) for reproducible dev environment
- `bunx bun-pr <pr-number>` — download release build from a PR's GitHub Actions artifacts

### Configuration (`bunfig.toml`)
- `[install]` — `registry`, `cache`, `frozen`, `production`, `dev`, `optional`, `peer`, `exact`, `auto` (install mode)
- `[install.scopes]` — per-scope registry and auth token configuration
- `[run]` — `bun` (prefer bun for scripts), `shell`
- `[test]` — `preload`, `timeout`, `coverage`, `coverageThreshold`, `coverageReporter`, `bail`, `testNamePattern`, `smol`
- `[serve]` — `port`, `hostname`
- `[debug]` — `editor`, `openUrl`
- `.npmrc` compatibility for registry and auth configuration

### Web APIs
- `fetch(url, options?)` — HTTP client; supports `AbortSignal`, `FormData`, `ReadableStream` body
- `Request`, `Response`, `Headers`, `URL`, `URLSearchParams` — Web standard types
- `ReadableStream`, `WritableStream`, `TransformStream` — WHATWG Streams
- `Blob` — binary data; `BunFile` extends `Blob` with file-specific methods
- `TextEncoder`, `TextDecoder` — UTF-8 encoding/decoding
- `WebSocket` — client WebSocket (browser-compatible)
- `EventSource` — server-sent events client
- `FormData` — multipart form data
- `crypto.subtle` — Web Crypto API (AES, RSA, ECDSA, HMAC, etc.)
- `crypto.getRandomValues`, `crypto.randomUUID`
- `performance.now()`, `performance.mark()`, `performance.measure()`
- `structuredClone(value, options?)` — deep clone with transfer support
- `queueMicrotask(fn)`, `setTimeout`, `setInterval`, `clearTimeout`, `clearInterval`, `setImmediate`
- `Worker` — Web Workers API
- `MessageChannel`, `MessagePort` — structured clone messaging

### Utilities
- `Bun.nanoseconds()` — high-resolution timer
- `Bun.sleep(ms)` / `Bun.sleepSync(ms)` — sleep
- `Bun.which(command)` — find executable in PATH
- `Bun.openInEditor(path)` — open file in editor
- `Bun.inspect(value, options?)` — format value for display
- `Bun.stringWidth(str)` — terminal string width (Unicode-aware)
- `Bun.color(input, format?)` — CSS color parsing and conversion
- `Bun.mmap(path, options?)` — memory-map a file
- `Bun.allocUnsafe(size)` — allocate uninitialized Buffer
- `Bun.shrink()` — trigger GC
- `Bun.gzipSync(data)`, `Bun.gunzipSync(data)`, `Bun.deflateSync(data)`, `Bun.inflateSync(data)` — compression
- `Bun.zstdCompressSync(data)`, `Bun.zstdDecompressSync(data)` — Zstandard compression
- `Bun.escapeHTML(str)` — HTML entity escaping
- `Bun.readableStreamToText(stream)`, `Bun.readableStreamToJSON(stream)`, `Bun.readableStreamToArrayBuffer(stream)`, `Bun.readableStreamToBlob(stream)`, `Bun.readableStreamToArray(stream)`, `Bun.readableStreamToBytes(stream)`
- `Bun.concatArrayBuffers(buffers)` — concatenate ArrayBuffers
- `Bun.peek(promise)` — synchronously peek at a Promise's resolved value
- `Bun.deepEquals(a, b, strict?)` — deep equality check
- `Bun.isMainThread` — true if running in main thread (not Worker)
- `Bun.main` — path to the main entry point
- `Bun.version` — Bun version string
- `Bun.revision` — git commit hash
- `Bun.env` — alias for `process.env`
- `Bun.argv` — alias for `process.argv`
- `Bun.cwd` — current working directory
- `Bun.embeddedFiles` — files embedded in a single-file executable
- `import.meta.dir` — directory of the current file
- `import.meta.file` — filename of the current file
- `import.meta.path` — absolute path of the current file
- `import.meta.main` — true if current file is the entry point
- `import.meta.resolve(specifier)` — resolve a module specifier to a URL
