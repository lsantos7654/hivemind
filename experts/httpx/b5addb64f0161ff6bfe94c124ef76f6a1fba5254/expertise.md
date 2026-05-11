### Core Architecture
- httpx is a Python HTTP client library built on top of `httpcore` (same Encode team)
- Dual API surface: synchronous (`httpx.Client`) and asynchronous (`httpx.AsyncClient`)
- `BaseClient` in `_client.py` holds shared configuration: auth, headers, cookies, timeout, base_url, event_hooks, trust_env, default_encoding
- `Client` and `AsyncClient` both inherit configuration patterns from `BaseClient` but split on sync/async transport dispatch
- Three-layer architecture: top-level API (`_api.py`), client orchestration (`_client.py`), transport abstraction (`_transports/`)
- `_models.py` defines the four core data classes: `Headers`, `Request`, `Response`, `Cookies`
- Transport layer is protocol-based (duck-typed `handle_request` / `handle_async_request`) rather than enforced via ABC
- Stream binding pattern: `BoundSyncStream` / `BoundAsyncStream` wrap transport streams to set `response.elapsed` on close
- `UseClientDefault` / `USE_CLIENT_DEFAULT` sentinel allows distinguishing "unset" from `None` for per-request parameter overrides
- `ClientState` enum tracks client lifecycle: `UNOPENED` → `OPENED` → `CLOSED`
- Private-by-convention modules: all internal modules use underscore prefix (`_api.py`, `_client.py`, etc.)
- `from __future__ import annotations` used throughout for PEP 604 style annotations
- Module `__all__` lists exported symbols; `httpx/__init__.py` is the sole public API surface
- Supports three async backends via `anyio`: asyncio, trio, and curio
- International domain name support via `idna` library

### Top-Level Convenience API (`httpx._api`)
- `httpx.request(method, url, *, params, content, data, files, json, headers, cookies, auth, proxy, timeout, follow_redirects, verify, trust_env)` — general-purpose request, returns `Response`
- `httpx.get(url, *, params, headers, cookies, auth, proxy, follow_redirects, verify, timeout, trust_env)` — HTTP GET
- `httpx.post(url, *, content, data, files, json, params, headers, cookies, auth, proxy, follow_redirects, verify, timeout, trust_env)` — HTTP POST
- `httpx.put(url, *, content, data, files, json, params, headers, cookies, auth, proxy, follow_redirects, verify, timeout, trust_env)` — HTTP PUT
- `httpx.patch(url, *, content, data, files, json, params, headers, cookies, auth, proxy, follow_redirects, verify, timeout, trust_env)` — HTTP PATCH
- `httpx.delete(url, *, params, headers, cookies, auth, proxy, follow_redirects, verify, timeout, trust_env)` — HTTP DELETE
- `httpx.head(url, *, params, headers, cookies, auth, proxy, follow_redirects, verify, timeout, trust_env)` — HTTP HEAD
- `httpx.options(url, *, params, headers, cookies, auth, proxy, follow_redirects, verify, timeout, trust_env)` — HTTP OPTIONS
- `httpx.stream(method, url, **kwargs)` — context manager yielding a `Response` with unread body for streaming
- All top-level functions create a temporary `Client`, send the request, and close the client

