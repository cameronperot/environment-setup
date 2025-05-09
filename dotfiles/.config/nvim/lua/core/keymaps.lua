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
vim.keymap.set(
    "n",
    "<Leader>yw",
    '<Cmd>normal "+yiw<CR>',
    { noremap = true, silent = true, desc = "Yank: Current word" }
)
vim.keymap.set(
    "n",
    "<Leader>yW",
    '<Cmd>normal "+yiW<CR>',
    { noremap = true, silent = true, desc = "Yank: Current WORD" }
)
vim.keymap.set(
    "v",
    "<Leader>y",
    '"+y',
    { noremap = true, silent = true, desc = "Yank: Visual selection" }
)
vim.keymap.set(
    "n",
    "<Leader>yas",
    '<Cmd>normal "+yas<CR>',
    { noremap = true, silent = true, desc = "Yank: Sentence" }
)
vim.keymap.set(
    "n",
    "<Leader>yab",
    '<Cmd>normal "+yab<CR>',
    { noremap = true, silent = true, desc = "Yank: Block" }
)
vim.keymap.set(
    "n",
    "<Leader>y$",
    '<Cmd>normal "+y$<CR>',
    { noremap = true, silent = true, desc = "Yank: To end of line" }
)
vim.keymap.set(
    "n",
    "<Leader>y0",
    '<Cmd>normal "+y0<CR>',
    { noremap = true, silent = true, desc = "Yank: To start of line" }
)

-- Windows
vim.keymap.set("n", "<C-h>", "<C-w>h", { noremap = true, silent = true, desc = "Window: Left" })
vim.keymap.set("n", "<C-j>", "<C-w>j", { noremap = true, silent = true, desc = "Window: Down" })
vim.keymap.set("n", "<C-k>", "<C-w>k", { noremap = true, silent = true, desc = "Window: Up" })
vim.keymap.set(
    "n",
    "<C-l>",
    "<C-w>l",
    { noremap = true, silent = true, desc = "Window: Right" }
)
vim.api.nvim_set_keymap(
    "t",
    "<C-h>",
    "<C-\\><C-n><C-w>h",
    { noremap = true, silent = true, desc = "Window: Left (from terminal)" }
)
vim.api.nvim_set_keymap(
    "t",
    "<C-j>",
    "<C-\\><C-n><C-w>j",
    { noremap = true, silent = true, desc = "Window: Down (from terminal)" }
)
vim.api.nvim_set_keymap(
    "t",
    "<C-k>",
    "<C-\\><C-n><C-w>k",
    { noremap = true, silent = true, desc = "Window: Up (from terminal)" }
)
vim.api.nvim_set_keymap(
    "t",
    "<C-l>",
    "<C-\\><C-n><C-w>l",
    { noremap = true, silent = true, desc = "Window: Left (from terminal)" }
)
vim.keymap.set(
    "n",
    "<C-Left>",
    "<Cmd>vertical resize -2<CR>",
    { noremap = true, silent = true, desc = "Window: Resize Left" }
)
vim.keymap.set(
    "n",
    "<C-Down>",
    "<Cmd>resize -2<CR>",
    { noremap = true, silent = true, desc = "Window: Resize Down" }
)
vim.keymap.set(
    "n",
    "<C-Up>",
    "<Cmd>resize +2<CR>",
    { noremap = true, silent = true, desc = "Window: Resize Up" }
)
vim.keymap.set(
    "n",
    "<C-Right>",
    "<Cmd>vertical resize +2<CR>",
    { noremap = true, silent = true, desc = "Window: Resize Right" }
)

-- Misc.
vim.keymap.set(
    "n",
    "<Leader>nh",
    "<Cmd>nohlsearch<CR>",
    { noremap = true, silent = true, desc = "Clear search highlighting" }
)
vim.keymap.set("", "<c-q>", "<nop>", { silent = true, desc = "Disable Ctrl-Q" })
