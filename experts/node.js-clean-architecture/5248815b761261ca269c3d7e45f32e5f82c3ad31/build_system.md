# node.js-clean-architecture — Build System

## Build System Type

The project uses **npm scripts** as the build orchestrator with **Babel** as the transpiler. There is no Webpack, Rollup, or other bundler — Babel is used purely to transpile ES module syntax (`import`/`export`, spread operators, async/await) to CommonJS format that Node.js can execute without the `--experimental-modules` flag.

## Configuration Files

### `package.json`
Primary build manifest. Contains all scripts, dependency declarations, and Husky hook configuration.

```json
{
  "scripts": {
    "clean":        "rm -rf build && mkdir build",
    "build-server": "babel --out-dir ./build . --source-maps --copy-files --ignore 'node_modules/**/*.js'",
    "build":        "npm run clean && npm run build-server",
    "start":        "pm2 start ./build/app.js -i ${NODE_PROCESSES} --no-daemon",
    "dev":          "NODE_ENV=development nodemon --exec babel-node app.js",
    "test":         "./node_modules/.bin/mocha --require @babel/register './tests/**/*.test.js' --timeout 30000",
    "lint":         "./node_modules/.bin/eslint --ignore-path .gitignore . --fix"
  },
  "husky": {
    "hooks": {
      "pre-commit": "npm run lint"
    }
  }
}
```

### `.babelrc`
```json
{
  "presets": ["@babel/preset-env"],
  "plugins": ["@babel/plugin-transform-runtime"]
}
```

- `@babel/preset-env` — Transpiles modern JS syntax to CommonJS-compatible output targeting the Node.js environment. Converts ES `import`/`export` to `require`/`module.exports`.
- `@babel/plugin-transform-runtime` — Replaces Babel helper inline code with imports from `@babel/runtime`, reducing bundle size and avoiding duplicate helper code across files.

### `.eslintrc.json`
- Extends `airbnb-base` (strict code style) and `prettier` (disables formatting rules that conflict with Prettier).
- Uses `babel-eslint` as the parser to support ES module syntax during linting.
- Custom rules: max line length 120 chars, allows `_id` underscore (MongoDB), no-console off (server logging), restricted syntax off (allows for...in loops).
- Prettier integration via `eslint-plugin-prettier` — Prettier violations appear as ESLint errors.

### `.prettierrc`
Standard Prettier configuration for code formatting. Enforced alongside ESLint.

## External Dependencies and Management

Dependencies are managed via **npm**. There is no lockfile committed (`package-lock.json` would be in `.gitignore`). The Dockerfile uses `yarn install --production` in the builder stage, indicating both npm and yarn are used in different contexts.

### Production Runtime Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `express` | ^4.17.1 | HTTP web framework |
| `mongoose` | ^8.8.3 | MongoDB ODM (Mongoose v8) |
| `redis` | ^3.0.2 | Redis client (callback-based v3 API) |
| `jsonwebtoken` | ^9.0.0 | JWT signing and verification |
| `bcryptjs` | ^2.4.3 | bcrypt password hashing (pure JS) |
| `@godaddy/terminus` | ^4.6.0 | Graceful shutdown + health endpoints |
| `helmet` | ^5.0.2 | HTTP security headers |
| `compression` | ^1.7.4 | gzip response compression |
| `body-parser` | ^1.19.0 | JSON and URL-encoded body parsing |
| `morgan` | ^1.10.0 | HTTP request logging (combined format) |
| `pm2` | ^6.0.9 | Node.js process manager (cluster mode) |
| `@babel/cli` | ^7.12.1 | CLI for Babel transpilation |
| `@babel/core` | ^7.12.17 | Babel core engine |
| `@babel/node` | ^7.12.17 | `babel-node` executable for development |
| `@babel/preset-env` | ^7.12.17 | Transpile preset for Node.js targets |
| `@babel/runtime` | ^7.12.18 | Runtime helpers for transform-runtime |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `@babel/plugin-transform-runtime` | ^7.12.17 | Deduplicate Babel helpers |
| `babel-eslint` | ^10.1.0 | ESLint parser for ES module syntax |
| `mocha` | ^9.2.0 | Test runner |
| `chai` | ^4.3.0 | Assertion library (BDD style) |
| `chai-http` | ^4.3.0 | HTTP assertion plugin for chai |
| `sinon` | ^9.2.4 | Test spies, stubs, mocks |
| `faker` | ^5.4.0 | Fake data generation in tests |
| `request` | ^2.88.2 | HTTP client (used in API tests for stubbing) |
| `eslint` | ^8.8.0 | JavaScript linter |
| `eslint-config-airbnb-base` | ^14.2.1 | Airbnb style guide rules |
| `eslint-config-prettier` | ^7.2.0 | Disable ESLint formatting rules |
| `eslint-plugin-import` | ^2.22.1 | ES module import linting |
| `eslint-plugin-prettier` | ^3.3.1 | Run Prettier as ESLint rule |
| `prettier` | ^2.2.1 | Code formatter |
| `husky` | ^4.3.8 | Git hooks |
| `nodemon` | ^2.0.7 | Dev server auto-restart |

