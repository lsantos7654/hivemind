# curl_cffi — Code Structure

## Annotated Directory Tree

```
curl_cffi/                         ← top-level repo root
├── curl_cffi/                     ← Python package (installed)
│   ├── __init__.py                ← Public namespace / re-exports all public symbols
│   ├── __main__.py                ← Enables `python -m curl_cffi` (delegates to CLI)
│   ├── __version__.py             ← Version metadata; reads libcurl version at import
│   ├── _asyncio_selector.py       ← Windows-only: selector-thread shim for ProactorEventLoop
│   ├── _wrapper.so                ← (generated) CFFI compiled extension — not in VCS
│   ├── aio.py                     ← AsyncCurl: curl_multi + asyncio integration
│   ├── cli/                       ← curl-cffi command-line tool
│   │   ├── __init__.py            ← Argument parser, main() entry point
│   │   ├── doctor.py              ← `doctor` subcommand: prints diagnostic info
│   │   ├── output.py              ← Coloured/plain output formatting for CLI responses
│   │   ├── parse.py               ← Request-item parsing (HTTPie-style key=value syntax)
│   │   ├── request.py             ← `handle_request()` — executes a single CLI request
│   │   └── run.py                 ← `run` subcommand: HAR / .http file replay
│   ├── const.py                   ← (auto-generated) IntEnum classes for all curl constants
│   ├── curl.py                    ← Low-level Curl and CurlMime wrappers
│   ├── py.typed                   ← PEP 561 marker (typed package)
│   ├── requests/                  ← High-level requests-like API
│   │   ├── __init__.py            ← Public surface + module-level HTTP verbs
│   │   ├── cookies.py             ← Cookies, CurlMorsel: cookie jar management
│   │   ├── errors.py              ← RequestsError alias
│   │   ├── exceptions.py          ← Full exception hierarchy + CurlECode→exception map
│   │   ├── headers.py             ← Headers: case-insensitive, multi-value dict
│   │   ├── impersonate.py         ← BrowserType enum, ExtraFingerprints, TLS/extension maps
│   │   ├── models.py              ← Request and Response data classes
│   │   ├── session.py             ← Session, AsyncSession, BaseSession, RetryStrategy
│   │   ├── utils.py               ← set_curl_options() — the central config function
│   │   └── websockets.py          ← WebSocket, AsyncWebSocket, WsCloseCode, retry policy
│   └── utils.py                   ← CurlCffiWarning, config_warnings(), is_pro()
│
├── ffi/                           ← C glue code for CFFI
│   ├── cdef.c                     ← CFFI declarations (function prototypes, structs)
│   ├── shim.c                     ← _curl_easy_setopt() shim (works around varargs)
│   └── shim.h                     ← Header for shim.c
│
├── scripts/                       ← Build-time utilities
│   ├── build.py                   ← ffibuilder definition; downloads libcurl-impersonate
│   ├── bump_version.sh            ← Release version bumping script
│   ├── download_curl.sh           ← Helper script for downloading curl source
│   ├── generate_consts.py         ← Regenerates curl_cffi/const.py from curl headers
│   └── homebrew.py                ← Homebrew formula generation helper
│
├── tests/
│   ├── unittest/                  ← Fast unit tests (no network); run via `make test`
│   ├── integration/               ← Integration tests (require network / test servers)
│   └── threads/                   ← Thread-safety and concurrency tests
│
├── docs/                          ← Sphinx documentation source
├── examples/                      ← Usage example scripts
├── benchmark/                     ← Performance comparison scripts
├── assets/                        ← Sponsor images for README
├── Formula/                       ← Homebrew formula
├── .github/                       ← GitHub Actions CI/CD workflows
├── .githooks/                     ← Git hooks (lint/format pre-commit)
├── Makefile                       ← Developer convenience targets
├── pyproject.toml                 ← PEP 517/518 project metadata + tool config
├── setup.py                       ← Minimal setup.py for abi3 wheel tagging + cffi_modules
├── libs.json                      ← Architecture → libcurl-impersonate download mapping
├── MANIFEST.in                    ← sdist manifest
└── AGENTS.md / skills/            ← AI agent instructions for contributors
```

