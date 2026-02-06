-- Options
vim.opt.encoding = "utf-8" -- File encoding
vim.opt.foldenable = true -- Enable folding
vim.opt.foldlevel = 99 -- Start with all folds open
vim.opt.fillchars:append({
    fold = " ", -- Remove default fold marker
    foldopen = "▾", -- Down arrow for open folds
    foldclose = "▸", -- Right arrow for closed folds
})
vim.opt.foldcolumn = "1" -- Show fold column
vim.opt.foldmethod = "expr" -- Use Treesitter for folding
vim.opt.foldexpr = "v:lua.vim.treesitter.foldexpr()" -- Treesitter folding expression
vim.opt.splitbelow = true -- Horizontal splits below
vim.opt.splitright = true -- Vertical splits to the right
vim.opt.smartindent = true -- Smart indentation
vim.opt.cursorline = true -- Highlight current line
vim.opt.expandtab = true -- Tabs to spaces
vim.opt.tabstop = 4 -- 4 spaces per tab
vim.opt.shiftwidth = 4 -- 4 spaces for indentation
vim.opt.number = true -- Line numbers
vim.opt.relativenumber = true -- Relative line numbers
vim.opt.colorcolumn = "88" -- Column limit marker
vim.opt.ignorecase = true -- Case-insensitive search
vim.opt.smartcase = true -- Case-sensitive if uppercase in search
vim.opt.hidden = true -- Allow hidden buffers
vim.opt.scrolloff = 8 -- Lines above/below cursor
vim.opt.list = true -- Show special characters
vim.opt.listchars = { tab = "»·", trail = "·" } -- Tab and trailing space markers
vim.opt.wrap = true -- Wrap long lines
vim.opt.linebreak = true -- Break at word boundaries
vim.opt.showbreak = " ↪" -- Wrapped line indicator
vim.opt.spell = true -- Enable spell checking
vim.opt.spelllang = "en_us" -- US English spelling
vim.opt.termguicolors = true -- 24-bit color support
vim.opt.ttyfast = true -- Speed up scrolling
vim.opt.mousemoveevent = true -- Mouse movement events
vim.opt.undofile = true
vim.cmd("syntax enable") -- Syntax highlighting
vim.cmd("filetype plugin indent on") -- Enable filetype
vim.cmd(
    "highlight LineNr term=bold cterm=NONE ctermfg=DarkGrey ctermbg=NONE gui=NONE guifg=DarkGrey guibg=NONE"
)
vim.api.nvim_create_autocmd("FileType", { -- Disable auto continuing comment on next line
    pattern = "*",
    callback = function()
        vim.opt_local.formatoptions:remove({ "c", "r", "o" })
    end,
})
vim.cmd("colorscheme onedark")

-- Python
vim.g.python3_host_prog = vim.env.HOME .. "/.micromamba/envs/dev/bin/python"

-- Markdown
vim.api.nvim_create_autocmd("FileType", {
    pattern = "markdown",
    callback = function()
        vim.opt_local.formatoptions:append("ro")
        vim.opt_local.comments = "b:*,b:-,b:+,b:1.,n:>"
    end,
})

-- Completion (:help completeopt)
vim.opt.completeopt = { "menuone", "noselect", "noinsert" }
vim.opt.shortmess = vim.opt.shortmess + { c = true }
vim.api.nvim_set_option("updatetime", 300)

-- No spellcheck in terminal
vim.api.nvim_create_autocmd("TermOpen", {
    callback = function()
        vim.opt_local.spell = false
    end,
})

-- Remove trailing whitespace and new lines
vim.api.nvim_create_autocmd("BufWritePre", {
    pattern = "*",
    callback = function()
        -- Save cursor position
        local save_cursor = vim.fn.getpos(".")
        -- Remove trailing whitespace
        vim.cmd([[silent! %s/\s\+$//e]])
        -- Remove trailing newlines
        vim.cmd([[silent! %s/\($\n\s*\)\+\%$//e]])
        -- Restore cursor position
        vim.fn.setpos(".", save_cursor)
    end,
})
