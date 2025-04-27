return {
    "nvim-tree/nvim-tree.lua",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    cmd = { "NvimTreeToggle" },
    keys = {
        {
            "<C-n>",
            "<Cmd>NvimTreeToggle<CR>",
            desc = "NvimTree: Toggle",
            noremap = true,
            silent = true,
        },
    },
    config = function()
        vim.g.loaded_netrw = 1
        vim.g.loaded_netrwPlugin = 1
        require("nvim-tree").setup({
            view = {
                width = 48,
                side = "right",
                number = true,
                relativenumber = true,
            },
            actions = {
                open_file = {
                    quit_on_open = true,
                },
            },
            renderer = {
                group_empty = true,
            },
            filters = {
                dotfiles = false,
            },
            update_focused_file = {
                enable = true,
                update_root = false,
            },
            on_attach = function(bufnr)
                local api = require("nvim-tree.api")

                local function opts(desc)
                    return {
                        desc = "nvim-tree: " .. desc,
                        buffer = bufnr,
                        noremap = true,
                        silent = true,
                        nowait = true,
                    }
                end

                api.config.mappings.default_on_attach(bufnr)
                vim.keymap.set(
                    "n",
                    "h",
                    api.node.navigate.parent_close,
                    { buffer = bufnr, noremap = true, silent = true }
                )
                vim.keymap.set(
                    "n",
                    "l",
                    api.node.open.edit,
                    { buffer = bufnr, noremap = true, silent = true }
                )
            end,
        })
    end,
}
