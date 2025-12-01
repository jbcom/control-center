# Token Management

## Overview

The unified control center manages two GitHub organizations with different tokens:

| Organization | Token Env Var | Use Case |
|--------------|---------------|----------|
| jbcom | `GITHUB_JBCOM_TOKEN` | Personal repos, packages |
| FlipsideCrypto | `GITHUB_FSC_TOKEN` | Enterprise infrastructure |

## Configuration

### Environment Variables

```bash
# Required
export GITHUB_JBCOM_TOKEN="ghp_..."
export GITHUB_FSC_TOKEN="ghp_..."

# Optional (defaults to GITHUB_JBCOM_TOKEN)
export GITHUB_TOKEN="$GITHUB_JBCOM_TOKEN"
```

### agentic.config.json

```json
{
  "tokens": {
    "organizations": {
      "jbcom": {
        "name": "jbcom",
        "tokenEnvVar": "GITHUB_JBCOM_TOKEN"
      },
      "FlipsideCrypto": {
        "name": "FlipsideCrypto",
        "tokenEnvVar": "GITHUB_FSC_TOKEN"
      }
    },
    "defaultTokenEnvVar": "GITHUB_TOKEN",
    "prReviewTokenEnvVar": "GITHUB_JBCOM_TOKEN"
  }
}
```

## Automatic Token Switching

The `agentic-control` CLI automatically selects the correct token based on repository organization:

```bash
# Uses GITHUB_JBCOM_TOKEN
agentic github pr create --repo jbcom/extended-data-types

# Uses GITHUB_FSC_TOKEN
agentic github pr create --repo FlipsideCrypto/terraform-modules
```

### How It Works

1. Parse repository URL to extract organization
2. Look up organization in `agentic.config.json`
3. Read token from specified environment variable
4. Use token for API calls

### PR Reviews Exception

**PR reviews ALWAYS use `GITHUB_JBCOM_TOKEN`**, regardless of target repo.

This ensures consistent identity across both ecosystems.

## Manual Token Usage

When using `gh` CLI directly:

```bash
# jbcom repos
GH_TOKEN="$GITHUB_JBCOM_TOKEN" gh pr create ...

# FlipsideCrypto repos
GH_TOKEN="$GITHUB_FSC_TOKEN" gh pr create ...
```

## Token Permissions

### GITHUB_JBCOM_TOKEN

Required scopes:
- `repo` - Full repository access
- `workflow` - GitHub Actions
- `write:packages` - Package publishing

### GITHUB_FSC_TOKEN

Required scopes:
- `repo` - Full repository access
- `admin:org` - Organization management (for enterprise)
- `workflow` - GitHub Actions

## Security

### DO
- Store tokens in environment variables
- Use `agentic.config.json` for organization mapping
- Let `agentic-control` handle token selection

### DON'T
- Hardcode tokens in code
- Commit tokens to git
- Log token values
- Share tokens across machines

## Troubleshooting

### "Bad credentials"

Token is invalid or expired. Generate a new one at:
- jbcom: https://github.com/settings/tokens
- FlipsideCrypto: https://github.com/settings/tokens (with org access)

### "Resource not accessible"

Token lacks required scopes. Check permissions and regenerate if needed.

### "Organization access denied"

For FlipsideCrypto, ensure:
1. Token has org access enabled
2. SSO authorization completed (if required)

## Related

- [`agentic.config.json`](/agentic.config.json) - Token configuration
- [`packages/agentic-control/`](/packages/agentic-control/) - Token switching implementation
