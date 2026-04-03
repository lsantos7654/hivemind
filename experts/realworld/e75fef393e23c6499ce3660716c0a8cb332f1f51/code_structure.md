# RealWorld — Code Structure

## Annotated Directory Tree

```
realworld/
├── README.md                          # Project overview and implementation links
├── CONTRIBUTING.md                    # Contribution guidelines and commit message format
├── LICENSE                            # MIT license
├── Makefile                           # Build commands (Bruno generation + docs)
├── .gitignore
├── .github/
│   ├── CODEOWNERS                     # Maintainer assignments
│   ├── dependabot.yml                 # Automated dependency updates
│   ├── workflows/
│   │   ├── deploy-docs.yml            # CI: build and deploy docs site
│   │   ├── bruno-check.yml            # CI: verify Bruno collection is in sync with Hurl
│   │   ├── codeql.yml                 # Security code scanning
│   │   └── spammy-guardian.yml        # Anti-spam bot for issues/PRs
│   └── ISSUE_TEMPLATE/
│       ├── BUG_REPORT.yml
│       └── FEATURE_REQUEST.yml
│
├── assets/
│   ├── theme/
│   │   └── styles.css                 # Shared Conduit CSS theme (all frontends use this)
│   └── media/
│       ├── default-avatar.svg         # Default avatar used when user.image is null
│       ├── conduit-logo.svg           # Conduit brand logo
│       ├── conduit-logo.svg.generate.ts  # Script to regenerate the logo
│       ├── realworld-logo.svg         # RealWorld brand logo
│       ├── realworld-logo.png         # PNG version
│       ├── realworld-dual-mode.png    # Screenshot used in README
│       ├── frameworks.svg             # Frameworks collage graphic in README
│       ├── stacks_hr.gif              # Animated stacks gif
│       ├── spacer-1669x257.gif        # Spacer gif
│       └── end.png                    # End graphic
│
├── specs/
│   ├── api/                           # Backend API specification and tests
│   │   ├── openapi.yml                # OpenAPI 3.1.0 spec (source of truth for API shape)
│   │   ├── README.md                  # How to run API tests locally
│   │   ├── run-api-tests-hurl.sh      # Run the Hurl test suite against a backend
│   │   ├── run-api-tests-bruno.sh     # Run the Bruno test suite against a backend
│   │   ├── hurl-to-bruno.js           # Code generator: converts Hurl to Bruno format
│   │   ├── hurl/                      # Hurl test files (SOURCE OF TRUTH for API tests)
│   │   │   ├── auth.hurl              # User registration, login, get/update user tests
│   │   │   ├── articles.hurl          # Article CRUD, tag handling, update behavior
│   │   │   ├── comments.hurl          # Comment create, list, delete, selective deletion
│   │   │   ├── favorites.hurl         # Favorite/unfavorite article tests
│   │   │   ├── feed.hurl              # Personalized feed with follow/pagination
│   │   │   ├── pagination.hurl        # Article list pagination (limit/offset)
│   │   │   ├── profiles.hurl          # Get profile, follow/unfollow
│   │   │   ├── tags.hurl              # Get tags endpoint
│   │   │   ├── errors_auth.hurl       # Auth error cases (empty fields, duplicates)
│   │   │   ├── errors_articles.hurl   # Article error cases (missing auth, validation)
│   │   │   ├── errors_authorization.hurl  # Cross-user 403 cases
│   │   │   ├── errors_comments.hurl   # Comment error cases
│   │   │   ├── errors_profiles.hurl   # Profile error cases (404, missing auth)
│   │   │   └── run-hurl-tests.sh      # Internal runner used by the outer script
│   │   └── bruno/                     # Bruno collection (auto-generated from Hurl)
│   │       ├── bruno.json             # Bruno collection metadata
│   │       ├── collection.bru         # Collection-level variables and auth
│   │       ├── environments/
│   │       │   └── local.bru          # Local environment config
│   │       ├── auth/                  # Bruno auth request files (01–20)
│   │       ├── articles/              # Bruno articles request files (01–20)
│   │       ├── comments/              # Bruno comments request files (01–13)
│   │       ├── favorites/             # Bruno favorites request files (01–09)
│   │       ├── feed/                  # Bruno feed request files (01–12)
│   │       ├── pagination/            # Bruno pagination request files (01–07)
│   │       ├── profiles/              # Bruno profiles request files (01–07)
│   │       ├── tags/                  # Bruno tags request files (01–04)
│   │       ├── errors-auth/           # Bruno auth error request files (01–15)
│   │       ├── errors-articles/       # Bruno article error request files (01–20)
│   │       ├── errors-authorization/  # Bruno authorization error request files (01–09)
│   │       ├── errors-comments/       # Bruno comment error request files (01–10)
│   │       └── errors-profiles/       # Bruno profile error request files (01–06)
│   │
│   └── e2e/                           # Frontend E2E test suite (Playwright)
│       ├── playwright.base.ts         # Base Playwright config for implementations to extend
│       ├── SELECTORS.md               # Selector contract: all CSS classes, routes, debug interface
│       ├── auth.spec.ts               # Auth tests: register, login, logout, session persistence
│       ├── articles.spec.ts           # Article tests: CRUD, favorites, editor, author permissions
│       ├── comments.spec.ts           # Comment tests: create, delete, display
│       ├── social.spec.ts             # Social tests: follow/unfollow, profile, feed
│       ├── settings.spec.ts           # Settings page: update profile fields
│       ├── navigation.spec.ts         # Navigation and routing tests
│       ├── url-navigation.spec.ts     # URL-based navigation tests
│       ├── null-fields.spec.ts        # Null field handling (bio, image)
│       ├── error-handling.spec.ts     # UI error handling tests
│       ├── user-fetch-errors.spec.ts  # API error interception tests
│       ├── health.spec.ts             # App health/load tests
│       ├── xss-security.spec.ts       # Basic XSS smoke tests
│       └── helpers/
│           ├── api.ts                 # Direct API helpers (register, login, create articles via API)
│           ├── auth.ts                # UI auth helpers (register/login/logout via browser)
│           ├── articles.ts            # UI article helpers (create, edit, delete, favorite)
│           ├── comments.ts            # UI comment helpers
│           ├── profile.ts             # UI profile helpers (follow/unfollow)
│           ├── config.ts              # Test config: API_MODE flag, API_BASE URL
│           ├── debug.ts               # window.__conduit_debug__ interface helpers
│           └── setup.ts               # Test setup utilities (isolated browser contexts)
│
└── docs/                              # Documentation site
    ├── astro.config.mjs               # Astro + Starlight config, sidebar nav
    ├── package.json                   # Docs dependencies (Astro, Starlight, Tailwind)
    ├── bun.lock                       # Bun lockfile
    ├── tsconfig.json                  # TypeScript config for docs
    ├── .gitignore                     # Ignores .astro, dist, node_modules
    ├── README.md                      # Docs dev instructions
    ├── public/
    │   └── favicon.svg
    ├── .vscode/
    │   ├── extensions.json
    │   └── launch.json
    ├── non-included/
    │   └── LICENSES_LOGOS.md          # Attribution for framework logos used in the repo
    └── src/
        ├── env.d.ts                   # TypeScript env declarations for Astro
        ├── tailwind.css               # Global Tailwind styles for docs site
        ├── assets/img/                # Static images for docs
        └── content/
            └── docs/
                ├── index.mdx          # Docs home page
                ├── introduction.mdx   # Getting started introduction
                ├── implementation-creation/
                │   ├── introduction.md  # How to create a new Conduit implementation
                │   ├── features.md      # Required features: JWT auth, CRUD, pagination, etc.
                │   └── expectations.md  # Quality expectations for submissions
                ├── specifications/
                │   ├── frontend/
                │   │   ├── templates.md  # Full HTML template spec for all pages
                │   │   ├── styles.md     # CSS/styling requirements
                │   │   ├── routing.md    # Required routes and URL patterns
                │   │   ├── api.md        # How frontend should call the backend API
                │   │   └── tests.md      # How to run the shared E2E tests
                │   ├── backend/
                │   │   ├── introduction.md         # Backend overview
                │   │   ├── endpoints.md            # All REST endpoints with examples
                │   │   ├── api-response-format.md  # JSON response schemas
                │   │   ├── error-handling.md        # Error format (422/401/403/404)
                │   │   ├── cors.md                  # CORS requirements
                │   │   ├── hurl.md                  # How to run Hurl tests
                │   │   ├── bruno.md                 # How to use Bruno collection
                │   │   ├── postman.md               # Legacy Postman info
                │   │   └── tests.md                 # Backend test overview
                │   └── mobile-specs/
                │       └── introduction.md          # Mobile implementation specs
                └── community/
                    ├── authors.md        # List of contributors
                    ├── resources.md      # Community links and resources
                    └── special-thanks.md # Acknowledgements
```

