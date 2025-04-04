local M = {
    "nvim-treesitter/nvim-treesitter",
    build = function()
        require("nvim-treesitter.install").update { with_sync = true }()
    end,
    config = function()
        local configs = require "nvim-treesitter.configs"
        configs.setup {
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
                "yaml",
            },
            ignore_install = {},
            highlight = {
                enable = true,
                disable = {},
            },
            fold = { enable = true },
        }
    end,
}

return { M }
