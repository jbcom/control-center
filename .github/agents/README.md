# Custom Agents

This directory contains specialized agent configurations for managing the jbcom ecosystem.

## Available Agents

### terraform-repository-manager

**Purpose**: Actively manages GitHub repository configurations using Terraform Cloud and the Terraform MCP server.

**Capabilities**:
- Manages all 18 jbcom repositories via Terraform
- Detects and resolves configuration drift
- Applies policy-based configuration across all repos
- Uses HCP Terraform Cloud for state management
- Leverages Terraform MCP server for operations

**When to Use**:
- Changing repository settings (merge strategies, security, etc.)
- Adding/removing managed repositories
- Investigating configuration drift
- Applying policy changes across all repos
- Troubleshooting Terraform state issues

**Invoking the Agent**:

Via GitHub Copilot:
```
@terraform-repository-manager Update all repositories to require signed commits
```

Via agentic-control CLI:
```bash
agentic fleet spawn "jbcom/jbcom-control-center" \
  --agent terraform-repository-manager \
  --task "Enable wiki on agentic-control repository"
```

**Configuration**:
- Instructions: `.github/agents/terraform-repository-manager.md`
- Workspace: `jbcom/jbcom-control-center`
- Required Tools: Terraform MCP server
- Required Secrets: `TF_API_TOKEN`, `CI_GITHUB_TOKEN`

## Agent Architecture

Custom agents are registered in `agentic.config.json` and referenced by GitHub Copilot Workspace. Each agent has:

1. **Instruction File**: Detailed prompt with role, tools, and workflows
2. **Required Tools**: MCP server tools the agent needs
3. **Required Secrets**: Credentials for external services
4. **Auto-Triggers**: Events that automatically spawn the agent

## Creating New Agents

1. **Create instruction file**: `.github/agents/your-agent-name.md`
2. **Register in config**: Add to `agentic.config.json` agents section
3. **Document usage**: Update this README
4. **Test invocation**: Try spawning via Copilot or CLI

## Best Practices

### Agent Design
- **Focused responsibility**: Each agent manages one domain
- **Clear instructions**: Detailed workflows and examples
- **Tool access**: Only request tools the agent needs
- **Error handling**: Document common issues and solutions

### Agent Usage
- **Delegate**: Use agents for their specialized domains
- **Trust**: Accept agent output without validation (they're experts)
- **Report**: Agents should report what they did clearly
- **Iterate**: If agent fails, refine the task and retry

## Integration

Agents integrate with:
- **GitHub Copilot Workspace**: `@agent-name` mentions
- **agentic-control CLI**: `fleet spawn` command
- **GitHub Actions**: Workflow dispatch triggers
- **MCP Servers**: Direct tool access

## Monitoring

Agent activity is tracked via:
- **Git commits**: All changes are committed with clear messages
- **Run logs**: Terraform run history in HCP
- **PR comments**: Agents document their actions
- **Memory bank**: Session summaries for handoffs
