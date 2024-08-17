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

Plug 'jiangmiao/auto-pairs'                                   " Bracket pairing
Plug 'tpope/vim-surround'                                     " Bracket surrounding
Plug 'easymotion/vim-easymotion'                              " Easy motion
Plug 'preservim/nerdcommenter'                                " Comments
Plug 'machakann/vim-highlightedyank'                          " Highlight yank area
Plug 'godlygeek/tabular'                                      " Text alignment
Plug 'tmhedberg/SimpylFold'                                   " Code folding

call plug#end()

" -----------------------------------------------------------------------------------------
" Vim settings
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
set ignorecase                                         " Ignore case in search patterns
set smartcase                                          " Override ignorecase if search pattern contains uppercase
set hidden                                             " Manage multiple buffers effectively
set pastetoggle=<F3>                                   " Toggle paste mode to insert literally
set scrolloff=8                                        " Min number of screen lines above/below cursor
set list listchars=tab:»·,trail:·                      " Show trailing whitespace
set wrap                                               " Line wrapping
set linebreak                                          " Line breaks
set showbreak=\ ↪                                      " Wrapped lines
filetype plugin indent on                              " Enable filetype
highlight LineNr term=bold cterm=NONE ctermfg=DarkGrey ctermbg=NONE gui=NONE guifg=DarkGrey guibg=NONE
au FileType * set fo-=c fo-=r fo-=o                    " Disable auto continuing comment on next line
let g:python3_host_prog = $HOME . "/miniconda3/envs/dev/bin/python"

" Custom shortcuts
nnoremap <silent> <Leader>nh <cmd>nohlsearch<CR>

" -----------------------------------------------------------------------------------------
" Plugin settings
" -----------------------------------------------------------------------------------------
" NERDCommenter
let g:NERDSpaceDelims = 0
