local M = {
    "neovim/nvim-lspconfig",
    dependencies = { "hrsh7th/cmp-nvim-lsp" },
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
        -- Set capabilities for all servers
        local capabilities = require("cmp_nvim_lsp").default_capabilities()
        vim.lsp.config("*", {
            capabilities = capabilities,
        })

        -- Configure servers with specific settings
        vim.lsp.config("pyright", {
            settings = {
                python = {
                    pythonPath = vim.g.python3_host_prog,
                },
            },
        })

        vim.lsp.config("rust_analyzer", {
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

        vim.lsp.config("lua_ls", {
            settings = {
                Lua = {
                    diagnostics = {
                        globals = { "vim" },
                    },
                },
            },
        })

        -- Enable all servers
        vim.lsp.enable({
            "pyright",
            "rust_analyzer",
            "clangd",
            -- "julials",
            "lua_ls",
            "jsonls",
            "texlab",
            "yamlls",
            "taplo",
        })
    end,
}

return { M }
