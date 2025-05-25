local M = {
    "joshuavial/aider.nvim",
    keys = {
        {
            "<Leader>Aa",
            "<Cmd>AiderOpen<CR>",
            desc = "Aider: Open",
            noremap = true,
            silent = true,
        },
    },
    opts = {
        auto_manage_context = false,
        default_bindings = false,
        debug = false,
    },
}

return {}