### Client API (`httpx._client`)
- `httpx.Client(*, auth, params, headers, cookies, timeout, follow_redirects, max_redirects, event_hooks, base_url, trust_env, default_encoding, transport, app, proxy, mounts, verify, cert, http2, limits)` — synchronous client
- `httpx.AsyncClient(*, auth, params, headers, cookies, timeout, follow_redirects, max_redirects, event_hooks, base_url, trust_env, default_encoding, transport, app, proxy, mounts, verify, cert, http2, limits)` — async client
- `client.request(method, url, **kwargs)` — general request method on both Client and AsyncClient
- `client.get()`, `client.post()`, `client.put()`, `client.patch()`, `client.delete()`, `client.head()`, `client.options()` — convenience methods
- `client.stream(method, url, **kwargs)` — streaming context manager on client instances
- `client.send(request, *, stream=False)` — send a pre-built `Request` instance directly through the transport
- `client.build_request(method, url, **kwargs)` — build and return a `Request` without sending
- `client.close()` / `client.aclose()` — close the client and release connections
- `client.is_closed` — boolean property
- `client.base_url` — `URL` base for resolving relative URLs; setter enforces trailing slash
- `client.headers` — default `Headers` (auto-includes `Accept: */*`, `Accept-Encoding`, `Connection: keep-alive`, `User-Agent`)
- `client.cookies` — default `Cookies` jar
- `client.auth` — default `Auth` instance; supports setting with tuples `("user", "pass")`
- `client.timeout` — default `Timeout` configuration
- `client.event_hooks` — dict of `"request"` and `"response"` hook lists
- `client.follow_redirects` — boolean, default False
- `client.max_redirects` — int, default 20
- `client.trust_env` — boolean, default True
- Per-host transport mounting via `mounts` dict: `{"all://": transport, "https://example.com": other_transport}`
- `client._send_handling_redirects()` — internal redirect loop, builds redirect chain in `response.history`
- `client._send_handling_auth()` — internal auth flow using generator-based `auth_flow`
- `client._get_proxy_map()` — resolves proxy configuration from explicit + environment variables
- Auto-detection of WSGI vs ASGI from `app` parameter (WSGI if callable returns non-coroutine, ASGI otherwise)
- `_same_origin(url, other)` — helper to detect cross-origin redirects
- `_is_https_redirect(url, location)` — helper for HTTP→HTTPS upgrade detection

### Request Model (`httpx._models.Request`)
- `httpx.Request(method, url, *, params, headers, cookies, content, data, files, json, stream, extensions)` — constructor
- `request.method` — uppercase string (e.g., "GET", "POST")
- `request.url` — `URL` instance
- `request.headers` — `Headers` instance
- `request.content` — bytes property, raises `RequestNotRead` if stream not consumed
- `request.read()` — consume and return body bytes; replaces stream with `ByteStream` for re-readability
- `request.aread()` — async version of `read()`
- `request.stream` — `SyncByteStream | AsyncByteStream | UnattachedStream`
- `request.extensions` — dict for transport-specific extensions
- Auto-populates `Host` header from URL if not explicitly set
- Auto-populates `Content-Length: 0` for POST/PUT/PATCH with no body and no explicit content headers
- Distinction: `content=...` auto-populates headers; `stream=...` does not (used internally for redirect/auth)
- `request.__repr__()` — returns `<Request('GET', 'https://...')>`
- `request.__getstate__()` / `request.__setstate__()` — pickle support (omits stream and extensions)

### Response Model (`httpx._models.Response`)
- `httpx.Response(status_code, *, headers, content, text, html, json, stream, request, extensions, history, default_encoding)` — constructor
- `response.status_code` — int (e.g., 200, 404)
- `response.headers` — `Headers` instance
- `response.text` — decoded string body, auto-detects encoding from Content-Type charset
- `response.content` — raw bytes body
- `response.json()` — parse JSON response body
- `response.html` — property, returns text as HTML (alias)
- `response.encoding` — str or None, the encoding used for text decoding
- `response.url` — `URL` of the final response after redirects
- `response.request` — `Request` instance that produced this response (or None)
- `response.next_request` — `Request` for next redirect, set by client when `follow_redirects=False`
- `response.elapsed` — `datetime.timedelta` of request duration
- `response.history` — `list[Response]` of previous redirect responses
- `response.links` — `dict[str, dict]` parsed from Link headers
- `response.is_success` — `status_code < 400`
- `response.is_redirect` — `300 <= status_code < 400`
- `response.is_client_error` — `400 <= status_code < 500`
- `response.is_server_error` — `500 <= status_code < 600`
- `response.is_error` — `400 <= status_code < 600`
- `response.raise_for_status()` — raises `HTTPStatusError` for 4xx/5xx responses
- `response.read()` — consume and return body bytes
- `response.aread()` — async consume and return body bytes
- `response.iter_bytes(chunk_size)` — sync iterator of body chunks
- `response.iter_text(chunk_size)` — sync iterator of decoded text chunks
- `response.iter_lines()` — sync iterator of text lines
- `response.aiter_bytes(chunk_size)` — async iterator of body chunks
- `response.aiter_text(chunk_size)` — async iterator of decoded text chunks
- `response.aiter_lines()` — async iterator of text lines
- `response.close()` / `response.aclose()` — close the response stream
- `response.next()` — follow the `next_request` redirect and return the next response
- `response.is_closed` / `response.is_stream_consumed` — stream state flags
- `response._num_bytes_downloaded` — counter updated during streaming
- `response.num_bytes_downloaded` — total bytes downloaded property
- `response.__repr__()` — returns `<Response [200 OK]>`

