local M = {
    "dense-analysis/ale",
    event = { "BufReadPost", "BufWritePre" },
    ft = {
        "c",
        "cpp",
        "json",
        "julia",
        "lua",
        "python",
        "rust",
        "sh",
        "tex",
        "toml",
        "yaml",
    },
    keys = {
        { "<Leader>af", "<Cmd>ALEFix<CR>", desc = "ALE: Fix", noremap = true, silent = true },
    },
    config = function()
        vim.g.ale_linters = {
            cpp = { "clang" },
            lua = { "luacheck" },
            python = { "ruff", "mypy" },
            rust = { "analyzer" },
            sh = { "shellcheck" },
            vim = { "vint" },
        }

        vim.g.ale_fixers = {
            cpp = { "clang-format" },
            lua = { "stylua" },
            python = { "ruff", "ruff_format" },
            rust = { "rustfmt" },
            sh = { "shfmt" },
        }

        vim.g.ale_python_ruff_options = "--line-length=98"
        vim.g.ale_python_mypy_options = ""
        vim.g.ale_sh_shfmt_options = "-i 4"
        vim.g.ale_c_clangformat_options =
            "-style='{BasedOnStyle: llvm, IndentWidth: 4, ColumnLimit: 100, AllowShortFunctionsOnASingleLine: None, KeepEmptyLinesAtTheStartOfBlocks: false}'"
        vim.g.ale_lua_luacheck_options = "--std=lua54 --no-unused-args"
        vim.g.ale_lua_stylua_options = "--column-width 96 --indent-width 4 --indent-type Spaces"
        vim.g.ale_linters_explicit = 1
        vim.g.ale_fix_on_save = 1
        vim.g.ale_lint_on_insert_leave = 1
        vim.g.ale_pattern_options = {
            ["lsq/ccxt"] = { ale_fix_on_save = 0 },
        }
    end,
}

return { M }
