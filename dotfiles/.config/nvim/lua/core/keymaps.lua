-- Buffers
vim.keymap.set(
    "n",
    "<Leader>bd",
    "<Cmd>bd<CR>",
    { noremap = true, silent = true, desc = "Buffer: Delete current" }
)
vim.keymap.set(
    "n",
    "<Leader>bD",
    "<Cmd>bd!<CR>",
    { noremap = true, silent = true, desc = "Buffer: Force delete current" }
)
vim.keymap.set(
    "n",
    "<Leader><Tab>",
    "<C-^>",
    { silent = true, desc = "Buffer: Switch to last used buffer" }
)
vim.keymap.set("n", "<Leader>bp", function()
    vim.cmd("bprevious")
end, { silent = true, desc = "Buffer: Go to previous" })
vim.keymap.set("n", "<Leader>bn", function()
    vim.cmd("bnext")
end, { silent = true, desc = "Buffer: Go to next" })

-- Yanking to clipboard
vim.keymap.set(
    "n",
    "<Leader>yy",
    '<Cmd>normal "+yy<CR>',
    { noremap = true, silent = true, desc = "Yank: Current line" }
)
vim.keymap.set(
    "n",
    "<Leader>yip",
    '<Cmd>normal "+yip<CR>',
    { noremap = true, silent = true, desc = "Yank: Inner paragraph" }
)
vim.keymap.set(
    "n",
    "<Leader>yaf",
    '<Cmd>normal "+yaf<CR>',
    { noremap = true, silent = true, desc = "Yank: Function" }
)
vim.keymap.set(
    "n",
    "<Leader>yac",
    '<Cmd>normal "+yac<CR>',
    { noremap = true, silent = true, desc = "Yank: Class" }
)
vim.keymap.set(
    "n",
    "<Leader>yb",
    "<Cmd>%y+<CR>",
    { noremap = true, silent = true, desc = "Yank: Buffer" }
)

-- Windows
vim.keymap.set("n", "<C-j>", "<C-w>j", { noremap = true, silent = true, desc = "Window: Down" })
vim.keymap.set("n", "<C-k>", "<C-w>k", { noremap = true, silent = true, desc = "Window: Up" })
vim.keymap.set(
    "n",
    "<C-l>",
    "<C-w>l",
    { noremap = true, silent = true, desc = "Window: Right" }
)
vim.keymap.set("n", "<C-h>", "<C-w>h", { noremap = true, silent = true, desc = "Window: Left" })

-- LSP
vim.keymap.set(
    "n",
    "gd",
    vim.lsp.buf.definition,
    { silent = true, desc = "LSP: Go to definition" }
)
vim.keymap.set(
    "n",
    "gr",
    vim.lsp.buf.references,
    { silent = true, desc = "LSP: Find references" }
)
vim.keymap.set("n", "K", vim.lsp.buf.hover, { silent = true, desc = "LSP: Show documentation" })
vim.keymap.set(
    "n",
    "<Leader>rn",
    vim.lsp.buf.rename,
    { silent = true, desc = "LSP: Rename symbol" }
)

-- Misc.
vim.keymap.set(
    "n",
    "<Leader>nh",
    "<Cmd>nohlsearch<CR>",
    { noremap = true, silent = true, desc = "Clear search highlighting" }
)
vim.keymap.set("", "<c-q>", "<nop>", { silent = true, desc = "Disable Ctrl-Q" })

-- Plugins
-- ALE
vim.keymap.set(
    "n",
    "<Leader>af",
    "<Cmd>ALEFix<CR>",
    { noremap = true, silent = true, desc = "ALE: Fix" }
)

-- Lualine tabs
for i = 1, 9 do
    vim.keymap.set("n", "<Leader>" .. i, function()
        local buffers = vim.fn.getbufinfo({ buflisted = 1 })
        if #buffers >= i then
            vim.api.nvim_set_current_buf(buffers[i].bufnr)
        end
    end, { silent = true, desc = "Buffer: Go to " .. i })
end

-- NeoGen
vim.keymap.set(
    "n",
    "<Leader>dg",
    require("neogen").generate,
    { silent = true, desc = "Neogen: Generate" }
)

-- Outline
vim.keymap.set(
    "n",
    "<Leader>o",
    "<Cmd>Outline<CR>",
    { silent = true, desc = "Outline: Toggle" }
)

-- Nvim-tree
vim.keymap.set(
    "n",
    "<C-n>",
    "<Cmd>NvimTreeToggle<CR>",
    { noremap = true, silent = true, desc = "NvimTree: Toggle" }
)

-- Telescope
local telescope_builtin = require("telescope.builtin")
vim.keymap.set(
    "n",
    "<Leader>ff",
    telescope_builtin.find_files,
    { silent = true, desc = "Telescope: Find files" }
)
vim.keymap.set(
    "n",
    "<Leader>fg",
    telescope_builtin.live_grep,
    { silent = true, desc = "Telescope: Live grep" }
)
vim.keymap.set(
    "n",
    "<Leader>fb",
    telescope_builtin.buffers,
    { silent = true, desc = "Telescope: Find buffers" }
)
vim.keymap.set(
    "n",
    "<Leader>fh",
    telescope_builtin.help_tags,
    { silent = true, desc = "Telescope: Find help tags" }
)

-- Trouble
vim.keymap.set(
    "n",
    "<Leader>xX",
    "<Cmd>Trouble diagnostics toggle<CR>",
    { noremap = true, silent = true, desc = "Trouble: Toggle workspace diagnostics" }
)
vim.keymap.set(
    "n",
    "<Leader>xx",
    "<Cmd>Trouble diagnostics toggle filter.buf=0<CR>",
    { noremap = true, silent = true, desc = "Trouble: Toggle buffer diagnostics" }
)
vim.keymap.set(
    "n",
    "<Leader>xs",
    "<Cmd>Trouble symbols toggle focus=false<CR>",
    { noremap = true, silent = true, desc = "Trouble: Toggle document symbols" }
)
vim.keymap.set(
    "n",
    "<Leader>xl",
    "<Cmd>Trouble lsp toggle focus=false win.position=right<CR>",
    { noremap = true, silent = true, desc = "Trouble: Toggle LSP references" }
)
vim.keymap.set(
    "n",
    "<Leader>xL",
    "<Cmd>Trouble loclist toggle<CR>",
    { noremap = true, silent = true, desc = "Trouble: Toggle location list" }
)
vim.keymap.set(
    "n",
    "<Leader>xQ",
    "<Cmd>Trouble qflist toggle<CR>",
    { noremap = true, silent = true, desc = "Trouble: Toggle quickfix list" }
)

-- Zen-mode
vim.keymap.set(
    "n",
    "<Leader>zm",
    "<Cmd>ZenMode<CR>",
    { noremap = true, silent = true, desc = "ZenMode: Toggle" }
)
