## APIs and Interfaces

### Top-Level Convenience API

The primary entry point for most users. All functions are in `httpx/__init__.py` and available as `httpx.<function>`.

**`httpx.request(method, url, **kwargs) -> Response`**
The general-purpose request function. All other convenience functions delegate to it. Creates a temporary `Client`, sends the request, and returns a `Response`.

```python
import httpx
r = httpx.request("GET", "https://api.example.com/data")
r = httpx.request("POST", "https://api.example.com/submit", json={"key": "value"})
```

**HTTP method convenience functions:**
- `httpx.get(url, *, params, headers, cookies, auth, proxy, follow_redirects, verify, timeout, trust_env) -> Response`
- `httpx.post(url, *, content, data, files, json, params, headers, cookies, auth, proxy, follow_redirects, verify, timeout, trust_env) -> Response`
- `httpx.put(url, *, content, data, files, json, params, headers, cookies, auth, proxy, follow_redirects, verify, timeout, trust_env) -> Response`
- `httpx.patch(url, *, content, data, files, json, params, headers, cookies, auth, proxy, follow_redirects, verify, timeout, trust_env) -> Response`
- `httpx.delete(url, *, params, headers, cookies, auth, proxy, follow_redirects, verify, timeout, trust_env) -> Response`
- `httpx.head(url, *, params, headers, cookies, auth, proxy, follow_redirects, verify, timeout, trust_env) -> Response`
- `httpx.options(url, *, params, headers, cookies, auth, proxy, follow_redirects, verify, timeout, trust_env) -> Response`

**`httpx.stream(method, url, **kwargs) -> Iterator[Response]`**
Context manager for streaming responses without loading the entire body into memory:

```python
with httpx.stream("GET", "https://example.com/large-file") as r:
    for chunk in r.iter_bytes():
        process(chunk)
```

### Client API (Session-Based)

For connection reuse, cookie persistence, and configuration sharing across requests.

**`httpx.Client(**kwargs)`** — Synchronous client with context manager support.

```python
with httpx.Client(base_url="https://api.example.com", timeout=10.0) as client:
    r = client.get("/users")
    r = client.post("/users", json={"name": "Alice"})
```

Key constructor parameters:
- `auth: AuthTypes | None` — Default authentication
- `params: QueryParamTypes | None` — Default query parameters
- `headers: HeaderTypes | None` — Default headers (auto-includes `Accept`, `Accept-Encoding`, `Connection`, `User-Agent`)
- `cookies: CookieTypes | None` — Default cookies
- `timeout: TimeoutTypes` — Default timeout (default: 5 seconds)
- `follow_redirects: bool` — Auto-follow redirects (default: False)
- `max_redirects: int` — Maximum redirect chain length (default: 20)
- `base_url: URL | str` — Base URL for relative request URLs
- `trust_env: bool` — Use environment variables for proxy/SSL config (default: True)
- `default_encoding: str | Callable` — Default text encoding (default: "utf-8")
- `event_hooks: Mapping[str, list[Callable]]` — Request/response event hooks
- `transport: BaseTransport | None` — Custom transport
- `app: Callable | None` — WSGI/ASGI app for direct testing (auto-selects transport)
- `proxy: ProxyTypes | None` — Proxy URL
- `verify: ssl.SSLContext | str | bool` — SSL verification
- `http2: bool` — Enable HTTP/2 (default: False)
- `limits: Limits` — Connection pool limits

Client methods mirror the top-level API: `client.request()`, `client.get()`, `client.post()`, `client.put()`, `client.patch()`, `client.delete()`, `client.head()`, `client.options()`, `client.stream()`. Additional methods:

- `client.send(request, *, stream=False) -> Response` — Send a pre-built `Request` instance
- `client.build_request(method, url, **kwargs) -> Request` — Build a `Request` without sending
- `client.close()` — Close the client and release connections
- `client.is_closed` — Property, True if client is closed

**`httpx.AsyncClient(**kwargs)`** — Async client with `async with` support.

```python
async with httpx.AsyncClient() as client:
    r = await client.get("https://api.example.com/data")
```

Same constructor parameters and methods as `Client`, but all request methods are `async`. Additional async methods: `client.aclose()`.

### Request and Response Models

**`httpx.Request`** — Represents an HTTP request.
```python
req = httpx.Request("POST", "https://example.com/api", json={"key": "value"})
req.method        # "POST"
req.url           # URL("https://example.com/api")
req.headers       # Headers(...)
req.content       # bytes (raises RequestNotRead if stream not consumed)
req.read()        # bytes — consume and return body
req.aread()       # async bytes — consume and return body
req.stream        # SyncByteStream | AsyncByteStream
req.extensions    # dict
```

