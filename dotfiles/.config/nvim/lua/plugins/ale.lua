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
        -- Define and register the JuliaFormatter fixer
        -- Define the fixer function globally in Vimscript namespace
        vim.cmd([[
            function! JuliaFormatterFixer(buffer) abort
                return {
                \   'command': 'julia -e "using JuliaFormatter; format_file(ARGS[1])" %t',
                \   'read_temporary_file': 1,
                \}
            endfunction
        ]])

        -- Register the fixer after ALE is loaded (using function name as string)
        vim.api.nvim_create_autocmd("User", {
            pattern = "ALEWantResults",
            once = true,
            callback = function()
                vim.fn["ale#fix#registry#Add"](
                    "juliaformatter",
                    "JuliaFormatterFixer",
                    { "julia" },
                    "Format Julia code with JuliaFormatter"
                )
            end,
        })

        vim.g.ale_linters = {
            cpp = { "clang" },
            julia = { "julials" },
            lua = { "luacheck" },
            python = { "ruff", "mypy" },
            rust = { "analyzer" },
            sh = { "shellcheck" },
            vim = { "vint" },
        }

        vim.g.ale_fixers = {
            cpp = { "clang-format" },
            julia = { "juliaformatter" },
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
        vim.g.ale_disable_lsp = 0
    end,
}

return { M }
