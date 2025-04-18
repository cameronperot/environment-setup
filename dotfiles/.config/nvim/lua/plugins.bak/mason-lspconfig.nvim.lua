local M = {
    "williamboman/mason-lspconfig.nvim",
    config = function()
        require("mason-lspconfig").setup({
            ensure_installed = {
                "pyright",
                "rust_analyzer",
                "clangd",
                "julials",
                "jsonls",
                "texlab",
                "yamlls",
                "taplo",
                "lua_ls",
            },
            automatic_installation = true,
        })
    end,
}

return { M }
