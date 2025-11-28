# Copilot MCP Secrets Configuration

## Environment Secrets

The following secrets are configured in the `copilot` GitHub environment with the `COPILOT_MCP_` prefix:

| Secret Name | Purpose |
|-------------|---------|
| `COPILOT_MCP_CURSOR_API_KEY` | Cursor background agent API access |
| `COPILOT_MCP_ANTHROPIC_API_KEY` | Anthropic Claude API access |
| `COPILOT_MCP_OPENAI_API_KEY` | OpenAI API access |
| `COPILOT_MCP_GITHUB_TOKEN` | GitHub API access (jbcom repos) |
| `COPILOT_MCP_AWS_ASSUME_ROLE_ARN` | AWS IAM role for Cursor agents |

## How Secrets Work

### For Copilot Coding Agent (GitHub.com)
Secrets with the `COPILOT_MCP_` prefix in the `copilot` environment are automatically passed to MCP servers when Copilot Coding Agent runs.

### For VS Code (Local Development)
Use the `${input:xxx}` mechanism in `.vscode/mcp.json`. VS Code prompts for values and stores them securely.

### For Cursor IDE
Secrets are read from environment variables directly. Set them in your shell:
```bash
export GITHUB_JBCOM_TOKEN="..."
export ANTHROPIC_API_KEY="..."
```

## Adding New Secrets

```bash
# Add a new secret to the copilot environment
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh secret set COPILOT_MCP_NEW_SECRET \
  --env copilot \
  --repo jbcom/jbcom-control-center \
  --body "secret-value"
```

## Verifying Secrets

```bash
# List all secrets in copilot environment
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh api \
  /repos/jbcom/jbcom-control-center/environments/copilot/secrets \
  --jq '.secrets[].name'
```

## Security Notes

1. **Never commit secrets** to repository files
2. **Use environment secrets** for Copilot Coding Agent
3. **Use `${input:}` mechanism** for VS Code local development
4. **Rotate secrets regularly** via GitHub UI or API

---

**Last Updated**: 2025-11-28
**Secrets Count**: 5
