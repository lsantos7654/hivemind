# Pydoll: Summary

## Repository Purpose and Goals

Pydoll (`pydoll-python` on PyPI, v2.22.1) is an async-native Python library for automating Chromium-based browsers (Google Chrome and Microsoft Edge) using the Chrome DevTools Protocol (CDP) directly over WebSocket. Unlike Selenium or Playwright, **Pydoll requires no WebDriver binary** — it communicates with the browser's built-in debugging interface, which means there is no `navigator.webdriver` flag set and no driver compatibility issues.

The library's primary goals are:

1. **Stealth automation**: Bypass bot-detection systems through humanized interactions, direct CDP access, and fingerprint control.
2. **Structured data extraction**: Provide a Pydantic-powered declarative extraction engine that maps the DOM directly to typed Python objects.
3. **Full async support**: Built on `asyncio` from the ground up with 100% type annotation coverage (`mypy`-verified).
4. **Low-level CDP access**: Expose the full Chrome DevTools Protocol for fine-grained control over network, DOM, runtime, and browser behavior.

## Key Features and Capabilities

- **WebDriver-free automation**: Direct CDP WebSocket communication, no Selenium/ChromeDriver.
- **Pydantic extraction engine**: Define `ExtractionModel` subclasses, call `tab.extract()` or `tab.extract_all()`, receive fully typed and validated Python objects.
- **Humanized mouse movement**: Bezier curves, Fitts's Law timing, minimum-jerk velocity, physiological tremor, and overshoot correction.
- **Shadow DOM support**: Full access to both open and closed shadow roots (CDP operates below JavaScript's visibility restrictions).
- **Shadow root discovery**: `tab.find_shadow_roots(deep=True)` traverses cross-origin iframes (OOPIFs).
- **Network interception**: Pause, inspect, modify, continue, fail, or fulfill HTTP requests via the Fetch domain.
- **Network monitoring**: Capture all request/response traffic and filter by URL pattern.
- **HAR recording**: Record browser sessions to HTTP Archive (HAR 1.2) format; replay recorded flows.
- **Hybrid automation**: Log in via the browser UI (handling CAPTCHAs, JS challenges), then use `tab.request` for fast authenticated API calls that inherit the full browser session.
- **Browser contexts**: Isolated sessions (like incognito) with per-context proxy and cookie management.
- **Multi-tab concurrency**: Full `asyncio.gather`-based concurrent tab management.
- **Remote connections**: Connect to browsers running in Docker, cloud, or behind a WebSocket proxy (preserves query-string tokens for authenticated proxies like Browserless).
- **Cloudflare Turnstile bypass**: Automatic detection and clicking via shadow root inspection.
- **Page bundles**: Save pages + all assets as `.zip` for offline viewing; supports inlining as data URIs.
- **Screenshots and PDFs**: Full-page screenshots (JPEG/PNG/WebP), PDF generation with print options.
- **File upload automation**: Intercept file chooser dialogs programmatically.
- **Retry decorator**: `@retry` with exponential backoff, custom recovery callbacks, and configurable exception matching.
- **Browser fingerprint control**: Granular Chrome `Preferences` JSON management via `ChromiumOptions.browser_preferences`.

## Primary Use Cases and Target Audience

**Target audience**: Python developers building web scrapers, test automation pipelines, RPA systems, and browser-based data extraction tools — particularly those needing to evade bot-detection systems.

**Use cases**:
- Anti-bot web scraping (e.g., sites protected by Cloudflare Turnstile, JS challenges)
- Automated end-to-end testing without WebDriver overhead
- API discovery via network monitoring
- Structured data extraction with full type safety
- Hybrid automation: UI for login/CAPTCHA, then direct API calls using browser session
- Browser fingerprinting and session management for multi-account automation

## High-Level Architecture Overview

```
pydoll/
├── browser/               # Browser process management and Tab control
│   ├── chromium/          # Chrome and Edge concrete implementations
│   ├── managers/          # Process, options, proxy, temp-dir management
│   ├── requests/          # HTTP request abstraction (fetch API + HAR)
│   ├── tab.py             # Tab class (primary user-facing interface)
│   └── options.py         # ChromiumOptions configuration
├── connection/            # WebSocket connection to CDP
│   └── connection_handler.py  # Command execution + event dispatch
├── elements/              # DOM element wrappers
│   ├── web_element.py     # WebElement class
│   ├── shadow_root.py     # ShadowRoot class
│   └── mixins/            # FindElementsMixin (shared query logic)
├── extractor/             # Pydantic-powered structured extraction
│   ├── engine.py          # ExtractionEngine (orchestrates extraction)
│   ├── model.py           # ExtractionModel base class
│   └── field.py           # Field descriptor + ExtractionMetadata
├── interactions/          # Input simulation (mouse, keyboard, scroll)
├── protocol/              # CDP domain type stubs and event definitions
│   ├── fetch/, network/,  # Per-domain events, methods, types
│   ├── dom/, page/, ...
│   └── base.py            # Base CDP types
├── commands/              # CDP command builder functions
├── constants.py           # By, Key, PageLoadState, Scripts enums
├── decorators.py          # @retry decorator
└── exceptions.py          # Full exception hierarchy
```

The flow is: `Browser` (Chrome/Edge) starts the process → `ConnectionHandler` manages a WebSocket to the CDP endpoint → `Tab` dispatches commands through `ConnectionHandler` → `WebElement` / `ShadowRoot` wrap CDP object IDs for element interaction → `ExtractionEngine` uses `Tab`/`WebElement` queries to populate `ExtractionModel` instances.

## Related Projects and Dependencies

| Dependency | Role |
|---|---|
| `websockets >= 14, < 17` | Async WebSocket client for CDP communication |
| `aiohttp ^3.9.5` | Async HTTP for resource fetching (bundle mode) |
| `aiofiles ^25.1.0` | Async file I/O (screenshots, PDFs, bundles) |
| `pydantic ^2.0` | Model validation and serialization for `ExtractionModel` |
| `typing_extensions ^4.14.0` | Backported typing features (TypedDict, etc.) |

**Runtime**: Python >= 3.10 required (uses `match`, `TypeAlias`, union type syntax).

**Related tools/alternatives**: Selenium (WebDriver-based), Playwright (multi-browser, WebDriver alternative), Puppeteer (Node.js CDP), nodriver (also WebDriver-free CDP), undetected-chromedriver (Selenium anti-detection fork).