**`httpx.Response`** — Represents an HTTP response.
```python
r = httpx.get("https://api.example.com/data")
r.status_code     # int (200, 404, etc.)
r.headers         # Headers (case-insensitive multi-dict)
r.text            # str — decoded response body
r.content         # bytes — raw response body
r.json()          # Any — parse JSON response
r.html            # str — response body as HTML
r.encoding        # str — detected or set encoding
r.url             # URL — final URL after redirects
r.request         # Request — the originating request
r.elapsed         # timedelta — request duration
r.history         # list[Response] — redirect chain
r.links           # dict[str, dict] — parsed Link headers
r.is_success      # bool — 2xx status
r.is_redirect     # bool — 3xx status
r.is_client_error # bool — 4xx status
r.is_server_error # bool — 5xx status
r.raise_for_status()  # raises HTTPStatusError on 4xx/5xx
r.read()           # bytes — consume and return body
r.aread()          # async bytes
r.iter_bytes()     # Iterator[bytes] — stream body in chunks
r.iter_text()      # Iterator[str] — stream decoded text
r.iter_lines()     # Iterator[str] — stream lines
r.aiter_bytes()    # AsyncIterator[bytes]
r.aiter_text()     # AsyncIterator[str]
r.aiter_lines()    # AsyncIterator[str]
r.close()          # Close the response stream
r.aclose()         # Async close
r.next()           # Response — follow redirect (if next_request is set)
```

### Headers

**`httpx.Headers`** — Case-insensitive multi-dict for HTTP headers.
```python
h = httpx.Headers({"Content-Type": "application/json", "Accept": "text/html"})
h["content-type"]           # "application/json" (case-insensitive)
h.get("x-custom")           # None (no KeyError)
h.get_list("set-cookie")    # list[str] — all values for a key
h.get_list("accept", split_commas=True)  # split comma-separated values
h.multi_items()             # list[tuple[str, str]] — all items, duplicates preserved
h.raw                       # list[tuple[bytes, bytes]] — raw byte pairs
h.encoding                  # str — detected encoding (ascii, utf-8, iso-8859-1)
h.update({"X-New": "value"})
h.copy()
```

### Cookies

**`httpx.Cookies`** — Mutable mapping wrapping `http.cookiejar.CookieJar`.
```python
c = httpx.Cookies()
c.set("session", "abc123", domain="example.com", path="/")
c["session"]                # "abc123"
c.get("missing", "default") # "default"
c.delete("session")
c.clear()                   # Clear all
c.extract_cookies(response) # Load Set-Cookie headers from response
c.set_cookie_header(request) # Set Cookie header on request
```

### URL and Query Parameters

**`httpx.URL`** — Full RFC 3986 URL representation.
```python
url = httpx.URL("https://user:pass@example.com:8080/path?q=1#frag")
url.scheme      # "https"
url.username    # "user"
url.password    # "pass"
url.host        # "example.com" (unicode, lowercased)
url.raw_host    # b"example.com" (IDNA-encoded bytes)
url.port        # 8080 (int) or None for default ports
url.path        # "/path"
url.query       # b"q=1"
url.fragment    # "frag"
url.raw_path    # b"/path?q=1"
url.is_ssl      # bool
url.is_absolute_url  # bool
url.copy_with(scheme="http")  # URL — modified copy
url.join("/other")            # URL — resolve relative
url.params                    # QueryParams — parsed query
```

**`httpx.QueryParams`** — Multi-dict for URL query parameters.
```python
q = httpx.QueryParams("a=1&b=2&a=3")
q["a"]           # "1" (first value)
q.get_list("a")  # ["1", "3"] (all values)
q.update("c=4")
```

### Authentication

**`httpx.BasicAuth(username, password)`** — HTTP Basic authentication.
```python
auth = httpx.BasicAuth("user", "pass")
client = httpx.Client(auth=auth)
# Or per-request:
httpx.get("https://example.com", auth=("user", "pass"))
```

**`httpx.DigestAuth(username, password)`** — HTTP Digest authentication with automatic nonce/cnonce/opaque handling.

**`httpx.NetRCAuth(file=None)`** — Authentication from `.netrc` files.

**`httpx.FunctionAuth(func)`** — Custom authentication via a callable `func(request) -> request`.

**`httpx.Auth`** — Base class for custom auth schemes. Override `auth_flow(request)` (generator-based), `sync_auth_flow(request)`, or `async_auth_flow(request)`.

### Configuration

