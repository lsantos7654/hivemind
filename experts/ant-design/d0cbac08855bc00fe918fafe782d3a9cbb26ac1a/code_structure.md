# Ant Design — Code Structure

## Annotated Directory Tree

```
ant-design/
├── components/                     # All component source code (primary deliverable)
│   ├── index.ts                    # Root public export — re-exports all 84+ components + types
│   │
│   ├── _util/                      # Shared internal utilities (not exported from antd directly)
│   │   ├── warning.ts              # devUseWarning(), WarningContext, warning() — dev-mode alerts
│   │   ├── type.ts                 # Shared TypeScript helpers: GetProp, GetProps, GetRef, AnyObject
│   │   ├── responsiveObserver.ts   # Breakpoint observation for responsive grid
│   │   ├── motion.ts               # Motion/animation utilities
│   │   ├── hooks/                  # Shared hooks (useMergeSemantic, etc.)
│   │   ├── wave/                   # Click wave effect (ripple) implementation
│   │   ├── PurePanel.tsx           # HOC for rendering components without a Provider (popup testing)
│   │   ├── ContextIsolator.tsx     # Utility to isolate React context for portal components
│   │   ├── statusUtils.ts          # Status helpers (error, warning, success, validating)
│   │   ├── placements.ts           # Shared tooltip/popup placement constants
│   │   ├── zindexContext.ts        # Z-index stacking context
│   │   └── scrollTo.ts             # Smooth scroll utilities
│   │
│   ├── theme/                      # Design Token System
│   │   ├── index.tsx               # Public API: useToken, defaultAlgorithm, darkAlgorithm, compactAlgorithm, getDesignToken
│   │   ├── internal.ts             # Internal token context and useToken hook (array-based for perf)
│   │   ├── context.ts              # React context for DesignTokenContext
│   │   ├── useToken.ts             # Re-exported hook
│   │   ├── getDesignToken.ts       # Static design token computation (no React required)
│   │   ├── interface/              # TypeScript interfaces for all token tiers
│   │   │   ├── index.ts            # Re-exports: SeedToken, MapToken, AliasToken, GlobalToken
│   │   │   ├── seeds.ts            # SeedToken interface (primitive design values)
│   │   │   ├── maps/               # MapToken interfaces (colour scales, font scales, etc.)
│   │   │   ├── alias.ts            # AliasToken interface (semantic names)
│   │   │   ├── components.ts       # Per-component token overrides interface
│   │   │   └── presetColors.ts     # Preset palette color names
│   │   └── themes/                 # Algorithm implementations
│   │       ├── seed.ts             # Default seed token values (colorPrimary: '#1677ff', etc.)
│   │       ├── default/            # Default (light) theme mapping functions
│   │       ├── dark/               # Dark theme mapping functions
│   │       ├── compact/            # Compact (dense) theme mapping functions
│   │       └── shared/             # Shared token derivation utilities
│   │
│   ├── config-provider/            # Global configuration provider (most critical component)
│   │   ├── index.tsx               # ConfigProvider component implementation
│   │   ├── context.ts              # ConfigConsumerProps interface, React context object
│   │   ├── SizeContext.tsx         # SizeType context ('small' | 'middle' | 'large')
│   │   ├── DisabledContext.tsx     # Global disabled state context
│   │   ├── defaultRenderEmpty.tsx  # Default empty state renderer
│   │   ├── MotionWrapper.tsx       # Animation motion wrapper
│   │   ├── hooks/                  # useSize, useConfig, useComponentConfig hooks
│   │   └── style/                  # ConfigProvider's own CSS-in-JS styles
│   │
│   ├── locale/                     # Internationalisation locale packs
│   │   ├── index.tsx               # LocaleProvider component + Locale interface
│   │   ├── context.ts              # LocaleContext
│   │   ├── useLocale.ts            # useLocale hook
│   │   ├── en_US.ts                # English (US) locale (default)
│   │   ├── zh_CN.ts                # Chinese Simplified locale
│   │   └── <xx_XX>.ts             # 80+ additional locale files
│   │
│   ├── style/                      # Global shared styles
│   │   ├── index.tsx               # genStyleUtils, genComponentStyleHook factory
│   │   ├── reset.css               # CSS reset / normalisation
│   │   ├── antd.css                # Pre-built static CSS (layer-based)
│   │   ├── compact-item.ts         # Compact mode item style helpers
│   │   ├── compact-item-vertical.ts
│   │   ├── motion/                 # Shared animation keyframe/transition helpers
│   │   ├── placementArrow.ts       # Popup arrow placement style helpers
│   │   └── roundedArrow.ts         # Rounded arrow shape CSS generator
│   │
│   ├── button/                     # Button component (representative example)
│   │   ├── Button.tsx              # Main implementation (BaseButtonProps, ButtonProps)
│   │   ├── ButtonGroup.tsx         # Button.Group sub-component
│   │   ├── buttonHelpers.tsx       # ButtonType, ButtonVariantType, ButtonColorType, helpers
│   │   ├── DefaultLoadingIcon.tsx  # Animated loading spinner
│   │   ├── IconWrapper.tsx         # Icon positioning wrapper
│   │   ├── index.tsx               # Public export
│   │   ├── style/                  # CSS-in-JS styles for button (uses genComponentStyleHook)
│   │   ├── demo/                   # 20+ interactive demos (.tsx + .md)
│   │   └── __tests__/             # Unit, snapshot, semantic, image tests
│   │
│   ├── form/                       # Form with validation (uses @rc-component/form)
│   │   ├── Form.tsx                # Main Form component
│   │   ├── FormItem.tsx            # Form.Item with label + validation display
│   │   ├── FormList.tsx            # Dynamic form list
│   │   ├── ErrorList.tsx           # Validation error list display
│   │   ├── context.tsx             # FormProvider
│   │   ├── hooks/                  # useForm, useWatch, useFormInstance
│   │   └── index.tsx               # Public export
│   │
│   ├── table/                      # Table with sorting, filtering, pagination
│   │   ├── Table.tsx               # Main Table wrapper
│   │   ├── InternalTable.tsx       # Core table logic
│   │   ├── Column.tsx              # Column definition type
│   │   ├── interface.ts            # ColumnType, ColumnsType, etc.
│   │   └── index.tsx               # Public export
│   │
│   ├── modal/                      # Modal dialog
│   ├── drawer/                     # Drawer / side panel
│   ├── select/                     # Select dropdown
│   ├── date-picker/                # Date/range picker (dayjs-based)
│   ├── input/                      # Input, Input.Search, Input.Password, OTP
│   ├── menu/                       # Navigation menu
│   ├── tree/                       # Tree data display
│   ├── upload/                     # File upload
│   ├── notification/               # Toast notification (imperative API)
│   ├── message/                    # Brief status message (imperative API)
│   ├── typography/                 # Typography.Text, Title, Paragraph, Link
│   ├── masonry/                    # Masonry layout (newer component)
│   ├── splitter/                   # Resizable pane splitter
│   ├── color-picker/               # HSV/RGB/Hex colour picker
│   ├── qr-code/                    # QR code renderer (SVG/Canvas)
│   ├── watermark/                  # Watermark overlay
│   ├── float-button/               # FAB-style floating button
│   └── ...                         # 60+ additional components
│
├── tests/                          # Shared test infrastructure
│   ├── setup.ts                    # Jest setup (mocks, globals)
│   ├── setupAfterEnv.ts            # jest-dom matchers, jest-axe setup
│   ├── utils.tsx                   # render() wrapper, act() helpers
│   └── changelog.test.ts           # Automated changelog lint test
│
├── scripts/                        # Build and release automation
│   ├── build-style.tsx             # Generates static CSS output per component
│   ├── generate-token-meta.ts      # Generates token metadata JSON for docs
│   ├── collect-token-statistic.ts  # Analyses token usage across components
│   ├── generate-version.ts         # Injects version string into source
│   ├── generate-component-changelog.ts  # Changelog lint/generation
│   ├── pre-publish.ts              # Pre-publish validation
│   ├── post-publish.ts             # Post-publish OSS/CDN sync
│   ├── check-cssinjs.tsx           # Validates CSS-in-JS token usage
│   └── check-repo.ts               # Repo consistency checks
│
├── docs/                           # Additional site documentation pages
│   └── resources.*.md              # Resource links (bilingual)
│
├── typings/                        # Global TypeScript declaration files
│   ├── index.d.ts                  # Module augmentations
│   ├── cssType.d.ts                # CSS type extensions
│   └── jest.d.ts                   # Jest type extensions
│
├── alias/
│   └── cssinjs.js                  # cssinjs alias for UMD build (bundles cssinjs inline)
│
├── public/
│   └── versions.json               # Version history manifest for docs site
│
├── package.json                    # NPM manifest (name: antd, version: 6.3.5)
├── tsconfig.json                   # TypeScript configuration (strict, esnext modules)
├── .fatherrc.ts                    # father library build config (UMD bundles)
├── .jest.js                        # Jest configuration (jsdom environment)
├── .jest.node.js                   # Jest config for Node.js-environment tests
├── .dumirc.ts                      # Dumi documentation site configuration
├── biome.json                      # Biome linter/formatter configuration
├── eslint.config.mjs               # ESLint flat config
├── .lintstagedrc.json              # Lint-staged hooks
├── webpack.config.js               # Webpack config for custom build scenarios
├── mako.config.json                # Mako bundler config (experimental)
├── CHANGELOG.en-US.md              # English changelog
├── CHANGELOG.zh-CN.md              # Chinese changelog
└── CLAUDE.md / AGENTS.md           # AI assistant development guidelines
```

