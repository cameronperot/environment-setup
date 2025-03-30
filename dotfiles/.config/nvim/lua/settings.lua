-- General Settings
vim.opt.encoding = "utf-8"                        -- File encoding
vim.opt.foldenable = false                        -- Enable folding
vim.opt.foldmethod = "expr"                       -- Use Treesitter for folding
vim.opt.foldexpr = "nvim_treesitter#foldexpr()"   -- Treesitter folding expression
vim.opt.splitbelow = true                         -- Horizontal splits below
vim.opt.splitright = true                         -- Vertical splits to the right
vim.opt.smartindent = true                        -- Smart indentation
vim.opt.cursorline = true                         -- Highlight current line
vim.opt.expandtab = true                          -- Tabs to spaces
vim.opt.tabstop = 4                               -- 4 spaces per tab
vim.opt.shiftwidth = 4                            -- 4 spaces for indentation
vim.opt.number = true                             -- Line numbers
vim.opt.relativenumber = true                     -- Relative line numbers
vim.opt.colorcolumn = "96"                        -- Column limit marker
vim.opt.ignorecase = true                         -- Case-insensitive search
vim.opt.smartcase = true                          -- Case-sensitive if uppercase in search
vim.opt.hidden = true                             -- Allow hidden buffers
vim.opt.scrolloff = 8                             -- Lines above/below cursor
vim.opt.list = true                               -- Show special characters
vim.opt.listchars = { tab = "»·", trail = "·" }   -- Tab and trailing space markers
vim.opt.wrap = true                               -- Wrap long lines
vim.opt.linebreak = true                          -- Break at word boundaries
vim.opt.showbreak = " ↪"                          -- Wrapped line indicator
vim.opt.spell = true                              -- Enable spell checking
vim.opt.spelllang = "en_us"                       -- US English spelling
vim.opt.termguicolors = true                      -- 24-bit color support
vim.cmd("syntax enable")                          -- Syntax highlighting
vim.cmd("filetype plugin indent on")              -- Enable filetype
vim.cmd("highlight LineNr term=bold cterm=NONE ctermfg=DarkGrey ctermbg=NONE gui=NONE guifg=DarkGrey guibg=NONE")
vim.api.nvim_create_autocmd("FileType", {         -- Disable auto continuing comment on next line
  pattern = "*",
  callback = function()
    vim.opt_local.formatoptions:remove({ "c", "r", "o" })
  end
})
vim.cmd("colorscheme onedark")

