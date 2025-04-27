local M = {
    "hedyhli/outline.nvim",
    lazy = true,
    cmd = { "Outline", "OutlineOpen" },
    opts = {
        outline_window = {
            show_numbers = true,
        },
    },
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
