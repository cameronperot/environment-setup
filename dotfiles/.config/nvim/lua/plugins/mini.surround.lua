local M = {
    "nvim-mini/mini.surround",
    version = "*",
    event = "VeryLazy",
    opts = {
        mappings = {
            add = "ys",
            delete = "ds",
            replace = "cs",
            find = "",
            find_left = "",
            highlight = "",
            update_n_lines = "",
        },
    },
    config = function(_, opts)
        require("mini.surround").setup(opts)
        -- mini.surround maps 'ys' in visual mode, but 'y' yanks immediately
        -- in visual mode. Delete that and use 'S' like vim-surround instead.
        vim.keymap.del("x", "ys")
        vim.keymap.set("x", "S", [[:<C-u>lua MiniSurround.add('visual')<CR>]], {
            silent = true,
            desc = "Surround: Add",
        })
    end,
}

return { M }
