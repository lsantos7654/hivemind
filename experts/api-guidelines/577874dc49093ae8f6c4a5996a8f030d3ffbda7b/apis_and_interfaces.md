# Microsoft REST API Guidelines — APIs and Interfaces

This repository defines REST API design guidelines, not a code library. "APIs and interfaces" here refers to the REST API patterns, schemas, and conventions prescribed by the guidelines themselves.

---

## URL Patterns

### Standard Resource URL Pattern (`azure/Guidelines.md`)

```text
https://<tenant>.<region>.<service>.<cloud>/<service-root>/<resource-collection>/<resource-id>
```

Example:
```text
https://blobstore.azure.net/contoso.com/account1/container1/blob2
```

Direct endpoint variant:
```text
https://<tenant>-<service-root>.<service>.<cloud>/...
```

### Action URL Patterns

Resource action:
```text
https://.../<resource-collection>/<resource-id>:<action>?<input parameters>
```
Example: `https://.../users/Bob:grant?access=read`

Collection action:
```text
https://.../<resource-collection>:<action>?<input parameters>
```
Example: `https://.../users:grant?access=read`

### API Versioning

Every request must include `api-version` as a required query parameter:
```text
PUT https://service.azure.com/users/Jeff?api-version=2021-06-04
```
Version format: `YYYY-MM-DD` for GA, `YYYY-MM-DD-preview` for preview.

---

## HTTP Method Conventions

| Method | Use Case | Success Status |
|--------|----------|---------------|
| GET (collection) | List resources | 200 OK |
| GET (resource) | Read resource | 200 OK |
| PUT | Create or replace whole resource | 200 OK or 201 Created |
| PATCH (JSON Merge Patch) | Create or modify resource | 200 OK or 201 Created |
| POST (create) | Create resource (service-assigned ID) | 201 Created + Location header |
| POST (action) | Invoke action | 200 OK |
| DELETE | Remove resource | 204 No Content |
| PUT/POST/DELETE (async) | Initiate long-running operation | 202 Accepted |

---

## Error Response Schema

All Azure REST APIs must return errors in this structure (`azure/Guidelines.md`):

```json
{
  "error": {
    "code": "InvalidPasswordFormat",
    "message": "Human-readable description",
    "target": "target of error",
    "details": [
      {
        "code": "...",
        "message": "..."
      }
    ],
    "innererror": {
      "code": "PasswordTooShort",
      "minLength": 6
    }
  }
}
```

**ErrorResponse** object:
| Property | Type | Required | Description |
|----------|------|:--------:|-------------|
| `error` | ErrorDetail | ✓ | Top-level error, `code` must match `x-ms-error-code` header |

**ErrorDetail** object:
| Property | Type | Required | Description |
|----------|------|:--------:|-------------|
| `code` | String | ✓ | Server-defined error code string |
| `message` | String | ✓ | Human-readable error description |
| `target` | String | | Field or path that caused the error |
| `details` | ErrorDetail[] | | Array of sub-errors |
| `innererror` | InnerError | | More specific error information |

**Required headers on error responses:**
- `x-ms-error-code` — string error code (part of API contract, must not change)

---

## Collections Response Schema

```json
{
  "value": [
    { "id": "Item 01", "etag": "\"abc\"", "price": 99.95, "size": "Medium" },
    { "id": "Item 99", "etag": "\"def\"", "price": 59.99, "size": "Large" }
  ],
  "nextLink": "{opaqueUrl}"
}
```

Rules:
- Top-level array field named `value` (preferred)
- `nextLink` is an absolute URL for the next page; omit entirely on the last page; never set to null
- Each item must include `id` and `etag` (if ETags are supported)

### Query Parameters for Collections

| Parameter | Type | Description |
|-----------|------|-------------|
| `filter` | string | OData-like filter expression |
| `orderby` | string array | Sort expressions (asc/desc) |
| `skip` | integer | Offset into collection (min 0) |
| `top` | integer | Max resources to return (min 1) |
| `maxpagesize` | integer | Max resources per page |
| `select` | string array | Fields to return |
| `expand` | string array | Related resources to inline |

