// Hivemind connection-state indicator for the OpenCode TUI.
// Detects whether the TUI was launched bare (`opencode`), attached to the
// hivemind-managed server (`opencode attach http://127.0.0.1:4096`), or
// attached to some other remote server, and renders a bullet + label in the
// home-screen footer and the persistent session sidebar footer.
// Installed to ~/.config/opencode/tui-plugins/ by `hivemind init`.
import { createElement, insert, spread } from "@opentui/solid"
import { existsSync, readFileSync } from "node:fs"
import { homedir } from "node:os"
import { join } from "node:path"

const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "::1", "0.0.0.0"])

function readManagedServer() {
  const path = join(homedir(), ".cache", "hivemind", "server.json")
  try {
    if (!existsSync(path)) return null
    return JSON.parse(readFileSync(path, "utf8"))
  } catch {
    return null
  }
}

function extractAttachUrl(argv) {
  for (let i = 0; i < argv.length - 1; i++) {
    const cur = argv[i]
    if (cur === "attach" || cur === "--attach") {
      const next = argv[i + 1]
      if (typeof next === "string" && next.startsWith("http")) return next
    }
  }
  return null
}

function detectConnection(argv) {
  const url = extractAttachUrl(argv)
  if (!url) {
    return { mode: "standalone", label: "standalone (in-process)", detail: "" }
  }

  let host = ""
  let port = ""
  try {
    const u = new URL(url)
    host = u.hostname
    port = u.port
  } catch {
    return { mode: "standalone", label: "standalone (in-process)", detail: "" }
  }

  const managed = readManagedServer()
  if (managed && host === managed.hostname && port === String(managed.port)) {
    return { mode: "hivemind", label: "connected (hivemind)", detail: `${host}:${port}` }
  }

  const hostPort = port ? `${host}:${port}` : host
  if (LOOPBACK_HOSTS.has(host)) {
    return { mode: "remote", label: "connected (local server)", detail: hostPort }
  }
  return { mode: "remote", label: "connected (remote)", detail: hostPort }
}

function buildIndicator(theme, state) {
  const row = createElement("box")
  spread(row, { flexDirection: "row", gap: 1 }, true)

  const bulletChar = state.mode === "standalone" ? "○" : "●"
  const bulletColor =
    state.mode === "hivemind" ? theme.success
    : state.mode === "remote" ? theme.warning
    : theme.textMuted

  const bullet = createElement("text")
  spread(bullet, { fg: bulletColor, selectable: false }, true)
  insert(bullet, bulletChar)
  insert(row, bullet)

  const labelText = state.detail ? `${state.label} ${state.detail}` : state.label
  const label = createElement("text")
  spread(label, { fg: theme.textMuted, selectable: false }, true)
  insert(label, labelText)
  insert(row, label)

  return row
}

export default {
  id: "hivemind-connection",
  tui: async (api) => {
    // Connection state is fixed for the lifetime of the TUI (attach vs standalone
    // is determined at launch). Detected from process.argv because the SDK
    // client on api.client does not publicly expose its baseUrl.
    const state = detectConnection(process.argv)

    const unregister = api.slots.register({
      slots: {
        home_footer() {
          return buildIndicator(api.theme.current, state)
        },
        sidebar_footer() {
          return buildIndicator(api.theme.current, state)
        },
      },
    })
    api.lifecycle.onDispose(unregister)
  },
}
