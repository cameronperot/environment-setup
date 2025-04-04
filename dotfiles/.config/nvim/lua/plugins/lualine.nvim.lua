local M = {
    "nvim-lualine/lualine.nvim",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    config = function()
        require("lualine").setup({
            options = {
                theme = "onedark",
                icons_enabled = true,
            },
            sections = {
                lualine_a = { "mode" },
                lualine_b = { "branch" },
                lualine_c = { "filename" },
                lualine_x = { "encoding", "fileformat", "filetype" },
                lualine_y = { "progress" },
                lualine_z = { "location" },
            },
            tabline = {
                lualine_a = {
                    {
                        "buffers",
                        show_filename_only = true,
                        show_modified_status = true,
                        mode = 2,
                        max_length = function()
                            return vim.o.columns
                        end,
                        fmt = function(name, buf)
                            if buf and buf.index then
                                return string.format("%d:%s", buf.index, name)
                            else
                                return name
                            end
                        end,
                    },
                },
                lualine_b = {},
                lualine_c = {},
                lualine_x = {},
                lualine_y = {},
                lualine_z = { "tabs" },
            },
        })
    end,
}

return { M }
