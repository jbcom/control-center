# MCP Server Configuration Guide

## Overview

This repository uses **MCP (Model Context Protocol)** servers to provide AI agents with structured access to tools and data. The configuration is centrally managed in `.ruler/ruler.toml` and automatically distributed to all supported agent platforms.

## What is MCP?

MCP (Model Context Protocol) is a standardized protocol for connecting AI agents to external tools and data sources. It allows agents to:

- Access file systems
- Execute git operations
- Call GitHub APIs
- Query databases
- Interact with cloud services
- And more...

## Configuration Architecture

```
.ruler/ruler.toml          ← Single source of truth
       ↓ (ruler apply)
       ├→ .cursor/mcp.json           (Cursor IDE)
       ├→ .github/copilot/mcp.json   (GitHub Copilot - future)
       ├→ CLAUDE.md                  (Claude Desktop)
       ├→ .aider.conf.yml            (Aider)
       └→ [Other agent configs]      (Platform-specific)
```

## MCP Servers Defined

### Core Development Servers

#### 1. **filesystem**
- **Purpose:** Access repository files
- **Command:** `npx -y @modelcontextprotocol/server-filesystem /workspace`
- **Access:** Read/write files in `/workspace`
- **Use:** File operations, code reading, editing

#### 2. **git**
- **Purpose:** Git repository operations
- **Command:** `uvx mcp-server-git --repository /workspace`
- **Access:** Git commands, history, branches
- **Use:** Commits, diffs, status checks

#### 3. **github**
- **Purpose:** GitHub API access
- **Command:** `npx -y @modelcontextprotocol/server-github`
- **Credentials:** Uses `GITHUB_JBCOM_TOKEN` environment variable
- **Use:** PRs, issues, workflows, releases

#### 4. **memory**
- **Purpose:** Persistent agent memory
- **Command:** `npx -y @modelcontextprotocol/server-memory`
- **Use:** Remember context across sessions

### Agent Coordination Servers

#### 5. **conport**
- **Purpose:** Context portal for agent state management
- **Command:** `uvx --from context-portal-mcp conport-mcp --mode stdio --workspace_id /workspace`
- **Config:** `CONPORT_FILES=projectBrief.md`
- **Use:** Share context between agents

#### 6. **cursor_agents**
- **Purpose:** Manage Cursor background agents
- **Command:** `cursor-background-agent-mcp-server`
- **Credentials:** Uses `CURSOR_API_KEY`, `CURSOR_WORKSPACE_ID`
- **Use:** Spawn, monitor, control background agents

#### 7. **aider**
- **Purpose:** AI pair programming integration
- **Command:** `aider --mcp`
- **Credentials:** Uses `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
- **Use:** Code forensics, validation

### AWS Infrastructure Servers

All AWS servers use `uvx awslabs.<server-name>@latest` for easy updates.

#### 8. **aws-iac** - Infrastructure as Code
- CloudFormation, CDK, best practices, security validation

#### 9. **aws-serverless** - Serverless Services
- Lambda, SAM, Step Functions, API Gateway

#### 10. **aws-api** - Direct AWS API Access
- Any AWS service via boto3

#### 11. **aws-cdk** - AWS CDK Development
- CDK with compliance checks

#### 12. **aws-cfn** - CloudFormation
- Template and stack operations

#### 13. **aws-support** - AWS Support API
- Case management

#### 14. **aws-pricing** - AWS Pricing API
- Cost analysis

#### 15. **billing-cost-management** - Billing & Costs
- Cost Explorer, Budgets, Cost and Usage Reports

#### 16. **aws-documentation** - AWS Docs
- Real-time access to official AWS documentation

### Documentation Servers

#### 17. **python-stdlib**
- **Purpose:** Python standard library documentation
- **Command:** `npx -y @modelcontextprotocol/server-python-stdlib`
- **Use:** Python API reference

## How Ruler Manages MCP

### Adding a New MCP Server

1. **Edit `.ruler/ruler.toml`:**

```toml
[mcp_servers.my-new-server]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-my-new-server"]

[mcp_servers.my-new-server.env]
API_KEY = "${MY_API_KEY}"
```

2. **Run `ruler apply`:**

```bash
ruler apply
```

This automatically updates:
- `.cursor/mcp.json`
- Agent-specific configurations
- `.gitignore` entries

3. **Verify in Cursor:**

Open `.cursor/mcp.json` and verify the new server appears.

### Environment Variables

MCP servers can use environment variables for credentials:

```toml
[mcp_servers.github.env]
GITHUB_PERSONAL_ACCESS_TOKEN = "${GITHUB_JBCOM_TOKEN}"
```

**Available in this environment:**
- `GITHUB_JBCOM_TOKEN` - jbcom org access
- `CURSOR_API_KEY` - Cursor agent API
- `CURSOR_WORKSPACE_ID` - Workspace identifier
- `ANTHROPIC_API_KEY` - Claude API
- `OPENAI_API_KEY` - OpenAI API
- `AWS_PROFILE` - AWS profile name
- `AWS_REGION` - AWS region

### Server Types

```toml
# Standard stdio server
[mcp_servers.example]
command = "npx"
args = ["-y", "@example/mcp-server"]
type = "stdio"  # Default, can be omitted

