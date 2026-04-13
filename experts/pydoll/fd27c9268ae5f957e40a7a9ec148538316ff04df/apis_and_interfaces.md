# Pydoll: APIs and Interfaces

## Public Entry Points

### Installation and Import

```python
pip install pydoll-python
```

```python
from pydoll.browser import Chrome, Edge
from pydoll.browser.options import ChromiumOptions
from pydoll.extractor import ExtractionModel, Field
from pydoll.decorators import retry
from pydoll.constants import By, Key, PageLoadState, ScrollPosition
from pydoll.exceptions import ElementNotFound, NavigationError
```

---

## Browser Classes

### `Chrome` / `Edge`  (`pydoll/browser/chromium/chrome.py`, `edge.py`)

Concrete browser implementations. Both accept the same arguments.

```python
class Chrome(Browser):
    def __init__(
        self,
        options: Optional[ChromiumOptions] = None,
        connection_port: Optional[int] = None,  # Random 9223-9322 if None
    ): ...
```

**Usage patterns**:

```python
# Context manager (auto-start and stop)
async with Chrome() as browser:
    tab = await browser.start()

# With options
options = ChromiumOptions()
options.headless = True
options.add_argument('--no-sandbox')
async with Chrome(options=options) as browser:
    tab = await browser.start()

# Connect to existing browser (Docker, remote)
async with Chrome() as browser:
    tab = await browser.connect('ws://localhost:9222/devtools/browser/abc123...')
```

### `Browser` Key Methods (`pydoll/browser/chromium/base.py`)

| Method | Signature | Description |
|---|---|---|
| `start()` | `async (headless=False) -> Tab` | Launch browser, return first tab |
| `stop()` | `async () -> None` | Kill browser process |
| `connect()` | `async (ws_address: str) -> Tab` | Connect to running browser via WS |
| `new_tab()` | `async (url='', browser_context_id=None) -> Tab` | Open new tab |
| `get_opened_tabs()` | `async () -> list[Tab]` | All open page tabs |
| `get_targets()` | `async () -> list[TargetInfo]` | All CDP targets |
| `create_browser_context()` | `async (proxy_server=None, proxy_bypass_list=None) -> str` | Isolated session |
| `delete_browser_context()` | `async (browser_context_id: str)` | Delete context + its tabs |
| `get_cookies()` | `async (browser_context_id=None) -> list[Cookie]` | All cookies |
| `set_cookies()` | `async (cookies, browser_context_id=None)` | Set cookies |
| `delete_all_cookies()` | `async (browser_context_id=None)` | Clear cookies |
| `set_download_path()` | `async (path: str, browser_context_id=None)` | Set download dir |
| `set_download_behavior()` | `async (behavior, download_path=None, ...)` | Full download config |
| `grant_permissions()` | `async (permissions, origin=None, browser_context_id=None)` | Grant browser perms |
| `set_window_bounds()` | `async (bounds: Bounds)` | Resize/move window |
| `set_window_maximized()` | `async ()` | Maximize window |
| `on()` | `async (event_name, callback, temporary=False) -> int` | Register CDP event listener |
| `remove_callback()` | `async (callback_id: int)` | Remove event listener |
| `enable_fetch_events()` | `async (handle_auth_requests=False, resource_type=None)` | Enable request interception |
| `continue_request()` | `async (request_id, url=None, method=None, ...)` | Continue paused request |
| `fail_request()` | `async (request_id, error_reason)` | Block a request |
| `fulfill_request()` | `async (request_id, response_code, headers=None, body=None)` | Mock a response |
| `get_version()` | `async () -> GetVersionResult` | Browser version info |

---

## Tab Class

`Tab` (`pydoll/browser/tab.py`) is the primary automation interface. It inherits `FindElementsMixin`.

### Navigation

```python
await tab.go_to('https://example.com', timeout=300)
await tab.refresh(ignore_cache=False)
url = await tab.current_url      # async property
title = await tab.title          # async property
html = await tab.page_source     # async property
```

### Element Finding

`Tab` and `WebElement` both use `FindElementsMixin` (`pydoll/elements/mixins/find_elements_mixin.py`):