Filter expression examples:
```text
GET /products?filter=price lt 10.00
GET /products?filter=name eq 'Milk' and price lt 2.55
GET /products?filter=(name eq 'Milk' or name eq 'Eggs') and price lt 2.55
```

Filter operators: `eq`, `ne`, `gt`, `ge`, `lt`, `le`, `and`, `or`, `not`, `( )`

---

## Long-Running Operation (LRO) Patterns

### PUT LRO (Create/Replace with async processing)

Request:
```text
PUT /UrlToResourceBeingCreated?api-version=<api-version>
Operation-Id: <optionalStatusMonitorResourceId>

<JSON Resource body>
```

Response:
```text
201 Created
Operation-Id: <statusMonitorResourceId>
Operation-Location: https://operations/<operation-id>?api-version=<api-version>

<JSON Resource body>
```

### DELETE LRO

Request:
```text
DELETE /UrlToResourceBeingDeleted?api-version=<api-version>
Operation-Id: <optionalStatusMonitorResourceId>
```

Response:
```text
202 Accepted
Operation-Id: <statusMonitorResourceId>
Operation-Location: https://operations/<operation-id>
```

### POST Action LRO

Request:
```text
POST /UrlToExistingResource:<action>?api-version=<api-version>
Operation-Id: <optionalStatusMonitorResourceId>

<JSON Action parameters>
```

Response:
```text
202 Accepted
Operation-Id: <statusMonitorResourceId>
Operation-Location: https://operations/<operation-id>

<JSON Status Monitor Resource>
```

### Status Monitor Schema

Returned by GET on the `operation-location` URL:

| Property | Type | Required | Description |
|----------|------|:--------:|-------------|
| `id` | string | ✓ | Unique operation ID |
| `kind` | string enum | ✓* | Kind of operation (required for polymorphic monitors) |
| `status` | string enum | ✓ | `NotStarted`, `Running`, `Succeeded`, `Failed`, `Canceled` |
| `error` | ErrorDetail | | Present if `status == "Failed"` |
| `result` | object | | Present if `status == "Succeeded"` and operation is an action (POST/PUT) |

Poll the status monitor:
```text
GET <operation-endpoint>/<operation-id>?api-version=<api-version>
```

Response includes `retry-after` header (seconds to wait before next poll) if not yet complete.

---

## Conditional Request Headers (ETags)

| Header | Direction | Purpose |
|--------|-----------|---------|
| `ETag` | Response | Resource version tag (escaped quotes: `"\"abc\""`) |
| `If-Match` | Request | Execute only if ETag matches |
| `If-None-Match` | Request | Execute only if ETag does NOT match (or `*` for existence check) |
| `If-Modified-Since` | Request | Cache freshness check |
| `If-Unmodified-Since` | Request | Optimistic concurrency check |

Conditional request behavior:

| Operation | Header | Value | Result |
|-----------|--------|-------|--------|
| PATCH/PUT | `If-None-Match` | `*` | Create if not exists, `412` if exists |
| PATCH/PUT | `If-Match` | ETag value | Update if matches, `412` if not |
| DELETE | `If-Match` | ETag value | Delete if matches, `412` if not |
| GET | `If-None-Match` | ETag value | `304` if unchanged, `200` with body if changed |

---

## Repeatability Headers (Idempotent POST)

```text
Repeatability-Request-ID: <GUID>
Repeatability-First-Sent: <RFC 7231 date>
```

Response:
```text
Repeatability-Result: accepted | rejected
```

The tracked time window must be at least 5 minutes.

---

## Standard Response Headers

| Header | Direction | Description |
|--------|-----------|-------------|
| `x-ms-request-id` | Response | Globally unique request correlation GUID |
| `x-ms-client-request-id` | Both | Optional caller-provided correlation GUID |
| `x-ms-error-code` | Response | String error code (API contract) |
| `azure-deprecating` | Response | Semicolon-delimited deprecation notices |
| `operation-location` | Response | Absolute URL of LRO status monitor |
| `operation-id` | Response | ID of LRO status monitor resource |
| `ETag` | Response | Resource version tag |
| `last-modified` | Response | Last modification timestamp (RFC 7231) |
| `retry-after` | Response | Seconds to wait before retrying |
| `content-type` | Both | e.g., `application/json`, `application/merge-patch+json` |

