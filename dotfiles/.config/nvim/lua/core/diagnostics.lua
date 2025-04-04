-- Diagnostics Options
vim.diagnostic.config {
    virtual_text = false,
    update_in_insert = true,
    underline = true,
    severity_sort = false,
    float = {
        border = "rounded",
        source = "always",
        header = "",
        prefix = "",
    },
    signs = {
        text = {
            [vim.diagnostic.severity.ERROR] = "✕",
            [vim.diagnostic.severity.WARN] = "⚠",
            [vim.diagnostic.severity.HINT] = "→",
            [vim.diagnostic.severity.INFO] = "ℹ",
        },
        numhl = {
            [vim.diagnostic.severity.ERROR] = "",
            [vim.diagnostic.severity.WARN] = "",
            [vim.diagnostic.severity.HINT] = "",
            [vim.diagnostic.severity.INFO] = "",
        },
    },
}

-- Diagnostics UI Fix
vim.cmd [[
    set signcolumn=yes
    autocmd CursorHold * lua vim.diagnostic.open_float(nil, { focusable = false })
]]

-- Diagnostics Message Filter
function filter_array(a, f)
    local j = 1
    local n = #a
    for i, x in ipairs(a) do
        if f(x, i) then
            a[j] = x
            j = j + 1
        end
    end
    for i = j, n do
        a[i] = nil
    end
end

function filter_diagnostic(diagnostic)
    if diagnostic.source == "Pyright" then
        return false
    end
    return true
end

function on_publish_diagnostics_filtered(a, params, client_id, c, config)
    filter_array(params.diagnostics, filter_diagnostic)
    vim.lsp.diagnostic.on_publish_diagnostics(a, params, client_id, c, config)
end

vim.lsp.handlers["textDocument/publishDiagnostics"] = vim.lsp.with(on_publish_diagnostics_filtered, {})
