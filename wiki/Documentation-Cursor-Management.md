# Cursor Background Agent Management

## Overview

The Cursor Background Agent MCP Server enables this background agent to create, monitor, and manage other Cursor background agents programmatically.

## Architecture

```
This Background Agent
    ├─> cursor-agent-manager (MCP server via process-compose)
    │     ├─> Uses CURSOR_API_KEY for authentication
    │     └─> Manages agent lifecycle via Cursor API
    │
    └─> CLI Wrapper (.cursor/scripts/mcp-bridge/cursor-agents)
          └─> Provides shell access to agent management
```

## Process-Compose Service

The `cursor-agent-manager` service runs continuously in the background:

```yaml
cursor-agent-manager:
  command: "cursor-background-agent-mcp-server"
  environment:
    - "CURSOR_API_KEY=${CURSOR_API_KEY}"
    - "CURSOR_WORKSPACE_ID=${PWD}"
```

**Start the service:**
```bash
process-compose up -d cursor-agent-manager
process-compose logs cursor-agent-manager
```

## CLI Usage

The `cursor-agents` CLI wrapper provides easy access:

### List All Active Agents
```bash
cursor-agents list
```

### Create New Background Agent
```bash
cursor-agents create "Review PR #169 and fix any linting issues"
cursor-agents create "Update all package dependencies to latest versions"
cursor-agents create "Generate comprehensive test coverage report"
```

### Check Agent Status
```bash
cursor-agents status agent-abc123
```

### Stop an Agent
```bash
cursor-agents stop agent-abc123
```

## MCP Server Configuration

In `.ruler/ruler.toml`:

```toml
[mcp_servers.cursor_agents]
command = "cursor-background-agent-mcp-server"
env.CURSOR_API_KEY = "${CURSOR_API_KEY}"
env.CURSOR_WORKSPACE_ID = "${CURSOR_WORKSPACE_ID:-${PWD}}"
```

## Use Cases

### Parallel PR Reviews
```bash
# Spawn multiple agents to review different aspects
cursor-agents create "Review security implications in PR #169"
cursor-agents create "Review performance optimizations in PR #169"
cursor-agents create "Review test coverage in PR #169"
```

### Automated Maintenance
```bash
# Spawn agents for routine tasks
cursor-agents create "Update all outdated dependencies"
cursor-agents create "Run security audit and fix vulnerabilities"
cursor-agents create "Generate missing documentation"
```

### CI/CD Integration
```bash
# From GitHub Actions workflow
cursor-agents create "Fix failing tests in commit ${{ github.sha }}"
cursor-agents create "Apply code review suggestions from Amazon Q"
```

## Multi-Agent Coordination

As a background agent, I can:

1. **Spawn child agents** for parallel work
2. **Monitor their progress** via status checks
3. **Synthesize their outputs** into cohesive results
4. **Manage workload distribution** across multiple agents

### Example: Comprehensive PR Review

```bash
#!/bin/bash
# Spawn multiple specialized review agents

PR_NUM=169

# Create review agents
SECURITY=$(cursor-agents create "Security review of PR #$PR_NUM")
PERFORMANCE=$(cursor-agents create "Performance review of PR #$PR_NUM")
TESTS=$(cursor-agents create "Test coverage review of PR #$PR_NUM")
DOCS=$(cursor-agents create "Documentation review of PR #$PR_NUM")

echo "Spawned 4 review agents:"
echo "  Security: $SECURITY"
echo "  Performance: $PERFORMANCE"
echo "  Tests: $TESTS"
echo "  Docs: $DOCS"

# Wait for completion
while true; do
  ALL_DONE=true
  
  for AGENT in $SECURITY $PERFORMANCE $TESTS $DOCS; do
    STATUS=$(cursor-agents status $AGENT | grep -o "status: [^,]*")
    if [[ "$STATUS" != *"completed"* ]]; then
      ALL_DONE=false
    fi
  done
  
  if [ "$ALL_DONE" = true ]; then
    break
  fi
  
  sleep 10
done

echo "All review agents completed!"
```

## Authentication

The service uses `CURSOR_API_KEY` which is automatically available in the Cursor cloud agent environment:

```bash
echo $CURSOR_API_KEY  # Available automatically
```

## Monitoring

**Check service health:**
```bash
process-compose ps | grep cursor-agent-manager
```

**View logs:**
```bash
tail -f ./logs/cursor-agent-manager.log
```

**Check active agents:**
```bash
cursor-agents list
```

## Best Practices

### Agent Naming
Use descriptive task names:
- ✅ "Review security implications in authentication module"
- ✅ "Fix TypeScript errors in packages/extended-data-types"
- ❌ "Fix stuff"
- ❌ "Do work"

### Resource Management
- Limit concurrent agents to avoid overwhelming resources
- Monitor agent completion and clean up finished agents
- Use specific, focused tasks rather than broad "fix everything" tasks

### Error Handling
```bash
# Always check if agent creation succeeded
AGENT_ID=$(cursor-agents create "Task description")
if [ $? -ne 0 ]; then
  echo "Failed to create agent"
  exit 1
fi
```

## Integration with Multi-AI Review

The multi-AI review workflow can spawn child agents:

```yaml
- name: Spawn Review Agents
  run: |
    cursor-agents create "Review Python code quality in PR"
    cursor-agents create "Review AWS infrastructure changes in PR"
    cursor-agents create "Review documentation updates in PR"
```

## Troubleshooting

**Service not running:**
```bash
process-compose up -d cursor-agent-manager
```

**CURSOR_API_KEY not set:**
```bash
# Check environment
env | grep CURSOR_API_KEY

# Service should have access automatically in Cursor cloud agent
```

**MCP server not responding:**
```bash
# Check logs
process-compose logs cursor-agent-manager

# Restart service
process-compose restart cursor-agent-manager
```

## Future Enhancements

- Agent pooling for reuse
- Priority queues for tasks
- Agent-to-agent communication
- Distributed workload management
- Performance metrics and analytics

---

**Last Updated:** 2025-11-27
**Status:** Configured and ready to use
**Service:** cursor-agent-manager (process-compose)
