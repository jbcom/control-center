# Model Context Protocol (MCP) Setup

This directory contains MCP server configuration and Cursor agents that leverage MCP for powerful GitHub integration.

## What is MCP?

Model Context Protocol (MCP) is an open protocol that enables AI assistants to connect to external tools and data sources. Instead of using hacky CLI commands like `gh`, MCP provides a standardized way to interact with GitHub, filesystems, and other services.

## MCP Servers Configured

### 1. GitHub MCP Server
- **Package**: `@modelcontextprotocol/server-github`
- **Capabilities**:
  - Create/update files in repos
  - Create pull requests and issues
  - Search code and repositories
  - Manage branches and commits
  - Check workflow runs
  - Much more...

### 2. Filesystem MCP Server  
- **Package**: `@modelcontextprotocol/server-filesystem`
- **Capabilities**:
  - Read/write files
  - Create directories
  - Search files
  - Move/rename files

### 3. Git MCP Server
- **Package**: `@modelcontextprotocol/server-git`
- **Capabilities**:
  - Git status, diff, log
  - Stage and commit changes
  - View commit history

## Configuration Files

### `mcp.json`
Defines MCP servers that Cursor can connect to. This is automatically loaded by Cursor.

### `process-compose.yml`
Optional: Use with [process-compose](https://github.com/F1bonacc1/process-compose) to manage MCP servers as background processes.

```bash
# Install process-compose
brew install process-compose  # macOS
# or
go install github.com/F1bonacc1/process-compose@latest

# Run all MCP servers
process-compose up
```

### `agents/`
Custom Cursor agents that leverage MCP tools:

- **`jbcom-ecosystem-manager.md`** - Central coordinator for the entire ecosystem
- **`ci-deployer.md`** - Specialized in CI/CD workflow deployment

## Usage

### Automatic (Recommended)
Cursor automatically detects `mcp.json` and starts MCP servers when needed.

### Manual (with process-compose)
```bash
cd /workspace/.cursor
process-compose up
```

This keeps MCP servers running in the background for instant access.

## Environment Variables

MCP servers need access to GitHub:

```bash
export GITHUB_JBCOM_TOKEN="your_token_here"
```

Or configure in Cursor settings:
```json
{
  "cursor.mcp.env": {
    "GITHUB_JBCOM_TOKEN": "your_token_here"
  }
}
```

## Cursor Agent Usage

Instead of:
```bash
gh pr create --title "..."
```

Cursor agents with MCP can do:
```typescript
await mcp.github.create_pull_request({
  owner: "jbcom",
  repo: "extended-data-types",
  title: "Update CI/CD",
  body: "...",
  head: "feature-branch",
  base: "main"
});
```

This is:
- ✅ Faster
- ✅ More reliable  
- ✅ Better error handling
- ✅ Type-safe
- ✅ No shell command parsing

## Benefits Over CLI

| Feature | `gh` CLI | MCP |
|---------|----------|-----|
| Speed | Slow (subprocess spawn) | Fast (direct API) |
| Error Handling | Parse stderr | Structured errors |
| Type Safety | None | Full TypeScript types |
| Rate Limiting | Manual | Automatic |
| Batching | Manual loops | Built-in |
| Authentication | Token files | Environment vars |

## Available MCP Operations

See agent files for comprehensive lists, but key operations include:

### GitHub
- `create_pull_request`
- `create_issue`
- `search_repositories`
- `search_code`
- `list_workflow_runs`
- `get_file_contents`
- `create_or_update_file`
- `create_branch`
- And 20+ more...

### Filesystem
- `read_file`
- `write_file`
- `list_directory`
- `search_files`
- `create_directory`

### Git
- `git_status`
- `git_diff`
- `git_commit`
- `git_log`

## Debugging

Check MCP server logs:
```bash
tail -f /tmp/mcp-github.log
tail -f /tmp/mcp-filesystem.log
tail -f /tmp/mcp-git.log
```

Or use Cursor's MCP inspector (if available in settings).

## References

- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [MCP GitHub Server](https://github.com/modelcontextprotocol/servers/tree/main/src/github)
- [Process Compose](https://github.com/F1bonacc1/process-compose)
- [Cursor Documentation](https://docs.cursor.com/)

---

**This setup gives Cursor agents the same powerful capabilities that GitHub Copilot has**, without relying on brittle shell commands.
