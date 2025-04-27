local M = {
    "simrat39/rust-tools.nvim",
    ft = "rust",
    keys = {
        {
            "<Leader>rh",
            function()
                require("rust-tools").hover_actions.hover_actions()
            end,
            desc = "Rust: Hover actions",
            ft = "rust",
        },
        {
            "<Leader>ra",
            function()
                require("rust-tools").code_action_group.code_action_group()
            end,
            desc = "Rust: Code actions",
            ft = "rust",
        },
    },
    config = function()
        require("rust-tools").setup({})
    end,
}

return { M }
