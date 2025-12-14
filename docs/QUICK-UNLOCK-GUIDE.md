# Quick Unlock Guide

When the terraform-sync workflow fails with "workspace is locked" errors, use one of these methods:

## Method 1: Let the Workflow Handle It (Recommended)

The terraform-sync workflow now automatically checks for and unlocks locked workspaces. Simply retry the workflow:

```bash
gh workflow run terraform-sync.yml
```

The workflow will:
1. Check for locked workspaces
2. Automatically unlock them
3. Proceed with Terraform operations

## Method 2: Manual Unlock via GitHub Actions

If you prefer manual control:

1. Go to Actions → "Unlock TFC Workspaces"
2. Click "Run workflow"
3. Set `dry_run: false`
4. Click "Run workflow"

Or via CLI:
```bash
# Check for locks (dry-run)
gh workflow run unlock-tfc-workspaces.yml

# Unlock all locked workspaces
gh workflow run unlock-tfc-workspaces.yml -f dry_run=false

# Unlock specific workspace
gh workflow run unlock-tfc-workspaces.yml -f dry_run=false -f workspace=jbcom-repo-agentic-control
```

## Method 3: Run Script Locally

If you have TFC API access:

```bash
# Set your TFC token
export TF_API_TOKEN="your-token-here"

# Check for locks
./scripts/unlock-tfc-workspaces.sh --dry-run

# Unlock all
./scripts/unlock-tfc-workspaces.sh

# Unlock specific workspace
./scripts/unlock-tfc-workspaces.sh --workspace jbcom-repo-agentic-control
```

## How to Get TFC Token

1. Go to https://app.terraform.io/app/settings/tokens
2. Generate a new token
3. Set as environment variable: `export TF_API_TOKEN="your-token"`

## Common Scenarios

### Scenario 1: Cancelled Workflow
**Problem**: You cancelled a terraform-sync run mid-execution  
**Solution**: Wait 5 minutes or run unlock manually

### Scenario 2: Network Failure
**Problem**: Workflow failed due to network timeout  
**Solution**: Automatic unlock will handle it on retry

### Scenario 3: Multiple Simultaneous Runs
**Problem**: Two workflows tried to run Terraform simultaneously  
**Solution**: Use concurrency control (already in place), unlock if needed

## Verification

After unlocking, verify workspace status:

```bash
# Via API
curl -s \
  --header "Authorization: Bearer $TF_API_TOKEN" \
  "https://app.terraform.io/api/v2/organizations/jbcom/workspaces/jbcom-repo-agentic-control" \
  | jq '.data.attributes.locked'
```

Should return `false`.

## Prevention

1. **Don't cancel Terraform runs** unless absolutely necessary
2. **Use workflow concurrency control** (already configured)
3. **Let runs complete** before starting new ones
4. **Monitor run status** in TFC UI: https://app.terraform.io/app/jbcom/workspaces

## Need More Help?

See full documentation: [UNLOCKING-TFC-WORKSPACES.md](./UNLOCKING-TFC-WORKSPACES.md)
