# React Repository Code Structure

## Annotated Directory Tree

```
react/
├── packages/                     # 38 npm packages (monorepo core)
│   ├── react/                    # Main React library (v19.3.0)
│   ├── react-dom/                # Web DOM renderer
│   ├── react-reconciler/         # Platform-agnostic fiber reconciler
│   ├── scheduler/                # Cooperative task scheduler
│   ├── react-server/             # Server-side primitives
│   ├── react-client/             # Client-side RSC utilities
│   ├── react-art/                # ART vector graphics renderer
│   ├── react-native-renderer/    # React Native renderer
│   ├── react-noop-renderer/      # No-op renderer for testing
│   ├── react-test-renderer/      # Unit test renderer
│   ├── react-server-dom-webpack/ # RSC + Webpack (Flight protocol)
│   ├── react-server-dom-turbopack/ # RSC + Turbopack
│   ├── react-server-dom-parcel/  # RSC + Parcel
│   ├── react-server-dom-unbundled/ # RSC without bundler
│   ├── react-server-dom-esm/     # RSC with native ESM
│   ├── react-server-dom-fb/      # RSC internal Facebook
│   ├── react-devtools/           # DevTools browser integration
│   ├── react-devtools-core/      # DevTools core logic
│   ├── react-devtools-extensions/ # Chrome/Firefox extensions
│   ├── react-devtools-inline/    # Inline DevTools embedding
│   ├── react-devtools-shared/    # Shared DevTools utilities
│   ├── react-devtools-shell/     # DevTools shell app
│   ├── react-devtools-timeline/  # Profiling timeline
│   ├── react-debug-tools/        # Debug hooks and utilities
│   ├── react-is/                 # Runtime type checking (v19.3.0)
│   ├── react-refresh/            # Fast Refresh (v0.19.0)
│   ├── react-cache/              # Experimental caching primitives
│   ├── react-markup/             # Experimental markup (experimental channel)
│   ├── use-subscription/         # External store subscription (v1.13.0)
│   ├── use-sync-external-store/  # External store sync hook (v1.7.0)
│   ├── react-suspense-test-utils/ # Suspense testing helpers
│   ├── shared/                   # Internal shared types/utilities (not published)
│   ├── eslint-plugin-react-hooks/ # Hooks linting rules (v7.1.0)
│   ├── jest-react/               # Jest configuration helpers (v0.18.0)
│   ├── internal-test-utils/      # Internal testing utilities (not published)
│   └── dom-event-testing-library/ # DOM event test helpers
│
├── scripts/                      # Build, test, CI scripts
│   ├── rollup/                   # Rollup build system
│   ├── jest/                     # Jest configuration & utilities
│   ├── flags/                    # Feature flag management
│   ├── error-codes/              # Error message extraction
│   ├── tasks/                    # Build task utilities
│   └── release/                  # Release automation
│
├── compiler/                     # React Compiler (separate codebase)
│   ├── packages/                 # Compiler packages
│   └── docs/                     # Compiler design docs
│
├── fixtures/                     # Manual test fixtures
│   ├── dom/                      # DOM behavior tests
│   ├── ssr/                      # SSR behavior tests
│   └── ...                       # Various manual testing scenarios
│
├── flow-typed/                   # Flow type definitions
├── .github/                      # GitHub Actions workflows
├── .codesandbox/                 # CodeSandbox integration
├── ReactVersions.js              # Single source of truth for versions
├── babel.config.js               # Root Babel config
├── babel.config-ts.js            # TypeScript Babel config
├── babel.config-react-compiler.js # Compiler Babel config
├── .eslintrc.js                  # ESLint config (21KB)
├── dangerfile.js                 # Danger.js CI validation
└── yarn.lock                     # Dependency lock file
```

## Package Deep Dive

### `packages/react/` — Core React API

```
packages/react/
├── index.js                      # Main export (client conditions)
├── package.json                  # Exports map with conditions
├── src/
│   ├── ReactClient.js            # Client React exports
│   ├── ReactServer.js            # Server React exports (react-server condition)
│   ├── ReactBaseClasses.js       # Component, PureComponent
│   ├── ReactChildren.js          # React.Children utilities (14KB)
│   ├── ReactContext.js           # createContext
│   ├── ReactCreateRef.js         # createRef
│   ├── ReactForwardRef.js        # forwardRef
│   ├── ReactHooks.js             # All hooks (useState, useEffect, etc.)
│   ├── ReactLazy.js              # lazy()
│   ├── ReactMemo.js              # memo()
│   ├── ReactAct.js               # act() testing utility (14KB)
│   ├── ReactStartTransition.js   # startTransition
│   ├── ReactTaint.js             # Server taint utilities
│   ├── jsx/
│   │   ├── ReactJSX.js           # JSX runtime entry
│   │   └── ReactJSXElement.js    # JSX element creation/validation (29KB)
│   └── __tests__/                # 25 test files
```

### `packages/react-dom/` — DOM Renderer

