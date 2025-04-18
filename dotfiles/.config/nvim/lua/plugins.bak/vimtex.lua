local M = {
    "lervag/vimtex",
    ft = { "tex", "latex" },
    config = function()
        vim.g.vimtex_quickfix_ignore_filters = {
            "Overfull",
            "Underfull",
            "Package hyperref Warning: Token not allowed in a PDF string",
            "contains only floats.",
            '`h" float specifier changed to `ht".',
        }
    end,
}

return { M }
