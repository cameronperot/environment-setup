-- Keymap Options
local opts = { silent = true }
local opts_expr = { expr = true, silent = true }
local opts_noremap = { noremap = true, silent = true }
local opts_remap = { noremap = false, silent = true }

-- Buffers
vim.keymap.set("n", "<leader>bd", "<cmd>bd<cr>", opts_noremap)
vim.keymap.set("n", "<leader>bD", "<cmd>bd!<cr>", opts_noremap)
vim.keymap.set("n", "<leader>bb", "<cmd>ls<cr><cmd>b<Space>", opts_noremap)
vim.keymap.set("n", "<leader><tab>", "<C-^>", opts)
-- copy current line to clipboard
vim.keymap.set("n", "<leader>yy", '<cmd>normal "+yy<cr>', opts_noremap)
vim.keymap.set("n", "<leader>yip", '<cmd>normal "+yip<cr>', opts_noremap)
vim.keymap.set("n", "<leader>yaf", '<cmd>normal "+yaf<cr>', opts_noremap)
vim.keymap.set("n", "<leader>yac", '<cmd>normal "+yac<cr>', opts_noremap)
vim.keymap.set("n", "<leader>yb", "<cmd>%y+<CR>", opts_noremap)
vim.keymap.set("n", "<leader>bp", function()
    vim.cmd("bprevious")
end, opts)
vim.keymap.set("n", "<leader>bn", function()
    vim.cmd("bnext")
end, opts)

-- Windows
vim.keymap.set("n", "<C-j>", "<C-w>j", opts_noremap)
vim.keymap.set("n", "<C-k>", "<C-w>k", opts_noremap)
vim.keymap.set("n", "<C-l>", "<C-w>l", opts_noremap)
vim.keymap.set("n", "<C-h>", "<C-w>h", opts_noremap)

-- LSP
vim.keymap.set("n", "gd", vim.lsp.buf.definition, opts)
vim.keymap.set("n", "gr", vim.lsp.buf.references, opts)
vim.keymap.set("n", "K", vim.lsp.buf.hover, opts)
vim.keymap.set("n", "<leader>rn", vim.lsp.buf.rename, opts)

-- Misc.
vim.keymap.set("n", "<leader>nh", "<cmd>nohlsearch<cr>", opts_noremap)
vim.keymap.set("", "<c-q>", "<nop>", opts)

-- Plugins
-- ALE
vim.keymap.set("n", "<leader>af", "<cmd>ALEFix<cr>", opts_noremap)

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
vim.keymap.set("n", "<C-n>", "<cmd>NvimTreeToggle<cr>", opts_noremap)

-- Telescope
local builtin = require("telescope.builtin")
vim.keymap.set("n", "<leader>ff", builtin.find_files, opts)
vim.keymap.set("n", "<leader>fg", builtin.live_grep, opts)
vim.keymap.set("n", "<leader>fb", builtin.buffers, opts)
vim.keymap.set("n", "<leader>fh", builtin.help_tags, opts)

-- Trouble
vim.keymap.set("n", "<leader>xX", "<cmd>Trouble diagnostics toggle<cr>", opts_noremap)
vim.keymap.set(
    "n",
    "<leader>xx",
    "<cmd>Trouble diagnostics toggle filter.buf=0<cr>",
    opts_noremap
)
vim.keymap.set("n", "<leader>xs", "<cmd>Trouble symbols toggle focus=false<cr>", opts_noremap)
vim.keymap.set(
    "n",
    "<leader>xl",
    "<cmd>Trouble lsp toggle focus=false win.position=right<cr>",
    opts_noremap
)
vim.keymap.set("n", "<leader>xL", "<cmd>Trouble loclist toggle<cr>", opts_noremap)
vim.keymap.set("n", "<leader>xQ", "<cmd>Trouble qflist toggle<cr>", opts_noremap)

-- Vimspector
vim.keymap.set("n", "<leader>di", "<Plug>VimspectorBalloonEval", opts_remap)
vim.keymap.set("x", "<leader>di", "<Plug>VimspectorBalloonEval", opts_remap)

-- Zen-mode
vim.keymap.set("n", "<leader>zm", "<cmd>ZenMode<cr>", opts_noremap)
