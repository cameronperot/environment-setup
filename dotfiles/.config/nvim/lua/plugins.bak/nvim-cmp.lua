local M = {
    "hrsh7th/nvim-cmp",
    event = "InsertEnter",
    dependencies = {
        "hrsh7th/cmp-nvim-lsp",
        "hrsh7th/cmp-buffer",
        "hrsh7th/cmp-path",
        "hrsh7th/cmp-nvim-lua",
        "hrsh7th/cmp-nvim-lsp-signature-help",
        "saadparwaiz1/cmp_luasnip",
        "L3MON4D3/LuaSnip",
    },
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
                -- ["<Tab>"] = cmp.mapping.select_next_item(),
                -- ["<S-Tab>"] = cmp.mapping.select_prev_item(),
                ["<Tab>"] = cmp.mapping(function(fallback)
                    if cmp.visible() then
                        cmp.select_next_item()
                    elseif luasnip.expand_or_jumpable() then
                        luasnip.expand_or_jump()
                    else
                        fallback()
                    end
                end, { "i", "s" }),
                ["<S-Tab>"] = cmp.mapping(function(fallback)
                    if cmp.visible() then
                        cmp.select_prev_item()
                    elseif luasnip.jumpable(-1) then
                        luasnip.jump(-1)
                    else
                        fallback()
                    end
                end, { "i", "s" }),
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
                { name = "lua_snip", keyword_length = 2 },
                { name = "calc" },
            },
            sorting = {
                priority_weight = 2,
                comparators = {
                    cmp.config.compare.offset,
                    cmp.config.compare.exact,
                    cmp.config.compare.score,
                    cmp.config.compare.recently_used,
                    cmp.config.compare.kind,
                    cmp.config.compare.sort_text,
                    cmp.config.compare.length,
                    cmp.config.compare.order,
                },
            },
            window = {
                completion = cmp.config.window.bordered(),
                documentation = cmp.config.window.bordered(),
            },
            formatting = {
                fields = { "kind", "abbr", "menu" },
                format = function(entry, item)
                    local menu_icon = {
                        nvim_lsp = "λ",
                        luasnip = "⋗",
                        buffer = "Ω",
                        path = "🖫",
                        nvim_lua = "Λ",
                        calc = "Σ",
                        nvim_lsp_signature_help = "󰊕",
                    }
                    item.menu = menu_icon[entry.source.name]
                    return item
                end,
            },
        })
    end,
}

return { M }
