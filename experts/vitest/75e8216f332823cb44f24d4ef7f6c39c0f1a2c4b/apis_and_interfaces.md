# Vitest APIs and Interfaces

## Public APIs and Entry Points

Vitest provides a comprehensive set of APIs designed for different use cases, from simple test writing to advanced framework integration:

### Primary Entry Points

**Main Package (`vitest`)**: The primary entry point provides all essential testing APIs through multiple specialized exports:

- `vitest` - Core testing framework with CLI functionality
- `vitest/config` - Configuration utilities and type definitions  
- `vitest/node` - Node.js-specific APIs for programmatic usage
- `vitest/browser` - Browser testing context and utilities
- `vitest/runners` - Custom test runner implementations
- `vitest/reporters` - Test result reporting interfaces

**Global Test APIs**: The framework automatically injects testing functions into the global scope or provides them via imports:

```typescript
import { describe, test, it, expect, vi } from 'vitest'
// or use globally without imports when globals: true
```

### Configuration API

**defineConfig Function**: Primary configuration interface that provides type safety and IntelliSense:

```typescript
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    coverage: {
      reporter: ['text', 'html']
    }
  }
})
```

**defineProject Function**: For workspace and multi-project configurations:

```typescript
import { defineProject } from 'vitest/config'

export default defineProject({
  test: {
    name: 'unit-tests',
    include: ['src/**/*.test.ts']
  }
})
```

## Key Classes, Functions, and Macros

### Test Definition APIs

**Core Test Functions**: Vitest provides Jest-compatible test definition functions with enhanced TypeScript support:

```typescript
// Test suites
describe('Calculator', () => {
  // Individual tests
  test('should add numbers correctly', () => {
    expect(1 + 1).toBe(2)
  })
  
  // Alternative syntax
  it('should subtract numbers', () => {
    expect(5 - 3).toBe(2)
  })
})

// Standalone tests
test('standalone test', () => {
  expect(true).toBeTruthy()
})
```

**Test Lifecycle Hooks**: Setup and teardown functions for managing test state:

```typescript
import { beforeAll, beforeEach, afterAll, afterEach } from 'vitest'

beforeAll(() => {
  // Run once before all tests
  return setupDatabase()
})

beforeEach(() => {
  // Run before each test
  resetTestData()
})

afterEach(() => {
  // Run after each test
  cleanupTestData()
})

afterAll(() => {
  // Run once after all tests
  teardownDatabase()
})
```

### Assertion Library

**Expect Interface**: Comprehensive assertion API with Jest-compatible matchers:

```typescript
import { expect } from 'vitest'

// Basic matchers
expect(value).toBe(2)
expect(value).toEqual({foo: 'bar'})
expect(value).toBeTruthy()
expect(value).toBeNull()

// Array and object matchers
expect(array).toContain(item)
expect(array).toHaveLength(3)
expect(object).toHaveProperty('key', 'value')

// String matchers
expect(string).toMatch(/pattern/)
expect(string).toContain('substring')

// Function matchers
expect(fn).toThrow()
expect(fn).toHaveBeenCalled()
expect(fn).toHaveBeenCalledWith(arg1, arg2)
```

**Snapshot Testing**: Built-in snapshot functionality:

```typescript
expect(component).toMatchSnapshot()
expect(data).toMatchInlineSnapshot(`"expected value"`)
```

**Async Testing**: Promise and async/await support:

```typescript
await expect(promise).resolves.toBe(value)
await expect(promise).rejects.toThrow()

test('async test', async () => {
  const result = await asyncFunction()
  expect(result).toBe(expected)
})
```

### Mocking and Spying APIs

**Vi Utilities**: Comprehensive mocking capabilities through the `vi` object:

```typescript
import { vi } from 'vitest'

// Function mocking
const mockFn = vi.fn()
const mockFnWithReturn = vi.fn(() => 'mocked')

// Module mocking
vi.mock('./module', () => ({
  default: vi.fn(),
  namedExport: vi.fn()
}))

// Timers
vi.useFakeTimers()
vi.advanceTimersByTime(1000)
vi.runAllTimers()

// System mocking
vi.setSystemTime(new Date('2023-01-01'))
```

**Spy Functions**: Function behavior monitoring:

```typescript
const spy = vi.spyOn(object, 'method')
expect(spy).toHaveBeenCalled()
spy.mockRestore()
```

## Usage Examples with Code Snippets

### Basic Test Setup

**Simple Unit Test**:

```typescript
// math.test.ts
import { describe, test, expect } from 'vitest'
import { add, multiply } from './math.js'

describe('Math utilities', () => {
  test('add function', () => {
    expect(add(2, 3)).toBe(5)
    expect(add(-1, 1)).toBe(0)
  })
  
  test('multiply function', () => {
    expect(multiply(3, 4)).toBe(12)
    expect(multiply(0, 5)).toBe(0)
  })
})
```

### Component Testing

**React Component Test**:

```typescript
// Button.test.tsx
import { render, screen } from '@testing-library/react'
import { test, expect } from 'vitest'
import Button from './Button'

test('renders button with text', () => {
  render(<Button>Click me</Button>)
  expect(screen.getByRole('button')).toHaveTextContent('Click me')
})
```