## Module and Package Organization

The package is split into two tiers:

### Tier 1 — Low-level (`curl_cffi/curl.py`, `curl_cffi/aio.py`, `curl_cffi/const.py`)

Direct Python wrappers around the libcurl C API. Consumers that need fine-grained control can use these directly but are expected to manage curl handles and options manually.

### Tier 2 — High-level (`curl_cffi/requests/`)

A `requests`-compatible façade that hides curl handle management, option setting, response parsing, cookie management, and retry logic. Most users interact exclusively with this layer.

## Main Source Files and Their Roles

### `curl_cffi/curl.py`

- **`Curl`** — Wraps a `curl_easy_*` handle. Provides:
  - `setopt(option, value)` — Translates Python values to C types and calls `_curl_easy_setopt()`.
  - `getinfo(option)` — Reads post-response metrics.
  - `impersonate(target, default_headers)` — Calls `curl_easy_impersonate()` (the impersonate-fork extension).
  - `perform()` — Executes the request, ensures CA cert is set.
  - `ws_recv()`, `ws_send()`, `ws_close()` — WebSocket frame I/O.
  - `duphandle()` — Creates a shallow clone for streaming responses.
  - `reset()` — Resets options without reallocating the handle.
  - Pre-allocated CFFI buffers for WebSocket I/O (`_ws_recv_buffer`, etc.).
- **`CurlMime`** — Wraps `curl_mime_*` for multipart form uploads.
- **CFFI callbacks** — `buffer_callback`, `write_callback`, `read_callback`, `read_buffer_callback`, `debug_function` defined with `@ffi.def_extern()` for libcurl to call back into Python.

### `curl_cffi/aio.py`

- **`AsyncCurl`** — Wraps `curl_multi_*` to integrate with asyncio's event loop via `add_reader`/`add_writer`. Uses the `curl_multi_socket_action` API:
  - `timer_function` CFFI callback: schedules `process_data` via `loop.call_later`.
  - `socket_function` CFFI callback: registers/removes asyncio readers/writers per socket fd.
  - `process_data()`: called when a fd is ready; drives `curl_multi_socket_action` and resolves futures via `curl_multi_info_read`.
  - `add_handle(curl)` returns an `asyncio.Future` that resolves when the transfer completes.
  - Windows workaround: `_asyncio_selector.py` adds selector-based `add_reader`/`add_writer` to ProactorEventLoop.

### `curl_cffi/const.py`

Auto-generated from curl headers by `scripts/generate_consts.py`. Contains `IntEnum` classes:
- `CurlOpt` — All `CURLOPT_*` constants (628 entries).
- `CurlInfo` — All `CURLINFO_*` constants.
- `CurlECode` — All `CURLcode` error codes.
- `CurlMOpt` — Multi-handle options (`CURLMOPT_*`).
- `CurlHttpVersion`, `CurlFollow`, `CurlSslVersion`, `CurlWsFlag` — Smaller enums.

### `curl_cffi/requests/session.py`

The largest file (~1400 lines). Contains:
- **`BaseSession[R]`** — Generic base holding all session-level defaults (headers, cookies, auth, proxies, impersonation target, retry strategy, etc.). Implements `_parse_response()` which reads all `CurlInfo` fields after a perform.
- **`Session(BaseSession)`** — Synchronous session. Uses `threading.local()` for a per-thread `Curl` handle. `_request_once()` manages streaming vs. non-streaming paths. Retry loop in `request()`. Optional eventlet/gevent thread integration.
- **`AsyncSession(BaseSession)`** — Async session. Maintains a `asyncio.LifoQueue` pool of `Curl` handles (size: `max_clients`, default 10). `_request_once()` runs `curl.perform` in a thread executor and awaits the future.
- **`RetryStrategy`** dataclass — `count`, `delay`, `jitter`, `backoff` ("linear" | "exponential").
- **`ProxySpec`** TypedDict — Keys: `all`, `http`, `https`, `ws`, `wss`.

### `curl_cffi/requests/utils.py`

- **`set_curl_options()`** — The central function (~600 lines) that takes all request parameters and calls `curl.setopt()` for each one. Handles URL construction (with query params, base_url, quoting), header merging, cookie serialization, authentication, proxy routing, impersonation (calls `curl.impersonate()` and optionally sets `ExtraFingerprints` options), HTTP version, streaming queue setup, and timeout.