---

## Deprecation Notification Header

```text
azure-deprecating: <description> will retire on <date> (<url>); <description2> will retire on <date2> (<url2>)
```

Example:
```text
azure-deprecating: API version 2009-27-07 will retire on 2022-12-01 (https://azure.microsoft.com/updates/video-analyzer-retirement);TLS 1.0 & 1.1 will retire on 2020-10-30 (https://azure.microsoft.com/updates/...)
```

---

## JSON Conventions

**Field naming:** camelCase for all JSON field names. Do not upper-case acronyms.

**Null values:** Services must NOT send null-valued fields in responses. Omit the field instead. For PATCH requests using JSON Merge Patch, `null` instructs deletion of the field.

**Date/time:** RFC 3339 format in JSON body (`YYYY-MM-DDTHH:mm:ss.sssZ`). RFC 7231 IMF-fixdate in HTTP headers (`Sun, 06 Nov 1994 08:49:37 GMT`).

**Durations:** Use fixed time intervals with the unit in the property name (e.g., `backupTimeInMinutes`, `ttlSeconds`).

**UUIDs:** RFC 4122 format — `123e4567-e89b-12d3-a456-426614174000` (no curly braces, case-insensitive).

**Integers:** Must be in range -2⁵³+1 to +2⁵³-1 (JSON number limits).

**Polymorphic types:** Must include a `kind` discriminator field. Example:
```json
{
  "kind": "rectangle",
  "x": 100,
  "y": 50,
  "width": 10,
  "length": 24
}
```

**Extensible enums** — mark with `"modelAsString": true` in `x-ms-enum`:
```json
"createdByType": {
  "type": "string",
  "enum": ["User", "Application", "ManagedIdentity", "Key"],
  "x-ms-enum": {
    "name": "createdByType",
    "modelAsString": true
  }
}
```

---

## String Offset/Length Schema

When returning substring positions, include all three encodings:
```json
{
  "offset": {
    "utf8": 12,
    "utf16": 12,
    "codePoint": 11
  },
  "length": {
    "utf8": 5,
    "utf16": 5,
    "codePoint": 5
  }
}
```

---

## Bring Your Own Storage (BYOS) Request Schema

```json
{
  "input": {
    "location": "https://mycompany.blob.core.windows.net/documents/english/?<sas token>",
    "delimiter": "/",
    "extensions": [".bmp", ".jpg", ".tif", ".png"],
    "lastModified": "Wed, 21 Oct 2015 07:28:00 GMT"
  },
  "output": {
    "location": "https://mycompany.blob.core.windows.net/documents/spanish/?<sas token>",
    "delimiter": "/"
  }
}
```

---

## Microsoft Graph API Conventions

Graph APIs follow OData conventions. Key differences from Azure guidelines:

- URLs use `/v1.0/` or `/beta/` version segment (not `api-version` query parameter)
- Resource IDs are exposed as `id` string properties
- Collection items must have durable `id` values
- All identifiers use `lowerCamelCase`
- Navigation properties express relationships between resources
- `$filter`, `$select`, `$expand`, `$orderby` query parameters use `$` prefix (unlike Azure guidelines which prohibit `$` prefix)
- OData `@odata.type` annotations used for type information

Example Graph URL:
```text
GET https://graph.microsoft.com/v1.0/teamwork/devices/0f3ce432-e432-0f3c-32e4-3c0f32e43c0f
```

Graph collection response:
```json
{
  "value": [
    {
      "id": "0f3ce432-e432-0f3c-32e4-3c0f32e43c0f",
      "@odata.type": "#microsoft.graph.teamworkDevice",
      "deviceType": "CollaborationBar",
      ...
    }
  ]
}
```
