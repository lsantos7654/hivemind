# Posting — APIs and Interfaces

## Public API (Exported from `__init__.py`)

The public Python API consists of the core data model classes and the scripting interface:

```python
from posting import (
    Auth,
    Cookie,
    Header,
    QueryParam,
    RequestBody,
    RequestModel,
    FormItem,
    Options,
    Scripts,
    Posting,       # Scripting API
)
```

These types are available for external code and for writing Posting scripts.

---

## Core Data Models (`collection.py`)

### `RequestModel`

The central data structure representing an HTTP request.

```python
class RequestModel(BaseModel):
    name: str = ""
    description: str = ""
    method: HttpRequestMethod = "GET"
    url: str = ""
    path: Path | None = None          # File path for persistence
    body: RequestBody | None = None
    auth: Auth | None = None
    headers: list[Header] = []
    params: list[QueryParam] = []
    path_params: list[PathParam] = []  # For :param placeholders in URL
    cookies: list[Cookie] = []
    posting_version: str = POSTING_VERSION
    scripts: Scripts = Scripts()
    options: Options = Options()

    # Key methods:
    def apply_template(variables: dict[str, object]) -> None
        # Substitutes $VAR / ${VAR} in url, headers, params, body, auth

    def to_httpx(client: httpx.AsyncClient) -> httpx.Request
        # Converts to httpx Request object ready to send

    def save_to_disk(path: Path) -> None
        # Serializes to YAML and writes to path

    def to_curl(extra_args: str = "") -> str
        # Converts to cURL command string
```

### `Collection`

A tree of requests organized into a directory hierarchy.

```python
class Collection(BaseModel):
    path: Path
    name: str = "__default__"
    requests: list[RequestModel] = []
    children: list[Collection] = []  # Subdirectories as sub-collections
    readme: str | None = None

    @classmethod
    def from_directory(directory: str) -> Collection
        # Loads all .posting.yaml files from a directory tree

    @classmethod
    def from_openapi_spec(path: Path, info: APIInfo) -> Collection
        # Creates a Collection from an OpenAPI spec

    def save_to_disk() -> None
    def add_request(request: RequestModel) -> None
```

### `Auth`

```python
class Auth(BaseModel):
    type: Literal["basic", "digest", "bearer_token"] | None = None
    basic: BasicAuth | None = None
    digest: DigestAuth | None = None
    bearer_token: BearerTokenAuth | None = None

    def to_httpx_auth() -> httpx.Auth | None
        # Converts to appropriate httpx.Auth subclass

class BasicAuth(BaseModel):
    username: str = ""
    password: str = ""

class DigestAuth(BaseModel):
    username: str = ""
    password: str = ""

class BearerTokenAuth(BaseModel):
    token: str = ""
```

### `RequestBody`

```python
class RequestBody(BaseModel):
    content: str | None = None
    form_data: list[FormItem] | None = None

    @property
    def content_type() -> str | None
        # Computed from content (tries JSON detection) or form_data presence

    def to_httpx_args() -> dict
        # Returns {"content": ...} or {"data": ...} for httpx
```

### `Options`

```python
class Options(BaseModel):
    follow_redirects: bool = True
    verify_ssl: bool = True
    attach_cookies: bool = True
    proxy_url: str = ""
    timeout: float = 5.0
```

### `Scripts`

```python
class Scripts(BaseModel):
    setup: str | None = None          # Path to script run before variable substitution
    on_request: str | None = None     # Path to script run before sending request
    on_response: str | None = None    # Path to script run after response received
```

### Component Models

```python
class Header(BaseModel):
    name: str = ""
    value: str = ""
    enabled: bool = True

class QueryParam(BaseModel):
    name: str = ""
    value: str = ""
    enabled: bool = True

class PathParam(BaseModel):
    name: str = ""
    value: str = ""

class Cookie(BaseModel):
    name: str = ""
    value: str = ""
    enabled: bool = True

class FormItem(BaseModel):
    name: str = ""
    value: str = ""
    enabled: bool = True
```

---

## Type Aliases (`types.py`)

```python
HttpRequestMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
VALID_HTTP_METHODS: tuple = get_args(HttpRequestMethod)

PostingLayout = Literal["horizontal", "vertical"]

CertTypes = (
    str                                          # certfile path
    | tuple[str, str | None]                     # (certfile, keyfile)
    | tuple[str, str | None, str | None]         # (certfile, keyfile, password)
)
```