## Build Targets and Commands

### Development

```sh
npm run dev
```

Runs `nodemon --exec babel-node app.js` with `NODE_ENV=development`. Nodemon watches for file changes and restarts; `babel-node` transpiles on-the-fly so no build output is needed. Port defaults to 1234.

**Prerequisites:**
- MongoDB running on `localhost:27017` (or set `MONGO_URL` env var)
- Redis running on `localhost:6379` (or set `REDIS_URL` env var)

### Production Build

```sh
npm run build
```

Runs `npm run clean && npm run build-server`:

1. `clean`: deletes the `./build` directory and recreates it empty.
2. `build-server`: runs `babel --out-dir ./build . --source-maps --copy-files --ignore 'node_modules/**/*.js'`. This transpiles all `.js` files from the project root into `./build/`, copies non-JS files as-is (`--copy-files`), and generates source maps.

The build output in `./build/` is plain CommonJS that Node.js can run natively.

### Production Start

```sh
npm run start
```

Runs `pm2 start ./build/app.js -i ${NODE_PROCESSES} --no-daemon`. The `NODE_PROCESSES` environment variable controls the cluster worker count. `--no-daemon` keeps pm2 in the foreground (required in Docker).

### Testing

```sh
npm test
```

Runs Mocha with `@babel/register` (on-the-fly transpilation for tests) against all files matching `./tests/**/*.test.js` with a 30-second timeout.

### Linting

```sh
npm run lint
```

Runs ESLint with `--fix` on the entire project (excluding `.gitignore` paths). Also triggered automatically as a Husky pre-commit hook.

## Docker Build and Deployment

### Multi-Stage Dockerfile

The Dockerfile uses a two-stage build to minimize the final image size:

**Stage 1 — builder** (`node:22.21.0-alpine`):
- Copies `package.json` and installs dependencies with `yarn install --production`.
- Copies all source files (adapters, application, config, frameworks, src, tests, babel config).
- Runs `yarn run build` to produce `./build/`.

**Stage 2 — production** (`node:22.21.0-alpine`):
- Sets `HTTP_MODE=http` and accepts `NODE_PROCESSES` build arg (default: 2).
- Installs pm2 globally.
- Copies only `./build/` and `package.json` from builder stage.
- Creates a non-root `node` user with UID/GID 9999 for security.
- `CMD ["npm", "start"]` — runs the transpiled build under pm2.
- `USER node` — runs as non-root.

### Docker Compose

```yaml
services:
  mongo-database:  # mongo:latest, port 27017, persists to ./mongo_data volume
  redis-database:  # redis (latest), port 6379
  web:             # built from Dockerfile, port 1234, depends on mongo + redis
                   # MONGO_URL and REDIS_URL set to internal service names
```

All services share the `my-net` bridge network for internal DNS resolution.

```sh
docker-compose up -d
```

### CI/CD (GitHub Actions)

`.github/workflows/node.js.yml` runs on push/PR to `master`:
- Matrix: Node.js 12.x and 14.x on `ubuntu-latest`.
- Steps: `npm install` → `npm run build` → `npm test`.

Note: The CI matrix targets Node 12/14 while the Dockerfile uses Node 22, indicating the CI configuration has not been updated alongside the Docker base image.
