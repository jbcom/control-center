# Token Management

## Overview

The control center uses a unified GitHub token for all operations:

| Variable | Purpose |
|----------|---------|
| `GITHUB_TOKEN` | All GitHub API operations (gh CLI, Terraform, etc.) |
| `CI_GITHUB_TOKEN` | Same token, used in CI/CD workflows |

## Configuration

### Environment Variables

```bash
# Required - set in your environment or CI
export GITHUB_TOKEN="ghp_..."

# CI workflows use this (same value)
export CI_GITHUB_TOKEN="$GITHUB_TOKEN"
```

### agentic.config.json

The config maps all organizations to use the unified token:

```json
{
  "tokens": {
    "organizations": {
      "jbcom": {
        "name": "jbcom",
        "tokenEnvVar": "GITHUB_TOKEN"
      },
      "": {
        "name": "", 
        "tokenEnvVar": "GITHUB_TOKEN"
      }
    },
    "defaultTokenEnvVar": "GITHUB_TOKEN"
  }
}
```

## Usage

### gh CLI

The `gh` CLI automatically uses `GITHUB_TOKEN` from environment:

```bash
# All repos work without explicit token
gh pr list --repo jbcom/jbcom-control-center
gh pr list --repo /terraform-modules
gh issue create --repo jbcom/agentic-control
```

### Terraform/Terragrunt

Terraform uses `GITHUB_TOKEN` via the GitHub provider:

```hcl
provider "github" {
  owner = "jbcom"
  # Token from GITHUB_TOKEN env var
}
```

## Token Permissions

The unified token requires these scopes:

- `repo` - Full repository access
- `workflow` - GitHub Actions
- `write:packages` - Package publishing (npm, PyPI)
- `admin:org` - Organization management (for enterprise repos)

## CI/CD Workflows

Workflows use `CI_GITHUB_TOKEN` secret:

```yaml
env:
  GITHUB_TOKEN: ${{ secrets.CI_GITHUB_TOKEN }}
```

This is the same token as `GITHUB_TOKEN`, just stored as a secret.

## Security

### DO
- Store tokens in environment variables
- Use secrets in CI/CD workflows
- Rotate tokens periodically

### DON'T
- Hardcode tokens in code
- Commit tokens to git
- Log token values
- Share tokens across machines

## Troubleshooting

### "Bad credentials"

Token is invalid or expired. Generate a new one at:
- https://github.com/settings/tokens

### "Resource not accessible"

Token lacks required scopes. Check permissions and regenerate if needed.

### "Organization access denied"

For  or enterprise orgs, ensure:
1. Token has org access enabled
2. SSO authorization completed (if required)

## Related

- [`agentic.config.json`](/agentic.config.json) - Token configuration
- [`.github/workflows/`](/.github/workflows/) - CI/CD workflows using tokens
