# Terragrunt Repository Manager - Quick Start

## Overview

Manage all 18 jbcom repositories using Terragrunt with a shared module.

## Prerequisites

- Terraform >= 1.5.0
- Terragrunt >= 0.77
- `GITHUB_TOKEN` with repo admin permissions

## Quick Start

### 1. Plan All Repositories

```bash
cd terragrunt-stacks
terragrunt run-all plan --non-interactive
```

### 2. Apply All Repositories

```bash
cd terragrunt-stacks
terragrunt run-all apply --non-interactive
```

### 3. Check Single Repository

```bash
cd terragrunt-stacks/python/agentic-crew
terragrunt plan
```

## Directory Structure

```
terragrunt-stacks/
├── terragrunt.hcl              # Root config
├── modules/repository/main.tf  # Shared module
├── python/                     # 8 Python repos
├── nodejs/                     # 6 Node.js repos
├── go/                         # 2 Go repos
└── terraform/                  # 2 Terraform repos

repository-files/
├── always-sync/                # Files synced every apply
├── initial-only/               # Files created once
└── {language}/                 # Language-specific rules
```

## Common Changes

### Enable Wiki on a Repository

```hcl
# terragrunt-stacks/nodejs/agentic-control/terragrunt.hcl
inputs = {
  name     = "agentic-control"
  language = "nodejs"
  has_wiki = true  # Enable wiki
}
```

### Change Required Approvals

```hcl
inputs = {
  name               = "agentic-control"
  language           = "nodejs"
  required_approvals = 1  # Require 1 approval
}
```

### Disable File Sync for a Repository

```hcl
inputs = {
  name       = "agentic-control"
  language   = "nodejs"
  sync_files = false  # Don't sync Cursor rules
}
```

## What's Managed

- Repository settings (merge options, features)
- Branch protection (approvals, linear history)
- Security (secret scanning, push protection)
- GitHub Pages (Actions workflow)
- File sync (Cursor rules, workflows)

## Workflow Automation

The GitHub Actions workflow (`terraform-sync.yml`) handles:
- **Pull Request**: Plans changes
- **Push to main**: Applies changes
- **Daily at 2 AM UTC**: Drift detection
- **Manual dispatch**: On-demand plan/apply

## Next Steps

1. Review plan output
2. Apply to establish baseline
3. Monitor drift detection
4. Make incremental changes via PR
