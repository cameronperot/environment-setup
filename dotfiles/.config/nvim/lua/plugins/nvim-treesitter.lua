local M = {
    "nvim-treesitter/nvim-treesitter",
    event = { "BufReadPost", "BufNewFile" },
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
    build = function()
        require("nvim-treesitter.install").update({ with_sync = true })()
    end,
    config = function()
        local configs = require("nvim-treesitter.configs")
        configs.setup({
            ensure_installed = {
                "bash",
                "cpp",
                "json",
                "julia",
                "lua",
                "python",
                "rust",
                "toml",
                "yaml",
            },
            ignore_install = {},
            highlight = {
                enable = true,
                disable = {},
            },
            fold = { enable = true },
        })
    end,
}

return { M }
