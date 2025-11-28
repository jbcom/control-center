# MCP Proxy Bridge Strategy

## Problem Statement

**Background agents cannot directly use Model Context Protocol (MCP) servers** because:
- MCP servers use `stdio` (standard input/output) transport
- Background agents run in non-interactive shells
- No persistent stdin/stdout connection exists for background processes

## Solution: Multi-Layered Bridge Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  IDE Agents (Cursor, Claude)                                    │
│  ✅ Can use MCP directly via stdio (Cursor handles this)       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    Uses MCP stdio natively
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│  Background Agents (shell scripts, automated tasks)             │
│  ❌ Cannot use stdio MCP servers                                │
│  ✅ Use HTTP/CLI bridge instead                                 │
└──────────────────────────┬───────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │   CLI Wrappers         │
              │   (.cursor/scripts/    │
              │    mcp-bridge/)        │
              │                        │
              │  - aws-iac             │
              │  - aws-serverless      │
              │  - aws-api             │
              │  - github-mcp          │
              │  - etc.                │
              └───────────┬────────────┘
                          │
                          │ HTTP POST to /call-tool
                          ▼
              ┌────────────────────────┐
              │   mcp-proxy            │
              │   (Node.js)            │
              │                        │
              │  HTTP → stdio bridge   │
              │  Port 3001-3010        │
              └───────────┬────────────┘
                          │
                          │ stdio (stdin/stdout)
                          ▼
              ┌────────────────────────┐
              │   MCP Servers          │
              │                        │
              │  - aws-iac-mcp-server  │
              │  - aws-serverless-mcp  │
              │  - aws-api-mcp         │
              │  - server-github       │
              │  - etc.                │
              └────────────────────────┘
```

## Components

### 1. MCP Proxy (mcp-proxy npm package)

**What it does:**
- Converts stdio MCP servers to HTTP/SSE endpoints
- Maintains session state for persistent connections
- Provides `/mcp` (streamable HTTP) and `/sse` (Server-Sent Events) endpoints
- Handles MCP protocol translation

**How we run it:**
```bash
mcp-proxy --port 3001 -- uvx awslabs.aws-iac-mcp-server@latest
```

**Key options:**
- `--port <N>`: Port to listen on
- `--`: Separates mcp-proxy options from the command to run
- Command after `--`: The actual MCP server to wrap

### 2. Process-Compose (Background Service Manager)

**File:** `/workspace/process-compose.yml`

**What it does:**
- Runs all MCP proxy instances as background services
- Auto-restarts failed services
- Health monitoring
- Log management
- Environment variable injection (AWS IAM role, GitHub tokens, etc.)

**Services configured:**

| Service | Port | MCP Server | Purpose |
|---------|------|-----------|---------|
| `mcp-proxy-aws-iac` | 3001 | aws-iac-mcp-server | Terraform, CloudFormation, CDK |
| `mcp-proxy-aws-serverless` | 3002 | aws-serverless-mcp-server | Lambda, SAM, Step Functions |
| `mcp-proxy-aws-api` | 3003 | aws-api-mcp-server | General AWS API access |
| `mcp-proxy-aws-cdk` | 3004 | aws-cdk-mcp-server | AWS CDK operations |
| `mcp-proxy-aws-cfn` | 3005 | aws-cfn-mcp-server | CloudFormation stacks |
| `mcp-proxy-aws-support` | 3006 | aws-support-mcp-server | AWS Support cases |
| `mcp-proxy-aws-pricing` | 3007 | aws-pricing-mcp-server | AWS pricing queries |
| `mcp-proxy-billing-cost` | 3008 | billing-cost-management | Billing & cost analytics |
| `mcp-proxy-aws-docs` | 3009 | aws-documentation | AWS documentation search |
| `mcp-proxy-github` | 3010 | server-github | GitHub API operations |

**Environment variables injected:**
- `AWS_REGION` - Default AWS region
- `CURSOR_AWS_ASSUME_IAM_ROLE_ARN` - IAM role for AWS MCP servers
- `FASTMCP_LOG_LEVEL` - Log verbosity
- `GITHUB_PERSONAL_ACCESS_TOKEN` - GitHub auth for server-github

### 3. CLI Wrappers

**Location:** `/workspace/.cursor/scripts/mcp-bridge/`

**What they do:**
- Provide simple CLI interface for background agents
- Call mcp-proxy HTTP endpoints
- Parse and format responses
- Handle errors gracefully

**Wrapper structure:**
```bash
#!/bin/bash
# CLI wrapper for <service>
set -e

MCP_PROXY_URL="${MCP_PROXY_<SERVICE>_URL:-http://localhost:<PORT>}"
TOOL_NAME="$1"
ARGS_JSON="${2:-{}}"