```python
# Keyword-based find (builds CSS selector from kwargs)
element = await tab.find(id='submit')
element = await tab.find(tag_name='textarea', name='q')
element = await tab.find(tag_name='h3', text='pydoll', timeout=10)
elements = await tab.find(class_name='card', find_all=True)

# CSS/XPath selector
element = await tab.query('.search-box')         # CSS
element = await tab.query('//h1[@id="title"]')   # XPath (auto-detected)
elements = await tab.query_all('li.item')

# Wait for element (polling)
element = await tab.wait_element('#dynamic-content', timeout=15)
```

### JavaScript Execution

```python
# Execute in page context
result = await tab.execute_script('return document.title')
result = await tab.execute_script('return window.location.href')

# Execute on a specific element (callFunctionOn)
result = await tab.execute_script('function(){ return this.innerText }', element)
```

### Screenshots and PDF

```python
# Save screenshot to file (extension determines format: png/jpeg/webp)
await tab.take_screenshot(path='screenshot.png')
await tab.take_screenshot(path='screenshot.jpeg', quality=85)
await tab.take_screenshot(path='full.png', beyond_viewport=True)

# Get base64
b64 = await tab.take_screenshot(as_base64=True)

# PDF
await tab.print_to_pdf(path='page.pdf', landscape=False, print_background=True)

# Page bundle (zip with all assets)
await tab.save_bundle('page.zip')
await tab.save_bundle('page-inline.zip', inline_assets=True)
```

### CDP Events

```python
from pydoll.protocol.page.events import PageEvent
from pydoll.protocol.fetch.events import FetchEvent, RequestPausedEvent
from pydoll.protocol.network.events import NetworkEvent

# Enable domains
await tab.enable_page_events()
await tab.enable_network_events()
await tab.enable_fetch_events(handle_auth=False, resource_type=None)
await tab.enable_dom_events()
await tab.enable_runtime_events()

# Register listeners
callback_id = await tab.on(PageEvent.LOAD_EVENT_FIRED, my_callback)
await tab.on(FetchEvent.REQUEST_PAUSED, handle_request)

# Remove listener
await tab._connection_handler.remove_callback(callback_id)

# Disable domains
await tab.disable_page_events()
await tab.disable_fetch_events()
```

### Network Interception

```python
from pydoll.protocol.fetch.events import FetchEvent, RequestPausedEvent
from pydoll.protocol.network.types import ErrorReason

async def block_images(event: RequestPausedEvent):
    request_id = event['params']['requestId']
    resource_type = event['params']['resourceType']
    if resource_type in ['Image', 'Stylesheet']:
        await tab.fail_request(request_id, ErrorReason.BLOCKED_BY_CLIENT)
    else:
        await tab.continue_request(request_id)

await tab.enable_fetch_events()
await tab.on(FetchEvent.REQUEST_PAUSED, block_images)
await tab.go_to('https://example.com')
```

### Network Monitoring

```python
await tab.enable_network_events()
await tab.go_to('https://example.com')

# Get all network logs
logs = await tab.get_network_logs()

# Filter by URL pattern
api_logs = await tab.get_network_logs(filter='/api/')

# Get response body for specific request
body = await tab.get_network_response_body(request_id)
```

### Cookie Management

```python
cookies = await tab.get_cookies()
await tab.set_cookies([{'name': 'session', 'value': 'abc', 'domain': '.example.com'}])
await tab.delete_all_cookies()
```

### Dialogs

```python
await tab.enable_page_events()
has_dialog = await tab.has_dialog()
message = await tab.get_dialog_message()
await tab.handle_dialog(accept=True)              # Accept/confirm
await tab.handle_dialog(accept=False)             # Dismiss/cancel
await tab.handle_dialog(accept=True, prompt_text='my input')  # Prompt
```

### Shadow DOM

```python
# Get shadow root from element
shadow = await element.get_shadow_root()
inner = await shadow.query('.internal-btn')
await inner.click()

# Find all shadow roots on page
shadow_roots = await tab.find_shadow_roots()

# Include cross-origin iframes (OOPIFs)
shadow_roots = await tab.find_shadow_roots(deep=True)

# Wait for shadow roots to appear (e.g., async Cloudflare Turnstile)
shadow_roots = await tab.find_shadow_roots(timeout=10)
```

### Cloudflare Turnstile Auto-Bypass

```python
await tab.enable_auto_solve_cloudflare_captcha(time_to_wait_captcha=5)
await tab.go_to('https://cloudflare-protected-site.com')
# Turnstile checkbox is automatically detected and clicked
```

