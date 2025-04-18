local M = {
    "lukas-reineke/indent-blankline.nvim",
    event = { "BufReadPost", "BufNewFile" },
    config = function()
        require("ibl").setup({})
    end,
}

return { M }