# List available tools if no tool name provided
if [ -z "$TOOL_NAME" ]; then
  curl -s "${MCP_PROXY_URL}/list-tools" | jq -r '.tools[] | "  - \(.name): \(.description)"'
  exit 1
fi

# Call the MCP tool via proxy
RESPONSE=$(curl -sf -X POST "${MCP_PROXY_URL}/call-tool" \
  -H "Content-Type: application/json" \
  -d "{\"name\": \"${TOOL_NAME}\", \"arguments\": ${ARGS_JSON}}")

# Pretty print response
echo "$RESPONSE" | jq -r '.content[0].text // .error // .'
```

**Available wrappers:**
- `aws-iac` - Infrastructure as Code operations
- `aws-serverless` - Lambda and serverless
- `aws-api` - General AWS API
- `aws-cdk` - AWS CDK operations
- `aws-cfn` - CloudFormation management
- `aws-support` - AWS Support interactions
- `aws-pricing` - Pricing queries
- `billing-cost` - Billing and cost management
- `aws-docs` - AWS documentation search
- `github-mcp` - GitHub operations

## Usage

### Starting Services

```bash
# Start all MCP proxy services
cd /workspace
process-compose up -d

# Check service status
process-compose ps

# View logs
process-compose logs mcp-proxy-aws-iac

# Stop all services
process-compose down
```

### Using CLI Wrappers

**Install wrappers:**
```bash
cd /workspace/.cursor/scripts/mcp-bridge
./setup.sh                # Makes scripts executable
./setup.sh --global       # Also symlinks to /usr/local/bin
```

**List available tools:**
```bash
aws-iac
aws-serverless
github-mcp
```

**Call a specific tool:**
```bash
# List CloudFormation stacks
aws-iac list_stacks '{"region": "us-east-1"}'

# Get Lambda functions
aws-serverless list_functions '{"runtime": "python3.13"}'

# Search AWS documentation
aws-docs search '{"query": "s3 permissions", "service": "s3"}'

# GitHub operations
github-mcp list_issues '{"owner": "jbcom", "repo": "extended-data-types"}'
```

**Using in background agent scripts:**
```bash
#!/bin/bash
# Example: Background agent task

# Ensure MCP services are running
if ! curl -sf http://localhost:3001/mcp > /dev/null 2>&1; then
    echo "Starting MCP services..."
    process-compose up -d
    sleep 10
fi

# Use AWS IAC tool
STACKS=$(aws-iac list_stacks '{"region": "us-east-1"}')
echo "Found stacks: $STACKS"

# Validate a template
VALIDATION=$(aws-iac validate_template '{"template_path": "./template.yaml"}')
if echo "$VALIDATION" | grep -q "error"; then
    echo "❌ Template validation failed"
    exit 1
fi

echo "✅ Template validated successfully"
```

## AWS Authentication

### Automatic IAM Role Usage

All AWS MCP proxy services automatically use the `CURSOR_AWS_ASSUME_IAM_ROLE_ARN` environment variable if set.

**How it works:**
1. Cursor background agent environment includes `CURSOR_AWS_ASSUME_IAM_ROLE_ARN`
2. `process-compose.yml` passes this to each AWS MCP proxy
3. AWS MCP servers automatically assume the role
4. No manual AWS credential configuration needed

**Fallback:**
If `CURSOR_AWS_ASSUME_IAM_ROLE_ARN` is not set, AWS MCP servers fall back to:
1. `AWS_PROFILE` environment variable
2. Default credential chain (~/.aws/credentials)

### Setting up AWS Profile (manual fallback)

```bash
# Configure AWS profile
export AWS_PROFILE=my-profile
export AWS_REGION=us-east-1

# Start services
process-compose up -d

# Verify authentication
aws sts get-caller-identity
```

## MCP Proxy API

### Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/mcp` | POST | Streamable HTTP MCP requests |
| `/sse` | GET | Server-Sent Events (SSE) stream |
| `/list-tools` | GET | List available MCP tools (custom) |
| `/call-tool` | POST | Call a specific tool (custom) |

### Example API Calls

**List available tools:**
```bash
curl -s http://localhost:3001/list-tools | jq
```

**Call a tool:**
```bash
curl -X POST http://localhost:3001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "name": "validate_template",
    "arguments": {
      "template_path": "./template.yaml"
    }
  }' | jq
```

## Monitoring and Debugging

### Health Checks

**Process-compose health checker:**
```bash
# Automatically checks all proxies every 60 seconds
process-compose logs health-checker
```

**Manual health check:**
```bash
for port in 3001 3002 3003 3004 3005 3006 3007 3008 3009 3010; do
  if curl -sf http://localhost:$port/mcp > /dev/null 2>&1; then
    echo "✅ Port $port healthy"
  else
    echo "❌ Port $port unhealthy"
  fi
done
```

### Log Files

