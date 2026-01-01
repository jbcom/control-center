# MCP Bridge Scripts for Background Agents

## The Problem

Background agents cannot use MCP servers directly because MCP uses stdio transport which requires persistent bidirectional communication.

## The Solution

**mcp-proxy** bridges stdio MCP servers to HTTP/SSE endpoints that background agents can call via `curl`.

## Architecture

```
MCP Server (stdio)
    ↓
mcp-proxy (converts to HTTP/SSE)
    ↓
HTTP endpoint (localhost:300X)
    ↓
CLI wrapper script (this directory)
    ↓
Background agent (curl + jq)
```

## Available Wrappers

### `aws-iac` - AWS Infrastructure as Code
```bash
# List available tools
aws-iac

# Call specific tool
aws-iac list_stacks '{"region": "us-east-1"}'
aws-iac validate_template '{"template_path": "./template.yaml"}'
```

### `aws-serverless` - AWS Serverless Functions
```bash
# List Lambda functions
aws-serverless list_functions '{"runtime": "python3.13"}'
```

### `aws-api` - General AWS API Access
```bash
# Call any AWS API
aws-api describe_instances '{"region": "us-east-1"}'
```

## Setup

### 1. Start MCP Proxy Services
```bash
process-compose up -d
```

This starts:
- ConPort (agent memory)
- mcp-proxy-aws-iac (port 3001)
- mcp-proxy-aws-serverless (port 3002)
- mcp-proxy-aws-api (port 3003)
- mcp-proxy-github (port 3010)

### 2. Install CLI Wrappers
```bash
.cursor/scripts/mcp-bridge/setup.sh
```

This symlinks all wrapper scripts to `/usr/local/bin/`

### 3. Verify
```bash
aws-iac  # Should list available tools
process-compose ps  # Check all services running
```

## Usage in Background Agent Workflows

### Example: List CloudFormation Stacks
```bash
# Start services if not running
process-compose up -d

# Wait for services to be ready
sleep 5

# Call MCP tool via wrapper
aws-iac list_stacks '{"region": "us-east-1"}' | jq .
```

### Example: Validate Terraform
```bash
# Use Terraform directly for plan/apply
terraform plan -out=tfplan

# Use MCP server for best practices validation
aws-iac validate_iac '{"file_path": "./main.tf"}' | jq .
```

## Environment Variables

### AWS Configuration
```bash
export AWS_PROFILE=your-profile
export AWS_REGION=us-east-1
```

### MCP Proxy URLs (optional overrides)
```bash
export MCP_PROXY_AWS_IAC_URL=http://localhost:3001
export MCP_PROXY_AWS_SERVERLESS_URL=http://localhost:3002
export MCP_PROXY_AWS_API_URL=http://localhost:3003
export MCP_PROXY_GITHUB_URL=http://localhost:3010
```

## Troubleshooting

### Wrapper Returns "MCP proxy not running"
```bash
# Check process-compose status
process-compose ps

# Check logs
process-compose logs mcp-proxy-aws-iac

# Restart if needed
process-compose restart mcp-proxy-aws-iac
```

### Connection Refused
```bash
# Check if port is listening
netstat -tlnp | grep 3001

# Test directly
curl http://localhost:3001/tools
```

### AWS Credentials Not Working
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check environment in process
process-compose logs mcp-proxy-aws-iac | grep AWS_
```

## Adding New MCP Server Wrappers

### 1. Add to process-compose.yml
```yaml
mcp-proxy-new-server:
  command: "mcp-proxy --server 'uvx package@latest' --port 30XX"
  availability:
    restart: "always"
```

### 2. Create wrapper script
```bash
cp aws-iac new-server
# Edit to change MCP_PROXY_URL and port
chmod +x new-server
```

### 3. Update agent rules
Document new wrapper in `.cursor/rules/` as needed.

## Security

- ✅ All proxies bind to localhost only (no external access)
- ✅ AWS credentials from IAM role or profile (not hardcoded)
- ✅ GitHub token from environment variable
- ✅ process-compose manages process isolation
- ✅ Health checks ensure services are responsive

## Performance

- Latency: ~10-50ms per call (acceptable for background agents)
- Persistent proxies (no startup cost)
- Can handle concurrent requests
- Health checks prevent calling failed proxies

---

**Status**: Implemented
**Requires**: process-compose up -d
**Location**: `/workspace/.cursor/scripts/mcp-bridge/`
**Last Updated**: 2025-11-27
