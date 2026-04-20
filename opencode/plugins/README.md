# OpenCode plugins

Each `.js` file in this directory is a **standalone opencode TUI plugin**. When
`hivemind init` runs, `src/hivemind/provider.py:_post_init_dirs()` globs
`*.js` here, copies each file to `~/.config/opencode/tui-plugins/`, and
registers each as a `file://` entry in `~/.config/opencode/tui.json`.

## Convention

One capability per file. Each file:

- Exports `default { id, tui }` where `id` is unique across the registry (see
  `opencode/packages/opencode/src/plugin/shared.ts` — IDs must be unique).
- Uses only the public plugin API — `api.slots`, `api.theme`, `api.client`,
  `api.state`, `api.lifecycle`, `api.kv`, `api.event`. No private imports
  (`@/bus`, `effect/instance-state.ts`, etc.) — those are opencode internals
  and may break on any version bump.
- Is self-contained. No imports from sibling plugins. If two plugins need to
  share logic, factor it into `opencode/plugins/utils/` (created on demand,
  not speculatively).
- Returns whatever it built from its slot render function; does not hold
  state across `Instance.dispose()` (which tears down the plugin instance).
- Cleans up via `api.lifecycle.onDispose(unregister)`.

## Do NOT add to `plugins/`

Server-side plugins (those exporting `server` instead of `tui`) must not live
here. OpenCode's config loader auto-scans `~/.config/opencode/{plugin,plugins}/`
and loads everything it finds as a *server* plugin, which fails the validator
for TUI-only plugins. That's why we install to `tui-plugins/` instead of
`plugins/`.

If you need a server-side plugin later, we'll introduce a separate
`opencode/server-plugins/` directory with its own install path.

## Current plugins

| File | Slot(s) | Purpose |
|---|---|---|
| `branding.js` | `home_logo` | HIVEMIND ASCII art on the home screen |
| `connection-indicator.js` | `home_footer`, `sidebar_footer` | Shows whether the TUI is standalone, attached to the hivemind server, or attached to a remote server |

## Adding a new plugin

1. Create `opencode/plugins/<your-plugin>.js`.
2. Give it a unique `id` (convention: `hivemind-<feature>`).
3. Register into one or more slots via `api.slots.register(...)`.
4. Run `uv run hivemind init` — the new plugin is picked up automatically.
