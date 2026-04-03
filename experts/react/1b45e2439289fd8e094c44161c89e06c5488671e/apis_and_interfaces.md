# React APIs and Interfaces

## Public API Entry Points

### `react` Package

The main `react` package exports the core programming model. Import from `'react'`:

```js
import React, {
  // Component primitives
  Component, PureComponent, StrictMode, Suspense, Profiler, Fragment,
  // Element creation
  createElement, cloneElement, isValidElement, createRef,
  // Composition helpers
  createContext, forwardRef, lazy, memo, cache,
  // Hooks
  useState, useReducer, useContext, useRef, useCallback, useMemo,
  useEffect, useLayoutEffect, useInsertionEffect,
  useDebugValue, useId, useSyncExternalStore,
  useTransition, useDeferredValue, useOptimistic, useActionState,
  useEffectEvent,
  // Utilities
  startTransition, version,
  // Children utilities
  Children,
} from 'react';
```

Source: `packages/react/src/ReactClient.js`

### `react-dom` Package

```js
import { createPortal, flushSync } from 'react-dom';

// Resource hints (web performance)
import {
  prefetchDNS, preconnect, preload, preloadModule, preinit, preinitModule
} from 'react-dom';

// Form utilities
import { useFormStatus, requestFormReset } from 'react-dom';
```

Source: `packages/react-dom/src/shared/ReactDOM.js`

### `react-dom/client`

```js
import { createRoot, hydrateRoot } from 'react-dom/client';
```

Source: `packages/react-dom/src/client/ReactDOMClient.js`

### `react-dom/server` (Node.js)

```js
import {
  renderToPipeableStream,    // Streaming SSR for Node.js
  renderToStaticMarkup,      // Static HTML (no React runtime)
  renderToString,            // Legacy synchronous SSR
} from 'react-dom/server';   // or 'react-dom/server.node'
```

### `react-dom/server` (Browser/Edge)

```js
import {
  renderToReadableStream,    // Web Streams API (Cloudflare, Deno, etc.)
} from 'react-dom/server.browser'; // or server.edge, server.bun
```

---

## Key APIs and Usage Examples

### `createRoot` / `hydrateRoot`

```js
import { createRoot } from 'react-dom/client';

// Mount a React tree
const root = createRoot(document.getElementById('root'));
root.render(<App />);

// Unmount
root.unmount();

// Hydration (SSR -> Client)
import { hydrateRoot } from 'react-dom/client';
const root = hydrateRoot(document.getElementById('root'), <App />, {
  onRecoverableError(error) { console.error(error); }
});
```

Source: `packages/react-dom/src/client/ReactDOMRoot.js`

### Hooks

#### `useState`

```js
const [state, setState] = useState(initialValue);
// Or with initializer function (lazy initialization):
const [state, setState] = useState(() => computeExpensiveValue());
```

#### `useReducer`

```js
const [state, dispatch] = useReducer(reducer, initialState);
// With initializer:
const [state, dispatch] = useReducer(reducer, initialArg, init);
```

#### `useEffect` / `useLayoutEffect` / `useInsertionEffect`

```js
useEffect(() => {
  // Runs after paint (async)
  const sub = subscribe(id);
  return () => sub.unsubscribe(); // cleanup
}, [id]);

useLayoutEffect(() => {
  // Runs synchronously after DOM mutations, before paint
}, []);

useInsertionEffect(() => {
  // Runs before any DOM mutations (CSS-in-JS use case)
}, []);
```

#### `useContext`

```js
const ThemeContext = createContext('light');

function Button() {
  const theme = useContext(ThemeContext);
  return <button className={theme}>...</button>;
}
```

#### `useRef`

```js
const ref = useRef(null);
// DOM ref:
<input ref={ref} />
// ref.current === DOM node after mount

// Mutable instance variable:
const timerRef = useRef(null);
```

#### `useTransition`

```js
const [isPending, startTransition] = useTransition();

function handleClick() {
  startTransition(() => {
    // Non-urgent update — can be interrupted
    setFilter(newFilter);
  });
}
```

#### `useDeferredValue`

```js
const deferredQuery = useDeferredValue(query);
// deferredQuery lags behind query during concurrent rendering
// Use to defer expensive renders without blocking input
```

#### `useOptimistic`