```
packages/react-dom/
├── index.js                      # Main export
├── client.js                     # createRoot, hydrateRoot
├── server.js / server.node.js / server.browser.js / server.edge.js / server.bun.js
├── src/
│   ├── client/
│   │   ├── ReactDOMClient.js     # createRoot API
│   │   └── ReactDOMRoot.js       # Root implementation
│   ├── server/
│   │   ├── ReactDOMFizzServer.js         # Shared Fizz server logic
│   │   ├── ReactDOMFizzServerNode.js     # Node.js streaming (pipeableStream)
│   │   ├── ReactDOMFizzServerBrowser.js  # Browser/Edge streaming (readableStream)
│   │   └── ReactDOMLegacyServer.js       # renderToString (legacy)
│   ├── shared/
│   │   ├── ReactDOM.js           # createPortal, flushSync, resource preloading
│   │   ├── ReactDOMFloat.js      # prefetchDNS, preconnect, preload, preinit
│   │   └── ReactDOMFormActions.js # useFormState, useFormStatus, requestFormReset
│   └── events/                   # Synthetic event system
│       └── __tests__/            # 131 test files
```

### `packages/react-reconciler/` — Fiber Reconciler

```
packages/react-reconciler/
├── index.js
├── src/
│   ├── ReactFiber.js             # Fiber node creation and cloning
│   ├── ReactFiberBeginWork.js    # Render phase: process unit of work (4,448 lines)
│   ├── ReactFiberCommitWork.js   # Commit phase: DOM mutations (5,349 lines)
│   ├── ReactFiberCompleteWork.js # Completion phase (77KB)
│   ├── ReactChildFiber.js        # Child reconciliation, key diffing (74KB)
│   ├── ReactFiberHooks.js        # Hook dispatcher (all hook implementations)
│   ├── ReactFiberClassComponent.js # Class component lifecycles
│   ├── ReactFiberClassUpdateQueue.js # setState update queue
│   ├── ReactFiberWorkLoop.js     # Main work loop and scheduling
│   ├── ReactFiberLane.js         # Concurrent rendering lane model
│   ├── ReactFiberConfig.js       # Host config interface (platform abstraction)
│   ├── ReactFiberSuspenseComponent.js # Suspense boundary logic
│   ├── ReactFiberAsyncAction.js  # Async action (server actions, transitions)
│   ├── ReactFiberCommitEffects.js # Effect cleanup/setup (32KB)
│   ├── ReactFiberCommitViewTransitions.js # View transition support (35KB)
│   ├── ReactFiberContext.js      # Legacy context API
│   ├── ReactFiberNewContext.js   # Modern context API
│   ├── ReactFiberDevToolsHook.js # DevTools fiber hooks
│   ├── ReactFiberErrorDialog.js  # Error boundary dialog
│   └── ReactFiberReconciler.js   # Public reconciler API
└── README.md                     # Host config API reference (354 lines)
```

### `packages/scheduler/` — Task Scheduler

```
packages/scheduler/
├── index.js
├── src/
│   ├── Scheduler.js              # Main scheduling algorithm
│   ├── SchedulerFeatureFlags.js  # Feature flags
│   ├── SchedulerMinHeap.js       # Priority queue (min-heap)
│   ├── SchedulerPriorities.js    # Priority constants
│   └── forks/
│       ├── Scheduler.www.js      # Facebook www variant
│       └── Scheduler.native-fb.js # React Native Facebook variant
```

### `packages/shared/` — Internal Shared Utilities

```
packages/shared/
├── ReactFeatureFlags.js          # All feature flag definitions (265 lines)
├── ReactTypes.js                 # Shared TypeScript/Flow types
├── ReactSymbols.js               # Well-known React symbols
├── ReactErrorUtils.js            # Error handling utilities
├── ReactComponentStackFrame.js   # Component stack traces
├── ReactElement.js               # ReactElement type utilities
└── forks/
    ├── ReactFeatureFlags.www.js         # Facebook www flags
    ├── ReactFeatureFlags.www-dynamic.js # Dynamic www flags
    ├── ReactFeatureFlags.native-fb.js   # React Native Facebook
    ├── ReactFeatureFlags.native-oss.js  # React Native OSS
    └── ReactFeatureFlags.test-renderer.js # Test renderer flags
```

## Module and Package Organization Patterns

### Export Conditions Pattern

React packages use Node.js package `exports` with conditions to serve different code based on environment:

```json
{
  "exports": {
    ".": {
      "react-server": "./react.react-server.js",
      "default": "./index.js"
    }
  }
}
```

Conditions used: `react-server`, `react-client`, `node`, `browser`, `development`, `production`.

### Fork Pattern

The build system resolves platform-specific implementations through a `forks/` directory system. Files like `ReactFeatureFlags.js` have platform overrides in `forks/ReactFeatureFlags.www.js`. The Rollup plugin `use-forks-plugin.js` substitutes these at build time.

### Host Config Pattern

`react-reconciler` is fully platform-agnostic. Each renderer provides a host configuration module that implements methods like `createInstance`, `appendChildToContainer`, `commitUpdate`, etc. This is resolved via `ReactFiberConfig.js` which acts as an interface definition.

## Key Files and Their Roles

| File | Role |
|------|------|
| `ReactVersions.js` | Single source of truth for all package versions |
| `packages/shared/ReactFeatureFlags.js` | All feature flag definitions and default values |
| `packages/shared/ReactSymbols.js` | Well-known symbols (REACT_ELEMENT_TYPE, etc.) |
| `packages/react-reconciler/src/ReactFiberWorkLoop.js` | Main concurrent work loop |
| `packages/react-reconciler/src/ReactFiberLane.js` | Lane-based concurrent priority model |
| `packages/react-reconciler/src/ReactFiberHooks.js` | All hook implementations |
| `scripts/rollup/bundles.js` | All bundle definitions (39KB) |
| `scripts/rollup/build.js` | Rollup build orchestrator (27KB) |
| `scripts/jest/jest-cli.js` | Custom Jest CLI with channel support |
