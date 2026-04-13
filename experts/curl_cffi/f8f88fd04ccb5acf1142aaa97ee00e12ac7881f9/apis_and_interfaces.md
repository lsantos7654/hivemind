# curl_cffi — APIs and Interfaces

## Public Entry Points

Everything exported via `curl_cffi/__init__.py` is the stable public surface. Key symbols:

```python
# High-level convenience functions (stateless, open a new Session per call)
from curl_cffi import get, post, put, patch, delete, head, options, request

# Session classes (connection/cookie reuse)
from curl_cffi import Session, AsyncSession

# Low-level handle
from curl_cffi import Curl, AsyncCurl, CurlMime, CurlError

# Enums and constants
from curl_cffi import CurlOpt, CurlInfo, CurlECode, CurlHttpVersion
from curl_cffi import CurlFollow, CurlSslVersion, CurlWsFlag, CurlMOpt

# Types
from curl_cffi import BrowserType, BrowserTypeLiteral, ExtraFingerprints
from curl_cffi import Cookies, Headers, Request, Response
from curl_cffi import CookieTypes, HeaderTypes, ProxySpec

# WebSocket
from curl_cffi import WebSocket, AsyncWebSocket
from curl_cffi import WebSocketError, WebSocketClosed, WebSocketTimeout
from curl_cffi import WebSocketRetryStrategy, WsCloseCode

# CFFI objects (for low-level use)
from curl_cffi import ffi, lib
```

---

## High-Level requests-like API

### Module-level HTTP functions (`curl_cffi/requests/__init__.py`)

All functions share the same signature and accept `**kwargs` forwarded to `Session.request()`.

```python
def get(url: str, **kwargs) -> Response: ...
def post(url: str, **kwargs) -> Response: ...
def put(url: str, **kwargs) -> Response: ...
def patch(url: str, **kwargs) -> Response: ...
def delete(url: str, **kwargs) -> Response: ...
def head(url: str, **kwargs) -> Response: ...
def options(url: str, **kwargs) -> Response: ...
def request(method: str, url: str, **kwargs) -> Response: ...
```

Additional HTTP methods supported only through `request()`: `trace`, `query`.

**Key keyword arguments** (defined in `RequestParams` TypedDict, `session.py:96-130`):

| Parameter | Type | Description |
|---|---|---|
| `params` | `dict\|list\|tuple` | Query string parameters |
| `data` | `dict\|str\|bytes\|BytesIO` | Request body (form-encoded if dict) |
| `json` | `dict\|list` | JSON request body; sets `Content-Type: application/json` |
| `headers` | `HeaderTypes` | Additional headers |
| `cookies` | `CookieTypes` | Cookies to send |
| `auth` | `tuple[str, str]` | `(username, password)` for HTTP Basic auth |
| `timeout` | `float\|tuple[float,float]` | Seconds; tuple is `(connect, read)` |
| `allow_redirects` | `bool\|CurlFollow\|"safe"` | Follow redirects; `"safe"` blocks private IPs |
| `max_redirects` | `int` | Default 30; `-1` = unlimited |
| `proxies` | `ProxySpec` | `{"http": url, "https": url, "all": url}` |
| `proxy` | `str` | Single proxy URL; shortcut for `proxies={"all": ...}` |
| `verify` | `bool` | SSL cert verification (default `True`) |
| `impersonate` | `BrowserTypeLiteral` | Browser to impersonate, e.g. `"chrome"`, `"safari"` |
| `ja3` | `str` | Custom JA3 string |
| `akamai` | `str` | Custom Akamai HTTP/2 fingerprint string |
| `extra_fp` | `ExtraFingerprints\|dict` | Fine-grained TLS/HTTP2/3 knobs |
| `default_headers` | `bool` | Add browser default headers (default `True`) |
| `http_version` | `"v1"\|"v2"\|"v2tls"\|"v2_prior_knowledge"\|"v3"\|"v3only"` | Force HTTP version |
| `stream` | `bool` | Enable streaming response |
| `content_callback` | `Callable[[bytes], None]` | Per-chunk callback instead of buffering |
| `multipart` | `CurlMime` | Multipart form upload |
| `cert` | `str\|tuple[str,str]` | Client certificate file(s) |
| `interface` | `str` | Outgoing network interface name |
| `max_recv_speed` | `int` | Throttle download bytes/sec |
| `quote` | `str\|False` | Characters to percent-encode; `False` = no encoding |
| `referer` | `str` | Shortcut for `Referer` header |
| `accept_encoding` | `str` | Default `"gzip, deflate, br"` |
| `discard_cookies` | `bool` | Don't store server-set cookies in session |
| `curl_options` | `dict[CurlOpt, Any]` | Raw curl option overrides |

