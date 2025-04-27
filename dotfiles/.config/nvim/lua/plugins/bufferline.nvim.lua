local M = {
    "akinsho/bufferline.nvim",
    version = "*",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    event = "VeryLazy",
    keys = {
        { "<Leader>bmr", "<Cmd>BufferLineMoveNext<CR>", desc = "BufferLine: Move tab right" },
        { "<Leader>bml", "<Cmd>BufferLineMovePrev<CR>", desc = "BufferLine: Move tab left" },
    },
    config = function()
        require("bufferline").setup({
            options = {
                numbers = function(opts)
                    return string.format("%d", opts.ordinal, opts.id)
                end,
                separator_style = "slant",
                hover = {
                    enabled = true,
                    delay = 200,
                    reveal = { "close" },
                },
            },
            highlights = {
                buffer_selected = { bold = true, italic = false },
                numbers_selected = { bold = true, italic = false },
                diagnostic_selected = { bold = true, italic = false },
                info_selected = { bold = true, italic = false },
                warning_selected = { bold = true, italic = false },
                error_selected = { bold = true, italic = false },
                hint_selected = { bold = true, italic = false },
                pick_selected = { bold = true, italic = false },
                modified_selected = { bold = true, italic = false },
            },
        })
        for i = 1, 9 do
            vim.api.nvim_set_keymap(
                "n",
                string.format("<Leader>%d", i),
                string.format(":BufferLineGoToBuffer %d<CR>", i),
                { noremap = true, silent = true, desc = "BufferLine: Go to " }
            )
        end
    end,
}

return { M }
