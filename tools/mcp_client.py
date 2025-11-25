#!/usr/bin/env python3
"""MCP client for background agents.

This allows background agents (like Cursor background agents) to call MCP servers
via the mcp-proxy HTTP interface instead of trying to spawn MCP servers directly.
"""

import json
import os
import sys
from typing import Any
from urllib.parse import urljoin

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)


class MCPClient:
    """Client for calling MCP servers via mcp-proxy."""

    def __init__(self, proxy_url: str = "http://localhost:3000"):
        """Initialize MCP client.

        Args:
            proxy_url: Base URL of mcp-proxy server
        """
        self.proxy_url = proxy_url
        self.session = requests.Session()

    def call(self, server: str, method: str, params: dict[str, Any] | None = None) -> Any:
        """Call an MCP server method.

        Args:
            server: Server name (github, filesystem, git)
            method: Method name (e.g., 'search_repositories')
            params: Method parameters

        Returns:
            Method result

        Example:
            >>> client = MCPClient()
            >>> repos = client.call('github', 'search_repositories', {
            ...     'query': 'org:jbcom',
            ...     'sort': 'updated'
            ... })
        """
        url = urljoin(self.proxy_url, f"/{server}/{method}")

        try:
            response = self.session.post(
                url,
                json=params or {},
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"ERROR: MCP call failed: {e}")
            print(f"  Server: {server}")
            print(f"  Method: {method}")
            print(f"  URL: {url}")
            raise


# Convenience functions for common operations
class GitHubMCP:
    """GitHub MCP operations."""

    def __init__(self, client: MCPClient):
        self.client = client

    def search_repositories(self, query: str, **kwargs: Any) -> dict:
        """Search repositories."""
        params = {"query": query, **kwargs}
        return self.client.call("github", "search_repositories", params)

    def create_pull_request(
        self, owner: str, repo: str, title: str, body: str, head: str, base: str
    ) -> dict:
        """Create a pull request."""
        params = {
            "owner": owner,
            "repo": repo,
            "title": title,
            "body": body,
            "head": head,
            "base": base,
        }
        return self.client.call("github", "create_pull_request", params)

    def list_workflow_runs(self, owner: str, repo: str, **kwargs: Any) -> dict:
        """List workflow runs."""
        params = {"owner": owner, "repo": repo, **kwargs}
        return self.client.call("github", "list_workflow_runs", params)

    def list_issues(self, owner: str, repo: str, **kwargs: Any) -> dict:
        """List issues."""
        params = {"owner": owner, "repo": repo, **kwargs}
        return self.client.call("github", "list_issues", params)

    def get_file_contents(self, owner: str, repo: str, path: str) -> dict:
        """Get file contents."""
        params = {"owner": owner, "repo": repo, "path": path}
        return self.client.call("github", "get_file_contents", params)


class FilesystemMCP:
    """Filesystem MCP operations."""

    def __init__(self, client: MCPClient):
        self.client = client

    def read_file(self, path: str) -> str:
        """Read file contents."""
        result = self.client.call("filesystem", "read_file", {"path": path})
        return result.get("content", "")

    def write_file(self, path: str, content: str) -> None:
        """Write file contents."""
        self.client.call("filesystem", "write_file", {"path": path, "content": content})

    def list_directory(self, path: str) -> list[str]:
        """List directory contents."""
        result = self.client.call("filesystem", "list_directory", {"path": path})
        return result.get("files", [])


class GitMCP:
    """Git MCP operations."""

    def __init__(self, client: MCPClient):
        self.client = client

    def status(self) -> dict:
        """Get git status."""
        return self.client.call("git", "git_status", {})

    def diff(self, **kwargs: Any) -> str:
        """Get git diff."""
        result = self.client.call("git", "git_diff", kwargs)
        return result.get("diff", "")

    def commit(self, message: str, **kwargs: Any) -> dict:
        """Make a commit."""
        params = {"message": message, **kwargs}
        return self.client.call("git", "git_commit", params)


# Main client with all MCP servers
class MCP:
    """Main MCP client with access to all servers."""

    def __init__(self, proxy_url: str = "http://localhost:3000"):
        """Initialize MCP client.

        Args:
            proxy_url: Base URL of mcp-proxy server
        """
        client = MCPClient(proxy_url)
        self.github = GitHubMCP(client)
        self.filesystem = FilesystemMCP(client)
        self.git = GitMCP(client)


def main() -> None:
    """Test MCP client."""
    print("Testing MCP client...")

    # Check if proxy is running
    try:
        response = requests.get("http://localhost:3000/health", timeout=5)
        print(f"✅ MCP Proxy is running: {response.status_code}")
    except requests.exceptions.RequestException:
        print("❌ MCP Proxy is not running!")
        print("   Start it with: ./tools/start-mcp-proxy.sh")
        sys.exit(1)

    # Test GitHub MCP
    mcp = MCP()

    try:
        print("\n🔍 Testing GitHub MCP - Searching for jbcom repos...")
        repos = mcp.github.search_repositories("org:jbcom", sort="updated", per_page=5)
        print(f"   Found {len(repos.get('items', []))} repositories")
        for repo in repos.get("items", [])[:3]:
            print(f"   - {repo['name']}")

        print("\n✅ MCP client is working!")
    except Exception as e:
        print(f"\n❌ MCP client test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