**`httpx.Timeout(timeout, *, connect, read, write, pool)`** — Per-operation timeout configuration.
```python
httpx.Timeout(5.0)                          # 5s on all operations
httpx.Timeout(5.0, connect=10.0)            # 10s connect, 5s elsewhere
httpx.Timeout(None, connect=5.0)            # 5s connect only
httpx.Timeout(5.0, pool=None)               # No pool timeout
```

**`httpx.Limits(max_connections, max_keepalive_connections, keepalive_expiry)`** — Connection pool limits.
```python
httpx.Limits(max_connections=100, max_keepalive_connections=20, keepalive_expiry=5.0)
```

**`httpx.Proxy(url, *, auth, headers)`** — Proxy configuration.
```python
httpx.Proxy("http://proxy.example.com:8080")
httpx.Proxy("socks5://proxy.example.com:1080")  # Requires socks extra
```

**`httpx.create_ssl_context(verify, cert, trust_env) -> ssl.SSLContext`** — SSL context factory using certifi.

### Transports

**`httpx.HTTPTransport(**kwargs)`** — Default sync transport wrapping httpcore. Supports `verify`, `cert`, `http2`, `proxy`, `limits`, `retries`, `uds`, `local_address`.

**`httpx.AsyncHTTPTransport(**kwargs)`** — Default async transport.

**`httpx.ASGITransport(app, *, raise_app_exceptions, root_path, client, app_state)** — Direct-to-ASGI transport for testing.

**`httpx.WSGITransport(app, *, script_name, remote_addr, raise_app_exceptions, send_extensions)** — Direct-to-WSGI transport for testing.

**`httpx.MockTransport(handler)`** — Test transport with a callable handler `handler(request) -> Response`.

### Exception Hierarchy

```
HTTPError
├── RequestError
│   ├── TransportError
│   │   ├── TimeoutException
│   │   │   ├── ConnectTimeout
│   │   │   ├── ReadTimeout
│   │   │   ├── WriteTimeout
│   │   │   └── PoolTimeout
│   │   ├── NetworkError
│   │   │   ├── ConnectError
│   │   │   ├── ReadError
│   │   │   ├── WriteError
│   │   │   └── CloseError
│   │   ├── ProtocolError
│   │   │   ├── LocalProtocolError
│   │   │   └── RemoteProtocolError
│   │   ├── ProxyError
│   │   └── UnsupportedProtocol
│   ├── DecodingError
│   └── TooManyRedirects
└── HTTPStatusError
InvalidURL
CookieConflict
StreamError
├── StreamConsumed
├── StreamClosed
├── ResponseNotRead
└── RequestNotRead
```

### Status Codes

**`httpx.codes`** — Namespace of HTTP status code constants:
```python
httpx.codes.OK              # 200
httpx.codes.CREATED         # 201
httpx.codes.NOT_FOUND       # 404
httpx.codes.INTERNAL_SERVER_ERROR  # 500
```

### CLI Interface

```bash
httpx https://example.com                    # GET request
httpx -m POST -j '{"key":"val"}' https://... # POST with JSON
httpx -h "Authorization: Bearer tok" https://... # Custom headers
httpx --http2 https://example.com            # HTTP/2
httpx --follow-redirects https://...         # Follow redirects
httpx --download -o output.bin https://...   # Download to file
httpx --offline https://example.com          # Print request without sending
```

### Event Hooks

Register callbacks for request/response lifecycle events:
```python
def log_request(request):
    print(f"Request: {request.method} {request.url}")

def log_response(response):
    print(f"Response: {response.status_code}")

client = httpx.Client(event_hooks={
    "request": [log_request],
    "response": [log_response],
})
```

### Integration Patterns

**Testing WSGI apps directly:**
```python
from myapp import application
with httpx.Client(app=application, base_url="http://testserver") as client:
    r = client.get("/api/health")
    assert r.status_code == 200
```

**Testing ASGI apps directly:**
```python
from myapp import application
async with httpx.AsyncClient(app=application, base_url="http://testserver") as client:
    r = await client.get("/api/health")
    assert r.status_code == 200
```

**Mocking HTTP in tests:**
```python
def mock_handler(request):
    return httpx.Response(200, json={"status": "ok"})

client = httpx.Client(transport=httpx.MockTransport(mock_handler))
r = client.get("https://any-url.com/")
assert r.json() == {"status": "ok"}
```

**Streaming large responses:**
```python
with httpx.stream("GET", "https://example.com/large-file") as r:
    with open("output.bin", "wb") as f:
        for chunk in r.iter_bytes(chunk_size=8192):
            f.write(chunk)
```

**Async concurrent requests:**
```python
import asyncio
async def fetch_all():
    async with httpx.AsyncClient() as client:
        tasks = [client.get(f"https://api.example.com/item/{i}") for i in range(10)]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]
```