local M = {
    "danymat/neogen",
    dependencies = "nvim-treesitter/nvim-treesitter",
    ft = {
        "python",
        "rust",
    },
    cmd = { "Neogen" },
    keys = {
        {
            "<Leader>dg",
            function()
                require("neogen").generate()
            end,
            desc = "Neogen: Generate",
        },
    },
    config = function()
        require("neogen").setup({
            enabled = true,
            input_after_comment = true,
            languages = {
                python = {
                    template = {
                        annotation_convention = "reST",
                    },
                },
            },
        })
    end,
    version = "*",
}

return { M }
