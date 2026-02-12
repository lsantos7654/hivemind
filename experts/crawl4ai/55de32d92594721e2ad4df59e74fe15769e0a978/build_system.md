# Crawl4AI Build System

## Build System Type

Crawl4AI uses **modern Python packaging** with `pyproject.toml` as the primary configuration file, following [PEP 517](https://peps.python.org/pep-0517/) and [PEP 518](https://peps.python.org/pep-0518/) standards. The build backend is **setuptools** with a compatibility `setup.py` for backward compatibility.

## Configuration Files

### `pyproject.toml` - Primary Build Configuration

```toml
[build-system]
requires = ["setuptools>=64.0.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "Crawl4AI"
dynamic = ["version"]  # Version read from crawl4ai/__version__.py
requires-python = ">=3.10"
```

**Key Sections:**

1. **Dependencies** (lines 15-50): Core dependencies including:
   - `playwright>=1.49.0` - Browser automation
   - `patchright>=1.49.0` - Undetected browser support
   - `litellm>=1.53.1` - LLM integration
   - `lxml~=5.3` - HTML parsing
   - `aiohttp>=3.11.11`, `httpx>=0.27.2` - Async HTTP
   - `aiosqlite~=0.20` - Async database
   - `pydantic>=2.10` - Data validation
   - `beautifulsoup4~=4.12` - HTML parsing
   - `rank-bm25~=0.2` - Text relevance
   - `nltk>=3.9.1` - NLP utilities

2. **Optional Dependencies** (lines 61-76):
   - `[pdf]`: pypdf for PDF processing
   - `[torch]`: PyTorch, nltk, scikit-learn for ML features
   - `[transformer]`: Hugging Face models for embeddings
   - `[cosine]`: Dependencies for cosine similarity extraction
   - `[sync]`: Selenium for deprecated synchronous crawler
   - `[all]`: All optional features combined

3. **Script Entry Points** (lines 78-83):
   - `crawl4ai-setup`: Post-installation browser setup
   - `crawl4ai-doctor`: Diagnostic tool
   - `crawl4ai-download-models`: ML model downloader
   - `crawl4ai-migrate`: Database migration utility
   - `crwl`: Main CLI interface

4. **Package Discovery** (line 86):
   - Auto-discovers all `crawl4ai*` packages

5. **Package Data** (lines 88-89):
   - Includes JavaScript snippets from `js_snippet/*.js`

### `setup.py` - Backward Compatibility Wrapper

The `setup.py` file (66 lines) provides backward compatibility for older pip versions and performs post-installation setup:

**Key Functions:**
1. Creates `~/.crawl4ai/` directory structure
2. Initializes cache folders (html_content, cleaned_html, markdown_content, etc.)
3. Cleans old cache on reinstall
4. Reads version from `crawl4ai/__version__.py`
5. Delegates most configuration to `pyproject.toml`

**Directory Structure Created:**
```
~/.crawl4ai/
├── cache/
├── html_content/
├── cleaned_html/
├── markdown_content/
├── extracted_content/
└── screenshots/
```

Environment variable `CRAWL4_AI_BASE_DIRECTORY` can override the base directory location.

### `requirements.txt` - Development Requirements

Simple pinned dependencies for development environments:
```
crawl4ai
aiohttp
aiosqlite
```

### Docker Configuration

#### `Dockerfile` (130 lines)
Multi-stage build optimized for production:

**Stage 1: Base**
- Ubuntu 24.04 with Python 3.12
- Installs system dependencies (browsers, fonts, multimedia codecs)
- Sets up non-root user for security

**Stage 2: Builder**
- Installs Python dependencies in virtual environment
- Downloads Playwright browsers
- Pre-downloads NLTK data

**Stage 3: Production**
- Minimal runtime image
- Copies virtual environment and browsers
- Exposes port 11235
- Runs FastAPI server with Uvicorn

**Key Features:**
- Multi-architecture support (amd64/arm64)
- Shared memory configuration (`--shm-size=1g` recommended)
- Health check endpoint
- Non-root user execution

#### `docker-compose.yml` (50 lines)
Orchestrates the Docker deployment:

```yaml
services:
  crawl4ai:
    image: unclecode/crawl4ai:latest
    ports:
      - "11235:11235"
    environment:
      - CRAWL4AI_HOOKS_ENABLED=false  # Security: hooks disabled by default
      - DEFAULT_LLM_PROVIDER=openai/gpt-4o
    volumes:
      - ./data:/data  # Persistent storage
    shm_size: 1gb  # Required for browser stability
```

**Environment Variables:**
- `CRAWL4AI_HOOKS_ENABLED`: Enable/disable custom hooks (default: false)
- `DEFAULT_LLM_PROVIDER`: LLM provider string (e.g., "openai/gpt-4o")
- `DEFAULT_LLM_PROVIDER_TOKEN`: API token for LLM provider
- `CRAWL4_AI_BASE_DIRECTORY`: Custom base directory path

## External Dependencies Management

### Python Dependencies

**Core Dependencies (Required):**
- **Browser Automation**: playwright, patchright, tf-playwright-stealth
- **HTTP/Network**: aiohttp, httpx (with HTTP/2 support), requests
- **HTML Processing**: lxml, beautifulsoup4, cssselect
- **LLM Integration**: litellm (supports 100+ providers)
- **Data Validation**: pydantic (v2.10+)
- **Database**: aiosqlite for async SQLite
- **Utilities**: python-dotenv, xxhash, pillow, psutil, PyYAML
- **NLP**: nltk, rank-bm25, snowballstemmer
- **CLI**: click, rich (for terminal UI), humanize
- **DSL Parser**: lark
- **Security**: pyOpenSSL (>=25.3.0 for security fixes)
- **Geometry**: alphashape, shapely (for adaptive crawler)

**Optional Dependencies:**
- **PDF Support**: pypdf (replaces deprecated PyPDF2)
- **ML/AI**: torch, transformers, sentence-transformers, scikit-learn
- **Legacy**: selenium (deprecated synchronous crawler)

**Version Strategy:**
- Uses `~=` for patch-level flexibility (e.g., `lxml~=5.3` allows 5.3.x)
- Uses `>=` for libraries needing latest features (e.g., `playwright>=1.49.0`)
- Pins major versions to avoid breaking changes

### System Dependencies (Docker)

Installed via apt in Dockerfile:
```bash
# Browsers and drivers
chromium-browser
firefox-esr
webkit2gtk-driver

# Multimedia codecs
ffmpeg
libvpx7
libopus0

# Fonts (internationalization)
fonts-noto-cjk  # Chinese, Japanese, Korean
fonts-noto-color-emoji

# Development tools
git
curl
```

### Browser Dependencies

Managed by Playwright:
```bash
# Installation
playwright install chromium firefox webkit
# Or via crawl4ai-setup
crawl4ai-setup
```

**Browser Versions (as of v0.8.0):**
- Chromium: Latest stable
- Firefox: Latest stable
- WebKit: Latest stable
- Patchright (Undetected Chrome): Bundled

### ML Model Dependencies

Downloaded on-demand by `crawl4ai-download-models`:
- **NLTK Data**: punkt, stopwords, averaged_perceptron_tagger
- **HuggingFace Models**: sentence-transformers/all-MiniLM-L6-v2 (default)
- Cached in `~/.crawl4ai/models/`

## Build Targets and Commands

### Installation Commands

#### Basic Installation
```bash
pip install crawl4ai
crawl4ai-setup  # Sets up browsers and NLTK data
crawl4ai-doctor # Verifies installation
```

#### Pre-release Versions
```bash
pip install crawl4ai --pre
```

#### Development Installation
```bash
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
pip install -e .  # Editable mode
```

#### With Optional Features
```bash
pip install "crawl4ai[torch]"         # PyTorch support
pip install "crawl4ai[transformer]"   # Transformers
pip install "crawl4ai[cosine]"        # Cosine similarity
pip install "crawl4ai[pdf]"           # PDF processing
pip install "crawl4ai[all]"           # All features
```

### Build Commands

#### Build Package
```bash
python -m build  # Creates wheel and sdist in dist/
```

#### Build Docker Image
```bash
docker build -t crawl4ai:latest .
# Or with BuildKit
DOCKER_BUILDKIT=1 docker build -t crawl4ai:latest .
```

#### Multi-architecture Build
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t crawl4ai:latest .
```

### Testing Commands

#### Run Tests
```bash
pytest tests/                           # All tests
pytest tests/async_webcrawler_test.py  # Specific test file
pytest -v -s tests/                     # Verbose output
```

#### Memory Tests
```bash
python tests/memory/test_memory_usage.py
```

#### Docker Tests
```bash
python deploy/docker/tests/test_1_basic.py
python deploy/docker/tests/run_security_tests.py
```

### CLI Commands

#### Basic Crawling
```bash
crwl https://example.com                    # Simple crawl
crwl https://example.com -o markdown        # Markdown output
crwl https://example.com -o json           # JSON output
```

#### Deep Crawling
```bash
crwl https://example.com --deep-crawl bfs --max-pages 10
crwl https://example.com --deep-crawl dfs --max-depth 3
```

#### LLM Extraction
```bash
crwl https://example.com -q "Extract all product prices"
```

#### Browser Configuration
```bash
crwl https://example.com --headless false   # Show browser
crwl https://example.com --proxy http://proxy:8080
```

### Utility Commands

#### Setup and Diagnosis
```bash
crawl4ai-setup      # Install browsers and NLTK data
crawl4ai-doctor     # Check installation status
```

#### Model Management
```bash
crawl4ai-download-models  # Download ML models
```

#### Database Migration
```bash
crawl4ai-migrate    # Migrate cache database schema
```

## Deployment

### Local Development
```bash
# Clone and install in editable mode
git clone https://github.com/unclecode/crawl4ai.git
cd crawl4ai
pip install -e ".[all]"
crawl4ai-setup
```

### Docker Deployment

#### Quick Start
```bash
docker pull unclecode/crawl4ai:latest
docker run -d -p 11235:11235 --name crawl4ai --shm-size=1g unclecode/crawl4ai:latest
```

#### With Docker Compose
```bash
docker-compose up -d
```

#### Production Configuration
```yaml
services:
  crawl4ai:
    image: unclecode/crawl4ai:latest
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '2.0'
    environment:
      - CRAWL4AI_HOOKS_ENABLED=false
      - MAX_PAGES=30  # Browser pool size
    volumes:
      - crawl4ai-cache:/app/.crawl4ai
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11235/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Cloud Deployment

#### AWS ECS/Fargate
- Use official Docker image
- Configure task with at least 2GB memory
- Set `--shm-size=1gb` or use tmpfs mount

#### Google Cloud Run
- Deploy from Docker image
- Increase memory to 2GB minimum
- Set concurrency based on load

#### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: crawl4ai
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: crawl4ai
        image: unclecode/crawl4ai:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: dshm
          mountPath: /dev/shm
      volumes:
      - name: dshm
        emptyDir:
          medium: Memory
          sizeLimit: 1Gi
```

### Monitoring

The Docker deployment includes:
- **Health Check**: `/health` endpoint
- **Monitoring Dashboard**: http://localhost:11235/dashboard
- **Prometheus Metrics**: `/metrics` endpoint
- **WebSocket Streaming**: Real-time updates via WebSocket

Access monitoring:
```bash
curl http://localhost:11235/monitor/health
curl http://localhost:11235/metrics
```

### Version Numbering

Crawl4AI follows semantic versioning with pre-release identifiers:

- **Stable**: `0.8.0` (production-ready)
- **Beta**: `0.8.0b1` (feature complete, testing)
- **Alpha**: `0.8.0a1` (experimental features)
- **Dev**: `0.8.0dev1` (development builds)

Install pre-release versions:
```bash
pip install crawl4ai --pre
```

The build system is designed for ease of use, with sensible defaults for common use cases while supporting advanced configurations for production deployments.
