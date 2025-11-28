#!/bin/bash
# Push MCP configuration files to GitHub repositories via PR
#
# This script creates a PR with MCP config files for repos with branch protection.
#
# Supported targets:
# - .vscode/mcp.json - VS Code with Copilot
# - .cursor/mcp.json - Cursor IDE
#
# Usage:
#   ./push-mcp-config.sh jbcom/jbcom-control-center vscode
#   ./push-mcp-config.sh jbcom/extended-data-types all
#   ./push-mcp-config.sh --list repos.txt all
#
# Environment:
#   GITHUB_JBCOM_TOKEN - GitHub PAT with repo scope

set -e

# Check for token
TOKEN="${GITHUB_JBCOM_TOKEN:-$GITHUB_TOKEN}"
if [ -z "$TOKEN" ]; then
    echo "❌ Error: GITHUB_JBCOM_TOKEN or GITHUB_TOKEN required"
    exit 1
fi

export GH_TOKEN="$TOKEN"

# VS Code MCP config template
VSCODE_CONFIG='{
  "mcp": {
    "inputs": [
      {
        "type": "promptString",
        "id": "github_token",
        "description": "GitHub Personal Access Token",
        "password": true
      }
    ],
    "servers": {
      "github": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
          "GITHUB_PERSONAL_ACCESS_TOKEN": "${input:github_token}"
        }
      },
      "filesystem": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "${workspaceFolder}"]
      },
      "git": {
        "command": "uvx",
        "args": ["mcp-server-git", "--repository", "${workspaceFolder}"]
      },
      "memory": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-memory"]
      }
    }
  }
}'

# Cursor MCP config template
CURSOR_CONFIG='{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_JBCOM_TOKEN}"
      },
      "type": "stdio"
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "."],
      "type": "stdio"
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "."],
      "type": "stdio"
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "type": "stdio"
    }
  }
}'

push_file_to_branch() {
    local repo="$1"
    local branch="$2"
    local path="$3"
    local content="$4"
    local message="$5"
    
    local encoded
    encoded=$(echo -n "$content" | base64 -w 0)
    
    # Check if file exists to get SHA
    local sha
    sha=$(gh api "/repos/${repo}/contents/${path}?ref=${branch}" --jq '.sha' 2>/dev/null || echo "")
    
    local payload
    if [ -n "$sha" ]; then
        payload=$(jq -n --arg msg "$message" --arg content "$encoded" --arg sha "$sha" --arg branch "$branch" \
            '{message: $msg, content: $content, sha: $sha, branch: $branch}')
        action="Updated"
    else
        payload=$(jq -n --arg msg "$message" --arg content "$encoded" --arg branch "$branch" \
            '{message: $msg, content: $content, branch: $branch}')
        action="Created"
    fi
    
    if gh api "/repos/${repo}/contents/${path}" -X PUT --input - <<< "$payload" > /dev/null 2>&1; then
        echo "  ✅ $action: $path"
        return 0
    else
        echo "  ❌ Failed: $path"
        return 1
    fi
}

create_branch() {
    local repo="$1"
    local branch="$2"
    
    # Get main branch SHA
    local sha
    sha=$(gh api "/repos/${repo}/git/refs/heads/main" --jq '.object.sha' 2>/dev/null)
    
    if [ -z "$sha" ]; then
        echo "  ❌ Could not get main branch SHA"
        return 1
    fi
    
    # Create branch
    local payload
    payload=$(jq -n --arg ref "refs/heads/${branch}" --arg sha "$sha" '{ref: $ref, sha: $sha}')
    
    if gh api "/repos/${repo}/git/refs" -X POST --input - <<< "$payload" > /dev/null 2>&1; then
        echo "  ✅ Created branch: $branch"
        return 0
    else
        echo "  ⚠️  Branch may already exist: $branch"
        return 0
    fi
}