### `Session` class (`curl_cffi/requests/session.py:404`)

```python
class Session(BaseSession[R]):
    def __init__(
        self,
        curl: Optional[Curl] = None,
        thread: Optional[Literal["eventlet", "gevent"]] = None,
        use_thread_local_curl: bool = True,
        **kwargs,   # same as BaseSessionParams
    ): ...

    # HTTP methods
    def request(self, method, url, **kwargs) -> R: ...
    def get(self, url, **kwargs) -> R: ...
    def post(self, url, **kwargs) -> R: ...
    def put(self, url, **kwargs) -> R: ...
    def patch(self, url, **kwargs) -> R: ...
    def delete(self, url, **kwargs) -> R: ...
    def head(self, url, **kwargs) -> R: ...
    def options(self, url, **kwargs) -> R: ...
    def trace(self, url, **kwargs) -> R: ...
    def query(self, url, **kwargs) -> R: ...

    # Streaming context manager
    @contextmanager
    def stream(self, method, url, **kwargs) -> Generator[R, None, None]: ...

    # WebSocket (deprecated; use WebSocket class directly)
    def ws_connect(self, url, on_message=None, ...) -> WebSocket: ...

    # Context manager protocol
    def __enter__(self) -> Session: ...
    def __exit__(self, *args) -> None: ...
    def close(self) -> None: ...
```

**Usage example — basic session with cookie persistence:**

```python
from curl_cffi import Session

with Session(impersonate="chrome") as s:
    r = s.get("https://httpbin.org/cookies/set/foo/bar")
    print(s.cookies)      # <Cookies[<Cookie foo=bar for httpbin.org />]>
    r = s.get("https://httpbin.org/cookies")
    print(r.json())       # {'cookies': {'foo': 'bar'}}
```

**Usage example — custom JA3/Akamai fingerprints:**

```python
from curl_cffi import Session

with Session() as s:
    r = s.get(
        "https://tls.browserleaks.com/json",
        ja3="771,4865-4866-4867-49195-49199,0-23-65281-10-11-35-16-5-13-18-51-45-43-27-17513-21,29-23-24,0",
        akamai="1:65536,2:0,3:1000,4:6291456,6:262144|15663105|0|m,a,s,p",
    )
```

**Usage example — streaming SSE / large downloads:**

```python
with Session() as s:
    with s.stream("GET", "https://example.com/big-file") as r:
        for chunk in r.iter_content():
            process(chunk)
```

### `AsyncSession` class (`curl_cffi/requests/session.py:866`)

```python
class AsyncSession(BaseSession[R]):
    def __init__(
        self,
        loop: asyncio.AbstractEventLoop | None = None,
        async_curl: AsyncCurl | None = None,
        max_clients: int = 10,
        **kwargs,   # same as BaseSessionParams
    ): ...

    async def request(self, method, url, **kwargs) -> R: ...
    async def get(self, url, **kwargs) -> R: ...
    # ... same HTTP methods as Session ...

    @asynccontextmanager
    async def stream(self, method, url, **kwargs) -> AsyncGenerator[R, None]: ...

    def ws_connect(self, url, **kwargs) -> AsyncWebSocketContext: ...

    async def __aenter__(self) -> AsyncSession: ...
    async def __aexit__(self, *args) -> None: ...
    async def close(self) -> None: ...
```

**Usage example — concurrent async requests:**

