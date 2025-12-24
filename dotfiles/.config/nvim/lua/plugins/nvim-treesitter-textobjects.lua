local M = {
    "nvim-treesitter/nvim-treesitter-textobjects",
    branch = "main",
    lazy = false,
    dependencies = { "nvim-treesitter/nvim-treesitter" },
    config = function()
        local select = require("nvim-treesitter-textobjects.select")
        local move = require("nvim-treesitter-textobjects.move")
        local swap = require("nvim-treesitter-textobjects.swap")

        -- Select text objects
        local select_maps = {
            { "af", "@function.outer" },
            { "if", "@function.inner" },
            { "ac", "@class.outer" },
            { "ic", "@class.inner" },
            { "ai", "@conditional.outer" },
            { "ii", "@conditional.inner" },
            { "al", "@loop.outer" },
            { "il", "@loop.inner" },
            { "aa", "@parameter.outer" },
            { "ia", "@parameter.inner" },
            { "a/", "@comment.outer" },
        }
        for _, m in ipairs(select_maps) do
            vim.keymap.set({ "x", "o" }, m[1], function()
                select.select_textobject(m[2], "textobjects")
            end)
        end

        -- Move to next/previous
        local move_maps = {
            { "]f", "goto_next_start", "@function.outer" },
            { "]c", "goto_next_start", "@class.outer" },
            { "]a", "goto_next_start", "@parameter.outer" },
            { "]F", "goto_next_end", "@function.outer" },
            { "]C", "goto_next_end", "@class.outer" },
            { "[f", "goto_previous_start", "@function.outer" },
            { "[c", "goto_previous_start", "@class.outer" },
            { "[a", "goto_previous_start", "@parameter.outer" },
            { "[F", "goto_previous_end", "@function.outer" },
            { "[C", "goto_previous_end", "@class.outer" },
        }
        for _, m in ipairs(move_maps) do
            vim.keymap.set({ "n", "x", "o" }, m[1], function()
                move[m[2]](m[3], "textobjects")
            end)
        end

        -- Swap parameters
        vim.keymap.set("n", "<Leader>a", function()
            swap.swap_next("@parameter.inner")
        end)
        vim.keymap.set("n", "<Leader>A", function()
            swap.swap_previous("@parameter.inner")
        end)
    end,
}

return { M }