create_pr() {
    local repo="$1"
    local branch="$2"
    local target="$3"
    
    local title="chore: Add MCP configuration for IDE integration"
    local body="## Summary

Adds MCP (Model Context Protocol) configuration files for IDE integration.

### Files Added
"
    
    if [ "$target" = "vscode" ] || [ "$target" = "all" ]; then
        body+="- \`.vscode/mcp.json\` - VS Code with GitHub Copilot
"
    fi
    if [ "$target" = "cursor" ] || [ "$target" = "all" ]; then
        body+="- \`.cursor/mcp.json\` - Cursor IDE
"
    fi
    
    body+="
### MCP Servers Configured
- **github** - GitHub repository access
- **filesystem** - Local file system access
- **git** - Git operations
- **memory** - Persistent memory

### Usage
After merge, IDE will auto-detect the MCP configuration and prompt for GitHub token authentication.
"
    
    local pr_url
    pr_url=$(gh pr create --repo "$repo" --head "$branch" --base main \
        --title "$title" --body "$body" 2>&1)
    
    if [[ "$pr_url" =~ github.com ]]; then
        echo "  ✅ Created PR: $pr_url"
        return 0
    else
        echo "  ⚠️  PR may already exist or failed: $pr_url"
        return 0
    fi
}

push_mcp_config() {
    local repo="$1"
    local target="$2"
    
    echo ""
    echo "📤 Pushing MCP config to $repo via PR"
    
    local branch="chore/add-mcp-config-$(date +%Y%m%d)"
    
    # Create branch
    if ! create_branch "$repo" "$branch"; then
        return 1
    fi
    
    local success=0
    
    if [ "$target" = "cursor" ] || [ "$target" = "all" ]; then
        if ! push_file_to_branch "$repo" "$branch" ".cursor/mcp.json" "$CURSOR_CONFIG" "chore: Add Cursor MCP configuration"; then
            success=1
        fi
    fi
    
    if [ "$target" = "vscode" ] || [ "$target" = "all" ]; then
        if ! push_file_to_branch "$repo" "$branch" ".vscode/mcp.json" "$VSCODE_CONFIG" "chore: Add VS Code MCP configuration"; then
            success=1
        fi
    fi
    
    # Create PR
    create_pr "$repo" "$branch" "$target"
    
    return $success
}

usage() {
    echo "Usage: $0 <owner/repo> <target>"
    echo "       $0 --list <repos-file> <target>"
    echo ""
    echo "Arguments:"
    echo "  owner/repo    Repository in owner/repo format"
    echo "  target        One of: vscode, cursor, all"
    echo ""
    echo "Options:"
    echo "  --list FILE   Process multiple repos from file (one per line)"
    echo ""
    echo "Environment:"
    echo "  GITHUB_JBCOM_TOKEN    GitHub PAT with repo scope"
    echo ""
    echo "Examples:"
    echo "  $0 jbcom/jbcom-control-center vscode"
    echo "  $0 jbcom/extended-data-types all"
    echo "  $0 --list repos.txt all"
    echo ""
    echo "Note: Creates a PR due to branch protection. Merge manually or auto-merge if enabled."
}

# Main
if [ $# -lt 2 ]; then
    usage
    exit 1
fi

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    usage
    exit 0
fi

if [ "$1" = "--list" ]; then
    if [ ! -f "$2" ]; then
        echo "❌ Error: File not found: $2"
        exit 1
    fi
    target="$3"
    all_success=0
    while IFS= read -r repo || [ -n "$repo" ]; do
        [ -z "$repo" ] && continue
        [[ "$repo" =~ ^# ]] && continue
        if ! push_mcp_config "$repo" "$target"; then
            all_success=1
        fi
    done < "$2"
    exit $all_success
else
    repo="$1"
    target="$2"
    
    if [[ ! "$repo" =~ / ]]; then
        echo "❌ Error: Invalid repo format. Use owner/repo"
        exit 1
    fi
    
    if [[ ! "$target" =~ ^(vscode|cursor|all)$ ]]; then
        echo "❌ Error: Invalid target. Use: vscode, cursor, or all"
        exit 1
    fi
    
    push_mcp_config "$repo" "$target"
fi

echo ""
echo "✅ Done!"
