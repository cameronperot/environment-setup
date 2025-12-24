local M = {
    "folke/which-key.nvim",
    event = "VeryLazy",
    config = function(_, opts)
        local wk = require("which-key")
        wk.setup(opts)
        wk.add({
            { "<Leader>a", group = "code actions/parameter swap" },
            { "<Leader>b", group = "buffer" },
            { "<Leader>d", group = "debug/documentation" },
            { "<Leader>f", group = "find/telescope" },
            { "<Leader>g", group = "git/lazygit" },
            { "<Leader>h", group = "hunks/gitsigns" },
            { "<Leader>r", group = "rename/refactor" },
            { "<Leader>t", group = "toggle" },
            { "<Leader>p", group = "python" },
            { "<Leader>u", group = "uv" },
            { "<Leader>x", group = "trouble/diagnostics" },
            { "<Leader>y", group = "yank to clipboard" },
            { "g", group = "goto" },
            { "]", group = "next" },
            { "[", group = "previous" },
        })
    end,
}

return { M }
