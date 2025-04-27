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

-- Misc.
vim.keymap.set(
    "n",
    "<Leader>nh",
    "<Cmd>nohlsearch<CR>",
    { noremap = true, silent = true, desc = "Clear search highlighting" }
)
vim.keymap.set("", "<c-q>", "<nop>", { silent = true, desc = "Disable Ctrl-Q" })