-- Remove trailing whitespace and new lines
vim.api.nvim_create_autocmd('BufWritePre', {
  pattern = '*',
  callback = function()
    -- Save cursor position
    local save_cursor = vim.fn.getpos('.')
    -- Remove trailing whitespace
    vim.cmd([[silent! %s/\s\+$//e]])
    -- Remove trailing newlines
    vim.cmd([[silent! %s/\($\n\s*\)\+\%$//e]])
    -- Restore cursor position
    vim.fn.setpos('.', save_cursor)
  end
})

-- Python
vim.g.python3_host_prog = vim.env.HOME .. "/miniconda3/envs/dev/bin/python" -- Python interpreter

-- Airline
vim.g.airline_theme = "onedark"
vim.g.airline_powerline_fonts = 1
vim.g["airline#extensions#branch#enabled"] = 1
vim.g["airline#extensions#bufferline#overwrite_variables"] = 0
vim.g["airline#extensions#tabline#enabled"] = 1
vim.g["airline#extensions#tabline#tab_nr_type"] = 1  -- tab number
vim.g["airline#extensions#tabline#show_tab_nr"] = 1
vim.g["airline#extensions#tabline#formatter"] = "unique_tail"  -- Note: this overrides the duplicate formatter below
vim.g["airline#extensions#tabline#buffer_nr_show"] = 1
vim.g["airline#extensions#tabline#fnametruncate"] = 16
vim.g["airline#extensions#tabline#fnamecollapse"] = 2
vim.g["airline#extensions#tabline#buffer_idx_mode"] = 1
vim.g["airline#extensions#tabline#left_sep"] = " "
vim.g["airline#extensions#tabline#left_alt_sep"] = "|"

-- ALE
vim.g.ale_linters = {
    cpp = {"clang"},
    python = {"flake8", "pylint", "mypy"},
    rust = { "analyzer" },
    sh = {"shellcheck"},
    vim = {"vint"},
}

vim.g.ale_fixers = {
    cpp = {"clang-format"},
    python = {"black", "isort"},
    rust = { "rustfmt" },
    sh = {"shfmt"},
}
vim.g.ale_python_pylint_options = "--disable=missing-module-docstring,wrong-import-position"
vim.g.ale_python_flake8_options = "--max-line-length=98 --extend-ignore=E203"
vim.g.ale_python_black_options = "--config=$HOME/.config/black.conf"
vim.g.ale_python_isort_options = "--profile=black --line-length=98"
vim.g.ale_python_mypy_options = ""
vim.g.ale_sh_shfmt_options = "-i 4"
vim.g.ale_c_clangformat_options = "-style='{BasedOnStyle: llvm, IndentWidth: 4, ColumnLimit: 100, AllowShortFunctionsOnASingleLine: None, KeepEmptyLinesAtTheStartOfBlocks: false}'"
vim.g.ale_linters_explicit = 1
vim.g.ale_fix_on_save = 1
vim.g.ale_lint_on_insert_leave = 1

-- Bufferline
vim.g.bufferline_echo = 0

-- Complete (:help completeopt)
vim.opt.completeopt = {"menuone", "noselect", "noinsert"}
vim.opt.shortmess = vim.opt.shortmess + { c = true}
vim.api.nvim_set_option("updatetime", 300)

-- DOcument GEnerator
vim.g.doge_doc_standard_python = "sphinx"
vim.keymap.set("n", "<Leader>dg", "<Plug>(doge-generate)", { silent = true, noremap = false })

-- Markdown settings
vim.api.nvim_create_autocmd("FileType", {
  pattern = "markdown",
  callback = function()
    vim.opt_local.formatoptions:append("ro")
    vim.opt_local.comments = "b:*,b:-,b:+,b:1.,n:>"
  end
})

-- Markdown Preview
vim.g.mkdp_auto_start = 0
vim.g.mkdp_auto_close = 0
vim.g.mkdp_refresh_slow = 1
vim.g.mkdp_browser = "firefox"

-- NERDCommenter
vim.g.NERDSpaceDelims = 0

-- NERDTree
vim.g.NERDTreeShowHidden = 1
vim.g.NERDTreeShowLineNumbers = 1
vim.g.NERDTreeQuitOnOpen = 1
vim.api.nvim_create_autocmd("FileType", {
  pattern = "nerdtree",
  callback = function()
    vim.opt_local.relativenumber = true
  end
})

-- Treesitter
require("nvim-treesitter.configs").setup {
    ensure_installed = {
        "bash",
        "cpp",
        "json",
        "julia",
        "latex",
        "lua",
        "python",
        "rust",
        "toml",
        "yaml"
    },
    ignore_install = { },
    highlight = {
        enable = true,
        disable = { },
    },
    fold = { enable = true },
}

-- Vimtex
vim.g.vimtex_quickfix_ignore_filters = {
  "Overfull",
  "Underfull",
  "Package hyperref Warning: Token not allowed in a PDF string",
  "contains only floats.",
  "`h\" float specifier changed to `ht\".",
}

-- Fixed column for diagnostics to appear
-- Show autodiagnostic popup on cursor hover_range
-- Goto previous / next diagnostic warning / error
-- Show inlay_hints more frequently
vim.cmd([[
    set signcolumn=yes
    autocmd CursorHold * lua vim.diagnostic.open_float(nil, { focusable = false })
]])
