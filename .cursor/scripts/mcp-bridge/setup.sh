#!/bin/bash
# Make all MCP bridge scripts executable and add to PATH
# Run this after building Docker image

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Make all scripts executable
chmod +x "$SCRIPT_DIR"/*

# Add to PATH via symlinks
for script in "$SCRIPT_DIR"/*; do
    if [ -f "$script" ] && [ "$(basename "$script")" != "setup.sh" ]; then
        ln -sf "$script" /usr/local/bin/$(basename "$script")
    fi
done

echo "✅ MCP bridge scripts installed to /usr/local/bin/"
echo "Available commands:"
ls -1 /usr/local/bin/ | grep -E "aws-|github-mcp"
