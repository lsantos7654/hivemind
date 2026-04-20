# Hivemind × OpenCode Architecture

This doc describes the layered architecture hivemind uses to integrate with
[opencode](https://opencode.ai) without forking it. Read this when:

- Adding a new capability and deciding which layer it belongs in.
- Touching anything that crosses a layer boundary.
- Diagnosing why something works differently than expected.

## The shape

Hivemind is a **sidecar** to opencode: a separately-owned process that
attaches to the primary opencode application and extends it without modifying
core. Four layers:

```
┌───────────────────────────────────────────────────────────────────────┐
│  L1 — Hivemind Core  (Python, opencode-agnostic)                      │
│                                                                       │
│  Owns: experts, teams, knowledge docs, git, AI analysis.              │
│  Does NOT know about opencode paths, agent file format, or HTTP API.  │
│  Exports: pure Python functions returning domain objects.             │
│                                                                       │
│  Modules: experts.py, teams.py, analysis.py, git.py, models.py,       │
│           templates.py (template source), constants.py                │
└──────────────────────────────┬────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────────┐
│  L2 — Bridge  (Python + thin JS shim)                                 │
│                                                                       │
│  Owns: translation of L1 domain objects → opencode filesystem         │
│        artifacts. The Anti-Corruption Layer between hivemind's model  │
│        and opencode's config schema.                                  │
│                                                                       │
│  Touches only the public opencode surface:                            │
│   - writes to ~/.config/opencode/{agents,experts,commands,            │
│     tui-plugins}/                                                     │
│   - merges ~/.config/opencode/opencode.json (hardening, permissions,  │
│     MCP entry)                                                        │
│   - lists plugins in ~/.config/opencode/tui.json                      │
│   - POSTs /global/dispose after mutations                             │
│                                                                       │
│  Modules: provider.py, server.py, deployment.py, mcp/notify.py        │
└──────────┬───────────────────────────────────────────┬────────────────┘
           │ atomic file writes                         │ HTTP (dispose)
           ▼                                            ▼
┌───────────────────────────────────────┐   ┌─────────────────────────┐
│  L3 — Opencode Plugins  (JS, ESM)     │   │                         │
│                                       │   │   L4 — OpenCode Core    │
│  opencode/plugins/                    │   │   (unchanged)           │
│   ├── branding.js                     │   │                         │
│   ├── connection-indicator.js         │◀──┤   Treated as a          │
│   └── ... (one file per capability)   │   │   versioned external    │
│                                       │   │   contract. We never    │
│  Uses only public plugin ABI:         │   │   modify it; we depend  │
│   api.slots, api.theme, api.client,   │   │   only on:              │
│   api.state, api.lifecycle, api.kv    │   │    - PluginInput shape  │
│                                       │   │    - Hooks interface    │
│  NEVER: publishes Bus events          │   │    - public HTTP API    │
│         (not exposed), registers      │   │                         │
│         HTTP routes (not exposed),    │   │                         │
│         holds state across dispose.   │   │                         │
└───────────────────────────────────────┘   └─────────────────────────┘
```

## Layer contracts

### L1 — Hivemind Core

**Purpose:** domain model. Defines what an expert, team, or knowledge doc
*is*, independent of how opencode consumes them.

**Must do:** return plain Python domain objects (`AgentSpec`, `TeamData`,
`ProgressInfo`, etc.) from its public functions.

**Must not:** import from `provider.py` or `server.py`, hardcode opencode
paths, know the `expert-*.md` frontmatter schema, make HTTP calls to
anything opencode-specific.

**Relocate out of L1 if you find:** `~/.config/opencode`, `yaml frontmatter`,
`httpx.post("http://127.0.0.1...")`, or any mention of "agents" as a
specific opencode concept.

### L2 — Bridge

**Purpose:** Anti-Corruption Layer. Translates L1 domain objects into the
specific filesystem artifacts and HTTP calls opencode expects. Absorbs
schema drift.

**Must do:** be the *only* layer that knows opencode paths, frontmatter
format, and HTTP endpoints. Read opencode version/schema before writing;
fail fast on mismatch.

**Must not:** run domain logic (that's L1), render UI (that's L3), or
import opencode internal modules (`@/bus`, `effect/instance-state.ts`).

**When opencode schema changes:** L2 is the *only* layer that updates.

### L3 — Opencode Plugins

**Purpose:** in-process extensions of opencode's TUI. Deployed by L2 but
run inside the opencode process.

**Must do:** each plugin is one file, one capability, unique `id`, uses
only public ABI. Clean up via `api.lifecycle.onDispose`.

**Must not:** shell out directly to L1 Python (route through the hivemind
MCP server or CLI, which is L2 territory). Hold state across
`Instance.dispose()` (plugin instances are torn down per-dispose). Use
private imports (`@/bus`, etc.).

**Convention:** see `opencode/plugins/README.md`.

### L4 — Opencode Core

**Purpose:** the thing we don't touch. Treated as a versioned external API.

**Public contract hivemind depends on:**

- `packages/plugin/src/index.ts` — `PluginInput`, `Hooks` interfaces
- Public HTTP endpoints (`/global/dispose`, `/agent`, `/session/*`, …)
- File layout: `~/.config/opencode/opencode.json`, `tui.json`, `agents/`,
  `experts/`, `commands/`, `plugins/`, `tui-plugins/`

If opencode changes any of these, L2 updates to match. L3 plugins stay
resilient by only using the documented `api.*` surface.

## Boundary rules

1. **L1 imports nothing from L2, L3, or L4.** Pure domain.
2. **L3 never shells directly to L1.** Plugins invoke the hivemind CLI or
   MCP, both of which are L2 entry points.
3. **No layer hard-codes opencode's private module paths** (`@/bus`,
   `effect/instance-state.ts`, etc.). Those are internal to L4 and
   unstable.