---

## Scripting API (`scripts.py`)

The `Posting` class is injected into user scripts as the `posting` variable.

```python
class Posting:
    """API available in user-defined scripts."""

    request: RequestModel | None    # Current request being processed
    response: httpx.Response | None # Response (only in on_response scripts)

    @property
    def variables() -> dict[str, object]
        # Get all currently loaded variables

    def get_variable(name: str, default: object = None) -> object
        # Get a single variable by name

    def set_variable(name: str, value: object) -> None
        # Set a variable (persists for the request lifecycle)

    def clear_variable(name: str) -> None
        # Remove a single variable

    def clear_all_variables() -> None
        # Clear all runtime variables

    def notify(
        message: str,
        title: str = "",
        severity: Literal["information", "warning", "error"] = "information",
        timeout: float | None = None
    ) -> None
        # Show a notification in the TUI
```

**Script execution order:**
1. `setup` script — runs first, before variable substitution. Good for setting variables.
2. `on_request` script — runs after variable substitution, before sending. Can modify `posting.request`.
3. HTTP request is sent
4. `on_response` script — runs after response received. `posting.response` is available.

**Example script (`setup.py`):**
```python
import time

posting.set_variable("timestamp", str(int(time.time())))
posting.set_variable("auth_header", "Bearer " + posting.get_variable("API_KEY", ""))
```

**Example script (`on_response.py`):**
```python
import json

data = json.loads(posting.response.text)
posting.set_variable("last_user_id", str(data.get("id", "")))
posting.notify(f"Request completed: {posting.response.status_code}", title="Done")
```

---

## CLI Interface (`__main__.py`)

```bash
# Launch TUI (default, no subcommand needed)
posting
posting --collection /path/to/collection/dir
posting --env .env --env .env.local   # Multiple env files
posting --theme dracula
posting --layout horizontal

# Show file paths
posting locate config
posting locate collection
posting locate themes

# Import API specs
posting import openapi.yaml
posting import postman_collection.json
posting import openapi.yaml --output ./my-collection

# Show sponsors
posting sponsors
```

**Key CLI options for `posting` (default/TUI command):**
```
--collection PATH        Directory containing .posting.yaml files
--env PATH               .env file to load (repeatable)
--theme NAME             Theme name to use
--layout [horizontal|vertical]  Layout mode
--config PATH            Custom config file path
--no-cache               Disable module cache for scripts
```

---

## Import/Export APIs

### cURL Import (`importing/curl.py`)

```python
class CurlImport:
    def __init__(self, curl_command: str):
        """Parse a cURL command string."""

    # Parsed properties:
    method: HttpRequestMethod
    url: str
    headers: list[tuple[str, str]]
    body: RequestBody | None
    auth: Auth | None
    params: list[QueryParam]

    def to_request_model() -> RequestModel
        # Convert parsed data to a RequestModel
```

**Usage:**
```python
from posting.importing.curl import CurlImport

curl_cmd = "curl -X POST https://api.example.com/users -H 'Content-Type: application/json' -d '{\"name\": \"Alice\"}'"
importer = CurlImport(curl_cmd)
request = importer.to_request_model()
```

### Postman Import (`importing/postman.py`)

```python
def import_postman_spec(
    spec_path: str | Path,
    output_path: str | Path | None = None,
) -> tuple[Collection, PostmanCollection]
    # Returns (posting Collection, raw Postman model)

def create_env_file(
    path: Path,
    env_filename: str,
    variables: list[Variable],
) -> Path
    # Creates a .env file from Postman environment variables
```

**Usage:**
```python
from posting.importing.postman import import_postman_spec

collection, postman_raw = import_postman_spec(
    "MyAPI.postman_collection.json",
    output_path="./my-api-collection"
)
```

### OpenAPI Import (`importing/open_api.py`)

```python
def import_openapi_spec(spec_path: str | Path) -> Collection
    # Parses OpenAPI 3.x YAML/JSON, returns a Collection

def generate_unique_env_filename(base_name: str, server_url: str) -> str
    # Creates a unique .env filename based on spec name and server URL

def extract_server_variables(spec: dict) -> dict
    # Extracts server URL template variables from OpenAPI spec

def resolve_url_variables(url: str, variables: dict) -> str
    # Resolves {variable} placeholders in server URLs
```

---

## URL Utilities (`urls.py`)

