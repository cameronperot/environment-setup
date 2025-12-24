local M = {
    "linux-cultist/venv-selector.nvim",
    dependencies = {
        "neovim/nvim-lspconfig",
        "nvim-telescope/telescope.nvim",
        "mfussenegger/nvim-dap-python",
    },
    ft = "python",
    keys = {
        { "<Leader>pv", "<cmd>VenvSelect<cr>", desc = "Python: Select venv" },
    },
    opts = {
        options = {
            picker = "telescope",
            notify_user_on_venv_activation = true,
            on_venv_activate_callback = function()
                require("dap-python").setup(require("venv-selector").python())
            end,
        },
        search = {
            micromamba = {
                command = "fd /bin/python$ ~/.micromamba/envs --full-path --color never -a",
                type = "anaconda",
            },
        },
    },
}

return { M }
