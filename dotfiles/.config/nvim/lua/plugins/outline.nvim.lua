local M = {
    "hedyhli/outline.nvim",
    lazy = true,
    cmd = { "Outline", "OutlineOpen" },
    opts = {},
    keys = {
        {
            "<Leader>o",
            "<Cmd>Outline<CR>",
            desc = "Outline: Toggle",
            mode = "n",
            silent = true,
        },
    },
}

return { M }