## Module and Package Organization

### `specs/api/` — Backend Specification Layer

The API spec has three levels:
1. **OpenAPI YAML** (`openapi.yml`) — formal machine-readable schema for all request/response shapes
2. **Hurl tests** (`hurl/*.hurl`) — executable API tests that are the authoritative behavioral spec
3. **Bruno collection** (`bruno/`) — generated from Hurl, provides an interactive GUI for the same tests

The Hurl files are the single source of truth. The Bruno collection is generated by `hurl-to-bruno.js` and kept in sync by CI.

### `specs/e2e/` — Frontend Validation Layer

Organized into:
- **Spec files** (`*.spec.ts`) — individual test scenarios, grouped by feature area
- **Helper modules** (`helpers/`) — reusable utilities that abstract UI interactions and API calls, keeping specs readable
- **Config** (`helpers/config.ts`) — a single `API_MODE` flag that switches tests between demo-backend mode and fullstack mode
- **Base config** (`playwright.base.ts`) — shared Playwright configuration that implementations extend

### `docs/src/content/docs/` — Specification Documentation

Organized by audience and topic:
- `implementation-creation/` — how to start building a new implementation
- `specifications/frontend/` — what a frontend must do (templates, routes, styles, tests)
- `specifications/backend/` — what a backend must do (endpoints, response formats, error codes, CORS)
- `community/` — contributor attribution

