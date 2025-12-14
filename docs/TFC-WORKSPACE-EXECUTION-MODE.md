# TFC Workspace Execution Mode

## Issue

After the workspace unlock operation, Terraform apply was failing with:

```
Error: No Terraform configuration files found in working directory
```

This error affected all 18 repository workspaces in Terraform Cloud.

## Root Cause

The TFC workspaces were configured with `execution_mode = "remote"`, which tells Terraform Cloud to execute Terraform itself. However:

1. **Our Setup**: The GitHub Actions workflow runs **Terragrunt locally** (CLI-driven workflow)
2. **TFC's Role**: TFC is used ONLY for **remote state storage**, not for executing Terraform
3. **Directory Structure**: The working directories (`terragrunt-stacks/{language}/{repo}`) only contain `terragrunt.hcl` files, NOT `.tf` files
4. **The Problem**: When TFC tries to execute with `execution_mode = "remote"`, it looks for `.tf` files in the working directory and finds none

### Why No .tf Files?

Terragrunt generates `.tf` files dynamically during `terragrunt init/plan/apply`:
- `provider.tf` - Generated from root config
- `backend.tf` - Generated from root config
- `imports.tf` - Generated from unit config

These files are:
- Generated in `.terragrunt-cache/` (excluded from git)
- Never committed to the repository
- Not available to TFC when it tries to execute remotely

## Solution

Change the execution mode from `"remote"` to `"local"` in the bootstrap configuration.

### What Changed

**File**: `terragrunt-stacks/bootstrap/terragrunt.hcl`

```hcl
# Before
default_execution_mode = "remote"

# After
default_execution_mode = "local"
```

### Execution Mode Comparison

| Mode | Where Terraform Runs | TFC Role | Requires .tf Files in Repo |
|------|---------------------|----------|---------------------------|
| `remote` | In Terraform Cloud | Executes Terraform | ✅ Yes |
| `local` | On your machine / CI | Stores state only | ❌ No |
| `agent` | On TFC agent | Executes Terraform | ✅ Yes |

### Why "local" is Correct

Our GitHub Actions workflow (`.github/workflows/terraform-sync.yml`) runs:

```bash
terragrunt run-all plan --non-interactive
terragrunt run-all apply --non-interactive
```

This is a **CLI-driven workflow**:
1. Terragrunt runs locally (in GitHub Actions runner)
2. Terragrunt generates `.tf` files locally
3. Terragrunt runs `terraform init/plan/apply` locally
4. Terraform connects to TFC **only** to read/write state
5. TFC never executes Terraform itself

## Applying the Fix

### Prerequisites

```bash
export TF_API_TOKEN="your-terraform-cloud-api-token"
```

### Steps

1. **Navigate to bootstrap directory**:
   ```bash
   cd terragrunt-stacks/bootstrap
   ```

2. **Initialize Terragrunt**:
   ```bash
   terragrunt init
   ```

3. **Review the changes**:
   ```bash
   terragrunt plan
   ```

   You should see updates for all 18 workspaces changing `execution_mode` from "remote" to "local".

4. **Apply the changes**:
   ```bash
   terragrunt apply
   ```

5. **Verify**:
   - Visit https://app.terraform.io/app/jbcom/workspaces
   - Check any workspace (e.g., `jbcom-repo-strata`)
   - Under "Settings" → "General", verify "Execution Mode" is now "Local"

## Testing

After applying the bootstrap changes, test that terraform-sync workflow works:

1. **Manual test via workflow dispatch**:
   - Go to Actions → "Terragrunt Repository Sync"
   - Click "Run workflow"
   - Select "apply: false" (plan only)
   - Verify no "No Terraform configuration files found" errors

2. **Full test with apply**:
   - Run workflow dispatch with "apply: true"
   - Verify all 18 repositories are updated successfully

## Prevention

The `default_execution_mode` variable in `terragrunt-stacks/modules/tfe-workspaces/main.tf` now has enhanced documentation:

```hcl
variable "default_execution_mode" {
  type        = string
  description = <<-EOT
    Execution mode for workspaces:
    - "local": Terraform runs locally (CLI-driven), TFC only stores state (recommended for this setup)
    - "remote": TFC runs Terraform (requires .tf files in working_directory, not compatible with Terragrunt-only repos)
    - "agent": TFC agent runs Terraform
  EOT
  default     = "remote"
  ...
}
```

## References

- [Terraform Cloud Execution Modes](https://developer.hashicorp.com/terraform/cloud-docs/workspaces/settings#execution-mode)
- [CLI-Driven Workflow](https://developer.hashicorp.com/terraform/cloud-docs/run/cli)
- [Terragrunt Generate Blocks](https://terragrunt.gruntwork.io/docs/reference/config-blocks-and-attributes/#generate)

## Related Issues

- Original issue: "TFC workspaces showing 'No Terraform configuration files found'"
- Related to workspace unlock operation and Docker Hub removal
- `agentic-triage` was not affected because it doesn't have a TFC workspace (not in repo lists)
