#!/bin/bash

# Check if stylua is installed
if ! command -v stylua &>/dev/null; then
    echo "stylua is not installed. Please install it first:"
    echo "You can install it using: cargo install stylua"
    exit 1
fi

# Base directory of Neovim config
NVIM_CONFIG_DIR="$HOME/.config/nvim"

# Create a stylua configuration file
cat <<EOF >"$NVIM_CONFIG_DIR/stylua.toml"
column_width = 96
line_endings = "Unix"
indent_type = "Spaces"
indent_width = 4
quote_style = "AutoPreferDouble"
no_call_parentheses = false
EOF

# Directories to format
DIRS=(
    "$NVIM_CONFIG_DIR/lua/plugins"
    "$NVIM_CONFIG_DIR/lua/core"
    "$NVIM_CONFIG_DIR"
)

# Function to format Lua files
format_lua_files() {
    local dir="$1"
    echo "Formatting Lua files in $dir..."
    find "$dir" -name "*.lua" -print0 | while IFS= read -r -d '' file; do
        # Skip the stylua.toml file if it exists in the search path
        if [[ "$(basename "$file")" != "stylua.toml" ]]; then
            echo "Formatting: $file"
            stylua "$file"
        fi
    done
}

# Format files in each directory
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        format_lua_files "$dir"
    else
        echo "Directory not found: $dir"
    fi
done

# Attempt to format init.lua in the base config directory if it exists
if [ -f "$NVIM_CONFIG_DIR/init.lua" ]; then
    echo "Formatting: $NVIM_CONFIG_DIR/init.lua"
    stylua "$NVIM_CONFIG_DIR/init.lua"
fi

# Clean up the temporary stylua configuration
rm "$NVIM_CONFIG_DIR/stylua.toml"

echo "Formatting complete!"
