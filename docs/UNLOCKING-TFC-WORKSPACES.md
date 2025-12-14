# Unlocking Terraform Cloud Workspaces

## Problem

Terraform Cloud workspaces can become locked when:
1. A previous Terraform run was interrupted (cancelled workflow, network failure, etc.)
2. Multiple runs attempt to execute simultaneously
3. A run crashes without releasing the lock

When workspaces are locked, the `terraform-sync.yml` workflow will fail with errors like:
```
Error: Error acquiring the state lock
Error: workspace is locked by run
```

## Solution

Use the `unlock-tfc-workspaces.sh` script to unlock workspaces via the Terraform Cloud API.

### Prerequisites

You need a Terraform Cloud API token with permissions to manage workspaces in the `jbcom` organization.

The token can be set via any of these environment variables:
- `TF_API_TOKEN`
- `TF_TOKEN_app_terraform_io`
- `TFE_TOKEN`

### Usage

#### List all locked workspaces (dry-run)

```bash
export TF_API_TOKEN="your-token-here"
./scripts/unlock-tfc-workspaces.sh --dry-run
```

#### Unlock all locked workspaces

```bash
export TF_API_TOKEN="your-token-here"
./scripts/unlock-tfc-workspaces.sh
```

#### Unlock a specific workspace

```bash
export TF_API_TOKEN="your-token-here"
./scripts/unlock-tfc-workspaces.sh --workspace jbcom-repo-agentic-control
```

### Script Options

| Option | Description |
|--------|-------------|
| `--dry-run` | List locked workspaces without unlocking them |
| `--workspace NAME` | Unlock only the specified workspace |
| `--organization ORG` | Target organization (default: jbcom) |
| `-h, --help` | Show help message |

## Using in GitHub Actions

### Option 1: Manual Workflow Dispatch

If you have access to GitHub Actions secrets, you can trigger the unlock via workflow dispatch:

1. Go to Actions → Terraform Sync workflow
2. Click "Run workflow"
3. Before running the main workflow, manually run the unlock script

### Option 2: Integrate into Workflow

Add a step to automatically unlock workspaces before running Terraform:

```yaml
- name: Unlock any locked workspaces
  if: always()
  working-directory: /home/runner/work/jbcom-control-center/jbcom-control-center
  run: |
    ./scripts/unlock-tfc-workspaces.sh --dry-run
    # Only unlock if there are locked workspaces
    if ./scripts/unlock-tfc-workspaces.sh --dry-run | grep -q "Found [1-9]"; then
      echo "Found locked workspaces, unlocking..."
      ./scripts/unlock-tfc-workspaces.sh
    fi
  env:
    TF_API_TOKEN: ${{ secrets.TF_TOKEN_APP_TERRAFORM_IO }}
```

## Understanding Workspace Locks

### Lock Information

Each workspace in Terraform Cloud can be in one of these states:
- **Unlocked**: Available for new runs
- **Locked**: Currently running or improperly locked from a previous run

### Lock Metadata

When listing workspaces, the API returns:
```json
{
  "id": "ws-xxxxx",
  "attributes": {
    "name": "jbcom-repo-agentic-control",
    "locked": true,
    "lock-reason": "Locked by run run-xxxxx"
  }
}
```

### Force Unlock API

The script uses the Terraform Cloud API endpoint:
```
POST /workspaces/{workspace-id}/actions/force-unlock
```

This forcefully releases the lock, even if a run is still in progress. Use with caution.

## Troubleshooting

### Error: No TFC token found

Ensure one of the required environment variables is set:
```bash
export TF_API_TOKEN="your-token-here"
```

### Error: 401 Unauthorized

Your token may be expired or lack permissions. Generate a new token from:
https://app.terraform.io/app/settings/tokens

Required permissions:
- Workspace: Read and write

### Error: 404 Not Found

The workspace or organization doesn't exist. Verify:
```bash
curl -s \
  --header "Authorization: Bearer $TF_API_TOKEN" \
  https://app.terraform.io/api/v2/organizations/jbcom/workspaces
```

## Prevention

To prevent locks in the future:

1. **Use concurrency control in workflows**:
   ```yaml
   concurrency:
     group: terragrunt-${{ github.ref }}
     cancel-in-progress: false  # Important: don't cancel running Terraform
   ```

2. **Let runs complete**: Don't cancel Terraform runs unless absolutely necessary

3. **Monitor run status**: Check the Terraform Cloud UI before starting new runs

4. **Use workspace-level locking**: Configure auto-apply carefully

## References

- [Terraform Cloud API - Workspaces](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspaces)
- [Terraform Cloud API - Force Unlock](https://developer.hashicorp.com/terraform/cloud-docs/api-docs/workspaces#force-unlock-a-workspace)
- [Terraform State Locking](https://developer.hashicorp.com/terraform/language/state/locking)