### Headers (`httpx._models.Headers`)
- `httpx.Headers(headers, encoding)` — case-insensitive multi-dict, accepts dicts, sequences of tuples, or another Headers
- `headers["content-type"]` — case-insensitive key lookup, concatenates duplicate values with commas
- `headers.get(key, default)` — safe lookup
- `headers.get_list(key, split_commas=False)` — return all values for a key as list; split_commas=True splits comma-separated values
- `headers.multi_items()` — list of (key, value) tuples preserving duplicate keys
- `headers.raw` — list of (bytes, bytes) raw header pairs
- `headers.encoding` — detected encoding (ascii → utf-8 → iso-8859-1)
- `headers.keys()` / `headers.values()` / `headers.items()` — standard mapping interface
- `headers.update(headers)` — merge headers, replaces existing keys
- `headers.copy()` — deep copy
- `headers.setdefault(key, value)` — set if not present
- Internally stores `_list` of `(raw_key: bytes, lower_key: bytes, value: bytes)` tuples
- `_normalize_header_key(key, encoding)` / `_normalize_header_value(value, encoding)` — coerce to bytes

### Cookies (`httpx._models.Cookies`)
- `httpx.Cookies(cookies)` — wraps `http.cookiejar.CookieJar`, accepts dict, list of tuples, another Cookies, or CookieJar
- `cookies["name"]` — get cookie value, raises KeyError if missing
- `cookies.get(name, default, domain, path)` — safe lookup with optional domain/path scoping
- `cookies.set(name, value, domain="", path="/")` — set a cookie
- `cookies.delete(name, domain, path)` — delete a cookie
- `cookies.clear(domain, path)` — clear all cookies or scoped subset
- `cookies.update(cookies)` — merge in another cookies collection
- `cookies.extract_cookies(response)` — parse Set-Cookie headers from response
- `cookies.set_cookie_header(request)` — set Cookie header on request
- `__len__()`, `__iter__()`, `__bool__()`, `__delitem__()` — standard mapping interface
- Cookie scoping via optional `domain` and `path` parameters
- Raises `CookieConflict` when `get()` finds multiple cookies with same name
- Inner `_CookieCompatRequest` and `_CookieCompatResponse` adapt httpx models to `urllib` interfaces

### URL and Query Parameters (`httpx._urls`)
- `httpx.URL(url, **kwargs)` — RFC 3986 URL; accepts string or another URL; kwargs can set scheme, host, port, path
- `url.scheme` — lowercase string (e.g., "https")
- `url.username` — string, URL-decoded
- `url.password` — string, URL-decoded
- `url.userinfo` — raw bytes `b"user:pass"` without URL decoding
- `url.host` — lowercase unicode host, IDNA-decoded (e.g., "müller.de")
- `url.raw_host` — lowercase IDNA-encoded bytes (e.g., `b"xn--mller-kva.de"`)
- `url.port` — int or None (default ports for http/https/ws/wss/ftp normalized to None)
- `url.netloc` — raw bytes `b"host:port"`
- `url.path` — string
- `url.query` — raw bytes `b"key=value"`
- `url.fragment` — string
- `url.raw_path` — raw bytes of path + query
- `url.is_ssl` — True for https/wss schemes
- `url.is_absolute_url` — True if scheme is present
- `url.copy_with(**kwargs)` — return modified copy (scheme, username, password, host, port, path, query, fragment, raw_path)
- `url.join(url)` — resolve relative URL against this one
- `url.params` — `QueryParams` parsed from query string
- `url.setdefault_params(params)` — set query parameters if not already present
- `url.__eq__()` — compares normalized forms (scheme, host, port, path)
- `url.__hash__()` — hash of normalized string
- `url.__str__()` — full URL string
- `httpx.QueryParams(*args, **kwargs)` — multi-dict for query string, accepts str, dict, list of tuples, or another QueryParams
- `queryparams["key"]` — first value for key
- `queryparams.get_list("key")` — all values for key as list
- `queryparams.update(...)` — merge parameters
- `queryparams.add(key, value)` — append a parameter
- `queryparams.setdefault(key, value)` — set if not present

