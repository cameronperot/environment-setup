local M = {
    "neovim/nvim-lspconfig",
    dependencies = { "hrsh7th/cmp-nvim-lsp" },
    event = { "BufReadPost", "BufNewFile" },
    ft = {
        "c",
        "cpp",
        "json",
        "julia",
        "latex",
        "lua",
        "python",
        "rust",
        "sh",
        "tex",
        "toml",
        "yaml",
    },
    keys = {
        {
            "gd",
            vim.lsp.buf.definition,
            desc = "LSP: Go to definition",
            mode = "n",
            silent = true,
        },
        {
            "gr",
            vim.lsp.buf.references,
            desc = "LSP: Find references",
            mode = "n",
            silent = true,
        },
        {
            "K",
            vim.lsp.buf.hover,
            desc = "LSP: Show documentation",
            mode = "n",
            silent = true,
        },
        {
            "<Leader>rn",
            vim.lsp.buf.rename,
            desc = "LSP: Rename symbol",
            mode = "n",
            silent = true,
        },
    },
    config = function()
        local capabilities = require("cmp_nvim_lsp").default_capabilities()
        local lspconfig = require("lspconfig")
        lspconfig.pyright.setup({
            capabilities = capabilities,
            settings = {
                python = {
                    pythonPath = vim.g.python3_host_prog,
                },
            },
        })
        lspconfig.rust_analyzer.setup({
            capabilities = capabilities,
            settings = {
                ["rust-analyzer"] = {
                    checkOnSave = {
                        command = "clippy",
                    },
                    cargo = {
                        allFeatures = true,
                    },
                    diagnostics = {
                        enable = true,
                    },
                },
            },
        })
        lspconfig.clangd.setup({ capabilities = capabilities })
        lspconfig.julials.setup({ capabilities = capabilities })
        lspconfig.lua_ls.setup({
            capabilities = capabilities,
            settings = {
                Lua = {
                    diagnostics = {
                        globals = { "vim" },
                    },
                },
            },
        })
        lspconfig.jsonls.setup({ capabilities = capabilities })
        lspconfig.texlab.setup({ capabilities = capabilities })
        lspconfig.yamlls.setup({ capabilities = capabilities })
        lspconfig.taplo.setup({ capabilities = capabilities })
    end,
}

return { M }
