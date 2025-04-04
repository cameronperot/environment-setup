local M = {
    "puremourning/vimspector",
    cmd = { "VimspectorInstall", "VimspectorUpdate", "VimspectorReset", "VimspectorEval" },
    config = function()
        vim.cmd [[
            let g:vimspector_sidebar_width = 85
            let g:vimspector_bottombar_height = 15
            let g:vimspector_terminal_maxwidth = 70
        ]]
    end,
}

return { M }