```python
import asyncio
from curl_cffi import AsyncSession

async def main():
    async with AsyncSession(impersonate="chrome") as s:
        results = await asyncio.gather(
            s.get("https://google.com/"),
            s.get("https://example.com/"),
            s.get("https://httpbin.org/get"),
        )
    for r in results:
        print(r.status_code)

asyncio.run(main())
```

---

## Response Object (`curl_cffi/requests/models.py:60`)

```python
class Response:
    url: str
    status_code: int
    reason: str
    ok: bool                          # True if 200 <= status_code < 400
    headers: Headers
    cookies: Cookies
    content: bytes
    text: str                         # decoded content (lazy)
    encoding: str                     # charset from header or default_encoding
    charset: str                      # alias for encoding
    charset_encoding: Optional[str]   # from Content-Type header only
    elapsed: timedelta
    http_version: int                 # 10, 11, 20, 30
    redirect_count: int
    redirect_url: str
    primary_ip: str
    primary_port: int
    local_ip: str
    local_port: int
    download_size: int
    upload_size: int
    header_size: int
    request_size: int
    response_size: int
    infos: dict                       # custom CurlInfo values if curl_infos= was set

    def json(self, **kw): ...          # orjson.loads or json.loads
    def raise_for_status(self): ...    # raises HTTPError if not ok
    def iter_content(self, ...): ...   # sync streaming chunks
    def iter_lines(self, ...): ...     # sync streaming lines
    async def aiter_content(self, ...): ...
    async def aiter_lines(self, ...): ...
    async def acontent(self) -> bytes: ...
    async def atext(self) -> str: ...
    def markdown(self) -> str: ...     # requires curl_cffi[extra]
    def close(self): ...               # close streaming connection
    async def aclose(self): ...
```

---

## WebSocket APIs

### Synchronous WebSocket (`curl_cffi/requests/websockets.py`)

```python
from curl_cffi import WebSocket

def on_message(ws: WebSocket, message: str | bytes):
    print(message)

def on_error(ws: WebSocket, error: CurlError):
    print("error:", error)

def on_open(ws: WebSocket):
    ws.send("hello")

ws = WebSocket(
    on_message=on_message,
    on_error=on_error,
    on_open=on_open,
    impersonate="chrome",
)
ws.run_forever("wss://echo.websocket.org")
```

Key `WebSocket` methods:
- `send(data: str | bytes)` — send a text or binary frame
- `send_bytes(data: bytes)` — explicit binary
- `send_str(data: str)` — explicit text
- `recv()` — receive one message
- `run_forever(url, **kwargs)` — blocking loop
- `connect(url, **kwargs)` — connect without blocking loop
- `close(code, message)` — close the connection

### Asynchronous WebSocket (`curl_cffi/requests/websockets.py`)

```python
from curl_cffi import AsyncSession

async with AsyncSession(impersonate="chrome") as s:
    async with s.ws_connect("wss://echo.websocket.org") as ws:
        await ws.send_str("Hello!")
        async for msg in ws:
            print(msg)
            break
```

`AsyncSession.ws_connect()` returns an `AsyncWebSocketContext`. Inside the `async with` block, the `AsyncWebSocket` object provides:
- `await send(data)` / `await send_str(s)` / `await send_bytes(b)`
- `await recv()` → `str | bytes`
- `await recv_str()` → `str`
- `await recv_bytes()` → `bytes`
- `async for msg in ws:` — iterate incoming messages
- `await close(code, message)`
- `terminate()` — force close without handshake

`ws_connect()` parameters of note:
- `recv_queue_size=32` — max buffered incoming messages
- `send_queue_size=16` — max buffered outgoing messages
- `coalesce_frames=False` — merge multiple sends into one frame (use only for stream protocols)
- `ws_retry: WebSocketRetryStrategy` — retry policy for recv failures
- `max_message_size=4*1024*1024` — max single message size
- `drain_on_error=False` — consume buffered messages before raising errors

---

## Low-Level Curl API

### `Curl` class (`curl_cffi/curl.py:211`)

