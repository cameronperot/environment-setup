-- Buffers
vim.keymap.set(
    "n",
    "<leader>bd",
    "<cmd>bd<cr>",
    { noremap = true, silent = true, desc = "Delete current buffer" }
)
vim.keymap.set(
    "n",
    "<leader>bD",
    "<cmd>bd!<cr>",
    { noremap = true, silent = true, desc = "Force delete current buffer" }
)
vim.keymap.set(
    "n",
    "<leader><tab>",
    "<C-^>",
    { silent = true, desc = "Switch to last used buffer" }
)
vim.keymap.set("n", "<leader>bp", function()
    vim.cmd("bprevious")
end, { silent = true, desc = "Go to previous buffer" })
vim.keymap.set("n", "<leader>bn", function()
    vim.cmd("bnext")
end, { silent = true, desc = "Go to next buffer" })

-- Yanking to clipboard
vim.keymap.set(
    "n",
    "<leader>yy",
    '<cmd>normal "+yy<cr>',
    { noremap = true, silent = true, desc = "Yank current line to clipboard" }
)
vim.keymap.set(
    "n",
    "<leader>yip",
    '<cmd>normal "+yip<cr>',
    { noremap = true, silent = true, desc = "Yank inner paragraph to clipboard" }
)
vim.keymap.set(
    "n",
    "<leader>yaf",
    '<cmd>normal "+yaf<cr>',
    { noremap = true, silent = true, desc = "Yank around function to clipboard" }
)
vim.keymap.set(
    "n",
    "<leader>yac",
    '<cmd>normal "+yac<cr>',
    { noremap = true, silent = true, desc = "Yank around class to clipboard" }
)
vim.keymap.set(
    "n",
    "<leader>yb",
    "<cmd>%y+<CR>",
    { noremap = true, silent = true, desc = "Yank entire buffer to clipboard" }
)

-- Windows
vim.keymap.set(
    "n",
    "<C-j>",
    "<C-w>j",
    { noremap = true, silent = true, desc = "Move to window below" }
)
vim.keymap.set(
    "n",
    "<C-k>",
    "<C-w>k",
    { noremap = true, silent = true, desc = "Move to window above" }
)
vim.keymap.set(
    "n",
    "<C-l>",
    "<C-w>l",
    { noremap = true, silent = true, desc = "Move to window right" }
)
vim.keymap.set(
    "n",
    "<C-h>",
    "<C-w>h",
    { noremap = true, silent = true, desc = "Move to window left" }
)

-- LSP
vim.keymap.set("n", "gd", vim.lsp.buf.definition, { silent = true, desc = "Go to definition" })
vim.keymap.set("n", "gr", vim.lsp.buf.references, { silent = true, desc = "Find references" })
vim.keymap.set("n", "K", vim.lsp.buf.hover, { silent = true, desc = "Show documentation" })
vim.keymap.set("n", "<leader>rn", vim.lsp.buf.rename, { silent = true, desc = "Rename symbol" })

-- Misc.
vim.keymap.set(
    "n",
    "<leader>nh",
    "<cmd>nohlsearch<cr>",
    { noremap = true, silent = true, desc = "Clear search highlighting" }
)
vim.keymap.set("", "<c-q>", "<nop>", { silent = true, desc = "Disable Ctrl-Q" })

-- Plugins
-- ALE
vim.keymap.set(
    "n",
    "<leader>af",
    "<cmd>ALEFix<cr>",
    { noremap = true, silent = true, desc = "Run ALEFix" }
)

-- DOGE
vim.keymap.set(
    "n",
    "<Leader>dg",
    "<Plug>(doge-generate)",
    { silent = true, noremap = false, desc = "Generate documentation" }
)

-- Lualine tabs
for i = 1, 9 do
    vim.keymap.set("n", "<leader>" .. i, function()
        local buffers = vim.fn.getbufinfo({ buflisted = 1 })
        if #buffers >= i then
            vim.api.nvim_set_current_buf(buffers[i].bufnr)
        end
    end, { silent = true, desc = "Go to buffer " .. i })
end

-- Nvim-tree
vim.keymap.set(
    "n",
    "<C-n>",
    "<cmd>NvimTreeToggle<cr>",
    { noremap = true, silent = true, desc = "Toggle NvimTree" }
)

-- Telescope
local builtin = require("telescope.builtin")
vim.keymap.set("n", "<leader>ff", builtin.find_files, { silent = true, desc = "Find files" })
vim.keymap.set("n", "<leader>fg", builtin.live_grep, { silent = true, desc = "Live grep" })
vim.keymap.set("n", "<leader>fb", builtin.buffers, { silent = true, desc = "Find buffers" })
vim.keymap.set("n", "<leader>fh", builtin.help_tags, { silent = true, desc = "Find help tags" })

-- Trouble
vim.keymap.set(
    "n",
    "<leader>xX",
    "<cmd>Trouble diagnostics toggle<cr>",
    { noremap = true, silent = true, desc = "Toggle workspace diagnostics" }
)
vim.keymap.set(
    "n",
    "<leader>xx",
    "<cmd>Trouble diagnostics toggle filter.buf=0<cr>",
    { noremap = true, silent = true, desc = "Toggle buffer diagnostics" }
)
vim.keymap.set(
    "n",
    "<leader>xs",
    "<cmd>Trouble symbols toggle focus=false<cr>",
    { noremap = true, silent = true, desc = "Toggle document symbols" }
)
vim.keymap.set(
    "n",
    "<leader>xl",
    "<cmd>Trouble lsp toggle focus=false win.position=right<cr>",
    { noremap = true, silent = true, desc = "Toggle LSP references" }
)
vim.keymap.set(
    "n",
    "<leader>xL",
    "<cmd>Trouble loclist toggle<cr>",
    { noremap = true, silent = true, desc = "Toggle location list" }
)
vim.keymap.set(
    "n",
    "<leader>xQ",
    "<cmd>Trouble qflist toggle<cr>",
    { noremap = true, silent = true, desc = "Toggle quickfix list" }
)

-- Zen-mode
vim.keymap.set(
    "n",
    "<leader>zm",
    "<cmd>ZenMode<cr>",
    { noremap = true, silent = true, desc = "Toggle Zen Mode" }
)
