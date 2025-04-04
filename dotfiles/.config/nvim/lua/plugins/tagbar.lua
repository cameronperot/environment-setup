local M = {
    "preservim/tagbar",
    config = function()
        vim.g.tagbar_foldlevel = 0
        vim.g.tagbar_autofocus = 1
        vim.g.tagbar_compact = 1
    end,
}

return { M }