```js
const [optimisticState, addOptimistic] = useOptimistic(
  actualState,
  (currentState, optimisticValue) => ({...currentState, ...optimisticValue})
);
```

#### `useActionState`

```js
const [state, formAction, isPending] = useActionState(
  async (prevState, formData) => {
    const result = await submitForm(formData);
    return result;
  },
  initialState
);
```

#### `useId`

```js
const id = useId();
// Stable, SSR-consistent unique ID
return <label htmlFor={id}>Name: <input id={id} /></label>;
```

#### `useSyncExternalStore`

```js
const snapshot = useSyncExternalStore(
  store.subscribe,   // (callback) => unsubscribe
  store.getSnapshot, // () => snapshot (client)
  store.getServerSnapshot // () => snapshot (SSR, optional)
);
```

#### `useDebugValue`

```js
function useFriendStatus(friendID) {
  const isOnline = useIsOnline(friendID);
  useDebugValue(isOnline ? 'Online' : 'Offline');
  return isOnline;
}
```

Source: `packages/react-reconciler/src/ReactFiberHooks.js`

---

### Suspense

```jsx
<Suspense fallback={<Spinner />}>
  <LazyComponent />
</Suspense>
```

For data fetching, Suspense works with frameworks that integrate with React's cache/promise mechanism:

```js
const LazyComponent = lazy(() => import('./HeavyComponent'));
```

Source: `packages/react-reconciler/src/ReactFiberSuspenseComponent.js`

### Context API

```js
// Create context with default value
const ThemeContext = createContext({ theme: 'light' });

// Provide context
function App() {
  return (
    <ThemeContext.Provider value={{ theme: 'dark' }}>
      <ChildTree />
    </ThemeContext.Provider>
  );
}

// Consume context
function Child() {
  const ctx = useContext(ThemeContext);
  return <div>{ctx.theme}</div>;
}
```

Source: `packages/react/src/ReactContext.js`, `packages/react-reconciler/src/ReactFiberNewContext.js`

### `forwardRef`

```js
const FancyInput = forwardRef((props, ref) => (
  <input ref={ref} {...props} />
));

// Usage
const inputRef = useRef();
<FancyInput ref={inputRef} />
```

Source: `packages/react/src/ReactForwardRef.js`

### `memo`

```js
const MemoizedComponent = memo(function MyComponent({ value }) {
  return <div>{value}</div>;
});

// Custom comparison
const MemoizedComponent = memo(MyComponent, (prevProps, nextProps) => {
  return prevProps.id === nextProps.id;
});
```

Source: `packages/react/src/ReactMemo.js`

### `createPortal`

```js
import { createPortal } from 'react-dom';

function Modal({ children }) {
  return createPortal(
    <div className="modal">{children}</div>,
    document.getElementById('modal-root')
  );
}
```

Source: `packages/react-dom/src/shared/ReactDOM.js`

---

## Server-Side Rendering APIs

### Streaming SSR (Node.js)

```js
import { renderToPipeableStream } from 'react-dom/server';

const { pipe, abort } = renderToPipeableStream(<App />, {
  bootstrapScripts: ['/main.js'],
  onShellReady() {
    res.setHeader('content-type', 'text/html');
    pipe(res);
  },
  onShellError(error) {
    res.statusCode = 500;
    res.send('<h1>Server Error</h1>');
  },
  onAllReady() {
    // All content rendered, including Suspense boundaries
  },
  onError(error) {
    console.error(error);
  }
});

// Abort after timeout
setTimeout(abort, 10000);
```

Source: `packages/react-dom/src/server/ReactDOMFizzServerNode.js`

### Streaming SSR (Edge/Browser)

```js
import { renderToReadableStream } from 'react-dom/server.browser';

const stream = await renderToReadableStream(<App />, {
  bootstrapScripts: ['/main.js'],
  onError(error) { console.error(error); }
});

return new Response(stream, {
  headers: { 'content-type': 'text/html' }
});
```

Source: `packages/react-dom/src/server/ReactDOMFizzServerBrowser.js`

---

## React Reconciler (Custom Renderer API)

For building custom renderers, use `react-reconciler`:

