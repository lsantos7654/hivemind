# Jina Reader — Build System

## Build System Type and Configuration Files

The project uses **Node.js with TypeScript** compiled by the standard `tsc` compiler. There is no bundler (Webpack/Rollup/esbuild); the TypeScript compiler outputs CommonJS modules (targeting Node.js `node16` module resolution) directly to the `build/` directory.

Key configuration files:

| File | Purpose |
|---|---|
| `package.json` | Scripts, dependencies, engines constraint |
| `tsconfig.json` | TypeScript compiler options |
| `integrity-check.cjs` | Pre-build integrity check (runs before `tsc`) |
| `Dockerfile` | Production container definition |
| `.gitmodules` | References the `thinapps-shared` submodule |

## TypeScript Configuration (`tsconfig.json`)

```json
{
  "compilerOptions": {
    "module": "node16",
    "noImplicitReturns": true,
    "noUnusedLocals": true,
    "outDir": "build",
    "sourceMap": true,
    "strict": true,
    "allowJs": true,
    "target": "es2022",
    "lib": ["es2022"],
    "skipLibCheck": true,
    "useDefineForClassFields": false,
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true,
    "esModuleInterop": true,
    "noImplicitOverride": true
  },
  "compileOnSave": true,
  "include": ["src"]
}
```

Key settings of note:
- `"experimentalDecorators": true` and `"emitDecoratorMetadata": true` are required for the `tsyringe` dependency-injection decorators (`@singleton`, `@injectable`) and for `civkit`'s `@Method`, `@Param`, `@Ctx`, `@RPCReflect` decorators to work correctly.
- `"useDefineForClassFields": false` is critical for TypeScript decorators with class fields to behave as expected (standard decorator semantics, not the newer ES `define` semantics).
- `"module": "node16"` enables Node.js-style module resolution that respects `package.json` `exports` fields.
- Output goes to `build/` at the root level.

## External Dependencies and Management

All dependencies are managed via **npm** (`package-lock.json` is committed). The project requires **Node.js >= 18** (`"engines": { "node": ">=18" }`).

### Key Production Dependencies

| Package | Version | Purpose |
|---|---|---|
| `civkit` | `^0.9.0-2570394` | Internal RPC framework, async services, utilities |
| `puppeteer` | `^23.3.0` | Headless Chrome automation |
| `puppeteer-extra` | `^3.3.6` | Puppeteer plugin system |
| `puppeteer-extra-plugin-block-resources` | `^2.4.3` | Block unnecessary resource types |
| `@mozilla/readability` | `^0.6.0` | Article content extraction |
| `linkedom` | `^0.18.4` | Fast server-side DOM parsing |
| `node-libcurl` | `^4.1.0` | Native libcurl bindings (requires native build) |
| `turndown` | `^7.1.3` | HTML → Markdown conversion |
| `turndown-plugin-gfm` | `^1.0.2` | GFM tables/task lists for Turndown |
| `pdfjs-dist` | `^4.10.38` | PDF text extraction |
| `@napi-rs/canvas` | `^0.1.68` | Server-side canvas (native addon) |
| `koa` | `^2.16.0` | Web framework |
| `@koa/bodyparser` | `^5.1.1` | Request body parsing |
| `koa-compress` | `^5.1.1` | Response compression middleware |
| `firebase-admin` | `^12.1.0` | Firestore + Cloud Storage |
| `firebase-functions` | `^6.1.1` | Cloud Functions integration |
| `openai` | `^4.20.0` | OpenAI API client (for LM integration) |
| `tiktoken` | `^1.0.16` | Token counting for billing |
| `lru-cache` | `^11.0.2` | In-memory LRU cache (rate limit, high-freq keys) |
| `robots-parser` | `^3.0.1` | robots.txt parsing |
| `maxmind` | `^4.3.18` | MaxMind GeoIP database reader |
| `axios` | `^1.3.3` | HTTP client (used in some services) |
| `undici` | `^7.8.0` | Modern HTTP/2 client |
| `simple-zstd` | `^1.4.2` | Zstandard decompression |
| `jose` | `^5.1.0` | JWT/JWK handling for auth tokens |
| `bcrypt` | `^5.1.0` | Password hashing |
| `minio` | `^7.1.3` | Object storage client (alternative to Firebase Storage) |
| `stripe` | `^11.11.0` | Payment/billing integration |
| `@esm2cjs/normalize-url` | `^8.0.0` | URL normalization |
| `tld-extract` | `^2.1.0` | TLD/domain extraction |
| `langdetect` | `^0.2.1` | Language detection |
| `@google-cloud/translate` | `^8.2.0` | Google Cloud Translation API |
| `dayjs` | `^1.11.9` | Date/time utilities |

### Native Addons

Several dependencies require native compilation or pre-built binaries:
- `node-libcurl` — requires `libcurl` on the host. In Docker, `libcurl-impersonate` is copied from `lwthiker/curl-impersonate:0.6-chrome-slim-bullseye`.
- `@napi-rs/canvas` — pre-built N-API native addon.
- `bcrypt` — native bcrypt binding.

