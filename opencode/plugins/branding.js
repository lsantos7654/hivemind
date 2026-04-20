// Hivemind branding plugin for OpenCode TUI.
// Renders the HIVEMIND ASCII art in the home-screen logo slot.
// Installed to ~/.config/opencode/tui-plugins/ by `hivemind init`.
import { createElement, insert, spread } from "@opentui/solid"

const LOGO_LINES = [
  "    __  _______    __________  ________   ______",
  '   / / / /  _/ |  / / ____/  |/  /  _/ | / / __ \\',
  "  / /_/ // / | | / / __/ / /|_/ // //  |/ / / / /",
  " / __  // /  | |/ / /___/ /  / // // /|  / /_/ /",
  "/_/ /_/___/  |___/_____/_/  /_/___/_/ |_/_____/",
]

export default {
  id: "hivemind-branding",
  tui: async (api) => {
    const unregister = api.slots.register({
      slots: {
        home_logo() {
          const theme = api.theme.current
          const container = createElement("box")
          for (const line of LOGO_LINES) {
            const row = createElement("box")
            spread(row, { flexDirection: "row" }, true)
            const text = createElement("text")
            spread(text, { fg: theme.primary, attributes: 1, selectable: false }, true)
            insert(text, line)
            insert(row, text)
            insert(container, row)
          }
          return container
        },
      },
    })
    api.lifecycle.onDispose(unregister)
  },
}
