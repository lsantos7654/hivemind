# Pydoll: Code Structure

## Annotated Directory Tree

```
pydoll-python/                         # Repository root
├── pydoll/                            # Main Python package
│   ├── __init__.py                    # Empty (no top-level exports)
│   ├── py.typed                       # PEP 561 marker for mypy
│   ├── constants.py                   # Enums: By, PageLoadState, ScrollPosition, Key, Scripts
│   ├── decorators.py                  # @retry decorator with backoff + recovery callbacks
│   ├── exceptions.py                  # Complete exception hierarchy (30+ exceptions)
│   │
│   ├── browser/                       # Browser lifecycle and high-level tab API
│   │   ├── __init__.py                # Exports Chrome, Edge
│   │   ├── interfaces.py              # ABCs: Options, BrowserOptionsManager
│   │   ├── options.py                 # ChromiumOptions class (CLI args + prefs management)
│   │   ├── tab.py                     # Tab class — primary automation interface (~2000 lines)
│   │   │
│   │   ├── chromium/                  # Concrete browser implementations
│   │   │   ├── __init__.py            # Exports Chrome, Edge
│   │   │   ├── base.py                # Browser ABC — process lifecycle + CDP commands (~1061 lines)
│   │   │   ├── chrome.py              # Chrome: default binary paths per OS
│   │   │   └── edge.py                # Edge: default binary paths per OS
│   │   │
│   │   ├── managers/                  # Browser management utilities
│   │   │   ├── __init__.py            # Exports all managers
│   │   │   ├── browser_options_manager.py  # ChromiumOptionsManager: initializes options + args
│   │   │   ├── browser_process_manager.py  # Launches/terminates the browser subprocess
│   │   │   ├── proxy_manager.py       # Parses proxy config from options args
│   │   │   └── temp_dir_manager.py    # Creates/cleans up temporary user-data-dir
│   │   │
│   │   └── requests/                  # HTTP request abstraction over browser fetch API
│   │       ├── __init__.py            # Exports Request, Response
│   │       ├── request.py             # Request class: get/post/put/delete + HAR record/replay
│   │       ├── response.py            # Response class: status, headers, text(), json(), bytes()
│   │       └── har_recorder.py        # HarCapture, HarRecorder: HAR 1.2 recording
│   │
│   ├── connection/                    # WebSocket communication layer
│   │   ├── __init__.py                # Exports ConnectionHandler
│   │   ├── connection_handler.py      # WebSocket manager: execute_command + event dispatch
│   │   └── managers/                  # Sub-managers for commands and events
│   │       ├── __init__.py
│   │       ├── commands_manager.py    # Pending command registry; matches responses by id
│   │       └── events_manager.py      # Event callback registry; network_logs; dialog state
│   │
│   ├── elements/                      # DOM element wrappers
│   │   ├── __init__.py
│   │   ├── web_element.py             # WebElement: click, type, scroll, screenshot, JS exec (~1058 lines)
│   │   ├── shadow_root.py             # ShadowRoot: query inside shadow DOM (open + closed)
│   │   ├── mixins/
│   │   │   ├── __init__.py
│   │   │   └── find_elements_mixin.py # FindElementsMixin: find/query/wait methods (~907 lines)
│   │   └── utils/
│   │       ├── __init__.py
│   │       └── selector_parser.py     # SelectorParser: auto-detect CSS vs XPath
│   │
│   ├── extractor/                     # Pydantic-powered structured extraction
│   │   ├── __init__.py                # Public exports: ExtractionModel, Field, exceptions
│   │   ├── model.py                   # ExtractionModel(BaseModel): cached field metadata
│   │   ├── field.py                   # Field() descriptor + ExtractionMetadata dataclass + registry
│   │   ├── engine.py                  # ExtractionEngine: orchestrates DOM queries + model building
│   │   └── exceptions.py             # ExtractionException, FieldExtractionFailed, InvalidExtractionModel
│   │
│   ├── interactions/                  # Human-like input simulation
│   │   ├── __init__.py                # Exports KeyboardAPI, MouseAPI, ScrollAPI
│   │   ├── mouse.py                   # Mouse class: move/click/double-click/drag with physics
│   │   ├── keyboard.py                # Keyboard class: key events, key combos
│   │   ├── scroll.py                  # ScrollAPI: scroll up/down/left/right with humanization
│   │   ├── iframe.py                  # IFrameContext, IFrameContextResolver: iframe routing
│   │   └── utils.py                   # bezier_2d, fitts_duration, minimum_jerk, random_control_points
│   │
│   ├── protocol/                      # CDP domain type stubs, events, method signatures
│   │   ├── __init__.py
│   │   ├── base.py                    # CDPEvent, Command, Response, EmptyResponse TypedDicts
│   │   ├── accessibility/             # CDP Accessibility domain
│   │   ├── browser/                   # Browser: types, events, methods
│   │   ├── debugger/                  # Debugger domain stubs
│   │   ├── dom/                       # DOM: Node type, events, methods
│   │   ├── emulation/                 # Emulation: setUserAgentOverride, etc.
│   │   ├── fetch/                     # Fetch: FetchEvent enum, RequestPausedEvent, types
│   │   ├── input/                     # Input: KeyEventType, MouseEventType, KeyModifier
│   │   ├── io/                        # IO domain
│   │   ├── network/                   # Network: events, har_types, methods, types
│   │   ├── page/                      # Page: PageEvent enum, ScreenshotFormat, FrameResourceTree
│   │   ├── runtime/                   # Runtime: EvaluateResponse, CallFunctionOnResponse
│   │   ├── security/                  # Security domain
│   │   ├── storage/                   # Storage: cookie methods
│   │   └── target/                    # Target: TargetInfo, create/attach/dispose
│   │
│   ├── commands/                      # CDP command builder functions (factory pattern)
│   │   ├── __init__.py                # Exports all *Commands classes
│   │   ├── accessibility_commands.py  # AccessibilityCommands
│   │   ├── browser_commands.py        # BrowserCommands: close, version, window bounds, permissions
│   │   ├── dom_commands.py            # DomCommands: getDocument, querySelector, resolveNode
│   │   ├── emulation_commands.py      # EmulationCommands: setUserAgentOverride
│   │   ├── fetch_commands.py          # FetchCommands: enable, disable, continueRequest, failRequest
│   │   ├── input_commands.py          # InputCommands: dispatchMouseEvent, dispatchKeyEvent
│   │   ├── network_commands.py        # NetworkCommands: enable, getCookies, getResponseBody
│   │   ├── page_commands.py           # PageCommands: navigate, reload, screenshot, PDF, frameTree
│   │   ├── runtime_commands.py        # RuntimeCommands: evaluate, callFunctionOn, enable
│   │   ├── storage_commands.py        # StorageCommands: getCookies, setCookies, clearCookies
│   │   └── target_commands.py         # TargetCommands: createTarget, getTargets, attachToTarget
│   │
│   └── utils/                         # General-purpose utilities
│       ├── __init__.py                # Exports: decode_base64_to_bytes, get_browser_ws_address, etc.
│       ├── general.py                 # HTTP polling for CDP endpoint, base64, text extraction
│       ├── bundle.py                  # collect_frame_resources, inline_all_assets, rewrite_html_urls
│       ├── socks5_proxy_forwarder.py  # SOCKS5 proxy tunnel for browser connections
│       └── user_agent_parser.py       # UserAgentParser: UA → navigator JS override + Client Hints
│
├── tests/                             # pytest test suite
│   ├── conftest.py                    # Fixtures: mock WebSocket, browser, tab instances
│   ├── pages/                         # HTML test pages for integration tests
│   ├── test_browser/                  # Browser and tab unit tests
│   ├── test_commands/                 # Command builder tests
│   ├── test_extractor/                # Extraction engine tests
│   ├── test_interactions/             # Mouse, keyboard, scroll tests
│   ├── test_managers/                 # Browser manager tests
│   ├── test_connection_handler.py     # Connection handler unit tests
│   ├── test_web_element.py            # WebElement tests
│   ├── test_find_elements_mixin.py    # Element finding tests
│   ├── test_shadow_root.py            # ShadowRoot tests
│   ├── test_core_integration.py       # Core integration tests
│   ├── test_shadow_root_integration.py
│   ├── test_iframe_integration.py
│   ├── test_nested_oopif_integration.py
│   ├── test_har_recording_integration.py
│   └── test_click_nested_integration.py
│
├── docs/                              # MkDocs source (not deployed here)
│   └── ...                            # Markdown docs mirroring pydoll.tech
│
├── examples/                          # Runnable usage examples
├── public/                            # Sponsor/branding images for README
├── pyproject.toml                     # Poetry project config + build + lint + test config
├── poetry.lock                        # Pinned dependency versions
├── mkdocs.yml                         # MkDocs + Material configuration
├── CHANGELOG.md                       # Conventional commit changelog
├── CONTRIBUTING.md                    # Contribution guidelines
└── README.md                          # Project overview with code examples
```

