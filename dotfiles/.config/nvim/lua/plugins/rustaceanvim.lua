local M = {
    "mrcjkb/rustaceanvim",
    version = "^5",
    ft = "rust",
    keys = {
        {
            "<Leader>rh",
            function()
                vim.cmd.RustLsp({ "hover", "actions" })
            end,
            desc = "Rust: Hover actions",
            ft = "rust",
        },
        {
            "<Leader>ra",
            function()
                vim.cmd.RustLsp("codeAction")
            end,
            desc = "Rust: Code actions",
            ft = "rust",
        },
    },
}

return { M }
