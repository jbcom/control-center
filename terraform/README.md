# Terraform Repository Management

This directory contains Terraform configuration for managing all jbcom repositories.

## Overview

Manages 18 repositories across 4 language ecosystems:
- **Python** (8 repos): agentic-crew, ai_game_dev, directed-inputs-class, extended-data-types, lifecyclelogging, python-terraform-bridge, rivers-of-reckoning, vendor-connectors
- **Node.js** (6 repos): agentic-control, otter-river-rush, otterfall, pixels-pygame-palace, rivermarsh, strata
- **Go** (2 repos): port-api, vault-secret-sync
- **Terraform** (2 repos): terraform-github-markdown, terraform-repository-automation

## What's Managed

### Repository Settings
- Merge strategies (squash only)
- Branch deletion on merge
- Feature flags (issues, wiki, projects, discussions)
- Security scanning (secret scanning, push protection)
- Dependabot security updates

### Branch Protection
- Pull request requirements
- Review settings
- Status checks
- Linear history enforcement
- Force push protection

### GitHub Pages
- Automatic enablement with GitHub Actions workflow build

## Workspace Configuration

- **Organization**: jbcom
- **Workspace**: jbcom-control-center
- **Execution Mode**: local
- **State**: Managed in HCP Terraform Cloud

## Usage

### Initialize Terraform

```bash
cd terraform
terraform init
```

This will:
1. Download the GitHub provider (~> 6.0)
2. Configure HCP Terraform Cloud backend
3. Authenticate with your HCP token

### Plan Changes

```bash
terraform plan
```

Review the proposed changes carefully before applying.

### Apply Changes

```bash
terraform apply
```

This will sync all repository configurations to match the desired state.

### Import Existing Repositories

If repositories already exist (which they do), import them first:

```bash
# Import repository
terraform import 'github_repository.managed["agentic-control"]' agentic-control

# Import branch protection
terraform import 'github_branch_protection.main["agentic-control"]' agentic-control:main

# Repeat for all repositories...
```

Or use the provided import script:

```bash
./scripts/import-repositories.sh
```

## Environment Variables

### Required

- `TF_TOKEN_app_terraform_io`: HCP Terraform Cloud token (automatically provided in Copilot environment)
- `GITHUB_TOKEN`: GitHub PAT with repo scope (use CI_GITHUB_TOKEN secret)

### Optional

- `TF_LOG`: Set to `DEBUG` for verbose logging

## Workflow Integration

The `.github/workflows/terraform-sync.yml` workflow automatically:
1. Runs `terraform plan` on every push
2. Runs `terraform apply` on push to main
3. Runs `terraform plan` daily to detect drift
4. Comments on PRs with plan output

## Migration from Sync Workflow

The Terraform configuration replaces these jobs from `.github/workflows/sync.yml`:
- ✅ `sync-rulesets` → Replaced by `github_branch_protection`
- ✅ `sync-repo-settings` → Replaced by `github_repository`
- ✅ `sync-code-scanning` → Replaced by `github_repository_security_and_analysis`
- ✅ `sync-pages` → Replaced by `github_repository_pages`
- ⏸️ `sync-secrets` → Kept (not managed by Terraform)
- ⏸️ `sync-files` → Kept (not managed by Terraform)

## State Management

State is stored in HCP Terraform Cloud and is:
- Encrypted at rest
- Versioned (full history)
- Shareable across team members
- Locked during operations

## Troubleshooting

### Authentication Issues

```bash
# Verify HCP token
terraform login

# Verify GitHub token
gh auth status
```

### Import Conflicts

If import fails due to existing resources:

```bash
# Remove from state (doesn't delete the actual resource)
terraform state rm 'github_repository.managed["repo-name"]'

# Re-import
terraform import 'github_repository.managed["repo-name"]' repo-name
```

### Drift Detection

To check for configuration drift:

```bash
terraform plan -detailed-exitcode
```

Exit codes:
- 0: No changes needed
- 1: Error
- 2: Changes needed (drift detected)

## Files

- `providers.tf`: Provider and backend configuration
- `variables.tf`: Input variables
- `main.tf`: Repository resources
- `outputs.tf`: Output values
- `README.md`: This file
- `.terraform.lock.hcl`: Provider version lock file (committed)
- `.terraform/`: Provider binaries (ignored)
- `terraform.tfstate`: Local state (not used with cloud backend)

## References

- [GitHub Provider Documentation](https://registry.terraform.io/providers/integrations/github/latest/docs)
- [HCP Terraform Cloud](https://app.terraform.io/app/jbcom)
- [Terraform Cloud Backend](https://developer.hashicorp.com/terraform/language/backend/cloud)