### IFrame Interaction

```python
# Direct interaction with iframe WebElements (preferred)
iframe_el = await tab.find(tag_name='iframe')
inner_button = await iframe_el.find(id='submit-btn')
await inner_button.click()
```

### File Download Tracking

```python
from pydoll.protocol.browser.types import DownloadBehavior

await browser.set_download_path('/tmp/downloads')
# or
await browser.set_download_behavior(
    behavior=DownloadBehavior.ALLOW,
    download_path='/tmp/downloads',
    events_enabled=True,
)
await tab.wait_download(timeout=30)
```

### Misc Tab Methods

```python
await tab.bring_to_front()
await tab.close()
await tab.enable_intercept_file_chooser_dialog()
```

---

## WebElement Class (`pydoll/elements/web_element.py`)

`WebElement` wraps a CDP runtime object ID. It inherits `FindElementsMixin` so you can search for child elements within it.

### Key Methods

```python
# Interaction
await element.click(humanize=False)              # Click element
await element.double_click(humanize=False)
await element.right_click()
await element.type_text('hello world', humanize=False)  # Type using keyboard events
await element.insert_text('hello')               # Fast text insertion (no key events)
await element.press_keyboard_key(Key.ENTER)
await element.clear_input()                      # Clear input field value

# Scrolling
await element.scroll_into_view()
await element.scroll_to_bottom()

# Attributes and state
tag = element.tag_name                           # str property (sync)
attrs = element.attributes                       # dict (sync)
value = element.get_attribute('href')            # str or None
is_visible = await element.is_visible()          # bool
is_on_top = await element.is_on_top()            # bool
is_interactive = await element.is_interactive()  # bool
outer_html = await element.get_outer_html()      # str
inner_text = await element.get_inner_text()      # str

# Shadow DOM
shadow = await element.get_shadow_root()         # ShadowRoot

# Screenshot of just this element
await element.take_screenshot(path='element.png')
await element.take_screenshot(path='el.jpeg', quality=90)

# File upload
await element.set_input_files(['/path/to/file.pdf'])

# JavaScript
result = await element.execute_script('function(){ return this.value }')

# Element child finding (same API as Tab)
child = await element.find(class_name='child-class')
children = await element.query_all('li')
```

---

## Extraction Engine (`pydoll/extractor/`)

### Defining Models

```python
from pydoll.extractor import ExtractionModel, Field

class Quote(ExtractionModel):
    text: str = Field(selector='.text', description='The quote text')
    author: str = Field(selector='.author', description='Author name')
    tags: list[str] = Field(selector='.tag', description='Tag list')
    year: int | None = Field(selector='.year', default=None)
```

`Field()` parameters (`pydoll/extractor/field.py:56`):

| Parameter | Type | Description |
|---|---|---|
| `selector` | `Optional[str]` | CSS or XPath (auto-detected). Required if no `description`. |
| `attribute` | `Optional[str]` | HTML attribute to extract (default: `innerText`) |
| `description` | `Optional[str]` | Semantic description. Required if no `selector`. |
| `default` | `Any` | Default value if extraction fails (`PydanticUndefined` = required) |
| `transform` | `Optional[Callable[[str], Any]]` | Post-process raw string value |

### Nested Models and Transforms

```python
from datetime import datetime

def parse_date(raw: str) -> datetime:
    return datetime.strptime(raw.strip(), '%B %d, %Y')

class Author(ExtractionModel):
    name: str = Field(selector='.author-title')
    born: datetime = Field(selector='.author-born-date', transform=parse_date)

class Article(ExtractionModel):
    title: str = Field(selector='h1')
    url: str = Field(selector='.source-link', attribute='href')
    author: Author = Field(selector='.author-card', description='Nested model')
```

### Extracting Data

```python
# Single model from page
article = await tab.extract(Article, timeout=5)

# Scoped to a region
product = await tab.extract(Product, scope='#product-container', timeout=5)

# Multiple items (list)
quotes = await tab.extract_all(Quote, scope='.quote', timeout=5)
quotes = await tab.extract_all(Quote, scope='.quote', limit=10)

# Pydantic serialization works as-is
print(article.model_dump_json())
```

---

## Input Interaction APIs (`pydoll/interactions/`)