```js
import ReactReconciler from 'react-reconciler';

const hostConfig = {
  // Required: Create a DOM/host instance
  createInstance(type, props, rootContainer, hostContext, internalHandle) { ... },
  createTextInstance(text, rootContainer, hostContext, internalHandle) { ... },
  appendChildToContainer(container, child) { ... },
  appendChild(parentInstance, child) { ... },
  insertBefore(parentInstance, child, beforeChild) { ... },
  removeChild(parentInstance, child) { ... },
  removeChildFromContainer(container, child) { ... },
  prepareUpdate(instance, type, oldProps, newProps, rootContainer, hostContext) { ... },
  commitUpdate(instance, updatePayload, type, prevProps, nextProps, internalHandle) { ... },
  // ... many more methods

  // Configuration constants
  supportsMutation: true,
  supportsPersistence: false,
  supportsHydration: false,
  isPrimaryRenderer: true,
  noTimeout: -1,
};

const Renderer = ReactReconciler(hostConfig);

const container = Renderer.createContainer(hostRoot, ConcurrentMode, null, false, null, '', {}, null);
Renderer.updateContainer(<App />, container, null, null);
```

Source: `packages/react-reconciler/README.md`, `packages/react-reconciler/src/ReactFiberReconciler.js`

---

## Resource Preloading APIs

```js
import { prefetchDNS, preconnect, preload, preloadModule, preinit, preinitModule } from 'react-dom';

// DNS prefetch
prefetchDNS('https://api.example.com');

// Preconnect (DNS + TCP + TLS)
preconnect('https://api.example.com');

// Preload a resource
preload('/hero.jpg', { as: 'image' });
preload('/font.woff2', { as: 'font', crossOrigin: 'anonymous' });

// Preload an ES module
preloadModule('/module.js', { as: 'script' });

// Preinit (preload + execute)
preinit('/analytics.js', { as: 'script' });
preinitModule('/chunk.js', { as: 'script' });
```

Source: `packages/react-dom/src/shared/ReactDOMFloat.js`

---

## Feature Flags and Configuration

Feature flags are defined in `packages/shared/ReactFeatureFlags.js`. They control experimental features and optimizations. Key flags:

```js
// Experimental features
enableViewTransition       // View Transitions API support
enableGestureTransition    // Gesture-based transitions
enableFragmentRefs         // Refs on Fragment nodes
enableTaint               // Server taint mechanism
enableAsyncIterableChildren // Async iterable as children

// Optimizations
enableNoCloningMemoCache   // Memo cache without cloning
enableYieldingBeforePassive // Yield scheduler optimization

// Development
enableInfiniteRenderLoopDetection // Detect infinite render loops

// Legacy/Experimental
enableLegacyCache          // React.cache (legacy)
enableScopeAPI             // Experimental Scope API
```

Platform-specific flag values live in `packages/shared/forks/ReactFeatureFlags.*.js`.

---

## Integration Patterns

### React Server Components (RSC)

For frameworks integrating RSC, use `react-server-dom-webpack` (or turbopack/parcel variant):

```js
// Server: serialize component tree to Flight wire format
import { renderToPipeableStream } from 'react-server-dom-webpack/server.node';

const { pipe } = renderToPipeableStream(reactTree, moduleMap);
pipe(response);

// Client: deserialize Flight format
import { createFromFetch } from 'react-server-dom-webpack/client';

const serverComponentPromise = createFromFetch(fetch('/rsc-endpoint'));
// Wrap in Suspense:
<Suspense fallback={<Loading />}>
  <ServerComponent data={serverComponentPromise} />
</Suspense>
```

### Testing with `act()`

```js
import { act } from 'react';

// Wrap state updates and effects in act() for testing
await act(async () => {
  root.render(<Component />);
});

// Check resulting DOM
expect(container.textContent).toBe('expected');
```

Source: `packages/react/src/ReactAct.js`

### `Profiler` API

```js
function onRenderCallback(
  id,           // "id" prop of the Profiler
  phase,        // "mount" | "update" | "nested-update"
  actualDuration, // ms rendering the committed update
  baseDuration,   // ms to render the entire subtree without memoization
  startTime,
  commitTime
) { ... }

<Profiler id="Navigation" onRender={onRenderCallback}>
  <Navigation />
</Profiler>
```

Source: `packages/react-reconciler/src/ReactFiberBeginWork.js`