### Authentication (`httpx._auth`)
- `httpx.Auth` — base class with generator-based `auth_flow(request)` protocol: yield requests, receive responses via `response = yield request`
- `auth.sync_auth_flow(request)` — sync wrapper calling into `auth_flow`, handles request/response body pre-reading
- `auth.async_auth_flow(request)` — async wrapper, same pattern
- `auth.requires_request_body` — bool flag for schemes needing request body before signing (e.g., Digest auth)
- `auth.requires_response_body` — bool flag for schemes needing response body
- `httpx.BasicAuth(username, password)` — HTTP Basic, adds `Authorization: Basic <base64>` header
- `httpx.DigestAuth(username, password)` — HTTP Digest with full nonce/cnonce/opaque/nc/qop challenge-response flow
- `DigestAuth._get_digest_values()` — parses WWW-Authenticate challenge headers
- `DigestAuth._build_digest_header()` — constructs Authorization header with MD5/SHA-256/SHA-512 hashing
- `httpx.NetRCAuth(file)` — reads credentials from `.netrc` files for matching hosts
- `httpx.FunctionAuth(func)` — wraps a callable `func(request) -> request` as an Auth
- Auth can be passed per-client (default) or per-request; per-request overrides client default
- Tuple shorthand: `auth=("username", "password")` auto-creates `BasicAuth`; `auth=("username", "password", "digest")` for DigestAuth

### Configuration (`httpx._config`)
- `httpx.Timeout(timeout, *, connect, read, write, pool)` — per-operation timeout in seconds
- `Timeout(timeout=5.0)` — uniform timeout, default if unspecified
- `Timeout(5.0, connect=10.0)` — granular: 10s connect, 5s everything else
- `Timeout(None)` — no timeouts
- `Timeout.DEFAULT_TIMEOUT_CONFIG` — sentinel for default (5 seconds)
- `httpx.Limits(*, max_connections, max_keepalive_connections, keepalive_expiry)` — connection pool limits
- `httpx.Proxy(url, *, auth, headers)` — proxy URL configuration
- `httpx.create_ssl_context(verify=True, cert=None, trust_env=True) -> ssl.SSLContext` — creates SSL context using certifi by default
- `create_ssl_context(verify=True)` — uses certifi CA bundle
- `create_ssl_context(verify=False)` — disables verification
- `create_ssl_context(verify=ssl_context)` — uses custom context
- `UnsetType` / `UNSET` — sentinel for distinguishing "not provided" from `None` in Timeout constructor

### Transport Layer (`httpx._transports`)
- `httpx.BaseTransport` — sync transport protocol with `handle_request(request) -> Response` and `close()`
- `httpx.AsyncBaseTransport` — async transport protocol with `handle_async_request(request) -> Response` and `aclose()`
- Both base classes support context manager protocol (`__enter__`/`__exit__` and `__aenter__`/`__aexit__` calling close)
- `httpx.HTTPTransport(*, verify, cert, http2, proxy, limits, retries, uds, local_address, socket_options, trust_env)` — default sync transport wrapping httpcore
- `httpx.AsyncHTTPTransport(*, verify, cert, http2, proxy, limits, retries, uds, local_address, socket_options, trust_env)` — default async transport
- Default transports map `httpcore` exceptions to httpx's exception hierarchy via `HTTPCORE_EXC_MAP`
- `httpx.ASGITransport(app, *, raise_app_exceptions, root_path, client, app_state)` — sends requests directly to an ASGI app
- `ASGITransport` auto-detects trio vs asyncio backend via sniffio
- `ASGIResponseStream` — async byte stream collecting ASGI response body chunks
- `httpx.WSGITransport(app, *, script_name, remote_addr, raise_app_exceptions, send_extensions)` — sends requests directly to a WSGI app
- `WSGIByteStream` — sync byte stream wrapping WSGI response iterable, skips leading empty chunks
- `httpx.MockTransport(handler)` — implements both sync and async transport with a callable handler; handler can be sync or async
- `MockTransport.handle_request(request)` — reads request body, calls handler, returns response
- `MockTransport.handle_async_request(request)` — async version, awaits handler if it returns a coroutine