### MouseAPI (`pydoll/interactions/mouse.py`)

Accessed via `tab.mouse`. All methods have `humanize: bool = True` parameter.

```python
await tab.mouse.move(500, 300, humanize=True)
await tab.mouse.click(500, 300)
await tab.mouse.click(500, 300, humanize=False)   # Skip humanization
await tab.mouse.double_click(500, 300)
await tab.mouse.right_click(500, 300)
await tab.mouse.drag(100, 200, 500, 400)          # Drag from (100,200) to (500,400)
```

Mouse physics (`pydoll/interactions/mouse.py:26`):
- Bezier curves with asymmetric control points
- Fitts's Law timing (duration scales with distance)
- Minimum-jerk velocity profile
- Physiological tremor (Gaussian noise)
- Overshoot correction (~70% probability on fast moves)

### KeyboardAPI (`pydoll/interactions/keyboard.py`)

Accessed via `tab.keyboard`:

```python
from pydoll.constants import Key

await tab.keyboard.press(Key.ENTER)
await tab.keyboard.press(Key.TAB)
await tab.keyboard.key_down(Key.SHIFT)
await tab.keyboard.key_up(Key.SHIFT)
await tab.keyboard.type_text('Hello World')
```

### ScrollAPI (`pydoll/interactions/scroll.py`)

Accessed via `tab.scroll`:

```python
from pydoll.constants import ScrollPosition

await tab.scroll.up(pixels=500)
await tab.scroll.down(pixels=500)
await tab.scroll.left(pixels=200)
await tab.scroll.right(pixels=200)
await tab.scroll.to_top()
await tab.scroll.to_bottom()
```

---

## HTTP Request API (`pydoll/browser/requests/request.py`)

`tab.request` provides a `requests`-like interface that runs inside the browser's JavaScript context, inheriting cookies, session state, and CORS policies.

```python
# GET
response = await tab.request.get('https://api.example.com/data')
data = response.json()
text = response.text()
raw = response.bytes()

# POST with JSON
response = await tab.request.post(
    'https://api.example.com/submit',
    json={'key': 'value'},
)

# With custom headers
response = await tab.request.get(
    url,
    headers={'Authorization': 'Bearer TOKEN'},
)

# HAR recording
async with tab.request.record() as capture:
    await tab.go_to('https://example.com')
capture.save('flow.har')
print(f'Captured {len(capture.entries)} requests')

# Replay HAR
responses = await tab.request.replay('flow.har')
```

---

## ChromiumOptions (`pydoll/browser/options.py`)

```python
from pydoll.browser.options import ChromiumOptions

options = ChromiumOptions()

# Common flags
options.headless = True                   # --headless
options.webrtc_leak_protection = True     # Prevent WebRTC IP leaks
options.binary_location = '/path/to/chrome'
options.start_timeout = 15                # Seconds to wait for browser to start
options.page_load_state = PageLoadState.COMPLETE  # or INTERACTIVE

# CLI arguments
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--proxy-server=http://proxy:8080')
options.remove_argument('--no-sandbox')

# Preferences (browser internal settings)
options.browser_preferences = {
    'profile': {
        'default_content_setting_values': {
            'notifications': 2,  # Block notifications
            'geolocation': 2,    # Block geolocation
        },
        'password_manager_enabled': False,
    },
    'intl': {'accept_languages': 'en-US,en'},
}

# Convenience setters
options.block_notifications = True
options.block_popups = True
options.password_manager_enabled = False
options.prompt_for_download = False
options.allow_automatic_downloads = True
options.open_pdf_externally = True
options.set_default_download_directory('/tmp/downloads')
options.set_accept_languages('en-US,en')
```

---

## @retry Decorator (`pydoll/decorators.py`)

```python
from pydoll.decorators import retry
from pydoll.exceptions import ElementNotFound, NetworkError

@retry(
    max_retries=3,
    exceptions=[ElementNotFound, NetworkError],
    on_retry=refresh_page_callback,   # Called after each failed attempt
    delay=1.0,                        # Seconds between attempts
    exponential_backoff=True,         # delay * 2^attempt
    exception_to_raise=MyCustomError, # Raise this after exhaustion (optional)
)
async def scrape_product(self, url: str):
    ...
```

---

## Constants and Enums (`pydoll/constants.py`)

