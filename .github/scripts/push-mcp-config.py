#!/usr/bin/env python3
"""Push MCP configuration files to GitHub repositories.

This script programmatically commits MCP config files to repos,
enabling IDE-specific MCP server configurations.

Supported targets:
- .vscode/mcp.json - VS Code with Copilot
- .cursor/mcp.json - Cursor IDE

Usage:
    python push-mcp-config.py --repo jbcom/jbcom-control-center --target vscode
    python push-mcp-config.py --repo jbcom/extended-data-types --target all
    
Environment:
    GITHUB_JBCOM_TOKEN - GitHub PAT with repo scope
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)


# Default MCP configuration template
DEFAULT_MCP_CONFIG = {
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
}

# VS Code specific format (slightly different structure)
VSCODE_MCP_CONFIG = {
    "mcp": {
        "inputs": [
            {
                "type": "promptString",
                "id": "github_token",
                "description": "GitHub Personal Access Token",
                "password": True
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
            }
        }
    }
}


def get_github_token() -> str:
    """Get GitHub token from environment."""
    token = os.environ.get("GITHUB_JBCOM_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_JBCOM_TOKEN or GITHUB_TOKEN required")
        sys.exit(1)
    return token


def get_file_sha(token: str, owner: str, repo: str, path: str) -> str | None:
    """Get SHA of existing file (needed for updates)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get("sha")
    return None


def push_file(
    token: str,
    owner: str,
    repo: str,
    path: str,
    content: str,
    message: str
) -> bool:
    """Push a file to a GitHub repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Check if file exists (need SHA for update)
    sha = get_file_sha(token, owner, repo, path)
    
    payload = {
        "message": message,
        "content": base64.b64encode(content.encode()).decode(),
    }
    if sha:
        payload["sha"] = sha
    
    response = requests.put(url, headers=headers, json=payload)
    
    if response.status_code in (200, 201):
        action = "Updated" if sha else "Created"
        print(f"  ✅ {action}: {path}")
        return True
    else:
        print(f"  ❌ Failed: {path} - {response.status_code}: {response.text[:200]}")
        return False


def push_mcp_config(
    owner: str,
    repo: str,
    target: str,
    config_file: str | None = None
) -> bool:
    """Push MCP configuration to a repository."""
    token = get_github_token()
    
    print(f"\n📤 Pushing MCP config to {owner}/{repo}")
    
    # Load custom config if provided
    if config_file and Path(config_file).exists():
        with open(config_file) as f:
            custom_config = json.load(f)
        cursor_config = custom_config
        vscode_config = {"mcp": {"servers": custom_config.get("mcpServers", {})}}
    else:
        cursor_config = DEFAULT_MCP_CONFIG
        vscode_config = VSCODE_MCP_CONFIG
    
    success = True
    
    if target in ("cursor", "all"):
        content = json.dumps(cursor_config, indent=2)
        if not push_file(
            token, owner, repo,
            ".cursor/mcp.json",
            content,
            "chore: Add Cursor MCP configuration"
        ):
            success = False
    
    if target in ("vscode", "all"):
        content = json.dumps(vscode_config, indent=2)
        if not push_file(
            token, owner, repo,
            ".vscode/mcp.json",
            content,
            "chore: Add VS Code MCP configuration"
        ):
            success = False
    
    return success


def main():
    parser = argparse.ArgumentParser(
        description="Push MCP configuration to GitHub repositories"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="Repository in owner/repo format (e.g., jbcom/jbcom-control-center)"
    )
    parser.add_argument(
        "--target",
        choices=["vscode", "cursor", "all"],
        default="all",
        help="Target IDE(s) for MCP config"
    )
    parser.add_argument(
        "--config",
        help="Path to custom MCP config JSON file"
    )
    parser.add_argument(
        "--repos-file",
        help="File with list of repos (one per line) to update"
    )
    
    args = parser.parse_args()
    
    repos = []
    
    if args.repos_file and Path(args.repos_file).exists():
        with open(args.repos_file) as f:
            repos = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    else:
        repos = [args.repo]
    
    all_success = True
    for repo in repos:
        if "/" not in repo:
            print(f"⚠️  Skipping invalid repo format: {repo}")
            continue
        
        owner, repo_name = repo.split("/", 1)
        if not push_mcp_config(owner, repo_name, args.target, args.config):
            all_success = False
    
    print("\n" + ("✅ All done!" if all_success else "⚠️  Some operations failed"))
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()
