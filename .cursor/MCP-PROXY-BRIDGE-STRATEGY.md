# MCP-PROXY BRIDGE STRATEGY

## The Problem

**Background agents (like Cursor background agent) CANNOT use MCP servers directly.**

MCP servers use stdio transport, which requires:
1. Persistent bidirectional communication
2. JSON-RPC message passing
3. Process lifecycle management

Background agents execute:
- Discrete CLI commands
- Fire-and-forget operations
- Shell script workflows

## The Solution: Multi-Layer Bridge

### Layer 1: mcp-proxy (SSE Proxy)
Convert stdio MCP servers to HTTP/SSE endpoints that can be called via curl/fetch.

```bash
# Install mcp-proxy globally
pnpm install -g mcp-proxy

# Start proxy for AWS IAC server (example)
mcp-proxy --server "uvx awslabs.aws-iac-mcp-server@latest" --port 3001
```

### Layer 2: process-compose Integration
Run mcp-proxy instances as persistent background services.

**File: `/workspace/process-compose.yml`**
```yaml
processes:
  # ConPort memory management
  conport:
    command: "uvx --from context-portal-mcp conport-mcp --mode stdio --workspace_id ${PWD} --log-file ./logs/conport.log --log-level INFO"
    availability:
      restart: "always"

  # MCP Proxy for AWS IAC
  mcp-proxy-aws-iac:
    command: "mcp-proxy --server 'uvx awslabs.aws-iac-mcp-server@latest' --port 3001 --log-level error"
    availability:
      restart: "always"
    environment:
      - "AWS_PROFILE=${AWS_PROFILE:-default}"
      - "AWS_REGION=${AWS_REGION:-us-east-1}"

  # MCP Proxy for AWS Serverless
  mcp-proxy-aws-serverless:
    command: "mcp-proxy --server 'uvx awslabs.aws-serverless-mcp-server@latest' --port 3002 --log-level error"
    availability:
      restart: "always"
    environment:
      - "AWS_PROFILE=${AWS_PROFILE:-default}"
      - "AWS_REGION=${AWS_REGION:-us-east-1}"

  # MCP Proxy for AWS API
  mcp-proxy-aws-api:
    command: "mcp-proxy --server 'uvx awslabs.aws-api-mcp-server@latest' --port 3003 --log-level error"
    availability:
      restart: "always"
    environment:
      - "AWS_PROFILE=${AWS_PROFILE:-default}"
      - "AWS_REGION=${AWS_REGION:-us-east-1}"

  # MCP Proxy for GitHub
  mcp-proxy-github:
    command: "mcp-proxy --server 'npx -y @modelcontextprotocol/server-github' --port 3010 --log-level error"
    availability:
      restart: "always"
    environment:
      - "GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_JBCOM_TOKEN}"
```

### Layer 3: CLI Wrapper Scripts
Create bash/python wrappers that call mcp-proxy HTTP endpoints.

**File: `/workspace/.cursor/scripts/mcp-bridge/aws-iac`**
```bash
#!/bin/bash
# CLI wrapper for AWS IAC MCP server via mcp-proxy
# Usage: aws-iac <tool_name> <arguments_json>

set -e

MCP_PROXY_URL="${MCP_PROXY_AWS_IAC_URL:-http://localhost:3001}"
TOOL_NAME="$1"
ARGS_JSON="${2:-{}}"

if [ -z "$TOOL_NAME" ]; then
    echo "Usage: aws-iac <tool_name> [args_json]"
    echo "Available tools:"
    curl -s "$MCP_PROXY_URL/tools" | jq -r '.tools[].name'
    exit 1
fi

# Call MCP tool via HTTP
curl -s -X POST "$MCP_PROXY_URL/call-tool" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$TOOL_NAME\", \"arguments\": $ARGS_JSON}" \
    | jq .

# Example usage:
# aws-iac list_stacks '{"region": "us-east-1"}'
# aws-iac validate_template '{"template_path": "./template.yaml"}'
```

### Layer 4: Background Agent Integration
Background agents call the CLI wrappers as if they were normal commands.

**In agent workflow:**
```bash
# Instead of trying to use MCP directly (impossible)
# Use the CLI wrapper:
aws-iac list_stacks '{"region": "us-east-1"}'
aws-serverless list_functions '{"runtime": "python3.13"}'
```

## Implementation Checklist

- [ ] Add mcp-proxy to Dockerfile NODE.JS GLOBAL TOOLS
- [ ] Create process-compose.yml with mcp-proxy services
- [ ] Create .cursor/scripts/mcp-bridge/ directory
- [ ] Generate CLI wrapper for each AWS MCP server
- [ ] Update agent rules to document available wrappers
- [ ] Add health check endpoint monitoring
- [ ] Document in TOOLS_REFERENCE.md

## Why This Works

1. **mcp-proxy** converts stdio → HTTP/SSE
2. **process-compose** keeps proxies running
3. **CLI wrappers** provide shell-friendly interface
4. **Background agents** use familiar CLI patterns

## Alternative: Direct MCP Client

For Python-based background agents, could use mcp client library:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# But this requires async/await and persistent connection
# Not suitable for discrete background agent tasks
```

CLI wrapper approach is simpler and more robust.

## Security Considerations

- mcp-proxy runs on localhost only (no external access)
- AWS credentials from environment (IAM role or profile)
- GitHub token from secure environment variable
- process-compose manages process isolation

## Performance

- mcp-proxy adds ~10-50ms latency per call
- Acceptable for background agent use cases
- Proxies are persistent (no startup cost per call)
- Can scale with multiple proxy instances if needed

---

**Status**: PROPOSED
**Next**: Implement in Dockerfile + process-compose.yml + scripts
**Owner**: Cursor background agent
**Date**: 2025-11-27