### Exception Hierarchy (`httpx._exceptions`)
- `httpx.HTTPError` — root exception, has `.request` property (set via `request_context()`)
- `httpx.RequestError(HTTPError)` — base for errors during request issuance
- `httpx.TransportError(RequestError)` — base for transport-level errors
- `httpx.TimeoutException(TransportError)` — base timeout
- `httpx.ConnectTimeout(TimeoutException)` — connection timed out
- `httpx.ReadTimeout(TimeoutException)` — read timed out
- `httpx.WriteTimeout(TimeoutException)` — write timed out
- `httpx.PoolTimeout(TimeoutException)` — waiting for pool connection timed out
- `httpx.NetworkError(TransportError)` — base network error
- `httpx.ConnectError(NetworkError)` — connection failed
- `httpx.ReadError(NetworkError)` — read from network failed
- `httpx.WriteError(NetworkError)` — write to network failed
- `httpx.CloseError(NetworkError)` — close connection failed
- `httpx.ProtocolError(TransportError)` — protocol violation
- `httpx.LocalProtocolError(ProtocolError)` — client-side protocol violation
- `httpx.RemoteProtocolError(ProtocolError)` — server-side protocol violation
- `httpx.ProxyError(TransportError)` — proxy connection error
- `httpx.UnsupportedProtocol(TransportError)` — unsupported URL scheme
- `httpx.DecodingError(RequestError)` — content decoding (decompression) failed
- `httpx.TooManyRedirects(RequestError)` — exceeded max_redirects
- `httpx.HTTPStatusError(HTTPError)` — 4xx/5xx response, raised by `response.raise_for_status()`, has `.request` and `.response`
- `httpx.InvalidURL(Exception)` — malformed URL
- `httpx.CookieConflict(Exception)` — multiple cookies with same name in `.get()`
- `httpx.StreamError(RuntimeError)` — base stream error (programming error)
- `httpx.StreamConsumed(StreamError)` — stream already consumed
- `httpx.StreamClosed(StreamError)` — stream already closed
- `httpx.ResponseNotRead(StreamError)` — tried to access streaming content without `.read()`
- `httpx.RequestNotRead(StreamError)` — tried to access streaming request content without `.read()`
- `request_context(request)` — context manager attaching request to any `RequestError` raised within block

### Content Encoding/Decoding (`httpx._content`, `httpx._decoders`)
- `httpx.ByteStream(bytes)` — sync and async in-memory byte stream
- `IteratorByteStream(iterable)` — sync byte stream from iterable; 64KB chunk size; detects generators for StreamConsumed protection
- `AsyncIteratorByteStream(async_iterable)` — async byte stream
- `encode_request(content, data, files, json, boundary)` — returns (headers_dict, stream) for request body
- `encode_response(content, text, html, json)` — returns (headers_dict, stream) for response body
- `ContentDecoder` — base class with `decode(data) -> bytes` and `flush() -> bytes`
- `IdentityDecoder` — pass-through (no encoding)
- `DeflateDecoder` — raw deflate decompression
- `GZipDecoder` — gzip decompression via `zlib.decompressobj(wbits=16+zlib.MAX_WBITS)`
- `BrotliDecoder` — brotli decompression (optional, requires `brotli` or `brotlicffi`)
- `ZStandardDecoder` — zstandard decompression (optional, requires `zstandard`)
- `MultiDecoder` — chains multiple decoders for stacked Content-Encoding (e.g., `gzip, deflate`)
- `LineDecoder` — decodes bytes into text lines with configurable line ending
- `TextDecoder` — decodes bytes into text chunks with configurable encoding
- `ByteChunker` — chunks raw bytes for streaming with configurable chunk size
- `TextChunker` — chunks decoded text for streaming
- `SUPPORTED_DECODERS` — dict mapping Content-Encoding names to decoder classes, includes optional brotli and zstd
- `ACCEPT_ENCODING` — auto-generated Accept-Encoding header value from `SUPPORTED_DECODERS` keys (minus "identity")

