local M = {
    "nvim-treesitter/nvim-treesitter",
    event = { "BufReadPost", "BufNewFile" },
    ft = {
        "c",
        "cpp",
        "json",
        "julia",
        "latex",
        "lua",
        "markdown",
        "python",
        "rust",
        "sh",
        "tex",
        "toml",
        "vim",
        "vimdoc",
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
                "c",
                "cpp",
                "json",
                "julia",
                "latex",
                "lua",
                "markdown",
                "python",
                "rust",
                "toml",
                "vim",
                "vimdoc",
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