4. **L2 has no TUI rendering logic. L3 has no domain logic.**
5. **Only L2 calls opencode HTTP endpoints.**

## Known limitations (honest pain-point map)

Three UX limitations that come from opencode's current plugin ABI:

| Pain point | Layer workaround | Requires core change? |
|---|---|---|
| Enable/disable doesn't propagate to attached TUIs instantly | L2 POSTs `/global/dispose` → full reload of each attached client. Blunt but functional. | Narrow invalidation (`Agent.reload()`) would be ideal but isn't exposed publicly. |
| Fresh TUI session shows stale experts | Resolved: L2 sequences file writes + dispose *before* a new session opens. | No. |
| `hivemind_enable_expert` from inside a session shows "Tool execution aborted" | Mitigated: dispose is deferred (500ms), fire-and-forget, after the MCP tool returns. The mutation itself completes on disk either way. | **Yes** — a scoped-dispose primitive that doesn't tear down the caller's `InstanceState` would fully fix this. Not pursued yet. |

See `/Users/santos/.claude/teams/architecture/expert-opencode/notes.md` and
`expert-architecture-center/notes.md` for the grounded audit.

## Adding a new capability — where does it go?

| If it's… | It lives in… |
|---|---|
| A new expert/team concept or schema | L1 (`src/hivemind/models.py`, `experts.py`, …) |
| A new thing hivemind writes into opencode's config dir | L2 (`src/hivemind/provider.py`) |
| A new opencode CLI command invocation | L2 (`src/hivemind/server.py`) |
| A new MCP tool exposed to opencode agents | L2 (`src/hivemind/mcp/`) |
| A new TUI slot / widget / AI-callable tool inside opencode | L3 (`opencode/plugins/<new>.js`) |
| A new opencode core behavior | Not here — open an upstream PR to opencode. |

## Scalability: registry-manifest pattern

L3 plugins scale O(files), not O(features × concerns). Each new capability:

1. One new file in `opencode/plugins/<feature>.js`.
2. Unique `id`, register into `api.slots.*`.
3. Run `uv run hivemind init` — auto-installed, auto-registered in
   `tui.json`.

Shared utilities (atomic manifest reads, CLI subprocess wrappers) land in
`opencode/plugins/utils/` **on demand** — not speculatively. If a second
plugin needs them, factor out; otherwise keep them inline.

## See also

- `opencode/plugins/README.md` — plugin-authoring conventions
- `src/hivemind/provider.py` — the L2 bridge, canonical home for opencode
  coupling
- Team notes: `~/.claude/teams/architecture/*/notes.md`
