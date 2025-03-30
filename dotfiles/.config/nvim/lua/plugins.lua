-- Ensure Packer is installed
local ensure_packer = function()
  local fn = vim.fn
  local install_path = fn.stdpath('data')..'/site/pack/packer/start/packer.nvim'
  if fn.empty(fn.glob(install_path)) > 0 then
    fn.system({'git', 'clone', '--depth', '1', 'https://github.com/wbthomason/packer.nvim', install_path})
    vim.cmd [[packadd packer.nvim]]
    return true
  end
  return false
end
local packer_bootstrap = ensure_packer()

require("packer").startup(function(use)
    -- Packer
    use "wbthomason/packer.nvim"

    -- General Utilities
    use "rhysd/vim-grammarous"
    use "tpope/vim-surround"
    use "easymotion/vim-easymotion"
    use "preservim/nerdcommenter"
    use "preservim/nerdtree"
    use "machakann/vim-highlightedyank"
    use "godlygeek/tabular"
    use "tmhedberg/SimpylFold"
    use "williamboman/mason.nvim"
    use "williamboman/mason-lspconfig.nvim"
    use {
        "windwp/nvim-autopairs",
        event = "InsertEnter",
        config = function()
            require("nvim-autopairs").setup {}
        end
    }

    -- Themes
    use "joshdick/onedark.vim"
    use "NLKNguyen/papercolor-theme"
    use "junegunn/seoul256.vim"

    -- Git
    use "airblade/vim-gitgutter"
    use "tpope/vim-fugitive"
    use "tpope/vim-rhubarb"

    -- UI
    use "vim-airline/vim-airline"
    use "vim-airline/vim-airline-themes"

    -- Completion/LSP
    use "hrsh7th/nvim-cmp"
    use "hrsh7th/cmp-nvim-lsp"
    use "hrsh7th/cmp-nvim-lua"
    use "hrsh7th/cmp-nvim-lsp-signature-help"
    use "hrsh7th/cmp-vsnip"
    use "hrsh7th/cmp-path"
    use "hrsh7th/cmp-buffer"
    use "hrsh7th/vim-vsnip"
    use "neovim/nvim-lspconfig"
    use "simrat39/rust-tools.nvim"

    -- Linting/Formatting
    use "dense-analysis/ale"

    -- Languages
    use "rust-lang/rust.vim"
    use "JuliaEditorSupport/julia-vim"
    use "lervag/vimtex"
    use "plasticboy/vim-markdown"
    use "elzr/vim-json"

    -- Treesitter
    use {
        "nvim-treesitter/nvim-treesitter",
        run = function()
            local ts_update = require("nvim-treesitter.install").update({ with_sync = true })
            ts_update()
        end,
    }

    -- Snippets
    use "SirVer/ultisnips"
    use "honza/vim-snippets"

    -- Documentation
    use "kkoomen/vim-doge"

    -- Markdown Preview
    use { "iamcco/markdown-preview.nvim", run = "cd app && yarn install" }
end)