```python
from curl_cffi import Curl, CurlOpt, CurlInfo

c = Curl()
c.setopt(CurlOpt.URL, "https://example.com")
c.setopt(CurlOpt.WRITEDATA, buffer)      # auto-sets WRITEFUNCTION to buffer_callback
c.setopt(CurlOpt.HTTPHEADER, [b"Accept: application/json"])
c.impersonate("chrome131")
c.perform()

url = c.getinfo(CurlInfo.EFFECTIVE_URL)   # bytes
code = c.getinfo(CurlInfo.RESPONSE_CODE)  # int
time = c.getinfo(CurlInfo.TOTAL_TIME)     # float

c.reset()     # reset options (reuse handle)
c.close()     # free handle
```

`setopt()` handles type conversion automatically:
- `int` → `ffi.new("long*", value)`
- `str` → encoded `bytes` (Windows file paths use ANSI encoding)
- `WRITEDATA` / `HEADERDATA` → wraps a file-like object, auto-installs `buffer_callback`
- `WRITEFUNCTION` / `HEADERFUNCTION` / `READFUNCTION` → wraps a Python callable via `ffi.new_handle`
- `HTTPHEADER` / `PROXYHEADER` → appends to `curl_slist`
- `DEBUGFUNCTION` → wraps callable; `True` uses the default `debug_function_default` printer

### `CurlMime` class (`curl_cffi/curl.py:693`)

```python
from curl_cffi import Curl, CurlMime, CurlOpt

c = Curl()
mime = CurlMime(curl=c)
mime.addpart(
    name="file",
    filename="photo.jpg",
    content_type="image/jpeg",
    local_path="/path/to/photo.jpg",
)
mime.addpart(name="description", data=b"My photo")
mime.attach(c)   # sets MIMEPOST option
c.perform()
mime.close()     # must call after perform
```

`CurlMime.from_list(files: list[dict])` — class method for batch creation.

### `AsyncCurl` class (`curl_cffi/aio.py:171`)

```python
from curl_cffi import AsyncCurl, Curl
import asyncio

async def main():
    loop = asyncio.get_running_loop()
    acurl = AsyncCurl(loop=loop)
    curl = Curl()
    # ... set options on curl ...
    future = acurl.add_handle(curl)
    await future
    # read response from curl
    await acurl.close()
```

Typically not used directly; `AsyncSession` manages `AsyncCurl` internally.

---

## Impersonation Configuration

### Built-in targets (`curl_cffi/requests/impersonate.py`)

Pass the target as a string to the `impersonate` parameter on any request or session.

```python
# Latest alias (tracks newest supported version)
impersonate="chrome"      # → chrome146
impersonate="safari"      # → safari2601
impersonate="safari_ios"  # → safari260_ios
impersonate="firefox"     # → firefox147
impersonate="edge"        # → edge101
impersonate="chrome_android"  # → chrome131_android

# Pinned versions
impersonate="chrome136"
impersonate="safari184_ios"
impersonate="firefox144"
impersonate="tor145"
```

### Custom fingerprints

```python
r = curl_cffi.get(
    "https://tls.browserleaks.com/json",
    ja3="771,4865-4866-...,0-23-...,29-23-24,0",
    akamai="1:65536,2:0,...|15663105|0|m,a,s,p",
    extra_fp={
        "tls_min_version": 0x0303,       # TLS 1.2
        "tls_grease": True,
        "tls_permute_extensions": True,
        "tls_cert_compression": "brotli",
        "http2_stream_weight": 256,
        "http2_stream_exclusive": 1,
    }
)
```

### `ExtraFingerprints` dataclass fields (`curl_cffi/requests/impersonate.py:177`)

| Field | Type | Default | Description |
|---|---|---|---|
| `tls_min_version` | `int` | `TLSv1_2` | Minimum TLS version (use `TLS_VERSION_MAP`) |
| `tls_grease` | `bool` | `False` | Enable TLS GREASE |
| `tls_permute_extensions` | `bool` | `False` | Randomize extension order |
| `tls_cert_compression` | `"zlib"\|"brotli"` | `"brotli"` | Certificate compression |
| `tls_signature_algorithms` | `list[str]\|None` | `None` | Override sig algorithm list |
| `tls_delegated_credential` | `str` | `""` | Delegated credential string |
| `tls_record_size_limit` | `int` | `0` | TLS record_size_limit extension value |
| `http2_stream_weight` | `int` | `256` | HTTP/2 stream priority weight |
| `http2_stream_exclusive` | `int` | `1` | HTTP/2 stream exclusive flag |
| `http2_no_priority` | `bool` | `False` | Disable HTTP/2 priority frames |
| `split_cookies` | `bool\|None` | `None` | Split cookies into individual headers |
| `form_boundary` | `bool\|None` | `None` | Custom form boundary behavior |
| `http3_sig_hash_algs` | `str\|None` | `None` | HTTP/3 signature hash algorithms |
| `http3_tls_extension_order` | `str\|None` | `None` | HTTP/3 TLS extension order |