## Key Files and Their Roles

| File | Role |
|------|------|
| `specs/api/openapi.yml` | Machine-readable API contract — the definitive schema for all request/response shapes |
| `specs/api/hurl/*.hurl` | Executable behavioral tests — the authoritative spec for backend behavior |
| `specs/api/hurl-to-bruno.js` | Code generator — converts Hurl test files into Bruno collection format |
| `specs/e2e/SELECTORS.md` | Selector contract — documents every CSS class, route, and interface frontends must implement |
| `specs/e2e/playwright.base.ts` | Base config — implementations extend this to plug in their frontend URL and server command |
| `specs/e2e/helpers/config.ts` | Runtime mode switch — `API_MODE` and `API_BASE` control which backend E2E tests use |
| `specs/e2e/helpers/debug.ts` | Debug interface — defines and uses `window.__conduit_debug__` for programmatic auth state inspection |
| `assets/theme/styles.css` | Shared theme — all frontend implementations use this for identical UI appearance |
| `Makefile` | Task runner — commands for Bruno generation/check and docs dev/build/preview |
| `docs/astro.config.mjs` | Docs site config — Astro + Starlight + Tailwind setup with sidebar navigation |

## Code Organization Patterns

**Tests-as-specification**: The Hurl and Playwright test files are not just tests — they are the behavioral specification. A backend is only considered spec-compliant when all Hurl tests pass; a frontend is considered compliant when all Playwright tests pass.

**API_MODE dual-mode testing**: The E2E test helpers use `process.env.API_MODE` to select between two testing strategies. In `API_MODE` (default), tests call the real backend API directly for setup and use the hosted demo backend. In fullstack mode, tests only use the browser UI and test frontend+backend together.

**Numbered Bruno files**: Bruno request files are numbered sequentially (e.g., `01-register.bru`, `02-login.bru`) to enforce test execution order, since later tests depend on state created by earlier ones.

**Helper abstraction in E2E**: UI interactions are wrapped in helpers (`helpers/auth.ts`, `helpers/articles.ts`, etc.) so spec files remain readable and changes to UI selectors only need updating in one place.