### `By` Enum — element finding strategies
```python
By.CSS_SELECTOR, By.XPATH, By.CLASS_NAME, By.ID, By.TAG_NAME, By.NAME
```

### `Key` Enum — keyboard keys
```python
Key.ENTER, Key.TAB, Key.ESCAPE, Key.SPACE, Key.BACKSPACE, Key.DELETE,
Key.ARROW_UP, Key.ARROW_DOWN, Key.ARROW_LEFT, Key.ARROW_RIGHT,
Key.F1 ... Key.F12, Key.SHIFT, Key.CTRL, Key.ALT, ...
```

### `PageLoadState` Enum
```python
PageLoadState.COMPLETE, PageLoadState.INTERACTIVE, PageLoadState.LOADING
```

### `ScrollPosition` Enum
```python
ScrollPosition.UP, ScrollPosition.DOWN, ScrollPosition.LEFT, ScrollPosition.RIGHT
```

---

## CDP Protocol Events (`pydoll/protocol/*/events.py`)

Common event enums used with `tab.on()`:

```python
from pydoll.protocol.page.events import PageEvent
from pydoll.protocol.fetch.events import FetchEvent
from pydoll.protocol.network.events import NetworkEvent
from pydoll.protocol.dom.events import DomEvent

# Page events
PageEvent.LOAD_EVENT_FIRED
PageEvent.DOM_CONTENT_LOADED
PageEvent.FRAME_NAVIGATED
PageEvent.FILE_CHOOSER_OPENED

# Fetch/interception events
FetchEvent.REQUEST_PAUSED
FetchEvent.AUTH_REQUIRED

# Network monitoring events
NetworkEvent.REQUEST_WILL_BE_SENT
NetworkEvent.RESPONSE_RECEIVED
NetworkEvent.LOADING_FAILED
```

---

## Exception Hierarchy (`pydoll/exceptions.py`)

```
PydollException
├── ConnectionException
│   ├── ConnectionFailed
│   ├── ReconnectionFailed
│   ├── WebSocketConnectionClosed
│   └── NetworkError
├── BrowserException
│   ├── BrowserNotRunning
│   ├── FailedToStartBrowser
│   ├── UnsupportedOS
│   ├── NoValidTabFound
│   ├── InvalidConnectionPort
│   ├── InvalidWebSocketAddress
│   └── MissingTargetOrWebSocket
├── ProtocolException
│   ├── TopLevelTargetRequired
│   ├── InvalidCommand / InvalidResponse
│   ├── CommandExecutionTimeout
│   └── InvalidCallback
├── ElementException
│   ├── ElementNotFound
│   ├── ElementNotVisible
│   ├── ElementNotInteractable
│   ├── ClickIntercepted
│   ├── ElementNotAFileInput
│   ├── ShadowRootNotFound
│   └── ElementPreconditionError
├── TimeoutException
│   ├── PageLoadTimeout
│   ├── WaitElementTimeout
│   └── DownloadTimeout
├── ConfigurationException
│   ├── InvalidOptionsObject
│   ├── InvalidBrowserPath
│   ├── InvalidFileExtension
│   ├── ArgumentAlreadyExistsInOptions
│   └── MissingScreenshotPath
├── NavigationError
├── DialogException / NoDialogPresent
├── RequestException / HTTPError / HarRecordingError
└── ScriptException / InvalidScriptWithElement
```

---

## Integration Patterns

### Multi-Tab Concurrent Scraping

```python
async with Chrome() as browser:
    tab1 = await browser.start()
    tab2 = await browser.new_tab()

    results = await asyncio.gather(
        scrape_page('https://google.com/', tab1),
        scrape_page('https://duckduckgo.com/', tab2),
    )
```

### Isolated Browser Contexts

```python
async with Chrome() as browser:
    context_id = await browser.create_browser_context(
        proxy_server='http://user:pass@proxy:8080'
    )
    tab = await browser.new_tab(browser_context_id=context_id)
    # tab operates in isolated session
    await browser.delete_browser_context(context_id)
```

### Remote Browser Connection (e.g., Browserless)

```python
async with Chrome() as browser:
    # Tokens in query string are preserved for per-tab WS URLs
    tab = await browser.connect('wss://chrome.browserless.io?token=MY_TOKEN')
    await tab.go_to('https://example.com')
```
