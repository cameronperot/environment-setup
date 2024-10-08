" -----------------------------------------------------------------------------------------
" Plugins
" -----------------------------------------------------------------------------------------
" Automatically download vim-plug if not already available
if empty(glob('~/.local/share/nvim/site/autoload/plug.vim'))
  silent !curl -fLo ~/.local/share/nvim/site/autoload/plug.vim --create-dirs
    \ https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
  autocmd VimEnter * PlugInstall --sync | source $MYVIMRC
endif

call plug#begin('~/.local/share/nvim/plugged')

Plug 'rhysd/vim-grammarous'                                   " Grammar
Plug 'jiangmiao/auto-pairs'                                   " Bracket pairing
Plug 'tpope/vim-surround'                                     " Bracket surrounding
Plug 'easymotion/vim-easymotion'                              " Easy motion
Plug 'preservim/nerdcommenter'                                " Comments
Plug 'preservim/nerdtree'                                     " File navigation tree
Plug 'machakann/vim-highlightedyank'                          " Highlight yank area
Plug 'godlygeek/tabular'                                      " Text alignment
Plug 'tmhedberg/SimpylFold'                                   " Code folding
" treesitter might require one to run `cargo install tree-sitter-cli` (or via npm) beforehand
Plug 'nvim-treesitter/nvim-treesitter', {'do': ':TSUpdate'}   " Better code coloring
Plug 'joshdick/onedark.vim'                                   " Theme
Plug 'NLKNguyen/papercolor-theme'                             " Theme
Plug 'junegunn/seoul256.vim'                                  " Theme
Plug 'airblade/vim-gitgutter'                                 " Git
Plug 'tpope/vim-fugitive'                                     " Git
Plug 'tpope/vim-rhubarb'                                      " Git
Plug 'vim-airline/vim-airline'                                " Status bar
Plug 'vim-airline/vim-airline-themes'                         " Status bar themes
Plug 'bling/vim-bufferline'                                   " Display buffers in status bar
Plug 'Shougo/deoplete.nvim', { 'do': ':UpdateRemotePlugins' } " Autocomplete
Plug 'Shougo/deoplete-lsp'                                    " Autocomplete lsp
Plug 'neovim/nvim-lsp'                                        " Nvim lsp support
Plug 'neovim/nvim-lspconfig'                                  " Nvim lsp config
Plug 'dense-analysis/ale'                                     " Code linting
Plug 'rust-lang/rust.vim'                                     " Rust
Plug 'JuliaEditorSupport/julia-vim', { 'for': 'julia' }       " Julia
Plug 'davidhalter/jedi-vim', { 'for': 'python' }              " Python jedi
Plug 'zchee/deoplete-jedi', { 'for': 'python' }               " Python jedi autocomplete for deoplete
Plug 'deoplete-plugins/deoplete-clang'                        " C++ autocomplete
Plug 'lervag/vimtex'                                          " LaTeX
Plug 'plasticboy/vim-markdown'                                " Markdown
Plug 'elzr/vim-json'                                          " JSON
Plug 'honza/vim-snippets'                                     " Snippets
Plug 'SirVer/ultisnips'                                       " Snippet engine
Plug 'kkoomen/vim-doge', { 'do': { -> doge#install() } }      " DOcument GEneration
Plug 'iamcco/markdown-preview.nvim', { 'do': 'cd app & yarn install'  } " Markdown preview (requires nodejs and yarn)

call plug#end()

" -----------------------------------------------------------------------------------------
" General settings
" -----------------------------------------------------------------------------------------
set encoding=utf-8                                     " File encoding
set nofoldenable                                       " Disable folding
set foldmethod=indent                                  " Fold based on indentation
set splitbelow                                         " Open split below on horizontal split
set splitright                                         " Open split to the right on vertical split
set smartindent                                        " Smart autoindenting when starting a new line
set cursorline                                         " Highlight current line
set expandtab                                          " Expand tab into spaces
set tabstop=4                                          " Number of spaces per tab
set shiftwidth=4                                       " Number of spaces when autoindenting
set number relativenumber                              " Enable line numbers
set colorcolumn=98                                     " Number of characters per line
set ignorecase                                         " Ignore case in search patterns
set smartcase                                          " Override ignorecase if search pattern contains uppercase
set hidden                                             " Manage multiple buffers effectively
set pastetoggle=<F3>                                   " Toggle paste mode to insert literally
set scrolloff=8                                        " Min number of screen lines above/below cursor
set list listchars=tab:»·,trail:·                      " Show trailing whitespace
set wrap                                               " Line wrapping
set linebreak                                          " Line breaks
set showbreak=\ ↪                                      " Wrapped lines
set spell spelllang=en_us                              " Spell checking
colorscheme onedark                                    " Set theme
set notermguicolors                                    " Disable termguicolors
syntax enable                                          " Syntax highlighting
filetype plugin indent on                              " Enable filetype
highlight LineNr term=bold cterm=NONE ctermfg=DarkGrey ctermbg=NONE gui=NONE guifg=DarkGrey guibg=NONE
au FileType * set fo-=c fo-=r fo-=o                    " Disable auto continuing comment on next line
let g:python3_host_prog = $HOME . '/miniconda3/envs/dev/bin/python'

" Buffer navigation
nnoremap <leader>bd :bd<cr>
nnoremap <Leader>bb :ls<CR>:b<Space>
nnoremap <leader>af :ALEFix<cr>

" Remove trailing whitespace and new lines
function RemoveTrailingWhitespace()
    let save_cursor = getpos('.')
    silent! %s/\s\+$//e
    call setpos('.', save_cursor)
endfunction
function RemoveEndLines()
    let save_cursor = getpos('.')
    silent! %s/\($\n\s*\)\+\%$//e
    call setpos('.', save_cursor)
endfunction
autocmd BufWritePre * call RemoveTrailingWhitespace()
autocmd BufWritePre * call RemoveEndLines()

" Remap window navigation shortcuts
nnoremap <C-J> <C-W><C-J>
nnoremap <C-K> <C-W><C-K>
nnoremap <C-L> <C-W><C-L>
nnoremap <C-H> <C-W><C-H>

" Custom shortcuts
nnoremap <silent> <Leader>nh <cmd>nohlsearch<CR>

" Quick edit commands
command Viconfig :e ~\/.config\/nvim\/init.vim
command! -nargs=0 Sw w !sudo tee % > /dev/null

" Custom commands
command Spellcheck :set spell spelllang=en_us <CR>

" Disable ctrl-q since used in tmux
map <c-q> <nop>

" -----------------------------------------------------------------------------------------
" Plugin settings
" -----------------------------------------------------------------------------------------
" Autocomplete
inoremap <silent><expr> <TAB>  pumvisible() ? '<C-n>' : '<TAB>'
inoremap <silent><expr> <S-TAB>  pumvisible() ? '<C-p>' : '<TAB>'
let g:deoplete#enable_at_startup = 1
let g:deoplete#sources#jedi#python_path = python3_host_prog

" Airline
let g:airline_theme = 'onedark'
let g:airline#extensions#branch#enabled = 1
let g:airline#extensions#bufferline#overwrite_variables = 0
let g:airline_powerline_fonts = 1
let g:airline#extensions#tabline#enabled = 1
let g:airline#extensions#tabline#tab_nr_type = 1 " tab number
let g:airline#extensions#tabline#show_tab_nr = 1
let g:airline#extensions#tabline#formatter = 'default'
let g:airline#extensions#tabline#buffer_nr_show = 1
let g:airline#extensions#tabline#fnametruncate = 16
let g:airline#extensions#tabline#fnamecollapse = 2
let g:airline#extensions#tabline#formatter = 'unique_tail'
let g:airline#extensions#tabline#buffer_idx_mode = 1
let g:airline#extensions#tabline#left_sep = ' '
let g:airline#extensions#tabline#left_alt_sep = '|'
nmap <leader>1 <Plug>AirlineSelectTab1
nmap <leader>2 <Plug>AirlineSelectTab2
nmap <leader>3 <Plug>AirlineSelectTab3
nmap <leader>4 <Plug>AirlineSelectTab4
nmap <leader>5 <Plug>AirlineSelectTab5
nmap <leader>6 <Plug>AirlineSelectTab6
nmap <leader>7 <Plug>AirlineSelectTab7
nmap <leader>8 <Plug>AirlineSelectTab8
nmap <leader>9 <Plug>AirlineSelectTab9

" Ale
let g:ale_linters = {
    \ 'python': ['flake8', 'pylint', 'mypy'],
    \ 'sh': ['shellcheck'],
    \ 'vim': ['vint'],
    \ 'cpp': ['clang'],
\}
    ""\ '*': ['remove_trailing_lines', 'trim_whitespace'],
let g:ale_fixers = {
    \ 'python': ['black', 'isort'],
    \ 'cpp': ['clang-format'],
    \ 'sh': ['shfmt'],
\}
let g:ale_python_pylint_options = '--disable=missing-module-docstring,wrong-import-position'
let g:ale_python_flake8_options = '--max-line-length=98 --extend-ignore=E203'
let g:ale_python_black_options = '--config=$HOME/.config/black.conf'
let g:ale_python_isort_options = '--profile=black --line-length=98'
let g:ale_python_mypy_options = ''
let g:ale_sh_shfmt_options = '-i 4'
let g:ale_c_clangformat_options = '-style="{BasedOnStyle: llvm, IndentWidth: 4, ColumnLimit: 100, AllowShortFunctionsOnASingleLine: None, KeepEmptyLinesAtTheStartOfBlocks: false}"'
let g:ale_linters_explicit = 1
let g:ale_fix_on_save = 1
let g:ale_lint_on_insert_leave = 1

" Bufferline
let g:bufferline_echo = 0

" DOcument GEnerator
let g:doge_doc_standard_python = 'sphinx'
nmap <silent> <Leader>dg <Plug>(doge-generate)

" Jedi
let g:jedi#completions_enabled = 0
let g:jedi#use_splits_not_buffers = 'right'

" Markdown
autocmd filetype markdown set formatoptions+=ro
autocmd filetype markdown set comments=b:*,b:-,b:+,b:1.,n:>

" Markdown Preview
let g:mkdp_auto_start = 0
let g:mkdp_auto_close = 0
let g:mkdp_refresh_slow = 1
let g:mkdp_browser = 'firefox'

" NERDCommenter
let g:NERDSpaceDelims = 0

" NERDTree
let g:NERDTreeShowHidden = 1
let g:NERDTreeShowLineNumbers=1
let g:NERDTreeQuitOnOpen = 1
autocmd FileType nerdtree setlocal relativenumber
map <C-n> :NERDTreeToggle<CR>

" Treesitter
lua <<EOF
require'nvim-treesitter.configs'.setup {
    ensure_installed = {
        'bash',
        'cpp',
        'json',
        'julia',
        'latex',
        'lua',
        'python',
        'toml',
        'yaml'
    },
    ignore_install = { },
    highlight = {
      enable = true,
      disable = { },
    },
}
EOF

" UtiliSnips
let g:UltiSnipsExpandTrigger = '<C-K>'
let g:tex_flavor = 'latex'

" Vimtex
let g:vimtex_quickfix_ignore_filters = [
    \ 'Overfull',
    \ 'Underfull',
    \ 'Package hyperref Warning: Token not allowed in a PDF string',
    \ 'contains only floats.',
    \ "`h' float specifier changed to `ht'.",
\]