## Module and Package Organisation

### Component Directory Convention

Every component in `components/<name>/` follows this contract:

| File/Dir | Purpose |
|---|---|
| `ComponentName.tsx` | Core React component implementation |
| `index.tsx` | Public-facing export (default export + named TypeScript types) |
| `style/index.ts` | CSS-in-JS style registration via `genComponentStyleHook` |
| `style/token.ts` | Component-specific token definitions (when needed) |
| `__tests__/*.test.tsx` | Unit tests, semantic snapshot tests, image regression tests |
| `demo/*.tsx` + `demo/*.md` | Interactive code examples for documentation site |
| `index.en-US.md` | English API documentation (rendered at ant.design) |
| `index.zh-CN.md` | Chinese API documentation |

### Semantic API Pattern

Components expose three tiers of customisation:
1. **`className` / `style`** — applied to the root element.
2. **`classNames` / `styles`** (semantic maps) — applied to named internal elements (e.g., `{ root, icon, content }` for Button).
3. **Design tokens** via `ConfigProvider theme.components.<ComponentName>` — override component-level design tokens globally.

### Key Code Organisation Patterns

- **CSS-in-JS via `useStyle()`** — each component calls its own `useStyle(prefixCls)` hook which registers styles in the cssinjs cache keyed by the hash token. Styles are injected once per token combination.
- **`useComponentConfig()`** — components read per-component ConfigProvider props (e.g., `buttonConfig`) from context, merging global defaults with local props.
- **`@rc-component/*` as primitive layer** — the unstyled logic (virtualised scroll, form validation, tree traversal, overlay positioning) lives in `@rc-component` packages. Ant Design adds styling, theming, and design language on top.
- **Compound components** — many components use a pattern like `Form.Item`, `Form.List`, `Table.Column`, exposing sub-components as properties of the main component export.