# HTTP server (future)
[mcp_servers.example-http]
url = "http://localhost:3000/mcp"
type = "http"
```

## Testing MCP Servers

### Test Individual Server

```bash
# Test filesystem server
npx -y @modelcontextprotocol/server-filesystem /workspace

# Test git server
uvx mcp-server-git --repository /workspace

# Test AWS server
uvx awslabs.aws-documentation-mcp-server@latest
```

### Test in Cursor

1. Open Cursor IDE
2. Open Copilot chat
3. Try a command that uses MCP: "List files in the repository"
4. Cursor will use the filesystem MCP server

### Debug MCP Issues

**Server not found:**
```bash
# Verify command exists
which npx
which uvx

# Test command manually
npx -y @modelcontextprotocol/server-filesystem /workspace
```

**Credentials not working:**
```bash
# Check environment variable
echo $GITHUB_JBCOM_TOKEN

# Test with env var
GITHUB_PERSONAL_ACCESS_TOKEN=$GITHUB_JBCOM_TOKEN \
  npx -y @modelcontextprotocol/server-github
```

**Server crashes:**
```bash
# Check logs in Cursor
# Settings → MCP → View Logs

# Enable debug logging
[mcp_servers.debug-server.env]
FASTMCP_LOG_LEVEL = "DEBUG"  # For awslabs servers
LOG_LEVEL = "debug"           # For other servers
```

## MCP Server Lifecycle

### When are servers started?

- **Cursor IDE:** When Cursor starts, all MCP servers in `mcp.json` are initialized
- **CLI agents:** When agent is invoked with MCP support
- **Background agents:** Via process-compose (see `process-compose.yml`)

### Server Process Management

MCP servers run as child processes of the agent/IDE. They communicate via stdio (standard input/output).

```
┌─────────────┐
│ Cursor IDE  │
│  or Agent   │
└──────┬──────┘
       │
       ├──[stdio]──→ filesystem server
       ├──[stdio]──→ git server
       ├──[stdio]──→ github server
       └──[stdio]──→ ... more servers
```

## Best Practices

### 1. Version Pinning

For reproducibility, pin versions where possible:

```toml
# Good - pinned version
[mcp_servers.example]
command = "npx"
args = ["-y", "@example/mcp-server@1.2.3"]

# Acceptable - latest (for tools that update frequently)
[mcp_servers.aws-docs]
command = "uvx"
args = ["awslabs.aws-documentation-mcp-server@latest"]
```

### 2. Error Handling

Set appropriate log levels:

```toml
[mcp_servers.production.env]
FASTMCP_LOG_LEVEL = "ERROR"  # Quiet in production

[mcp_servers.development.env]
FASTMCP_LOG_LEVEL = "DEBUG"  # Verbose for debugging
```

### 3. Resource Limits

Some servers can be resource-intensive. Monitor:

```bash
# Check running MCP processes
ps aux | grep mcp

# Check resource usage
htop  # Filter by 'mcp'
```

### 4. Security

- Never commit API keys to `.ruler/ruler.toml`
- Use environment variable references: `"${API_KEY}"`
- Restrict filesystem access: `["-y", "server-filesystem", "/workspace"]` not `/`

## Troubleshooting

### Problem: Ruler apply doesn't update mcp.json

**Solution:**
1. Check `.ruler/ruler.toml` syntax
2. Ensure `[mcp]` section has `enabled = true`
3. Verify `[agents.cursor.mcp]` is enabled
4. Run with verbose: `ruler apply --verbose` (if available)

### Problem: MCP server not accessible in Cursor

**Solution:**
1. Restart Cursor IDE
2. Check `.cursor/mcp.json` was updated
3. Verify command exists: `which npx` / `which uvx`
4. Check Cursor MCP logs

### Problem: Authentication fails

**Solution:**
1. Verify environment variable is set: `echo $GITHUB_JBCOM_TOKEN`
2. Check variable name matches in `ruler.toml`
3. Restart IDE to reload environment

### Problem: Server starts but doesn't respond

**Solution:**
1. Test server manually in terminal
2. Check server version compatibility
3. Review server-specific documentation
4. Enable debug logging

## Advanced Configuration

### Agent-Specific MCP Overrides

```toml
# Global MCP configuration
[mcp_servers.example]
command = "npx"
args = ["-y", "@example/server"]

# Cursor-specific override
[agents.cursor.mcp]
enabled = true
merge_strategy = "merge"  # merge or replace

# Can add cursor-only servers here if needed
```

### Conditional Servers

Some servers only work on certain platforms:

```toml
# Available everywhere
[mcp_servers.filesystem]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]

# Cursor-specific (background agents)
[mcp_servers.cursor_agents]
command = "cursor-background-agent-mcp-server"
# This won't work in Claude Desktop, only in Cursor
```

## Resources

- **Ruler Documentation:** https://ai.intellectronica.net/ruler
- **MCP Specification:** https://modelcontextprotocol.io/
- **MCP Servers List:** https://github.com/modelcontextprotocol/servers
- **AWS MCP Servers:** https://github.com/awslabs/mcp

---

**Last Updated:** 2025-11-27
**MCP Servers:** 17 configured
**Configuration:** `.ruler/ruler.toml`
**Status:** Production
