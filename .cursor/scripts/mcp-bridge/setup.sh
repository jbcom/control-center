#!/bin/bash
# Setup script for MCP bridge CLI wrappers
# Makes all wrappers executable and optionally symlinks to /usr/local/bin

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🔧 Setting up MCP bridge CLI wrappers..."

# Make all wrapper scripts executable
chmod +x "$SCRIPT_DIR"/{aws-iac,aws-serverless,aws-api,aws-cdk,aws-cfn,aws-support,aws-pricing,billing-cost,aws-docs,github-mcp}

echo "✅ Made wrappers executable"

# Optionally symlink to /usr/local/bin for global access
if [ "$1" = "--global" ]; then
  echo "🔗 Creating global symlinks in /usr/local/bin..."
  
  for script in aws-iac aws-serverless aws-api aws-cdk aws-cfn aws-support aws-pricing billing-cost aws-docs github-mcp; do
    if [ -L "/usr/local/bin/$script" ]; then
      rm "/usr/local/bin/$script"
    fi
    ln -s "$SCRIPT_DIR/$script" "/usr/local/bin/$script"
    echo "  ✓ $script"
  done
  
  echo "✅ Global symlinks created"
else
  echo "ℹ️  Run with --global to create symlinks in /usr/local/bin"
  echo "   Or add to PATH: export PATH=\"$SCRIPT_DIR:\$PATH\""
fi

echo ""
echo "🎉 MCP bridge setup complete!"
echo ""
echo "Usage examples:"
echo "  aws-iac list_terraform_modules '{\"directory\": \"/workspace\"}'"
echo "  aws-serverless list_lambda_functions '{\"region\": \"us-east-1\"}'"
echo "  github-mcp list_issues '{\"owner\": \"jbcom\", \"repo\": \"extended-data-types\"}'"
echo ""
echo "To see available tools for a wrapper:"
echo "  aws-iac"
echo "  aws-serverless"
echo "  github-mcp"
