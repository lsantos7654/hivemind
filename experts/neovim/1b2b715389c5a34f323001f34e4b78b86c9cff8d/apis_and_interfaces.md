# Neovim APIs and Interfaces

## API Layers Overview

Neovim exposes three distinct API layers, each with different transports and use cases:

1. **Vim API** — Inherited Ex commands and Vimscript functions (`vim.cmd()`, `vim.fn.*`)
2. **Nvim C API** — C functions exposed over msgpack-RPC (`vim.api.*`)
3. **Lua API** — Pure Lua modules in the `vim.*` namespace (`vim.lsp`, `vim.treesitter`, etc.)

## The Nvim C API (msgpack-RPC)

### Transport

Neovim creates a default RPC socket on startup. Access it via:
- Unix socket (default): path in `$NVIM` environment variable
- TCP: `nvim --listen 127.0.0.1:6666`
- Embedded: `jobstart(['nvim', '--embed'], {'rpc': v:true})`

### API Type System

Defined in `src/nvim/api/private/defs.h`:

```c
typedef bool     Boolean;
typedef int64_t  Integer;
typedef double   Float;
// String: { char* data, size_t size }
// Array:  kvec
// Dict:   kvec (map)
// Object: any of the above

// Handle types (opaque integers, msgpack EXT)
typedef handle_T Buffer;
typedef handle_T Window;
typedef handle_T Tabpage;
```

Indexing: **0-based**, ranges are end-exclusive. Exceptions:
- Mark-like functions (e.g., `nvim_win_get_cursor`) use 1-based lines, 0-based columns
- Extmark functions use 0-based, end-inclusive indexing

### Global API Functions (`src/nvim/api/vim.c`)

```c
// Execute a Lua chunk
Object nvim_exec_lua(String code, Array args, Arena *arena, Error *err);

// Execute an Ex command
void nvim_command(String command, Error *err);

// Evaluate a Vimscript expression
Object nvim_eval(String expr, Arena *arena, Error *err);

// Call a function with args
Object nvim_call_function(String fn, Array args, Arena *arena, Error *err);

// Feed keys as if typed
void nvim_feedkeys(String keys, String mode, Boolean escape_ks);

// Get/set Neovim option values
Object nvim_get_option_value(String name, Dict(option) *opts, Arena *arena, Error *err);
void   nvim_set_option_value(String name, Object value, Dict(option) *opts, Error *err);

// Input handling
Integer nvim_input(String keys);
void    nvim_input_mouse(String button, String action, String modifier,
                         Integer grid, Integer row, Integer col, Error *err);

// Get current mode
Dictionary nvim_get_mode(Arena *arena);

// List open buffers/windows/tabpages
Array nvim_list_bufs(Arena *arena);
Array nvim_list_wins(Arena *arena);
Array nvim_list_tabpages(Arena *arena);

// Get/set current buffer/window/tabpage
Buffer  nvim_get_current_buf(void);
Window  nvim_get_current_win(void);
Tabpage nvim_get_current_tabpage(void);

// Context (save/restore editor state)
Dictionary nvim_get_context(Dict(context) *opts, Arena *arena, Error *err);
Object     nvim_load_context(Dictionary dict, Error *err);

// Notifications and echoing
void nvim_echo(Array chunks, Boolean history, Dict(echo_opts) *opts, Error *err);
void nvim_notify(String msg, Integer log_level, Dictionary opts, Arena *arena, Error *err);

// API introspection
Dictionary nvim_get_api_info(Arena *arena);
```

### Buffer API (`src/nvim/api/buffer.c`)

```c
// Read/write buffer lines (0-indexed, end-exclusive)
ArrayOf(String) nvim_buf_get_lines(Buffer buffer, Integer start, Integer end,
                                   Boolean strict_indexing, Arena *arena, Error *err);
void nvim_buf_set_lines(Buffer buffer, Integer start, Integer end,
                        Boolean strict_indexing, ArrayOf(String) replacement, Error *err);

// Read/write text ranges (byte-indexed)
String nvim_buf_get_text(Buffer buffer, Integer start_row, Integer start_col,
                         Integer end_row, Integer end_col, Dictionary opts,
                         Arena *arena, Error *err);
void   nvim_buf_set_text(Buffer buffer, Integer start_row, Integer start_col,
                         Integer end_row, Integer end_col,
                         ArrayOf(String) replacement, Error *err);

// Buffer metadata
Integer nvim_buf_line_count(Buffer buffer, Error *err);
String  nvim_buf_get_name(Buffer buffer, Arena *arena, Error *err);
void    nvim_buf_set_name(Buffer buffer, String name, Error *err);
Boolean nvim_buf_is_loaded(Buffer buffer);
Boolean nvim_buf_is_valid(Buffer buffer);

// Variables (b: scope)
Object nvim_buf_get_var(Buffer buffer, String name, Arena *arena, Error *err);
void   nvim_buf_set_var(Buffer buffer, String name, Object value, Error *err);
void   nvim_buf_del_var(Buffer buffer, String name, Error *err);

// Keymap
void  nvim_buf_set_keymap(Buffer buffer, String mode, String lhs, String rhs,
                          Dict(keymap) *opts, Error *err);
void  nvim_buf_del_keymap(Buffer buffer, String mode, String lhs, Error *err);
Array nvim_buf_get_keymap(Buffer buffer, String mode, Arena *arena, Error *err);
```

