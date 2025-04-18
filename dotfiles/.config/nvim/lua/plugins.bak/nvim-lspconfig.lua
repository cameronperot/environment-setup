local M = {
    "neovim/nvim-lspconfig",
    dependencies = { "hrsh7th/cmp-nvim-lsp" },
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
