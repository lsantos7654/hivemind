# Ant Design — Repository Summary

## Repository Purpose and Goals

Ant Design (`antd`) is an enterprise-class UI design language and React component library maintained by the Ant Group (Alibaba). The project's core mission is to provide a comprehensive, production-ready set of high-quality React components that implement the Ant Design specification — a systematic design language for enterprise-grade web applications. As of commit d0cbac08, the library is at version **6.3.5** and targets **React 18+** (with React 19 already supported).

The library is published to npm as the `antd` package and is one of the most widely downloaded React component libraries in the world, used across e-commerce, financial, government, and SaaS products primarily in the Chinese technology ecosystem, with strong international adoption as well.

## Key Features and Capabilities

- **84+ production-ready components** covering layout, navigation, data entry, data display, feedback, and general utility needs.
- **Design Token theming system** — a CSS-in-JS approach powered by `@ant-design/cssinjs` allowing full token-level customisation (seed tokens → map tokens → alias tokens). Includes built-in default, dark, and compact algorithms.
- **Dark mode** and **compact mode** out of the box via `theme.darkAlgorithm` and `theme.compactAlgorithm`.
- **RTL (right-to-left) layout support** via `ConfigProvider direction="rtl"`.
- **Server-Side Rendering (SSR)** supported through static style extraction utilities.
- **150+ locale packs** covering almost every language, managed via `LocaleProvider` / `ConfigProvider locale`.
- **Full TypeScript support** with strict typings, semantic class name / style APIs per component, and exported type helpers (`GetProp`, `GetProps`, `GetRef`).
- **CSS Variables mode** — opt-in CSS custom-property output alongside the hash-based class system.
- **Accessibility** — components include ARIA attributes, keyboard navigation, and axe-verified markup.
- **Tree-shakeable** — ES module output (`es/`) allows bundlers to eliminate unused components.

## Primary Use Cases and Target Audience

Ant Design targets **front-end engineers and design teams** building enterprise dashboards, admin systems, CRM/ERP products, and data-heavy web applications. It is especially popular in:

- Internal tools and back-office systems at large organisations.
- Financial and government digital portals.
- SaaS products requiring polished, accessible, localised UIs.
- Rapid prototyping where a consistent design language matters.

## High-Level Architecture Overview

```
antd (npm package)
├── components/          ← All 84+ component implementations (TypeScript/React)
│   ├── _util/           ← Shared utilities, hooks, warning system
│   ├── theme/           ← Design token system (seed → map → alias → component tokens)
│   ├── locale/          ← 80+ locale files
│   ├── style/           ← Global/reset CSS, shared style helpers
│   └── <component>/     ← Per-component directory (impl + style + tests + docs + demos)
├── scripts/             ← Build, token, publish, changelog automation scripts
├── tests/               ← Shared test setup and utilities
├── docs/                ← Site documentation (rendered with dumi)
└── dist/                ← UMD bundles (built output, not in source)
```

Each component follows a consistent internal layout:
1. `ComponentName.tsx` — main React implementation.
2. `index.tsx` — public export entry (re-exports component and TypeScript types).
3. `style/index.ts` — CSS-in-JS style registration using `@ant-design/cssinjs`.
4. `__tests__/` — Jest unit tests, semantic tests, snapshot/image tests.
5. `demo/` — interactive demo files used by the documentation site.
6. `index.en-US.md` / `index.zh-CN.md` — bilingual API documentation rendered on ant.design.

The CSS-in-JS styling pipeline: **Seed tokens** (raw design primitives) are transformed by a **mapping algorithm** (default/dark/compact) into **map tokens** (e.g. colour palettes), then into **alias tokens** (semantic names like `colorPrimary`), and finally into **component-level tokens** via per-component `genComponentStyleHook`. Components consume tokens via `useToken()` inside `useStyle()` hooks.

Global configuration is handled by `ConfigProvider`, which pushes configuration downward via React Context — covering theme, locale, RTL direction, component size, disabled state, prefix class, and per-component prop defaults.

## Related Projects and Dependencies

| Package | Role |
|---|---|
| `@ant-design/cssinjs` | CSS-in-JS engine (hash-based class generation, SSR extraction) |
| `@ant-design/cssinjs-utils` | Shared utilities for the CSS-in-JS pipeline |
| `@ant-design/icons` | Official icon library |
| `@ant-design/colors` | Colour palette generation utilities |
| `@ant-design/fast-color` | High-performance colour manipulation |
| `@rc-component/*` | Low-level headless primitive components (50+ packages) used as the unstyled base |
| `dayjs` | Date/time library used by date pickers |
| `clsx` | Conditional class name utility |
| `@ant-design/tools` | Build toolchain (antd-tools CLI, Jest preprocessors) |
| `father` | Library build tool (ESM/CJS/UMD compilation) |
| `dumi` | Documentation site framework |
| `@ant-design/x` | AI-native component extensions (dev dependency / demo) |
