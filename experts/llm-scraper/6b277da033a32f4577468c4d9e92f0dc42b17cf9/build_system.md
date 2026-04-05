# LLM Scraper — Build System

## Build System Type

LLM Scraper uses the standard **TypeScript compiler (`tsc`)** as its sole build tool, invoked directly via an npm script. There is no bundler (no Webpack, Rollup, esbuild, or Vite) — the TypeScript sources are compiled to ESM JavaScript and shipped as-is. Test execution is handled by **Vitest**.

## Configuration Files

### `package.json`

The central manifest for the package. Key fields:

```json
{
  "type": "module",
  "name": "llm-scraper",
  "version": "2.0.0",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "test": "vitest run"
  }
}
```

- `"type": "module"` — all `.js` files in the package are treated as ES modules
- `"main": "dist/index.js"` — entry point for consumers after compilation
- No `"exports"` field — single-entry package, no subpath exports

### `tsconfig.json`

```json
{
  "compilerOptions": {
    "outDir": "dist",
    "declaration": true,
    "lib": ["ESNext", "DOM"],
    "module": "NodeNext",
    "target": "ESNext",
    "moduleResolution": "NodeNext"
  },
  "include": ["src/**/*.ts"]
}
```

Key settings:
- `"outDir": "dist"` — compiled output goes to `dist/`, which is what npm consumers import
- `"declaration": true` — generates `.d.ts` type declaration files alongside `.js` files
- `"lib": ["ESNext", "DOM"]` — includes both modern JS globals and browser DOM types (needed because `cleanup.ts` runs inside the browser context via `page.evaluate`)
- `"module": "NodeNext"` + `"moduleResolution": "NodeNext"` — strict ESM Node.js module resolution; all imports must use `.js` extensions
- `"target": "ESNext"` — no downleveling; outputs modern JavaScript
- `"include": ["src/**/*.ts"]` — only source files are compiled; tests and examples are excluded

### `vitest.config.ts`

```ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: ['tests/**/*.test.ts'],
    testTimeout: 30000,
  },
})
```

- Tests are discovered from `tests/**/*.test.ts`
- 30-second timeout per test (necessary because tests launch a real browser and make live LLM API calls)

### `.prettierrc`

Prettier configuration file for code formatting. Not involved in the build pipeline.

## External Dependencies

### Runtime Dependencies (bundled with the package)

| Package | Version | Purpose |
|---------|---------|---------|
| `ai` | ^6.0.77 | Vercel AI SDK — `generateText`, `streamText`, `Output`, `LanguageModel` types |
| `@ai-sdk/provider` | ^3.0.8 | Provider interface types shared across AI SDK packages |
| `turndown` | ^7.2.2 | HTML-to-Markdown conversion for the `markdown` preprocessing format |

### Dev Dependencies (not shipped, required for development/testing)

| Package | Version | Purpose |
|---------|---------|---------|
| `@ai-sdk/openai` | ^3.0.26 | OpenAI provider for tests and examples |
| `@types/node` | ^25.2.1 | Node.js TypeScript type definitions |
| `@types/react` | ^19.2.13 | React types (pulled in transitively by AI SDK) |
| `playwright` | ^1.58.2 | Browser automation — required by callers, used in tests |
| `typescript` | ^5.9.3 | TypeScript compiler |
| `vitest` | ^4.0.18 | Test runner |
| `zod` | ^4.3.6 | Schema definition for tests and examples |

### Optional Peer Dependencies (installed by end users per provider)

Users install the AI SDK provider for their chosen LLM:

```bash
npm i @ai-sdk/openai       # OpenAI / GPT models
npm i @ai-sdk/anthropic    # Anthropic / Claude models
npm i @ai-sdk/google       # Google / Gemini models
npm i ollama-ai-provider-v2 # Local Ollama models
```

Playwright must also be installed and browsers downloaded by the caller:

```bash
npm i playwright
npx playwright install chromium
```

### Dynamic CDN Dependency

The `text` format mode dynamically imports `@mozilla/readability` from `https://cdn.skypack.dev/@mozilla/readability` via `page.evaluate()` at runtime. This means:
- No npm installation required
- Requires network access from the browser context during scraping
- Version is not pinned; latest from Skypack CDN is always fetched

## Build Targets and Commands

### `npm run build`

Runs `tsc -p tsconfig.json`. This:
1. Type-checks all files in `src/`
2. Compiles `.ts` → `.js` (no downleveling, ESNext target)
3. Generates `.d.ts` declaration files
4. Outputs to `dist/`

Result: `dist/index.js`, `dist/preprocess.js`, `dist/models.js`, `dist/cleanup.js` plus their `.d.ts` counterparts.

There is no watch mode configured in scripts. For development, run `tsc -p tsconfig.json --watch` manually.

### `npm test`

Runs `vitest run` (non-interactive, single-pass). All tests in `tests/**/*.test.ts` are executed.

**Important**: Tests make live network requests and real LLM API calls. The `OPENAI_API_KEY` environment variable must be set. Tests also launch a real Chromium browser via Playwright, so Playwright browsers must be installed.

Running tests without the API key or Playwright browsers will cause test failures.

### No additional targets

There is no:
- `lint` script (though `.prettierrc` is present for editor integration)
- `prepublish` / `prepare` hook that auto-builds before `npm publish`
- Docker or container build
- CI configuration file in the repository

## How to Build from Source

```bash
# 1. Clone the repository
git clone https://github.com/mishushakov/llm-scraper.git
cd llm-scraper

# 2. Install dependencies
npm install

# 3. Build the TypeScript sources
npm run build
# Output appears in dist/

# 4. (Optional) Install Playwright browsers for testing
npx playwright install chromium
```

## How to Run Tests

```bash
# Set OpenAI API key (tests use gpt-4o-mini)
export OPENAI_API_KEY=sk-...

# Run all tests
npm test
```

Tests hit real URLs (`news.ycombinator.com`, `example.com`) and make real API calls. Test timeout is 30 seconds per test. The test suite uses a shared Chromium browser instance (singleton, initialized lazily, closed in `afterAll`).

## How to Use from npm (End Users)

```bash
npm i zod playwright llm-scraper
npm i @ai-sdk/openai   # or whichever provider
npx playwright install chromium
```

Consumers import from the built `dist/index.js` via `import LLMScraper from 'llm-scraper'`. No build step required for consumers — they use the pre-compiled `dist/` output.

## Publishing

No automated publish workflow is present in the repository. The package is published to npm as `llm-scraper`. Since there is no `prepare` script, the maintainer must manually run `npm run build` before `npm publish`.