### Dev Dependencies

| Package | Purpose |
|---|---|
| `typescript` | `^5.5.4` | TypeScript compiler |
| `eslint` + plugins | Linting (Google style + import rules) |
| `@typescript-eslint/*` | TypeScript-specific ESLint rules |
| `pino-pretty` | Log beautification for development |
| `firebase-functions-test` | Cloud Functions unit testing |
| `replicate` | Replicate.com API (dev-time LM testing) |

## Build Targets and Commands

All commands are defined in `package.json` under `"scripts"`:

```json
{
  "lint":        "eslint --ext .js,.ts .",
  "build":       "node ./integrity-check.cjs && tsc -p .",
  "build:watch": "tsc --watch",
  "build:clean": "rm -rf ./build",
  "serve":       "npm run build && npm run start",
  "debug":       "npm run build && npm run dev",
  "start":       "node ./build/stand-alone/crawl.js",
  "dry-run":     "NODE_ENV=dry-run node ./build/stand-alone/search.js"
}
```

## How to Build

### Prerequisites

1. Install Node.js >= 18.
2. Ensure `libcurl-impersonate` is available (Linux; handled by Docker).
3. Clone including the submodule:
   ```bash
   git clone --recurse-submodules https://github.com/jina-ai/reader.git
   cd reader
   ```
4. Install dependencies:
   ```bash
   npm ci
   ```
5. Compile TypeScript:
   ```bash
   npm run build
   ```
   This first runs `integrity-check.cjs` (a pre-build validation step) then `tsc -p .`. Output lands in `build/`.

### Development with watch mode

```bash
npm run build:watch
```

This keeps `tsc` running and recompiles on every file change.

### Clean build

```bash
npm run build:clean && npm run build
```

## How to Run

### Standalone crawl server

```bash
npm start
# Equivalent to: node ./build/stand-alone/crawl.js
```

The server listens on port `3000` by default (HTTP/2 + HTTP/1.1 on port `3001`). Set `PORT` env var to override.

### Dry-run mode

```bash
npm run dry-run
# NODE_ENV=dry-run node ./build/stand-alone/search.js
```

In dry-run mode, the server initializes all services (including warm-up of Puppeteer and pre-compilation of Node.js JIT cache) and then shuts down cleanly. Used in the Docker build to pre-warm the `node_modules` compile cache.

## How to Test

No automated test suite is present in the open-source repository. The `firebase-functions-test` dev dependency suggests cloud function unit tests may exist internally.

Linting is available:
```bash
npm run lint
```

## How to Deploy via Docker

The `Dockerfile` defines the production deployment:

```dockerfile
# Stage 1: Extract curl-impersonate library
FROM lwthiker/curl-impersonate:0.6-chrome-slim-bullseye

# Stage 2: Production image
FROM node:22
# Install Google Chrome stable + required fonts
RUN apt-get update && apt-get install -y google-chrome-stable ...

# Copy curl-impersonate native library
COPY --from=0 /usr/local/lib/libcurl-impersonate.so /usr/local/lib/libcurl-impersonate.so

# Non-root user setup
RUN groupadd -r jina && useradd -g jina -G audio,video -m jina
USER jina

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Copy pre-built artifacts (not source — build outside container)
COPY build ./build
COPY public ./public
COPY licensed ./licensed

# Pre-warm Node.js JIT compile cache
RUN NODE_COMPILE_CACHE=node_modules npm run dry-run

ENV OVERRIDE_CHROME_EXECUTABLE_PATH=/usr/bin/google-chrome-stable
ENV LD_PRELOAD=/usr/local/lib/libcurl-impersonate.so
ENV CURL_IMPERSONATE=chrome116
ENV CURL_IMPERSONATE_HEADERS=no
ENV NODE_COMPILE_CACHE=node_modules
ENV PORT=8080

EXPOSE 3000 3001 8080 8081
ENTRYPOINT ["node"]
CMD ["build/stand-alone/crawl.js"]
```

Important notes:
- The build step (`npm run build`) must be run **before** building the Docker image, as the image copies pre-built `build/` artifacts.
- `LD_PRELOAD` injects `libcurl-impersonate.so` to override system libcurl, enabling Chrome TLS/HTTP fingerprint impersonation.
- `NODE_COMPILE_CACHE=node_modules` enables V8 bytecode caching for faster startup.
- The dry-run step inside `RUN` pre-warms the JIT cache during image build time.

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `PORT` | `3000` (Docker: `8080`) | HTTP server port |
| `OVERRIDE_CHROME_EXECUTABLE_PATH` | (auto-detect) | Path to Chrome/Chromium binary |
| `LD_PRELOAD` | — | Preload `libcurl-impersonate.so` |
| `CURL_IMPERSONATE` | — | Set Chrome version for curl impersonation |
| `NODE_COMPILE_CACHE` | — | Directory for V8 bytecode cache |
| `NODE_ENV` | — | Set to `dry-run` for initialization-only mode |
| Firebase credentials | — | Provided via application default credentials or `GOOGLE_APPLICATION_CREDENTIALS` |
