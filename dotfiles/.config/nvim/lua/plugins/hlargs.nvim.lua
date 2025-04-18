local M = {
    "m-demare/hlargs.nvim",
    event = { "BufReadPost", "BufNewFile" },
    config = function()
        require("hlargs").setup({})
    end,
}

return { M }
