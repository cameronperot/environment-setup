-- Bootstrap Lazy
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
    vim.fn.system({
        "git",
        "clone",
        "--filter=blob:none",
        "https://github.com/folke/lazy.nvim.git",
        "--branch=stable",
        lazypath,
    })
end
vim.opt.rtp:prepend(lazypath)

-- Enable Lua module loader cache for performance
vim.loader.enable()

-- Setup Lazy and load plugins
require("lazy").setup("plugins")

-- Load configurations
require("core.options")
require("core.keymaps")
require("core.commands")
require("core.diagnostics")

-- Fedora installs: sudo dnf install luarocks cmake ctags
-- Debian installs: sudo apt-get install luarocks cmake exuberant-ctags
-- Cargo installs: cargo install stylua tree-sitter-cli
-- Mason installs: MasonInstall codelldb

-- Nerd Fonts
-- https://www.nerdfonts.com/font-downloads
-- https://github.com/ryanoasis/nerd-fonts/releases/download/v3.3.0/JetBrainsMono.zip

-- Plugins to look into:
-- https://nvimdev.github.io/lspsaga/
