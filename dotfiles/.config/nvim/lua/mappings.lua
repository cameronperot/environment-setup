-- Remapping Options
local opts = { silent = true }

-- Buffers
vim.keymap.set("n", "<leader>bd", ":bd<CR>", opts)
vim.keymap.set("n", "<Leader>bb", ":ls<CR>:b<Space>", opts)
vim.keymap.set("n", "<leader>af", ":ALEFix<CR>", opts)
vim.keymap.set("n", "<leader>1", "<Plug>AirlineSelectTab1", opts)
vim.keymap.set("n", "<leader>2", "<Plug>AirlineSelectTab2", opts)
vim.keymap.set("n", "<leader>3", "<Plug>AirlineSelectTab3", opts)
vim.keymap.set("n", "<leader>4", "<Plug>AirlineSelectTab4", opts)
vim.keymap.set("n", "<leader>5", "<Plug>AirlineSelectTab5", opts)
vim.keymap.set("n", "<leader>6", "<Plug>AirlineSelectTab6", opts)
vim.keymap.set("n", "<leader>7", "<Plug>AirlineSelectTab7", opts)
vim.keymap.set("n", "<leader>8", "<Plug>AirlineSelectTab8", opts)
vim.keymap.set("n", "<leader>9", "<Plug>AirlineSelectTab9", opts)

-- Windows
vim.keymap.set("n", "<C-j>", "<C-w>j", opts) -- Move down
vim.keymap.set("n", "<C-k>", "<C-w>k", opts) -- Move up
vim.keymap.set("n", "<C-l>", "<C-w>l", opts) -- Move right
vim.keymap.set("n", "<C-h>", "<C-w>h", opts) -- Move left

-- NERDTree
vim.keymap.set("n", "<C-n>", ":NERDTreeToggle<CR>", opts) -- Toggle NERDTree

-- LSP
vim.keymap.set("n", "gd", vim.lsp.buf.definition, opts)     -- Go to definition
vim.keymap.set("n", "gr", vim.lsp.buf.references, opts)     -- Go to references
vim.keymap.set("n", "K", vim.lsp.buf.hover, opts)           -- Show hover info
vim.keymap.set("n", "<Leader>rn", vim.lsp.buf.rename, opts) -- Rename symbol

-- Misc.
vim.keymap.set('n', '<Leader>nh', '<cmd>nohlsearch<CR>', opts) -- Unhighlight searched text
vim.keymap.set('', '<c-q>', '<nop>', { silent = true })        -- Disable ctrl-q since used in tmux