## Module and Package Organization

### Layer 1 — Browser Process (`pydoll/browser/`)

The topmost layer users interact with. `Chrome` and `Edge` are thin subclasses of the abstract `Browser` base class (`pydoll/browser/chromium/base.py`). `Browser` provides:
- Process lifecycle: `start()`, `stop()`, `connect(ws_address)`
- Tab management: `new_tab()`, `get_opened_tabs()`, `get_targets()`
- Browser-level CDP: cookies, permissions, window bounds, download behavior
- Proxy configuration with per-context credential storage

`Tab` (`pydoll/browser/tab.py`) is the primary user-facing class for page-level operations: navigation, element finding, JS execution, screenshot/PDF, network events, and the extraction engine.

### Layer 2 — Connection (`pydoll/connection/`)

`ConnectionHandler` manages a single WebSocket connection to a CDP endpoint. It serializes CDP `Command` TypedDicts as JSON, waits for matching responses by command ID, and dispatches incoming events to registered callbacks. Both `Browser` and `Tab` hold their own `ConnectionHandler` instances (browser-level and page-level endpoints respectively).

### Layer 3 — Elements (`pydoll/elements/`)

`WebElement` wraps a CDP `objectId` (a runtime JS object reference). It provides click, type, scroll, screenshot, JavaScript execution, and attribute access — all via `RuntimeCommands.callFunctionOn` or `DomCommands`. `FindElementsMixin` is the shared query logic used by both `Tab` and `WebElement` (and `ShadowRoot`), providing `find()`, `query()`, `query_all()`, `wait_element()`.