### API Testing with Mocks

**HTTP API Test**:

```typescript
// api.test.ts
import { test, expect, vi } from 'vitest'
import { fetchUser } from './api'

// Mock the fetch function
global.fetch = vi.fn()

test('fetchUser returns user data', async () => {
  const mockUser = { id: 1, name: 'John Doe' }
  
  // Setup mock response
  vi.mocked(fetch).mockResolvedValueOnce({
    ok: true,
    json: async () => mockUser,
  } as Response)
  
  const user = await fetchUser(1)
  
  expect(fetch).toHaveBeenCalledWith('/api/users/1')
  expect(user).toEqual(mockUser)
})
```

### Browser Testing

**Browser Environment Test**:

```typescript
// @vitest-environment jsdom
import { test, expect } from 'vitest'

test('DOM manipulation', () => {
  document.body.innerHTML = '<div id="app"></div>'
  const app = document.getElementById('app')
  
  expect(app).toBeDefined()
  expect(app?.tagName).toBe('DIV')
})
```

## Integration Patterns and Workflows

### Configuration Patterns

**Multi-Environment Setup**:

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    environment: 'node', // default
    globals: true,
    setupFiles: ['./test/setup.ts']
  },
  
  // Environment-specific configs
  environments: {
    jsdom: {
      test: {
        environment: 'jsdom',
        include: ['src/**/*.dom.test.ts']
      }
    },
    
    node: {
      test: {
        environment: 'node',
        include: ['src/**/*.node.test.ts']
      }
    }
  }
})
```

**Workspace Configuration**:

```typescript
// vitest.workspace.ts
import { defineWorkspace } from 'vitest/config'

export default defineWorkspace([
  // Unit tests
  {
    extends: './vitest.config.ts',
    test: {
      name: 'unit',
      include: ['src/**/*.test.ts']
    }
  },
  
  // Integration tests  
  {
    extends: './vitest.config.ts',
    test: {
      name: 'integration',
      include: ['tests/integration/**/*.test.ts']
    }
  },
  
  // Browser tests
  {
    extends: './vitest.config.ts',
    test: {
      name: 'browser',
      browser: {
        enabled: true,
        name: 'chrome'
      },
      include: ['tests/browser/**/*.test.ts']
    }
  }
])
```

### Custom Reporters

**Custom Reporter Implementation**:

```typescript
// custom-reporter.ts
import type { Reporter } from 'vitest/reporters'

export class CustomReporter implements Reporter {
  onTestResult(test: TestResult) {
    console.log(`Test ${test.name}: ${test.result}`)
  }
  
  onFinished(files: File[], errors: unknown[]) {
    console.log(`Tests completed: ${files.length} files`)
  }
}

// vitest.config.ts
export default defineConfig({
  test: {
    reporters: ['default', new CustomReporter()]
  }
})
```

### Programmatic Usage

**Running Tests Programmatically**:

```typescript
// test-runner.ts
import { startVitest } from 'vitest/node'

const vitest = await startVitest('test', [], {
  watch: false,
  run: true,
  reporter: ['json'],
  outputFile: './test-results.json'
})

if (!vitest) {
  process.exit(1)
}

await vitest.close()
```

## Configuration Options and Extension Points

### Core Configuration Options

**Test Execution Control**:

- `include/exclude` - File patterns for test discovery
- `globals` - Enable global test functions without imports
- `environment` - Test environment ('node', 'jsdom', 'happy-dom')
- `threads` - Enable/disable multi-threading
- `maxThreads` - Maximum number of worker threads
- `testTimeout` - Default timeout for tests
- `hookTimeout` - Timeout for lifecycle hooks

**Coverage Configuration**:

```typescript
coverage: {
  provider: 'v8', // or 'istanbul'
  reporter: ['text', 'html', 'lcov'],
  threshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80
    }
  }
}
```

**Browser Testing Options**:

```typescript
browser: {
  enabled: true,
  name: 'chrome', // or 'firefox', 'safari', 'edge'
  provider: 'playwright', // or 'webdriverio'
  headless: true,
  viewport: { width: 1280, height: 720 }
}
```

### Extension Points

**Plugin System**: Vitest supports Vite plugins and custom Vitest plugins:

```typescript
// Custom plugin
function customVitestPlugin(): Plugin {
  return {
    name: 'custom-vitest-plugin',
    configureServer(server) {
      // Custom server configuration
    }
  }
}

// Configuration
export default defineConfig({
  plugins: [customVitestPlugin()],
  test: {
    // test configuration
  }
})
```

**Custom Test Environments**: Create custom environments for specialized testing:

```typescript
// custom-environment.ts
export default {
  name: 'custom',
  setup(global) {
    // Setup custom global environment
    global.customAPI = new CustomAPI()
    
    return {
      teardown() {
        // Cleanup
        global.customAPI.cleanup()
      }
    }
  }
}
```

This comprehensive API surface provides developers with the tools needed for testing applications of any complexity, from simple unit tests to complex integration testing scenarios with browser automation and custom environments.