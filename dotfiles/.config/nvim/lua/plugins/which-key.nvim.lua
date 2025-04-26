local M = {
    "folke/which-key.nvim",
    event = "VeryLazy",
    config = function(_, opts)
        local wk = require("which-key")
        wk.setup(opts)

        -- Register groups using the new syntax format from the README
        wk.add({
            { "<leader>b", group = "buffer" },
            { "<leader>y", group = "yank to clipboard" },
            { "<leader>r", group = "rename" },
            { "<leader>f", group = "find" },
            { "<leader>x", group = "trouble/diagnostics" },
            { "<leader>d", group = "debug" },
            { "g", group = "goto" },
        })
    end,
}

return { M }
