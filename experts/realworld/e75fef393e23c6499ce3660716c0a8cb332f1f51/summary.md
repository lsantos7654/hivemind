# RealWorld — Summary

## Repository Purpose and Goals

RealWorld (also known as "Conduit") is the canonical exemplar project for demonstrating how to build a real-world, full-featured web application. It defines a standard API specification, shared CSS theme, frontend HTML templates, backend endpoint requirements, and test suites that any implementation must satisfy. The guiding principle is: **any frontend implementation must work interchangeably with any backend implementation**, because all implementations adhere to the same API contract.

The project was created to go beyond "Todo" apps, which are too simple to teach real application architecture. The Conduit app is a Medium.com-like social blogging platform featuring user authentication, article CRUD, comments, favorites, user follows, tag filtering, and pagination — complex enough to meaningfully exercise a framework's strengths and idioms.

## Key Features and Capabilities

**Shared API Specification (OpenAPI 3.1.0)**
- A fully specified REST API at `specs/api/openapi.yml` covering all Conduit operations
- JWT-based authentication (token passed in the `Authorization: Token <jwt>` header)
- Resources: Users, Profiles, Articles, Comments, Tags, Favorites, and Feed

**API Test Suite (Hurl + Bruno)**
- Authoritative Hurl tests at `specs/api/hurl/*.hurl` covering happy paths and error scenarios for all resources
- Auto-generated Bruno collection derived from the Hurl source of truth
- Backends are considered "spec-compliant" only if they pass the full Hurl test suite
- Tests cover: auth, articles, comments, favorites, feed, profiles, tags, pagination, error handling, and cross-user authorization

**Frontend E2E Test Suite (Playwright)**
- Shared TypeScript/Playwright tests at `specs/e2e/*.spec.ts` that any frontend implementation can run
- Tests cover: authentication, articles CRUD, social features (follow/unfollow, feed), comments, settings, navigation, null field handling, XSS security basics, and error handling
- Implementations extend a base Playwright config from `specs/e2e/playwright.base.ts`
- Two operating modes: `API_MODE` (connects to the hosted demo backend at `api.realworld.show`) and fullstack mode (tests frontend+backend together)

**Shared CSS Theme**
- A single CSS file at `assets/theme/styles.css` that all frontend implementations share for identical UI/UX

**Documentation Site (Astro + Starlight)**
- Full specification docs at `docs/` built with Astro and the Starlight theme
- Covers frontend templates, routing, styles, API integration guide, backend endpoints, error handling, CORS, and testing

**Selector Contract**
- `specs/e2e/SELECTORS.md` documents every CSS class, HTML attribute, route, and `window.__conduit_debug__` interface that frontend implementations must provide for the shared tests to pass

## Primary Use Cases and Target Audience

- **Framework authors and implementers** building new frontend or backend implementations of Conduit to demonstrate their framework's strengths
- **Developers evaluating frameworks** using the CodebaseShow listings to compare how the same app is built in React, Angular, Vue, Django, Rails, etc.
- **Backend developers** who need a well-specified API contract with an automated test suite to validate compliance
- **Frontend developers** who need a realistic, full-featured app specification including routing, auth state management, pagination, and social features

## High-Level Architecture Overview

The repository is **not** an implementation itself — it is the **specification hub**. It contains:

```
specs/
  api/          ← Backend API specification: OpenAPI YAML, Hurl tests, Bruno collection
  e2e/          ← Frontend E2E test suite: Playwright specs, helper utilities
assets/
  theme/        ← Shared CSS for all frontend implementations
  media/        ← Logo and promotional images
docs/           ← Documentation site (Astro + Starlight)
Makefile        ← Dev commands for docs and Bruno generation
```

Backend implementations expose the REST API defined in `specs/api/openapi.yml` and must pass the Hurl test suite. Frontend implementations render the Conduit UI matching the HTML templates in the docs, use the shared CSS, and must pass the Playwright E2E test suite.

The hosted public backend lives at `https://api.realworld.show/api` and can be used by any frontend implementation during development or testing.

## Related Projects and Dependencies

- **CodebaseShow** (`codebase.show/projects/realworld`) — directory of all 100+ implementations
- **RealWorld Starter Kit** — GitHub template for creating new implementations
- **Demo site** — `demo.realworld.show` (Angular frontend + hosted backend)
- **Nitro + Prisma + Zod backend** — reference spec-compliant TypeScript backend
- **Django Ninja backend** — reference spec-compliant Python backend
- **Hurl** — HTTP testing tool used for API test suite (`hurl.dev`)
- **Bruno** — API client used for interactive test collection (`usebruno.com`)
- **Playwright** — E2E testing framework for frontend tests
- **Astro + Starlight** — Documentation site build system
- **Bun** — JavaScript runtime used for docs build and Bruno generation scripts
