# Ant Design — Build System

## Build System Overview

Ant Design uses a multi-tool build pipeline:

| Tool | Role |
|---|---|
| **father** (v4.6.17) | Compiles ESM (`es/`) and CJS (`lib/`) outputs from TypeScript source |
| **utoopack** (via father UMD config) | Bundles UMD output (`dist/antd.js`, `dist/antd.min.js`) |
| **antd-tools** (`@ant-design/tools`) | Custom Ant Design CLI for compilation, API sorting, diff checks |
| **dumi** (v2.4.x) | Documentation site generator (dev server + static build) |
| **webpack** | Alternative bundler config for special build scenarios |
| **mako** | Experimental high-performance bundler (mako.config.json present) |
| **tsx** | TypeScript script runner used by all `scripts/*.ts` files |

## Configuration Files

| File | Purpose |
|---|---|
| `.fatherrc.ts` | father build config — defines UMD entries and copy rules |
| `tsconfig.json` | TypeScript compiler settings (strict, esnext, bundler resolution) |
| `tsconfig-old-react.json` | TypeScript config for React 17 compatibility checks |
| `.jest.js` | Jest config for main test suite (jsdom environment) |
| `.jest.node.js` | Jest config for Node.js environment tests |
| `webpack.config.js` | Webpack configuration for UMD builds via antd-tools |
| `mako.config.json` | Mako bundler configuration (experimental) |
| `.dumirc.ts` | Dumi documentation site configuration |
| `biome.json` | Biome linter and formatter config |
| `eslint.config.mjs` | ESLint flat config |
| `.lintstagedrc.json` | Lint-staged hooks for pre-commit validation |

## Key Build Commands

### Development

```bash
# Start dev documentation server (port 8001)
npm run start
# Pre-start runs: version + token:statistic + token:meta + lint:changelog + style
```

### Compilation (Library Output)

```bash
# Full compile: clean + ESM/CJS via antd-tools + UMD dist
npm run build

# Only ESM/CJS (no UMD):
npm run compileOnly
# Runs: clean → antd-tools run compile

# Only UMD bundle:
npm run dist
# Pre-dist: version + token:statistic + token:meta + style
# Installs React 18 for UMD build compatibility, then antd-tools run dist
```

The `compile` step produces two output trees:
- `es/` — ES module format (tree-shakeable, used by bundlers)
- `lib/` — CommonJS format (used by older toolchains)

The `dist` step produces:
- `dist/antd.js` / `dist/antd.min.js` — full UMD bundle (React/ReactDOM/dayjs external)
- `dist/antd-with-locales.js` / `dist/antd-with-locales.min.js` — with all locale packs bundled
- `dist/reset.css` — CSS reset (copied from `components/style/reset.css`)
- `dist/antd.css` — Pre-built static CSS (copied from `components/style/antd.css`)

### Style Generation

```bash
# Generate static CSS files (used for SSR/non-JS environments)
npm run style
# Runs: tsx scripts/build-style.tsx
# Optionally with CSS @layer argument for cascade layers support
```

### Testing

```bash
# Full unit test suite (jsdom)
npm run test
# Equivalent: jest --config .jest.js --no-cache

# Update snapshots
npm run test:update

# Node.js environment tests
npm run test:node

# All test variants (unit + node + dekko + image)
npm run test:all  # sh ./scripts/test-all.sh

# Image regression tests (requires puppeteer)
npm run test:image

# Site tests
npm run test:site

# Visual regression
npm run test:visual-regression
```

### Linting and Type Checking

```bash
# Full lint suite
npm run lint
# Runs: version + tsc + lint:script + lint:biome + lint:md + lint:changelog

# TypeScript type check only
npm run tsc

# ESLint
npm run lint:script

# Biome lint
npm run lint:biome

# Markdown lint (remark)
npm run lint:md

# CSS-in-JS token validation
npm run lint:style

# Format with biome
npm run format

# Format with prettier
npm run prettier
```

### Token Tooling

```bash
# Collect token usage statistics across all components
npm run token:statistic  # tsx scripts/collect-token-statistic.ts

# Generate token metadata JSON (used by documentation)
npm run token:meta       # tsx scripts/generate-token-meta.ts
```

### Publishing

```bash
# Pre-publish validation (run automatically by npm)
# Validates version bump, checks repo state
npm run prepublishOnly   # tsx scripts/pre-publish.ts

# Post-publish (run automatically by npm)
# Syncs to OSS/CDN, triggers downstream jobs
npm run postpublish      # tsx scripts/post-publish.ts
```

### Documentation Site

```bash
# Build static documentation site
npm run site
# Pre-site: prestart + style (with @layer)
# Runs: dumi build, copies .surgeignore → _site/

# Deploy to GitHub Pages
npm run deploy  # gh-pages -d _site -b gh-pages -f
```

## External Dependencies

### Runtime Dependencies (bundled in `antd` npm package)

- `@ant-design/cssinjs` — CSS-in-JS engine for style generation and injection
- `@ant-design/cssinjs-utils` — Shared utilities (token merging, style caching)
- `@ant-design/colors` — Color palette generation (e.g., primary color → 10-shade palette)
- `@ant-design/fast-color` — High-performance colour parsing/manipulation
- `@ant-design/icons` — Icon font and SVG icon components
- `@ant-design/react-slick` — Carousel slider (fork of react-slick)
- `@rc-component/*` (50+ packages) — Headless primitive components for every complex widget
- `dayjs` — Lightweight date library (date pickers)
- `clsx` — Conditional CSS class name joining
- `scroll-into-view-if-needed` — Scroll utilities
- `throttle-debounce` — Rate limiting utilities
- `@babel/runtime` — Babel helper runtime

### Peer Dependencies

```json
{
  "react": ">=18.0.0",
  "react-dom": ">=18.0.0"
}
```

React 18 is the minimum; React 19 is fully supported (antd v6 dropped the v5-patch-for-react-19 compatibility shim).

### Dev-Only Tooling (not shipped in package)

- `@ant-design/tools` — `antd-tools` CLI (compile, dist, api-collection, package-diff)
- `father` — Library build tool (ESM/CJS compilation)
- `dumi` — Documentation site (dev server + static build)
- `jest` + `@testing-library/react` + `jest-axe` — Testing
- `typescript` — Type checking
- `biome` + `eslint` — Linting and formatting
- `webpack` + `webpack-bundle-analyzer` — Bundle analysis
- `puppeteer` — Image/visual regression testing
- `size-limit` — Bundle size tracking (limit: 434 KiB gzipped for antd.min.js)

## Output Package Structure

The published `antd` npm package contains:

```
antd/
├── es/           # ESM output (import antd from 'antd/es/button')
├── lib/          # CJS output (require('antd/lib/button'))
├── dist/         # UMD bundles
│   ├── antd.js
│   ├── antd.min.js
│   ├── antd-with-locales.js
│   ├── antd-with-locales.min.js
│   ├── reset.css
│   └── antd.css
├── locale/       # Locale files (CommonJS)
│   ├── en_US.js
│   └── ...
└── BUG_VERSIONS.json
```

The `package.json` entry points:
- `"main": "lib/index.js"` — CJS entry
- `"module": "es/index.js"` — ESM entry
- `"unpkg": "dist/antd.min.js"` — CDN entry
- `"typings": "es/index.d.ts"` — TypeScript types