### Layer 4 — Extraction Engine (`pydoll/extractor/`)

The extraction system uses a module-level registry pattern: `Field()` registers `ExtractionMetadata` (selector, attribute, transform) in a dict keyed by a unique int, storing only the key in Pydantic's `json_schema_extra`. At model class creation time, `ExtractionModel.get_extraction_fields()` reads the registry to build a cached `{field_name → ExtractionMetadata}` map. The `ExtractionEngine` then queries the DOM for each field and builds model instances.

### Layer 5 — Protocol (`pydoll/protocol/`)

Each CDP domain gets its own sub-package with:
- `types.py` — TypedDicts for CDP data structures
- `events.py` — `str` Enum of event names + TypedDicts for event params
- `methods.py` — TypedDicts for command response structures

### Layer 6 — Commands (`pydoll/commands/`)

Stateless factory functions (grouped into classes like `PageCommands`, `DomCommands`) that build `Command` TypedDicts from typed Python arguments. These are passed directly to `ConnectionHandler.execute_command()`.

## Code Organization Patterns

1. **TypedDict for CDP messages**: All CDP commands, responses, and events are typed using `TypedDict`. The `Command[T_Params, T_Response]` generic allows response types to be inferred at call sites.

2. **Abstract base + concrete subclasses**: `Browser` is an ABC; `Chrome` and `Edge` only override `_get_default_binary_location()`.

3. **Mixins for shared behavior**: `FindElementsMixin` is used by `Tab`, `WebElement`, and `ShadowRoot` to avoid duplication of the ~900-line element-finding logic.

4. **Lazy initialization**: `Tab.request`, `Tab.scroll`, `Tab.keyboard`, `Tab._extractor` are instantiated on first access via `@property` with `Optional` backing fields.

5. **Module-level registry**: `ExtractionMetadata` uses a `_FIELD_METADATA_REGISTRY` dict (keyed by `itertools.count`) for decoupled field registration without metaclass complexity.

6. **Event callback system**: `ConnectionHandler` maintains a dict of `{event_name: [callbacks]}`. `Browser.on()` and `Tab.on()` register async or sync functions; async callbacks are wrapped in `asyncio.create_task()` to avoid blocking the message-receive loop.

7. **CDP domain segregation**: The `protocol/` tree mirrors the CDP domain structure. `commands/` contains builders that produce commands consumed by the connection layer.

8. **IFrame routing**: `IFrameContext` and `IFrameContextResolver` manage routing CDP commands to the correct session when operating inside cross-origin iframes (OOPIFs), injected as `_iframe_context` on `WebElement` instances.