---

## Exception Hierarchy (`curl_cffi/requests/exceptions.py`)

```
CurlError (base)
└── RequestException(CurlError, OSError)
    ├── SessionClosed
    ├── ImpersonateError
    ├── CookieConflict
    ├── HTTPError
    │   └── IncompleteRead
    ├── ConnectionError
    │   ├── DNSError
    │   └── SSLError
    │       └── CertificateVerifyError
    ├── ProxyError
    ├── Timeout
    ├── TooManyRedirects
    ├── InvalidURL
    ├── InvalidSchema
    ├── InterfaceError
    └── WebSocketError (also in websockets.py)
        ├── WebSocketClosed
        └── WebSocketTimeout
```

Exceptions carry a `.code` attribute (`CurlECode`) and `.response` for HTTP-level errors.

---

## RetryStrategy (`curl_cffi/requests/session.py:174`)

```python
from curl_cffi.requests import RetryStrategy, Session

with Session(
    retry=RetryStrategy(
        count=3,
        delay=1.0,
        jitter=0.3,
        backoff="exponential",  # or "linear"
    )
) as s:
    r = s.get("https://example.com")
```

Or simply pass `retry=3` for `count=3, delay=0, no jitter, linear`.

---

## CLI Interface (`curl_cffi/cli/__init__.py`)

The `curl-cffi` command is registered as a console script in `pyproject.toml`:
```
curl-cffi = "curl_cffi.cli:main"
```

```bash
# HTTP verb commands
curl-cffi get https://httpbin.org/get Accept:application/json
curl-cffi post https://httpbin.org/post field=value field2:='{"key": "val"}'
curl-cffi get tls.browserleaks.com/json --impersonate chrome136

# HTTP version
curl-cffi get https://example.com --http3

# Output control
curl-cffi get https://example.com --headers   # response headers only
curl-cffi get https://example.com --body      # body only
curl-cffi get https://example.com --verbose   # full request + response
curl-cffi get https://example.com -p hb       # h=resp headers, b=resp body

# File replay
curl-cffi run requests.http --session
curl-cffi run archive.har

# Diagnostics
curl-cffi doctor
```

Request item syntax (HTTPie-style):
- `Header:Value` — HTTP header
- `param==value` — query parameter
- `field=value` — data field (JSON or form)
- `field:=json_value` — raw JSON value
- `@file` — file upload
- `+key=value` — cookie

---

## Integration Patterns

### Custom response class

```python
from curl_cffi import Session
from curl_cffi.requests.models import Response

class MyResponse(Response):
    @property
    def data(self):
        return self.json().get("data")

with Session(response_class=MyResponse) as s:
    r = s.get("https://api.example.com/items")
    print(r.data)  # MyResponse.data
```

### Content callback for streaming

```python
import sys
from curl_cffi import Session

with Session() as s:
    s.get(
        "https://example.com/large-file",
        content_callback=lambda chunk: sys.stdout.buffer.write(chunk),
        stream=True,
    )
```

### Scrapy integration (third-party)

```python
# scrapy-curl-cffi / scrapy-impersonate
# settings.py
DOWNLOADER_MIDDLEWARES = {
    "scrapy_impersonate.ImpersonateMiddleware": 543,
}
IMPERSONATE = "chrome"
```

### Direct curl_options override

```python
from curl_cffi import Session, CurlOpt

with Session() as s:
    r = s.get(
        "https://example.com",
        curl_options={CurlOpt.TCP_FASTOPEN: 1},
    )
```
