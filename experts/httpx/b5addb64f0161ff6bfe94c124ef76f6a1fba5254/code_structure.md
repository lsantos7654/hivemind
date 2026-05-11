## Code Structure

### Top-Level Directory Layout

```
httpx/
├── .github/                  # CI workflows (GitHub Actions)
├── docs/                     # MkDocs documentation source
│   ├── advanced/             # Advanced usage guides (clients, auth, SSL, proxies, etc.)
│   ├── img/                  # Documentation images
│   └── overrides/            # MkDocs Material theme overrides
├── httpx/                    # Main source package
│   ├── __init__.py           # Public API surface — re-exports all public symbols
│   ├── __version__.py        # Version string (0.28.1)
│   ├── _api.py               # Top-level convenience functions (get, post, put, etc.)
│   ├── _auth.py              # Authentication classes (BasicAuth, DigestAuth, etc.)
│   ├── _client.py            # Client, AsyncClient, BaseClient — core orchestration
│   ├── _config.py            # Timeout, Limits, Proxy, create_ssl_context
│   ├── _content.py           # ByteStream, content encoding/decoding helpers
│   ├── _decoders.py          # Content-Encoding decoders (gzip, deflate, brotli, zstd)
│   ├── _exceptions.py        # Exception hierarchy (HTTPError, TransportError, etc.)
│   ├── _main.py              # CLI entry point (click + rich)
│   ├── _models.py            # Headers, Request, Response, Cookies
│   ├── _multipart.py         # Multipart form data encoding
│   ├── _status_codes.py      # HTTP status code constants (codes.OK, codes.NOT_FOUND, etc.)
│   ├── _transports/          # Transport abstraction layer
│   │   ├── __init__.py       # Re-exports all transport classes
│   │   ├── base.py           # BaseTransport, AsyncBaseTransport — protocol interfaces
│   │   ├── default.py        # HTTPTransport, AsyncHTTPTransport — wraps httpcore
│   │   ├── asgi.py           # ASGITransport — direct-to-ASGI app transport
│   │   ├── wsgi.py           # WSGITransport — direct-to-WSGI app transport
│   │   └── mock.py           # MockTransport — callable-based test transport
│   ├── _types.py             # Type aliases (AuthTypes, HeaderTypes, CookieTypes, etc.)
│   ├── _urlparse.py          # Custom URL parser (RFC 3986 compliant)
│   ├── _urls.py              # URL and QueryParams classes
│   ├── _utils.py             # Internal utility functions
│   └── py.typed              # PEP 561 marker for type checking
├── tests/                    # Test suite (pytest)
│   ├── conftest.py           # Shared fixtures (ASGI app, TLS certs, uvicorn server)
│   ├── common.py             # Shared test utilities
│   ├── concurrency.py        # Async concurrency helpers
│   ├── fixtures/             # Test fixture data
│   ├── client/               # Client-level tests
│   │   ├── test_async_client.py
│   │   ├── test_auth.py
│   │   ├── test_client.py
│   │   ├── test_cookies.py
│   │   ├── test_event_hooks.py
│   │   ├── test_headers.py
│   │   ├── test_properties.py
│   │   ├── test_proxies.py
│   │   ├── test_queryparams.py
│   │   └── test_redirects.py
│   ├── models/               # Model-level tests
│   │   ├── test_cookies.py
│   │   ├── test_headers.py
│   │   ├── test_queryparams.py
│   │   ├── test_requests.py
│   │   ├── test_responses.py
│   │   ├── test_url.py
│   │   ├── test_whatwg.py
│   │   └── whatwg.json
│   ├── test_api.py           # Top-level API function tests
│   ├── test_asgi.py          # ASGI transport tests
│   ├── test_auth.py          # Authentication tests
│   ├── test_config.py        # Timeout/Limits/Proxy config tests
│   ├── test_content.py       # Content encoding tests
│   ├── test_decoders.py      # Content-Encoding decoder tests
│   ├── test_exceptions.py    # Exception hierarchy tests
│   ├── test_exported_members.py  # Public API surface validation
│   ├── test_main.py          # CLI tests
│   ├── test_multipart.py     # Multipart encoding tests
│   ├── test_status_codes.py  # Status code tests
│   ├── test_timeouts.py      # Timeout behavior tests
│   ├── test_utils.py         # Utility function tests
│   └── test_wsgi.py          # WSGI transport tests
├── scripts/                  # Build/release scripts
├── mkdocs.yml                # MkDocs configuration
├── pyproject.toml            # Project metadata, build config, tool configs
├── requirements.txt          # Dev/test dependencies
├── CHANGELOG.md              # Release history
├── LICENSE.md                # BSD-3-Clause
└── README.md                 # Project README
```

