local M = {
    "akinsho/bufferline.nvim",
    version = "*",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    event = "VeryLazy",
    keys = {
        { "[b", "<Cmd>BufferLineCyclePrev<CR>", desc = "BufferLine: Cycle tab left" },
        { "]b", "<Cmd>BufferLineCycleNext<CR>", desc = "BufferLine: Cycle tab right" },
        { "[B", "<Cmd>BufferLineMovePrev<CR>", desc = "BufferLine: Move tab left" },
        { "]B", "<Cmd>BufferLineMoveNext<CR>", desc = "BufferLine: Move tab right" },
    },
    config = function()
        local bufferline = require("bufferline")
        bufferline.setup({
            options = {
                style_preset = bufferline.style_preset.no_italic,
                numbers = function(opts)
                    return string.format("%s", opts.ordinal, opts.id)
                end,
                hover = {
                    enabled = true,
                    delay = 200,
                    reveal = { "close" },
                },
                offsets = {
                    {
                        filetype = "NvimTree",
                        separator = false,
                        highlight = "NvimTreeNormal",
                    },
                },
            },
            highlights = {
                fill = { bg = "NONE" },
                background = { bg = "NONE" },
                tab = { bg = "NONE" },
                numbers = { bg = "NONE" },
                close_button = { bg = "NONE" },
                separator = { bg = "NONE" },
                modified = { bg = "NONE" },
                duplicate = { bg = "NONE" },
                indicator_selected = { fg = "#98c379" },
            },
        })
        for i = 1, 9 do
            vim.api.nvim_set_keymap(
                "n",
                string.format("<Leader>%d", i),
                string.format("<Cmd>BufferLineGoToBuffer %d<CR>", i),
                { noremap = true, silent = true, desc = "BufferLine: Go to " }
            )
        end
    end,
}

return { M }
