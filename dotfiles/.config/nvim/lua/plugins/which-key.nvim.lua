local M = {
    "folke/which-key.nvim",
    event = "VeryLazy",
    config = function()
        require("which-key").setup {
            plugins = {
                spelling = { enabled = true },
            },
            window = {
                border = "rounded",
                padding = { 1, 1, 1, 1 },
            },
        }
        require("which-key").register {
            ["<leader>f"] = { name = "Find (Telescope)" },
            ["<leader>b"] = { name = "Buffers" },
            ["<leader>g"] = { name = "Git" },
            ["<leader>x"] = { name = "Diagnostics/Trouble" },
            ["<leader>d"] = { name = "Debug" },
        }
    end,
}

return {}
