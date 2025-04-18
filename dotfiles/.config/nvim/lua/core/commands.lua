vim.api.nvim_create_user_command("Scratch", function()
    vim.cmd("edit ~/tmp/scratch.md")
end, {})
