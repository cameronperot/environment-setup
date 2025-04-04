local M = {
    "dense-analysis/ale",
    config = function()
        vim.g.ale_linters = {
            cpp = { "clang" },
            lua = { "luacheck" },
            python = { "flake8", "pylint", "mypy" },
            rust = { "analyzer" },
            sh = { "shellcheck" },
            vim = { "vint" },
        }

        vim.g.ale_fixers = {
            cpp = { "clang-format" },
            lua = { "stylua" },
            python = { "black", "isort" },
            rust = { "rustfmt" },
            sh = { "shfmt" },
        }
        vim.g.ale_python_pylint_options =
            "--disable=missing-module-docstring,wrong-import-position"
        vim.g.ale_python_flake8_options = "--max-line-length=98 --extend-ignore=E203"
        vim.g.ale_python_black_options = "--config=$HOME/.config/black.conf"
        vim.g.ale_python_isort_options = "--profile=black --line-length=98"
        vim.g.ale_python_mypy_options = ""
        vim.g.ale_sh_shfmt_options = "-i 4"
        vim.g.ale_c_clangformat_options =
            "-style='{BasedOnStyle: llvm, IndentWidth: 4, ColumnLimit: 100, AllowShortFunctionsOnASingleLine: None, KeepEmptyLinesAtTheStartOfBlocks: false}'"
        vim.g.ale_lua_luacheck_options = "--std=lua54 --no-unused-args"
        vim.g.ale_lua_stylua_options = "--column-width 96 --indent-width 4 --indent-type Spaces"
        vim.g.ale_linters_explicit = 1
        vim.g.ale_fix_on_save = 1
        vim.g.ale_lint_on_insert_leave = 1
    end,
}

return { M }
