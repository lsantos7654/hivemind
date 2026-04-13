# curl_cffi — Repository Summary

## Repository Purpose and Goals

`curl_cffi` (version 0.15.1 at this commit) is a Python binding for `curl-impersonate` — a fork of libcurl that can impersonate the TLS/JA3 and HTTP/2 fingerprints of real browsers. The project is built via CFFI (C Foreign Function Interface), which lets Python call into the compiled `libcurl-impersonate` shared library with near-native performance.

The core problem it solves is **TLS fingerprinting**. Modern anti-bot systems (Cloudflare, Akamai, DataDome, etc.) inspect the TLS ClientHello and HTTP/2 SETTINGS frames sent by a client to detect automation. Standard HTTP clients (`requests`, `httpx`, `aiohttp`) advertise their own fingerprint, which bots detectors trivially flag. `curl_cffi` lets developers switch to any supported browser fingerprint simply by passing `impersonate="chrome"`.

## Key Features and Capabilities

- **Browser impersonation** — Matches the TLS (JA3/JA3N) and HTTP/2 (Akamai) fingerprints of Chrome, Safari, Firefox, Edge, Tor, and their mobile variants. The open-source release covers ~30 fingerprint targets; a commercial "pro" tier adds more.
- **Custom fingerprints** — Callers may supply raw `ja3=...` and `akamai=...` strings instead of a predefined target, enabling impersonation of arbitrary non-browser clients.
- **Extra fingerprint control** — The `ExtraFingerprints` dataclass exposes low-level TLS knobs: minimum TLS version, GREASE, extension permutation, certificate compression, delegated credentials, record size limit, HTTP/2 stream priority, and HTTP/3 signature/extension configuration.
- **HTTP/1.1, HTTP/2, and HTTP/3** — All three HTTP versions are supported. HTTP/3 (QUIC) gained fingerprint support in v0.15.0, including UDP SOCKS5 proxy tunneling.
- **Sync and async** — A synchronous `Session` backed by a thread-local `Curl` handle and an asynchronous `AsyncSession` backed by `curl_multi` with proper asyncio event-loop integration.
- **WebSocket** — Both synchronous (`WebSocket`) and asynchronous (`AsyncWebSocket`) WebSocket clients. The async client implements a producer/consumer architecture with configurable queue sizes, frame coalescing, retry policies, and backpressure.
- **requests-compatible API** — Module-level convenience functions (`get`, `post`, `put`, `patch`, `delete`, `head`, `options`) and a `Session`/`AsyncSession` interface mirror the `requests` library, reducing the migration cost.
- **Streaming** — `session.stream(...)` and `response.iter_content()` / `response.iter_lines()` provide chunked streaming for large responses or server-sent events.
- **Built-in retry** — `RetryStrategy` with linear or exponential backoff and jitter.
- **CLI** — `curl-cffi` command-line tool supporting all HTTP verbs, HAR/HTTP-file replay (`run` subcommand), and a `doctor` diagnostic subcommand.
- **Multipart uploads** — `CurlMime` wraps the `curl_mime_*` API for multipart form data.
- **Pre-compiled wheels** — Binary wheels are published for Linux (glibc/musl), macOS (x86_64/arm64), Windows (x64/arm64), Android, and free-threaded CPython 3.14t builds.

## Primary Use Cases and Target Audience

- **Web scraping / data extraction** — Developers who need to bypass TLS/bot-detection systems on sites that block common Python HTTP libraries.
- **Reverse engineering** — Security researchers or developers needing to replicate a browser's exact network handshake.
- **Browser automation replacement** — Use cases where a headless browser would be overkill and a fingerprint-matching HTTP client is sufficient.
- **High-performance async crawling** — `AsyncSession` with `curl_multi` achieves aiohttp-level throughput while supporting fingerprinting.
- **AI agent web access** — The `curl-cffi` CLI can serve as a `web_fetch` replacement for coding agents and LLM tools.
- **Scrapy integration** — Third-party adapters (`scrapy-curl-cffi`, `scrapy-impersonate`) make it easy to plug into Scrapy spiders.

## High-Level Architecture Overview

```
curl_cffi/
  _wrapper.so          ← CFFI-compiled C extension (generated at build time)
  curl.py              ← Low-level Curl / CurlMime wrappers (curl_easy_*)
  aio.py               ← AsyncCurl wrapping curl_multi with asyncio
  const.py             ← Auto-generated enums: CurlOpt, CurlInfo, CurlECode, ...
  requests/            ← High-level requests-like API layer
    session.py         ← Session / AsyncSession (main public surface)
    models.py          ← Request / Response models
    impersonate.py     ← BrowserType enum, ExtraFingerprints, TLS maps
    cookies.py         ← Cookies (http.cookiejar-based)
    headers.py         ← Headers (case-insensitive dict)
    exceptions.py      ← Exception hierarchy mirroring requests
    utils.py           ← set_curl_options() — the central option-setting routine
    websockets.py      ← WebSocket / AsyncWebSocket
  cli/                 ← curl-cffi command-line tool
ffi/
  cdef.c               ← CFFI C declarations fed to ffibuilder.cdef()
  shim.c / shim.h      ← Thin C shim that unifies curl_easy_setopt's varargs
scripts/
  build.py             ← ffibuilder definition; downloads libcurl-impersonate at build time
```

The data path for a typical request:
1. `Session.request()` → `set_curl_options()` sets all `CurlOpt` values on a `Curl` handle.
2. `Curl.perform()` / `AsyncCurl.add_handle()` drives the libcurl I/O.
3. Callbacks registered via CFFI (`buffer_callback`, `write_callback`) fill `BytesIO` buffers.
4. `BaseSession._parse_response()` reads `CurlInfo` fields to build the `Response` object.

## Related Projects and Dependencies

- **curl-impersonate** (`lexiforest/curl-impersonate`) — The patched libcurl that `curl_cffi` links against.
- **cffi** (≥2.0.0) — The Python-to-C FFI layer; required at both build and runtime.
- **certifi** (≥2024.2.2) — Default CA bundle; overridden by `SSL_CERT_FILE`, `CURL_CA_BUNDLE`, or `REQUESTS_CA_BUNDLE` environment variables.
- **orjson** (optional) — Used instead of `json.loads` for faster JSON parsing if installed.
- **rich** (optional, `curl_cffi[cli]`) — Colored CLI output.
- **readability-lxml + markdownify** (optional, `curl_cffi[extra]`) — Enables `Response.markdown()` for extracting readable text from HTML.
- **Scrapy adapters** — `scrapy-curl-cffi`, `scrapy-impersonate`, `scrapy-fingerprint`.
- **requests/httpx adapters** — `curl-adapter`, `httpx-curl-cffi`.
