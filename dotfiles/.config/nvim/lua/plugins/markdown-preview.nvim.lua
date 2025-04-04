local M = {
    "iamcco/markdown-preview.nvim",
    ft = { "markdown", "md" },
    build = "cd app && yarn install",
    cmd = { "MarkdownPreview", "MarkdownPreviewToggle" },
    config = function()
        vim.g.mkdp_auto_start = 0
        vim.g.mkdp_auto_close = 0
        vim.g.mkdp_refresh_slow = 1
        vim.g.mkdp_browser = "firefox"
    end,
}

return { M }