### Extmark API (`src/nvim/api/extmark.c`)

Extmarks are persistent buffer positions/ranges that track edits and support virtual text and decorations.

```c
// Create or update an extmark
Integer nvim_buf_set_extmark(Buffer buffer, Integer ns_id,
                             Integer line, Integer col,
                             Dict(set_extmark) *opts, Error *err);

// Get extmarks in a range
Array nvim_buf_get_extmarks(Buffer buffer, Integer ns_id,
                            Object start, Object end,
                            Dict(get_extmarks) *opts, Arena *arena, Error *err);

// Get a specific extmark
Array nvim_buf_get_extmark_by_id(Buffer buffer, Integer ns_id, Integer id,
                                  Dictionary opts, Arena *arena, Error *err);

// Delete an extmark
Boolean nvim_buf_del_extmark(Buffer buffer, Integer ns_id, Integer id, Error *err);

// Namespace management
Integer nvim_create_namespace(String name);
Dictionary nvim_get_namespaces(Arena *arena);
```

### Autocmd API (`src/nvim/api/autocmd.c`)

```c
// Create an autocmd
Integer nvim_create_autocmd(Object event, Dict(create_autocmd) *opts, Error *err);
void    nvim_del_autocmd(Integer id, Error *err);
void    nvim_clear_autocmds(Dict(clear_autocmds) *opts, Error *err);
void    nvim_exec_autocmds(Object event, Dict(exec_autocmds) *opts, Error *err);
Array   nvim_get_autocmds(Dict(get_autocmds) *opts, Arena *arena, Error *err);

// Autocommand groups
Integer nvim_create_augroup(String name, Dict(create_augroup) *opts, Error *err);
void    nvim_del_augroup_by_id(Integer id, Error *err);
void    nvim_del_augroup_by_name(String name, Error *err);
```

### UI API (`src/nvim/api/ui.c`)

```c
// Attach a remote UI
void nvim_ui_attach(Integer width, Integer height, Dictionary options, Error *err);

// Detach a remote UI
void nvim_ui_detach(Error *err);

// Resize the UI
void nvim_ui_try_resize(Integer width, Integer height, Error *err);
void nvim_ui_try_resize_grid(Integer grid, Integer width, Integer height, Error *err);

// Set UI options (e.g., "ext_linegrid", "ext_popupmenu")
void nvim_ui_set_option(String name, Object value, Error *err);

// Set focus
void nvim_ui_set_focus(Boolean gained, Error *err);
```

## Lua API (`vim.*` namespace)

### Core `vim` Functions

```lua
-- Run an Ex command
vim.cmd("edit foo.txt")
vim.cmd({ cmd = "edit", args = { "foo.txt" } })

-- Evaluate a Vimscript expression
local val = vim.eval("&textwidth")

-- Call a Vimscript function
local abs = vim.fn.abs(-5)

-- Access options
vim.o.number = true         -- global option
vim.bo.expandtab = true     -- buffer-local
vim.wo.wrap = false         -- window-local
vim.opt.shiftwidth = 4      -- smart option wrapper

-- Access variables
vim.g.my_plugin_setting = true   -- g: (global)
vim.b[bufnr].my_var = "value"    -- b: (buffer)
vim.w[winid].my_var = "value"    -- w: (window)

-- Key mappings
vim.keymap.set("n", "<leader>f", function() vim.cmd("Find") end, { desc = "Find" })
vim.keymap.del("n", "<leader>f")

-- Autocommands
local augroup = vim.api.nvim_create_augroup("MyGroup", { clear = true })
vim.api.nvim_create_autocmd("BufWritePre", {
  group = augroup,
  pattern = "*.lua",
  callback = function(ev)
    -- ev.buf, ev.file, ev.match available
  end,
})

-- Notifications
vim.notify("Hello", vim.log.levels.WARN)
```

### LSP Client (`runtime/lua/vim/lsp/`)

