# Markdowner — Build System

## Build System Type and Configuration Files

Markdowner uses **Cloudflare Wrangler** as its build, development, and deployment toolchain. Wrangler is the official Cloudflare Workers CLI that handles TypeScript compilation (via esbuild), local emulation, and deployment to the Cloudflare edge network.

**Key configuration files:**
- `wrangler.toml` — primary Wrangler/Workers configuration (bindings, KV namespaces, AI, rate limiter, migrations)
- `package.json` — npm scripts and dev dependency declarations
- `tsconfig.json` — TypeScript compiler options (type checking only; Wrangler/esbuild handles bundling)
- `worker-configuration.d.ts` — auto-generated Cloudflare binding type declarations
- `.editorconfig` — editor-level formatting rules (tabs, LF line endings, UTF-8)
- `.prettierrc` — Prettier code formatter configuration

## External Dependencies

### Runtime Dependencies (loaded dynamically, not bundled)

These libraries are not npm-installed; they are injected as `<script>` tags inside the browser page at runtime via `page.evaluate()`:

| Library | Source URL | Purpose |
|---------|-----------|---------|
| `@mozilla/readability` | `https://unpkg.com/@mozilla/readability/Readability.js` | Article extraction — strips nav, footer, ads; returns main content HTML |
| `turndown` | `https://unpkg.com/turndown/dist/turndown.js` | HTML-to-Markdown conversion |

### npm Dev Dependencies (declared in `package.json`)

| Package | Version | Purpose |
|---------|---------|---------|
| `@cloudflare/workers-types` | `^4.20240502.0` | TypeScript type definitions for all Cloudflare Workers APIs (KV, DO, AI, etc.) |
| `typescript` | `^5.0.4` | TypeScript compiler for type checking (not used for emit — Wrangler handles that) |
| `wrangler` | `^3.53.1` | Cloudflare Workers CLI: local dev server, deployment, type generation |

### Implicit Runtime Dependencies (Cloudflare platform)

These are not installed as npm packages; they are provided by the Cloudflare Workers runtime:

| Binding | Type | Purpose |
|---------|------|---------|
| `MYBROWSER` | Browser Rendering API | Headless Chromium instances for page rendering |
| `BROWSER` | Durable Object Namespace | Persistent stateful browser session management |
| `MD_CACHE` | KV Namespace | Distributed key-value store for caching markdown results |
| `RATELIMITER` | Rate Limit Binding | IP-based rate limiting (10 req / 60 sec) |
| `AI` | Workers AI | LLM inference via `@cf/qwen/qwen1.5-14b-chat-awq` model |

### Indirect Dependencies (via `react-tweet/api`)

The `Tweet` TypeScript type is imported from `react-tweet/api`. This is a type-only import used in `getTweet()` to type the Twitter syndication API response. It is referenced in `src/index.ts:2` and shapes the `worker-configuration.d.ts` tweet interfaces.

## Build Targets and Commands

All commands are defined in `package.json` scripts and executed via `npm run <script>`:

### `npm run dev` / `npm run start`
```
wrangler dev
```
Starts a local development server that emulates the Cloudflare Workers environment. Note: **Browser Rendering API and Durable Objects require the Workers paid plan** and do NOT fully emulate locally — a live Cloudflare account with paid plan is effectively required for full local testing.

### `npm run deploy`
```
wrangler deploy
```
Builds (via esbuild) and deploys the Worker to the Cloudflare edge network. This command:
1. Compiles `src/index.ts` to a single bundled JavaScript file via esbuild (TypeScript stripping + bundling).
2. Uploads the compiled Worker bundle to Cloudflare's edge.
3. Provisions/updates the declared bindings (KV, Durable Objects, AI, Rate Limiter, Browser).
4. Runs Durable Object migrations defined in `[[migrations]]` (creates the `Browser` class, tagged `v1`).

### `npm run cf-typegen`
```
wrangler types
```
Regenerates `worker-configuration.d.ts` from the current `wrangler.toml` bindings. Run this whenever `wrangler.toml` bindings change to keep TypeScript types in sync.

## How to Build, Test, and Deploy

### Prerequisites

1. **Node.js** — required to run npm and Wrangler.
2. **Cloudflare account** — must be logged in via `wrangler login`.
3. **Workers paid plan** — required for Browser Rendering API and Durable Objects.

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/dhravya/markdowner
cd markdowner

# 2. Install dependencies
npm install

# 3. Create the KV namespace for caching
npx wrangler kv:namespace create md_cache
# This outputs a KV namespace ID — copy it

# 4. Update wrangler.toml
# In [[kv_namespaces]], replace the `id` value with the ID from step 3:
# id = "<your-kv-namespace-id>"
```

### Deployment

```bash
npm run deploy
```

The `BACKEND_SECURITY_TOKEN` environment variable should be set as a Cloudflare Workers secret for bypassing rate limits:
```bash
npx wrangler secret put BACKEND_SECURITY_TOKEN
```

### Local Development

```bash
npm run dev
```

For local development, many features (Browser Rendering, Durable Objects) require a Cloudflare account with paid plan and remote bindings. Purely local emulation of these features is limited.

### Type Generation

After modifying `wrangler.toml` bindings:
```bash
npm run cf-typegen
```
This regenerates `worker-configuration.d.ts` with up-to-date TypeScript types for all bindings.

### Testing

There are **no automated tests** in this repository. Verification is done manually by:
1. Running the development server (`npm run dev`)
2. Making curl requests:
   ```bash
   curl 'http://localhost:8787/?url=https://example.com'
   curl 'http://localhost:8787/?url=https://example.com&enableDetailedResponse=true'
   curl 'http://localhost:8787/?url=https://example.com&crawlSubpages=true' -H 'Content-Type: application/json'
   curl 'http://localhost:8787/?url=https://example.com&llmFilter=true'
   ```
3. Testing against the production deployment at `https://md.dhr.wtf`.

### KV Namespace Considerations

The production KV namespace ID is hardcoded in `wrangler.toml` (`id = "3186489f943d409a9b772d876a58a73e"`). When self-hosting, this ID must be replaced with the ID from your own `wrangler kv:namespace create md_cache` output.

For preview/development environments, a separate preview KV namespace can be added:
```toml
[[kv_namespaces]]
binding = "MD_CACHE"
id = "<production-id>"
preview_id = "<preview-id>"
```

## Cloudflare Workers Runtime Details

- **Compatibility date**: `2023-09-04` — pins the Workers runtime to a specific behavior snapshot.
- **Compatibility flags**: `nodejs_compat` — enables Node.js APIs within the Worker runtime (required for certain npm packages that rely on Node.js built-ins).
- **Durable Object migration**: Tagged `v1` with `new_classes = ["Browser"]`. This migration creates the Durable Object class on first deploy and must not be modified after deployment (new migrations must be added as new entries).
- **esbuild**: Wrangler uses esbuild internally for bundling, with TypeScript transpilation. The `tsconfig.json` has `noEmit: true` since Wrangler's bundler handles actual compilation.