### Module Organization and Key Files

**`httpx/__init__.py`** — The public API surface. Re-exports all public symbols from internal modules via wildcard imports (`from ._api import *`, etc.) and defines the `__all__` list with 100+ entries. Also provides a fallback `main()` function for when CLI dependencies are not installed. Sets `__module__` to `"httpx"` on all exported symbols for clean repr output.

**`httpx/_api.py`** — The top-level convenience API. Provides module-level functions `request()`, `get()`, `post()`, `put()`, `patch()`, `delete()`, `head()`, `options()`, and the `stream()` context manager. Each function creates a temporary `Client` instance, sends the request, and returns a `Response`. The `stream()` function is a context manager that yields a `Response` with an unread body for streaming consumption.

**`httpx/_client.py`** — The core orchestration layer (2019 lines). Contains `BaseClient` (shared configuration: auth, headers, cookies, timeout, base_url, event_hooks, trust_env, default_encoding), `Client` (synchronous HTTP client with `__enter__`/`__exit__` context manager support), and `AsyncClient` (async HTTP client with `__aenter__`/`__aexit__`). Both implement `request()`, `get()`, `post()`, etc., plus `send()` for low-level request dispatch, `build_request()` for request construction, and `_send_handling_redirects()` / `_send_handling_auth()` for redirect and auth flows. Also contains `BoundSyncStream` and `BoundAsyncStream` which wrap transport streams to set `response.elapsed` on close, and `UseClientDefault` / `USE_CLIENT_DEFAULT` sentinel for distinguishing "unset" from `None`.

**`httpx/_models.py`** — The data model layer (1277 lines). Defines four core classes:
- `Headers` — A case-insensitive multi-dict for HTTP headers. Stores raw bytes internally (`_list` of `(raw_key, lower_key, value)` tuples). Supports `multi_items()` for duplicate headers, `get_list()` with optional comma splitting, and automatic encoding detection (ascii → utf-8 → iso-8859-1).
- `Request` — An HTTP request. Constructed with `method`, `url`, and optional `params`, `headers`, `cookies`, `content`, `data`, `files`, `json`, `stream`, `extensions`. Auto-populates `Host` and `Content-Length` headers. Supports `read()` / `aread()` for consuming the body.
- `Response` — An HTTP response. Constructed with `status_code`, `headers`, and optional `content`, `text`, `html`, `json`, `stream`, `request`, `extensions`, `history`, `default_encoding`. Provides `text`, `content`, `json()`, `html`, `raise_for_status()`, `iter_bytes()`, `iter_text()`, `iter_lines()`, `aiter_bytes()`, `aiter_text()`, `aiter_lines()`, `read()`, `aread()`, `close()`, `aclose()`, `next()` for redirect chains, `links` property for Link header parsing, and `elapsed` timedelta.
- `Cookies` — A mutable mapping wrapping `http.cookiejar.CookieJar`. Supports `extract_cookies(response)` for Set-Cookie handling, `set_cookie_header(request)` for Cookie header injection, and `set()`/`get()`/`delete()`/`clear()` with optional domain/path scoping.

**`httpx/_transports/`** — The transport abstraction layer:
- `base.py` — `BaseTransport` (sync) and `AsyncBaseTransport` (async) define the protocol: `handle_request(request) -> Response` and `handle_async_request(request) -> Response`. Both support context manager usage.
- `default.py` — `HTTPTransport` and `AsyncHTTPTransport` wrap `httpcore` connection pools. Map `httpcore` exceptions to httpx's exception hierarchy. Support `http2`, `proxy`, `verify`, `cert`, `retries`, `uds`, `local_address`, `socket_options`, `limits`, and `trust_env` parameters.
- `asgi.py` — `ASGITransport` sends requests directly to an ASGI application callable. Supports both asyncio and trio backends. Useful for testing ASGI web apps without a running server.
- `wsgi.py` — `WSGITransport` sends requests directly to a WSGI application callable. Runs the WSGI app in-process. Supports `script_name`, `raise_app_exceptions`, and `send_extensions` options.
- `mock.py` — `MockTransport` accepts a callable `handler(request) -> Response` and implements both sync and async transport interfaces. The handler can be sync or async.