### Multipart Encoding (`httpx._multipart`)
- `MultipartStream(data, files, boundary, content_type)` — generates multipart/form-data byte stream
- `_format_form_param(name, value)` — HTML5 form encoding for multipart parameters
- `_guess_content_type(filename)` — MIME type detection from file extension
- `get_multipart_boundary_from_content_type(content_type)` — extract or generate boundary string
- File upload types support: bytes, str, `Path`, file-like objects, or tuples of (filename, content, content_type)
- `_HTML5_FORM_ENCODING_REPLACEMENTS` — character replacements for HTML5 form encoding spec

### CLI (`httpx._main`)
- Entry point: `httpx` command (registered as `httpx = "httpx:main"` in pyproject.toml)
- `main()` — CLI entry point using `click` for argument parsing
- Supports `-m/--method`, `-p/--params`, `-c/--content`, `-d/--data`, `-f/--files`, `-j/--json`, `-h/--headers`, `--cookies`, `--auth`, `--proxy`, `--timeout`, `--follow-redirects`, `--no-verify`, `--http2`, `--download`, `--max-redirects`, `--offline`
- `print_help()` — formatted help output using `rich` tables
- Response display uses `pygments` for syntax-highlighted JSON/HTML
- Download progress bar via `rich.progress`
- `--offline` prints the request that would be sent without actually sending it

### Status Codes (`httpx._status_codes`)
- `httpx.codes` — namespace object with HTTP status code constants
- `codes.OK` → 200, `codes.CREATED` → 201, `codes.NO_CONTENT` → 204
- `codes.MOVED_PERMANENTLY` → 301, `codes.FOUND` → 302, `codes.NOT_MODIFIED` → 304
- `codes.BAD_REQUEST` → 400, `codes.UNAUTHORIZED` → 401, `codes.FORBIDDEN` → 403, `codes.NOT_FOUND` → 404
- `codes.INTERNAL_SERVER_ERROR` → 500, `codes.BAD_GATEWAY` → 502, `codes.SERVICE_UNAVAILABLE` → 503
- String representation via `codes.OK` returns `<HTTPStatus.OK: 200>`
- Phrase lookup via `codes.get_reason_phrase(200)` → "OK"

### Type System (`httpx._types`)
- `URLTypes = URL | str`
- `QueryParamTypes = QueryParams | Mapping | list[tuple] | str | bytes`
- `HeaderTypes = Headers | Mapping[str, str] | Mapping[bytes, bytes] | Sequence[tuple[str, str]] | Sequence[tuple[bytes, bytes]]`
- `CookieTypes = Cookies | CookieJar | dict[str, str] | list[tuple[str, str]]`
- `TimeoutTypes = float | None | tuple[float|None, ...] | Timeout`
- `ProxyTypes = URL | str | Proxy`
- `CertTypes = str | tuple[str, str] | tuple[str, str, str]`
- `AuthTypes = tuple[str|bytes, str|bytes] | Callable[[Request], Request] | Auth`
- `RequestContent = str | bytes | Iterable[bytes] | AsyncIterable[bytes]`
- `RequestData = Mapping[str, Any]`
- `FileTypes = bytes | str | IO[bytes] | tuple[str|None, FileContent] | tuple[str|None, FileContent, str|None] | tuple[str|None, FileContent, str|None, Mapping[str, str]]`
- `RequestFiles = Mapping[str, FileTypes] | Sequence[tuple[str, FileTypes]]`
- `SyncByteStream` / `AsyncByteStream` — base classes for streaming content

### Build and Development
- Build backend: hatchling with hatch-fancy-pypi-readme plugin
- Version from `httpx/__version__.py`: `"0.28.1"`
- Requires Python >= 3.9, supports up to 3.13
- Core deps: `certifi`, `httpcore==1.*`, `anyio`, `idna`
- Optional extras: `brotli`, `cli` (click, pygments, rich), `http2` (h2), `socks` (socksio), `zstd` (zstandard)
- Test runner: pytest with markers `copied_from` and `network`
- Testing against live ASGI server via uvicorn in conftest.py
- TLS testing with trustme and cryptography for certificate generation
- Lint: ruff (E, F, I, B, PIE rules), typecheck: mypy (strict), format: ruff format
- 100% test coverage target
- Docs: mkdocs-material with structure covering quickstart, advanced usage, guides, and API reference