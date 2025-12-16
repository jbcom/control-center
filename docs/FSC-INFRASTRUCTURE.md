#  Infrastructure Maintenance

## Overview

This control center manages infrastructure that deploys to these FSC repositories:

| Repo | Purpose |
|------|---------|
| `/terraform-modules` | Reusable Terraform modules |
| `/cluster-ops` | Kubernetes cluster operations |
| `/terraform-organization-administration` | Org-level Terraform |

All repos use `GITHUB_TOKEN` for API access.

## Local Infrastructure

The `ecosystems//` directory mirrors and extends these repos:

```
ecosystems//
├── terraform/
│   ├── modules/           # 100+ reusable modules
│   └── workspaces/        # 44 live workspaces
├── sam/                   # AWS Lambda apps
├── lib/terraform_modules/ # Python library
└── config/                # State paths, pipelines
```

## jbcom Package Dependencies

These FSC repos consume jbcom packages:

| Package | Used By | Purpose |
|---------|---------|---------|
| `vendor-connectors` | terraform-modules, cluster-ops | AWS, GCP, Slack clients |
| `lifecyclelogging` | All | Structured logging |
| `extended-data-types` | All | Config utilities |

### Checking Package Versions in FSC Repos

```bash
# terraform-modules (gh CLI auto-uses GITHUB_TOKEN)
gh api /repos//terraform-modules/contents/requirements.txt \
  --jq '.content' | base64 -d | grep -E "vendor-connectors|lifecyclelogging|extended-data-types"

# cluster-ops
gh api /repos//cluster-ops/contents/requirements.txt \
  --jq '.content' | base64 -d | grep -E "vendor-connectors|lifecyclelogging|extended-data-types"
```

### Updating FSC to Use New Package Versions

After releasing a jbcom package:

```bash
# Clone the FSC repo (uses GITHUB_TOKEN from environment)
git clone https://github.com//terraform-modules.git /tmp/terraform-modules
cd /tmp/terraform-modules

# Update requirements
# Edit requirements.txt or pyproject.toml with new versions

# Test
pip install -e .
pytest

# Create PR
git checkout -b deps/update-jbcom-packages
git add requirements.txt
git commit -m "deps: update jbcom packages

- vendor-connectors: X.Y.Z
- lifecyclelogging: X.Y.Z"
gh pr create --title "deps: update jbcom packages"
```

## Token Configuration

All FSC organizations use the unified `GITHUB_TOKEN`:

| Org | Repos |
|-----|-------|
|  | terraform-modules |
|  | cluster-ops |
|  | terraform-organization-administration |

The `gh` CLI automatically uses `GITHUB_TOKEN` from environment.

## Key Operations

### Check CI Status

```bash
# terraform-modules (gh CLI auto-uses GITHUB_TOKEN)
gh run list --repo /terraform-modules --limit 5

# cluster-ops
gh run list --repo /cluster-ops --limit 5
```

### View Open PRs

```bash
gh pr list --repo /terraform-modules
gh pr list --repo /cluster-ops
```

### Spawn Agent to FSC Repo

```bash
agentic fleet spawn "https://github.com//terraform-modules" "Update to latest jbcom packages"
agentic fleet spawn "https://github.com//cluster-ops" "Fix CI"
```

## Local Development

### Terraform

```bash
cd ecosystems//terraform/workspaces/terraform-aws-organization/<workspace>
terraform init
terraform plan
terraform apply  # Requires AWS creds
```

### SAM Lambda

```bash
cd ecosystems//sam/<app>
sam build
sam local invoke  # Test locally
sam deploy        # Requires AWS creds
```

### Python Library

```bash
cd ecosystems//lib
pip install -e .
python -m terraform_modules --help
```

## Sync Relationship

```
jbcom-control-center (this repo)
├── packages/vendor-connectors  ─────→  PyPI
│                                         │
│                                         ▼
└── ecosystems//     FSC repos consume from PyPI
                                    ├── /terraform-modules
                                    ├── /cluster-ops
                                    └── /...
```

---

**Related**: [docs/JBCOM-ECOSYSTEM-INTEGRATION.md](./JBCOM-ECOSYSTEM-INTEGRATION.md)
