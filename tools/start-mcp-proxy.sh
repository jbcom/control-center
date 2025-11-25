#!/bin/bash
# Start mcp-proxy to make MCP servers accessible to background agents

set -e

echo "🚀 Starting MCP Proxy for Background Agents"

# Check if mcp-proxy is installed
if ! command -v mcp-proxy &> /dev/null; then
    echo "📦 Installing mcp-proxy..."
    cd /tmp
    if [ ! -d "mcp-proxy" ]; then
        git clone https://github.com/sparfenyuk/mcp-proxy.git
    fi
    cd mcp-proxy
    npm install
    npm link
fi

# Start MCP proxy with config from .cursor/mcp.json
echo "🔧 Starting MCP servers via proxy..."

# Export GitHub token
export GITHUB_PERSONAL_ACCESS_TOKEN="${GITHUB_JBCOM_TOKEN:-$GITHUB_TOKEN}"

# Start mcp-proxy in background
mcp-proxy --config /workspace/.cursor/mcp.json --port 3000 &
MCP_PROXY_PID=$!

echo "✅ MCP Proxy started on http://localhost:3000 (PID: $MCP_PROXY_PID)"
echo "   GitHub MCP: http://localhost:3000/github"
echo "   Filesystem MCP: http://localhost:3000/filesystem"
echo "   Git MCP: http://localhost:3000/git"
echo ""
echo "💡 Background agents can now make HTTP requests to MCP servers"
echo "   Example: curl -X POST http://localhost:3000/github/search_repositories"
echo ""
echo "⏹️  To stop: kill $MCP_PROXY_PID"

# Keep proxy running
wait $MCP_PROXY_PID
