local M = {
    "kkoomen/vim-doge",
    cmd = { "DogeGenerate" },
    config = function()
        vim.g.doge_doc_standard_python = "sphinx"
    end,
}

return { M }