All logs are in `/workspace/logs/`:
- `mcp-proxy-aws-iac.log` - AWS IAC proxy
- `mcp-proxy-aws-serverless.log` - AWS Serverless proxy
- `mcp-proxy-github.log` - GitHub proxy
- `health-checker.log` - Health monitoring
- `conport.log` - ConPort agent memory

**Viewing logs:**
```bash
# Via process-compose
process-compose logs mcp-proxy-aws-iac

# Direct file access
tail -f /workspace/logs/mcp-proxy-aws-iac.log
```

### Common Issues

**Issue: Port already in use**
```bash
# Kill all mcp-proxy processes
pkill -f mcp-proxy

# Restart services
process-compose up -d
```

**Issue: AWS credentials not working**
```bash
# Check IAM role variable
echo $CURSOR_AWS_ASSUME_IAM_ROLE_ARN

# Verify AWS credentials
aws sts get-caller-identity

# Check proxy logs for auth errors
process-compose logs mcp-proxy-aws-iac | grep -i error
```

**Issue: GitHub token not set**
```bash
# Set GitHub token
export GITHUB_JBCOM_TOKEN="ghp_your_token_here"

# Restart GitHub proxy
process-compose restart mcp-proxy-github
```

## Adding New MCP Services

**Steps:**

1. **Add to process-compose.yml:**
```yaml
mcp-proxy-new-service:
  command: "mcp-proxy --port 3011 -- uvx new-mcp-server@latest"
  availability:
    restart: "always"
    backoff_seconds: 5
  log_location: ./logs/mcp-proxy-new-service.log
  environment:
    - "REQUIRED_ENV_VAR=${REQUIRED_ENV_VAR}"
  readiness_probe:
    http_get:
      host: localhost
      port: 3011
      path: /mcp
    initial_delay_seconds: 8
    period_seconds: 10
```

2. **Create CLI wrapper:**
```bash
cp .cursor/scripts/mcp-bridge/aws-iac .cursor/scripts/mcp-bridge/new-service
# Edit to update:
# - MCP_PROXY_URL default port
# - Script description
```

3. **Make executable:**
```bash
chmod +x .cursor/scripts/mcp-bridge/new-service
```

4. **Update health checker:**
```yaml
# Add to health-checker command
for port in 3001 3002 ... 3011; do
```

5. **Document:**
- Add to this file
- Add to `.cursor/rules/12-mcp-bridge-usage.mdc`

## Why This Architecture?

### Benefits

✅ **Background agents can access MCP functionality**
- No stdio dependency
- Standard HTTP/CLI interface
- Works in any shell script or automated task

✅ **Automatic credential injection**
- AWS IAM role from Cursor environment
- GitHub tokens from environment
- No manual configuration

✅ **Persistent services**
- Always running in background
- Auto-restart on failure
- Health monitoring

✅ **Developer-friendly**
- Simple CLI wrappers
- JSON arguments
- Formatted output

✅ **IDE agents unaffected**
- Cursor continues using stdio MCP natively
- No performance overhead
- No changes to IDE workflow

### Tradeoffs

⚠️ **Additional complexity**
- More moving parts (mcp-proxy, process-compose)
- More ports to manage
- More logs to monitor

⚠️ **Resource usage**
- Each proxy is a Node.js process
- Memory overhead (~50-100MB per proxy)
- 10+ background processes running

⚠️ **Latency**
- HTTP overhead vs. direct stdio
- Minimal for most use cases (~10-50ms)

⚠️ **Maintenance**
- Must keep mcp-proxy updated
- Monitor process-compose status
- Manage log rotation

## Best Practices

### For Background Agents

1. **Always check service health** before using wrappers
2. **Use specific tools** (aws-iac) over general (aws-api) when available
3. **Parse JSON responses** with `jq`
4. **Handle errors gracefully**
5. **Log MCP calls** for debugging

### For Developers

1. **Use IDE MCP** when working interactively
2. **Use CLI wrappers** only in automated scripts
3. **Monitor logs** for errors
4. **Update wrappers** when adding new tools
5. **Document usage** in scripts

### For Operations

1. **Start process-compose** at system boot
2. **Monitor health-checker** logs
3. **Set up log rotation** for `/workspace/logs/`
4. **Back up process-compose.yml** configuration
5. **Test all proxies** after updates

## Future Enhancements

### Potential improvements:

- **Authentication**: Add API keys to proxy endpoints
- **Rate limiting**: Prevent abuse of MCP tools
- **Caching**: Cache frequent MCP tool responses
- **Metrics**: Prometheus metrics for monitoring
- **Load balancing**: Multiple instances per service
- **Web UI**: Dashboard for managing proxies

---

**Last Updated:** 2025-11-27
**Status:** Production-ready for jbcom-control-center
**Requires:** mcp-proxy (npm), process-compose, jq
