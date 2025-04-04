local M = {
    "kkoomen/vim-doge",
    config = function()
        vim.g.doge_doc_standard_python = "sphinx"
        vim.keymap.set("n", "<Leader>dg", "<Plug>(doge-generate)", { silent = true, noremap = false })
    end,
}

return { M }