```lua
-- Start an LSP client
vim.lsp.start({
  name = "my-server",
  cmd = { "my-lsp-server" },
  root_dir = vim.fs.root(0, { ".git" }),
  capabilities = vim.lsp.protocol.make_client_capabilities(),
  on_attach = function(client, bufnr)
    -- Set up buffer-local keymaps
    vim.keymap.set("n", "gd", vim.lsp.buf.definition, { buffer = bufnr })
    vim.keymap.set("n", "K",  vim.lsp.buf.hover,      { buffer = bufnr })
  end,
})

-- Buffer-level LSP actions (vim.lsp.buf.*)
vim.lsp.buf.definition()          -- Go to definition
vim.lsp.buf.hover()               -- Show hover documentation
vim.lsp.buf.references()          -- Find references
vim.lsp.buf.rename()              -- Rename symbol
vim.lsp.buf.code_action()         -- Code actions
vim.lsp.buf.format({ async = true }) -- Format buffer

-- Diagnostics
vim.diagnostic.setloclist()        -- Populate location list
vim.diagnostic.open_float()        -- Show diagnostic in float
vim.diagnostic.goto_next()         -- Jump to next diagnostic
vim.diagnostic.config({
  virtual_text = true,
  signs = true,
  underline = true,
  update_in_insert = false,
  severity_sort = true,
})
```

### Tree-sitter (`runtime/lua/vim/treesitter/`)

```lua
-- Get or create a parser for a buffer
local parser = vim.treesitter.get_parser(bufnr, "lua")
local tree = parser:parse()[1]
local root = tree:root()

-- Query nodes
local query = vim.treesitter.query.parse("lua", [[
  (function_declaration name: (identifier) @name) @func
]])
for id, node, metadata in query:iter_captures(root, bufnr, 0, -1) do
  local name = query.captures[id]
  local text = vim.treesitter.get_node_text(node, bufnr)
  print(name, text)
end

-- Enable treesitter highlighting
vim.treesitter.start(bufnr, "lua")  -- or via filetype detection

-- Get node at cursor
local node = vim.treesitter.get_node()
```

### Filesystem Utilities (`runtime/lua/vim/fs.lua`)

```lua
-- Find a root directory
local root = vim.fs.root(bufnr, { "package.json", ".git" })

-- Find files/directories matching a pattern
for name, type in vim.fs.dir("/some/path") do
  print(name, type)  -- type: "file" | "directory" | "link" | …
end

-- Path utilities
vim.fs.joinpath("a", "b", "c")   -- "a/b/c"
vim.fs.basename("/path/to/file") -- "file"
vim.fs.dirname("/path/to/file")  -- "/path/to"
vim.fs.normalize("~/foo")        -- expands ~ and ..
```

### Iterator Utilities (`runtime/lua/vim/iter.lua`)

```lua
local result = vim.iter({ 1, 2, 3, 4, 5 })
  :filter(function(x) return x % 2 == 0 end)
  :map(function(x) return x * 10 end)
  :totable()
-- result = { 20, 40 }

-- Works on tables (key-value pairs too)
vim.iter(vim.api.nvim_list_bufs())
  :filter(vim.api.nvim_buf_is_loaded)
  :each(function(bufnr) print(bufnr) end)
```

## Configuration and Extension Points

### init.lua

```lua
-- ~/.config/nvim/init.lua

-- Set options
vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.tabstop = 2
vim.opt.shiftwidth = 2
vim.opt.expandtab = true

-- Load plugins (using any plugin manager)
require("lazy").setup({ ... })

-- Autocommands
vim.api.nvim_create_autocmd("FileType", {
  pattern = "python",
  callback = function()
    vim.bo.shiftwidth = 4
  end,
})
```

### Plugin Development Pattern

```lua
-- lua/myplugin/init.lua
local M = {}

function M.setup(opts)
  opts = vim.tbl_deep_extend("force", {
    -- defaults
    enabled = true,
  }, opts or {})
  -- ...
end

return M
```

### User Commands

```lua
vim.api.nvim_create_user_command("MyCmd", function(opts)
  print(opts.args)
end, {
  nargs = "*",
  desc = "My custom command",
})
```

### Health Checks

```lua
-- lua/myplugin/health.lua
local M = {}
function M.check()
  vim.health.start("myplugin")
  if vim.fn.executable("some-tool") == 1 then
    vim.health.ok("some-tool found")
  else
    vim.health.warn("some-tool not found", "Install it with ...")
  end
end
return M
-- Check with :checkhealth myplugin
```

## RPC Integration Examples

### Python (pynvim)

```python
import pynvim
nvim = pynvim.attach('socket', path='/tmp/nvim.sock')
nvim.command('edit README.md')
lines = nvim.current.buffer[:]
nvim.current.window.cursor = (1, 0)
```

### Lua (from another Nvim instance)

```lua
local chan = vim.fn.jobstart({'nvim', '--embed'}, { rpc = true })
vim.rpcrequest(chan, 'nvim_command', 'echo "hello"')
vim.fn.jobstop(chan)
```

## API Versioning and Stability

- **`api_level`**: Monotonically increasing integer; check with `nvim_get_api_info().version.api_level`
- **`api_compatible`**: Minimum API level this version is backwards-compatible with
- **`{fn}.since`**: API level when a function was introduced
- **`{fn}.deprecated_since`**: API level when a function was deprecated
- Functions prefixed `nvim__` (double underscore) are **private/experimental** and may change without notice
- Stable API functions are prefixed with `nvim_`
