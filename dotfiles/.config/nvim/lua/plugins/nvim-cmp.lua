local M = {
    "hrsh7th/nvim-cmp",
    event = "InsertEnter",
    config = function()
        local cmp = require("cmp")
        cmp.setup({
            snippet = {
                expand = function(args)
                    vim.fn["vsnip#anonymous"](args.body)
                end,
            },
            mapping = {
                ["<C-p>"] = cmp.mapping.select_prev_item(),
                ["<C-n>"] = cmp.mapping.select_next_item(),
                ["<Tab>"] = cmp.mapping.select_next_item(),
                ["<S-Tab>"] = cmp.mapping.select_prev_item(),
                ["<C-d>"] = cmp.mapping.scroll_docs(8),
                ["<C-u>"] = cmp.mapping.scroll_docs(-8),
                ["<C-Space>"] = cmp.mapping.complete(),
                ["<C-e>"] = cmp.mapping.close(),
                ["<CR>"] = cmp.mapping.confirm({
                    behavior = cmp.ConfirmBehavior.Insert,
                    select = true,
                }),
            },
            sources = {
                { name = "path" },
                { name = "nvim_lsp", keyword_length = 2 },
                { name = "nvim_lsp_signature_help" },
                { name = "nvim_lua", keyword_length = 2 },
                { name = "buffer", keyword_length = 2 },
                { name = "vsnip", keyword_length = 2 },
                { name = "ultisnips", keyword_length = 2 },
                { name = "calc" },
            },
            window = {
                completion = cmp.config.window.bordered(),
                documentation = cmp.config.window.bordered(),
            },
            formatting = {
                fields = { "menu", "abbr", "kind" },
                format = function(entry, item)
                    local menu_icon = {
                        nvim_lsp = "λ",
                        vsnip = "⋗",
                        buffer = "Ω",
                        path = "🖫",
                    }
                    item.menu = menu_icon[entry.source.name]
                    return item
                end,
            },
        })
    end,
}

return { M }
