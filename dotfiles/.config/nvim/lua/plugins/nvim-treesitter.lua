local M = {
    "nvim-treesitter/nvim-treesitter",
    branch = "main",
    lazy = false,
    build = ":TSUpdate",
    config = function()
        require("nvim-treesitter").install({
            "bash",
            "c",
            "cpp",
            "json",
            "julia",
            "lua",
            "python",
            "rust",
            "toml",
            "yaml",
        })

        -- Enable treesitter highlighting
        vim.api.nvim_create_autocmd("FileType", {
            pattern = {
                "bash",
                "c",
                "cpp",
                "json",
                "julia",
                "lua",
                "python",
                "rust",
                "sh",
                "toml",
                "yaml",
            },
            callback = function()
                vim.treesitter.start()
            end,
        })
    end,
}

return { M }