```python
def ensure_protocol(url: str) -> str
    # Adds "http://" if no protocol is present
    # ensure_protocol("api.example.com") → "http://api.example.com"
    # ensure_protocol("https://api.example.com") → "https://api.example.com"

def extract_path_param_names(url: str) -> list[str]
    # Finds :param style placeholders in URL path
    # extract_path_param_names("/users/:id/posts/:postId") → ["id", "postId"]
    # Note: "::param" is an escape sequence for a literal colon

def substitute_path_params(url: str, params: dict[str, str]) -> str
    # Replaces :param placeholders with values
    # substitute_path_params("/users/:id", {"id": "42"}) → "/users/42"
```

---

## Variable System (`variables.py`)

```python
# Module-level singleton
VARIABLES: SharedVariables

class SharedVariables:
    def get() -> dict[str, object]
    def set(variables: dict[str, object]) -> None
    def update(new_variables: dict[str, object]) -> None

def load_variables(
    environment_files: tuple[Path, ...],
    use_host_environment: bool = True,
    avoid_cache: bool = False,
) -> dict[str, object]
    # Loads variables from .env files and optionally host environment

def substitute_variables(text: str) -> str
    # Replaces $VAR and ${VAR} using Python's string.Template

def get_variables() -> dict[str, object]
def update_variables(new_variables: dict[str, object]) -> None
```

**Variable syntax in requests:** `$VARIABLE` or `${VARIABLE}`

```yaml
# In a .posting.yaml file
url: https://${BASE_URL}/api/users/$USER_ID
headers:
  - name: Authorization
    value: Bearer $API_TOKEN
```

---

## Configuration API (`config.py`)

Settings are loaded via Pydantic Settings from `$XDG_CONFIG_HOME/posting/config.yaml`.

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        yaml_file=get_config_path(),  # from locations.py
        env_prefix="POSTING_",        # env var override: POSTING_LAYOUT=horizontal
    )

    layout: PostingLayout = "vertical"
    use_host_environment: bool = True
    theme: str = "galaxy"

    heading: HeadingSettings
    url_bar: UrlBarSettings
    response: ResponseSettings
    focus: FocusSettings
    certificate: CertificateSettings
    text_input: TextInputSettings
    command_palette: CommandPaletteSettings
    # ... more nested settings
```

**Config file format (`~/.config/posting/config.yaml`):**
```yaml
layout: horizontal
theme: monokai
use_host_environment: false

focus:
  on_startup: url
  on_response: body

response:
  prettify_json: true

certificate:
  ca_bundle: /path/to/ca-bundle.crt
  certfile: /path/to/client.crt
  keyfile: /path/to/client.key
```

**Environment variable overrides:** Any setting can be overridden via `POSTING_<SETTING>` environment variables (e.g., `POSTING_LAYOUT=horizontal`, `POSTING_THEME=dracula`).

---

## Request File Format (`.posting.yaml`)

```yaml
name: Get User by ID
description: Fetch a single user from the API
method: GET
url: https://${BASE_URL}/api/users/:id
headers:
  - name: Accept
    value: application/json
    enabled: true
  - name: Authorization
    value: Bearer $API_TOKEN
    enabled: true
params:
  - name: format
    value: json
    enabled: true
path_params:
  - name: id
    value: "42"
auth:
  type: bearer_token
  bearer_token:
    token: $API_TOKEN
options:
  follow_redirects: true
  verify_ssl: true
  timeout: 10.0
scripts:
  setup: ./setup.py
  on_request: ./before_request.py
  on_response: ./after_response.py
posting_version: "2"
```

---

## Extension Points

### Custom Themes

User themes are YAML files placed in `$XDG_DATA_HOME/posting/themes/`:

```yaml
# ~/.local/share/posting/themes/my_theme.yaml
name: My Theme
primary: "#7aa2f7"
secondary: "#bb9af7"
background: "#1a1b26"
surface: "#24283b"
error: "#f7768e"
warning: "#e0af68"
success: "#9ece6a"
accent: "#73daca"
```

### Custom Keybindings

Keybindings are defined in `config.yaml`:

```yaml
# In ~/.config/posting/config.yaml
keymap:
  send_request: ctrl+enter
  save_request: ctrl+s
  new_request: ctrl+n
  toggle_jump_mode: ctrl+o
```

### Environment Files

Any `.env` format file can be loaded:
```bash
posting --env .env --env .env.production
```

Variables are available as `$VAR` in all request fields.