### `curl_cffi/requests/impersonate.py`

- **`BrowserTypeLiteral`** — Union of all supported browser version strings.
- **`BrowserType`** — `str, Enum` version of the same (deprecated, kept for compatibility).
- **`ExtraFingerprints`** / **`ExtraFpDict`** — Fine-grained TLS and HTTP/2/3 knobs.
- **`normalize_browser_type()`** — Maps aliases (`"chrome"`, `"safari"`, etc.) to versioned targets.
- **`toggle_extension()`** — Maps TLS extension IDs to `CurlOpt` calls for enabling/disabling individual TLS extensions.
- **`TLS_CIPHER_NAME_MAP`**, **`TLS_EXTENSION_NAME_MAP`**, **`TLS_EC_CURVES_MAP`**, **`TLS_VERSION_MAP`** — Lookup tables used when parsing JA3 strings.

### `curl_cffi/requests/websockets.py`

~1929 lines. Contains:
- **`WebSocket`** — Synchronous WebSocket client. Uses a background thread, `select()`-based polling, and callback hooks (`on_message`, `on_error`, `on_open`, `on_close`).
- **`AsyncWebSocket`** — Async WebSocket client. Producer/consumer model with separate `_recv_loop` and `_send_loop` asyncio tasks. Supports frame coalescing, backpressure (`recv_queue_size`, `send_queue_size`), and `WebSocketRetryStrategy`.
- **`BaseWebSocket`** — Shared state (`_curl`, `autoclose`, `closed`, etc.).
- **`WsCloseCode`** — IntEnum of WebSocket close codes per IANA registry.
- **`WebSocketError`**, **`WebSocketClosed`**, **`WebSocketTimeout`** — Exception hierarchy.
- **`WebSocketRetryStrategy`** — Dataclass for retry policy on receive failures.

### `curl_cffi/requests/models.py`

- **`Response`** — Holds all response data. Properties: `text`, `encoding`, `charset`, `charset_encoding`. Methods: `json()`, `raise_for_status()`, `iter_content()`, `iter_lines()`, `aiter_content()`, `aiter_lines()`, `acontent()`, `atext()`, `markdown()` (optional). Streaming is implemented via a `queue.Queue` / `asyncio.Queue` filled by callbacks.
- **`Request`** — Simple struct: `url`, `headers`, `method`, `body`.

### `curl_cffi/cli/`

- `__init__.py` — `argparse`-based CLI. Subcommands: HTTP verbs (GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS/TRACE/QUERY), `run`, `doctor`.
- `request.py` — `handle_request()`: builds and executes a session request from parsed CLI args, hands off to `output.py`.
- `run.py` — `handle_run()`: reads `.http`/`.har` files, replays them through a `Session`.
- `parse.py` — HTTPie-style `key=value`, `key:=json`, `Header:Value`, `+cookie=value`, `@file` item parsing.
- `output.py` — Formats and prints the response (rich-colored or plain text).
- `doctor.py` — Prints platform, Python, libcurl version, impersonate targets, and other diagnostic info.

## Code Organization Patterns

- **CFFI callbacks** are defined at module level with `@ffi.def_extern()` in both `curl.py` and `aio.py`. This is required by CFFI's ABI mode.
- **Generic response type** — `BaseSession[R]` and `Session[R]` use a `TypeVar R bound=Response` so users can pass a custom `response_class` and get typed return values.
- **TypedDict for parameters** — `RequestParams`, `StreamRequestParams`, `BaseSessionParams`, `ProxySpec` are all `TypedDict` under `TYPE_CHECKING`, with runtime stubs that satisfy Python's type system without overhead.
- **Thread-local curl handles** — `Session` defaults to `use_thread_local_curl=True`, creating a fresh `Curl` per thread. This avoids locks while making the session thread-safe for most use cases.
- **Async curl pool** — `AsyncSession` maintains a `LifoQueue` of `Curl` handles (LIFO = better connection reuse). When the pool is exhausted, `await pop_curl()` blocks the coroutine.
