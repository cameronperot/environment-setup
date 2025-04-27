local M = {
    "folke/zen-mode.nvim",
    cmd = "ZenMode",
    keys = {
        {
            "<Leader>zm",
            "<Cmd>ZenMode<CR>",
            desc = "ZenMode: Toggle",
            noremap = true,
            silent = true,
        },
    },
    opts = {
        window = {
            width = 0.75,
        },
    },
}

return { M }