**`httpx/_auth.py`** — Authentication framework (348 lines). `Auth` base class with generator-based `auth_flow(request)` pattern (yield requests, receive responses). `BasicAuth` for HTTP Basic, `DigestAuth` for HTTP Digest (with nonce/cnonce/opaque handling), `FunctionAuth` for callable-based auth, and `NetRCAuth` for `.netrc` file-based authentication.

**`httpx/_config.py`** — Configuration classes. `Timeout` with per-operation granularity (connect, read, write, pool), `Limits` for connection pool limits (max_connections, max_keepalive_connections, keepalive_expiry), `Proxy` for proxy URL configuration, and `create_ssl_context()` for SSL context creation using `certifi`.

**`httpx/_exceptions.py`** — Exception hierarchy rooted at `HTTPError`, branching into `RequestError` (transport-level errors: `TimeoutException`, `NetworkError`, `ProtocolError`, `ProxyError`, `UnsupportedProtocol`, `DecodingError`, `TooManyRedirects`) and `HTTPStatusError` (4xx/5xx responses). Also includes `InvalidURL`, `CookieConflict`, and `StreamError` subclasses (`StreamConsumed`, `StreamClosed`, `ResponseNotRead`, `RequestNotRead`). The `request_context()` context manager attaches request context to raised exceptions.

**`httpx/_content.py`** — Content encoding/decoding. `ByteStream` (in-memory bytes), `IteratorByteStream` (sync iterable), `AsyncIteratorByteStream` (async iterable). Functions `encode_request()` and `encode_response()` handle content negotiation (JSON, form data, multipart, raw bytes/text).

**`httpx/_decoders.py`** — Content-Encoding decoders for HTTP response body decompression. `IdentityDecoder`, `DeflateDecoder`, `GZipDecoder`, `BrotliDecoder` (optional), `ZStandardDecoder` (optional). `MultiDecoder` chains multiple decoders. `LineDecoder` and `TextDecoder` for text-mode streaming. `ByteChunker` and `TextChunker` for chunked transfer encoding.

**`httpx/_urls.py`** — `URL` class with full RFC 3986 support: scheme, username, password, host (unicode), raw_host (IDNA-encoded bytes), port, path, query, fragment. Supports `copy_with()`, `join()`, `__eq__` with normalization. `QueryParams` is a multi-dict for URL query parameters.

**`httpx/_types.py`** — Type aliases used throughout the public API: `URLTypes`, `QueryParamTypes`, `HeaderTypes`, `CookieTypes`, `TimeoutTypes`, `ProxyTypes`, `CertTypes`, `AuthTypes`, `RequestContent`, `ResponseContent`, `RequestData`, `RequestFiles`, `FileTypes`, `RequestExtensions`, `ResponseExtensions`. Also defines `SyncByteStream` and `AsyncByteStream` base classes.

**`httpx/_main.py`** — CLI entry point using `click` for argument parsing and `rich` for formatted output. Supports `-m/--method`, `-p/--params`, `-c/--content`, `-d/--data`, `-f/--files`, `-j/--json`, `-h/--headers`, `--cookies`, `--auth`, `--proxy`, `--timeout`, `--follow-redirects`, `--no-verify`, `--http2`, `--download`, `--max-redirects`, and `--offline` flags. Entry point registered as `httpx = "httpx:main"` in pyproject.toml.

**`httpx/_status_codes.py`** — `codes` namespace object mapping HTTP status code constants (e.g., `codes.OK` → 200, `codes.NOT_FOUND` → 404). Provides both numeric and descriptive access.

### Code Organization Patterns

- **Private-by-convention modules**: All internal modules use underscore prefixes (`_api.py`, `_client.py`, etc.) to signal they are implementation details. The public API is defined exclusively through `__init__.py` re-exports.
- **`from __future__ import annotations`** at the top of every module for PEP 604-style type hints.
- **`if typing.TYPE_CHECKING`** guards for import-time type-only dependencies to avoid circular imports.
- **Generator-based auth flow**: The `Auth.auth_flow()` pattern uses Python generators (`yield request` / `response = yield request`) for multi-step authentication (e.g., Digest auth challenge-response).
- **Transport polymorphism**: The transport layer uses a simple protocol (duck-typed `handle_request` / `handle_async_request`) rather than abstract base classes with ABC enforcement, allowing `MockTransport` to implement both sync and async in one class.
- **Stream binding**: `BoundSyncStream` / `BoundAsyncStream` wrap transport-level streams to set `response.elapsed` timing on close, decoupling timing from the transport layer.